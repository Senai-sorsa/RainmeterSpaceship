# Start here: the Windows session

For a Claude Code session that starts on the Windows PC that runs Rainmeter, after `git pull` of `main`. Everything was written on an Ubuntu VM; **nothing Windows-side has ever run** (no Rainmeter, no WebView2, no PowerShell, no C# window). Treat every Windows behaviour in the docs as a hypothesis until you see it.

## 0. First five minutes
1. Read `CLAUDE.md`, `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md` (mandatory before any test or script), then `docs/HANDOFF-2026-10-20-session3.md` and `docs/PAUSED-2026-10-20.md`.
2. `git pull` on `main`; confirm `git log --oneline -3` matches what the user expects.
3. Run `powershell -ExecutionPolicy Bypass -File tools\windows\preflight.ps1` (read-only). If something is missing (dotnet SDK 10, WebView2 runtime), tell the user and ask before installing anything (project rule: no installs or system changes without approval).
4. Ask the user what they want first. The planned order is: (a) the prototype run, (b) UI changes, (c) JARVIS Phase 10B and 11.

## 1. The prototype run (P-D)
`docs/P-D-PROTOTYPE.md` has the checklist. Short: `cd SpaceshipApp` then `dotnet run --project ShipCore.Proto`. It is a transparent, click-through, animated window; quit from the tray icon. Afterwards `tools\windows\collect-pd-results.ps1` writes `%TEMP%\spaceship-pd\report.txt` (hardware, CSV averages, WebView2 process count). The user supplies PASS/FAIL for each checklist item and the Task Manager CPU/GPU numbers, Rainmeter vs prototype. Do not interpret numbers you did not see.
- GO: record it in `tasks/spaceship-migration-plan-v2.md`, then plan P-E (write goal/scope/non-goals/acceptance/validation/risks/rollback and wait for a go).
- NO-GO: stop, keep Rainmeter, say so plainly.
- If the first run crashes, fix from the error text. A known untested spot: the DirectComposition COM calls in `ShipCore.Proto/Program.cs` (vtable slots 3, 6, 7), and `CoreWebView2CompositionController` usage.

## 2. Tests that can run on Windows
- UI: from `SpaceshipApp\SpaceshipUI`: `npm install` (first time; needs the user's OK), `python -I ..\..\tools\export_ui_assets.py` (the `src\generated` folder is git-ignored), then `npx tsc --noEmit`, `npm test`, `npm run test:e2e` (Playwright needs its browsers: `npx playwright install chromium`, ask first). One heavy command at a time.
- C# core: `dotnet test SpaceshipApp\ShipCore.Core.Tests` (83 tests passed on Ubuntu).
- Python tools: `py -3 -I tools\test_contract_check.py`, `py -3 -I tools\test_launch_target.py`, `py -3 -I tools\test_export_ui_assets.py`.
- JARVIS: `py -3 -B Skins\Spaceship\@Resources\Jarvis\test_jarvis.py` has NOT been run on Windows since Phase 10B (owed by the user). It is about 4,000 lines and touches system actions: read `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md`, grep it for real recycle bin, power, sleep, Bluetooth, registry, process-kill and file-deletion calls, confirm fakes are installed first, and tell the user before running it.
- Rainmeter-side checks that only Windows can do: the calendar change (ring smaller and left, `10:24AM` times), the hover-hint cleanup (21 files; hovering everything once is the real test), and the Kokoro SHA-256 check in `Jarvis\Setup-Jarvis.ps1`. Ask the user to look and report; do not claim they work.

## 3. Open items waiting on the user
Windows `test_jarvis.py` run; confirmed lockdown-browser process names (`contract/exam-browsers.json`, from Task Manager > Details while the browser runs); the rest of the GPU-spike sentence ("Why does GPU usage spike whenever I actively ..."); what looks inaccurate about the music/noise ball; whether to keep Rainmeter commit `003b6f4`; the module-position question in PICTURE frame mode; what "Phase 12" meant (the repair plan ends at Phase 11).

## 4. Rules that still apply
Never merge or push without asking. Smallest change; no destructive git; no deploying without approval. Performance claims need measurements, labelled as such. Subagents only where they save tokens. Commit messages end with the attribution line the session gives. `git status --porcelain -- Skins` should be empty unless a skin edit was approved (the calendar, hints, launch allowlist and Kokoro hash edits were).
