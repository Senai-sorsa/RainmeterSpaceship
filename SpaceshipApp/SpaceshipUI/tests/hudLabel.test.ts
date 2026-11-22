import { describe, expect, it, vi } from 'vitest';

describe('hudLabel', () => {
  it('an empty name and an unusable label still give a non-empty label', async () => {
    vi.stubGlobal('location', { search: '', href: 'http://localhost/' });
    const { hudLabel } = await import('../src/Hud');
    expect(hudLabel({ JarvisName: '', AssistantLabel: '###' }).length).toBeGreaterThan(0);
    vi.unstubAllGlobals();
  }, 30000); // first import of the whole HUD is slow
});
