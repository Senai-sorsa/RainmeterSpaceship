import { type Readings, val } from './readings';

// Port of Skins/Spaceship/@Resources/Scripts/sources.lua, with the H.bytes, H.rate and H.mbps formatters from lib.lua.
// Net rates are bytes per second under netDown and netUp. The Lua side reads them from Data\net.txt, which is not ported yet.

export type Reading = { value?: number; text?: string };
export type Source = {
  label: string;
  /** Position of a value on the graph, 0..1. Auto-scaled sources leave this out. */
  frac?: (x: number) => number;
  get: (r: Readings) => Reading;
};

const GIB = 1073741824;
const UNITS = ['B', 'KB', 'MB', 'GB', 'TB'];

const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));
const lin = (lo: number, hi: number) => (x: number) => (x - lo) / (hi - lo);

/** H.bytes: 1024 steps, whole numbers from 100 up and for plain bytes, one decimal below that. */
export function bytes(b: number): string {
  let i = 0;
  while (b >= 1024 && i < UNITS.length - 1) { b /= 1024; i++; }
  return b >= 100 || i === 0 ? `${b.toFixed(0)} ${UNITS[i]}` : `${b.toFixed(1)} ${UNITS[i]}`;
}

export const rate = (bps: number) => `${bytes(bps)}/s`;

/** H.mbps, the long form used by the graph. */
export function mbps(bps: number): string {
  const m = (bps * 8) / 1000000;
  return m >= 99.5 ? `${m.toFixed(0)} Mbps` : `${m.toFixed(1)} Mbps`;
}

export const SOURCES: Record<string, Source> = {
  cpu: { label: 'CPU LOAD', frac: lin(0, 100), get: (r) => { const v = val(r, 'mCPU'); return { value: v, text: `${v.toFixed(0)}%` }; } },
  ram: {
    label: 'MEMORY USED', frac: lin(0, 100), get: (r) => {
      const u = val(r, 'mRamUsed'), t = Math.max(1, val(r, 'mRamTotal', 1));
      return { value: (u / t) * 100, text: `${(u / GIB).toFixed(1)} / ${(t / GIB).toFixed(0)} GB` };
    },
  },
  gpu: { label: 'GPU LOAD', frac: lin(0, 100), get: (r) => { const v = clamp(val(r, 'mGPU'), 0, 100); return { value: v, text: `${v.toFixed(0)}%` }; } },
  vram: {
    label: 'VIDEO MEMORY', frac: lin(0, 12 * GIB), get: (r) => { const b = val(r, 'mVRAM'); return { value: b, text: `${(b / GIB).toFixed(1)} GB` }; },
  },
  cputemp: {
    label: 'CPU TEMP', frac: lin(30, 100), get: (r) => {
      const v = r.mHwCpuTemp;
      return v === undefined ? {} : { value: v, text: `${v.toFixed(0)} C` };
    },
  },
  gputemp: {
    label: 'GPU TEMP', frac: lin(30, 90), get: (r) => {
      const v = r.mHwGpuTemp;
      return v === undefined ? {} : { value: v, text: `${v.toFixed(0)} C` };
    },
  },
  power: {
    label: 'POWER DRAW', frac: lin(0, 160), get: (r) => {
      const c = r.mHwCpuPower, g = r.mHwGpuPower;
      if (c === undefined && g === undefined) return {};
      const v = (c ?? 0) + (g ?? 0);
      return { value: v, text: `${v.toFixed(0)} W` };
    },
  },
  disk: {
    label: 'DISK I/O', get: (r) => { const v = val(r, 'mDiskRead') + val(r, 'mDiskWrite'); return { value: v, text: rate(v) }; },
  },
  netdown: { label: 'NET DOWN', get: (r) => { const v = val(r, 'netDown'); return { value: v, text: mbps(v) }; } },
  netup: { label: 'NET UP', get: (r) => { const v = val(r, 'netUp'); return { value: v, text: mbps(v) }; } },
  battery: { label: 'BATTERY LEVEL', frac: lin(0, 100), get: (r) => { const v = val(r, 'mBattPct'); return { value: v, text: `${v.toFixed(0)}%` }; } },
};

export const ORDER = ['cpu', 'ram', 'gpu', 'vram', 'cputemp', 'gputemp', 'power', 'disk', 'netdown', 'netup', 'battery'];

/** S.next: step through the order with wrap-around in both directions. An unknown id gives the first source. */
export function nextSource(id: string, dir: number): string {
  const i = ORDER.indexOf(id);
  if (i < 0) return ORDER[0];
  const n = ORDER.length;
  // Lua's % floors, so a negative step wraps; JavaScript's does not, hence the second %.
  return ORDER[(((i + dir) % n) + n) % n];
}

/** S.normalise: 0..1 for the graph. Auto-scaled sources are divided by 110% of their peak, starting at 1. */
export function normalise(src: Source, hist: number[]): number[] {
  const { frac } = src;
  if (frac) return hist.map((x) => clamp(frac(x), 0, 1));
  const peak = Math.max(1, ...hist);
  return hist.map((x) => x / (peak * 1.1));
}
