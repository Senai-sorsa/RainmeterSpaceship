# HANDOFF: JARVIS refactor state + live-test feedback loop (written 2026-11-04)

Read this first in a new chat. Older detail: `tasks/HANDOFF-jarvis-semi-live.md` (section 6 log, entries h to l are the refactor),
`tasks/jarvis-refactor-plan-2026-11-03.md` (the plan), `Skins/Spaceship/@Resources/Jarvis/ARCHITECTURE.md` (what the code is now).
Rules that apply: `CLAUDE.md` (repo root, smallest change, report real command output), `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md`
(fakes first, dry-run grep, no real destructive calls). Work only in `Skins/Spaceship/@Resources/Jarvis/` and `tasks/`.

## 1. What code is what (verify with `git log` before assuming)
| Place | Branch / commit | Contains |
|---|---|---|
| Live checkout `C:\Users\Senai\RainmeterSpaceship` | `main` at `adda63f` (at time of writing) | Refactor phases 0-7 (my last merge was `88b27e0`, a fast-forward) + another session's UI merge on top |
| Refactor worktree `C:\Users\Senai\RainmeterSpaceship-refactor` | `refactor/jarvis-pipeline` at `d92c477` | Everything in main from me + phases 6d and 6e (gated, committed, NOT in main) |
| Same worktree, uncommitted | working tree of `jarvis.py` | Phase 6f (`_command`, 87 lines moved). Also saved as `tasks/jarvis-refactor-6f-commands-stage.patch` |
| Other worktree `C:\Users\Senai\RainmeterSpaceship-livefix` | `fix/live-test` | NOT mine (UI session; its branch was merged into main by it) |
Branch `jarvis-live` = the pre-refactor JARVIS code (phase 0 commit). It is merged into main and safe to delete.
Nothing was pushed (`origin/main` is far behind; I never pushed).
**So when you run JARVIS from the live checkout you are running main = refactor through phase 7, WITHOUT 6d/6e/6f.**
The main-vs-original comparison (final A/B below) is the evidence for that exact code.

## 2. What the refactor did (all behaviour-preserving) and what it did not
Done: 0 safety net (golden routes/replies, inventory) - 1 settings table `jarvislib/config.py` - 2 fixed-line registry `reply/fixed.py` +
`reply/policy.py` - 3 voice package `jarvislib/voice/` (old import paths still work) - 4 rule ladder cut into 15 ordered areas
(`RULES`) - 5 only `session.reset_turn_state()` - 6a/6b/6c `_record_chat`, `_hear`, `_gate` out of `exchange()` (in main), 6d `Turn`
object + `_fixed`, 6e `_preempt` (branch only), 6f `_command` (uncommitted) - 7 action-table test + ARCHITECTURE.md.
NOT done: phase 8 (re-home the 4.7k-line `test_jarvis.py` onto injected fakes), phase 9 (tools through the same fakes, remove the
`RES = sys.argv[1]` import trap), Session for history/last_turn/cancel/busy/turn_id and the structural stale-turn guard, phase 6 model-answer
stage (`_answer`, the last slice of `exchange()`), `Intent` type, `feed()`-style filters, settings call sites still use `setting("Key","default")`
(table only checks them). `JarvisVoiceSmooth=0` legacy voice path was KEPT.

## 3. Evidence for main (phase 7 code) - how far to trust it
Gate on the final code: `test_jarvis` OK (venv python AND `py -3`), `test_host_pipe` failed: 0, `tests/run_all.py` OK (7 files),
golden routes 0 diffs / 834 phrases, golden replies 0 diffs / 2512 replays, `voice_gaps --no-synth` identical old vs new, silent WASAPI smoke ok.
Semi-live, original code vs refactor, same hour, seed 7, 0 tripwires (cost, lower is better; run noise is +-5..10 per bank because the prompt
carries the clock minute):  8B main 35->40, fresh 22->32, persona 12->16;  3B main 61->57, fresh 27->19, persona 37->29.
Turn decisions (route + requested actions) equal on 400/400 turns (8B) and 398/400 (3B; the 2 differ because the 3B model's first reply
ended in a question that turn, not because of code). First sentence p50 unchanged (8B 0.36 s, 3B 0.24 s).
HONEST LIMITS: semi-live types text, so audio, microphone, wake word, barge-in and the real speakers have NOT been exercised by me
since the voice work. A real test of the voice work was never confirmed by the user. Mutation checks showed some rules in
`exchange()` had no unit test (4 were covered by new tests, on the branch); 6f's rules were not mutation-checked (the run was killed, see 4).

## 4. Unfinished at the moment of writing
- 6f mutation checks: a background `mutate.sh` run (`%LOCALAPPDATA%\Temp\jarvis-gate\`) was still running or orphaned; the system had run low on memory
  and Claude Code killed an earlier copy. Do not restart it unless RAM is free (check; unload Ollama first: `curl -s localhost:11434/api/generate -d "{\"model\":\"llama3.1:8b\",\"keep_alive\":0}"`).
  Procedure: for each rule in `_command` (`kind == "end"|"heard"|"again"`, `empty`, `multi`, `diag`, `act`, `command_reply`) disable it in a scratch copy
  and run `test_jarvis`; if the suite still passes, add a test next to the courtesy tests (pattern: `talk(99, words=...)` then assert `asked[-1]` and `len(prompts)`).
- Cleanup NOT yet done (all mine, none needed for live use): `%LOCALAPPDATA%\Temp\jarvis-gate\` (gate scripts, scratch mirror, semi-live results, backups),
  branch `jarvis-live` (`git branch -d jarvis-live`), the worktree when finished (`git worktree remove ..\RainmeterSpaceship-refactor`),
  untracked `tasks/voice-measurements/` (voice scratch; the earlier plan said delete when done). Do not touch the other session's files.
- Merging 6d/6e/(6f) into main is a normal merge now (main moved), not a fast-forward; do it only after the checks above and after the live test.

## 5. What has NEVER been live-tested (the point of the next session)
Voice (`JarvisVoiceSmooth` is ON by default in code; `JarvisVoiceSmooth=0` in `Settings.inc` restores the old path):
1 time from end of speech to first word; 2 no gap/click/glitch between chunks, pauses sound chosen not random; 3 "stop" and barge-in cut within about one 40 ms block;
4 headphone level (`JarvisHeadphoneLevel`, default 60 %); 5 pop-up text types at speaking pace; 6 fillers ("Searching your notes.") join the reply cleanly;
7 busy/odd output device: log line `player: WASAPI not available` and speech still works; 8 does he sound OK vs before (speed/voice by ear, never decided: A/B script `tools/voice_ab.py`).
Behaviour added by the semi-live work: no invented readings (`I don't have that reading right now, sir.`), can't-do lines (payments, bookings, messages,
printing, other devices), crisis line (do not test casually), a lone "yes" with nothing asked, "show/close the log", "sir" used sparingly and never forced,
Mr. Sorsa only on serious turns, chat answers capped (3 sentences), once-per-night late-night remark, room-talk handling in the 3 s open ear
(`ear:` log lines; "?" or "you" counts as for him, the user's S2-10 design).

## 6. Open product work (none started, all need the user's yes)
Persona A1/A2/A3/A7 (dry understatement, calm-under-crisis, formal-crisp, signature phrases) in `tasks/jarvis-persona-plan-2026-11-03.md`, bank + baseline
ready (`semi_live_persona.jsonl`; 8B persona cost ranged 8-19 across runs of the same code, 3B 28-37). S3 voice/speed choice by ear, V13 high-pass/limiter, B3/B4/B8 model options, B5-B9.
Known gaps: offers ("Would you like me to...") still happen; 8B sometimes ignores HUD data; `DID` has no sentence for the `mood` action (he says "mood").

## 7. How to investigate a complaint (fast)
Log: `Skins\Spaceship\@Resources\Data\jarvis.log` (counts and route names only, never your words). Useful lines:
`route: <lane>.<kind> <action> via <rule|context|ai-reread|model>, total X s -> <result>`, `timing: reply start -> first audio`,
`timing: end of speech -> reply start`, `voice gaps: N chunks, seams [..] ms, K under-runs`, `player: ...`, `kokoro loaded (... GPU|CPU)`,
`ear: ...`, `control: ended by you`, `autocorrect: ...`, `interpreter: ...`, `turn failed: ...`.
Reproduce a typed phrase without audio or Windows actions (temp folder, tripwires on destructive calls, never your real Data):
write a one-line case file `{"id":"x1","tags":["live"],"turns":[{"say":"what I said"}]}` then
`%LOCALAPPDATA%\SpaceshipHUD\venv\Scripts\python.exe -B tools\semi_live.py --model llama3.1:8b --cases x1.jsonl --seed 7 --out out.jsonl`
(run from the Jarvis folder; Ollama must be running; unload the model afterwards). Score with `tools\score_semi_live.py out.jsonl`.
Routing question, no model: `tools\golden_routes.py` helpers or `route()` via `tests`. Hearing/wake problems: `tools\hearing_eval.py`.
Gate (always on a scratch copy that mirrors repo depth, env `TZ=ABC+12`): `python -B test_jarvis.py` with the venv python AND `py -3`,
`python -B test_host_pipe.py`, `python -B tests\run_all.py`, `python -B tools\golden_routes.py --check`, `python -B tools\golden_replies.py --check`.
The gate scripts I used are in the temp folder above (may be gone: rebuild from ARCHITECTURE.md "Gates").

## 8. Traps (found the hard way)
Never run a test or tool that can reach the real recycle bin, shutdown, sleep or file deletion (use the tripwire guards in `tools/semi_live.py`).
jarvislib reads `RES` from `sys.argv[1]` at import: always point it at a temp folder or you write the real log. Regexes contain `\b`: edit with a tool that
does not eat backslashes, then grep for 0x08. Tests fake by name across all modules (`Everywhere`): a moved function must stay bound in every module that used it.
Mutation/scratch copies must start from the real file every time (I once saved a mutated copy as the baseline). Free RAM was 4-6 GB of 31 GB while Ollama
had the 8B model loaded: unload it after runs. Other processes on this PC (flight_sim venv, uv, VS Code) are the user's: never kill them.
The Kokoro voice may fall back to the CPU if CUDA is blocked by an Application Control policy; say which one a measurement used.

## 9. Rollback
Live use: set `JarvisVoiceSmooth=0` in `Settings.inc` (old voice path). Code: main's refactor commits are `7ba312b..88b27e0` (revert newest first),
or check out branch `jarvis-live` (the exact pre-refactor code) in a clean tree. Branch work: delete `refactor/jarvis-pipeline` and remove its worktree.
