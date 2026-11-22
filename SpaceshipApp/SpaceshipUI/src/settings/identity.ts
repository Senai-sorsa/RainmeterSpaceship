export const DEFAULT_NAME = 'Jarvis';
export type Checked = { ok: boolean; value: string; reason?: string };

const NAME = /^[A-Za-z0-9]{1,24}$/;
const LABEL = /^[A-Za-z0-9. ]{1,24}$/;

/** Letters/digits only (same rule as the skin's `[^%w]`); empty falls back to the default name. */
export function validateName(s: string): Checked {
  const v = s.trim();
  if (v === '') return { ok: true, value: DEFAULT_NAME };
  if (!NAME.test(v)) return { ok: false, value: v, reason: 'Use 1-24 letters or digits (A-Z, 0-9), no spaces or symbols.' };
  return { ok: true, value: v };
}

/** "Jarvis" -> "J.A.R.V.I.S" */
export function deriveLabel(name: string): string {
  return [...name.replace(/[^A-Za-z0-9]/g, '')].join('.').toUpperCase();
}

/** Display label: 1-24 of letters, digits, dots, spaces; must contain a letter or digit; empty derives from the name. */
export function validateLabel(s: string, name: string = DEFAULT_NAME): Checked {
  const v = s.trim().replace(/ {2,}/g, ' ');
  if (v === '') return { ok: true, value: deriveLabel(name) };
  if (!LABEL.test(v)) return { ok: false, value: v, reason: 'Use 1-24 letters, digits, dots or spaces.' };
  if (!/[A-Za-z0-9]/.test(v)) return { ok: false, value: v, reason: 'Add at least one letter or digit.' };
  return { ok: true, value: v };
}
