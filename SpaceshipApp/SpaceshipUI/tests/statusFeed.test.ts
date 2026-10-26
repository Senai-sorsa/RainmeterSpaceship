import { describe, expect, it } from 'vitest';
import { acceptStatusUpdate, devStatus, upkeepStatus } from '../src/host/statusFeed';

describe('acceptStatusUpdate', () => {
  // shapes StatusScripts.ToJson sends (ShipCore.Core.Tests/StatusScriptsTests)
  it('takes upkeep and keeps the mail reason', () => {
    acceptStatusUpdate({ type: 'status.update', kind: 'upkeep', updates: 3, upgrades: 12, av: 'WINDOWS DEFENDER', avOn: true });
    expect(upkeepStatus.value).toEqual({ mailWhy: 'no host data', updates: 3 });
  });
  it('takes dev; bad counts become unknown', () => {
    acceptStatusUpdate({ type: 'status.update', kind: 'dev', wsl: 2, llm: '1', tailscale: 'RUNNING', docker: -1 });
    expect(devStatus.value).toEqual({ wsl: 2, llm: undefined });
  });
  it('ignores other messages', () => {
    acceptStatusUpdate({ type: 'status.update', kind: 'other', wsl: 9 });
    acceptStatusUpdate({ type: 'system.metrics', kind: 'dev', wsl: 9 });
    expect(devStatus.value.wsl).toBe(2);
  });
});
