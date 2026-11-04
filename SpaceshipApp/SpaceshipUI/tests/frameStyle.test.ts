import { describe, expect, it } from 'vitest';
import { MockHost } from '../src/host/HostBridge';
import { DEFS } from '../src/settings/instance';
import { applyFrameStyle, frameStyleOf, frameVirtuals, type FrameStyle } from '../src/settings/frameStyle';
import { createSettingsStore } from '../src/settings/store';

describe('frame style', () => {
  it('round-trips all four styles', () => {
    for (const s of ['rendered', 'picture', 'fitted', 'none'] as FrameStyle[]) expect(frameStyleOf(applyFrameStyle(s))).toBe(s);
  });
  it('the Cockpit frame row offers rendered, picture, picture (fitted) and none, in that order', () => {
    const d = DEFS.find((x) => x.key === 'frameStyle')!;
    expect(d.control.kind).toBe('select');
    expect((d.control as { options: { value: string; label: string }[] }).options).toEqual([
      { value: 'rendered', label: 'Rendered' }, { value: 'picture', label: 'Picture' }, { value: 'fitted', label: 'Picture (fitted)' }, { value: 'none', label: 'None' },
    ]);
  });
  it('switching to fitted writes UseShipImage and PictureFit, and back to picture clears PictureFit', () => {
    const host = new MockHost({ storage: null, seed: { UseShipImage: '0', FrameOff: '0', PictureFit: '0' } });
    const store = createSettingsStore(host, DEFS, { virtuals: frameVirtuals, throttleMs: 0 });
    store.set('frameStyle', 'fitted'); store.flush();
    expect(store.values.value.frameStyle).toBe('fitted');
    expect(host.sent.filter((m) => m.type === 'config.set').map((m) => m.key + '=' + m.value).sort()).toEqual(['PictureFit=1', 'UseShipImage=1']);
    store.set('frameStyle', 'picture'); store.flush();
    expect(store.values.value.frameStyle).toBe('picture');
    expect(host.sent.filter((m) => m.type === 'config.set').map((m) => m.key + '=' + m.value).slice(-1)).toEqual(['PictureFit=0']);
  });
  it('FrameOff wins over UseShipImage; missing keys mean rendered', () => {
    expect(frameStyleOf({ FrameOff: '1', UseShipImage: '1' })).toBe('none');
    expect(frameStyleOf({})).toBe('rendered');
    expect(frameStyleOf({ UseShipImage: '1' })).toBe('picture'); // PictureFit missing: the plain picture
    expect(frameStyleOf({ UseShipImage: '1', PictureFit: '1' })).toBe('fitted');
    expect(frameStyleOf({ UseShipImage: '0', PictureFit: '1' })).toBe('rendered'); // fitted needs the picture on
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
    expect(store.visibleDefs().some((d) => d.key === 'UseShipImage' || d.key === 'FrameOff' || d.key === 'PictureFit')).toBe(false);
    expect(store.search('Frame uses picture')).toEqual([]);
  });
});
