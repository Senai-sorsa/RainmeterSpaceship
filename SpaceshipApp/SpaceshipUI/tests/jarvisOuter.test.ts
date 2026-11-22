import { describe, expect, it } from 'vitest';
import type { Style } from '../src/draw/canvas';
import { jarvisFrame, orbStep } from '../src/modules/jarvis';

// Live test: when JARVIS starts speaking (or listens, or thinks) only the main inner animation (the ball) may change. The spinning outer ring, the
// geometric shell and the orbit rings stay exactly as they are at rest; only "offline" dims them.
const style: Style = {
  s: 1, tier: 0, glowA: 46, glowW: 3.2, coreWhite: 0.3, hudA: 255, edit: false,
  textGlow: 4, textGlowA: 150, textSmall: 1.85, textLarge: 1.45, fontText: 'Oxanium', fontNum: 'B612 Mono', fontTitle: 'Michroma',
  white: [215, 240, 255, 255], dim: [0, 140, 185, 255], panel: [0, 30, 45, 90], accent: [0, 210, 255, 255],
  warn: [255, 130, 40, 255], alert: [255, 60, 70, 255], text: [170, 235, 255, 255], hi: [255, 105, 135, 255], good: [60, 255, 170, 255],
};
const zone = { x: 0, y: 0, w: 1000, h: 800 };
const LB: [number, number] = [20, 780]; // the label corner, bottom left
const ops = (state: string, level: number, frame: number) => jarvisFrame(frame, { state, level }, style, zone, 500, 400, 'CLOVER', LB);

// everything except the status label (its text, its dot and the callout line are informational and follow the real state)
const outerOf = (list: ReturnType<typeof ops>) => JSON.stringify(list.filter((o) => {
  const s = JSON.stringify(o);
  if (/"text"|"kind":"text"/.test(s)) return false;
  const b = o.shape as { cx?: number; cy?: number; x?: number; y?: number };
  const px = b.cx ?? b.x, py = b.cy ?? b.y;
  return !(typeof px === 'number' && typeof py === 'number' && px < 140 && py > 700); // the label block, bottom left
}));

describe('the outer parts do not react to JARVIS speaking', () => {
  for (const frame of [0, 37, 900]) {
    it(`frame ${frame}: speaking, listening and thinking draw the same outer parts as idle`, () => {
      const idle = outerOf(ops('idle', 0, frame));
      expect(idle.length).toBeGreaterThan(2000);
      expect(outerOf(ops('speaking', 0.9, frame))).toBe(idle);
      expect(outerOf(ops('speaking', 0.2, frame))).toBe(idle);
      expect(outerOf(ops('listening', 0.7, frame))).toBe(idle);
      expect(outerOf(ops('thinking', 0, frame))).toBe(idle);
    });
  }
  it('the voice level changes nothing outside the ball', () => {
    expect(outerOf(ops('speaking', 1, 123))).toBe(outerOf(ops('speaking', 0, 123)));
  });
  it('offline still dims them (that is not a speaking change)', () => {
    expect(outerOf(ops('offline', 0, 50))).not.toBe(outerOf(ops('idle', 0, 50)));
  });
  it('the status label still shows the real state', () => {
    const texts = (state: string) => ops(state, 0.5, 10).map((o) => JSON.stringify(o)).filter((s) => /SPEAKING|STANDBY/.test(s)).join('');
    expect(texts('speaking')).toContain('SPEAKING');
    expect(texts('idle')).toContain('STANDBY');
  });
  it('the inner ball (orbStep) still reacts to speaking', () => {
    const rest = { lvl: 0, act: 0, fIdle: 0, fAct: 0 };
    expect(orbStep(rest, 'speaking', 0.9, 1).act).toBeGreaterThan(0);
    expect(orbStep(rest, 'speaking', 0.9, 1).lvl).toBeGreaterThan(0);
    expect(orbStep(rest, 'idle', 0, 1).act).toBe(0);
  });
});
