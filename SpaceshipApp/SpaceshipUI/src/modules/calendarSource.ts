import type { CalState } from './calendar';

/** Where the mission clock gets its events. The real feed (ShipCore's Data\calendar.txt) is not wired yet: it waits on the HTTP fetch policy. */
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
