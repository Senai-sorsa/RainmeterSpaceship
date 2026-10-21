import { Canvas, type Op, type Style, type Zone } from '../draw/canvas';
import type { Pt } from '../lib/geometry';

// Port of the usage mode of Skins/Spaceship/@Resources/Scripts/target.lua: the target lock reticle that roams the upper
// windscreen. It glides to a new spot (smoothstep), dwells one second with a lock pulse, then moves on, and every spot
// is checked so the whole reticle stays on the glass. Not ported: the Obsidian to-do mode (needs a note-file channel),
// the sprite haze, the hover text and the clicks (rank change and taskmgr are actions for later).
// The readout shows rank 1 and -- for memory until per-process figures are fed.

const SXR = 2560 / 1260, SYR = 1600 / 709;
const ZX = 412, ZY = 108; // zone origin in reference px (ref_layout C_target) and the windscreen's slanted sides
const WIN_TOP = 104, WIN_LX0 = 342.3, WIN_RX0 = 917.7, SLOPE = (500.8 - 342.3) / (365.5 - 104);
const EXT_L = 126, EXT_R = 102, EXT_U = 102, EXT_D = 102; // reticle extents from its centre, zone px (box + readout on the left)
const RED: [number, number, number, number] = [255, 70, 52, 255], HOT: [number, number, number, number] = [255, 150, 130, 255];

export type TargetState = {
  frame: number; pos: Pt; from: Pt; to: Pt | null; t0: number; dur: number; dwellUntil: number;
  rot: number; lockAnim: number; lastName: string;
};
export type TargetInput = { name?: string; cpu?: number; ram?: number };
export type Rnd = () => number;

export const targetState = (zone: Zone): TargetState => {
  const p: Pt = [zone.w / 2, zone.h / 2];
  return { frame: 0, pos: p, from: p, to: null, t0: 0, dur: 1, dwellUntil: 1, rot: 0, lockAnim: 0, lastName: '' };
};

/** Is the reticle centred at zone px (x, y) fully on the windscreen glass? The lowest point decides: the glass narrows down. */
export function inside(zone: Zone, x: number, y: number): boolean {
  if (x - EXT_L < 0 || x + EXT_R > zone.w || y - EXT_U < 0 || y + EXT_D > zone.h) return false;
  const yr = ZY + (y + EXT_D) / SYR;
  if (yr < WIN_TOP) return false;
  const left = WIN_LX0 + (yr - WIN_TOP) * SLOPE;
  const right = WIN_RX0 - (yr - WIN_TOP) * SLOPE;
  return ZX + (x - EXT_L) / SXR >= left + 2 && ZX + (x + EXT_R) / SXR <= right - 2;
}

/** A random inside spot at least 140 px (Manhattan) from where it is now; the zone centre when forty tries fail. */
export function pickNext(zone: Zone, from: Pt, rnd: Rnd): Pt {
  for (let i = 0; i < 40; i++) {
    const x = EXT_L + rnd() * (zone.w - EXT_L - EXT_R);
    const y = EXT_U + rnd() * (zone.h - EXT_U - EXT_D);
    if (inside(zone, x, y) && Math.abs(x - from[0]) + Math.abs(y - from[1]) > 140) return [x, y];
  }
  return [zone.w / 2, zone.h / 2];
}

/** Ease in, speed up, ease out. */
const smoother = (t: number) => t * t * t * (t * (t * 6 - 15) + 10);

/** One step of the roam. step 0 parks it (LOW and STEALTH tiers), 1 is the full rate, 2 the lite rate. */
export function targetMove(state: TargetState, zone: Zone, input: TargetInput, step: number, rnd: Rnd) {
  state.frame += 1;
  const now = state.frame * 0.05;
  if (input.name !== undefined && input.name !== state.lastName) {
    state.lastName = input.name;
    state.lockAnim = 18;
  }
  if (step === 0) return;
  if (state.to) {
    const k = Math.min(1, (now - state.t0) / state.dur);
    const e = smoother(k);
    const { from, to } = state;
    state.pos = [from[0] + (to[0] - from[0]) * e, from[1] + (to[1] - from[1]) * e];
    if (k >= 1) {
      state.pos = to;
      state.to = null;
      state.dwellUntil = now + 1;
      state.lockAnim = 12;
    }
  } else if (now >= state.dwellUntil) {
    state.from = [state.pos[0], state.pos[1]];
    state.to = pickNext(zone, state.pos, rnd);
    const dist = Math.hypot(state.to[0] - state.from[0], state.to[1] - state.from[1]);
    state.t0 = now;
    state.dur = Math.max(1.4, Math.min(3.2, dist / 220));
  }
  state.rot = (state.rot + 1.6 * step) % 360;
}

export function targetFrame(state: TargetState, input: TargetInput, zone: Zone, st: Style, step = 1): Op[] {
  const c = new Canvas(zone, st);
  const [cx, cy] = state.pos;
  const cpu = input.cpu ?? 0;
  const now = state.frame * 0.05;
  const rot = state.rot;
  let zoom = 1;
  if (state.lockAnim > 0) {
    zoom = 1 + (state.lockAnim / 18) * 0.08;
    state.lockAnim -= step;
  }
  const R = 86 * zoom;
  // four outer arcs, gaps on the diagonals, rotating
  for (let q = 0; q < 4; q++) {
    const a0 = rot + q * 90 - 33;
    c.arc(cx, cy, R, a0, a0 + 66, RED, 2.6, 250);
  }
  // thick segmented inner ring, counter-rotating, breathing with the target's CPU share
  const pulse = step > 0 ? Math.sin(now * 4) * 0.05 : 0;
  const r2 = 36 * (1 + pulse);
  const thick = 5 + 3 * Math.max(0, Math.min(1, cpu / 50));
  for (let q = 0; q < 3; q++) {
    const a0 = -rot * 1.4 + q * 120 + 5;
    c.arc(cx, cy, r2, a0, a0 + 116, HOT, thick, 250);
  }
  c.fillCircle(cx, cy, r2 - thick - 2, [20, 60, 140, 255], 150);
  c.dot(cx, cy, 3.5, st.accent);
  // [n] box and memory readout to the left
  const bx0 = cx + (604 - 657) * SXR, by0 = cy + (192 - 203) * SYR;
  const bw = 11 * SXR, bh = 11 * SYR;
  const flash = state.lockAnim > 0 && state.lockAnim % 4 < 2;
  c.rect(bx0, by0, bw, bh, RED, 1.8, flash ? 120 : 255);
  c.text(bx0 + bw / 2, by0 + bh / 2, '1', { size: 8, weight: 700, align: 'CenterCenter', color: RED });
  const ram = input.ram ?? 0;
  c.text(bx0 + bw / 2 - 2, cy + 7 * SYR, ram > 0 ? `${Math.round(ram / 1048576)}m` : '--', { size: 7.5, weight: 700, align: 'CenterCenter', color: RED });
  return c.flush();
}
