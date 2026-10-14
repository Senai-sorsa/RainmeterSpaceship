# Phase 6 plan (revised 2026-10-14)

Spec: `JARVIS-Repair-Plan.txt` PHASE 6 (6b rewritten, 6c/6h moved to PHASE 10). Code: `Skins/Spaceship/@Resources/Jarvis/jarvis.py`, `test_jarvis.py`.

## 6a in detail

### S1. Only send what the question needs (6a, about 40 lines)
- **Change:**
  - `context(text, kind)` builds named blocks: time, calendar, mail, to-dos, PC, network, apps.
  - A small keyword table picks the blocks. Time is always in. `kind == "brief"` takes all blocks.
  - `system_prompt(text, kind)` passes them through. Every caller is updated (grep `system_prompt(`).
  - The profile goes in only for questions about the user ("my", "me", "I"), capped at 500 characters.
  - `sensors()` lines (the `hud` list) are added only when the PC block is picked. The thread still starts,
    so nothing gets slower.
  - One SYSTEM line: "Answer only what was asked. Do not mention the data below unless the question is about it."
- **Not in this slice:** memory filtering (S5). It keeps today's "all facts" until then.
- **Done when:**
  - "tell me a joke" → the prompt has the time block only.
  - "what's on tomorrow" → time and calendar.
  - "how hot is my GPU" → time and PC (with the sensor lines).
  - "brief me" → every block.
  - "what's my sister's name" → the profile, ≤500 characters.
- **Test:** call `system_prompt()` directly with the fake data files and check which block headers it contains.


## Context
The first Phase 6 plan (`tasks/plan.md`) had two problems for the user:
- **6b kept talk too briefly and dumbly.** It kept the last 2 exchanges for 2 minutes and then threw them
  away. The user wants older talk **kept as memory, sorted by topic**, and brought back **only when the
  question is about that topic**, so it never leaks into an unrelated conversation.
- **6h cut sentences out of the model's answers**, which would make him sound odd. The user wants honesty
  handled by **personality** work in a later phase.
- **6c (tone)** is personality too, so it moves out with 6h.

The answers given on 2026-10-14:
- **Topic memory:** 7 days and at most 100 topics. It is stored **by topic, not by conversation**.
- **Old topics:** they are **compacted into tiny facts**, not deleted. Those facts don't expire. If needed,
  they are compacted again once a month.
- **Active memory:** the last 2 exchanges, kept for 2 minutes.
  - Cleared by "new topic", or by a question with no keyword link to the last one and no follow-up start.
  - **"Never mind" does NOT clear it.**
- **6c and 6h** move to a later personality phase.

## Phase 6 after the change
| Part | What | Status |
|---|---|---|
| 6a | Only send what the question needs (keyword blocks) | unchanged (S1 in tasks/plan.md) |
| **6b** | **One memory system: active → topics → compact facts, plus the user's facts and what he really did** | **new, replaces old 6b and 6d** |
| 6e | Wording for the ear + the `speakable()` cleaner | **all → PHASE 10** (2026-10-14: style rules = tone, the rest = voice) |
| 6g | Voice smoothness | **→ PHASE 10** (2026-10-14: everything about the voice) |
| 6f / 6i | Model compare, GPU spikes: measure first, each needs approval | unchanged |
| 6c, 6h | Tone, serious-topic switch, identity and honesty lines, self-claim check | **parked → new PHASE 10 PERSONALITY** |

The existing **1d action-claim check** ("I've set the alarm" when nothing ran) **stays**. That is a safety
rule from Phase 1, not personality. Only its 6h *widening* is parked.

## 6b. The memory design: four layers, one path

This draws on how other assistants do it:
- **MemGPT / Letta:** a small working context. Older talk is moved out and summarized, not deleted.
- **Generative Agents** (Park et al., 2023): what to recall is picked by relevance plus recency.
- **Mem0:** each new fact is either added, used to update an old one, or ignored, never blindly stacked.
  That is the "Replace …?" step.
- **ChatGPT memory:** two kinds. "Saved memories" are explicit facts you can list and delete. "Chat history"
  is referenced only when it is relevant.

These are the ideas only; their code isn't used. The whole thing runs locally on the files and the model
already in use.

```
 you speak ─> keywords(q)
              │
   L1 ACTIVE  │ last 2 exchanges, 2 min. Kept if q links to them (shared keyword or a follow-up start)
   (working)  │ else: "filed" into L2, and q starts fresh. "new topic" files it at once.
              ▼
   L2 TOPICS  │ Data\jarvis_topics.json. A topic = keywords + short exchanges + last_used.
   (episodic) │ Filed talk JOINS the best-matching topic (shared keywords) or starts a new one.
              │ Recalled only when q shares keywords with the topic; top 2, about 600 characters.
              ▼ after 7 days unused, or when over 100 topics (oldest first)
   L3 GIST    │ Data\jarvis_gist.txt. Tiny facts made from an old topic by the local model,
   (compact)  │ CHECKED by code (below). They never expire. Monthly: re-compacted only if over the cap.
              │
   L4 FACTS   │ Data\jarvis_memory.txt: what YOU told him (the old 6d). Word for word, never
   (yours)    │ rewritten by the model. Plus a short "what I actually did" list (deterministic).
```

### What goes into the prompt each turn (replaces "all facts" and `history[-8:]`)
- **Active:** the L1 messages, if they are still linked to the question.
- **"Facts the user told you. Use them exactly.":** L4 facts that share keywords with the question, at most 5.
- **"From earlier talks (only if it helps the question)":** at most 2 L2 topics plus the matching L3 gist
  lines.
- **"What you actually did recently":** only when the question is about him ("what did you do", "did you
  set", "what have you been doing", "why is the GPU busy"). See L4b.
- **Nothing matches → nothing is added.** That is the main fix for "brings up unrelated stuff".

### Parts (vertical slices; each has its own test and its own commit on the user's word)

**M1. The active window** (about 25 lines, in `turn()` and `fixed()`)
- `keywords(text)`: lowercase words, stop-words and filler removed, a trailing "s" cut off.
  - It is shared by L1, L2 and L4. 6a's block keywords stay a separate table.
- History rules:
  - `history[-4:]`.
  - `ACTIVE_TTL = 120` replaces both `600`s (~3022, ~3121).
  - The question is "linked" if it shares a keyword with the active window, or starts like a follow-up:
    it, that, this, he, she, they, and, but, so, what about, how about, why, then, also. A question of 3
    words or fewer also counts.
  - Unlinked, timed out, or "new topic" → `file_active()` (L2), then the window is emptied.
  - "new topic" gets the fixed reply "Okay." **"Never mind" is left as it is.**
- Briefing and notes turns neither send nor file the window.
- The FORGET pipe command (~3536) still empties it.

**M2. Topic memory** (about 60 lines)
- File:
  - `Data\jarvis_topics.json`, written as `.tmp` then `os.replace`, like `save_memory`.
  - Each topic: `{kw: [...], talk: [[when, you, him], ...], used}`.
  - Each line is capped at 200 characters, each topic keeps its last 6 exchanges, and there are at most 100
    topics.
- Filing (`file_active`):
  - Only **chat** exchanges are filed. Commands, briefings and fixed replies are not.
  - Words that look like a password, or runs of 6 or more digits, are replaced with "[number]" before
    saving.
  - Filed talk joins a topic it shares at least 2 keywords with, or 1 rare keyword (one that appears in only
    one topic). Otherwise it starts a new topic.
- Recall:
  - Score = shared keywords, weighted by how rare they are, plus a small bonus for recent use.
  - It must pass a floor, so one common word ("time", "day") never pulls a topic in.
  - The best 2 topics are recalled, and their `used` is updated.
- Setting: `JarvisRecall` = on | off. Off means only L1 and L4, as today.
- Voice:
  - "Forget what we said about X" reads back the matching topic names and waits for yes, the same pattern
    as 6d's forget.
  - "What do you remember about X" lists the topics and gist **by code**.

**M3. Compaction into tiny facts** (about 45 lines)
- **When:** once a day at an idle moment: the busy lock is free and it's not during a game or LITE. It
  compacts topics unused for 7 days, or the oldest topics while there are more than 100.
- **How:** one non-streaming call to the chat model with a JSON schema. This copies the existing
  `http_json(... "format": AI_SCHEMA ...)` call at ~638. The output is up to 3 short facts per topic, each
  under 120 characters.
- **The code checks every fact before saving it.** This keeps the old rule that the model can't put things
  into memory unchecked:
  - Every number, name (capitalised word) and content word must appear in that topic's saved talk.
  - Facts that fail are dropped.
  - If all of them fail, or the model can't be reached, the topic stays and is tried again tomorrow. Only
    after 3 failures is it removed without a gist, and that is logged with a count only.
- **Gist file:** `Data\jarvis_gist.txt`, one line per fact with its keywords and date. These lines never
  expire.
- **Monthly:** only if the gist file has more than 200 lines, the oldest gist lines that share a topic are
  re-compacted under the same check.
- **Your own facts (L4) are never compacted or reworded by the model.** You said facts shouldn't expire, and
  6d already decided they are used word for word.

**M4. Your facts and what he actually did** (the old 6d, about 45 lines, plus about 15 new lines)
- **4a:** the 6d list as already planned:
  - The wider save phrases.
  - Matching facts only, at most 5.
  - "What do you know about…" answered by code.
  - "Replace '…'?" when a new fact contradicts an old one.
  - Forget reads back and waits for yes.
  - He offers "Want me to remember that?" (`JarvisLearn` = ask | off). Only a yes saves.
  - Limits stay: 50 facts, 200 characters each.
- **4b (honesty through memory, not by cutting sentences):**
  - Code keeps a small in-memory list of what it really ran: the last 20 actions, each with the time, what
    it was, and whether it worked.
  - It is fed from the places that already confirm actions (`can_undo` and the act and remind paths). Which
    hook covers every action gets checked while building.
  - When the question is about him, the list goes into the prompt. If it's empty: "You ran nothing in this
    session."
  - Questions like "what were you doing" get answered from facts, and nothing is cut out of his answer.

### Order and checkpoints
- S1 (6a) → M1 → M2 → **Checkpoint A**:
  - test_jarvis passes, `check_route.py` shows nothing new, commit on your word, copy to live on your word.
  - Live test: talk about two topics, come back to the first one later; check that an unrelated question
    gets no old talk.
- M4a → M4b → M3 → **Checkpoint B**:
  - The same gates.
  - Live test: facts, "what did you do", and compaction run once by hand with a short test age.
- 6f and 6i: measure, report, then a fix only on your approval. (6g is in Phase 10.)

## Phase 10: Personality and voice (parked, not built now)
This is a new section in JARVIS-Repair-Plan.txt. It holds:
- **6c in full:** the natural default tone, a NATURAL button in Control Center, the serious-topic switch,
  and the identity line.
- **6h:** the honesty line, the serious-topic list extension, and the self-claim widening, recorded as
  "rejected as output cuts; solve by personality design instead".

Two ideas to look at when that phase starts:
- A persona card: a few example answers that show the voice.
- A per-mood honesty rule that is part of the persona rather than a filter.

Also moved here (the user, 2026-10-14: anything about tone not finished): 6e's style rules (contractions,
1–2 short sentences, never "as an AI", acknowledgements).

Also moved here (the user, 2026-10-14: everything about the voice): the rest of 6e (speech-safe rules and the
`speakable()` cleaner, was Task 10) and all of 6g (smoother voice, was in Tasks 12–14). The voice part does
not wait for the personality review; it still starts only on the user's word.

**Gate: the user's review first.** Before any Phase 10 code, gather everything the model gets about its
personality (SYSTEM text, MOODS, identity line, style rules, persona card draft, how the ABOUT THE USER note
is used), tell the user the review is due, and show it in one place. The user customizes it by hand and gives
feedback. No Phase 10 work goes ahead until that feedback is in.

Issues 3 and 28 stay open and point to Phase 10. Phase 6's M4b (what he really did) already gives him the
true facts to work from.

## Files
- `Skins/Spaceship/@Resources/Jarvis/jarvis.py`:
  - `context()` and `system_prompt()` (233, 404).
  - The history code in `turn()` and `fixed()` (~2950–3150).
  - The memory code (~2173).
  - Reuse: `save_memory`'s atomic write, `http_json` with `format` (~638), `can_undo`, `log`, `setting`,
    `strip_name`.
- `test_jarvis.py`: new tests next to the memory tests. They use the fake clock (`_Clock`) and a fake model
  for compaction.
- `JARVIS-Repair-Plan.txt` (LF):
  - Rewrite 6b and fold 6d into it.
  - Move 6c and 6h to PHASE 10.
  - Add a STATUS line.
- `tasks/plan.md` and `tasks/todo.md` are rewritten to match.
- **No `control.lua` change in Phase 6** (the NATURAL button moves to Phase 10).

## Verification
- **Unit tests** (fake clock, temporary Data files, fake model):
  - Linked and unlinked questions; "never mind" keeps the window; "new topic" files it.
  - A question 3 minutes later gets no active window.
  - Filing merges into the right topic.
  - An unrelated question recalls nothing; a related one recalls the right topic.
  - The 101st topic triggers compaction.
  - The checker drops a fact with a number or name not in the talk.
  - Model down → the topic is kept.
  - Digit runs are stored as "[number]".
  - `JarvisRecall=off` leaves only L1 and L4.
  - An action-list question gets the real list; an empty list gives "You ran nothing".
- **Commands:**
  - `TZ=ABC+12 py -3 -I test_jarvis.py` and the venv run, both on the scratch copy. I expect "OK" and exit 0.
  - `check_route.py` on the 65 phrases, expecting no new differences.
  - `check_voice` after 6e (Phase 10).
- **Live scripts** at each checkpoint. You paste the log lines; I never read `Data\`.

## Risks
- **Matching is words OR meaning** (`related()`, all-MiniLM-L6-v2 on the CPU; 6a cut-off 0.6, talk 0.35).
  The cut-offs come from a small sample; words only until the model loads (~3 s) or without ChromaDB.
- **Compaction can lose detail.** The checker stops invented details, not lost ones. It runs on the GPU once
  a day while idle.
- **Conversation text is stored on disk** in `Data\` (ignored by git). `JarvisRecall=off` turns this off, and
  digit runs are masked.
- **It is bigger than the old 6b+6d:** about 190 lines instead of about 45. Each slice can be reverted on its
  own.

## Rollback
- Each slice is its own commit, so `git revert` works on any one of them.
- After going live: restore the robocopy backup.
- `JarvisRecall=off` turns off topic memory without a code change. The data files can be deleted by you.

## After approval
1. Rewrite `tasks/plan.md`, `tasks/todo.md` and the Phase 6/10 text in `JARVIS-Repair-Plan.txt`. DONE.
2. Build S1 first, then stop for your test. DONE (S1 committed in 1036282).
3. No commit without your word.

---

# Task breakdown: the rest of Phase 6 (added 2026-10-14, after M1 and the meaning match)

## Where things stand
- **Committed:** S1 (6a), in 1036282.
- **Built, not committed:** M1 (the active window) and the meaning match (words OR meaning; 6a 0.6, talk 0.35).
- **Live is not the repo.** The live `jarvis.py` is byte-for-byte commit 301c22f (Phase 3 + 4). It does not
  have 123d829 (wake word training), 23b290c (Phase 5 alarms), S1, M1 or the meaning match. A live test only
  tests what was copied. Live and the repo can also differ in `Settings.inc` and the venv's packages.

## Dependency graph
```
keywords() / related() / meaning()   (built with M1 + the meaning match)
  ├── M1 active window (built) ── NEW_TOPIC, ACTIVE_TTL, file_active()
  │     ├── M1b last results          (uses ACTIVE_TTL and NEW_TOPIC; the reminder list + app paths)
  │     └── M2a topics: file + recall (file_active() starts writing to jarvis_topics.json)
  │           ├── M2b voice: forget / what do you remember about X
  │           └── M3 compaction        (reads topics; http_json + schema; writes jarvis_gist.txt)
  ├── M4a-1 matching facts only        (related() on jarvis_memory.txt; does not need M2)
  │     └── M4a-2 save / replace / forget / "what do you know" ── M4a-3 offer to remember
  └── (none) M4b action list ── run_action() / can_undo() / the remind paths
6j route + timing log         independent; must come before 6f / 6i (and 6g in Phase 10)
6i, 6f                        measure → report → fix only on approval
(6e, 6g → Phase 10)
```
Order: what fails fast first (the live gap), then the memory core (M1b, M2), then facts. M4b and 6j are
small and independent, so they can move earlier if a live test needs them.

## Gates for every task (not repeated below)
- Copy `jarvis.py` and `test_jarvis.py` to the scratch `run\Jarvis\`, then run
  `TZ=ABC+12 py -3 -I test_jarvis.py` and the same with the venv Python. Both must print "test_jarvis: OK"
  and exit 0.
- `py -3 -I check_route.py <old> <new>`: no new differences beyond the N14 time-stamp line.
- A STATUS line in `JARVIS-Repair-Plan.txt` (LF) and the box in `tasks/todo.md`.
- No commit and no live copy without the user's word. Claude never reads `Data\`.
- Tests use fakes (fake clock, a fake `_embed[0]`, a fake `http_json`) and never load the real model.

## Tasks

### Live tests: all at the end of Phase 6 (the user, 2026-10-14)
- No live copy or live test between tasks. Checkpoints A and B are commit points only (on the user's word).
- After T11 (6j): one live copy and one full live test of everything since 301c22f (wake word training,
  Phase 5, S1, M1, meaning, M1b-M4b, M3), using "Your live test after Phase 6" plus the checkpoint lists
  below. The 6j route lines make a fault easier to place, which is why 6j moves before the live test.
- 6i / 6f measure on the live run, after that test.

### Task 1: M1b, the last results (S: jarvis.py, test_jarvis.py; about 30 lines)
- **Description:** "Cancel the second one" and "cancel it" work against the list or target he just read out.
  Code resolves the item, never the model.
- **Acceptance:**
  - "What alarms do I have" then "cancel the second one" cancels that alarm after the usual confirmation.
  - "The fourth one" with 3 items, no list, or a list older than 120 s → the fixed line "Which one?".
  - "New topic" clears it. Nothing is stored on disk, and only the kind and the count are logged.
- **Verification:** tests for each case above, plus "a joke after a list gets no list in the prompt". The gates.
- **Depends on:** M1.
- **Files:** `jarvis.py` (the schedule list ~2666, `run_action` ~1994, the open / close app path, `route()`),
  `test_jarvis.py`.
- **Scope:** only kinds that already have a command: reminders, alarms and timers, and open / close app.
  Calendar and to-do items are listed but have no "cancel" command, so they are left out.

### Task 2: M2a, topic memory: filing and recall (M: jarvis.py, test_jarvis.py; about 45 lines)
- **Description:** talk that leaves the active window is filed by topic in `Data\jarvis_topics.json`, and
  comes back only when a new question is about that topic.
- **Acceptance:**
  - Filing: chat exchanges only; digit runs of 6+ → "[number]"; it joins the topic with 2 shared keywords
    or 1 rare one, otherwise it starts a new topic. Limits: 200 characters a line, 6 exchanges a topic,
    100 topics. Atomic write (.tmp, then `os.replace`).
  - Recall: score = rare-weighted shared keywords + meaning + a small recency bonus, above a floor. The best
    2 are recalled, about 600 characters, and their `used` is updated. An unrelated question gets nothing.
  - `JarvisRecall=off` → no file is written and nothing is recalled.
- **Verification:** tests for filing into the right topic, unrelated → nothing, related → the right topic,
  masking, recall off. Plus the gates.
- **Depends on:** M1 (`file_active()`).
- **Files:** `jarvis.py` (`file_active` ~3001, the chat path in `turn()`, the `setting` defaults),
  `test_jarvis.py`, and `Settings.inc` only if the defaults live there (check while building).

### Task 3: M2b, topic memory by voice (S: jarvis.py, test_jarvis.py; about 20 lines)
- **Acceptance:**
  - "Forget what we said about X" reads back the matching topics and deletes only after a yes.
  - "What do you remember about X" lists the topics (and, after M3, the gist) by code, not by the model.
- **Verification:** tests for read-back, then yes / no; a list with no matches; the new phrases in the
  route check. The gates.
- **Depends on:** M2a.

### Checkpoint A: commit on the user's word (live checks saved for the end of Phase 6)
- Talk about two topics, wait, come back to the first: it is recalled.
- An unrelated question gets no old talk.
- "Cancel the second one" after a list works.

### Task 4: M4a-1, only matching facts in the prompt (S; about 15 lines)
- **Description:** today every saved fact (up to 50) goes into every prompt. This is the main remaining
  cause of issue 5.
- **Acceptance:** facts are picked by `related()`, 5 at most, word for word under "Facts the user told you.
  Use them exactly." A joke gets none. "When is my dentist" gets the dentist fact only.
- **Verification:** tests for those cases. The gates.
- **Depends on:** `related()` (built). Not M2.

### Task 5: M4a-2, save, replace, forget, "what do you know" (S–M; about 25 lines)
- **Acceptance:**
  - New save phrases: remember / note / don't forget / keep in mind that.
  - A contradicting fact → "Replace '…'?"; it changes only after a yes.
  - Forget reads back and waits for yes.
  - "What do you know about X" is answered by code.
  - Limits stay: 50 facts, 200 characters.
- **Verification:** tests per phrase and per confirmation; the route check with the new phrases added
  (they must not steal current routes). The gates.
- **Depends on:** Task 4. **Files:** `jarvis.py` (memory code ~2274, `route()` ~1886), `test_jarvis.py`.

### Task 6: M4a-3, offer to remember (XS–S; about 10 lines)
- **Acceptance:** "my sister's name is Ana" → one offer, "Want me to remember that?"; it saves only after
  yes. A digit string is never offered. `JarvisLearn=off` → no offers.
- **Depends on:** Task 5.

### Task 7: M4b, what he actually did (S; about 15 lines)
- **Acceptance:**
  - An in-memory list of the last 20 actions really run (time, what, worked or not). It is fed from
    `run_action` / `can_undo` and the remind paths; while building, check that every action passes through
    one of them.
  - The list goes into the prompt only for questions about him. An empty list → "You ran nothing in this
    session."
  - A joke gets no list.
- **Verification:** tests for each. The gates.
- **Depends on:** none.

### Task 8: M3a, daily compaction into checked facts (M; about 35 lines)
- **Acceptance:**
  - Runs once a day when idle (the busy lock is free, not in a game or LITE). It compacts topics unused for
    7 days, or the oldest while there are more than 100.
  - One `http_json` call with a JSON schema returns up to 3 facts, each under 120 characters.
  - Code check: every number, name and content word must be in the topic's saved talk, or the fact is
    dropped.
  - All facts dropped or the model down → the topic is kept and tried again tomorrow. After 3 failures it
    is removed and logged as a count only.
- **Verification:** fake model and fake clock: the 101st topic triggers compaction; an invented name or
  number is dropped; model down keeps the topic. The gates.
- **Depends on:** M2a.

### Task 9: M3b, monthly re-compaction (XS–S; about 10 lines)
- **Acceptance:** only when `jarvis_gist.txt` has more than 200 lines, under the same check. L4 facts are
  never touched.
- **Depends on:** Task 8.

### Task 10: 6e, wording for the ear (S; about 15 lines)   MOVED to Phase 10 (2026-10-14, voice)
- **Acceptance:**
  - Prompt rules: no lists, headings or symbols; numbers, dates and times said the way they are spoken.
    (Contractions, 1–2 sentences, "as an AI" and acknowledgements moved to Phase 10: tone.)
  - A cleaner before `speak_all()` removes asterisks, bullets and "#", and turns "°C" and "%" into words.
  - The cleaner is named `speakable(text)`: `for_ear()` already exists (~2061) as the number formatter
    and is kept as it is.
- **Verification:** the cleaner's output has no symbols; `check_voice`. The gates.
- **Depends on:** none.

### Checkpoint B: commit on the user's word (live checks saved for the end of Phase 6)
- Facts in three wordings, then asked about the next day.
- "What did you do?"
- One compaction run by hand with a short test age.

### Task 11: 6j, route + timing log (XS; about 10 lines)
- **Acceptance:** one line per turn, "route: <kind> [<action>] via rule | ai-reread | model, total <s>s", with
  no words from the question.
- **Verification:** a fixed command, an action and a chat turn each log one line with the right path.
- **Depends on:** none. Must come before the end-of-phase live test and Tasks 12–14.

### Tasks 12–14: 6i GPU spikes, 6f model compare (measure only); 6g voice smoothness MOVED to Phase 10
- Each one: measure as its spec says (no install), report the numbers, and fix only on approval.
- 6f downloads a model only on approval.
- The user pastes the 6j lines; Claude does not read `Data\`.

## Risks (added for this breakdown)
| Risk | Impact | Mitigation |
|---|---|---|
| Live is many slices behind; one live test at the end | High: a live fault is harder to place | 6j route lines first; each slice is its own commit, so `git revert` / bisect |
| Recall brings unrelated talk back | High: the issue this phase fixes | A score floor, top 2, a test with unrelated questions, `JarvisRecall=off` |
| New voice phrases steal existing routes | Med | The route check on 65 phrases plus the new ones |
| The model's gist invents details | Med | The code check drops unknown names, numbers and words |
| Meaning cut-offs from a small sample | Med | Words still decide when the model is off; tune after live logs |
| Memory from the second model copy not measured | Low–Med | Measure at the end-of-phase live test (Task Manager) |

## Open questions
- Decided (spec as written): M1b covers only kinds with a command (reminders / alarms / timers, open / close
  app). Calendar / to-do look-ups can be added later if the live test asks for them.
