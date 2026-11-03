import { css } from '../lib/theme';
import { FONT_SCALE, type Op } from './canvas';
import type { BloomEntry } from './bloomBus';
import { PT_PX, textAlign } from './ops';

// Painters for the light canvas (tasks/hyperrealism-plan.md Task 2). Pure: they only call the context they are given,
// so the tests run them on a recording fake.

export type Ctx2D = Pick<CanvasRenderingContext2D, 'setTransform' | 'beginPath' | 'moveTo' | 'lineTo' | 'closePath' | 'ellipse'
  | 'rect' | 'fill' | 'stroke' | 'fillText' | 'save' | 'restore' | 'drawImage' | 'clearRect'> & {
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

/** Draws every entry's ops; scale is canvas px per CSS px (0.25 for the quarter-res canvas). Images are skipped. */
export function paintOps(ctx: Ctx2D, entries: Iterable<BloomEntry>, scale: number) {
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  for (const { ops, ctm } of entries) {
    ctx.setTransform(ctm.a * scale, ctm.b * scale, ctm.c * scale, ctm.d * scale, ctm.e * scale, ctm.f * scale);
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
    ctx.fillText(sh.text, sh.x, sh.y);
    return;
  }
  ctx.beginPath();
  if (sh.kind === 'poly') {
    sh.pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
    if (sh.closed) ctx.closePath();
  } else if (sh.kind === 'ellipse') ctx.ellipse(sh.cx, sh.cy, Math.abs(sh.rx), Math.abs(sh.ry), 0, 0, Math.PI * 2);
  else ctx.rect(sh.x, sh.y, sh.w, sh.h);
  if (fill) { ctx.fillStyle = css(fill); ctx.fill(); }
  if (op.stroke) { ctx.strokeStyle = css(op.stroke.color); ctx.lineWidth = op.stroke.width; ctx.stroke(); }
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
