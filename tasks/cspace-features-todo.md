# CSpace features to-do (2026-10-29). Plan and decisions: tasks/cspace-features-plan.md

Gates for every task (from SpaceshipApp, then SpaceshipUI):
- `dotnet build ShipCore.App -v q -nologo -clp:ErrorsOnly` 0 errors; `dotnet test ShipCore.Core.Tests` passes
- `tsc --noEmit -p .`, `npx vitest run`, `npx vite build`, `npx playwright test e2e/hud.spec.ts` pass
- Efficiency note in the commit message (RAM/CPU)
- Commit with explicit paths; never main.tsx, ui.css, ui/kit, cspace.ico/png or App Icons/ (another session's changes)

## Task 1: Host reads and checks JarvisPython
**Acceptance criteria:**
- [x] `JarvisStatus.PythonW` takes the Settings.inc value first. It accepts the value only if it is fully qualified, local (no `\\`), named pythonw.exe or pyw.exe, and exists. If the value is set and fails a check, the result is null (NO PYTHON), with no fallback. If it is empty, the current default order is used.
- [x] Program.cs reads the value from Settings.inc itself; it is not added to the page schema
- [x] Unit tests cover: empty → venv; valid → it; relative, UNC, python.exe-named-cmd and missing → null
**Verification:** JarvisStatusTests pass; the Program.cs shortcut comment is removed
**Files:** ShipCore.Core/JarvisStatus.cs, ShipCore.App/Program.cs, ShipCore.Core.Tests/JarvisStatusTests.cs
**Scope:** S

## Task 2: Voice echo and level smoothing on the orb
**Acceptance criteria:**
- [x] lvl is smoothed (0.55 attack, 0.18 release); act goes toward 0.55+0.45·lvl while speaking, 0.25 while thinking, else 0, at 0.25 a tick
- [x] Echo image: Active frames if any, else Idle offset by n/2; size 330·size·(1.12+0.28·lvl); colour mix(col, white, 0.4); alpha act·150; rendered only when act·255 ≥ 3
- [x] A pure-function test for the smoother and the echo parameters
**Verification:** vitest; preview screenshots at ?jarvis=speaking and idle
**Files:** modules/JarvisModule.tsx, modules/jarvis.ts, tests/jarvisEcho.test.ts
**Scope:** M

## Checkpoint A: all gates, preview check, efficiency note

## Task 3: Icons served at run time from the host
**Acceptance criteria:**
- [x] Host maps `@Resources\Icons` to its own virtual host (read-only, DenyCors) and posts `icons.list` {ids, v} on page load and after an icon run
- [x] `appIconUrls` uses the list (undefined until it arrives → line icons); the build-time glob is removed; contract checks the new message
- [x] With no host (preview), the line icons show and there are no broken images
**Verification:** vitest (appIcons + contract), ProtocolTests, vite build size drops about 3.7 MB
**Files:** ShipCore.App/Program.cs, ShipCore.Core/Protocol.cs, SpaceshipUI/src/draw/appIcons.ts, src/host/contract.ts, tests
**Scope:** M

## Task 4: Icon queue, app-icons.ps1 after each scan, and the hourly rescan
**Acceptance criteria:**
- [x] Host builds the IconQueue lines from the catalog (id pattern, shell:AppsFolder or fully qualified existing exe/lnk) and writes them atomically to `Data\IconQueue.txt`
- [x] After ScanApps finishes, app-icons.ps1 runs once (single-run guard, exit code logged), then `icons.list` is posted again
- [x] Rescan every hour while the app runs (controller.lua tick % 3600)
- [x] Unit test for the queue builder (bad ids and paths are dropped)
**Verification:** tests; one manual run against a scratch copy of @Resources, with the output checked before the real folder is ever used
**Files:** ShipCore.Core/AppsFeed.cs (or a new IconQueue.cs), ShipCore.App/Program.cs, tests
**Scope:** M

## Checkpoint B: all gates, dist size, scratch run checked

## Task 5: Fix the out-of-date "not ported" comments and log the round
**Acceptance criteria:**
- [x] Headers corrected in drawer.ts, slot.ts, jarvis.ts, dial.ts, alert.ts, power.ts, strip.ts, graph.ts (only lines that are now false)
- [x] tasks/cspace-pm-log.md entry; memory handoff updated
**Scope:** XS

## Checkpoint: Complete. Report the commands run, the exit codes and the unverified live checks.
