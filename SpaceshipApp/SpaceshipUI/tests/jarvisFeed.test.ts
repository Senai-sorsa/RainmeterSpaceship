import { describe, expect, it } from 'vitest';
import { acceptJarvisUpdate, jarvisFeed, jarvisFeedFrom, jarvisLog, jarvisLogFrom, jarvisPop } from '../src/host/jarvisFeed';

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
  it('keeps the pop request', () => {
    acceptJarvisUpdate({ ...ok, pop: '4 open' });
    expect(jarvisPop.value).toBe('4 open');
  });
});

describe('jarvisLogFrom', () => {
  // the shape JarvisStatus.LogJson sends
  const ok = { type: 'jarvis.log', log: 'U|1|hi\nJ|2|yo\n', live: '', muted: true };
  it('takes the host message', () => expect(jarvisLogFrom(ok)).toEqual({ log: ok.log, live: '', muted: true }));
  it.each([
    ['muted as text', { ...ok, muted: '1' }],
    ['log missing', { ...ok, log: undefined }],
    ['too long', { ...ok, log: 'x'.repeat(80000) }],
  ])('refuses %s', (_, m) => expect(jarvisLogFrom(m)).toBeNull());
  it('is accepted by the same listener', () => {
    acceptJarvisUpdate(ok);
    expect(jarvisLog.value.log).toBe(ok.log);
  });
});
