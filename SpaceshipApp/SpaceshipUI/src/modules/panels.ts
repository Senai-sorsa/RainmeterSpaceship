// Data side of Skins/Spaceship/@Resources/Scripts/panels.lua: the left screen's date, week and year rows and the
// span text the uptime and idle rows use. The drawing is not ported yet.

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
  return `UTC${minutes < 0 ? '-' : '+'}${String(Math.floor(a / 60)).padStart(2, '0')}:${String(a % 60).padStart(2, '0')}`;
}

/** The span text of the uptime and idle rows: 3D 04:20, 2:04 H, 2:05 or 45 S. */
export function spanText(seconds: number): string {
  const sec = Math.max(0, Math.floor(seconds));
  const d = Math.floor(sec / 86400), h = Math.floor(sec / 3600) % 24, m = Math.floor(sec / 60) % 60, s = sec % 60;
  const p = (n: number) => String(n).padStart(2, '0');
  if (d > 0) return `${d}D ${p(h)}:${p(m)}`;
  if (h > 0) return `${h}:${p(m)} H`;
  if (m > 0) return `${m}:${p(s)}`;
  return `${s} S`;
}
