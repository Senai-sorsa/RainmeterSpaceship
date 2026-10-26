import { Canvas, type Op, type Style, type Zone } from '../draw/canvas';
import { type App, type Cat, type Catalog } from './apps';

// Port of Skins/Spaceship/@Resources/Scripts/drawer.lua: the CARGO HOLD drawer (560 x 560). ALL INSTALLED APPS, then an
// accordion of every category. Opened from a side slot it shows just that folder. Not ported: the Start-menu app
// images (line icons are drawn instead), launching (an OS action, goes through the action gate), the clicks and the
// idle close timer.

export const ROWS = 19, RH = 26, TOP = 50;
export type Row = { kind: 'all' } | { kind: 'cat'; cat: Cat; jump?: boolean } | { kind: 'app'; app: App };
export type DrawerState = { open: Record<string, boolean>; focus?: string; scroll: number };

export const drawerState = (): DrawerState => ({ open: {}, scroll: 0 });

/** The rows the drawer shows: one folder with a back row, or the whole accordion with ALL first. */
export function drawerRows(cat: Catalog, st: DrawerState): Row[] {
  const rows: Row[] = [];
  const focused = st.focus ? cat.cats[st.focus] : undefined;
  if (focused) {
    for (const app of focused.apps) rows.push({ kind: 'app', app });
    rows.push({ kind: 'all' });
    return rows;
  }
  rows.push({ kind: 'cat', cat: cat.cats.all, jump: true });
  for (const id of cat.catOrder) {
    rows.push({ kind: 'cat', cat: cat.cats[id] });
    if (st.open[id]) for (const app of cat.cats[id].apps) rows.push({ kind: 'app', app });
  }
  return rows;
}

/** The scroll, held inside the rows that fit. */
export const clampScroll = (scroll: number, count: number) => Math.max(0, Math.min(scroll, count - ROWS));

export function drawerFrame(cat: Catalog, st: DrawerState, zone: Zone, style: Style): Op[] {
  const rows = drawerRows(cat, st);
  const scroll = clampScroll(st.scroll, rows.length);
  const focused = st.focus ? cat.cats[st.focus] : undefined;
  const c = new Canvas(zone, style);
  const { w, h } = zone;
  const A1 = style.accent, D = style.dim, T = style.text;
  c.chamfer(0, 0, w, h, 18, A1, 1.6, 255, 230);
  c.fillRect(0, 0, w, h, [2, 8, 14, 255], 170);
  const title = focused ? focused.name.toUpperCase() : 'CARGO HOLD';
  c.text(20, 12, title, { size: title.length > 14 ? 9.5 : 13, font: style.fontTitle, weight: 700, color: A1, clip: w - 190 });
  const count = focused ? focused.apps.length : cat.cats.all.apps.length;
  c.text(w - 50, 15, focused ? `${count} APPS` : `${count} APPS INSTALLED`, { size: 9, align: 'RightTop', color: D });
  c.line(20, 42, w - 20, 42, D, 1, 200);
  c.line(w - 34, 14, w - 18, 30, A1, 1.6);
  c.line(w - 18, 14, w - 34, 30, A1, 1.6);
  rows.slice(scroll, scroll + ROWS).forEach((row, i) => {
    const y = TOP + i * RH;
    if (row.kind === 'all') {
      c.hair(20, y + 2, w - 40, y + 2, D, 1, 80);
      c.text(54, y + 6, 'BACK TO ALL FOLDERS', { size: 9.5, weight: 700, color: A1 });
    } else if (row.kind === 'cat') {
      const open = !!st.open[row.cat.id];
      c.fillRect(20, y, w - 40, RH - 3, style.panel, 150);
      c.icon(row.cat.icon, 36, y + RH / 2 - 1, 18, A1, 1.2);
      c.poly(open ? [[w - 40, y + 8], [w - 34, y + 15], [w - 28, y + 8]] : [[w - 37, y + 6], [w - 30, y + 12], [w - 37, y + 18]], A1, 1.4);
      c.text(54, y + 3, row.cat.name, { size: 10.5, font: style.fontText, weight: 700, color: T, clip: 330 });
      c.text(w - 50, y + 4, `${row.cat.apps.length} APPS`, { size: 9, align: 'RightTop', color: D });
    } else {
      const app = row.app;
      if (app.missing || !c.appIcon(app.id, 68, y + RH / 2 - 1, 24)) c.icon(app.icon, 68, y + RH / 2 - 1, 16, app.missing ? D : A1, 1.1);
      c.text(86, y + 4, app.name, { size: 10, color: app.missing ? D : T, clip: 280 });
      c.text(w - 50, y + 5, app.missing ? 'NOT FOUND' : app.short, { size: 8.5, align: 'RightTop', color: app.missing ? style.warn : D });
      c.hair(60, y + RH - 2, w - 40, y + RH - 2, D, 1, 50);
    }
  });
  if (rows.length > ROWS) {
    const frac = scroll / (rows.length - ROWS);
    c.line(w - 12, TOP, w - 12, TOP + ROWS * RH, D, 1, 120);
    c.fillRect(w - 15, TOP + frac * (ROWS * RH - 40), 6, 40, A1, 200);
  }
  return c.flush();
}
