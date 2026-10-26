import { describe, expect, it } from 'vitest';
import { acceptNetUpdate, acceptSpxUpdate, acceptStatusUpdate, devStatus, netRows, netStatus, spxStatus, upkeepStatus } from '../src/host/statusFeed';

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

describe('net', () => {
  it('takes net.update and refuses non-addresses', () => {
    acceptNetUpdate({ type: 'net.update', ping: 23, lan: '192.168.1.20', wan: '<b>' });
    expect(netStatus.value).toEqual({ ping: 23, lan: '192.168.1.20', wan: null });
  });
  it('masks by default and reads lost / none like sysinfo.lua', () => {
    expect(netRows({ ping: 23, lan: '192.168.1.20', wan: '203.0.113.7' }, true)).toEqual({ ping: 23, lan: 'XXX.XXX.X.XX', wan: 'XXX.X.XXX.X' });
    expect(netRows({ ping: 23, lan: '10.0.0.2', wan: '' }, false)).toEqual({ ping: 23, lan: '10.0.0.2', wan: '...' });
    expect(netRows({ ping: 0, lan: '', wan: '' }, true)).toEqual({ ping: 0, lan: 'NONE', wan: 'OFFLINE' });
    expect(netRows({ ping: null, lan: null, wan: null }, true)).toEqual({ ping: undefined, lan: undefined, wan: undefined });
  });
});

describe('spx', () => {
  it('takes spx.update and keeps the last good one', () => {
    acceptSpxUpdate({ type: 'spx.update', price: 5800.5, prev: 5750, open: true });
    acceptSpxUpdate({ type: 'spx.update', price: 'x', prev: 5750, open: false });
    acceptSpxUpdate({ type: 'spx.update', price: 1, prev: 0, open: false });
    expect(spxStatus.value).toEqual({ spxPrice: 5800.5, spxPrev: 5750, spxOpen: true });
  });
});
