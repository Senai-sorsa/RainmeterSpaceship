import { ActionGate, type ActionDef, type Args, type Outcome, type Runner } from '../actions/gate';
import type { HostBridge } from '../host/HostBridge';
import { CONTROLS } from './dial';

// Writes from the systems dial. Glow is a setting, so it goes to the settings store. Brightness, volume, mic, power mode
// and refresh rate change the system, so they go through the action gate, and power and refresh wait for a confirm
// click. They reach the host as dial.set (hostDialRunner); the default runner refuses (NO HOST), which tests use.
// shortcut: the dial ids are not on the host's action list (contract/config-keys.json); they go as dial.set instead.

const steps = (id: string) => CONTROLS.find((c) => c.id === id)?.steps ?? [];
const percent = { kind: 'int', min: 0, max: 100 } as const;

export const DIAL_DEFS: Record<string, ActionDef> = {
  'dial.brightness': { args: { percent }, confirm: false },
  'dial.volume': { args: { percent }, confirm: false },
  'dial.mic': { args: { percent }, confirm: false },
  'dial.power': { args: { mode: { kind: 'enum', values: steps('power') } }, confirm: true },
  'dial.refresh': { args: { hz: { kind: 'enum', values: steps('hz') } }, confirm: true },
};

/** note is the short text the dial shows; pending is the gate id to confirm; ok is false when nothing was sent. */
export type DialNote = { note: string | null; ok: boolean; pending?: number };
export type DialSetter = { set(id: string, v: number): Promise<DialNote>; confirm(id: number): Promise<DialNote> };
type Store = { set(key: string, value: string, o?: { coalesce?: boolean }): void };

/** The default runner: no host connected, so it throws and the gate reports it as NO HOST. */
export const noHostRunner: Runner = async () => { throw new Error('no host action'); };

const CONTROL_OF: Record<string, string> = {
  'dial.brightness': 'brightness', 'dial.volume': 'volume', 'dial.mic': 'mic', 'dial.power': 'power', 'dial.refresh': 'refresh',
};
const ANSWER_MS = 5000;

/** Sends dial.set to the host and waits for its dial.result with the same id. A refused or failed write is exit 1; a host that never answers rejects, so the dial shows NO HOST. */
export function hostDialRunner(host: HostBridge): Runner {
  const waiting = new Map<number, (ran: boolean) => void>();
  host.onMessage((m) => {
    if (m.type !== 'dial.result' || typeof m.id !== 'number') return;
    const done = waiting.get(m.id);
    waiting.delete(m.id);
    done?.(m.ran === true);
  });
  let nextId = 1;
  return (action, args) => new Promise((resolve, reject) => {
    const id = nextId++;
    const timer = setTimeout(() => { waiting.delete(id); reject(new Error('no answer from the host')); }, ANSWER_MS);
    waiting.set(id, (ran) => { clearTimeout(timer); resolve({ exitCode: ran ? 0 : 1 }); });
    // each dial action has exactly one argument: the percent, the mode or the rate
    host.send({ type: 'dial.set', id, control: CONTROL_OF[action], value: Object.values(args)[0] });
  });
}

const pct = (v: number) => Math.round(v * 100);
const ROUTE: Record<string, (v: number) => [string, Args]> = {
  bright: (v) => ['dial.brightness', { percent: pct(v) }],
  vol: (v) => ['dial.volume', { percent: pct(v) }],
  mic: (v) => ['dial.mic', { percent: pct(v) }],
  power: (v) => ['dial.power', { mode: steps('power')[v - 1] ?? '' }],
  hz: (v) => ['dial.refresh', { hz: steps('hz')[v - 1] ?? '' }],
};

function noteOf(o: Outcome): DialNote {
  switch (o.kind) {
    case 'ran': return o.ok ? { note: null, ok: true } : { note: `EXIT ${o.exitCode}`, ok: false };
    case 'pending': return { note: 'CLICK CENTRE TO CONFIRM', ok: true, pending: o.id };
    case 'refused': return { note: 'NOT SENT', ok: false };
    case 'error': return { note: 'NO HOST', ok: false };
  }
}

export function createDialSetter(store: Store, gate = new ActionGate(DIAL_DEFS, noHostRunner)): DialSetter {
  return {
    async set(id, v) {
      if (id === 'glow') {
        store.set('GlowAlpha', String(Math.round(v * 160)), { coalesce: true });
        return { note: null, ok: true };
      }
      const route = ROUTE[id];
      if (!route) return { note: 'NOT SENT', ok: false };
      const [action, args] = route(v);
      return noteOf(await gate.request(action, args, 'user'));
    },
    async confirm(id) {
      return noteOf(await gate.confirm(id));
    },
  };
}
