import { Canvas, type Op, type Style } from '../draw/canvas';
import { skinMs } from '../host/scheduler';
import type { RGBA } from '../lib/theme';
import { popupFrame } from '../draw/popup';

// The timeline and the system check of Skins/Spaceship/Overlay/Boot (boot.lua, Boot.ini), redrawn (2026-11-02): no
// scanner line. Ignition: corner brackets lock on from the screen edges, a ring draws itself with a bright head, a
// dashed counter-ring and a tick ring flicker on, and INITIALIZING counts up over a bar. Then the system check panel
// (the pop-ups' lit glass) lists six rows, each flickering in and filling a small bar before its status, and a verdict
// band; then the overlay fades out. Elements enter with a short flicker, as film and game start-ups do. Not ported: the panel fade-ins (the live modules are the panels here, not the old meters), the
// boot sound (an OS action), and the Storage / Audio / Network readings (no host feed yet: they show --).
// shortcut: the panel count is the 29 modules in Data/zones.lua, copied as a constant, upgrade: read it from the layout.

export const FRAME_MS = skinMs(16); // the skin's Update=16, which Rainmeter runs at ~32 fps
export const PANELS = 29;
const P0 = 22, PSTEP = 0.7, PFADE = 12;
const ROW_Y0 = 627, ROW_STEP = 27; // Boot.ini: row 1 at Y 627, each next row 27 lower

export type Timeline = { c0: number; verdict: number; fade: number; done: number };
/** The frames of each stage, for a given number of panels. */
export function bootTimeline(panels = PANELS): Timeline {
  const last = P0 + Math.floor((panels - 1) * PSTEP) + PFADE;
  const c0 = last + 4;
  const verdict = c0 + 4 + 6 * 5 + 4;
  const fade = verdict + 60;
  return { c0, verdict, fade, done: fade + 14 };
}

const ease = (t: number) => { const k = Math.max(0, Math.min(1, t)); return k < 0.5 ? 2 * k * k : 1 - ((-2 * k + 2) ** 2) / 2; };

/** How far the ignition ring has drawn itself at frame f, 0..1. */
export function ringProgress(f: number): number {
  return ease((f - 4) / 30);
}

/** Entry flicker: hidden before frame a, then a short on-off-on, then steady. Returns a 0..1 alpha factor. */
export function flicker(f: number, a: number): number {
  const age = f - a;
  return age < 0 ? 0 : age === 0 ? 0.55 : age === 1 ? 0.15 : age === 2 ? 0.8 : 1;
}

export type Sev = 'ok' | 'warn' | 'alert' | 'unknown';
export type CheckRow = { label: string; value: string; sev: Sev };
export type BootInput = { cpu?: number; mem?: number; onAc?: boolean; bat?: number };

const pct = (v: number) => `${Math.round(v)}%`;

/** The six rows of the system check. Unknown readings show -- and are not counted as faults. */
export function bootRows(input: BootInput): CheckRow[] {
  const { cpu, mem, onAc, bat } = input;
  const power: { value: string; sev: Sev } = onAc === undefined && bat === undefined
    ? { value: '--', sev: 'unknown' }
    : {
      value: [onAc === undefined ? '' : onAc ? 'AC' : 'BAT', bat === undefined ? '--' : pct(bat)].filter(Boolean).join(' '),
      sev: onAc === false && bat !== undefined && bat < 20 ? 'warn' : 'ok',
    };
  return [
    { label: 'CPU / GPU', value: cpu === undefined ? '--' : `${pct(cpu)} / --`, sev: cpu === undefined ? 'unknown' : cpu >= 90 ? 'warn' : 'ok' },
    { label: 'MEMORY', value: mem === undefined ? '--' : pct(mem), sev: mem === undefined ? 'unknown' : mem >= 90 ? 'warn' : 'ok' },
    { label: 'STORAGE', value: '--', sev: 'unknown' },
    { label: 'NETWORK', value: '--', sev: 'unknown' },
    { label: 'AUDIO', value: '--', sev: 'unknown' },
    { label: 'POWER', ...power },
  ];
}

/** The verdict line. Unknown rows are named, so a half-checked system is not reported as all nominal. */
export function bootVerdict(rows: CheckRow[]): { text: string; warn: boolean } {
  const warns = rows.filter((r) => r.sev === 'warn' || r.sev === 'alert').length;
  const unknown = rows.filter((r) => r.sev === 'unknown').length;
  if (warns > 0) return { text: `${warns} SYSTEM${warns > 1 ? 'S' : ''} NEED ATTENTION`, warn: true };
  if (unknown > 0) return { text: `NO FAULTS, ${unknown} NOT FED`, warn: false };
  return { text: 'ALL SYSTEMS NOMINAL', warn: false };
}

const CX = 1280, CY = 520; // the ignition ring sits in the windscreen, above the check panel
const PX = 1068, PY = 566, PW = 424, PH = 266; // the check panel, where Boot.ini put its box

/** One frame of the overlay: the ignition (brackets, ring, count-up), then the check panel with its rows and verdict. */
export function bootFrame(f: number, rows: CheckRow[], tl: Timeline, canvas: { w: number; h: number }, st: Style): Op[] {
  const c = new Canvas({ x: 0, y: 0, w: canvas.w, h: canvas.h }, st);
  const A1 = st.accent, W = st.white;
  const checking = f >= tl.c0;
  const dimK = checking ? 0.35 : 1; // the ignition stays behind the check panel, quieter
  const say = (x: number, ty: number, t: string, align: string, color: RGBA, size: number, alpha = 255, font = st.fontText) =>
    c.text(x, ty, t, { size: size / st.textLarge, align, color, alpha, font, glow: true });

  // corner brackets lock on from the screen edges to the windscreen box
  const lk = ease(f / 18);
  const bx0 = 40 + (840 - 40) * lk, by0 = 40 + (250 - 40) * lk, bx1 = canvas.w - bx0, by1 = 790 - (790 - (canvas.h - 40)) * (1 - lk);
  const bl = 46, ba = 230 * dimK;
  c.poly([[bx0, by0 + bl], [bx0, by0], [bx0 + bl, by0]], A1, 1.8, ba);
  c.poly([[bx1 - bl, by0], [bx1, by0], [bx1, by0 + bl]], A1, 1.8, ba);
  c.poly([[bx1, by1 - bl], [bx1, by1], [bx1 - bl, by1]], A1, 1.8, ba);
  c.poly([[bx0 + bl, by1], [bx0, by1], [bx0, by1 - bl]], A1, 1.8, ba);

  // the ring: a faint full guide, the drawn arc and its bright head
  const p = ringProgress(f), R = 196;
  c.circle(CX, CY, R, A1, 0.8, 50 * dimK);
  if (p > 0) {
    const a0 = -90, a1 = -90 + 360 * p;
    c.arc(CX, CY, R, a0, a1, A1, 2.2, 240 * dimK);
    if (p < 1) { const ah = (a1 * Math.PI) / 180; c.dot(CX + R * Math.cos(ah), CY + R * Math.sin(ah), 4, W, 255 * dimK); }
  }
  // dashed counter-ring, turning the other way
  const fd = flicker(f, 12);
  if (fd > 0) c.dashArc(CX, CY, 222, -f * 2, -f * 2 + 300, A1, 1.2, 170 * fd * dimK, 14, 9);
  // tick ring: each tick flickers on in turn, every sixth one long
  for (let i = 0; i < 72; i++) {
    const k = flicker(f, 14 + Math.floor(i * 0.3));
    if (k === 0) continue;
    const ang = ((i * 5 - 90) * Math.PI) / 180, r1 = i % 6 === 0 ? 262 : 254;
    c.hair(CX + 246 * Math.cos(ang), CY + 246 * Math.sin(ang), CX + r1 * Math.cos(ang), CY + r1 * Math.sin(ang), A1, i % 6 === 0 ? 1.6 : 1, (i % 6 === 0 ? 220 : 120) * k * dimK);
  }
  // centre: the name, a caption and the count-up over its bar
  // the centre text gives way to the check panel (the ring and ticks stay behind it, quieter)
  const gone = checking ? Math.max(0, 1 - (f - tl.c0) / 3) : 1;
  const ft = flicker(f, 20) * gone, fc = flicker(f, 24) * gone, fp = flicker(f, 26) * gone;
  if (ft > 0) say(CX, CY - 46, 'CSPACE', 'CenterCenter', W, 30, 255 * ft * dimK, st.fontTitle);
  if (fc > 0) say(CX, CY - 8, 'FLIGHT SYSTEMS', 'CenterCenter', A1, 13, 230 * fc * dimK);
  if (fp > 0) {
    const pct = Math.min(100, Math.max(0, Math.round(((f - 26) / Math.max(1, tl.c0 - 6 - 26)) * 100)));
    const done = pct >= 100;
    say(CX - 120, CY + 34, done ? 'ONLINE' : 'INITIALIZING', 'LeftCenter', done ? st.good : st.text, 11, 255 * fp * dimK);
    say(CX + 120, CY + 34, `${pct}%`, 'RightCenter', W, 11, 255 * fp * dimK, st.fontNum);
    c.fillRect(CX - 120, CY + 52, 240, 3, A1, 50 * fp * dimK);
    c.fillRect(CX - 120, CY + 52, 240 * pct / 100, 3, done ? st.good : A1, 240 * fp * dimK);
  }

  // the system check panel
  if (checking) {
    const fpnl = flicker(f, tl.c0);
    popupFrame(c, st, PW, PH, 40, 16, PX, PY, 255 * fpnl);
    say(PX + 22, PY + 21, 'SYSTEM CHECK', 'LeftCenter', W, 13, 255 * fpnl);
    say(PX + PW - 22, PY + 21, '02 //', 'RightCenter', A1, 10, 200 * fpnl, st.fontNum);
    c.hair(PX + 14, PY + 40, PX + PW - 14, PY + 40, st.dim, 1, 160 * fpnl);
    c.line(PX + 14, PY + 40, PX + 134, PY + 40, A1, 1.4, 230 * fpnl);
    rows.forEach((r, i) => {
      const at = tl.c0 + 4 + i * 5, k = flicker(f, at);
      if (k === 0) return;
      const ry = ROW_Y0 + i * ROW_STEP;
      const col = r.sev === 'alert' ? st.alert : r.sev === 'warn' ? st.warn : r.sev === 'ok' ? st.good : st.dim;
      const fill = Math.min(1, (f - at) / 4);
      say(PX + 24, ry, r.label, 'LeftCenter', st.text, 11, 255 * k);
      say(PX + 296, ry, r.value, 'RightCenter', W, 11, 255 * k);
      c.fillRect(PX + 310, ry - 1.5, 54, 3, A1, 45 * k);
      c.fillRect(PX + 310, ry - 1.5, 54 * fill, 3, fill < 1 ? A1 : col, 230 * k);
      if (fill >= 1) say(PX + PW - 24, ry, r.sev === 'ok' ? 'OK' : r.sev === 'unknown' ? '--' : r.sev === 'alert' ? 'FAIL' : 'CHECK', 'RightCenter', col, 11, 255 * k);
    });
    if (f >= tl.verdict) {
      const v = bootVerdict(rows), k = flicker(f, tl.verdict), vc = v.warn ? st.warn : st.good;
      c.fillRect(PX + 14, 792, PW - 28, 30, vc, 34 * k);
      c.fillRect(PX + 14, 792, 3, 30, vc, 255 * k);
      say(CX, 808, v.text, 'CenterCenter', vc, 13, 255 * k);
    }
  }
  return c.flush();
}
