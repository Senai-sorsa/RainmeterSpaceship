import { signal } from '@preact/signals';

/** The host's sys.info, sent once per page: the Windows user and machine names, Hardware.inc's OS, CPU and GPU names, and the primary screen. */
export type SysInfo = { user?: string; host?: string; os?: string; cpu?: string; gpu?: string; display?: string };

export const sysInfo = signal<SysInfo>({});

const KEYS = ['user', 'host', 'os', 'cpu', 'gpu', 'display'] as const;

/** Keeps the short text fields of a sys.info message; anything else is ignored. */
export function acceptSysInfo(m: unknown): void {
  const o = m as Record<string, unknown> | null;
  if (typeof o !== 'object' || o === null || o.type !== 'sys.info') return;
  const info: SysInfo = {};
  for (const k of KEYS) { const v = o[k]; if (typeof v === 'string' && v.length > 0 && v.length <= 80) info[k] = v; }
  sysInfo.value = info;
}
