import { describe, expect, it } from 'vitest';
import type { Style } from '../src/draw/canvas';
import { batteryFrame, type BatteryState } from '../src/modules/battery';
import { duration } from '../src/modules/readings';

// Fake readings and a fake clock only. Expected values are worked out from battery.lua. Zone 100 x 20.
const st: Style = {
  s: 1, tier: 2, glowA: 46, glowW: 3.2, coreWhite: 0, hudA: 255, edit: false,
  textGlow: 4, textGlowA: 150, textSmall: 1.85, textLarge: 1.45, fontText: 'Oxanium', fontNum: 'B612 Mono', fontTitle: 'Michroma',
  white: [215, 240, 255, 255], dim: [0, 110, 150, 255], panel: [0, 30, 45, 90], accent: [0, 210, 255, 255],
  warn: [255, 130, 40, 255], alert: [255, 60, 70, 255], text: [170, 235, 255, 255], hi: [255, 105, 135, 255], good: [60, 255, 170, 255],
};
const zone = { x: 0, y: 0, w: 100, h: 20 };
const fresh = (): BatteryState => ({ samples: [] });

describe('duration (H.duration)', () => {
  it('formats h:mm and reports no value as --:--', () => {
    expect(duration(12600)).toBe('3:30');
    expect(duration(0)).toBe('0:00');
    expect(duration(undefined)).toBe('--:--');
    expect(duration(-1)).toBe('--:--');
  });
});

describe('battery status (battery.lua)', () => {
  it('on AC, under the limit, with no estimate yet: CHG TO the limit', () => {
    const f = batteryFrame({ mAC: 1, mBattPct: 50 }, zone, st, fresh(), 0);
    expect(f.status).toBe('CHG TO 80%');
    expect(f.pct).toBe(50);
  });

  it('on AC, at the limit: HELD and the samples are cleared', () => {
    const state: BatteryState = { samples: [[0, 50]] };
    const f = batteryFrame({ mAC: 1, mBattPct: 80 }, zone, st, state, 10);
    expect(f.status).toBe('HELD 80%');
    expect(state.samples).toEqual([]);
  });

  it('uses the charge rate when HWiNFO gives capacity: 20 Wh to go at 2 W is 10:00', () => {
    // need = (0.8 * 50000 - 20000) / 1000 = 20; rate 2 => 10 h
    const f = batteryFrame({ mAC: 1, mBattPct: 40, mHwFullCap: 50000, mHwRemainCap: 20000, mHwChargeRate: 2 }, zone, st, fresh(), 0);
    expect(f.status).toBe('10:00 TO 80%');
  });

  it('estimates from two samples over a minute: 2% in 120 s is 28 min to 80%', () => {
    const state = fresh();
    batteryFrame({ mAC: 1, mBattPct: 50 }, zone, st, state, 0);
    const f = batteryFrame({ mAC: 1, mBattPct: 52 }, zone, st, state, 120);
    expect(f.status).toBe('0:28 TO 80%');
  });

  it('on battery: time left from the lifetime, or ON BATT when there is none', () => {
    expect(batteryFrame({ mAC: 0, mBattPct: 60, mLifetime: 12600 }, zone, st, fresh(), 0).status).toBe('3:30 LEFT');
    expect(batteryFrame({ mAC: 0, mBattPct: 60 }, zone, st, fresh(), 0).status).toBe('ON BATT');
  });
});

describe('battery bar', () => {
  it('readout is the percentage, two spaces, then the status', () => {
    const f = batteryFrame({ mAC: 0, mBattPct: 60, mLifetime: 12600 }, zone, st, fresh(), 0);
    const text = f.ops.find((o) => o.shape.kind === 'text' && o.shape.size < 9) as { shape: { text: string } };
    expect(text.shape.text).toBe('60%  3:30 LEFT');
  });

  it('colour: alert when on battery at or under the warn level, good on AC, highlight otherwise', () => {
    const colourOf = (r: Record<string, number>) => {
      const f = batteryFrame(r, zone, st, fresh(), 0);
      return f.ops.find((o) => o.stroke?.width === 2.6)?.stroke?.color;
    };
    expect(colourOf({ mAC: 0, mBattPct: 20, mLifetime: 1 })).toEqual(st.alert);
    expect(colourOf({ mAC: 1, mBattPct: 50 })).toEqual(st.good);
    expect(colourOf({ mAC: 0, mBattPct: 21, mLifetime: 1 })).toEqual(st.hi);
  });
});
