import { Canvas, mix, type Op, type Style, type Zone } from '../draw/canvas';
import type { Pt } from '../lib/geometry';
import { parseColor, type RGBA } from '../lib/theme';

// Port of Skins/Spaceship/@Resources/Scripts/jarvis.lua (the centre core) and jarvislog.lua (the log window).
// Ported: the 3D plexus shell, the two tilted orbit rings with satellites, the HUD dial, the side data bars, the
// status label, and the conversation log. Not ported: the plasma orb and its voice echo (the 210-frame sprite is not
// in the app's assets), the Python service, the clicks and keys, the auto-start and the MUTED file write. The text is copied as written in the Lua and is queued for the
// Phase 10 hand review.
// shortcut: no orb sprite, levels are not smoothed, and bars are not smoothed, upgrade: add the Images\Jarvis frames and a per-key smoother.

/** Same centre as the old globe, in the Lua's zone units (jarvis.lua line 16). */
export const CX = ((746 - 514) / 2) * (2560 / 1260);
export const CY = (491 - 407) * (1600 / 709);
const RP = 168;             // plexus shell radius
const OCC = 330 * 0.4;      // anything behind the orb, inside this radius, is hidden by it
const STALE_S = 8;          // a feed older than this is offline

export type JarvisState = 'idle' | 'listening' | 'thinking' | 'speaking' | 'offline';
export const LABEL: Record<JarvisState, string> = { idle: 'STANDBY', listening: 'LISTENING', thinking: 'THINKING', speaking: 'SPEAKING', offline: 'OFFLINE' };
const SPIN: Record<string, number> = { idle: 1, listening: 0.7, thinking: 3, speaking: 1.4, offline: 0.3 };

export type Feed = { state: string; level: number; note?: string }; // note: the host's caption (STARTING, NO PYTHON...) in place of the state's

/** Data\jarvis.txt lines (T, STATE, LEVEL). No file, or one older than 8 s, means offline. */
export function feedFrom(text: string | undefined, nowS: number): Feed {
  if (text === undefined) return { state: 'offline', level: 0 };
  let state = 'idle', level = 0, t = 0;
  for (const line of text.split('\n')) {
    const m = /^([A-Z]+) ?(.*)$/.exec(line);
    if (!m) continue;
    if (m[1] === 'T') t = Number(m[2]) || 0;
    else if (m[1] === 'STATE') state = m[2];
    else if (m[1] === 'LEVEL') level = Number(m[2]) || 0;
  }
  if (nowS - t > STALE_S) return { state: 'offline', level: 0 };
  return { state, level };
}

type P3 = [number, number, number];

/** Points spread evenly on a sphere (slightly jittered, the same seed as the Lua), each linked to its 3 nearest. */
export function plexus(n = 56) {
  const nodes: P3[] = [];
  let seed = 7;
  const rnd = () => {
    seed = (seed * 1103515245 + 12345) % 2147483648;
    return seed / 2147483648;
  };
  for (let i = 0; i < n; i++) {
    const y = 1 - (2 * (i + 0.5)) / n;
    const r = Math.sqrt(1 - y * y);
    const th = Math.PI * (3 - Math.sqrt(5)) * i;
    const j = 0.9 + 0.2 * rnd();
    nodes.push([Math.cos(th) * r * j, y * j, Math.sin(th) * r * j]);
  }
  const edges: [number, number][] = [];
  const seen = new Set<string>();
  nodes.forEach((a, i) => {
    const near = nodes
      .map((b, k) => ({ k, d: (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2 }))
      .filter((p) => p.k !== i)
      .sort((p, q) => p.d - q.d);
    for (let m = 0; m < 3; m++) {
      const k = near[m].k;
      const key = `${Math.min(i, k)}:${Math.max(i, k)}`;
      if (!seen.has(key)) {
        seen.add(key);
        edges.push([i, k]);
      }
    }
  });
  return { nodes, edges };
}
const PLEXUS = plexus();

/** 3D to screen: yaw about Y, then tilt about X, light perspective. Returns x, y and depth (-1 back .. 1 front). */
function proj(p: P3, r: number, yw: number, tilt: number, cx: number, cy: number): [number, number, number] {
  let [x, y, z] = p;
  const cyw = Math.cos(yw), syw = Math.sin(yw);
  [x, z] = [x * cyw + z * syw, -x * syw + z * cyw];
  const ct = Math.cos(tilt), st = Math.sin(tilt);
  [y, z] = [y * ct - z * st, y * st + z * ct];
  const f = 1 / (1 - z * 0.18);
  return [cx + x * r * f, cy - y * r * f, z];
}

const hiddenBy = (x: number, y: number, z: number, cx: number, cy: number) =>
  z < 0 && (x - cx) ** 2 + (y - cy) ** 2 < OCC * OCC;

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));

/** JarvisColorIdle / Listen / Speak, empty or unreadable = the theme default (jarvis.lua colorSetting). */
export type JarvisColors = { idle?: string; listen?: string; speak?: string };

/** The state colour, as jarvis.lua lines 312-316: offline is the idle colour dimmed. */
export function stateColor(state: string, style: Style, cols: JarvisColors = {}): RGBA {
  const idle = parseColor(cols.idle, style.accent);
  if (state === 'listening') return parseColor(cols.listen, mix(style.accent, [0, 70, 210, 255], 0.55));
  if (state === 'speaking') return parseColor(cols.speak, idle);
  return state === 'offline' ? mix(style.dim, idle, 0.45) : idle;
}

/**
 * One frame of the core, drawn on a canvas-sized zone with the centre at (cx, cy). `frame` is the update count.
 * Layers back to front: plexus shell, orbit rings, dial, thinking sweep, side bars, name and status label.
 * `name` is the dotted assistant label (none when empty); `lb` the label corner in the zone's units.
 */
export function jarvisFrame(frame: number, feed: Feed, style: Style, zone: Zone, cx: number, cy: number, name = '', lb?: [number, number], cols: JarvisColors = {}): Op[] {
  const c = new Canvas(zone, style);
  const state = feed.state in LABEL ? (feed.state as JarvisState) : 'idle';
  const dim = state === 'offline';
  const lvl = clamp(feed.level, 0, 1);
  const A1 = style.accent, W = style.white, D = style.dim;
  const col = stateColor(state, style, cols);
  const rc = dim ? D : col;
  const hot = mix(rc, W, 0.45);
  const spin = state === 'speaking' ? 1.4 + 2 * lvl : SPIN[state] ?? 1;
  const yaw = (frame * 0.006 * spin) % (2 * Math.PI);
  const rot1 = (frame * 0.5 * spin) % 360, rot2 = (frame * 0.8 * spin) % 360, rot3 = (-frame * 0.25 * spin) % 360;

  // 3D plexus shell
  const r = RP * (1 + 0.07 * lvl);
  const tilt = 0.38 + 0.08 * Math.sin(frame * 0.006);
  const ea = dim ? 0.6 : 1 + 0.8 * lvl;
  const P = PLEXUS.nodes.map((n) => {
    const [x, y, z] = proj(n, r, yaw, tilt, cx, cy);
    return { x, y, z, hid: hiddenBy(x, y, z, cx, cy) };
  });
  for (const [i, k] of PLEXUS.edges) {
    const a = P[i], b = P[k];
    if (a.hid || b.hid) continue;
    const z = (a.z + b.z) / 2;
    let alpha = z >= 0 ? 70 + 110 * z : 22 + 30 * (1 + z);
    const mx = (a.x + b.x) / 2 - cx, my = (a.y + b.y) / 2 - cy;
    if (mx * mx + my * my < OCC * OCC * 0.8) alpha *= 0.4;
    c.hair(a.x, a.y, b.x, b.y, z >= 0 ? hot : rc, z >= 0 ? 1.1 : 0.8, clamp(alpha * ea, 0, 235));
  }
  for (const p of P) {
    if (p.hid || p.z <= -0.35) continue;
    c.dot(p.x, p.y, p.z > 0.3 ? 1.5 + 1.2 * lvl : 1, p.z > 0.3 ? W : hot, clamp((120 + 120 * p.z) * ea, 30, 255));
  }

  // two tilted orbit rings with satellites; the part behind the core is hidden, the front part glows
  const rings = [
    { R: 200, inc: (13 * Math.PI) / 180, ph: ((rot1 * 0.9) * Math.PI) / 180, roll: (16 * Math.PI) / 180 },
    { R: 184, inc: (24 * Math.PI) / 180, ph: ((-rot2 * 0.7) * Math.PI) / 180, roll: (-24 * Math.PI) / 180 },
  ];
  for (const R of rings) {
    const rr = R.R * (1 + 0.04 * lvl);
    const toScreen = (x: number, y: number, z: number) => {
      const xr = x * Math.cos(R.roll) - y * Math.sin(R.roll), yr = x * Math.sin(R.roll) + y * Math.cos(R.roll);
      return proj([xr, yr, z], rr, 0, 0, cx, cy);
    };
    const pts: { x: number; y: number; front: boolean | null }[] = [];
    for (let s = 0; s <= 64; s++) {
      const a = (s / 64) * 2 * Math.PI;
      const [sx, sy, sz] = toScreen(Math.cos(a), Math.sin(a) * Math.sin(R.inc), Math.sin(a) * Math.cos(R.inc));
      pts.push({ x: sx, y: sy, front: hiddenBy(sx, sy, sz, cx, cy) ? null : sz >= 0 });
    }
    // runs of one depth; each run starts on the last point of the one before, so the pieces join
    const runs: { pts: Pt[]; front: boolean | null }[] = [];
    let cur: Pt[] = [], curFront: boolean | null | undefined;
    for (const q of pts) {
      if (q.front !== curFront || cur.length === 0) {
        if (cur.length > 1) runs.push({ pts: cur, front: curFront ?? null });
        cur = cur.length ? [cur[cur.length - 1]] : [];
        curFront = q.front;
      }
      cur.push([q.x, q.y]);
    }
    if (cur.length > 1) runs.push({ pts: cur, front: curFront ?? null });
    for (const run of runs) {
      if (run.front === true) c.poly(run.pts, hot, 1.4, dim ? 130 : 210);
      else if (run.front === false) c.hairPoly(run.pts, rc, dim ? 45 : 70, 1);
    }
    for (const k of [0, 1]) {
      const a = R.ph + k * Math.PI;
      const [sx, sy, sz] = toScreen(Math.cos(a), Math.sin(a) * Math.sin(R.inc), Math.sin(a) * Math.cos(R.inc));
      if (!hiddenBy(sx, sy, sz, cx, cy)) c.dot(sx, sy, sz >= 0 ? 3 : 1.8, sz >= 0 ? W : rc, sz >= 0 ? 255 : 110);
    }
  }

  // HUD dial: outer hairline, segmented arcs, tick ring, dashed ring
  c.circle(cx, cy, 203, rc, 1, dim ? 70 : 90);
  for (let q = 0; q < 3; q++) c.arc(cx, cy, 196, q * 120 + rot1, q * 120 + rot1 + 52, rc, 3.6 + 1.5 * lvl, dim ? 160 : 230);
  for (let q = 0; q < 6; q++) c.arc(cx, cy, 196, q * 60 + rot1 + 70, q * 60 + rot1 + 74, hot, 3.6, dim ? 130 : 200);
  const seg = (189 * 2 * Math.PI) / 120;
  c.dashArc(cx, cy, 189, rot3, rot3 + 360, rc, 4, dim ? 75 : 110, seg * 0.12, seg * 0.88, true);
  if (state === 'thinking') c.arc(cx, cy, 196, (frame * 9) % 360, ((frame * 9) % 360) + 80, W, 3, 250);

  // side data bars, heights from his voice with a little life of their own (not smoothed here)
  const nb = 11;
  for (let side = 0; side < 2; side++) {
    for (let i = 1; i <= nb; i++) {
      const key = side * nb + i;
      const a = ((side === 0 ? 180 : 0) + (i - (nb + 1) / 2) * 5.2) * (Math.PI / 180);
      const wob = 0.5 + 0.5 * Math.sin(frame * 0.11 + key * 1.7);
      const h = 3 + (dim ? 0 : 4 * wob + 22 * lvl * (0.5 + 0.5 * Math.sin(frame * 0.35 + key * 2.3)));
      const r0 = 212;
      c.hair(cx + r0 * Math.cos(a), cy + r0 * Math.sin(a), cx + (r0 + h) * Math.cos(a), cy + (r0 + h) * Math.sin(a),
        i === (nb + 1) / 2 ? W : rc, 2.6, dim ? 110 : 200);
    }
  }

  // name and status label at the bottom left of the hologram's zone (lb is that corner; the zone's own corner without it)
  const [lx, ly] = lb ?? [0, zone.h];
  const labelCol = state === 'listening' ? mix(col, W, 0.35) : state === 'offline' ? mix(col, W, 0.2) : W;
  if (name) c.text(lx + 8, ly - 26, name, { size: 5, weight: 700, align: 'LeftBottom', color: mix(A1, W, 0.3) });
  c.text(lx + 8, ly - 12, feed.note || LABEL[state], { size: 4.4, weight: 700, align: 'LeftBottom', color: labelCol, glow: false });
  return c.flush();
}

// ---- conversation log (jarvislog.lua) ----

export type LogLine = { who: string; text: string; first: boolean };

/** Monospace-style wrap by character count: long words are cut, short ones are joined up to the width. */
export function wrap(text: string, width: number): string[] {
  const out: string[] = [];
  let line = '';
  for (let word of text.match(/\S+/g) ?? []) {
    while (word.length > width) {
      if (line !== '') {
        out.push(line);
        line = '';
      }
      out.push(word.slice(0, width));
      word = word.slice(width);
    }
    if (line === '') line = word;
    else if (line.length + 1 + word.length <= width) line += ' ' + word;
    else {
      out.push(line);
      line = word;
    }
  }
  if (line !== '') out.push(line);
  if (out.length === 0) out.push('');
  return out;
}

/** Data\jarvis_log.txt lines (U|unix|text, J|unix|text, S|unix|text), then the reply being written (Data\jarvis_live.txt). */
export function logLines(log: string, live: string, width: number): LogLine[] {
  const lines: LogLine[] = [];
  const add = (who: string, text: string) => {
    wrap(text, width).forEach((l, i) => lines.push({ who, text: l, first: i === 0 }));
    lines.push({ who: '', text: '', first: false });
  };
  for (const m of log.matchAll(/([UJS])\|(\d+)\|([^\n]*)/g)) add(m[1], m[3]);
  const lm = /([UJ])\|(\d+)\|([^\n]*)/.exec(live);
  if (lm && lm[3] !== '') add('L', lm[3] + ' _');
  return lines;
}

const LOG_ROWS = 20, LOG_RH = 26, LOG_TOP = 66, LX = 40, TX = 150;

/** The log window, newest at the bottom. Scroll and the mic box are not ported; the window shows the last rows. */
/** scroll: lines scrolled up from the bottom; clamped here as jarvislog.lua does. */
export function logScrollMax(log: string, live: string, w: number, style: Style): number {
  return Math.max(0, logLines(log, live, logWidth(w, style)).length - LOG_ROWS);
}

const logWidth = (w: number, style: Style) => Math.max(20, Math.floor((w - TX - 90) / (8.6 * style.textSmall * (96 / 72) * 0.6)));

export function jarvisLogFrame(log: string, live: string, muted: boolean, assistant: string, style: Style, zone: Zone, scroll = 0): Op[] {
  const c = new Canvas(zone, style);
  const { w, h } = zone;
  const A1 = style.accent, D = style.dim, T = style.text, W = style.white;
  const lines = logLines(log, live, logWidth(w, style));
  const n = lines.length, maxScroll = Math.max(0, n - LOG_ROWS);
  const sc = Math.min(Math.max(scroll, 0), maxScroll);
  c.chamfer(0, 0, w, h, 18, A1, 1.6, 255, 230);
  c.fillRect(0, 0, w, h, [2, 8, 14, 255], 175);
  c.text(LX, 14, assistant.toUpperCase().split('').join('.'), { size: 13, font: style.fontTitle, weight: 700, color: A1 });
  c.text(w - 64, 18, muted ? 'SPEAKERS MUTED - TEXT ONLY' : 'CONVERSATION LOG', { size: 7.5, align: 'RightTop', color: muted ? A1 : D });
  c.line(LX - 10, 50, w - 30, 50, D, 1, 200);
  c.line(w - 36, 16, w - 20, 32, A1, 1.6);
  c.line(w - 20, 16, w - 36, 32, A1, 1.6);
  c.text(w - 250, 18, 'TYPE', { size: 7.5, weight: 700, align: 'RightTop', color: A1 });
  if (lines.length === 0) {
    c.text(w / 2, h / 2, 'Nothing said yet - click the hologram and talk', { size: 8, align: 'CenterCenter', color: D });
  }
  lines.slice(Math.max(0, n - LOG_ROWS - sc), n - sc).forEach((L, r) => {
    const y = LOG_TOP + r * LOG_RH;
    if (L.text === '') return;
    if (L.first && L.who !== '') {
      const tag = L.who === 'U' ? 'YOU' : L.who === 'S' ? 'SYSTEM' : assistant.toUpperCase();
      c.text(LX, y, tag, { size: 7.2, weight: 700, color: L.who === 'U' ? D : L.who === 'S' ? style.warn : A1, glow: false });
    }
    c.text(TX, y, L.text, { size: 8.6, color: L.who === 'U' ? T : L.who === 'S' ? style.warn : W, font: style.fontNum, glow: false });
  });
  if (maxScroll > 0) {
    // scroll bar on the right
    const barH = (h - LOG_TOP - 24) * LOG_ROWS / n;
    const pos = (h - LOG_TOP - 24 - barH) * (1 - sc / maxScroll);
    c.line(w - 30, LOG_TOP, w - 30, h - 24, D, 1, 120);
    c.line(w - 30, LOG_TOP + pos, w - 30, LOG_TOP + pos + barH, A1, 3, 230);
  }
  return c.flush();
}
