import { mix, type Canvas, type Style } from './canvas';

/** A rail gauge's track: a quiet rail with a tick scale under it (every 10 %, majors at 0, 50 and 100 %), the way
 *  instrument bars read in the reference cockpits. The fill and the needle are drawn by the caller over it. */
export function railTrack(c: Canvas, st: Style, x0: number, x1: number, y: number) {
  c.line(x0, y, x1, y, mix(st.white, st.accent, 0.35), 1.1, 150);
  for (let i = 0; i <= 10; i++) {
    const x = x0 + ((x1 - x0) * i) / 10, major = i % 5 === 0;
    c.hair(x, y + 3, x, y + (major ? 8 : 5.5), st.accent, 1, major ? 170 : 90);
  }
}
