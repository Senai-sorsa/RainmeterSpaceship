import { css } from '../lib/theme';
import { FONT_SCALE, type Op } from './canvas';
import type { BloomEntry } from './bloomBus';
import { PT_PX, textAlign } from './ops';

// Painters for the light canvas (tasks/hyperrealism-plan.md Task 2). Pure: they only call the context they are given,
// so the tests run them on a recording fake.

export type Ctx2D = Pick<CanvasRenderingContext2D, 'setTransform' | 'beginPath' | 'moveTo' | 'lineTo' | 'closePath' | 'ellipse'
  | 'rect' | 'fill' | 'stroke' | 'fillText' | 'save' | 'restore' | 'drawImage' | 'clearRect' | 'clip' | 'setLineDash'> & {
  fillStyle: unknown; strokeStyle: unknown; lineWidth: number; font: string; textAlign: CanvasTextAlign;
  textBaseline: CanvasTextBaseline; globalAlpha: number; globalCompositeOperation: GlobalCompositeOperation; filter: string;
  lineCap: CanvasLineCap; lineJoin: CanvasLineJoin;
};

/** Optical falloff: the same light blurred at three radii, each wider and fainter (Kawase 2004, Jimenez 2014). */
export const BLOOM_STACK: readonly (readonly [radiusMul: number, alpha: number])[] = [[1, 0.6], [3, 0.3], [9, 0.15]];

const BASE: Record<string, CanvasTextBaseline> = { 'text-before-edge': 'top', central: 'middle', 'text-after-edge': 'bottom' };
const ANCHOR: Record<string, CanvasTextAlign> = { start: 'left', middle: 'center', end: 'right' };

/** A gradient or pattern fill falls back to its brightest-looking stop: the glow only needs the colour. */
const fillOf = (op: Op) => op.fill ?? op.grad?.stops.at(-1)?.[1];

/** Draws every entry's ops; scale is canvas px per CSS px (0.25 for the quarter-res canvas); dx/dy shift the result
 *  (a tile's origin). Images are skipped. */
export function paintOps(ctx: Ctx2D, entries: Iterable<BloomEntry>, scale: number, dx = 0, dy = 0) {
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  for (const { ops, ctm } of entries) {
    ctx.setTransform(ctm.a * scale, ctm.b * scale, ctm.c * scale, ctm.d * scale, ctm.e * scale - dx, ctm.f * scale - dy);
    for (const op of ops) paintOp(ctx, op);
  }
  ctx.setTransform(1, 0, 0, 1, 0, 0);
}

function paintOp(ctx: Ctx2D, op: Op) {
  const sh = op.shape, fill = fillOf(op);
  if (sh.kind === 'image') return;
  if (sh.kind === 'text') {
    if (!fill) return;
    const { anchor, base } = textAlign(sh.align);
    const px = sh.size * PT_PX * (FONT_SCALE[sh.font] ?? 1);
    ctx.font = `${FONT_SCALE[sh.font] ? sh.weight : 400} ${px.toFixed(2)}px ${sh.font}`;
    ctx.textAlign = ANCHOR[anchor];
    ctx.textBaseline = BASE[base];
    ctx.fillStyle = css(fill);
    if (sh.clipW === undefined) { ctx.fillText(sh.text, sh.x, sh.y); return; }
    // the same box as the SVG clip-path (ops.tsx): from the anchor, back for right-aligned and centred text
    const left = anchor === 'end' ? sh.x - sh.clipW : anchor === 'middle' ? sh.x - sh.clipW / 2 : sh.x;
    ctx.save();
    ctx.beginPath();
    ctx.rect(left, sh.y - px, sh.clipW, px * 2);
    ctx.clip();
    ctx.fillText(sh.text, sh.x, sh.y);
    ctx.restore();
    return;
  }
  ctx.beginPath();
  if (sh.kind === 'poly') {
    sh.pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
    if (sh.closed) ctx.closePath();
  } else if (sh.kind === 'ellipse') ctx.ellipse(sh.cx, sh.cy, Math.abs(sh.rx), Math.abs(sh.ry), 0, 0, Math.PI * 2);
  else ctx.rect(sh.x, sh.y, sh.w, sh.h);
  if (fill) { ctx.fillStyle = css(fill); ctx.fill(); }
  if (op.stroke) {
    ctx.strokeStyle = css(op.stroke.color);
    ctx.lineWidth = op.stroke.width;
    if (op.stroke.dash) { ctx.setLineDash(op.stroke.dash); ctx.stroke(); ctx.setLineDash([]); } else ctx.stroke();
  }
}

/** The stacked blur: src drawn three times onto dst, each pass wider and fainter (BLOOM_STACK). */
export function stackBlur(dst: Ctx2D, src: CanvasImageSource, baseRadius: number) {
  for (const [m, a] of BLOOM_STACK) {
    dst.filter = `blur(${+(baseRadius * m).toFixed(2)}px)`;
    dst.globalAlpha = a;
    dst.drawImage(src, 0, 0);
  }
  dst.filter = 'none';
  dst.globalAlpha = 1;
}

export type Box = { x: number; y: number; w: number; h: number };

/** The canvas-px box an entry's light can reach: its ops through ctm x scale, padded by pad (the widest blur), clamped to
 *  the canvas. null when it is off the canvas. Text is boxed by its font size and length (generous: light only). */
export function entryBounds(e: BloomEntry, scale: number, pad: number, cw: number, ch: number): Box | null {
  const { a, b, c, d, e: tx, f: ty } = e.ctm;
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  const add = (x: number, y: number) => {
    const X = (a * x + c * y + tx) * scale, Y = (b * x + d * y + ty) * scale;
    x0 = Math.min(x0, X); y0 = Math.min(y0, Y); x1 = Math.max(x1, X); y1 = Math.max(y1, Y);
  };
  for (const { shape: s } of e.ops) {
    if (s.kind === 'poly') s.pts.forEach(([x, y]) => add(x, y));
    else if (s.kind === 'ellipse') { add(s.cx - s.rx, s.cy - s.ry); add(s.cx + s.rx, s.cy + s.ry); add(s.cx - s.rx, s.cy + s.ry); add(s.cx + s.rx, s.cy - s.ry); }
    else if (s.kind === 'rect') { add(s.x, s.y); add(s.x + s.w, s.y + s.h); add(s.x, s.y + s.h); add(s.x + s.w, s.y); }
    else if (s.kind === 'text') {
      const px = s.size * PT_PX * (FONT_SCALE[s.font] ?? 1), len = px * s.text.length * 0.75;
      add(s.x - len, s.y - px); add(s.x + len, s.y + px);
    }
  }
  if (x0 === Infinity) return null;
  const bx = Math.max(0, Math.floor(x0 - pad)), by = Math.max(0, Math.floor(y0 - pad));
  const ex = Math.min(cw, Math.ceil(x1 + pad)), ey = Math.min(ch, Math.ceil(y1 + pad));
  return ex > bx && ey > by ? { x: bx, y: by, w: ex - bx, h: ey - by } : null;
}

/** One cached light tile per anchor (Chrome: blur what changes, reuse what does not). An entry object is replaced by the
 *  bus only when its ops or CTM change, so object identity says whether a tile must be rebuilt. minMs caps how often one
 *  tile is re-blurred (the audio ring changes 20 times a second; its glow at 10 is indistinguishable under the crisp
 *  lines): update() keeps the old tile and returns how many ms until a retry is due (0 = nothing waiting). */
export class TileCache<T> {
  readonly tiles = new Map<string, { entry: BloomEntry; tile: T; at: number }>();
  constructor(private readonly make: (key: string, e: BloomEntry) => T, private readonly minMs = 0,
    private readonly clock: () => number = () => performance.now()) {}
  update(entries: ReadonlyMap<string, BloomEntry>): number {
    for (const k of [...this.tiles.keys()]) if (!entries.has(k)) this.tiles.delete(k);
    const now = this.clock();
    let wait = 0;
    for (const [k, e] of entries) {
      const t = this.tiles.get(k);
      if (t && t.entry === e) continue;
      if (t && now - t.at < this.minMs) { const w = t.at + this.minMs - now; wait = wait ? Math.min(wait, w) : w; continue; }
      this.tiles.set(k, { entry: e, tile: this.make(k, e), at: now });
    }
    return wait;
  }
}

/** The light tiles' rebuild cap (TileCache minMs). */
export const TILE_MS = 100;

/** Glass (Task 6): how faint the HUD's reflection is, how much larger than the HUD (a second surface a bit nearer), and
 *  how soft (light-canvas px; no text shape survives in it). LENS_SPREAD: the light scattered across the lens, which is
 *  what lights the dirt - wide, so a smudge glows near any bright part of the HUD, not only on top of it. */
export const GHOST_ALPHA = 0.07;
export const GHOST_SCALE = 1.035;
export const GHOST_BLUR = 2;
export const LENS_SPREAD = 7;
/** The glass is painted at half the light canvas size (so the blurs above are in those px) and at most every GLASS_MS:
 *  the lens glow drifts slowly to the eye, the HUD light under it does not need to (Task 13 measurement). */
export const GLASS_SCALE = 0.5;
export const GLASS_MS = 250;

/** The lens's own light: the HUD light spread wide, times the dirt mask (smudges show only near bright parts), then a
 *  faint, soft, slightly enlarged ghost of the light (its reflection in the glass). */
export function paintGlass(ctx: Ctx2D, bloom: CanvasImageSource, dirt: CanvasImageSource, w: number, h: number) {
  ctx.clearRect(0, 0, w, h);
  ctx.globalCompositeOperation = 'source-over';
  ctx.globalAlpha = 1;
  ctx.filter = `blur(${LENS_SPREAD}px)`;
  ctx.drawImage(bloom, 0, 0, w, h);
  ctx.drawImage(bloom, 0, 0, w, h); // twice: the spread light is faint, the dirt needs it at full strength
  ctx.filter = 'none';
  ctx.globalCompositeOperation = 'destination-in';
  ctx.drawImage(dirt, 0, 0, w, h);
  ctx.globalCompositeOperation = 'source-over';
  ctx.globalAlpha = GHOST_ALPHA;
  ctx.filter = `blur(${GHOST_BLUR}px)`;
  const gw = w * GHOST_SCALE, gh = h * GHOST_SCALE;
  ctx.drawImage(bloom, (w - gw) / 2, (h - gh) / 2, gw, gh);
  ctx.filter = 'none';
  ctx.globalAlpha = 1;
}
