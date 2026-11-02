import type { Canvas, Style } from './canvas';

// The HUD's pop-up panels (JARVIS log, CARGO drawer): one look for all of them. Lit glass: a dark chamfered body, a
// header band lit from the top, a hairline frame with bright corner brackets, and a header rule with a lit start.

const BODY: [number, number, number, number] = [2, 8, 14, 255];

/** The panel w x h in zone units; head is the header band's height (its rule sits at head). */
export function popupFrame(c: Canvas, st: Style, w: number, h: number, head = 50, cut = 18) {
  const A1 = st.accent;
  c.fillPoly([[cut, 0], [w, 0], [w, h - cut], [w - cut, h], [0, h], [0, cut]], BODY, 215);
  c.fillRect(0, 0, w, head, A1, 16);
  c.fillRect(0, 0, w, 3, A1, 30);
  c.chamfer(0, 0, w, h, cut, A1, 1, 140);
  c.poly([[0, cut + 28], [0, cut], [cut, 0], [cut + 52, 0]], A1, 1.8);
  c.poly([[w - cut - 52, h], [w - cut, h], [w, h - cut], [w, h - cut - 28]], A1, 1.8);
  c.poly([[w - 40, 0], [w, 0], [w, 26]], A1, 1.4, 200);
  c.poly([[0, h - 26], [0, h], [40, h]], A1, 1.4, 200);
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
