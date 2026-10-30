import { Canvas, type Op, type Style, type Zone } from '../draw/canvas';
import { type Readings, val } from './readings';

// Port of Skins/Spaceship/@Resources/Scripts/alert.lua: the warning triangle and its count, in the top bar.
// The triangle blinks on every frame while there are alerts, except on LOW and STEALTH. Its click opens the
// Control Center (TopModule.tsx), in place of the Rainmeter config it opened.

export type Thresholds = { WarnCpuTemp: number; WarnGpuTemp: number; WarnDiskPct: number; WarnBattery: number };
export const DEFAULT_THRESHOLDS: Thresholds = { WarnCpuTemp: 92, WarnGpuTemp: 85, WarnDiskPct: 90, WarnBattery: 20 };
/** blink flips between 0 and 1 on every frame. */
export type AlertState = { blink: number };
export type AlertFrame = { ops: Op[]; count: number; tip: string };

export function alertList(r: Readings, t: Thresholds = DEFAULT_THRESHOLDS): string[] {
  const list: string[] = [];
  const ct = r.mHwCpuTemp, gt = r.mHwGpuTemp;
  if (ct !== undefined && ct >= t.WarnCpuTemp) list.push(`CPU HOT ${ct.toFixed(0)} C`);
  if (gt !== undefined && gt >= t.WarnGpuTemp) list.push(`GPU HOT ${gt.toFixed(0)} C`);
  const tot = val(r, 'mDiskTotal');
  if (tot > 0) {
    const used = ((tot - val(r, 'mDiskFree')) / tot) * 100;
    if (used >= t.WarnDiskPct) list.push(`C: ${used.toFixed(0)}% FULL`);
  }
  // alert.lua defaults the threshold check to 100 but the printed value to 0; keep both
  if (val(r, 'mAC', 1) === 0 && val(r, 'mBattPct', 100) <= t.WarnBattery) list.push(`BATTERY ${Math.trunc(val(r, 'mBattPct'))}%`);
  if (val(r, 'mCPU') >= 95) list.push('CPU SATURATED');
  return list;
}

export function alertFrame(r: Readings, zone: Zone, st: Style, state: AlertState, t: Thresholds = DEFAULT_THRESHOLDS): AlertFrame {
  state.blink = 1 - state.blink;
  const list = alertList(r, t), n = list.length;
  const c = new Canvas(zone, st);
  const a = n > 0 && state.blink === 1 && st.tier < 2 ? 130 : 255;
  const s = zone.h * 0.62, cx = s * 0.55 + 4, cy = zone.h / 2;
  c.poly([[cx + s * 0.5, cy], [cx - s * 0.35, cy - s * 0.5], [cx - s * 0.35, cy + s * 0.5]], st.hi, 2, a, true);
  c.text(zone.w, cy, String(n), { size: 9, weight: 700, align: 'RightCenter', color: st.hi, alpha: a });
  return { ops: c.flush(), count: n, tip: list.join('  |  ') };
}
