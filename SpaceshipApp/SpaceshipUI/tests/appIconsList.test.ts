import { beforeEach, describe, expect, it } from 'vitest';
import { acceptIconsList, appIconUrls, iconList } from '../src/draw/appIcons';

describe('icons.list (host-served app icons)', () => {
  beforeEach(() => { iconList.value = null; });

  it('has no icons until the host sends the list', () => {
    expect(appIconUrls('chrome')).toBeUndefined();
  });

  it('builds versioned URLs on the icons host, with the glow only when it exists', () => {
    acceptIconsList({ type: 'icons.list', ids: ['chrome', 'chrome_glow', 'code'], v: 42 });
    expect(appIconUrls('chrome')).toEqual({ icon: 'https://icons.spaceship.local/chrome.png?v=42', glow: 'https://icons.spaceship.local/chrome_glow.png?v=42' });
    expect(appIconUrls('code')).toEqual({ icon: 'https://icons.spaceship.local/code.png?v=42', glow: undefined });
    expect(appIconUrls('nope')).toBeUndefined();
  });

  it('ignores bad messages and bad names', () => {
    acceptIconsList({ type: 'icons.list', ids: 'chrome' });
    acceptIconsList({ type: 'other', ids: ['chrome'] });
    acceptIconsList({ type: 'icons.list', ids: new Array(4001).fill('a') });
    expect(iconList.value).toBeNull();
    acceptIconsList({ type: 'icons.list', ids: ['../x', 'a/b', 'ok', 7, 'x'.repeat(71)], v: NaN });
    expect([...iconList.value!.names]).toEqual(['ok']);
    expect(iconList.value!.v).toBe(0);
  });
});
