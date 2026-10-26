import { Canvas, type Op, type Style, type Zone } from '../draw/canvas';
import { type Readings } from './readings';
import { usedShare } from './storage';

// Port of Skins/Spaceship/@Resources/Scripts/strip.lua: the two readout strips under the dash arch. Left: CPU temp, GPU temp,
// CPU load, fan. Right: drive fill, disk activity, ping, Wi-Fi. Warn limits are the skin's defaults (WarnCpuTemp 92,
// WarnGpuTemp 85, WarnDiskPct 90, from Settings.inc), not read from settings yet. Click (Task Manager, drive) is not ported.

const STEP = 84, CELLW = 76;

export type Cell = { icon: string; text: string; lvl?: 0 | 1 | 2; size?: number };

/** 0 normal, 1 warn (within the margin of the limit), 2 alert (over the limit). A missing value is normal. */
export function level(v: number | undefined, limit: number, margin: number): 0 | 1 | 2 {
  if (v === undefined) return 0;
  if (v >= limit) return 2;
  if (v >= limit - margin) return 1;
  return 0;
}

/** strip.lua short(): a per-second rate that fits a cell, e.g. 820B/s, 4.1KB/s, 47KB/s, 312MB/s. */
export function rateShort(bytesPerSec: number): string {
  const units = ['B', 'KB', 'MB', 'GB'];
  let b = bytesPerSec, i = 0;
  while (b >= 1000 && i < units.length - 1) { b /= 1024; i++; }
  // Lua's index starts at 1 for B, so the decimal rule is i > 1 here (KB and up), and a value under 10
  return i > 0 && b < 10 ? `${b.toFixed(1)}${units[i]}/s` : `${b.toFixed(0)}${units[i]}/s`;
}

/** The cells of one strip: icon and text, from the outer end inward. The right strip is mirrored. */
function cellsFrame(list: Cell[], mirror: boolean, zone: Zone, st: Style): Op[] {
  const c = new Canvas(zone, st);
  const y = zone.h / 2 - 2; // strip.lua uses h/2; lifted on the user's ask so the cells clear the lower neon line
  list.forEach((cl, i) => {
    const x0 = mirror ? zone.w - 4 - i * STEP - CELLW : 4 + i * STEP;
    const lv = cl.lvl ?? 0;
    const col = lv === 2 ? st.alert : lv === 1 ? st.warn : st.white;
    c.icon(cl.icon, x0 + 9, y, 15, lv === 2 ? st.alert : lv === 1 ? st.warn : st.accent, 1.2);
    c.text(x0 + 20, y, cl.text, { size: cl.size ?? 5, weight: 700, align: 'LeftCenter', color: col, font: st.fontNum, clip: CELLW - 22 });
  });
  return c.flush();
}

export function stripLeftFrame(r: Readings, zone: Zone, st: Style): Op[] {
  const ct = r.mHwCpuTemp, gt = r.mHwGpuTemp, load = r.mCPU, fan = r.mHwFan1;
  return cellsFrame([
    { icon: 'gauge', text: ct === undefined ? '--' : `${ct.toFixed(0)}C`, lvl: level(ct, 92, 5) },
    { icon: 'gpu', text: gt === undefined ? '--' : `${gt.toFixed(0)}C`, lvl: level(gt, 85, 5) },
    { icon: 'wave', text: load === undefined ? '--' : `${Math.trunc(load)}%`, lvl: level(load, 95, 10) },
    { icon: 'gear', text: fan === undefined ? '--' : fan.toFixed(0) },
  ], false, zone, st);
}

export function stripRightFrame(r: Readings, zone: Zone, st: Style): Op[] {
  const tot = r.mD1Total;
  const used = tot === undefined ? undefined : usedShare(tot, r.mD1Free ?? 0) * 100;
  const ping = r.mPing, wifi = r.mWifi;
  return cellsFrame([
    { icon: 'drive', text: used === undefined ? '--' : `C ${Math.floor(used + 0.5)}%`, lvl: level(used, 90, 5) },
    { icon: 'disk', text: r.mDiskIO === undefined ? '--' : rateShort(r.mDiskIO), size: 4.6 },
    { icon: 'orbit', text: ping === undefined ? '--' : `${Math.trunc(ping)}ms` },
    { icon: 'wave', text: wifi === undefined ? '--' : `${Math.trunc(wifi)}%` },
  ], true, zone, st);
}
