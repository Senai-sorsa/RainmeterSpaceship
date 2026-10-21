import { Canvas, type Op, type Style, type Zone } from '../draw/canvas';
import { type Pt } from '../lib/geometry';
import { type Readings, val } from './readings';

// Port of Skins/Spaceship/@Resources/Scripts/audio.lua: band smoothing, the peak and loudness followers, the pulse
// ring, the volume arc and the readout text. Volume and device are not reported by the host yet, so they show --.
// shortcut: the dial geometry is set by eye from the zone, not copied from audio.lua; check it against rmsim before live use.

export const NB = 96;
export const DASH_A0 = 120;
export const DASH_SWEEP = 300;
const NS = 96;
const CX = 94.5, CY = 82.5, DIAL_R = 30, RING_R = 36, RING_MAX = 16;

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
  // shortcut: idle is a quiet loudness follower, not the Lua's exact idle test
  const idle = s.rmsS < 0.02;
  const lv = ringLevels(s, idle, frame);
  const pts: Pt[] = lv.map((x, k) => {
    const a = (-90 + (k * 360) / NS) * Math.PI / 180;
    const rr = RING_R + RING_MAX * x;
    return [CX + rr * Math.cos(a), CY + rr * Math.sin(a)];
  });
  c.poly(pts, st.accent, 1.3, 200, true);
  lv.forEach((x, k) => {
    if (k % 4 !== 0) return;
    const a = (-90 + (k * 360) / NS) * Math.PI / 180;
    c.line(CX + (RING_R - 4) * Math.cos(a), CY + (RING_R - 4) * Math.sin(a), CX + (RING_R + RING_MAX * x) * Math.cos(a), CY + (RING_R + RING_MAX * x) * Math.sin(a), st.accent, 1, 110);
  });
  c.dashArc(CX, CY, DIAL_R, DASH_A0, DASH_A0 + DASH_SWEEP, st.accent, 1.2, 60, 3, 4, true);
  if (vol !== undefined) c.dashArc(CX, CY, DIAL_R, DASH_A0, volumeAngle(vol, 1), st.accent, 2.4, 230, 3, 4);
  c.fillCircle(CX, CY, DIAL_R - 7, st.dim, 40);
  c.icon('wave', CX, CY - 8, 12, st.accent, 1.2);
  c.text(CX, CY + 6, vol === undefined ? '--' : readout(vol, 1), { size: 7, weight: 700, align: 'CenterCenter', color: st.white });
  c.text(CX, zone.h - 12, deviceLabel(dev), { size: 4.2, weight: 700, align: 'CenterCenter', color: st.accent, clip: zone.w - 20 });
  return c.flush();
}
