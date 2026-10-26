import { describe, expect, it } from 'vitest';
import { openSlot } from '../src/modules/hit';
import { drawerOpen } from '../src/modules/overlays';
import type { App, Cat } from '../src/modules/apps';

describe('slot click (slot.lua OnClick, row style)', () => {
  const app = { id: 'a', name: 'A' } as App;
  it('opens the drawer on a folder that has apps', () => {
    drawerOpen.value = null;
    openSlot({ kind: 'cat', cat: { id: 'dev', apps: [app] } as unknown as Cat }, app);
    expect(drawerOpen.value).toEqual({ focus: 'dev' });
  });
  it('leaves the drawer shut for an empty folder', () => {
    drawerOpen.value = null;
    openSlot({ kind: 'cat', cat: { id: 'none', apps: [] } as unknown as Cat }, undefined);
    expect(drawerOpen.value).toBeNull();
  });
});
