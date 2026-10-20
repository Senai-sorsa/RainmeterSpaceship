export type Level = 'normal' | 'advanced';
export type CategoryId = 'display' | 'layout' | 'apps' | 'sensors' | 'performance' | 'assistant' | 'integrations' | 'system';
export type Control =
  | { kind: 'toggle' }
  | { kind: 'select'; options: { value: string; label: string }[] }
  | { kind: 'slider'; min: number; max: number; step: number }
  | { kind: 'text'; pattern: string; max: number }
  | { kind: 'color' }
  | { kind: 'action'; id: string };
export type WizardStep = 'you' | 'assistant' | 'look' | 'modules' | 'apps' | 'integrations';
export interface SettingDef {
  key: string;
  file: 'Settings.inc' | 'State.inc' | 'Offsets.inc';
  label: string;
  help: string;
  category: CategoryId;
  group: string;
  level: Level;
  control: Control;
  default: string;
  optional?: boolean; // absent from the .inc until first change; the skin's own fallback applies
  virtual?: true; // UI-only row (action or mapped state), never written as a key
  helpId?: string;
  wizard?: WizardStep;
  restartRequired?: boolean;
}
