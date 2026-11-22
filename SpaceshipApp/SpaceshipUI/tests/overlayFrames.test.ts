import { describe, expect, it } from 'vitest';
import { bootFrame, bootRows, bootTimeline, bootVerdict, flicker, ringProgress } from '../src/modules/boot';
import { clampScroll, drawerFrame, drawerRows, drawerState, ROWS } from '../src/modules/drawer';
import { fakeCatalog } from '../src/modules/appsSource';
import { styleFrom } from '../src/modules/style';

const st = styleFrom({});
const canvas = { w: 2560, h: 1600 };
const zone = { id: 'O_drawer', x: 0, y: 0, w: 560, h: 560, matrix: [1, 0, 0, 1, 0, 0] as const };

describe('boot overlay', () => {
  it('the stages come in order for the 29 panels', () => {
    const tl = bootTimeline();
    expect(tl).toEqual({ c0: 57, verdict: 95, fade: 155, done: 169 });
    expect(tl.c0).toBeLessThan(tl.verdict);
    expect(tl.verdict).toBeLessThan(tl.fade);
    expect(tl.fade).toBeLessThan(tl.done);
  });

  it('the ignition ring draws itself once, from nothing to closed, before the check starts', () => {
    expect(ringProgress(0)).toBe(0);
    expect(ringProgress(20)).toBeGreaterThan(0);
    expect(ringProgress(20)).toBeLessThan(1);
    expect(ringProgress(34)).toBe(1);
    expect(ringProgress(34)).toBeLessThanOrEqual(bootTimeline().c0);
  });

  it('elements enter with a short flicker, then hold steady', () => {
    expect([9, 10, 11, 12, 13].map((f) => flicker(f, 10))).toEqual([0, 0.55, 0.15, 0.8, 1]);
  });

  it('unknown readings are shown as -- and are not faults', () => {
    const rows = bootRows({});
    expect(rows).toHaveLength(6);
    expect(rows.every((r) => r.sev === 'unknown')).toBe(true);
    expect(bootVerdict(rows)).toEqual({ text: 'NO FAULTS, 6 NOT FED', warn: false });
  });

  it('a hot CPU is a warning and the verdict says so', () => {
    const rows = bootRows({ cpu: 95, mem: 40, onAc: true, bat: 80 });
    expect(rows[0].sev).toBe('warn');
    expect(bootVerdict(rows).warn).toBe(true);
    expect(bootVerdict(rows).text).toContain('NEED ATTENTION');
  });

  it('a fully fed check with no faults still names the unfed rows', () => {
    expect(bootVerdict(bootRows({ cpu: 10, mem: 20, onAc: true, bat: 90 }))).toEqual({ text: 'NO FAULTS, 3 NOT FED', warn: false });
  });

  it('feeds storage, network, audio and GPU from the host readings', () => {
    const rows = bootRows({ cpu: 10, gpu: 5, mem: 20, onAc: true, bat: 90, driveTotal: 1000, driveFree: 400, netDown: 0, netUp: 0, volume: 35, muted: false });
    expect(rows.map((r) => [r.label, r.value, r.sev])).toEqual([
      ['CPU / GPU', '10% / 5%', 'ok'], ['MEMORY', '20%', 'ok'], ['STORAGE', '40% FREE', 'ok'],
      ['NETWORK', 'ONLINE', 'ok'], ['AUDIO', '35%', 'ok'], ['POWER', 'AC 90%', 'ok'],
    ]);
    expect(bootVerdict(rows).text).toBe('ALL SYSTEMS NOMINAL');
    expect(bootRows({ driveTotal: 1000, driveFree: 50 })[2].sev).toBe('warn');
    expect(bootRows({ volume: 35, muted: true })[4].value).toBe('MUTED');
  });

  it('a frame draws the ignition, then the check panel and verdict once due', () => {
    const tl = bootTimeline();
    const rows = bootRows({ cpu: 10, mem: 20, onAc: true, bat: 90 });
    expect(bootFrame(5, rows, tl, canvas, st).length).toBeGreaterThan(0);
    expect(bootFrame(tl.verdict + 1, rows, tl, canvas, st).length).toBeGreaterThan(bootFrame(5, rows, tl, canvas, st).length);
  });
});

describe('cargo drawer', () => {
  it('the root shows ALL first, then each category, with no apps until one is open', () => {
    const rows = drawerRows(fakeCatalog, drawerState());
    expect(rows[0]).toMatchObject({ kind: 'cat', jump: true });
    expect(rows).toHaveLength(1 + fakeCatalog.catOrder.length);
    expect(rows.every((r) => r.kind === 'cat')).toBe(true);
  });

  it('an open category lists its apps under it', () => {
    const st2 = drawerState();
    st2.open.dev = true;
    const rows = drawerRows(fakeCatalog, st2);
    expect(rows.length).toBe(1 + fakeCatalog.catOrder.length + fakeCatalog.cats.dev.apps.length);
  });

  it('a focused folder shows its apps and a back row', () => {
    const st2 = { ...drawerState(), focus: 'dev' };
    const rows = drawerRows(fakeCatalog, st2);
    expect(rows).toHaveLength(fakeCatalog.cats.dev.apps.length + 1);
    expect(rows[rows.length - 1]).toEqual({ kind: 'all' });
  });

  it('scroll is held inside the rows that fit', () => {
    expect(clampScroll(100, 30)).toBe(30 - ROWS);
    expect(clampScroll(-5, 30)).toBe(0);
    expect(clampScroll(3, 5)).toBe(0);
  });

  it('draws with the fixture catalog, at the root and in a folder', () => {
    expect(drawerFrame(fakeCatalog, drawerState(), zone, st).length).toBeGreaterThan(0);
    expect(drawerFrame(fakeCatalog, { ...drawerState(), focus: 'dev' }, zone, st).length).toBeGreaterThan(0);
  });
});
