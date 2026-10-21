import { Canvas, type Op, type Style, type Zone } from '../draw/canvas';
import { duration, type Readings, val } from './readings';

// Port of Skins/Spaceship/@Resources/Scripts/battery.lua: the PWR bar in the top right, with the time to the charge
// limit or to empty. The fallback estimate uses wall-clock samples, so `now` (seconds) is passed in. OnClick is not
// ported: it opened Windows battery settings through a Rainmeter bang.

/** [seconds, percent] samples for the estimate when HWiNFO gives no charge rate. */
export type BatteryState = { samples: [number, number][] };
export type BatteryOpts = { limit: number; warn: number };
export type BatteryFrame = { ops: Op[]; pct: number; status: string };

const DEFAULTS: BatteryOpts = { limit: 80, warn: 20 };

/** Seconds to reach the limit, or undefined when there is no estimate yet. */
function timeToLimit(r: Readings, state: BatteryState, pct: number, limit: number, now: number): number | undefined {
  const rem = r.mHwRemainCap, full = r.mHwFullCap, rate = r.mHwChargeRate;
  if (rem !== undefined && full !== undefined && rate !== undefined && rate > 0.5) {
    const need = (((limit / 100) * full - rem) / 1000);
    if (need <= 0) return 0;
    return (need / rate) * 3600;
  }
  const s = state.samples;
  if (s.length === 0 || s[s.length - 1][1] !== pct) s.push([now, pct]);
  while (s.length > 2 && now - s[0][0] > 600) s.shift();
  if (s.length >= 2) {
    const dt = s[s.length - 1][0] - s[0][0], dp = s[s.length - 1][1] - s[0][1];
    if (dt > 60 && dp > 0) return (limit - pct) / (dp / dt);
  }
  return undefined;
}

export function batteryFrame(r: Readings, zone: Zone, st: Style, state: BatteryState, now: number, opts: BatteryOpts = DEFAULTS): BatteryFrame {
  const { limit, warn } = opts;
  const pct = val(r, 'mBattPct'), ac = val(r, 'mAC') > 0;
  let status: string;
  if (ac) {
    if (pct >= limit - 1) {
      status = `HELD ${limit}%`;
      state.samples = [];
    } else {
      const t = timeToLimit(r, state, pct, limit, now);
      status = t !== undefined ? `${duration(t)} TO ${limit}%` : `CHG TO ${limit}%`;
    }
  } else {
    state.samples = [];
    const life = val(r, 'mLifetime', -1);
    status = life > 0 ? `${duration(life)} LEFT` : 'ON BATT';
  }
  const c = new Canvas(zone, st);
  const y = zone.h * 0.76, x0 = 48, x1 = zone.w;
  c.text(0, y, 'PWR', { size: 8.5, weight: 700, align: 'LeftCenter', color: st.white });
  c.line(x0, y, x1, y, st.white, 1.3, 200);
  const low = !ac && pct <= warn;
  c.line(x0, y, x0 + ((x1 - x0) * pct) / 100, y, low ? st.alert : ac ? st.good : st.hi, 2.6);
  const lx = x0 + ((x1 - x0) * limit) / 100;
  c.line(lx, y - 6, lx, y + 3, st.white, 1.2, 200);
  c.text(x0, 0, `${Math.trunc(pct)}%  ${status}`, { size: 4.8, weight: 700, align: 'LeftTop', color: st.white, alpha: 210, clip: (x1 - x0) * 0.7 });
  return { ops: c.flush(), pct, status };
}
