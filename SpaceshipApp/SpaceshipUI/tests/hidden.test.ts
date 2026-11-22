import { describe, expect, it } from 'vitest';
import { hiddenZones, visible } from '../src/modules/hidden';

describe('Off_ module toggles', () => {
  it('lists the zones of each key set to 1', () => {
    expect(hiddenZones({ Off_TopBattery: '1', Off_LeftCategory: '1', Off_RightDev: '0' })).toBe('L_tabs,L_category,L_dots,T_battery');
    expect(hiddenZones({})).toBe('');
  });
  it('blanks hidden zones and slots, and returns the same table when nothing is hidden', () => {
    const Z = { a: { id: 'L_app1' }, b: { id: 'T_battery' }, slots: [{ id: 'L_app1' }, { id: 'L_app2' }] };
    expect(visible(Z, '')).toBe(Z);
    expect(visible(Z, 'L_app1')).toEqual({ a: undefined, b: { id: 'T_battery' }, slots: [undefined, { id: 'L_app2' }] });
  });
});
