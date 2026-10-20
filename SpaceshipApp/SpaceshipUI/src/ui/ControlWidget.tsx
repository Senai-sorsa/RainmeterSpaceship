import { useState } from 'preact/hooks';
import type { HostBridge } from '../host/HostBridge';
import type { SettingsStore } from '../settings/store';
import type { SettingDef } from '../settings/types';

type P = { def: SettingDef; store: SettingsStore; host: HostBridge; describedBy?: string };

/** Text-like input (text, color): commits on Enter/blur; the store validates and reports the error. User text is only ever a value, never HTML. */
function TextInput({ def, store, describedBy }: Omit<P, 'host'>) {
  const [draft, setDraft] = useState<string | null>(null);
  const shown = draft ?? store.values.value[def.key] ?? '';
  const commit = () => { if (draft !== null) { store.set(def.key, draft); setDraft(null); } };
  return (
    <input class="ctl-text" type="text" data-primary value={shown} aria-label={def.label} aria-describedby={describedBy}
      onInput={(e) => setDraft((e.target as HTMLInputElement).value)}
      onKeyDown={(e) => { if (e.key === 'Enter') commit(); }}
      onBlur={commit} />
  );
}

const FLOW_OF: Record<string, string> = { 'flow.gmail': 'gmail', 'flow.calendar': 'calendars' };

export function ControlWidget({ def, store, host, describedBy }: P) {
  const c = def.control;
  const v = store.values.value[def.key] ?? def.default;
  switch (c.kind) {
    case 'toggle':
      return (
        <button type="button" class="ctl-switch" role="switch" data-primary aria-checked={v === '1'} aria-label={def.label} aria-describedby={describedBy}
          onClick={() => store.set(def.key, v === '1' ? '0' : '1')}><i /></button>
      );
    case 'select':
      return (
        <select class="ctl-select" data-primary data-native-arrows value={v} aria-label={def.label} aria-describedby={describedBy}
          onChange={(e) => store.set(def.key, (e.target as HTMLSelectElement).value)}>
          {c.options.map((o) => <option value={o.value}>{o.label}</option>)}
        </select>
      );
    case 'slider':
      return (
        <span class="ctl-slider">
          <input type="range" data-primary data-native-arrows min={c.min} max={c.max} step={c.step} value={v} aria-label={def.label} aria-describedby={describedBy}
            onInput={(e) => store.set(def.key, (e.target as HTMLInputElement).value, { coalesce: true })}
            onChange={() => store.flush()} onPointerUp={() => store.flush()} />
          <output>{v}</output>
        </span>
      );
    case 'color': {
      const rgb = v.split(',').slice(0, 3).map((n) => Math.min(255, Math.max(0, Number(n) || 0))).join(',');
      return <span class="ctl-color"><i class="swatch" style={{ background: `rgb(${rgb})` }} /><TextInput def={def} store={store} describedBy={describedBy} /></span>;
    }
    case 'text':
      return <TextInput def={def} store={store} describedBy={describedBy} />;
    case 'action':
      return <button type="button" class="ctl-action" data-primary aria-describedby={describedBy} onClick={() => host.send(c.id === 'flow.open' ? { type: 'flow.open', flow: FLOW_OF[def.key] } : { type: 'action', id: c.id })}>{def.label}</button>;
  }
}
