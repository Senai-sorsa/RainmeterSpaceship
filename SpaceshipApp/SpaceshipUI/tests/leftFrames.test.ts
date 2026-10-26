import { describe, expect, it } from 'vitest';
import { schematicFrame, dotsFrame, scanFrame, tabsFrame } from '../src/modules/category';
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
});
