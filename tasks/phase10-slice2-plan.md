# Phase 10 Slice 2 plan (pipeline changes). Repo only: nothing is copied to the live skin, nothing pushed.

Approved by the user 2026-10-17: "apply slice 2, finish the entire slice moving through each checkpoint ... Most things
should be conditional and shouldn't be fed into the AI unless necessary."

## Goal
Everything in JARVIS-Phase10-Personality-Questions.txt that needs a change in how a turn is routed, prompted or spoken,
without rebuilding anything (Slice 3 / Stage 2 stay unbuilt).

## Design rule: nothing rare is always-on
- The always-on prompt (persona.txt [system] + mood + SAFE) stays <= 1500 characters (test-enforced).
- Rare situations are ADDITIONS, chosen per turn by code from plain word lists (C7, no embedder) and added to the prompt
  only on the turn they apply: serious softener, apology, rudeness, homework, opinions/advice, repeated question,
  long answer, privacy, late night, talk-less. Text lives in code, overridable in persona.txt sections.
- Behaviour that code can do is done by code, not by prompt: "hope this helps" is stripped from the spoken answer,
  the serious-mood timer, class-time mood, mood commands, silent room talk, auto-remember, speakable numbers/apps.

## New / changed files
| File | Change |
|---|---|
| jarvislib/mood.py (new) | word lists, serious-topic state (C1/C5), class-time mood (B9), turn additions, hope-this-helps filter (E3), promise detector (D4), mood command parser (M2) |
| jarvislib/say.py (new) | speakable() (E5/E6) + pronunciation fixes from Jarvis/pronounce.txt (K9) |
| jarvislib/prompt.py | system_prompt takes the turn's mood + additions; privacy hides calendar/to-do detail in context() |
| jarvislib/routing.py | mood command route -> ("act","mood",...) ; "what do you know about me" |
| jarvislib/base.py | HUD_SETTINGS gets "mood" (value validated) |
| Scripts/jarvis.lua | HUD_OK gets mood (only the 4 known values) |
| jarvis.py | exchange(): hooks; room talk silent (setting JarvisRoomAsk=0 default); auto-remember (JarvisLearn=auto default) |
| jarvislib/speech.py, tts.py | speakable in the speak path; headphone volume; shorter pauses; voice speed (JarvisVoiceSpeed) |
| Scripts/control.lua | rows: NAME, VOICE SPEED, SERIOUS TOPICS, TALK LESS (<= 4 buttons per row) |
| Jarvis/persona.txt | optional addition sections (commented defaults) |
| test_jarvis.py, Jarvis/prompt_cases.txt, tools/run_prompt_cases.py | tests, 20-30 prompt cases (fake first; real model only with OK) |
| Docs, JARVIS-Repair-Plan.txt, memory | status |

## Non-goals
Temporary moods (M3), streaming voice (K6), voice training, speaker detection (I1), Hey Clover model; any live copy,
deploy or push; model downloads or real-model runs (need the user's OK); changing live setting values.

## Acceptance (whole slice)
- `py -3 -B test_jarvis.py` prints `test_jarvis: OK` after every checkpoint.
- A plain chat turn's prompt is byte-identical in size to Slice 1 (no additions), except a late-night hint at night.
- Each addition appears only for its trigger (test per trigger and a test that unrelated text adds nothing).
- Mood changes by voice go through the HUD whitelist, are confirmed once, and "undo" / "never mind" / "back to before" restores.
- No real OS call in tests (fakes first, dry-run grep of the test file for destructive calls).

## Validation
Test suite with fakes; prompt-case list through the fake LLM (checks the prompt a case would send); Lua reviewed by eye
(no Lua parser on this machine - flagged unverified); the real model and real ears wait for the single combined live test.

## Risks
- A 3B model may ignore an addition: mitigated by keeping each short and by doing the work in code where possible.
- Keyword lists miss wording or over-trigger (a false serious mood is silent by C6): lists are plain data, user adds more later.
- Defaults changed in code (room talk silent, auto-remember): both have a setting to restore the old behaviour.
- Lua edit unverifiable here.

## Rollback
One commit per checkpoint on fix/phase7-9-audit: `git revert <sha>` for a checkpoint, or reset the branch to 30d3a82
(Slice 1 end). Settings: JarvisRoomAsk=1, JarvisLearn=ask restore the old behaviour.

## Checkpoints
- A: mood.py core (serious topic, class time, additions, E3 filter) wired into the prompt.
- B: voice mood commands + undo, silent room talk, auto-remember, promises, what-do-you-know.
- C: speech: speakable, pronunciation, headphones, pauses, voice speed.
- D: privacy, Control Center rows, model comparison script, prompt cases, docs/status.
