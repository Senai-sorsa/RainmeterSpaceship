# HANDOFF 2026-10-21: CSpace (standalone Spaceship app), audit and redone plan

Read `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md` and `CLAUDE.md` first. This file replaces the plan in
`C:\Users\Senai\.claude\plans\spicy-dreaming-minsky.md` (now a pointer) and corrects
`docs/HANDOFF-2026-10-20-standalone-app.md` (still useful for background, wrong on the kill chord).

The user named the app **CSpace** ("Computer spaceship app"). Their goal: build it so they can *see* it, then finish the
remaining phases. Autostart is deferred on purpose: do not build it yet.

## 1. State right now

- Branch `feature/standalone-host`, 42 commits ahead of `main`, nothing pushed. Latest commit `292fa59`.
- All 25 most recent commits (`26c8b0c` .. `292fa59`) were written by Claude Haiku 5.5 and have had only unit tests, never a
  live look. Treat them as unreviewed (see section 4).
- **Uncommitted, unbuilt edits from this session (the CSpace slice, stopped half way):**
  - `SpaceshipApp/ShipCore.App/ShipCore.App.csproj`: `AssemblyName` CSpace, `Product` CSpace, `ApplicationIcon` Assets\cspace.ico
  - `SpaceshipApp/ShipCore.App/Program.cs`: single-instance mutex `Local\CSpace.SingleInstance` in `Main`, `AppIcon()` (tray icon read from the exe), tray text and form title "CSpace"
  - `SpaceshipApp/ShipCore.App/Assets/cspace.png` and `cspace.ico` (new; made from `Skins/Spaceship/@Resources/Icons/rasaero.png`, one 128 px PNG-in-ICO entry; placeholder art)
  - `tools/windows/Live-Check.ps1`, `Live-Preflight.ps1`, `Switch-HudHost.ps1`: exe/process name `ShipCore.App` -> `CSpace`
  - Not verified: it has never compiled. `docs/LIVE-TEST-STANDALONE.md` and the 10-20 handoff still say ShipCore.App; grep them.
  - Rollback: `git restore SpaceshipApp/ShipCore.App/ShipCore.App.csproj SpaceshipApp/ShipCore.App/Program.cs tools/windows/Live-Check.ps1 tools/windows/Live-Preflight.ps1 tools/windows/Switch-HudHost.ps1`, then delete `SpaceshipApp/ShipCore.App/Assets/`.
- **Build is blocked:** the old app (`ShipCore.App.exe`, PID 18940, started ~16:04 UTC) is still running from
  `SpaceshipApp\ShipCore.App\bin\Debug\net10.0-windows\` and locks `ShipCore.Core.dll` (MSB3027). Ask the user to close it
  (tray Quit, or chord **Ctrl+Alt+Shift+1**). Do not kill it yourself.
- `CLAUDE.md.tokenwise-backup-20261013-113305` is untracked. Leave it; the user decides.
- Verified this session by re-running: `dotnet test SpaceshipApp/ShipCore.Core.Tests/...` exit 0, 166 passed; `npm test` exit 0; `npx tsc --noEmit` exit 0.

## 2. Mistakes found (evidence, then what to do)

1. **The CPU comparison given to the user was invalid. Retract it.** The app was measured at 0.63% of one core, but the
   page it drew was nearly empty. `src/Hud.tsx` (lines ~30-41, 99-108) turns every module on only with `?module=<name>`, and
   `Program.cs` navigates to a bare `index.html`, so only the frame images and a row of test icons rendered. Rainmeter ran
   its full skin. The 0.63% / 485 MB / 231 MB figures are real but describe an empty page. Redo the baseline with the full HUD.
2. **The full HUD cannot be shown at all.** Each module flag is `module === 'x'`, so exactly one module per page, never all.
   This is the main reason the user "does not see" the app. Fix first (section 3, step 1).
3. **The rAF scheduler (`292fa59`) changed animation speed; its commit message says "cadence unchanged", which is false.**
   `tick` sets `j.last = t`, dropping the remainder each time. Simulated with the same logic (not run in a browser):
   the 50 ms centre job gives 17.7/s on 60 Hz (want 20), 18.0/s on 144 Hz, 18.3/s on 165 Hz; the 16 ms boot job gives
   60/s at 60 Hz, 48/s at 144 Hz, 55/s at 165 Hz (want 62.5); the 33 ms Jarvis job gives 27.5-30/s (want 30.3). The user's
   Legion screen offers 165 Hz. Fix: carry the remainder (`j.last = t - ((t - j.last) % j.ms)`, or step by `ms`), add a test at 60/144/165 Hz, then commit.
   `tests/scheduler.test.ts` did not catch it because it uses an exact clock.
4. **Wrong kill chord in docs and memory.** `docs/HANDOFF-2026-10-20-standalone-app.md` (lines 15, 23, 46, 49, 51, 57, 95, 100, 106) says
   Ctrl+Alt+1. Real chord is **Ctrl+Alt+Shift+1** (`ShipCore.Core/KillChord.cs:9`). Fix the doc; memory already corrected this session.
5. **Stale claims in the old plan:** "dial work uncommitted, Phase 1 to do" (it is committed in `f063ce5` and wired in `Program.cs:124`);
   "HomeSize hard-coded 2560x1600" (it is the default of a setting read in `HomeScreen`); a first draft listed a Phase 2 WebP step that needs
   Pillow, which is **not installed** (`python -I -c "import PIL"` fails). A new dependency needs the user's approval.
6. **Rainmeter figure (175% of one core) is unchecked.** It is over 100% for a mostly single-thread app. The sampler maths read as correct
   (100 ns ticks, /1e7), but there was no cross-check with `Get-Process` and the run was only 43 rows (15:59:39-16:03:20, about 3.7 min) against 5 min for the app.
   Real averages from the CSVs: Rainmeter 175.2% (range 145.5-206.1), 8.76% of machine, working set 501 MB, private 450 MB, max 6 processes.
   App (empty page): 0.63%, 0.03% of machine, working set 485 MB, private 231 MB, max 7 processes. (An earlier summary said ~480 MB for Rainmeter; 501 is right.)
7. **No GPU number exists for either run.** `tools/gpu_baseline.ps1` fails with "The data in one of the performance counter samples is not valid" and a first attempt wrote 0 bytes. Cause not investigated.
8. **Commit messages:** `37b91a5` says "hudl.lua" (typo, not amended); `f063ce5` bundles the Phase 0 sampler columns with the dial work and calls WindowsDial "unit-free".
9. **Never run on hardware:** `WindowsDial.cs` (powercfg `/setactive`, `ChangeDisplaySettingsEx`, brightness through a PowerShell/WMI script). Once modules are on, a dial click is a real OS change. Volume, mic and brightness need no confirm dialog; power plan and refresh rate do (`ConfirmAsync`). Tell the user before the first live run.
10. **Leftover in the UI:** `Hud.tsx` always draws a row of test neon icons at y=700 (`ICONS.map`). Remove or hide when the real modules show.
11. `Settings.inc` has `JarvisAutoStart=1` (line 196). The old memory note said it was temporarily 0; it is 1 now. Do not change it without the user's word. The file is skip-worktree and personal: never stage it.

### Notes on each mistake (numbers match the list above)

1. **Invalid CPU comparison.** Cause: the measurement was started before anyone checked what the page drew. Never quote 0.63% / 485 MB / 231 MB without the words "empty page". Redo in Step 2 only after Step 1 shows the full HUD, with the same modules on in both programs.
2. **One module at a time.** Cause: each flag in `Hud.tsx` is its own `=== 'x'` test, written as "off until proven" and never generalised. Keep the single-value form working (existing tests and fixtures use it) and add `all` and comma lists on top. Check `tests/` for anything that reads these flags before changing them.
3. **Scheduler cadence.** Cause: `j.last = t` throws away the part of a frame past the period, and the test clock was exact so it hid this. Fix in `src/host/scheduler.ts`, add a test that feeds frame times for 60, 144 and 165 Hz and checks jobs per second within 3%. Put the correction ("the earlier message said cadence unchanged; it was not") in the new commit body. Do not amend `292fa59`.
4. **Wrong chord in docs.** Cause: the first handoff was written before the chord was read from `KillChord.cs`. After fixing the 10-20 handoff, also grep `docs/` and `tools/` for "Ctrl+Alt+1" and for `ShipCore.App` (the rename).
5. **Stale plan claims.** Cause: the plan was written from memory of earlier notes, not from the code. The old plan file is already replaced by a pointer. Do not restore it. Ask the user before adding Pillow or any package.
6. **Rainmeter 175% unchecked.** Cause: one sampler, no second source, and the run ended early (the "done" signal fired before 5 min). To check: with Rainmeter running (needs the user's go), compare the sampler against `Get-Process Rainmeter` `TotalProcessorTime` over a 10 s window. Run both programs for the same length.
7. **No GPU number.** Cause not found. Start read-only: `Get-Counter -ListSet "GPU Engine"` and one `Get-Counter '\GPU Engine(*)\Utilization Percentage'` sample to see which instances return invalid data, then skip those instances in `tools/gpu_baseline.ps1` instead of failing the whole read.
8. **Commit messages.** Cause: written fast in a long run. Nothing is pushed, but amending rewrites history, so leave them and mention `37b91a5` and `f063ce5` in any final report. Use accurate messages from now on.
9. **Dial never run on hardware.** Cause: it was built with fakes only, by design. Before the first live run, tell the user in one line that a dial click changes real volume, mic and brightness, and that power plan and refresh rate ask first. Consider keeping the dial's host runner off until the user agrees (the default runner already refuses with NO HOST).
10. **Test icon row.** Cause: left from the first prototype. Hide it when any module is on, or remove it. Check `tests/` for `data-icon` before deleting.
11. **JarvisAutoStart.** Cause: an old memory note said it was temporarily 0. The file says 1. Do not edit it; the user owns that file and it must never be staged.

## 3. Redone plan (one step at a time; commit per slice by explicit path; no push, merge or deploy without asking)

**Step 0, housekeeping (no live run):** ask the user to close the old app; `dotnet build SpaceshipApp/ShipCore.App/ShipCore.App.csproj`;
confirm `bin\Debug\net10.0-windows\CSpace.exe` exists and has the icon; grep docs for `ShipCore.App.exe`; run Live-Preflight (dry); commit the CSpace slice.

**Step 1, SEE IT (the user's first goal):**
a. Fix the scheduler (mistake 3) with a test; commit.
b. Let the page show several modules: accept `?module=all` and comma lists (`?module=top,left,center`); keep the old single-value form working so no test or fixture breaks.
c. Decide with the user whether CSpace opens with all modules by default (architecture plan rule 4 said "off until proven"). Recommended: host navigates to `index.html?module=all` once the user has seen each module.
d. Hide the test icon row when modules are on.
e. `npm test`, `tsc`, `vite build`, `dotnet build`, `dotnet test`. Then ask for a live go and say exactly what it does: starts CSpace.exe, desktop overlay, tray icon, dial clicks change real volume/brightness; chord Ctrl+Alt+Shift+1 stops it.
f. Tell the user where it is: `SpaceshipApp\ShipCore.App\bin\Debug\net10.0-windows\CSpace.exe`; tray icon (may sit in the overflow arrow). No Start-menu shortcut exists; adding one writes outside the repo, so ask first.

**Step 2, valid baseline (needs a live go):** Rainmeter and CSpace with the same modules, same screen, same 5 min each, plus a `Get-Process` cross-check of the Rainmeter number. Fix or replace `gpu_baseline.ps1`. Use private bytes next to working set (WebView2 children share pages). Sampler: `C:\Users\Senai\.claude\jobs\bd35207b\tmp\sample-tree.ps1` (outside the repo; copy it to `tools/` if kept). Decision gate: keep WebView2 if within budget, else plan a native renderer (needs the user's numbers).

**Step 3, host robustness (live checks need a go):** real hit regions replacing the fixed `Hit (80,80,360,220)`; the UI reports interactive rectangles (new `hit.regions` message: `Protocol.cs`, `contract.ts`, `contract/fixtures/ui-to-host.json`, tests in both); multiply by devicePixelRatio; right/middle click; cursor shape; `TaskbarCreated` re-attach and a retry while WorkerW is missing; `WM_DISPLAYCHANGE`; Windows 11 24H2 Progman check; per-monitor DPI only with a live check; named-pipe commands; graceful quit.

**Step 4, packaging (autostart stays out):** `dotnet publish -c Release -r win-x64 --self-contained` (check the WebView2 native loader with single-file). Installer tool is an open decision (Inno Setup vs WiX). Final ship art is an open decision. The `--autostart` argument parsing and the Run value stay unbuilt until the user says.

**Step 5, performance work (only what Step 2 justifies):** baked glow instead of per-text drop-shadow, WebP (needs Pillow approval or another route), WebView2 flags, FULL/LITE/LOW/STEALTH tiers.

**Step 6, later:** boot stage triggered by the host; Phase 6 parity (Gmail, iCal, speed test, brightness/mic, winget/WU/AV, WSL/Ollama/Tailscale/Docker, WAN/LAN IP, per-process CPU/RAM, S&P, to-do, location, HWiNFO, JARVIS start/stop, Legion controls, presets, edit mode, hot reload, Apps.ini), each with a fake first and secrets kept out of git; Phase 7 ideas need the user's choice; cutover (`Switch-HudHost.ps1 -Apply`, 6 h soak, rollback drill) never without explicit approval. Phase 10 tone work needs the user's hand review.

## 4. Suggested review of Haiku's 25 commits (before building more on them)
Highest risk first: `WindowsDial.cs` and `DialGate.cs` (OS writes), `Program.cs` (WorkerW, hit test, kill tree), `ShipCore.Core/Protocol.cs` and `MessageRouter.cs` (untrusted input), `WasapiLoopback.cs`, then the Lua ports (`lib.lua`, `graph.lua`, `target.lua`...), checked against the skin with `tools/parity_diff.py`. A `agent-skills:code-reviewer` pass per area is reasonable.

## 5. Standing rules (from CLAUDE.md, the 10-20 handoff and the user)
No live run without an explicit go and a one-line description of what it does. Fake first, dry run first (grep for recycle bin, power, shutdown, sleep, Bluetooth, Wi-Fi, service, registry, process kill, file deletion). Never `git add .`; never stage `Settings.inc`; never commit weights, logs or secrets. Do not kill processes the user did not name. No HKCU Run change, no `Switch-HudHost.ps1 -Apply`. Commit trailer for this session: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Report exact commands, exit codes and every unverified check. Bash tip: forward slashes in `powershell -File` arguments.

## 6. Unbuilt work: do it all in a separate session
The user asked that everything still unbuilt be done in a fresh session, not by continuing this one. This session made no further changes after the audit. The fresh session should do, in order:
1. Step 0: get the old app closed (the user), build, confirm `CSpace.exe` exists with its icon and the single-instance guard works (start it twice only with a live go), grep docs for `ShipCore.App.exe`, commit the CSpace slice by explicit path.
2. Step 1: scheduler fix, `all` and comma module lists, hide the test icon row, fix the Ctrl+Alt+1 text in the 10-20 handoff, run every check, then ask for the live go.
3. Steps 2 to 6 in order, each as its own slice. Phase 6 parity items, Phase 7 and the cutover need the user's decisions first (see section 3).
Autostart stays unbuilt until the user says.

## 7. First message for the next session
"Read docs/HANDOFF-2026-10-21-cspace.md. Do Step 0 and Step 1. Stop and ask before any live run."
