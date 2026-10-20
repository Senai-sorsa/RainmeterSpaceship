import { describe, it, expect } from 'vitest';
import { MockHost, type Msg } from '../src/host/HostBridge';

const mem = (init: Record<string, string> = {}): Storage => {
  const m = new Map(Object.entries(init));
  return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => void m.set(k, String(v)), removeItem: (k) => void m.delete(k),
    clear: () => m.clear(), key: () => null, get length() { return m.size; } } as Storage;
};
const run = (h: MockHost, msg: Msg) => { const out: Msg[] = []; h.onMessage((m) => out.push(m)); out.length = 0; h.send(msg); return out; };
const opts = { seed: { ColorAccent: '0,210,255' }, allow: (k: string) => k === 'ColorAccent' || k === 'Other' };

describe('MockHost config/setup', () => {
  it('config.set of a registry key is acked ok and readable via config.get', () => {
    const h = new MockHost({ ...opts, storage: null });
    const ack = run(h, { type: 'config.set', key: 'ColorAccent', value: '1,2,3', id: 7 });
    expect(ack).toEqual([{ type: 'config.ack', id: 7, key: 'ColorAccent', ok: true }]);
    expect(run(h, { type: 'config.get', keys: ['ColorAccent', 'Other'] })).toEqual([{ type: 'config.values', values: { ColorAccent: '1,2,3' } }]);
  });
  it('config.set of an unknown key is refused', () => {
    const h = new MockHost({ ...opts, storage: null });
    expect(run(h, { type: 'config.set', key: 'Nope', value: 'x', id: 1 })).toEqual([{ type: 'config.ack', id: 1, key: 'Nope', ok: false, error: 'not allowed' }]);
  });
  it('failKeys forces ok:false and leaves value unchanged', () => {
    const h = new MockHost({ ...opts, storage: null, failKeys: new Set(['ColorAccent']) });
    const [a] = run(h, { type: 'config.set', key: 'ColorAccent', value: '9', id: 2 });
    expect(a.ok).toBe(false);
    expect(run(h, { type: 'config.get', keys: ['ColorAccent'] })).toEqual([{ type: 'config.values', values: { ColorAccent: '0,210,255' } }]);
  });
  it('setup.get is false on fresh host, true after setup.finish', () => {
    const h = new MockHost({ storage: null });
    expect(run(h, { type: 'setup.get' })).toEqual([{ type: 'setup.state', done: false }]);
    expect(run(h, { type: 'setup.finish', mode: 'defaults' })).toEqual([{ type: 'setup.state', done: true }]);
    expect(run(h, { type: 'setup.get' })).toEqual([{ type: 'setup.state', done: true }]);
  });
  it('state survives a second MockHost on the same storage', () => {
    const s = mem();
    const a = new MockHost({ ...opts, storage: s });
    run(a, { type: 'config.set', key: 'ColorAccent', value: '5,5,5', id: 1 });
    run(a, { type: 'setup.finish', mode: 'custom' });
    run(a, { type: 'aboutme.set', text: 'hi' });
    const b = new MockHost({ ...opts, storage: s });
    expect(run(b, { type: 'config.get', keys: ['ColorAccent'] })).toEqual([{ type: 'config.values', values: { ColorAccent: '5,5,5' } }]);
    expect(run(b, { type: 'setup.get' })).toEqual([{ type: 'setup.state', done: true }]);
    expect(run(b, { type: 'aboutme.get' })).toEqual([{ type: 'aboutme.value', text: 'hi' }]);
  });
  it('blocked storage (getItem throws) falls back to memory without throwing', () => {
    const bad = { getItem() { throw new Error('blocked'); }, setItem() { throw new Error('blocked'); }, removeItem() { throw new Error('blocked'); } } as unknown as Storage;
    const h = new MockHost({ ...opts, storage: bad });
    expect(run(h, { type: 'config.set', key: 'ColorAccent', value: '4', id: 1 })[0].ok).toBe(true);
    expect(run(h, { type: 'config.get', keys: ['ColorAccent'] })).toEqual([{ type: 'config.values', values: { ColorAccent: '4' } }]);
  });
  it('corrupt JSON in storage is ignored', () => {
    const h = new MockHost({ ...opts, storage: mem({ 'mockhost.v1': '{not json' }) });
    expect(run(h, { type: 'setup.get' })).toEqual([{ type: 'setup.state', done: false }]);
    expect(run(h, { type: 'config.get', keys: ['ColorAccent'] })).toEqual([{ type: 'config.values', values: { ColorAccent: '0,210,255' } }]);
  });
  it('aboutme.set over 4000 chars is refused and text unchanged', () => {
    const h = new MockHost({ storage: null });
    run(h, { type: 'aboutme.set', text: 'ok' });
    expect(run(h, { type: 'aboutme.set', text: 'x'.repeat(4001) })).toEqual([{ type: 'aboutme.value', text: 'ok', ok: false }]);
  });
});
