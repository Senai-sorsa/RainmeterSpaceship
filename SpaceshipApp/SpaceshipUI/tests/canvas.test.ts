import { describe, expect, it } from 'vitest';
import { arcPts, Canvas, mix, ramp, type Op, type Style } from '../src/draw/canvas';
import type { Pt } from '../src/lib/geometry';
import type { RGBA } from '../src/lib/theme';
import icons from '../src/generated/icons.json';

// Expected values are worked out by hand from Skins/Spaceship/@Resources/Scripts/lib.lua, not read back from the port.
const ACCENT: RGBA = [0, 210, 255, 255], DIM: RGBA = [0, 110, 150, 255], WARN: RGBA = [255, 130, 40, 255], ALERT: RGBA = [255, 60, 70, 255];

function style(over: Partial<Style> = {}): Style {
  return {
    s: 1, tier: 0, glowA: 46, glowW: 3.2, coreWhite: 0, hudA: 255, edit: false,
    white: [255, 255, 255, 255], dim: DIM, panel: [0, 30, 45, 90], accent: ACCENT, warn: WARN, alert: ALERT,
    ...over,
  };
}
const zone = { x: 0, y: 0, w: 100, h: 100 };

describe('coordinates', () => {
  it('offsets by the zone origin, then scales', () => {
    const c = new Canvas({ x: 100, y: 200, w: 50, h: 50 }, style({ s: 2 }));
    c.fillRect(10, 20, 5, 6, ACCENT, 255);
    const [op] = c.flush();
    expect(op.shape).toEqual({ kind: 'rect', x: 220, y: 440, w: 10, h: 12, r: 0 });
    expect(op.fill).toEqual([0, 210, 255, 255]);
  });
});

describe('neon glow tiers (lib.lua Canvas:neon)', () => {
  it('FULL draws a wide faint halo, a medium glow and the core', () => {
    const c = new Canvas(zone, style({ tier: 0 }));
    c.line(0, 0, 10, 0, ACCENT, 2);
    const ops = c.flush();
    expect(ops.map((o) => o.stroke?.width)).toEqual([2 * 3.2 * 2.1, 2 * 3.2, 2]);
    expect(ops[0].stroke?.color[3]).toBe(17); // floor(46 * 0.38)
    expect(ops[1].stroke?.color[3]).toBe(46);
    expect(ops[2].stroke?.color).toEqual(ACCENT);
  });

  it('LITE drops the outer halo', () => {
    const c = new Canvas(zone, style({ tier: 1 }));
    c.line(0, 0, 10, 0, ACCENT, 2);
    expect(c.flush().map((o) => o.stroke?.width)).toEqual([2 * 3.2, 2]);
  });

  it('LOW and STEALTH draw the core only', () => {
    for (const tier of [2, 3]) {
      const c = new Canvas(zone, style({ tier }));
      c.line(0, 0, 10, 0, ACCENT, 2);
      expect(c.flush().length).toBe(1);
    }
  });

  it('no glow at all when GlowAlpha is 0', () => {
    const c = new Canvas(zone, style({ glowA: 0 }));
    c.circle(0, 0, 5, ACCENT, 1);
    expect(c.flush().length).toBe(1);
  });
});

describe('colour', () => {
  it('HudAlpha scales every colour alpha once', () => {
    const c = new Canvas(zone, style({ hudA: 128 }));
    c.fillRect(0, 0, 1, 1, ACCENT, 255);
    expect(c.flush()[0].fill?.[3]).toBe(128);
  });

  it('CoreWhite pulls the core colour toward white with a floor per channel', () => {
    const c = new Canvas(zone, style({ coreWhite: 0.5 }));
    c.line(0, 0, 10, 0, ACCENT, 1);
    const core = c.flush().at(-1)!;
    expect(core.stroke?.color).toEqual([127, 232, 255, 255]);
  });

  it('ramp runs accent, then warn, then alert', () => {
    const st = style();
    expect(ramp(st, 0.5)).toEqual(ACCENT);
    expect(ramp(st, 0.7)).toEqual(ACCENT); // blend fraction 0: the breakpoints are exact
    expect(ramp(st, 0.9)).toEqual(WARN);
    expect(mix(ACCENT, WARN, 0.5)).toEqual([127, 170, 147, 255]); // 0.5 is exact; 0.75-style values hit float floor edges
    expect(mix(WARN, ALERT, 0.5)).toEqual([255, 95, 55, 255]);
  });
});

describe('layers and halo', () => {
  it('flush gives base, then glow, then core, then top', () => {
    const c = new Canvas(zone, style());
    c.line(0, 0, 10, 0, ACCENT, 1.6);
    c.fillRect(0, 0, 1, 1, DIM, 255);
    const ops = c.flush();
    expect(ops[0].fill).toBeDefined(); // base, even though it was drawn second
    expect(ops.slice(1).map((o) => o.stroke?.width)).toEqual([1.6 * 3.2 * 2.1, 1.6 * 3.2, 1.6]);
  });

  it('a bright dot gets three stacked halo discs before the disc', () => {
    const c = new Canvas(zone, style());
    c.dot(0, 0, 2, ACCENT, 255);
    const ops = c.flush();
    expect(ops.slice(0, 3).map((o) => (o.shape as { rx: number }).rx)).toEqual([2 * 3.7, 2 * 2.8, 2 * 1.9]);
    expect(ops.slice(0, 3).map((o) => o.fill?.[3])).toEqual([17, 23, 35]);
    expect(ops[3].fill).toEqual([0, 210, 255, 255]);
  });

  it('no halo on LOW', () => {
    const c = new Canvas(zone, style({ tier: 2 }));
    c.dot(0, 0, 2, ACCENT, 255);
    expect(c.flush().length).toBe(1);
  });
});

describe('shapes', () => {
  it('arcs use the lib.lua segment count: one per 6 degrees, at least 6', () => {
    const pts = arcPts(0, 0, 10, 10, 0, 90);
    expect(pts.length).toBe(16);
    expect(pts[0][0]).toBeCloseTo(10);
    expect(pts[0][1]).toBeCloseTo(0);
    expect(pts[15][0]).toBeCloseTo(0);
    expect(pts[15][1]).toBeCloseTo(10);
  });

  it('a dashed arc scales its dash and gap with the zone scale', () => {
    const c = new Canvas(zone, style({ s: 2 }));
    c.dashArc(0, 0, 10, 0, 90, ACCENT, 1, 255, 4, 2);
    const ops = c.flush();
    expect(ops.at(-1)!.stroke).toMatchObject({ width: 2, dash: [8, 4] });
    expect(ops[0].stroke).toMatchObject({ width: 1 * 1.8 * 2, dash: [8, 4] });
  });

  it('a segment bar lights round(v * n) segments and dims the rest', () => {
    const c = new Canvas(zone, style());
    c.segBar(0, 0, 10, 2, 0.5, 4);
    const fills = c.flush().map((o) => o.fill);
    expect(fills).toEqual([
      [0, 210, 255, 230], // ramp((0+1)/4) is accent below 0.7
      [0, 210, 255, 230],
      [0, 110, 150, 60],
      [0, 110, 150, 60],
    ]);
  });

  it('chamfer fills with the panel colour, not the line colour', () => {
    const c = new Canvas(zone, style());
    c.chamfer(0, 0, 10, 10, 2, ACCENT, 1, 255, 200);
    expect(c.flush()[0].fill).toEqual([0, 30, 45, 200]);
  });
});

describe('icons (lib.lua Canvas:icon)', () => {
  it('fits the 100 box to size and centres it on cx, cy', () => {
    const c = new Canvas(zone, style({ tier: 2 }));
    c.icon('gear', 10, 10, 50, ACCENT, 1);
    const [hub, body] = c.flush();
    expect(hub.shape).toEqual({ kind: 'ellipse', cx: 10, cy: 10, rx: 7, ry: 7 }); // gear hub 50,50 r14 at half size
    expect(body.shape).toMatchObject({ kind: 'poly', closed: true });
    expect((body.shape as { pts: Pt[] }).pts[0]).toEqual([7, -11]); // 44,8 in the box
  });

  it('an unknown name draws the gear', () => {
    const a = new Canvas(zone, style({ tier: 2 })), b = new Canvas(zone, style({ tier: 2 }));
    a.icon('no-such-icon', 50, 50, 100, ACCENT);
    b.icon('gear', 50, 50, 100, ACCENT);
    expect(a.flush()).toEqual(b.flush());
  });

  it('every icon in icons.json draws something', () => {
    for (const name of Object.keys(icons.icons)) {
      const c = new Canvas(zone, style());
      c.icon(name, 50, 50, 40, ACCENT, 1.2);
      expect(c.flush().length, name).toBeGreaterThan(0);
    }
  });
});

describe('edit mode', () => {
  it('adds an unscaled zone outline as the last op', () => {
    const c = new Canvas({ x: 10, y: 20, w: 30, h: 40 }, style({ s: 2, edit: true }));
    const outline: Op = c.flush().at(-1)!;
    expect(outline.shape).toEqual({ kind: 'rect', x: 20, y: 40, w: 60, h: 80, r: 0 });
    expect(outline.fill).toEqual([255, 200, 0, 18]);
    expect(outline.stroke).toEqual({ color: [255, 200, 0, 200], width: 2 });
  });
});
