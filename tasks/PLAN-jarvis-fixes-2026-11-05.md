# PLAN: JARVIS fixes found by the 2026-11-05 review

**Status: plan only. No JARVIS source file was changed in this review** (`git status` shows only new files under `tasks/`).
Evidence and reproductions: `tasks/REVIEW-jarvis-2026-11-05.md`, scripts and raw output in `tasks/review-2026-11-05/`.
Every fix below follows CLAUDE.md section 3 (goal, scope, non-goals, acceptance, validation, risk, rollback) and your review rule:
**class A** = plain bug fix with a test that fails before and passes after (I show you the diff before it goes live);
**class B** = changes what he says, a setting default or a timing, or adds behaviour: **needs your yes first**.

Run all checks only through the tripwire runner and the scratch-mirror gate (`tasks/review-2026-11-05/gate.sh`, `TZ=ABC+12`).
Order = severity, then cost. Each fix is its own commit so any one can be reverted alone.

## Summary table

| ID | Severity | Class | What | Where |
|---|---|---|---|---|
| F-01 | **High** (safety) | B | Crisis line is narrow, depends on Ollama/model, can be switched off, dropped in the open ear, and its wiring has no test | `mood.py:232-246`, `jarvis.py:927-933,1005,1269` |
| F-02 | Medium-high | A | Negated commands ("Please do not lower the volume") reach the AI reread and **lowered the volume** | `routing.py:36-37,60-66` |
| F-03 | Medium | B | "Remember to buy milk" -> "I'll remind you...", no reminder exists (false promise) | `routing.py:504`, `mood.py:219`, `routing.py:318-325` |
| F-04 | Medium | B | "What did you just do?" is answered with "I didn't catch that as a command" (claims filter eats the true answer) | `routing.py:328-345`, `turnstate.py:24-29` |
| F-05 | Medium | A | `DANGER` regex matches inside words: hackathon, Shackleton, destroyer, Brickell, "delete all my emails", "format my resume" -> guard route | `confirm.py:8-10`, `routing.py:413`, `jarvis.py:1243` |
| F-06 | Medium | A | Undo window accepts "No, make it 50" then cannot understand it | `followup.py:76-83`, `jarvis.py:743-758` |
| F-07 | Medium | A | Trailing name breaks a timer: "Set a timer for five minutes, Jarvis" -> "How long?" after 7 s | `routing.py:228-240,412` |
| F-08 | Medium | A (+B) | Hung turn: watchdog never frees the lock, an alarm ring disables the watchdog, a turn dropped while busy is silent, watchdog untested | `jarvis.py:529,672-679,1298-1299` |
| F-09 | Low-medium | B | Typed "Lock the computer" says "Confirm with yes. Cancelled." (dead end) | `jarvis.py:826-828` |
| F-10 | Low-medium | B | "What's in my notes about X" is not a notes search (model answers instead) | `routing.py:547` |
| F-11 | Low | B | "close the door" / "close the deal" -> "I don't see door open." | `routing.py:757-764` |
| F-12 | Low | B (+live) | "stop the music", "pause", "play", "resume" are one toggle key | `routing.py:745-746` |
| F-13 | Low | B | Plain yeses refused: "yeah sure", "sure thing", "go for it", "absolutely", "ok do it" -> "Cancelled." | `confirm.py:7-18` |
| F-14 | Low | A | Every `HTTPError` (404 model missing, 500 out of memory) is shown as "Lost the connection to Ollama" | `jarvis.py:1328-1330` |
| F-15 | Low | A | `log(f"...{e!r}")` can put spoken words in the log (e.g. `ValueError: invalid literal ... 'seven up'`) | `jarvis.py:155,1333` and 9 more |
| F-16 | Low | B | "Set the volume to 30, no, 40" and compound with a confirm action -> generic "Could you say that again?" | `routing.py:793-798` |
| F-18 | Low | A | `inf` / `-inf` in `JarvisContext`, `JarvisKeepAlive`, `PerfTier` raises `OverflowError` (only `ValueError` is caught) | `llm.py:13-18,85-89`, `jarvis.py:1352-1356` |
| F-17 | Docs | A | `LATER-2026-11-05.md` item 6 and some counts are slightly off | `tasks/LATER-2026-11-05.md` |
| T-01..T-09 | Tests | A | Coverage gaps and mutation survivors (see the end) | `test_jarvis.py`, `tests/` |

---

## F-01 Crisis line: coverage, independence, wiring test  (class B, safety)
**Confirmed evidence**
- `mood.crisis("my life is not worth living")`, `"I took too many pills"`, `"everyone would be better off without me"`, `"no reason to go on"`, `"I might just disappear forever"` -> **False** (probe_misc). With the 8B model the answers were: "I'm not a therapist, sir..." / "you didn't say anything about taking pills before. Are you feeling unwell?" / "A rather... bleak outlook, sir." (semi-live `rv-crisis1..3`).
- False positives: "what is suicide squad about" and "the movie suicide squad" -> crisis line (`suicid\w*`, `mood.py:232`).
- `crisis()` returns `on("JarvisSeriousTopics") and ...` (`mood.py:246`); `test_jarvis.py:4450` **pins** "SERIOUS TOPICS off turns the fixed line off too". So the switch-off is deliberate; it is still a safety trade-off you should decide on knowingly.
- With Ollama down or no model installed the turn ends in `_hear` (`jarvis.py:927-933`) before the crisis check (`jarvis.py:1269`): probe4 printed `said: []` and only the "Ollama isn't running" problem.
- In the open ear with no name, `directed("I want to die", False)` is `"ask"`; with the default `JarvisRoomAsk=0` that is silence (`jarvis.py:1005-1008`).
- **Mutation M07** (the `if lane == "chat" and mood.crisis(turn.text):` line replaced by `if False:`) **survives all 1,292 asserts**: only the regex function and the line text are tested, never that a turn says it.

**Goal:** anyone who says something that signals self-harm hears the fixed line, whatever the model, Ollama, the setting or the ear window is doing.
**Scope (proposal, each part separable):**
1. Reviewed phrase list (add: not worth living, no reason to (go on|live), better off without me, too many pills / overdose, disappear forever, end it, don't want to be here...). Title exclusions (suicide squad). Idioms ("kill myself laughing") policy is **your call**; default proposal: keep as crisis (safe side) except "laughing/dying of laughter" forms.
2. Run the crisis check on the transcript **before** the Ollama/model preflight can end the turn (reorder in `_hear`; the preflight message still shows for non-crisis speech).
3. Decide whether `JarvisSeriousTopics=0` should disable the crisis line (today yes, pinned by test). Proposal: no, it only controls the serious *mood*.
4. A crisis phrase in the open ear counts as for him (`directed` -> `"yes"`).
5. End-to-end test: `talk(...)` of 12 phrases asserts `asked[-1] == CRISIS_LINE` and the model was not called.
**Non-goals:** the wording of `CRISIS_LINE` (unchanged unless you ask), anything logged (route name `crisis line` only, as today), clinical advice.
**Acceptance:** 20+ phrases true, 10+ benign false; Ollama-down test says the line; M07 and a new "ear window" mutant are caught.
**Validation:** gate + `semi_live` crisis cases (do not test casually; typed only, 8B and 3B). **Risk:** false positives say a heavy line to a harmless question; mitigated by the exclusion list. **Rollback:** revert the commit; `CRISIS_LINE` is a registered fixed line.

## F-02 Negation guard for the AI reread  (class A)
**Evidence:** `ask_ai("Please do not lower the volume.", chat)` -> True, `"Don't set a timer."` -> True, `"never turn the volume down"` -> True, `"I said don't mute"` -> True (probe4). In the 8B run (`rv-neg`) "Please do not lower the volume." became `act volume step -10 via ai-reread`: **it lowered the volume**. `AI_NOT` (`routing.py:36`) only matches question/past openers at the start and `don't` has no word boundary after `do`.
**Goal:** a sentence that negates the command is never re-read into that command.
**Scope:** in `ask_ai` (or in `interpret`'s acceptance check) skip when the text has `\b(?:don'?t|do not|never|no need to|stop|without)\b` before the command verb; keep "stop" commands that already route by rule.
**Non-goals:** no change to the model prompt; no change to rule routes (they already return chat for `don't change the volume`).
**Acceptance (test fails before):** `ask_ai` is False for the 9 phrases above; `understand("Please do not lower the volume.", ...)` is `chat` with the reread stub never called; `ask_ai("Please set the volume to 30.")` unchanged.
**Validation:** gate; golden routes will show diffs **only** on negated phrases (inspect each, then regenerate on purpose); semi-live `rv-neg`. **Risk:** a real command containing "no need to repeat" ... low. **Rollback:** revert one condition.

## F-03 "Remember to ..." promises a reminder that does not exist  (class B)
**Evidence:** `route("remember to buy milk")` -> chat (the memory rule has `(?!to )`, `routing.py:504`; `reminder_cmd` needs a time). 8B reply: "I'll remind you to purchase milk, sir." Nothing was set. `CANT_PROMISE` (`routing.py:318`) does not list "remind you" because he *can* remind, but only via the rule path; `mood.PROMISE` (`mood.py:219`) then **writes "I promised: I'll remind you to purchase milk" into the facts file**, which never rings.
**Goal:** he never promises a reminder he did not create.
**Second gap, seen with the 3B model:** `CANT_PROMISE` (`routing.py:318`) does not list `schedule`, `arrange`, `set up`, `add ... to your calendar`: the 3B said "I'll schedule a meeting for you for tomorrow at 3 PM, Mr. Sorsa." (calendar write is not built) and then the claims line followed it, so the user heard a promise and a contradiction (`rv-unbuilt2`, `rv-unbuilt3`).
**Options (your choice):** (a) route "remember to X" / "don't let me forget to X" with no time into the reminder path so he asks "When?" (the same "When? I didn't catch the time." line used today); (b) add `remind you` to the claims filter so the sentence becomes `CLAIM_LINE`/a new fixed line; (c) both.
**Acceptance:** `understand("remember to buy milk")` is `remind set` with `due None` -> "When?"; semi-live `rv-unbuilt3` has no promise; `mood.promise` no longer stores a reminder promise. **Needs approval:** new/changed spoken line. **Rollback:** revert.

## F-04 "What did you just do?" is answered with the claims line  (class B)
**Evidence:** after "Set a timer for 5 minutes", "What did you just do?" -> `I didn't catch that as a command, so nothing changed. Say it again, like: set an alarm for 7 AM.` (`rv-did`). The prompt carries the `did` list for exactly this question (`turnstate.DID_ASK`), the model answers truthfully ("I set a timer..."), and `no_claims` (`routing.py:328-345`) replaces any "I set" sentence with `CLAIM_LINE` because it cannot tell a report from a claim. The reply is also factually wrong (something *did* change).
**Goal:** a question about what he did is answered correctly.
**Options:** (a) answer it **from code** from `did` like `heard`/`again` ("I set a timer for 3:05 PM, then..."), no model (preferred: consistent with "decided by code"); (b) pass a flag to `reply_chain` so claims about items present in `did` are allowed.
**Acceptance:** after a timer + mute, "what did you do" lists both, in order, with no model call; empty `did` -> "I haven't done anything yet." **Needs approval:** new spoken lines. **Rollback:** revert.

## F-05 `DANGER` matches inside words  (class A)
**Evidence (probe_routes, 9 false positives -> `guard`):** "tell me about the Shackleton expedition" (`shack`**`hack`**`leton`), "what is a hackathon", "who is the hacker in mr robot", "what is a destroyer ship", "the brickell neighborhood", "explain what a nuke is", "I want to blow up this balloon", "how do I delete all my emails in gmail", "how do I format my resume". With the 8B model `chat.guard` + the GUARDRAIL prompt produced "I'm not capable of executing commands, sir. But I can suggest..." for the Gmail question (`rv-fp-delete`). `DANGER` is `confirm.py:8-10`; it is checked first in `route()` (`routing.py:413`).
**Goal:** the guard fires on the joke/destructive *commands*, not on words inside questions.
**Scope:** add `\b` to `hack|brick|destroy|nuke`, anchor `delete (all|every...)` and `format (my|the|c)` to command position (`^(?:please )?...`) and exclude question openers (`how|what|why|who`); keep every phrase the current test expects (`test_jarvis.py` has 1 DANGER test, M13 proves it is covered).
**Acceptance (fails before):** the 9 phrases route to `chat`; "delete all my files", "format the c drive", "disable the antivirus", "self destruct", "rm -rf" still `guard`.
**Validation:** gate + goldens (inspect diffs). **Risk:** a real jokey command slips to the model, which still has no OS actions. **Rollback:** revert regex.

## F-06 "No, make it 50" in the undo window  (class A)
**Evidence:** `followup.takes` lets level words through for 30 s after a volume change (`followup.py:76-83`, `SOUND_WORDS` contains "make it"), but `level_fix` (`jarvis.py:743-758`) uses `LEVEL.fullmatch` that starts with `(?:about|around|...|make it|to|at|um|uh|so|and)` and does not allow "no"/"actually"/"I meant", so the text becomes a chat turn and the claims filter answers "I didn't catch that as a command, so nothing changed" (`rv-act-act`). Also dropped silently: "Too loud." (`rv-toolow`), "Make it 20 minutes." after a timer (`rv-makeit`).
**Goal (A):** whatever the undo window lets in is understood. **Scope:** allow a leading `no|nope|actually|i meant|i mean|sorry` in `LEVEL`. **Not in this fix (feature, class B, listed in `LATER`):** "too loud / too quiet" as volume steps and "make it N minutes" for the last timer.
**Acceptance:** after a volume change `understand("No, make it 50.")` -> `act volume set 50 via context`; "No, I like it" stays chat. **Rollback:** revert regex.

## F-07 Trailing name breaks timers  (class A)
**Evidence:** `understand("set a timer for 5 minutes jarvis")` -> `remind set` with `due None`, label "5 minutes jarvis" (probe3); live typed run: "Set a timer for five minutes, Jarvis." -> "How long? I didn't catch the time." after **7.11 s** (the AI reread ran first). "Volume to 30 please Jarvis." only worked through the reread (1.66 s). `strip_name` removes only a leading name (`routing.py:228-240`).
**Scope:** in `route()` next to `,? please$` (`routing.py:412`) also remove `[, ]+(?:jarvis|clover)$` (names list from `NAME`, aliases only with a comma as today). **Non-goal:** alias names without comma.
**Acceptance:** 6 phrases with trailing name route like their plain versions with no reread call; "service the car" and "Travis Scott is..." unchanged. **Rollback:** revert.

## F-08 Hung turns, watchdog and silent drops  (class A for tests/logging, class B for behaviour)
**Evidence (probe5):** (A) a turn stuck for 181 s with `turn_id` untouched: watchdog sets `cancel`. (B) the same turn after an alarm ring set `turn_id[0] = time.time()` (`jarvis.py:529`): `watchdog` returns without cancelling (`while busy.locked() and started == turn_id[0]`, `jarvis.py:674`). (C) after the watchdog cancels, `busy` is still locked (it only sets an Event). (D) a second `exchange()` while busy returns with **no log line, no sound, no pop-up** (`jarvis.py:1298-1299`). The only test mentions the watchdog to **fake it** (`test_jarvis.py:1082`); mutation M27 is expected to survive.
**Goal:** a stuck turn is noticed, reported and recoverable; a refused turn is visible in the log.
**Scope A (tests + log):** test `watchdog` with a fake clock for A and B; add `log("turn ignored: busy")` (a count, no words). **Scope B (behaviour, needs yes):** keep the watchdog's own start time (do not reuse the alarm-touched `turn_id`); after cancel, if `busy` is still held 30 s later, set `S.err` "Stuck - restart JARVIS" once.
**Non-goals:** killing threads; changing the 180 s limit. **Acceptance:** tests for A/B; M27 caught. **Rollback:** revert.

## F-09 Typed confirmation dead end  (class B)
`rv-typed-confirm`: typed "Lock the computer." -> spoken/popup "You want me to lock the PC. Confirm with yes. Cancelled." The typed channel is never confirmed by the microphone (`jarvis.py:826-828`, design 8d), but the prompt still invites a yes and then cancels at once. A later typed "Yes." gets "There's nothing waiting for a yes."
**Options:** (a) for typed turns replace the prompt with "Say it out loud to confirm, sir." and do not say "Cancelled."; (b) let a *typed* yes confirm a *typed* ask (the offer mechanism already pairs channels: `jarvis.py:1049-1050`). **Needs approval** (wording; (b) changes the security rule). Preferred: (a).

## F-10 "What's in my notes about X?"  (class B)
`_rules_lookup` (`routing.py:547`) needs `search|check|look in|find|what do` before "notes". "What's in my notes about the trip" -> chat; the model then answers about "notes" from whatever is in its prompt (`rv-notes`, the harness uses a made-up profile, so what it said is not evidence of invention in your real data: **UNKNOWN**). Proposal: add `what(?:'s| is| did i (?:write|put)) (?:in|on) my notes` and "what did I write about X". Acceptance: routes to `notes` with target "the trip".

## F-11 "close the door" -> "I don't see door open."  (class B)
`_rules_apps` (`routing.py:757-764`) takes any `close X`. For X that is not a running window and not a known app word the better answer is chat. Proposal: say "I don't see ... open" only when X resembles an installed app name (`best_app`) or a running exe; otherwise fall through. Acceptance: "close the deal with the client" -> chat; "close chrome" unchanged.

## F-12 Play/pause/stop/resume are one toggle  (class B, needs live)
"stop the music", "pause", "play", "resume" all send the single `VK_MEDIA_PLAY_PAUSE` key (`routing.py:745-746`, `actions.py:275`). "Stop the music" while paused starts it; "play" while playing pauses (documented in the code comment). **Improvement:** read the playback state (Windows SMTC, `GlobalSystemMediaTransportControlsSessionManager`) and send the key only when it would change state; say "Nothing is playing." otherwise. Needs a live test with Spotify and a browser.

## F-13 Plain yeses refused  (class B)
`is_yes` (`confirm.py:12-18`) accepts a closed set. Refused (probe_misc): "yeah sure", "sure thing", "uh huh", "go for it", "absolutely", "ok do it", "yes lock it", "correct". Result: "Cancelled." For destructive actions refusing is the safe default, so any widening must be deliberate. Proposal: add only `yeah sure, sure thing, go for it, absolutely, ok do it, yes please do` (never `uh huh`, never a bare `right`). Acceptance: new list tested, "yes but don't" and "yes... no" still refused.

## F-14 HTTP errors reported as "Lost the connection"  (class A)
`urllib.error.HTTPError` is a subclass of `URLError`, so a 404 (model missing) or 500 (out of memory) reaches `except urllib.error.URLError` (`jarvis.py:1328`) and is shown as "Lost the connection to Ollama (...) - is it still running?". Also `chat_stream` ignores an `{"error": ...}` object inside the stream (`llm.py:178-194`), so the user sees "gave no answer". Scope: check `isinstance(e, HTTPError)` first and map 404 / 5xx to their own problem lines; log the status code only. **Wording is new -> show it to you.**

## F-15 Exceptions in the log may contain your words  (class A)
`log(f"turn failed: {e!r}")` (`jarvis.py:1333`) and nine similar lines (`jarvis.py:126,155,595,814,1545,1566,1671,1679`, `meaning.py:35`, `search.py:105,119`) log `repr(e)`. A `ValueError("invalid literal for int() with base 10: 'seven up'")` or `KeyError` repeats spoken text, against the "counts and route names only" rule. Scope: log `type(e).__name__` plus the module/line from the traceback, not the message. Acceptance: a test raises an exception whose message contains a marker word and asserts the log has no marker.

## F-16 Self-correction and compound-with-confirm wording  (class B)
"Set the volume to 30, no, 40" and "set the volume to 20 and lock the pc" both end in "Could you say that again?" (NEAR_MISS). Proposal: for "X, no, Y" / "X, I mean Y" take the last number; for compound-with-confirm say "One thing at a time, sir." Wording change -> approval.

## F-18 Numeric settings that raise on `inf`  (class A)
`ctx_tokens()` (`llm.py:13`), `keep_alive()` (`llm.py:85`) and `hud_tier()` (`jarvis.py:1352`) catch `ValueError` only; `int(float("inf"))` raises `OverflowError`, which would end every turn with "turn failed: OverflowError" (probe6). Other odd values (empty, text, negative, zero, 1e9, nan, 99999, "3,5") are handled. Scope: catch `(ValueError, OverflowError)` in the three places (the Control Center writes these keys, so this is hardening against a hand-edited `Settings.inc`). Acceptance: `settings_schema` test extended with "inf"; the three getters return their defaults. Rollback: revert.

## F-17 Documentation corrections  (class A)
- `LATER-2026-11-05.md` "Needs the user live" item 6 says `not an undo - dropped` "should now only appear for chatter". It also appears for real corrections: "Too loud." and "Make it 20 minutes." are dropped there (rv-toolow, rv-makeit). Reword it.
- Same file, Phase 8: "355 monkeypatch assignments over 72 names, `setting` reassigned 84 times". A quick regex count of `j.<name> = ...` lines (including tuple targets) gives 548 / 95 names / 94 for `setting`. Counting method unknown; the 4,875 lines and 1,292 asserts match exactly.

---

## Small capabilities found by testing (class B, all need your yes; none is a bug)
| ID | Idea | Evidence | Sketch |
|---|---|---|---|
| Q-01 | "Make it 20 minutes" / "make that 20 minutes" changes the last timer | `rv-makeit` dropped silently; listed in `LATER` | `_rules_followups`: if `last`/`did` says a timer was just set, route to the existing `("move", "timer", ...)` op (`reminders.py` already has it for "make the timer 10 minutes") |
| Q-02 | "Too loud" / "too quiet" / "I can't hear you" as volume steps | `rv-toolow`; reread-only today; listed in `LATER` | `_rules_sound`: bare feeling words map to `("step", -10)` / `+10`, only within `ACTIVE_TTL` of a volume change or as a full utterance |
| Q-03 | Verbless brightness: "brightness down a bit", "it's too bright" | `probe_routes` (chat) | add the verbless forms next to `bit` in `_rules_display` |
| Q-04 | A question asked in the 2 s undo window is dropped without a word | `rv-mem` ("What is my sister called?") | product choice: after a command also accept anything `directed()` calls "yes" (questions, commands), keep dropping chatter. Interacts with `UNDO_WAIT` (pinned by a test) |
| Q-05 | Calendar write / meeting requests get "I didn't catch that as a command" | `rv-unbuilt2` | add `calendar|meeting|appointment|event` + add/schedule/book verbs to `UNBUILT_CAPS` so he says the existing `CANT` line |
| Q-06 | "X-ray" line in the pop-up log: route kind, via (rule / context / ai-reread / model), seconds, result (names and numbers only, the same string as the `route:` log line) behind a setting | the line exists in `jarvis.log` (`jarvis.py:1342`); OpenJarvis shows the same idea in `XRayFooter.tsx` / `TraceDebugger.tsx` | cheap way to answer "why did he do that?" live; touches the pop-up feed (UI session owns the HUD side) |

---

## Tests to add (coverage gaps and mutation survivors)
Mutation results are in the review (section b4). Survivors and untested decision code:

| ID | Gap | Test to write |
|---|---|---|
| T-01 | **M07** crisis wiring in `_answer` untested | `talk()` 12 phrases, assert fixed line, `len(prompts)==0` |
| T-02 | **M06** `ask_yes` ignores his own prompt echoing back | fake `hear()` returns the prompt text; assert `confirm: heard only the prompt's own words - ignored` and action not run |
| T-03 | **M09** offer channel check (typed offer answered by voice) | typed fact offer, then spoken yes -> not saved, and the reverse |
| T-04 | **M17** `CORRECTION_TTL` | volume change, 31 s later "make it 30" in undo window -> dropped |
| T-05 | watchdog and busy (**M27**, probe5) | fake clock; A/B cases; "ignored: busy" log |
| T-06 | DANGER false positives (F-05) | the 9 phrases + 6 true guards |
| T-07 | negation reread (F-02) | the 9 `ask_ai` cases |
| T-08 | trailing name (F-07) | 6 phrases, reread stub not called |
| T-09 | **M05b** a typed destructive command is never confirmed by the microphone (`jarvis.py:826-828`), plus the F-09 wording | fake `hear()` returning "yes"; typed "lock the computer"; assert `run_action` not called |
| T-10 | `directed()` for crisis / questions in the open ear | table test |
| T-11 | **M26** a spoken yes to an offer with `heard_score < -1.0` does not save/close | offer + weak yes -> nothing happens |
All 37 mutants are reported in the review (b5): 8 survivors (M05b, M06, M07, M09, M17, M26, M27, M36); M17 is probably equivalent and M36 is equivalent (defence in depth); M28 hangs the suite.

## Order of work (if you approve)
1. T-01..T-05 first (tests only, no behaviour change), then F-15 and F-14 (class A, logging/wording-neutral except F-14 text).
2. F-02, F-05, F-06, F-07 (class A, small regex changes; golden diffs inspected one by one).
3. F-01 (needs your decisions on idioms and the `JarvisSeriousTopics` switch).
4. F-03, F-04, F-09 (wording).
5. F-08 behaviour part, F-10, F-11, F-13, F-16.
6. F-12 last (needs you at the PC).
Each step ends with the full gate and a rollback note; nothing is pushed.
