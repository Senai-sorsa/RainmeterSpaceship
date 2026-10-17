# Phase 10 Slice 1 todo (plan: tasks/phase10-slice1-plan.md; NOT approved yet)

- [x] T1 persona.txt loader with per-section fallback (prompt.py, test_jarvis.py, Jarvis/persona.txt)
- [x] T2 new SYSTEM text from the answers (persona.txt, prompt.py, tests)
- [x] T3 four moods mirror/serious/brief/playful; old values mapped (persona.txt, prompt.py, tests lines ~1487-1491)
- [x] CHECKPOINT A: full test run passes; user reads the printed text and hand-edits persona.txt
- [x] T4 Control Center PERSONALITY row, 4 buttons (control.lua)
- [x] T5 JarvisName (default in code; no settings file entry needed)
- [x] T6 "You're welcome, sir." (jarvis.py, tests lines ~2597-2606)
- [x] T7 blended "default" voice: confirm kokoro API first, then tts.py + control.lua KV (tests with a fake engine)
- [ ] CHECKPOINT B: all tests pass; diff reviewed; commit by file name
- [x] T8 update JARVIS-Repair-Plan.txt PHASE 10 status and the memory file

Open questions to answer first: contractions (B7), live playful (B11), answer length (E1), JarvisCallMe (A3), "who made you" wording (A6), "as an AI" (E3).
