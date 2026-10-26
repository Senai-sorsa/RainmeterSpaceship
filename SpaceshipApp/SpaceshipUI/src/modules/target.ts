import { Canvas, type Op, type Style, type Zone } from '../draw/canvas';
import type { Pt } from '../lib/geometry';
import type { TodoItem } from '../host/statusFeed';
import haze from '../../../../Skins/Spaceship/@Resources/Images/haze.png?url';

// Port of the usage mode of Skins/Spaceship/@Resources/Scripts/target.lua: the target lock reticle that roams the upper
// windscreen. It glides to a new spot (smoothstep), dwells one second with a lock pulse, then moves on, and every spot
// is checked so the whole reticle stays on the glass. With open to-dos (host todo.update, ReticleTodo) it locks onto the
// next one due: count in the box, countdown, label and blips for the next three. Not ported: the hover
// text and the clicks (open the note, rank change and taskmgr are actions for later).
// Without to-dos it locks onto the rank-th busiest process (host procs.top): the rank in the box, its memory below.

const SXR = 2560 / 1260, SYR = 1600 / 709;
const ZX = 412, ZY = 108; // zone origin in reference px (ref_layout C_target) and the windscreen's slanted sides
const WIN_TOP = 104, WIN_LX0 = 342.3, WIN_RX0 = 917.7, SLOPE = (500.8 - 342.3) / (365.5 - 104);
const EXT_L = 126, EXT_R = 102, EXT_U = 102, EXT_D = 102; // reticle extents from its centre, zone px (box + readout on the left)
const RED: [number, number, number, number] = [255, 70, 52, 255], HOT: [number, number, number, number] = [255, 150, 130, 255];

export type TargetState = {
  frame: number; pos: Pt; from: Pt; to: Pt | null; t0: number; dur: number; dwellUntil: number;
  rot: number; lockAnim: number; lastName: string;
};
export type TargetInput = { rank?: number; name?: string; cpu?: number; ram?: number; todos?: TodoItem[]; todoCount?: number; nowS?: number };
const DAYS = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
const MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
const pad = (n: number) => String(n).padStart(2, '0');

/** Time left as target.lua shows it: LATE, 42M, 5H07, 3D. */
export function countdown(sec: number): string {
  if (sec < 0) return 'LATE';
  if (sec < 3600) return `${Math.floor(sec / 60)}M`;
  if (sec < 86400) return `${Math.floor(sec / 3600)}H${pad(Math.floor((sec % 3600) / 60))}`;
  return `${Math.floor(sec / 86400)}D`;
}

/** The label under the reticle: the text, cut at 26, then the due day (and time when it has one), local time. */
export function todoLabel(t: TodoItem): string {
  let label = t.text.toUpperCase();
  if (label.length > 26) label = `${label.slice(0, 25)}.`;
  if (t.due === null) return label;
  const d = new Date(t.due * 1000);
  const when = t.timed ? `${DAYS[d.getDay()]} ${pad(d.getHours())}:${pad(d.getMinutes())}` : `${DAYS[d.getDay()]} ${pad(d.getDate())} ${MONTHS[d.getMonth()]}`;
  return `${label}  |  ${when}`;
}
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
  // haze (pre-blurred sprite, wide and horizontal like the reference)
  c.sprite(cx, cy, R * 2.4, R * 1.5, haze, RED, st.tier < 2 ? 235 : 140);
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
  const todos = input.todos ?? [];
  const todo = todos[0];
  if (todo) {
    const nowS = input.nowS ?? Date.now() / 1000;
    c.text(bx0 + bw / 2, by0 + bh / 2, String(input.todoCount ?? todos.length), { size: 8, weight: 700, align: 'CenterCenter', color: RED });
    c.text(bx0 + bw / 2 - 2, cy + 7 * SYR, todo.due === null ? 'NO DUE' : countdown(todo.due - nowS), { size: 7.5, weight: 700, align: 'CenterCenter', color: RED });
    c.text(cx, cy + R + 12, todoLabel(todo), { size: 6.2, weight: 700, align: 'CenterCenter', color: RED, font: st.fontNum });
    // the next items: blips on the ring, closer to the centre the sooner they're due (within a week)
    todos.slice(1, 4).forEach((it, i) => {
      if (it.due === null) return;
      const d = Math.max(0, Math.min(1, (it.due - nowS) / (7 * 86400)));
      const rr = r2 + 8 + (R - r2 - 8) * d;
      const a = ((rot * 0.3 + i * 120 - 90) * Math.PI) / 180;
      const x = cx + rr * Math.cos(a), y = cy + rr * Math.sin(a);
      c.poly([[x, y - 5], [x + 5, y], [x, y + 5], [x - 5, y]], HOT, 1.4, 230, true);
    });
    return c.flush();
  }
  c.text(bx0 + bw / 2, by0 + bh / 2, String(input.rank ?? 1), { size: 8, weight: 700, align: 'CenterCenter', color: RED });
  const ram = input.ram ?? 0;
  c.text(bx0 + bw / 2 - 2, cy + 7 * SYR, ram > 0 ? `${Math.round(ram / 1048576)}m` : '--', { size: 7.5, weight: 700, align: 'CenterCenter', color: RED });
  return c.flush();
}
