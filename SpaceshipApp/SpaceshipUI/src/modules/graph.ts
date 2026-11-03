import { Canvas, heat, mix, type Op, type Style, type Zone, ramp } from '../draw/canvas';
import { type Readings } from './readings';
import { normalise, nextSource, SOURCES } from './sources';

// Port of Skins/Spaceship/@Resources/Scripts/graph.lua: the history instrument in the top console. Mode 'fixed' always shows
// one source; 'select' shows a source the user picks. OnClick, OnRightClick and OnScroll live in TopModule.tsx: they step
// the source with selectSource() and save it (GraphA_Source / GraphB_Source).

export type GraphMode = 'fixed' | 'select';
export type GraphState = { src: string; hist: number[] };
export type GraphFrame = { ops: Op[]; value: number };

const N = 48;
const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

/** A new graph on a source. An unknown id falls back to cpu, as Initialize does. */
export function graphState(src: string): GraphState {
  return { src: SOURCES[src] ? src : 'cpu', hist: [] };
}

/** setSource with the step: the next or previous source, with an empty history. */
export function selectSource(state: GraphState, dir: number): GraphState {
  return graphState(nextSource(state.src, dir));
}

export function graphFrame(state: GraphState, r: Readings, zone: Zone, st: Style, mode: GraphMode): GraphFrame {
  const def = SOURCES[state.src];
  const { value: v, text: txt } = def.get(r);
  if (v !== undefined) {
    state.hist.push(v);
    if (state.hist.length > N) state.hist.shift();
  }
  const norm = normalise(def, state.hist);
  const cur = norm.length ? norm[norm.length - 1] : 0;
  const col = ramp(st, cur);
  const c = new Canvas(zone, st);
  const live = v !== undefined;
  // a small lit display (K2), backlit from the bottom; a busier source lights it a little more
  c.screen(1, 2, zone.w - 2, zone.h - 4, { from: 'bottom', cut: 6, lit: live ? 0.35 + 0.3 * cur : 0.2, col: cur >= 0.7 ? col : st.accent });
  // instrument plate: label top-left, a hero readout bottom-left, the history on the right over a faint grid
  const gx0 = zone.w * 0.4, gx1 = zone.w - 8, gy0 = 12, gy1 = zone.h - 9, gh = gy1 - gy0;
  for (let i = 0; i <= 4; i++) {
    const y = gy1 - (gh * i) / 4;
    c.hair(4, y, i % 2 === 0 ? 11 : 8, y, st.dim, 1, i % 2 === 0 ? 150 : 90);
    if (i > 0) c.hair(gx0, y, gx1, y, st.dim, 0.6, i === 4 ? 40 : 28);
  }
  c.hair(gx0, gy1, gx1, gy1, st.dim, 0.8, 110);
  for (let i = 0; i <= 6; i++) c.hair(gx0 + ((gx1 - gx0) * i) / 6, gy1, gx0 + ((gx1 - gx0) * i) / 6, gy1 + (i % 3 === 0 ? 3 : 1.6), st.dim, 0.8, 120);
  if (norm.length >= 2) {
    const pad = [...new Array<number>(N - norm.length).fill(0), ...norm];
    const pts = pad.map((x, i): [number, number] => [gx0 + (i * (gx1 - gx0)) / (pad.length - 1), gy1 - clamp01(x) * gh]);
    // the area is light falling off below the line (K1): bright at the top of the scale, gone at the floor
    c.gradPoly([[gx0, gy1], ...pts, [gx1, gy1]], { kind: 'linear', x1: 0, y1: gy0, x2: 0, y2: gy1,
      stops: [[0, [col[0], col[1], col[2], 120]], [0.55, [col[0], col[1], col[2], 45]], [1, [col[0], col[1], col[2], 6]]] });
    c.hairPoly(pts, col, 210, 1.2);
    const [lx, ly] = pts[pts.length - 1];
    c.hair(lx, ly, lx, gy1, col, 0.6, 90);
    // the newest sample burns white-hot (K3)
    c.dot(lx, ly, 2, heat(st, col, 1), 240);
  }
  // label: one small line, dim, so the number leads
  c.text(14, 8, def.label, { size: 4.4, weight: 600, align: 'LeftTop', color: mix(st.accent, st.white, 0.15), alpha: 200, glow: false });
  // hero readout: the number large and white (ramp colour when high), its unit small after it
  const t = txt ?? '--';
  const m = /^([-+]?[\d.,]+)\s*(.*)$/.exec(t);
  const [num, unit] = m ? [m[1], m[2]] : [t, ''];
  const hero = live ? (cur >= 0.7 ? col : heat(st, st.accent, 1)) : st.dim, hs = 15;
  c.text(13, zone.h - 7, num, { size: hs, weight: 700, align: 'LeftBottom', color: hero });
  if (unit) c.text(15 + num.length * hs * st.textLarge * (4 / 3) * 0.47, zone.h - 10, unit, { size: 4.2, weight: 600, align: 'LeftBottom', color: st.dim, alpha: 230, glow: false });
  if (mode === 'select') {
    // the two chevrons say "click to change the source"; top right, clear of the readout
    const x = zone.w - 22, y = 10;
    c.poly([[x, y - 3], [x + 4, y], [x, y + 3]], st.accent, 1.1, 200);
    c.poly([[x + 6, y - 3], [x + 10, y], [x + 6, y + 3]], st.accent, 1.1, 200);
  }
  return { ops: c.flush(), value: v ?? 0 };
}
