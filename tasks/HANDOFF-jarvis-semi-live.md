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
