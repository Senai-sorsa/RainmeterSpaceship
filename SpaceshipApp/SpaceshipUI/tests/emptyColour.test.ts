import { describe, expect, it } from 'vitest';
import { MockHost } from '../src/host/HostBridge';
import { DEFS } from '../src/settings/instance';
import { createSettingsStore } from '../src/settings/store';

describe('empty colour', () => {
  it('is valid only for colour rows whose default is empty (follow the theme)', () => {
    const host = new MockHost({ storage: null });
    const store = createSettingsStore(host, DEFS, { throttleMs: 0 });
    store.set('JarvisColorIdle', '1,2,3');
    store.set('JarvisColorIdle', '');
    expect(store.error.value).toBeNull();
    expect(store.values.value.JarvisColorIdle).toBe('');
    store.set('ColorAccent', '');
    expect(store.error.value?.key).toBe('ColorAccent');
  });
});
