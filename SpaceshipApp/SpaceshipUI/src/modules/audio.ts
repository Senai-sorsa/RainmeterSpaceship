import { type Readings, val } from './readings';

// Data side of Skins/Spaceship/@Resources/Scripts/audio.lua: band smoothing, the peak and loudness followers, the pulse
// ring's spoke levels, the volume arc and the readout text. The drawing is not ported yet.
// shortcut: volume and device name are parameters, the host does not report them yet (the Lua reads the Audio measure).

export const NB = 96;
export const DASH_A0 = 120;
export const DASH_SWEEP = 300;
const NS = 96;

export type AudioState = { sm: number[]; rmsS: number; peakS: number; breath: number; quiet: number };

export const audioState = (): AudioState => ({ sm: new Array<number>(NB).fill(0), rmsS: 0, peakS: 0, breath: 0, quiet: 0 });

const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));

/** One smoothing step per redraw. `every` is the frame step since the last redraw; `disabled` zeroes the levels. */
export function follow(s: AudioState, r: Readings, every: number, disabled: boolean): void {
  const rms = disabled ? 0 : clamp(val(r, 'mRMS'), 0, 1);
  const peak = disabled ? 0 : clamp(val(r, 'mPeak'), 0, 1);
  s.rmsS = s.rmsS * 0.6 + rms * 0.4;
  s.peakS = Math.max(peak, s.peakS * 0.85);
  s.quiet = rms < 0.01 ? s.quiet + every : 0;
  for (let i = 0; i < NB; i++) {
    const v = disabled ? 0 : clamp(val(r, `mBand${i}`), 0, 1);
    s.sm[i] = s.sm[i] * 0.5 + v * 0.5;
  }
}

/** Spoke tip levels 0..1 for the pulse ring. Moves the breath toward the loudness; idle gives a slow ripple. */
export function ringLevels(s: AudioState, idle: boolean, frame: number): number[] {
  // the spectrum is laid out twice round the ring (mirrored), so the ring stays balanced
  const raw: number[] = [];
  for (let k = 0; k < NS; k++) {
    let u = (k / NS) * 2;
    if (u > 1) u = 2 - u;
    const f = u * (NB - 1);
    const i0 = Math.floor(f), i1 = Math.min(NB - 1, i0 + 1);
    raw[k] = Math.sqrt(clamp(s.sm[i0] * (1 - (f - i0)) + s.sm[i1] * (f - i0), 0, 1));
  }
  // a wide gaussian window turns the spectrum into gentle rounded swells
  const soft: number[] = [];
  for (let k = 0; k < NS; k++) {
    let acc = 0, wsum = 0;
    for (let d = -8; d <= 8; d++) {
      const w = Math.exp(-(d * d) / 18);
      acc += raw[(((k + d) % NS) + NS) % NS] * w;
      wsum += w;
    }
    soft[k] = acc / wsum;
  }
  const mean = soft.reduce((a, b) => a + b, 0) / NS;
  s.breath += (clamp(mean * 1.4 + s.rmsS * 1.2, 0, 1) - s.breath) * 0.35;
  return soft.map((x, k) =>
    idle ? 0.12 + 0.04 * Math.sin((k / NS) * 2 * Math.PI * 3 + frame * 0.05) : 0.7 * s.breath + 0.3 * x);
}

/** End angle in degrees of the volume arc: sweeps from DASH_A0 by the volume share, scaled by the spin-up (0..1). */
export const volumeAngle = (vol: number, spin: number) => DASH_A0 + DASH_SWEEP * clamp(vol / 100, 0, 1) * spin;

/** The readout under the dial: MUTED for a negative volume, else the percent after the spin-up. */
export function readout(vol: number, spin: number): string {
  if (vol < 0) return 'MUTED';
  return `${Math.floor(Math.max(0, vol) * spin + 0.5)}%`;
}

/** The device name as the dial shows it: upper case, the bracketed part dropped. */
export function deviceLabel(name = 'NO DEVICE'): string {
  // shortcut: a nested bracket keeps its tail (Lua's %b() drops the whole group), upgrade when a device name needs it
  return name.toUpperCase().replace(/\s*\([^)]*\)/g, '');
}
