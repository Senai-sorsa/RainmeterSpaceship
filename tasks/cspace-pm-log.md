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
