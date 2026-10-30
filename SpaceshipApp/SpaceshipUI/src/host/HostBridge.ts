import { messageProblem } from './contract';
import settings from '../generated/settings.json';
import modules from '../generated/modules.json';
import { REGISTRY, allowedKeys } from '../settings/registry';

export type Msg = { type: string; [k: string]: unknown };
export interface HostBridge {
  send(msg: Msg): void;
  /** Returns a function that removes the listener (hosts that cannot may return nothing). */
  onMessage(cb: (msg: Msg) => void): void | (() => void);
  telemetry(): Float32Array;
}

const STORE_KEY = 'mockhost.v1';
type Persisted = { config: Record<string, string>; setupDone: boolean; aboutMe: string };
export type MockOpts = { seed?: Record<string, string>; allow?: (key: string) => boolean; storage?: Storage | null; failKeys?: Set<string> };

/** Deterministic: telemetry depends only on the number of tick() calls. Replies reach onMessage callbacks synchronously inside send(). */
export class MockHost implements HostBridge {
  sent: Msg[] = [];
  private cbs: ((m: Msg) => void)[] = [];
  private t = 0;
  private st: Persisted = { config: {}, setupDone: false, aboutMe: '' };
  private storage: Storage | null;
  constructor(private o: MockOpts = {}) {
    this.storage = o.storage === undefined ? safeLocalStorage() : o.storage;
    try {
      const raw = this.storage?.getItem(STORE_KEY);
      const p = raw ? JSON.parse(raw) : null;
      if (p && typeof p === 'object') {
        const c = p.config && typeof p.config === 'object' ? p.config : {};
        for (const [k, v] of Object.entries(c)) if (typeof v === 'string') this.st.config[k] = v;
        this.st.setupDone = p.setupDone === true;
        if (typeof p.aboutMe === 'string') this.st.aboutMe = p.aboutMe;
      }
    } catch { /* blocked or corrupt storage: start empty */ }
  }
  private save() { try { this.storage?.setItem(STORE_KEY, JSON.stringify(this.st)); } catch { /* memory only */ } }
  private reply(m: Msg) { for (const cb of this.cbs) cb(m); }
  send(msg: Msg) {
    this.sent.push(msg);
    switch (msg.type) {
      case 'config.get': {
        const all = { ...this.o.seed, ...this.st.config };
        const values: Record<string, string> = {};
        for (const k of Array.isArray(msg.keys) ? msg.keys : []) if (typeof k === 'string' && k in all) values[k] = all[k];
        return this.reply({ type: 'config.values', values });
      }
      case 'config.set': {
        const { key, value, id } = msg as unknown as { key: string; value: string; id: number };
        const ack = (ok: boolean, error?: string) => this.reply({ type: 'config.ack', id, key, ok, ...(error ? { error } : {}) });
        if (typeof key !== 'string' || typeof value !== 'string' || (this.o.allow && !this.o.allow(key))) return ack(false, 'not allowed');
        if (this.o.failKeys?.has(key)) return ack(false, 'write failed');
        this.st.config[key] = value;
        this.save();
        return ack(true);
      }
      case 'setup.get': return this.reply({ type: 'setup.state', done: this.st.setupDone });
      case 'setup.finish':
        this.st.setupDone = true;
        this.save();
        return this.reply({ type: 'setup.state', done: true });
      case 'action': // rerun reopens the wizard now; reset only clears the saved flag for the next start
        if (msg.id === 'setup.reset') { this.st.setupDone = false; this.save(); }
        else if (msg.id === 'setup.rerun') this.reply({ type: 'setup.state', done: false });
        return;
      case 'aboutme.get': return this.reply({ type: 'aboutme.value', text: this.st.aboutMe });
      case 'aboutme.set': {
        const text = msg.text as string; // checked just below
        if (messageProblem(msg) !== null) return this.reply({ type: 'aboutme.value', text: this.st.aboutMe, ok: false });
        this.st.aboutMe = text;
        this.save();
        return this.reply({ type: 'aboutme.value', text });
      }
      case 'speed.run': return this.reply({ type: 'status.update', kind: 'speed', state: 'testing', why: '' }); // the mock never finishes one
    }
  }
  onMessage(cb: (m: Msg) => void) {
    this.cbs.push(cb);
    cb({ type: 'state.init', version: 1, mock: true });
    return () => { this.cbs = this.cbs.filter((f) => f !== cb); };
  }
  tick() { this.t++; }
  telemetry(): Float32Array {
    const f = new Float32Array(8);
    for (let i = 0; i < 8; i++) f[i] = Math.fround(0.5 + 0.5 * Math.sin(this.t * 0.1 + i));
    return f;
  }
}

/** The part of window.chrome.webview this bridge uses. The host sends replies as JSON objects and reads whatever string the page posts. */
export interface WebViewApi {
  postMessage(text: string): void;
  addEventListener(type: 'message', cb: (e: { data: unknown }) => void): void;
  removeEventListener(type: 'message', cb: (e: { data: unknown }) => void): void;
}

export class WebView2Host implements HostBridge {
  constructor(private api: WebViewApi) {}
  send(m: Msg): void { this.api.postMessage(JSON.stringify(m)); }
  onMessage(cb: (m: Msg) => void): () => void {
    const listener = (e: { data: unknown }) => {
      let msg: unknown;
      try { msg = typeof e.data === 'string' ? JSON.parse(e.data) : e.data; } catch { return; }
      if (isObj(msg) && typeof msg.type === 'string') cb(msg as Msg);
    };
    this.api.addEventListener('message', listener);
    return () => this.api.removeEventListener('message', listener);
  }
  /** The host does not send telemetry yet, so the page gets silence rather than made-up motion. */
  telemetry(): Float32Array { return new Float32Array(8); }
}

function isObj(m: unknown): m is Record<string, unknown> { return typeof m === 'object' && m !== null && !Array.isArray(m); }

function safeLocalStorage(): Storage | null {
  try { return globalThis.localStorage ?? null; } catch { return null; }
}

export function chooseHost(): HostBridge {
  const q = new URLSearchParams(globalThis.location?.search ?? '');
  const forced = q.get('host') === 'mock';
  const w = (globalThis as { chrome?: { webview?: WebViewApi } }).chrome;
  if (!forced && w?.webview) return new WebView2Host(w.webview);
  const storage = safeLocalStorage();
  if (q.get('fresh') === '1') { try { storage?.removeItem(STORE_KEY); } catch { /* ignore */ } }
  const allowed = allowedKeys(modules);
  const seed: Record<string, string> = {};
  for (const d of REGISTRY) if (!d.virtual) seed[d.key] = d.default;
  Object.assign(seed, (settings as { variables: Record<string, string> }).variables, (settings as { state?: Record<string, string> }).state);
  // ?host=mock&fail=<Key> makes the mock reject writes to that key (e2e failure injection)
  const fail = forced ? q.get('fail') : null;
  const host = new MockHost({ seed, allow: (k) => allowed.has(k), storage, ...(fail ? { failKeys: new Set([fail]) } : {}) });
  if (forced) (globalThis as { __host?: MockHost }).__host = host; // Playwright reads __host.sent
  return host;
}
