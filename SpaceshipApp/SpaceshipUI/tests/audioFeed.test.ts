import { describe, expect, it } from 'vitest';
import { acceptAudioSpectrum, audioSpectrum } from '../src/host/audioFeed';

describe('audio.spectrum (AudioSpectrumFeed.cs)', () => {
  it('takes 1..64 bands in 0..1 and ignores anything else', () => {
    acceptAudioSpectrum({ type: 'audio.spectrum', bands: [0, 0.5, 1] });
    expect(audioSpectrum.value).toEqual([0, 0.5, 1]);
    for (const bad of [
      { type: 'audio.spectrum', bands: [] },
      { type: 'audio.spectrum', bands: new Array(65).fill(0) },
      { type: 'audio.spectrum', bands: [0.2, 1.5] },
      { type: 'audio.spectrum', bands: [0.2, Number.NaN] },
      { type: 'audio.spectrum', bands: '0,1' },
      { type: 'system.metrics', bands: [0.1] },
      null,
    ]) acceptAudioSpectrum(bad);
    expect(audioSpectrum.value).toEqual([0, 0.5, 1]);
  });
});
