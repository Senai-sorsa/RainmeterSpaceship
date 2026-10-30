import { signal, type ReadonlySignal } from '@preact/signals';
import type { HostBridge, Msg } from '../host/HostBridge';
import type { SettingsStore } from '../settings/store';
import type { CategoryId, SettingDef, WizardStep } from '../settings/types';
import type { PartId } from '../ui/kit/shipGeometry';

export type StepId = 'copilot' | 'visor' | 'systems' | 'uplinks';
/** A pre-flight module: the settings tagged with any of `wizard` in `categories`, and the ship part it lights. */
export type Step = { id: StepId; index: string; title: string; categories: CategoryId[]; wizard: WizardStep[]; part: PartId };
export const STEPS: Step[] = [
  { id: 'copilot', index: '01', title: 'Co-pilot', categories: ['assistant'], wizard: ['you', 'assistant'], part: 'canopy' },
  { id: 'visor', index: '02', title: 'Visor', categories: ['display'], wizard: ['look'], part: 'wings' },
  { id: 'systems', index: '03', title: 'Systems', categories: ['layout'], wizard: ['modules'], part: 'wingtips' },
  { id: 'uplinks', index: '04', title: 'Uplinks', categories: ['apps', 'integrations'], wizard: ['apps', 'integrations'], part: 'engines' },
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
  const open = signal(0); // module being edited
  const done = signal<StepId[]>([]); // confirmed this run (memory only)
  const select = (i: number) => { open.value = Math.min(STEPS.length - 1, Math.max(0, i)); };
  /** Never writes: edits are written by the controls. Confirming marks the module done and opens the next unconfirmed one. */
  const confirm = () => {
    const id = STEPS[open.value].id;
    if (!done.value.includes(id)) done.value = [...done.value, id];
    const next = STEPS.findIndex((s) => !done.value.includes(s.id));
    if (next >= 0) open.value = next;
  };

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

  /** Settings that differ from their default, for the Launch list. Module Off_ keys are left out: the skin's own State.inc hides some by default, so they are current state, not edits (see hiddenModules). */
  function changes(): Change[] {
    const v = store.values.value;
    return defs.filter((d) => !d.hidden && d.wizard !== 'modules' && store.isChanged(d.key)).map((d) => ({ key: d.key, label: d.label, from: d.default, to: v[d.key] }));
  }

  /** How many HUD modules are currently hidden. */
  const hiddenModules = () => defs.filter((d) => d.wizard === 'modules' && store.values.value[d.key] === '1').length;

  return { hiddenModules, open: open as ReadonlySignal<number>, done: done as ReadonlySignal<StepId[]>, select, confirm, useDefaults, finish, changes };
}
export type Wizard = ReturnType<typeof createWizard>;
