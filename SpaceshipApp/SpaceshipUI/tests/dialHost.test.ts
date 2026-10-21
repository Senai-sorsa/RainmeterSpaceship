import { afterEach, describe, expect, it, vi } from 'vitest';
import { ActionGate } from '../src/actions/gate';
import { messageProblem } from '../src/host/contract';
import type { HostBridge, Msg } from '../src/host/HostBridge';
import { createDialSetter, DIAL_DEFS, hostDialRunner } from '../src/modules/dialSetter';

// Fake host only: it records what the UI sends and answers each dial.set with the given ran value. Nothing reaches the OS.
function fakeHost(ran: boolean | undefined) {
  const sent: Msg[] = [];
  let listener: ((m: Msg) => void) | undefined;
  const host: HostBridge = {
    send(m) {
      sent.push(m);
      if (ran !== undefined) listener?.({ type: 'dial.result', id: m.id, control: m.control, ran, reason: ran ? 'ran' : 'refused' });
    },
    onMessage(cb) { listener = cb; },
    telemetry: () => new Float32Array(8),
  };
  return { host, sent };
}

const setterFor = (host: HostBridge) => createDialSetter({ set: () => undefined }, new ActionGate(DIAL_DEFS, hostDialRunner(host)));

afterEach(() => vi.useRealTimers());

describe('dial host runner', () => {
  it('a percent control sends dial.set with its value and reports ok when the host ran it', async () => {
    const { host, sent } = fakeHost(true);
    const r = await setterFor(host).set('vol', 0.25);
    expect(sent).toEqual([{ type: 'dial.set', id: 1, control: 'volume', value: 25 }]);
    expect(r).toEqual({ note: null, ok: true });
  });

  it('a power mode waits for the confirm click before anything is sent', async () => {
    const { host, sent } = fakeHost(true);
    const setter = setterFor(host);
    const first = await setter.set('power', 2);
    expect(sent).toEqual([]);
    const done = await setter.confirm(first.pending!);
    expect(sent).toEqual([{ type: 'dial.set', id: 1, control: 'power', value: 'balance' }]);
    expect(done).toEqual({ note: null, ok: true });
  });

  it('a refresh rate is sent as its string name after the confirm', async () => {
    const { host, sent } = fakeHost(true);
    const setter = setterFor(host);
    const first = await setter.set('hz', 2);
    await setter.confirm(first.pending!);
    expect(sent[0]).toMatchObject({ control: 'refresh', value: '165' });
  });

  it('a write the host refused is reported as EXIT 1, not as done', async () => {
    const { host } = fakeHost(false);
    expect(await setterFor(host).set('mic', 0.4)).toEqual({ note: 'EXIT 1', ok: false });
  });

  it('a host that never answers shows NO HOST after the wait', async () => {
    vi.useFakeTimers();
    const { host } = fakeHost(undefined);
    const p = setterFor(host).set('bright', 0.5);
    await vi.advanceTimersByTimeAsync(5000);
    expect(await p).toEqual({ note: 'NO HOST', ok: false });
  });

  it('every message the runner sends passes the shared contract check', async () => {
    const { host, sent } = fakeHost(true);
    const setter = setterFor(host);
    await setter.set('bright', 1);
    await setter.set('vol', 0);
    await setter.set('mic', 0.5);
    const power = await setter.set('power', 1);
    await setter.confirm(power.pending!);
    const hz = await setter.set('hz', 1);
    await setter.confirm(hz.pending!);
    expect(sent).toHaveLength(5);
    for (const m of sent) expect(messageProblem(m)).toBeNull();
  });
});
