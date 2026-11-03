import { describe, expect, it } from 'vitest';
import type { Op } from '../src/draw/canvas';
import { css, type RGBA } from '../src/lib/theme';
import { bloomEntries, dropBloom, postBloom } from '../src/draw/bloomBus';
import { BLOOM_STACK, HAZE_STACK, paintOps, paintTile, stackBlur, type Ctx2D } from '../src/draw/bloomPaint';
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
  it('spreads the light wide for the dirt and blurs the ghost so no text survives in it', async () => {
    const { paintGlass, LENS_SPREAD, GHOST_BLUR } = await import('../src/draw/bloomPaint');
    const { ctx, seen } = fakeCtx();
    paintGlass(ctx, {} as CanvasImageSource, {} as CanvasImageSource, 400, 300);
    expect(seen.filter?.slice(0, 3)).toEqual([`blur(${LENS_SPREAD}px)`, 'none', `blur(${GHOST_BLUR}px)`]);
    expect(seen.filter?.at(-1)).toBe('none');
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

describe('glass layer (Task 6)', () => {
  it('composites dirt into the light, then adds the ghost', async () => {
    const { paintGlass, GHOST_SCALE } = await import('../src/draw/bloomPaint');
    const { ctx, calls, seen } = fakeCtx();
    paintGlass(ctx, {} as CanvasImageSource, {} as CanvasImageSource, 400, 300);
    expect(seen.globalCompositeOperation?.slice(0, 3)).toEqual(['source-over', 'destination-in', 'source-over']);
    const draws = calls.filter((c) => c[0] === 'drawImage');
    expect(draws).toHaveLength(4); // spread light twice, dirt, ghost
    expect(draws[3][4]).toBeCloseTo(400 * GHOST_SCALE); // [name, image, x, y, w, h]
    expect(GHOST_SCALE).toBe(1.035);
    expect(seen.globalCompositeOperation?.at(-1)).toBe('source-over');
    expect(seen.globalAlpha?.at(-1)).toBe(1);
  });
});

describe('TileCache rate cap', () => {
  it('keeps a tile rebuilt less than minMs ago and reports the wait', async () => {
    const { TileCache } = await import('../src/draw/bloomPaint');
    let now = 0;
    const built: number[] = [];
    const cache = new TileCache(() => { built.push(now); return {}; }, 100, () => now);
    const e = (x: number) => new Map([['a', { ops: [poly], ctm: { ...ID, e: x } }]]);
    expect(cache.update(e(1))).toBe(0);
    now = 40;
    expect(cache.update(e(2))).toBe(60); // too soon: old tile kept, retry in 60 ms
    now = 100;
    expect(cache.update(e(3))).toBe(0);
    expect(built).toEqual([0, 100]);
  });
});

describe('paintOps keeps the SVG look (final review)', () => {
  it('clips clipped text to its box, as the SVG does', () => {
    const { ctx, calls } = fakeCtx();
    const t: Op = { shape: { kind: 'text', x: 10, y: 20, text: 'DENTIST APPOINTMENT AND A LONG NAME', size: 8, align: 'LeftCenter', weight: 600, font: 'Rajdhani', blur: 4, clipW: 50 }, fill: COL };
    paintOps(ctx, [{ ops: [t], ctm: ID }], 1);
    const names = calls.map((c) => c[0]);
    expect(names).toContain('clip');
    expect(names.indexOf('clip')).toBeLessThan(names.indexOf('fillText'));
    const r = calls.find((c) => c[0] === 'rect')!;
    expect(r[1]).toBe(10);
    expect(r[3]).toBe(50);
    expect(names.lastIndexOf('restore')).toBeGreaterThan(names.indexOf('fillText'));
  });
  it('draws dashed glow dashed', () => {
    const { ctx, calls } = fakeCtx();
    const d: Op = { shape: { kind: 'poly', pts: [[0, 0], [40, 0]], closed: false }, stroke: { color: COL, width: 2, dash: [3, 5] } };
    paintOps(ctx, [{ ops: [d, poly], ctm: ID }], 1);
    const dashes = calls.filter((c) => c[0] === 'setLineDash').map((c) => c[1]);
    expect(dashes).toEqual([[3, 5], []]);
  });
});

describe('paintOps rounded rects (deferred minor)', () => {
  it('glows a rounded rect with rounded corners, as the SVG rx draws it', () => {
    const { ctx, calls } = fakeCtx();
    const r: Op = { shape: { kind: 'rect', x: 2, y: 3, w: 40, h: 10, r: 4 }, fill: COL };
    paintOps(ctx, [{ ops: [r], ctm: ID }], 1);
    expect(calls.find((c) => c[0] === 'roundRect')).toEqual(['roundRect', 2, 3, 40, 10, 4]);
    expect(calls.some((c) => c[0] === 'rect')).toBe(false);
  });
  it('keeps square rects on rect()', () => {
    const { ctx, calls } = fakeCtx();
    paintOps(ctx, [{ ops: [{ shape: { kind: 'rect', x: 0, y: 0, w: 5, h: 5, r: 0 }, fill: COL }], ctm: ID }], 1);
    expect(calls.some((c) => c[0] === 'rect')).toBe(true);
    expect(calls.some((c) => c[0] === 'roundRect')).toBe(false);
  });
});

describe('depth haze (K8): far light is softer, at the same cost', () => {
  const run = (far: boolean) => {
    const { ctx, calls, seen } = fakeCtx();
    paintTile(ctx, {} as CanvasImageSource, 2, far);
    return { draws: calls.filter((c) => c[0] === 'drawImage').length, filters: seen.filter, alphas: seen.globalAlpha };
  };
  it('a near tile is the bloom stack plus the half-strength core', () => {
    const t = run(false);
    expect(t.draws).toBe(BLOOM_STACK.length + 1);
    expect(t.alphas).toEqual([...BLOOM_STACK.map(([, a]) => a), 1, 0.5, 1]);
  });
  it('a far tile uses the same radii and pass count, with the weight moved to the wide passes and a fainter core', () => {
    const near = run(false), far = run(true);
    expect(far.draws).toBe(near.draws);
    expect(far.filters).toEqual(near.filters);
    expect(HAZE_STACK.map(([m]) => m)).toEqual(BLOOM_STACK.map(([m]) => m));
    expect(HAZE_STACK[0][1]).toBeLessThan(BLOOM_STACK[0][1]);
    expect(HAZE_STACK[2][1]).toBeGreaterThan(BLOOM_STACK[2][1]);
    expect(far.alphas!.at(-2)).toBeLessThan(0.5);
  });
  it('the bus treats a change of far as a change', () => {
    const ops = [poly];
    postBloom('far', { ops, ctm: ID });
    const before = bloomEntries.value;
    postBloom('far', { ops, ctm: ID, far: true });
    expect(bloomEntries.value).not.toBe(before);
    expect(bloomEntries.value.get('far')!.far).toBe(true);
    dropBloom('far');
  });
});
