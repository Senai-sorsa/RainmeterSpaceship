import { describe, expect, it, vi } from 'vitest';
import { host } from '../src/settings/instance';
import { orbClick } from '../src/modules/JarvisModule';

describe('orbClick (jarvis.lua OnClick)', () => {
  it('wakes when idle, cancels otherwise, once a second, never offline or disabled', () => {
    const send = vi.spyOn(host, 'send').mockImplementation(() => {});
    expect(orbClick(true, 'idle', 10_000)).toBe('wake');
    expect(orbClick(true, 'listening', 10_500)).toBeNull(); // within a second
    expect(orbClick(true, 'speaking', 11_000)).toBe('cancel');
    expect(orbClick(true, 'offline', 20_000)).toBeNull();
    expect(orbClick(false, 'idle', 30_000)).toBeNull();
    expect(send.mock.calls).toEqual([[{ type: 'jarvis.cmd', cmd: 'wake' }], [{ type: 'jarvis.cmd', cmd: 'cancel' }]]);
    send.mockRestore();
  });
});
