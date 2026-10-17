# JARVIS: Architecture and Stabilization (Phase 3)

Written 2026-10-15 on branch `chore/jarvis-baseline-and-performance`. It covers the code as of the
commit that adds this file. Nothing here was copied to the live skin or deployed.

Status words used below:
- **verified**: a check was run in this session and its output was read.
- **mocked**: covered by `test_jarvis.py` with fakes (no real mic, Ollama, speakers or OS action).
- **manual**: still needs the user's live test (see section 7).

## 1. Architecture overview

Three processes talk only through small text files in `Data\`:

| Process | Code | Job |
|---|---|---|
| Rainmeter HUD | `Scripts\jarvis.lua` (+ the skin .ini files) | Shows JARVIS's state, the log pop-up, and sends click commands |
| JARVIS service | `Jarvis\jarvis.py` + `Jarvis\jarvislib\*.py` | Wake word, listening, routing, actions, the LLM and speech |
| ShipCore helper | `Scripts\core.ps1` builds and starts `ShipCore.exe` | Writes `windows.txt` (open windows) and other system readings |

`jarvis.py` (1472 lines, down from about 2600) is now the integrator only. It holds the turn loop (`turn` /
`exchange`), the room and ear checks, run_action and undo, reminder replies and alarms, wake word code and
training, and `main`. Everything else lives in `jarvislib\`. A module imports only the standard library
and modules above it, and never imports `jarvis.py`:

| Module | Owns |
|---|---|
| base | paths, Data\ file names, settings, log, State (jarvis.txt writer), the instance lock, the pop-up log, `write_atomic` |
| gpu, hearing, stopwords | GPU checks; Whisper and its filters; Vosk stop words |
| tts, speech, audio, mic | voices; the speak queue and fillers; speaker endpoint; mic listening, duck / unduck |
| llm | Ollama: models, warm, `chat_stream`, `chat_json` (the one non-streamed JSON call) |
| notes, search | Obsidian vault text search; the ChromaDB vault index and `smart_search` |
| calc | time, units and maths answers |
| actions, confirm, stopkey | the OS actions with exit-code checks; the one place a "yes" is judged; the End-key stop |
| turnstate, todo | the turn's short-term memory (undo, last, did); the to-do note |
| reminders, diag | the reminder store and parsers; HUD sensor readings |
| meaning, memory | meaning match (embeddings); the facts, topic and gist stores, recall and compaction |
| routing | the deterministic router `route`, autocorrect, claim / unbuilt guards, the AI fallback `interpret` |
| prompt | the system prompt, context blocks and info-question lanes |

## 2. Request lifecycle (one spoken command)

1. **Wake.** `wake_loop` hears the wake word, or the HUD writes `WAKE <time> <tier>` to `jarvis_cmd.txt`.
   `main` runs `turn(tier)` on a thread. A click command older than 30 s is ignored.
2. **Hear.** `mic.listen` records until silence and `hearing.transcribe` runs Whisper. The phantom, loop
   and repeat filters drop noise phrases.
3. **Directed?** `directed` / `room_talk` decide whether the words were meant for JARVIS.
4. **Route.** `routing.route(text)` is plain code (regex plus tables) and returns `(kind, action, target)`.
   Only when nothing matches and the words look like a command does `interpret` ask the LLM. The answer must
   be on a whitelist, and it goes back through `route`. A protected action is never taken from the LLM.
5. **Act.** `command_reply` calls `run_action` through the `ACTIONS` table. A DANGER action (shut down,
   restart, sleep, ...) first calls `ask_yes`, which asks once, waits up to 15 s and needs a confident yes
   (`confirm.confirmed` plus a Whisper score of at least -1.0) with no cancel. The action functions check
   exit codes. Only a real success is recorded for undo and reported as done.
6. **Chat.** Other talk gets `prompt.system_prompt`, plus the recalled memory and the active window, and
   goes to `llm.chat_stream`. Sentences are spoken as they arrive (`speech.speak_all`).
7. **Report.** `base.State` writes `jarvis.txt` for the HUD, `convo_add` adds to the pop-up log, and the
   service log gets only word and character counts, never the words.

## 3. Cross-language contracts

| File (Data\) | Writer | Reader | Format |
|---|---|---|---|
| jarvis.txt | base.State (atomic) | jarvis.lua `readState` | `T`, `STATE`, `LEVEL`, `SAY`, `ERR`, `POP <n> <open/close>` lines |
| jarvis_cmd.txt | jarvis.lua | jarvis.py `main` | `<WORD> <unix time> [tier]`. Words: WAKE, CANCEL, REINDEX, FORGET, TRAINWAKE, QUIT |
| jarvis_env.txt | HUD | speech.muted | `MUTED 0/1` |
| jarvis_log.txt / jarvis_live.txt | base.convo_add / live (atomic) | log pop-up | `U|unix|text`, `J|unix|text` |
| jarvis_duck.txt | mic.duck | mic.unduck | the volume before ducking |
| windows.txt | ShipCore | actions.act_close | `T <unix>` then `W <exe>` lines |
| Settings.inc | the skin | base.settings / setting | `Jarvis*` keys (read only by Python) |

These were checked key by key by the contracts review this session (all matched). SAY and ERR are written
but not drawn by jarvis.lua; that is harmless and left as is.

## 4. State ownership

- Turn state (undo, last, did, offer): `turnstate`. Pending yes: local to `ask_yes` (never shared and never
  inherited by a later turn).
- Active talk window (`history`, `last_turn`): `jarvis.py` (the turn loop changes it).
- Stores on disk: facts, topics and gist in `memory`; reminders in `reminders`. All whole-file saves go
  through `base.write_atomic` (a .tmp file, then one rename). The daily gist add is an append (see section 8).
- HUD-visible state: `base.State` only.
- Models: `llm` (Ollama) and `hearing` (Whisper). `unload_idle` in `jarvis.py` frees them when idle.

## 5. Testing report

All tests ran in a scratch copy, never in the live skin.

| Check | Command | Result |
|---|---|---|
| Unit and flow tests | `t.sh` → venv `python test_jarvis.py` (706 asserts) | **verified**: `test_jarvis: OK` after every commit |
| Route regression | `check_route.py` HEAD-before vs working tree, 65 phrases | **verified**: 0 routed differently after every commit |
| Compile | `py_compile` on all Jarvis .py files (inside t.sh) | **verified** |
| Control characters | scan inside t.sh | **verified**: none |
| Lua syntax | lupa `loadstring` on `Scripts\jarvis.lua` | **verified**: OK |
| PowerShell syntax | `Parser::ParseFile` on `Scripts\core.ps1` | **verified**: 0 errors |

Mocked in test_jarvis: the AI router and Ollama (`http_json` raises or returns fakes), the mic and Whisper
(`hear` / `transcribe` fakes), `ctypes.windll` for sleep and lock, `subprocess` for app open / close,
and the window list for close.

## 6. Safety verification report

| Rule | How it holds | Status |
|---|---|---|
| The LLM can't authorize an OS action | `interpret` output is whitelisted and re-routed; protected kinds are dropped | mocked + read in review |
| A yes belongs to one pending action | `ask_yes` keeps its state local, asks once, 15 s expiry, no inheritance | mocked |
| An unsure yes doesn't count | Whisper score below -1.0 → no (fixed this phase) | mocked (−1.5 no, −0.3 yes) |
| A failure is not reported as success | `run_ok` checks exit codes; close needs a fresh window list without the app (fixed this phase) | mocked (stale and unreadable lists → not closed) |
| No real shutdown, restart or sleep in tests | all are faked; none was run | verified by reading the tests |
| No transcripts in jarvis.log | only word and character counts (fixed this phase) | mocked |
| No shell injection | no `shell=True`; TTS text goes to PowerShell on stdin | read in review |

## 7. Known limitations (left on purpose, or still to test live)

- Manual only: a real launch from the skin, the mic, Ollama, the speakers, the ShipCore build, and the
  STEALTH pop-up and auto-start fixes. These run in the user's combined live test after Phase 7.
- Self-echo: the speakers could in theory feed a "yes" back. The confidence check reduces this. Left as is.
- Sleep on Modern Standby falls back to turning the screen off and says "Done." (by design, S2-11).
- ERR stays on the HUD until the next turn after a quiet (no pop-up) problem. Accepted.
- W-a: Lua writes `jarvis_cmd.txt` in place. A half-read command is ignored (bad stamp), so the cost is one
  lost click.
- W-c: the daily gist add is an append. A crash mid-write can leave one cut-off fact line.
- W-d: seven Settings keys are read by Python but have no skin control yet.
- Non-ASCII mic names were not checked.
- `act_sleep` logs `ctypes.GetLastError()` without `use_last_error=True`, so the logged number may be wrong.
  It only affects the log.

## 8. Final change summary (this phase)

| Commit | Change |
|---|---|
| f89e700 | S1: no transcripts in the log; an unsure yes is a no; close checks a fresh window list (+ tests) |
| 30ad4a1 | S2: the HUD reads state in STEALTH (pop-up works); one-shot auto-start; unduck on QUIT; core.ps1 keeps the old ShipCore.exe when a build fails |
| 4007212 | S3: one atomic writer (`write_atomic`, fixes W-b) and one JSON chat call (`chat_json`) |
| 23e296f .. 646dc29 | R8-R14: reminders, diag, meaning, search, memory, routing and prompt moved verbatim into jarvislib |

Rollback: `git revert <sha>` for any single commit, newest first. Each commit is tested on its own.
