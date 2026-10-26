import { signal } from '@preact/signals';
import type { UpkeepInput } from '../modules/upkeep';
import type { DevInput } from '../modules/dev';
import type { ConsoleState } from '../modules/console';

// The host's status.update messages (Scripts\upkeep.ps1 and dev.ps1 output). -1 = unknown, which the blocks show as --.
const count = (v: unknown) => (Number.isInteger(v) && (v as number) >= -1 ? (v as number) : undefined);

export const upkeepStatus = signal<UpkeepInput>({ mailWhy: 'no host data' });
export const devStatus = signal<DevInput>({});
/** status.ps1 (Legion Toolkit and the NVIDIA device), lower-cased by the host. '' = unknown. */
export const consoleStatus = signal<ConsoleState>({ hybrid: '', power: '', refresh: '', battery: '', dgpu: '' });
const word = (v: unknown) => (typeof v === 'string' && /^[a-z0-9 ._-]{0,40}$/.test(v) ? v : '');

export function acceptStatusUpdate(m: unknown): void {
  if (typeof m !== 'object' || m === null) return;
  const o = m as Record<string, unknown>;
  if (o.type !== 'status.update') return;
  // mail stays unknown: Gmail needs the DPAPI slice
  if (o.kind === 'upkeep') upkeepStatus.value = { ...upkeepStatus.value, updates: count(o.updates) };
  else if (o.kind === 'dev') devStatus.value = { wsl: count(o.wsl), llm: count(o.llm) };
  else if (o.kind === 'llt') consoleStatus.value = { hybrid: word(o.hybrid), power: word(o.power), refresh: word(o.refresh), battery: word(o.battery), dgpu: word(o.dgpu) };
}

/** The host's net.update: ping in ms (0 = lost), LAN and WAN ('' = none / lookup failed). null = not read yet. */
export type NetStatus = { ping: number | null; lan: string | null; wan: string | null };
export const netStatus = signal<NetStatus>({ ping: null, lan: null, wan: null });

const ipv4 = (v: unknown) => (v === '' || (typeof v === 'string' && /^\d{1,3}(\.\d{1,3}){3}$/.test(v)) ? v : null);

export function acceptNetUpdate(m: unknown): void {
  if (typeof m !== 'object' || m === null) return;
  const o = m as Record<string, unknown>;
  if (o.type !== 'net.update') return;
  const ping = Number.isInteger(o.ping) && (o.ping as number) >= 0 ? (o.ping as number) : null;
  netStatus.value = { ping, lan: ipv4(o.lan), wan: ipv4(o.wan) };
}

/** The rows sysinfo.lua shows: NONE without a LAN address, OFFLINE when the ping is lost and the WAN lookup failed, ... while waiting. Masked digits become X (IpMask). */
export function netRows(n: NetStatus, mask: boolean): { ping?: number; lan?: string; wan?: string } {
  const hide = (ip: string) => (mask ? ip.replace(/\d/g, 'X') : ip);
  const lost = n.ping === 0;
  return {
    ping: n.ping ?? undefined,
    lan: n.lan === null ? undefined : n.lan === '' ? 'NONE' : hide(n.lan),
    // the host skips the public-IP lookup while masked, so a masked WAN shows the mask once the ping is in
    wan: n.wan === null ? (lost ? 'OFFLINE' : mask && n.ping != null ? 'XX.XXX.XX.XX' : undefined) : n.wan === '' ? (lost ? 'OFFLINE' : '...') : hide(n.wan),
  };
}

/** The host's spx.update (Yahoo ^GSPC): the centre HUD's day-change tape. Empty until the first good reply. */
export type SpxStatus = { spxPrice?: number; spxPrev?: number; spxOpen?: boolean };
export const spxStatus = signal<SpxStatus>({});

const positive = (v: unknown) => typeof v === 'number' && Number.isFinite(v) && v > 0;

export function acceptSpxUpdate(m: unknown): void {
  if (typeof m !== 'object' || m === null) return;
  const o = m as Record<string, unknown>;
  if (o.type !== 'spx.update' || !positive(o.price) || !positive(o.prev)) return;
  spxStatus.value = { spxPrice: o.price as number, spxPrev: o.prev as number, spxOpen: o.open === true };
}

/** The host's todo.update (ObsidianTodo note, TodoNote.cs): open count and the first few items, soonest due first. */
export type TodoItem = { text: string; due: number | null; timed: boolean };
export type TodoStatus = { count: number; items: TodoItem[] };
export const todoStatus = signal<TodoStatus>({ count: 0, items: [] });

export function acceptTodoUpdate(m: unknown): void {
  if (typeof m !== 'object' || m === null) return;
  const o = m as Record<string, unknown>;
  if (o.type !== 'todo.update' || !Number.isInteger(o.count) || (o.count as number) < 0 || !Array.isArray(o.items)) return;
  const items = o.items.slice(0, 4).flatMap((it: unknown): TodoItem[] => {
    const t = it as Record<string, unknown> | null;
    if (!t || typeof t.text !== 'string' || t.text === '') return [];
    return [{ text: t.text.slice(0, 120), due: Number.isInteger(t.due) ? (t.due as number) : null, timed: t.timed === true }];
  });
  todoStatus.value = { count: Math.max(o.count as number, items.length), items };
}
