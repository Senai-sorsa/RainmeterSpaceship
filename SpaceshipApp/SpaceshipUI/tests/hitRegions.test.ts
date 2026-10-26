import { describe, expect, it } from 'vitest';
import { regionsOf, startHitRegions } from '../src/host/hitRegions';
import { messageProblem } from '../src/host/contract';
import type { Msg } from '../src/host/HostBridge';
import type { Scheduler } from '../src/host/scheduler';

describe('regionsOf', () => {
  it('scales to device pixels, rounds outward and pads by 6', () => {
    expect(regionsOf([{ left: 10.4, top: 20, width: 30.2, height: 5 }], 1.5)).toEqual([[9, 24, 58, 20]]);
  });
  it('drops empty boxes and keeps at most 64', () => {
    const boxes = Array.from({ length: 70 }, (_, i) => ({ left: i, top: 0, width: 1, height: 1 }));
    expect(regionsOf([{ left: 0, top: 0, width: 0, height: 9 }, ...boxes], 1)).toHaveLength(64);
  });
  it('clamps far boxes so the host accepts them', () => {
    const [r] = regionsOf([{ left: 1e6, top: -1e6, width: 1e6, height: 10 }], 1);
    expect(messageProblem({ type: 'hit.regions', rects: [r], keyboard: false })).toBeNull();
  });
});

describe('startHitRegions', () => {
  type El = { attr: string; box: { left: number; top: number; width: number; height: number } };
  const docOf = (els: El[]) => ({
    querySelectorAll: () => els.map((e) => ({ getAttribute: () => e.attr, getBoundingClientRect: () => e.box })),
  }) as unknown as Document;

  it('sends once at start, again only on change, with keyboard from data-hit="keyboard"', () => {
    const sent: Msg[] = [];
    const host = { send: (m: Msg) => sent.push(m), onMessage: () => {}, telemetry: () => new Float32Array(8) };
    let job = () => {};
    const sched: Scheduler = { every: (_ms, fn) => { job = fn; return () => {}; } };
    const els: El[] = [{ attr: '', box: { left: 0, top: 0, width: 10, height: 10 } }];
    startHitRegions(host, docOf(els), sched, () => 1);
    job();
    expect(sent).toHaveLength(1);
    expect(sent[0]).toEqual({ type: 'hit.regions', rects: [[-6, -6, 22, 22]], keyboard: false });
    els.push({ attr: 'keyboard', box: { left: 100, top: 0, width: 10, height: 10 } });
    job();
    expect(sent).toHaveLength(2);
    expect(sent[1].keyboard).toBe(true);
    expect(messageProblem(sent[1])).toBeNull();
  });
});
