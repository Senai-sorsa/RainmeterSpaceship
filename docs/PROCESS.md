# The Process: from a Rainmeter skin to CSpace + JARVIS

Written 2026-11-03. This document records **how the project was built**: every stage, what was decided, and why.
It covers the time from the first commit (2026-10-09) to the `chore/ui-cleanup` branch (2026-11-03).

**How it was written.** The code diffs were not read. The sources were:
- all 470 commit subjects on `HEAD`, plus commit bodies and `--stat` for a few unclear commits;
- the plan, handoff, audit and review documents listed in [§16](#16-document-index);
- the branch list.

Line numbers, test counts and measurements are quoted from those documents. They were not re-run for this file.
Where a document says something was "not live-tested" or "not measured", that status is repeated here.

---

## Contents
1. [At a glance](#1-at-a-glance)
2. [How the work was run (the method that emerged)](#2-how-the-work-was-run)
3. [Stage 1: Building the Rainmeter skin (Oct 9-10)](#3-stage-1-building-the-rainmeter-skin-oct-9-10)
4. [Stage 2: Owner iteration and JARVIS appears (Oct 10-12)](#4-stage-2-owner-iteration-and-jarvis-appears-oct-10-12)
5. [Stage 3: JARVIS clean-up and the Repair Plan, Phases 0-6 (Oct 13-14)](#5-stage-3-jarvis-clean-up-and-the-repair-plan-phases-0-6-oct-13-14)
6. [Stage 4: Refactor, external audits, Phases 7-9 (Oct 15-16)](#6-stage-4-refactor-external-audits-phases-7-9-oct-15-16)
7. [Stage 5: Audit fixes, Clover, Phase 10 personality (Oct 16-17)](#7-stage-5-audit-fixes-clover-phase-10-personality-oct-16-17)
8. [Stage 6: Live test, then the standalone-app decision (Oct 20)](#8-stage-6-live-test-then-the-standalone-app-decision-oct-20)
9. [Stage 7: Porting the skin to TypeScript, and CSpace is named (Oct 21)](#9-stage-7-porting-the-skin-to-typescript-and-cspace-is-named-oct-21)
10. [Stage 8: CSpace autonomous build and Rainmeter parity (Oct 25-26)](#10-stage-8-cspace-autonomous-build-and-rainmeter-parity-oct-25-26)
11. [Stage 9: Feature sweep, wallpaper, QoL round (Oct 29-30)](#11-stage-9-feature-sweep-wallpaper-qol-round-oct-29-30)
12. [Stage 10: Visual overhaul, from line art to realism (Nov 2)](#12-stage-10-visual-overhaul-from-line-art-to-realism-nov-2)
13. [Stage 11: Hyperrealism, Blender hull and the live-test prep (Nov 2-3)](#13-stage-11-hyperrealism-blender-hull-and-live-test-prep-nov-2-3)
14. [Parallel track: JARVIS semi-live tuning, voice, persona, GOD mode (Oct 30 - Nov 3)](#14-parallel-track-jarvis-semi-live-tuning-voice-persona-god-mode)
15. [Reviews and audits: what each found and what happened](#15-reviews-and-audits)
16. [Document index](#16-document-index)
17. [Branches](#17-branches)
18. [Where things stand now (2026-11-03)](#18-where-things-stand-now-2026-11-03)
19. [Lessons from the process](#19-lessons-from-the-process)
20. [Appendix: commit map by stage](#20-appendix-commit-map-by-stage)

---

## 1. At a glance

| | |
|---|---|
| Span | 2026-10-09 → 2026-11-03 (26 days; work on 16 of them) |
| Commits on `HEAD` | 470 (473 across all branches) |
| Busiest days | Oct 15 (74 commits: refactor + audit + Phase 7-8), Oct 20 (59: standalone migration start), Nov 2 (48: visual overhaul) |
| Products | **Rainmeter skin** "Spaceship HUD" (v1.0.0) → **JARVIS/Clover** local voice assistant → **CSpace**, a standalone C# + WebView2 + Preact app that replaces Rainmeter → **GOD mode** (local large-model sandbox, untracked, not wired in) |
| Machine | "BLACK-CLOVER": Lenovo Legion, Ryzen AI 9 465 + Radeon 880M, RTX 5070 Laptop, 32 GB RAM, 2560x1600 panel |

### Timeline

```
Oct 09-10  ███ Rainmeter skin: plan → build → pixel-match the reference → v1.0.0 → 7 PRs merged
Oct 10-12  █   Owner edits; JARVIS voice assistant added (Whisper + Ollama + Kokoro)
Oct 13-14  ███ JARVIS repair plan (26-28 issues), Phases 0-6, Fix Rounds 3/5/6
Oct 15     ████ jarvis.py split into jarvislib (R1-R14), 3 external audits, AUDIT-0, Phase 7, Phase 8
Oct 16-17  ██  Phase 9 diagnosis, audit fixes, rename to "Clover", Phase 10 personality
Oct 20     ████ Live test → Gemini migration spec → review → plan v2 → SpaceshipUI + ShipCore host
Oct 21     ██  Lua→TypeScript port of every module (F0-F8); app named CSpace; audit of that work
Oct 25-26  ███ Autonomous PM run: desktop layer, data slices, perf tiers, security audit, Rainmeter parity R1-R6
Oct 29-30  ██  Every click/feature ported, live wallpaper, QoL/UI round, installer, JARVIS J-plan, GOD mode plan
Nov 02     ███ Visual overhaul (lit glass) → line-art-to-realism R1-R11 → hyperreal H0-H5
Nov 03     ██  Light canvas tuning, Blender-rendered hull, curved shell, UI clean-up, Live Test plan
           ‖   (parallel, uncommitted) JARVIS semi-live harness, voice/persona/refactor plans, GOD mode
```

### Four tracks

| Track | Lives in | Started | Main documents |
|---|---|---|---|
| A. The Rainmeter skin | `Skins/Spaceship/` (Lua + .ini), `layout/`, `tools/rmsim.py` | Oct 9 | `docs/PLAN.md`, `README.md` |
| B. JARVIS / Clover (voice assistant) | `Skins/Spaceship/@Resources/Jarvis/` (Python) | Oct 12 | `JARVIS-Repair-Plan.txt` (4,559 lines), `tasks/plan.md`, `tasks/jarvis-*` |
| C. CSpace (standalone app) | `SpaceshipApp/` (C# host, Preact UI), `contract/` | Oct 20 | `tasks/spaceship-migration-plan-v2.md`, `tasks/standalone-*`, `tasks/cspace-*` |
| D. Visual realism of CSpace | `SpaceshipApp/SpaceshipUI/src/draw`, Blender render | Nov 2 | `tasks/visual-overhaul-plan.md`, `tasks/line-art-realism-plan.md`, `tasks/hyperrealism-plan.md`, `tasks/UI-handoff.md` |

---

## 2. How the work was run

The method was not fixed on day one. It built up through mistakes and reviews. These are the rules now in force, with where each one came from.

| Rule | Where it came from |
|---|---|
| **Plan before code.** Each significant change needs a goal, scope, non-goals, acceptance criteria, validation, risks and a rollback plan (`CLAUDE.md` §3). | Project `CLAUDE.md`. The first instance is the HUD master plan in the second commit (`475d03d`). |
| **One master plan that a fresh chat can pick up.** `JARVIS-Repair-Plan.txt` says: "written so that a brand new chat can pick up any phase with no other context." | Oct 13. Context limits forced handoffs. One session hit 600k tokens (`line-art-realism-plan.md` §10). |
| **Vertical slices, one commit per slice, staged by file name.** Never `git add .`. | Phase 6 (Oct 14) onward. Formalised in `tasks/full-plan-2026-10-20.md`. |
| **Fakes first, dry run first, no real destructive calls in tests.** | `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md` (`6ef5336`, Oct 15). Added after a test run called the real `SHEmptyRecycleBinW` and may have emptied the recycle bin. Follow-ups: `f1e5dad` (fake the lock action, Oct 16) and `7d3e568` (fake the lock again, Nov 2). |
| **Model output never authorizes an OS action.** Every action goes through a fixed table, and "ask-first" actions need a spoken or clicked yes. | `CLAUDE.md` §5. Built as `ACTION_TABLE` in Phase 7-0 (`6273fc5`). Confirmed by the Opus 4.8 review ("the LLM has no execution authority"). |
| **Read-back truthfulness.** An action reports what Windows says happened, never "Done." by assumption. | Repair plan Phase 1 (`3b81ace`). Later invariant INV-5 in `rebuilding_jarvis.md`. |
| **Label every number:** [M] measured, [C] confirmed in code, [E] estimate, [?] unknown. | JARVIS improvement plan and GOD mode plan (Oct 30). It became the norm after the Gemini spec's targets ("<25 ms", "165 Hz P99") proved unmeasured. |
| **External audits are input, not orders.** Each audit is checked against the code, then sorted into fix / skip / later. | AUDIT-0 (Oct 15) and the migration review (Oct 20). |
| **No live run, push or deploy without the user's word.** | Every handoff. For example, `full-plan-2026-10-20.md`: "Live runs: fakes only… local commits only." |
| **Don't touch another session's files.** The UI sessions never stage JARVIS files, and the JARVIS sessions never stage UI files. | Nov 2-3, when the UI and JARVIS sessions ran at the same time (`UI-handoff.md` §1). |
| **Keep the base frame and the layout.** The goal is realism and finish, not a redesign. | The user's direction on 2026-11-02 (`visual-overhaul-plan.md`, memory `visual-overhaul-direction`). |
| **Keep the tier system:** FULL / LITE / LOW / STEALTH. Effects go on FULL, a cheaper subset on LITE, and nothing new on LOW or STEALTH. No GPU spikes. | Plan rev 2 §7 "Smart performance tiers" (Oct 9). Enforced in every UI slice since then. |

**Tooling used along the way:**
- Graphify: a knowledge graph in `graphify-out/`.
- Context7: library docs.
- agent-skills and ponytail: smallest change, review the diff.
- TokenWise model routing: added Oct 13, dropped Oct 20 (`676fa8b`).
- Superpowers plans/specs: `docs/superpowers/`.
- Playwright and vitest for the UI, xUnit for `ShipCore.Core`, and `test_jarvis.py` for JARVIS.
- `tools/rmsim.py`, a Rainmeter simulator used as an offline visual oracle.
- Blender 5.2: offline hull render.

**Models involved, per the documents:**
- Claude Opus: planning, most building, and reviews.
- Claude Haiku 5.5: the 25 module-port commits on Oct 21, later audited.
- Claude Sonnet: the repo fact-check in the migration review.
- Gemini: the migration spec, the Oct 15 JARVIS audit (AUDIT-0), the Oct 30 perf report and the persona report (each named as Gemini in the plans). Three other external reports (the Phase 7-9 audit, `rebuilding_jarvis.md`, `jarvis_user_improvment.md`) do not record their author.
- SOL and "Opus 4.8": two code reviews.

---

## 3. Stage 1: Building the Rainmeter skin (Oct 9-10)

**Goal.** A full-screen starship cockpit on the desktop. A hull frames the screen, and tinted windows look out onto the user's animated Lively wallpaper. Live widgets sit where the instruments sit in a Star Citizen-style canopy reference.

**Plan first.** `475d03d` added the HUD master plan (`docs/PLAN.md`), a zone layout (`layout/layout.json`) and an overlap checker (`tools/check_layout.py`). An hour later, rev 2 (`9ce5455`) curved the whole HUD and turned bars, rails and glyphs into frame art with cut-outs. It also added an Aurum-style Control Center and smart performance tiers that lighten the HUD under GPU load.

**Build and match the reference** (`3d6e7da` → `4b0f2c5`, ~20 commits in one day). The approach changed several times:

| Step | What changed |
|---|---|
| `3d6e7da` | First complete skin set |
| `8b5684e`, `9268c7b` | Rebuilt "one-to-one from the reference", then widgets aligned by **edge overlay** against the picture |
| `a07dac4`, `7efa90d` | Rebuilt **symmetric** from the owner's own window drawing (`art/window-lines-right.png`). The HUD is mirrored left/right. The neutral metal hull is **pre-rendered into one textured image** (`hull.png` + `window_mask.png`). Only theme-coloured parts stay live Shape meters, so colour themes still work. |
| `bd499bc` … `4b0f2c5` | Detail passes: a roaming red target, folder emblems, mist, lamps built like the reference, struts, a slatted console, corner bevels, info panels, spacing |

**Ship it.** The "Full install" PR (`e9d8131`) merged v1.0.0: 32 modules, the frame art, the Control Center and an `.rmskin` installer.

**First fixes from real use**, on the `claude/beautiful-einstein-7dpr0t` branch, PRs #2-#7:
- non-primary monitor and Windows display scaling: AutoFit recognises the panel by its 16:10 shape;
- z-order: the frame stayed above the modules;
- running behind the taskbar (`FrameBehindTaskbar`);
- tilted click areas for slanted panels;
- a "cockpit art OFF" mode;
- folder buttons, an app drawer with every installed app, and a Control Center that keeps its tab across refreshes.

**Outcome.** A working, installable skin with a design record (`docs/PLAN.md`, "Status: built (v1.0.0)") and a README covering install, external monitors and scaling.

---

## 4. Stage 2: Owner iteration and JARVIS appears (Oct 10-12)

The user made several large commits themselves:
- `831634c` "improvments update 1": 642 files, mostly `@Resources/Backups/PartC-*` snapshots and script edits;
- `7e87904` "fixes";
- `9c84da2` "work": 1,407 files.

`9c84da2` is where **JARVIS first appears** in history:
- `@Resources/Jarvis/` and an `Overlay/Jarvis` skin (the hologram orb);
- sounds;
- Kokoro TTS test scripts;
- images.

The design: a local voice assistant. It has an openWakeWord wake word, Whisper speech recognition, an Ollama chat model and Kokoro speech. It talks to the HUD through small text files in `Data\`.

---

## 5. Stage 3: JARVIS clean-up and the Repair Plan, Phases 0-6 (Oct 13-14)

**Clean-up first (Oct 13).**
- `55ff7e2` stopped tracking personal runtime data, backups, weights and scratch files.
- `c7fa276` added an assert-based self-check for routing and app matching. This became `test_jarvis.py`, about 3,569 lines by Oct 15.

Then came a run of small correctness fixes:
- idempotent mute/unmute;
- the 15 s confirm window starts after the prompt is spoken;
- whole-word app matching;
- the mic closes when JARVIS is off;
- cancel can end a blocked model call;
- idle model unload;
- cuBLAS/cuDNN discovery;
- **pinned packages in a private venv** (`0db2fa4`, `%LOCALAPPDATA%\SpaceshipHUD\venv`).

**Features (Oct 13):**
- GPU speech recognition;
- truthful action reports;
- Ollama only on the RTX;
- HUD sensor answers;
- volume and media control;
- timers and reminders;
- four Kokoro voices and a personality setting;
- follow-up without the wake word;
- snooze, repeating reminders, remembered facts, to-do by voice, and a daily briefing.

**The Repair Plan (`7bf9e14`, Oct 13).** After the first live test, `JARVIS-Repair-Plan.txt` listed 26 issues (28 later) and Phases 0-9. It grew to 4,559 lines and became the single source of truth for JARVIS. Its phases:

| Phase | Theme | Commits / status |
|---|---|---|
| 0 | Measure first (read-only) | done |
| 1 | He tells the truth and commands really run | `3b81ace` |
| 2 | GPU first: voice on the RTX, `small.en`, status-only hologram | `d7386dd` |
| 3 | Hearing you correctly | `301c22f` |
| 4 | Interrupting him (stop, barge-in) | `301c22f`, `f910b76` |
| 5 | Alarms that ring until answered (5 min cap, snooze) | `23b290c` |
| 6 | Relevance, memory, sounding human. Revised mid-way into "four memory layers, one path": M1 last results, M2 topic memory, M3 daily/monthly compaction, M4 facts and "what he actually did" | `1036282` → `aa3a48d`. Checkpoints A/B; detail in `tasks/plan.md` |
| Fix Round 3/5/6 | Live findings ("he wakes on noise"); then a **redesign in slices A-H**: lanes, no-data reply, follow-up gate, undo window, pop-up at speaking pace, stop words while speaking, stricter wake | `4e51364` → `560206c` |
| Audit 2 | Blank personal paths in `Settings.inc`, pinned clock in alarm tests, the sleep button never hibernates, DST-safe alarm roll-over | `f91ec33` |

**Process notes.**
- Each phase was approved, built in slices, tested with fakes, then committed "on the user's word".
- Live tests were batched: one at the end of Phase 6, not one per slice.
- Phase 10 (personality and voice) was parked on purpose so that function came before tone.

---

## 6. Stage 4: Refactor, external audits, Phases 7-9 (Oct 15-16)

**Oct 15 was the busiest day: 74 commits.**

**Stage-2 items S2-8..S2-13** (`ad8df7e`):
- a capability table;
- an outcome log;
- an "open ear";
- Modern Standby sleep;
- a CALL ME row;
- scroll-bar drag.

**The refactor: split `jarvis.py`** (the user's order: "before Phase 7"). `jarvis.py` was about 2,600 lines. Fourteen steps (R1-R14) moved it into `jarvislib/`:
- base, stopwords, gpu, hearing, tts, llm, audio, mic, notes;
- speech, calc, actions, confirm, stopkey, turnstate, todo;
- reminders, diag, meaning, search, memory, routing, prompt.

Each step was one commit. The first step (R1) made the test proxy split-safe, so the tests kept working while modules moved. The result is documented in `Improvments-and-Audits/JARVIS-Architecture-and-Stabilization.md` (`b412b60`):
- `jarvis.py` went down to 1,472 lines and became "the integrator only";
- there is a one-way import DAG: no module imports `jarvis.py`;
- three processes (the HUD, JARVIS and ShipCore) talk only through `Data\` files.

**Phase 3 "stabilization"** (`f89e700` → `4007212`):
- no spoken words in `jarvis.log` (privacy);
- an unsure "yes" never confirms;
- one atomic writer;
- one JSON chat call.

**Three external reviews arrived the same day** (details in [§15](#15-reviews-and-audits)):
- the **Opus 4.8** security review. It found no major issues ("Architecture Verdict: Strong"), plus low findings such as a quote in the TTS temp path;
- the **SOL** forensic audit of commit `8bd241f`;
- the **Gemini** audit. It was sorted into a new **AUDIT-0** block plus Phases 7-11 and Stage 2 (`869766e`).

The fixes were done in three review batches (`2e33b08`, `d5027fe`, `c871c1c`), then AUDIT-0 items P0-01 … P0-12:
- the volume direction now follows what was said ("too loud" = down);
- undo restores multi-command turns;
- the "Did you say…?" gate covers reminders and memory too;
- atomic gist saves;
- a fix for the date-dependent N7 timer test flake.

Some items were **declined on purpose and recorded** (`178afc2` "BUG-02 not fixed (the user's decision)"), and two stray files were deleted only "on the user's word" (`ca8899e`).

**The safety rule is born.** `6ef5336` added `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md` after a test reached the real recycle-bin call.

**Phase 7: more settings by voice** (`6273fc5` → `256a9cb`):
- **one `ACTION_TABLE`**: `run_action` refuses an ask-first row unless a confirmed pending action is passed in;
- the microphone: mute, level, device choice;
- brightness;
- dark/light mode;
- settings pages, screenshot, show desktop;
- recycle bin (asks first);
- power mode;
- Bluetooth radio and audio device connect;
- stealth mode by voice;
- "open X" focuses an app that is already running;
- weather/news questions get an honest "I can't look that up yet";
- the Control Center JARVIS tab regrouped.

**Phase 8: follow-up timing and sounds** (`6d6e50a` → `1416f23`):
- a 3 s follow-up window, or up to 10 s if his name is said;
- chime volume;
- an echoed-prompt guard;
- quiet during class (calendar-driven);
- **type to him** (the ASK command).

**Phase 9: "ask him what is wrong"** (`4516925` → `535b8f9`, Oct 16):
- a read-only `diag.ps1` snapshot and an event-log table;
- a findings rules table;
- a PROTECTED process set: "kill explorer" is refused before it reaches `taskkill`;
- code-made answers;
- a silent watch every 5 min, with rate limits.

The plan records real read-only trial numbers. Phases 7-9 were all "tested with fakes only, NOT live".

---

## 7. Stage 5: Audit fixes, Clover, Phase 10 personality (Oct 16-17)

**The Phase 7-9 audit** (an external report). `Jarvis Phase7 To 9 Audit And Fix Plan.md` reported 39 confirmed bugs, from targeted probe scripts and "industry edge-case" suites:
- confirmed actions said "Done." without a read-back;
- a stale `UNBUILT_CAPS`;
- noise-floor lock-in;
- an unclamped drawer scroll.

They were fixed in four themed commits (`81bdbb4`, `6ef6573`, `e200769`, `37b230a`).

**Wake-word hardening:**
- the trained "Hey Jarvis" needs a normal score of 0.3;
- a wake turn waits 10 s for the first word;
- a 25 s recording that was not for him is dropped.

**The rename** (`1ca4f18`, "Change 4"). The assistant is called **Clover** in everything seen or heard, and still answers to "Jarvis". The wake model became a setting (`JarvisWakeModel`), and a custom file that will not load falls back safely.

**Phase 10: personality.** The user answered a 411-line questionnaire (`JARVIS-Phase10-Personality-Questions.txt`). Then:
- **Slice 1** (`7ddc7a9`): `persona.txt`, four moods (mirror / serious / brief / playful), the Clover name, a blended voice. Tweaks: contractions allowed; "sir" almost always; "Mr. Sorsa" only on serious topics.
- **Slice 2, checkpoints A-D** (`dee829b` → `5b8b66c`): serious topics, class-time mood, mood by voice, silent room talk, auto-remember, promises, "what do you know about me", speakable text, a pronunciation file, voice speed, and privacy mode.
- Talk memory became "the whole talk (up to 40 messages) for 20 minutes" (`f63ada6`).
- The Control Center got a CLOVER/JARVIS name switch and a Quick Guide.

---

## 8. Stage 6: Live test, then the standalone-app decision (Oct 20)

**The live test.** The user's notes were committed as `User complaints - from live test.md` (643 lines, `80fc6a3`). Examples:
- "Just 'JARVIS' shouldn't work as a wake word";
- "GPU load is consistently at 80%, and it goes down when Rainmeter is turned off";
- "Whenever I say 'nevermind' he says 'okay nevermind'";
- "the chat takes a while".

These became **Phase 10B** (`bdfb8fb`, checkpoint): wake-word, follow-up and GPU-baseline fixes. An external usability benchmark (`jarvis_user_improvment.md`, an 11-product comparison) was checked and partly folded in.

**The pivot.** The GPU complaint and the limits of Rainmeter (no smooth animation, Lua/ini only) led to the plan to **leave Rainmeter**:

1. **Gemini spec** (`claude_spaceship_migration_phases.md`, 3,764 lines, committed in `d2e8d63`). C# host + WebView2 + Preact, named pipes, a 165 Hz intro, and copy-paste prompts per phase. Self-rated "10/10".
2. **Review** (`tasks/migration-review-2026-10-20.md`). A Sonnet repo fact-check plus an Opus design review, both read-only, found:
   - wrong repo facts: module counts, and almost every line number;
   - **5 critical design errors**:
     1. the transparent window was never specified (it needs `WS_EX_NOREDIRECTIONBITMAP` + DirectComposition);
     2. insecure named pipes;
     3. WebMessage → OS actions with no origin check, and model output able to write any `Settings.inc` key;
     4. every start force-kills Rainmeter skins;
     5. the startup task is installed without asking;
   - more high-severity issues;
   - "impossible numbers": <25 ms Stage 0, 165 Hz P99, <22 MB VRAM.
3. **Plan v2** (`tasks/spaceship-migration-plan-v2.md`), which wins over Gemini's. Principles:
   - **Rainmeter stays and is never modified**;
   - test-first, split by platform: logic builds on Linux, a thin Windows shell;
   - **measure, then promise**;
   - **one shared contract** (`contract/protocol.schema.json` + fixtures, tested from C#, TypeScript and Python);
   - model output never authorizes OS actions;
   - port 1:1 first, restyle second.
   - Phases P-A … P-H, with a **P-D go/no-go prototype** for the transparent window.

**Built the same day (Oct 20, ~45 commits):**
- `98f38d8` UI asset exporter. `841fcff` **SpaceshipUI** scaffold (Vite + Preact + signals), MockHost, static HUD, tests.
- `8650201`, `d0ea922` rmsim parity diff tools.
- A Superpowers **spec and plan** for the first-run setup, the Control Center redesign and frame modes (`1526f93`, `4d3f2d2`). Then, task by task:
  - a settings registry with a consistency test;
  - a config/setup contract;
  - a store with undo/redo/search;
  - shared settings components;
  - a Control Center with categories, levels, search and undo;
  - a wizard state machine and the first-run wizard;
  - frame modes (rendered / picture / none);
  - a help panel.
- `bc6f684` **ShipCore.Core**: config store, schema, protocol, and action and pipe gates, with xUnit tests. `cc1d4a5` fixed review items 1-11.
- `1458118` exam-browser list, AutoStart, Lifecycle, and the **P-D Windows prototype** with a run guide (`docs/P-D-PROTOTYPE.md`).
- Audit follow-ups:
  - `eb5e937` Python contract check;
  - `15a4403` SHA-256 check on the Kokoro voice downloads;
  - `7270160` launch-target allowlist.
- `d11bf8a`, `dd39bfa` UI improvement plan in three phases (`docs/UI-IMPROVEMENTS.md`, `docs/Future-UI-Improvements.md`). Rainmeter calendar and hint fixes (`35aab69`, `413001d`).
- `0d12860` → `3d6c349` the **standalone host**: shell, kill switch, message router, config, visibility, lifecycle, JARVIS pipe handshake, cutover script (dry run by default), real WebView bridge.
- `tasks/standalone-app-architecture.md`: the host is its own app, not part of the system, with guardrails so it can be switched off.
- `tasks/standalone-vision-plan.md`: the user's vision of "everything the skin does… **no Rainmeter anywhere in the new app**". Its own `settings.json` with a one-time import (`a4324bf`). The Rainmeter switch was removed from the tray (`1f392bb`).

`docs/IMPROVEMENTS.md` kept a running log. Its rule: "Nothing here was run on Windows, in Rainmeter, or in WebView2". Most of this day's work ran on an Ubuntu VM.

---

## 9. Stage 7: Porting the skin to TypeScript, and CSpace is named (Oct 21)

**Port the drawing layer, then every module** (`26c8b0c` → `292fa59`):
- `lib.lua` → TypeScript (shapes, icons, text);
- a Lua-to-TS converter draft;
- then modules F0-F8: power, alert, battery, graphs, console, top, bottom, left, right, centre (target, HUD, sphere), boot, cargo drawer, JARVIS core and log, systems dial;
- one rAF scheduler.

Each module sat behind `?module=<name>` for isolated checks. Host data sources came too:
- HWiNFO shared memory with a Windows-counter fallback;
- network rate;
- spectrum bands via WASAPI loopback;
- process names.

**Naming.** The user named the app **CSpace** ("Computer spaceship app") (`b57b9c1`).

**The audit of this stage** (`06e20d5`, `docs/HANDOFF-2026-10-21-cspace.md`):
- "All 25 most recent commits were written by Claude Haiku 5.5 and have had only unit tests, never a live look. Treat them as unreviewed."
- The P-D go/no-go was recorded as failed or pending.
- The build was blocked by a running instance.

The handoff gave a redone plan and a suggested review of Haiku's 25 commits. `tasks/cspace-gap-analysis.md` (Oct 25) then compared the Gemini spec with the code item by item: DONE / PARTIAL / MISSING / SUPERSEDED / UNWISE. It found CSpace used **one window + DirectComposition + `WM_NCHITTEST`**, not the spec's several windows.

---

## 10. Stage 8: CSpace autonomous build and Rainmeter parity (Oct 25-26)

**The autonomous PM run** (`tasks/cspace-pm-log.md`). Standing order: loop per slice = plan → code → unit/static checks → compare with similar apps (Wallpaper Engine, Lively, Rainmeter, Seelen UI, Windhawk, BeWidgets) → queue improvements. Ask the user only before actions that could damage the PC. No push (public repo).

**Window behaviour:**
- `f83655e`: desktop layer by z-order, as Rainmeter does (not a WorkerW child);
- `6066979`: click-through outside the page's hit regions;
- `3cc9543`: hide at once for fullscreen apps and exam browsers;
- `3c21dbd`: hide while the PC is locked.

**Data slices S5-S6:**
- JARVIS state reaches the HUD;
- upkeep and dev status scripts;
- ping/LAN/WAN;
- an S&P 500 tape;
- the reticle to-do mode from the Obsidian note;
- HWiNFO sensors bound by label.

**Performance slices S8-S11:**
- a capped perf log;
- a hidden HUD stops rendering;
- the offline orb draws at 10 fps;
- **perf tiers**;
- a Release publish profile;
- the audio loopback starts only while the HUD is shown;
- `Off_` module toggles are honoured.

Measurement-driven perf commits: `jarvis.txt` read only on change (it was throwing an IOException 5x/s), and `settings.json` parsed only on change.

**Security, efficiency and UI audit (user-requested)** (`220df0d` A1, `34f64ca` A2, `c70d3e8` A3):
- dropped the AV-flagged patterns (RemoteSigned not Bypass, no hidden windows) and hardened the WebView;
- per-frame timers stop while hidden;
- `3f58441`: only the app's own page may message the host.

**First live runs** (`10e6afb`, `7810730`). Fixes for clicks, flicker, layout size, wallpaper, fonts, the orb and the log pop-up.

**Rainmeter parity** (`tasks/cspace-rainmeter-parity-plan.md`, Oct 26). A segment-by-segment table of what Rainmeter does and what CSpace still lacked, e.g. per-skin `Update=`, Show Desktop handling, double-click/X buttons, the Audio and SysInfo measures, `!Refresh`, single-instance focus. Slices:
- **R1-R5** (`32c4ae3`): lifecycle, occlusion, input;
- **R6**: the real app catalog from `Apps.ini`, the live calendar, real PILOT/HOST/OS/CPU/GPU/RAM.

Then a **visual parity round**, driven by the user's screenshots (`853ec1b`, `09737c4`, `fa0e646`). About 30 commits, each "as `<file>.lua` does":
- text widths and ClipString ellipsis;
- the frame overlay drawn from the skin's Shape meters;
- the audio dial;
- neon app icons;
- battery time left;
- Wi-Fi quality;
- console status;
- RUNNING/BACKGROUND/READY slots;
- the text glow halo;
- Gmail unread count;
- the click targets.

`?preview=1` and sample host messages let headless screenshot checks show a filled HUD.

---

## 11. Stage 9: Feature sweep, wallpaper, QoL round (Oct 29-30)

**Per-feature sweep** (`tasks/cspace-features-plan.md`, `-todo.md`). Every remaining skin behaviour was ported, each citing its Lua source:
- hover captions;
- the console's Legion Toolkit/perf/master buttons;
- column picks that survive restarts;
- the NET speed test;
- right-click rechecks;
- output-device switching;
- the master switch remembering its tier;
- calendar refresh;
- the frame growing from the top-left like `Frame.ini`;
- select graphs;
- the real JARVIS log pop-up;
- the boot sequence once per start;
- click the hologram to wake JARVIS;
- type to him;
- the service buttons;
- auto-start JARVIS;
- tray CARGO and boot items;
- Start-menu app scan;
- hiding buttons that had no host side yet (instead of doing nothing).

**Architecture decision recorded.** `JarvisPython` is read by the host only. A value the page could write would let the page choose which program the host launches.

**New features beyond the skin:**
- **live wallpaper** under the HUD (`8259aba`), with quality re-encode and caching, pausing over Remote Desktop;
- a new icon, power saver, a remembered Stop;
- a **HUD kit, Control Center re-skin, pre-flight wizard, notices, help center and installer** (`5d4c5c8`).

**JARVIS J-plan** (`tasks/jarvis-improvement-plan.md`, Oct 30). A Gemini report was checked against the code; "most of its 'top fixes' already exist". It measured that torch was not installed at all, so "remove torch, save 1.1 GB" was void. Built:
- `f3a69b0`: faster end of short commands, no Whisper loops;
- `ce42b3e`: mirror mood, timed moods, opt-in weather/news, a CSpace restart supervisor.

**GOD mode plan** (`tasks/god-mode-plan.md`, draft). A local large-model mode with four named slots, and an "ULTRON" slot that can never have tools. It sat waiting for approval behind the JARVIS and wallpaper live tests.

---

## 12. Stage 10: Visual overhaul, from line art to realism (Nov 2)

**The user's direction** (`tasks/visual-overhaul-plan.md`):
> I like the base frame we have right now. What I don't like are the designs of the smaller features, ALL of the pop-ups, and a lot more of the frame… They could look so much smoother and more realistic.

The rules taken from the references (`Refrences-Art/`) and FUI practice:
- one hero value per cluster;
- hairlines for structure;
- glow only for what is lit, with soft falloff;
- panels as lit glass;
- callouts with leader lines;
- cyan structure, white live values, warn colours only for state.

**Pass 1: "lit glass"** (`763b5bb` → `c74d3a1`, ~20 commits):
- real bloom on the glow layer;
- Rajdhani body text with a weight hierarchy;
- large telemetry readouts;
- glass plates for rows;
- an orb callout;
- the Control Center finish;
- the log pop-up, drawer, wizard and notices in one lit-glass frame;
- a new boot sequence (ignition ring and lock-on);
- neon tube falloff;
- a dark tray menu and a dark installer;
- **the music ring "moves like a real visualizer"** (`7a262e2`). This followed the user's note that it "moves weirdly" and research into real visualizers.

**Pass 2: line art → realism** (`tasks/line-art-realism-plan.md`, slices R0-R12; K1-K12 techniques):
- **R1** realism kit in `canvas.ts`: gradient fills, lit displays, heat ramp, screen texture;
- **R2-R4** telemetry, app rows, dials and side panels as lit instruments;
- **R5** hot bloom and light spill on the hull;
- **R6** hologram projection;
- **R7** lit keys;
- **R8** pop-ups power on like cockpit screens;
- **R9** Control Center/wizard as hardware glass;
- **R10** the boot ring burns from a hot head;
- **R11** a faint chromatic fringe and flicker-on;
- **R12** a tier pass.

The plan also noted that the previous session reached 600k tokens of context, so a fresh session took over.

---

## 13. Stage 11: Hyperrealism, Blender hull and live-test prep (Nov 2-3)

**Plan** (`tasks/hyperrealism-plan.md`, 394 lines, Superpowers format). Goal: the hyperreal look of `Refrences-Art/`, with "**less** GPU than today (or no more than +5 GPU points on FULL)". Three cheap mechanisms:
1. one **quarter-resolution light canvas** (bloom, lens dirt, glass ghost). It replaces per-group CSS `blur()`, which the GPU re-blurs on every update;
2. an **offline Blender render** of the cockpit shell, with grayscale light passes tinted live at zero runtime cost;
3. a shared **curvature table** so that long HUD elements bend with the shell.

**Built:**

| Slice | Commit | What |
|---|---|---|
| H0 | `1591b8d` | Baseline. Live GPU not run: "needs the user's word" |
| H1 | `1dbc09d`, `b7e8600`, `37efe46` | Light bus and canvas painters; the quarter-res canvas replaces CSS blur on FULL; measured and tuned (cached tiles, no re-blur of equal ops) |
| H2 | `b2e8615`, `b16982e`, `96d0880` | Deterministic blue-noise and lens-dirt maps; lens dirt lit by the HUD light; grain to end gradient banding |
| H5 | `e2760f0` | Hot budget per cluster as a test |
| H13 (headless) | `2aa5856` | Tier pass and budget fixes |
| Session 2 | `d98b87c` … `80443ec` | Rounded glow, **music ring fixed for real** (`64958b7`: smoothing was per redraw, so a quiet frame made ~10 s of visible jumps), depth haze, screen bezels, CTM caching (65 reads/s idle → ~0), the orb lights the hull, the lens settles after boot |
| H3 | `dfeedcf`, `ba4dba6`, `009faba` | Blender-rendered shell + light passes, behind `HullRender` (default 0) |
| H4 | `5521c6c` | Barrel-curved shell and zone bend support |

**Measurements** (`tasks/UI-handoff.md` §5). Headless Chromium, software rendering, % of one core, interleaved medians of 3 rounds:

| Condition | Old SVG glow | New layers | Change |
|---|---|---|---|
| Idle | 134.7 | 139.3 | +3.4 % |
| Music | 133.0 | 145.8 | +9.6 % (budget +10 %) |

**Live WebView2 GPU/VRAM: never measured.** This is the biggest open number. The handoff also lists:
- rulings with "the cost if wrong";
- what was tried and dropped (an orb glare streak that "read as a flat grey bar");
- known flaky e2e tests;
- a 40-item improvement list (§12);
- audits to run (§13).

**UI clean-up for the Live Test** (`tasks/UI-cleanup-handoff.md`, branch `chore/ui-cleanup`):
- `1fcff97`: 12 longest hints condensed;
- `fc9ea15`: `ColorDim` brightened from 0,110,150 to 0,140,185. The old value was 3.27:1 contrast, under WCAG AA;
- `e99180a`: arbitrary brick-grid seams removed from the hull render;
- tests made to wait for state, not time;
- `tasks/LIVE-TEST.md`: what a separate session must check and measure before the user signs off, with checks C1-C10.

Gates at the latest recorded point:
- `tsc` clean;
- vitest 428/428;
- Playwright 57/57;
- `vite build` OK.

---

## 14. Parallel track: JARVIS semi-live tuning, voice, persona, GOD mode

These ran in other sessions at the same time as Stages 10-11. Most of it is **uncommitted** (it shows as modified or untracked in `git status`) and waits for the user's word.

- **Semi-live harness** (`tasks/HANDOFF-jarvis-semi-live.md`, `tasks/jarvis-next-plan-2026-11-02.md`):
  - **The idea.** Type what he "heard" into the real pipeline (real Ollama model, real prompt, real routing), with every OS action faked and guarded, then score every reply.
  - **Case banks.** 221 cases (44 held out) and then a fresh 121-case bank that was never tuned on.
  - **Results.** Cost scores dropped, e.g. llama3.1:8b 140 → 46 and held-out 35 → 11, confirmed on a second seed. Persona r2 was rejected because it was better on 8B but worse on 3B.
  - **Fixes found:**
    - 12-hour times;
    - follow-up pronouns;
    - the 988 crisis line;
    - "pull up Chrome" (the model claimed it opened);
    - "I need a ten minute timer" lost its time;
    - the late-night nag;
    - a headphone-softer voice;
    - a Whisper second check for wake words (off by default);
    - `hearing_eval.py`.
  - One part was committed: `7f1f18e` "semi-live test harness and the fixes it found".
- **Voice plan** (`tasks/jarvis-voice-plan-2026-11-03.md`). Measured why the voice is choppy:
  - 83 % of replies start with a mid-sentence fragment;
  - each seam is ~0.27-0.35 s of silence;
  - MME output costs ~123 ms per new stream, vs ~73 ms on WASAPI;
  - Kokoro adds 0.27-0.37 s of trailing silence.
  - The plan: fix chunking and playback, and keep the Kokoro engine. A/B WAVs are in `tasks/voice-measurements/`.
- **Persona plan** (`tasks/jarvis-persona-plan-2026-11-03.md`). It takes a Gemini movie-corpus report and keeps only the checkable style traits. It marks its 2026 papers and synthetic datasets as unverified, and rejects what conflicts with the rules (e.g. "execute next steps before being commanded").
- **Refactor plan** (`tasks/jarvis-refactor-plan-2026-11-03.md`). It must not start until the live test is done and the tree is committed. Its targets:
  - `exchange()` is ~410 lines;
  - `_route_rest` is a 320-line regex ladder;
  - the goal is one pipeline, behaviour-preserving, each phase revertible.
- **GOD mode** (`GodMode/`, untracked).
  - **What it is.** A standard-library Python package with:
    - its own low-integrity Ollama;
    - RAM caps that also cover memory-mapped model pages;
    - a freeze-on-low-RAM guard;
    - a separate low-IL file reader;
    - gated self-tweaks tested in an AppContainer;
    - opt-in secret-folder labels.
  - **Tested:** 111 unit tests OK, and spikes 4/4, 4/4, 5/5 and 7/7 on this laptop.
  - **Not done:** nothing is wired into CSpace or JARVIS, and no models are downloaded.

---

## 15. Reviews and audits

| Document | By / when | Scope | Key findings | What happened |
|---|---|---|---|---|
| `Improvments-and-Audits/Old/opus 4.8 Code review.md` | Opus 4.8, Oct 15 | Security/robustness of `jarvislib` | "Architecture verdict: Strong. The LLM has no execution authority." Low: PowerShell quote injection via the TTS temp path, etc. | Review fix batches 1-3 (`2e33b08`, `d5027fe`, `c871c1c`) |
| `Improvments-and-Audits/Old/SOL-Code-Review.md` | SOL, Oct 15 | Forensic read-only audit of `8bd241f` | Evidence-tracked findings | Folded into the review batches and the pre-Phase 7 handover (`08bf16f`: fixed / skipped / waiting) |
| Gemini audit (added `869766e`) | Gemini, Oct 15 | JARVIS | P0 bugs | **AUDIT-0** P0-01..P0-12, the rest to Phases 7-11 and Stage 2 |
| `Improvments-and-Audits/JARVIS-Architecture-and-Stabilization.md` | Claude, Oct 15 | Post-refactor architecture | Module map, verified / mocked / manual status | Reference for later phases |
| `Jarvis Phase7 To 9 Audit And Fix Plan.md` | External report (author not recorded), Oct 16; committed Oct 20 | Phases 7-9, edge cases, comparable assistants | 39 bugs + 5 recommendations, incl. a WebView2/Tauri migration idea | Audit-fix commits `81bdbb4` … `830a81b` |
| `Improvments-and-Audits/rebuilding_jarvis.md` | External report (author not recorded), committed Oct 20 | 10-assistant benchmark + spec | Invariants INV-1..INV-8 (import DAG, single writer, privacy log, read-back, 4-button cap, confirm for destructive actions) | Used as a checklist for Phase 10B |
| `jarvis_user_improvment.md` | External report (author not recorded), Oct 20 | Usability, 11-product benchmark | Six friction paths ("Did you say…?", blank-transcript apology, 2 s silence cut-off, 5-word TTS split) | Partly into Phase 10B; the TTS split resurfaced in the Nov 3 voice plan |
| `User complaints - from live test.md` | The user, Oct 17-20 | Live use | Wake on "JARVIS" alone, 80 % GPU, slow chat, "okay nevermind" | Phase 10B |
| `tasks/migration-review-2026-10-20.md` | Sonnet + Opus, Oct 20 | The Gemini migration spec | Wrong repo facts, 5 critical design errors, impossible numbers | Plan v2 replaced the spec |
| `docs/HANDOFF-2026-10-21-cspace.md` §4 | Claude, Oct 21 | Haiku's 25 port commits | Unreviewed, never seen live | Reviewed through the parity rounds |
| `tasks/cspace-gap-analysis.md` | Claude, Oct 25 | Spec vs code | DONE / PARTIAL / MISSING / SUPERSEDED / UNWISE per item | Fed the S-slices |
| CSpace audit A1-A3 | Claude, Oct 25 (user-requested) | Security, efficiency, UI | AV-flagged patterns, hidden-HUD timers | `220df0d`, `34f64ca`, `c70d3e8` |
| `tasks/jarvis-improvement-plan.md` | Claude, Oct 30 | A Gemini perf report | Most fixes already existed; torch not installed | J0-J7 |
| `tasks/UI-handoff.md` §13 | Claude, Nov 3 | UI risks | Audits to run, warm-colour misuse list, contrast | Clean-up branch |

**Pattern.** The external reports were long and confident, with self-ratings and precise line numbers. Checked against the code, they mixed real bugs, already-fixed items, wrong facts and unmeasured promises. Each one was triaged rather than applied.

---

## 16. Document index

**Design and plans, by track**

| Track | File | Role |
|---|---|---|
| Skin | `docs/PLAN.md` | HUD master plan, rev 1-3, design record |
| Skin | `README.md`, `Skins/Spaceship/@Resources/Docs/Spaceship-HUD-Guide.md` | User guide |
| JARVIS | `JARVIS-Repair-Plan.txt` | Master plan, Phases 0-11, Fix Rounds, AUDIT-0, REFACTOR, Stage 2 |
| JARVIS | `tasks/plan.md`, `tasks/todo.md` | Phase 6 revised plan and task breakdown |
| JARVIS | `JARVIS-Phase10-Personality-Questions.txt`, `tasks/phase10-slice{1,2}-{plan,todo}.md` | Personality spec and slices |
| JARVIS | `tasks/jarvis-improvement-plan.md`, `tasks/jarvis-next-plan-2026-11-02.md` | J-plan; semi-live plan |
| JARVIS | `tasks/jarvis-{voice,persona,refactor}-plan-2026-11-03.md` | Current JARVIS plans (not built) |
| JARVIS | `tasks/HANDOFF-jarvis-semi-live.md`, `Improvments-and-Audits/JARVIS-Live-Test.md` | Session handoff; live-test script |
| CSpace | `claude_spaceship_migration_phases.md` | Gemini spec (raw source only) |
| CSpace | `tasks/migration-review-2026-10-20.md`, `tasks/spaceship-migration-plan-v2.md` | Review; plan v2 |
| CSpace | `tasks/full-plan-2026-10-20.md`, `tasks/standalone-app-architecture.md`, `tasks/standalone-vision-plan.md` | Decisions, host shape, vision |
| CSpace | `docs/superpowers/specs/…setup-and-control-center-design.md`, `docs/superpowers/plans/…` | Wizard / Control Center spec and plan |
| CSpace | `docs/P-D-PROTOTYPE.md`, `docs/LIVE-TEST-STANDALONE.md`, `docs/WINDOWS-SESSION-START.md` | Windows run guides |
| CSpace | `tasks/cspace-gap-analysis.md`, `tasks/cspace-rainmeter-parity-plan.md`, `tasks/cspace-features-{plan,todo}.md`, `tasks/cspace-pm-log.md` | Gap audit, parity, feature sweep, PM log |
| UI | `docs/UI-IMPROVEMENTS.md`, `docs/Future-UI-Improvements.md`, `docs/IMPROVEMENTS.md` | UI improvement phases; running log |
| UI | `tasks/visual-overhaul-plan.md`, `tasks/line-art-realism-plan.md`, `tasks/hyperrealism-plan.md` | The three realism plans |
| UI | `tasks/UI-handoff.md`, `tasks/UI-cleanup-handoff.md`, `tasks/LIVE-TEST.md` | Current UI state, clean-up, live test |
| GOD | `tasks/god-mode-plan.md`, `tasks/god-mode-gemini-research-prompt.md`, `GodMode/*.md` | GOD mode design and handoff |
| All | `docs/HANDOFF-2026-10-20*.md`, `docs/HANDOFF-2026-10-21-cspace.md`, `docs/PAUSED-2026-10-20.md` | Session handoffs |
| Rules | `CLAUDE.md`, `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md` | Project rules |

---

## 17. Branches

| Branch | What it holds |
|---|---|
| `claude/beautiful-einstein-7dpr0t` (remote) | Oct 9-10 skin fixes, PRs #2-#7 |
| `chore/jarvis-baseline-and-performance` | Oct 13-17 JARVIS phases, refactor, audits |
| `fix/phase7-9-audit` | Oct 16-20 audit fixes up to the live-test notes (`80fc6a3`); now contained in `HEAD` |
| `feature/setup-control-center`, `feature/ui-phase1` (remote) | Oct 20 UI work, merged into `main` the same evening |
| `backup/main-before-merge-2026-10-20` | Safety copy before that merge |
| `feature/standalone-host` | CSpace host and module port (Oct 20-30) |
| `feature/visual-overhaul` | R1-R12 (stops at `296c8ed`) |
| `feature/hyperreal` | H0-H5. `main` was fast-forwarded to it on Nov 3 (local; `origin/main` is behind) |
| `feature/hull-render` → `feature/hull-curve` | Blender hull (H3), curved shell (H4); stacked, not merged |
| `chore/ui-cleanup` (current) | Off `feature/hull-curve`: Live-Test clean-up |

---

## 18. Where things stand now (2026-11-03)

**Built and committed:**
- the Rainmeter skin (still the default, untouched by CSpace);
- JARVIS Phases 0-10B;
- the CSpace host and full UI port with Rainmeter parity;
- the realism and hyperreal layers;
- the Blender hull and curve (behind `HullRender`, default 0).

**Open, in the order the documents give:**
1. **Live Test** (`tasks/LIVE-TEST.md`), including the **first live WebView2 GPU/VRAM measurement**. Every perf claim so far is headless.
2. Decide the merge order: `feature/hull-curve` into `main`, after the gates and the user's OK.
3. The JARVIS live test of the voice, B1/B2 and semi-live fixes. Commit the working-tree JARVIS changes on the user's word.
4. Then: the JARVIS voice plan, persona plan and refactor plan (in that dependency order).
5. Wake-word recordings (J6, H2-H4) need the user's recordings.
6. GOD mode needs approval, model downloads (G0) and wiring.
7. The UI improvement list (`UI-handoff.md` §12) and Phase 3 assets: art, video and sounds from the user.

**Never done:**
- push of the recent work;
- deploy/cutover of CSpace as the default HUD;
- autostart (deferred on purpose).

---

## 19. Lessons from the process

1. **Pixel-matching needed a reference the owner drew.** Three rebuilds on day one (reference copy → edge overlay → the owner's own window drawing) converged only once the source of truth was the user's drawing, mirrored.
2. **A single master plan beats chat memory.** `JARVIS-Repair-Plan.txt` let any new session resume a phase cold. Later tracks copied the pattern: handoff docs, PM logs, "read first" lists.
3. **Refactor before adding features, in reversible steps.** R1 made the tests split-safe first. Then R2-R14 moved one area per commit, so every step could be reverted on its own.
4. **Safety rules come from incidents.** The recycle-bin test led to "fake first, dry run first". The lock action was faked twice more.
5. **Triage outside reports; don't apply them.** The Gemini migration spec had five critical design errors and invented numbers. Gemini's perf report suggested removing a library that was not installed. Checking each claim against the code saved large amounts of wrong work.
6. **Measure, then promise.** Unmeasured targets were dropped. Real measurements drove fixes: the IOException 5x/s, the 65 CTM reads/s, the 83 % mid-sentence TTS seams, the music ring's 10 s of jumps. The biggest remaining gap is that GPU has only been measured headless.
7. **Cheaper models need a review gate.** Haiku's 25 port commits passed unit tests but had never been seen. Parity rounds against the real skin and the user's screenshots found the gaps.
8. **Parity first, then restyle.** CSpace matched Rainmeter feature by feature ("as `<file>.lua` does") before any visual overhaul. So the realism work changed the look without losing behaviour.
9. **Separate sessions need hard file boundaries.** Once the UI and JARVIS sessions ran in parallel, each handoff listed the other's files as untouchable.
10. **The user's direction is recorded verbatim.** "Keep the base frame", "the music ball moves weirdly", "condense most hints" were saved as memory and quoted in plans, so later sessions didn't drift into a redesign.

---

## 20. Appendix: commit map by stage

| Stage | Dates | Approx. commits | First → last |
|---|---|---|---|
| 1 Skin build + PRs | Oct 9-10 | 42 | `5db0b93` → `6bff4c9` |
| 2 Owner iteration, JARVIS appears | Oct 10-13 | 4 | `831634c` → `5d13f41` |
| 3 JARVIS clean-up, Repair Plan 0-6 | Oct 13-14 | 43 | `55ff7e2` → `bd0dd62` |
| 4 Refactor, audits, Phases 7-9 | Oct 15-16 | ~83 | `ad8df7e` → `d88402b` |
| 5 Audit fixes, Clover, Phase 10 | Oct 16-17 | ~25 | `03ac80a` → `4719c4e` |
| 6 Live test, migration, SpaceshipUI, host | Oct 20 | 59 | `d2e8d63` → `87e1ac1` |
| 7 Module port, CSpace named | Oct 21 | 31 | `6672940` → `06e20d5` |
| 8 PM run, audit, parity | Oct 25-26 | 76 | `d647f8e` → `fa0e646` |
| 9 Feature sweep, wallpaper, QoL | Oct 29-30 | 32 | `ee9dc35` → `ce42b3e` |
| 10 Visual overhaul + realism R1-R11 | Nov 2 | ~39 | `84d4c44` → `296c8ed` |
| 11 Hyperreal, Blender, clean-up | Nov 2-3 | ~38 | `d0bef9c` → `7e92f2a` |

To list any stage's commits: `git log --reverse --format="%ad %h %s" --date=short <first>^..<last>`.
