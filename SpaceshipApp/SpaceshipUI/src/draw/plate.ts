import type { Pt } from '../lib/geometry';
import type { RGBA } from '../lib/theme';
import { heat, type Canvas, type Style } from './canvas';

/** A block's glass plate as a lit display (K2): light coming down from the top rule and falling off towards the base
 *  rails, the screen texture, and a brighter band just under the rule. quad runs top-left, top-right, bottom-right,
 *  bottom-left; top and bottom are the y of the rule and of the base. */
export function litPlate(c: Canvas, st: Style, quad: Pt[], top: number, bottom: number) {
  const [ar, ag, ab] = st.accent, [pr, pg, pb] = st.panel;
  c.gradPoly(quad, { kind: 'linear', x1: 0, y1: top, x2: 0, y2: bottom, stops: [[0, [ar, ag, ab, 38]], [0.3, [pr, pg, pb, 78]], [1, [pr, pg, pb, 52]]] });
  c.texture(quad);
  const [tl, tr] = quad, band = Math.min(10, (bottom - top) * 0.15);
  c.gradPoly([tl, tr, [tr[0], top + band], [tl[0], top + band]], { kind: 'linear', x1: 0, y1: top, x2: 0, y2: top + band, stops: [[0, [ar, ag, ab, 60]], [1, [ar, ag, ab, 0]]] });
}

/** A row lit from its marker side (K10): a band in the row colour fading across the row. */
export function rowBand(c: Canvas, x0: number, x1: number, y: number, h: number, col: RGBA, a = 55) {
  c.gradRect(Math.min(x0, x1), y - h / 2, Math.abs(x1 - x0), h, { kind: 'linear', x1: x0, y1: 0, x2: x1, y2: 0,
    stops: [[0, [col[0], col[1], col[2], a]], [0.5, [col[0], col[1], col[2], Math.floor(a * 0.35)]], [1, [col[0], col[1], col[2], 0]]] });
}

/** A lit key (K1 + K3 + K5): the selected tab or mode as a small plate lit from its bottom edge, a white-hot line on that
 *  edge and, on FULL, a wide soft bloom along it. */
export function litKey(c: Canvas, st: Style, x: number, y: number, w: number, h: number, col: RGBA = st.accent) {
  const [r, g, b] = col, hh = heat(st, col, 0.8);
  c.gradRect(x, y, w, h, { kind: 'linear', x1: 0, y1: y + h, x2: 0, y2: y, stops: [[0, [r, g, b, 95]], [0.5, [r, g, b, 42]], [1, [r, g, b, 14]]] });
  c.hot([[x + 2, y + h], [x + w - 2, y + h]], col, 2, 120);
  c.hair(x + 1, y + h - 0.5, x + w - 1, y + h - 0.5, hh, 1.2, 230);
}
