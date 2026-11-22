import { describe, expect, it } from 'vitest';
import { FIXES, diagnose } from '../src/help/diagnosis';
import { messageProblem } from '../src/host/contract';

const base = { jarvis: { state: 'idle' }, notices: [] };

describe('help diagnosis', () => {
  it('says all is well when nothing is wrong', () => {
    expect(diagnose(base).map((f) => f.id)).toEqual(['none']);
  });
  it('offers to start JARVIS when offline, but not when Python is missing', () => {
    expect(diagnose({ ...base, jarvis: { state: 'offline' } })[0]).toMatchObject({ id: 'jarvis-offline', fix: 'start_jarvis' });
    const f = diagnose({ ...base, jarvis: { state: 'offline', note: 'NO PYTHON' } })[0];
    expect(f.level).toBe('error');
    expect(f.fix).toBeUndefined();
  });
  it('flags a failing mail check but not off or unknown', () => {
    expect(diagnose({ ...base, mailWhy: 'ERR 401' })[0].fix).toBe('recheck_mail');
    expect(diagnose({ ...base, mailWhy: 'off' })[0].id).toBe('none');
    expect(diagnose({ ...base, mailWhy: 'no host data' })[0].id).toBe('none');
  });
  it('lists host notices', () => {
    expect(diagnose({ ...base, notices: [{ source: 'apps', level: 'warn', text: 'x' }] })[0]).toMatchObject({ id: 'notice-apps', level: 'warn' });
  });
  it('every fix finding exists in the whitelist and every fix message passes the contract', () => {
    const all = diagnose({ ...base, jarvis: { state: 'offline' }, mailWhy: 'e', notices: [{ source: 's', level: 'error', text: 't' }] });
    for (const f of all) if (f.fix) expect(Object.keys(FIXES)).toContain(f.fix);
    for (const x of Object.values(FIXES)) if (x.msg) expect(messageProblem(x.msg)).toBeNull();
  });
});
