// Mission clock rules, mirrored from Skins/Spaceship/@Resources/Scripts/location.lua. Pure: no DOM, no clock of its own.

export type CalEvent = { s: number; e: number; allday: boolean; label: string; title: string }; // s, e in ms since epoch
export type CalState = { ok: boolean; calendars: number; errors: number; events: CalEvent[] };
export type Row = { when: string; title: string; live: boolean; allday: boolean };

const DAY = 86400000;
/** Titles longer than this are drawn cut with an ellipsis, and only then does their hover caption show the full text. */
export const TITLE_MAX = 30;
const WEEKDAY = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
const MONTH = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
const pad = (n: number) => String(n).padStart(2, '0');

/** 12-hour clock without a leading zero: 10:24AM, 9:05PM. Built by hand so the system language cannot change AM/PM. */
export function clock12(ts: number): string {
  const d = new Date(ts), h = d.getHours();
  return `${h % 12 === 0 ? 12 : h % 12}:${pad(d.getMinutes())}${h < 12 ? 'AM' : 'PM'}`;
}

/** Whole calendar days from today to the day of ts (noon-to-noon, so DST changes do not shift it). */
function dayDiff(ts: number, now: number): number {
  const a = new Date(ts), b = new Date(now);
  const noon = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate(), 12).getTime();
  return Math.round((noon(a) - noon(b)) / DAY);
}

/** Row label: clock time inside 24 h, a weekday inside a week, otherwise the date. */
export function whenLabel(e: CalEvent, now: number): string {
  const days = dayDiff(e.s, now);
  if (e.allday) { if (days === 0) return 'TODAY'; }
  else if (e.s - now < DAY) return clock12(e.s);
  if (days < 7) return WEEKDAY[new Date(e.s).getDay()];
  const d = new Date(e.s);
  return `${pad(d.getMonth() + 1)}/${pad(d.getDate())}`;
}

/** Up to three upcoming rows (not yet ended). A live timed event shows NOW. */
export function rows(state: CalState, now: number): Row[] {
  return state.events.filter((e) => e.e > now).slice(0, 3).map((e) => {
    const live = e.s <= now;
    const title = e.title.toUpperCase();
    return { when: !e.allday && live ? 'NOW' : whenLabel(e, now), title: title.length > TITLE_MAX ? title.slice(0, TITLE_MAX - 1) + '…' : title, live, allday: e.allday };
  });
}

/** Colour level of the first row: good while in progress, alert under 15 min, warn under 60 min, else accent. */
export function firstLevel(state: CalState, now: number): 'good' | 'alert' | 'warn' | 'accent' {
  const first = state.events.find((e) => e.e > now);
  if (!first) return 'accent';
  if (first.s <= now) return 'good';
  const dt = (first.s - now) / 1000;
  return dt < 900 ? 'alert' : dt < 3600 ? 'warn' : 'accent';
}

/** Empty-state text for the first row when there is nothing upcoming. */
export function emptyText(state: CalState): { when: string; title: string } {
  if (!state.ok) return { when: 'SETUP', title: 'CONTROL CENTER > DATA' };
  return state.calendars === 0 ? { when: 'CLEAR', title: 'NO CALENDARS ON' } : { when: 'CLEAR', title: 'NO EVENTS IN 3 WEEKS' };
}

/** Hover caption for a row: only when its title is cut, with the full title, time and calendar. Shortcut: counts characters, not measured width; upgrade to a measured fit when the zone's font is measured. */
export function rowTip(state: CalState, now: number, index: number): string | undefined {
  const e = state.events.filter((x) => x.e > now)[index];
  if (!e || e.title.length <= TITLE_MAX) return undefined;
  const d = new Date(e.s);
  const stamp = `${WEEKDAY[d.getDay()]} ${pad(d.getDate())} ${MONTH[d.getMonth()]}` + (e.allday ? '' : `  ${pad(d.getHours())}:${pad(d.getMinutes())}`);
  return `${e.title}   ${stamp}   ${e.label}`;
}
