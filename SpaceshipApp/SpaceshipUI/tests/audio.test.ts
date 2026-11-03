import { describe, expect, it } from 'vitest';
import { ATTACK, PEAK_HOLD_MS, RELEASE, audioState, deviceLabel, follow, readout, ringLevels, settled, volumeAngle } from '../src/modules/audio';

describe('audio followers', () => {
  it('attacks fast and releases slowly, and resets the quiet count on sound', () => {
    const s = audioState();
    follow(s, { mBand0: 1 }, 1, false);
    expect(s.sm).toHaveLength(1);                 // the band count follows the host
    expect(s.sm[0]).toBeCloseTo(ATTACK);
    expect(s.rmsS).toBeCloseTo(ATTACK);
    follow(s, { mBand0: 0 }, 1, false);
    expect(s.sm[0]).toBeCloseTo(ATTACK * (1 - RELEASE));
    expect(s.quiet).toBe(1);
    follow(s, { mBand0: 0.5 }, 1, false);
    expect(s.quiet).toBe(0);
  });

  it('the fast feed wins over the once-a-second metrics bands', () => {
    const s = audioState();
    follow(s, { mBand0: 1 }, 1, false, [0, 0, 1]);
    expect(s.sm).toHaveLength(3);
    expect(s.sm[0]).toBe(0);
    expect(s.sm[2]).toBeCloseTo(ATTACK);
  });

  it('lets the levels fall while disabled, keeping the shape', () => {
    const s = audioState();
    s.sm[0] = 1;
    follow(s, { mBand0: 1 }, 1, true);
    expect(s.sm[0]).toBeCloseTo(1 - RELEASE);
    expect(s.rmsS).toBe(0);
  });
});

describe('audio motion (2026-11-03: the user says the ball moves weirdly)', () => {
  it('smooths by time, not by call: two 25 ms steps land where one 50 ms step does', () => {
    const a = audioState(), b = audioState();
    follow(a, {}, 1, false, [1], 0); follow(a, {}, 1, false, [1], 50);
    follow(b, {}, 1, false, [1], 0); follow(b, {}, 1, false, [0.999], 25); follow(b, {}, 1, false, [1], 50);
    expect(b.sm[0]).toBeCloseTo(a.sm[0], 2);
  });
  it('steps once per spectrum frame: a metrics tick with the same frame does not step again', () => {
    const s = audioState(), f = [1];
    follow(s, {}, 1, false, f, 0);
    const v = s.sm[0];
    follow(s, { mBand0: 0.3 }, 1, false, f, 40);
    expect(s.sm[0]).toBe(v);
  });
  it('the peak meter holds, then falls with gravity', () => {
    const s = audioState();
    follow(s, {}, 1, false, [1], 0);
    expect(s.peakS).toBe(1);
    follow(s, {}, 1, true, null, PEAK_HOLD_MS - 50);
    expect(s.peakS).toBe(1);
    follow(s, {}, 1, true, null, PEAK_HOLD_MS + 150);
    const a = s.peakS;
    follow(s, {}, 1, true, null, PEAK_HOLD_MS + 300);
    expect(a).toBeLessThan(1);
    expect(1 - a).toBeLessThan(a - s.peakS); // accelerating
  });
  it('settles to rest once the sound has gone', () => {
    const s = audioState();
    follow(s, {}, 1, false, [1, 1], 0);
    expect(settled(s)).toBe(false);
    for (let t = 50; t < 4000; t += 50) { follow(s, {}, 1, true, null, t); ringLevels(s, false, 0); }
    expect(settled(s)).toBe(true);
  });
  it('fades between the idle ripple and the live ring instead of snapping', () => {
    const lo = audioState(), hi = audioState();
    lo.sm.fill(0.02); hi.sm.fill(0.02);
    lo.rmsS = 0.0195; hi.rmsS = 0.0205;
    const a = ringLevels(lo, false, 0), b = ringLevels(hi, false, 0);
    for (let k = 0; k < a.length; k++) expect(Math.abs(a[k] - b[k])).toBeLessThan(0.01);
    // silence shows the idle ripple by itself (the caller no longer switches on a threshold)
    for (const x of ringLevels(audioState(), false, 3)) expect(x).toBeGreaterThanOrEqual(0.08);
  });
});

describe('pulse ring', () => {
  it('idle keeps the ripple small and nearly even', () => {
    const v = ringLevels(audioState(), true, 3);
    expect(v).toHaveLength(96);
    for (const x of v) expect(x).toBeGreaterThanOrEqual(0.08);
    for (const x of v) expect(x).toBeLessThanOrEqual(0.16);
  });

  it('loud input raises the breath', () => {
    const s = audioState();
    s.sm.fill(1);
    s.rmsS = 1;
    ringLevels(s, false, 0);
    expect(s.breath).toBeCloseTo(0.35 * 1);
    expect(ringLevels(s, false, 0)[0]).toBeGreaterThan(0.2);
  });
});

describe('volume readout', () => {
  it('sweeps the arc from the bottom left by the volume share', () => {
    expect(volumeAngle(0, 1)).toBe(120);
    expect(volumeAngle(100, 1)).toBe(420);
    expect(volumeAngle(100, 0)).toBe(120);
  });

  it('shows MUTED for a negative volume and the percent otherwise', () => {
    expect(readout(-1, 1)).toBe('MUTED');
    expect(readout(49.6, 1)).toBe('50%');
    expect(readout(40, 0.5)).toBe('20%');
  });

  it('upper-cases the device and drops the bracketed part', () => {
    expect(deviceLabel('Speakers (Realtek)')).toBe('SPEAKERS');
    expect(deviceLabel()).toBe('NO DEVICE');
  });
});
