import { signal } from '@preact/signals';
import { useMemo, useState } from 'preact/hooks';
import type { HostBridge } from '../host/HostBridge';
import type { SettingsStore } from '../settings/store';
import type { SettingDef } from '../settings/types';
import { messageProblem } from '../host/contract';
import { validateLabel, validateName } from '../settings/identity';
import { STEPS, createWizard } from '../wizard/wizard';
import { SettingsPanel } from './SettingsPanel';

type P = { store: SettingsStore; host: HostBridge; defs: SettingDef[] };
const ABOUT_MAX = 4000;
const FLOWS = [['gmail', 'Gmail'], ['calendars', 'Calendars'], ['obsidian', 'Obsidian']] as const;
const aboutErr = signal(''); // set when the host refuses the about-me text; the typed text is kept
const aboutMe = signal(''); // personal text: kept only here and sent to the host, never logged
const listening = new WeakSet<HostBridge>();

const INTRO: Record<string, string> = {
  welcome: 'A few quick questions set up your HUD. Every step can be skipped, and you can change everything later in the Control Center.',
  apps: 'Connect the services your assistant can use. Each button opens the existing secure sign-in on your computer; nothing is stored here.',
};

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

  const i = w.step.value;
  const step = STEPS[i];
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

  return (
    <div class="wiz" role="dialog" aria-label="Setup" onInput={onInput}>
      <header class="wiz-head">
        <span class="label wiz-title">{step.title}</span>
        <ol class="wiz-dots" aria-label="Progress">
          {STEPS.map((s, n) => <li key={s.id} class={n === i ? 'on' : n < i ? 'done' : ''} aria-current={n === i ? 'step' : undefined} aria-label={`Step ${n + 1}: ${s.title}`} />)}
        </ol>
      </header>
      <main class="wiz-main" data-step={step.id}>
        {INTRO[step.id] && <p class="wiz-intro">{INTRO[step.id]}</p>}
        {step.wizard && (
          <SettingsPanel store={store} host={host} defs={defs} categories={step.categories} mode="wizard"
            only={(d) => d.wizard === step.wizard && d.control.kind !== 'action'} />
        )}
        {step.id === 'you' && (
          <label class="wiz-about">
            <span class="label">About me (optional, helps the assistant know you)</span>
            <textarea class="ctl-text" maxLength={ABOUT_MAX} rows={4} value={aboutMe.value} aria-label="About me"
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
        {step.id === 'assistant' && <Preview store={store} drafts={drafts} />}
        {step.id === 'apps' && (
          <div class="wiz-flows">
            {FLOWS.map(([flow, label]) => <button type="button" class="ctl-action" onClick={() => host.send({ type: 'flow.open', flow })}>Connect {label}</button>)}
          </div>
        )}
        {step.id === 'review' && (
          <ul class="wiz-changes" aria-label="Your changes">
            {w.changes().map((c) => <li key={c.key}><span class="label">{c.label}</span> <small>{c.from || '(empty)'} → {c.to || '(empty)'}</small></li>)}
            {w.changes().length === 0 && <li class="label empty">No changes: everything stays at its default.</li>}
          </ul>
        )}
        {msg && <p class="wiz-bad" role="alert">{msg}</p>}
      </main>
      <footer class="wiz-foot">
        <button type="button" class="ctl-action wiz-btn" disabled={busy} onClick={() => run(w.useDefaults)}>Use defaults</button>
        <span class="wiz-gap" />
        <button type="button" class="ctl-action wiz-btn" disabled={i === 0} onClick={() => go(w.back)}>Back</button>
        {i > 0 && i < STEPS.length - 1 && <button type="button" class="ctl-action wiz-btn" onClick={() => go(w.skip)}>Skip</button>}
        {i < STEPS.length - 1
          ? <button type="button" class="ctl-action wiz-btn wiz-primary" onClick={() => go(w.next)}>Next</button>
          : <button type="button" class="ctl-action wiz-btn wiz-primary" disabled={busy} onClick={() => run(w.finish)}>Finish</button>}
      </footer>
    </div>
  );
}
