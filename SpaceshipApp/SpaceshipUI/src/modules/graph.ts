import { Canvas, type Op, type Style, type Zone, ramp } from '../draw/canvas';
import { type Readings } from './readings';
import { normalise, nextSource, SOURCES } from './sources';

// Port of Skins/Spaceship/@Resources/Scripts/graph.lua: the history instrument in the top console. Mode 'fixed' always shows
// one source; 'select' shows a source the user picks. OnClick, OnRightClick and OnScroll are not ported: they changed the
// source and saved it through a Rainmeter bang. selectSource() makes the change without the save.

export type GraphMode = 'fixed' | 'select';
export type GraphState = { src: string; hist: number[] };
export type GraphFrame = { ops: Op[]; value: number };

const N = 48;
const GHOST: Style['white'] = [40, 82, 150, 255];
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
  const gx0 = 14, gx1 = zone.w - 8, gy0 = 8, gy1 = zone.h - 8, gh = gy1 - gy0;
  // faint scale ticks on the left edge: major at 0, 50 and 100 %
  for (let i = 0; i <= 4; i++) {
    const y = gy1 - (gh * i) / 4;
    c.hair(4, y, i % 2 === 0 ? 11 : 8, y, st.dim, 1, i % 2 === 0 ? 150 : 90);
  }
  // history: faint area and a thin line behind the label, padded on the left until the buffer is full
  if (norm.length >= 2) {
    const pad = [...new Array<number>(N - norm.length).fill(0), ...norm];
    const pts = pad.map((x, i): [number, number] => [gx0 + (i * (gx1 - gx0)) / (pad.length - 1), gy1 - clamp01(x) * gh]);
    c.fillPoly([[gx0, gy1], ...pts, [gx1, gy1]], col, 22);
    c.hairPoly(pts, col, 150, 1.3);
    const [lx, ly] = pts[pts.length - 1];
    c.dot(lx, ly, 2.2, col, 230);
  }
  // ghosted two-line label, centred on the plate
  const m = /^(\S+)\s+(.+)$/.exec(def.label);
  const [w1, w2] = m ? [m[1], m[2]] : [def.label, ''];
  const ghost = { size: 10, weight: 700, align: 'CenterCenter', color: GHOST, alpha: 235, glow: false };
  c.text(zone.w / 2, zone.h * 0.3, w1, ghost);
  c.text(zone.w / 2, zone.h * 0.62, w2, ghost);
  // live readout bottom-right: white when there is a reading, dim when not
  c.text(zone.w - 6, zone.h - 6, txt ?? '--', { size: 4.6, weight: 700, align: 'RightBottom', font: st.fontNum, color: v !== undefined ? st.white : st.dim });
  if (mode === 'select') {
    c.poly([[8, zone.h - 9], [12, zone.h - 6], [8, zone.h - 3]], st.accent, 1.1, 200);
    c.poly([[14, zone.h - 9], [18, zone.h - 6], [14, zone.h - 3]], st.accent, 1.1, 200);
  }
  return { ops: c.flush(), value: v ?? 0 };
}
