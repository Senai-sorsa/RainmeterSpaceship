import { describe, expect, it } from 'vitest';
import { acceptAppsState, acceptTopProcs, topProcs, appState, appStates, acceptNetUpdate, acceptSpxUpdate, acceptStatusUpdate, acceptTodoUpdate, consoleStatus, devStatus, netRows, netStatus, spxStatus, todoStatus, upkeepStatus } from '../src/host/statusFeed';

describe('acceptStatusUpdate', () => {
  // shapes StatusScripts.ToJson sends (ShipCore.Core.Tests/StatusScriptsTests)
  it('takes upkeep and keeps the mail reason', () => {
    acceptStatusUpdate({ type: 'status.update', kind: 'upkeep', updates: 3, upgrades: 12, av: 'WINDOWS DEFENDER', avOn: true });
    expect(upkeepStatus.value).toEqual({ mailWhy: 'no host data', updates: 3 });
  });
  it('takes the mail count or its reason, and keeps the update count', () => {
    acceptStatusUpdate({ type: 'status.update', kind: 'mail', unread: 19, why: '' });
    expect(upkeepStatus.value).toEqual({ updates: 3, mail: 19, mailWhy: undefined });
    acceptStatusUpdate({ type: 'status.update', kind: 'mail', unread: null, why: 'off' });
    expect(upkeepStatus.value).toEqual({ updates: 3, mail: undefined, mailWhy: 'off' });
    acceptStatusUpdate({ type: 'status.update', kind: 'mail', unread: -2, why: '<b>x</b>' });
    expect(upkeepStatus.value.mailWhy).toBe('bad reply');
  });
  it('takes dev; bad counts become unknown', () => {
    acceptStatusUpdate({ type: 'status.update', kind: 'dev', wsl: 2, llm: '1', tailscale: 'RUNNING', docker: -1 });
    expect(devStatus.value).toEqual({ wsl: 2, llm: undefined });
  });
  it('takes llt; an odd value becomes unknown', () => {
    acceptStatusUpdate({ type: 'status.update', kind: 'llt', hybrid: 'on-auto', power: 'Performance', refresh: '165', battery: 7, dgpu: 'on' });
    expect(consoleStatus.value).toEqual({ hybrid: 'on-auto', power: '', refresh: '165', battery: '', dgpu: 'on' });
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
    expect(netRows({ ping: 23, lan: null, wan: null }, true).wan).toBe('XX.XXX.XX.XX'); // masked: never looked up
    expect(netRows({ ping: 23, lan: null, wan: null }, false).wan).toBeUndefined();
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

describe('todo', () => {
  it('takes todo.update and drops bad items', () => {
    acceptTodoUpdate({ type: 'todo.update', count: 3, items: [{ text: 'call', due: 100, timed: true }, { text: 5 }, null, { text: 'x', due: 'soon' }] });
    expect(todoStatus.value).toEqual({ count: 3, items: [{ text: 'call', due: 100, timed: true }, { text: 'x', due: null, timed: false }] });
    acceptTodoUpdate({ type: 'todo.update', count: -1, items: [] });
    expect(todoStatus.value.count).toBe(3);
  });
});

describe('apps.state', () => {
  it('keeps valid exe names with 0/1/2 and looks a Proc up as the host keys it', () => {
    acceptAppsState({ type: 'apps.state', states: { 'chrome.exe': 2, 'rasaero ii.exe': 1, '..\\x.exe': 2, 'bad.exe': 7, 'notexe': 1 } });
    expect(appStates.value).toEqual({ 'chrome.exe': 2, 'rasaero ii.exe': 1 });
    expect(appState(appStates.value, 'Chrome')).toBe(2);
    expect(appState(appStates.value, 'RASAero II.exe')).toBe(1);
    expect(appState(appStates.value, '')).toBe(0);
    expect(appState(appStates.value, undefined)).toBe(0);
  });
});

describe('procs.top', () => {
  it('keeps up to five well-formed rows', () => {
    acceptTopProcs({ type: 'procs.top', top: [{ name: 'chrome', cpu: 10, ram: 150 }, { name: 'x', cpu: -1, ram: 1 }, { name: 5 }, null] });
    expect(topProcs.value).toEqual([{ name: 'chrome', cpu: 10, ram: 150 }]);
    acceptTopProcs({ type: 'other', top: [] });
    expect(topProcs.value).toHaveLength(1);
  });
});
