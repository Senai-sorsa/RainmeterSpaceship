# Standalone app architecture (replaces the P-F and P-H sign-off model)

Status: plan, written 2026-10-20. Supersedes the per-batch sign-off in `docs/HANDOFF-2026-10-20-standalone-app.md` (P-F) and the cutover wording in `tasks/spaceship-migration-plan-v2.md` section 6.
Owner decision: the user asked for the host to be its own app, not part of the system, with guardrails so it can be switched off and tested safely.

## Why the per-batch sign-off existed, and what replaces it
- It was a review gate: the user checks each batch visually against the Rainmeter skin. It was a process choice, not a technical limit.
- It is dropped. Work proceeds in the repo without asking per batch.
- Still required, from `CLAUDE.md`: no live run on the desktop without an explicit go; no deploy without explicit approval; no change to Rainmeter's own files or the global Claude config.
- Parity is checked with `tools/rmsim.py` and `tools/parity_diff.py` (a simulator). Simulator parity is not proof that the real Rainmeter look matches. Real parity needs one live run, which needs the go.

## Shape of the app
- `ShipCore.App` is a separate Windows process. Rainmeter does not load it, and it does not load Rainmeter. Both can be installed and running at once.
- Its own data folder: `%LOCALAPPDATA%\Spaceship\` (config, logs, cutover state). It never writes into `Skins\` or Rainmeter's `Rainmeter.ini` except through `tools\windows\Switch-HudHost.ps1`.
- Its own log: `%TEMP%\spaceship-app\perf-*.csv`, kept 7 days.
- Its own pipe for JARVIS: per-run name, nonce and session file, verified by pid (`JarvisPipe.cs`, `jarvislib/host_pipe.py`).
- Modules are data-driven: each module reads a data source behind an interface (`Core`) and renders in the UI. No module calls the OS directly.

## Current state (read-only check, 2026-10-20)
- Nothing installed: no `SpaceshipHud` entry in HKCU or HKLM Run, no scheduled task, no startup shortcut, no ShipCore process running, no WebView2 processes from the prototype folder.
- Two apps exist and must not be confused:
  - `SpaceshipApp/ShipCore.Proto` is the P-D prototype. A full-screen transparent WebView2 window at the bottom of the z-order, with a tray icon. Started only by hand (`dotnet run`). Its tray has Quit and no "Switch to Rainmeter" entry.
  - `SpaceshipApp/ShipCore.App` is the standalone host this plan targets. Its tray menu is Start, Stop, Start with Windows (off), Quit. It has no "Switch to Rainmeter" entry either; that is P-H work.
- Autostart code exists (`ShipCore.Core/AutoStart.cs`). Nothing calls it on startup. It is opt-in.
- The Rainmeter skin does not launch either app. The only link is the planned switch script, which is manual.
- Corrections to the earlier report: the Proto's UI-thread and COM pointer fixes are committed (`0d12860`), not uncommitted. Nothing in `ShipCore.Proto` is uncommitted. `ShipCore.App/Program.cs` is also committed (`57b71bd`, `f74c86e`).
- Confirmed uncommitted: `Settings.inc` `JarvisAutoStart` is `0` (was `1`). That is the voice assistant's autostart, not the UI. Restore to `1` only when you say.
- Unverified: the full-screen window may cover or interfere with the desktop and other apps underneath. The WebView2 and DirectComposition calls have never run on Windows, and their vtable offsets are untested.

## Requirements from the read-only check
1. Keep the app separate: its own launch command, and no link from the skin until the user opts in.
2. Make "off" obvious: tray Quit, and closing the window ends all of its processes (verify this live before relying on it).
3. Nothing is added to Windows startup by default. Any autostart stays behind an explicit switch.
4. Any change to these items waits for the user's go.

## Guardrails (each must hold before the next phase)
1. **Off by default.** No autostart. The HKCU Run entry is an opt-in toggle, off until the soak passes and the user approves.
2. **Three ways out:** tray Quit, tray Stop, kill switch Ctrl+Alt+Shift+1 (`KillChord.cs`, `KillSwitch.cs`). Sign-out also stops it (`Lifecycle`).
3. **Watchdog:** the web view is restarted at most 3 times, then the host stops and logs `GIVING_UP` (`Program.cs` ProcessFailed handling). Extend the same limit to the pipe and to module errors.
4. **Modules off until proven:** each module has an enable flag in config, default off. A module turns on only after its unit tests and its rmsim parity pass. Real-desktop enablement waits for the user's live go.
5. **No OS actions from the model or the UI:** `UnwiredHost` throws for power and flows. A new action needs its own plan, confirmation and a fake-first test.
6. **Tests are fake-first and dry-run-first** (`CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md`). No test reaches the recycle bin, power, process kill, registry or file deletion. The switch script's bare run is a dry run.
7. **Measured before cutover:** CPU, RAM, GPU, disk, pipe and animation rate baselines for Rainmeter and for the host, recorded in the handoff with a `perf-*.csv` from the host. The host must not be heavier than Rainmeter on the same run.
8. **Rollback is one command and one revert:** `Switch-HudHost.ps1 -Rollback` reactivates the recorded Rainmeter skins; `git revert` undoes the commits. Neither deletes data.
9. **Separate failure domains:** a host crash must not stop JARVIS, and a JARVIS crash must not stop the host (the pipe is advisory for the host).

## Modules to port (P-F, reframed)
The inventory was counted from `Skins\Spaceship` on 2026-10-20 (excluding `Backups`): 36 `.ini` files, of which 35 are in the skin folders listed below and 1 is elsewhere; 429 `Measure=Script` lines, 1902 `Measure=Plugin` lines, and these core measures: FreeDiskSpace 65, WebParser 42, CPU 35, PhysicalMemory 22, NetIn 22, NetOut 22, Uptime 15, Calc 14.

| Area | Skin files | Order |
|---|---|---|
| Frame + Controller | 2 | 1 |
| Top | 8 | 2 |
| Bottom | 4 | 3 |
| Left | 7 | 4 |
| Right | 7 | 5 |
| Center | 3 | 6 |
| Overlay | 4 | 7 |

Order is by how much each area shows on the desktop. Each module is done when: data source behind an interface, fake-data unit test, rmsim parity diff recorded, feature flag default off.

## Data sources to decide (blockers, not sign-offs)
- Plugin measures (1902 lines) are mostly the HWiNFO/hardware plugin family. The host has no equivalent yet. Decision needed: read HWiNFO's shared memory (needs HWiNFO running and the user's go), or drop hardware sensors from the host and show only what Windows provides. This is a product decision; it is the one item still needing the user.
- WebParser (42 lines) needs an HTTP fetch policy. Decided 2026-10-20, matching the legacy `ShipCore.cs` so existing links keep working: **https only** (`webcal://` is rewritten to `https://`, anything else refused); 30 s timeout per feed; a failed feed is counted as an error and the others still load; window from 6 h ago to 21 days ahead; refresh every 10 min or when `Data\calendar.refresh` appears; links in `%LOCALAPPDATA%\SpaceshipHUD\calendars.dat`, DPAPI CurrentUser with entropy `SpaceshipHUD`, never in code or logs (logs record the label and the error type only); output `Data\calendar.txt` written atomically. Not yet built: the host's fetch and the wiring to `calendarSource.ts`.

## Phases from here
Superseded for phase F by `tasks/standalone-vision-plan.md` (2026-10-20): no Rainmeter in the new app, own settings store, native collectors, and the vision extras per module.
- **A. Guardrails in code:** module enable flags in config (default off), per-module error count into the watchdog, data folder under `%LOCALAPPDATA%\Spaceship`. Fake-first tests. (Next.)
- **B. Frame + Controller port** with rmsim parity. No live run.
- **C. Top, Bottom, Left, Right, Center, Overlay** in the order above, each with parity and flags.
- **D. Measure baseline** of Rainmeter and host (needs live go for the desktop numbers).
- **E. Cutover** (needs deploy approval): HKCU Run opt-in, 6-hour soak (needs go), rollback drill (needs go).

## Status against "complete F, G, H" (2026-10-20)
- **G (JARVIS pipe):** code and fake tests done (`f74c86e`). Not done: a real named-pipe round trip, and any host-to-JARVIS message.
- **H (cutover):** switch script done (`43e685a`), dry run only. Not done, and each needs a live go: `-Apply`, HKCU Run enablement, the 6-hour soak, the rollback drill, and deploy. CLAUDE.md requires an explicit deploy approval even with the general approval for changes.
- **F (ports):** partly done. The host serves the built SpaceshipUI (`3d6c349`), so the real UI is on this branch. The mission clock and HUD caption are ported behind `?module=clock` (`926143b`, off by default, fake calendar feed). Not ported: the other modules; 35 skin modules remain (see the skin's module list). Porting them with parity is weeks of work. Real parity needs a live run.
- **Branch check (2026-10-20):** `origin/feature/setup-control-center` (`dd39bfa`) is an ancestor of `feature/standalone-host`. The branch is 55 commits ahead with 0 divergence. Nothing to merge. The earlier "diverged, 50 files" and "real UI only on origin" notes were wrong.
- **Decisions needed:** (1) none for the merge; (2) the go for live runs; (3) the HWiNFO data-source choice (see above).

## Not done by this plan
- No live run and no `-Apply` of the switch script.
- No HKCU Run change.
- No port of any module yet.
- No merge of `feature/setup-control-center` or `feature/standalone-host`.

## Rollback for this plan
Delete this file. It changes no code.
