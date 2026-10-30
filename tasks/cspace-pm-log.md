# CSpace PM log (autonomous run started 2026-10-25)

Standing order: memory `autonomous-pm-directive.md` (verbatim). Loop per slice: plan -> code -> unit/static checks
(no live runs of the app until everything is built) -> compare with similar apps (Wallpaper Engine, Lively,
Rainmeter, Seelen UI, Windhawk, BeWidgets...) -> queue improvements -> next slice. Ask the user only before
actions that could damage the PC. No push (public repo).

Sources read: docs/HANDOFF-2026-10-21-cspace.md (plan Steps 0-6), claude_spaceship_migration_phases.md (spec;
gap list in tasks/cspace-gap-analysis.md), JARVIS-Repair-Plan.txt (CURRENT STATE + PHASE 10B).

## Done this run
- Step 0: old app closed; `dotnet build ShipCore.App` exit 0, CSpace.exe exists (1 MSB3277 WindowsBase warning from WebView2.Wpf, harmless).
- d647f8e scheduler carries remainder (rates right on 60/144/165 Hz) + test.
- 96b2ff3 ?module= list/all, test icons hidden when modules on, Center skips sphere when Jarvis on, Center reticle stale-readings fix.
- Host opens index.html?module=all (decision: full HUD by default; user delegated the call).
- d5ab992 docs name the real kill chord; f83655e desktop layer by z-order (S2-S4).
- 6066979 S1 click-through outside the page's hit regions (hit.regions message, WS_EX_LAYERED + TRANSPARENT toggle).
- 8489368 tray never writes autostart; WM_DISPLAYCHANGE re-homes; hang restarts the page; idempotent teardown.
- 3cc9543 S7 foreground WinEvent hides at once for fullscreen apps / exam browsers.
- 643fa37 S5 JARVIS state into the core: host reads Data\jarvis.txt read-only (share delete), posts jarvis.update.
- b4a6fde S6a upkeep/dev status from the skin's scripts (every 120 s, the skin's schedule).
- 56f2514 S6b network block: ping 10 s, LAN 30 s, WAN (api.ipify.org) 300 s; IP mask honoured.
- a074077 perf: jarvis.txt re-read only when its write time changes (was an IOException 5x/s with JARVIS off).
- 7ed975d S6c S&P 500 tape (Yahoo ^GSPC, 5 min open / 60 min closed, 64 KB reply cap).
- 0131138 perf: settings.json parsed only when it changed.
- f3f7ed5 S6d reticle to-do mode from the ObsidianTodo note (read-only, 5 s, parsed on change, .md <= 1 MB).
- 2fc4fae S6e HWiNFO sensors bind by label in memory (skin's DETECT patterns, once a minute; a set index wins).
- 3c21dbd S8a HUD hidden while the PC is locked (SessionSwitch).
- e094dff S8b tray Diagnostics; perf CSV capped at 8 MB; WebView memory counts only this app's own processes.
- 5a3f488 S11a hidden HUD: WebView2 IsVisible=false + TrySuspendAsync (page sleeps, rAF stops).
- 96315a4 S11b offline JARVIS orb at 10 fps.
- 20f7162 S11c perf tiers: GPU load via PDH (busiest engine, every 2 s), controller.lua tier logic in the page (memory only),
  reticle 20/10/parked fps, Stealth hides sphere + bottom audio. Fixed the skin's inverted down margin (it flipped tiers).
- 3803f32 S11d Release publish profile (framework-dependent win-x64, publish/CSpace, 2.2 MB). No installer yet.
- f241070 dial writes off the UI thread, one at a time, child process capped at 15 s.
- 24b7279 S11e audio: the loopback was never started; now runs only while shown and Off_BottomAudio is not 1, retries 30 s.
- 3f58441 host ignores web messages not from https://spaceship.local/; confirm box owned by a topmost form, No default.
- de4f8b0 S11f Off_<module> toggles hide their zones (were only offered in settings); hidden zones are not drawn.
- d4495ff S11g audio follows a default-speaker switch (5 s id check while capturing). 6dd1c2f placeholder fps allowed.
- JARVIS fakes-only items W1 T1 T3 U2 U4 X1 were already built in bdfb8fb (queue was stale).
- Build stop (2026-10-25): everything buildable without the user's go is built. Known limit: the published folder finds
  the UI and skin by walking up, so it must stay inside the repo until an installer is chosen.
- Every slice now ends with an efficiency pass, noted in its commit (user, 2026-10-25).
- Audit (user, 2026-10-25): 220df0d A1 security (RemoteSigned not Bypass, no -WindowStyle Hidden, no ipify while masked,
  WebView2 locked down, profile out of %TEMP%, version resource); 34f64ca A2 frame timers off while hidden;
  c70d3e8 A3 UI motion (category scan line ported, panel open/slide/fade, HUD fade-in on show, reduced-motion off).
  Left for the user: code signing (biggest SmartScreen/AV factor), brightness still via powershell -Command on a dial
  turn, upkeep.ps1's SecurityCenter2 AV query and winget run (recon-like, user feature), Chrome UA to Yahoo.

## Queue (app)
1. Docs: Ctrl+Alt+1 -> Ctrl+Alt+Shift+1 in docs/HANDOFF-2026-10-20-standalone-app.md; ShipCore.App(.exe) -> CSpace in docs/tools.
2. Gap-analysis slices (tasks/cspace-gap-analysis.md).
3. Handoff Step 3 host robustness (hit regions, TaskbarCreated, WM_DISPLAYCHANGE, WM_QUERYENDSESSION, graceful quit).
4. Step 4 packaging (publish, installer decision). Autostart stays unbuilt (user's word).
5. Live go needed later for: first run, baseline (Step 2), dial on hardware.

## Queue (JARVIS track, fakes-only fixes from PHASE 10B)
W1 bare "Jarvis" wakes, T1 silent never-mind, T3 listen 1 s after stop, U2 count after tidy, U4 voices path, X1 persona path log line.
Need the user: W2 (training off-PC), T4 (measure live), G1 (measure), U5 wording (Phase 10 hand review).

## Decisions made (PM)
- Full HUD by default in the host (handoff 1c).
- Desktop layer = Rainmeter's "On Desktop" model (top-level, HWND_BOTTOM, held there on WM_WINDOWPOSCHANGING), not a
  WorkerW child. Why: a WorkerW child sits under the icon view (no clicks), and 24H2+ (this PC is 26300) changed the tree
  (0x052C needs 0xD/1, WorkerW is a Progman child). Sources: rainmeter/Library/System.cpp + Skin.cpp (ChangeZPos),
  kirie PR #11, VibingWrapper PR #7. Follow-up queued: Show Desktop (Win+D) lift like Rainmeter's CheckDesktopState.
- Win+D (Show Desktop) lift: deferred to after the live run (lifting on desktop focus would also cover apps; Explorer's
  behaviour can't be checked without a live run).
- TaskbarCreated: no code - WinForms NotifyIcon re-adds itself.
- S5 reads the file JARVIS already writes instead of the pipe: no JARVIS change, no live risk. POP/HUD lines are not acted
  on (they change settings / stealth). Pipe line-JSON postponed.
- Known S1 limits: layered + NOREDIRECTIONBITMAP render unverified (fallback: drop WS_EX_LAYERED); drag leaving a region
  loses moves; cursor shape not forwarded; DPI SystemAware.
- WatchProcesses has no settings key in contract/config-keys.json, so the watched-process feature is dormant (no UI to set it).
- Dial stays live (volume/brightness direct, power/refresh confirm) - same as the skin; announce before first live run.

## 2026-10-26 - visual parity against the user's Rainmeter screenshot
Commits (feature/standalone-host, not pushed): 10e6afb 7810730 02d2b87 32c4ae3 9270ed7 07bab37 162eb45 28b76ca 0e8191f
f56c8cf c3a508b d379580 895c34b 7000bf3 229cfc4 1ba284e d3b3f84 49db154 1f8715f 54b3caa 1087bc0 5038d4f 5bc5853 2bb0c26 a0bc456.
- Last gap closed: slot RUNNING / BACKGROUND / READY (host apps.state from EnumWindows + process list, 3 s, on change only).
- Compared over the wallpaper: hull, glass, scan lines, colours, strip, dials, audio ring, sysinfo, slots, console match.
- Remaining differences are data or preview-only: app counts (the preview treats every file target as installed; the host
  uses File.Exists like the skin), orb OFFLINE vs idle, net graph colour (fake sine data), agenda/upkeep content.
  C.L.O.V.E.R in the screenshot was the pre-reload name: Settings.inc was saved as JarvisName=Jarvis a minute before it.
- Unverified until a live run: the host reads (COM audio, PDH, WLAN, EnumWindows). Host unit tests are blocked by SAC.

## 2026-10-26 - live run: the user's second screenshot (clicks, fonts, speed, targeter, bottom band)
Commits: 426a0bd c58b300 8cc2cda eccd3c2 f438003 238bcc1 4e6f42c.
- Clicks: hit shapes moved onto the dials; tabs, pages, slots and the targeter are clickable (426a0bd, eccd3c2).
- Speed: frame timers halved to the skin's real rate (c58b300). Weight 400 for text; boot text in the number font (8cc2cda).
- "Bold" text: the glow copy was drop-shadow, which drew the letters twice; it is now a blur of the halo only (238bcc1).
- Panel glass sat off its text: the frame now draws at the skin's Scale (f438003).
- Live bug: METRICS_FAILED (InvalidCastException) on every other tick, because two ComImport classes fought over the
  singleton MMDeviceEnumerator. Fixed by creating it by CLSID once (4e6f42c). That also unblocks the targeter's procs.top.
- STATUS_FAILED llt: status.ps1 carried the downloaded-zip Zone.Identifier, so RemoteSigned refused it. It was reviewed
  as query-only and `Unblock-File`d (an NTFS stream, not in git). llt.ps1 still has the mark and is not run by the app.
- SAC no longer blocks the new unsigned exe (launched 2026-10-26).
- Open: the to-do targeting needs ObsidianTodo set (Control Center > DATA; empty now). JARVIS-offline brightness was not
  reproduced. The calendar countdown ring is missing. Clicks were not verified by mouse.

## 2026-10-26 - live run: the user's third list (volume, cargo, control center, click targets, mail)
Commits: d145ed8 1f94e55 eed3be2 24a867c (published and relaunched after 24a867c).
- Volume: raising it unmutes; the ring takes clicks like audio.lua (d145ed8).
- CARGO drawer, Control Center and the folder clicks open as in the skin (1f94e55).
- The skin's other click targets (terminal, about, calendar, update/gmail, network, drive, battery, ...) are ported as fixed host targets; the bottom strip cells were lifted off the neon line (eed3be2).
- Gmail count: MailRunner does the skin's IMAP check every 2 min while shown and writes Data\mail.txt (24a867c). Live: UNREAD 17.
- Next: picture-frame zoom (#5), condensed hover tips (#7), a per-feature .lua vs .ts diff (#8: console llt/perf/master/hud buttons, ToggleNext, picks not persisted, speedtest, dev right-click, mail/calendar refresh).
- Finding: CalendarRunner only reads the repo's Data while the skin's ShipCore runs; the live skin's Data is a separate folder.

## 2026-10-26 - OPEN (parked by the user): helper processes spike CPU/GPU
User report: apps tied to the internet and to File Explorer keep opening and spike the GPU. Parked; fix later.
Measured (not fixed):
- CSpace's own page (WebView2 renderer + GPU process) is ~1 core steady; perf log web CPU 55-108% of one core, ~1.2-1.4 GB.
  Task Manager names it "Microsoft Edge WebView2", which reads as a browser. 5 other apps also run WebView2
  (SearchHost, OneDrive, GoogleDriveFS, PowerToys Peek, Lenovo Vantage); only the one under CSpace.exe is ours.
- StatusRunner starts powershell.exe + conhost per script (StatusScripts.Kinds):
  - upkeep.ps1 (5 s after every CSpace start, then hourly): `winget upgrade` (network, source refresh) and a
    Microsoft.Update.Session search (Windows Update service) - the "internet" bursts; every relaunch repeats it.
  - dev.ps1 (every 120 s): wsl.exe, ollama ps, tailscale status --json, docker ps - four CLIs per run.
  - status.ps1 (every 120 s): llt.exe x2 (Legion Toolkit) + Get-PnpDevice on the NVIDIA device - likely to touch / wake the dGPU.
- explorer.exe ~1 core steady is NOT CSpace (same with CSpace stopped). CSpace opens Explorer only from clicks
  (target.open / app.launch, Program.cs:613/653); launches are not logged, so an unclicked open is unverified.
Fix ideas for later: log every launch; run upkeep's winget/WU search rarely and not on each start; skip dev.ps1 CLIs
that aren't installed/running; drop Get-PnpDevice/llt polling or lengthen it; profile the page's animation rates.

## 2026-10-29: hover captions (ee9dc35)
- Done: the condensed captions, the skin's H.hit tips minus what is already on screen; the targeter shows process, CPU % and RAM MB.
- Checked: vitest 50 files/360 tests, tsc 0, vite build OK, mission-clock e2e 4/4 (two stale tests updated), hover checked in the preview.
- Not checked: live CSpace (it is closed), and the targeter tip with real procs.top data (the mock host sends none).
- Still open: #5 the picture-frame zoom (need the user to say where), #8 per-feature diff (console llt/perf/master/HUD buttons,
  ToggleNext, picks not persisted, speed test, dev right-click, mail/calendar refresh), and the parked helper CPU/GPU issue.

## 2026-10-29: per-feature sweep vs the skin (#8) and the frame zoom (#5)
Slices, one commit each (none pushed):
- 1fc9204 console buttons (Legion Toolkit, perf, master, HUD, refresh) as console.lua.
- 0a83528 the columns' category/app picks persist, as State.inc.
- 4ae600e the NET boxes run the speed test (sphere.lua / sysinfo.lua).
- 1aebda5 right-click on upkeep/dev/mail blocks checks again (status_block.lua).
- f169942 the sound readout switches output device (audio.lua ToggleNext, IPolicyConfig in AudioOut.cs).
- 8eebeb4 master switch keeps the tier before STEALTH across restarts (MasterPrev).
- e25a89e right-click on the mission clock fetches the calendars (location.lua).
- 282ea6e #5: the cockpit frame grows from the top-left like Frame.ini, so it lines up at any Scale.
- 066075c select graphs save their source and step on the wheel (graph.lua).
- 9704cf6 the JARVIS log pop-up shows Data\jarvis_log/live/env (jarvislog.lua): POP open/close, wheel scroll, right-click opens Notepad, 180 s idle close.
- 11a207a the boot sequence plays once per app start, after config arrives, and obeys BootAnim (controller.lua).
Checked against the skin and matching: audio, battery, category, console, control, dial, drawer, graph, hud, jarvis,
jarvislog, location, panels, power, slot, alert, sphere, status_block, strip, sysinfo, target, boot. storage.lua is unused.
Checks (after 11a207a): tsc 0; vitest 50 files / 368 tests; e2e hud.spec 3/3; dotnet test 262 passed (after 9704cf6).
Not ported: the JARVIS TYPE box (ask by text), the "Play startup sequence" replay menu, edit mode.
Not verified live (CSpace closed): real llt.exe, speedtest.exe, the IPolicyConfig switch, real JARVIS log files, the targeter tip with real procs.

## 2026-10-29 (cont.) the rest of the skin's clicks
- 1d567dc JARVIS commands: orb click wakes/cancels, the log's TYPE box asks him, the Control Center's Service buttons
  (stop, forget, reindex, train). The host writes Data\jarvis_cmd.txt from a fixed verb list (JarvisStatus.CmdLine).
- cff0bd1 an offline orb click starts the service, JarvisAutoStart=1 starts it ~5 s after the app starts (jarvis.lua
  StartService): venv pythonw.exe, else pyw.exe, no shell; captions STARTING / NO PYTHON / NO SCRIPT / START FAILED / STOPPED.
- 520b757 tray: App drawer (CARGO) and Play startup sequence (Common.inc's context menu).
- fef0773 Scan apps runs Scripts\scan-apps.ps1, and the app scans when Data\StartApps.txt is missing or a day old (controller.lua).
- 675c348 Edit mode, Presets and Rebuild icons are hidden until they have a host side.
Checks (after 675c348): tsc 0; vitest 51 files / 370 tests; e2e hud.spec 3/3; dotnet test 266 passed.
Not ported: edit mode, presets, Rebuild icons (app-icons.ps1), JarvisPython from Settings.inc (not a schema key).
Not verified live: the JARVIS launch, jarvis.py reading jarvis_cmd.txt, scan-apps.ps1 from the app, the tray items.

## 2026-10-29 QoL pass (uncommitted, not published)
- Built: icon, HUD kit, live theming, Control Center re-skin, Pre-flight wizard, S1 About/version, S2 tray (Help, About, kill-switch label), S3 Reduce motion, S4 remembered Stop + last category, S5 Power saver (x4 status/mail/calendar periods on battery), S6 notices, S7 Help (deterministic diagnosis + whitelisted fixes + Ask JARVIS via existing `jarvis.cmd ask`; jarvis.py untouched).
- Non-goals: no commit, publish, live run, push; no Python changes (Phase 10 tone needs hand-review).
- Rollback: `git restore` the edited files you did not already have changes in; delete the new untracked files (src/ui/kit, About/Notices/HelpCenter.tsx, src/help, src/host/notices.ts, PowerPolicy*.cs, new tests).
- S8 installer NOT built: no Inno Setup/WiX installed (installing one needs your yes), and the published exe finds the UI and skin by walking up the repo, so an installer needs a layout decision first. Existing: `dotnet publish` profile -> SpaceshipApp/publish/CSpace.
- Unmeasured: S5 battery baseline, per-slice idle CPU/RAM.
- S8 installer (2026-10-30, Inno Setup 6.7.3 installed per-user via winget at your word): installer/CSpace.iss + installer/Build-Installer.ps1. Per-user install to %LOCALAPPDATA%\Programs\CSpace (the app writes @Resources\Data). Publishes to installer\stage (live publish\CSpace untouched). Excludes Data, Backups, caches and JARVIS models (vosk/kokoro/voices/wake: run Setup-Jarvis.ps1 after). Compiled -> installer/Output/CSpace-Setup-0.1.0.exe (33 MB). NOT run, NOT installed. Rollback: delete installer\ (uninstall Inno via winget uninstall JRSoftware.InnoSetup if wanted).

## 2026-10-30 features round (clicks, slots, app icons, JARVIS orb, JarvisPython)
- a4ad0ed JARVIS start reads JarvisPython from Settings.inc (local pythonw/pyw only; set but bad = NO PYTHON, no fallback).
- 8a5bf8c orb voice echo + level smoothing (jarvis.lua 317-350), Active frames, echo only while speaking/thinking.
- 8a208c7 app icons served by the host (icons.spaceship.local, icons.list); IconQueue + app-icons.ps1 after every Start-menu scan, at start when Icons\_index.txt is missing, and hourly. dist 19M -> 15M.
- Task 5: stale "not ported" headers corrected (drawer, slot, jarvis, dial, alert, power, strip, graph).
- Decisions: "clocks" read as clicks (all were already wired); slot styles compact/ship/card/rcompact skipped (layout uses only 'row'). CARGO is ported (drawer).
- Checks: dotnet build 0 errors; dotnet test 274 passed (SAC let the test DLL load this time); tsc 0; vitest 55 files / 386 tests; vite build; hud e2e 3/3; app-icons.ps1 on a scratch copy of @Resources: exit 0, icons=2, missing path skipped.
- Not verified live (CSpace closed): JARVIS launch with JarvisPython, the echo in WebView2, the icons virtual host, the first real icon run (a few hundred icons, 10 min timeout), the hourly rescan.
- 2026-10-30 JARVIS help context: Jarvis/help_cspace.txt (12 known problems + fixes) searched by meaning (same MiniLM model as the HUD blocks; shared-words fallback when it is off) in new jarvislib/helpdocs.py; prompt.context() adds a "CSPACE HELP" line (+ his last ERR) only when a passage is close (>= 0.35), for any question. No new service, no actions; read-only text. Rollback: git restore jarvislib/prompt.py test_jarvis.py, delete helpdocs.py and help_cspace.txt. Not live-tested.

## HANDOFF 2026-10-30 (read this first in a new session)
**State.** Branch `feature/standalone-host`. The whole QoL/UI/JARVIS effort is committed locally, NOT pushed, NOT published, NOT run live:
- f3a69b0 JARVIS: J2 fast end of short utterances (mic.py, `JarvisFastEnd=0` turns it off), J3 Whisper temperature 0 + loop-phrase collapse (hearing.py), CSpace help context (helpdocs.py, help_cspace.txt, prompt.py), `tasks/jarvis-improvement-plan.md`, test_jarvis.py fixes.
- 4fa51ad app host: new icon, PowerPolicy (x4 polling periods on battery), HostState remembers Stop/last category, tray Help/About, runner changes.
- 5d4c5c8 UI + installer: HUD kit (`src/ui/kit`), live theming, Control Center re-skin, 4-module Pre-flight wizard, About, Notices (apps launch + JARVIS no-Python only), HelpCenter (rule-based `diagnose()` + whitelisted fixes + "Ask JARVIS" via `jarvis.cmd ask` with an "About CSpace:" prefix), `installer/` (Inno Setup 6.7.3 installed per-user via winget; `CSpace.iss`, `Build-Installer.ps1`; output `installer/Output/CSpace-Setup-0.1.0.exe`, 33 MB, unsigned, NEVER RUN; stage/Output are gitignored).
- Left uncommitted on purpose: `App Icons/` (12 MB source art), `CLAUDE.md.tokenwise-backup-20261013-113305` (stray backup). Ask before committing either.
- Rollback of all three: `git reset --soft 9156924`.

**Last verified results (before the final commits; nothing changed in code after).** `npx tsc --noEmit` clean; `npm test` 54 files / 383 tests; `npx playwright test` 41 passed (port 5173 must be free); `dotnet build ShipCore.App` 0 errors; `dotnet test ShipCore.Core.Tests` 272 passed; `python -B test_jarvis.py` (run in `Skins/Spaceship/@Resources/Jarvis`, ~minutes, fakes installed first) ends `test_jarvis: OK` (needed 4 old test-order fixes: S_ moved up, `lines = []`, real `warm` restored for the T4 test then the no-op put back, real `chat_stream` restored for the T4 test).

**Not done / unverified.** No live WebView2 run; no S5 battery baseline; no per-slice CPU/RAM pass; the real MiniLM model's help answers not checked; Notices cover only two sources; Reduce motion does not touch HUD module animations; installer never run (and the .NET 10 Desktop Runtime check is warn-only); JARVIS models are excluded from the installer (run `Setup-Jarvis.ps1`); the 3 commits are split by area, so each may not build alone. Earlier "S8 not built" note above is superseded.

**Standing rules (also in CLAUDE.md files and memory).** Read `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md` before any test/script (fake first, dry run first, no real destructive calls). Don't push, publish, run live, run/install the installer, enable autostart, run `Switch-HudHost.ps1 -Apply`, or bypass Smart App Control without an explicit yes. Never `git add .`; name files; no weights/logs/secrets. Commit messages end `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. JARVIS tone work (Phase 10) needs the user's hand-review. Kill chord Ctrl+Alt+Shift+1. Ponytail mode on.

**Likely next steps (the user decides).** (1) Push/publish approval, then a live check of everything marked unverified; (2) the J-plan remainder in `tasks/jarvis-improvement-plan.md` (J0-J7, J2/J3 done); (3) Phase 10 slice 2 (`tasks/phase10-slice2-plan.md`); (4) extend Notices to more sources; (5) battery baseline + efficiency pass.
