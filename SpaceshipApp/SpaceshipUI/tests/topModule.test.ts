import { describe, expect, it } from 'vitest';
import { graphFrame, graphState } from '../src/modules/graph';
import { styleFrom } from '../src/modules/style';

describe('top console inputs', () => {
  it('the RAM graph reads the host percent until byte counts are reported', () => {
    const zone = { x: 0, y: 0, w: 200, h: 60 };
    const f = graphFrame(graphState('ram'), { mRamPct: 50 }, zone, styleFrom({}), 'fixed');
    expect(f.value).toBe(50);
  });

  it('the RAM graph uses bytes when both counts are there', () => {
    const zone = { x: 0, y: 0, w: 200, h: 60 };
    const f = graphFrame(graphState('ram'), { mRamPct: 50, mRamUsed: 6, mRamTotal: 8 }, zone, styleFrom({}), 'fixed');
    expect(f.value).toBe(75);
  });
});
