import { describe, expect, it } from 'vitest';
import { ATTACK, RELEASE, audioState, deviceLabel, follow, readout, ringLevels, volumeAngle } from '../src/modules/audio';

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
