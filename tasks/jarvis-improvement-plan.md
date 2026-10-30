# JARVIS improvement plan (2026-10-30) - DRAFT, awaiting the user's approval

Nothing here is built. Gemini's report was checked against the code; most of its "top fixes" already exist.
Labels: **[M]** measured, **[C]** confirmed in code, **[E]** estimate, **[?]** unknown / needs measuring.

## 1. What the investigation found

### Already built (Gemini treated these as open - skip them)
- [C] Persona path bug fixed (`prompt.py:137`). Same `num_ctx` in `warm`, `chat_json`, `chat_stream` (no model reload). Native `/api/chat`, `keep_alive` 10 min.
- [C] Streaming TTS: first chunk after 5 words, next sentence synthesised while the current one plays. Kokoro full model on the RTX via onnxruntime-gpu [M] 0.3 s/sentence vs 1.0 s CPU. Filler cache, `speakable()`, `pronounce.txt`.
- [C] Whisper small.en CUDA fp16, VAD, `condition_on_previous_text=False`, hotwords, repeat/phantom/confidence guards, CPU fallback.
- [C] Commands skip the LLM. Undo window, pending-yes, courtesy/ender regexes, room-talk logic, privacy mode, fixed "can't look that up" reply, stop -> 1 s ear, tone filters in `mood.py`.
- [C] Prompt ≤1500 chars, test-enforced, with conditional HUD blocks.

### Contradicts Gemini
- [M] **Torch is not installed** (no torch / sentence-transformers / transformers in the venv). "Remove torch, save 1.1 GB" is void. Embeddings are chroma's ONNX MiniLM.
- [M] Import-only RAM is ~181 MB total (openwakeword +75 is the biggest). The ~1.8 GB idle comes from **loaded models + CUDA mappings**, not packages. [?] per-component split not yet measured.
- [C] Chat model is qwen3:4b-instruct-2507 (non-thinking). `think:true/false` advice does nothing.

### Real open problems
1. [M, old data: 2026-10-17, llama3.1:8b] Chat first sentence is bimodal: 0.16-0.40 s on rapid follow-ups, **3.6-4.3 s on the first chat turn after a gap**. Cause [?]. Predates the qwen3 4B switch, so it needs a new baseline.
2. [C+M] Command latency = 1.0 s silence endpoint (`JarvisSilence`) + ~0.3 s Whisper + reply. The endpoint is the largest cheap win (~0.4-0.5 s [E]).
3. [M] Wake-turn "click -> listening" 0.9 s vs 0.4 s on a follow-up: `time.sleep(chime())` blocks up to 0.8 s before listening starts.
4. [C] Whisper has no `temperature=0.0`, so its fallback retry can add latency / hallucination on noisy clips.
5. [C] `context()` puts "Now: HH:MM" last in the system prompt; the cached prefix breaks at the clock line each minute. Small [E].
6. [?] Wake-word hit rate unmeasured. Two paths (W0 + HV); the planned "Hey Clover" training (10B) is the user's call.
7. [?] HUD GPU use (80% reported with Rainmeter on) belongs to the HUD/CSpace, not JARVIS.

### Rejected / deferred
- SQLite FTS5 memory swap (loses paraphrase recall) - defer.
- Kokoro FP16 / torch removal / `think` mode - moot or no gain.
- Silent "cancel/nothing" - could swallow a real cancel of a timer or confirmation.
- Global 2-sentence cap - breaks calendar/to-do readouts; per-lane only.
- New `\\.\pipe\cspace_jarvis` - reuse the existing `host_pipe.py` / `HostPipeWire`.
- "Can't set reminders yet" unsupported-capability lines - reminders/timers/to-do exist.
- Gemini persona exemplars that invent capabilities - Phase 10 tone work needs the user's hand-review first.

## 2. Slices (one at a time; failing test first; commit only on the user's word)

Gates for every slice: `test_jarvis: OK` under venv python AND `py -3`; `check_voice: OK`; `check_route.py` 0 of 65 changed; run on a scratch copy; RAM/CPU pass at the end; no weights/logs/secrets staged; stage by name.

### J0 - Baseline (measure first, no code change to JARVIS)
- Goal: replace guesses with numbers on the current qwen3 4B.
- Scope: a scratch script outside the repo that calls Ollama `/api/chat` and records `load_duration`, `prompt_eval_count/duration`, `eval_rate`, `/api/ps` (GPU vs CPU split), plus `nvidia-smi` clocks/VRAM, for: warm back-to-back, after 60 s idle, after 5 min idle. Plus per-component RAM/VRAM (load Whisper, Kokoro, MiniLM, Vosk, openWakeWord one at a time in the scratch copy) and GPU use by process (HUD vs JARVIS).
- Non-goals: no change to JARVIS or Ollama settings.
- Accept: a table of measured numbers; the spike either reproduced and attributed, or shown gone.
- Risk: loads the real chat model -> **needs the user's OK**. Rollback: delete the scratch script.

### J0 RESULT (2026-10-30, qwen3:4b-instruct-2507, num_ctx 2048, ~570-token prompt, Ollama alone, JARVIS not running) [M]
- Fully on GPU (2.88 GB VRAM, 100%). First-ever load 20.1 s (disk), so startup preload matters.
- Warm: first token 0.11 s. After 60 s and 300 s idle (GPU drops to P8, 180 MHz): 0.30-0.32 s, prefill 0.25 s vs 0.04 s warm. The idle penalty is ~0.2 s, not 3.6-4.3 s.
- Conclusion: the old 3.6-4.3 s spike is NOT reproduced by qwen3 4B alone. It was llama3.1:8b and/or contention with Whisper/Kokoro/wake word in the real pipeline [?]. J1 is downgraded: no keep-warm ping (0.2 s is not worth a GPU wake-up loop); re-check with the per-turn timing log (6j) in the combined live test.

### STATUS 2026-10-30
- J0 done. J2 + J3 built and committed (f3a69b0, by the other session together with its own work); test_jarvis OK under venv and py -3, check_voice OK. `check_route.py` no longer exists. NOT copied live, not pushed. Short utterances end after 0.72 s of quiet vs 1.02 s [M, fake mic stream].
- J4 measured, NO CHANGE (not worth it). Per component [M, same process, working set / VRAM]: Whisper small.en +160 MB / +704 MB; Kokoro on GPU +1063 MB / +564 MB; openWakeWord+VAD +40 MB; MiniLM +109 MB; Vosk small +14 MB; imports ~190 MB. Total ~1.54 GB RAM, 1.27 GB VRAM. Kokoro's RAM is the CUDA/cuDNN runtime; ORT options (no arena, device-allocator initializers) saved 0-13 MB. Dropping GPU Kokoro would save ~1 GB RAM but cost ~0.7 s per sentence; `JarvisIdleUnload` already frees it after 10 min idle. Left as is.
- J5 skipped: warm prefill is 0.04 s for 570 tokens, nothing to gain from moving the clock line.
- J6 (wake evaluator + any-name) and J7 (CSpace supervisor over the pipe) not started: J6 needs the user's own recordings; J7 touches the dirty SpaceshipApp tree.

### J1 - (downgraded, see J0 result) first-turn-after-gap spike
- If clocks / idle downclock: a cheap tiny keep-warm ping near the expected turn; if cold KV/prefill: stable-prefix ordering (clock to the end, J5); if partial CPU offload: fix `num_gpu`/`ollama_on_cpu` path.
- Accept: first-turn first-sentence p50 within 1 s of the warm figure, measured before/after. Worth it: yes, largest felt problem.
- Non-goal: no model change.

### J2 - Adaptive endpointing (+ chime overlap)
- Goal: short commands end ~0.4-0.5 s sooner without cutting off long sentences.
- Scope: `mic._listen` only. Keep `JarvisSilence` as the long ceiling; shorten the quiet window after a short utterance (e.g. ≤2 s of speech) and when the partial transcript is a known command shape; start listening while the chime plays (do not sleep the whole chime).
- Accept: unit test with synthetic audio blocks (speech/silence patterns); clipped-sentence rate not worse on a recorded set [?]. Setting `JarvisSilence` still wins when set explicitly. Rollback: revert one file.
- Risk: cutting people off. Mitigate: ceiling unchanged, new `JarvisFastEnd=0` switch.

### J3 - Whisper hygiene (small)
- `temperature=0.0`, an n-gram repeat guard added next to `no_repeats()`. Test: existing hallucination fixtures plus a looped-text case. Worth it: small, nearly free.

### J4 - Idle RAM (after J0)
- Only act on the biggest measured item. Candidates: unload Kokoro/MiniLM with the existing idle unload (`unload_idle` already frees Whisper + voices after 10 min), or defer openWakeWord's 75 MB. Accept: measured MB saved and no first-turn regression. Skip if the number is small.

### J5 - Prompt-prefix stability
- Move "Now: HH:MM" to the end of the user message. Accept: `prompt` tests green, `prompt_eval_duration` drop measured in J0's script; keep only if the gain is measurable.

### J6 - Wake word (DECIDED 2026-10-30: "Hey Jarvis" stays the default; any new name must be trainable from setup)
- Step 1: an evaluator (replay recorded clips; false accepts / misses at current thresholds) so changes are measured.
- Step 2: "any name" design. [C] today's training (`wake.train`) only builds a small check on top of the hey_jarvis model; it cannot make a different name work. A true new name needs either (a) a custom openWakeWord .onnx (synthetic-data training, heavy, offline), or (b) a Vosk grammar spotter for the typed name, gated by the existing Silero VAD (Vosk and the stop-word grammar already exist; no new package; [?] CPU/accuracy to measure). Smallest experiment first: (b) in a scratch script against recorded clips, report false accepts/misses and CPU, then ask before wiring it in. `JarvisWakeName` setting; default stays Jarvis.

### J7 - Process supervision over the existing pipe (CSpace side)
- P6-2 supervisor and the `jarvis.update` / `jarvis.cmd` messages through `HostPipeWire`/`Protocol.cs` and `jarvislib/host_pipe.py`. Needs a C# + Python contract test. Do after J0-J3.

J7 BUILT 2026-10-30 (not committed, not live): `JarvisSupervisor.cs` (pure logic, 5 tests) wired in `Program.cs` PushJarvis/JarvisCommand. The pipe was NOT needed: the app already starts JARVIS and watches jarvis.txt; the supervisor adds restart-after-crash only. `dotnet build` 0 errors, `dotnet test` 303/303. Never run against a real crash.

### Parked (user's call to pull forward)
Legion power mode (S2-35); tone/personality work (Phase 10: **tell the user and get their hand-review first**).

## 3. Order and checkpoints
J0 -> **checkpoint (user sees numbers)** -> J1 + J2 + J3 (independent, each its own commit) -> **checkpoint (one combined live test)** -> J4/J5 only if J0 numbers justify -> J6/J7 on the user's decision.

## 4. Risks
| Risk | Impact | Mitigation |
|---|---|---|
| Spike cause differs from guess | M | J0 before any fix |
| Faster endpointing clips speech | M | ceiling kept, switch to disable |
| Old 10-17 numbers misleading | M | re-baseline in J0 |
| Tests touch Windows destructive calls | H | fakes first, scratch copy, dry-run grep per `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md` |

## 5. Open questions for the user
1. OK to run J0 (loads the real qwen3 4B in Ollama, no JARVIS code change)?
2. Wake word: tune current "Hey Jarvis", or go to the planned "Hey Clover" training?
3. Pull the game governor / Legion power mode forward, or stay parked?
4. Weather/RSS: keep opt-in as planned?

### PHASE 10 ANSWERS APPLIED 2026-10-30 (not committed, not live-tested)
- (b) default mood is now `mirror` (prompt.py, mood.py, control.lua); no JarvisPersonality key was in Settings.inc, so the live setting follows the default. Tests that pinned "playful" as the default were changed.
- (c) `JarvisCallMe=Sir` -> `Mr. Sorsa` in Skins/Spaceship/@Resources/Settings.inc (one line; backup in the session scratchpad). persona.txt NOT edited: it still says "sir" in almost every reply and "Mr. Sorsa" only on serious topics. Needs the user's wording.
- (d) "As an AI" was already allowed (only "hope this helps" is banned). No change.
- Slice 3 done: timed mood ("be serious for the next ten minutes", up to 4 h, this session only, saved setting untouched). Not doable without approval: trained wake model, voice training, other-speaker detection.
- Still open: answer length (1-3 sentences) and the "who made you" wording.
