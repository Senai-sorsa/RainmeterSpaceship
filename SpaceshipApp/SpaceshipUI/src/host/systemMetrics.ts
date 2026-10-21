import { signal } from '@preact/signals';

/** One reading from the host's system.metrics message. Null means not available right now. */
export type SystemMetrics = {
  seq: number;
  cpuPercent: number | null;
  memoryPercent: number;
  uptimeMs: number;
  onAc: boolean | null;
  batteryPercent: number | null;
  hw: Record<string, number | null>;
};

const isNum = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v);
const isPct = (v: unknown): v is number => isNum(v) && v >= 0 && v <= 100;
const isObj = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v);

/** The reading, or null for anything that is not a valid system.metrics message. */
export function systemMetricsFrom(m: unknown): SystemMetrics | null {
  if (!isObj(m) || m.type !== 'system.metrics') return null;
  const { seq, cpuPercent, memoryPercent, uptimeMs, onAc, batteryPercent, hw } = m;
  if (!isNum(seq) || !(cpuPercent === null || isPct(cpuPercent)) || !isPct(memoryPercent)) return null;
  if (!isNum(uptimeMs) || uptimeMs < 0) return null;
  if (!(onAc === null || typeof onAc === 'boolean') || !(batteryPercent === null || isPct(batteryPercent))) return null;
  if (!isObj(hw) || !Object.values(hw).every((v) => v === null || isNum(v))) return null;
  return { seq, cpuPercent, memoryPercent, uptimeMs, onAc, batteryPercent, hw: hw as Record<string, number | null> };
}

export const systemMetrics = signal<SystemMetrics | null>(null);

/** The onMessage callback: keeps the latest valid reading and ignores everything else. */
export function acceptSystemMetrics(m: unknown): void {
  const reading = systemMetricsFrom(m);
  if (reading) systemMetrics.value = reading;
}
