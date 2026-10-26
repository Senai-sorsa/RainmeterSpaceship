import { describe, expect, it } from 'vitest';
import type { Style } from '../src/draw/canvas';
import { consoleActions, consoleFrame, isTabUnderline, consoleIntent, withHybridMode, type ConsoleConfig, type ConsoleState, type ConsoleView } from '../src/modules/console';

// Fake status and config only. Expected values are worked out from console.lua. Zone 580 x 104.
const st: Style = {
  s: 1, tier: 2, glowA: 46, glowW: 3.2, coreWhite: 0, hudA: 255, edit: false,
  textGlow: 4, textGlowA: 150, textSmall: 1.85, textLarge: 1.45, fontText: 'Oxanium', fontNum: 'B612 Mono', fontTitle: 'Michroma',
  white: [215, 240, 255, 255], dim: [0, 110, 150, 255], panel: [0, 30, 45, 90], accent: [0, 210, 255, 255],
  warn: [255, 130, 40, 255], alert: [255, 60, 70, 255], text: [170, 235, 255, 255], hi: [255, 105, 135, 255], good: [60, 255, 170, 255],
};
const zone = { x: 0, y: 0, w: 580, h: 104 };
const cfg: ConsoleConfig = {
  powerModes: ['quiet', 'balance', 'performance'], rates: ['60', '165'], conserveWord: 'conservation', normalWord: 'normal',
  chargeLimit: 80, perfOverride: -1, perfTier: 0,
};
const noStatus: ConsoleState = { hybrid: '', power: '', refresh: '', battery: '', dgpu: '' };
const view: ConsoleView = { armed: null, hudHidden: false, msg: '', msgAt: 0 };

describe('withHybridMode (console.lua hybridIndex)', () => {
  it('maps the raw Legion Toolkit value through the LltHybrid settings, defaults when unset', () => {
    expect(withHybridMode({ ...noStatus, hybrid: 'on-igpu-only' }, {}).hybrid).toBe('eco');
    expect(withHybridMode({ ...noStatus, hybrid: 'x1' }, { LltHybridAUTO: 'X1' }).hybrid).toBe('auto');
    expect(withHybridMode({ ...noStatus, hybrid: 'weird', dgpu: 'on' }, {})).toEqual({ ...noStatus, dgpu: 'on' });
  });
});

describe('console drawing (console.lua)', () => {
  it('quick settings show -- until the status arrives', () => {
    const labels = consoleFrame(noStatus, cfg, view, zone, st, 0).hits.filter((h) => h.id >= 8 && h.id <= 12);
    expect(labels.length).toBe(5);
    expect(labels[0].tip).toBe('Modes: quiet / balance / performance');
  });

  it('the power, refresh and battery labels use the status', () => {
    const s: ConsoleState = { hybrid: 'auto', power: 'performance', refresh: '165', battery: 'conservation on', dgpu: 'on' };
    const f = consoleFrame(s, cfg, view, zone, st, 0);
    const txt = f.ops.map((o) => (o.shape.kind === 'text' ? o.shape.text : '')).filter(Boolean);
    expect(txt).toEqual(expect.arrayContaining(['PERF', '165HZ', '80%', 'FULL', 'dGPU', 'CARGO', 'MASTER', 'CFG', 'AUTO']));
  });

  it('the active tab is the one that matches the hybrid status; with the HUD hidden it is OFF', () => {
    const underlines = (v: ConsoleView) => consoleFrame({ ...noStatus, hybrid: 'hybrid' }, cfg, v, zone, st, 0).ops.filter(isTabUnderline);
    expect(underlines(view).length).toBe(1);
    expect(underlines({ ...view, hudHidden: true }).length).toBe(1); // still one, now under OFF
  });

  it('a tab that is armed shows CONFIRM?', () => {
    const f = consoleFrame(noStatus, cfg, { ...view, armed: 4 }, zone, st, 0);
    expect(f.ops.some((o) => o.shape.kind === 'text' && o.shape.text === 'CONFIRM?')).toBe(true);
  });

  it('the message shows for six seconds only', () => {
    const shown = (now: number) => consoleFrame(noStatus, cfg, { ...view, msg: 'DONE', msgAt: 0 }, zone, st, now).ops
      .some((o) => o.shape.kind === 'text' && o.shape.text === 'DONE');
    expect(shown(5999)).toBe(true);
    expect(shown(6000)).toBe(false);
  });

  it('a discrete-GPU light shows only when the status has it', () => {
    const dots = (dgpu: string) => consoleFrame({ ...noStatus, dgpu }, cfg, view, zone, st, 0).ops.filter((o) => o.shape.kind === 'ellipse').length;
    expect(dots('')).toBe(0);
    expect(dots('on')).toBe(1);
  });
});

describe('console clicks (intent, not execution)', () => {
  const s: ConsoleState = { hybrid: '', power: 'quiet', refresh: '60', battery: 'normal', dgpu: '' };

  it('a GPU tab asks for the llt.hybrid action with its mode', () => {
    expect(consoleIntent(1, s, cfg, view)).toEqual({ kind: 'action', action: 'llt.hybrid', args: { mode: 'ECO' } });
    expect(consoleIntent(4, s, cfg, view)).toEqual({ kind: 'action', action: 'llt.hybrid', args: { mode: 'DGPU' } });
  });

  it('power cycles to the next mode, refresh to the next rate, battery toggles conservation', () => {
    // clicks come in as hit ids: power is 8, refresh 9, battery 10, the performance tier 11, master 12
    expect(consoleIntent(8, s, cfg, view)).toEqual({ kind: 'action', action: 'llt.power', args: { mode: 'balance' } });
    expect(consoleIntent(9, s, cfg, view)).toEqual({ kind: 'action', action: 'llt.refresh', args: { hz: '165' } });
    expect(consoleIntent(10, s, cfg, view)).toEqual({ kind: 'action', action: 'llt.battery', args: { mode: 'conservation' } });
  });

  it('hit ids above 5 map to the action Lua meant: 6 is the drawer, 7 the control centre, 14 status refresh', () => {
    expect(consoleIntent(6, s, cfg, view)).toEqual({ kind: 'ui', name: 'drawer' });
    expect(consoleIntent(7, s, cfg, view)).toEqual({ kind: 'ui', name: 'control' });
    expect(consoleIntent(14, s, cfg, view)).toEqual({ kind: 'action', action: 'status.refresh', args: {} });
    expect(consoleIntent(12, s, cfg, view)).toEqual({ kind: 'ui', name: 'master' });
  });

  it('the performance override steps -1, 0, 1, 2, 3 and wraps back to -1', () => {
    const next = (ov: number) => consoleIntent(11, s, { ...cfg, perfOverride: ov }, view);
    expect(next(-1)).toEqual({ kind: 'ui', name: 'perf', value: 0 });
    expect(next(3)).toEqual({ kind: 'ui', name: 'perf', value: -1 });
  });

  it('right-click on the tabs refreshes status; nothing else', () => {
    expect(consoleIntent(2, s, cfg, view, 'right')).toEqual({ kind: 'action', action: 'status.refresh', args: {} });
    expect(consoleIntent(9, s, cfg, view, 'right')).toEqual({ kind: 'none' });
  });

  it('every action the clicks can ask for is on the action list, and only the reads skip confirm', () => {
    const defs = consoleActions(cfg);
    expect(Object.keys(defs).sort()).toEqual(['llt.battery', 'llt.hybrid', 'llt.power', 'llt.refresh', 'status.refresh']);
    expect(defs['status.refresh'].confirm).toBe(false);
    expect(defs['llt.hybrid'].confirm).toBe(true);
  });
});
