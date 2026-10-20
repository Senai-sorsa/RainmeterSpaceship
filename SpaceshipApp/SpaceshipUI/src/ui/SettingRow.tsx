import type { HostBridge } from '../host/HostBridge';
import type { SettingsStore } from '../settings/store';
import type { SettingDef } from '../settings/types';
import { ControlWidget } from './ControlWidget';

type P = { def: SettingDef; store: SettingsStore; host: HostBridge; onHelp?: (key: string) => void };

export function SettingRow({ def, store, host, onHelp }: P) {
  const helpId = `help-${def.key}`;
  const err = store.error.value;
  const isAction = def.control.kind === 'action';
  return (
    <div class="row" data-key={def.key}>
      <div class="row-label">
        <span class="label">{def.label}</span>
        {def.level === 'advanced' && <span class="badge adv">adv</span>}
        {def.restartRequired && <span class="badge">restart</span>}
        {onHelp && <button type="button" class="help-btn" aria-label={`Help for ${def.label}`} onClick={() => onHelp(def.helpId ?? def.key)}>?</button>}
        <span class="row-help" id={helpId} role="tooltip">{def.help}</span>
      </div>
      <div class="row-ctl"><ControlWidget def={def} store={store} host={host} describedBy={helpId} /></div>
      <div class="row-state">
        {!isAction && store.isChanged(def.key) && (
          <button type="button" class="dot" aria-label={`Reset ${def.label} to default`} title="Changed from default. Click to reset." onClick={() => store.resetKey(def.key)} />
        )}
      </div>
      {err && err.key === def.key && <div class="row-err" role="alert">{err.message}</div>}
    </div>
  );
}
