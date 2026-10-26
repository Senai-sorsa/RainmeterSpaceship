import { Canvas, type Op, type Style } from '../draw/canvas';
import { skinMs } from '../host/scheduler';

// Port of the timeline, the system check and the drawing of Skins/Spaceship/Overlay/Boot (boot.lua, Boot.ini).
// The scanner line sweeps the canvas top to bottom, then the system check lists six rows and a verdict, then the
// overlay fades out. Not ported: the panel fade-ins (the live modules are the panels here, not the old meters), the
// boot sound (an OS action), and the Storage / Audio / Network readings (no host feed yet: they show --).
// shortcut: the panel count is the 29 modules in Data/zones.lua, copied as a constant, upgrade: read it from the layout.

export const FRAME_MS = skinMs(16); // the skin's Update=16, which Rainmeter runs at ~32 fps
export const PANELS = 29;
const SCAN0 = 2, SCANN = 28;
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

/** Scanner centre line in reference px, or null once the sweep is over. */
export function scanY(f: number, canvasH: number): number | null {
  if (f > SCAN0 + SCANN) return null;
  const t = Math.max(0, Math.min(1, (f - SCAN0) / SCANN));
  const eased = t < 0.5 ? 2 * t * t : 1 - ((-2 * t + 2) ** 2) / 2;
  return eased * 0.35 * canvasH + t * 0.65 * canvasH - 20;
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

/** One frame of the overlay: the scanner, the check box with the rows shown so far, the verdict. */
export function bootFrame(f: number, rows: CheckRow[], tl: Timeline, canvas: { w: number; h: number }, st: Style): Op[] {
  const c = new Canvas({ x: 0, y: 0, w: canvas.w, h: canvas.h }, st);
  const y = scanY(f, canvas.h);
  if (y !== null) {
    c.fillRect(0, y - 4, canvas.w, 8, st.accent, 150);
    c.line(0, y, canvas.w, y, [235, 252, 255, 255], 1.5);
  }
  if (f >= tl.c0) {
    const pts: [number, number][] = [[1084, 566], [1476, 566], [1492, 582], [1492, 816], [1476, 832], [1084, 832], [1068, 816], [1068, 582]];
    c.fillPoly(pts, [0, 10, 18, 255], 215);
    c.poly(pts, st.accent, 1.4, 110, true);
    c.fillRect(1100, 606, 360, 1.4, st.accent, 150);
    c.fillRect(1100, 783, 360, 1.4, st.accent, 150);
    c.fillRect(1084, 563, 120, 4, st.accent, 255);
    c.fillRect(1356, 831, 120, 4, st.accent, 255);
    c.text(1280, 588, 'SYSTEM CHECK', { size: 13, weight: 700, align: 'CenterCenter', color: st.accent });
    const shown = f <= tl.c0 + 4 ? 0 : Math.min(rows.length, Math.floor((f - tl.c0 - 4) / 5) + 1);
    rows.slice(0, shown).forEach((r, i) => {
      const ry = ROW_Y0 + i * ROW_STEP;
      const col = r.sev === 'alert' ? st.alert : r.sev === 'warn' ? st.warn : r.sev === 'ok' ? st.good : st.dim;
      c.text(1096, ry, r.label, { size: 13, weight: 700, align: 'LeftCenter', color: st.text });
      c.text(1392, ry, r.value, { size: 13, weight: 700, align: 'RightCenter', color: st.white });
      c.text(1466, ry, r.sev === 'ok' ? 'OK' : r.sev === 'unknown' ? '--' : r.sev === 'alert' ? 'FAIL' : 'CHECK', { size: 13, weight: 700, align: 'RightCenter', color: col });
    });
    if (f >= tl.verdict) {
      const v = bootVerdict(rows);
      c.text(1280, 808, v.text, { size: 13, weight: 700, align: 'CenterCenter', color: v.warn ? st.warn : st.good });
    }
  }
  return c.flush();
}
