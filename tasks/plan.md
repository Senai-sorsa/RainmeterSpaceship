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
| 6e | Wording for the ear + `for_ear()` cleaner | unchanged |
| 6f / 6g / 6i | Model compare, voice smoothness, GPU spikes: measure first, each needs approval | unchanged |
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
- M4a → M4b → M3 → 6e → **Checkpoint B**:
  - The same gates.
  - Live test: facts, "what did you do", and compaction run once by hand with a short test age.
- 6f, 6g and 6i: measure, report, then a fix only on your approval.

## Phase 10: Personality (parked, not built now)
This is a new section in JARVIS-Repair-Plan.txt. It holds:
- **6c in full:** the natural default tone, a NATURAL button in Control Center, the serious-topic switch,
  and the identity line.
- **6h:** the honesty line, the serious-topic list extension, and the self-claim widening, recorded as
  "rejected as output cuts; solve by personality design instead".

Two ideas to look at when that phase starts:
- A persona card: a few example answers that show the voice.
- A per-mood honesty rule that is part of the persona rather than a filter.

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
  - `check_voice` after 6e.
- **Live scripts** at each checkpoint. You paste the log lines; I never read `Data\`.

## Risks
- **Keyword matching misses** synonyms ("dentist" vs "teeth"). A miss means no recall, never a wrong one.
  - shortcut: keywords, not embeddings. If misses matter, reuse the existing Chroma setup (`_chroma`, ~2768).
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
1. Rewrite `tasks/plan.md`, `tasks/todo.md` and the Phase 6/10 text in `JARVIS-Repair-Plan.txt`.
2. Build S1 first, then stop for your test.
3. No commit without your word.
