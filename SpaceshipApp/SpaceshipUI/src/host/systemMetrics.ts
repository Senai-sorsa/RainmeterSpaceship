import { signal } from '@preact/signals';
import type { Readings } from '../modules/readings';

/** One reading from the host's system.metrics message. Null means not available right now. */
export type SystemMetrics = {
  seq: number;
  cpuPercent: number | null;
  memoryPercent: number;
  uptimeMs: number;
  onAc: boolean | null;
  batteryPercent: number | null;
  netDown: number | null;
  netUp: number | null;
  /** Audio bands, 0 to 1, low to high. Null while the audio capture is not running. */
  spectrum: number[] | null;
  /** Watched process name to whether it is running. */
  processes: Record<string, boolean>;
  hw: Record<string, number | null>;
};

const isNum = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v);
const isPct = (v: unknown): v is number => isNum(v) && v >= 0 && v <= 100;
const isRate = (v: unknown): v is number => isNum(v) && v >= 0;
const isUnit = (v: unknown): v is number => isNum(v) && v >= 0 && v <= 1;
const isObj = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v);

/** The reading, or null for anything that is not a valid system.metrics message. */
export function systemMetricsFrom(m: unknown): SystemMetrics | null {
  if (!isObj(m) || m.type !== 'system.metrics') return null;
  const { seq, cpuPercent, memoryPercent, uptimeMs, onAc, batteryPercent, netDown, netUp, spectrum, processes, hw } = m;
  if (!isNum(seq) || !(cpuPercent === null || isPct(cpuPercent)) || !isPct(memoryPercent)) return null;
  if (!isNum(uptimeMs) || uptimeMs < 0) return null;
  if (!(onAc === null || typeof onAc === 'boolean') || !(batteryPercent === null || isPct(batteryPercent))) return null;
  if (!(netDown === null || isRate(netDown)) || !(netUp === null || isRate(netUp))) return null;
  if (!(spectrum === null || (Array.isArray(spectrum) && spectrum.length <= 64 && spectrum.every(isUnit)))) return null;
  if (!isObj(processes) || !Object.values(processes).every((v) => typeof v === 'boolean')) return null;
  if (!isObj(hw) || !Object.values(hw).every((v) => v === null || isNum(v))) return null;
  return {
    seq, cpuPercent, memoryPercent, uptimeMs, onAc, batteryPercent, netDown, netUp, spectrum,
    processes: processes as Record<string, boolean>, hw: hw as Record<string, number | null>,
  };
}

/** The skin measures the host supplies (mCPU, mBattPct, mAC, netDown, netUp, and HW_X as mHwX). Unavailable values are left out, so the sources see them as missing. */
export function readingsFrom(m: SystemMetrics): Readings {
  const r: Readings = {};
  r.mRamPct = m.memoryPercent;
  if (m.cpuPercent !== null) r.mCPU = m.cpuPercent;
  if (m.batteryPercent !== null) r.mBattPct = m.batteryPercent;
  if (m.onAc !== null) r.mAC = m.onAc ? 1 : 0;
  if (m.netDown !== null) r.netDown = m.netDown;
  if (m.netUp !== null) r.netUp = m.netUp;
  r.mUptime = m.uptimeMs / 1000;
  if (m.spectrum !== null && m.spectrum.length > 0) {
    m.spectrum.forEach((v, i) => { r[`mBand${i}`] = v; });
    // shortcut: RMS and peak are derived from the bands (mean and max), not measured by the host, upgrade if the audio module needs the real values
    r.mRMS = m.spectrum.reduce((a, b) => a + b, 0) / m.spectrum.length;
    r.mPeak = Math.max(...m.spectrum);
  }
  for (const [k, v] of Object.entries(m.hw)) if (k.startsWith('HW_') && v !== null) r[`mHw${k.slice(3)}`] = v;
  return r;
}

export const systemMetrics = signal<SystemMetrics | null>(null);

/** The onMessage callback: keeps the latest valid reading and ignores everything else. */
export function acceptSystemMetrics(m: unknown): void {
  const reading = systemMetricsFrom(m);
  if (reading) systemMetrics.value = reading;
}
