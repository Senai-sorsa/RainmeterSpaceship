import { describe, expect, it } from 'vitest';
import { acceptJarvisUpdate, jarvisFeed, jarvisFeedFrom } from '../src/host/jarvisFeed';

describe('jarvisFeedFrom', () => {
  // the shape JarvisStatus.ToJson sends (ShipCore.Core.Tests/JarvisStatusTests)
  const ok = { type: 'jarvis.update', state: 'speaking', level: 0.642, say: 'Good evening', err: '' };
  it('takes the host message', () => expect(jarvisFeedFrom(ok)).toEqual({ state: 'speaking', level: 0.642 }));
  it.each([
    ['other type', { ...ok, type: 'system.metrics' }],
    ['unknown state', { ...ok, state: 'dancing' }],
    ['level above 1', { ...ok, level: 2 }],
    ['level as text', { ...ok, level: '0.5' }],
    ['null', null],
  ])('refuses %s', (_, m) => expect(jarvisFeedFrom(m)).toBeNull());
  it('keeps the last good feed', () => {
    acceptJarvisUpdate(ok);
    acceptJarvisUpdate({ ...ok, state: 'bad' });
    expect(jarvisFeed.value).toEqual({ state: 'speaking', level: 0.642 });
  });
});
