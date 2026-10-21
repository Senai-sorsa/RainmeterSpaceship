import { describe, expect, it } from 'vitest';
import { compact, driveText, nextPeak, PEAK0, percentText, ssdText, usedShare } from '../src/modules/storage';
import { level, rateShort } from '../src/modules/strip';
import { offsetText, spanText, weekOf, yearProgress } from '../src/modules/panels';

describe('storage data', () => {
  it('reads the used share and the drive text', () => {
    expect(usedShare(100, 25)).toBeCloseTo(0.75);
    expect(usedShare(0, 0)).toBe(0);
    expect(driveText(931 * 1073741824, 519 * 1073741824)).toBe('412/931G');
  });

  it('compacts sizes without spaces and decays the activity peak', () => {
    expect(compact(1572864)).toBe('1.5MB');
    expect(nextPeak(PEAK0, 0, 0)).toBeCloseTo(PEAK0 * 0.98);
    expect(nextPeak(0, 0, 0)).toBe(1048576);
  });

  it('shows -- for a missing SSD sensor and truncates the percent', () => {
    expect(ssdText(undefined)).toBe('--');
    expect(ssdText(41.6)).toBe('42C');
    expect(percentText(0.879)).toBe('87');
  });
});

describe('strip data', () => {
  it('gives warn inside the margin and alert over the limit', () => {
    expect(level(92, 92, 5)).toBe(2);
    expect(level(88, 92, 5)).toBe(1);
    expect(level(80, 92, 5)).toBe(0);
    expect(level(undefined, 92, 5)).toBe(0);
  });

  it('compacts the per-second rate for a cell', () => {
    expect(rateShort(820)).toBe('820B/s');
    expect(rateShort(4200)).toBe('4.1KB/s');
    expect(rateShort(47 * 1024)).toBe('47KB/s');
    expect(rateShort(312 * 1024 * 1024)).toBe('312MB/s');
  });
});

describe('panels data', () => {
  it('numbers the week and day of the year, Monday weeks', () => {
    expect(weekOf(new Date(2026, 9, 21, 12))).toEqual({ week: 43, yday: 294 });
  });

  it('gives the year progress for the day', () => {
    expect(Math.floor(yearProgress(new Date(2026, 9, 21, 12)))).toBe(80);
  });

  it('formats the offset and the spans', () => {
    expect(offsetText(180)).toBe('UTC+03:00');
    expect(offsetText(-330)).toBe('UTC-05:30');
    expect(spanText(0)).toBe('0 S');
    expect(spanText(125)).toBe('2:05');
    expect(spanText(7440)).toBe('2:04 H');
    expect(spanText(3 * 86400 + 4 * 3600 + 20 * 60)).toBe('3D 04:20');
  });
});
