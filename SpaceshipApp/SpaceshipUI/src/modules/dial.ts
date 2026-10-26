import { Canvas, arcPts, mix, type Op, type Style, type Zone } from '../draw/canvas';

// Port of Skins/Spaceship/@Resources/Scripts/dial.lua: the systems dial (round, bottom left) with six controls on a ring:
// BRT, VOL, MIC, PWR, HZ, GLW. Drawn from plain values only. Not ported: the clicks and scroll, the setters (ShipCore,
// Windows audio, Legion Toolkit, GlowAlpha), the power-on spin-up and the right-click settings pages. The power modes and
// refresh rates are the skin's defaults; shortcut: LltPowerModes and LltRefreshRates are not read, so a custom list shows as the defaults.

const K = 1.13;
const CX = 94.5, CY = 84;
const A0 = 135, SWEEP = 270;
const R_TICK = 74 * K, R_SEG = 64 * K, R_VAL = 55 * K, R_IN = 46 * K;
const R_LBL = 82 * K + 2;
const POWER_NAMES: Record<string, string> = { quiet: 'QUIET', balance: 'BALANCED', performance: 'PERFORM', custom: 'CUSTOM', godmode: 'GOD MODE' };

/** Sensor values for the dial. A missing one is unavailable, as the skin's -1 defaults are. */
export type DialInput = {
  bright?: number; mic?: number; micMuted?: boolean; vol?: number;
  power?: string; refresh?: string; glowAlpha?: number;
  /** Values just set, shown until a reading replaces them (Lua pending). Same units as the value: index for steps, 0..1 for ranges. */
  pending?: Partial<Record<string, number>>;
};

export type Ctl = { id: string; label: string; name: string; ang: number; steps?: string[] };
export const CONTROLS: Ctl[] = [
  { id: 'bright', label: 'BRT', name: 'BRIGHTNESS', ang: 205 },
  { id: 'vol', label: 'VOL', name: 'VOLUME', ang: 180 },
  { id: 'mic', label: 'MIC', name: 'MICROPHONE', ang: 155 },
  { id: 'power', label: 'PWR', name: 'POWER MODE', ang: -25, steps: ['quiet', 'balance', 'performance'] },
  { id: 'hz', label: 'HZ', name: 'REFRESH', ang: 0, steps: ['60', '165'] },
  { id: 'glow', label: 'GLW', name: 'HUD GLOW', ang: 25 },
];

/** Current value: a range gives 0..1 (undefined = unavailable); a stepped control gives its 1-based index (undefined = unknown). */
export function valueOf(c: Ctl, inp: DialInput): number | undefined {
  const p = inp.pending?.[c.id];
  if (p !== undefined) return p;
  if (c.id === 'bright') return inp.bright !== undefined && inp.bright >= 0 ? inp.bright / 100 : undefined;
  if (c.id === 'mic') return inp.mic !== undefined && inp.mic >= 0 ? inp.mic / 100 : undefined;
  if (c.id === 'vol') { const v = inp.vol ?? -1; return v >= 0 ? v / 100 : 0; }
  if (c.id === 'glow') return Math.min(1, Math.max(0, (inp.glowAlpha ?? 60) / 160));
  if (c.id === 'power') {
    const cur = (inp.power ?? '').toLowerCase();
    const i = c.steps!.findIndex((m) => cur.includes(m));
    return i >= 0 ? i + 1 : undefined;
  }
  const cur = (inp.refresh ?? '').match(/\d+/)?.[0];
  const i = c.steps!.indexOf(cur ?? '');
  return i >= 0 ? i + 1 : undefined;
}

const frac = (c: Ctl, v?: number) => (v === undefined ? 0 : c.steps ? (c.steps.length > 1 ? (v - 1) / (c.steps.length - 1) : 1) : v);

function labelOf(c: Ctl, v?: number): string {
  if (c.steps) {
    if (!v) return '--';
    const s = c.steps[v - 1];
    return c.id === 'hz' ? `${s} HZ` : POWER_NAMES[s] ?? s.toUpperCase();
  }
  return v === undefined ? '--' : `${Math.floor(v * 100 + 0.5)}%`;
}

/** The dial in its zone. sel is the 1-based control the glass wedge points at (DialSel in State.inc). */
export function dialFrame(inp: DialInput, zone: Zone, st: Style, sel = 1, note = ''): Op[] {
  const c = new Canvas(zone, st);
  const A1 = st.accent, W = st.white, D = st.dim;
  const cur = CONTROLS[sel - 1] ?? CONTROLS[0];
  const v = valueOf(cur, inp);
  const avail = v !== undefined;
  const f = frac(cur, v);
  const va = A0 + SWEEP * f;
  // core glass
  c.halo(CX, CY, 20, A1, 30);
  c.fillCircle(CX, CY, R_IN - 4, st.panel, 140);
  // tick scale across the top, lit up to the value
  for (let i = 0; i <= 10; i++) {
    const a = 225 + i * 9, lit = avail && a <= va, ar = (a * Math.PI) / 180;
    c.hair(CX + (R_TICK - 5) * Math.cos(ar), CY + (R_TICK - 5) * Math.sin(ar), CX + R_TICK * Math.cos(ar), CY + R_TICK * Math.sin(ar), lit ? A1 : D, lit ? 2.2 : 1.8, lit ? 255 : 170);
  }
  // segmented ring: 40 dashes for ranges, one segment per option for stepped controls
  const segs = cur.steps ? cur.steps.length : 40;
  const seglen = (R_SEG * (SWEEP * Math.PI / 180)) / segs;
  const dash = seglen * (cur.steps ? 0.86 : 0.68), gap = seglen * (cur.steps ? 0.14 : 0.32);
  c.dashArc(CX, CY, R_SEG, A0, A0 + SWEEP, D, 5, 175, dash, gap, true);
  if (avail) {
    const litTo = cur.steps ? A0 + (SWEEP * v) / segs : va;
    if (litTo > A0 + 0.5) c.dashArc(CX, CY, R_SEG, A0, litTo, A1, 5, 255, dash, gap);
  }
  // thick value arc and its track
  c.hairPoly(arcPts(CX, CY, R_VAL, R_VAL, A0, A0 + SWEEP, 60), D, 150, 3);
  if (avail && f > 0.002) c.arc(CX, CY, R_VAL, A0, va, mix(A1, W, 0.25), 3.6, 255);
  if (avail) {
    const ar = (va * Math.PI) / 180;
    c.dot(CX + R_VAL * Math.cos(ar), CY + R_VAL * Math.sin(ar), 3.4, W);
  }
  // inner thin ring with three gaps
  for (let q = 0; q < 3; q++) c.arc(CX, CY, R_IN, q * 120 + 100, q * 120 + 200, A1, 1.5, 220);
  // glass wedge pointing at the selected control
  c.sector(CX, CY, R_IN + 2, R_TICK + 6, cur.ang - 13, cur.ang + 13, A1, 46, 160);
  // labels around the dial
  CONTROLS.forEach((k, i) => {
    const ar = (k.ang * Math.PI) / 180;
    const on = i + 1 === sel;
    c.text(CX + R_LBL * Math.cos(ar), CY + R_LBL * Math.sin(ar), k.label, { size: 5.8, weight: 700, align: 'CenterCenter', color: on ? W : A1, alpha: on ? 255 : 225, font: st.fontNum });
  });
  // centre readout
  c.text(CX, CY - 17, cur.name, { size: 4.2, weight: 700, align: 'CenterCenter', color: A1, glow: false });
  c.text(CX, CY + 2, labelOf(cur, v), { size: cur.steps ? 7 : 10.5, weight: 700, align: 'CenterCenter', color: avail ? W : D, font: st.fontNum });
  let sub = '';
  if (note) sub = note;
  else if (!avail) sub = cur.id === 'power' || cur.id === 'hz' ? 'NEEDS LEGION TOOLKIT' : cur.id === 'bright' ? 'NO PANEL CONTROL' : 'NO DATA';
  else if (cur.id === 'mic' && inp.micMuted) sub = 'MUTED';
  else if (inp.pending?.[cur.id] !== undefined) sub = 'SETTING...';
  c.text(CX, CY + 20, sub, { size: 3.4, weight: 700, align: 'CenterCenter', color: st.warn, glow: false });
  return c.flush();
}

// Hit areas in zone coordinates, the same boxes the skin's H.hit makes: six 30 x 18 label boxes and the ring disc.
export const DIAL_LABEL_HITS = CONTROLS.map((k, i) => {
  const ar = (k.ang * Math.PI) / 180;
  return { i, x: CX + R_LBL * Math.cos(ar) - 15, y: CY + R_LBL * Math.sin(ar) - 9, w: 30, h: 18 };
});
export const DIAL_RING = { cx: CX, cy: CY, r: R_TICK + 2 };
export const DIAL_CENTRE = { cx: CX, cy: CY, r: R_IN - 4 };

/** Scroll on control i (0-based): a stepped control moves one option, a range moves 0.02 (glow 0.05). Returns the value to set. */
export function stepValue(i: number, inp: DialInput, dir: number): number {
  const c = CONTROLS[i];
  const v = valueOf(c, inp);
  if (c.steps) return Math.max(1, Math.min(c.steps.length, (v ?? 1) + dir));
  return Math.max(0, Math.min(1, (v ?? 0) + dir * (c.id === 'glow' ? 0.05 : 0.02)));
}

/** A click on the ring (dx, dy from the dial centre): the value at that point on the sweep, or undefined inside the inner disc. */
export function ringValue(i: number, dx: number, dy: number): number | undefined {
  if (Math.hypot(dx, dy) < R_IN - 4) return undefined;
  let a = (Math.atan2(dy, dx) * 180) / Math.PI;
  while (a < A0) a += 360;
  let f = (a - A0) / SWEEP;
  if (f > 1) f = (f - 1) * SWEEP < (360 - SWEEP) / 2 ? 1 : 0;
  const c = CONTROLS[i];
  return c.steps ? Math.floor(f * (c.steps.length - 1) + 0.5) + 1 : f;
}
