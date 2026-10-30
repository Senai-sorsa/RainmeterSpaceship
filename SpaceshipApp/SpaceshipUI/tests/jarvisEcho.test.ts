import { describe, expect, it } from 'vitest';
import { orbEcho, orbStep, type OrbMotion } from '../src/modules/jarvis';

const rest: OrbMotion = { lvl: 0, act: 0, fIdle: 0, fAct: 0 };
const W = [255, 255, 255, 255] as [number, number, number, number];

describe('orb motion (jarvis.lua 317-329)', () => {
  it('level rises fast and falls slowly', () => {
    const up = orbStep(rest, 'speaking', 1, 1);
    expect(up.lvl).toBeCloseTo(0.55);
    const down = orbStep({ ...rest, lvl: 1 }, 'idle', 1, 1); // idle ignores the level
    expect(down.lvl).toBeCloseTo(0.82);
  });

  it('echo strength heads to 0.55+0.45*lvl speaking, 0.25 thinking, 0 otherwise', () => {
    let m = rest;
    for (let i = 0; i < 80; i++) m = orbStep(m, 'speaking', 1, 1);
    expect(m.act).toBeCloseTo(1, 3);
    for (let i = 0; i < 80; i++) m = orbStep(m, 'thinking', 1, 1);
    expect(m.act).toBeCloseTo(0.25, 3);
    for (let i = 0; i < 80; i++) m = orbStep(m, 'idle', 0, 1);
    expect(m.act).toBeLessThan(3 / 255);
  });

  it('frames advance by dt times the state speed; a bad level counts as 0', () => {
    expect(orbStep(rest, 'thinking', 0, 2).fIdle).toBe(3);
    expect(orbStep(rest, 'offline', 0, 3).fIdle).toBeCloseTo(1.05);
    expect(orbStep(rest, 'speaking', NaN, 1)).toEqual({ lvl: 0, act: 0.1375, fIdle: 1, fAct: 1 });
  });
});

describe('orb echo (jarvis.lua 346-350)', () => {
  it('is not drawn while act is under 3/255', () => {
    expect(orbEcho({ ...rest, act: 2 / 255 }, [0, 200, 255, 255], W, 1, 1)).toBeNull();
  });

  it('swells with the level, lightens the colour and fades with act', () => {
    const e = orbEcho({ ...rest, act: 1, lvl: 1 }, [0, 200, 255, 255], W, 1.1, 1.2)!;
    expect(e.d).toBeCloseTo(330 * 1.1 * 1.4);
    expect(e.col).toEqual([102, 222, 255, 255]);
    expect(e.alpha).toBe(150);
    expect(e.k).toBeCloseTo(1.32);
    expect(e.tint).toBe(0.3);
  });
});
