import { describe, expect, it } from 'vitest';
import type { Style } from '../src/draw/canvas';
import { powerFrame } from '../src/modules/power';

// Fake sensor values only: no HWiNFO and no Rainmeter. Expected values are worked out from power.lua.
// Zone 100 x 20 gives y = 10, rail from x0 = 22 to x1 = 74 (zone.w - 26).
const st: Style = {
  s: 1, tier: 2, glowA: 46, glowW: 3.2, coreWhite: 0, hudA: 255, edit: false,
  textGlow: 4, textGlowA: 150, textSmall: 1.85, textLarge: 1.45, fontText: 'Oxanium',
  white: [215, 240, 255, 255], dim: [0, 110, 150, 255], panel: [0, 30, 45, 90], accent: [0, 210, 255, 255],
  warn: [255, 130, 40, 255], alert: [255, 60, 70, 255], text: [170, 235, 255, 255], hi: [255, 105, 135, 255],
};
const zone = { x: 0, y: 0, w: 100, h: 20 };
const textOf = (op: { shape: unknown }) => (op.shape as { text: string }).text;

describe('power draw (power.lua)', () => {
  it('with no reading: no hot segment, a W readout, and the HWiNFO hint', () => {
    const f = powerFrame({}, zone, st);
    expect(f.watts).toBe(0);
    expect(f.tip).toBe('Power draw needs HWiNFO: Control Center > SENSORS > DETECT');
    expect(f.ops.map(textOf).filter(Boolean)).toEqual(['P', 'W']);
    expect(f.ops.length).toBe(4); // rail, end tick, P, W
  });

  it('CPU plus GPU sets the hot segment: 100 W is 0.625 of the 160 W scale', () => {
    const f = powerFrame({ cpu: 40, gpu: 60 }, zone, st);
    expect(f.watts).toBe(100);
    expect(f.tip).toBe('CPU 40 W, GPU 60 W');
    const hot = f.ops[1];
    expect(hot.stroke?.color).toEqual([255, 105, 135, 255]);
    expect(hot.stroke?.width).toBe(2.6);
    const pts = (hot.shape as { pts: number[][] }).pts;
    expect(pts[1][0]).toBeCloseTo(22 + 52 * 0.625); // 54.5
    expect(f.ops.map(textOf).filter(Boolean)).toEqual(['P', '100W']);
  });

  it('a zero reading is a reading, not a missing one (Lua 0 is truthy)', () => {
    const f = powerFrame({ gpu: 0 }, zone, st);
    expect(f.watts).toBe(0);
    expect(f.tip).toBe('CPU -- W, GPU 0 W');
    expect(f.ops.map(textOf).filter(Boolean)).toEqual(['P', '0W']);
    expect(f.ops.length).toBe(4); // no hot segment at 0
  });

  it('falls back to battery discharge when no sensor reads', () => {
    const f = powerFrame({ chargeRate: -30 }, zone, st);
    expect(f.watts).toBe(30);
    expect(f.tip).toBe('CPU -- W, GPU -- W');
  });

  it('charging with no sensor reads is no draw', () => {
    const f = powerFrame({ chargeRate: 20 }, zone, st);
    expect(f.watts).toBe(0);
    expect(f.tip).toBe('Power draw needs HWiNFO: Control Center > SENSORS > DETECT');
  });

  it('clamps the bar at 160 W', () => {
    const f = powerFrame({ cpu: 400 }, zone, st);
    const pts = (f.ops[1].shape as { pts: number[][] }).pts;
    expect(pts[1][0]).toBe(74);
    expect(f.ops.map(textOf).filter(Boolean)).toEqual(['P', '400W']);
  });
});
