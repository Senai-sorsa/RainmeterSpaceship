import { describe, expect, it } from 'vitest';
import { acceptCalendarUpdate, calendarFeed, fakeCalendar, parseCalendarTxt } from '../src/modules/calendarSource';

describe('calendar.update from the host', () => {
  it('reads calendar.txt like location.lua', () => {
    const c = parseCalendarTxt('T 100\r\nC 2 1\r\nE 1000|2000|1|School|Quiz | part 2\r\nE bad\n');
    expect(c).toEqual({ ok: true, calendars: 2, errors: 1, events: [{ s: 1000000, e: 2000000, allday: true, label: 'School', title: 'Quiz | part 2' }] });
  });

  it('keeps the sample for other messages and swaps in the real events', () => {
    acceptCalendarUpdate({ type: 'calendar.update', text: 1 });
    expect(calendarFeed.value).toBe(fakeCalendar);
    acceptCalendarUpdate({ type: 'calendar.update', text: 'C 1 0\nE 5|6|0|A|B\n' });
    expect(calendarFeed.value.read(0).events.map((e) => e.title)).toEqual(['B']);
  });
});
