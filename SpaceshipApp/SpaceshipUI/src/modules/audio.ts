import { arcPts, Canvas, mix, type Op, type Style, type Zone } from '../draw/canvas';
import { type Pt } from '../lib/geometry';
import type { RGBA } from '../lib/theme';
import { type Readings, val } from './readings';

// Port of Skins/Spaceship/@Resources/Scripts/audio.lua: band smoothing, the peak and loudness followers, the pulse
// ring, the volume arc and the readout text. Volume and device are not reported by the host yet, so they show --.
// The boot spin-up is left out (the app has no boot sequence), so spin is always 1.

export const NB = 96;
export const DASH_A0 = 120;
export const DASH_SWEEP = 300;
const NS = 96;
// the skin window is 18 px larger than the zone on every side: the dial uses that margin
const K = 1.16;
const CX = 94.5, CY = 82.5;
const R_DASH = 70 * K, R_TICK = 78 * K, R_SWEEP = 58 * K, R_RING1 = 50 * K, R_RING2 = 45 * K, R_W0 = 25 * K, R_W1 = 41 * K;
const WEDGE = [-26, 26];
const VIOLET: RGBA = [150, 100, 255, 255];

export type AudioState = { sm: number[]; rmsS: number; peakS: number; breath: number; quiet: number };

export const audioState = (): AudioState => ({ sm: new Array<number>(NB).fill(0), rmsS: 0, peakS: 0, breath: 0, quiet: 0 });

const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));

/** One smoothing step per redraw. `every` is the frame step since the last redraw; `disabled` zeroes the levels. */
export function follow(s: AudioState, r: Readings, every: number, disabled: boolean): void {
  const rms = disabled ? 0 : clamp(val(r, 'mRMS'), 0, 1);
  const peak = disabled ? 0 : clamp(val(r, 'mPeak'), 0, 1);
  s.rmsS = s.rmsS * 0.6 + rms * 0.4;
  s.peakS = Math.max(peak, s.peakS * 0.85);
  s.quiet = rms < 0.01 ? s.quiet + every : 0;
  for (let i = 0; i < NB; i++) {
    const v = disabled ? 0 : clamp(val(r, `mBand${i}`), 0, 1);
    s.sm[i] = s.sm[i] * 0.5 + v * 0.5;
  }
}

/** Spoke tip levels 0..1 for the pulse ring. Moves the breath toward the loudness; idle gives a slow ripple. */
export function ringLevels(s: AudioState, idle: boolean, frame: number): number[] {
  // the spectrum is laid out twice round the ring (mirrored), so the ring stays balanced
  const raw: number[] = [];
  for (let k = 0; k < NS; k++) {
    let u = (k / NS) * 2;
    if (u > 1) u = 2 - u;
    const f = u * (NB - 1);
    const i0 = Math.floor(f), i1 = Math.min(NB - 1, i0 + 1);
    raw[k] = Math.sqrt(clamp(s.sm[i0] * (1 - (f - i0)) + s.sm[i1] * (f - i0), 0, 1));
  }
  // a wide gaussian window turns the spectrum into gentle rounded swells
  const soft: number[] = [];
  for (let k = 0; k < NS; k++) {
    let acc = 0, wsum = 0;
    for (let d = -8; d <= 8; d++) {
      const w = Math.exp(-(d * d) / 18);
      acc += raw[(((k + d) % NS) + NS) % NS] * w;
      wsum += w;
    }
    soft[k] = acc / wsum;
  }
  const mean = soft.reduce((a, b) => a + b, 0) / NS;
  s.breath += (clamp(mean * 1.4 + s.rmsS * 1.2, 0, 1) - s.breath) * 0.35;
  return soft.map((x, k) =>
    idle ? 0.12 + 0.04 * Math.sin((k / NS) * 2 * Math.PI * 3 + frame * 0.05) : 0.7 * s.breath + 0.3 * x);
}

/** End angle in degrees of the volume arc: sweeps from DASH_A0 by the volume share, scaled by the spin-up (0..1). */
export const volumeAngle = (vol: number, spin: number) => DASH_A0 + DASH_SWEEP * clamp(vol / 100, 0, 1) * spin;

/** The readout under the dial: MUTED for a negative volume, else the percent after the spin-up. */
export function readout(vol: number, spin: number): string {
  if (vol < 0) return 'MUTED';
  return `${Math.floor(Math.max(0, vol) * spin + 0.5)}%`;
}

/** The device name as the dial shows it: upper case, the bracketed part dropped. */
export function deviceLabel(name = 'NO DEVICE'): string {
  // shortcut: a nested bracket keeps its tail (Lua's %b() drops the whole group), upgrade when a device name needs it
  return name.toUpperCase().replace(/\s*\([^)]*\)/g, '');
}

export type AudioFrame = Op[];

/**
 * The audio zone: pulse ring, volume dash arc, readout and device. Advances the followers once per call (one per host reading).
 * vol is 0..100, or negative for muted; undefined means the host has no volume yet and the dial shows --.
 */
export function audioFrame(s: AudioState, r: Readings, zone: Zone, st: Style, frame: number, vol?: number, dev?: string): AudioFrame {
  follow(s, r, 1, st.tier >= 3);
  const c = new Canvas(zone, st);
  const A1 = st.accent, W = st.white, D = st.dim, RED = st.hi;
  const muted = vol !== undefined && vol < 0;
  const v = vol === undefined || muted ? 0 : vol;
  // halo, then the glass wedge holding the media keys
  c.halo(CX, CY, 22, A1, 34);
  c.sector(CX, CY, R_RING2 - 2, R_TICK + 4, WEDGE[0], WEDGE[1], A1, 40, 150);
  // top tick scale: red peak meter
  for (let i = 0; i < 13; i++) {
    const a = 238 + (i * 64) / 12;
    const [x0, y0] = P(R_TICK - 5, a), [x1, y1] = P(R_TICK + 2, a);
    if ((i + 1) / 13 <= s.peakS + 0.02) c.line(x0, y0, x1, y1, RED, 2.6, 255);
    else c.hair(x0, y0, x1, y1, RED, 2, 160);
  }
  // outer ring: 30 rounded dashes, lit for the volume
  const seg = (R_DASH * DASH_SWEEP * Math.PI) / 180 / 30;
  c.dashArc(CX, CY, R_DASH, DASH_A0, DASH_A0 + DASH_SWEEP, D, 4.2, 190, seg * 0.42, seg * 0.58, true);
  if (!muted && v > 0) c.dashArc(CX, CY, R_DASH, DASH_A0, volumeAngle(v, 1), A1, 4.2, 255, seg * 0.42, seg * 0.58);
  // thick loudness sweep, lower left: the cyan track always lit, live loudness bright over it
  c.arc(CX, CY, R_SWEEP, 112, 212, A1, 4.6, 150);
  if (s.rmsS > 0.01) c.arc(CX, CY, R_SWEEP, 112, 112 + 100 * clamp(s.rmsS * 1.6, 0, 1), mix(A1, W, 0.6), 5, 255);
  // thin concentric rings with gaps
  for (let q = 0; q < 4; q++) c.arc(CX, CY, R_RING1, q * 90 + 12, q * 90 + 78, A1, 1.5, 220);
  c.arc(CX, CY, R_RING2, 200, 340, W, 1.3, 190); c.arc(CX, CY, R_RING2, 20, 160, W, 1.3, 190);
  // pulse ring: 96 spokes in eight paths, cyan at the top left blending to violet at the bottom right
  // shortcut: idle is a quiet loudness follower, not the Lua's exact idle test
  const lv = ringLevels(s, s.rmsS < 0.02 || st.tier >= 3, frame);
  const tips = lv.map((x) => R_W0 + 2 + x * (R_W1 - R_W0 - 2));
  for (let q = 0; q < 8; q++) {
    const pts: Pt[] = [];
    for (let k = (q * NS) / 8; k <= ((q + 1) * NS) / 8; k++) {
      const a = (k / NS) * 360 - 90;
      pts.push(P(R_W0 + 1, a), P(tips[k % NS], a), P(R_W0 + 1, a));
    }
    const mid = ((((q + 0.5) / 8) * 360 - 90 - 45) * Math.PI) / 180;
    c.hairPoly(pts, mix(A1, VIOLET, 0.9 * (0.5 + 0.5 * Math.cos(mid))), 175, 1);
  }
  const ring: Pt[] = [];
  for (let k = 0; k <= NS; k++) ring.push(P(tips[k % NS] + 1.5, (k / NS) * 360 - 90));
  c.poly(ring, mix(A1, W, 0.55), 1.2, 235);
  c.hairPoly(arcPts(CX, CY, R_W0, R_W0, 0, 360, 64), A1, 190, 1.3);
  // glowing core, pulsing with the loudness; red X over it when muted
  const pulse = clamp(s.rmsS * 2.2, 0, 1);
  c.fillCircle(CX, CY, R_W0 - 3, st.panel, 170);
  if (st.tier < 2) for (let k = 3; k >= 1; k--) c.fillCircle(CX, CY, 7 + k * 4.5 + pulse * 4, mix(A1, W, 0.6), Math.floor((45 + pulse * 45) / k));
  c.dot(CX, CY, 3.8 + pulse * 2.5, muted ? D : W);
  if (muted) { c.line(CX - 7, CY - 7, CX + 7, CY + 7, RED, 1.8); c.line(CX + 7, CY - 7, CX - 7, CY + 7, RED, 1.8); }
  // media keys in the wedge
  (['prev', 'play', 'next'] as const).forEach((kind, i) => { const [x, y] = P(R_TICK - 6, -18 + i * 18); glyph(c, kind, x, y, i === 1 ? W : A1); });
  // readout in the ring's gap: volume (-- until the host reports one), device, and the title on top
  c.text(CX, CY + 71, vol === undefined ? '--' : readout(vol, 1), { size: 7.2, weight: 700, align: 'CenterCenter', color: muted ? RED : W, font: st.fontNum });
  c.text(CX, CY + 83, deviceLabel(dev), { size: 4, weight: 700, align: 'CenterCenter', color: D, glow: false, clip: 90 });
  c.text(CX, CY - 74, 'AUDIO', { size: 4, weight: 700, align: 'CenterCenter', color: A1, glow: false });
  return c.flush();
}

const P = (r: number, a: number): Pt => [CX + r * Math.cos((a * Math.PI) / 180), CY + r * Math.sin((a * Math.PI) / 180)];

/** Small media glyphs centred at x, y (audio.lua glyph). */
function glyph(c: Canvas, kind: 'prev' | 'play' | 'next', x: number, y: number, col: RGBA) {
  const s = 5.2;
  if (kind === 'prev') {
    c.poly([[x + s * 0.4, y - s], [x - s * 0.6, y], [x + s * 0.4, y + s]], col, 1.3, 255, true);
    c.line(x - s * 0.9, y - s, x - s * 0.9, y + s, col, 1.3);
  } else if (kind === 'next') {
    c.poly([[x - s * 0.4, y - s], [x + s * 0.6, y], [x - s * 0.4, y + s]], col, 1.3, 255, true);
    c.line(x + s * 0.9, y - s, x + s * 0.9, y + s, col, 1.3);
  } else c.poly([[x - s * 0.5, y - s * 1.1], [x + s * 0.8, y], [x - s * 0.5, y + s * 1.1]], col, 1.4, 255, true);
}
