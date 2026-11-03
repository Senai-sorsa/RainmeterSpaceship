# JARVIS voice smoothness plan (measured; PLAN ONLY, nothing in the product changed)

Written 2026-11-03 (measurement scripts and A/B WAVs are in tasks/voice-measurements/; see the appendix at the end for code map and context). User's problem: voice is choppy and not very human; user confirms playback and chunking are the
main issues. Scope: fix everything possible **without changing the TTS engine** (Kokoro stays; a more human engine
is deferred, see section 9). Companion: `jarvis-persona-plan-2026-11-03.md`.
Labels: **[measured]** by me this session, **[code]** read in the repo, **[guess]**.

## 1. What I measured (scratch scripts in the session scratchpad; no repo files touched, no audio played aloud)
Setup note: in this scratch run CUDA was blocked ("Application Control policy has blocked cublas64_12.dll"), so Kokoro ran on
the CPU (real-time factor ~0.30-0.41; live on the GPU it was ~0.24 s a sentence earlier). Seam/latency numbers below do not depend on this.

| Finding | Number | Meaning |
|---|---|---|
| Output device / API | Realtek speakers, **MME** host API (the default); device rate 44.1 kHz, Kokoro is 24 kHz | Slowest, highest-latency Windows audio path; the driver resamples |
| Cost of a new `OutputStream` (what `play_samples` does for every chunk) | open ~45 ms, first write ~77 ms, hardware latency 0.18 s; open+first write median **123 ms** (MME) | Every chunk starts with a dead stretch before sound |
| Same with `latency="low"` | 104 ms | Small gain |
| Same with **WASAPI** + auto-convert + low latency | **73 ms**, device latency **0.025 s** | WASAPI is ~7x lower latency |
| Silence at the END of every Kokoro clip (below -45 dB) | **0.27-0.37 s** (10 clips, all alike); at the start 0.02-0.05 s | Uneven, built-in pauses we do not control |
| Mid-sentence seam today (5-word fragment, then rest): fragment tail 0.10-0.12 s + rest lead 0.03-0.04 s + stream reopen ~0.12-0.18 s | about **0.27-0.35 s of silence in the middle of a clause** | The audible "chop". Whole-sentence synthesis has none of this |
| Which replies are cut this way (semi-live results, 308 model replies) | **83% start with a mid-sentence fragment** ("I can perform various tasks | to assist you, sir."); 211 replies have 2 chunks, 57 have 3, 19 have 4 | The seam is in almost every answer |
| Tiny trailing chunks | **178 of 389** later chunks are under 6 words (e.g. just "sir.") | Each tiny chunk = another stream open + another gap |
| Loudness across clips | RMS 0.054-0.058, peaks 0.45-0.57 | Already even: loudness normalisation is NOT needed (dropped from the plan) |
| Fragment vs whole sentence: total audio length | whole 3.66 s; fragment+rest 3.62-3.99 s (+ stream gap) | Splitting adds no content, only gaps |
| Pitch at the seam | my crude autocorrelation f0 was too noisy to trust | Not claimed; the intonation reset is still **[guess]** and is judged by ear on the A/B files below |
| Under-runs | not reproducible here (CPU synth of the rest chunk is borderline: ~1.3-1.7 s vs 1.4-1.9 s of fragment audio; on the GPU it is ~0.25 s) | Needs the new gap log (V0) in live use; not assumed |

Files for the user to listen to (same sentence, "You have three meetings today, and the first is at nine."):
`...\scratchpad\A_whole.wav` (whole sentence, reference), `B_current_seam.wav` (fragment + 0.15 s device gap, like today),
`C_trimmed_crossfade.wav` (fragment+rest, trimmed and faded), `D_overlap_15ms.wav` (trimmed with a 15 ms crossfade).
Folder: `C:\Users\Senai\AppData\Local\Temp\claude\C--Users-Senai-RainmeterSpaceship\bdabfc57-75bf-41cc-8e4e-dace94170cbb\scratchpad\`.

## 2. Root causes, now ranked by evidence
1. **A new audio stream per chunk, on the MME API [code + measured].** 120 ms of dead time plus up to 0.18 s device latency at every seam.
2. **Mid-sentence first chunk in 83% of replies [measured]** (the 5-word fast start), plus lots of tiny tail chunks.
3. **Uncontrolled silence [measured]:** 0.3 s tail on every clip, so sentence pauses are whatever Kokoro leaves, and mid-clause seams get tail + device gap.
4. **Playback API [measured]:** MME with driver resampling (24 kHz to 44.1 kHz) instead of WASAPI.
5. **Flattened punctuation [code]:** `speakable()` turns "-", ";", "..." into commas.
6. Under-runs: unconfirmed. 7. Voice/timbre naturalness: engine-limited, partly tunable (speed, voice blend).

## 3. Fix list (no engine change). Order = implementation order
All behind one switch `JarvisVoiceSmooth` (1 = new path, 0 = today), so rollback is a setting.

**Package 1 - playback (fixes causes 1, 3, 4)**
- **V1 Persistent stream.** One output stream per reply (or per "speech session"): opened when the first audio is ready, kept
  open, chunks written back to back, closed after the last chunk plus a short drain. Replace the per-chunk `with OutputStream`
  in `play_samples`/`_speak_queue` by a small `Player` object (open / write(chunk) / abort() / close()). Keep: 40 ms blocks, cancel
  and abort on barge-in/stop, the orb level (`S.set(level=...)`), the echo reference (`far_add`), headphone gain, pop-up typing progress.
- **V2 WASAPI shared mode, low latency, auto-convert** (measured 73 ms open, 0.025 s latency), with automatic fallback to the current default API if opening fails or the device is exclusive/unavailable. Resample 24 kHz to the device rate once in our code with a proper filter (`scipy.signal.resample_poly` if present, else a small numpy polyphase) only if auto-convert is unavailable.
- **V3 Trim + fade:** cut each clip's leading/trailing audio below -45 dB (keep ~20 ms), fade 8-15 ms in/out (or a 10-15 ms overlap crossfade when the next chunk is a continuation of the same sentence).
- **V4 Pause control:** the gap between chunks becomes a chosen number: continuation of the same sentence 0-40 ms (crossfade), after a comma-clause 120-180 ms, after a sentence 250-350 ms (about today's tail, but now consistent), after a paragraph/topic change 450 ms. Silence is written into the same open stream.
- **V5 Prime the device:** keep the stream warm (open and writing silence) from "speaking" state, so the first word does not wait for the device; close after about 1.5 s idle.

**Package 2 - chunking (fixes causes 2, 6)**
- **V6 Clause-aware first chunk.** Release the first chunk at the first natural boundary (sentence end, or comma/colon/dash) after at least 4 words; never inside "Mr./Dr.", numbers, times, or "sir". If no boundary arrives within about 9 words, release at that word count as today. Measure first-sound latency before/after; budget +0.15 s p50 (currently 0.3-0.5 s).
- **V7 No orphan chunks.** A trailing piece under ~4 words ("sir.") is held and joined to the previous clip's text if still unsynthesised, otherwise synthesised and joined with a 0 ms continuation join (no stream gap, since V1 keeps the stream open).
- **V8 Merge short sentences:** consecutive short sentences (under ~6 words) already waiting in the queue are synthesised as one clip, keeping the sentence punctuation so Kokoro still pauses naturally.
- **V9 Chunk ceiling:** a sentence over ~25 words is split at the best comma near the middle, not at an arbitrary word.
- **V10 Jitter buffer:** if the next chunk is not synthesised when the current one is about to end, write a short pause (V4 continuation length) and log an under-run, rather than letting the device starve; prefetch up to 2 chunks (queue is already 3 deep).

**Package 3 - text and voice character (cause 5, 7; judged by ear)**
- **V11 Punctuation:** keep commas as commas, let em dash/semicolon become a comma + slightly longer continuation pause, "..." a 350 ms hesitation pause (dry-wit lines), instead of flattening all to equal pauses. Pronunciation tests in `test_jarvis.py` stay green.
- **V12 Speed/voice A/B:** speed 0.92/0.96/1.00; voices `bm_lewis` (now), `bm_george`, `bm_fable`, `bm_daniel`, and blends (the existing 50/50 `default` blend style) through the A/B harness; pick by ear.
- **V13 Light finishing, optional switch:** 70 Hz high-pass, very mild limiter on the final mix (no coloration; echo reference taken after it).
- **V14 Fallback consistency:** if Kokoro fails mid-reply, speak the whole reply with the Windows voice instead of swapping per sentence.
- **V15 Warm model:** dummy synth at start and after idle unload.
- **V16 Fillers/acks** ("Opening Spotify.") go through the same Player so they join cleanly; their trailing 0.3 s is trimmed.

## 4. Expected effect (estimates from the measurements; to be confirmed after the build)
- Mid-sentence silence: 0.27-0.35 s now to ~0.00-0.04 s.
- Sentence gaps: variable ~0.45-0.65 s (tail + device open) to a chosen ~0.25-0.35 s.
- Orphan chunks: 178 of 389 later chunks to near zero.
- Device latency: 0.18 s (MME) to ~0.03 s (WASAPI), also helps barge-in/stop feel.

## 5. Test and measurement plan (I do all of it; the user only listens at the end)
1. **V0 baseline script** `tools/voice_gaps.py` (new, tools only): offline - renders the voice test set (`tools/voice_cases.txt`, ~25 lines: acks, 1-3 sentence answers, numbers/times, a long explanation, a status readout, a joke, 83%-style fragment cases) the old way (fragments, per-chunk streams modelled with the measured open cost) and the new way, and reports per-seam silence in ms, count of seams, orphan chunks, total length. Writes A/B WAVs in a scratch folder.
2. **Fake-device unit tests** in `test_jarvis.py` (fakes installed before import, no real audio): Player writes chunks in order into one stream; abort stops within one block; cancel drops queued audio; trim/fade keep length and never clip; pause lengths per boundary type; clause-aware chunker cases (including "Mr. Sorsa", "1:48 AM", "sir." orphans); `JarvisVoiceSmooth=0` yields the old behaviour.
3. **Real-device smoke** (me, silent): open the WASAPI stream with zero-amplitude audio, measure open time and confirm fallback to MME works when the device name is wrong. No audible test without the user's yes.
4. **Gap log** (live and semi-live): per reply, one line: chunks, per-seam gap ms, synth time vs audio length, under-run count, first-audio time. Semi-live harness adds a `voice` mode that synthesises the real replies from the banks (on whichever device is available) and writes the same stats.
5. **Regression gates:** `test_jarvis` OK (venv + py -3); `test_host_pipe` failed: 0; semi-live 8B main+fresh cost not higher; barge-in (wake and voice modes) and stop word still stop within one block (fake-clock test); first-audio p50 not worse than +0.15 s; zero tripwires.
6. **User listening session at the end** (blind A/B: today vs new, 10 replies); their choice decides speed/voice/pause constants (V4, V12). Constants live in settings so tuning needs no code.

## 6. Risks and how they are handled
- Barge-in/stop and echo cancellation share the playback loop: the Player keeps the same hooks; tests with a fake stream for abort timing.
- WASAPI quirks (exclusive-mode apps, device unplugged, Bluetooth headsets switching profile): automatic fallback to the current API and a log line; headphone gain code unchanged.
- A persistent stream must not hold the device when idle (other apps, Bluetooth headset profile): V5 closes after ~1.5 s idle.
- Clause-aware first chunk may delay the first word: measured against the +0.15 s budget; if over, fall back to the 5-word start only for long sentences.
- Do not touch the UI, the Rainmeter skin, or Settings.inc defaults without approval; `JarvisVoiceSmooth` ships default 0 until the user's listening test says 1.

## 7. Phasing
- **S0:** write `voice_cases.txt` + `tools/voice_gaps.py` (baseline numbers into the handoff). No product code.
- **S1:** V1-V5 (Player, WASAPI, trim/fade, pause control) + tests.
- **S2:** V6-V10 (chunking) + tests + first-audio check.
- **S3:** V11-V16 (text/voice character), A/B by ear with the user.
- Each slice: tests, semi-live gate, handoff entry; commit only on the user's word.

## 8. Rollback
`JarvisVoiceSmooth=0`; or `git checkout` of `speech.py`, `tts.py`, `say.py`, `test_jarvis.py`.

## 9. Deferred on purpose: a more human engine
Kokoro stays for now. If after S3 it still sounds too synthetic, the earlier research (Chatterbox Turbo, F5-TTS; Orpheus too heavy; Piper less natural; all web claims unverified, VRAM shared with the 8B model) is the next step, tested offline first with the same voice test set.

## 10. Open items for the user
1. Listen to the four WAVs above and say which seam sounds closest to "right" (B is how it sounds today; C/D are the fix).
2. OK to switch to WASAPI with automatic fallback (the biggest latency win)?
3. Acceptable first-word delay budget (+0.15 s proposed)?
4. Headphones or speakers? (decides V13 and levels)

## Sources used for background (web, unverified)
- [hematite-kokoros source (chunking, 10 ms crossfade, per-chunk handling)](https://docs.rs/crate/hematite-kokoros/latest/source/src/tts/koko.rs)
- [Kokoro prosody guide](https://deapi.ai/blog/kokoro-tts-guide-how-to-control-41-voices-with-nothing-but-punctuation)

## Appendix - context a new session needs (added 2026-11-03)
### A. Code map (line numbers as of 2026-11-03; re-grep before editing)
- `jarvislib/speech.py`: `play_samples` (l.41: opens `sd.OutputStream` per call, 40 ms blocks, `cancel.is_set()` -> `out.abort()`, `far_add` echo reference,
  `S.set(level=...)` orb, `progress` callback), `speak_all` (l.65: producer thread synthesises `speakable(clean)` via `synth_audio`, queue maxsize 3, logs
  "timing: reply start -> first sentence ..."), `_speak_queue` (l.116: plays each item with `play_samples`, text guard `saying`, `name_until` for his own "Jarvis"),
  `first_words` (l.166, JarvisFirstWords default 5, max 12), `sentences_from` (l.174: the 5-word fast first chunk), `prepare_fillers`/`filler` (l.245/260: status phrases also use `play_samples`).
- `jarvislib/tts.py`: `synth_audio` (l.204: Kokoro -> Piper -> Windows fallback), `_kokoro` (l.60: GPU session via onnxruntime-gpu else CPU; voice from JarvisKokoroVoice,
  default bm_lewis; "default" = 50/50 bm_lewis+am_michael blend; speed = JarvisVoiceRate and JarvisVoiceSpeed), `voice_speed` (l.31), `_windows` (l.144).
- `jarvislib/say.py`: `speakable` (l.39: times, percent, units, ".exe", then `...`, em/en dash, `;` -> ", " ("K5"), then `pronounce.txt` rules).
- `jarvis.py`: l.1214 builds the chain `polish(grounded(no_hope(no_claims(sentences_from(stream))))))`, l.1219 `speak_all(said)`; l.167 `speak_all([text])` for fixed lines;
  barge-in code l.1290-1453 (`barge_in`, `barge_turn`, `JarvisBargeIn` = off | wake (default) | voice); the S2-10 ear window ("Are you talking to me, sir?") l.700-720 and `JARVIS-Repair-Plan.txt` l.4399.
- `mood.polish()` is a generator fed piece by piece; the first piece can be a partial sentence. Any chunking change in `sentences_from` must keep polish/grounded behaviour (tests exist in `test_jarvis.py` near "polish").
### B. Settings that exist (read with `setting(name, default)`; defaults live in Settings.inc, do not edit it)
`JarvisVoice` (kokoro-v1.0.onnx path), `JarvisKokoroVoice`, `JarvisVoiceRate` (1), `JarvisVoiceSpeed` (1.0), `JarvisFirstWords` (5), `JarvisHeadphoneLevel` (60), `JarvisBargeIn` (wake), `JarvisMutedPopup`.
New key to add as a CODE default only: `JarvisVoiceSmooth` (0), plus tunables with code defaults: pause lengths per boundary, trim threshold (-45 dB), fade ms, WASAPI on/off, idle close seconds.
### C. Measurement files (tasks/voice-measurements/)
`m1.py` (per-clip synth time, lead/trail silence, RMS/peak, fragment vs whole), `m2.py` (OutputStream open/first-write/close timing), `m3.py` (host APIs, MME vs WASAPI open cost,
tail envelope, builds the A-D WAVs). Run with the venv python; they import `jarvislib` from the repo and use the real Settings (read-only). `A_whole.wav`, `B_current_seam.wav`, `C_trimmed_crossfade.wav`,
`D_overlap_15ms.wav` = the same sentence four ways, for listening. `NEW-SESSION-PROMPT.md` = the prompt for the next session. Delete the folder when done (not for commit; keep it out of staging).
### D. Environment facts
- Output device: Speakers (Realtek(R) Audio), default API MME (device rate 44.1 kHz); WASAPI index 8 (device latency 0.025 s). Kokoro output is 24 kHz.
- Venv python: `%LOCALAPPDATA%\SpaceshipHUD\venv\Scripts\python.exe`; also `py -3`. Tests must run on a scratch copy that mirrors repo depth (`Skins/Spaceship/@Resources` + `contract/`), env `TZ=ABC+12`.
- CUDA was blocked in the scratch run by an Application Control policy (cublas64_12.dll), so synth ran on the CPU (RTF 0.30-0.41); earlier live GPU measurement 0.24 s/sentence. Check which one you are on.
- Uncommitted working tree at handoff: `jarvislib/routing.py`, `jarvislib/mood.py`, `test_jarvis.py`, `tasks/HANDOFF-jarvis-semi-live.md`, `tasks/jarvis-*-plan-2026-11-03.md`, `tasks/voice-measurements/`.
  Other untracked paths (GodMode/, Refrences-Art/, Images/Render/, tools/blender/, tools/ref_layout_json.py, tools/test_render_frame.py) belong to other sessions: never stage them.
- Semi-live results are gitignored (`tools/semi-live-results/`); newest: `r8-*` (main) and `fresh-r9-llama3-1-8b.jsonl`.
### E. Decisions already made by the user
Kokoro stays; WASAPI with automatic fallback approved; first-word delay up to +0.15 s or somewhat more is fine; the voice flag ships off until the user listens; no new engine; light personality only
(no proactive lines); "sir" injection must not come back; commit only on the user's word.
