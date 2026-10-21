import { signal, type ReadonlySignal } from '@preact/signals';
import type { HostBridge, Msg } from '../host/HostBridge';
import type { SettingsStore } from '../settings/store';
import type { CategoryId, SettingDef, WizardStep } from '../settings/types';

export type StepId = 'welcome' | WizardStep | 'review';
export type Step = { id: StepId; title: string; categories: CategoryId[]; wizard: WizardStep | null };
export const STEPS: Step[] = [
  { id: 'welcome', title: 'Welcome', categories: [], wizard: null },
  { id: 'you', title: 'About you', categories: ['assistant'], wizard: 'you' },
  { id: 'assistant', title: 'Your assistant', categories: ['assistant'], wizard: 'assistant' },
  { id: 'look', title: 'Look and feel', categories: ['display'], wizard: 'look' },
  { id: 'apps', title: 'Apps and accounts', categories: ['apps', 'integrations'], wizard: 'apps' },
  { id: 'review', title: 'Review', categories: [], wizard: null },
];

export type Change = { key: string; label: string; from: string; to: string };
export type Outcome = { ok: boolean; failed?: string[]; error?: string };

/** Resolves with the host's saved "setup done" state; true (hide the wizard) is never guessed, so no reply means show it. */
export function shouldShow(host: HostBridge, timeoutMs = 2000): Promise<boolean> {
  return new Promise((res) => {
    let off: void | (() => void);
    const t = setTimeout(() => { if (typeof off === 'function') off(); res(true); }, timeoutMs);
    off = host.onMessage((m: Msg) => { if (m.type === 'setup.state') { clearTimeout(t); if (typeof off === 'function') off(); res(m.done !== true); } });
    host.send({ type: 'setup.get' });
  });
}

export function createWizard(store: SettingsStore, host: HostBridge, defs: SettingDef[]) {
  const step = signal(0);
  const last = STEPS.length - 1;
  const move = (d: number) => { step.value = Math.min(last, Math.max(0, step.value + d)); };

  /** Never blocked and never writes: edits are written by the controls, not by navigation. */
  const next = () => move(1);
  const skip = () => move(1);
  const back = () => move(-1);

  async function useDefaults(): Promise<Outcome> {
    const r = await store.applyDefaults();
    if (!r.ok) return { ok: false, failed: r.failed };
    host.send({ type: 'setup.finish', mode: 'defaults' });
    return { ok: true };
  }

  async function finish(): Promise<Outcome> {
    const acked = await store.settled();
    const err = store.error.value;
    if (!acked || err) return { ok: false, error: err?.message ?? 'a change was not saved' };
    host.send({ type: 'setup.finish', mode: 'custom' });
    return { ok: true };
  }

  /** Settings that differ from their default, for the Review step. */
  function changes(): Change[] {
    const v = store.values.value;
    return defs.filter((d) => !d.hidden && store.isChanged(d.key)).map((d) => ({ key: d.key, label: d.label, from: d.default, to: v[d.key] }));
  }

  return { step: step as ReadonlySignal<number>, next, back, skip, useDefaults, finish, changes };
}
export type Wizard = ReturnType<typeof createWizard>;
