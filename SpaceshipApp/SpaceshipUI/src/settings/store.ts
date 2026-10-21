import { computed, signal, type ReadonlySignal, type Signal } from '@preact/signals';
import type { HostBridge, Msg } from '../host/HostBridge';
import type { Control, Level, SettingDef } from './types';

export type Virtual = { read(v: Record<string, string>): string; write(value: string): Record<string, string> };
export type StoreOpts = {
  throttleMs?: number;
  ackTimeoutMs?: number; // applyDefaults counts a write unacked after this long as failed
  schedule?: (fn: () => void, ms: number) => () => void; // returns cancel
  virtuals?: Record<string, Virtual>;
};
/** ok=false when any write was rejected; failed lists the raw keys (those values were rolled back). */
export type ApplyResult = { ok: boolean; failed: string[] };

type Change = { from: string; to: string };
type Entry = { changes: Record<string, Change> };
type InFlight = { key: string; value: string; prev: string; prevId: number; res?: (ok: boolean) => void };
type Throttle = { cancel: (() => void) | null; pending?: string };

const HISTORY_MAX = 200;

/** Returns an error message, or null when the value is valid for the control. */
function validate(c: Control, v: string, allowEmpty = false): string | null {
  switch (c.kind) {
    case 'toggle': return v === '0' || v === '1' ? null : 'must be 0 or 1';
    case 'select': return c.options.some((o) => o.value === v) ? null : 'not an allowed option';
    case 'slider': {
      const n = Number(v);
      if (!/^-?\d+(\.\d+)?$/.test(v) || !Number.isFinite(n) || n < c.min || n > c.max) return `must be a number from ${c.min} to ${c.max}`;
      const q = (n - c.min) / c.step;
      return Math.abs(q - Math.round(q)) < 1e-6 ? null : `must step by ${c.step}`;
    }
    case 'text': {
      if (v.length > c.max) return `at most ${c.max} characters`;
      try { return new RegExp(c.pattern).test(v) ? null : 'contains characters that are not allowed'; } catch { return 'invalid pattern'; }
    }
    case 'color': if (allowEmpty && v === '') return null; // empty = follow the theme (rows whose default is empty)
      return /^\d{1,3},\d{1,3},\d{1,3}(,\d{1,3})?$/.test(v) && v.split(',').every((p) => Number(p) <= 255) ? null : 'must be r,g,b or r,g,b,a (0-255)';
    case 'action': return 'actions are not settings';
  }
}

export function createSettingsStore(host: HostBridge, defs: SettingDef[], opts: StoreOpts = {}) {
  const throttleMs = opts.throttleMs ?? 100;
  const ackTimeoutMs = opts.ackTimeoutMs ?? 5000;
  const schedule = opts.schedule ?? ((fn, ms) => { const t = setTimeout(fn, ms); return () => clearTimeout(t); });
  const virtuals = opts.virtuals ?? {};
  const byKey = new Map(defs.map((d) => [d.key, d]));
  const isRaw = (d?: SettingDef): d is SettingDef => !!d && !d.virtual && d.control.kind !== 'action';

  const initial = Object.fromEntries(defs.filter((d) => !d.virtual).map((d) => [d.key, d.default]));
  const raw = signal<Record<string, string>>(initial); // latest intent (optimistic)
  const sent: Record<string, string> = { ...initial }; // last value sent/loaded, the rollback base
  const latestId: Record<string, number> = {}; // newest live write per key; rollback is decided by write identity, not value
  const values = computed(() => {
    const v = { ...raw.value };
    for (const d of defs) if (d.virtual) v[d.key] = virtuals[d.key]?.read(raw.value) ?? d.default;
    return v;
  });
  const level = signal<Level>('normal');
  const query = signal('');
  const error = signal<{ key: string; message: string } | null>(null);
  const past = signal<Entry[]>([]);
  const future = signal<Entry[]>([]);
  const inflight = new Map<number, InFlight>();
  const th = new Map<string, Throttle>();
  let nextId = 1;
  let errId = 0; // id of the newest failed write; only a newer ok clears the error
  let openKey: string | null = null; // key of the coalesced run that new coalesced sets may merge into
  const waiters = new Set<() => void>(); // settled() callers, woken when inflight drains

  function send(key: string, value: string, res?: (ok: boolean) => void) {
    const id = nextId++;
    inflight.set(id, { key, value, prev: sent[key], prevId: latestId[key] ?? 0, res });
    latestId[key] = id;
    sent[key] = value;
    host.send({ type: 'config.set', key, value, id }); // MockHost acks synchronously, so register first
    return id;
  }
  function sendIfNew(key: string, value: string) { if (value !== sent[key]) send(key, value); }
  function flushKey(key: string) {
    const t = th.get(key);
    if (!t) return;
    t.cancel?.();
    th.delete(key);
    if (t.pending !== undefined) sendIfNew(key, t.pending);
  }
  function startWindow(key: string, t: Throttle) {
    t.cancel = schedule(() => {
      t.cancel = null;
      if (t.pending === undefined) return void th.delete(key);
      const v = t.pending;
      t.pending = undefined;
      sendIfNew(key, v);
      startWindow(key, t);
    }, throttleMs);
  }
  /** First write in a window goes out now; later coalesced ones keep only the last value for the window's end. */
  function emit(key: string, value: string, coalesce: boolean) {
    if (!coalesce) { flushKey(key); sendIfNew(key, value); return; }
    const t = th.get(key);
    if (t) { t.pending = value; return; }
    sendIfNew(key, value);
    const nt: Throttle = { cancel: null };
    th.set(key, nt);
    startWindow(key, nt);
  }
  function flush() { openKey = null; for (const k of [...th.keys()]) flushKey(k); }

  function onAck(m: Msg) {
    const id = m.id as number;
    const e = inflight.get(id);
    if (!e) return; // duplicate or foreign ack
    inflight.delete(id);
    if (!inflight.size) for (const w of [...waiters]) w();
    const latest = latestId[e.key] === id;
    if (m.ok === true) {
      if (latest && id > errId && error.value?.key === e.key) error.value = null; // a stale ok must not hide a newer failure
      e.res?.(true);
      return;
    }
    if (latest) {
      latestId[e.key] = e.prevId;
      sent[e.key] = e.prev;
      if (raw.value[e.key] === e.value && th.get(e.key)?.pending === undefined) raw.value = { ...raw.value, [e.key]: e.prev };
    } else {
      // a newer write is live: it now rolls back past this one
      let next: InFlight | undefined;
      let nid = Infinity;
      for (const [i, o] of inflight) if (o.key === e.key && i > id && i < nid) { next = o; nid = i; }
      if (next) { next.prev = e.prev; next.prevId = e.prevId; }
    }
    errId = Math.max(errId, id);
    error.value = { key: e.key, message: typeof m.error === 'string' ? m.error : 'write failed' };
    e.res?.(false);
  }
  function onValues(m: Msg) {
    const got = m.values && typeof m.values === 'object' ? (m.values as Record<string, unknown>) : {};
    const next = { ...raw.value };
    const busy = new Set<string>([...inflight.values()].map((e) => e.key));
    for (const k of th.keys()) busy.add(k);
    // a key being edited keeps the user's value; the host's older answer must not overwrite it
    for (const [k, v] of Object.entries(got)) if (typeof v === 'string' && isRaw(byKey.get(k)) && !busy.has(k)) { next[k] = v; sent[k] = v; }
    raw.value = next;
  }
  const off = host.onMessage((m) => {
    if (m.type === 'config.ack') onAck(m);
    else if (m.type === 'config.values') onValues(m);
  });
  function loadFromHost() { host.send({ type: 'config.get', keys: defs.filter(isRaw).map((d) => d.key) }); }
  loadFromHost();

  /** Maps one logical setting to the raw keys to write; throws a user-facing message when it cannot. */
  function plan(d: SettingDef | undefined, value: string, check = true): Record<string, string> {
    if (!d) throw new Error('unknown setting');
    if (check) { const bad = validate(d.control, value, d.default === ''); if (bad) throw new Error(bad); }
    if (d.control.kind === 'action') throw new Error('actions are not settings');
    if (!d.virtual) return { [d.key]: value };
    const v = virtuals[d.key];
    if (!v) throw new Error('no mapping for this setting');
    const t = v.write(value);
    for (const k of Object.keys(t)) if (!isRaw(byKey.get(k))) throw new Error(`mapping targets unknown key ${k}`);
    return t;
  }
  function apply(targets: Record<string, string>, coalesce: boolean) {
    raw.value = { ...raw.value, ...targets };
    for (const [k, v] of Object.entries(targets)) emit(k, v, coalesce);
  }
  function commit(targets: Record<string, string>, ckey: string | null) {
    const changes: Record<string, Change> = {};
    for (const [k, to] of Object.entries(targets)) if (raw.value[k] !== to) changes[k] = { from: raw.value[k], to };
    if (!Object.keys(changes).length) return;
    const last = past.value.at(-1);
    if (ckey && openKey === ckey && last) {
      for (const [k, c] of Object.entries(changes)) last.changes[k] = { from: last.changes[k]?.from ?? c.from, to: c.to };
    } else {
      past.value = [...past.value, { changes }].slice(-HISTORY_MAX);
    }
    future.value = [];
    openKey = ckey;
    apply(Object.fromEntries(Object.entries(changes).map(([k, c]) => [k, c.to])), !!ckey);
  }
  function set(key: string, value: string, o: { coalesce?: boolean } = {}) {
    try {
      const t = plan(byKey.get(key), value);
      if (error.value?.key === key) error.value = null; // a valid retry clears the old complaint even when nothing needs sending
      commit(t, o.coalesce ? key : null);
    } catch (e) { error.value = { key, message: (e as Error).message }; }
  }

  function step(from: Entry[], to: Entry[], dir: 'from' | 'to') {
    const e = from.at(-1);
    if (!e) return null;
    openKey = null;
    apply(Object.fromEntries(Object.entries(e.changes).map(([k, c]) => [k, c[dir]])), false);
    return { e, rest: from.slice(0, -1), to: [...to, e] };
  }
  function undo() { const r = step(past.value, future.value, 'from'); if (r) { past.value = r.rest; future.value = r.to; } }
  function redo() { const r = step(future.value, past.value, 'to'); if (r) { future.value = r.rest; past.value = r.to; } }

  const isChanged = (key: string) => { const d = byKey.get(key); return !!d && d.control.kind !== 'action' && values.value[key] !== d.default; };
  /** Default-writes for the given defs that differ from their current value (unmappable ones are skipped). */
  function defaultTargets(ds: SettingDef[]) {
    const t: Record<string, string> = {};
    for (const d of ds) {
      if (!isChanged(d.key)) continue;
      try { Object.assign(t, plan(d, d.default, false)); } catch { /* no mapping: nothing to write */ }
    }
    return t;
  }
  const resetKey = (key: string) => commit(defaultTargets(byKey.has(key) ? [byKey.get(key)!] : []), null);
  const resetGroup = (category: string, group: string) => commit(defaultTargets(defs.filter((d) => d.category === category && d.group === group)), null);

  /** Wizard "Use defaults": sequential, awaits each ack, not undoable. Resolves (never rejects); the wizard must not finish unless ok. */
  async function applyDefaults(): Promise<ApplyResult> {
    flush();
    const failed: string[] = [];
    const t = defaultTargets(defs);
    for (const [k, v] of Object.entries(t)) {
      if (raw.value[k] === v) continue;
      raw.value = { ...raw.value, [k]: v };
      const ok = await new Promise<boolean>((res) => {
        let cancel = () => {};
        const id = send(k, v, (x) => { cancel(); res(x); });
        if (inflight.has(id)) cancel = schedule(() => onAck({ type: 'config.ack', id, ok: false, error: 'timed out' }), ackTimeoutMs);
      });
      if (!ok) failed.push(k);
    }
    if (failed.length) loadFromHost(); // a timed-out write may still have landed: show what the host really has
    return { ok: failed.length === 0, failed };
  }

  /** Sends pending writes and resolves true once every write is acked; false if one stays unacked past ackTimeoutMs. Check `error` for rejected writes. */
  function settled(): Promise<boolean> {
    flush();
    if (!inflight.size) return Promise.resolve(true);
    return new Promise((res) => {
      let cancel = () => {};
      const done = (ok: boolean) => { waiters.delete(wake); cancel(); res(ok); };
      const wake = () => done(true);
      waiters.add(wake);
      cancel = schedule(() => done(false), ackTimeoutMs);
    });
  }

  function search(q: string): SettingDef[] {
    const s = q.trim().toLowerCase();
    if (!s) return [];
    const rank = (d: SettingDef) => (d.label.toLowerCase().includes(s) ? 0 : d.key.toLowerCase().includes(s) ? 1 : d.help.toLowerCase().includes(s) ? 2 : -1);
    return defs.map((d) => ({ d, r: rank(d) })).filter((x) => x.r >= 0 && !x.d.hidden).sort((a, b) => a.r - b.r).map((x) => x.d);
  }
  function visibleDefs(): SettingDef[] {
    const list = query.value.trim() ? search(query.value) : defs.filter((d) => !d.hidden);
    return level.value === 'normal' ? list.filter((d) => d.level !== 'advanced') : list;
  }

  return {
    values: values as ReadonlySignal<Record<string, string>>,
    level: level as Signal<Level>,
    query,
    error: error as ReadonlySignal<{ key: string; message: string } | null>,
    canUndo: computed(() => past.value.length > 0),
    canRedo: computed(() => future.value.length > 0),
    dispose: () => { if (typeof off === 'function') off(); },
    set, undo, redo, flush, settled, loadFromHost, resetKey, resetGroup, isChanged, applyDefaults, search, visibleDefs,
  };
}
export type SettingsStore = ReturnType<typeof createSettingsStore>;
