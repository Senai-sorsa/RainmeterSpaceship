import { signal } from '@preact/signals';
import { describe, expect, it } from 'vitest';
import { perfTier, startPerfTier, tierState, tierStep, wanted } from '../src/host/perfTier';
import type { SystemMetrics } from '../src/host/systemMetrics';

const AUTO = { PerfOverride: '-1' };

describe('wanted (controller.lua)', () => {
  it('goes up at the thresholds, down 15 below them, and is floored on battery', () => {
    expect(wanted(49, true, AUTO)).toEqual([0, 1]); // down 1: Lite holds until the load is under 35
    expect(wanted(80, true, AUTO)).toEqual([2, 3]);
    expect(wanted(30, true, AUTO)).toEqual([0, 0]);
    expect(wanted(90, true, AUTO)).toEqual([3, 3]);
    expect(wanted(10, false, AUTO)).toEqual([1, 1]);
    expect(wanted(10, false, { ...AUTO, BatteryMinTier: '0' })).toEqual([0, 0]);
  });
});

describe('tierStep', () => {
  it('an override forces its tier at once', () => {
    const s = tierState();
    expect(tierStep(s, 99, true, { PerfOverride: '2' }, 0)).toBe(2);
    expect(tierStep(s, 99, true, {}, 1)).toBe(2); // a missing setting means Auto, as in the skin; the hold starts again
  });
  it('Auto goes up after 5 s and down one step after 20 s', () => {
    const s = tierState();
    expect(tierStep(s, 90, true, AUTO, 0)).toBe(0);
    expect(tierStep(s, 90, true, AUTO, 4)).toBe(0);
    expect(tierStep(s, 90, true, AUTO, 5)).toBe(3);
    expect(tierStep(s, 10, true, AUTO, 6)).toBe(3);
    expect(tierStep(s, 10, true, AUTO, 26)).toBe(2);
    expect(tierStep(s, 10, true, AUTO, 27)).toBe(2); // the next step needs its own 20 s
    expect(tierStep(s, 10, true, AUTO, 47)).toBe(1);
  });
  it('a spike shorter than the hold changes nothing', () => {
    const s = tierState();
    tierStep(s, 90, true, AUTO, 0);
    tierStep(s, 10, true, AUTO, 3);
    expect(tierStep(s, 90, true, AUTO, 6)).toBe(0);
  });
});

describe('startPerfTier', () => {
  it('steps on each reading and stops', () => {
    const m = signal<SystemMetrics | null>(null);
    const v = signal<Record<string, string>>({ PerfOverride: '1' });
    const stop = startPerfTier(m, v, () => 0);
    expect(perfTier.value).toBe(1);
    v.value = { PerfOverride: '3' };
    expect(perfTier.value).toBe(3);
    stop();
    v.value = { PerfOverride: '0' };
    expect(perfTier.value).toBe(3);
  });
});
