import { Canvas, type Op, type Style, type Zone } from '../draw/canvas';

// Port of Skins/Spaceship/@Resources/Scripts/hud.lua: the flight HUD. Left ladder = S&P 500 change today, right ladder =
// GPU (clock in GHz when the host gives it, else load %), the bracket with the CPU-load pointer, and the diamond pipper.
// The S&P 500 comes from the host's spx.update (Yahoo ^GSPC, host/statusFeed.ts) and shows -- until the first good reply.
// Values ease toward their targets each frame (the caller passes the ease factor; 0.12 on the full tier, 1 otherwise).
// Clicks are not wired.
// shortcut: text widths are estimated from the character count, not measured.

const SXR = 2560 / 1260, SYR = 1600 / 709;
const X = (rx: number) => (rx - 484) * SXR; // zone centred on the screen axis (x = 630)
const Y = (ry: number) => (ry - 256) * SYR;
/** hud.lua H.hit boxes: 1 the GPU ladder (Task Manager), 2 the S&P box (its quote page). */
export const HUD_HITS = { gpu: { x: X(600), y: Y(290), w: X(660) - X(600), h: Y(332) - Y(290) }, spx: { x: X(486), y: Y(258), w: X(540) - X(486), h: Y(395) - Y(258) } };

export type HudState = { frame: number; cpu?: number; gpu?: number; load?: number; spx?: number };
export type HudInput = {
  cpuBaseMHz: number; cpuPerf: number; // CpuBaseMHz setting and the host's CPU performance percent
  gpuClockMHz?: number; gpuLoad?: number; // gpu clock when reported, else load
  load?: number; // CPU load percent
  spxPrice?: number; spxPrev?: number; spxOpen?: boolean;
};

export const hudState = (): HudState => ({ frame: 0 });

const ease = (old: number | undefined, nw: number, k: number) => (old === undefined ? nw : old + (nw - old) * k);
const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));

type Fmt = (v: number) => string;
const sign1: Fmt = (v) => `${v >= 0 ? '+' : ''}${v.toFixed(1)}`;

/** One ladder: a dashed rail that scrolls with the value, a centre tick, and the labels above, at and below the centre. */
function ladder(c: Canvas, x: number, side: -1 | 1, v: number, step: number, ppu: number, fmt: Fmt, centre: string, st: Style,
  sz: { big: number; mid: number; font?: string }, signed: boolean) {
  const A1 = st.accent;
  const top = Y(260), bot = Y(362), mid = Y(311);
  const spacing = 7;
  for (let y = top + ((v * ppu) % spacing); y <= bot; y += spacing) c.hair(x - 3, y, x + 3, y, A1, 1.4, 200);
  c.line(side < 0 ? x - 26 : x, mid, side < 0 ? x : x + 26, mid, A1, 2.2);
  const lx = side < 0 ? X(510) : X(750);
  const al = side < 0 ? 'RightCenter' : 'LeftCenter';
  c.text(lx, Y(268), fmt(v + step), { size: sz.big, weight: 700, align: al, color: A1 });
  c.text(side < 0 ? X(512) : X(748), mid, centre, { size: sz.mid, weight: 700, align: al, color: A1, font: sz.font });
  c.text(lx, Y(353), fmt(signed ? v - step : Math.max(0, v - step)), { size: sz.big, weight: 700, align: al, color: A1 });
  c.line(x - 4, Y(268), x + 4, Y(268), A1, 1.4);
  c.line(x - 4, Y(353), x + 4, Y(353), A1, 1.4);
}

export function hudFrame(state: HudState, input: HudInput, zone: Zone, st: Style, rate = 0.12): Op[] {
  state.frame += 1;
  const c = new Canvas(zone, st);
  const A1 = st.accent;
  const k = rate;
  const mhz = input.cpuBaseMHz * input.cpuPerf / 100;
  state.cpu = ease(state.cpu, mhz / 1000, k);
  let gfmt: Fmt, gstep: number, gppu: number, gtarget: number;
  if (input.gpuClockMHz !== undefined) {
    gfmt = (v) => v.toFixed(2); gstep = 0.25; gppu = 120; gtarget = input.gpuClockMHz / 1000;
  } else {
    gfmt = (v) => v.toFixed(0); gstep = 10; gppu = 3; gtarget = clamp(input.gpuLoad ?? 0, 0, 100);
  }
  state.gpu = ease(state.gpu, gtarget, k);
  state.load = ease(state.load, input.load ?? 0, k);
  const pct = input.spxPrice !== undefined && input.spxPrev !== undefined && input.spxPrev > 0
    ? ((input.spxPrice - input.spxPrev) / input.spxPrev) * 100 : undefined;
  state.spx = ease(state.spx, pct ?? 0, k);
  const spxSz = { big: 6.4, mid: 7.2, font: st.fontNum };
  const spxCentre = pct === undefined ? '--' : `${state.spx.toFixed(2).replace(/^(?!-)/, '+')}%`;
  ladder(c, X(527), -1, state.spx, 0.5, 60, sign1, spxCentre, st, spxSz, true);
  ladder(c, X(733), 1, state.gpu, gstep, gppu, gfmt, gfmt(state.gpu), st, { big: 7.6, mid: 12 }, false);
  // bracket with the CPU-load pointer
  const by0 = Y(311), by1 = Y(362);
  c.poly([[X(537.5), by0], [X(533.5), by0], [X(533.5), by1], [X(537.5), by1]], A1, 1.6);
  const py = by1 - (by1 - by0) * clamp(state.load / 100, 0, 1);
  c.poly([[X(542), py - 5], [X(537.5), py], [X(542), py + 5]], A1, 1.6, 255, true);
  c.text(X(544), py, state.load.toFixed(0), { size: 7.5, weight: 700, align: 'LeftCenter', color: A1 });
  // faint horizon and the diamond pipper with its corner ticks
  const cx = X(630), cy = Y(311);
  c.hair(cx, Y(268), cx, Y(296), A1, 1, 70);
  c.hair(cx, Y(326), cx, Y(354), A1, 1, 70);
  c.hair(X(567), cy, X(612), cy, A1, 1, 70);
  c.hair(X(648), cy, X(692), cy, A1, 1, 70);
  const d = 17 * (1 + Math.sin(state.frame * 0.1) * 0.04);
  c.poly([[cx, cy - d], [cx + d, cy], [cx, cy + d], [cx - d, cy]], A1, 2, 255, true);
  for (const [px, py2] of [[0, -1], [1, 0], [0, 1], [-1, 0]]) {
    c.line(cx + px * (d + 2), cy + py2 * (d + 2), cx + px * (d + 9), cy + py2 * (d + 9), A1, 1.6);
  }
  // readout
  c.text(X(525), Y(381), 'SPX', { size: 7, weight: 700, align: 'RightCenter', color: A1 });
  if (pct !== undefined && !input.spxOpen) c.text(X(525), Y(371), 'CLOSED', { size: 4.6, weight: 700, align: 'RightCenter', color: st.dim, glow: false });
  c.text(X(525), Y(391), `THR ${state.load.toFixed(0)}`, { size: 7, weight: 700, align: 'RightCenter', color: A1 });
  return c.flush();
}
