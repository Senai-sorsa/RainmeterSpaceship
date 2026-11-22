import { describe, expect, it } from 'vitest';
import { clock12, emptyText, firstLevel, rowTip, rows, whenLabel, TITLE_MAX, type CalEvent, type CalState } from '../src/modules/calendar';
import { fakeCalendar } from '../src/modules/calendarSource';

// Local-time constructors so the tests hold in any time zone. 2026-10-20 is a Tuesday.
const at = (d: number, h = 0, m = 0) => new Date(2026, 9, d, h, m).getTime();
const MIN = 60000;
const ev = (over: Partial<CalEvent>): CalEvent => ({ s: at(20, 12), e: at(20, 13), allday: false, label: 'Work', title: 'Lunch', ...over });
const state = (events: CalEvent[], over: Partial<CalState> = {}): CalState => ({ ok: true, calendars: 1, errors: 0, events, ...over });
const now = at(20, 9);

describe('clock12', () => {
  it('uses 12-hour time with AM and PM and no leading zero', () => {
    expect(clock12(at(20, 0, 5))).toBe('12:05AM');
    expect(clock12(at(20, 9, 30))).toBe('9:30AM');
    expect(clock12(at(20, 12, 0))).toBe('12:00PM');
    expect(clock12(at(20, 13, 5))).toBe('1:05PM');
    expect(clock12(at(20, 23, 59))).toBe('11:59PM');
  });
});

describe('whenLabel', () => {
  it('shows the clock time inside 24 hours', () => {
    expect(whenLabel(ev({ s: at(20, 12) }), now)).toBe('12:00PM');
  });
  it('shows the weekday inside a week and the date beyond it', () => {
    expect(whenLabel(ev({ s: at(22, 10) }), now)).toBe('THU'); // 49 h away, Thursday
    expect(whenLabel(ev({ s: at(30, 10) }), now)).toBe('10/30');
  });
  it('labels all-day events TODAY, then by weekday', () => {
    expect(whenLabel(ev({ allday: true, s: at(20, 0), e: at(21, 0) }), now)).toBe('TODAY');
    expect(whenLabel(ev({ allday: true, s: at(21, 0), e: at(22, 0) }), now)).toBe('WED');
  });
});

describe('rows', () => {
  it('shows NOW for a live timed event and uppercases the title', () => {
    const r = rows(state([ev({ s: now - 10 * MIN, e: now + 20 * MIN, title: 'Team sync' })]), now);
    expect(r).toEqual([{ when: 'NOW', title: 'TEAM SYNC', live: true, allday: false }]);
  });
  it('skips events that have ended and shows at most three', () => {
    const list = [
      ev({ s: at(20, 7), e: at(20, 8), title: 'Ended' }),
      ev({ title: 'A' }), ev({ title: 'B' }), ev({ title: 'C' }), ev({ title: 'D' }),
    ];
    expect(rows(state(list), now).map((r) => r.title)).toEqual(['A', 'B', 'C']);
  });
  it('cuts long titles with an ellipsis', () => {
    const long = 'x'.repeat(TITLE_MAX + 5);
    const [r] = rows(state([ev({ title: long })]), now);
    expect(r.title).toHaveLength(TITLE_MAX);
    expect(r.title.endsWith('…')).toBe(true);
  });
});

describe('firstLevel', () => {
  it('is good while in progress, alert under 15 minutes, warn under 60, else accent', () => {
    expect(firstLevel(state([ev({ s: now - MIN, e: now + MIN })]), now)).toBe('good');
    expect(firstLevel(state([ev({ s: now + 10 * MIN })]), now)).toBe('alert');
    expect(firstLevel(state([ev({ s: now + 40 * MIN })]), now)).toBe('warn');
    expect(firstLevel(state([ev({ s: now + 2 * 3600000 })]), now)).toBe('accent');
    expect(firstLevel(state([]), now)).toBe('accent');
  });
});

describe('emptyText', () => {
  it('says what is missing', () => {
    expect(emptyText(state([], { ok: false }))).toEqual({ when: 'SETUP', title: 'CONTROL CENTER > DATA' });
    expect(emptyText(state([], { calendars: 0 }))).toEqual({ when: 'CLEAR', title: 'NO CALENDARS ON' });
    expect(emptyText(state([]))).toEqual({ when: 'CLEAR', title: 'NO EVENTS IN 3 WEEKS' });
  });
});

describe('rowTip', () => {
  it('gives no caption when the title is not cut', () => {
    expect(rowTip(state([ev({ title: 'Lunch' })]), now, 0)).toBeUndefined();
  });
  it('gives the full title, date, time and calendar when the title is cut', () => {
    const long = 'Dentist appointment and a long title';
    expect(rowTip(state([ev({ title: long, s: at(20, 17, 5), e: at(20, 18), label: 'Personal' })]), now, 0))
      .toBe(`${long}   TUE 20 OCT  17:05   Personal`);
  });
  it('omits the time for all-day events', () => {
    const long = 'x'.repeat(TITLE_MAX + 1);
    expect(rowTip(state([ev({ title: long, allday: true, s: at(20), e: at(21), label: 'Work' })]), now, 0))
      .toBe(`${long}   TUE 20 OCT   Work`);
  });
});

describe('fakeCalendar', () => {
  it('gives an in-progress event first, a later one within 24 hours, and one three days out', () => {
    const r = fakeCalendar.read(now);
    expect(r.ok).toBe(true);
    expect(r.events.map((e) => e.title)).toEqual(['Team sync', 'Dentist appointment and a long title', 'Launch review']);
    expect(firstLevel(r, now)).toBe('good');
  });
});
