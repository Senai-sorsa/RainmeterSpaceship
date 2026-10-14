# Phase 6 to-do (revised 2026-10-14; details in tasks/plan.md)

Gates for every task:
- test_jarvis OK under py -3 and the venv (`TZ=ABC+12`, run on a scratch copy).
- `check_route.py` shows no new differences.
- Commit only on the user's word. Copy to live only on the user's word.

- [ ] S1 (6a) `context(text, kind)` blocks by keyword; profile ≤500 characters for "me" questions; sensor lines only for PC; Pending line alone for time questions; "Answer only what was asked" line — BUILT and committed (with the plan update), tests OK, awaiting live test
- [ ] M1 (6b) active window: last 2 exchanges, 120 s, linked by keyword or follow-up start; "new topic" files it ("never mind" doesn't)
- [ ] M2 (6b) topic memory `jarvis_topics.json`: file by topic, recall only on a keyword match (top 2), `JarvisRecall` on|off, forget/list by voice
- [ ] **Checkpoint A:** commit, live copy, live test (two topics, come back, unrelated question gets nothing)
- [ ] M4a (6b, old 6d) your facts: save phrases, matching only (5 at most), Replace?, forget read-back, offer to remember (`JarvisLearn`)
- [ ] M4b (6b) what he really did: last 20 actions in the prompt for questions about him
- [ ] M3 (6b) compaction: topics older than 7 days or over 100 → checked tiny facts in `jarvis_gist.txt`; monthly re-compact over 200
- [ ] 6e ear rules + `for_ear()` cleaner
- [ ] **Checkpoint B:** commit, live copy, live test
- [ ] 6g / 6i / 6f measure → report → fix only on approval
- [ ] (Phase 10, parked) 6c tone + 6h honesty: personality design, not output cuts
