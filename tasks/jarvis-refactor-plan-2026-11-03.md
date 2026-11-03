# JARVIS refactor plan: one pipeline, small parts, nothing scrambled (PLAN ONLY, nothing changed)

Written 2026-11-03 while the semi-live gate for the voice/B1/B2 work was running. Goal: make `Skins/Spaceship/@Resources/Jarvis/`
easy to read, check, edit, test and extend, with ONE path for each kind of work, so a change in one place cannot silently
change another. Hard rule from `CLAUDE.md`: **don't break anything**. This is a behaviour-preserving refactor: every phase must
leave all tests and both semi-live banks exactly where they were (or better), and every phase must be revertible on its own.

Labels: **[measured]** counted from the repo today, **[code]** read in the code, **[guess]** my judgement, to be checked.

## 0. DO NOT START until
1. The user's live test of the current work (voice smoothness default 1, B1, B2, B10/B11) is finished and its findings are fixed.
   A refactor on top of an unverified change makes every live bug ambiguous ("new code or moved code?").
2. The working tree is committed (user's word) or at least stashed to a branch, so phase 0 starts from a known commit.
3. The user has said yes to this plan (section 12 lists the questions).

## 1. What is wrong today (evidence)
| # | Problem | Evidence |
|---|---|---|
| P1 | One giant function holds the whole turn | `exchange()` in `jarvis.py` is ~410 lines (l.868-1281) [measured]; it mixes listening, transcribing, rules, confirmations, the model call, speech, history, memory and logging. Early `return`s inside a `try` already caused one bug (the comment "a `return` inside the try below would drop it", l.870) |
| P2 | Routing is a 320-line regex ladder | `_route_rest` (routing.py l.433-754) [measured]: order of `if`s IS the behaviour; adding a rule can shadow another. `route()` returns a positional 4-tuple `(kind, action, target, prompt)` whose meaning depends on `kind` |
| P3 | Several overlapping "is this for him / what does it mean" pipelines | rules (`route`), context follow-ups (`active`, `percent_follow`, `level_fix`), AI reread (`interpret`, `ask_ai`), `directed()` for the open ear, `for_me()`, `fix_route()`, `no_data()`, now `no_ability()`, plus `Decision` namedtuple (`REDESIGN slice B`) that only part of the code uses [code] |
| P4 | Reply post-filters are a hand-chained generator | `polish(grounded(no_hope(no_claims(sentences_from(stream)))))` (jarvis.py ~l.1214) [code]. Each stage re-implements "partial first piece", "collected[:] =" mutation of a shared list, and FIXED_LINES pass-through; order matters and is only documented in comments |
| P5 | Fixed ("canned") replies live in 5+ places | `routing.py` (CANT, CLAIM_LINE, NEAR_MISS, OTHER_DEVICE), `mood.py` (CRISIS_LINE, NO_READING), `prompt.py` (LIVE_FACT_LINE, NO_ABILITY), `jarvis.py` (inline strings "Done.", "Cancelled.", "That didn't work."), `speech.py` (FILLERS). Each must also be added to `FIXED_LINES` by hand or `polish` mangles it [code] |
| P6 | Hidden global state | ~42 module-level mutable lists/dicts across jarvis.py and jarvislib [measured] (`history`, `last_turn`, `recent`, `offer`, `undo`, `did`, `last`, `cancel`, `busy`, `turn_id`, `saying`, `name_until`, `_engines`, `_filler_*`, `player`...). Tests reach them with `j.X = fake` |
| P7 | Test seam is a monkeypatch trick | `test_jarvis.py` (4.7k lines, one script, plain asserts) uses class `Everywhere` to overwrite a name in jarvis.py AND every jarvislib module [code]. Consequences seen this session: fakes left behind by earlier tests (`j.sentences_from`, `j.speak_all`, `j.prepare_fillers`, `j.time.sleep`) broke later tests; new tests had to capture "REAL_*" handles at the top. One test run is ~90 s and cannot be run in parts |
| P8 | Settings read by string everywhere | `setting("JarvisX", "default")` with the default repeated at each call site (e.g. `JarvisVoiceSmooth`, `JarvisFirstWords` read in 2 modules). A default can differ between call sites; there is no list of valid keys [code] |
| P9 | Speech is split across 3 layers | chunking (`sentences_from`), queue/pacing (`speak_all`, `_speak_queue`), playback (`play_samples`, `Player`), plus `filler()`; `jarvis.py` imports internals (`_speak_queue`, `_filler_audio`, `_filler_thread`, `_filler_voice`) [code] |
| P10 | `jarvis.py` is also the module everything imports names from | 30 `from jarvislib...` import lines re-exported so tests/other code use `jarvis.X`; the refactor R1 (jarvislib split) stopped half-way [code] |
| P11 | Rule text/regex duplicated between runtime and tests/tools | scorer `CLAIM` regex vs routing `CLAIM`; `make_cases.py` copies |
| P12 | No single trace of "which path answered" | `way` dict + `log("route: ...")` exist but only as a log line; no structured record tests can assert on |

## 2. Target design (what "well made" means here)
Principles: (a) one owner per concern, (b) data flows forward through a few explicit stages, never sideways through globals,
(c) every stage is a plain function of its inputs that can be tested without audio, Ollama, the clock or the HUD,
(d) anything that must always hold (safety, never-claim-an-action, crisis, injection) is code in ONE stage, not text in a prompt,
(e) adding a feature = adding one file/entry in a registry, not editing the turn.

### 2.1 The turn as a pipeline of stages (replaces `exchange()`)
```
Input stage     listen/transcribe/typed  -> Utterance(text, source, onset, follow, woke, t_*)
Gate stage      stop words, stealth, late-no-name, open-ear `directed()`           -> proceed | drop | ask
Understand      ONE `understand(utterance, session) -> Intent` (see 2.2)
Execute         Intent -> Outcome via the action registry (confirm/undo handled here, once)
Answer          Outcome needs words? -> fixed line | HUD info | model (stream)       -> ReplyStream
Reply filters   ONE `ReplyPolicy` applied to the stream (see 2.3)
Speak           ONE `Voice` facade (see 2.4)
Record          history, memory, undo, did, logging from the Outcome only (see 2.5)
```
Each stage takes and returns small immutable dataclasses (`Utterance`, `Intent`, `Outcome`, `Reply`). `exchange()` becomes a
~40-line driver that calls the stages in order and owns the `try/finally` (busy lock, state reset, one route log line).
No stage calls a later one; no stage reads another stage's globals.

### 2.2 One understanding path with an explicit result type
- `Intent` dataclass: `kind` (enum: ACT, REMIND, LEVEL, MEDIA, MEMORY, INFO, CHAT, SAY, END, UNDO, ...), `action`, `target`,
  `prompt`, `via` (rule | context | ai-reread | fixed), `lane`, `reason`.  Replaces the positional 4-tuple and the half-used `Decision`.
- `understand()` is a ordered list of **named rule objects** (`Rule(name, match, build, priority)`), not an if-ladder. The
  registry is a plain list in `jarvislib/understand/rules_*.py` grouped by area (volume, media, timers/reminders, apps, system,
  memory, mood, info, can't-do). Order is explicit data (priority number) and printed by a test, so shadowing is visible.
- Context follow-ups (`active`, `percent_follow`, `level_fix`) and the AI reread become **rules/stages in the same list** with
  their own priority, instead of side paths called from `exchange()`.
- A **golden route table** (`tests/golden_routes.jsonl`: utterance -> kind/action/target/via) is generated from the CURRENT
  code in phase 0 over every phrase in both semi-live banks, the unit tests and `AI_CUES`; the refactor must reproduce it
  byte for byte. That is the main safety net for the regex ladder.
- `no_data` / `no_ability` / `LIVE_FACT` / unbuilt capabilities become rules of kind SAY with a shared `Fixed` registry.

### 2.3 One `ReplyPolicy` for what he may say
- `jarvislib/reply/` : `fixed.py` (every canned line, ONE registry: `Fixed.register(key, text)`; `FIXED_LINES` is derived, never
  hand-edited), `filters.py` (claims, promises, hope/stock, offers, grounded readings, miscounts, sir/length caps), `policy.py`
  (the ordered chain + the "partial first piece" contract written once).
- Each filter is `Filter.feed(piece, ctx) -> list[str] | REPLACE(fixed_key)` with a tiny state object instead of a generator
  that mutates a shared `collected` list. The chain runs them in a fixed order that is defined in one tuple and tested.
- A filter can only (1) pass, (2) edit, (3) end the reply with a registered fixed line. It cannot speak or log.
- The scorer imports the SAME regexes (`from jarvislib.reply import CLAIM`) so tools and runtime cannot drift (P11).

### 2.4 One `Voice` facade for everything audible
- `jarvislib/voice/`: `chunker.py` (sentences_from + smooth chunker, pure), `synth.py` (tts engines + fallback consistency),
  `player.py` (stream), `pacing.py` (pauses, merge, gap log), `fillers.py`, `speaker.py` (the `Voice` class:
  `say(stream_or_text, *, kind) -> Spoken(text_that_got_out, finished: bool)`).
- `jarvis.py` and tests only ever call `Voice.say(...)`, `Voice.stop()`, `Voice.filler(key)`. The legacy stream-per-chunk path
  stays as `LegacyPlayer` behind the same interface until the user retires `JarvisVoiceSmooth=0`.
- `Spoken` carries what really got out (B11) so history/follow-ups never need to guess.

### 2.5 One `Session` object instead of loose globals
- `Session` (dataclass, created once in `main()`): `history`, `last_turn`, `recent`, `offer`, `undo`, `did`, `last`, mood/timed
  mood, pending confirmations, the stop `cancel` event, the `busy` lock and a monotonically increasing `turn_id`.
- Stages receive `session` explicitly. Module-level mutable state is deleted module by module (phase 6), each time with a test
  that two `Session`s cannot see each other.
- **Stale-turn guard (B10) becomes structural:** every stage receives the `turn_id` it started with and `session.alive(turn_id)`
  is checked before any side effect (action, speech, memory write, history write). A late result from an older turn is dropped by
  construction rather than by scattered `if cancel.is_set()`.

### 2.6 Settings with a schema
- `jarvislib/config.py`: `SETTINGS = {key: Setting(default, type, range, doc)}` in one table; `cfg.voice_smooth` etc. are typed
  accessors; unknown keys are logged once. The default lives in ONE place (code), `Settings.inc` stays the user-facing file and is
  not edited by the refactor. A test asserts every `setting("X", ...)` call site in the repo uses a key present in the table
  (static grep test) and that no two sites pass different defaults.

### 2.7 Actions and capabilities as a registry
- `Action` table already exists (`ACTION_TABLE`); extend it into the single capability list: name, handler, confirm policy
  (none/ask/yes-word), undo handler, `did` text, done-line, sample phrases (used by the router's context scoring and by docs/help),
  and a `faked_in_tests` guard. "What he can do" in help, the can't-do lines, `UNBUILT_CAPS`, and the CLAUDE-READ-FIRST dry-run grep
  all read from this table, so a new feature = one entry + its rule(s).

### 2.8 Test layout
- `tests/` package: `test_route.py` (golden table), `test_reply_filters.py`, `test_voice_chunker.py`, `test_player.py`
  (fake sounddevice), `test_pacing.py`, `test_session.py`, `test_actions.py`, `test_exchange_flow.py` (end-to-end with all stages
  faked), `test_settings_schema.py`. Plain functions + a tiny runner (stdlib `unittest` or the existing assert style); each file
  runs alone in seconds, and `run_all.py` prints "tests: OK" exactly like today.
- **Fakes are injected, not monkeypatched:** stages take their collaborators (`clock`, `audio_out`, `llm`, `hud`, `os_actions`)
  as parameters/`Session.deps`; a `FakeDeps` in `tests/fakes.py` replaces `Everywhere`. The destructive-call fakes required by
  `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md` live in ONE module (`fakes.os_actions`) that fails the test if the real function is reachable.
- The old `test_jarvis.py` is kept and still run until the last phase; each moved test is MOVED (not rewritten) so assertions
  stay identical, and the old file shrinks to nothing.

## 3. Phases (each = its own branch/commits, own gate, own rollback)
General rules for every phase: smallest change; one concept per commit; no behaviour change (gate = identical golden outputs);
`git revert` of the phase's commits must restore the previous behaviour; update the handoff log; commit only on the user's word.

**Phase 0: safety net (no product code changes).**
0.1 Create branch `refactor/jarvis-pipeline` from a committed tree. Copy this plan's "session start" block (section 10) into the handoff.
0.2 `tools/golden_routes.py`: run `route()` + `understand` helpers over a corpus (both banks + test phrases + AI_CUES + 300 generated
    variants with ASR noise) with all OS/ctypes/subprocess guarded (reuse the tripwires from `tools/semi_live.py`), write `golden_routes.jsonl`.
0.3 `tools/golden_replies.py`: run the full reply chain (`sentences_from` -> filters) over recorded model streams from
    `semi-live-results/*.jsonl` (replays text, no model), write `golden_replies.jsonl`. Replays are deterministic.
0.4 Baselines recorded in the handoff: test_jarvis OK x2, test_host_pipe failed 0, semi-live 8B/3B main/fresh/persona cost, first-sentence p50.
0.5 Static inventory script `tools/inventory.py`: lists module-level mutable names, `setting(` call sites with defaults, canned strings,
    `j.X =` fakes used by tests. Output committed; it is the checklist the later phases tick off.
Acceptance: golden files stable across two consecutive runs on the unchanged code.

**Phase 1: settings schema (`config.py`).** Table + accessors; replace call sites one module at a time with `cfg.<key>`;
the old `setting()` stays as a thin wrapper so partial migration is safe. Static test for duplicate defaults. Risk: a default
that differed between sites (found by the inventory) must be resolved by keeping the value that is live today (grep Settings.inc
and the log), never a new one.

**Phase 2: fixed-line registry + `ReplyPolicy`.** Move canned strings into `reply/fixed.py` (same text, same objects imported under
the old names so nothing else changes), derive `FIXED_LINES`. Then convert the filters one at a time into the `feed()` interface
behind the existing generator names, golden_replies identical after each. Scorer switches to the shared regexes. Risk: generator
laziness (the first piece must still be released immediately; the voice timing depends on it) -> a test with a stream that
blocks after the first piece proves the first chunk is yielded before the second is read.

**Phase 3: voice package.** Move code only: `speech.py` -> `voice/{chunker,pacing,speaker,fillers}.py`, `tts.py` -> `voice/synth.py`,
`player.py` -> `voice/player.py`; `jarvislib.speech` keeps re-exporting the old names for one phase. `Voice.say` returns `Spoken`.
Then replace the three jarvis.py internals imports. Gate: all voice tests (fake sounddevice) + `tools/voice_gaps.py` numbers equal
to the post-S2 numbers (47 chunks, mid seams median 65 ms, clause 190, sentence 340) + silent real-device smoke.

**Phase 4: understanding as rules.** Introduce `Intent`; convert `route()`'s tuple at the boundary with an adapter so the old
callers keep working; move rules out of `_route_rest` in groups (volume, media, timers, apps...) keeping their ORIGINAL ORDER via
priorities; golden_routes must be identical after every group. Then fold context follow-ups and the AI reread into the same list.
`directed()` and `for_me()` stay separate (they answer a different question: "was it for him") but move to the Gate stage.
Risk: regex order dependence -> priorities are generated from the current order and a test asserts the printed order equals the file.
Never "tidy" a regex in the same commit as moving it.

**Phase 5: Session + stale-turn guard.** Create `Session`; pass it into the stages; move one global at a time (start with the
leaf ones: `did`, `undo`, `recent`, `offer`, `last`; then `history`/`last_turn`; last `cancel`/`busy`/`turn_id`). After each, the
inventory count of module-level mutables must drop and the full gate must pass. `session.alive(turn_id)` replaces ad-hoc cancel checks
only where a test proves equal behaviour (stop word, End key, new click, barge-in, late AI-reread, late action confirmation).

**Phase 6: slice `exchange()`.** Extract stages in this order (each extraction is a pure move + the stage gets a unit test):
Record (history/memory/log), Speak call, Answer (fixed/info/model), Execute, Understand call, Gate, Input. `exchange()` shrinks each
time; the final driver is <= ~60 lines. Keep the `left`/`way` side channels until the last step, then replace them by the
`Outcome` return value (note the existing warning about `return` inside `try`).

**Phase 7: actions registry + help/can't-do from one table.** Generate `help_cspace.txt` sections and the can't-do list from
`ACTION_TABLE`; static test that every action has an undo or an explicit `no_undo` reason and a `did` text.

**Phase 8: tests re-homed.** Move tests file by file into `tests/`, replacing `Everywhere` with injected fakes; delete `Everywhere` last.
Gate: assertion count not lower than before (count `assert` statements before/after; a moved test with fewer asserts is rejected).

**Phase 9: tools consolidate.** `tools/semi_live.py` runs the same stages through `FakeDeps` instead of patching `jarvis.*`;
banks and scorer unchanged. Remove the `RES = sys.argv[1]` import-time trap (see section 6).

## 4. Gates (run after EVERY phase and after every risky commit)
1. Scratch mirror (`<scratch>/Skins/Spaceship/@Resources/...` + `<scratch>/contract`), env `TZ=ABC+12`.
2. `venv python test_jarvis.py` -> "test_jarvis: OK"; `py -3 test_jarvis.py` -> OK; `venv python test_host_pipe.py` -> "failed: 0";
   plus the new `tests/run_all.py` once it exists. Never claim a pass that was not run.
3. `tools/golden_routes.py --check` and `tools/golden_replies.py --check`: zero diffs (or each diff explained and approved).
4. Semi-live llama3.1:8b and llama3.2:3b: main, fresh, persona banks, seed 7: cost <= baseline, tripwires 0, first-sentence p50 <= +0.15 s.
   (Phases 1, 3, 7, 8, 9 do not touch model-facing text, so 8B only; phases 2, 4, 5, 6 run both models.)
5. Voice phases: `tools/voice_gaps.py` equal, silent real-device smoke (zero amplitude), no audible test without the user's yes.
6. Read the replies, not only the cost (cost cannot see "sounds odd").
7. `git diff --stat` shows only the files the phase is allowed to touch; nothing from `GodMode/`, `Refrences-Art/`, `SpaceshipApp/`, UI.

## 5. Risk register (what can go wrong and what prevents it)
| Risk | Prevention |
|---|---|
| Behaviour change hidden in a "move" | Move and edit in separate commits; golden route/reply files; diff of moved code is whitespace/import only (`git diff --color-moved`) |
| Regex order changes route outcomes | Priorities generated from current order; printed-order test; one group per commit |
| Lazy generators become eager (first word delayed) | Blocking-stream test for first-piece latency; first-sentence p50 gate |
| Circular imports after splitting | Dependency direction fixed: `config` <- `reply`,`voice`,`understand`,`actions` <- `session` <- `stages` <- `jarvis.py`; a test imports every module alone in a fresh interpreter |
| Test fakes leaking between tests | Fakes injected per test via `FakeDeps`; each test file runs in its own process in `run_all.py` |
| A real destructive call reached by a moved test | The fakes module asserts the fake is installed; dry-run grep (CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md) before running any new test; `tools/semi_live.py` tripwires reused in the golden scripts |
| Barge-in/stop timing regresses (shared playback loop) | Keep the 40 ms block loop and abort tests with the fake stream; fake-clock test; never restructure `Player.play` in the same phase as stages |
| Global state removed but a thread still uses it (watchdog, alarm, wake loop, barge-in threads) | Inventory lists thread entry points (`watchdog`, `alarm`, `index_loop`, `wake_loop`, `barge_in`, filler/producer threads); each gets the `Session` explicitly and a test; migrate the thread functions last |
| Live process runs the repo copy (CSpace) | Refactor on a branch; the live copy only gets a phase after the user's yes; CSpace not running at merge time is checked like in the last commit |
| Settings default drift | One table; static test; keep today's live values |
| Time/cost blow-up | Phases are independent after 0; any can be dropped. Order by value/risk: 0, 1, 2, 3 (cheap, safe), then 5/6, then 4 (riskiest), 7-9 last |
| Context/token blow-up for the working session | Work from the inventory + one module at a time; never read `jarvis.py` or `routing.py` whole (grep to jump); keep this plan and the handoff as the memory |

## 6. Known traps in this repo (found the hard way this session)
- Python in a bash heredoc collapses `\\` to `\`: regexes with `\b` become backspace characters (0x08). Edit regex lines with the Edit
  tool, then check `grep -c $'\x08'` on the file.
- `jarvislib.base.RES = sys.argv[1]` at import time: a tool that keeps its own CLI args (`--cases x`) makes `RES="--cases"` and silently runs
  with no settings (Windows voice, stray `--cases/` folders). Clear `sys.argv[1:]` before importing jarvislib, or fix it in phase 9.
- Tools that import jarvislib without a temp RES append to the real `Data\jarvis.log`; use `sys.argv[1] = tempfile.mkdtemp()`.
- `time.sleep` / `time.time` are monkeypatched on the shared `time` module by earlier tests and not always restored; tests that need real
  waiting use `threading.Event().wait`.
- Earlier tests replace `j.speak_all`, `j.sentences_from`, `j.prepare_fillers`, `j.play_samples`: capture the real function at the top
  of the file (`REAL_*`) or, better, stop patching (phase 8).
- CUDA for Kokoro can be blocked by an Application Control policy in some runs (CPU fallback); report which was used.
- Git on this repo warns LF->CRLF; do not "fix" line endings in a refactor commit.
- `Data\`, logs, weights, voice clips, `semi-live-results`, Settings.inc are never staged. Other sessions own `SpaceshipApp/`, `GodMode/`,
  `Refrences-Art/`, `Images/Render/`, `tools/blender/`, `tools/contract_check.py`.

## 7. What "easier to check over" means in practice (deliverables)
- `docs/jarvis-architecture.md`: one page, the stage diagram, the module map, "where do I add X" table (a new command, a new canned
  line, a new filter, a new setting, a new action, a new voice behaviour, a new test).
- Every module <= ~400 lines, one responsibility, a docstring stating inputs/outputs and what it must NOT do.
- `tools/inventory.py` output kept current (counts of module-level mutables, setting call sites, canned strings must only go down).
- Structured trace per turn (`Outcome.trace`: stages passed, rule name that matched, filter that edited, fixed key used), logged as ONE
  line (keeps today's `route:` line format as a prefix so existing log readers still work). Tests assert on the trace, not on log text.

## 8. Feature slots the design must make cheap (acceptance for "easy to add features")
Each should be doable by adding files/entries only, with no edit to `exchange()`/the driver: a new voice command (rule + action entry),
a new canned reply (Fixed key), a new reply filter, a new info source (HUD block + example phrases), a new setting, proactive lines
(a separate `Triggers` stage that can only enqueue Outcomes through the same Execute/Speak path), routines/macros (a registry entry that
expands to existing actions), a new TTS engine (a `synth` backend), a second language. Prove it at the end by adding one throwaway
example of each in a test-only plugin and deleting it.

## 9. Order of value (if time is short)
1. Phase 0 + 1 + 2 (safety net, settings table, one fixed-line registry + one filter chain): removes the most "scrambling" for the least risk.
2. Phase 3 (voice package) and 5 (Session + stale-turn guard): fixes the overlapping speech paths and the global state.
3. Phase 6 (slice `exchange()`) and 4 (rules): the biggest readability win, the highest risk, done last with the strongest net.
4. Phases 7-9: polish.

## 10. Session start block (copy this into the new session's first message)
1. Read, in order: `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md`, `CLAUDE.md` (repo root), `tasks/HANDOFF-jarvis-semi-live.md` (sections 2-6, newest log entry),
   this file, `tasks/jarvis-voice-plan-2026-11-03.md` (section 3 and the appendix: code map).
2. Confirm the live test is done and the tree is committed (section 0). If not, stop and ask.
3. Work only in `Skins/Spaceship/@Resources/Jarvis/` and `tasks/`; never touch UI, Rainmeter skins, `Settings.inc`, or files other sessions own.
4. Scratch mirror + test commands: see the handoff section 4 ("Test commands"); done = `test_jarvis: OK` twice and `test_host_pipe` `failed: 0`.
5. Start with Phase 0 only. Write the plan-per-phase block (goal, scope, non-goals, acceptance, validation, risks, rollback) BEFORE each phase,
   log numbers in the handoff after each, commit only when the user says so.
6. Use Grep to jump into `jarvis.py` / `routing.py`; do not read them whole.
7. Report real command output; never claim a test passed that was not run.

## 11. Rollback
Per phase: `git revert` the phase's commits (they are self-contained and ordered). Whole refactor: delete the branch; `main` never
carried it. During a phase the old names are re-exported, so a half-finished phase can be abandoned by reverting only its last commits.

## 12. Questions for the user (before phase 0)
1. OK to run this on a branch and merge phase by phase (recommended), or do you want one long branch?
2. May tests be restructured into `tests/` (phase 8), keeping `test_jarvis.py` as a thin runner during the transition?
3. Is changing log line contents allowed if the old `route:` prefix stays (for the trace in section 7)?
4. Which phases are wanted at all? (My recommendation order is in section 9; 4 and 6 carry the most risk.)
5. Should the legacy stream-per-chunk path (`JarvisVoiceSmooth=0`) be kept after the live test, or removed in phase 3 to halve the voice code?
