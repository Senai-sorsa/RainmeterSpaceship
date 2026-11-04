# Prompt for the new session (copy everything below the line)

---

JARVIS finish-up session. Work only on JARVIS (Skins/Spaceship/@Resources/Jarvis/...). No UI, no Rainmeter skin, no Settings.inc
default changes, no commits unless I say so. Never touch files another session owns (SpaceshipApp/..., GodMode/, Refrences-Art/,
Images/Render/, tools/blender/). Low-token style: use Grep to jump into big files (jarvis.py, routing.py), never read them whole.

## 0. Read first (in this order)
1. `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md` (fakes first, dry-run grep before running, no real destructive calls) and `CLAUDE.md` rules
   (smallest change; before each significant change write goal/scope/non-goals/acceptance/validation/risks/rollback; report real command output).
2. `tasks/HANDOFF-jarvis-semi-live.md` sections 2-5 and the top log entry (2026-11-03 e).
3. `tasks/jarvis-voice-plan-2026-11-03.md` (measured voice plan; the main work) and `tasks/jarvis-persona-plan-2026-11-03.md`
   (only its Track A items listed in section 2 below, and Track B items in section 3).

## 1. State at handoff (2026-11-03, uncommitted working tree)
- Changed, tests green, NOT committed: `jarvislib/routing.py` (OTHER_DEVICE replies; NEAR_MISS = "Could you say that again?"),
  `jarvislib/mood.py` (OFFER_SENT: trailing "Would you like me to...?" cut in polish()), `test_jarvis.py` (tests for both),
  `tasks/HANDOFF-jarvis-semi-live.md` (log entry e). Plus the two plan files and this prompt in `tasks/`.
- Numbers (llama3.1:8b, seed 7): fresh bank cost 32, main 43; test_jarvis OK (venv + py -3), test_host_pipe failed: 0.
- Decisions from me: Kokoro stays (NO new TTS engine); WASAPI with automatic fallback to the current API is APPROVED;
  first-word delay up to +0.15 s or a bit more is fine; headphones/speakers not answered (design for both).
- Scratch measurements of the voice are in the old session scratchpad (m1/m2/m3.py, A-D wav files); recreate under your own
  scratchpad if needed, do not rely on them.

## 2. Scope: lighter personality improvements ONLY
Do (all prompt/text/code-fixed-lines, measured with the semi-live banks):
- A1 dry understatement: one short dry aside max, only when a prompt fact or my own boast earns it; never on serious turns, stress, or failed actions.
  Mirror mood currently says "joke only if the user jokes first": extend carefully, keep playful/serious/brief moods as they are.
- A2 calm "weather report" status readouts (number first, flat, at most one short recommendation) + calm fixed lines for hard failures (mic lost, model offline, Ollama down).
- A3 crisp slightly formal wording in readouts/warnings; contractions stay fine in chat (do NOT ban them).
- A7 acknowledgment phrase bank in our own words ("As you wish", "Right away", "Noted", "Online and ready"), rotated with no immediate repeat, for
  fixed replies that are now "Done." / "Sent." / "Opening X."; keep numbers (volume, timers) intact.
- A8 persona test cases (tag `persona`, ~30, new wording, held out) in `tools/make_cases.py` / `make_fresh_cases.py` + scorer flags
  (`OVERJOKE`, `DRAMA`, `PROACTIVE_CLAIM`, `NO_DRY` as needed) in `tools/score_semi_live.py`. Build these FIRST, take the baseline on 8B and 3B, then change persona.
Do NOT do: proactive unprompted lines (A4), sarcasm toggle / house rules / routines (A5), titles for other users (A6), film-quote copying,
fine-tuning, any "sir" injection by code (I said "sir" is not required).
Rules that must keep holding: never claims an action it did not do; grounded() readings; injection tests; crisis line; polish() caps.
Persona edits touch model output: run BOTH 8B and 3B banks, judge by reading replies as well as cost.

## 3. Fixes to implement (all of them)
### 3a. Voice smoothness (main work, no engine change) - follow `jarvis-voice-plan-2026-11-03.md` sections 3, 5, 7
Measured causes: per-chunk `sounddevice.OutputStream` on MME (open+first write ~123 ms, device latency 0.18 s); 83% of replies start with a
mid-sentence 5-word fragment; 178/389 later chunks under 6 words ("sir." orphans); every Kokoro clip ends with 0.27-0.37 s of near-silence;
`speakable()` flattens "-", ";", "..." to commas. Loudness is already even (no normalisation needed).
Order: S0 `tools/voice_cases.txt` + `tools/voice_gaps.py` baseline (no product code) -> S1 Player (one persistent stream per reply, WASAPI shared
low-latency auto-convert with automatic fallback to the old path, trim/fade or 10-15 ms overlap, pause control by boundary type, device warm-up,
close after ~1.5 s idle) -> S2 chunking (clause-aware first chunk after >=4 words, no orphan chunks, merge short sentences, split long ones at a comma,
jitter buffer + under-run log) -> S3 text/voice (punctuation pauses, speed 0.92-1.0 and voice/blend A/B files for me to listen to, fallback consistency, warm model, fillers through the Player).
Everything behind `JarvisVoiceSmooth` (ships default 0 until I listen; do not change Settings.inc defaults, add the key as a code default only).
Keep: barge-in/stop abort within one 40 ms block, orb level `S.set(level=...)`, echo reference `far_add`, headphone gain, pop-up typing progress.
Tests with a FAKE sounddevice installed before import (no real audio in tests). Real-device checks only silent (zero-amplitude); no audible playback without my yes.
Note: CUDA was blocked for scratch runs ("Application Control policy ... cublas64_12.dll"), so Kokoro ran on the CPU there; the repo/CSpace copy used the GPU before. Report which you used.

### 3b. Accuracy / robustness fixes
- B1: HUD-count claims must match the data (8B said "no unread emails" with 4 unread) -> code check, else a fixed "I don't have that reading right now" style line; also the open item "room talk with 'you'/'?' inside the 3 s open ear is answered" (look at my S2-10 rule in the handoff before touching).
- B2: more calm fixed-from-code lines for things he cannot do or cannot look up (e.g. "I can't look that up yet." for weather -> plain and useful), no robotic fallbacks left in the results (re-grep newest results for fixed lines).
- B10: stale-turn guard: when I interrupt or change my mind, a pending answer/action from the older turn is dropped and a late result is never spoken (audit `jarvis.py` turn state / `turnstate.py` first, smallest change).
- B11: log a line as "spoken" only after its audio actually finished playing (history/follow-ups stay honest; ties in with the Player).
- B3/B4/B8 (models: small tool-calling reread with qwen3:4b-instruct, qwen3 as busy-GPU fallback instead of llama3.2:3b after fixing its capability claims and curly quotes/em dashes, phi4-mini for `JarvisModelDeep`): only if time allows AND the fresh-bank evidence (command cases, both banks) beats the current setup. Models are already downloaded; no new downloads.
Out of scope without my approval: B5 routines, B6 reranker (new dependency), B7 vision (download), B9 hearing clips (needs my recordings).

## 4. How to work
- Start with a short plan per slice (goal, scope, non-goals, acceptance, validation, risks, rollback). Slices: P0 persona cases+baseline -> V S0 -> V S1 -> V S2 -> B1/B2 -> B10/B11 -> persona edits -> V S3 -> optional models. Re-run tests after each slice.
- Test commands (always on a scratch copy that mirrors the repo depth: `<scratch>/Skins/Spaceship/@Resources/...` plus `<scratch>/contract`, `TZ=ABC+12`):
  `%LOCALAPPDATA%\SpaceshipHUD\venv\Scripts\python.exe test_jarvis.py`, `py -3 test_jarvis.py`, `...venv python test_host_pipe.py` (needs the contract fixture at four levels up).
  Done = "test_jarvis: OK" twice and test_host_pipe "failed: 0".
- Semi-live: `tools/semi_live.py --model llama3.1:8b --cases tools/semi_live_fresh.jsonl --seed 7 --out ...` (and main bank `semi_live_cases.jsonl`); score with
  `tools/score_semi_live.py --compare/--show/--worst`. Run one model at a time; `ollama stop <model>` after. Gate: cost not higher than baseline (8B main 43, fresh 32; 3B main 85, fresh 41), tripwires 0, first sentence p50 not worse than +0.15 s.
- Editing tip: Windows/Python heredocs ate backslashes in regexes once; use the Edit tool for regex lines.
- Keep a short log entry at the top of `tasks/HANDOFF-jarvis-semi-live.md` (section 6) after each slice: what changed, numbers, tests.
- Commit only when I say so, JARVIS files + tools + docs only; never stage Settings.inc, Data\, logs, weights, voice clips, results.

## 5. Final report (under 15 lines)
What changed per slice, the exact commands run and results, before/after numbers (cost, voice seam ms, first-audio p50), what was skipped or unverified,
the A/B WAV paths for me to listen to, rollback (`JarvisVoiceSmooth=0` or `git checkout` of the touched files).
