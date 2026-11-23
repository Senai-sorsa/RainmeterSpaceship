import { describe, expect, it } from 'vitest';
import { cornerPieces, LEG } from '../src/ui/CornerPieces';

describe('cornerPieces', () => {
  const caps = cornerPieces();
  const corners = [[0, 0], [2560, 0], [0, 1600], [2560, 1600]];
  it('one cap per screen corner, each touching its corner and staying tiny (within LEG units of it)', () => {
    expect(caps).toHaveLength(4);
    caps.forEach((c, i) => {
      const [cx, cy] = corners[i];
      expect(c.outline).toContainEqual([cx, cy]);
      for (const [x, y] of [...c.outline, ...c.inner, c.rivet]) {
        expect(Math.abs(x - cx)).toBeLessThanOrEqual(LEG);
        expect(Math.abs(y - cy)).toBeLessThanOrEqual(LEG);
      }
    });
  });
  it('the caps mirror each other about the screen centre lines', () => {
    const [tl, tr, bl, br] = caps;
    tl.outline.forEach(([x, y], k) => {
      expect(tr.outline[k]).toEqual([2560 - x, y]);
      expect(bl.outline[k]).toEqual([x, 1600 - y]);
      expect(br.outline[k]).toEqual([2560 - x, 1600 - y]);
    });
  });
  it('stays out of the HUD: under 0.1% of the canvas area in all', () => {
    const area = (p: [number, number][]) => Math.abs(p.reduce((s, [x, y], i) => { const [nx, ny] = p[(i + 1) % p.length]; return s + x * ny - nx * y; }, 0)) / 2;
    expect(caps.reduce((s, c) => s + area(c.outline), 0) / (2560 * 1600)).toBeLessThan(0.001);
  });
});
