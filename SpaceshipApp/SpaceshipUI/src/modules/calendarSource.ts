import { signal } from '@preact/signals';
import type { CalState } from './calendar';

/** Where the mission clock gets its events: the host's calendar.update (Data\calendar.txt), or the sample in a browser. */
export interface CalendarSource { read(now: number): CalState }

const MIN = 60000, HOUR = 60 * MIN, DAY = 24 * HOUR;

/** Fixed sample events placed relative to now, so the rows always show the same states: in progress, under 24 h, a later date. */
export const fakeCalendar: CalendarSource = {
  read(now) {
    return {
      ok: true,
      calendars: 2,
      errors: 0,
      events: [
        { s: now - 10 * MIN, e: now + 20 * MIN, allday: false, label: 'Work', title: 'Team sync' },
        { s: now + 5 * HOUR, e: now + 6 * HOUR, allday: false, label: 'Personal', title: 'Dentist appointment and a long title' },
        { s: now + 3 * DAY, e: now + 3 * DAY + HOUR, allday: false, label: 'Work', title: 'Launch review' },
      ],
    };
  },
};

/** Data\calendar.txt (T, C calendars errors, E start|end|allday|label|title lines, times in s) as location.lua reads it. */
export function parseCalendarTxt(text: string): CalState {
  const c: CalState = { ok: true, calendars: 0, errors: 0, events: [] };
  for (const line of text.split('\n')) {
    const m = line.match(/^C (\d+) (\d+)/);
    if (m) { c.calendars = +m[1]; c.errors = +m[2]; continue; }
    const e = line.match(/^E (\d+)\|(\d+)\|(\d)\|([^|]*)\|(.*?)\r?$/);
    if (e) c.events.push({ s: +e[1] * 1000, e: +e[2] * 1000, allday: e[3] === '1', label: e[4], title: e[5] });
  }
  return c;
}

/** The sample until the host sends calendar.update (a browser without the host keeps the sample). */
export const calendarFeed = signal<CalendarSource>(fakeCalendar);

export function acceptCalendarUpdate(m: unknown): void {
  const o = m as { type?: unknown; text?: unknown } | null;
  if (o?.type !== 'calendar.update' || typeof o.text !== 'string') return;
  const state = parseCalendarTxt(o.text);
  calendarFeed.value = { read: () => state };
}
