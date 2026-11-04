import { describe, expect, it } from 'vitest';
import { acceptCalendarUpdate, calendarFeed, fakeCalendar, parseCalendarTxt } from '../src/modules/calendarSource';
import { rows } from '../src/modules/calendar';

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

describe('calendar text is bounded and sorted', () => {
  it('sorts events soonest first, and rows() shows the soonest first', () => {
    const c = parseCalendarTxt('E 300|400|0|A|third\nE 100|200|0|A|first\nE 200|300|0|A|second\n');
    expect(c.events.map((e) => e.title)).toEqual(['first', 'second', 'third']);
    expect(rows(c, 0)[0].title.toLowerCase()).toContain('first');
  });
  it('keeps at most 100 events', () => {
    const lines = Array.from({ length: 500 }, (_, i) => `E ${i + 1}|${i + 2}|0|A|t${i}`).join('\n');
    expect(parseCalendarTxt(lines).events).toHaveLength(100);
  });
  it('cuts a long title to 200 and a long label to 60', () => {
    const c = parseCalendarTxt(`E 1|2|0|${'L'.repeat(100)}|${'x'.repeat(5000)}\n`);
    expect(c.events[0].title).toHaveLength(200);
    expect(c.events[0].label).toHaveLength(60);
  });
  it('drops a line whose start is not a safe integer', () => {
    expect(parseCalendarTxt('E 99999999999999999999|5|0|A|B\nE 1|2|0|A|ok\n').events.map((e) => e.title)).toEqual(['ok']);
  });
  it('ignores a calendar.update larger than 262144 characters', () => {
    acceptCalendarUpdate({ type: 'calendar.update', text: 'C 1 0\nE 5|6|0|A|B\n' });
    const before = calendarFeed.value;
    acceptCalendarUpdate({ type: 'calendar.update', text: 'x'.repeat(300000) });
    expect(calendarFeed.value).toBe(before);
  });
});
