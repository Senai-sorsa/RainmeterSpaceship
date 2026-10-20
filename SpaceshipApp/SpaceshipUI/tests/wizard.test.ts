import { describe, expect, it } from 'vitest';
import { MockHost, type HostBridge, type Msg } from '../src/host/HostBridge';
import { createSettingsStore } from '../src/settings/store';
import type { SettingDef } from '../src/settings/types';
import { STEPS, createWizard, shouldShow } from '../src/wizard/wizard';

const base = { file: 'Settings.inc', help: '', category: 'assistant', group: 'G', level: 'normal' } as const;
const DEFS: SettingDef[] = [
  { ...base, key: 'name', label: 'Name', control: { kind: 'text', pattern: '^[A-Za-z]{1,10}$', max: 10 }, default: 'Jarvis', wizard: 'assistant' },
  { ...base, key: 'flag', label: 'Flag', control: { kind: 'toggle' }, default: '0' },
  { ...base, key: 'bad', label: 'Bad', control: { kind: 'toggle' }, default: '0' },
];
const mem = (): Storage => {
  const m = new Map<string, string>();
  return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => void m.set(k, String(v)), removeItem: (k) => void m.delete(k),
    clear: () => m.clear(), key: () => null, get length() { return m.size; } } as Storage;
};
function make(o: ConstructorParameters<typeof MockHost>[0] = {}) {
  const host = new MockHost({ storage: null, ...o });
  const store = createSettingsStore(host, DEFS, { throttleMs: 0 });
  const wiz = createWizard(store, host, DEFS);
  const sent = (t: string) => host.sent.filter((m) => m.type === t);
  return { host, store, wiz, sent };
}

describe('wizard', () => {
  it('has exactly 6 steps, welcome first and review last', () => {
    expect(STEPS.map((s) => s.id)).toEqual(['welcome', 'you', 'assistant', 'look', 'apps', 'review']);
  });
  it('next/back/skip move within bounds and write nothing', () => {
    const { wiz, host } = make();
    const before = host.sent.length;
    wiz.back();
    expect(wiz.step.value).toBe(0);
    for (let i = 0; i < 9; i++) wiz.skip();
    expect(wiz.step.value).toBe(5);
    wiz.back(); wiz.next();
    expect(wiz.step.value).toBe(5);
    expect(host.sent.slice(before).filter((m) => m.type !== 'config.get')).toEqual([]);
  });
  it('useDefaults writes changed keys, finishes as defaults, and is idempotent', async () => {
    const { store, wiz, sent } = make();
    store.set('flag', '1');
    expect((await wiz.useDefaults()).ok).toBe(true);
    expect(store.values.value.flag).toBe('0');
    expect(sent('setup.finish')).toEqual([{ type: 'setup.finish', mode: 'defaults' }]);
    const sets = sent('config.set').length;
    expect((await wiz.useDefaults()).ok).toBe(true);
    expect(sent('config.set').length).toBe(sets);
  });
  it('useDefaults does not finish when a write fails', async () => {
    const failKeys = new Set<string>();
    const { store, wiz, sent } = make({ failKeys });
    store.set('flag', '1'); // acked ok
    failKeys.add('flag'); // the reset write will now be rejected
    const r = await wiz.useDefaults();
    expect(r).toEqual({ ok: false, failed: ['flag'] });
    expect(sent('setup.finish')).toEqual([]);
  });
  it('finish refuses after a failed write and accepts a clean state', async () => {
    const bad = make({ failKeys: new Set(['bad']) });
    bad.store.set('bad', '1');
    const r = await bad.wiz.finish();
    expect(r.ok).toBe(false);
    expect(bad.sent('setup.finish')).toEqual([]);
    const good = make();
    good.store.set('flag', '1');
    expect((await good.wiz.finish()).ok).toBe(true);
    expect(good.sent('setup.finish')).toEqual([{ type: 'setup.finish', mode: 'custom' }]);
  });
  it('finish waits for an ack that arrives late and refuses on timeout', async () => {
    const sent: Msg[] = [];
    let cb: (m: Msg) => void = () => {};
    const host: HostBridge = { send: (m) => { sent.push(m); }, onMessage: (f) => { cb = f; }, telemetry: () => new Float32Array(8) };
    const store = createSettingsStore(host, DEFS, { throttleMs: 0, ackTimeoutMs: 20 });
    const wiz = createWizard(store, host, DEFS);
    store.set('flag', '1');
    const id = sent.find((m) => m.type === 'config.set')!.id;
    const p = wiz.finish();
    cb({ type: 'config.ack', id, key: 'flag', ok: true });
    expect((await p).ok).toBe(true);
    store.set('name', 'Zed');
    expect((await wiz.finish()).ok).toBe(false); // never acked
    expect(sent.filter((m) => m.type === 'setup.finish').length).toBe(1);
  });
  it('changes() lists only keys that differ from their default', () => {
    const { store, wiz } = make();
    expect(wiz.changes()).toEqual([]);
    store.set('flag', '1');
    store.set('name', 'Zed');
    expect(wiz.changes()).toEqual([
      { key: 'name', label: 'Name', from: 'Jarvis', to: 'Zed' },
      { key: 'flag', label: 'Flag', from: '0', to: '1' },
    ]);
    store.set('flag', '0');
    expect(wiz.changes().map((c) => c.key)).toEqual(['name']);
  });
  it('shouldShow is true on a fresh host, false after finish, true when the host never answers', async () => {
    const storage = mem();
    const a = make({ storage });
    expect(await shouldShow(a.host)).toBe(true);
    await a.wiz.finish();
    expect(await shouldShow(new MockHost({ storage }))).toBe(false);
    const mute: HostBridge = { send: () => {}, onMessage: () => {}, telemetry: () => new Float32Array(8) };
    expect(await shouldShow(mute, 10)).toBe(true);
  });
  it('reload mid-wizard starts at welcome with applied values prefilled', () => {
    const storage = mem();
    const a = make({ storage });
    a.wiz.next(); a.wiz.next();
    a.store.set('name', 'Zed');
    const b = make({ storage });
    expect(b.wiz.step.value).toBe(0);
    expect(b.store.values.value.name).toBe('Zed');
  });
});
