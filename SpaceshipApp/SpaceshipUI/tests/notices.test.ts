import { beforeEach, describe, expect, it } from 'vitest';
import { acceptNotice, dismissNotice, notices } from '../src/host/notices';

const msg = (source: string, text = 'x', level: string = 'warn'): unknown => ({ type: 'notice', source, level, text });

describe('notices', () => {
  beforeEach(() => { notices.value = []; });
  it('keeps one notice per source, newest first, at most three', () => {
    for (const s of ['a', 'b', 'c', 'd']) acceptNotice(msg(s));
    acceptNotice(msg('c', 'again'));
    expect(notices.value.map((n) => n.source)).toEqual(['c', 'd', 'b']);
    expect(notices.value[0].text).toBe('again');
  });
  it('ignores malformed messages', () => {
    acceptNotice({ type: 'other' });
    acceptNotice(msg('A!'));
    acceptNotice(msg('a', ''));
    acceptNotice(msg('a', 'x'.repeat(201)));
    acceptNotice(msg('a', 'x', 'info'));
    expect(notices.value).toEqual([]);
  });
  it('dismisses by source', () => {
    acceptNotice(msg('a')); acceptNotice(msg('b'));
    dismissNotice('a');
    expect(notices.value.map((n) => n.source)).toEqual(['b']);
  });
});
