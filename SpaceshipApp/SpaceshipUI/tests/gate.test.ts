import { describe, expect, it } from 'vitest';
import { ActionGate, type ActionDef, type Args } from '../src/actions/gate';

// Fake runner only: records what it was asked to run and returns the exit code it is given. No process is started.
const defs: Record<string, ActionDef> = {
  'llt.power': { args: { mode: { kind: 'enum', values: ['quiet', 'balance'] } }, confirm: true },
  'llt.refresh': { args: { hz: { kind: 'int', min: 60, max: 165 } }, confirm: true },
  'status.refresh': { args: {}, confirm: false },
};

function harness(exitCode = 0) {
  const ran: [string, Args][] = [];
  let clock = 1000;
  const gate = new ActionGate(defs, async (action, args) => { ran.push([action, args]); return { exitCode }; }, () => clock, 5000);
  return { gate, ran, tick: (ms: number) => { clock += ms; } };
}

describe('action gate: source and list', () => {
  it('refuses any request from model output, before anything else is checked', async () => {
    const { gate, ran } = harness();
    const out = await gate.request('status.refresh', {}, 'model');
    expect(out).toEqual({ kind: 'refused', reason: 'model output cannot trigger an action' });
    expect(ran).toEqual([]);
  });

  it('refuses an action that is not on the list', async () => {
    const { gate, ran } = harness();
    expect((await gate.request('shell.exec', {}, 'user')).kind).toBe('refused');
    expect(ran).toEqual([]);
  });
});

describe('action gate: arguments', () => {
  it('refuses an enum value that is not allowed, and a missing or extra argument', async () => {
    const { gate, ran } = harness();
    expect(await gate.request('llt.power', { mode: 'extreme' }, 'user')).toMatchObject({ kind: 'refused' });
    expect(await gate.request('llt.power', {}, 'user')).toMatchObject({ kind: 'refused', reason: 'missing argument mode' });
    expect(await gate.request('llt.power', { mode: 'quiet', x: 1 }, 'user')).toMatchObject({ kind: 'refused', reason: 'unknown argument x' });
    expect(ran).toEqual([]);
  });

  it('an int argument must be a whole number inside its range', async () => {
    const { gate } = harness();
    expect(await gate.request('llt.refresh', { hz: 59 }, 'user')).toMatchObject({ kind: 'refused' });
    expect(await gate.request('llt.refresh', { hz: 60.5 }, 'user')).toMatchObject({ kind: 'refused' });
    expect(await gate.request('llt.refresh', { hz: '165' as unknown as number }, 'user')).toMatchObject({ kind: 'refused' });
  });
});

describe('action gate: confirm and exit codes', () => {
  it('a change waits for a confirm and runs exactly once when confirmed', async () => {
    const { gate, ran } = harness();
    const p = await gate.request('llt.power', { mode: 'balance' }, 'user');
    expect(p).toEqual({ kind: 'pending', id: 1 });
    expect(ran).toEqual([]);
    expect(await gate.confirm(1)).toEqual({ kind: 'ran', ok: true, exitCode: 0 });
    expect(ran).toEqual([['llt.power', { mode: 'balance' }]]);
    expect((await gate.confirm(1)).kind).toBe('refused'); // a second confirm of the same id runs nothing
    expect(ran.length).toBe(1);
  });

  it('a read-only action runs at once', async () => {
    const { gate, ran } = harness();
    expect(await gate.request('status.refresh', {}, 'user')).toEqual({ kind: 'ran', ok: true, exitCode: 0 });
    expect(ran.length).toBe(1);
  });

  it('a non-zero exit code is reported as not ok', async () => {
    const { gate } = harness(3);
    await gate.request('status.refresh', {}, 'user');
    expect(await gate.request('status.refresh', {}, 'user')).toEqual({ kind: 'ran', ok: false, exitCode: 3 });
  });

  it('an expired confirm runs nothing', async () => {
    const { gate, ran, tick } = harness();
    await gate.request('llt.power', { mode: 'quiet' }, 'user');
    tick(5001);
    expect(await gate.confirm(1)).toEqual({ kind: 'refused', reason: 'confirmation expired' });
    expect(ran).toEqual([]);
  });

  it('a cancelled change never runs', async () => {
    const { gate, ran } = harness();
    await gate.request('llt.power', { mode: 'quiet' }, 'user');
    expect(gate.cancel(1)).toBe(true);
    expect((await gate.confirm(1)).kind).toBe('refused');
    expect(ran).toEqual([]);
  });

  it('a runner that throws reports an error, not a success', async () => {
    const gate = new ActionGate(defs, async () => { throw new Error('boom'); }, () => 0);
    expect(await gate.request('status.refresh', {}, 'user')).toEqual({ kind: 'error', reason: 'boom' });
  });
});
