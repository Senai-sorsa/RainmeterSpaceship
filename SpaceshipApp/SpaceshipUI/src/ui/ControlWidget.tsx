import { useEffect, useState } from 'preact/hooks';
import type { HostBridge } from '../host/HostBridge';
import type { SettingsStore } from '../settings/store';
import type { SettingDef } from '../settings/types';
import { PICK_KEYS } from '../settings/pick';

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

/** A path setting: the text box plus a Browse button that opens the host's Windows file (or folder) dialog; the chosen path comes back as file.picked and is set like typed text. */
function PathInput({ def, store, host, describedBy }: P) {
  const folder = PICK_KEYS[def.key] === 'folder';
  useEffect(() => {
    const off = host.onMessage((m) => { if (m.type === 'file.picked' && m.key === def.key && typeof m.path === 'string' && m.path) store.set(def.key, m.path); });
    return () => { if (typeof off === 'function') off(); };
  }, [host, store, def.key]);
  return (
    <span class="ctl-path">
      <TextInput def={def} store={store} describedBy={describedBy} />
      <button type="button" class="ctl-action ctl-browse" aria-label={`Browse for ${def.label}`} title={folder ? 'Choose a folder' : 'Choose a file'}
        onClick={() => host.send({ type: 'file.pick', key: def.key })}>Browse</button>
    </span>
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
      return Object.prototype.hasOwnProperty.call(PICK_KEYS, def.key) ? <PathInput def={def} store={store} host={host} describedBy={describedBy} /> : <TextInput def={def} store={store} describedBy={describedBy} />;
    case 'action':
      return <button type="button" class="ctl-action" data-primary aria-describedby={describedBy} onClick={() => host.send(c.id === 'flow.open' ? { type: 'flow.open', flow: FLOW_OF[def.key] } : { type: 'action', id: c.id })}>{def.label}</button>;
  }
}
