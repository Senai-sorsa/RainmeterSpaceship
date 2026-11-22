import { describe, expect, it } from 'vitest';
import { modulesOn } from '../src/modules/modulesOn';

describe('modulesOn', () => {
  it('no param turns nothing on', () => expect(modulesOn(null)('top')).toBe(false));
  it('one name turns only that one on', () => {
    const on = modulesOn('clock');
    expect([on('clock'), on('top')]).toEqual([true, false]);
  });
  it('a comma list turns each on, spaces and case ignored', () => {
    const on = modulesOn('top, Left,,center');
    expect([on('top'), on('left'), on('center'), on('right')]).toEqual([true, true, true, false]);
  });
  it('all turns every one on', () => expect(modulesOn('all')('jarvislog')).toBe(true));
});
