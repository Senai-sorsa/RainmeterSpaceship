import { describe, expect, it } from 'vitest';
import type { Style } from '../src/draw/canvas';
import { alertFrame, alertList } from '../src/modules/alert';

// Fake readings only. Expected values are worked out from alert.lua. Zone 100 x 20.
const st: Style = {
  s: 1, tier: 0, glowA: 46, glowW: 3.2, coreWhite: 0, hudA: 255, edit: false,
  textGlow: 4, textGlowA: 150, textSmall: 1.85, textLarge: 1.45, fontText: 'Oxanium', fontNum: 'B612 Mono', fontTitle: 'Michroma',
  white: [215, 240, 255, 255], dim: [0, 110, 150, 255], panel: [0, 30, 45, 90], accent: [0, 210, 255, 255],
  warn: [255, 130, 40, 255], alert: [255, 60, 70, 255], text: [170, 235, 255, 255], hi: [255, 105, 135, 255], good: [60, 255, 170, 255],
};
const zone = { x: 0, y: 0, w: 100, h: 20 };
const calm = { mHwCpuTemp: 50, mHwGpuTemp: 50, mDiskTotal: 100, mDiskFree: 50, mAC: 1, mBattPct: 90, mCPU: 10 };

describe('alert list (alert.lua alerts)', () => {
  it('is empty when nothing is over its threshold', () => {
    expect(alertList(calm)).toEqual([]);
  });

  it('lists each condition with its printed value, in the Lua order', () => {
    const list = alertList({
      mHwCpuTemp: 93, mHwGpuTemp: 86, mDiskTotal: 100, mDiskFree: 5, mAC: 0, mBattPct: 15, mCPU: 96,
    });
    expect(list).toEqual(['CPU HOT 93 C', 'GPU HOT 86 C', 'C: 95% FULL', 'BATTERY 15%', 'CPU SATURATED']);
  });

  it('thresholds are inclusive (>= and <=)', () => {
    expect(alertList({ mHwCpuTemp: 92 })).toEqual(['CPU HOT 92 C']);
    expect(alertList({ mAC: 0, mBattPct: 20 })).toEqual(['BATTERY 20%']);
  });

  it('a missing sensor raises no alert, and a missing AC reading counts as on AC', () => {
    expect(alertList({ mAC: 0 })).toEqual([]); // battery defaults to 100, so no battery alert
    expect(alertList({ mBattPct: 5 })).toEqual([]); // AC defaults to 1
  });

  it('a disk with no size reports nothing', () => {
    expect(alertList({ mDiskTotal: 0, mDiskFree: 0 })).toEqual([]);
  });
});

describe('alert frame', () => {
  it('count and tip join the alerts with the Lua separator', () => {
    const f = alertFrame({ mHwCpuTemp: 93, mCPU: 96 }, zone, st, { blink: 0 });
    expect(f.count).toBe(2);
    expect(f.tip).toBe('CPU HOT 93 C  |  CPU SATURATED');
    expect(alertFrame(calm, zone, st, { blink: 0 }).tip).toBe('');
  });

  it('blinks to alpha 130 on every other frame while there are alerts (FULL)', () => {
    const state = { blink: 0 };
    const alphas = [1, 2, 3].map(() => {
      const f = alertFrame({ mCPU: 96 }, zone, st, state);
      return f.ops.find((o) => o.stroke?.color[3] !== undefined && o.stroke.width === 2)?.stroke?.color[3];
    });
    expect(alphas).toEqual([130, 255, 130]);
  });

  it('never blinks without alerts', () => {
    const state = { blink: 0 };
    const f = alertFrame(calm, zone, st, state);
    expect(f.ops.some((o) => o.stroke?.color[3] === 130)).toBe(false);
  });

  it('never blinks on LOW or STEALTH', () => {
    const state = { blink: 0 };
    const f = alertFrame({ mCPU: 96 }, zone, { ...st, tier: 2 }, state);
    expect(f.ops.some((o) => o.stroke?.color[3] === 130)).toBe(false);
  });
});
