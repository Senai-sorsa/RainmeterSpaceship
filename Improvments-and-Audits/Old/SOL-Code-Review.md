# JARVIS / Rainmeter Spaceship — Comprehensive Forensic Code Audit

> **Audit status:** IN PROGRESS — this report is being maintained as evidence is verified.  
> **Audit mode:** Read-only except for this designated report. No source, configuration, test, build, or runtime-data file may be modified.

## 1. Audit metadata and scope

| Item | Value |
|---|---|
| Repository root | `C:/Users/Senai/RainmeterSpaceship` |
| Branch | `chore/jarvis-baseline-and-performance` |
| Audited commit | `8bd241fa44bf81d76c927325bcf3758a47db5427` |
| Commit date / subject | 2026-10-15; `JARVIS plan: Phase 3 left-overs into Phases 7-10, GUI automation review (S2-14), Phase 7 handover` |
| Audit date | 2026-10-15 |
| Python | 3.12.10 |
| Git | 2.55.0.windows.5 |
| Primary application | `Skins/Spaceship/@Resources/Jarvis/` |
| Report | `SOL-Code-Review.md` |

### Pre-existing working-tree state

Before this report was created, `git status --short --branch` showed:

- Branch tracking `origin/chore/jarvis-baseline-and-performance`.
- Untracked `.continue/`.
- Untracked `GPT terra review.txt`.
- Untracked `opus 4.8 Code review.md`.

These paths predate this audit and are preserved. `SOL-Code-Review.md` is the only project artifact created by this audit.

### Scope rationale

The connected scope starts at the active Python service (`Jarvis/jarvis.py`) and includes reachable `jarvislib` modules, its tests and setup/dependency files, the Rainmeter/Lua launch and IPC surfaces, the JARVIS overlay, relevant settings, and the PowerShell/C# helper paths that produce shared data consumed by JARVIS. Backup trees under `@Resources/Backups/` and the nested `Skins/Spaceship/Spaceship/` copy are excluded from implementation review unless active references prove they participate at runtime. Personal/runtime data files under `@Resources/Data/` are treated as interfaces only; their sensitive contents are not copied into this report.

Graphify artifacts exist under `graphify-out/`; the latest report is dated 2026-10-14. It reports 1,621 nodes and 3,313 edges, with 13% inferred edges. Graphify is used as a navigation aid, not treated as proof. Its configuration excludes backups, the nested skin copy, and runtime Data files.

## 2. Executive summary

**Provisional.** The audit is not yet complete. The prior review's broad “Architecture Verdict: Strong” is not adopted as an audit conclusion until the complete connected implementation and critical paths have been independently inspected.

The documented architecture claims a valuable security invariant: model output has no direct action authority and AI interpretations are revalidated through deterministic routing. This and all other critical invariants remain hypotheses pending direct end-to-end verification in the current source.

## 3. System inventory and preliminary dependency map

Documented process architecture, pending code verification:

1. Rainmeter HUD invokes `@Resources/Scripts/jarvis.lua`.
2. Lua resolves and starts `@Resources/Jarvis/jarvis.py`.
3. Python imports the `jarvislib` package for routing, actions, confirmation, LLM, audio, voice, memory, reminders, persistence, diagnostics, and prompt construction.
4. Rainmeter and Python exchange commands/status through files under `@Resources/Data/`.
5. `core.ps1` builds/starts `ShipCore.cs`; ShipCore produces system state including the window list consumed by JARVIS action handling.
6. `Overlay/Jarvis/` displays the assistant status/log surface.
7. `control.lua` and `Settings.inc` configure JARVIS.

Preliminary shared-file contracts from documentation, all pending direct producer/consumer verification:

| Interface | Documented producer | Documented consumer |
|---|---|---|
| `Data/jarvis_cmd.txt` | `jarvis.lua` | `jarvis.py` |
| `Data/jarvis.txt` | `jarvislib/base.py` | `jarvis.lua` / overlay |
| `Data/jarvis_env.txt` | HUD | Python speech/mute logic |
| `Data/jarvis_log.txt`, `jarvis_live.txt` | Python | `jarvislog.lua` |
| `Data/windows.txt` | ShipCore | Python action layer |
| `Settings.inc` | Rainmeter/control scripts and setup | Python/Lua/Rainmeter |

## 4. Methodology and limitations

Work completed so far:

- Recorded repository root, branch, commit, working-tree status, Python and Git versions.
- Inventoried the active JARVIS tree, cross-language integration files, Graphify artifacts, documentation, tests, and duplicate/backup trees.
- Read the opening/current-state portions of `CLAUDE.md`, `README.md`, architecture/stabilization document, repair plan, task plans, Graphify report, and the complete existing review.
- Did not read private runtime-data contents.
- Did not run the application, audio paths, Ollama, ShipCore, or destructive actions.
- No test has yet been run in this audit. Documentation describing old test results is historical evidence, not a current result.

Environmental limitations currently known:

- Real microphone, speaker, wake-word, GPU fallback, Rainmeter, Ollama, and Windows action behavior cannot be inferred as verified merely from static inspection.
- Importing `jarvis.py` reportedly writes runtime state; tests must therefore be isolated before execution.
- The active source is not necessarily the deployed live Rainmeter copy according to project documentation; repository behavior and deployed behavior may differ.

## 5. Coverage ledger

Statuses reflect actual inspection, not planned work.

| Component | Responsibility / connection | Status | Important dependencies / callers | Tests / findings / uncertainties |
|---|---|---|---|---|
| `CLAUDE.md` | Repository audit and safety instructions | INSPECTED | Applies repository-wide | Initial audit rules confirmed |
| `README.md`, `docs/PLAN.md`, task docs | Product behavior and design history | PARTIALLY INSPECTED | Documentation only | Must reconcile current implementation |
| `JARVIS-Architecture-and-Stabilization.md` | Current documented architecture and tests | INSPECTED | Describes active code at branch baseline | Claims require code verification |
| `JARVIS-Repair-Plan.txt` | Detailed history/contracts/known issues | PARTIALLY INSPECTED | Repository-wide | Large historical document; current-state and constraints read |
| `opus 4.8 Code review.md` | Prior security/robustness findings | INSPECTED | Historical review | Seven concerns queued for reconciliation |
| `GPT terra review.txt` | Prior forensic report lead | INSPECTED | Empty file | No findings to reconcile |
| `.graphifyignore`, `graphify-out/GRAPH_REPORT.md` | Dependency-map configuration/report | INSPECTED WITH LIMITATIONS | Static graph, partly inferred | Graph JSON/query details not yet inspected |
| `Jarvis/jarvis.py` | Entry point and orchestration | NOT STARTED | All main subsystems | Critical |
| `Jarvis/jarvislib/base.py` | Paths, settings, state, logging, lock, file writes | NOT STARTED | Broadly imported | Critical |
| `Jarvis/jarvislib/routing.py` | Deterministic and model-assisted routing | NOT STARTED | Main command flow | Critical |
| `Jarvis/jarvislib/actions.py` | OS actions | NOT STARTED | `run_action` orchestration | Critical |
| `Jarvis/jarvislib/confirm.py` | Affirmative interpretation | NOT STARTED | Destructive confirmation | Critical |
| `Jarvis/jarvislib/llm.py` | Ollama integration/cancellation | NOT STARTED | Routing/chat/memory | Critical |
| `Jarvis/jarvislib/hearing.py` | Whisper transcription/filtering | NOT STARTED | Mic/turn pipeline | Critical |
| `Jarvis/jarvislib/mic.py`, `audio.py` | Capture and endpoint control | NOT STARTED | Turn/speech pipeline | Critical |
| `Jarvis/jarvislib/speech.py`, `tts.py`, `stopwords.py`, `stopkey.py` | Speech, TTS, interruption | NOT STARTED | Turn pipeline | Critical |
| `Jarvis/jarvislib/prompt.py` | Prompt/context assembly | NOT STARTED | LLM chat | Critical |
| `Jarvis/jarvislib/memory.py`, `turnstate.py` | Durable/conversation state | NOT STARTED | Prompt/turn/routing | Critical |
| `Jarvis/jarvislib/reminders.py`, `notes.py`, `todo.py` | Reminder/note/task features | NOT STARTED | Routing/turn | Critical |
| Remaining `jarvislib` modules | Search, meaning, calculations, diagnostics, GPU | NOT STARTED | Capability/support paths | In scope |
| `Jarvis/test_jarvis.py` | Main test harness | NOT STARTED | Active Python implementation | Safe isolated execution must be assessed |
| `Jarvis/Setup-Jarvis.ps1`, requirements, `check_voice.py` | Install/dependencies/diagnostics | NOT STARTED | Deployment and voice setup | In scope |
| `Scripts/jarvis.lua`, `jarvislog.lua` | Launch, IPC, HUD/log control | NOT STARTED | Rainmeter/Python boundary | Critical |
| `Scripts/control.lua`, `lib.lua` | Settings/control/shared Lua helpers | NOT STARTED | Rainmeter/JARVIS configuration | Critical relevant portions |
| `Settings.inc`, JARVIS overlay files | Configuration and presentation | NOT STARTED | Lua/Python/Rainmeter | Critical relevant portions |
| `Scripts/core.ps1`, `ShipCore.cs` | Build/start helper; shared system state | NOT STARTED | Window/action integration | Relevant portions critical |
| Backup and nested duplicate trees | Historical/packaged copies | INSPECTED WITH LIMITATIONS (scope only) | No active reference established | Excluded unless references prove active |

## 6. Prior-finding reconciliation ledger

No historical concern is considered confirmed for this audit until checked against current source.

| Historical item | Prior characterization | Current audit status |
|---|---|---|
| H-01: PowerShell single-quote handling in `tts._windows()` temp path | Concrete low-severity robustness/local parsing issue | UNVERIFIED — source not yet rechecked |
| H-02: Prompt injection through contextual account/note/window data | Low, limited by no action authority; design tradeoff | UNVERIFIED — authority boundary and prompt construction not yet rechecked |
| H-03: No `fsync` in `write_atomic()` | Informational/acceptable | Pending confirmation; not presumptively a defect |
| H-04: Newlines in reminder labels can corrupt line store | Latent low issue; normal voice path reportedly unreachable | UNVERIFIED — producers/load failure handling not yet rechecked |
| H-05: Set-operator precedence in `memory.recompact()` | Behavior-neutral informational concern | UNVERIFIED — must avoid reporting as defect absent behavior impact |
| H-L1: Quote handling in `jarvis.lua` service launch bang | Concrete low–medium local robustness/parsing concern | UNVERIFIED — launch syntax and reachable source not yet rechecked |
| H-L2: Device/model names persisted to `Settings.inc` | Latent low hardening concern | UNVERIFIED — producer, line parsing, and Rainmeter behavior not yet rechecked |

## 7. Findings summary

No finding has yet met this audit's evidence threshold. Historical concerns remain in the reconciliation ledger rather than being duplicated here.

| ID | Title | Classification | Severity | Confidence | Priority | Main location | Status |
|---|---|---|---|---|---|---|---|
| — | No independently verified finding recorded yet | — | — | — | — | — | Audit in progress |

## 8. Verified-correct behavior and safeguards

None independently verified against the complete current execution path yet. Documented safeguards (LLM revalidation, local confirmation state, action exit-code checks, single-instance locking, bounded caches, and atomic replacement) are queued for inspection and are not yet audit conclusions.

## 9. Unresolved questions and next inspection targets

1. Verify the actual imports and launch path from Rainmeter to `jarvis.py`.
2. Trace command routing, AI interpretation, action whitelist, destructive confirmation, and final execution authorization.
3. Trace wake/click command IPC freshness, cancellation, turn/thread lifecycle, and state restoration.
4. Trace speech/TTS/cancellation and microphone ownership.
5. Trace reminder and memory persistence, corruption handling, and concurrent access.
6. Verify shared-file contracts producer-to-consumer.
7. Reconcile every prior concern against current code.
8. Inspect test realism and run only safely isolated static/tests after side effects are understood.

## 10. Final audit completeness statement

**INCOMPLETE.** Baseline, initial architecture inventory, Graphify availability, prior-review ingestion, and scope establishment are complete. Implementation inspection, critical-path tracing, safe validation, and findings reconciliation remain in progress.