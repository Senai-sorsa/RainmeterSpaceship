import icons from '../generated/icons.json';
import type { RGBA } from '../lib/theme';
import type { Pt } from '../lib/geometry';
import { appIconUrls } from './appIcons';
import { bendFor, warpPoly, type Curve, type Warp } from './curve';

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
/** bloom: set on glow-layer ops on FULL; the view blurs that run of ops by this many device units, so the halo strokes
 *  fall off like light instead of ending in a hard edge. */
export type Op = { shape: Shape; fill?: RGBA; stroke?: Stroke; bloom?: number; grad?: Grad; pattern?: string; shimmer?: string };
/** A gradient fill (realism kit K1): offsets 0..1 with their colours. Coordinates are zone units in Canvas calls and
 *  device units in ops (userSpaceOnUse), so a gradient skews with its zone. When an op has grad it wins over fill. */
export type GradStop = [number, RGBA];
export type Grad =
  | { kind: 'linear'; x1: number; y1: number; x2: number; y2: number; stops: GradStop[] }
  | { kind: 'radial'; cx: number; cy: number; r: number; stops: GradStop[] };
/** The shared screen texture (K4), defined once by HudDefs in ops.tsx. */
export const HUD_SCAN = 'hud-scan';
export type ScreenOpts = {
  /** body colour; defaults to the accent */
  col?: RGBA;
  /** the edge the backlight sits at: brightest there, falling off across the panel */
  from?: 'top' | 'bottom' | 'left' | 'right';
  /** corner cut in zone units (top-left and bottom-right, as chamfer draws them); 0 = square */
  cut?: number;
  /** backlight strength 0..1 (default 0.5) */
  lit?: number;
  /** screen texture on FULL and LITE (default true) */
  texture?: boolean;
  /** soft outer glow on FULL (default true) */
  glow?: boolean;
};

/** Settings the skin reads from H.init (PerfTier, GlowAlpha, GlowWidth, CoreWhite, HudAlpha, Scale, EditMode, text settings) and its colours. */
export type Style = {
  s: number; tier: number; glowA: number; glowW: number; coreWhite: number; hudA: number; edit: boolean; /** the fitted picture frame is on: zones are seated into its slots (modules/pictureSlots.ts) */ fitted?: boolean;
  textGlow: number; textGlowA: number; textSmall: number; textLarge: number; fontText: string; fontNum: string; fontTitle: string;
  white: RGBA; dim: RGBA; panel: RGBA; accent: RGBA; warn: RGBA; alert: RGBA; text: RGBA; hi: RGBA; good: RGBA;
  /** screen() draws a hardware bezel round each display (setting ScreenBezel); off when left out */
  bezel?: boolean;
  /** HullRender: the shell's curve table (tools/frame_src/curve.json); long elements in its zones bend with it */
  curve?: Curve;
};
export type Zone = { x: number; y: number; w: number; h: number; id?: string };
export type TextOpts = { size?: number; color?: RGBA; alpha?: number; align?: string; weight?: number; font?: string; glow?: boolean; clip?: number;
  /** K7: faint red/blue fringe copies on large bright text (FULL only); default on for sizes 13 and up */
  fringe?: boolean;
  /** K9: a key for the readout's value; when it changes the text flickers on once (FULL only, CSS, off for reduced motion) */
  shimmer?: string };

/** The app's typeface roles beyond the skin: condensed display faces sit small on their em box, so they draw larger to
 *  match the cap height of B612 Mono, and they keep the weight the module asks for (the skin's Rainmeter could not).
 *  Fonts not listed draw exactly as the skin does (regular weight, no scale). */
export const FONT_SCALE: Record<string, number> = { Rajdhani: 1.14 };

/** Per-channel floor blend (lib.lua H.mix); alpha is always 255. */
export function mix(c1: RGBA, c2: RGBA, t: number): RGBA {
  const k = Math.min(1, Math.max(0, t));
  return [0, 1, 2].map((i) => Math.floor(c1[i] + (c2[i] - c1[i]) * k)).concat(255) as RGBA;
}

/** Hot-core colour ramp (K3): a bright core burns towards white and keeps a trace of its hue, more so the hotter it is
 *  (k 0..1 maps to 55..75 % white). CoreWhite 0 means the user wants no white cores, so the colour is kept. */
export function heat(st: Style, col: RGBA, k = 0.5): RGBA {
  if (st.coreWhite <= 0) return [col[0], col[1], col[2], col[3]];
  const c = mix(col, st.white, 0.55 + 0.2 * Math.min(1, Math.max(0, k)));
  return [c[0], c[1], c[2], col[3]];
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
  /** K5: the wide second bloom for the few hottest things; FULL only, drawn first in the glow layer */
  private readonly hotOps: Op[] = [];

  private readonly warp?: Warp;

  constructor(private readonly zone: Zone, private readonly st: Style) {
    if (st.curve) this.warp = bendFor(zone.id, zone, st.curve);
  }

  /** Task 10: the zone's bend, in zone units. A rect becomes a closed poly (long edges split); text, ellipses and images move by their anchor. */
  private bent(shape: Shape): Shape {
    const w = this.warp;
    if (!w) return shape;
    switch (shape.kind) {
      case 'poly': return { ...shape, pts: warpPoly(shape.pts, w) };
      case 'rect': {
        const { x, y, w: rw, h } = shape;
        return { kind: 'poly', closed: true, pts: warpPoly([[x, y], [x + rw, y], [x + rw, y + h], [x, y + h], [x, y]], w).slice(0, -1) };
      }
      case 'ellipse': { const [cx, cy] = w([shape.cx, shape.cy]); return { ...shape, cx, cy }; }
      case 'text': case 'image': { const [x, y] = w([shape.x, shape.y]); return { ...shape, x, y }; }
    }
  }

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

  private push(layer: Layer, shape: Shape, fill?: RGBA, stroke?: Stroke, paint?: { grad?: Grad; pattern?: string }) {
    const s = this.st.s;
    const dev = stroke && { color: stroke.color, width: stroke.width * s, dash: stroke.dash && ([stroke.dash[0] * s, stroke.dash[1] * s] as [number, number]) };
    const op: Op = { shape: this.scaled(this.bent(shape)), fill, stroke: dev };
    if (paint?.grad) op.grad = this.scaledGrad(paint.grad);
    if (paint?.pattern) op.pattern = paint.pattern;
    this.layers[layer].push(op);
  }

  /** A gradient to device units, its stop colours through HudAlpha. */
  private scaledGrad(g: Grad): Grad {
    const { s } = this.st, { x, y } = this.zone;
    const stops = g.stops.map(([o, c]) => [Math.min(1, Math.max(0, o)), this.tint(c, c[3])] as GradStop);
    return g.kind === 'linear'
      ? { kind: 'linear', x1: (x + g.x1) * s, y1: (y + g.y1) * s, x2: (x + g.x2) * s, y2: (y + g.y2) * s, stops }
      : { kind: 'radial', cx: (x + g.cx) * s, cy: (y + g.cy) * s, r: g.r * s, stops };
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
      // display faces: small print stays at medium weight under the bold titles, so the rows read title-then-detail
      weight: FONT_SCALE[font] && base < 8 ? Math.min(opts.weight ?? 600, 500) : opts.weight ?? 600, font, clipW: opts.clip, blur: 0,
    };
    const before = this.layers.top.length;
    if (st.tier < 2 && st.textGlow > 0 && opts.glow !== false) {
      // a heavier face fills its own halo, so its glow is softer (0.55) to keep the letters apart
      const ga = Math.floor((st.textGlowA * (opts.alpha ?? 255) * (FONT_SCALE[font] ? 0.55 : 1)) / 255);
      this.push('top', { ...shape, blur: st.textGlow }, this.tint(tc, ga));
    }
    if (st.tier === 0 && (opts.fringe ?? base >= 13)) {
      // a lens's chromatic fringe: red a hair left, blue a hair right (0.6 device px), faint, under the letters
      const d = 0.6 / st.s, fa = Math.floor(((opts.alpha ?? 255) * 0.17));
      this.push('top', { ...shape, x: x - d }, this.tint([255, 70, 70, 255], fa));
      this.push('top', { ...shape, x: x + d }, this.tint([70, 130, 255, 255], fa));
    }
    this.push('top', shape, this.tint(fill, opts.alpha ?? fill[3]));
    if (opts.shimmer !== undefined && st.tier === 0) for (const o of this.layers.top.slice(before)) o.shimmer = opts.shimmer;
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

  /** A tinted image under the shapes (lib.lua H.sprite: a separate meter before the canvas, ImageTint + ImageAlpha). */
  sprite(cx: number, cy: number, w: number, h: number, href: string, col: RGBA, alpha = 255) {
    const a = Math.floor((alpha * this.st.hudA) / 255) / 255;
    const [r, g, b] = col.map((v) => v / 255);
    this.push('base', { kind: 'image', x: cx - w / 2, y: cy - h / 2, w, h, href, matrix: [r, 0, 0, 0, 0, 0, g, 0, 0, 0, 0, 0, b, 0, 0, 0, 0, 0, a, 0] });
  }

  /** Rectangle filled with a gradient (K1), under everything else. */
  gradRect(x: number, y: number, w: number, h: number, grad: Grad, r = 0) {
    this.push('base', { kind: 'rect', x, y, w, h, r }, undefined, undefined, { grad });
  }

  /** Polygon filled with a gradient (K1), under everything else. */
  gradPoly(pts: Pt[], grad: Grad) {
    if (pts.length < 3) return;
    this.push('base', poly(pts, true), undefined, undefined, { grad });
  }

  /** Wide soft bloom (K5) around one of the hottest things in a cluster (a live value, an active key, the orb's rings):
   *  a broad faint stroke the view blurs about three times wider than the normal glow. FULL only. */
  hot(pts: Pt[], col: RGBA, w = 2, alpha = 120, closed = false) {
    const st = this.st;
    if (st.tier !== 0 || st.glowA <= 0 || pts.length < 2) return;
    const before = this.layers.glow.length;
    this.push('glow', poly(pts, closed), undefined, { color: this.tint(col, Math.floor((st.glowA * 0.5 * alpha) / 255)), width: w * st.glowW * 2.6 });
    this.hotOps.push(...this.layers.glow.splice(before));
  }

  /** K5 for a round light (a lamp, a leading dot): a broad faint disc under the wide bloom. FULL only. */
  hotDot(cx: number, cy: number, r: number, col: RGBA, alpha = 110) {
    const st = this.st;
    if (st.tier !== 0 || st.glowA <= 0) return;
    const before = this.layers.glow.length;
    this.push('glow', { kind: 'ellipse', cx, cy, rx: r * 3, ry: r * 3 }, this.tint(col, Math.floor((st.glowA * 0.6 * alpha) / 255)));
    this.hotOps.push(...this.layers.glow.splice(before));
  }

  /** The screen texture (K4) over a lit shape, on FULL and LITE only. */
  texture(pts: Pt[]) {
    if (this.st.tier >= 2 || pts.length < 3) return;
    this.push('base', poly(pts, true), undefined, undefined, { pattern: HUD_SCAN });
  }

  /** Backlit display (K2): a glass body lit from one edge, the screen texture, a faint inner border, a bright line along
   *  the lit edge and, on FULL, a soft glow beyond the outline. Graphics drawn afterwards sit on it. LITE drops the glow;
   *  LOW and STEALTH get the flat body and the inner border only (no gradient, texture or glow). */
  screen(x: number, y: number, w: number, h: number, opts: ScreenOpts = {}) {
    const st = this.st, col = opts.col ?? st.accent, lit = Math.min(1, Math.max(0, opts.lit ?? 0.5));
    const c = Math.min(opts.cut ?? 0, w / 2, h / 2), from = opts.from ?? 'top';
    const box = (i: number): Pt[] => {
      const [x0, y0, x1, y1, k] = [x + i, y + i, x + w - i, y + h - i, Math.max(0, c - i * 0.6)];
      return k > 0 ? [[x0 + k, y0], [x1, y0], [x1, y1 - k], [x1 - k, y1], [x0, y1], [x0, y0 + k]] : [[x0, y0], [x1, y0], [x1, y1], [x0, y1]];
    };
    const body = box(0);
    // the bezel (12 #11), FULL and LITE: a dark recess round the glass, so the readout sits in the hull, and a faint lip
    // on the lower outer edge, where the cabin light catches the hardware. Under the body; never glowing.
    const lip = box(-2.4), y1 = Math.max(...lip.map(([, py]) => py));
    this.bezel(box(-1.2), lip.filter(([, py]) => py === y1));
    if (st.tier >= 2) {
      this.fillPoly(body, col, Math.floor(26 * lit));
    } else {
      // the gradient runs from the lit edge across the panel
      const [x1, y1, x2, y2] = from === 'top' ? [x, y, x, y + h] : from === 'bottom' ? [x, y + h, x, y] : from === 'left' ? [x, y, x + w, y] : [x + w, y, x, y];
      this.gradPoly(body, { kind: 'linear', x1, y1, x2, y2, stops: [[0, alpha(col, 70 * lit)], [0.45, alpha(col, 30 * lit)], [1, alpha(st.panel, 40)]] });
      if (opts.texture !== false) this.push('base', poly(body, true), undefined, undefined, { pattern: HUD_SCAN });
      if (st.tier === 0 && opts.glow !== false && st.glowA > 0) {
        this.push('glow', poly(body, true), undefined, { color: this.tint(col, Math.floor(st.glowA * 0.6 * lit)), width: 3 * st.glowW });
      }
      const [ex1, ey1, ex2, ey2] = from === 'top' ? [x + c, y, x + w, y] : from === 'bottom' ? [x, y + h, x + w - c, y + h] : from === 'left' ? [x, y + c, x, y + h] : [x + w, y, x + w, y + h - c];
      this.push('base', poly([[ex1, ey1], [ex2, ey2]]), undefined, { color: this.tint(heat(st, col, lit), Math.floor(120 + 110 * lit)), width: 1 });
    }
    this.push('base', poly(box(1.5), true), undefined, { color: this.tint(col, 77), width: 1 });
  }

  /** The hardware round a display (12 #11, #22), FULL and LITE with the ScreenBezel setting: a dark recess along the
   *  closed outline just outside the glass, and a faint lip along the open lower edge (where the cabin light catches
   *  it). Call it before the body, so both sit under it. Never glows. */
  bezel(recess: Pt[], lip: Pt[]) {
    const st = this.st;
    if (!st.bezel || st.tier >= 2) return;
    this.push('base', poly(recess, true), undefined, { color: [0, 0, 0, 150], width: 1.6 });
    if (lip.length >= 2) this.push('base', poly(lip), undefined, { color: this.tint(st.white, 40), width: 0.7 });
  }

  /** Panel outline with chamfered corners, optionally filled with the panel colour. */
  chamfer(x: number, y: number, w: number, h: number, c: number, col: RGBA, lw?: number, alpha?: number, fillAlpha?: number) {
    const pts: Pt[] = [[x + c, y], [x + w, y], [x + w, y + h - c], [x + w - c, y + h], [x, y + h], [x, y + c]];
    if (fillAlpha && fillAlpha > 0) this.fillPoly(pts, this.st.panel, fillAlpha);
    this.poly(pts, col, lw, alpha, true);
  }

  /** Ops in paint order: base, glow, core, top. Edit mode adds the zone outline, which is not scaled. */
  flush(): Op[] {
    // FULL: the glow strokes are blurred by about a third of the widest halo, so a line's light fades out softly
    const st = this.st, bloom = st.tier === 0 ? 1.6 * st.glowW * 0.45 * st.s : 0;
    const glow = bloom > 0 ? this.layers.glow.map((o) => (o.shape.kind === 'image' ? o : { ...o, bloom })) : this.layers.glow;
    // the hot bloom: one wider blurred group ahead of the normal glow (only recorded on FULL, where bloom > 0)
    if (bloom > 0 && this.hotOps.length) glow.unshift(...this.hotOps.map((o) => ({ ...o, bloom: bloom * 3 })));
    const out = [...this.layers.base, ...glow, ...this.layers.core, ...this.layers.top];
    if (this.st.edit) {
      const { x, y, w, h } = this.zone, s = this.st.s;
      out.push({ shape: { kind: 'rect', x: x * s, y: y * s, w: w * s, h: h * s, r: 0 }, fill: [255, 200, 0, 18], stroke: { color: [255, 200, 0, 200], width: 2 } });
    }
    return out;
  }
}

function alpha(c: RGBA, a: number): RGBA {
  return [c[0], c[1], c[2], Math.max(0, Math.min(255, Math.floor(a)))];
}

function poly(pts: Pt[], closed = false): Shape {
  return { kind: 'poly', pts, closed };
}
