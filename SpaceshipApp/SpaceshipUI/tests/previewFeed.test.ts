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
    startPreviewFeed();
    expect(sysInfo.value.host).toBe('preview-pc');
    expect(netStatus.value.ping).toBe(7);
    expect(jarvisFeed.value.state).toBe('idle');
    expect(systemMetrics.value?.seq).toBe(1);
    vi.advanceTimersByTime(1000);
    expect(systemMetrics.value?.seq).toBe(3);
  });
});
