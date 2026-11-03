import { describe, expect, it } from 'vitest';
import { Canvas, heat, HUD_SCAN, type Op, type Style } from '../src/draw/canvas';
import { HudDefs, OpsView } from '../src/draw/ops';
import { popupFrame } from '../src/draw/popup';
import type { RGBA } from '../src/lib/theme';

// The realism kit (tasks/line-art-realism-plan.md §4, K1-K4): gradient fills, the backlit display, the hot-core ramp
// and the shared screen texture. Behaviour checks, not op counts.
const ACCENT: RGBA = [0, 210, 255, 255];
function style(over: Partial<Style> = {}): Style {
  return {
    s: 1, tier: 0, glowA: 46, glowW: 3.2, coreWhite: 0.3, hudA: 255, edit: false,
    textGlow: 4, textGlowA: 150, textSmall: 1.85, textLarge: 1.45, fontText: 'Oxanium', fontNum: 'B612 Mono', fontTitle: 'Michroma',
    white: [255, 255, 255, 255], dim: [0, 110, 150, 255], panel: [0, 30, 45, 90], accent: ACCENT, warn: [255, 130, 40, 255],
    alert: [255, 60, 70, 255], text: [200, 240, 255, 255], hi: [255, 105, 135, 255], good: [60, 255, 170, 255],
    ...over,
  };
}
const zone = { x: 0, y: 0, w: 200, h: 100 };

describe('heat ramp (K3)', () => {
  it('burns towards white with the heat and keeps a trace of the hue', () => {
    const cool = heat(style(), ACCENT, 0), hot = heat(style(), ACCENT, 1);
    expect(cool).toEqual([140, 234, 255, 255]); // 55 % white: floor(255 * 0.55), floor(210 + 45 * 0.55)
    expect(hot).toEqual([191, 243, 255, 255]); // 75 % white
    expect(hot[0]).toBeGreaterThan(cool[0]);
  });
  it('keeps the colour when CoreWhite is 0 and keeps the input alpha', () => {
    expect(heat(style({ coreWhite: 0 }), [0, 210, 255, 90], 1)).toEqual([0, 210, 255, 90]);
    expect(heat(style(), [0, 210, 255, 90], 0.5)[3]).toBe(90);
  });
});

describe('gradient fills (K1)', () => {
  it('scales the gradient with the zone and tints its stops by HudAlpha', () => {
    const c = new Canvas({ x: 10, y: 20, w: 50, h: 50 }, style({ s: 2, hudA: 128 }));
    c.gradRect(0, 0, 10, 4, { kind: 'linear', x1: 0, y1: 0, x2: 10, y2: 0, stops: [[0, [0, 210, 255, 255]], [1.5, [255, 255, 255, 100]]] });
    const [op] = c.flush();
    expect(op.shape).toEqual({ kind: 'rect', x: 20, y: 40, w: 20, h: 8, r: 0 });
    expect(op.fill).toBeUndefined();
    expect(op.grad).toEqual({ kind: 'linear', x1: 20, y1: 40, x2: 40, y2: 40, stops: [[0, [0, 210, 255, 128]], [1, [255, 255, 255, 50]]] });
  });
  it('a radial gradient scales its radius', () => {
    const c = new Canvas(zone, style({ s: 1.5 }));
    c.gradPoly([[0, 0], [10, 0], [5, 8]], { kind: 'radial', cx: 4, cy: 4, r: 10, stops: [[0, ACCENT]] });
    expect(c.flush()[0].grad).toMatchObject({ kind: 'radial', cx: 6, cy: 6, r: 15 });
  });
  it('the view draws a gradient op with its own userSpaceOnUse gradient', () => {
    const op: Op = { shape: { kind: 'rect', x: 0, y: 0, w: 4, h: 4, r: 0 }, grad: { kind: 'linear', x1: 0, y1: 0, x2: 4, y2: 0, stops: [[0, [1, 2, 3, 51]]] } };
    const el = OpsView({ ops: [op], name: 'g' }).props.children[0];
    const frag = el.type(el.props);
    const [defs, shape] = frag.props.children;
    const grad = defs.props.children.type(defs.props.children.props);
    expect(grad.type).toBe('linearGradient');
    expect(grad.props.id).toBe('gr-g-0');
    expect(grad.props.gradientUnits).toBe('userSpaceOnUse');
    expect(grad.props.children[0].props['stop-opacity']).toBeCloseTo(0.2);
    expect(shape.props.fill).toBe('url(#gr-g-0)');
  });
  it('plain ops still draw as before (one svg element, solid fill)', () => {
    const op: Op = { shape: { kind: 'rect', x: 0, y: 0, w: 4, h: 4, r: 0 }, fill: [1, 2, 3, 255] };
    const el = OpsView({ ops: [op], name: 'p' }).props.children[0];
    const out = el.type(el.props);
    expect(out.type).toBe('rect');
    expect(out.props.fill).toBe('rgb(1,2,3)');
  });
});

describe('screen texture (K4)', () => {
  it('is one static pattern, faint enough to keep text crisp', () => {
    const pat = HudDefs().props.children;
    expect(pat.type).toBe('pattern');
    expect(pat.props.id).toBe(HUD_SCAN);
    expect(Number(pat.props.children.props['fill-opacity'])).toBeLessThanOrEqual(0.05);
  });
});

describe('screen bezels (12 #11): the readouts sit in the hull', () => {
  const draw = (tier: number, bezel: boolean) => { const c = new Canvas(zone, style({ tier, bezel })); c.screen(10, 10, 100, 40, { from: 'bottom', lit: 1 }); return c.flush(); };
  const outside = (o: Op) => o.shape.kind === 'poly' && o.shape.pts.some(([x, y]) => x < 10 || x > 110 || y < 10 || y > 50);
  it('FULL and LITE: a dark recess round the body, drawn under it, and a faint lip below, never glowing', () => {
    for (const tier of [0, 1]) {
      const ops = draw(tier, true);
      const recess = ops.find((o) => outside(o) && o.shape.kind === 'poly' && o.shape.closed)!;
      expect(recess.stroke!.color.slice(0, 3)).toEqual([0, 0, 0]);
      expect(ops.indexOf(recess)).toBeLessThan(ops.findIndex((o) => o.grad));
      const lip = ops.find((o) => outside(o) && o.shape.kind === 'poly' && !o.shape.closed)!;
      expect(lip.shape.kind === 'poly' && lip.shape.pts.every(([, y]) => y > 50)).toBe(true);
      expect(lip.stroke!.color[3]).toBeLessThanOrEqual(60);
      expect(ops.filter(outside).every((o) => !o.bloom)).toBe(true);
    }
  });
  it('LOW and STEALTH, or the setting off: nothing outside the body', () => {
    for (const tier of [2, 3]) expect(draw(tier, true).filter(outside)).toEqual([]);
    expect(draw(0, false).filter(outside).filter((o) => !o.bloom)).toEqual([]);
  });
});

describe('pop-up bezels (12 #22): the pop-ups share the screens hardware look', () => {
  const draw = (tier: number, bezel: boolean) => { const c = new Canvas(zone, style({ tier, bezel })); popupFrame(c, style({ tier, bezel }), 100, 60, 20, 10, 20, 20); return c.flush(); };
  const outside = (o: Op) => o.shape.kind === 'poly' && o.shape.pts.some(([x, y]) => x < 19 || x > 121 || y < 19 || y > 81);
  it('FULL and LITE: a dark recess round the panel, under it, and a faint lip on its lower edge', () => {
    for (const tier of [0, 1]) {
      const ops = draw(tier, true);
      const recess = ops.find((o) => outside(o) && o.shape.kind === 'poly' && o.shape.closed && o.stroke && !o.bloom)!;
      expect(recess.stroke!.color.slice(0, 3)).toEqual([0, 0, 0]);
      expect(ops.indexOf(recess)).toBeLessThan(ops.findIndex((o) => o.fill && o.shape.kind === 'poly' && o.shape.closed));
      const lip = ops.find((o) => outside(o) && o.shape.kind === 'poly' && !o.shape.closed && !o.bloom)!;
      expect(lip.shape.kind === 'poly' && lip.shape.pts.every(([, y]) => y > 80)).toBe(true);
    }
  });
  it('LOW, STEALTH or the setting off: no bezel', () => {
    for (const [tier, b] of [[2, true], [3, true], [0, false]] as const) expect(draw(tier, b).filter((o) => outside(o) && !o.bloom && o.stroke?.color[0] === 0 && o.stroke.color[1] === 0)).toEqual([]);
  });
});

describe('backlit display (K2) by tier', () => {
  const draw = (tier: number, opts = {}) => { const c = new Canvas(zone, style({ tier })); c.screen(10, 10, 100, 40, opts); return c.flush(); };

  it('FULL: gradient body lit from the chosen edge, texture, bright edge, inner border and a bloomed outer glow', () => {
    const ops = draw(0, { from: 'bottom', lit: 1 });
    const body = ops.find((o) => o.grad)!;
    expect(body.grad).toMatchObject({ kind: 'linear', y1: 50, y2: 10 }); // brightest at the bottom edge
    expect(body.grad!.stops[0][1][3]).toBeGreaterThan(body.grad!.stops[2][1][3]);
    expect(ops.some((o) => o.pattern === HUD_SCAN)).toBe(true);
    expect(ops.some((o) => o.bloom && o.stroke)).toBe(true);
    const edge = ops.find((o) => o.shape.kind === 'poly' && !o.shape.closed)!;
    expect(edge.shape).toMatchObject({ pts: [[10, 50], [110, 50]] });
  });
  it('LITE drops the glow but keeps the gradient and texture', () => {
    const ops = draw(1);
    expect(ops.some((o) => o.grad)).toBe(true);
    expect(ops.some((o) => o.pattern)).toBe(true);
    expect(ops.some((o) => o.bloom)).toBe(false);
  });
  it('LOW and STEALTH: a flat body and the inner border only', () => {
    for (const t of [2, 3]) {
      const ops = draw(t);
      expect(ops.some((o) => o.grad || o.pattern || o.bloom)).toBe(false);
      expect(ops.filter((o) => o.fill)).toHaveLength(1);
    }
  });
  it('texture and glow can be turned off', () => {
    const ops = draw(0, { texture: false, glow: false });
    expect(ops.some((o) => o.pattern || o.bloom)).toBe(false);
  });
  it('a corner cut makes a six-point body', () => {
    const body = draw(0, { cut: 8 }).find((o) => o.grad)!;
    expect(body.shape.kind === 'poly' && body.shape.pts.length).toBe(6);
  });
});

describe('R2 adoption: telemetry cells and rails', async () => {
  const { graphFrame, graphState } = await import('../src/modules/graph');
  const { powerFrame } = await import('../src/modules/power');
  it('a telemetry cell sits on a lit display and its history area is a gradient that fades to the floor', () => {
    const g = graphState('cpu');
    let ops: Op[] = [];
    for (const v of [10, 40, 60]) ops = graphFrame(g, { mCPU: v } as never, { x: 0, y: 0, w: 120, h: 40 }, style({ tier: 0 }), 'fixed').ops;
    expect(ops.some((o) => o.pattern === HUD_SCAN)).toBe(true);
    const area = ops.filter((o) => o.grad && o.shape.kind === 'poly' && o.grad.kind === 'linear' && o.grad.y2 > o.grad.y1);
    const fades = area.find((o) => o.grad!.stops[0][1][3] > o.grad!.stops[o.grad!.stops.length - 1][1][3] && o.grad!.stops[0][1][0] === ACCENT[0]);
    expect(fades).toBeDefined();
  });
  it('the rail fill is a gradient bar that ends at the value, brightest at its leading end', () => {
    const ops = powerFrame({ cpu: 40, gpu: 60 }, { x: 0, y: 0, w: 100, h: 20 }, style({ tier: 0 })).ops;
    const bar = ops.find((o) => o.grad && o.shape.kind === 'rect' && o.grad.kind === 'linear' && o.grad.x2 > o.grad.x1)!;
    expect(bar.shape.kind === 'rect' && bar.shape.x + bar.shape.w).toBeCloseTo(22 + 52 * 0.625);
    const st = bar.grad!.stops;
    expect(st[st.length - 1][1][3]).toBeGreaterThan(st[0][1][3]);
  });
});

describe('R3 adoption: rows and blocks', async () => {
  const { slotRowFrame } = await import('../src/modules/slot');
  it('a running app row is a textured lit plate with a filled status lamp in the good colour', () => {
    const st = style({ tier: 0 });
    const ops = slotRowFrame({ app: { id: 'x', name: 'X', short: 'X', icon: 'gear', missing: false } as never, state: 2, mirror: false }, { x: 0, y: 0, w: 400, h: 110 }, st);
    expect(ops.some((o) => o.pattern === HUD_SCAN)).toBe(true);
    expect(ops.some((o) => o.shape.kind === 'rect' && o.fill?.[1] === st.good[1] && o.fill?.[0] === st.good[0] && o.shape.h === 8)).toBe(true);
  });
  it('LOW keeps the rows free of texture', () => {
    const ops = slotRowFrame({ state: 0, mirror: true }, { x: 0, y: 0, w: 400, h: 110 }, style({ tier: 2 }));
    expect(ops.some((o) => o.pattern)).toBe(false);
  });
});

describe('R5: hot bloom (K5) and hull spill (K6)', async () => {
  const { spillBackground } = await import('../src/ui/spill');
  it('hot bloom is FULL only, blurred about three times wider than the glow, and grouped ahead of it', () => {
    const full = new Canvas(zone, style({ tier: 0 }));
    full.line(0, 0, 10, 0, ACCENT, 2);
    full.hotDot(5, 5, 2, ACCENT);
    const ops = full.flush(), blooms = ops.filter((o) => o.bloom).map((o) => o.bloom!);
    expect(ops[0].bloom).toBeCloseTo(Math.max(...blooms));
    expect(Math.max(...blooms) / Math.min(...blooms)).toBeCloseTo(3);
    for (const t of [1, 2, 3]) {
      const c = new Canvas(zone, style({ tier: t }));
      c.hotDot(5, 5, 2, ACCENT); c.hot([[0, 0], [9, 9]], ACCENT);
      expect(c.flush()).toHaveLength(0);
    }
  });
  it('spill: one pool per lit feature, none for hidden zones, none on LOW and STEALTH', () => {
    const all = spillBackground('rgb(0,210,255)', 0);
    expect(all.split('radial-gradient').length - 1).toBe(11);
    expect(spillBackground('rgb(0,210,255)', 1, 'C_sphere,B_audio').split('radial-gradient').length - 1).toBe(9);
    expect(spillBackground('rgb(0,210,255)', 2)).toBe('');
    expect(spillBackground('rgb(0,210,255)', 3)).toBe('');
  });
});

describe('R11: fringe (K7) and shimmer (K9)', () => {
  const texts = (ops: Op[]) => ops.filter((o) => o.shape.kind === 'text' && !(o.shape as { blur: number }).blur);
  it('large text on FULL gets a faint red copy left and blue copy right, under the letters; LITE and small text do not', () => {
    const c = new Canvas(zone, style({ tier: 0, s: 2 }));
    c.text(50, 10, '42', { size: 15 });
    const [r, b, main] = texts(c.flush());
    expect(r.shape.kind === 'text' && r.shape.x).toBeCloseTo(99.4); // 0.6 device px left of 100
    expect(b.shape.kind === 'text' && b.shape.x).toBeCloseTo(100.6);
    expect(r.fill![0]).toBeGreaterThan(r.fill![2]);
    expect(b.fill![2]).toBeGreaterThan(b.fill![0]);
    expect(r.fill![3]).toBeLessThan(50);
    expect(main.shape.kind === 'text' && main.shape.x).toBe(100);
    const lite = new Canvas(zone, style({ tier: 1 })); lite.text(0, 0, '42', { size: 15 });
    expect(texts(lite.flush())).toHaveLength(1);
    const small = new Canvas(zone, style({ tier: 0 })); small.text(0, 0, 'cpu', { size: 8 });
    expect(texts(small.flush())).toHaveLength(1);
  });
  it('a shimmer readout carries its value key on FULL only, and the view remounts it when the value changes', () => {
    const draw = (tier: number, v: string) => { const c = new Canvas(zone, style({ tier })); c.text(0, 0, v, { size: 6, shimmer: v }); return c.flush(); };
    expect(draw(0, '44%').every((o) => o.shimmer === '44%')).toBe(true);
    expect(draw(1, '44%').some((o) => o.shimmer)).toBe(false);
    const keyOf = (v: string) => OpsView({ ops: draw(0, v), name: 's' }).props.children.map((e: { key: string }) => e.key);
    expect(keyOf('44%')).not.toEqual(keyOf('45%'));
    expect(OpsView({ ops: draw(0, '44%'), name: 's' }).props.children[0].props.class).toBe('shimmer');
  });
});
