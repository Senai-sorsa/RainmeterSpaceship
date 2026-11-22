import { describe, expect, it } from 'vitest';
import { roundedPath } from '../src/ui/PictureTrim';

const nums = (d: string) => (d.match(/-?\d+(\.\d+)?/g) ?? []).map(Number);

describe('roundedPath', () => {
  it('starts and ends on the first and last point, and every number is finite', () => {
    const pts: [number, number][] = [[0, 0], [100, 0], [100, 100], [0, 100]];
    const d = roundedPath(pts, 20), n = nums(d);
    expect(d.startsWith('M0 0')).toBe(true);
    expect(d.endsWith('L0 100')).toBe(true);
    expect(n.every(Number.isFinite)).toBe(true);
  });
  it('rounds each inner corner with one quadratic curve whose control point is the corner', () => {
    const d = roundedPath([[0, 0], [100, 0], [100, 100]], 20);
    expect(nums(d)).toEqual([0, 0, 80, 0, 100, 0, 100, 20, 100, 100]);
  });
  it('never takes more than half a segment, so neighbouring curves cannot overlap', () => {
    const d = roundedPath([[0, 0], [10, 0], [10, 10], [20, 10]], 50);
    expect(nums(d)).toEqual([0, 0, 5, 0, 10, 0, 10, 5, 10, 5, 10, 10, 15, 10, 20, 10]);
  });
  it('a path of fewer than three points is a plain line', () => {
    expect(roundedPath([[0, 0], [5, 5]], 10)).toBe('M0 0L5 5');
  });
});
