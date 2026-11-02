import { signal } from '@preact/signals';

// The host's audio.spectrum (AudioSpectrumFeed.cs): ~20 frames a second while sound plays, one quiet frame when it stops.
// The audio ring follows it; system.metrics' once-a-second spectrum is only the fallback before the first frame.

/** The newest bands, 0 to 1, low to high; null until the host sends one. */
export const audioSpectrum = signal<number[] | null>(null);

const isUnit = (v: unknown) => typeof v === 'number' && Number.isFinite(v) && v >= 0 && v <= 1;

/** Accepts {type:'audio.spectrum', bands:[1..64 numbers in 0..1]}; anything else is ignored. */
export function acceptAudioSpectrum(m: unknown): void {
  const o = m as Record<string, unknown> | null;
  if (typeof o !== 'object' || o === null || o.type !== 'audio.spectrum') return;
  const b = o.bands;
  if (!Array.isArray(b) || b.length === 0 || b.length > 64 || !b.every(isUnit)) return;
  audioSpectrum.value = b as number[];
}
