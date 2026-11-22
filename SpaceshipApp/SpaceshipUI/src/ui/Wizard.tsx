import { signal } from '@preact/signals';
import { useMemo, useState } from 'preact/hooks';
import type { HostBridge } from '../host/HostBridge';
import type { SettingsStore } from '../settings/store';
import type { SettingDef } from '../settings/types';
import { messageProblem } from '../host/contract';
import { validateLabel, validateName } from '../settings/identity';
import { STEPS, createWizard } from '../wizard/wizard';
import { SettingsPanel } from './SettingsPanel';
import { HudPanel } from './kit/HudPanel';
import { Reticle } from './kit/Reticle';
import { Ship } from './kit/Ship';
import { StatusPill } from './kit/StatusPill';
import type { PartId } from './kit/shipGeometry';

type P = { store: SettingsStore; host: HostBridge; defs: SettingDef[] };
const ABOUT_MAX = 4000;
const FLOWS = [['gmail', 'Gmail'], ['calendars', 'Calendars'], ['obsidian', 'Obsidian']] as const;
const aboutErr = signal(''); // set when the host refuses the about-me text; the typed text is kept
const aboutMe = signal(''); // personal text: kept only here and sent to the host, never logged
const listening = new WeakSet<HostBridge>();

/** Live label preview: reads what is being typed, so an invalid label explains itself before it is saved. */
function Preview({ store, drafts }: { store: SettingsStore; drafts: Record<string, string> }) {
  const v = store.values.value;
  const name = validateName(drafts.JarvisName ?? v.JarvisName ?? '');
  const label = validateLabel(drafts.AssistantLabel ?? v.AssistantLabel ?? '', name.ok ? name.value : undefined);
  const bad = !name.ok ? name : !label.ok ? label : null;
  return (
    <p class="wiz-preview" data-preview aria-live="polite">
      {bad ? <span class="wiz-bad">{bad.reason}</span> : <>On the HUD: <b>{label.value}</b> (called "{name.value}")</>}
    </p>
  );
}

export function Wizard({ store, host, defs }: P) {
  const w = useMemo(() => createWizard(store, host, defs), []);
  const [msg, setMsg] = useState('');
  const [busy, setBusy] = useState(false);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  if (!listening.has(host)) {
    listening.add(host);
    host.onMessage((m) => {
      if (m.type !== 'aboutme.value' || typeof m.text !== 'string') return;
      if (m.ok === false) aboutErr.value = 'Could not save your text (too long or contains unsupported characters). Your text is still here; edit it and try again.';
      else { aboutMe.value = m.text; aboutErr.value = ''; }
    });
  }
  useMemo(() => host.send({ type: 'aboutme.get' }), []);

  const i = w.open.value;
  const step = STEPS[i];
  const done = w.done.value;
  const run = async (f: () => Promise<{ ok: boolean; failed?: string[]; error?: string }>) => {
    setBusy(true); setMsg('');
    const r = await f();
    setBusy(false);
    if (!r.ok) setMsg(r.error ?? `Could not save: ${(r.failed ?? []).join(', ')}`);
  };
  const go = (f: () => void) => { setMsg(''); setDrafts({}); f(); };
  const onInput = (e: Event) => {
    const t = e.target as HTMLElement;
    const key = t.closest<HTMLElement>('[data-key]')?.dataset.key;
    if (key === 'JarvisName' || key === 'AssistantLabel') setDrafts((d) => ({ ...d, [key]: (t as HTMLInputElement).value }));
  };
  const lit: PartId[] = [...STEPS.filter((s) => done.includes(s.id)).map((s) => s.part), ...(done.length ? ['fuselage' as PartId] : []), ...(busy ? ['exhaust' as PartId] : [])];
  const changes = w.changes();
  const only = (d: SettingDef) => !!d.wizard && step.wizard.includes(d.wizard) && d.control.kind !== 'action';

  return (
    <div class="wiz" data-hit="keyboard" role="dialog" aria-label="Setup" onInput={onInput}>
      <aside class="wiz-bay">
        <div class="wiz-craft" aria-hidden="true"><Reticle lit={done.length} size={200} /><Ship lit={lit} size={120} /></div>
        <h1 class="wiz-h">Pre-flight</h1>
        <p class="wiz-intro">Four quick modules set up your HUD. All are optional, and everything can be changed later in the Control Center.</p>
        <section aria-label="Your changes">
          <ul class="wiz-changes">
            {changes.map((c) => <li key={c.key}><span class="label">{c.label}</span> <small>{c.from || '(empty)'} → {c.to || '(empty)'}</small></li>)}
            {changes.length === 0 && <li class="label empty">No changes: everything stays at its default.</li>}
          </ul>
          {w.hiddenModules() > 0 && <small class="wiz-hidden">{w.hiddenModules()} HUD modules are hidden (see Systems).</small>}
        </section>
        {msg && <p class="wiz-bad" role="alert">{msg}</p>}
        <button type="button" class="ctl-action wiz-btn wiz-primary wiz-launch" disabled={busy} onClick={() => run(w.finish)}>Launch CSpace</button>
        <button type="button" class="wiz-link" disabled={busy} onClick={() => run(w.useDefaults)}>Use defaults</button>
      </aside>
      <div class="wiz-work">
        <nav class="wiz-mods" aria-label="Modules">
          {STEPS.map((s, n) => (
            <button type="button" key={s.id} class="wiz-mod" aria-current={n === i ? 'step' : undefined} onClick={() => go(() => w.select(n))}>
              <span class="hp-index">{s.index} //</span> {s.title}
              <StatusPill state={done.includes(s.id) ? 'linked' : 'offline'} text={done.includes(s.id) ? 'Ready' : 'Default'} />
            </button>
          ))}
        </nav>
        <HudPanel index={step.index} title={step.title} id={`mod-${step.id}`} class="wiz-panel">
          <div class="wiz-main" data-step={step.id}>
            {step.id === 'uplinks' && <p class="wiz-intro">Connect the services your assistant can use. Each button opens the existing secure sign-in on your computer; nothing is stored here.</p>}
            {step.id === 'systems' && <p class="wiz-intro">Choose which HUD modules to hide. Everything is shown by default.</p>}
            <SettingsPanel store={store} host={host} defs={defs} categories={step.categories} mode="wizard" only={only} />
            {step.id === 'copilot' && (
              <label class="wiz-about">
                <span class="label">About me (optional, helps the assistant know you)</span>
                <textarea class="ctl-text" maxLength={ABOUT_MAX} rows={3} value={aboutMe.value} aria-label="About me"
                  onInput={(e) => { aboutMe.value = (e.target as HTMLTextAreaElement).value; }}
                  onBlur={() => {
                    const msg = { type: 'aboutme.set', text: aboutMe.value };
                    const bad = messageProblem(msg);
                    if (bad) aboutErr.value = 'Your text contains characters the assistant cannot store (control characters). Remove them and try again.';
                    else host.send(msg);
                  }} />
                {aboutErr.value && <p class="wiz-bad" role="alert">{aboutErr.value}</p>}
                <small>{aboutMe.value.length}/{ABOUT_MAX}</small>
              </label>
            )}
            {step.id === 'copilot' && <Preview store={store} drafts={drafts} />}
            {step.id === 'uplinks' && (
              <div class="wiz-flows">
                {FLOWS.map(([flow, label]) => <button type="button" class="ctl-action" onClick={() => host.send({ type: 'flow.open', flow })}>Connect {label}</button>)}
              </div>
            )}
          </div>
          <div class="wiz-foot">
            <button type="button" class="ctl-action wiz-btn wiz-primary" onClick={() => go(w.confirm)}>Confirm</button>
          </div>
        </HudPanel>
      </div>
    </div>
  );
}
