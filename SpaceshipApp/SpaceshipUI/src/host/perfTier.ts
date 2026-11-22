import { effect, signal, type ReadonlySignal } from '@preact/signals';
import type { SystemMetrics } from './systemMetrics';

/** Where the tier stands between readings: the tier in use and since when a change has been wanted (seconds). */
export type TierState = { tier: number; upSince: number | null; downSince: number | null };
export const tierState = (): TierState => ({ tier: 0, upSince: null, downSince: null });

const num = (v: Record<string, string>, k: string, d: number) => {
  const n = Number(v[k]);
  return v[k] !== undefined && v[k] !== '' && Number.isFinite(n) ? n : d;
};

/**
 * controller.lua wanted(): the tier the GPU load asks for going up (at the thresholds) and going down (15 below them),
 * floored on battery. The skin passes -15, which puts the down thresholds 15 above and makes a load between the two
 * flip the tier every 25 s; +15 is the hysteresis it meant.
 */
export function wanted(gpu: number, ac: boolean, v: Record<string, string>): [up: number, down: number] {
  const lite = num(v, 'TierLite', 50), low = num(v, 'TierLow', 75), st = num(v, 'TierStealth', 85);
  const level = (margin: number) => (gpu >= st - margin ? 3 : gpu >= low - margin ? 2 : gpu >= lite - margin ? 1 : 0);
  const minT = ac ? 0 : num(v, 'BatteryMinTier', 1);
  return [Math.max(level(0), minT), Math.max(level(15), minT)];
}

/**
 * One controller.lua tick: PerfOverride 0-3 forces that tier; Auto (-1) goes up once the higher tier has been wanted
 * for 5 s and down one step once a lower one has been wanted for 20 s. A missing GPU reading counts as 0, as in the skin.
 */
export function tierStep(s: TierState, gpu: number | null, ac: boolean | null, v: Record<string, string>, now: number): number {
  const ov = num(v, 'PerfOverride', -1);
  if (ov >= 0) { s.tier = Math.min(3, Math.floor(ov)); s.upSince = s.downSince = null; return s.tier; }
  const [up, down] = wanted(Math.min(100, Math.max(0, gpu ?? 0)), ac ?? true, v);
  if (up > s.tier) {
    s.upSince ??= now;
    if (now - s.upSince >= 5) { s.tier = up; s.upSince = null; }
  } else s.upSince = null;
  if (down < s.tier) {
    s.downSince ??= now;
    if (now - s.downSince >= 20) { s.tier -= 1; s.downSince = null; }
  } else s.downSince = null;
  return s.tier;
}

/** The tier the page draws at, 0 full to 3 stealth. Kept in memory only; the skin's PerfTier setting is not written. */
export const perfTier = signal(0);

/** Steps the tier on each host reading and each settings change. Returns the stop function. */
export function startPerfTier(metrics: ReadonlySignal<SystemMetrics | null>, values: ReadonlySignal<Record<string, string>>, clock = () => Date.now() / 1000) {
  const s = tierState();
  return effect(() => {
    const m = metrics.value;
    perfTier.value = tierStep(s, m?.gpuPercent ?? null, m?.onAc ?? null, values.value, clock());
  });
}
