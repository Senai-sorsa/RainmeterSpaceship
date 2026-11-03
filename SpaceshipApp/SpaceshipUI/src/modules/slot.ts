import { Canvas, heat, mix, type Op, type Style, type Zone } from '../draw/canvas';
import { type App, type Cat } from './apps';

// Port of the 'row' style of Skins/Spaceship/@Resources/Scripts/slot.lua: one slot as a button with icon, name,
// status (or app count for a category), the OPEN or LAUNCH hint and the stepped underline. Mirror flips it for the
// right column. The other styles (compact, ship, card, rcompact) are left out on purpose: the HUD layout uses only 'row'.
// The clicks live in LeftModule.tsx and RightModule.tsx.

export type SlotStatus = { text: string; color: 'good' | 'warn' | 'white' | 'bg' };

/** slot.lua runState over the host's apps.state: 2 RUNNING (app window), 1 BACKGROUND (process only), NOT FOUND when the target is missing, else READY. */
export function slotStatus(app: App | undefined, state: number): SlotStatus {
  if (!app) return { text: 'EMPTY', color: 'white' };
  if (app.missing) return { text: 'NOT FOUND', color: 'warn' };
  return state === 2 ? { text: 'RUNNING', color: 'good' } : state === 1 ? { text: 'BACKGROUND', color: 'bg' } : { text: 'READY', color: 'white' };
}

export type SlotInput = { app?: App; cat?: Cat; state: number; mirror: boolean };

export function slotRowFrame(input: SlotInput, zone: Zone, st: Style): Op[] {
  const { app, cat, state, mirror } = input;
  const c = new Canvas(zone, st);
  const { w, h } = zone;
  const X = (f: number) => f * w, Y = (f: number) => f * h;
  const MX = (f: number) => (mirror ? (1 - f) * w : f * w);
  const isCat = cat !== undefined;
  const status = slotStatus(app, state);
  const scol = status.color === 'good' ? st.good : status.color === 'warn' ? st.warn : status.color === 'bg' ? mix(st.accent, st.dim, 0.35) : st.white;
  const icol = app && !app.missing ? st.accent : st.dim;
  const ix = MX(0.14), iy = Y(0.46);
  // glass plate under the row, bounded by the stepped underline: a faint body and a brighter band along the rule,
  // so the row reads as a lit panel instead of text floating on the hull
  const rule: [number, number][] = [[MX(0.005), Y(0.98)], [MX(0.327), Y(0.935)], [MX(0.362), Y(0.84)], [MX(0.96), Y(0.83)]];
  // the plate is a small display lit from the emblem side (K2): bright by the emblem, falling off to the far edge
  const plate: [number, number][] = [[MX(0.26), Y(0.02)], [MX(0.96), Y(0.02)], rule[3], rule[2], [MX(0.26), Y(0.86)]];
  const [ar, ag, ab] = st.accent, [pr, pg, pb] = st.panel;
  c.gradPoly(plate, { kind: 'linear', x1: MX(0.26), y1: 0, x2: MX(0.96), y2: 0,
    stops: [[0, [ar, ag, ab, 42]], [0.35, [pr, pg, pb, 80]], [1, [pr, pg, pb, 55]]] });
  c.texture(plate);
  // the lit bottom edge: light rising from the stepped rule
  c.gradPoly([rule[2], rule[3], [MX(0.96), Y(0.66)], [MX(0.362), Y(0.67)]], { kind: 'linear', x1: 0, y1: Y(0.84), x2: 0, y2: Y(0.66),
    stops: [[0, [ar, ag, ab, 46]], [1, [ar, ag, ab, 0]]] });
  c.hair(MX(0.26), Y(0.02), MX(0.5), Y(0.02), st.accent, 0.8, 90);
  c.hair(MX(0.26), Y(0.02), MX(0.26), Y(0.14), st.accent, 0.8, 90);
  if (isCat) {
    // folder emblem: a chamfered frame with corner ticks around the category icon
    const s2 = h * 0.4;
    c.chamfer(ix - s2, iy - s2, 2 * s2, 2 * s2, s2 * 0.32, st.accent, 1.4, 220, 60);
    // a lit tile: the light pools in the middle of the emblem
    c.gradPoly([[ix - s2 + s2 * 0.32, iy - s2], [ix + s2, iy - s2], [ix + s2, iy + s2 - s2 * 0.32], [ix + s2 - s2 * 0.32, iy + s2], [ix - s2, iy + s2], [ix - s2, iy - s2 + s2 * 0.32]],
      { kind: 'radial', cx: ix, cy: iy, r: s2 * 1.2, stops: [[0, [ar, ag, ab, 70]], [1, [ar, ag, ab, 8]]] });
    c.line(ix - s2 - 5, iy - s2 * 0.5, ix - s2 - 5, iy + s2 * 0.5, st.accent, 1.2, 160);
    c.line(ix + s2 + 5, iy - s2 * 0.5, ix + s2 + 5, iy + s2 * 0.5, st.accent, 1.2, 160);
    c.icon(cat.icon || 'folder', ix, iy, s2 * 1.05, heat(st, st.accent, 0.6), 1.6);
  } else {
    // app emblem: a thin ring with four ticks, the same footprint as the folder frame
    const r = h * 0.42;
    // a lit lens behind the icon
    c.gradPoly(Array.from({ length: 24 }, (_, i): [number, number] => [ix + Math.cos(i * Math.PI / 12) * r, iy + Math.sin(i * Math.PI / 12) * r]),
      { kind: 'radial', cx: ix, cy: iy, r, stops: [[0, [icol[0], icol[1], icol[2], 85]], [0.7, [icol[0], icol[1], icol[2], 30]], [1, [icol[0], icol[1], icol[2], 4]]] });
    c.circle(ix, iy, r, icol, 0.9, 120);
    for (const a of [45, 135, 225, 315]) {
      const k = Math.PI / 180 * a;
      c.hair(ix + Math.cos(k) * (r - 2), iy + Math.sin(k) * (r - 2), ix + Math.cos(k) * (r + 4), iy + Math.sin(k) * (r + 4), icol, 1, 170);
    }
    if (app && !c.appIcon(app.id, ix, iy, h * 0.56)) c.icon(app.icon, ix, iy, h * 0.5, icol, 1.7);
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
    // status lamp (K10): a small filled pill with a white-hot core, not a dot
    const lx = MX(0.30) + (mirror ? 6 : -6);
    c.halo(lx, Y(0.5), 2.2, scol, 50);
    if (status.color === 'good') c.hotDot(lx, Y(0.5), 2.4, scol, 80);
    c.fillRect(lx - 1.7, Y(0.5) - 4, 3.4, 8, scol, 230, 1.7);
    c.fillRect(lx - 0.6, Y(0.5) - 2.6, 1.2, 5.2, heat(st, scol, 1), 220, 0.6);
  }
  // the hint sits on the outer end of the underline: OPEN for a category, LAUNCH for an app
  const hx = MX(0.95), cd = mirror ? -1 : 1;
  c.text(hx + (mirror ? 18 : -18), Y(0.72), isCat ? 'OPEN' : 'LAUNCH', { size: 5, weight: 700, align: RA, color: st.accent, alpha: 220 });
  c.poly([[hx - 6 * cd, Y(0.72) - 6], [hx, Y(0.72)], [hx - 6 * cd, Y(0.72) + 6]], st.accent, 1.5);
  if (isCat) c.poly([[hx - 12 * cd, Y(0.72) - 6], [hx - 6 * cd, Y(0.72)], [hx - 12 * cd, Y(0.72) + 6]], st.accent, 1.2, 160);
  // stepped underline (reference weapon rows)
  c.poly(rule, st.accent, 1.4);
  // a faint second rule under the first and ticks at the step, the way instrument panels double their edges
  c.hairPoly(rule.map(([x, y]) => [x, y + 3.5]), st.accent, 70, 0.8);
  for (let i = 1; i <= 4; i++) c.hair(rule[2][0] + (rule[3][0] - rule[2][0]) * i * 0.18, Y(0.84) + 2, rule[2][0] + (rule[3][0] - rule[2][0]) * i * 0.18, Y(0.84) + 5, st.accent, 0.8, 90);
  return c.flush();
}
