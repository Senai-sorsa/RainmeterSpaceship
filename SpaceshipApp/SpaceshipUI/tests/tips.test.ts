import { describe, expect, it } from 'vitest';
import { targetTip } from '../src/modules/target';
import { slotTip } from '../src/modules/hit';
import type { App } from '../src/modules/apps';

const app = (missing: boolean) => ({ id: 'a', name: 'Steam', missing } as App);

describe('hover captions', () => {
  it('names the targeted process and what it takes', () => {
    expect(targetTip({ name: 'chrome.exe', cpu: 12.4, ram: 840 * 1048576 })).toBe('chrome.exe   12% CPU   840 MB');
    expect(targetTip({ name: 'idle', cpu: 0, ram: 0 })).toBe('idle   0% CPU');
    expect(targetTip({})).toBe('');
  });
  it('shows the to-do instead while there is one', () => {
    expect(targetTip({ name: 'x', todos: [{ text: 'Pay rent', due: null, timed: false }], todoCount: 3 })).toBe('Pay rent   3 open');
  });
  it('only speaks up for a missing app or an empty slot', () => {
    expect(slotTip({ kind: 'app', app: app(false) }, 2)).toBeUndefined();
    expect(slotTip({ kind: 'app', app: app(true) }, 2)).toBe('Steam not installed or moved');
    expect(slotTip(undefined, 6)).toBe('Slot 6 unassigned');
  });
});
