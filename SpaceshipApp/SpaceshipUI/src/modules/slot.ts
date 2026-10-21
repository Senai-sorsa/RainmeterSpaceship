import { Canvas, type Op, type Style, type Zone } from '../draw/canvas';
import { type App, type Cat } from './apps';

// Port of the 'row' style of Skins/Spaceship/@Resources/Scripts/slot.lua: one slot as a button with icon, name,
// status (or app count for a category), the OPEN or LAUNCH hint and the stepped underline. Mirror flips it for the
// right column. The other styles (compact, ship, card, rcompact) are not ported yet. Clicks are not wired.

export type SlotStatus = { text: string; color: 'good' | 'warn' | 'white' };

/** RUNNING when the app's process is up, NOT FOUND when its target is missing, otherwise READY. Background state needs the helper, not built. */
export function slotStatus(app: App | undefined, running: boolean): SlotStatus {
  if (!app) return { text: 'EMPTY', color: 'white' };
  if (app.missing) return { text: 'NOT FOUND', color: 'warn' };
  return running ? { text: 'RUNNING', color: 'good' } : { text: 'READY', color: 'white' };
}

export type SlotInput = { app?: App; cat?: Cat; running: boolean; mirror: boolean };

export function slotRowFrame(input: SlotInput, zone: Zone, st: Style): Op[] {
  const { app, cat, running, mirror } = input;
  const c = new Canvas(zone, st);
  const { w, h } = zone;
  const X = (f: number) => f * w, Y = (f: number) => f * h;
  const MX = (f: number) => (mirror ? (1 - f) * w : f * w);
  const isCat = cat !== undefined;
  const status = slotStatus(app, running);
  const scol = status.color === 'good' ? st.good : status.color === 'warn' ? st.warn : st.white;
  const icol = app && !app.missing ? st.accent : st.dim;
  const ix = MX(0.14), iy = Y(0.46);
  if (isCat) {
    // folder emblem: a chamfered frame with corner ticks around the category icon
    const s2 = h * 0.4;
    c.chamfer(ix - s2, iy - s2, 2 * s2, 2 * s2, s2 * 0.32, st.accent, 1.4, 220, 60);
    c.line(ix - s2 - 5, iy - s2 * 0.5, ix - s2 - 5, iy + s2 * 0.5, st.accent, 1.2, 160);
    c.line(ix + s2 + 5, iy - s2 * 0.5, ix + s2 + 5, iy + s2 * 0.5, st.accent, 1.2, 160);
    c.icon(cat.icon || 'folder', ix, iy, s2 * 1.05, st.accent, 1.6);
  } else if (app) {
    c.icon(app.icon, ix, iy, h * 0.6, icol, 1.7);
  }
  const LA = mirror ? 'RightCenter' : 'LeftCenter', RA = mirror ? 'LeftCenter' : 'RightCenter';
  const title = isCat ? cat.name : app ? app.name : 'UNASSIGNED';
  c.text(MX(0.30), Y(0.24), title, { size: 8, weight: 700, align: LA, color: st.white, clip: X(0.62) });
  if (isCat) {
    const n = cat.apps.length;
    const last = app ? `   LAST  ${app.short}` : '';
    c.text(MX(0.30), Y(0.5), n === 0 ? 'NONE INSTALLED' : `${n} APPS${last}`, { size: 5.6, weight: 700, align: LA,
      color: n === 0 ? st.warn : [160, 178, 190, 255], clip: X(0.62) });
  } else {
    c.text(MX(0.30), Y(0.5), status.text, { size: 5.6, weight: 700, align: LA, color: scol, clip: X(0.62) });
    c.dot(MX(0.30) + (mirror ? 6 : -6), Y(0.5), 2.6, scol);
  }
  // the hint sits on the outer end of the underline: OPEN for a category, LAUNCH for an app
  const hx = MX(0.95), cd = mirror ? -1 : 1;
  c.text(hx + (mirror ? 18 : -18), Y(0.72), isCat ? 'OPEN' : 'LAUNCH', { size: 5, weight: 700, align: RA, color: st.accent, alpha: 220 });
  c.poly([[hx - 6 * cd, Y(0.72) - 6], [hx, Y(0.72)], [hx - 6 * cd, Y(0.72) + 6]], st.accent, 1.5);
  if (isCat) c.poly([[hx - 12 * cd, Y(0.72) - 6], [hx - 6 * cd, Y(0.72)], [hx - 12 * cd, Y(0.72) + 6]], st.accent, 1.2, 160);
  // stepped underline (reference weapon rows)
  c.poly([[MX(0.005), Y(0.98)], [MX(0.327), Y(0.935)], [MX(0.362), Y(0.84)], [MX(0.96), Y(0.83)]], st.accent, 1.4);
  return c.flush();
}
