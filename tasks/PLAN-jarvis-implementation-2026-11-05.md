# Implementation plan (2026-11-05, after your go-ahead)

Your instructions: solve findings 1-8, plan and take in the recommended OpenJarvis parts, keep idioms out of the crisis line unless that is hard or dangerous,
save "miss capture" (A-08, storing words) for later but stop him saying "sorry, what did you say?" unless the audio is genuinely garbled, **do not run GPU/CPU-heavy tests, only make sure it builds**.
Verification therefore = `py_compile` of every touched file + short sandboxed probes (no model, no GPU, seconds). The multi-minute gate and the model runs are NOT run here (see "Verification").
Nothing is committed (no commit without your yes). Each fix is small and listed with its rollback (`git checkout -- <file>`).

## Solutions for findings 1-8

| # | Finding | Solution | Files |
|---|---|---|---|
| 1 | Crisis line narrow / needs Ollama / switch / open ear / untested | (a) Widen `CRISIS` with reviewed phrases; **idioms stay out** ("kill myself laughing", "dying of laughter", "killing me" etc.) by removing idiom spans *before* matching (same technique as `TECH` in `serious_topic`); titles ("suicide squad", "suicide prevention month") excluded the same way. This is easy and safe, so it is built now. (b) `crisis()` no longer depends on `JarvisSeriousTopics` (that setting keeps controlling only the serious *mood*). The old test that pinned "switch off turns the line off" is changed. (c) `_hear`: when Ollama/model preflight fails the problem is still shown at once, but the turn keeps listening/reading the text and a crisis phrase still gets the fixed line. (d) `directed()`: a crisis phrase in the open ear is "yes". (e) New tests for the wiring. | `mood.py`, `jarvis.py`, `test_jarvis.py` |
| 2 | Negated command acted via AI reread | `ask_ai` refuses to re-read text that negates the command (`don't / do not / never / not` before the verb, "I said don't ..."). Rule routes were already safe. | `routing.py` |
| 3 | "Remember to ..." false promise, promise filter gaps | "remember to X" / "don't let me forget to X" with no time becomes a reminder request (he asks "When?"). `CANT_PROMISE` gains schedule / arrange / set up / add to your calendar / remind you, so a chat reply promising these is replaced by the existing can't-do line. | `routing.py` |
| 4 | "What did you just do?" -> claims line | Answered **from code** from the `did` list (like "what did you hear"); empty list -> "I haven't done anything yet." No model call. | `jarvis.py`, `turnstate.py` |
| 5 | `DANGER` inside words | Word boundaries on hack / brick / destroy / nuke; the two broad patterns (delete all, format) and the word list only count when the sentence is not a question or "tell me about / explain" opener. Real commands still guard. | `confirm.py`, `routing.py` |
| 6 | "No, make it 50" | `level_fix` accepts a leading no / nope / actually / I meant / sorry. Also: "30, no, 40" / "30, I mean 40" take the last number (F-16). | `jarvis.py`, `routing.py` |
| 7 | Trailing name | `route()` strips a trailing name after a comma, after "please", or after a unit/direction word. Never a bare name ("who is jarvis" is untouched). | `routing.py` |
| 8 | Hung turn | Watchdog uses its own `turn_started` (the alarm no longer disables it); after cancel it waits 30 s and, if the lock is still held, shows "A turn is stuck - restart JARVIS" once; a turn refused because busy writes `turn ignored: busy` to the log (no words). | `jarvis.py` |

## Miss handling ("sorry, what did you say?")
Sources found: (i) `hearing.missed_line` said "Pardon?" on the **first** empty transcript even for quiet noise; (ii) the model's own "Pardon sir, what did you say?" when Whisper's score was only mediocre (< -1.0);
(iii) `NEAR_MISS` "Could you say that again?" for command-looking sentences no rule parsed. Changes built now:
- (i) A quiet or short miss gets a short non-apologetic "Yes?" (then "I'm listening.", then the type box on the third); only loud speech that produced no words gets "Pardon?". Near-silence still points at the microphone.
- (ii) The "clear words never get Pardon" guard now covers anything Whisper scored above -1.7 or any text of 4+ words; real garbage (very low score, 1-3 odd words) may still be asked about.
- (iii) unchanged except that self-corrections are understood first (item 6) and the near-miss line fires only when a command verb and a thing are both present, as before.
- **A-08 (storing missed phrases to build test cases) is saved for later, not built.**

## Other fixes built in the same pass
F-09 typed confirmation (new fixed line, no more "Confirm with yes. Cancelled."), F-10 notes phrasing, F-11 "close the door", F-13 more plain yeses (list in code), F-14 HTTP error mapping and Ollama stream errors, F-15 exception text no longer logged (type name only), F-18 `inf` settings, Q-01 "make it N minutes" after a timer, Q-02 "too loud / too quiet / I can't hear you", Q-03 verbless brightness, Q-05 calendar writes -> existing can't-do line.
**Not built:** F-12 play/pause state (needs Windows media-session API and you at the PC), Q-04 (product choice), Q-06 (HUD side belongs to the UI session).

## OpenJarvis parts taken in
| ID | What | How it is built |
|---|---|---|
| A-01 | Gate in the repo + lint | `tools/gate.sh`, `tools/gate.cmd`, `ruff.toml` (pyflakes-class only) |
| A-02 | Self-check | `tools/doctor.py` (read-only, `--json`, concurrent probes, hint per failure) |
| A-03 | Untrusted note text | `jarvislib/untrusted.py` (small injection scanner) used on note snippets before they reach the prompt |
| A-04 | Error classes + one retry | HTTP mapping (F-14) + one retry before the first token in `chat_stream` |
| A-05 | Whisper compute ladder | CUDA `float16` -> CUDA `int8_float16` -> CPU `int8` (code only, logged; effect needs a live GPU check) |
| A-06 | Timing stats | `tools/log_stats.py` (p50/p95 per stage from `jarvis.log`) |
| A-09 | Sensitive files skipped by notes search/index | name filter in `notes.py` / `search.py` |
| A-11 | Settings check | `tools/settings_check.py` (validates `Settings.inc` against `config.py`) |
Deferred (need your decision or you at the PC): A-07 custom commands, A-08 miss capture, A-10 pre-computed brief, A-12 action audit, A-14 HUD ideas.

## Verification (no heavy runs)
1. `py_compile` on every touched file.
2. Short sandboxed probes (`review-2026-11-05/probe_*.py`, `verify_fixes.py`): seconds, one core, no model, no GPU, tripwires on.
3. **Not run on purpose:** `test_jarvis.py` (about 3 min of one core, twice), goldens, semi-live (GPU). The tests I changed/added are in `test_jarvis.py` and are syntax-checked only; the first full gate must be run by you (or on your word) and may need golden regeneration on purpose for the phrases listed in the report.

---
## STATUS at the end of the build pass (2026-11-05) - all uncommitted
**Built:** F-01 crisis (wider list, idioms/titles excluded, independent of the mood switch, works with Ollama down, never dropped by the ear windows), F-02, F-03 (+ promise filter), F-04 (`what did you do` from code), F-05, F-06, F-07, F-08 (watchdog, stuck notice, busy log), F-09, F-10, F-11, F-13, F-14 (+ one retry before the first piece, stream errors), F-15, F-16, F-18, Q-01, Q-02, Q-03, Q-05, miss handling (weak miss answers "Yes?"; Pardon guard -1.7 / 4+ words), A-01 (`tools/gate.sh`, `gate.cmd`, `ruff.toml`), A-02 (`tools/doctor.py`), A-03 + A-09 (`jarvislib/untrusted.py`, notes/search), A-04, A-05 (code only), A-06 (`tools/log_stats.py`), A-11 (`tools/settings_check.py`).
**Not built (deferred):** F-12, Q-04, Q-06, A-07, A-08, A-10, A-12, A-14.
**Checked (light):** `py_compile` on every touched file; `ruff --select F821,E9` clean; `tests/run_all.py` (11 files incl. the new `test_review_fixes.py`, 3.8 s, includes rule order, settings schema, fixed lines, reply policy); `tasks/review-2026-11-05/verify_fixes.py` (about 110 checks incl. whole typed turns with Ollama down) all passed; `doctor.py`, `settings_check.py`, `log_stats.py` run on the real files (read-only).
**Not run:** `test_jarvis.py`, golden routes/replies, semi-live, mutation, anything with the GPU. Expected golden diffs: negated phrases, trailing-name phrases, DANGER phrases (hack*/destroy*/nuke/blow up/delete all/format in questions), "remember to ...", "too loud/quiet", "make it N minutes", "what's in my notes", "close the <non-app>", calendar writes, "30, no, 40", crisis phrases; regenerate on purpose after inspecting each diff.
**Existing tests edited (unrun):** `test_jarvis.py` crisis section (the switch-off assertion now asserts the line stays on, idioms asserted not crisis) and the "remember to buy milk" route assertion.
