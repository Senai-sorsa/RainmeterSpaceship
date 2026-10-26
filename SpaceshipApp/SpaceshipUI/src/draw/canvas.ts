import icons from '../generated/icons.json';
import type { RGBA } from '../lib/theme';
import type { Pt } from '../lib/geometry';
import { appIconUrls } from './appIcons';

// Port of the drawing layer in Skins/Spaceship/@Resources/Scripts/lib.lua (Canvas). Records draw ops in zone units; the
// output is device units, so it can be drawn as SVG without the Rainmeter meter strings. Glow tiers and colour rules match lib.lua.

/** icons.json holds the lib.lua op layout: [op, numbers...]. */
const ICONS = icons.icons as unknown as Record<string, [string, ...number[]][]>;

export type Layer = 'base' | 'glow' | 'core' | 'top';
export type Stroke = { color: RGBA; width: number; dash?: [number, number] };
export type Shape =
  | { kind: 'poly'; pts: Pt[]; closed: boolean }
  | { kind: 'ellipse'; cx: number; cy: number; rx: number; ry: number }
  | { kind: 'rect'; x: number; y: number; w: number; h: number; r: number }
  // blur is the shadow radius for a glow-layer copy of the text; 0 for the text itself. clipW is set only when clipped.
  | { kind: 'text'; x: number; y: number; text: string; size: number; align: string; weight: number; font: string; clipW?: number; blur: number }
  // matrix is an SVG feColorMatrix (20 numbers), the stand-in for Rainmeter's ColorMatrix / ImageTint / ImageAlpha
  | { kind: 'image'; x: number; y: number; w: number; h: number; href: string; matrix: number[] };
export type Op = { shape: Shape; fill?: RGBA; stroke?: Stroke };

/** Settings the skin reads from H.init (PerfTier, GlowAlpha, GlowWidth, CoreWhite, HudAlpha, Scale, EditMode, text settings) and its colours. */
export type Style = {
  s: number; tier: number; glowA: number; glowW: number; coreWhite: number; hudA: number; edit: boolean;
  textGlow: number; textGlowA: number; textSmall: number; textLarge: number; fontText: string; fontNum: string; fontTitle: string;
  white: RGBA; dim: RGBA; panel: RGBA; accent: RGBA; warn: RGBA; alert: RGBA; text: RGBA; hi: RGBA; good: RGBA;
};
export type Zone = { x: number; y: number; w: number; h: number };
export type TextOpts = { size?: number; color?: RGBA; alpha?: number; align?: string; weight?: number; font?: string; glow?: boolean; clip?: number };

/** Per-channel floor blend (lib.lua H.mix); alpha is always 255. */
export function mix(c1: RGBA, c2: RGBA, t: number): RGBA {
  const k = Math.min(1, Math.max(0, t));
  return [0, 1, 2].map((i) => Math.floor(c1[i] + (c2[i] - c1[i]) * k)).concat(255) as RGBA;
}

/** Value colour: accent below 0.7, blending to warn, then to alert (lib.lua H.ramp). */
export function ramp(st: Style, v: number): RGBA {
  if (v < 0.7) return st.accent;
  if (v < 0.9) return mix(st.accent, st.warn, (v - 0.7) / 0.2);
  return mix(st.warn, st.alert, (v - 0.9) / 0.1);
}

/** Width in zone units of text at a skin size, as lib.lua H.textWidth estimates it: 0.65 em per character, pt to px 4/3. Exact for the number font (B612 Mono). */
export const textWidth = (st: Style, txt: string, size: number) => txt.length * size * (size < 9.5 ? st.textSmall : st.textLarge) * (4 / 3) * 0.65;

/** Points along an arc in degrees (0 = right, clockwise on screen). Segment count defaults as in lib.lua. */
export function arcPts(cx: number, cy: number, rx: number, ry: number, a0: number, a1: number, segs = Math.max(6, Math.floor(Math.abs(a1 - a0) / 6))): Pt[] {
  const pts: Pt[] = [];
  for (let i = 0; i <= segs; i++) {
    const a = ((a0 + ((a1 - a0) * i) / segs) * Math.PI) / 180;
    pts.push([cx + rx * Math.cos(a), cy + ry * Math.sin(a)]);
  }
  return pts;
}

export class Canvas {
  private readonly layers: Record<Layer, Op[]> = { base: [], glow: [], core: [], top: [] };

  constructor(private readonly zone: Zone, private readonly st: Style) {}

  /** Zone units to device units: offset by the zone origin, then scale. Widths and dashes only scale. */
  private scaled(shape: Shape): Shape {
    const { s } = this.st, { x, y } = this.zone;
    switch (shape.kind) {
      case 'poly': return { ...shape, pts: shape.pts.map(([px, py]) => [(x + px) * s, (y + py) * s] as Pt) };
      case 'ellipse': return { kind: 'ellipse', cx: (x + shape.cx) * s, cy: (y + shape.cy) * s, rx: shape.rx * s, ry: shape.ry * s };
      case 'rect': return { kind: 'rect', x: (x + shape.x) * s, y: (y + shape.y) * s, w: shape.w * s, h: shape.h * s, r: shape.r * s };
      case 'text': return { ...shape, x: (x + shape.x) * s, y: (y + shape.y) * s, size: shape.size * s, clipW: shape.clipW && shape.clipW * s, blur: shape.blur * s };
      case 'image': return { ...shape, x: (x + shape.x) * s, y: (y + shape.y) * s, w: shape.w * s, h: shape.h * s };
    }
  }

  private push(layer: Layer, shape: Shape, fill?: RGBA, stroke?: Stroke) {
    const s = this.st.s;
    const dev = stroke && { color: stroke.color, width: stroke.width * s, dash: stroke.dash && ([stroke.dash[0] * s, stroke.dash[1] * s] as [number, number]) };
    this.layers[layer].push({ shape: this.scaled(shape), fill, stroke: dev });
  }

  /** HudAlpha scales every colour once, as H.rgba does. */
  private tint(c: RGBA, a: number): RGBA {
    return [c[0], c[1], c[2], Math.floor((a * this.st.hudA) / 255)];
  }

  private coreColour(c: RGBA): RGBA {
    return this.st.coreWhite > 0 ? mix(c, this.st.white, this.st.coreWhite) : c;
  }

  /** Neon line: on FULL a wide faint halo and a medium glow, on LITE the medium glow, on LOW and STEALTH only the core. */
  neon(shape: Shape, col: RGBA, w = 1.6, alpha?: number, layer: Layer = 'core') {
    const a = alpha ?? col[3], st = this.st;
    if (st.tier < 2 && st.glowA > 0) {
      if (st.tier === 0) this.push('glow', shape, undefined, { color: this.tint(col, Math.floor((st.glowA * 0.38 * a) / 255)), width: w * st.glowW * 2.1 });
      this.push('glow', shape, undefined, { color: this.tint(col, Math.floor((st.glowA * a) / 255)), width: w * st.glowW });
    }
    this.push(layer, shape, undefined, { color: this.tint(this.coreColour(col), a), width: w });
  }

  /** Soft round halo: three stacked translucent discs. Off on LOW and STEALTH. */
  halo(cx: number, cy: number, r: number, col: RGBA, alpha = 60) {
    if (this.st.tier >= 2) return;
    for (let i = 3; i >= 1; i--) {
      this.push('glow', { kind: 'ellipse', cx, cy, rx: r * (1 + i * 0.9), ry: r * (1 + i * 0.9) }, this.tint(col, Math.floor(alpha / (i + 1))));
    }
  }

  line(x1: number, y1: number, x2: number, y2: number, col: RGBA, w?: number, alpha?: number) {
    this.neon(poly([[x1, y1], [x2, y2]]), col, w, alpha);
  }

  /** Thin line with no glow, for grids and ticks. */
  hair(x1: number, y1: number, x2: number, y2: number, col: RGBA, w = 1, alpha = 120) {
    this.push('base', poly([[x1, y1], [x2, y2]]), undefined, { color: this.tint(col, alpha), width: w });
  }

  poly(pts: Pt[], col: RGBA, w?: number, alpha?: number, closed = false) {
    if (pts.length < 2) return;
    this.neon(poly(pts, closed), col, w, alpha);
  }

  /** Thin polyline with no glow, for back faces and grids. */
  hairPoly(pts: Pt[], col: RGBA, alpha = 120, w = 1) {
    if (pts.length < 2) return;
    this.push('base', poly(pts), undefined, { color: this.tint(col, alpha), width: w });
  }

  /** Filled polygon with no stroke, drawn under everything else. */
  fillPoly(pts: Pt[], col: RGBA, alpha?: number) {
    if (pts.length < 3) return;
    this.push('base', poly(pts, true), this.tint(col, alpha ?? col[3]));
  }

  fillRect(x: number, y: number, w: number, h: number, col: RGBA, alpha?: number, r = 0) {
    this.push('base', { kind: 'rect', x, y, w, h, r }, this.tint(col, alpha ?? col[3]));
  }

  rect(x: number, y: number, w: number, h: number, col: RGBA, lw?: number, alpha?: number, r = 0) {
    this.neon({ kind: 'rect', x, y, w, h, r }, col, lw, alpha);
  }

  circle(cx: number, cy: number, r: number, col: RGBA, lw?: number, alpha?: number) {
    this.neon({ kind: 'ellipse', cx, cy, rx: r, ry: r }, col, lw, alpha);
  }

  /** Lit light: a halo for bright dots, then the solid disc. */
  dot(cx: number, cy: number, r: number, col: RGBA, alpha?: number) {
    if ((alpha ?? 255) > 150) this.halo(cx, cy, r, col, 70);
    this.push('core', { kind: 'ellipse', cx, cy, rx: r, ry: r }, this.tint(col, alpha ?? col[3]));
  }

  fillCircle(cx: number, cy: number, r: number, col: RGBA, alpha?: number) {
    this.push('base', { kind: 'ellipse', cx, cy, rx: r, ry: r }, this.tint(col, alpha ?? col[3]));
  }

  /** Arc in degrees; ry defaults to r. */
  arc(cx: number, cy: number, r: number, a0: number, a1: number, col: RGBA, lw?: number, alpha?: number, ry?: number) {
    this.poly(arcPts(cx, cy, r, ry ?? r, a0, a1), col, lw, alpha);
  }

  /** Dashed arc. dash and gap are zone units. Same start angle and pattern line up segment for segment. */
  dashArc(cx: number, cy: number, r: number, a0: number, a1: number, col: RGBA, lw: number, alpha: number | undefined, dash: number, gap: number, noGlow = false) {
    const shape = poly(arcPts(cx, cy, r, r, a0, a1, Math.max(12, Math.floor(Math.abs(a1 - a0) / 3))));
    const a = alpha ?? 255, st = this.st, d: [number, number] = [dash, gap];
    if (!noGlow && st.tier < 2 && st.glowA > 0) this.push('glow', shape, undefined, { color: this.tint(col, Math.floor((st.glowA * a) / 255)), width: lw * 1.8, dash: d });
    this.push('core', shape, undefined, { color: this.tint(this.coreColour(col), a), width: lw, dash: d });
  }

  /** Annular wedge between radii r0 and r1, a0 to a1 degrees. */
  sector(cx: number, cy: number, r0: number, r1: number, a0: number, a1: number, col: RGBA, fillAlpha?: number, strokeAlpha?: number) {
    const pts = [...arcPts(cx, cy, r1, r1, a0, a1, 10), ...arcPts(cx, cy, r0, r0, a1, a0, 10)];
    this.fillPoly(pts, col, fillAlpha ?? 40);
    if (strokeAlpha && strokeAlpha > 0) this.poly(pts, col, 1, strokeAlpha, true);
  }

  /** n segments, the first round(v * n) lit. Unlit segments use the dim colour. */
  segBar(x: number, y: number, w: number, h: number, v: number, n: number, col?: RGBA, gap = 3) {
    const sw = (w - gap * (n - 1)) / n;
    const lit = Math.floor(Math.min(1, Math.max(0, v)) * n + 0.5);
    for (let i = 0; i < n; i++) {
      const sx = x + i * (sw + gap);
      if (i < lit) this.fillRect(sx, y, sw, h, col ?? ramp(this.st, (i + 1) / n), 230);
      else this.fillRect(sx, y, sw, h, this.st.dim, 60);
    }
  }

  /** History graph from values in 0..1 (newest last): filled area under a line. */
  graph(x: number, y: number, w: number, h: number, hist: number[], col: RGBA, fillAlpha?: number) {
    const n = hist.length;
    if (n < 2) return;
    const pts: Pt[] = hist.map((v, i) => [x + (i * w) / (n - 1), y + h - Math.min(1, Math.max(0, v)) * h]);
    this.fillPoly([[x, y + h], ...pts, [x + w, y + h]], col, fillAlpha ?? 40);
    this.poly(pts, col, 1.4);
  }

  /** Corner brackets around a box. */
  brackets(x: number, y: number, w: number, h: number, len = 14, col: RGBA, lw?: number, alpha?: number) {
    this.poly([[x, y + len], [x, y], [x + len, y]], col, lw, alpha);
    this.poly([[x + w - len, y], [x + w, y], [x + w, y + len]], col, lw, alpha);
    this.poly([[x + w, y + h - len], [x + w, y + h], [x + w - len, y + h]], col, lw, alpha);
    this.poly([[x + len, y + h], [x, y + h], [x, y + h - len]], col, lw, alpha);
  }

  /** Text at x, y in zone units, as H.text: sizes under 9.5 scale up, a zero-offset glow shadow on FULL and LITE, optional clip width. Empty text draws nothing. */
  text(x: number, y: number, txt: string, opts: TextOpts = {}) {
    if (!txt) return;
    const st = this.st, base = opts.size ?? 11;
    const tc = opts.color ?? st.text;
    const fill = st.coreWhite > 0 ? mix(tc, st.white, st.coreWhite * 0.5) : tc;
    const size = base * (base < 9.5 ? st.textSmall : st.textLarge), font = opts.font ?? st.fontText;
    // ClipString=1 trims the end with an ellipsis; the number font is monospaced, so the fit is exact.
    // shortcut: proportional fonts only get the clip box, measure the text if their trim must match too
    const fit = opts.clip !== undefined && font === st.fontNum ? Math.floor(opts.clip / textWidth(st, 'x', base)) : Infinity;
    const shape = {
      kind: 'text' as const, x, y, text: txt.length > fit ? txt.slice(0, Math.max(0, fit - 1)) + '…' : txt, size, align: opts.align ?? 'LeftTop',
      weight: opts.weight ?? 600, font, clipW: opts.clip, blur: 0,
    };
    if (st.tier < 2 && st.textGlow > 0 && opts.glow !== false) {
      this.push('top', { ...shape, blur: st.textGlow }, this.tint(tc, Math.floor((st.textGlowA * (opts.alpha ?? 255)) / 255)));
    }
    this.push('top', shape, this.tint(fill, opts.alpha ?? fill[3]));
  }

  /** Icon from icons.json, authored in a 100x100 box and fitted to sz, centred on cx, cy. Unknown names draw the gear, as lib.lua does. */
  icon(name: string, cx: number, cy: number, sz: number, col: RGBA, lw?: number, alpha?: number) {
    const k = sz / 100;
    const P = (x: number, y: number): Pt => [cx + (x - 50) * k, cy + (y - 50) * k];
    for (const [t, ...v] of ICONS[name] ?? ICONS.gear) {
      if (t === 'l' || t === 'p') {
        const pts: Pt[] = [];
        for (let i = 0; i + 1 < v.length; i += 2) pts.push(P(v[i], v[i + 1]));
        this.poly(pts, col, lw, alpha, t === 'p');
      } else if (t === 'c') {
        this.circle(cx + (v[0] - 50) * k, cy + (v[1] - 50) * k, v[2] * k, col, lw, alpha);
      } else if (t === 'a') {
        const [x, y, r, a0, a1, ry = r] = v;
        this.poly(arcPts(cx + (x - 50) * k, cy + (y - 50) * k, r * k, ry * k, a0, a1), col, lw, alpha);
      } else if (t === 'e') {
        const [x, y, rx, ry] = v;
        this.poly(arcPts(cx + (x - 50) * k, cy + (y - 50) * k, rx * k, ry * k, 0, 360, 36), col, lw, alpha);
      }
    }
  }

  /** The app's own icon (lib.lua H.image): greyscale recoloured from the accent (dark) to white (bright), over its glow
   *  tinted in the accent at 0.8 alpha and 1.25x size, the glow off on LOW and STEALTH. False when there is no icon file,
   *  so the caller draws its line icon instead. */
  appIcon(id: string, cx: number, cy: number, size: number, alpha = 255): boolean {
    const urls = appIconUrls(id);
    if (!urls) return false;
    const st = this.st, a = Math.floor((alpha * st.hudA) / 255) / 255;
    const [r, g, b] = st.accent.map((v) => v / 255);
    const box = (s: number) => ({ x: cx - s / 2, y: cy - s / 2, w: s, h: s });
    if (urls.glow && st.tier < 2) {
      this.push('glow', { kind: 'image', ...box(size * 1.25), href: urls.glow, matrix: [r, 0, 0, 0, 0, 0, g, 0, 0, 0, 0, 0, b, 0, 0, 0, 0, 0, Math.floor(a * 255 * 0.8) / 255, 0] });
    }
    this.push('core', { kind: 'image', ...box(size), href: urls.icon, matrix: [1 - r, 0, 0, 0, r, 1 - g, 0, 0, 0, g, 1 - b, 0, 0, 0, b, 0, 0, 0, a, 0] });
    return true;
  }

  /** Panel outline with chamfered corners, optionally filled with the panel colour. */
  chamfer(x: number, y: number, w: number, h: number, c: number, col: RGBA, lw?: number, alpha?: number, fillAlpha?: number) {
    const pts: Pt[] = [[x + c, y], [x + w, y], [x + w, y + h - c], [x + w - c, y + h], [x, y + h], [x, y + c]];
    if (fillAlpha && fillAlpha > 0) this.fillPoly(pts, this.st.panel, fillAlpha);
    this.poly(pts, col, lw, alpha, true);
  }

  /** Ops in paint order: base, glow, core, top. Edit mode adds the zone outline, which is not scaled. */
  flush(): Op[] {
    const out = [...this.layers.base, ...this.layers.glow, ...this.layers.core, ...this.layers.top];
    if (this.st.edit) {
      const { x, y, w, h } = this.zone, s = this.st.s;
      out.push({ shape: { kind: 'rect', x: x * s, y: y * s, w: w * s, h: h * s, r: 0 }, fill: [255, 200, 0, 18], stroke: { color: [255, 200, 0, 200], width: 2 } });
    }
    return out;
  }
}

function poly(pts: Pt[], closed = false): Shape {
  return { kind: 'poly', pts, closed };
}
