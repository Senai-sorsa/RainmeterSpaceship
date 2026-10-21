import { describe, expect, it } from 'vitest';
import { feedFrom, jarvisFrame, jarvisLogFrame, logLines, plexus, wrap } from '../src/modules/jarvis';
import { styleFrom } from '../src/modules/style';

const st = styleFrom({});
const zone = { x: 0, y: 0, w: 2560, h: 1600 };

describe('jarvis feed', () => {
  it('no feed, or one older than 8 s, is offline', () => {
    expect(feedFrom(undefined, 100).state).toBe('offline');
    expect(feedFrom('T 50\nSTATE speaking\nLEVEL 0.5', 100).state).toBe('offline');
  });

  it('a fresh feed gives its state and level', () => {
    expect(feedFrom('T 100\nSTATE speaking\nLEVEL 0.5', 101)).toEqual({ state: 'speaking', level: 0.5 });
  });
});

describe('jarvis plexus', () => {
  it('56 nodes, each linked to up to 3 others, with no duplicate or self links', () => {
    const p = plexus();
    expect(p.nodes).toHaveLength(56);
    const keys = new Set(p.edges.map(([a, b]) => `${Math.min(a, b)}:${Math.max(a, b)}`));
    expect(keys.size).toBe(p.edges.length);
    expect(p.edges.every(([a, b]) => a !== b)).toBe(true);
    expect(p.edges.length).toBeGreaterThan(56);
  });
});

describe('jarvis core frame', () => {
  it('draws for every state and for a frame with a voice level', () => {
    for (const state of ['idle', 'listening', 'thinking', 'speaking', 'offline']) {
      expect(jarvisFrame(10, { state, level: 0.4 }, st, zone, 1280, 1116).length).toBeGreaterThan(0);
    }
  });

  it('an unknown state draws as standby, not an error', () => {
    expect(jarvisFrame(1, { state: 'nonsense', level: 0 }, st, zone, 1280, 1116).length).toBeGreaterThan(0);
  });
});

describe('jarvis log', () => {
  it('wraps by character count and cuts words longer than the width', () => {
    expect(wrap('one two three four', 9)).toEqual(['one two', 'three', 'four']);
    expect(wrap('abcdefghij', 4)).toEqual(['abcd', 'efgh', 'ij']);
    expect(wrap('', 10)).toEqual(['']);
  });

  it('reads U, J and S lines, then the live reply with a cursor', () => {
    const lines = logLines('U|1|hi there\nJ|2|hello\n', 'J|3|typing', 40);
    expect(lines.filter((l) => l.first).map((l) => l.who)).toEqual(['U', 'J', 'L']);
    expect(lines.find((l) => l.who === 'L')?.text).toBe('typing _');
  });

  it('draws the empty state and a filled log', () => {
    const z = { x: 0, y: 0, w: 1200, h: 616 };
    expect(jarvisLogFrame('', '', false, 'Clover', st, z).length).toBeGreaterThan(0);
    expect(jarvisLogFrame('U|1|hi\n', '', true, 'Clover', st, z).length).toBeGreaterThan(0);
  });
});
