# Phase 6 to-do (revised 2026-10-14; details and acceptance criteria in tasks/plan.md "Task breakdown")

Gates for every task:
- test_jarvis OK under py -3 and the venv (`TZ=ABC+12`, run on a scratch copy).
- `check_route.py` shows no new differences.
- Commit only on the user's word. Copy to live only on the user's word.
- Live tests: ALL at the end of Phase 6 (the user, 2026-10-14). Checkpoints A and B are commit points only.
- NOTE: live jarvis.py = commit 301c22f (Phase 3 + 4). It does not have wake word training, Phase 5, S1, M1 or the meaning match.

- [ ] S1 (6a) `context(text, kind)` blocks by keyword; profile ≤500 characters for "me" questions; sensor lines only for PC; Pending line alone for time questions; "Answer only what was asked" line — BUILT and committed (with the plan update), tests OK, awaiting live test
- [ ] M1 (6b) active window: last 2 exchanges, 120 s, linked by keyword or follow-up start; "new topic" files it ("never mind" doesn't) — BUILT, tests OK, NOT committed, awaiting the user's word
- [ ] Meaning match (6a strict 0.6, M1/M2/M4a 0.35, words fallback) — BUILT, tests OK, NOT committed, awaiting the user's word
- [ ] T1 M1b last results: "the second one" / "it" resolved by code against the last reminder list or app, 120 s, normal confirmation, else "Which one?" — BUILT, tests OK, NOT committed
- [ ] T2 M2a topics: file into `jarvis_topics.json` and recall (top 2, score floor), digits masked, `JarvisRecall` on|off — BUILT, tests OK, NOT committed
- [ ] T3 M2b topics by voice: "forget what we said about X" (read back, yes), "what do you remember about X" (by code) — BUILT, tests OK, NOT committed
- [x] **Checkpoint A:** committed a74b235 (live checks for the end: two topics, come back, unrelated gets nothing, "cancel the second one")
- [x] T4 M4a-1 only matching facts in the prompt (`related()`, 5 at most) — committed c33d37f, awaiting live test
- [x] T5 M4a-2 save phrases, Replace?, forget read-back, "what do you know about X" by code — committed c33d37f, awaiting live test (no yes to Replace keeps both)
- [x] T6 M4a-3 offer to remember (`JarvisLearn` ask|off), never digit strings — committed c33d37f, awaiting live test ("remember ..." wordings save at once)
- [x] (committed c33d37f, awaiting live test) T7 M4b last 20 actions really run, in the prompt only for questions about him
- [x] (committed c33d37f; model down counts no try) T8 M3a daily idle compaction into checked facts (`jarvis_gist.txt`), model down keeps the topic
- [x] (committed c33d37f) T9 M3b monthly re-compaction over 200 gist lines
- [ ] ~~T10 6e~~ MOVED to Phase 10 (2026-10-14: everything about the voice)
- [x] **Checkpoint B:** committed c33d37f (live checks for the end: facts, "what did you do", one compaction by hand)
- [ ] T11 6j route + timing log: one line per turn (path, total seconds, no words) — BUILT, tests OK, NOT committed (awaiting the user's word)
- [ ] **End of Phase 6:** live copy + the full live test (everything since 301c22f), the user pastes the log lines — use "PHASE 6 LIVE TEST CHECKLIST" in JARVIS-Repair-Plan.txt
- [ ] T12–14 6i / 6f measure on the live run → report → fix only on approval
- [ ] (Phase 10, parked) 6c tone + 6h honesty + 6e style rules: personality design, not output cuts
- [ ] (Phase 10, parked) voice: 6e speech-safe rules + `speakable()` cleaner, 6g smoother voice (measure from 6j lines first); on the user's word
  - [ ] FIRST: tell the user the personality review is due; show everything the model gets about its personality; the user hand-customizes it and gives feedback. Nothing else in Phase 10 until then.
