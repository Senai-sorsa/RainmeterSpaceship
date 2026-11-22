import type { SettingDef } from './types';

/** Per-module keys from modules.json (the skin's real module keys): Off_/CT_ (State.inc), _DX/_DY (Offsets.inc). */
export function moduleDefs(modules: { keys: string[] }): SettingDef[] {
  const out: SettingDef[] = [];
  for (const k of modules.keys) {
    const name = k.replace(/([a-z0-9])([A-Z])/g, '$1 $2');
    const base = { category: 'layout', group: 'Modules', optional: true } as const;
    out.push(
      { ...base, key: `Off_${k}`, file: 'State.inc', label: `${name}: hidden`, help: 'Hide this module on the HUD.', level: 'normal', control: { kind: 'toggle' }, default: '0', wizard: 'modules' },
      { ...base, key: `CT_${k}`, file: 'State.inc', label: `${name}: click-through`, help: 'Let clicks pass through this module to the desktop.', level: 'normal', control: { kind: 'toggle' }, default: '0' },
      { ...base, key: `${k}_DX`, file: 'Offsets.inc', label: `${name}: shift X`, help: 'Move this module sideways, in base-canvas pixels.', level: 'advanced', control: { kind: 'slider', min: -2560, max: 2560, step: 1 }, default: '0' },
      { ...base, key: `${k}_DY`, file: 'Offsets.inc', label: `${name}: shift Y`, help: 'Move this module up or down, in base-canvas pixels.', level: 'advanced', control: { kind: 'slider', min: -1600, max: 1600, step: 1 }, default: '0' },
    );
  }
  return out;
}
