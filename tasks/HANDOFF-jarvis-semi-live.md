# HANDOFF: JARVIS semi-live tuning session (started 2026-11-02)

Updated after every major change. Newest entry on top of the log (section 6). Read this first if you pick the work up.

## 1. What this session is
Make JARVIS (Clover) less odd/annoying and smarter WITHOUT audio, by typing what he "heard" into the real pipeline
(real Ollama model, real prompt, real routing) and scoring every reply. Then fix code/prompt, re-run, keep only what
helps on both models and on cases never tuned on. No UI work. No Rainmeter. Live (audio) test comes later.

## 2. Rules followed (from the repo)
- `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md`: fakes first, dry-run grep before running, no real destructive calls.
- Tests run on a scratch copy with `TZ=ABC+12`, under the venv (`%LOCALAPPDATA%\SpaceshipHUD\venv`) and `py -3`.
- Commit only on the user's word. Never commit Settings.inc, Data\, logs, weights, voice clips, results.
- Another session works on UI files (SpaceshipApp/...): never stage those with JARVIS work.

## 3. Tools built (all in `Skins/Spaceship/@Resources/Jarvis/tools/`)
| File | What |
|---|---|
| `semi_live.py` | Harness. Temp @Resources (Settings.inc, Data, persona, made-up profile/to-do/calendar/mail). Guards installed BEFORE import: subprocess/os.startfile/os.system blocked, ctypes.windll only read-only calls, every ACTIONS entry + run_action faked. A blocked call = TRIPWIRE in the results. `--model --cases --persona --opts --seed --only --out` |
| `make_cases.py` -> `semi_live_cases.jsonl` | Main bank: 221 cases, 44 held out (never tuned on). Categories: commands, small talk, identity, knowledge, can't-do, unclear, room talk, serious, rude, mistakes, moods, injection, homework, opinion, follow-ups, HUD info, lone words, ASR-noise variants |
| `make_fresh_cases.py` -> `semi_live_fresh.jsonl` | Fresh bank: 121 cases in new wording, ALL held out. Checks the fixes generalise |
| `score_semi_live.py` | Rule-based flags (no model judge): CLAIM, PROMISE, TOO_LONG, STOCK, OFFER, TIME24, META, ROUTE, SILENT/SPOKE_WHEN_SILENT, GUESSED, ... with weights -> "cost" (lower = better). `--compare a b`, `--show FLAG`, `--worst N` |
| `hearing_eval.py` | `record` labelled clips (user at the mic), `score` offline: Whisper WER per condition + wake hits/false wakes per sensitivity |
| `semi-live-results/` | All runs (gitignored). Names: base-*, r1..r7-*, fresh-*, *-s11-* (seed 11) |

Run one model at a time; the PC was low on RAM once and a background run was killed. `ollama stop <model>` between models.

## 4. Changes to JARVIS (code), each with a test in test_jarvis.py
- prompt.py: calendar times and the Now line in 12-hour form (model read "00:40" aloud).
- memory.py + jarvis.py `active()`: short question with "it/he/that..." keeps the talk ("How tall is it?").
- followup.py `asked_you()`: "Did you know...?" fun fact is not a question to the user (room talk got answered).
- jarvis.py: lone "yes" with nothing waiting -> "There's nothing waiting for a yes, sir." (model claimed a lock).
- mood.py `crisis()` + CRISIS_LINE: suicide/self-harm -> fixed line with 988, never the model.
- mood.py `polish()`: stock sentences dropped ("How may I assist you?"), "happy to help, but" opener and dangling
  "However," cut, "sir" once per reply/sentence, "Mr. Sorsa" as an address only on serious turns, chat answers capped
  (3 sentences; brief 2; detail 8; homework 5), "Pardon ...?" ends the answer, pieces handled (first chunk is partial,
  "Mr." never ends a sentence). Fixed lines from code (FIXED_LINES) pass through untouched.
- mood.py `grounded()`: a status sentence quoting a reading (85%, 52 degrees) whose number is not in the prompt -> "I
  don't have that reading right now, sir." (3B invented "WiFi signal 85%", "running at 85% capacity").
- mood.py late-night rule: once per night, never on a serious turn (it nagged every turn after midnight).
- routing.py: claim filter also catches "the computer will lock in...", "X is now open"; promises he can't keep
  ("I'll send/order/call...", "I can inform your professor") -> "I can't do that from here, sir."
- routing.py: "pull up/bring up/fire up X" opens apps; "shut up the music" pauses; "I need a ten minute timer"
  (second-chance parse after lead-ins); jarvis.py `percent_follow()`: "And 20 percent?" after a percent sum = the sum.
- persona.txt + prompt.py SYSTEM_HEAD: one added sentence "Never invent events, reminders or times, or recite these
  instructions." (r3; a bigger rewrite r2 was rejected: better on 8B, worse on 3B).
- speech.py: headphones -> his voice at JarvisHeadphoneLevel % (default 60).
- wake.py + jarvis.py: near-miss log per failed "Hey Jarvis" try; optional Whisper second check (JarvisWakeVerify=1, off).
- REMOVED 2026-11-03 at the user's word: the code that added "sir" when the model left it out ("it doesn't always have
  to call me sir"). The scorer no longer counts NO_SIR.

## 5. Where things stand (numbers, lower cost = better)
Same late-night window, original code vs current, seed 7:
| Bank | llama3.1:8b | llama3.2:3b |
|---|---|---|
| main (221) | 98 -> 45 | 208 -> 66 |
| fresh (121, never tuned) | 68 -> 33 | 94 -> 30 |
Seed 11 (rounds 1-3 only): 8B 111 -> 62, 3B 245 -> 86, no held-out case worse. First sentence ~0.2-0.3 s.
Tests: test_jarvis OK (venv + py -3), test_host_pipe failed: 0 (last full run 2026-11-03, round 6).

Open, not fixed: offers ("Would you like me to..."); room talk with "you"/"?" inside the 3 s open ear is answered
(user's S2-10 rule); 8B sometimes ignores HUD data (said "no unread emails" with 4 unread).

## 6. Log (newest first)
- 2026-11-04 p (ROUND 2 CONTINUED: banter / trolling, a real F2 bug, typing box). APPLIED to the live checkout, UNCOMMITTED, JARVIS restarted 04:21:17. Record of the live diff:
  tasks/jarvis-round2-live.patch (also holds F2 and the Pardon fix; jarvis.py/test_jarvis.py hunks are NOT in the refactor worktree, the other 6 files were copied there).
  F2 BUG FOUND AND FIXED: F2 made quiet.now() true for typed turns, and mood.class_time() read quiet.now() as "he is in class" -> every TYPED turn (and every semi-live run since F2,
  which types) was answered in SERIOUS mood, so mood text had no effect and banter looked flat. Now quiet.in_class() is the real quiet-hours check, now() = typed or in_class(),
  mood.class_time() uses in_class(). Test: F2 block in test_jarvis.py checks the real mood.class_time() during a typed turn; mutation-checked (caught).
  Semi-live results before this fix (the 3B baseline, banter flat, "playful barely moves him") were measured in that wrong serious mood: treat them as invalid for J1.
  BANTER: persona head no longer says "politely and formally" (now "courteous butler's manner, no swearing"); [mirror] = dry wit, plays along when teased; [playful] = shameless
  affectionate troll, teases only with what he was told or obvious exaggeration, never claims to have seen screen/browsing/files/readings; PLAYFUL_TAIL (last in the prompt, prompt.py)
  forces a jab after every answer (3-4 sentences). New mood.BANTER regex + ADD["banter"]: in mirror only, only when no other rule applies ("You're slow today.", "Roast me.",
  "Applaud", "I bet you can't...") -> one dry witty line, never a disclaimer, never invented numbers. Prompt cap in test_jarvis raised 1500 -> 1800 (default prompt is 1760;
  first sentence p50 stayed 0.38-0.40 s). Mirror cost 187 -> 183 on 262 conversation cases; serious cases (grandfather, job, lonely, sick dog) stay gentle in playful; knowledge
  answers stay plain. Tests: test_jarvis (banter/playful tail), mutation-checked 3 ways (caught). Gate: venv + py -3 OK, host_pipe 0, run_all OK, golden 0/834 and 0/2512.
  TYPING BOX (UI, user said fix it): SpaceshipApp/SpaceshipUI/src/modules/JarvisModule.tsx. Cause: Program.cs WM_LBUTTONDOWN takes keyboard focus only when a keyboard hit-region
  already exists; TYPE button was not one, so the box opened unfocused and onBlur closed it. Fix: TYPE rect is data-hit="keyboard" + 0.8 s blur grace. tsc clean, 4 vitest files
  (36 tests) pass. NOT rebuilt / not seen running: CSpace must be rebuilt (npm run build + publish) and restarted for it to take effect. TYPING BOX REBUILT 04:2x: the app serves SpaceshipUI/dist from disk (no dotnet publish needed): ran `npx vite build` (no `gen`), restarted CSpace (old pid 21724 -> 30024, JARVIS kept running);
  bundle checked: TYPE rect has data-hit=keyboard + the blur grace. Perf log clean, no Code Integrity block this time. NOT VERIFIED: the real click-and-type on the desktop (no desktop control here);
  a throwaway Playwright test (deleted) failed at its own first step (could not find/click the TYPE rect on /?host=mock&module=jarvislog&jarvislog=demo), so it proves nothing either way.
  Another session is editing JarvisModule.tsx (orb filter ids) and rebuilt/restarted CSpace at 03:56: its changes and mine are both in the working copy, uncommitted. WAKE SENSITIVITY: parked by the user, last.
- 2026-11-04 o (LIVE TEST ROUND 2: F1 better, wake word, "what did you say", typing, jokes). APPLIED to the live checkout, UNCOMMITTED, JARVIS restarted 03:25:53
  (needs a restart for any further change). F1: user says NO cracks any more after the restart (F1 buffer + F2 live). Nahimic (sound-processing driver) is installed and
  running; not touched; cause of the earlier cracks still unproven. Research + sources: tasks/jarvis-f1-glitch-research-2026-11-04.md.
  "WHAT DID YOU SAY": Whisper heard right (pop-up log: "I think you're annoying.", "What did I ask you?") and the MODEL answered "Pardon sir, what did you say?" because
  persona.txt/prompt.py SYSTEM_HEAD said "If the input is unclear, say Pardon...". FIX 1 (persona.txt + prompt.py, same words, prompt stays under the 1500-char test cap):
  Pardon only for garbled words. FIX 2 (new jarvislib/reply/pardon.py `no_pardon`, one call in jarvis.py, tests/test_pardon.py): if the opening of a chat answer asks to repeat while the
  words were clear (typed, or Whisper score >= -1.0), the model is asked once more with a firm hint; gibberish still gets the Pardon. Numbers (8B, seed 7, same cases):
  14 clear lines x2: 24 of 28 wrong Pardons (old) -> 0 (both fixes); 262 conversation cases: 21.6% (old, 483-case set) -> 6.1% (fix 1) -> 3.9% (fix 1+2), cost 195 -> 187; the 3
  gibberish controls and cut-off sentences ("What's the square root of") still ask, on purpose. Not fixed: lone "What?"/"Huh?"/"Jarvis." with no earlier reply (test artifact, but the
  retried answer is odd). Gate on live: test_jarvis venv + py -3 OK, host_pipe 0 failures, run_all OK (incl. test_pardon), golden routes 0/834, replies 0/2512. Patch (record of the
  live diff, jarvis.py hunk also holds F2's 2 lines): tasks/jarvis-pardon-fix.patch. NOT ported to the refactor worktree (its jarvis.py is split differently): port before merging it.
  JOKES / BANTER (J1): measured, NOT fixed. 8B answers teasing with disclaimers ("I don't have personal preferences", "That's not a question, sir"). Rewording the [mirror] mood line did
  nothing (replies identical), even the existing [playful] mood barely moves it: the main system text ("politely and formally") wins and the prompt is at its 1500-char cap. Next: few-shot
  banter examples or a lighter system text (needs the user's yes: it changes what he says), judged by the user's blind rating. New bank + scorer flags: tasks/jarvis-f3-bank-and-scorer.patch
  (not applied). 3B baseline on the chat bank: cost 172 (M1 misreads 84).
  WAKE WORD: log shows hits at 0.90-0.99 and misses at 0.24-0.37 (needs 0.50), misses below 0.15 are not logged. Suspect: the speech filter (vad_threshold=0.5 in jarvis.py wake_loop) and
  sensitivity 0.5 (Settings.inc, user said not to touch). My probe (scratchpad wake_probe.py: scores only, 4 filter settings at once) got NO speech on its first run (silent mic block, user
  was not speaking yet): must be re-run with the user saying "Hey Jarvis" ~10 times. TYPING BOX: nothing reached JARVIS (no ASK in the log); the box is SpaceshipApp JarvisModule.tsx
  and closes on blur (onBlur -> setTyping(false)); not my area, reported.
- 2026-11-04 n (LIVE FEEDBACK F1 revised, F2, F3, "blocked" check). Everything below is APPLIED to the live checkout, UNCOMMITTED; the running JARVIS
  must be restarted to use it. Rollback for each: `git apply -R tasks/<patch>`.
  F1 (cracked speech on speakers): the own-48 kHz-resample fix (entry m) was REVERTED. Blind A/B by ear (the user, 4 playback paths, one listen each,
  order hidden): own48 = the only one with glitches; current Windows-converted path clean; the same path with a 100 ms buffer smoothest. So: stream buffer
  default 0.1 s, setting `JarvisPlayerLatency` (0 = old "low"): `tasks/jarvis-f1-wasapi-buffer.patch` (player.py `stream_latency()`, config.py, tests).
  User after trying it: "still small glitches, but smaller". NOT SOLVED. One listen per version, position effect not excluded. Next: more A/B rounds with the
  first slot a throwaway; try 0.2 s; Windows audio enhancements / spatial sound on the Realtek device; mic stream in the same process; log the real device
  underflow count and per-reply peak (diagnostic only). Evidence so far: no clipping (peaks 0.38-0.57), GPU = CPU output, 0 underflows in a sandbox with Kokoro
  load, so the sandbox cannot reproduce it; only ears can.
  F2 (typed text only): what is typed in the chat is answered in the chat, never out loud: `quiet.typed[0]` set for the length of a typed turn
  (`quiet.now()` true, so every `muted()` call is true: pop-up text, no speakers), cleared in exchange()'s finally. `tasks/jarvis-f2-typed-text-only.patch`.
  F3 (wake word too hard, misreads, no jesting): PLAN ONLY, `tasks/jarvis-chat-quality-plan-2026-11-04.md`. Needs the user's real example lines and a yes
  to record wake clips. Nothing started.
  GATE: worktree (F1 buffer + F2 together): test_jarvis venv + py -3 OK, host_pipe failed: 0, run_all OK, golden routes 0/834, golden replies 0/2512. The LIVE
  checkout was only syntax-checked after applying (py ast parse of the 5 files); the full gate was NOT re-run on live. Mutation checks for F1/F2 were NOT
  completed: a mutated test run HANGS instead of failing (the earlier orphaned mutate.sh was one such run), so use `timeout 300` on every mutated run.
  "BLOCKED" messages: Windows Application Control (WDAC) policy {0283ac0f-fff1-49ae-ada1-8a933130cad6}, enforced for user mode. Event log
  Microsoft-Windows-CodeIntegrity/Operational, last 3 days: 3077 (enforced block) x3: `SpaceshipApp\publish\CSpace\CSpace.dll` loaded by CSpace.exe (11-03
  23:50), `SpaceshipApp\ShipCore.Core.Tests\...\ShipCore.Core.dll` loaded by testhost.exe (11-04 01:34), scipy `_peak_finding_utils.pyd` (11-04 00:20, my test);
  also `nvidia\cublas\bin\cublas64_12.dll` x26 (11-03 09:36-10:00, JARVIS python; Kokoro/Whisper ran on the CPU then, GPU from 10:17); and Windhawk's
  windhawk.dll into Chrome/Edge x541 (11-03 11:44-11:46). Cause: the self-built / pip-installed DLLs are unsigned. Fix is the user's call (sign them or add a
  supplemental policy / file-path rule); NOT touched. The CSpace.dll block is the SpaceshipApp session's area.
- 2026-11-04 m (LIVE FEEDBACK F1: speech "cracked at times" on the SPEAKERS, random slight glitches at random, non-repeating spots, start to end of a reply; user
  heard it in both replies at 00:01 and 00:02). EVIDENCE: log had only 2 smooth-voice replies, 0 under-runs, no player errors (but "under-runs" counts late synth,
  NOT device underflows). Offline, silent: Kokoro peaks 0.38-0.57, 0 clipped samples, GPU vs CPU click scores equal -> not clipping, not a CUDA artifact.
  Real Player.play in a sandbox under Kokoro load: 0 underflow flags in 323 writes, work between writes p99 6.9 ms (buffer 25 ms) -> not a write stall. What is
  left and UNPROVEN by ear: the 24 kHz stream goes into a 48 kHz Realtek device and Windows converts it (`auto_convert=True`, player.py). Random spots fit a
  per-sample conversion fault better than a seam or a Kokoro flaw (those would repeat). FIX (candidate, needs the user's ears): `JarvisOwnResample` (default 1,
  config.py; 0 = old way): player.py opens WASAPI at the device's own rate when it is a whole 2-4x multiple and upsamples the clip itself (`upsample()`, 129-tap
  Kaiser sinc, 10 ms for a 5.8 s clip). Tests added in test_jarvis.py (filter image < -50 dB, stream rate, pause at device rate, off switch, 44.1 kHz untouched,
  WASAPI-refused fallback); mutation-checked (2 mutations fail the new tests). Gate: test_jarvis venv + py -3 OK, host_pipe failed: 0, run_all OK, golden routes
  0/834, golden replies 0/2512. Real device smoke: stream open (wasapi, 48000 Hz, clips upsampled by us from 24000 Hz). APPLIED to the live checkout (uncommitted, user said yes 2026-11-04): patch
  `tasks/jarvis-f1-own-resample.patch`, files player.py, config.py, test_jarvis.py; gate re-run on the live code: all green (same numbers). Also in worktree
  refactor/jarvis-pipeline, uncommitted. The running JARVIS process (started 23:50) still has the OLD code until it is restarted. Rollback: `git apply -R` the patch.
  The orphaned `mutate.sh` chain (bash + test_jarvis python, started 23:52 from the refactor session, harmless, only touches the scratch mirror) was still running:
  stopping it was refused by the permission check, so the user decides (see its PIDs in the log of the session). NOT verified:
  that it removes the glitches (blind A/B of 4 playback paths was played, answer pending; key in the session scratchpad ab_key.json). If glitches stay, next
  suspects: Windows "audio enhancements" / spatial sound on the Realtek device, the mic stream open in the same process, WASAPI shared-mode period.
- 2026-11-03 l (REFACTOR phases 6, 4, 7 + final A/B; branch refactor/jarvis-pipeline at 147b66d, NOT merged to main, live checkout still on jarvis-live).
  PHASE 6 (exchange() slices, move only, 3 commits): `_record_chat` (31 lines, 17c32cb), `_hear` (74 lines, 966ab84; returns (text, model, hud,
  reading, t_spoke, wait) or None), `_gate` (27 lines, f2c9199; True to go on). Each: lines copied unchanged, gate green, plus a mutation check in
  the scratch mirror that makes test_jarvis fail (recent[me] not set; wait+99; heard_as==no disabled). The middle of exchange() (courtesies,
  confirmations, understand, commands, HUD blocks, prompt) is NOT split: it shares `quiet`, `text`, `way`, `left` and the `fixed()` closure
  with the code around it, and `text`/`quiet` are reassigned in it. Semi-live 8B (p6 vs p5): 35/33/16 vs 37/33/9, decisions 400/400.
  PHASE 4 (12e2c36): the 319-line `_route_rest` ladder cut into 15 ordered area functions (`_rules_undo` ... `_rules_misc`) + one `RULES` tuple;
  `_route_rest` is a 9-line driver. Cut points came from a static flow check (59 free cuts; the 15 used are contiguous groups); no regex or
  line touched, the diff is 72 insertions + the 4 header lines. `tests/test_rule_order.py` pins/prints the order. Golden routes 0/834 diffs;
  removing one area gives 7 golden diffs (net works), restoring gives 0. NOT DONE: Intent type instead of the positional 4-tuple, folding
  percent_follow/level_fix/AI reread into the list (an API change; route() is used everywhere).
  PHASE 7 (147b66d, checks only): `tests/test_action_table.py` (31 actions: callable, risk in read/change/ask, description, DID sentence or a
  written exemption, destructive rows are "ask"). FOUND, NOT CHANGED: `DID` has no sentence for the `mood` action (did_add falls back to
  the bare word "mood"); `open`/`close` are built from the target. help_cspace.txt NOT generated from the table (user-visible text).
  `ARCHITECTURE.md` (Jarvis folder): turn flow, module map, where-to-add table, gates, traps.
  PHASES 8 and 9 NOT DONE: re-homing the 4.7k-line test_jarvis.py (443 `j.X =` fakes across 81 names, `Everywhere`) into injected fakes and making
  semi_live run through them are the largest and least safe steps, and the current suite is the safety net for everything above; the traps
  (RES from sys.argv at import, shared-module fakes) are documented in ARCHITECTURE.md. Phase 1's call-site migration to config.py also waits for 8.
  FINAL A/B, original Phase 0 code (live checkout) vs finished refactor, same hour, seed 7, TZ=ABC+12, tripwires 0 everywhere
  (cost old -> new; first-sentence p50 old -> new):
    8B  main 35 -> 40 (0.36 -> 0.36)  fresh 22 -> 32 (0.34 -> 0.35)  persona 12 -> 16 (0.37 -> 0.37)   decisions 400/400 equal
    3B  main 61 -> 57 (0.24 -> 0.24)  fresh 27 -> 19 (0.24 -> 0.25)  persona 37 -> 29 (0.24 -> 0.24)   decisions 398/400 equal
  The 3B differences: room-00 and room-01 second turn, "ear -> not for me - quiet" (old) vs "chat via model -> answered" (new): both are
  the open-ear window. Cause checked in the result files: turn 0 differs. The new run's 3B reply ended in a question ("...what kind of topic
  would you be interested in?"), so asked_you() made the next line count as for him; the old run's reply was a statement. Model output
  variation, not a code change (golden `directed()` 0/834 diffs, 8B decisions 400/400). 8B fresh +10: 2 cases worse (a GUESSED time line, and
  fresh-serious-4 MUST_NOT, which already flipped between two runs of UNCHANGED code earlier today); 92/130 spoken turns identical, the
  rest differ because the prompt carries the clock minute and old/new ran minutes apart. Same-code spread seen today on 8B fresh: 22-35.
  Whole-refactor gate: test_jarvis OK (venv + py -3), host_pipe failed: 0, run_all OK (7 files), golden routes 0/834, replies 0/2512.
  ROLLBACK: `git revert` the commit range 7ba312b..147b66d (newest first), or delete branch refactor/jarvis-pipeline and remove the worktree
  (`git worktree remove ../RainmeterSpaceship-refactor`). The live HUD never ran this code. To adopt it: stop CSpace, merge the branch,
  restart, and do the live test of the voice work first (it was never confirmed finished).
- 2026-11-03 k (REFACTOR phases 3 and 5 done as far as is safe; commits 91ed765 phase 3, then phase 5; branch refactor/jarvis-pipeline).
  PHASE 3 voice package (move only): speech.py cut by line range (text unchanged) into `jarvislib/voice/` chunker (first_words..sentences_from),
  pacing (merged, plan_chunks, hesitation_parts), output (headphone_gain, output_name, play_samples, muted, say_text_only, SHOW/HIDE_LOG),
  fillers, speaker (speak_all, _speak_queue); tts.py -> voice/synth.py and player.py -> voice/player.py by `git mv`. `output` exists so
  speaker <-> fillers has no import cycle. `jarvislib/tts.py` and `player.py` are sys.modules ALIASES of the moved modules (tests set
  attributes such as `jarvislib.player.SMOOTH_DEFAULT`, tools set `tts.RES`); `speech.py` re-exports every old name (checked against the
  old file's names from git: none missing). Static undefined-name check on all voice modules: none. Schema test now scans sub-packages.
  Gate: test_jarvis OK x2, host_pipe failed: 0, run_all OK, golden 0/834 + 0/2512; `tools/voice_gaps.py --no-synth` identical old vs new
  (47 chunks, 19 seams, mid-clause seams 13 -> 4, first chunk 6.2 words); silent zero-amplitude WASAPI smoke through the moved player ok
  (api wasapi, closes clean). Semi-live 8B old vs new, seed 7, same hour, tripwires 0: main 36 -> 37, fresh 32 -> 33, persona 18 -> 8,
  first sentence p50 0.44-0.48 -> 0.41-0.44 s. NEW CHECK `route_ab.py` (jarvis-gate folder): turn decisions (route line without timing +
  requested actions) old vs new: 400/400 turns equal; use it as the exchange-level gate for phases 4 and 6.
  NOT DONE in phase 3 on purpose: `Voice.say() -> Spoken` facade (an API change, not a move), jarvis.py importing the voice internals
  (`_speak_queue`, `_filler_*`) from the new modules instead of the shim (no gain, pure risk), removing JarvisVoiceSmooth=0: KEPT as the
  legacy path until the user's live test is confirmed (decision for phase 3 was "keep", plan question 5).
  PHASE 5 session (the safe slice only): `jarvislib/session.py` `reset_turn_state()` clears mood + timed mood, offer, last, recent, undo, did,
  heard_score in place; tools/semi_live.py and tools/golden_common.py call it instead of two copies of those lines; tests/test_session.py.
  Product code does not call it. Gate: tests OK x2, host_pipe failed: 0, run_all OK (5 files), golden 0 diffs; semi-live 8B (p5 vs p3-new):
  main 37 -> 37, fresh 33 -> 33, persona 8 -> 9, decisions 400/400 equal, tripwires 0.
  NOT DONE in phase 5 on purpose: moving `history`, `last_turn`, `cancel`, `busy`, `turn_id` into a Session and the structural stale-turn
  guard. Reasons: tests rebind `j.offer`, `j.last`, `j.history`, `j.last_turn` outright (a Session holding its own copy would diverge
  silently); `turn_id` is a timestamp the watchdog thread compares; cancel/busy are shared with the wake/barge-in threads and no test can
  exercise those races. B10 audit (log g) already found the stale-turn paths guarded. Module-level mutable state count stays 59 (inventory).
- 2026-11-03 j (REFACTOR phase 2 DONE, commits 514dc36 move, d6c3758 edits; branch refactor/jarvis-pipeline, not merged to main).
  `jarvislib/reply/fixed.py`: ONE registry of 31 fixed lines (11 moved from routing/mood/prompt/memory/diag, 18 jarvis.py literals,
  NO_ABILITY lines listed too); FIXED_LINES is derived from `passthrough=True` entries (same 3 lines as before); the old names are
  re-exported, so nothing else changed. jarvis.py uses `FX.<NAME>` for 35 inline literals (tokenize-based replace, f-strings and
  comments untouched). `reply/policy.py`: `reply_chain()` = the old polish(grounded(no_hope(no_claims(sentences_from)))) call, ORDER tuple.
  Tests (tests/): test_fixed_lines (registry, pass-through set, no raw literal into fixed()/reply_line() in jarvis.py), test_reply_policy
  (600 corpus replies identical to the old chain, smooth 1 and 0; first piece released before the stream ends), test_settings_schema.
  Gate: venv + py -3 test_jarvis OK, host_pipe failed: 0, run_all: OK (3 files), golden routes 0/834, replies 0/2512 diffs.
  Semi-live A/B, old code (phase 0, live checkout) vs new, seed 7, same hour, TZ=ABC+12, tripwires 0 everywhere
  (cost old -> new; first-sentence p50 old -> new):
    8B  main 38 -> 34 (0.35 -> 0.36 s)   fresh 35 -> 34 (0.33 -> 0.33)   persona 19 -> 13 (0.37 -> 0.38)
    3B  main 50 -> 53 (0.24 -> 0.24 s)   fresh 38 -> 35 (0.24 -> 0.24)   persona 36 -> 37 (0.23 -> 0.25)
  All inside the +-5 run noise measured in entry h; first sentence within +0.02 s. Replies not read line by line (cost cannot see
  "sounds odd"), but the code path is byte-identical on the golden replies.
  NOT DONE on purpose: (1) filters as feed() objects: the lazy-generator contract (first piece out before the stream ends) is the
  voice timing, the rewrite buys readability only and carries the highest risk in this phase; revisit with phase 6. (2) Scorer sharing
  the runtime CLAIM regex: kept independent so a gap in the runtime filter cannot blind the measurement. (3) The remaining non-fixed
  strings (prompts, AI_PROMPT, regex tables) stay with their rules. Phase 1 call-site migration also still open (waits for phase 8).
  Gate script and A/B runner: C:\Users\Senai\AppData\Local\Temp\jarvis-gate\ (outside the repo; gate.sh, sl_ab.sh).
- 2026-11-03 i (REFACTOR phase 1, settings table, commit fe3b017). User: do all phases, check and commit myself, no per-phase check-ins.
  Work happens in a git worktree `C:\Users\Senai\RainmeterSpaceship-refactor` (branch refactor/jarvis-pipeline); the live checkout
  stays on branch `jarvis-live` (= phase 0 commit), so the running HUD never sees a half-done phase. Nothing is merged into main.
  Gate script: session scratchpad `gate.sh` (mirror of the worktree code + live Settings/Data copies, TZ=ABC+12).
  Added `jarvislib/config.py` (DEFAULTS: 65 keys, RAW_READS for the two deliberate "" reads) and `tests/test_settings_schema.py`
  (static: every setting()/on()/_num()/PAUSES/settings().get read uses a table key with the table default; no unused key) +
  `tests/run_all.py`. Call sites NOT rewritten on purpose: test_jarvis.py fakes `setting` per module (`_mic.setting`, `_on.setting`),
  a `conf()` indirection would bypass those fakes; the move waits for injected fakes (phase 8). Mutation check: wrong default,
  missing key and unused key each fail the test. Gate: venv + py -3 test_jarvis OK, host_pipe failed: 0, tests: OK, golden routes 0/834,
  replies 0/2512 diffs. Semi-live not re-run: no runtime module imports config.py (no behaviour can change).
- 2026-11-03 h (REFACTOR phase 0, branch `refactor/jarvis-pipeline`, plan `tasks/jarvis-refactor-plan-2026-11-03.md`):
  User answers to plan section 12: branch + merge phase by phase; tests/ restructure OK; log text may change if the `route:` prefix stays;
  phases in the recommended order (0,1,2,3, then 5/6, then 4, then 7-9); legacy `JarvisVoiceSmooth=0` path: decide at phase 3.
  Live test of voice/B1/B2/B10 NOT confirmed done (user said "do as you recommend"); phase 0 changes no product code, so it went ahead.
  Commit 5fa6e3d on the branch = the uncommitted g/f work as the known starting point (JARVIS files, tools, task docs only).
  Session start block for later phases: plan section 10. Phase 0 added (no product code touched):
  `tools/golden_common.py` (sandbox: semi_live guards, temp RES, frozen clock 2026-11-03 15:00 at TZ=ABC+12, model calls trip),
  `tools/golden_routes.py` -> `tests/golden/route_corpus.txt` (540 phrases from the 3 banks + test_jarvis literals + AI_PROMPT examples,
  + 294 seeded ASR variants) and `routes.jsonl` (route, fix_route, ask_ai, understand, directed x2, level_fix, percent_follow, crisis,
  no_ability, LIVE_FACT, logs). `tools/golden_replies.py` -> `reply_corpus.jsonl` (28 trigger lines + 600 seeded replies from
  semi-live-results) and `replies.jsonl` (exchange() chain, 4 configs: smooth 1/0 x cap3/serious). `tools/inventory.py` -> `inventory.md`.
  Results: routes 834 phrases, 34 AI rereads asked (faked), 0 model calls, 0 tripwires, `--check` 0 diffs (2nd run, new process).
  Replies 2512 replays, 0 tripwires, `--check` 0 diffs; filters seen acting: reading 36, promise 24, claim 12, hope 4.
  Inventory: 59 module-level mutable state names, 46 UPPER tables, 82 setting()/on() sites (59 keys), 2 keys with different defaults
  (JarvisKokoroVoice '' vs 'bm_lewis'; JarvisSilence '' vs '1.0': phase 1 must keep today's live behaviour), 32 canned strings,
  443 `j.X =` fakes (81 names), 28 Thread sites, 30 jarvislib import lines in jarvis.py.
  Gate (scratch mirror, TZ=ABC+12): venv test_jarvis OK (91 s), py -3 test_jarvis OK (88 s), test_host_pipe failed: 0.
  Semi-live 8B seed 7 baseline, run 12:3x local: main 42, fresh 27 (re-run 31), persona 17; tripwires 0; first sentence p50 0.39-0.41 s.
  NOISE: same code, same seed, back to back: fresh 27 vs 31 (2 held-out better, 2 worse). Log g numbers (36/16/16) were another clock
  window (prompt has the real time), so gates compare only with a baseline from the same session, tolerance about +-5 per bank.
  3B baseline NOT run (phase 1 is 8B only per plan section 4; run 3B before phase 2). Real Data\jarvis.log untouched by the golden tools.
- 2026-11-03 g (pre-live-test finish, NOT committed): JarvisVoiceSmooth now defaults to ON in code (`player.SMOOTH_DEFAULT = "1"`;
  Settings.inc untouched; `JarvisVoiceSmooth=0` in Settings.inc restores the old stream-per-chunk path). B10/B11: `reply_line` no longer
  logs/remembers a fixed line that was stopped before a word got out; the other stale-turn paths were audited and already guarded (busy lock +
  cancel checks after listen, transcribe, model read, ask_yes). New `tools/voice_ab.py`; A/B WAVs (5 voices x speeds 0.92/0.96/1.0 x 3 lines)
  in the session scratchpad `voice-ab\` for the user to listen to. Refactor plan written: `tasks/jarvis-refactor-plan-2026-11-03.md` (do not start before the live test).
  Semi-live seed 7, current code (cost; before in brackets): 8B main 36 (43), fresh 16 (32), persona 16 (14); 3B main 56 (85), fresh 36 (41),
  persona 32 (28). Tripwires 0. First sentence p50 8B 0.33-0.43 s (0.28-0.30). Persona rises are within run noise (no persona edits made yet).
  Tests: test_jarvis OK (venv + py -3), test_host_pipe failed: 0 (scratch mirror, TZ=ABC+12).
  NOT DONE (needs the live test first or the user's call): persona edits A1/A2/A3/A7 (bank + baseline ready), S3 choice of voice/speed by ear,
  V13, B3/B4/B8 models, B5-B9. Live check list: first word latency, no gap/click between chunks, "stop" and barge-in cut within a block, headphone
  level, pop-up typing, fillers join the reply, WASAPI falls back if the device is busy (log line "player: WASAPI not available").
- 2026-11-03 f (finish-up session, NOT committed, stopped here on the user's word; continue from "Next"):
  DONE: P0 persona bank `tools/make_persona_cases.py` -> `semi_live_persona.jsonl` (29 cases, held out; separate file so the main/fresh
  baselines stay comparable) + scorer flags OVERJOKE / DRAMA / PROACTIVE_CLAIM / NO_DRY (only where a case sets expect.dry / readout).
  Baseline persona cost (seed 7): llama3.1:8b 14 (NO_DRY 7, OFFER 2, PROACTIVE_CLAIM 1), llama3.2:3b 28.
  V S0: `tools/voice_cases.txt` (28 lines) + `tools/voice_gaps.py` (silent, offline). Baseline (old way, CPU Kokoro): 52 chunks, mid-clause seam
  silence median 256 ms, clause 275, sentence 418; first chunk 4.5 words.
  V S1 `jarvislib/player.py` (new): persistent stream, WASAPI shared/low-latency/auto-convert with automatic fallback, trim -45 dB + 10 ms fade,
  chosen pauses (cont 25 / clause 150 / sentence 300 / hesitate 350 ms), idle close 1.5 s, warm-up. Silent real-device smoke: WASAPI open 48 ms +
  first write 26 ms, device latency 0.025 s vs default API 49 + 75 ms, 0.182 s; second clip in the same stream has no open cost; bad device ->
  fallback works.  S2 (speech.py): clause-aware first chunk (>=4 words, >=3 left in the sentence, never before "sir", no weak/number ending,
  cap 9 words), long sentences split at a comma, short pieces merged (V8), "..." hesitation, V14 one voice after a fallback, V15 warm voice
  after idle unload, fillers through the player, B11 only words that got out count as said. After (GPU Kokoro): 47 chunks, mid seams 13 -> 4
  (median 65 ms), clause 190, sentence 340; first chunk 6.2 words (about +0.05-0.1 s, not measured live).
  Everything is behind JarvisVoiceSmooth (code default 0; Settings.inc untouched). New code defaults: JarvisWasapi 1, JarvisPause*, JarvisTrimDb,
  JarvisFadeMs, JarvisIdleClose. Skipped: V13 high-pass/limiter, paragraph pause (no paragraph info), crossfade overlap (fade + 25 ms instead).
  B1: mood.miscounted() (no/other unread count, no events/to-dos/apps against data) -> NO_READING; S2-10 room-talk rule left unchanged on
  purpose (it is the user's design: "?"/you = for him). B2: prompt.no_ability() fixed lines (payments, bookings, travel, meetings, messages/calls,
  subscriptions, print, TV/lights, named music app), hooked in jarvis.py for chat kind with no HUD blocks.
  Tests: test_jarvis OK (venv + py -3) and test_host_pipe failed: 0 after the last edit, scratch mirror, TZ=ABC+12 (earlier gate
  before them: host_pipe failed: 0). Semi-live 8B/3B main+fresh NOT re-run yet (B1/B2/persona changes touch replies).
  NEXT: re-run the gate (venv + py -3 + host_pipe) and both semi-live banks for B1/B2; B10 stale-turn guard; persona edits A1/A2/A3/A7
  (judge on the persona bank, both models); S3 voice A/B WAVs (speed 0.92/0.96/1.0, voices) for the user to listen; optional B3/B4/B8.
  Voice scratch outputs: scratchpad wav-ab\ (old/new WAVs from voice_gaps), wav-baseline\.
- 2026-11-03 e (final fixes, not committed): routing.py OTHER_DEVICE: "Set my alarm on my phone" -> "I can't reach your
  phone from here. I can set that on this PC, though."; other device commands (TV, car, watch, iPad...) -> "...I only
  control this PC." NEAR_MISS reworded to "Could you say that again?".
  mood.py OFFER_SENT: a trailing "Would you like me to...?" sentence is cut in polish() (a lone offer and real questions
  stay). Tests added in test_jarvis.py (route + polish). test_jarvis OK (venv + py -3), test_host_pipe failed: 0
  (scratch copy, TZ=ABC+12). Semi-live 8B seed 7: fresh 32 -> 32 (OFFER 4 -> 1, one TOO_LONG noise), cantdo/command/
  unclear (main) cost 8, 0 tripwires. 3B not run (no model-output change besides the offer cut).
- 2026-11-03 d (FINAL for this session): user: "finish up, log everything, commit, live only into CSpace".
  Final numbers (round 8, current code, seed 7; NO_SIR no longer counted):
  | Model | main (221) | fresh (121) | clean main | first sentence p50 |
  |---|---|---|---|---|
  | llama3.1:8b (main, keep) | 43 | 32 | 193 | 0.30 s |
  | llama3.2:3b (busy-GPU fallback) | 85 | 41 | 187 | 0.22 s |
  | qwen3:4b-instruct-2507 (downloaded, not used) | 85 | 12 | 166 | 0.24 s |
  | phi4-mini (downloaded, not used; round 7) | 81 | 41 | 196 | 0.23 s |
  Quality read by hand (Claude): 8B sounds the most intelligent (accurate, short, natural); 3B knows the same facts
  but is wordier and offers things; qwen3 4B explains best (best fresh score) but offered to "message your group
  chat" (a capability it lacks) and uses curly quotes / em dashes. Keep llama3.1:8b. qwen3 is the candidate to
  test next as the busy-GPU fallback (replacing llama3.2:3b) and as the AI-reread model.
  Odd reply still from code: "Set my alarm on my phone" -> "I heard a command but couldn't work it out."
  Research (not built, ideas for next time; specialist models already trained for one job, no fine-tuning):
  - Vision skill "what's on my screen": qwen2.5vl:3b (~3.2 GB) or gemma3:4b via Ollama; needs a download + approval.
  - Reasoning / "think hard": JarvisModelDeep already exists (empty); deepseek-r1 distill or phi4-mini (downloaded).
  - Command reading: the AI reread (llama 8B, up to 7 s) could use a small tool-calling model (qwen3 4B in Ollama
    supports tools); test it on the fresh bank's command cases first.
  - Memory recall: a small reranker (ms-marco MiniLM / bge-reranker-v2-m3 ONNX) on top of the MiniLM search.
  - Hearing: distil-whisper models are faster but less accurate than small.en; decide with hearing_eval clips.
  - Smart-home style fine-tunes (home-llm by acon96) exist but target Home Assistant and carry non-commercial
    licences; not a fit as-is.
  Tests at the end: test_jarvis OK (venv + py -3), test_host_pipe failed: 0. Committed (JARVIS files + tools + docs
  only). Live = CSpace (it runs the repo copy); the Rainmeter live skin was NOT touched (user: "only into C-space").
  CSpace was not running at commit time: its next JARVIS start uses this code.
- 2026-11-03 c: user: "sir" not required; judge intelligence by reading replies; research efficiency + prompt
  engineering; keep fixing; keep this doc. Removed sir injection; harness prints UTF-8 (qwen3 run crashed on "→").
  Candidate models already downloaded (no download needed): qwen3:4b-instruct-2507 (partial run looked best so far),
  phi4-mini (main 81 / fresh 41: worse than llama3.1:8b). Next: full qwen3 run, read replies for intelligence.
- 2026-11-03 b: round 7: grounding filter + sir fallback (sir fallback since removed). NO_SIR 7 -> 1.
- 2026-11-03 a: rounds 4-6: fresh bank, routing fixes, late-night, Mr. Sorsa, promises. Second seed confirmed.
- 2026-11-02: plan approved; harness, banks, scorer, rounds 1-3, headphones, wake tools, hearing_eval. Commit 7d3e568
  (timed-mood fix) was the only commit; everything since is uncommitted.

## 7. Rollback
Everything after 7d3e568 is in ONE commit (see `git log -1 -- tasks/HANDOFF-jarvis-semi-live.md`): undo with
`git revert <that commit>`, then restart JARVIS in CSpace. The Rainmeter live skin was never changed.
Files touched: jarvis.py, jarvislib/{followup,memory,mood,prompt,routing,speech,wake}.py, persona.txt, test_jarvis.py,
Docs/Jarvis-Assumed-Settings-and-Guide.txt, .gitignore, tasks/{jarvis-next-plan-2026-11-02,phase10-slice2-todo}.md.
