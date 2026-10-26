import { Canvas, type Op, type Style, type Zone } from '../draw/canvas';
import { type RGBA } from '../lib/theme';
import type { SysInfo } from '../host/sysInfo';
import type { Readings } from './readings';

// Port of Skins/Spaceship/@Resources/Scripts/panels.lua: the two tilted screens at the bottom of the dash.
// Left: pilot, date, time, week, year, time zone, boot, uptime, idle. Right: the condensed ship card and the TERMINAL button.
// The names come from the host's sys.info, idle and RAM total from system.metrics; a missing one shows --. Clicks: BottomModule (calendar, about, terminal).

const DAYS = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
const MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
const p2 = (n: number) => String(n).padStart(2, '0');

export type Row = { label: string; value: string; color?: RGBA };

/** Week of the year (Monday weeks) and the day of the year, from the local date. */
export function weekOf(d: Date): { week: number; yday: number } {
  const jan1 = new Date(d.getFullYear(), 0, 1);
  const yday = Math.round((new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime() - jan1.getTime()) / 86400000) + 1;
  const wd = ((d.getDay() + 6) % 7) + 1; // Monday = 1 ... Sunday = 7
  return { week: Math.max(1, Math.floor((yday - wd + 10) / 7)), yday };
}

/** Share of the year gone, as the YEAR row shows it: 0..100 for the current day. */
export function yearProgress(d: Date): number {
  const y = d.getFullYear();
  const ylen = (y % 4 === 0 && (y % 100 !== 0 || y % 400 === 0)) ? 366 : 365;
  return ((weekOf(d).yday - 1) / ylen) * 100;
}

/** UTC offset text from minutes east of UTC, e.g. UTC+03:00, UTC-05:30. */
export function offsetText(minutes: number): string {
  const a = Math.abs(minutes);
  return `UTC${minutes < 0 ? '-' : '+'}${p2(Math.floor(a / 60))}:${p2(a % 60)}`;
}

/** The span text of the uptime and idle rows: 3D 04:20, 2:04 H, 2:05 or 45 S. */
export function spanText(seconds: number): string {
  const sec = Math.max(0, Math.floor(seconds));
  const d = Math.floor(sec / 86400), h = Math.floor(sec / 3600) % 24, m = Math.floor(sec / 60) % 60, s = sec % 60;
  if (d > 0) return `${d}D ${p2(h)}:${p2(m)}`;
  if (h > 0) return `${h}:${p2(m)} H`;
  if (m > 0) return `${m}:${p2(s)}`;
  return `${s} S`;
}

/** The DATE row, upper case: WED 21 OCT. */
export const dateText = (d: Date) => `${DAYS[d.getDay()]} ${p2(d.getDate())} ${MONTHS[d.getMonth()]}`;

/** The BOOT row: when the machine came up, as the clock shows it, or -- with no uptime. */
export function bootText(now: Date, uptimeSec?: number): string {
  if (uptimeSec === undefined || uptimeSec <= 0) return '--';
  const t = new Date(now.getTime() - uptimeSec * 1000);
  const hm = `${p2(t.getHours())}:${p2(t.getMinutes())}`;
  return (uptimeSec < 86400 ? hm : `${DAYS[t.getDay()]} ${hm}`).toUpperCase();
}

/** The rows of the left screen, from the clock, the readings (mUptime, mIdle, in seconds) and the user name. */
export function leftRows(now: Date, r: Readings = {}, info: SysInfo = {}, hi?: RGBA): Row[] {
  const { week, yday } = weekOf(now);
  const uptimeSec = r.mUptime;
  return [
    { label: 'PILOT', value: info.user?.toUpperCase() ?? '--' },
    { label: 'DATE', value: dateText(now) },
    // the skin draws the clock row in the highlight colour (H.C.hi)
    { label: 'TIME', value: `${p2(now.getHours())}:${p2(now.getMinutes())}:${p2(now.getSeconds())}`, color: hi },
    { label: 'WEEK', value: `W${p2(week)}  D${String(yday).padStart(3, '0')}` },
    { label: 'YEAR', value: `${now.getFullYear()}  ${yearProgress(now).toFixed(0)}%` },
    { label: 'ZONE', value: offsetText(-now.getTimezoneOffset()) },
    { label: 'BOOT', value: bootText(now, uptimeSec) },
    { label: 'UP', value: uptimeSec !== undefined && uptimeSec > 0 ? spanText(uptimeSec) : '--' },
    { label: 'IDLE', value: r.mIdle !== undefined ? spanText(r.mIdle) : '--' },
  ];
}

// the skin tints the uptime row between accent and white (H.mix 0.4)
const mixAccent = (st: Style): RGBA => [0, 1, 2].map((i) => Math.floor(st.accent[i] + (st.white[i] - st.accent[i]) * 0.4)).concat(255) as RGBA;

/** The rows of the right screen (the card): the machine's names, RAM total (mRamTotal bytes), screen and uptime. */
export function rightRows(r: Readings, st: Style, info: SysInfo = {}): Row[] {
  const uptimeSec = r.mUptime, ram = r.mRamTotal ?? 0;
  return [
    { label: 'HOST', value: info.host?.toUpperCase() ?? '--' },
    { label: 'OS', value: (info.os ?? 'WINDOWS').toUpperCase() },
    { label: 'CPU', value: info.cpu ?? '--' },
    { label: 'GPU', value: info.gpu ?? '--' },
    { label: 'RAM', value: ram > 0 ? `${(ram / 1073741824).toFixed(0)} GB` : '--' },
    { label: 'DISP', value: info.display ?? '--' },
    { label: 'UP', value: uptimeSec !== undefined && uptimeSec > 0 ? spanText(uptimeSec) : '--', color: mixAccent(st) },
  ];
}

/** The label and value rows, spread over height the way the skin does. */
function rowsInto(c: Canvas, zone: Zone, list: Row[], height: number, st: Style) {
  const rh = height / (list.length + 0.3);
  list.forEach((r, i) => {
    const y = rh * (i + 1 - 0.35);
    if (i < list.length - 1) c.hair(6, y + rh * 0.5, zone.w - 6, y + rh * 0.5, st.accent, 1, 45);
    c.text(6, y, r.label, { size: 3.0, weight: 700, align: 'LeftCenter', color: st.accent, alpha: 220, glow: false });
    c.text(zone.w - 5, y, r.value, { size: 3.3, weight: 700, align: 'RightCenter', color: r.color ?? st.white, font: st.fontNum, clip: zone.w * 0.66 });
  });
}

export function panelLeftFrame(list: Row[], zone: Zone, st: Style): Op[] {
  const c = new Canvas(zone, st);
  rowsInto(c, zone, list, zone.h, st);
  return c.flush();
}

/** The card and the TERMINAL button under it (left click Windows Terminal, right click PowerShell; the hit is in BottomModule). */
export function panelRightFrame(list: Row[], zone: Zone, st: Style): Op[] {
  const c = new Canvas(zone, st);
  rowsInto(c, zone, list, zone.h * 0.76, st);
  const bx = 6, by = zone.h * 0.8, bw = zone.w - 12, bh = zone.h * 0.16;
  c.chamfer(bx, by, bw, bh, bh * 0.35, st.accent, 1.2, 230, 90);
  c.text(bx + bw / 2, by + bh / 2, '>_ TERMINAL', { size: 3.6, weight: 700, align: 'CenterCenter', color: st.white, font: st.fontNum });
  return c.flush();
}
