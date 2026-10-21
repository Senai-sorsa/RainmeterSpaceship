import { ActionGate, type ActionDef, type Args, type Outcome, type Runner } from '../actions/gate';
import { CONTROLS } from './dial';

// Writes from the systems dial. Glow is a setting, so it goes to the settings store. Brightness, volume, mic, power mode
// and refresh rate change the system, so they go through the action gate, and power and refresh wait for a confirm
// click. The host has no dial actions yet, so the default runner refuses (NO HOST): nothing changes the OS until the
// host side is built and approved. shortcut: the ids and args here are not on the host's action list (contract/config-keys.json) yet.

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

/** The default runner: no host action exists for the dial yet, so it throws and the gate reports it as NO HOST. */
export const noHostRunner: Runner = async () => { throw new Error('no host action'); };

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
