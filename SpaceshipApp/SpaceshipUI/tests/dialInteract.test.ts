import { describe, expect, it } from 'vitest';
import { ActionGate, type Args } from '../src/actions/gate';
import { DIAL_LABEL_HITS, ringValue, stepValue, valueOf, CONTROLS } from '../src/modules/dial';
import { createDialSetter, DIAL_DEFS } from '../src/modules/dialSetter';

// Fake runner and fake store only: they record calls. No process starts and no setting is written to disk.
function harness(exitCode = 0) {
  const ran: [string, Args][] = [];
  const sets: [string, string][] = [];
  const gate = new ActionGate(DIAL_DEFS, async (a, args) => { ran.push([a, args]); return { exitCode }; }, () => 0);
  const store = { set: (k: string, v: string) => { sets.push([k, v]); } };
  return { ran, sets, setter: createDialSetter(store, gate) };
}

describe('dial stepping and ring', () => {
  it('steps a stepped control one option and holds it at the ends', () => {
    expect(stepValue(3, {}, 1)).toBe(2);
    expect(stepValue(3, { power: 'performance' }, 1)).toBe(3);
    expect(stepValue(3, { power: 'quiet' }, -1)).toBe(1);
  });

  it('moves a range by 0.02, or 0.05 for glow, and holds it between 0 and 1', () => {
    expect(stepValue(0, {}, 1)).toBeCloseTo(0.02);
    expect(stepValue(0, { bright: 100 }, 1)).toBe(1);
    expect(stepValue(5, { glowAlpha: 160 }, -1)).toBeCloseTo(0.95);
  });

  it('a ring point maps to the sweep, and the inner disc is not a value', () => {
    expect(ringValue(3, 0, 0)).toBeUndefined();
    const r = 60;
    const at = (deg: number) => [r * Math.cos((deg * Math.PI) / 180), r * Math.sin((deg * Math.PI) / 180)] as const;
    const [x1, y1] = at(135); // start of the sweep: the first power mode
    const [x2, y2] = at(45); // end of the sweep: the last
    expect(ringValue(3, x1, y1)).toBe(1);
    expect(ringValue(3, x2, y2)).toBe(3);
    expect(ringValue(1, x1, y1)).toBe(0);
  });

  it('has one label hit per control, and reads a pending value back', () => {
    expect(DIAL_LABEL_HITS).toHaveLength(CONTROLS.length);
    expect(valueOf(CONTROLS[0], { bright: 10, pending: { bright: 0.7 } })).toBe(0.7);
  });
});

describe('dial setter', () => {
  it('glow writes GlowAlpha to the settings store, scaled to its 0..160 range', async () => {
    const h = harness();
    const r = await h.setter.set('glow', 0.5);
    expect(h.sets).toEqual([['GlowAlpha', '80']]);
    expect(r).toEqual({ note: null, ok: true });
    expect(h.ran).toEqual([]);
  });

  it('brightness goes through the gate as a whole-number percent', async () => {
    const h = harness();
    const r = await h.setter.set('bright', 0.5);
    expect(h.ran).toEqual([['dial.brightness', { percent: 50 }]]);
    expect(r.ok).toBe(true);
  });

  it('power waits for confirm, then runs the chosen mode', async () => {
    const h = harness();
    const first = await h.setter.set('power', 2);
    expect(h.ran).toEqual([]);
    expect(first.note).toBe('CLICK CENTRE TO CONFIRM');
    const done = await h.setter.confirm(first.pending!);
    expect(h.ran).toEqual([['dial.power', { mode: 'balance' }]]);
    expect(done.ok).toBe(true);
  });

  it('a non-zero exit is reported, not hidden', async () => {
    const h = harness(3);
    const r = await h.setter.set('vol', 0.2);
    expect(r).toEqual({ note: 'EXIT 3', ok: false });
  });

  it('with no host action connected, the default runner reports NO HOST and changes nothing', async () => {
    const setter = createDialSetter({ set: () => undefined });
    const r = await setter.set('mic', 0.4);
    expect(r).toEqual({ note: 'NO HOST', ok: false });
  });

  it('an unknown control is not sent', async () => {
    const h = harness();
    expect((await h.setter.set('nonsense', 1)).ok).toBe(false);
    expect(h.ran).toEqual([]);
  });
});
