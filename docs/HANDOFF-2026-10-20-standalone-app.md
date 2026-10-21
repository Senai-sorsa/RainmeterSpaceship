# Handoff: standalone Spaceship app (2026-10-20)

Read this first, then `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md`, then `tasks/spaceship-migration-plan-v2.md`.

## Rules that still apply
- No live run on the desktop without the user's explicit go. Say what the run does first.
- Fake first, dry run first. Destructive Windows calls (power, recycle bin, process kill, file deletion, registry) get fakes in tests only.
- No blind `git add .`. Never `git add` `Skins/Spaceship/@Resources/Settings.inc` (skip-worktree, personal paths). Never commit weights, logs or secrets.
- Commit only when asked. Never merge, push or deploy without asking.
- Do not kill processes the user did not ask about. The permission system denied a process-stop attempt earlier; ask instead.
- Phase 10 personality work needs the user's hand-review first.

## What the user asked for (latest)
1. A standalone app, not Rainmeter: own Start / Stop / Quit like Rainmeter, a reliable tray.
2. Ctrl+Alt+1 immediately stops everything this app started (kill switch), so testing cannot lock the user out.
3. The window covers the whole screen, under the taskbar (Rainmeter "On desktop" behaviour).
4. Fix all audit issues, then finish the remaining migration phases before the live test.
5. The user approved the design (with the full-screen change). The live test has not run.

## State on disk (all UNCOMMITTED, HEAD is `215e500`)
| Path | Status | Purpose |
|---|---|---|
| `SpaceshipApp/ShipCore.App/Program.cs` | new | Standalone host: transparent window, WebView2 via DirectComposition, tray Start/Stop/Quit, Ctrl+Alt+1 hotkey thread, kill-tree switch, WorkerW attach, home-display pick, log cleanup, perf CSV |
| `SpaceshipApp/ShipCore.App/ShipCore.App.csproj` | new | net10.0-windows WinForms, WebView2 1.0.3179.45, refs ShipCore.Core |
| `SpaceshipApp/ShipCore.Core/KillSwitch.cs` | new | Runs the kill once per process |
| `SpaceshipApp/ShipCore.Core/HostRules.cs` | new | `PickHomeDisplay`, `ExpiredLogs` (no Windows types) |
| `SpaceshipApp/ShipCore.Core.Tests/KillSwitchTests.cs` | new | fake kill action |
| `SpaceshipApp/ShipCore.Core.Tests/HostRulesTests.cs` | new | display and log rules |
| `SpaceshipApp/ShipCore.Proto/Program.cs` | modified | P-D prototype: `RootVisualTarget` COM fix, UI-thread guard, error dialog |
| `CLAUDE.md`, `.gitignore`, `.graphifyignore` | modified | TokenWise lines removed (earlier session) |
| `tasks/spaceship-migration-plan-v2.md` | modified | earlier edit (not reviewed this session) |
| `Skins/Spaceship/@Resources/Settings.inc` | modified, personal | line 196 `JarvisAutoStart=0` (was 1). Restore to 1 when the user says |
| `CLAUDE.md.tokenwise-backup-20261013-113305` | untracked | four rules missing from current CLAUDE.md; user decides keep or delete |
| `docs/HANDOFF-2026-10-20-standalone-app.md` | new | this file |

Tests: `dotnet test SpaceshipApp/ShipCore.Core.Tests` -> 86 passed, 0 failed (run 2026-10-20). `dotnet build SpaceshipApp/ShipCore.App` -> 0 errors, 1 known MSB3277 WindowsBase warning.

## Verified vs not verified
Verified (by build or test only):
- Core logic: kill once, display choice, log expiry.
- App compiles. Destructive-call scan: the only process kill is `Process.GetCurrentProcess().Kill(entireProcessTree: true)`, reached only from the hotkey.

NOT verified (needs the live run, user watching):
- Window appears; WorkerW attach puts it under desktop icons and the taskbar draws over it.
- Click-through outside the 360x220 panel; the button counts clicks.
- Ctrl+Alt+1 kills the app and its WebView2 children (`msedgewebview2` with the app as ancestor); no leftover processes.
- Tray Start / Stop / Quit; Stop releases the web view; sign-out not blocked.
- `js_fps` near refresh rate; CPU/GPU compared with Rainmeter on the same run.
- Whether Ctrl+Alt+1 is free on the user's machine.

Live check script (already written, not run): `C:\Users\Senai\.claude\jobs\bd35207b\tmp\live-check.ps1`. It launches the app, lists its tree, reads the perf CSV, presses Ctrl+Alt+1 via SendKeys, and checks what is left. A 90 s watchdog stops only its PID. Its launch and keypress were denied by the permission system in the last session, so the user may need to run it with `!` or approve it.

## Known issues / decisions still open
- **Auto-hide taskbar:** WorkingArea is not used any more, so the window sits behind the taskbar. Behaviour with auto-hide is unverified.
- **Multi-monitor:** the home display is chosen by size 2560x1600 (hard-coded in `Program.cs`, should come from `HomeSize` in Settings.inc). Falls back to primary.
- **Orphaned WebView2 processes:** the tree kill only reaches children still linked to the app. Unverified.
- **Hotkey conflict:** if Ctrl+Alt+1 is taken, one balloon tip and no retry.
- **Ghost tray icon:** the kill switch ends the process without tray cleanup; Windows usually clears it on hover.
- **Sign-out:** `WM_QUERYENDSESSION` returns 1, `WM_ENDSESSION` quits. Unverified.
- Rainmeter ZPos -2 / WorkerW reference: docs https://docs.rainmeter.net/manual/settings/skin-sections/ and forum https://forum.rainmeter.net/viewtopic.php?p=206049. The WorkerW mechanism is from general knowledge, not a primary source.
- `JarvisAutoStart=0` in Settings.inc (see table).

## Migration plan status (`tasks/spaceship-migration-plan-v2.md` section 6)
- P-0 DONE. P-A DONE (feature branch). P-B DONE on `feature/setup-control-center`, not merged to main. P-C mostly done.
- **P-D** gate: prototype fixed; checklist items 1-9 NOT run. Needs the live run. Decision rules are in `docs/P-D-PROTOTYPE.md`. The plan's FAIL note is stale until the rerun.
- **P-E** host shell: window, tray, hotkey, kill are in the new app. Missing: ConfigStore wiring, HKCU Run glue (AutoStart in Core), exam-process visibility with real window snapshots (`IWindowSnapshotSource`), named pipes, ProcessFailed handling.
- **P-F** module ports (35 skins, parity diff each). NOT started in the host. Largest phase.
- **P-G** JARVIS integration: BUG-01 change, pipe client, contract tests. NOT started.
- **P-H** opt-in cutover: HKCU Run, 6-hour soak, rollback drill, explicit user approval to deploy. Cannot be finished before a live test.

## Next steps (in order)
1. User decides: merge `feature/setup-control-center`? (not without asking). Commit the new files and the prototype change? (ask).
2. Live run of the app, with the user watching: placement, click-through, kill switch (see live-check). Record results in this file.
3. P-D checklist items 1-9 on the same run, using the app or the prototype, per `docs/P-D-PROTOTYPE.md`.
4. Fix whatever the live run shows. Re-run `dotnet test` and the build after each fix.
5. P-E glue, then P-G pipe client against a Python stub (fakes first).
6. P-F, batch by batch, each with a parity diff. Needs the user's sign-off per batch.
7. P-H only after explicit approval.

## Rollback
- Standalone app: delete `SpaceshipApp/ShipCore.App/`, `ShipCore.Core/KillSwitch.cs`, `ShipCore.Core/HostRules.cs`, and the two new test files.
- Prototype: `git checkout -- SpaceshipApp/ShipCore.Proto/Program.cs`.
- Jarvis: set `JarvisAutoStart=1` in `Skins/Spaceship/@Resources/Settings.inc` (user's call).
- Rainmeter skin: untouched except Settings.inc above; `Skins/Spaceship` still loads under Rainmeter.

## Complete remaining work (everything not done)

### A. Skipped in the last session (live or Windows-only)
1. **Live run of the standalone app** (user watching). Launch, then check each of these and write the result beside it:
   - window appears with the desktop visible (no black or white rectangle)
   - window sits under desktop icons and normal windows, and the taskbar draws over it
   - clicks outside the 360x220 panel reach the desktop
   - the panel button counts clicks
   - Ctrl+Alt+1 stops the app and every `msedgewebview2` child that has it as an ancestor
   - tray Start / Stop / Quit each do what they say; Stop releases the web view
   - sign-out and restart are not blocked
   - `js_fps` in the perf CSV near the monitor refresh rate
   - CPU and GPU compared with Rainmeter on the same idle desktop, 5 minutes each (`tools/gpu_baseline.ps1`)
   - Ctrl+Alt+1 is free on this machine (balloon tip absent)
2. **Live-check script not run.** `C:\Users\Senai\.claude\jobs\bd35207b\tmp\live-check.ps1`. Its launch and SendKeys step was denied by the permission system. Either the user runs it with `!`, or the user approves it.
3. **P-D checklist items 1-9** (`docs/P-D-PROTOTYPE.md`). Not run. Items 6 (lockdown browser) and 9 (baselines) need the user. The plan's "P-D FAIL" note in `tasks/spaceship-migration-plan-v2.md` line 80 is stale until a rerun is recorded.
4. **Taskbar auto-hide case.** Unverified. With auto-hide on, the window may cover the taskbar edge.
5. **Multi-monitor.** The home display is hard-coded to 2560x1600 in `Program.cs`. It should read `HomeSize` and `HomeMonitor` from `Settings.inc`.
6. **Orphaned WebView2 processes.** The tree kill may miss any child that got detached. Needs a check after the live run.
7. **Hotkey conflict path.** Not tested: what happens when Ctrl+Alt+1 is taken. There is no retry.
8. **Ghost tray icon** after the kill switch. Expected, but unverified.
9. **WorkerW attach fallback.** If WorkerW is not found, the code falls back to HWND_BOTTOM, which is not verified to stay under the taskbar.
10. **Stuck PowerShell processes** from the earlier gpu_baseline run (PIDs 53856, 16452). Gone at the last check. Confirm before the live run.
11. **Rainmeter ZPos -2 mechanism** is from general knowledge (WorkerW). Confirm against a source or the Rainmeter source before relying on it.

### B. Code not written (P-E to P-H, plan section 6)
12. **P-E host shell glue:** ConfigStore wiring (read and atomic write of Settings), HKCU Run through `AutoStart` in Core, exam-process visibility using real window snapshots (`IWindowSnapshotSource`), named pipes, ProcessFailed handling, and the Lifecycle tray menu the Core already defines (the app's own menu is used now).
13. **P-F module ports.** Each of the 35 skins ported to the UI with a parity diff against the rmsim render of the real skin. Also: the data feed (CPU, GPU, network, etc.) that Rainmeter measures supplied; the host must replace them. The UI scaffold (P-B) is on `feature/setup-control-center`, not main.
14. **P-G JARVIS integration:** BUG-01 change (`rainmeter_running()` also true when host IPC is live), pipe client, contract tests against a Python stub.
15. **P-H cutover:** HKCU Run entry, 6-hour soak, rollback drill. Needs explicit approval before deploy.

### C. Git and repo decisions (need the user)
16. Commit the new `ShipCore.App`, `ShipCore.Core` (`KillSwitch.cs`, `HostRules.cs`) and test files, plus the prototype change. Not committed.
17. Merge `feature/setup-control-center` into main (P-A/P-B work). Not merged. Not without a yes.
18. Keep or delete `CLAUDE.md.tokenwise-backup-20261013-113305`. It holds four rules missing from the current CLAUDE.md: wait for approval before the first repair; preserve uncommitted work; no commit, push, merge, release or deploy without approval; and the TokenWise line.
19. Untrack `.tokenwise/log.ndjson` (tracked since commit `bdfb8fb`) or leave it.
20. `tasks/spaceship-migration-plan-v2.md` has an uncommitted change not reviewed this session.
21. Whether `generated/` (UI exporter output) is git-ignored (the plan says yes; not confirmed).
22. `sudo apt install dotnet-sdk-10.0` (plan section 8, item 1): it was for the Ubuntu VM. This Windows machine has the SDK, so likely unneeded. Confirm.
23. Plan section 8, item 2: P-D before P-C was the recommendation. P-C is mostly done; confirm the order is accepted.

### D. Settings and restores
24. `Skins/Spaceship/@Resources/Settings.inc` line 196: `JarvisAutoStart=0`, changed for the measurement. Restore to `1` when the user says. Personal file, skip-worktree: never `git add`.

### E. JARVIS (separate track, not the migration)
25. **Phase 10B** Windows verification: `py -3 -B test_jarvis.py` has not run on Windows since commit `bdfb8fb`. Its fakes were tested before a crash, not re-verified.
26. **Phase 10 slice 2** (`tasks/phase10-slice1-plan.md` indexes it). Slice 1 is committed (`7ddc7a9`), not live, not pushed.
27. **Phase 10 personality work** needs the user's hand-review before any of it.
28. **Phase 11 and UI Phase 1** not started; each needs the user's go.
29. **Live tests of JARVIS** wait until the user's go (memory: since 2026-10-15).
30. **Phase 9** built 2026-10-16; no live test recorded.

### F. Ponytail "not checked" items from this session (carry forward)
31. Animation and CPU/GPU baselines (see A1).
32. Multi-monitor and auto-hide taskbar (see A4, A5).
33. Whether the earlier lock-out came from the prototype or from the Rainmeter skins. Unknown. The live test should run with the kill switch ready.

## Start a new session with
```
cd C:\Users\Senai\RainmeterSpaceship
git status --short
dotnet test SpaceshipApp\ShipCore.Core.Tests\ShipCore.Core.Tests.csproj
dotnet build SpaceshipApp\ShipCore.App\ShipCore.App.csproj
```
