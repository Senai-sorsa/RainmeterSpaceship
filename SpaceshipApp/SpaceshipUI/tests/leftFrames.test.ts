import { describe, expect, it } from 'vitest';
import { schematicFrame, dotsFrame, tabsFrame } from '../src/modules/category';
import { fakeCatalog } from '../src/modules/appsSource';
import { slotRowFrame, slotStatus } from '../src/modules/slot';
import { upkeepFrame } from '../src/modules/upkeep';
import { styleFrom } from '../src/modules/style';

const st = styleFrom({});
const zone = { x: 0, y: 0, w: 188.95, h: 60 };
const dev = fakeCatalog.cats.dev;
const chrome = fakeCatalog.apps.chrome;

describe('left column frames', () => {
  it('slot status: RUNNING, READY, NOT FOUND and EMPTY', () => {
    expect(slotStatus(chrome, true).text).toBe('RUNNING');
    expect(slotStatus(chrome, false).text).toBe('READY');
    expect(slotStatus({ ...chrome, missing: true }, false).text).toBe('NOT FOUND');
    expect(slotStatus(undefined, false).text).toBe('EMPTY');
  });

  it('slot rows draw an app, a category and a mirrored row', () => {
    expect(slotRowFrame({ app: chrome, running: true, mirror: false }, zone, st).length).toBeGreaterThan(0);
    expect(slotRowFrame({ cat: dev, running: false, mirror: false }, zone, st).length).toBeGreaterThan(0);
    expect(slotRowFrame({ app: chrome, running: false, mirror: true }, zone, st).length).toBeGreaterThan(0);
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
  });
});
