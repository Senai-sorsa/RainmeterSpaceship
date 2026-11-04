# F1 (cracked speech on the speakers): what others found online (2026-11-04)

Searched: sounddevice/PortAudio WASAPI, Kokoro TTS, Realtek, NVIDIA DPC latency. Nothing found matches our exact case (24 kHz Kokoro,
sounddevice blocking writes, WASAPI shared + auto_convert, Realtek), so everything below is a LEAD to test, not a diagnosis.
Our own evidence (handoff log m, n): no clipping, GPU = CPU output, 0 device underflows reported in a sandbox, own-48 kHz resample was WORSE,
100 ms buffer smoothest, glitches at random spots.

## Leads, with what was reported and how it fits us
1. **Windows' own sample-rate converter in shared mode.** `auto_convert=True` makes WASAPI insert Windows' converter; quality depends on the driver.
   SDL turned WASAPI auto-conversion OFF in 2021 after "reports that WASAPI's resampler introduces distortions", and for some drivers (RME)
   "resampling quality issues". Fits: our 24 kHz stream into a 48 kHz Realtek device. Test: open the stream at the device's own 48 kHz with a
   GOOD resampler. Our own 129-tap sinc was blind-tested glitchier (one listen each, position effect not excluded), so a rerun with a throwaway
   first slot is needed before dropping this lead. NOTE: scipy's `resample_poly` is blocked here (Application Control blocks scipy's .pyd), so any
   other resampler must be pure numpy.
2. **Driver-level stalls that PortAudio cannot see (DPC latency).** Several threads blame `nvlddmkm.sys` (NVIDIA) DPC spikes for audio crackle,
   especially while the GPU is busy; rule of thumb above about 2000 microseconds = audible pops. JARVIS runs Kokoro/Whisper on the GPU, which matches
   "random spots, only while he speaks". A DPC stall breaks the device's playback even when `write()` never reports an underflow, which would explain
   why our sandbox saw 0 underflows. Test (read-only, nothing installed): sample Windows performance counters `% DPC Time` and `DPCs Queued/sec`
   during a spoken reply with synthesis running, compare with silence; LatencyMon (a free tool, the user would install it) names the driver.
   Fix candidates if confirmed: NVIDIA Studio driver or a different driver version, "Prefer maximum performance" power mode, run synth on the CPU
   (JarvisKokoro device setting) as a test.
3a. **FOUND ON THIS PC (read-only check, 2026-11-04):** Nahimic is installed and RUNNING: NahimicService (Automatic), processes NahimicSvc32/64 and
   NahimicAPO4Volume, drivers "Nahimic APO 4" 4.15.4.0, "Nahimic VAD", "Nahimic mirroring device", "Nahimic Easy Surround device" (all dated 2025-10-09);
   Realtek driver 6.0.9986.1 (2026-05-04). Nahimic is a sound-processing layer (APO) in the playback path and is the OEM suite the Realtek-crackle
   guides most often name as a conflict. Idle DPC baseline measured: % DPC time avg 0.91 (max 1.56), DPCs queued/sec avg 6178, % interrupt time avg 1.83.
   CHEAPEST TEST (user, 1 minute, reversible): in the Nahimic app switch its processing OFF (or Sound settings > the speakers > Properties >
   Enhancements > disable), restart JARVIS, listen to a reply. I did not touch it (system setting, not mine).
3. **Realtek / Windows enhancements.** Common advice: disable Audio Enhancements and Spatial Sound on the device, check power management, remove OEM
   suites (Nahimic, Waves MaxxAudio), try Microsoft's generic High Definition Audio driver or roll the Realtek driver back. Already on our list.
4. **Bigger/steadier writes.** sounddevice docs: raise `latency`/`blocksize`; keep work off the thread that writes. We write 40 ms blocks from a worker
   thread; the 100 ms buffer helped. Try 0.2 s and a 100 ms block as one more A/B slot (setting `JarvisPlayerLatency` already exists).
5. **Kokoro chunk-join clicks.** Other Kokoro projects fixed clicks at sentence joins with edge fades or an 8-30 ms crossfade, and by NOT
   normalizing per chunk. We already trim and fade 10 ms per clip and do not normalize per chunk, and the log shows seams are measured by
   `voice_gaps`. Our glitches are at random spots, not at joins, so this is a weak lead.
6. **Sample-rate framing.** Playback must match Kokoro's 24 kHz; partial frames can click. We write whole float32 blocks; weak lead.

## Proposed order (smallest first, each needs the user's ears or one read-only measurement)
A. Ship the diagnostic (device under-run count + peak per clip in `jarvis.log`; `tasks/jarvis-f1-diagnostic.patch`), no change in sound.
B. Read-only DPC measurement during speech (lead 2).
C. Blind A/B round 2 (first slot a throwaway): 0.1 s / 0.2 s / the device's native 48 kHz with a numpy polyphase resampler. Tell the user BEFORE any sound.
D. FIRST, cheapest: user switches Nahimic processing off (lead 3a) and listens; then Windows enhancements / spatial sound off (lead 3).

## Sources
- sounddevice platform-specific settings (auto_convert): https://python-sounddevice.readthedocs.io/en/latest/api/platform-specific-settings.html
- PortAudio issue 314 (shared mode rate mismatch / auto-convert): https://github.com/PortAudio/portaudio/issues/314
- SDL disabled WASAPI built-in resampling (distortion reports): https://git.axiodl.com/encounter/SDL/commit/9e264b921b2f81e2c3d55693f76e06d143c2fbb7
- sounddevice underflow discussions: https://github.com/spatialaudio/python-sounddevice/issues/384 and https://github.com/spatialaudio/python-sounddevice/issues/155
- Kokoro boundary clicks: https://github.com/ZirekHQ/dengjen-tts/issues/305 and https://github.com/ZirekHQ/dengjen-tts/pull/312
- Realtek crackling fixes: https://helpdeskgeek.com/fix-realtek-audio-crackling-popping-windows/ and https://appuals.com/realtek-sound-crackling-issue-windows-11/
- NVIDIA DPC latency and audio: https://forums.developer.nvidia.com/t/driver-version-516-94-introduces-high-dpc-latency-and-serious-audio-problems/238290 and https://www.bluecataudio.com/Blog/?p=4390
