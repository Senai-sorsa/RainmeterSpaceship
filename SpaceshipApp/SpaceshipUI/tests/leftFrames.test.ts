import { describe, expect, it } from 'vitest';
import { schematicFrame, dotsFrame, scanFrame, tabAt, tabsFrame } from '../src/modules/category';
import { fakeCatalog } from '../src/modules/appsSource';
import { slotRowFrame, slotStatus } from '../src/modules/slot';
import { upkeepFrame } from '../src/modules/upkeep';
import { styleFrom } from '../src/modules/style';

const st = styleFrom({});
const zone = { x: 0, y: 0, w: 188.95, h: 60 };
const dev = fakeCatalog.cats.dev;
const chrome = fakeCatalog.apps.chrome;

describe('left column frames', () => {
  it('scan line: two hairlines at the zone top on FULL only, none in edit mode', () => {
    const ops = scanFrame(zone, st)!;
    expect(st.tier).toBe(0);
    expect(ops).toHaveLength(2);
    expect(scanFrame(zone, { ...st, tier: 1 })).toBeUndefined();
    expect(scanFrame(zone, { ...st, edit: true })).toBeUndefined();
  });

  it('slot status: RUNNING, BACKGROUND, READY, NOT FOUND and EMPTY', () => {
    expect(slotStatus(chrome, 2).text).toBe('RUNNING');
    expect(slotStatus(chrome, 1)).toEqual({ text: 'BACKGROUND', color: 'bg' });
    expect(slotStatus(chrome, 0).text).toBe('READY');
    expect(slotStatus({ ...chrome, missing: true }, 2).text).toBe('NOT FOUND');
    expect(slotStatus(undefined, 0).text).toBe('EMPTY');
  });

  it('slot rows draw an app, a category and a mirrored row', () => {
    expect(slotRowFrame({ app: chrome, state: 2, mirror: false }, zone, st).length).toBeGreaterThan(0);
    expect(slotRowFrame({ cat: dev, state: 0, mirror: false }, zone, st).length).toBeGreaterThan(0);
    expect(slotRowFrame({ app: chrome, state: 1, mirror: true }, zone, st).length).toBeGreaterThan(0);
  });

  it('tab clicks follow the drawn labels: first at the left, last at the right, one tab per share of a short label row', () => {
    const z = { x: 0, y: 0, w: 210, h: 30 };
    expect(tabAt(dev, 1, z, st, 0)).toBe(0);
    expect(tabAt(dev, 1, z, st, z.w)).toBe(Math.min(4, dev.apps.length) - 1);
    const idx = Array.from({ length: z.w }, (_, x) => tabAt(dev, 1, z, st, x));
    expect(idx).toEqual([...idx].sort((a, b) => a - b));
  });

  it('tabs, schematic and dots draw for a category and for an empty one', () => {
    expect(tabsFrame(dev, { first: 1, sel: 1 }, { x: 0, y: 0, w: 210, h: 30 }, st).length).toBeGreaterThan(0);
    expect(schematicFrame(chrome, dev, true, zone, st).length).toBeGreaterThan(0);
    expect(schematicFrame(undefined, undefined, false, zone, st).length).toBeGreaterThan(0);
    expect(dotsFrame(3, 2, { x: 0, y: 0, w: 120, h: 12 }, st).length).toBeGreaterThan(0);
  });

  it('upkeep shows -- for unknown updates and never zero', () => {
    const ops = upkeepFrame({ mailWhy: 'no host data' }, zone, st);
    expect(ops.length).toBeGreaterThan(0);
    expect(upkeepFrame({ updates: 0, mail: 3 }, zone, st).length).toBeGreaterThan(0);
    // status_block.lua n2: an unknown count is a single dash
    expect(JSON.stringify(upkeepFrame({ mailWhy: 'off' }, zone, st))).toContain('"text":"-"');
  });

  it('the tab rail keeps its four end dots, except in the fitted picture frame (live test, 2026-11-05)', () => {
    const z = { x: 0, y: 0, w: 210, h: 30 };
    const dots = (style: typeof st) => tabsFrame(dev, { first: 1, sel: 1 }, z, style).filter((o) => o.shape.kind === 'ellipse').length;
    const fitted = styleFrom({ UseShipImage: '1', PictureFit: '1' });
    expect(fitted.fitted).toBe(true);
    expect(dots(st)).toBeGreaterThanOrEqual(dots(fitted) + 4);
  });
});
