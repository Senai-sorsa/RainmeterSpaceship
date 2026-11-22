import { describe, expect, it } from 'vitest';
import type { Style } from '../src/draw/canvas';
import { consoleFrame, type ConsoleConfig, type ConsoleState, type ConsoleView } from '../src/modules/console';

// Picture (fitted): the console's first row stays put, the gap to its second row closes to 0.6, and the hit boxes follow the text.
const base: Style = {
  s: 1, tier: 2, glowA: 46, glowW: 3.2, coreWhite: 0, hudA: 255, edit: false,
  textGlow: 4, textGlowA: 150, textSmall: 1.85, textLarge: 1.45, fontText: 'Oxanium', fontNum: 'B612 Mono', fontTitle: 'Michroma',
  white: [215, 240, 255, 255], dim: [0, 110, 150, 255], panel: [0, 30, 45, 90], accent: [0, 210, 255, 255],
  warn: [255, 130, 40, 255], alert: [255, 60, 70, 255], text: [170, 235, 255, 255], hi: [255, 105, 135, 255], good: [60, 255, 170, 255],
};
const zone = { x: 0, y: 0, w: 580, h: 104 };
const cfg: ConsoleConfig = {
  powerModes: ['quiet', 'balance', 'performance'], rates: ['60', '165'], conserveWord: 'conservation', normalWord: 'normal',
  chargeLimit: 80, perfOverride: -1, perfTier: 0,
};
const state: ConsoleState = { hybrid: '', power: '', refresh: '', battery: '', dgpu: '' };
const view: ConsoleView = { armed: null, hudHidden: false, msg: '', msgAt: 0 };
const hits = (s: Style) => Object.fromEntries(consoleFrame(state, cfg, view, zone, s, 0).hits.map((h) => [h.id, h]));

describe('console rows in Picture (fitted)', () => {
  const plain = hits(base), fitted = hits({ ...base, fitted: true });
  const cy = (h: { y: number; h: number }) => h.y + h.h / 2;

  it('keeps the first row (the mode tabs) exactly where it was', () => {
    for (const id of [1, 2, 3, 4, 5]) { expect(fitted[id].y).toBeCloseTo(plain[id].y); expect(fitted[id].x).toBeCloseTo(plain[id].x); }
  });
  it('closes the gap to the second row (CARGO, CFG, the quick row) to 0.6, same x', () => {
    const gapPlain = cy(plain[6]) - cy(plain[1]), gapFitted = cy(fitted[6]) - cy(fitted[1]);
    expect(gapPlain).toBeGreaterThan(40);
    expect(gapFitted / gapPlain).toBeCloseTo(0.6, 1);
    for (const id of [6, 7, 8, 9, 10, 11, 12]) expect(fitted[id].x).toBeCloseTo(plain[id].x);
  });
  it('the second row sits in one line: CARGO, CFG and the quick buttons move together', () => {
    const d = (id: number) => cy(plain[id]) - cy(fitted[id]);
    for (const id of [7, 8, 9, 10, 11, 12]) expect(Math.abs(d(id) - d(6))).toBeLessThanOrEqual(3.5);
  });
  it('without fitted nothing changes (the style flag off or missing)', () => {
    expect(hits({ ...base, fitted: false })).toEqual(plain);
  });
});
