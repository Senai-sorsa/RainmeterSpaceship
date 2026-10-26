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
  /** The busiest GPU engine, 0 to 100, as Task Manager counts it. Null when the counter is unavailable; older hosts leave it out. */
  gpuPercent: number | null;
  /** Physical memory in bytes; older hosts leave both out. */
  memoryTotal: number | null;
  memoryUsed: number | null;
  /** Time since the last keyboard or mouse input. */
  idleMs: number | null;
  /** Drive C: in bytes, all disks' I/O in bytes per second, the screen's refresh rate; older hosts leave them out. */
  driveTotal: number | null;
  driveFree: number | null;
  diskIo: number | null;
  refreshHz: number | null;
  /** The default speaker and mic: level 0 to 100, mute flag, and the speaker's Windows name. */
  volume: number | null;
  volumeMuted: boolean | null;
  audioDevice: string | null;
  mic: number | null;
  micMuted: boolean | null;
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
  const { seq, cpuPercent, memoryPercent, uptimeMs, onAc, batteryPercent, netDown, netUp, spectrum, processes, gpuPercent = null, memoryTotal = null, memoryUsed = null, idleMs = null, hw } = m;
  const { driveTotal = null, driveFree = null, diskIo = null, refreshHz = null, volume = null, volumeMuted = null, audioDevice = null, mic = null, micMuted = null } = m;
  if (![driveTotal, driveFree, diskIo, refreshHz].every((v) => v === null || isRate(v))) return null;
  if (![volume, mic].every((v) => v === null || isPct(v)) || ![volumeMuted, micMuted].every((v) => v === null || typeof v === 'boolean')) return null;
  if (!(audioDevice === null || (typeof audioDevice === 'string' && audioDevice.length <= 256))) return null;
  if (!isNum(seq) || !(cpuPercent === null || isPct(cpuPercent)) || !isPct(memoryPercent)) return null;
  if (!isNum(uptimeMs) || uptimeMs < 0) return null;
  if (!(onAc === null || typeof onAc === 'boolean') || !(batteryPercent === null || isPct(batteryPercent))) return null;
  if (!(netDown === null || isRate(netDown)) || !(netUp === null || isRate(netUp))) return null;
  if (!(spectrum === null || (Array.isArray(spectrum) && spectrum.length <= 64 && spectrum.every(isUnit)))) return null;
  if (!isObj(processes) || !Object.values(processes).every((v) => typeof v === 'boolean')) return null;
  if (!(gpuPercent === null || isPct(gpuPercent))) return null;
  if (![memoryTotal, memoryUsed, idleMs].every((v) => v === null || isRate(v))) return null;
  if (!isObj(hw) || !Object.values(hw).every((v) => v === null || isNum(v))) return null;
  return {
    seq, cpuPercent, memoryPercent, uptimeMs, onAc, batteryPercent, netDown, netUp, spectrum,
    processes: processes as Record<string, boolean>, gpuPercent,
    memoryTotal: memoryTotal as number | null, memoryUsed: memoryUsed as number | null, idleMs: idleMs as number | null, hw: hw as Record<string, number | null>,
    driveTotal: driveTotal as number | null, driveFree: driveFree as number | null, diskIo: diskIo as number | null, refreshHz: refreshHz as number | null,
    volume: volume as number | null, volumeMuted: volumeMuted as boolean | null, audioDevice: audioDevice as string | null,
    mic: mic as number | null, micMuted: micMuted as boolean | null,
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
  if (m.gpuPercent !== null) r.mGPU = m.gpuPercent;
  if (m.memoryTotal) { r.mRamTotal = m.memoryTotal; r.mRamUsed = m.memoryUsed ?? 0; }
  if (m.idleMs !== null) r.mIdle = m.idleMs / 1000;
  if (m.driveTotal) { r.mD1Total = m.driveTotal; r.mD1Free = m.driveFree ?? 0; }
  if (m.diskIo !== null) r.mDiskIO = m.diskIo;
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
