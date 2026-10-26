import { signal } from '@preact/signals';
import type { UpkeepInput } from '../modules/upkeep';
import type { DevInput } from '../modules/dev';

// The host's status.update messages (Scripts\upkeep.ps1 and dev.ps1 output). -1 = unknown, which the blocks show as --.
const count = (v: unknown) => (Number.isInteger(v) && (v as number) >= -1 ? (v as number) : undefined);

export const upkeepStatus = signal<UpkeepInput>({ mailWhy: 'no host data' });
export const devStatus = signal<DevInput>({});

export function acceptStatusUpdate(m: unknown): void {
  if (typeof m !== 'object' || m === null) return;
  const o = m as Record<string, unknown>;
  if (o.type !== 'status.update') return;
  // mail stays unknown: Gmail needs the DPAPI slice
  if (o.kind === 'upkeep') upkeepStatus.value = { ...upkeepStatus.value, updates: count(o.updates) };
  else if (o.kind === 'dev') devStatus.value = { wsl: count(o.wsl), llm: count(o.llm) };
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
    wan: n.wan === null ? (lost ? 'OFFLINE' : undefined) : n.wan === '' ? (lost ? 'OFFLINE' : '...') : hide(n.wan),
  };
}
