export type PillState = 'offline' | 'linked' | 'warn' | 'error';
const TEXT: Record<PillState, string> = { offline: 'Offline', linked: 'Linked', warn: 'Warning', error: 'Error' };

/** Always carries a text label, so state never rests on colour alone. */
export function StatusPill({ state, text }: { state: PillState; text?: string }) {
  return <span class={`pill pill-${state}`}>{text ?? TEXT[state]}</span>;
}
