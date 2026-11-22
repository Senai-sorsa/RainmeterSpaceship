import { describe, it, expect } from 'vitest';
import { deriveLabel, validateLabel, validateName } from '../src/settings/identity';

describe('identity', () => {
  it('deriveLabel dots the letters', () => {
    expect(deriveLabel('Jarvis')).toBe('J.A.R.V.I.S');
    expect(deriveLabel('Clover')).toBe('C.L.O.V.E.R');
    expect(deriveLabel('R2D2')).toBe('R.2.D.2');
  });
  it('validateName("") falls back to Jarvis', () => {
    expect(validateName('')).toEqual({ ok: true, value: 'Jarvis' });
    expect(validateName('   ').value).toBe('Jarvis');
  });
  it('validateName rejects hostile and odd text', () => {
    expect(validateName('<script>').ok).toBe(false);
    expect(validateName('a'.repeat(200)).ok).toBe(false);
    const z = validateName('Zoë');
    expect(z.ok).toBe(false);
    expect(z.reason).toMatch(/letters or digits/);
    expect(validateName('two words').ok).toBe(false);
    expect(validateName(' Clover ')).toEqual({ ok: true, value: 'Clover' });
  });
  it('validateLabel accepts dotted labels and normalises spaces', () => {
    expect(validateLabel('C.L.O.V.E.R').ok).toBe(true);
    expect(validateLabel('  A  B ').value).toBe('A B');
  });
  it('validateLabel rejects dots-only, symbols and overlong text', () => {
    expect(validateLabel('....').ok).toBe(false);
    expect(validateLabel('<b>x</b>').ok).toBe(false);
    expect(validateLabel('x'.repeat(25)).ok).toBe(false);
  });
  it('validateLabel("") derives from the name', () => {
    expect(validateLabel('', 'Clover').value).toBe('C.L.O.V.E.R');
    expect(validateLabel('').value).toBe('J.A.R.V.I.S');
  });
});
