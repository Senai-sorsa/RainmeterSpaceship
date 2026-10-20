export type Msg = { type: string; [k: string]: unknown };
export interface HostBridge {
  send(msg: Msg): void;
  onMessage(cb: (msg: Msg) => void): void;
  telemetry(): Float32Array;
}

/** Deterministic: telemetry depends only on the number of tick() calls. */
export class MockHost implements HostBridge {
  sent: Msg[] = [];
  private cbs: ((m: Msg) => void)[] = [];
  private t = 0;
  send(msg: Msg) { this.sent.push(msg); }
  onMessage(cb: (m: Msg) => void) {
    this.cbs.push(cb);
    cb({ type: 'state.init', version: 1, mock: true });
  }
  tick() { this.t++; }
  telemetry(): Float32Array {
    const f = new Float32Array(8);
    for (let i = 0; i < 8; i++) f[i] = Math.fround(0.5 + 0.5 * Math.sin(this.t * 0.1 + i));
    return f;
  }
}

export class WebView2Host implements HostBridge {
  send(_m: Msg): void { throw new Error('not implemented (P-E)'); }
  onMessage(_cb: (m: Msg) => void): void { throw new Error('not implemented (P-E)'); }
  telemetry(): Float32Array { throw new Error('not implemented (P-E)'); }
}

export function chooseHost(): HostBridge {
  const forced = new URLSearchParams(globalThis.location?.search ?? '').get('host') === 'mock';
  const w = (globalThis as { chrome?: { webview?: unknown } }).chrome;
  return !forced && w?.webview ? new WebView2Host() : new MockHost();
}
