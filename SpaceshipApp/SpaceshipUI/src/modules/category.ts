import { arcPts, Canvas, mix, textWidth, type Op, type Style, type Zone } from '../draw/canvas';
import { type App, type Cat, type Catalog } from './apps';

// Port of Skins/Spaceship/@Resources/Scripts/category.lua: the tab rail (zone 1), the wireframe schematic of the
// selected app (zone 2) and the page dots (zone 3). The scan line is drawn once and swept by CSS (scanFrame).

export const MAXTABS = 4;

export type CatState = { first: number; sel: number };

/**
 * The page and app a panel opens on (category.lua Initialize): TopCat<panel> if it names a category, else Apps.ini Layout
 * Top<panel>, else the first; then Sel_<cat> (1-based, back to the first past the end). Returns 0-based indexes.
 */
export function skinPick(catalog: Catalog, panel: 1 | 2, state: Record<string, string>): { ci: number; ai: number } {
  const saved = state[`TopCat${panel}`] ?? '';
  const id = catalog.cats[saved] ? saved : catalog.layout[`Top${panel}`] ?? '';
  const ci = Math.max(0, catalog.catOrder.indexOf(id));
  return { ci, ai: selIndex(catalog.cats[catalog.catOrder[ci]], state) };
}

/** A category's saved pick (State.inc Sel_<cat>, 1-based) as a 0-based index; the first app when unset or out of range (slot.lua current). */
export function selIndex(cat: Cat | undefined, state: Record<string, string>): number {
  const n = cat?.apps.length ?? 0;
  const sel = cat ? Math.floor(Number(state[`Sel_${cat.id}`] ?? 1)) || 1 : 1;
  return sel >= 1 && sel <= n ? sel - 1 : 0;
}

/** The tab rail: up to four labels justified along the rail, the selected one in the accent colour. */
export function tabsFrame(cat: Cat | undefined, state: CatState, zone: Zone, st: Style): Op[] {
  const c = new Canvas(zone, st);
  const { w, h } = zone;
  c.line(10, 4, w - 4, 4, st.accent, 1.3, 220);
  c.line(4, h - 4, w - 8, h - 4, st.accent, 1.3, 220);
  c.dot(10, 4, 3, st.accent); c.dot(4, h - 4, 3, st.accent);
  c.dot(w - 4, 4, 3, st.accent); c.dot(w - 8, h - 4, 3, st.accent);
  const n = cat?.apps.length ?? 0;
  const vis = Math.min(MAXTABS, n);
  const x0 = 16, len = w - 32;
  let size = 6.2;
  const labels: string[] = [], widths: number[] = [];
  let total = 0;
  for (let t = 0; t < vis; t++) {
    labels.push(cat!.apps[state.first + t - 1]?.short ?? '');
    widths.push(textWidth(st, labels[t], size));
    total += widths[t];
  }
  const MINGAP = 12, MAXGAP = 70;
  if (vis > 1 && total + MINGAP * (vis - 1) > len) {
    const f = Math.min(1, Math.max(0.7, (len - MINGAP * (vis - 1)) / total));
    size *= f;
    total = 0;
    for (let t = 0; t < vis; t++) { widths[t] *= f; total += widths[t]; }
  }
  const gap = vis > 1 ? Math.min(MAXGAP, (len - total) / (vis - 1)) : 0;
  const span = total + gap * Math.max(0, vis - 1);
  let x = x0 + (len - span) / 2;
  for (let t = 0; t < vis; t++) {
    const i = state.first + t;
    const on = i === state.sel;
    // the pick sits on a soft lit plate with corner ticks; the others are split by faint dividers
    if (on) {
      const px = x - 6, pw = widths[t] + 12, py = h / 2 - 8, ph = 16;
      c.fillRect(px, py, pw, ph, st.accent, 34);
      c.hairPoly([[px, py + 4], [px, py], [px + 4, py]], st.accent, 230, 1.2);
      c.hairPoly([[px + pw - 4, py + ph], [px + pw, py + ph], [px + pw, py + ph - 4]], st.accent, 230, 1.2);
    }
    c.text(x, h / 2, labels[t], { size, weight: 700, align: 'LeftCenter', color: on ? st.white : [175, 190, 200, 255], alpha: on ? 255 : 210, font: st.fontNum });
    if (t < vis - 1) c.hair(x + widths[t] + gap / 2, h / 2 - 5, x + widths[t] + gap / 2, h / 2 + 5, st.accent, 1, 70);
    x += widths[t] + gap;
  }
  return c.flush();
}

/** The schematic of the selected app, or a dim category hologram with NONE INSTALLED when nothing is installed. */
export function schematicFrame(app: App | undefined, cat: Cat | undefined, running: boolean, zone: Zone, st: Style): Op[] {
  const c = new Canvas(zone, st);
  const cx = zone.w / 2, cy = zone.h / 2;
  const sz = Math.min(zone.w, zone.h) * 0.94;
  if (app) {
    const col = app.missing ? st.dim : mix(st.accent, st.white, 0.45);
    // instrument dressing, as the reference wireframes have: a faint dashed targeting ring behind the craft, rulers on
    // the left and bottom of the bracket box, and a small caption in the box's lower left
    const hb = sz * 0.5, top = cy - hb * 0.92, bot = cy + hb * 0.92, left = cx - hb, right = cx + hb;
    // hologram projection (K11): an emitter under the craft, a faint beam rising from it, interference lines in the box
    const [ar, ag, ab] = st.accent, ey = Math.min(zone.h - 3, bot + 18), ew = hb * 0.55;
    c.gradPoly([[cx - ew * 0.35, ey], [cx + ew * 0.35, ey], [right - 4, top + 6], [left + 4, top + 6]],
      { kind: 'linear', x1: 0, y1: ey, x2: 0, y2: top, stops: [[0, [ar, ag, ab, app.missing ? 14 : 36]], [0.6, [ar, ag, ab, 10]], [1, [ar, ag, ab, 0]]] });
    c.gradPoly(arcPts(cx, ey, ew, 4, 0, 360, 32), { kind: 'radial', cx, cy: ey, r: ew,
      stops: [[0, [255, 255, 255, app.missing ? 60 : 200]], [0.25, [ar, ag, ab, 150]], [1, [ar, ag, ab, 0]]] });
    c.texture([[left, top], [right, top], [right, bot], [left, bot]]);
    c.dashArc(cx, cy, sz * 0.47, 0, 360, st.accent, 0.8, 60, 5, 9, true);
    for (let i = 0; i <= 10; i++) {
      const y = top + ((bot - top) * i) / 10, x = left + ((right - left) * i) / 10, major = i % 5 === 0;
      c.hair(left - 7, y, left - (major ? 15 : 11), y, st.accent, 1, major ? 140 : 70);
      c.hair(x, bot + 7, x, bot + (major ? 15 : 11), st.accent, 1, major ? 140 : 70);
    }
    c.text(left + 16, bot - 6, `${(app.short || app.name).toUpperCase()} // SCHEMATIC`, { size: 3.6, weight: 600, align: 'LeftBottom', color: mix(st.accent, st.dim, 0.3), alpha: 210, glow: false, clip: right - left - 32 });
    c.icon(app.icon, cx, cy, sz, col, 1.6);
    c.icon(app.icon, cx + 3, cy - 3, sz * 0.97, st.white, 0.7, 60);
    const h2 = sz * 0.5;
    for (const [px, py] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) {
      const x = cx + px * h2, y = cy + py * h2 * 0.92;
      c.poly([[x - px * 10, y], [x, y], [x, y - py * 10]], st.white, 1.4, 220);
    }
    c.fillCircle(cx, cy + sz * 0.02, sz * 0.07, st.hi, running ? 150 : 70);
    c.circle(cx, cy + sz * 0.02, sz * 0.07, st.hi, 1.4, running ? 230 : 120);
    if (running) c.icon(app.icon, cx, cy, sz * 0.3, st.hi, 1.6);
  } else {
    c.icon(cat?.icon ?? 'box', cx, cy - sz * 0.06, sz * 0.62, st.dim, 1.4, 170);
    c.text(cx, cy + sz * 0.36, 'NONE INSTALLED', { size: 7.5, weight: 700, align: 'CenterCenter', color: st.warn });
  }
  return c.flush();
}

/**
 * The schematic's scan line, FULL tier only: two hairlines at the top of the zone. LeftModule sweeps them down with a CSS
 * animation instead of redrawing (category.lua moves them 1.5% of the height per 100 ms frame: one sweep per 6.7 s).
 */
export function scanFrame(zone: Zone, st: Style): Op[] | undefined {
  if (st.tier !== 0 || st.edit) return undefined; // edit mode's zone outline must not sweep with it
  const c = new Canvas(zone, st);
  const cx = zone.w / 2, h2 = Math.min(zone.w, zone.h) * 0.47;
  c.hair(cx - h2, 0, cx + h2, 0, st.accent, 1.5, 90);
  c.hair(cx - h2, -6, cx + h2, -6, st.accent, 1, 35);
  return c.flush();
}

/** The page dots: one per category (up to twelve), the current one in the accent colour. */
export function dotsFrame(count: number, index: number, zone: Zone, st: Style): Op[] {
  const c = new Canvas(zone, st);
  const n = Math.min(count, 12);
  const step = zone.w / n;
  for (let i = 1; i <= n; i++) {
    const x = step * (i - 0.5), dy = zone.h * 0.21;
    // segment pips: a short dash per page, the current one longer, brighter and lit
    if (i === index) {
      c.fillRect(x - 9, dy - 1.6, 18, 3.2, st.accent, 255);
      c.halo(x, dy, 3, st.accent, 50);
    } else c.fillRect(x - 4, dy - 1, 8, 2, [170, 185, 195, 255], 120);
  }
  return c.flush();
}
