import { heat, type Canvas, type Style } from './canvas';

// The HUD's pop-up panels (JARVIS log, CARGO drawer, boot system check): one look for all of them. Lit glass: a dark
// chamfered body, a header band lit from the top, a hairline frame with bright corner brackets, and a header rule with
// a lit start. x, y place the panel inside the canvas's zone (0, 0 for a panel that is its own zone).

const BODY: [number, number, number, number] = [2, 8, 14, 255];

/** The panel w x h at x, y in zone units; head is the header band's height. alpha scales the whole frame (0..255). */
export function popupFrame(c: Canvas, st: Style, w: number, h: number, head = 50, cut = 18, x = 0, y = 0, alpha = 255) {
  const A1 = st.accent, k = alpha / 255;
  const P = (pts: [number, number][]) => pts.map(([px, py]): [number, number] => [x + px, y + py]);
  const body = P([[cut, 0], [w, 0], [w, h - cut], [w - cut, h], [0, h], [0, cut]]), [ar, ag, ab] = A1;
  // the screens' bezel (12 #22): the panel sits in a dark recess, with a faint lip along its lower edge
  const d = 1.5, e = 3;
  if (alpha >= 250) c.bezel(P([[cut - d * 0.4, -d], [w + d, -d], [w + d, h - cut + d * 0.4], [w - cut + d * 0.4, h + d], [-d, h + d], [-d, cut - d * 0.4]]),
    P([[-e, h + e], [w - cut + e * 0.4, h + e]]));
  c.fillPoly(body, BODY, 215 * k);
  // a screen powered from its header (K2): light falls from the header down the glass, the header band is lit from
  // its top, a white specular line runs along the top edge, and the screen texture sits on the open panel
  c.gradPoly(body, { kind: 'linear', x1: 0, y1: y, x2: 0, y2: y + Math.min(h, head * 5), stops: [[0, [ar, ag, ab, Math.floor(30 * k)]], [1, [ar, ag, ab, 0]]] });
  c.gradRect(x, y, w, head, { kind: 'linear', x1: 0, y1: y, x2: 0, y2: y + head, stops: [[0, [ar, ag, ab, Math.floor(44 * k)]], [1, [ar, ag, ab, Math.floor(10 * k)]]] });
  if (alpha >= 250) c.texture(body);
  c.hair(x + cut + 4, y + 0.5, x + w - 44, y + 0.5, heat(st, A1, 1), 1, 190 * k);
  c.hot(P([[cut, 0], [w, 0], [w, h - cut], [w - cut, h], [0, h], [0, cut]]), A1, 3, 60 * k, true);
  c.chamfer(x, y, w, h, cut, A1, 1, 140 * k);
  c.poly(P([[0, cut + 28], [0, cut], [cut, 0], [cut + 52, 0]]), A1, 1.8, 255 * k);
  c.poly(P([[w - cut - 52, h], [w - cut, h], [w, h - cut], [w, h - cut - 28]]), A1, 1.8, 255 * k);
  c.poly(P([[w - 40, 0], [w, 0], [w, 26]]), A1, 1.4, 200 * k);
  c.poly(P([[0, h - 26], [0, h], [40, h]]), A1, 1.4, 200 * k);
}

/** A list row's band (K10): every other row faintly lit so the eye follows it; the active row lit from its left. */
export function popupRowBand(c: Canvas, st: Style, x: number, y: number, w: number, h: number, i: number, active = false) {
  const [r, g, b] = st.accent;
  if (active) c.gradRect(x, y, w, h, { kind: 'linear', x1: x, y1: 0, x2: x + w, y2: 0, stops: [[0, [r, g, b, 70]], [0.6, [r, g, b, 22]], [1, [r, g, b, 6]]] });
  else if (i % 2 === 1) c.fillRect(x, y, w, h, st.accent, 9);
}

/** The header rule: a dim hairline from x0 to x1 with a lit first stretch. */
export function popupRule(c: Canvas, st: Style, x0: number, x1: number, y: number) {
  c.hair(x0, y, x1, y, st.dim, 1, 160);
  c.line(x0, y, x0 + 120, y, st.accent, 1.4, 230);
}

/** A chamfered chip (button face) at x, y, w x h; filled when lit. */
export function popupChip(c: Canvas, st: Style, x: number, y: number, w: number, h: number, lit = false) {
  c.chamfer(x, y, w, h, 6, st.accent, 1, lit ? 200 : 160, lit ? 120 : 0);
}

/** The close chip with its X, over a 32 x 30 hit box at x, y. */
export function popupClose(c: Canvas, st: Style, x: number, y: number) {
  popupChip(c, st, x, y, 32, 30);
  c.line(x + 10, y + 9, x + 22, y + 21, st.accent, 1.4);
  c.line(x + 22, y + 9, x + 10, y + 21, st.accent, 1.4);
}
