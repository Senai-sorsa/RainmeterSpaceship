import { describe, expect, it } from 'vitest';
import layout from '../src/generated/layout.json';
import { consoleCutout, type SlabZone } from '../src/ui/panelSlab';

const zones = layout.zones.filter((z) => z.id === 'B_panelL' || z.id === 'B_panelR') as SlabZone[];

describe('consoleCutout', () => {
  it('stops short of the slabs so both bottom panels keep all four corners (the fitted decor clip cut one off)', () => {
    const c = consoleCutout(zones);
    expect(c.left).toBeGreaterThan(700); // the left slab reaches past x 700
    expect(c.right).toBeLessThan(1860);  // the right slab reaches in before x 1860
    expect(c.left).toBeLessThan(c.right);
  });
  it('falls back to the console edges without the zones', () => {
    expect(consoleCutout([])).toEqual({ left: 700, right: 1860 });
  });
});
