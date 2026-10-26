# CSpace gap analysis: spec vs code (2026-10-25)

This compares the spec `claude_spaceship_migration_phases.md` (3765 lines) with the code on branch `feature/standalone-host`.
It is a read-only audit. Nothing was run, built or tested. Statuses come from reading the code and running grep.
The things the handoff already reports (the rename to CSpace, the build blocked by PID 18940, the invalid CPU baseline, the kill chord, no GPU number, WindowsDial never run on hardware) are not repeated as findings here.

Status meanings:
- DONE: works as the spec intends, even if the shape differs.
- PARTIAL: some of it exists; the note says what is missing.
- MISSING: no code found.
- SUPERSEDED: CSpace solves the same problem another way.
- UNWISE: the spec's approach is wrong or risky.

NEEDS-USER-GO marks an item that touches real OS state: power, registry, Task Scheduler, killing processes, Rainmeter bangs, or personal files.

Main finding: the spec assumes several windows (NativeHullWindow, HudCanvasWindow, ModalOverlayWindow, SetWindowRgn hit-testing, a SharedBuffer). CSpace is built differently: one window parented to WorkerW, drawn through DirectComposition, using WM_NCHITTEST HTTRANSPARENT plus mouse forwarding (Program.cs:187-214, 247, 403-430). Many spec items therefore do not apply as written. Judge them against CSpace's design, not the spec's.

## Improvements (IMP-01..07)

| ID | Item | Status | Evidence | Note |
|---|---|---|---|---|
| IMP-01a | ReadyToRun publish, not compressed single-file | MISSING | ShipCore.App.csproj:4-15 has no publish props | One-line csproj change. The spec calls R2R "0 ms JIT"; that is wrong, because R2R still loads the runtime and some code still JITs. |
| IMP-01b | Task Scheduler autostart XML (Priority 4, battery flags, PT0S limit) | SUPERSEDED / NEEDS-USER-GO | AutoStart.cs uses the HKCU Run value `SpaceshipHud --autostart`; tray toggle at Program.cs:141-150 | The handoff says autostart is deferred, yet the toggle is already in the tray. Hide it or confirm it is intended. |
| IMP-01c | Stage 0 GDI+ boot reticle in under 25 ms, handed off on `ui.ready` | MISSING | no NativeHullWindow; no `ui.ready` in UI | "Under 25 ms" is unmeasured. Low value for a desktop HUD. |
| IMP-02 | 30px hit margin + `ui.animationLease` | PARTIAL / SUPERSEDED | fixed `Hit (80,80,360,220)` at Program.cs:68; no lease | The real gap is real hit regions from the UI (handoff Step 3). SetWindowRgn may not apply to a DComp/NOREDIRECTIONBITMAP window. Do the margin in the UI-supplied rects instead. |
| IMP-03 | 2-frame DwmFlush handoff | SUPERSEDED | no DwmFlush | CSpace has no hull-to-web window swap, so there is nothing to hand off. |
| IMP-04a | Ignore WM_CLOSE | MISSING | WndProc Program.cs:395-430 has no WM_CLOSE case | Small. Check first what currently closes the window. |
| IMP-04b | QUERYENDSESSION/ENDSESSION | DONE (better than spec) | Lifecycle.cs:17,22; Program.cs:401-402 | The spec calls Environment.Exit inside QUERYENDSESSION, which is wrong because the session end can still be cancelled. CSpace correctly tears down on ENDSESSION wParam=TRUE. |
| IMP-04c | Tell JARVIS QUIT/unduck within 100 ms on session end | MISSING | JarvisPipe.cs:64 says "host sends nothing else yet" | Needs the pipe command channel first. |
| IMP-04d | TaskbarCreated re-register tray icon + re-anchor | MISSING | grep found no TaskbarCreated | If explorer restarts, the HUD and tray icon are lost. High value, low risk. |
| IMP-05 | build_orb_atlas.py (RGBA atlas, webp/BC7, manifest) | MISSING | no tools/build_orb_atlas.py; no atlas or WebGL in UI | The orb is drawn procedurally on canvas (draw/canvas.ts, modules/sphere.ts). A 21.5 MB atlas would conflict with the perf goals, so only build it if the procedural orb fails parity. |
| IMP-06 | WebView ProcessFailed recovery | PARTIAL | Program.cs:275, 313-331: restarts on RenderProcessExited/BrowserProcessExited, max 3 | GpuProcessExited and Unresponsive are not handled. CreateSharedBuffer does not apply because CSpace uses PostWebMessageAsJson. |
| IMP-07a | Single-instance mutex | DONE (renamed) | Program.cs:16 `Local\CSpace.SingleInstance` | The name differs from the spec's `Local\SpaceshipHud_HostMutex`, which is fine. |
| IMP-07b | Guard against Rainmeter / ShipCore.exe running together | MISSING | grep found no DummyRainWClass in SpaceshipApp | A read-only "Rainmeter is running" warning is safe. Deactivating skins is NEEDS-USER-GO. |
| IMP-07c | Switch-HudHost.ps1 | DONE (safer than spec) | tools/windows/Switch-HudHost.ps1:3-7,62-73: dry run by default, -Apply/-Rollback, "never force-kills" | The spec's version uses Stop-Process -Force; the repo's version correctly does not. Running -Apply is NEEDS-USER-GO. |

## Bugs (BUG-01..10)

| ID | Item | Status | Evidence | Note |
|---|---|---|---|---|
| BUG-01 | JARVIS exits when Rainmeter is gone even though the host runs | DONE | base.py:199-201 `... or host_live()`; host_pipe.py:38-46; test_host_pipe.py:87-90 | Uses WaitNamedPipe on the session pipe instead of the spec's window class, which is better. |
| BUG-02 | 30px hit margin | PARTIAL | see IMP-02 | |
| BUG-03 | AppScanner.cs (jumbo shell icons to @Resources\Icons) | MISSING | no AppScanner in SpaceshipApp | Writing into the skin folder is shared with Rainmeter, so keep the same file names. |
| BUG-04 | DPAPI for Gmail/calendar secrets | MISSING | grep found no ProtectedData; Protocol.cs:10 / ActionGate.cs:24 only know the flow names | Good news: grep found no GmailPassword key in @Resources *.inc/lua/ps1/py, so nothing is stored in plain text today. Needed before the Gmail/iCal collectors. |
| BUG-05 | `_DX/_DY` in Offsets.inc, `Off_/CT_` in State.inc | PARTIAL | ConfigStore.cs:7 writes Settings/State/Offsets.inc via the schema | No `_DX`/`Off_`/`CT_` keys found in ShipCore.Core; it is unclear whether ConfigSchema lists them. Needed by edit mode. |
| BUG-06 | Module-to-script mapping (dial.lua, location.lua, sysinfo.lua) | DONE | UI ports modules/dial.ts, MissionClock.tsx, sysinfo.ts | This is a spec documentation fix; the ports follow the right sources. |
| BUG-07 | Keep the SharedBuffer on the main realm | SUPERSEDED | no SharedBuffer | Not applicable. |
| BUG-08 | export_ui_assets.py writes JSON data | DONE (other path) | tools/export_ui_assets.py:280-282 writes to `SpaceshipUI/src/generated`; test_export_ui_assets.py exists | Spec path `@Resources\UI\generated` was dropped. Tests not run in this audit. |
| BUG-09 | ORT_ENABLE_ALL + ORT_SEQUENTIAL in tts.py; intra_op 1 for openWakeWord | PARTIAL | tts.py:86-87 sets only intra_op_num_threads on the CPU path | graph_optimization_level is already ENABLE_ALL by default in onnxruntime, so the gain is small. openWakeWord not checked. |
| BUG-10 | Duplicate comment blocks in Settings.inc | NOT CHECKED / NEEDS-USER-GO | Settings.inc is skip-worktree and personal | Comment-only cleanup. Low value; never stage the file. |

## Phase 0: foundations

| ID | Item | Status | Evidence | Note |
|---|---|---|---|---|
| P0-1 | BUG-01/09/10 edits | PARTIAL | see bugs | 01 done, 09 partial, 10 not checked |
| P0-2 | export_ui_assets.py | DONE | tools/export_ui_assets.py | |
| P0-3 | Host csproj (self-contained, single-file, R2R, WebView2 1.0.2903.40, System.Management, ProtectedData) | PARTIAL | ShipCore.App.csproj:1-22, net10, WebView2 1.0.3179.45 | Missing publish props and ProtectedData. The spec's WebView2 version is older than the repo's, so keep the repo's. tools/package.py exists but was not read. |
| P0-4 | app.manifest (asInvoker + PerMonitorV2) | MISSING | no ApplicationManifest in csproj | Needed for per-monitor DPI (Step 3). Low risk. |
| P0-5 | SystemChangeLedger.cs | MISSING | none | Only needed once the host changes OS state (power plans, Run key). Switch-HudHost has its own record/rollback. |
| P0-6 | RecoveryTrayHost (Ctrl+Alt+Shift+H hide, TaskbarCreated, QUERYENDSESSION) | PARTIAL | tray + Lifecycle exist; kill chord in KillChord.cs:9 | Missing: a hide/show hotkey and TaskbarCreated. |
| P0-7 | Program.cs HostMutex + Rainmeter guard | PARTIAL | Program.cs:16 | Mutex yes, Rainmeter guard no. |
| P0-8 | Switch-HudHost.ps1 | DONE | tools/windows/Switch-HudHost.ps1 | |
| P0-9 | Gate: test_jarvis.py 100% | NOT RUN | | Not run in this audit, by rule. |

## Phase 1: shell integration

| ID | Item | Status | Evidence | Note |
|---|---|---|---|---|
| P1-1 | BootIntegrationManager (schtasks, RestartOnFailure PT10S x3, ledger) | SUPERSEDED / UNWISE / NEEDS-USER-GO | AutoStart.cs (Run key) | Task Scheduler's RestartOnFailure minimum interval is PT1M, so PT10S is invalid XML. Autostart is deferred by the user. |
| P1-2 | NativeHullWindow (layered hull + reticle) | SUPERSEDED | single DComp window | Not needed. |
| P1-3a | Desktop attach (findHome/fitTo) | DONE | Program.cs:187-214 (Progman 0x052C → WorkerW, else HWND_BOTTOM) | |
| P1-3b | WaitForExplorerShellReady / WorkerW retry | MISSING | no retry | At early logon the attach can fall back to HWND_BOTTOM and stay there. |
| P1-3c | TaskbarCreated re-attach | MISSING | | Same as IMP-04d. |
| P1-3d | WM_POWERBROADCAST resume re-anchor | MISSING | grep found nothing | |
| P1-3e | WM_DISPLAYCHANGE / monitor change refit | MISSING | grep found nothing | |
| P1-3f | Win+D guard (WM_WINDOWPOSCHANGING) | NOT CHECKED | | A WorkerW child should survive Win+D. Verify live. |
| P1-3g | 24H2 Progman check | MISSING | | 24H2+ changed the WorkerW layering (Progman hosts the wallpaper differently). This OS is 26300, so it is a real risk. Verify live. |
| P1-4a | Hit testing from real module rects (`hit.regions`) | MISSING | Program.cs:68 fixed rect; no hit.regions in UI | Top user-visible gap: clicks outside the fixed rect fall through. |
| P1-4b | Right/middle click, cursor shape, devicePixelRatio | MISSING | Program.cs:409-430 left button + wheel only | |
| P1-4c | SetWindowRgn polygons + lease + DwmFlush | SUPERSEDED | | Use UI-supplied rects in WM_NCHITTEST instead. |
| P1-5a | WebView env pre-warm, `--gpu-preference=low-power` | MISSING | Program.cs:246 no browser args | Belongs to the perf slice. Measure before and after. |
| P1-5b | RasterizationScale 1.0 / ShouldDetectMonitorScaleChanges false | MISSING | grep found nothing | Belongs with the DPI work, not on its own. |
| P1-5c | Virtual hosts spaceship.ui + spaceship.res | PARTIAL | Program.cs:289 one host `spaceship.local` → dist | Fine unless the UI must load skin images from @Resources directly. |
| P1-5d | NewWindowRequested → modal window | SUPERSEDED | Program.cs:277-278 blocks new windows | CSpace renders ControlCenter/Settings inside the same page (ui/ControlCenter.tsx, SettingsPanel.tsx). |
| P1-5e | ProcessFailed recovery | PARTIAL | see IMP-06 | |

## Phase 2: config and IPC

| ID | Item | Status | Evidence | Note |
|---|---|---|---|---|
| P2-1a | ConfigStore single writer, keeps file bytes | DONE | ConfigStore.cs:7,22,40,109 (lock + temp file + atomic replace) | A lock instead of SemaphoreSlim is fine. Apps.ini is not covered. |
| P2-1b | DPAPI | MISSING | | see BUG-04 |
| P2-1c | SavePreset/LoadPreset | MISSING | grep found no Preset in Core | Port from control.lua:195-213. It writes the user's real config files, so back them up first. |
| P2-1d | config.get/config.set from UI | DONE | MessageRouter.cs:33-38 | |
| P2-2a | HudIpcServer, two simplex pipes, 64-hex nonce | SUPERSEDED | JarvisPipe.cs:11,37 one duplex CurrentUserOnly pipe, 32-hex nonce, PID check at :60,70 | The duplex design is fine and already tested (PipeGate, HostPipeWire). The 128-bit nonce is enough. |
| P2-2b | welcome.snapshot, state stream, commands both ways | MISSING | JarvisPipe.cs:64-65 holds the connection only | Blocks JARVIS state in the HUD (the jarvis module) and QUIT on end session. |
| P2-2c | base.py IPC client (start_ipc_client, pop_ipc_cmd) | PARTIAL | host_pipe.py:49-71 handshake + host_live | Only liveness and handshake exist; no message loop. |
| P2-3 | Gate: 10,000 messages, no deadlock | MISSING | | Write it together with P2-2b, against fake streams. |

## Phase 3: collectors and UI base

| ID | Item | Status | Evidence | Note |
|---|---|---|---|---|
| P3-1a | CPU/RAM/disk/net metrics | DONE | WindowsMetrics.cs, SystemSampler/SystemMetrics.cs, NetworkRate.cs; system.metrics 1 Hz at Program.cs:343-352 | |
| P3-1b | HWiNFO sensors | PARTIAL | HwinfoSensors.cs:10-30 (map from settings), WindowsMetrics.cs:43-50 | Reads ValueRaw by index from the settings map. The spec's Label0..199 auto-binding (controller.lua:140-153) is missing. |
| P3-1c | Top 5 processes by CPU/RAM | NOT CHECKED | WindowsProcessNames.cs exists | Not read. |
| P3-2 | LegionToolkitBridge (llt.exe) | MISSING | | NEEDS-USER-GO when it runs: it changes power and GPU modes. |
| P3-3 | AppScanner | MISSING | | see BUG-03 |
| P3-4a | CloudPoller: Gmail, iCal, S&P (^GSPC), Obsidian to-do | MISSING | only flow names in Protocol.cs:10 | Gmail/iCal need DPAPI first. |
| P3-4b | Upkeep (WU/winget/AV) + dev (wsl/ollama/tailscale/docker) | MISSING (host side) | UI has modules upkeep.ts, dev.ts | The UI is ready but has no data source. Use read-only queries only. |
| P3-4c | NetworkMonitor (WAN/LAN IP, speedtest) | PARTIAL | WindowsNetwork.cs (rates) | No IPs, no speedtest. |
| P3-5a | Vite UI | DONE | SpaceshipUI/vite.config.ts | Single page. Multi-page modal not needed (see P1-5d). |
| P3-5b | tokens.css fonts (B612 Mono/Oxanium/Michroma) | NOT CHECKED | | |
| P3-5c | HudPrimitives (lib.lua port) | DONE (other form) | src/lib/ (Matrix, Prim, parseColor), draw/canvas.ts | Canvas rather than SVG/TSX. Fine. |
| P3-5d | CockpitFrame + CockpitTextureBaker.cs | PARTIAL | ui/FrameLayers.tsx, tools/ship_frame.py, frame_render.py | No baked texture in the host. The baked glow is in handoff Step 5. |
| P3-6 | Gate: 0 PowerShell spawns | NOT CHECKED | | grep the host for `powershell` before claiming this. |

## Phase 4: visibility, audio, orb, intro

| ID | Item | Status | Evidence | Note |
|---|---|---|---|---|
| P4-1 | build_orb_atlas.py | MISSING / likely UNWISE | | see IMP-05 |
| P4-2 | VisibilityGovernor (SetWinEventHook, 50 ms debounce, DWMWA_CLOAKED) | PARTIAL | VisibilityPolicy.cs:7-21 + 3 s poll at Program.cs:334-340 | The logic is tested. Event hooks would react faster and wake less often than polling. Cloaked windows (UWP) are not filtered, so a false "fullscreen" is possible. |
| P4-3 | WASAPI spectrum (event-driven, 96 bands, sleeps in silence) | PARTIAL | WasapiLoopback.cs, SpectrumBands.cs:9 (40 Hz-16 kHz, band count is a parameter) | The spec's "wait INFINITE" is wrong: loopback raises no events during silence, so use a timeout. Band count and silence sleep not verified. |
| P4-4 | AudioReactor | PARTIAL | modules/audio.ts | Not read in depth. |
| P4-5 | JarvisCore3D (WebGL2, contextlost fallback, shockwave lease) | SUPERSEDED | modules/sphere.ts, Jarvis.tsx on canvas; grep found no webgl | Canvas avoids the GPU context-loss class of bugs. |
| P4-6 | IntroSequence (5 stages, 4.5 s failsafe) | PARTIAL | modules/Boot.tsx, boot.ts | Stage count and failsafe not verified. Handoff Step 6 wants the boot triggered by the host. |

## Phase 5: modules and editors

| ID | Item | Status | Evidence | Note |
|---|---|---|---|---|
| P5-1 | 22 modules (5.1) | PARTIAL | modules/: Top, Left, Right, Center, Bottom, Dial, Drawer, Jarvis, MissionClock, Boot + ports for power, battery, console, alert, graph, category, slot, target, strip, panels, storage, sysinfo | Most are drawn. Live data is missing for anything that needs P3-4. The dGPU confirm button and quick toggles in TopConsole are NEEDS-USER-GO when wired. |
| P5-2 | ControlCenterModal (10 tabs), CargoDrawer, JarvisLog | PARTIAL | ui/ControlCenter.tsx, SettingsPanel.tsx, modules/Drawer.tsx | Tab count not matched against the spec. JarvisLog needs P2-2b. |
| P5-3 | LayoutStudio (SAT guard, snapping, writes `_DX/_DY`) | MISSING | no LayoutStudio; tools/check_layout.py, layoutlib.py are offline only | Edit mode. Depends on BUG-05 keys. |
| P5-4 | Power actions (`sys.powerAction`) | PARTIAL / NEEDS-USER-GO | ActionGate.cs; Program.cs uses UnwiredHost | Deliberately not wired. Keep it that way until the user says go. |
| P5-5 | Dial (refresh/power plan/brightness) | PARTIAL / NEEDS-USER-GO | DialGate.cs, WindowsDial.cs, MessageRouter.cs:69 | Never run on hardware (handoff). |

## Phase 6: hardening

| ID | Item | Status | Evidence | Note |
|---|---|---|---|---|
| P6-1 | PrivacyGovernor (SetWindowDisplayAffinity 0x11, Ctrl+Alt+Shift+P, SessionSwitch) | MISSING | grep found nothing | WDA_EXCLUDEFROMCAPTURE needs Win10 2004+ and a top-level window. **It may not work on a WorkerW child.** Verify before building. Hiding on lock via SessionSwitch is cheap. |
| P6-2 | JarvisSupervisor (pythonw, backoff 2/5/15 s, max 5 per 10 min, QUIT within 80 ms) | MISSING | | Today JARVIS starts itself (JarvisAutoStart=1, which must not change). Overlaps handoff Step 6. Starting/stopping processes is NEEDS-USER-GO. |
| P6-3 | DiagnosticOverlay (Ctrl+Alt+Shift+D) | MISSING | perf CSV in temp\spaceship-app only | Cheap to do in the UI from system.metrics + perf data. |
| P6-4 | 6 h soak | MISSING | | Run after the hit-region and re-attach slices. Needs a go (live run). |
| P6-5 | SharedBuffer layout (3.2) | SUPERSEDED | JSON messages | Not needed at 1 Hz. Only revisit if spectrum data via JSON shows up in profiling. |
| P6-6 | Message list (3.3) | PARTIAL | MessageRouter.cs:33-69 has config.*, setup.*, aboutme.*, action, flow.open, dial.set | Missing: ui.ready, intro.done, preset.*, app.launch, llt.set, shell.open allowlist, jarvis.cmd, hit.regions, visibility.mode, jarvis.update. |

## Spec claims that look technically wrong

1. **RestartOnFailure PT10S:** Task Scheduler rejects intervals under PT1M.
2. **"ReadyToRun = 0 ms JIT / under 25 ms":** R2R reduces JIT work but does not remove it. The startup number is unmeasured.
3. **Environment.Exit in WM_QUERYENDSESSION:** wrong, because the session end can be cancelled. Exit on WM_ENDSESSION(TRUE), as Lifecycle.cs already does.
4. **WASAPI loopback "wait INFINITE":** no events arrive during silence, so the thread stalls. A timeout is needed.
5. **SetWindowRgn on the HUD:** CSpace's DComp/no-redirection window inside WorkerW may not clip the way the spec expects. HTTRANSPARENT is said not to work across processes; it works here only because the window is a WorkerW child. Verify live.
6. **WDA_EXCLUDEFROMCAPTURE on a child window:** documented for top-level windows. Likely a no-op on a WorkerW child.
7. **Stop-Process -Force in Switch-HudHost:** destructive. The repo's script correctly avoids it.
8. **WebView2 1.0.2903.40:** older than the repo's 1.0.3179.45. Do not downgrade.
9. **21.5 MB orb atlas:** conflicts with the perf goals while the procedural canvas orb exists.

## Recommended build order

Each slice is small and gets its own commit. Fake tests come first, then a dry run (per CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md). Building still needs PID 18940 closed by the user.

**S1. Clicks land where the HUD is drawn (highest visible value, low risk).**
- UI sends `hit.regions` (module rects × devicePixelRatio, plus the 30px margin) when the layout changes. Host replaces the fixed rect at Program.cs:68.
- Add right/middle click and cursor forwarding.
- Add app.manifest with PerMonitorV2.
- Tests: a TS unit test for the rect math and a C# test for the region check.

**S2. Survive explorer restart, resume, display change (high value, low risk).**
- On TaskbarCreated: re-add the tray icon and re-run attach.
- Retry the WorkerW attach N times at startup.
- On WM_DISPLAYCHANGE and WM_POWERBROADCAST resume: refit.
- Ignore WM_CLOSE.
- Read-only check of the 24H2 Progman layout.
- Needs one live check, with a go: restarting explorer is a real OS action, so NEEDS-USER-GO for that check only.

**S3. WebView resilience (low risk).**
- Handle GpuProcessExited and Unresponsive in the existing ProcessFailed handler (Program.cs:313-331).

**S4. Tray autostart decision (NEEDS-USER-GO).**
- The tray toggle at Program.cs:141-150 writes the HKCU Run key even though the user deferred autostart. Ask: hide it until Step 4, or keep it.

**S5. JARVIS pipe channel (medium value, medium risk).**
- After `ready`, add a line-JSON message loop: host→JARVIS `quit`; JARVIS→host `jarvis.update`.
- The UI shows JARVIS state, and end-session sends QUIT.
- Fake-stream tests plus the 10,000-message gate.
- No process start/stop yet.

**S6. Read-only collectors for the existing UI modules (medium value, low risk).**
- In order: WAN/LAN IP, upkeep (WU/winget/AV, query only), dev (wsl/ollama/tailscale/docker status, query only), S&P, Obsidian to-do, HWiNFO label auto-binding.
- One collector per commit, each behind a fake interface like the existing IHwinfoRegistry.
- Before calling the Phase 3 gate done, grep each one for process spawns.

**S7. Visibility via WinEvent hooks + cloaked filter (perf, low risk).**
- Replace the 3 s poll in Program.cs:334-340 and keep VisibilityPolicy as the decision logic.
- Measure CPU before and after against a valid baseline (with the HUD rendering).

**S8. Diagnostic overlay + hide-on-lock (low risk).**
- Ctrl+Alt+Shift+D toggles a UI overlay.
- SessionSwitch lock hides the HUD.
- First a spike to check that WDA_EXCLUDEFROMCAPTURE does anything on a WorkerW child; only then build PrivacyGovernor.

**S9. Secrets + Gmail/iCal (medium risk).**
- DPAPI store under %LOCALAPPDATA%\SpaceshipHUD, then the pollers.
- Creating secret files is NEEDS-USER-GO, and the user must enter the credentials.

**S10. Presets + edit mode (medium risk, writes real config).**
- Add the BUG-05 keys to ConfigSchema.
- Port SavePreset/LoadPreset with a backup.
- Then LayoutStudio writing `_DX/_DY`.
- Writing the real Settings/State/Offsets.inc is NEEDS-USER-GO the first time.

**S11. Perf tiers + publish (handoff Steps 4-5).**
- R2R publish props, `--gpu-preference=low-power`, baked glow, FULL/LITE/LOW/STEALTH tiers.
- Each one is measured.

**S12. OS-changing features (all NEEDS-USER-GO).**
- Wire power actions (UnwiredHost → real).
- Run WindowsDial on hardware.
- LegionToolkitBridge.
- JarvisSupervisor (start/stop pythonw).
- Rainmeter guard that deactivates skins / Switch-HudHost -Apply.
- Cutover.

**Do not build:**
- NativeHullWindow / boot reticle
- DwmFlush handoff
- SharedBuffer
- the orb atlas (unless the procedural orb fails parity)
- simplex pipe pair
- the multi-page modal window
- Task Scheduler XML as specced (it is invalid as written)
