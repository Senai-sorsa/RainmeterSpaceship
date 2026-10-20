import { describe, expect, it } from 'vitest';
import { MockHost, type HostBridge, type Msg } from '../src/host/HostBridge';
import { createSettingsStore } from '../src/settings/store';
import type { SettingDef } from '../src/settings/types';

const base = { file: 'Settings.inc', help: '', category: 'display', group: 'G1', level: 'normal' } as const;
const DEFS: SettingDef[] = [
  { ...base, key: 'vol', label: 'Volume', help: 'Loudness of the voice', control: { kind: 'slider', min: 0, max: 100, step: 5 }, default: '50' },
  { ...base, key: 'name', label: 'Assistant name', help: 'What to call it', control: { kind: 'text', pattern: '^[A-Za-z0-9 ]{1,20}$', max: 20 }, default: 'Jarvis' },
  { ...base, key: 'mode', label: 'Mode', help: 'Display mode', control: { kind: 'select', options: [{ value: 'a', label: 'A' }, { value: 'b', label: 'B' }] }, default: 'a' },
  { ...base, key: 'flag', label: 'Flag', group: 'G2', control: { kind: 'toggle' }, default: '0' },
  { ...base, key: 'adv', label: 'Advanced flag', group: 'G2', level: 'advanced', control: { kind: 'toggle' }, default: '1' },
  { ...base, key: 'tint', label: 'Tint', group: 'G2', control: { kind: 'color' }, default: '0,0,0' },
  { ...base, key: 'opt', label: 'Optional', group: 'G2', optional: true, control: { kind: 'toggle' }, default: '0' },
  { ...base, key: 'X', label: 'X', group: 'G3', control: { kind: 'toggle' }, default: '0' },
  { ...base, key: 'Y', label: 'Y', group: 'G3', control: { kind: 'toggle' }, default: '1' },
  { ...base, key: 'frame', label: 'Frame', group: 'G3', virtual: true, control: { kind: 'select', options: [{ value: 'a', label: 'A' }, { value: 'b', label: 'B' }] }, default: 'b' },
  { ...base, key: 'ghost', label: 'Ghost', group: 'G3', virtual: true, control: { kind: 'select', options: [{ value: 'a', label: 'A' }] }, default: 'a' },
  { ...base, key: 'act', label: 'Do it', group: 'G3', virtual: true, control: { kind: 'action', id: 'do' }, default: '' },
];
const VIRT = {
  frame: { read: (v: Record<string, string>) => (v.X === '1' ? 'a' : 'b'), write: (x: string) => (x === 'a' ? { X: '1', Y: '0' } : { X: '0', Y: '1' }) },
};

function clock() {
  let t = 0;
  let n = 0;
  const tasks = new Map<number, { at: number; fn: () => void }>();
  return {
    schedule: (fn: () => void, ms: number) => { const id = n++; tasks.set(id, { at: t + ms, fn }); return () => { tasks.delete(id); }; },
    advance(ms: number) {
      const end = t + ms;
      for (;;) {
        const next = [...tasks.entries()].filter(([, x]) => x.at <= end).sort((a, b) => a[1].at - b[1].at)[0];
        if (!next) break;
        tasks.delete(next[0]);
        t = next[1].at;
        next[1].fn();
      }
      t = end;
    },
  };
}
function make(o: ConstructorParameters<typeof MockHost>[0] = {}) {
  const host = new MockHost({ storage: null, ...o });
  const c = clock();
  const store = createSettingsStore(host, DEFS, { schedule: c.schedule, virtuals: VIRT });
  const sets = () => host.sent.filter((m) => m.type === 'config.set');
  return { host, store, c, sets };
}
/** Host whose acks the test delivers by hand (for ordering tests). */
function manual() {
  const sent: Msg[] = [];
  let cb: (m: Msg) => void = () => {};
  const host: HostBridge = { send: (m) => { sent.push(m); }, onMessage: (f) => { cb = f; }, telemetry: () => new Float32Array(8) };
  const store = createSettingsStore(host, DEFS, { schedule: clock().schedule, virtuals: VIRT });
  const sets = () => sent.filter((m) => m.type === 'config.set');
  const ack = (id: unknown, ok: boolean) => cb({ type: 'config.ack', id, key: 'vol', ok });
  return { store, sets, ack };
}

describe('settings store', () => {
  it('set sends config.set and updates value on ack', () => {
    const { store, sets } = make();
    store.set('mode', 'b');
    expect(sets()).toHaveLength(1);
    expect(sets()[0]).toMatchObject({ type: 'config.set', key: 'mode', value: 'b' });
    expect(typeof sets()[0].id).toBe('number');
    expect(store.values.value.mode).toBe('b');
    expect(store.error.value).toBeNull();
  });

  it('ack ok:false rolls value back and sets error', () => {
    const { store, sets } = make({ failKeys: new Set(['mode']) });
    store.set('mode', 'b');
    expect(sets()).toHaveLength(1);
    expect(store.values.value.mode).toBe('a');
    expect(store.error.value).toEqual({ key: 'mode', message: 'write failed' });
  });

  it('host allowlist rejection rolls back, and the error clears on the next ok ack for that key', () => {
    let ok = false;
    const { store } = make({ allow: (k) => k !== 'flag' || ok });
    store.set('flag', '1');
    expect(store.values.value.flag).toBe('0');
    expect(store.error.value?.key).toBe('flag');
    store.set('mode', 'b'); // other key ok does not clear it
    expect(store.error.value?.key).toBe('flag');
    ok = true;
    store.set('flag', '1');
    expect(store.values.value.flag).toBe('1');
    expect(store.error.value).toBeNull();
  });

  it('undo/redo restore values and send writes', () => {
    const { store, sets } = make();
    expect(store.canUndo.value).toBe(false);
    store.set('mode', 'b');
    expect(store.canUndo.value).toBe(true);
    store.undo();
    expect(store.values.value.mode).toBe('a');
    expect(sets().at(-1)).toMatchObject({ key: 'mode', value: 'a' });
    expect(store.canUndo.value).toBe(false);
    expect(store.canRedo.value).toBe(true);
    store.redo();
    expect(store.values.value.mode).toBe('b');
    expect(sets().at(-1)).toMatchObject({ key: 'mode', value: 'b' });
    store.undo();
    store.set('flag', '1'); // new set clears redo
    expect(store.canRedo.value).toBe(false);
  });

  it('history is capped at 200 entries', () => {
    const { store } = make();
    for (let i = 0; i < 250; i++) store.set('mode', i % 2 ? 'a' : 'b');
    let n = 0;
    while (store.canUndo.value) { store.undo(); n++; }
    expect(n).toBe(200);
  });

  it('slider drag coalesces to one undo entry, writes at most one per 100ms, last value always sent', () => {
    const { store, sets, c } = make();
    const opt = { coalesce: true };
    store.set('vol', '10', opt);
    expect(sets()).toHaveLength(1); // first write goes out immediately
    store.set('vol', '15', opt);
    store.set('vol', '20', opt);
    c.advance(50);
    store.set('vol', '25', opt);
    expect(sets()).toHaveLength(1);
    expect(store.values.value.vol).toBe('25'); // UI is optimistic
    c.advance(50);
    expect(sets()).toHaveLength(2);
    expect(sets()[1]).toMatchObject({ key: 'vol', value: '25' });
    store.set('vol', '30', opt);
    c.advance(100);
    c.advance(100);
    expect(sets().map((m) => m.value)).toEqual(['10', '25', '30']);
    store.undo(); // one entry for the whole drag
    expect(store.values.value.vol).toBe('50');
    expect(store.canUndo.value).toBe(false);
  });

  it('flush sends the pending trailing write immediately', () => {
    const { store, sets } = make();
    store.set('vol', '10', { coalesce: true });
    store.set('vol', '20', { coalesce: true });
    expect(sets()).toHaveLength(1);
    store.flush();
    expect(sets().at(-1)).toMatchObject({ value: '20' });
    store.flush();
    expect(sets()).toHaveLength(2);
  });

  it('a non-coalesced set or undo flushes the key pending write first, in order', () => {
    const { store, sets } = make();
    store.set('vol', '10', { coalesce: true });
    store.set('vol', '20', { coalesce: true });
    store.set('vol', '30');
    expect(sets().map((m) => m.value)).toEqual(['10', '20', '30']);
    store.set('vol', '40', { coalesce: true });
    store.set('vol', '45', { coalesce: true });
    store.undo(); // undoes the 40->45 drag entry; pending 45 goes first
    expect(sets().slice(-2).map((m) => m.value)).toEqual(['45', '30']);
  });

  it('Normal hides advanced defs, Advanced shows all', () => {
    const { store } = make();
    expect(store.visibleDefs().some((d) => d.key === 'adv')).toBe(false);
    expect(store.visibleDefs().some((d) => d.key === 'act')).toBe(true); // action rows and virtuals stay
    store.level.value = 'advanced';
    expect(store.visibleDefs().map((d) => d.key)).toEqual(DEFS.map((d) => d.key));
  });

  it('query filters visibleDefs and still honours level', () => {
    const { store } = make();
    store.query.value = 'flag';
    expect(store.visibleDefs().map((d) => d.key)).toEqual(['flag']);
    store.level.value = 'advanced';
    expect(store.visibleDefs().map((d) => d.key)).toEqual(['flag', 'adv']);
  });

  it('search finds by label/help/key and ranks label first', () => {
    const { store } = make();
    expect(store.search('')).toEqual([]);
    expect(store.search('  ')).toEqual([]);
    expect(store.search('LOUDNESS').map((d) => d.key)).toEqual(['vol']);
    expect(store.search('mode').map((d) => d.key)).toEqual(['mode']);
    expect(store.search('vol')[0].key).toBe('vol'); // key and label
    expect(store.search('it').map((d) => d.key)).toEqual(['act', 'name']); // label 'Do it' before help-only 'name'
    expect(store.search('X').map((d) => d.key)[0]).toBe('X');
  });

  it('isChanged false at default, true otherwise', () => {
    const { store } = make();
    expect(store.isChanged('mode')).toBe(false);
    store.set('mode', 'b');
    expect(store.isChanged('mode')).toBe(true);
    expect(store.isChanged('frame')).toBe(false);
    expect(store.isChanged('nope')).toBe(false);
    expect(store.isChanged('act')).toBe(false);
  });

  it('resetKey writes the default for changed keys only and is undoable', () => {
    const { store, sets } = make();
    store.resetKey('mode');
    expect(sets()).toHaveLength(0);
    store.set('mode', 'b');
    store.resetKey('mode');
    expect(store.values.value.mode).toBe('a');
    expect(sets()).toHaveLength(2);
    store.undo();
    expect(store.values.value.mode).toBe('b');
  });

  it('resetGroup resets only that group', () => {
    const { store, sets } = make();
    store.set('mode', 'b');
    store.set('vol', '10');
    store.set('flag', '1');
    store.set('tint', '1,2,3');
    const n = sets().length;
    store.resetGroup('display', 'G1');
    expect(store.values.value).toMatchObject({ mode: 'a', vol: '50', flag: '1', tint: '1,2,3' });
    expect(sets()).toHaveLength(n + 2); // changed keys only (name unchanged)
    store.undo(); // one undo entry for the whole group
    expect(store.values.value).toMatchObject({ mode: 'b', vol: '10' });
  });

  it('applyDefaults writes only differing keys and twice writes nothing the second time', async () => {
    const { store, sets } = make();
    store.set('vol', '10');
    store.set('name', 'Bob');
    const n = sets().length;
    expect(await store.applyDefaults()).toEqual({ ok: true, failed: [] });
    expect(sets()).toHaveLength(n + 2);
    expect(store.values.value).toMatchObject({ vol: '50', name: 'Jarvis' });
    expect(await store.applyDefaults()).toEqual({ ok: true, failed: [] });
    expect(sets()).toHaveLength(n + 2);
  });

  it('applyDefaults reports failed keys', async () => {
    const { store, sets } = make({ seed: { mode: 'b', vol: '10' }, failKeys: new Set(['mode']) });
    expect(store.values.value.mode).toBe('b');
    const r = await store.applyDefaults();
    expect(r).toEqual({ ok: false, failed: ['mode'] });
    expect(store.values.value).toMatchObject({ vol: '50', mode: 'b' });
    expect(sets().filter((m) => m.key === 'vol')).toHaveLength(1);
    expect(store.error.value?.key).toBe('mode');
  });

  it('applyDefaults waits for each ack', async () => {
    const m = manual();
    m.store.set('vol', '10');
    let done = false;
    const p = m.store.applyDefaults().then(() => { done = true; });
    await Promise.resolve();
    expect(done).toBe(false);
    m.ack(m.sets()[0].id, true);
    await Promise.resolve();
    expect(done).toBe(false);
    m.ack(m.sets()[1].id, true);
    await p;
    expect(done).toBe(true);
  });

  it('missing optional key shows default', () => {
    const { store, host } = make({ seed: { vol: '70', zzz: '1' } });
    expect(store.values.value.opt).toBe('0');
    expect(store.values.value.vol).toBe('70');
    expect('zzz' in store.values.value).toBe(false);
    const get = host.sent.find((m) => m.type === 'config.get') as unknown as { keys: string[] };
    expect(get.keys).toContain('vol');
    expect(get.keys).not.toContain('frame');
    expect(get.keys).not.toContain('act');
  });

  it('loadFromHost merges a later reply and ignores non-string values', () => {
    const { store, host } = make({ seed: { vol: '70' } });
    host.send({ type: 'config.set', key: 'mode', value: 'b', id: 99 }); // changed behind the store's back
    store.loadFromHost();
    expect(store.values.value).toMatchObject({ vol: '70', mode: 'b', name: 'Jarvis' });
  });

  it('virtual set writes every target with one undo entry', () => {
    const { store, sets } = make();
    expect(store.values.value.frame).toBe('b');
    store.set('frame', 'a');
    expect(sets().map((m) => [m.key, m.value])).toEqual([['X', '1'], ['Y', '0']]);
    expect(store.values.value.frame).toBe('a');
    store.undo();
    expect(store.values.value).toMatchObject({ X: '0', Y: '1', frame: 'b' });
    expect(store.canUndo.value).toBe(false);
    store.redo();
    expect(store.values.value.frame).toBe('a');
  });

  it('virtual key without a mapping rejects', () => {
    const { store, sets } = make();
    store.set('ghost', 'a');
    expect(store.error.value?.key).toBe('ghost');
    expect(sets()).toHaveLength(0);
  });

  it('rejects invalid values before any write', () => {
    const { store, sets } = make();
    const bad: [string, string][] = [
      ['name', '<script>alert(1)</script>'],
      ['name', 'a'.repeat(200)],
      ['name', ''],
      ['vol', '105'],
      ['vol', '-5'],
      ['vol', '12'],
      ['vol', 'NaN'],
      ['vol', ''],
      ['vol', 'Infinity'],
      ['mode', 'c'],
      ['flag', '2'],
      ['flag', 'true'],
      ['tint', '256,0,0'],
      ['tint', '1,2'],
      ['tint', 'red'],
      ['tint', '1,2,3,4,5'],
      ['nope', '1'],
      ['act', 'x'],
      ['frame', 'zzz'],
    ];
    for (const [k, v] of bad) {
        store.set(k, v);
      expect([k, v, store.error.value?.key]).toEqual([k, v, k]);
    }
    expect(sets()).toHaveLength(0);
    expect(store.values.value).toMatchObject({ name: 'Jarvis', vol: '50', mode: 'a', flag: '0', tint: '0,0,0' });
    expect(store.canUndo.value).toBe(false);
  });

  it('accepts valid boundary values', () => {
    const { store } = make();
    store.set('vol', '0');
    store.set('vol', '100');
    store.set('tint', '255,128,0');
    store.set('tint', '255,128,0,255');
    store.set('name', 'Jarvis Two');
    expect(store.values.value).toMatchObject({ vol: '100', tint: '255,128,0,255', name: 'Jarvis Two' });
    expect(store.error.value).toBeNull();
  });

  it('out-of-order failed acks do not corrupt state', () => {
    const m = manual();
    m.store.set('vol', '10');
    m.store.set('vol', '20');
    const [a, b] = m.sets();
    m.ack(b.id, true);
    m.ack(a.id, false); // stale failure must not undo the newer value
    expect(m.store.values.value.vol).toBe('20');

    const m2 = manual();
    m2.store.set('vol', '10');
    m2.store.set('vol', '20');
    const [a2, b2] = m2.sets();
    m2.ack(b2.id, false);
    expect(m2.store.values.value.vol).toBe('10');
    m2.ack(a2.id, false);
    expect(m2.store.values.value.vol).toBe('50');
  });

  it('duplicate and unknown acks are ignored', () => {
    const m = manual();
    m.store.set('vol', '10');
    const first = m.sets()[0];
    m.ack(first.id, false);
    expect(m.store.values.value.vol).toBe('50');
    m.store.set('vol', '30');
    m.ack(first.id, false); // replay of the old ack
    m.ack(999, false);
    m.ack('x', false);
    expect(m.store.values.value.vol).toBe('30');
    m.ack(m.sets()[1].id, true);
    m.ack(m.sets()[1].id, false);
    expect(m.store.values.value.vol).toBe('30');
  });

  it('ignores unrelated host messages', () => {
    const { store, host } = make();
    host.send({ type: 'setup.get' });
    host.send({ type: 'aboutme.get' });
    expect(store.values.value.vol).toBe('50');
    expect(store.error.value).toBeNull();
  });
});
