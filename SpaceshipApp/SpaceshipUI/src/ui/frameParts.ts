// Frame/Parts/*.inc (tools/ship_frame.py output) read as SVG: Rainmeter Shape meters in the 2560x1600 canvas.
// Only what the parts use: Ellipse, Rectangle, Path of LineTo/ClosePath, Fill Color / LinearGradient, Stroke Color,
// StrokeWidth and StrokeLineJoin, with #Var# values and formulas of + - * / ( ) Min Max Clamp.

export type Grad = { x1: number; y1: number; x2: number; y2: number; stops: { off: number; color: string }[] };
export type PartShape = {
  kind: 'ellipse' | 'rect' | 'path';
  geo: Record<string, number | string>;
  fill: string | Grad;
  stroke: string;
  width: number;
  join: 'round' | 'miter';
};

/** A Rainmeter formula after the variables are in: numbers, + - * /, brackets and Min/Max/Clamp. NaN when it is anything else. */
export function evalExpr(s: string): number {
  const t = s.match(/\d*\.?\d+|[A-Za-z]+|[-+*/(),]|\S/g) ?? [];
  let i = 0;
  const atom = (): number => {
    const k = t[i++];
    if (k === '(') { const v = sum(); return t[i++] === ')' ? v : NaN; }
    if (k === '-') return -atom();
    if (k !== undefined && /^[A-Za-z]/.test(k)) {
      if (t[i++] !== '(') return NaN;
      const a = [sum()];
      while (t[i] === ',') { i++; a.push(sum()); }
      if (t[i++] !== ')') return NaN;
      const f = k.toLowerCase();
      return f === 'min' ? Math.min(...a) : f === 'max' ? Math.max(...a) : f === 'clamp' && a.length === 3 ? Math.min(a[2], Math.max(a[1], a[0])) : NaN;
    }
    return k !== undefined && /^\d*\.?\d+$/.test(k) ? Number(k) : NaN;
  };
  const prod = (): number => { let v = atom(); while (t[i] === '*' || t[i] === '/') v = t[i++] === '*' ? v * atom() : v / atom(); return v; };
  const sum = (): number => { let v = prod(); while (t[i] === '+' || t[i] === '-') v = t[i++] === '+' ? v + prod() : v - prod(); return v; };
  const v = sum();
  return i === t.length ? v : NaN;
}

/** Splits on commas outside brackets ("0,210,255,(Min(255,66*0.75))" is four parts). */
function splitTop(s: string): string[] {
  const out: string[] = [];
  let depth = 0, cur = '';
  for (const ch of s) {
    if (ch === ',' && depth === 0) { out.push(cur); cur = ''; continue; }
    if (ch === '(') depth++;
    else if (ch === ')') depth--;
    cur += ch;
  }
  out.push(cur);
  return out;
}

const nums = (s: string) => splitTop(s).map((x) => evalExpr(x.trim()));
const clamp255 = (x: number) => Math.min(255, Math.max(0, x));

/** "r,g,b[,a]" as CSS; 'none' for a fully clear or unreadable colour. */
export function cssColor(s: string): string {
  const [r, g, b, a = 255] = nums(s);
  if (![r, g, b, a].every(Number.isFinite) || a <= 0) return 'none';
  return `rgb(${[r, g, b].map((x) => Math.round(clamp255(x))).join(' ')} / ${+(clamp255(a) / 255).toFixed(4)})`;
}

/** "angle | color ; offset | ..." -- angle 0 runs left to right and turns clockwise (90 is top to bottom), across the shape's box. */
function gradient(s: string): Grad | null {
  const [head, ...rest] = s.split('|');
  const deg = evalExpr(head.trim());
  if (!Number.isFinite(deg)) return null;
  const c = +(Math.cos((deg * Math.PI) / 180) / 2).toFixed(4), n = +(Math.sin((deg * Math.PI) / 180) / 2).toFixed(4);
  const stops = rest.map((p) => { const [col, off] = p.split(';'); return { off: evalExpr((off ?? '').trim()), color: cssColor(col.trim()) }; });
  return { x1: 0.5 - c, y1: 0.5 - n, x2: 0.5 + c, y2: 0.5 + n, stops: stops.filter((x) => Number.isFinite(x.off)).map((x) => ({ ...x, color: x.color === 'none' ? 'transparent' : x.color })) };
}

/** "x,y | LineTo x,y | ... | ClosePath 1" as SVG path data. */
function pathD(s: string): string | null {
  const segs = s.split('|').map((x) => x.trim());
  const start = nums(segs[0]);
  if (start.length !== 2 || !start.every(Number.isFinite)) return null;
  let d = `M${start.join(' ')}`;
  for (const seg of segs.slice(1)) {
    const [cmd, arg = ''] = seg.split(/\s+(.*)/);
    if (cmd === 'LineTo') { const p = nums(arg); if (p.length !== 2 || !p.every(Number.isFinite)) return null; d += `L${p.join(' ')}`; }
    else if (cmd === 'ClosePath') { if (evalExpr(arg) !== 0) d += 'Z'; }
    else return null; // shortcut: only the commands the parts use; add ArcTo/CurveTo here if ship_frame.py starts writing them
  }
  return d;
}

/**
 * The Shape, Shape2, ... keys of one part section in order, read with the given variables (ColorAccent, GlowAlpha, ...).
 * A shape that does not parse is left out. Rainmeter's defaults apply: white fill, black stroke 1 wide, mitred joins.
 */
export function partShapes(sec: Record<string, string>, vars: Record<string, string>): PartShape[] {
  const sub = (s: string) => s.replace(/#(\w+)#/g, (m, k: string) => vars[k] ?? m);
  const keys = Object.keys(sec).filter((k) => /^Shape\d*$/.test(k)).sort((a, b) => Number(a.slice(5) || 1) - Number(b.slice(5) || 1));
  const out: PartShape[] = [];
  for (const k of keys) {
    const [geoSeg, ...mods] = sub(sec[k]).split('|').map((x) => x.trim());
    const [kind, arg = ''] = geoSeg.split(/\s+(.*)/);
    let shape: PartShape['kind'], geo: PartShape['geo'];
    if (kind === 'Ellipse' || kind === 'Rectangle') {
      const v = nums(arg);
      if (v.length < 3 || !v.every(Number.isFinite)) continue;
      if (kind === 'Ellipse') { shape = 'ellipse'; geo = { cx: v[0], cy: v[1], rx: v[2], ry: v[3] ?? v[2] }; }
      else { if (v.length < 4 || v[2] <= 0 || v[3] <= 0) continue; shape = 'rect'; geo = { x: v[0], y: v[1], width: v[2], height: v[3] }; }
    } else if (kind === 'Path') {
      const d = pathD(sub(sec[arg.trim()] ?? ''));
      if (!d) continue;
      shape = 'path'; geo = { d };
    } else continue;
    let fill: PartShape['fill'] = 'rgb(255 255 255 / 1)', stroke = 'rgb(0 0 0 / 1)', width = 1, join: PartShape['join'] = 'miter';
    for (const m of mods) {
      const [name, val = ''] = m.split(/\s+(.*)/);
      if (name === 'Fill') {
        const [how, rest = ''] = val.split(/\s+(.*)/);
        if (how === 'Color') fill = cssColor(rest);
        else if (how === 'LinearGradient') fill = gradient(sub(sec[rest.trim()] ?? '')) ?? 'none';
      } else if (name === 'Stroke') stroke = cssColor(val.replace(/^Color\s+/, ''));
      else if (name === 'StrokeWidth') width = Math.max(0, evalExpr(val) || 0);
      else if (name === 'StrokeLineJoin') join = val.trim().toLowerCase() === 'round' ? 'round' : 'miter';
    }
    out.push({ kind: shape, geo, fill, stroke: width > 0 ? stroke : 'none', width, join });
  }
  return out;
}
