# Handoff: JARVIS review fixes (2026-11-05)

Read first: `CLAUDE.md`, `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md`. Branch `fix/sol-review`. **Everything is uncommitted** (11 modified, 9+ new files); nothing pushed.

## State
- Review + evidence: `tasks/REVIEW-jarvis-2026-11-05.md`. Bug plan: `PLAN-jarvis-fixes-2026-11-05.md`. OpenJarvis comparison/adoptions: `PLAN-jarvis-from-openjarvis-2026-11-05.md`. What was built and what was not: **`PLAN-jarvis-implementation-2026-11-05.md` (STATUS section at the end)**. Probes, mutation script, case bank, raw output: `tasks/review-2026-11-05/`.
- Built: crisis line (wider, idioms excluded, independent of the mood switch, works with Ollama down), negation guard, "remember to" -> reminder, "what did you do" from code, DANGER word boundaries, "no, make it 50", trailing name, watchdog/busy fixes, typed-confirm line, notes phrasing, "too loud", "make it N minutes", calendar can't-do, HTTP error mapping + one retry, log without exception text, miss handling, plus tools: `tools/gate.sh|cmd`, `doctor.py`, `log_stats.py`, `settings_check.py`, `ruff.toml`, `jarvislib/untrusted.py`.
- **Miss handling (latest decision from the user):** a weak/short miss must RESPOND, not stay silent: "Yes?", then "I'm listening.", then the type box; "Pardon?" only for loud speech that produced no words; the model's own "Pardon sir" is blocked unless Whisper's score < -1.7 and under 4 words (`hearing.missed_line`, `jarvis.py` pardon guard).

## NOT done / NOT run (the next session must do these)
1. **The full gate was never run on the edited code**: `bash Skins/Spaceship/@Resources/Jarvis/tools/gate.sh` (about 10 min of one core; user asked for no heavy runs). Expect `test_jarvis.py` possibly to need fixes: I edited two existing assertions (crisis section; `remember to buy milk` route) without running it.
2. Golden routes/replies will differ on purpose (negations, trailing names, DANGER phrases, "remember to", "too loud", "make it N minutes", notes phrasing, "close the <non-app>", calendar writes, "30, no, 40", crisis phrases). Inspect each diff, then regenerate deliberately.
3. Semi-live (GPU) re-run of `tasks/review-2026-11-05/rv_cases.jsonl` and mutation re-run (`mutate.py`) to confirm the new tests catch M05b/M06/M07/M09/M26/M27 (tests T-01..T-05, T-09, T-11 in the fixes plan are still to be written into `test_jarvis.py`; only pure-function checks exist in `tests/test_review_fixes.py`).
4. Live-only checks for the user: spoken confirmations, wake word, A-05 Whisper int8 fallback, real vault.
- Deferred by decision: F-12 play/pause state, Q-04, Q-06, A-07 custom commands, A-08 storing missed phrases, A-10, A-12, A-14 (HUD, belongs to the UI session).

## Quick checks that are cheap (seconds)
`tests/run_all.py` (11 files pass), `tasks/review-2026-11-05/verify_fixes.py <scratch mirror Jarvis dir>` (all pass), `py -3 -m py_compile` on touched files. Run only inside a scratch mirror with `TZ=ABC+12`; heredocs in this shell collapse backslashes (regexes got `\b` -> backspace once): write patch scripts with the Write tool, grep for 0x08 afterwards. Repo files are CRLF.

Rollback: `git checkout -- <file>` per file (new files: delete).
