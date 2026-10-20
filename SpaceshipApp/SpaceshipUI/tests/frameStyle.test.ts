import { describe, expect, it } from 'vitest';
import { MockHost } from '../src/host/HostBridge';
import { DEFS } from '../src/settings/instance';
import { applyFrameStyle, frameStyleOf, frameVirtuals, type FrameStyle } from '../src/settings/frameStyle';
import { createSettingsStore } from '../src/settings/store';

describe('frame style', () => {
  it('round-trips all three styles', () => {
    for (const s of ['rendered', 'picture', 'none'] as FrameStyle[]) expect(frameStyleOf(applyFrameStyle(s))).toBe(s);
  });
  it('FrameOff wins over UseShipImage; missing keys mean rendered', () => {
    expect(frameStyleOf({ FrameOff: '1', UseShipImage: '1' })).toBe('none');
    expect(frameStyleOf({})).toBe('rendered');
  });
  it('the store writes both real keys for one undoable step and never lists them', () => {
    const host = new MockHost({ storage: null, seed: { UseShipImage: '0', FrameOff: '0' } });
    const store = createSettingsStore(host, DEFS, { virtuals: frameVirtuals, throttleMs: 0 });
    store.set('frameStyle', 'picture');
    store.flush();
    expect(store.values.value.frameStyle).toBe('picture');
    expect(host.sent.filter((m) => m.type === 'config.set').map((m) => `${m.key}=${m.value}`).sort()).toEqual(['UseShipImage=1']);
    store.undo();
    expect(store.values.value.frameStyle).toBe('rendered');
    expect(store.visibleDefs().some((d) => d.key === 'UseShipImage' || d.key === 'FrameOff')).toBe(false);
    expect(store.search('Frame uses picture')).toEqual([]);
  });
});
