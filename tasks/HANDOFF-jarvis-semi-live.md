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
