# Phase 10, Slice 1 plan: easy changes (persona text, four moods, name, blended voice)

Spec: `JARVIS-Phase10-Personality-Questions.txt` (answers, 2026-10-16/17) and PHASE 10 in `JARVIS-Repair-Plan.txt` (~line 3707).
Status: PLAN ONLY, not approved, no code changed. Slices 2 and 3 are listed at the end, not planned here.
Rules in force: `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md` (fakes first, no real destructive calls), no live test until the combined end test, commit by file name, no deploy without the user's word.

## Overview
Give him the personality the user described, using only text and small settings changes. No new pipeline: no per-turn state, no new voice commands, no new threads. The model is told who he is, how to be honest, and which of four moods to use.

## What exists today (read from the code, 2026-10-17)
- `jarvislib/prompt.py`: `SYSTEM` (already says "You are CLOVER", already wraps data in `<<hud-data>>`), `MOODS` (proper / playful / brief), `system_prompt()` picks the mood from `JarvisPersonality` (default playful).
- `control.lua:587-598`: PERSONALITY row with 3 buttons. `control.lua:579`: voice row cycles `KV = bm_lewis, bf_emma, am_michael, af_heart`.
- `jarvislib/tts.py:_kokoro()`: reads `JarvisKokoroVoice`, passes the name to `eng.create(voice=name)`.
- `jarvis.py:~668`: `COURTESY` fixed replies ("You're welcome.", "Hello{name}.").
- `test_jarvis.py` (run: `py -3 -B test_jarvis.py`): lines 1394, 1487-1491 pin the SYSTEM text and the three moods; lines 2597-2606 pin the courtesy replies.
- `JarvisName` does not exist yet. `JarvisCallMe=Senai` in the live Settings.inc.

## Dependency graph
```
T1 persona.txt loader + fallback
 ├─ T2 SYSTEM text (identity, honesty, style, user answers)
 └─ T3 four moods (mirror/serious/brief/playful) ──> T4 Control Center 4 buttons
T5 JarvisName setting (uses T2's text)
T6 "You're welcome, sir." (independent)
T7 blended "default" voice (independent, tts.py + control.lua voice row)
T8 doc/memory update (last)
```

## Architecture decisions
- **Text lives in `Jarvis\persona.txt`** (user's choice, L4). Sections `[system]`, `[mirror]`, `[serious]`, `[brief]`, `[playful]`. If the file is missing, unreadable or lacks a section, the built-in text in `prompt.py` is used and one line is logged. So a bad edit can never silence him.
- **No persona card, no few-shot examples** (L1, L5). Rules only.
- **Old setting values keep working:** `proper` -> serious, `natural` -> mirror, unknown -> mirror. The live `playful` value is NOT changed (the plan rule: live values are never changed silently).
- **Fixed code replies stay as they are** (section F), except the one "You're welcome" change (I3).
- **The serious-topic switch is Slice 2.** In Slice 1 `serious` is only a mood you pick with the button.

## Tasks

### Task 1: persona.txt loader with fallback (S)
**Description:** `prompt.py` reads `Jarvis\persona.txt` once per call (cheap, file is small; mtime-cached), splits it by `[section]`, and falls back per section to the built-in text.
**Acceptance:**
- [ ] File present and valid: its text is used.
- [ ] File missing / unreadable / section missing: built-in text used, one log line, no crash.
- [ ] Only plain text is read; nothing in the file is executed or used as a path.
**Verification:** new asserts in `test_jarvis.py` (temp file, fake `setting`/`log`). `py -3 -B test_jarvis.py` all pass.
**Dependencies:** None. **Files:** `jarvislib/prompt.py`, `test_jarvis.py`, new `Jarvis/persona.txt`. **Scope:** Small.

### Task 2: new SYSTEM text (M)
**Description:** Write the `[system]` section from the user's answers. Contents (each maps to an answer):
- Identity: his own thing, not the film character, runs locally on this PC, the user is his creator (A1, A2, A5, A6).
- Honesty: "Never state you completed a task or did something you did not do, and if you do not know something, say so." (D1). Cannot see something: say so plainly, no joke (D2).
- Cannot do something: plain reply, no sarcasm, may offer an alternative; obviously fake commands may be joked about (D3).
- Unclear or mis-heard input: say "Pardon sir, what did you say?" and never guess a meaning (D5, evidence a, e).
- Questions: one at a time, no speculative multiple choice (D7, evidence d).
- Opinions allowed, logical, with the reason; medical/legal/money advice with no disclaimer (D8).
- Admit mistakes: start with "I apologize, sir..." then state the mistake (D10).
- Never pretend to be human, no swearing, no slang, not too rude, no insulting the user or family (A8, B6, B7). May tease and disagree (B6).
- Insulted: joke with a mild comeback, never say he is hurt (I2). Silly or repeated asks: tease (I4). Confirmations: neutral (I5).
- Thanks: handled by code (Task 6), not here.
- Homework: gives answers and explains, may tease (J1). No topic is refused beyond the code's hard limits (J2).
- Does not hallucinate things the user said or did (M6); does not mention errors unprompted (I6).
- Facts, ABOUT ME, and past talk only when relevant to the question (H1, H2, H4); "what do you know about me" lists them in a normal voice (H5).
- Fahrenheit and American units; app names simplified ("Chrome"); English only; numbers said as people say them (E5, E6, E7).
- Address: "sir" in about 4 of 5 replies, "Mr. Sorsa" mainly on serious topics, never the first name (A3, E8).
- Only banned phrase: "hope this helps" (E3). Length: see open question Q3.
- Late night: add a "Now:" hint when the clock is between midnight and 5 am so he can say "staying up, I see" (G2). One line in `context()`.
- Soft speech note for headphone/speaker is Slice 2 (needs the output device).
**Acceptance:**
- [ ] Every bullet above is present in the text, or listed as deferred.
- [ ] The prompt still contains the `<<hud-data>>` rule and the "Never say you set or changed something" rule (INV: claim guard unchanged).
- [ ] Prompt kept MINIMAL (user, 2026-10-17): measure today's SYSTEM + mood size first; the new [system] + active mood stays within ~1.5x of it, enforced by a test that fails if it grows past the cap. One clause per rule, overlapping rules merged. Only the active mood is ever sent.
- [ ] Rules for rare situations (insults, homework, opinions, serious topics) are NOT in the always-on text; they wait for the Slice 2 per-turn triggers. Slice 1 keeps only rules that matter every turn.
- [ ] Stable text stays at the start of the prompt (cache-friendly); HUD data stays last.
**Verification:** asserts on key phrases in `system_prompt()`; pytest-style run as above. User reads the printed final text before it counts as done (the "review first" rule).
**Dependencies:** T1. **Files:** `persona.txt`, `prompt.py`, `test_jarvis.py`. **Scope:** Medium (mostly text).

### Task 3: four moods (S)
**Description:** `[mirror]`, `[serious]`, `[brief]`, `[playful]` sections.
- mirror (default): "Sound like a calm, friendly person. Joke only if the user jokes first; match their tone." (B1, A7)
- serious: calm, precise, never jokes, acknowledges then recommends something helpful (C2). The softener wording is added by the switch in Slice 2.
- brief: one short sentence, rarely jokes (B5).
- playful: jokes constantly, mainly dark humor or witty banter, helps first on real questions, never jokes about a failed action (B4, B5).
- `system_prompt()` maps old/unknown values as in the decisions above; code default becomes mirror.
**Acceptance:**
- [ ] `mirror/serious/brief/playful` each give a different mood sentence; `proper` gives serious, `natural` gives mirror, nonsense gives mirror.
- [ ] The failed-action joke ban survives in playful.
**Verification:** update `test_jarvis.py` lines ~1487-1491 (they currently expect proper/playful/brief and playful for nonsense).
**Dependencies:** T1. **Files:** `persona.txt`, `prompt.py`, `test_jarvis.py`. **Scope:** Small.

### Task 4: Control Center PERSONALITY row, 4 buttons (S)
**Description:** `control.lua:587-598`: buttons MIRROR, SERIOUS, BRIEF, PLAYFUL; the current-mood normalisation accepts old values. Row count unchanged (INV-6, max 4 buttons).
**Acceptance:**
- [ ] Four buttons, the active one highlighted, including when Settings.inc still says `playful` or `proper`.
- [ ] No other row moves; no layout change.
**Verification:** read the Lua diff; check the skin's layout-count invariant script if one exists (`tools/check`). The real click is part of the end live test. Not run live now.
**Dependencies:** T3. **Files:** `Scripts/control.lua`. **Scope:** Small.

### Task 5: JarvisName setting (S)
**Description:** `{name}` placeholder in `[system]`, filled from `JarvisName` (default "Clover"). Do not touch the wake word; the existing `wake_name()` rule stays.
**Acceptance:**
- [ ] Setting empty or missing gives "Clover".
- [ ] A renamed value appears in the identity line; if it differs from `wake_name()`, the prompt tells him the wake word is still "Hey <wake name>" (plan A4).
**Verification:** asserts with fake `setting`.
**Dependencies:** T2. **Files:** `prompt.py`, `persona.txt`, `test_jarvis.py`; add the key to `settings-add.txt` only. **Scope:** Small.
**Note:** Settings.inc is skip-worktree and personal; I will NOT edit it. The code default covers a missing key.

### Task 6: "You're welcome, sir." (XS)
**Description:** Fixed thanks reply in `COURTESY` becomes "You're welcome, sir." (I3). Hello/Goodbye lines stay (F).
**Acceptance:**
- [ ] Thanks gives the new line, still no model call and no follow-up.
**Verification:** update `test_jarvis.py` lines 2597-2606.
**Dependencies:** None. **Files:** `jarvis.py`, `test_jarvis.py`. **Scope:** XS.

### Task 7: blended "default" voice (S)
**Description:** New voice name `default` = the mix of `bm_lewis` and `am_michael` style vectors (K1, K2, K3: blending only). In `_kokoro()`, if the name is `default`, build the voice array once (cached) with `eng.get_voice_style(...)` and pass it to `create`. If the installed kokoro-onnx cannot take an array, or either pack is missing, log once and fall back to `bm_lewis`. Add `default` to the voice row `KV` list in `control.lua`. The filler cache already re-renders when the voice setting changes.
**Acceptance:**
- [ ] `JarvisKokoroVoice=default` speaks (with the blend ratio constant 50/50 to start).
- [ ] Missing pack or unsupported API: falls back to `bm_lewis`, no silence.
- [ ] Existing four voices unchanged.
**Verification:** first, read the installed `kokoro_onnx` source to confirm `create()` accepts a vector (its type hint says `str`, so this must be confirmed, not assumed). Fake-engine test in `test_jarvis.py` for the name mapping and fallback. The sound itself is judged by the user at the end live test.
**Dependencies:** None. **Files:** `jarvislib/tts.py`, `Scripts/control.lua`, `test_jarvis.py`. **Scope:** Small.
**Risk:** the blend may sound odd; the ratio is one constant, easy to change.

### Task 8: records (XS)
**Description:** Update the PHASE 10 status in `JARVIS-Repair-Plan.txt` and the memory file; list Slices 2 and 3 in the plan so nothing is lost.
**Acceptance:** [ ] Plan says Slice 1 built, not live tested, not pushed. **Dependencies:** T1-T7.

## Checkpoints
- **After T1-T3:** `py -3 -B test_jarvis.py` passes in full. The user reads the printed final text (SYSTEM + four moods) and edits `persona.txt` by hand BEFORE T4-T7 go on. (This is the plan's "your review first".)
- **After T4-T7:** all tests pass; diff reviewed file by file; commit by file name, one commit per task group.
- **Final:** nothing is live tested or deployed; wait for the user.

## Risks and mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| Long SYSTEM text slows the small model or crowds context | Med | Measure growth in T2; keep rules short; first word must stay under 4 s at the end live test |
| A small model ignores many rules | Med | Slice 2 has the 20-30 prompt test list and model comparison |
| persona.txt edit breaks the prompt | Low | Per-section fallback to built-in text |
| Old `proper`/`playful` values mis-highlighted | Low | Normalisation tested |
| Blend API not supported | Low | Confirmed in T7 first; fallback to bm_lewis |
| "Never invent" rules conflict with "may promise" (D4) | Med | Promise recording is Slice 2; Slice 1 text says nothing about promising |

## Rollback
Each task is its own commit: `git revert <hash>`. Deleting `persona.txt` alone returns the built-in text. `JarvisKokoroVoice` back to `bm_lewis` undoes T7 at runtime.

## Open questions (need the user's word before the matching task)
1. **B7:** "no contradictions" read as NO contractions. Confirm? (The plan said contractions yes.) Affects T2.
2. **B11:** leave live `playful` as is (default in this plan), or move it to mirror?
3. **E1:** base answer length: 1, 1-2 or 1-3 sentences? Not answered. Affects T2, plus the long-answer trigger phrases in Slice 2.
4. **A3:** `JarvisCallMe=Senai` makes greetings say "Hello, Senai". Blank it (a live-file edit, needs your yes)?
5. **A6:** exact "who made you?" wording. This plan says "Senai Sorsa made me" unless told otherwise.
6. **E3 vs A8:** "as an AI" is not banned; "never pretend to be human" stands. OK?
7. **D6** (room talk silent) changes the existing "Are you talking to me, sir?" ask. Planned in Slice 2.

## Slices 2 and 3 (index only, from the user's answers)
- **Slice 2 (pipeline):** serious-topic word list + softener + 1-extra-turn return; class-time serious then restore; voice mood commands with undo; auto-remember facts (no ask); promises recorded to memory; room talk silent; long-answer triggers; privacy setting; softer speech on headphones; shorter pauses; `speakable()` + simple pronunciation fix; model comparison; 20-30 prompt test list.
- **Slice 3 (rebuild / Stage 2):** temporary moods; streaming speech and emotion; training a new voice; other-speaker detection; trained "Hey Clover" wake model if not done; anything heavy on tokens.
