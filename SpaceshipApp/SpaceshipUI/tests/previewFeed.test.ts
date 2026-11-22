import { afterEach, describe, expect, it, vi } from 'vitest';
import { startPreviewFeed } from '../src/host/previewFeed';
import { systemMetrics } from '../src/host/systemMetrics';
import { sysInfo } from '../src/host/sysInfo';
import { jarvisFeed } from '../src/host/jarvisFeed';
import { netStatus } from '../src/host/statusFeed';

afterEach(() => { vi.clearAllTimers(); vi.useRealTimers(); });

describe('preview feed', () => {
  it('every sample passes the host validators, and the metrics keep coming', () => {
    vi.useFakeTimers();
    const stop = startPreviewFeed();
    expect(sysInfo.value.host).toBe('preview-pc');
    expect(netStatus.value.ping).toBe(7);
    expect(jarvisFeed.value.state).toBe('idle');
    expect(systemMetrics.value?.seq).toBe(1);
    vi.advanceTimersByTime(1000);
    expect(systemMetrics.value?.seq).toBe(3);
    stop();
  });
});

describe('preview feed lifecycle', () => {
  it('starting twice keeps one interval pair, and the returned stop clears them', () => {
    vi.useFakeTimers();
    const spy = vi.spyOn(globalThis, 'setInterval');
    const stop = startPreviewFeed();
    const first = spy.mock.calls.length;
    expect(first).toBeGreaterThan(0);
    startPreviewFeed();
    expect(spy.mock.calls.length).toBe(first);
    expect(typeof stop).toBe('function');
    stop();
    expect(vi.getTimerCount()).toBe(0);
    spy.mockRestore();
  });
});
