import { Canvas, mix, textWidth, type Op, type Style, type Zone } from '../draw/canvas';
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
    c.text(x, h / 2, labels[t], { size, weight: 700, align: 'LeftCenter', color: on ? st.accent : [175, 190, 200, 255], alpha: on ? 255 : 210, font: st.fontNum });
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
    if (i === index) c.dot(x, dy, 4, st.accent);
    else c.dot(x, dy, 3, [170, 185, 195, 255], 150);
  }
  return c.flush();
}
