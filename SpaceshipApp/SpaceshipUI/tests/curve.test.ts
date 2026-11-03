import { describe, expect, it } from 'vitest';
import { Canvas, type Style } from '../src/draw/canvas';
import { bendFor, warpPoly } from '../src/draw/curve';
import { styleFrom } from '../src/modules/style';

const st = (over: Partial<Style> = {}): Style => ({ ...styleFrom({}), s: 1, tier: 0, ...over });
const Z = { id: 'T_test', x: 0, y: 0, w: 200, h: 40 };

describe('bendFor', () => {
  it('is undefined for a zone with no sag (or none in the table)', () => {
    expect(bendFor('nope', Z, { zones: {} })).toBeUndefined();
    expect(bendFor('T_test', Z, { zones: { T_test: 0 } })).toBeUndefined();
  });
  it('keeps the ends and moves the middle by the sag', () => {
    const w = bendFor('T_test', Z, { zones: { T_test: 10 } })!;
    expect(w([0, 5])).toEqual([0, 5]);
    expect(w([200, 5])).toEqual([200, 5]);
    expect(w([100, 5])).toEqual([100, 15]);
  });
});

describe('Canvas with a warp', () => {
  const sag = { zones: { T_test: 10 } };
  it('turns a wide rect into a poly whose middle top point is 10 lower than its ends', () => {
    const c = new Canvas(Z, st({ curve: sag }));
    c.fillRect(0, 0, 200, 10, [255, 255, 255, 255]);
    const [op] = c.flush();
    expect(op.shape.kind).toBe('poly');
    const pts = (op.shape as { pts: [number, number][] }).pts;
    const topAt = (x: number) => Math.min(...pts.filter(([px]) => px === x).map(([, y]) => y));
    expect([topAt(0), topAt(100), topAt(200)]).toEqual([0, 10, 0]);
  });
  it('splits a long line so it bends, and moves text only in y', () => {
    const c = new Canvas(Z, st({ curve: sag }));
    c.poly([[0, 0], [200, 0]], [255, 255, 255, 255]);
    c.text(100, 0, 'x', { glow: false });
    const ops = c.flush();
    const line = ops.find((o) => o.shape.kind === 'poly')!.shape as { pts: [number, number][] };
    expect(line.pts.length).toBeGreaterThan(3);
    expect(Math.max(...line.pts.map(([, y]) => y))).toBeCloseTo(10, 5);
    const t = ops.find((o) => o.shape.kind === 'text')!.shape as { x: number; y: number };
    expect([t.x, t.y]).toEqual([100, 10]);
  });
  it('leaves everything alone without a table entry', () => {
    const c = new Canvas({ ...Z, id: 'other' }, st({ curve: sag }));
    c.fillRect(0, 0, 200, 10, [255, 255, 255, 255]);
    expect(c.flush()[0].shape.kind).toBe('rect');
  });
});

it('warpPoly splits long segments', () => {
  expect(warpPoly([[0, 0], [300, 0]], ([x, y]) => [x, y]).length).toBeGreaterThan(4);
});

describe('HullRender gate', () => {
  it('only HullRender=1 gives the Style a curve table; 0 and unset never bend', () => {
    expect(styleFrom({}).curve).toBeUndefined();
    expect(styleFrom({ HullRender: '0' }).curve).toBeUndefined();
    expect(styleFrom({ HullRender: '1' }).curve).toBeDefined();
  });
  it('a HullRender=0 Canvas leaves a wide rect as a rect', () => {
    const c = new Canvas(Z, styleFrom({ HullRender: '0' }));
    c.fillRect(0, 0, 200, 4, [255, 255, 255, 255]);
    expect(c.flush().every((o) => o.shape.kind !== 'poly')).toBe(true);
  });
});
