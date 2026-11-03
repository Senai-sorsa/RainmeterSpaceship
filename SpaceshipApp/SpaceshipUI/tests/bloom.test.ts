import { describe, expect, it } from 'vitest';
import type { Op } from '../src/draw/canvas';
import { css, type RGBA } from '../src/lib/theme';
import { bloomEntries, dropBloom, postBloom } from '../src/draw/bloomBus';
import { paintOps, stackBlur, type Ctx2D } from '../src/draw/bloomPaint';
import { bloomMode } from '../src/draw/bloomMode';

// The quarter-res light canvas (tasks/hyperrealism-plan.md Task 2): the bus the OpsView anchors post to, and the painters
// that draw those ops onto a 2D context. A recording fake context stands in for the canvas.
type Call = [string, ...unknown[]];
function fakeCtx() {
  const calls: Call[] = [];
  const seen: Record<string, unknown[]> = {};
  const props: Record<string, unknown> = {
    fillStyle: '#000', strokeStyle: '#000', lineWidth: 1, font: '', textAlign: 'start', textBaseline: 'alphabetic',
    globalAlpha: 1, globalCompositeOperation: 'source-over', filter: 'none', lineCap: 'butt', lineJoin: 'miter',
  };
  const ctx = new Proxy({} as Record<string, unknown>, {
    get(_, k: string) {
      if (k in props) return props[k];
      return (...args: unknown[]) => { calls.push([k, ...args]); };
    },
    set(_, k: string, v) { props[k] = v; (seen[k] ??= []).push(v); return true; },
  });
  return { ctx: ctx as unknown as Ctx2D, calls, seen };
}
const COL: RGBA = [0, 210, 255, 128];
const ID = { a: 1, b: 0, c: 0, d: 1, e: 0, f: 0 };
const poly: Op = { shape: { kind: 'poly', pts: [[0, 0], [10, 0], [10, 5]], closed: false }, stroke: { color: COL, width: 3 } };

describe('light bus', () => {
  it('postBloom then dropBloom removes the entry', () => {
    postBloom('k', { ops: [poly], ctm: ID });
    expect(bloomEntries.value.has('k')).toBe(true);
    dropBloom('k');
    expect(bloomEntries.value.has('k')).toBe(false);
  });
  it('posting identical ops keeps the same map', () => {
    const ops = [poly];
    postBloom('same', { ops, ctm: { ...ID } });
    const before = bloomEntries.value;
    postBloom('same', { ops, ctm: { ...ID } });
    expect(bloomEntries.value).toBe(before);
    dropBloom('same');
  });
});

describe('paintOps', () => {
  it('scales the CTM to the canvas', () => {
    const { ctx, calls } = fakeCtx();
    paintOps(ctx, [{ ops: [poly], ctm: { a: 2, b: 0, c: 0, d: 2, e: 10, f: 20 } }], 0.25);
    expect(calls.find((c) => c[0] === 'setTransform')).toEqual(['setTransform', 0.5, 0, 0, 0.5, 2.5, 5]);
  });
  it('strokes a poly with the op colour and width', () => {
    const { ctx, calls, seen } = fakeCtx();
    paintOps(ctx, [{ ops: [poly], ctm: ID }], 1);
    expect(seen.strokeStyle).toContain(css(COL));
    expect(seen.lineWidth).toContain(3);
    expect(calls.some((c) => c[0] === 'stroke')).toBe(true);
  });
  it('draws glow text with the HUD font size', () => {
    const { ctx, calls, seen } = fakeCtx();
    const text: Op = { shape: { kind: 'text', x: 5, y: 6, text: 'CPU', size: 10, align: 'LeftTop', weight: 600, font: 'Rajdhani', blur: 4 }, fill: COL };
    paintOps(ctx, [{ ops: [text], ctm: ID }], 1);
    const font = String(seen.font?.at(-1));
    expect(font).toContain('px Rajdhani');
    expect(font).toContain(`${(10 * 4 / 3 * 1.14).toFixed(2)}px`);
    expect(calls.filter((c) => c[0] === 'fillText')).toHaveLength(1);
  });
  it('skips image ops', () => {
    const { ctx, calls } = fakeCtx();
    const img: Op = { shape: { kind: 'image', x: 0, y: 0, w: 4, h: 4, href: 'x.png', matrix: [] } };
    paintOps(ctx, [{ ops: [img], ctm: ID }], 1);
    expect(calls.some((c) => c[0] === 'drawImage')).toBe(false);
  });
});

describe('stackBlur', () => {
  it('draws three passes with growing radii', () => {
    const { ctx, calls, seen } = fakeCtx();
    stackBlur(ctx, {} as CanvasImageSource, 2);
    expect(seen.filter?.slice(0, 3)).toEqual(['blur(2px)', 'blur(6px)', 'blur(18px)']);
    expect(seen.globalAlpha?.slice(0, 3)).toEqual([0.6, 0.3, 0.15]);
    expect(calls.filter((c) => c[0] === 'drawImage')).toHaveLength(3);
    expect(seen.filter?.at(-1)).toBe('none');
    expect(seen.globalAlpha?.at(-1)).toBe(1);
  });
});

describe('bloomMode', () => {
  it('canvas on FULL by default, svg when asked, off below FULL', () => {
    expect(bloomMode(0, {})).toBe('canvas');
    expect(bloomMode(0, { BloomEngine: 'svg' })).toBe('svg');
    expect(bloomMode(1, {})).toBe('off');
    expect(bloomMode(3, {})).toBe('off');
  });
});

describe('light tiles (Task 4: cache each anchor\'s blurred light, rebuild only what changed)', () => {
  it('entryBounds covers the ops in canvas px, padded and clamped to the canvas', async () => {
    const { entryBounds } = await import('../src/draw/bloomPaint');
    const e = { ops: [poly], ctm: { a: 2, b: 0, c: 0, d: 2, e: 100, f: 40 } };
    // poly spans x 0..10, y 0..5 -> css 100..120, 40..50 -> canvas (x0.25) 25..30, 10..12.5; pad 4
    expect(entryBounds(e, 0.25, 4, 400, 300)).toEqual({ x: 21, y: 6, w: 13, h: 11 });
    expect(entryBounds({ ops: [poly], ctm: { a: 1, b: 0, c: 0, d: 1, e: -50, f: -50 } }, 1, 2, 400, 300)).toBeNull();
  });
  it('TileCache rebuilds only new or changed entries and drops removed ones', async () => {
    const { TileCache } = await import('../src/draw/bloomPaint');
    const built: string[] = [];
    const cache = new TileCache((key) => { built.push(key); return { key }; });
    const a = { ops: [poly], ctm: ID }, b = { ops: [poly], ctm: { ...ID, e: 5 } };
    cache.update(new Map([['a', a], ['b', b]]));
    cache.update(new Map([['a', a], ['b', b]]));
    expect(built).toEqual(['a', 'b']);
    cache.update(new Map([['a', a], ['b', { ...b }]]));
    expect(built).toEqual(['a', 'b', 'b']);
    cache.update(new Map([['b', b]]));
    expect([...cache.tiles.keys()]).toEqual(['b']);
  });
});
