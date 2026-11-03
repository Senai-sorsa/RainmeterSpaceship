import { heat, mix, type Canvas, type Style } from './canvas';
import type { RGBA } from '../lib/theme';

/** A rail gauge's track: a recessed channel (dark at the top, its lower lip catching light), a quiet rail and a tick
 *  scale under it (every 10 %, majors at 0, 50 and 100 %), the way instrument bars read in the reference cockpits.
 *  The fill and the needle are drawn by the caller over it. */
export function railTrack(c: Canvas, st: Style, x0: number, x1: number, y: number) {
  c.gradRect(x0 - 2, y - 4, x1 - x0 + 4, 8, { kind: 'linear', x1: 0, y1: y - 4, x2: 0, y2: y + 4,
    stops: [[0, [0, 0, 0, 170]], [0.55, [0, 10, 18, 110]], [1, [st.accent[0], st.accent[1], st.accent[2], 34]]] }, 1.5);
  c.hair(x0 - 1, y + 4, x1 + 1, y + 4, st.accent, 0.8, 85);
  c.line(x0, y, x1, y, mix(st.white, st.accent, 0.35), 1.1, 150);
  for (let i = 0; i <= 10; i++) {
    const x = x0 + ((x1 - x0) * i) / 10, major = i % 5 === 0;
    c.hair(x, y + 3, x, y + (major ? 8 : 5.5), st.accent, 1, major ? 170 : 90);
  }
}

/** The lit part of a rail (K10): a gradient bar in the channel, faint at the start and bright at the value, with a
 *  white-hot leading edge. Drawn under the caller's hot line, which stays the bar's core. Nothing when empty. */
export function railFill(c: Canvas, st: Style, x0: number, xv: number, y: number, col: RGBA) {
  if (xv - x0 < 0.5) return;
  c.gradRect(x0, y - 3, xv - x0, 6, { kind: 'linear', x1: x0, y1: 0, x2: xv, y2: 0,
    stops: [[0, [col[0], col[1], col[2], 30]], [0.7, [col[0], col[1], col[2], 120]], [1, [col[0], col[1], col[2], 200]]] }, 1);
  c.line(xv, y - 3, xv, y + 3, heat(st, col, 1), 1.2, 230);
}
