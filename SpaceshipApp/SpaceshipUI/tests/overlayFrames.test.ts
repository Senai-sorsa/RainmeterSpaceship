import { describe, expect, it } from 'vitest';
import { bootFrame, bootRows, bootTimeline, bootVerdict, scanY } from '../src/modules/boot';
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

  it('the scanner sweeps, then stops', () => {
    expect(scanY(2, canvas.h)).not.toBeNull();
    expect(scanY(31, canvas.h)).toBeNull();
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

  it('a frame draws the scanner, then the check box and verdict once due', () => {
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
