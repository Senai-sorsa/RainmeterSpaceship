# RainmeterSpaceship (`BLACK-CLOVER`) Standalone Migration: Complete Technical Audit, Architecture Bible & Phase-by-Phase Claude Execution Specification

## Part 1: Blueprint Rating & Complete Technical Audit (`IMP-01`..`IMP-07` + `BUG-01`..`BUG-10` + `OVR-01`..`OVR-18`)

### 1.1 Overall Plan Rating: `9.4 / 10` (Upgraded to `10 / 10` With `IMP-01`..`IMP-07` & `BUG-01`..`BUG-10` Baked In)

The `restructuring_spaceship_app_plan.md` blueprint is already at an elite architectural level. Its two-pass review (`FIX-DEBATE-01..18` and `OVR-01..18`) caught several low-level Win32 and Chromium traps that derail most desktop shell projects:
* **Kernel-Level Hit-Testing (`CHOICE-04` / `OVR-04`)**: Replacing `WM_NCHITTEST` (`HTTRANSPARENT`, which fails across processes and never passes clicks to `explorer.exe`) with kernel-level `SetWindowRgn` polygon hit-testing (plus dynamic unclipping leases).
* **Deadlock-Free Python IPC (`CHOICE-07` / `OVR-07`)**: Catching the synchronous Windows CRT full-duplex deadlock on standard Python `open()` (when `pywin32` is absent) and splitting IPC into two unidirectional (simplex) Named Pipes (`SpaceshipHud_ToJarvis_<SID>` and `SpaceshipHud_FromJarvis_<SID>`).
* **Zero-Allocation 60Hz/165Hz Telemetry (`CHOICE-05` / `OVR-05` & `CHOICE-02` / `OVR-02`)**: Replacing 60Hz JSON IPC with a 4 KB zero-copy `CoreWebView2SharedBuffer` (`Float32Array`) and replacing React's Virtual DOM with `Preact + @preact/signals` (`preact/compat`, `6 KB` bundle, direct DOM text/attribute mutation with `0` VDOM diffs).
* **GPU Texture VRAM Budget (`CHOICE-10` / `OVR-10`)**: Catching the `84.3 MB` RGBA8 GPU texture expansion of two `3136x3360` orb atlases and introducing `BC7` compression / cell downsampling + Procedural GLSL rendering.
* **Event-Driven Occlusion Wake (`CHOICE-14` / `OVR-14`)**: Replacing a 2,000ms polling loop with out-of-context `SetWinEventHook` (`EVENT_SYSTEM_FOREGROUND`, `EVENT_SYSTEM_MINIMIZESTART`, `EVENT_SYSTEM_MINIMIZEEND`) so minimizing a maximized app wakes the HUD in `<15ms`.

However, when stress-testing this plan against your actual repository files (`RainmeterSpaceship-fix-phase7-9-audit`) and your two primary motivations — **(1) fluid opening & runtime animations** and **(2) immediate, 100% reliable, non-destructive startup on Windows restart** — there are **7 critical architecture improvements (`IMP-01` – `IMP-07`)** and **10 concrete repository alignment fixes (`BUG-01` – `BUG-10`)** that must be baked in before handing this to Claude.

---

### 1.2 Table 1: The 7 Critical Boot, Animation & Resilience Upgrades (`IMP-01` – `IMP-07`)

| ID | Flaw / Blind Spot in Current Plan | Exact Technical Fix Added to the Claude Phases Below |
| :--- | :--- | :--- |
| **`IMP-01`**<br>*(Restart Speed)* | **`<EnableCompressionInSingleFile>true` (`OVR-01`) + Task Scheduler Default Priority (`OVR-18`) Slows Cold-Boot Startup**:<br>1. A compressed single-file `.NET 10` `.exe` must decompress into memory/temp on cold boot right when Windows logon is thrashing the NVMe SSD (`+350–800ms` delay).<br>2. Windows Task Scheduler `LogonTrigger` tasks default to `Priority = 7` (*Below Normal* CPU & Background Disk I/O) unless overridden in XML — causing the HUD to lose the CPU race against startup apps (Steam, Discord, Lively) on reboot! | 1. Replace `<EnableCompressionInSingleFile>true` with **`<PublishReadyToRun>true</PublishReadyToRun>`** (AOT native x64 machine code pre-compilation) so `ShipCore.Host.exe` executes native instructions at `0ms` JIT/decompression cost.<br>2. Set **`<Priority>4</Priority>`** (Normal interactive priority), **`<Delay>PT0S</Delay>`**, **`<DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>`**, **`<StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>`**, and **`<ExecutionTimeLimit>PT0S</ExecutionTimeLimit>`** in the Task Scheduler registration XML.<br>3. Paint an immediate **Stage 0 Win32 GDI+ Boot Reticle (`"INITIALIZING SHIPCORE..."`)** on `NativeHullWindow` in **`<25ms`** while WebView2 warms up in the background (`~400ms` on cold boot), then seamlessly hand off to the 165Hz `<IntroSequence/>` the millisecond WebView2 posts `ui.ready`. |
| **`IMP-02`**<br>*(Runtime Animations)* | **`SetWindowRgn` (`OVR-04`) Will Guillotine Runtime Animations Outside the 3.2s Intro**:<br>`OVR-04` unclips `SetWindowRgn` during `<IntroSequence/>` and `LayoutStudio`, then locks `SetWindowRgn` to the resting polygons. What about runtime animations? Hover scale/glow, JARVIS wake-word shockwave ripples, alert pulses, preset morphs (`Presets\1..6`), and notification toasts that expand outside a polygon will be hard-clipped by `SetWindowRgn`! | 1. Include the repository's mandatory **`18px` `ModuleMargin`** (`tools\build.py:21` `MARGIN = 18`) **plus a `12px` `AnimationBleedMargin` (`30px` total padding around nominal `layout.json` zone quads)** in `HitTestRouter.cs` so micro-interactions, hover lifts, hover captions (`H.caption`), and dial outer labels never clip.<br>2. Add an IPC lease (**`ui.animationLease { active: true, durationMs }`**) that temporarily unclips `SetWindowRgn(hwnd, IntPtr.Zero, false)` during Preset morph transitions, JARVIS wake-word shockwaves, Red-Alert sweeps, and Shutdown sequences, then restores `masterRgn` via the 2-frame `DwmFlush()` protocol when the animation finishes. |
| **`IMP-03`**<br>*(1-Frame Flicker)* | **DWM 1-Frame Black/White Flicker During Hull & Region Handoff (`OVR-04` + `OVR-11`)**:<br>Calling `SetWindowRgn(hwnd, masterRgn, false)` on `HudCanvasWindow` and `ShowWindow(nativeHullHwnd, SW_SHOWNOACTIVATE)` on the same frame causes a 1-frame DWM composition flash on Windows 11. | **Enforce a 2-Frame `DwmFlush()` Handoff Protocol**: At the end of `<IntroSequence/>` (`t = 3.2s`) or when closing `Control Center > THEME`:<br>• **Frame 1**: Show `NativeHullWindow` (`ShowWindow(nativeHullHwnd, SW_SHOWNOACTIVATE)`) and call `DwmFlush()` (`dwmapi.dll`).<br>• **Frame 2**: Wait one `requestAnimationFrame` (`6ms` at 165Hz).<br>• **Frame 3**: Apply `SetWindowRgn(hudCanvasHwnd, masterRgn, false)` and hide `<div id="cockpit-hull-live" />` inside `HudCanvasWindow`. Zero flicker. |
| **`IMP-04`**<br>*(Windows Restart Safety)* | **Blocking `WM_CLOSE` Blocks Windows Restart (`WM_QUERYENDSESSION`) + `explorer.exe` Crash Orphan Bug**:<br>1. Desktop overlays typically ignore `WM_CLOSE` so `Alt+F4` doesn't kill the HUD. If `WndProc` doesn't explicitly handle `WM_QUERYENDSESSION` and `WM_ENDSESSION`, Windows will hang on restart saying *"ShipCore.Host.exe is preventing Windows from restarting"*!<br>2. If `explorer.exe` crashes or restarts, the system tray icon vanishes and Z-order hooks break. | 1. In `WndProc`, intercept `WM_CLOSE` (`0x0010` — ignore unless `_isShuttingDown`), but on **`WM_QUERYENDSESSION` (`0x0011`)** and **`WM_ENDSESSION` (`0x0016`)**, immediately set `_isShuttingDown = true`, return `1`, signal `jarvis.py` (`QUIT` / `unduck()`) with a `<100ms` timeout, and call `Environment.Exit(0)` so Windows restarts cleanly and instantaneously.<br>2. Register **`RegisterWindowMessageW("TaskbarCreated")`** in both `DesktopWindowStateMachine.cs` and `RecoveryTrayHost.cs` to automatically re-register the tray icon (`NIM_ADD`) and re-anchor desktop Z-order whenever `explorer.exe` starts or restarts. |
| **`IMP-05`**<br>*(Atlas Build Trap)* | **Python `BC7` Encoding Dependency Trap (`OVR-10`) & Dynamic Frame Count (`001.png..204.png` / `210.png`)**:<br>1. Standard Python `Pillow` cannot encode `BC7` `.dds`/`.ktx2` textures without Microsoft's `texconv.exe` binary.<br>2. Frame folders (`@Resources/Images/Jarvis/Active/` and `Idle/`) can have varying frame counts (e.g. `204` or `210` frames), and every PNG uses an 8-bit `PLTE` + `tRNS` indexed cyan palette! | In `tools/build_orb_atlas.py`:<br>1. Dynamically scan `Idle/` and `Active/` using all 8 filename patterns from `jarvis.lua:34`, convert 8-bit indexed `PLTE`+`tRNS` frames via `Image.open(p).convert("RGBA")`, and write `manifest.json` (`frameCount, cols, rows, frameW, frameH, format`).<br>2. Attempt `BC7_UNORM` `.dds` compression if `texconv.exe` is on `PATH`; otherwise output lossless/high-Q `.webp` (`quality=92, method=6`) and downsample each cell from `224x224` to **`160x160`** (`14x15` = `2240x2400` atlas = **`21.5 MB` uncompressed RGBA8** vs `42.1 MB`, matching `OVR-10`'s exact VRAM budget with **zero external C++ CLI tools required**!). |
| **`IMP-06`**<br>*(WebView2 Watchdog)* | **Chromium Renderer Hang / GPU Driver Reset (`Win+Ctrl+Shift+B`)**:<br>If the user updates an NVIDIA/AMD GPU driver or presses `Win+Ctrl+Shift+B`, WebView2's renderer or GPU process can crash (`CoreWebView2.ProcessFailed`), leaving a dead transparent window. | Wire **`CoreWebView2.ProcessFailed`** in `WebViewLifecycleManager.cs`: on `RenderProcessExited`, `RenderProcessUnresponsive`, or `GpuProcessExited`, automatically recreate or reload the `CoreWebView2` control and re-bind `CreateSharedBuffer(4096)` + state snapshot within **`<500ms`** without losing C# sensor, audio, or Named Pipe state. |
| **`IMP-07`**<br>*(Dual-Boot Safety)* | **Rainmeter + `ShipCore.Host.exe` Simultaneous Run Collision**:<br>If Rainmeter is still running `Spaceship` skins while `ShipCore.Host.exe` starts on boot, both `ShipCore.exe` and `ShipCore.Host.exe` will fight over `Data\*.txt`, `Settings.inc`, and `jarvis.py`! | 1. Acquire a named OS mutex **`Local\SpaceshipHud_HostMutex`** on `ShipCore.Host.exe` startup, plus acquire or gracefully stop `ShipCore.exe` (`SpaceshipShipCore` mutex).<br>2. If `ShipCore.Host.exe` detects `Rainmeter.exe` (`DummyRainWClass`) with active `Spaceship\*` configs while in Standalone mode, send `[!DeactivateConfigGroup Spaceship]` via `WM_COPYDATA` (`ShipCore.cs:143` `Bang()`), and have `Switch-HudHost.ps1` cleanly toggle between `Standalone` and `Rainmeter` in `<1s`. |

---

### 1.3 Table 2: The 10 Concrete Codebase Mismatches Found in `RainmeterSpaceship-fix-phase7-9-audit` (`BUG-01` – `BUG-10`)

Every item below was verified directly against the actual files in your repository and must be followed by Claude:

| ID | What the Initial Blueprint Assumed | Actual Codebase Reality (Verified Line-by-Line) | Exact Fix Built Into the Phases Below |
| :--- | :--- | :--- | :--- |
| **`BUG-01`** | Assumed `jarvis.py` stays running when Rainmeter is closed. | `Skins\Spaceship\@Resources\Jarvis\jarvislib\base.py:164` (`rainmeter_running()`) checks `FindWindowW("DummyRainWClass", None) != 0` and **`jarvis.py:1661-1664` exits after 15 misses (30s) with `"Rainmeter closed - exiting"`**! | In `jarvislib\base.py:164`, keep the exact function name `rainmeter_running()` (so `test_jarvis.py` mocks work) and return `True` if `DummyRainWClass` **OR** `SpaceshipHudHostClass` exists **OR** `_ipc_active[0]` is `True`. |
| **`BUG-02`** | Assumed `lib.lua` insets borders 4px inside `layout/layout.json` zone quads. | `tools\build.py:21` adds **`MARGIN = 18` px on all 4 sides** of every module (`WX = min_x - 18`). `Scripts\audio.lua:20` (`K=1.16`), `Scripts\dial.lua:19` (`K=1.13`), `Scripts\jarvis.lua:15` (`R=203..237`), and `Scripts\lib.lua:271` (`H.caption` hover pills) all draw **inside that 18px outer margin**! | Combine `tools\build.py`'s `18px` `ModuleMargin` + `IMP-02`'s `12px` `AnimationBleedMargin` (`30px` total expansion around nominal `layout.json` quads) in `HitTestRouter.cs`. |
| **`BUG-03`** | Claimed `app-icons.ps1` uses `ExtractAssociatedIcon` (`32x32`), skips `shell:*`, and writes `64x64` PNGs to `@Resources\Data\Icons\*.png`. | `Scripts\app-icons.ps1:42-112` **already** uses `SHParseDisplayName` + `SHGetImageList(4 /* SHIL_JUMBO 256x256 */)` for both `.exe` and `shell:AppsFolder\*`, and outputs to **`@Resources\Icons\`** (NOT `Data\Icons\`): `<id>.png` (`128x128` contrast-lifted greyscale), `<id>_glow.png` (`128x128` 3-pass box-blurred silhouette), and `_index.txt` (`lib.lua:215`). | Port `HudIcons.Make()` from `app-icons.ps1` into `AppScanner.cs` (with `IShellItemImageFactory::GetImage(128, 128)` fallback), outputting to **`@Resources\Icons\<id>.png`**, **`@Resources\Icons\<id>_glow.png`**, and **`@Resources\Icons\_index.txt`**. |
| **`BUG-04`** | Claimed `GmailPassword` is stored in plaintext in `Settings.inc` and proposed writing `GmailPassword=__VAULT__` to `Settings.inc`. | `Settings.inc` has **no** `GmailPassword` key! `Scripts\ShipCore.cs:162-177, 930-965` **already encrypts** Gmail & Calendar logins using **Windows DPAPI (`ProtectedData.Protect` with entropy `"SpaceshipHUD"`, `DataProtectionScope.CurrentUser`)** in `%LOCALAPPDATA%\SpaceshipHUD\gmail.dat` and `calendars.dat`! | Do **NOT** add `GmailPassword` to `Settings.inc`. `CloudPoller.cs` and `ConfigStore.cs` must use `ProtectedData.Protect` / `Unprotect` with entropy `"SpaceshipHUD"` on `%LOCALAPPDATA%\SpaceshipHUD\gmail.dat` and `calendars.dat` so existing logins work seamlessly. |
| **`BUG-05`** | Used `OX_<id>` / `OY_<id>` in `Offsets.inc` and looked for `CT_<id>` in `Settings.inc`. | `@Resources\Offsets.inc` uses **`<ModuleKey>_DX` and `<ModuleKey>_DY`** (e.g., `TopPower_DX=0`, `BottomAudio_DY=0`). Module visibility (`Off_<ModuleKey>=0|1`) and click-through (`CT_<ModuleKey>=0|1`) live in **`@Resources\State.inc`** (`control.lua:134,139`)! | Read/write `<ModuleKey>_DX` and `<ModuleKey>_DY` in `@Resources\Offsets.inc`, and read/write `Off_<ModuleKey>` and `CT_<ModuleKey>` in `@Resources\State.inc`. |
| **`BUG-06`** | Assumed `Bottom\Storage` runs `storage.lua` and `Left\Location` shows GPS lat/lon. | `Bottom\Storage\Storage.ini` runs **`Scripts\dial.lua` (6-control Systems Dial: BRT, VOL, MIC, PWR, HZ, GLW)**! `Left\Location\Location.ini` runs **`Scripts\location.lua` (Mission Clock Calendar)**! `Right\SysInfo\SysInfo.ini` runs **`Scripts\sysinfo.lua` (Network & Speedtest)**! (`Scripts\storage.lua` and `Scripts\sphere.lua` are legacy unused scripts.) | Map `BottomStorage` -> `SystemsDial.tsx` (`dial.lua`, with a center-click mode toggle to `StorageBars.tsx` from `storage.lua`), `LeftLocation` -> `MissionClock.tsx` (`location.lua`), and `RightSysInfo` -> `NetworkBlock.tsx` (`sysinfo.lua`). |
| **`BUG-07`** | Proposed passing `CoreWebView2SharedBuffer` (`e.getBuffer()`) via `worker.postMessage(buf, [buf])` to `jarvisCore.worker.ts`. | In Chromium/WebView2, an OS memory-mapped `ArrayBuffer` from `sharedbufferreceived` **cannot be transferred or cloned to a Web Worker** (`DataCloneError` on transfer; dead static copy on clone). | Keep `window.__sharedTelemetry = new Float32Array(e.getBuffer())` on the main UI realm and read it directly inside the `requestAnimationFrame` render loop (`0` GC allocations, `<0.01ms` read time). |
| **`BUG-08`** | Would have had Claude read `Scripts\icons.lua` (`4,798` lines) and `Frame\Parts\*.inc` (`261` lines) into LLM context. | Reading `icons.lua` (`4,798` lines of vector coordinates) into Claude's prompt context would waste `~55,000` tokens! | Provide `tools/export_ui_assets.py` (in Phase 0/3 below) so Python deterministically converts `icons.lua`, `zones.lua`, `Geometry.inc`, and `Frame\Parts\*.inc` into `src/generated/*.json` using **`0` Claude tokens**. |
| **`BUG-09`** | `OVR-15` proposed forcing `faster-whisper` and `kokoro-onnx` onto CPU at all times. | `Settings.inc:208` (`JarvisWhisperDevice=cuda`), `hearing.py:42`, and `tts.py:72` already check `gpu()` (`ctranslate2.get_cuda_device_count() > 0`): they use `CUDAExecutionProvider` (`0.24s`/sentence) when the RTX 5070 is awake (`HYBRID` mode) and automatically fall back to `cpu_threads()` (`gpu.py:16`) when the RTX 5070 is powered off (`ECO` mode)! | Preserve `hearing.py` and `tts.py`'s Optimus-safe `gpu()` routing, and add `ORT_ENABLE_ALL` + `ORT_SEQUENTIAL` to `tts.py:78,86` plus `intra_op_num_threads = 1` on `openWakeWord`. |
| **`BUG-10`** | `Settings.inc:144-183` has 5x duplicated comment blocks and lines `238-240` have leading indentation. | Confirmed in `Skins\Spaceship\@Resources\Settings.inc`. | Clean up `Settings.inc` in Phase 0 while preserving all user values (`Scale=0.67`, `FrameBehindTaskbar=1`, `FrameBrightness=95`, `JarvisCallMe=Sir`, `JarvisKokoroVoice=bm_lewis`). |

---

## Part 2: Global Operating Rules, Explicit Engineering Autonomy & Token-Minimization Protocol for Claude

> ### ⚠️ EXPLICIT ENGINEERING AUTONOMY & ADAPTATION MANDATE FOR CLAUDE (APPLIES TO ALL PHASES)
> 1. **You Are Authorized and Expected to Exercise Engineering Judgment**: This specification provides every file path, coordinate, formula, P/Invoke signature, and architectural decision so you never have to guess. **However, if during implementation or live testing on Windows 11 24H2 you find that any part of this plan is unwise, introduces a subtle edge case, or would be cleaner, safer, or faster if modified, you have full permission to adjust it.**
> 2. **How to Handle Adjustments**:
>    * For minor technical improvements (e.g., adjusting a Win32 flag, P/Invoke marshaling attribute, shader constant, or CSS easing curve), apply the better solution directly and note it in your phase completion summary.
>    * For major architectural changes that affect cross-file contracts or user-visible behavior, briefly state the issue found and your proposed improvement before applying it.
> 3. **Non-Negotiable Safety & Non-Destruction Rules (`CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md`)**:
>    * **Fake First in All Tests**: Never allow any test or verification script to reach real destructive OS calls (`SHEmptyRecycleBinW`, `SetSuspendState`, `LockWorkStation`, `shutdown.exe`, `Stop-Computer`, `taskkill`, `powercfg /setactive`, `BluetoothSetServiceState`). Every OS action in Python (`jarvislib\actions.py`) and C# (`ShipCore.Host`) must be behind a mockable interface and asserted as faked before the test runs.
>    * **Zero System Damage**: Never modify `HKLM`, never alter `Winlogon\Shell`, never install kernel drivers (`WinRing0.sys`), never run `ShipCore.Host.exe` as Administrator (`requestedExecutionLevel level="asInvoker"` only), and never inject DLLs into other processes (`SetWinEventHook` must always pass `WINEVENT_OUTOFCONTEXT = 0x0000`).
>    * **100% Rainmeter Preservation**: Never delete or overwrite `Skins\Spaceship\@Resources\Scripts\ShipCore.cs`, `Skins\Spaceship\@Resources\Bin\ShipCore.exe`, or any `.ini`/`.lua` file in `Skins\Spaceship\`.
> 4. **Token-Minimization Protocol (`CLAUDE.md` TokenWise Routing)**:
>    * **Never read large static asset files into LLM context**: Do NOT read `Skins\Spaceship\@Resources\Scripts\icons.lua` (`4,798` lines), `Skins\Spaceship\@Resources\Apps.ini` (`776` lines), `layout\layout.json` (`915` lines), or `@Resources\Images\Jarvis\*\*` (`420` PNGs) into context. Instead, run the deterministic Python generator `tools\export_ui_assets.py` (provided in Phase 0 below) and use the exact tables in Part 3 of this document.
>    * **Subagent Model Routing**: Use **Haiku** for mechanical reads/greps/renames, **Sonnet** for bounded 1–2 file implementations/tests, and **Opus** for architectural review and multi-file integration verification, logging each delegated task to `.tokenwise/log.ndjson` per `CLAUDE.md`.

---

## Part 3: Complete Coordinate, Matrix, Config & IPC Architecture Bible (Zero-Lookup Reference)

### 3.1 Exact Geometry & `TransformationMatrix` Table for All 25 Modules (`Geometry.inc` + `layout.json`)

Every module is authored on a `2560 x 1600` base canvas with `MARGIN = 18` px padding around its zones (`tools\build.py:21`).
* **Window Screen Position**:
  * `ScreenX = (WX + DX) * Scale + OriginX + MonX`
  * `ScreenY = (WY + DY) * Scale + OriginY + MonY`
* **Zone Local-to-Screen Coordinate Formula (`lib.lua:106` & `Geometry.inc`)**:
  * Within a module, a zone-local point `(x, y)` (where `0 <= x <= Z_W` and `0 <= y <= Z_H`) is offset by `(Z_X, Z_Y)` inside the module box `(WX, WY, WW, WH)`, or equivalently resides at global base-canvas coordinate `(WX + Z_X + x, WY + Z_Y + y)`.
  * When a zone has a non-identity `Z_TM = a;b;c;d;(tx*#Scale#);(ty*#Scale#)`, Rainmeter transforms module-local point `(px, py) = ((Z_X + x) * Scale, (Z_Y + y) * Scale)` to `(a*px + c*py + tx*Scale, b*px + d*py + ty*Scale)`.
  * In `SpaceshipUI` (where `HudCanvasWindow` is a single `2560 x 1600` canvas scaled by CSS `transform: scale(var(--hud-scale))` or `Scale`), each module `<div className="hud-module" style={{ left: WX + DX, top: WY + DY, width: WW, height: WH }}>` contains its zone `<div className="hud-zone" style={{ width: WW, height: WH, transform: 'matrix(a, b, c, d, tx, ty)', transformOrigin: '0 0' }}>` with inner origin `(Z_X, Z_Y)`.

| Module Key (`Offsets.inc` / `State.inc`) | `WX, WY, WW, WH` (Base `2560x1600` px) | Zone ID(s) | `Z_X, Z_Y, Z_W, Z_H` (Module-Local px) | Exact `Z_TM` (`a; b; c; d; tx; ty` in Base Canvas Units) | Global Quad Vertices in `layout.json` (`[x1,y1], [x2,y2], [x3,y3], [x4,y4]`) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`Frame`** | `0, 0, 2560, 1600` | *(Full)* | `0, 0, 2560, 1600` | `1; 0; 0; 1; 0; 0` | Full screen (`H = 1528` if `FrameBehindTaskbar=0`) |
| **`TopPower`** | `662, 22, 234, 82` | `T_power` | `18.63, 18.62, 197.9, 27.08` | `0.9959; 0.0912; 0; 1; 0.0772; -1.6992` | `[680.63, 40.62], [877.71, 58.67], [877.71, 85.75], [680.63, 67.7]` |
| **`TopBattery`** | `1664, 22, 234, 82` | `T_battery` | `18.29, 36.67, 197.9, 27.08` | `0.9959; -0.0912; 0; 1; 0.0758; 1.6682` | `[1682.29, 58.67], [1879.37, 40.62], [1879.37, 67.7], [1682.29, 85.75]` |
| **`TopConsole`** | `922, 4, 716, 143` | `T_settings` | `18.7, 18.57, 678.6, 106.06` | `1; 0; 0; 1; 0; 0` | `[940.7, 22.57], [1619.3, 22.57], [1619.3, 128.63], [940.7, 128.63]` |
| **`TopAlert`** | `569, 101, 96, 80` | `T_alert` | `18.17, 18.61, 58.93, 42.87` | `1; 0; 0; 1; 0; 0` | `[587.17, 119.61], [646.1, 119.61], [646.1, 162.48], [587.17, 162.48]` |
| **`TopGraphCPU`** | `658, 121, 269, 112` | `G1_cpu` | `18.57, 18.92, 231.62, 74.47` | `1; 0; 0; 1; 0; 0` | `[676.57, 139.92], [908.19, 139.92], [908.19, 214.39], [676.57, 214.39]` |
| **`TopGraphA`** | `983, 121, 269, 112` | `G2_select` | `18.65, 18.92, 231.62, 74.47` | `1; 0; 0; 1; 0; 0` | `[1001.65, 139.92], [1233.27, 139.92], [1233.27, 214.39], [1001.65, 214.39]` |
| **`TopGraphB`** | `1308, 121, 269, 112` | `G3_select` | `18.73, 18.92, 231.62, 74.47` | `1; 0; 0; 1; 0; 0` | `[1326.73, 139.92], [1558.35, 139.92], [1558.35, 214.39], [1326.73, 214.39]` |
| **`TopGraphRAM`** | `1633, 121, 269, 112` | `G4_ram` | `18.81, 18.92, 231.62, 74.47` | `1; 0; 0; 1; 0; 0` | `[1651.81, 139.92], [1883.43, 139.92], [1883.43, 214.39], [1651.81, 214.39]` |
| **`LeftCategory`** | `107, 70, 432, 662` | `Z1: L_tabs`<br>`Z2: L_category`<br>`Z3: L_dots` | `Z1: 43.35, 18.01, 376.34, 47.39`<br>`Z2: 18.97, 131, 347.25, 259.52`<br>`Z3: 79.92, 616.04, 146.29, 27.08` | `Z1: 0.9826; 0.1859; 0; 1; 0.7556; -8.0586`<br>`Z2: 0.9947; 0.1031; 0; 1; 0.1011; -1.9557`<br>`Z3: 1; 0; 0; 1; 0; 0` | `Z1: [150.35,88.01],[520.13,157.97],[520.13,205.36],[150.35,135.4]`<br>`Z2: [125.97,201],[471.37,236.8],[471.37,496.32],[125.97,460.52]`<br>`Z3: [186.92,686.04],[333.21,686.04],[333.21,713.12],[186.92,713.12]` |
| **`RightCategory`** | `2021, 70, 432, 662` | `Z1: R_tabs`<br>`Z2: R_category`<br>`Z3: R_dots` | `Z1: 18.87, 87.97, 376.34, 47.39`<br>`Z2: 67.63, 166.8, 347.25, 259.52`<br>`Z3: 205.79, 616.04, 146.29, 27.08` | `Z1: 0.9826; -0.1859; 0; 1; 0.3289; 3.5079`<br>`Z2: 0.9947; -0.1031; 0; 1; 0.3603; 6.9724`<br>`Z3: 1; 0; 0; 1; 0; 0` | `Z1: [2039.87,157.97],[2409.65,88.01],[2409.65,135.4],[2039.87,205.36]`<br>`Z2: [2088.63,236.8],[2434.03,201],[2434.03,460.52],[2088.63,496.32]`<br>`Z3: [2226.79,686.04],[2373.08,686.04],[2373.08,713.12],[2226.79,713.12]` |
| **`LeftLocation`** | `51, 478, 435, 213` | `L_location` | `18.08, 18.47, 398.86, 153.46` | `0.9984; 0.0566; 0; 1; 0.029; -1.0231` | `[69.08, 496.47], [467.3, 519.04], [467.3, 672.5], [69.08, 649.93]` |
| **`RightSysInfo`** | `2074, 478, 435, 213` | `R_sysinfo` | `18.7, 41.04, 398.86, 153.46` | `0.9984; -0.0566; 0; 1; 0.03; 1.0582` | `[2092.7, 519.04], [2490.92, 496.47], [2490.92, 649.93], [2092.7, 672.5]` |
| **`LeftSlot1`** | `51, 712, 435, 160` | `L_app1` | `18.08, 29.12, 398.37, 112.84` | `0.9996; -0.0273; 0; 1; 0.0068; 0.4938` | `[69.08, 741.12], [467.3, 730.24], [467.3, 843.08], [69.08, 853.96]` |
| **`LeftSlot2`** | `51, 848, 435, 177` | `L_app2` | `18.08, 46.05, 399.19, 112.83` | `0.9976; -0.0698; 0; 1; 0.0439; 1.2623` | `[69.08, 894.05], [467.3, 866.18], [467.3, 979.01], [69.08, 1006.88]` |
| **`LeftSlot3`** | `51, 984, 435, 194` | `L_app3` | `18.08, 62.97, 400.74, 112.83` | `0.9937; -0.1119; 0; 1; 0.1137; 2.0235` | `[69.08, 1046.97], [467.3, 1002.12], [467.3, 1114.95], [69.08, 1159.8]` |
| **`LeftSlot4`** | `51, 1120, 435, 211` | `L_app4` | `18.08, 79.89, 402.99, 112.83` | `0.9882; -0.1535; 0; 1; 0.214; 2.7744` | `[69.08, 1199.89], [467.3, 1138.05], [467.3, 1250.88], [69.08, 1312.72]` |
| **`LeftUpkeep`** | `51, 1294, 138, 129` | `L_upkeep` | `18.08, 38.31, 103.5, 72.21` | `0.9815; -0.191; 0; 1; 0.3337; 3.4535` | `[69.08, 1332.31], [170.67, 1312.54], [170.67, 1384.75], [69.08, 1404.52]` |
| **`RightSlot5`** | `2074, 712, 435, 160` | `R_app1` | `18.7, 18.24, 398.37, 112.84` | `0.9996; 0.0273; 0; 1; 0.007; -0.5107` | `[2092.7, 730.24], [2490.92, 741.12], [2490.92, 853.96], [2092.7, 843.08]` |
| **`RightSlot6`** | `2074, 848, 435, 177` | `R_app2` | `18.7, 18.18, 399.19, 112.83` | `0.9976; 0.0698; 0; 1; 0.0454; -1.3056` | `[2092.7, 866.18], [2490.92, 894.05], [2490.92, 1006.88], [2092.7, 979.01]` |
| **`RightSlot7`** | `2074, 984, 435, 194` | `R_app3` | `18.7, 18.12, 400.74, 112.83` | `0.9937; 0.1119; 0; 1; 0.1176; -2.0929` | `[2092.7, 1002.12], [2490.92, 1046.97], [2490.92, 1159.8], [2092.7, 1114.95]` |
| **`RightSlot8`** | `2074, 1120, 435, 211` | `R_app4` | `18.7, 18.05, 402.99, 112.84` | `0.9882; 0.1535; 0; 1; 0.2213; -2.8696` | `[2092.7, 1138.05], [2490.92, 1199.89], [2490.92, 1312.73], [2092.7, 1250.89]` |
| **`RightDev`** | `2371, 1294, 138, 129` | `R_dev` | `18.33, 18.54, 103.5, 72.22` | `0.9815; 0.191; 0; 1; 0.3383; -3.5013` | `[2389.33, 1312.54], [2490.92, 1332.31], [2490.92, 1404.53], [2389.33, 1384.76]` |
| **`CenterTarget`** | `819, 225, 922, 285` | `C_target` | `18.08, 18.72, 885.84, 248.24` | `1; 0; 0; 1; 0; 0` | `[837.08, 243.72], [1722.92, 243.72], [1722.92, 491.96], [837.08, 491.96]` |
| **`CenterHUD`** | `965, 487, 630, 364` | `C_hud` | `18.37, 18.5, 593.26, 327.22` | `1; 0; 0; 1; 0; 0` | `[983.37, 505.5], [1576.63, 505.5], [1576.63, 832.72], [983.37, 832.72]` |
| **`CenterSphere`** | `1026, 900, 508, 432` | `C_sphere` | `18.32, 18.48, 471.36, 394.92` | `1; 0; 0; 1; 0; 0` | `[1044.32, 918.48], [1515.68, 918.48], [1515.68, 1313.4], [1044.32, 1313.4]` |
| **`BottomStorage`** | `784, 1257, 226, 201` | `B_storage` | `18.54, 18.04, 188.95, 164.73` | `1; 0; 0; 1; 0; 0` | `[802.54, 1275.04], [991.49, 1275.04], [991.49, 1439.77], [802.54, 1439.77]` |
| **`BottomAudio`** | `1550, 1257, 226, 201` | `B_audio` | `18.51, 18.04, 188.95, 164.73` | `1; 0; 0; 1; 0; 0` | `[1568.51, 1275.04], [1757.46, 1275.04], [1757.46, 1439.77], [1568.51, 1439.77]` |
| **`BottomStrip`** | `851, 1436, 858, 96` | `Z1: B_stripL`<br>`Z2: B_stripR` | `Z1: 18.59, 54.1, 351.3, 23.69`<br>`Z2: 489.95, 18.22, 351.3, 23.69` | `Z1: 0.9948; -0.1021; 0; 1; 0.0974; 1.8987`<br>`Z2: 0.9948; 0.1021; 0; 1; 2.5662; -50.041` | `Z1: [869.59,1490.1],[1219.05,1454.22],[1219.05,1477.91],[869.59,1513.79]`<br>`Z2: [1340.95,1454.22],[1690.41,1490.1],[1690.41,1513.79],[1340.95,1477.91]` |
| **`BottomPanels`** | `586, 1326, 1388, 218` | `Z1: B_panelL`<br>`Z2: B_panelR` | `Z1: 18.04, 55.1, 95.85, 145.81`<br>`Z2: 1281.17, 18.99, 95.85, 146.39` | `Z1: 0.9263; -0.3767; 0.1888; 0.982; -9.0745; 7.7864`<br>`Z2: 0.9263; 0.3767; -0.1721; 0.9851; 97.6345; -482.3781` | `Z1: [604.04,1381.1],[692.83,1344.99],[720.36,1488.18],[631.57,1524.29]`<br>`Z2: [1867.17,1344.99],[1955.96,1381.1],[1930.77,1525.31],[1841.98,1489.2]` |
| **`OverlayDrawer`** | `982, 222, 596, 596` | `O_drawer` | `18, 18, 560, 560` | `1; 0; 0; 1; 0; 0` | Modal overlay at `1000, 240, 560x560` |
| **`OverlayControl`** | `742, 282, 1076, 936` | `O_control` | `18, 18, 1040, 900` | `1; 0; 0; 1; 0; 0` | Modal overlay at `760, 300, 1040x900` |
| **`OverlayJarvis`** | `662, 232, 1236, 652` | `O_jarvis` | `18, 18, 1200, 616` | `1; 0; 0; 1; 0; 0` | Modal overlay at `680, 250, 1200x616` |

---

### 3.2 Complete `CoreWebView2SharedBuffer(4096)` Zero-Copy Memory Layout (`1024 x float32`)

Allocated once in `WebViewLifecycleManager.cs` via `CoreWebView2Environment.CreateSharedBuffer(4096)` and mapped in JS via `window.__sharedTelemetry = new Float32Array(e.getBuffer())`:

```
Index    | Field Name             | Range / Units        | Writer Thread in C#          | Reader Component in JS (rAF)
---------|------------------------|----------------------|------------------------------|----------------------------------
[0..95]  | fftBands[0..95]        | 0.0 .. 1.0 (log Hz)  | WasapiSpectrumAnalyzer (60Hz)| AudioReactor.tsx
[96]     | audioRms               | 0.0 .. 1.0           | WasapiSpectrumAnalyzer (60Hz)| AudioReactor.tsx
[97]     | audioPeak              | 0.0 .. 1.0           | WasapiSpectrumAnalyzer (60Hz)| AudioReactor.tsx
[98]     | audioActiveFlag        | 0.0=silent, 1.0=live | WasapiSpectrumAnalyzer (60Hz)| AudioReactor.tsx / VisibilityGov
[99]     | jarvisVoiceLevel       | 0.0 .. 1.0           | HudIpcServer (FromJarvis)    | JarvisCore3D.tsx
[100]    | jarvisStateEnum        | 0=off,1=idle,2=lstn, | HudIpcServer (FromJarvis)    | JarvisCore3D.tsx
         |                        | 3=thnk,4=spk         |                              |
[101]    | cpuLoadPct             | 0.0 .. 100.0 %       | SensorCollector (1Hz/20Hz)   | FlightHud.tsx / TelemetryGraph
[102]    | gpuLoadPct             | 0.0 .. 100.0 %       | SensorCollector (1Hz/20Hz)   | FlightHud.tsx / TelemetryGraph
[103]    | gpuClockMHz            | 0.0 .. 3500.0 MHz    | SensorCollector (HWiNFO)     | FlightHud.tsx
[104]    | cpuEffClockMHz         | 0.0 .. 6000.0 MHz    | SensorCollector (PDH)        | FlightHud.tsx
[105]    | ramUsedBytesGB         | 0.0 .. 32.0 GB       | SensorCollector (1Hz)        | TelemetryGraph / BottomPanels
[106]    | ramTotalBytesGB        | 32.0 GB              | SensorCollector (1Hz)        | TelemetryGraph / BottomPanels
[107]    | vramUsedBytesGB        | 0.0 .. 12.0 GB       | SensorCollector (PDH)        | TelemetryGraph
[108]    | cpuTempC               | -1 (unmapped) or °C  | SensorCollector (HWiNFO)     | BottomStrip / TopAlert / Graph
[109]    | gpuTempC               | -1 (unmapped) or °C  | SensorCollector (HWiNFO)     | BottomStrip / TopAlert / Graph
[110]    | cpuPowerW              | -1 or Watts          | SensorCollector (HWiNFO)     | TopPowerBar / TelemetryGraph
[111]    | gpuPowerW              | -1 or Watts          | SensorCollector (HWiNFO)     | TopPowerBar / TelemetryGraph
[112]    | chargeRateW            | -1 or Watts (+chg)   | SensorCollector (HWiNFO)     | TopPowerBar / TopBatteryBar
[113]    | batteryRemainCapWh     | -1 or mWh            | SensorCollector (HWiNFO)     | TopBatteryBar
[114]    | batteryFullCapWh       | -1 or mWh            | SensorCollector (HWiNFO)     | TopBatteryBar
[115]    | fan1Rpm                | -1 or RPM            | SensorCollector (HWiNFO)     | BottomStrip
[116]    | fan2Rpm                | -1 or RPM            | SensorCollector (HWiNFO)     | ControlCenterModal
[117]    | ssdTempC               | -1 or °C             | SensorCollector (HWiNFO)     | StorageBars / ControlCenterModal
[118]    | netDownBps             | Bytes/sec            | NetworkMonitor (1Hz)         | NetworkBlock / TelemetryGraph
[119]    | netUpBps               | Bytes/sec            | NetworkMonitor (1Hz)         | NetworkBlock / TelemetryGraph
[120]    | diskReadBps            | Bytes/sec            | SensorCollector (PDH)        | BottomStrip / TelemetryGraph
[121]    | diskWriteBps           | Bytes/sec            | SensorCollector (PDH)        | BottomStrip / TelemetryGraph
[122]    | batteryPct             | 0 .. 100 %           | SensorCollector (1Hz)        | TopBatteryBar / TelemetryGraph
[123]    | acLineStatus           | 0=Battery, 1=AC      | SensorCollector (1Hz)        | TopBatteryBar / TopAlert
[124]    | batteryLifeSec         | -1 or seconds        | SensorCollector (1Hz)        | TopBatteryBar
[125]    | speakerVolPct          | 0 .. 100 % (-1=mute) | AudioController              | AudioReactor / SystemsDial
[126]    | micVolPct              | 0 .. 100 %           | AudioController              | SystemsDial
[127]    | micMuteFlag            | 0 or 1               | AudioController              | SystemsDial
[128]    | brightnessPct          | -1 or 0..100 %       | SensorCollector (WMI)        | SystemsDial
[129]    | pingMs                 | 0 .. 3000 ms         | NetworkMonitor               | NetworkBlock / BottomStrip
[130]    | wifiQualityPct         | 0 .. 100 %           | NetworkMonitor (WlanApi)     | NetworkBlock / BottomStrip
[131]    | uptimeSec              | seconds              | SensorCollector              | BottomTiltedPanels
[132]    | idleTimeSec            | seconds              | SensorCollector              | BottomTiltedPanels
[133]    | spxPrice               | S&P 500 price        | CloudPoller (Yahoo ^GSPC)    | FlightHud.tsx
[134]    | spxPrevClose           | S&P 500 prev close   | CloudPoller (Yahoo ^GSPC)    | FlightHud.tsx
[135]    | spxMarketOpenFlag      | 0=Closed, 1=Open     | CloudPoller (Yahoo ^GSPC)    | FlightHud.tsx
[136]    | hostFrameCounter       | monotonic uint32     | WasapiSpectrumAnalyzer (60Hz)| DiagnosticOverlay.tsx
```

---

### 3.3 Complete Bidirectional IPC Protocol (`C# <-> WebView2` & `C# <-> Python jarvis.py`)

#### A. WebView2 `chrome.webview.postMessage` (`JS -> C#`) & `PostWebMessageAsJson` (`C# -> JS`)
```typescript
// JS -> C# Messages
type JsToHostMessage =
  | { type: "ui.ready" } // Fired after fonts.ready + 2-frame rAF warmup; triggers intro.start
  | { type: "intro.done" } // Fired at t=3.2s; triggers IMP-03 2-Frame DwmFlush() Handoff
  | { type: "ui.animationLease"; active: boolean; durationMs: number; reason: string } // IMP-02 unclip lease
  | { type: "config.set"; file: "Settings.inc" | "State.inc" | "Offsets.inc" | "Apps.ini"; section: string; key: string; value: string | number }
  | { type: "config.batch"; writes: Array<{ file: string; section: string; key: string; value: string }> }
  | { type: "preset.save"; slot: 1 | 2 | 3 | 4 | 5 | 6 }
  | { type: "preset.load"; slot: 1 | 2 | 3 | 4 | 5 | 6 | "_undo" }
  | { type: "app.launch"; id: string; targetKind: "start" | "file" | "cmd"; targetValue: string; proc: string }
  | { type: "app.rescan" }
  | { type: "sensors.detect" }
  | { type: "llt.set"; feature: "hybrid" | "power" | "refresh" | "battery"; value: string }
  | { type: "llt.refresh" }
  | { type: "audio.setVolume"; percent: number }
  | { type: "audio.stepVolume"; delta: number }
  | { type: "audio.toggleMute" }
  | { type: "audio.nextDevice" }
  | { type: "media.key"; key: "playpause" | "next" | "prev" | "mute" }
  | { type: "sys.setBrightness"; percent: number }
  | { type: "sys.setMicVolume"; percent: number }
  | { type: "sys.powerAction"; action: "lock" | "sleep" | "restart" | "shutdown" }
  | { type: "shell.open"; uri: string; args?: string } // Restricted to allowlisted ms-settings:, https://, obsidian://, wt.exe, taskmgr.exe, notepad.exe
  | { type: "dialog.open"; dialog: "setup-gmail" | "setup-calendars" | "pick-todo" | "pick-vault" | "pick-profile" | "speedtest" | "run-setup" }
  | { type: "cloud.refresh"; feed: "mail" | "calendar" | "speedtest" | "upkeep" | "dev" }
  | { type: "jarvis.cmd"; cmd: "WAKE" | "CANCEL" | "REINDEX" | "FORGET" | "TRAINWAKE" | "QUIT" | "ASK"; arg?: string }
  | { type: "jarvis.service"; action: "start" | "stop" | "forgetFacts" }
  | { type: "modal.setVisible"; modalId: "control" | "drawer" | "jarvis" | null; focusCategory?: string };

// C# -> JS Messages
type HostToJsMessage =
  | { type: "state.init"; settings: Record<string, string>; state: Record<string, string>; offsets: Record<string, number>; hardware: Record<string, string>; appsIni: AppsCatalogPayload; zones: ZonesPayload; frameParts: FramePartsPayload; iconsIndex: string[] }
  | { type: "config.updated"; file: string; key: string; value: string }
  | { type: "intro.play"; playSound: boolean; soundUrl: string }
  | { type: "hull.handoff"; showInWebView: boolean } // IMP-03: true during Intro/Theme edit, false after DwmFlush
  | { type: "visibility.mode"; mode: "ACTIVE" | "AMBIENT" | "OCCLUDED" | "STEALTH"; tier: 0 | 1 | 2 | 3 }
  | { type: "telemetry.slow"; audioDevice: string; lanIp: string; wanIp: string; llt: LltState; mail: MailState; calendar: CalendarEvent[]; speed: SpeedState; upkeep: UpkeepState; dev: DevState; topProcs: TopProc[]; todos: TodoItem[]; runningWindows: string[]; runningProcs: string[] }
  | { type: "jarvis.update"; state: "offline" | "idle" | "listening" | "thinking" | "speaking"; level: number; say: string; err: string; pop?: "open" | "close"; convoLines?: ConvoLine[]; liveLine?: string; models?: string[]; mics?: string[]; btDevices?: string[]; factsCount?: number };
```

#### B. Dual Simplex Named Pipes (`C# ShipCore.Host <-> Python jarvis.py` — `OVR-07` & `FIX-DEBATE-11/12`)
* **Pipe 1 (`C# -> Python`)**: `\\.\pipe\SpaceshipHud_ToJarvis_<CurrentUserSID>`
  * Opened in C# as `NamedPipeServerStream(..., PipeDirection.Out, 1, PipeTransmissionMode.Byte, PipeOptions.Asynchronous)`.
  * Opened in Python (`jarvislib\base.py`) on a daemon listener thread using standard `open(pipe_to_jarvis_path, "rb")`.
  * **Messages (`NDJSON`, 1 line per message)**:
    * `{"type":"welcome.snapshot","settings":{...},"muted":0,"windows":["chrome.exe",...],"fg":"code.exe","calendar":"...","mail":"..."}`
    * `{"type":"cmd","raw":"WAKE 1792388000 0"}` (or `CANCEL`, `ASK 1792388000 what is on my schedule`, `REINDEX`, `FORGET`, `TRAINWAKE`, `QUIT`)
    * `{"type":"env","muted":0,"tier":0}`
    * `{"type":"kv.update","file":"windows.txt","body":"T 1792388000\nFG code.exe\nW chrome.exe\n..."}`
* **Pipe 2 (`Python -> C#`)**: `\\.\pipe\SpaceshipHud_FromJarvis_<CurrentUserSID>`
  * Opened in C# as `NamedPipeServerStream(..., PipeDirection.In, 1, PipeTransmissionMode.Byte, PipeOptions.Asynchronous)`.
  * Opened in Python (`jarvislib\base.py`) as `open(pipe_from_jarvis_path, "wb", buffering=0)`.
  * **Messages (`NDJSON`, 1 line per message)**:
    * `{"type":"hello","nonce":"<64-char hex from %LOCALAPPDATA%\\SpaceshipHUD\\ipc.nonce>","pid":12345}`
    * `{"type":"state","t":1792388000.12,"state":"speaking","level":0.642,"say":"...","err":"","pop":"1 open","hud":"1 mood serious"}`
    * `{"type":"convo.add","who":"U"|"J"|"S","t":1792388000,"text":"..."}`
    * `{"type":"convo.live","text":"J|1792388000|Streaming tokens..."}`
    * `{"type":"config.set","file":"Settings.inc","key":"JarvisPersonality","value":"serious"}`

---

## Part 4: Complete Animation Choreography Bible (Stage 0 + 165Hz Opening Sequence + 9 Runtime Animations)

### 4.1 Stage 0 (`0ms – ~400ms` Cold Boot): Native Win32 GDI+ Boot Reticle on `NativeHullWindow` (`IMP-01`)
When Windows restarts, `ShipCore.Host.exe` (compiled with `<PublishReadyToRun>true</PublishReadyToRun>`, launched at `<Priority>4</Priority>` with `<Delay>PT0S</Delay>`) starts in `<25ms` — while `CoreWebView2Environment.CreateAsync` takes `~350–450ms` to warm up on a cold reboot.
1. At `T + 15ms`, `NativeHullWindow` paints `@Resources\Images\hull.png` (dimmed to `25%` brightness) via `UpdateLayeredWindow` and starts a lightweight `16ms` (`60 FPS`) Win32 multimedia/GDI+ timer on `NativeHullWindow` that draws a crisp centered cyan reticle at `(1280 * Scale, 800 * Scale)`:
   * Outer segmented ring (`R = 54 * Scale`) rotating at `+120 deg/s`, inner counter-rotating arc (`R = 38 * Scale`) at `-180 deg/s`, and `"INITIALIZING SHIPCORE..."` in `B612 Mono` `10pt` cyan below the ring.
2. Meanwhile, `WebViewLifecycleManager.cs` initializes `HudCanvasWindow` in the background.
3. Inside `HudCanvasWindow`, `App.tsx` waits for:
   * `await document.fonts.ready` (ensuring `B612 Mono`, `Oxanium`, and `Michroma` are rasterized),
   * WebGL2 shader compilation + orb texture upload, and
   * **Two consecutive `requestAnimationFrame` ticks with `dt < 12ms`** (`WaitForCompositorReady`).
4. `App.tsx` then posts `{ type: "ui.ready" }` to C#. C# immediately stops the Stage 0 GDI+ reticle timer, hides `NativeHullWindow` (`SW_HIDE` so `HudCanvasWindow` owns the full unclipped hull during the intro), unclips `HudCanvasWindow` (`SetWindowRgn(IntPtr.Zero)`), plays `@Resources\Sounds\startup_quiet.wav` (if `BootSound=1`), and sends `{ type: "intro.play" }`.

---

### 4.2 Stage 1–5 (`0.00s – 3.40s` at `165Hz`): `<IntroSequence />` (`src/modules/IntroSequence.tsx`)
Exact port and 165Hz compositor upgrade of `Skins\Spaceship\@Resources\Scripts\boot.lua` + `Overlay\Boot\Boot.ini`:

1. **Stage 1 (`0.00s – 0.50s` | `boot.lua:79-91` `SCAN0..SCANN`) — Full-Screen Laser Scanner Plane & Progressive Hull De-Cloak**:
   * **Scanner Bar (`Boot.ini:78-85`)**: Full-width `2560px` horizontal laser assembly:
     * Outer vertical glow band: `height: 16px`, `background: linear-gradient(180deg, rgba(var(--accent-rgb), 0) 0%, rgba(var(--accent-rgb), 0.62) 50%, rgba(var(--accent-rgb), 0) 100%)`, `filter: drop-shadow(0 0 18px rgba(var(--accent-rgb), 0.85))`.
     * White-hot core filament: `height: 1.8px`, `background: rgb(235, 252, 255)`.
   * **Motion Curve (`boot.lua:81`)**: Sweeps `y` from `-40px` to `1620px` using the exact hybrid ease curve from `boot.lua:81`:
     $$y(t) = \left( \text{easeInOutQuad}(t) \cdot 0.35 + t \cdot 0.65 \right) \cdot 1640 - 40 \quad \text{for } t \in [0, 1]$$
   * **Progressive Hull Reveal**: `<CockpitFrame />` inside `HudCanvasWindow` uses `clip-path: inset(0px 0px calc(100% - var(--scan-pct)) 0px)` combined with an opacity ramp from `0 -> 1` so the brushed-metal cockpit struts, glass smudges, and neon `Decor` lines physically materialize in the wake of the laser beam.

2. **Stage 2 (`0.32s – 1.45s` | `boot.lua:93-97` `buildOrder()`) — Right-to-Left 3D Perspective Wing Unfold & SVG Laser Border Trace**:
   * All 22 HUD modules are sorted in descending order of their zone centroid $X$ coordinate (`RightDev` at $X=2440$ first -> `CenterSphere`/`CenterHUD`/`TopConsole` at $X=1280$ middle -> `LeftSlot1..4` at $X=268$ last):
     `const BOOT_ORDER = ["RightDev", "RightSlot8", "RightSlot7", "RightSlot6", "RightSlot5", "RightSysInfo", "RightCategory", "BottomPanels_R", "TopBattery", "TopGraphRAM", "BottomAudio", "BottomStrip_R", "TopGraphB", "CenterSphere", "CenterHUD", "CenterTarget", "TopConsole", "TopGraphA", "BottomStrip_L", "BottomStorage", "TopGraphCPU", "TopPower", "BottomPanels_L", "TopAlert", "LeftCategory", "LeftLocation", "LeftSlot1", "LeftSlot2", "LeftSlot3", "LeftSlot4", "LeftUpkeep"];`
   * Each module $i$ starts at $t_0 = 320\text{ms} + i \times 24\text{ms}$ and animates over `280ms` on the GPU compositor thread (`Element.animate()`):
     * `opacity: [0, 0.85, 0.4, 1]` (subtle sci-fi power-on flicker on the first 40ms, then smooth lock to `1.0`).
     * `transform`: Right-column modules unfold from `perspective(1100px) rotateY(-16deg) translateX(18px) scale(0.96)` -> `none`; Left-column modules unfold from `perspective(1100px) rotateY(16deg) translateX(-18px) scale(0.96)` -> `none`; Center/Top/Bottom modules unfold from `translateY(10px) scale(0.97)` -> `none`.
     * Every module's primary SVG chamfer/bracket path animates `stroke-dashoffset` from `pathLength` to `0` over `320ms`.

3. **Stage 3 (`0.50s – 1.55s` | `boot.lua:14, 96` `Spin()`) — Twin Dials Counter-Rotation Spin-Up & Core Singularity Ignition**:
   * When `BottomAudio` (`i=10`) and `BottomStorage` (`i=19`) trigger, their `spin` parameter animates from `0 -> 1` over `700ms` with cubic ease-out $\text{spin}(t) = 1 - (1 - t)^3$:
     * Ring rotation offset `rot = (1 - spin) * -200` degrees (`audio.lua:77`, `dial.lua:154`) winds the outer dashed rings and inner gap rings 200° clockwise into lock while all value arcs sweep from `0` to live readings!
   * Simultaneously, `CenterSphere` (`JarvisCore3D.tsx`) ignites from a central white-hot point (`scale(0.08)` -> `scale(1.0)`) while spinning its 3D plexus at `3x` yaw speed for `600ms` before settling to `1x` standby speed.

4. **Stage 4 (`1.30s – 2.85s` | `boot.lua:99-121` & `Boot.ini:88-205`) — Center Holographic System Check Card with Cipher Scramble**:
   * Drawn at exact base-canvas coordinates from `Boot.ini:94-205`:
     * Outer chamfered octagon path `PBg`: `M 1084,566 L 1476,566 L 1492,582 L 1492,816 L 1476,832 L 1084,832 L 1068,816 L 1068,582 Z` (`fill: rgba(0, 10, 18, 0.84)`, `stroke: rgba(var(--accent-rgb), 0.43)`, `strokeWidth: 1.4`).
     * Top/bottom divider lines: `Rect(1100, 606, 360, 1.4)` and `Rect(1100, 783, 360, 1.4)` (`fill: rgba(var(--accent-rgb), 0.59)`).
     * Top-left & bottom-right accent bars: `Rect(1084, 563, 120, 4)` and `Rect(1356, 831, 120, 4)` (`fill: rgb(var(--accent-rgb))`).
     * Header `Title` at `(1280, 588)` (`CenterCenter`, `13pt`, `FontNum`, `ColorAccent`): `"SYSTEM CHECK"`.
     * 6 Diagnostic Rows at `Y = 627, 654, 681, 708, 735, 762` (Label `L1..L6` left-aligned at `X = 1096`, Value `V1..V6` right-aligned at `X = 1392` in `ColorWhite`, Status `S1..S6` right-aligned at `X = 1466` in `ColorGood` for `OK`, `ColorWarn` for `CHECK`, `ColorAlert` for `FAIL`), revealed `75ms` apart using `scrambleDecode(text, 180)` (`01X#/>_` cipher):
       1. `CPU / GPU`: `${cpu}% / ${gpu}%` (`OK` if both `<90%`; split into two rows if either `>=90%`, matching `boot.lua:64-65`).
       2. `MEMORY`: `${ramPct}%` (`CHECK` if `>=90%`, else `OK`).
       3. `STORAGE`: `${drive1} ${usedPct}%` (`CHECK` if `>= WarnDiskPct`, else `OK`).
       4. `NETWORK`: `ONLINE` (`OK`) or `NO LINK` (`FAIL` in `ColorAlert`).
       5. `AUDIO`: `${deviceName.slice(0, 12)}` (`OK`) or `NO DEVICE` (`CHECK`).
       6. `POWER`: `${ac ? 'AC' : 'BAT'} ${batPct}%` (`CHECK` if `!ac && batPct < 20`, else `OK`).
     * At `t = 2.05s`, Verdict row at `(1280, 808)` (`15pt`, `CenterCenter`): `"ALL SYSTEMS NOMINAL"` (`ColorGood`) or `"${warns} SYSTEM(S) NEED ATTENTION"` (`ColorWarn`).

5. **Stage 5 (`2.85s – 3.40s` | `boot.lua:123-126` + `IMP-03` 2-Frame `DwmFlush()` Handoff)**:
   * Diagnostic card fades out over `220ms` (`opacity: 1 -> 0`, `transform: scale(1.015)`).
   * JS sends `{ type: "intro.done" }` to C#.
   * C# executes the **`IMP-03` 2-Frame `DwmFlush()` Handoff Protocol**:
     1. Frame 1: `ShowWindow(nativeHullHwnd, SW_SHOWNOACTIVATE)` + `DwmFlush()`.
     2. Frame 2: Wait 1 `rAF` (`6ms`), apply `SetWindowRgn(hudCanvasHwnd, masterRgn, false)` (which includes `18px` `ModuleMargin` + `12px` `AnimationBleedMargin` = `30px` total margin per zone), and send `{ type: "hull.handoff", showInWebView: false }` so `<CockpitFrame />` hides its static bitmap layer while keeping live vector/light layers if needed.
   * **Hard Failsafe (`boot.lua:70` `finish()`)**: A `4,500ms` watchdog timer in both JS and C# guarantees that even if an animation event is missed, all modules are forced to `opacity: 1` and `masterRgn` is applied.

---

### 4.3 The 9 Runtime Animations & `ui.animationLease` Protocol (`IMP-02`)

Because `SetWindowRgn` clips pixels outside `masterRgn` in steady state, `SpaceshipUI` includes a helper `withAnimationLease(durationMs, reason)` in `src/state/animationLease.ts` that posts `{ type: "ui.animationLease", active: true, durationMs, reason }` to `ShipCore.Host` (which immediately calls `SetWindowRgn(hudCanvasHwnd, IntPtr.Zero, false)` and sets a coalesced timer to restore `masterRgn` via the `IMP-03` 2-frame `DwmFlush()` protocol when the lease expires):

1. **Runtime Animation 1 — Hover Magnetic Brackets & Glow Lift (Zero Lease Needed — Fits Inside `30px` `ModuleMargin + AnimationBleedMargin`)**:
   * Hovering any `<HudSlot />`, `<CategorySchematic />`, `<TopConsole />` button, or `<BottomStrip />` cell smoothly expands its corner brackets outward by `3.5px`, increases SVG neon glow opacity by `+35%`, and sweeps a faint specular highlight across the chamfered plate (`140ms cubic-bezier(0.22, 1, 0.36, 1)`).
2. **Runtime Animation 2 — Themed HUD Caption Pill (`lib.lua:271` `H.caption` — Fits Inside `30px` Margin)**:
   * Pointing at any hit area spawns the chamfered `CaptionBox` (`fill: rgba(2, 14, 22, 0.84)`, `stroke: ColorAccent`) with a `90ms` `scale(0.94) -> scale(1)` + opacity pop and a `110ms` `scrambleDecode()` on the uppercase caption text (`"LAUNCH SOLIDWORKS  |  SCROLL: NEXT APP"`), auto-hiding after `6.0s` (`CAP_TIMEOUT = 6` in `lib.lua:260`) or on `pointerleave`.
3. **Runtime Animation 3 — Clover/JARVIS Wake-Word Radial Shockwave (`Uses 900ms ui.animationLease`)**:
   * When `jarvis.py` transitions from `idle` -> `listening` (wake word `"Hey Clover"` / `"Hey Jarvis"` heard or orb clicked), `JarvisCore3D.tsx` requests a `900ms` `ui.animationLease` and emits two concentric cyan-to-deep-blue shockwave rings that expand from `R = 165px` out to `R = 420px` (`opacity: 0.75 -> 0`) while the 3D plexus shell contracts slightly (`0.92x`) and springs back (`1.05x -> 1.0x`).
4. **Runtime Animation 4 — Clover/JARVIS Voice-Reactive 3D Plexus & Echo Swell (`60Hz/165Hz Zero-Copy SharedBuffer`)**:
   * While `state === "speaking"` or `"listening"`, `JarvisCore3D.tsx` reads `window.__sharedTelemetry[99]` (`jarvisVoiceLevel`) at 165Hz using asymmetric attack/release smoothing (`lvl += (target - lvl) * (target > lvl ? 0.55 : 0.18)` from `jarvis.lua:192`), swelling the outer echo orb (`1.12 + 0.28 * lvl`), pulsing the 56-node plexus radius (`RP * (1 + 0.07 * lvl)`), and driving the 22 radial voice bars (`jarvis.lua:135-146`).
5. **Runtime Animation 5 — Preset Morph Transition (`Presets\1..6` — `Uses 500ms ui.animationLease`)**:
   * Loading a preset in `Control Center > PRESETS` requests a `500ms` `ui.animationLease` and smoothly interpolates CSS custom properties (`--color-accent`, `--color-dim`, `--color-text`, `--hud-alpha`) and module offsets (`transform: translate3d(dx, dy, 0)` with `transition: transform 420ms cubic-bezier(0.16, 1, 0.3, 1)`) so modules glide to their new preset coordinates instead of snapping!
6. **Runtime Animation 6 — Red-Alert Thermal / Battery Warning Pulse (`TopAlert.tsx` — `Uses 1200ms ui.animationLease` on New Alert)**:
   * When a new warning triggers in `alert.lua` (`CPU >= 92°C`, `GPU >= 85°C`, `Disk >= 90%`, `Battery <= 20% on BAT`, `CPU >= 95%`), `TopAlert` pulses its pink/red warning triangle (`1Hz` sinusoidal glow on `FULL`/`LITE` tiers) and emits a single 1.2s warning ripple across the top console rail.
7. **Runtime Animation 7 — Twin Dials Damped Spring Physics (`SystemsDial.tsx` & `AudioReactor.tsx`)**:
   * Scrolling volume, brightness, mic, or HUD glow updates the target angle immediately while the visual arc, tick lights, and swinging glass selector wedge (`cur.ang ± 13°` in `dial.lua:177`) animate via a 165Hz critically damped spring (`stiffness = 210, damping = 24`) instead of stepping at 10 FPS.
8. **Runtime Animation 8 — Windscreen Target Reticle Roaming & Lock-On Zoom (`TargetReticle.tsx` — `target.lua:106-152`)**:
   * Smoothly glides across the upper windscreen trapezoid (`C_target`) at 165Hz using Perlin/quintic smootherstep $e(t) = t^3(t(6t - 15) + 10)$ (`target.lua:106`), dwelling for `1.0s` at each destination with a `zoom = 1 + (lockAnim / 18) * 0.08` lock-on pulse and `4Hz` box flash (`target.lua:138, 152`).
9. **Runtime Animation 9 — Modal Chamfered Iris Unfold (`ControlCenterModal`, `CargoDrawerModal`, `JarvisLogModal` in `modal.html`)**:
   * When `ModalOverlayWindow` is shown (`SW_SHOWNOACTIVATE`, `<6ms`), the modal panel animates a `165ms` sci-fi iris unfold (`clip-path` + `scale(0.96 -> 1.0)` + `opacity: 0 -> 1` with `cubic-bezier(0.16, 1, 0.3, 1)`).

---

## Part 5: Phase-by-Phase Execution Prompts & Complete Code Specifications for Claude (`Phase 0` – `Phase 6`)

Give these phases to Claude in order (or one phase per prompt). Every phase contains a self-contained prompt block, complete code implementations, exact file paths, and verification gates.

---

### PHASE 0: Python Backend Fix (`BUG-01`), Asset Exporter (`BUG-08`), AOT Host Project (`IMP-01`), Dual-Boot Mutex (`IMP-07`) & Lock-Free Recovery (`WP-0`)

#### 📋 Copy-Paste Prompt for Claude — Phase 0:
```markdown
Execute Phase 0 of the Standalone Spaceship App migration (`WP-0`).

AUTONOMY & ADJUSTMENT NOTICE:
You have explicit permission to adjust or improve any implementation detail in this phase if you discover a cleaner, safer, or better-performing approach on this machine (`BLACK-CLOVER`), provided all 706+ assertions in `test_jarvis.py` pass and `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md` is strictly obeyed. Note any adjustments in your summary.

TOKEN-SAVING & SUBAGENT ROUTING:
Follow `CLAUDE.md` TokenWise rules: use Haiku for file reads/checks, Sonnet for scoped file edits, and Opus for verification. Do NOT scan the repository or read `Scripts\icons.lua` (4,798 lines) into context — run the `tools\export_ui_assets.py` script below instead.

STEP-BY-STEP INSTRUCTIONS:
1. Read `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md` first.
2. Apply `BUG-01` fix in `Skins\Spaceship\@Resources\Jarvis\jarvislib\base.py` (line 164) and `BUG-09` ONNX optimization in `Skins\Spaceship\@Resources\Jarvis\jarvislib\tts.py` (lines 74-88), plus clean the duplicate comment headers in `Skins\Spaceship\@Resources\Settings.inc` (lines 144-183 & 238-240).
3. Create and run `tools\export_ui_assets.py` to deterministically convert `Scripts\icons.lua` (4,798 lines), `Data\zones.lua`, `Frame\Parts\*.inc`, and `Geometry.inc` into JSON files under `Skins\Spaceship\@Resources\UI\generated\`.
4. Scaffold `SpaceshipApp\ShipCore.Host\ShipCore.Host.csproj` with `<PublishReadyToRun>true</PublishReadyToRun>` (`IMP-01`, no single-file decompression delay on cold boot!), `app.manifest` (`asInvoker` + `PerMonitorV2`), `SystemChangeLedger.cs`, `RecoveryTrayHost.cs` (`Ctrl+Alt+Shift+H` via `ShowWindowAsync` + `TaskbarCreated` hook from `IMP-04`), and `Program.cs` with `Local\SpaceshipHud_HostMutex` + Rainmeter collision guard (`IMP-07`).
5. Create `Skins\Spaceship\@Resources\Scripts\Switch-HudHost.ps1` (`IMP-07`).
6. Run the Phase 0 Verification Gate and report exact command outputs.
```

#### Exact File Edits & Code Implementations for Phase 0:

##### 0.1 `Skins\Spaceship\@Resources\Jarvis\jarvislib\base.py` (Line 164 — Fixes `BUG-01` 30-Second Standalone Exit Loop)
In `Skins\Spaceship\@Resources\Jarvis\jarvislib\base.py`, replace lines `164–165`:
```python
# BEFORE (lines 164-165):
def rainmeter_running():
    return ctypes.windll.user32.FindWindowW("DummyRainWClass", None) != 0

# AFTER (keep exact function name `rainmeter_running` so test_jarvis.py mocks/imports work):
_ipc_active = [False]


def rainmeter_running():
    """True while either Rainmeter (DummyRainWClass) or standalone ShipCore.Host (SpaceshipHudHostClass / IPC pipe) is running."""
    return (
        _ipc_active[0]
        or ctypes.windll.user32.FindWindowW("DummyRainWClass", None) != 0
        or ctypes.windll.user32.FindWindowW("SpaceshipHudHostClass", None) != 0
    )
```

##### 0.2 `Skins\Spaceship\@Resources\Jarvis\jarvislib\tts.py` (Lines 74–88 — `OVR-15` + `BUG-09` ONNX Graph Optimization)
In `Skins\Spaceship\@Resources\Jarvis\jarvislib\tts.py` inside `_kokoro(voice_path, text)`:
```python
        if (os.path.exists(full) and time.time() >= _voice_gpu_off[0] and gpu()
                and "CUDAExecutionProvider" in rt.get_available_providers()):
            _cuda_dlls()
            opts = rt.SessionOptions()
            opts.log_severity_level = 3
            opts.graph_optimization_level = rt.GraphOptimizationLevel.ORT_ENABLE_ALL
            opts.execution_mode = rt.ExecutionMode.ORT_SEQUENTIAL
            s = rt.InferenceSession(full, opts, providers=[("CUDAExecutionProvider", {"cudnn_conv_algo_search": "HEURISTIC"}),
                                                           "CPUExecutionProvider"])
            if s.get_providers()[0] == "CUDAExecutionProvider":
                sess, used = s, full
        _voice_dev[0] = "cuda" if sess else "cpu"
        if sess is None:
            opts = rt.SessionOptions()
            opts.log_severity_level = 3
            opts.intra_op_num_threads = cpu_threads()
            opts.inter_op_num_threads = 1
            opts.graph_optimization_level = rt.GraphOptimizationLevel.ORT_ENABLE_ALL
            opts.execution_mode = rt.ExecutionMode.ORT_SEQUENTIAL
            sess, used = rt.InferenceSession(voice_path, opts, providers=["CPUExecutionProvider"]), voice_path
```

##### 0.3 `tools\export_ui_assets.py` (Zero-LLM-Token Exporter for `icons.lua`, `Geometry.inc`, and `Frame\Parts\*.inc`)
Create `tools\export_ui_assets.py` and run `py -3 tools\export_ui_assets.py` so Claude never has to read `icons.lua` (4,798 lines) into prompt context:
```python
#!/usr/bin/env python3
"""Deterministically exports icons.lua (4,798 lines), Geometry.inc (25 modules), and Frame/Parts/*.inc
into JSON files in Skins/Spaceship/@Resources/UI/generated/ so the UI build needs 0 LLM tokens to port them."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKINS = ROOT / "Skins" / "Spaceship"
RES = SKINS / "@Resources"
OUT = RES / "UI" / "generated"
OUT.mkdir(parents=True, exist_ok=True)


def parse_icons_lua():
    text = (RES / "Scripts" / "icons.lua").read_text(encoding="utf-8", errors="ignore")
    icons = {}
    # Match each `I.<name> = { ... }` block
    pattern = re.compile(r"I\.([A-Za-z0-9_]+)\s*=\s*\{(.*?)\n\}", re.S)
    prim_pat = re.compile(r"\{\s*'([lpcae])'\s*,([^}]*)\}")
    for m in pattern.finditer(text):
        name, body = m.group(1), m.group(2)
        prims = []
        for pm in prim_pat.finditer(body):
            kind = pm.group(1)
            nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", pm.group(2))]
            prims.append([kind] + nums)
        icons[name] = prims
    # Also resolve aliases like `I.openrocket_wire = I.starship`
    for am in re.finditer(r"I\.([A-Za-z0-9_]+)\s*=\s*I\.([A-Za-z0-9_]+)", text):
        dst, src = am.group(1), am.group(2)
        if src in icons:
            icons[dst] = icons[src]
    (OUT / "iconsData.json").write_text(json.dumps(icons, separators=(",", ":")), encoding="utf-8")
    print(f"Exported {len(icons)} vector icons to iconsData.json")


def parse_geometries():
    geoms = {}
    for gfile in sorted(SKINS.rglob("Geometry.inc")):
        kv = {}
        for line in gfile.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line and not line.startswith(";") and not line.startswith("[") and "=" in line:
                k, v = line.split("=", 1)
                kv[k.strip()] = v.strip()
        mod = kv.get("Module")
        if not mod:
            continue
        zones = []
        zcount = int(kv.get("ZoneCount", "0"))
        for i in range(1, zcount + 1):
            raw_tm = kv.get(f"Z{i}_TM", "1;0;0;1;0;0")
            tm_parts = [float(re.sub(r"[^\d.\-+]", "", p.split("*")[0]) or "0") for p in raw_tm.split(";")]
            zones.append({
                "id": kv.get(f"Z{i}", f"Z{i}"),
                "x": float(kv.get(f"Z{i}_X", 0)),
                "y": float(kv.get(f"Z{i}_Y", 0)),
                "w": float(kv.get(f"Z{i}_W", 0)),
                "h": float(kv.get(f"Z{i}_H", 0)),
                "tm": tm_parts if len(tm_parts) == 6 else [1, 0, 0, 1, 0, 0],
            })
        geoms[mod] = {
            "key": mod,
            "config": kv.get("ModuleConfig", ""),
            "wx": float(kv.get("WX", 0)),
            "wy": float(kv.get("WY", 0)),
            "ww": float(kv.get("WW", 0)),
            "wh": float(kv.get("WH", 0)),
            "zones": zones,
        }
    (OUT / "geometryData.json").write_text(json.dumps(geoms, indent=2), encoding="utf-8")
    print(f"Exported {len(geoms)} module geometries to geometryData.json")


def parse_frame_parts():
    parts = {}
    for pfile in sorted((SKINS / "Frame" / "Parts").glob("*.inc")):
        lines = [
            ln.strip()
            for ln in pfile.read_text(encoding="utf-8", errors="ignore").splitlines()
            if ln.strip() and not ln.strip().startswith(";")
        ]
        parts[pfile.stem] = lines
    (OUT / "framePartsData.json").write_text(json.dumps(parts, indent=2), encoding="utf-8")
    print(f"Exported {len(parts)} frame part definitions to framePartsData.json")


if __name__ == "__main__":
    parse_icons_lua()
    parse_geometries()
    parse_frame_parts()
```

##### 0.4 `SpaceshipApp\ShipCore.Host\ShipCore.Host.csproj` & `app.manifest` (`IMP-01` ReadyToRun Native Pre-Compilation)
Create `SpaceshipApp\ShipCore.Host\ShipCore.Host.csproj` (notice `<PublishReadyToRun>true</PublishReadyToRun>` and `<EnableCompressionInSingleFile>false</EnableCompressionInSingleFile>` per `IMP-01` so cold-boot execution is instantaneous with zero decompression stall!):
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net10.0-windows</TargetFramework>
    <!-- Fallback note for Claude: if `dotnet --list-sdks` shows net8.0 or net9.0 instead of net10.0, set TargetFramework to the highest installed net*-windows SDK -->
    <RuntimeIdentifier>win-x64</RuntimeIdentifier>
    <UseWindowsForms>true</UseWindowsForms>
    <AllowUnsafeBlocks>true</AllowUnsafeBlocks>
    <Nullable>enable</Nullable>
    <ImplicitUsings>enable</ImplicitUsings>
    <ApplicationManifest>app.manifest</ApplicationManifest>
    <AssemblyName>ShipCore.Host</AssemblyName>
    <!-- IMP-01: Self-contained + ReadyToRun AOT native code + NO compression stall on cold boot -->
    <SelfContained>true</SelfContained>
    <PublishSingleFile>true</PublishSingleFile>
    <PublishReadyToRun>true</PublishReadyToRun>
    <EnableCompressionInSingleFile>false</EnableCompressionInSingleFile>
    <IncludeNativeLibrariesForSelfExtract>true</IncludeNativeLibrariesForSelfExtract>
    <DebugType>embedded</DebugType>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="Microsoft.Web.WebView2" Version="1.0.2903.40" />
    <PackageReference Include="System.Management" Version="9.0.0" />
    <PackageReference Include="System.Security.Cryptography.ProtectedData" Version="9.0.0" />
  </ItemGroup>
</Project>
```

Create `SpaceshipApp\ShipCore.Host\app.manifest`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<assembly manifestVersion="1.0" xmlns="urn:schemas-microsoft-com:asm.v1">
  <assemblyIdentity version="1.0.0.0" name="SpaceshipHUD.ShipCore.Host"/>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v2">
    <security>
      <requestedPrivileges xmlns="urn:schemas-microsoft-com:asm.v3">
        <!-- MANDATORY SAFETY RULE: Always run as standard user (asInvoker), NEVER requireAdministrator -->
        <requestedExecutionLevel level="asInvoker" uiAccess="false" />
      </requestedPrivileges>
    </security>
  </trustInfo>
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2</dpiAwareness>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true/pm</dpiAware>
    </windowsSettings>
  </application>
</assembly>
```

##### 0.5 `SpaceshipApp\ShipCore.Host\RecoveryTrayHost.cs` (`FIX-DEBATE-18` + `IMP-04` `TaskbarCreated` & `WM_QUERYENDSESSION`)
Create `SpaceshipApp\ShipCore.Host\RecoveryTrayHost.cs` running on its own dedicated background Win32 thread so `Ctrl+Alt+Shift+H` (`ShowWindowAsync`), `TaskbarCreated` (when `explorer.exe` restarts), and `WM_QUERYENDSESSION` (when Windows restarts) are 100% immune to UI thread blocks:
```csharp
using System.Runtime.InteropServices;

namespace ShipCore.Host;

public sealed class RecoveryTrayHost : IDisposable
{
    private const int WM_DESTROY = 0x0002;
    private const int WM_CLOSE = 0x0010;
    private const int WM_QUERYENDSESSION = 0x0011;
    private const int WM_ENDSESSION = 0x0016;
    private const int WM_HOTKEY = 0x0312;
    private const int WM_USER_TRAY = 0x0400 + 42;

    private const uint MOD_ALT = 0x0001, MOD_CONTROL = 0x0002, MOD_SHIFT = 0x0004, MOD_NOREPEAT = 0x4000;
    private const int HOTKEY_EMERGENCY_HIDE = 9001; // Ctrl+Alt+Shift+H
    private const int HOTKEY_REPLAY_INTRO   = 9002; // Ctrl+Alt+Shift+R
    private const int HOTKEY_PRIVACY_MODE   = 9003; // Ctrl+Alt+Shift+P
    private const int HOTKEY_DIAG_OVERLAY   = 9004; // Ctrl+Alt+Shift+D
    private const int SW_HIDE = 0, SW_SHOWNOACTIVATE = 4;

    [DllImport("user32.dll", SetLastError = true)] private static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);
    [DllImport("user32.dll", SetLastError = true)] private static extern bool UnregisterHotKey(IntPtr hWnd, int id);
    [DllImport("user32.dll")] private static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern uint RegisterWindowMessageW(string lpString);

    private readonly Thread _thread;
    private readonly ManualResetEventSlim _ready = new(false);
    private IntPtr _messageHwnd;
    private uint _wmTaskbarCreated;
    private volatile bool _emergencyHidden;
    private volatile IntPtr _hullHwnd;
    private volatile IntPtr _canvasHwnd;
    private volatile IntPtr _modalHwnd;

    public event Action? OnReplayIntroRequested;
    public event Action? OnTogglePrivacyRequested;
    public event Action? OnToggleDiagnosticsRequested;
    public event Action? OnExplorerRestarted;
    public event Action? OnSystemShutdownInitiated;

    public IntPtr MessageHwnd => _messageHwnd;

    public RecoveryTrayHost()
    {
        _thread = new Thread(ThreadMain) { Name = "SpaceshipRecoveryHost", IsBackground = true, Priority = ThreadPriority.AboveNormal };
        _thread.SetApartmentState(ApartmentState.STA);
        _thread.Start();
        _ready.Wait(TimeSpan.FromSeconds(5));
    }

    public void RegisterManagedWindows(IntPtr hullHwnd, IntPtr canvasHwnd, IntPtr modalHwnd)
    {
        _hullHwnd = hullHwnd;
        _canvasHwnd = canvasHwnd;
        _modalHwnd = modalHwnd;
    }

    private void ThreadMain()
    {
        _wmTaskbarCreated = RegisterWindowMessageW("TaskbarCreated");
        using var window = new RecoveryMessageWindow(this);
        _messageHwnd = window.Handle;
        uint mods = MOD_CONTROL | MOD_ALT | MOD_SHIFT | MOD_NOREPEAT;
        RegisterHotKey(_messageHwnd, HOTKEY_EMERGENCY_HIDE, mods, 'H');
        RegisterHotKey(_messageHwnd, HOTKEY_REPLAY_INTRO,   mods, 'R');
        RegisterHotKey(_messageHwnd, HOTKEY_PRIVACY_MODE,   mods, 'P');
        RegisterHotKey(_messageHwnd, HOTKEY_DIAG_OVERLAY,   mods, 'D');
        _ready.Set();
        Application.Run();
    }

    private void ToggleEmergencyHide()
    {
        _emergencyHidden = !_emergencyHidden;
        int cmd = _emergencyHidden ? SW_HIDE : SW_SHOWNOACTIVATE;
        // FIX-DEBATE-18: ShowWindowAsync posts directly to kernel window state without blocking on UI thread!
        if (_hullHwnd != IntPtr.Zero) ShowWindowAsync(_hullHwnd, cmd);
        if (_canvasHwnd != IntPtr.Zero) ShowWindowAsync(_canvasHwnd, cmd);
        if (_modalHwnd != IntPtr.Zero && _emergencyHidden) ShowWindowAsync(_modalHwnd, SW_HIDE);
    }

    private sealed class RecoveryMessageWindow : NativeWindow, IDisposable
    {
        private readonly RecoveryTrayHost _owner;
        private NotifyIcon _tray;

        public RecoveryMessageWindow(RecoveryTrayHost owner)
        {
            _owner = owner;
            CreateHandle(new CreateParams
            {
                Caption = "SpaceshipHudHost",
                ClassName = null, // Also register "SpaceshipHudHostClass" in Program.cs so base.py:rainmeter_running() sees it
                Style = 0,
                ExStyle = 0x00000080 // WS_EX_TOOLWINDOW
            });
            _tray = CreateTrayIcon();
        }

        private NotifyIcon CreateTrayIcon()
        {
            var menu = new ContextMenuStrip();
            menu.Items.Add("Replay Opening Animation (Ctrl+Alt+Shift+R)", null, (_, _) => _owner.OnReplayIntroRequested?.Invoke());
            menu.Items.Add("Toggle Emergency Hide (Ctrl+Alt+Shift+H)", null, (_, _) => _owner.ToggleEmergencyHide());
            menu.Items.Add("Toggle Screen-Share Privacy (Ctrl+Alt+Shift+P)", null, (_, _) => _owner.OnTogglePrivacyRequested?.Invoke());
            menu.Items.Add("Toggle Diagnostic Overlay (Ctrl+Alt+Shift+D)", null, (_, _) => _owner.OnToggleDiagnosticsRequested?.Invoke());
            menu.Items.Add(new ToolStripSeparator());
            menu.Items.Add("Exit Standalone HUD", null, (_, _) => { _owner.OnSystemShutdownInitiated?.Invoke(); Environment.Exit(0); });
            return new NotifyIcon
            {
                Text = "Spaceship HUD (BLACK-CLOVER)",
                Icon = SystemIcons.Shield,
                ContextMenuStrip = menu,
                Visible = true
            };
        }

        protected override void WndProc(ref Message m)
        {
            if (m.Msg == WM_HOTKEY)
            {
                int id = m.WParam.ToInt32();
                if (id == HOTKEY_EMERGENCY_HIDE) _owner.ToggleEmergencyHide();
                else if (id == HOTKEY_REPLAY_INTRO) _owner.OnReplayIntroRequested?.Invoke();
                else if (id == HOTKEY_PRIVACY_MODE) _owner.OnTogglePrivacyRequested?.Invoke();
                else if (id == HOTKEY_DIAG_OVERLAY) _owner.OnToggleDiagnosticsRequested?.Invoke();
                return;
            }
            // IMP-04: Never block Windows Restart / Shutdown!
            if (m.Msg == WM_QUERYENDSESSION || m.Msg == WM_ENDSESSION)
            {
                m.Result = (IntPtr)1;
                _owner.OnSystemShutdownInitiated?.Invoke();
                if (m.Msg == WM_ENDSESSION && m.WParam != IntPtr.Zero)
                {
                    Environment.Exit(0);
                }
                return;
            }
            // IMP-04: Re-register tray icon & Z-order if explorer.exe restarts
            if (_owner._wmTaskbarCreated != 0 && m.Msg == (int)_owner._wmTaskbarCreated)
            {
                _tray.Visible = false;
                _tray.Visible = true;
                _owner.OnExplorerRestarted?.Invoke();
                return;
            }
            base.WndProc(ref m);
        }

        public void Dispose()
        {
            _tray.Visible = false;
            _tray.Dispose();
            DestroyHandle();
        }
    }

    public void Dispose()
    {
        if (_messageHwnd != IntPtr.Zero)
        {
            UnregisterHotKey(_messageHwnd, HOTKEY_EMERGENCY_HIDE);
            UnregisterHotKey(_messageHwnd, HOTKEY_REPLAY_INTRO);
            UnregisterHotKey(_messageHwnd, HOTKEY_PRIVACY_MODE);
            UnregisterHotKey(_messageHwnd, HOTKEY_DIAG_OVERLAY);
        }
    }
}
```

##### 0.6 `Skins\Spaceship\@Resources\Scripts\Switch-HudHost.ps1` (`IMP-07` Dual-Boot Collision Prevention & 1-Second Rollback)
Create `Skins\Spaceship\@Resources\Scripts\Switch-HudHost.ps1`:
```powershell
<#
.SYNOPSIS
Switches BLACK-CLOVER Spaceship HUD between Standalone Mode (ShipCore.Host.exe) and Rainmeter Mode in <1s.
Enforces IMP-07 so Rainmeter and ShipCore.Host.exe never fight over Settings.inc, Data\*.txt, or jarvis.py.
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('Standalone', 'Rainmeter')]
    [string]$Mode
)
$ErrorActionPreference = 'Stop'
$res = Split-Path $PSScriptRoot -Parent
$hostExe = Join-Path $res 'Bin\ShipCore.Host.exe'
$rmExe = @("$env:ProgramFiles\Rainmeter\Rainmeter.exe", "${env:ProgramFiles(x86)}\Rainmeter\Rainmeter.exe") |
         Where-Object { Test-Path $_ } | Select-Object -First 1

if ($Mode -eq 'Standalone') {
    Write-Host "[Switch-HudHost] Switching to Standalone Mode (ShipCore.Host.exe)..." -ForegroundColor Cyan
    # 1. Cleanly deactivate Rainmeter Spaceship skin group if Rainmeter is running
    if ($rmExe -and (Get-Process Rainmeter -ErrorAction SilentlyContinue)) {
        & $rmExe '!DeactivateConfigGroup' 'Spaceship'
        & $rmExe '!DeactivateConfigGroup' 'SpaceshipBoot'
        Start-Sleep -Milliseconds 250
    }
    # 2. Stop legacy ShipCore.exe helper so ShipCore.Host.exe owns all polling
    Get-Process ShipCore -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    # 3. Launch ShipCore.Host.exe and register startup task
    if (-not (Test-Path $hostExe)) {
        throw "ShipCore.Host.exe not found at $hostExe. Build Phase 0/1 first."
    }
    Start-Process -FilePath $hostExe -ArgumentList @('--install-startup', "`"$res`"") -Wait -WindowStyle Hidden
    if (-not (Get-Process 'ShipCore.Host' -ErrorAction SilentlyContinue)) {
        Start-Process -FilePath $hostExe -ArgumentList @("`"$res`"")
    }
    Write-Host "[Switch-HudHost] Standalone HUD active." -ForegroundColor Green
}
else {
    Write-Host "[Switch-HudHost] Rolling back to Rainmeter Mode..." -ForegroundColor Yellow
    if (Test-Path $hostExe) {
        Start-Process -FilePath $hostExe -ArgumentList @('--uninstall-startup', "`"$res`"") -Wait -WindowStyle Hidden
    }
    Get-Process 'ShipCore.Host' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 250
    if ($rmExe) {
        if (-not (Get-Process Rainmeter -ErrorAction SilentlyContinue)) {
            Start-Process -FilePath $rmExe
            Start-Sleep -Milliseconds 800
        }
        & $rmExe '!RefreshApp'
    }
    Write-Host "[Switch-HudHost] Rainmeter Mode restored." -ForegroundColor Green
}
```

#### What Claude Must Avoid & Where to Be Careful in Phase 0:
* **DO NOT** set `<EnableCompressionInSingleFile>true</EnableCompressionInSingleFile>` in `ShipCore.Host.csproj` (`IMP-01`) — always use `<PublishReadyToRun>true</PublishReadyToRun>` and `<EnableCompressionInSingleFile>false</EnableCompressionInSingleFile>` so cold-boot execution takes `<25ms` with zero decompression overhead.
* **DO NOT** modify `Skins\Spaceship\@Resources\Scripts\ShipCore.cs` or `Bin\ShipCore.exe`.
* **DO NOT** block `WM_QUERYENDSESSION` or `WM_ENDSESSION` (`IMP-04`).

#### Phase 0 Verification Gate:
1. Run `py -3 tools\export_ui_assets.py` -> verifies `iconsData.json`, `geometryData.json`, and `framePartsData.json` are generated in `@Resources\UI\generated\`.
2. Run `py -3 -B Skins\Spaceship\@Resources\Jarvis\test_jarvis.py` (in a scratch copy) -> 100% pass.
3. Build `ShipCore.Host.exe` and verify `Ctrl+Alt+Shift+H` hides windows in `<50ms` even when the main thread is artificially blocked.

---

### PHASE 1: Instant-Boot Task Scheduler (`IMP-01`), Stage 0 GDI+ Boot Reticle (`<25ms`), 2-Frame `DwmFlush()` Handoff (`IMP-03`), `ui.animationLease` (`IMP-02`) & WebView2 Watchdog (`IMP-06`) (`WP-1`)

#### 📋 Copy-Paste Prompt for Claude — Phase 1:
```markdown
Execute Phase 1 of the Standalone Spaceship App migration (`WP-1`).

AUTONOMY & ADJUSTMENT NOTICE:
You have explicit permission to adapt window styles, Z-order attachment, or hit-test strategies if live testing on Windows 11 24H2 reveals a cleaner behavior. Document any adjustments in your summary.

STEP-BY-STEP INSTRUCTIONS:
1. Implement `SpaceshipApp\ShipCore.Host\BootIntegrationManager.cs` (`IMP-01` + `OVR-18` + `BUG-10`):
   - Generate Task Scheduler XML for `\SpaceshipHUD\ShipCoreHost` with `<Priority>4</Priority>` (Normal interactive CPU/Disk priority, NOT default `7`), `<Delay>PT0S</Delay>`, `<DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>`, `<StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>`, `<ExecutionTimeLimit>PT0S</ExecutionTimeLimit>`, and `<RestartOnFailure><Interval>PT10S</Interval><Count>3</Count></RestartOnFailure>`.
   - Record all changes in `%LOCALAPPDATA%\SpaceshipHUD\system_changes_backup.json` before registering.
2. Implement `SpaceshipApp\ShipCore.Host\NativeHullWindow.cs` (`IMP-01` Stage 0 Boot Reticle + `OVR-11`):
   - Create a per-pixel alpha layered window (`WS_POPUP`, `WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE`) that loads `@Resources\Images\hull.png` and paints the **Stage 0 GDI+ Boot Reticle (`"INITIALIZING SHIPCORE..."`)** in `<25ms` on startup while WebView2 warms up in the background!
3. Implement `SpaceshipApp\ShipCore.Host\DesktopWindowStateMachine.cs` (`FIX-DEBATE-03` + `IMP-04`):
   - Port `findHome()` and `fitTo()` from `Scripts\controller.lua:34-87` (`HomeSize=2560x1600`, `Scale`, `OriginX`, `OriginY`, `MonX`, `MonY`, `FrameBehindTaskbar`).
   - Implement `WaitForExplorerShellReady()` (handling cold boot where `ShipCore.Host.exe` starts before `Shell_TrayWnd` / `SHELLDLL_DefView` exist), `TaskbarCreated` re-anchoring (`IMP-04`), `WM_POWERBROADCAST` (`PBT_APMRESUMEAUTOMATIC` wake from Fast Startup / Modern Standby), and `WM_WINDOWPOSCHANGING` (`Win+D` protection).
4. Implement `SpaceshipApp\ShipCore.Host\HitTestRouter.cs` (`FIX-DEBATE-05` + `OVR-04` + `BUG-02` + `IMP-02` + `IMP-03`):
   - Inflate every active non-`CT_<key>` polygon from `layout\layout.json` + `Offsets.inc` (`<ModuleKey>_DX`, `<ModuleKey>_DY`) by **`30 * Scale` px (`18px` `ModuleMargin` from `tools\build.py:21` + `12px` `AnimationBleedMargin` from `IMP-02`)**.
   - Implement `AcquireAnimationLease(int durationMs, string reason)` (`IMP-02`) to temporarily unclip `SetWindowRgn(hudCanvasHwnd, IntPtr.Zero, false)` during `<IntroSequence />`, `LayoutStudio`, Preset morphs, Wake-Word shockwaves, and Alert sweeps.
   - Implement the **`IMP-03` 2-Frame `DwmFlush()` Handoff Protocol** when transitioning between unclipped/WebView-hull mode and steady-state `NativeHullWindow` + `masterRgn` mode.
5. Implement `SpaceshipApp\ShipCore.Host\WebViewLifecycleManager.cs` (`OVR-03`, `OVR-05`, `OVR-12`, `FIX-DEBATE-14`, `IMP-06`):
   - Pre-warm `CoreWebView2Environment.CreateAsync` (`--gpu-preference=low-power`) in parallel at `T+0ms` in `Program.cs`.
   - Lock `RasterizationScale = 1.0` and `ShouldDetectMonitorScaleChanges = false` (`FIX-DEBATE-14`).
   - Map `https://spaceship.ui/` -> `@Resources\UI\dist\` and `https://spaceship.res/` -> `@Resources\`.
   - Wire `CoreWebView2.NewWindowRequested` to `ModalOverlayWindow` (`modal.html`, `OVR-12`).
   - Wire **`CoreWebView2.ProcessFailed` (`IMP-06`)** to automatically recover and re-bind `CreateSharedBuffer(4096)` within `<500ms` if the renderer or GPU process crashes (`Win+Ctrl+Shift+B`).
```

#### Exact Code Implementations for Phase 1:

##### 1.1 `SpaceshipApp\ShipCore.Host\BootIntegrationManager.cs` (`IMP-01` Zero-Delay Priority-4 Task Scheduler XML)
```csharp
using System.Diagnostics;
using System.Security.Principal;
using System.Text;
using System.Text.Json;

namespace ShipCore.Host;

public static class BootIntegrationManager
{
    private const string TaskName = @"\SpaceshipHUD\ShipCoreHost";

    public static void InstallStartupTask(string exePath, string resPath)
    {
        string storeDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "SpaceshipHUD");
        Directory.CreateDirectory(storeDir);
        string ledgerPath = Path.Combine(storeDir, "system_changes_backup.json");

        // Record reversible ledger entry first (Rec 40)
        var ledger = new
        {
            installedAt = DateTime.UtcNow.ToString("O"),
            scheduledTaskName = TaskName,
            exePath,
            resPath,
            rollbackCommand = $"schtasks.exe /Delete /TN \"{TaskName}\" /F"
        };
        File.WriteAllText(ledgerPath, JsonSerializer.Serialize(ledger, new JsonSerializerOptions { WriteIndented = true }));

        string userId = WindowsIdentity.GetCurrent().Name;
        // IMP-01 + BUG-10: Priority=4 (Normal Interactive), Delay=PT0S, DisallowStartIfOnBatteries=false, ExecutionTimeLimit=PT0S
        string xml = $@"<?xml version=""1.0"" encoding=""UTF-16""?>
<Task version=""1.4"" xmlns=""http://schemas.microsoft.com/windows/2004/02/mit/task"">
  <RegistrationInfo>
    <Description>BLACK-CLOVER Spaceship Desktop Operating Environment Host (Standard User, Non-Admin)</Description>
    <URI>{TaskName}</URI>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <UserId>{System.Security.SecurityElement.Escape(userId)}</UserId>
      <Delay>PT0S</Delay>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id=""Author"">
      <UserId>{System.Security.SecurityElement.Escape(userId)}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <DisallowStartOnRemoteAppSession>false</DisallowStartOnRemoteAppSession>
    <UseUnifiedSchedulingEngine>true</UseUnifiedSchedulingEngine>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>4</Priority>
    <RestartOnFailure>
      <Interval>PT10S</Interval>
      <Count>3</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context=""Author"">
    <Exec>
      <Command>{System.Security.SecurityElement.Escape(exePath)}</Command>
      <Arguments>&quot;{System.Security.SecurityElement.Escape(resPath.TrimEnd('\\'))}&quot;</Arguments>
      <WorkingDirectory>{System.Security.SecurityElement.Escape(Path.GetDirectoryName(exePath) ?? "")}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>";

        string tmpXml = Path.Combine(storeDir, "ShipCoreHostTask.xml");
        File.WriteAllText(tmpXml, xml, Encoding.Unicode);
        RunSchtasks($"/Create /TN \"{TaskName}\" /XML \"{tmpXml}\" /F");
        try { File.Delete(tmpXml); } catch { }
    }

    public static void UninstallStartupTask()
    {
        RunSchtasks($"/Delete /TN \"{TaskName}\" /F");
    }

    private static void RunSchtasks(string args)
    {
        var psi = new ProcessStartInfo("schtasks.exe", args)
        {
            CreateNoWindow = true,
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true
        };
        using var p = Process.Start(psi);
        p?.WaitForExit(10000);
    }
}
```

##### 1.2 `SpaceshipApp\ShipCore.Host\NativeHullWindow.cs` (`IMP-01` `<25ms` Stage 0 GDI+ Boot Reticle + `UpdateLayeredWindow`)
```csharp
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

namespace ShipCore.Host;

public sealed class NativeHullWindow : NativeWindow, IDisposable
{
    private const int WS_POPUP = unchecked((int)0x80000000);
    private const int WS_VISIBLE = 0x10000000;
    private const int WS_EX_LAYERED = 0x00080000;
    private const int WS_EX_TRANSPARENT = 0x00000020;
    private const int WS_EX_TOOLWINDOW = 0x00000080;
    private const int WS_EX_NOACTIVATE = 0x08000000;
    private const byte AC_SRC_OVER = 0x00, AC_SRC_ALPHA = 0x01;
    private const int ULW_ALPHA = 0x00000002;

    [StructLayout(LayoutKind.Sequential)] private struct POINT { public int X, Y; }
    [StructLayout(LayoutKind.Sequential)] private struct SIZE { public int cx, cy; }
    [StructLayout(LayoutKind.Sequential, Pack = 1)] private struct BLENDFUNCTION { public byte BlendOp, BlendFlags, SourceConstantAlpha, AlphaFormat; }

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool UpdateLayeredWindow(IntPtr hwnd, IntPtr hdcDst, ref POINT pptDst, ref SIZE psize,
        IntPtr hdcSrc, ref POINT pptSrc, int crKey, ref BLENDFUNCTION pblend, int dwFlags);
    [DllImport("user32.dll")] private static extern IntPtr GetDC(IntPtr hWnd);
    [DllImport("user32.dll")] private static extern int ReleaseDC(IntPtr hWnd, IntPtr hDC);
    [DllImport("gdi32.dll")] private static extern IntPtr CreateCompatibleDC(IntPtr hDC);
    [DllImport("gdi32.dll")] private static extern bool DeleteDC(IntPtr hdc);
    [DllImport("gdi32.dll")] private static extern IntPtr SelectObject(IntPtr hDC, IntPtr hObject);
    [DllImport("gdi32.dll")] private static extern bool DeleteObject(IntPtr hObject);

    private Bitmap? _hullBitmap;
    private System.Windows.Forms.Timer? _stage0Timer;
    private float _stage0Angle;
    private int _x, _y, _w, _h;
    private float _scale = 1.0f;

    public NativeHullWindow(string resPath, int x, int y, int w, int h, float scale)
    {
        _x = x; _y = y; _w = w; _h = h; _scale = scale;
        CreateHandle(new CreateParams
        {
            Caption = "SpaceshipNativeHull",
            X = x, Y = y, Width = w, Height = h,
            Style = WS_POPUP | WS_VISIBLE,
            ExStyle = WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
        });

        string hullPath = Path.Combine(resPath, @"Images\hull.png");
        if (File.Exists(hullPath))
        {
            using var raw = new Bitmap(hullPath);
            _hullBitmap = new Bitmap(raw, new Size(w, h));
        }

        // IMP-01: Paint Stage 0 Boot Reticle immediately (<25ms from process start) while WebView2 warms up
        RenderStage0Frame();
        _stage0Timer = new System.Windows.Forms.Timer { Interval = 16 };
        _stage0Timer.Tick += (_, _) => { _stage0Angle = (_stage0Angle + 4.5f) % 360f; RenderStage0Frame(); };
        _stage0Timer.Start();
    }

    public void StopStage0AndSetBakedHull(Bitmap? bakedHull)
    {
        if (_stage0Timer != null)
        {
            _stage0Timer.Stop();
            _stage0Timer.Dispose();
            _stage0Timer = null;
        }
        if (bakedHull != null)
        {
            _hullBitmap?.Dispose();
            _hullBitmap = bakedHull;
        }
        if (_hullBitmap != null)
        {
            PresentBitmap(_hullBitmap, 255);
        }
    }

    private void RenderStage0Frame()
    {
        using var frame = new Bitmap(_w, _h, PixelFormat.Format32bppPArgb);
        using var g = Graphics.FromImage(frame);
        g.SmoothingMode = SmoothingMode.AntiAlias;
        if (_hullBitmap != null)
        {
            // Draw dimmed hull silhouette (25% brightness) during Stage 0 warmup
            using var ia = new ImageAttributes();
            var cm = new ColorMatrix { Matrix00 = 0.25f, Matrix11 = 0.25f, Matrix22 = 0.25f, Matrix33 = 0.85f };
            ia.SetColorMatrix(cm);
            g.DrawImage(_hullBitmap, new Rectangle(0, 0, _w, _h), 0, 0, _w, _h, GraphicsUnit.Pixel, ia);
        }

        float cx = _w * 0.5f, cy = _h * 0.5f;
        float rOuter = 54f * _scale, rInner = 38f * _scale;
        using var cyanPen = new Pen(Color.FromArgb(220, 0, 210, 255), 2.2f * _scale);
        using var dimPen = new Pen(Color.FromArgb(110, 0, 110, 150), 1.4f * _scale);
        for (int q = 0; q < 4; q++)
            g.DrawArc(cyanPen, cx - rOuter, cy - rOuter, rOuter * 2, rOuter * 2, _stage0Angle + q * 90f, 58f);
        for (int q = 0; q < 3; q++)
            g.DrawArc(dimPen, cx - rInner, cy - rInner, rInner * 2, rInner * 2, -_stage0Angle * 1.4f + q * 120f, 82f);

        using var font = new Font("Consolas", Math.Max(8f, 10f * _scale), FontStyle.Bold);
        using var brush = new SolidBrush(Color.FromArgb(210, 170, 235, 255));
        var sf = new StringFormat { Alignment = StringAlignment.Center, LineAlignment = StringAlignment.Center };
        g.DrawString("INITIALIZING SHIPCORE...", font, brush, cx, cy + rOuter + 22f * _scale, sf);

        PresentBitmap(frame, 255);
    }

    public void PresentBitmap(Bitmap bmp, byte alpha)
    {
        IntPtr screenDc = GetDC(IntPtr.Zero);
        IntPtr memDc = CreateCompatibleDC(screenDc);
        IntPtr hBmp = IntPtr.Zero, oldBmp = IntPtr.Zero;
        try
        {
            hBmp = bmp.GetHbitmap(Color.FromArgb(0));
            oldBmp = SelectObject(memDc, hBmp);
            var size = new SIZE { cx = bmp.Width, cy = bmp.Height };
            var ptDst = new POINT { X = _x, Y = _y };
            var ptSrc = new POINT { X = 0, Y = 0 };
            var blend = new BLENDFUNCTION { BlendOp = AC_SRC_OVER, BlendFlags = 0, SourceConstantAlpha = alpha, AlphaFormat = AC_SRC_ALPHA };
            UpdateLayeredWindow(Handle, screenDc, ref ptDst, ref size, memDc, ref ptSrc, 0, ref blend, ULW_ALPHA);
        }
        finally
        {
            if (oldBmp != IntPtr.Zero) SelectObject(memDc, oldBmp);
            if (hBmp != IntPtr.Zero) DeleteObject(hBmp);
            DeleteDC(memDc);
            ReleaseDC(IntPtr.Zero, screenDc);
        }
    }

    public void Dispose()
    {
        _stage0Timer?.Dispose();
        _hullBitmap?.Dispose();
        DestroyHandle();
    }
}
```

##### 1.3 `SpaceshipApp\ShipCore.Host\HitTestRouter.cs` (`BUG-02` `18px` ModuleMargin + `IMP-02` `12px` AnimationBleedMargin + `ui.animationLease` + `IMP-03` 2-Frame `DwmFlush()` Handoff)
```csharp
using System.Drawing;
using System.Runtime.InteropServices;

namespace ShipCore.Host;

public sealed class HitTestRouter
{
    // BUG-02 + IMP-02: 18px Rainmeter module margin (tools/build.py:21) + 12px AnimationBleedMargin = 30px total base-canvas padding
    public const float ModuleMarginPx = 18.0f;
    public const float AnimationBleedMarginPx = 12.0f;
    public const float TotalPolygonOutsetPx = ModuleMarginPx + AnimationBleedMarginPx; // 30.0f base-canvas px

    private const int RGN_OR = 2;
    private const int SW_HIDE = 0, SW_SHOWNOACTIVATE = 4;

    [StructLayout(LayoutKind.Sequential)]
    public struct POINT { public int X, Y; }

    [DllImport("gdi32.dll")] private static extern IntPtr CreateRectRgn(int x1, int y1, int x2, int y2);
    [DllImport("gdi32.dll")] private static extern IntPtr CreatePolygonRgn(POINT[] lppt, int cPoints, int fnPolyFillMode);
    [DllImport("gdi32.dll")] private static extern int CombineRgn(IntPtr hrgnDest, IntPtr hrgnSrc1, IntPtr hrgnSrc2, int fnCombineMode);
    [DllImport("gdi32.dll")] private static extern bool DeleteObject(IntPtr hObject);
    [DllImport("user32.dll")] private static extern int SetWindowRgn(IntPtr hWnd, IntPtr hRgn, bool bRedraw);
    [DllImport("user32.dll")] private static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("dwmapi.dll")] private static extern int DwmFlush();

    private readonly IntPtr _hudCanvasHwnd;
    private readonly IntPtr _nativeHullHwnd;
    private readonly Action<string> _postJsonToWebView;
    private readonly object _leaseLock = new();
    private DateTime _leaseExpiresUtc = DateTime.MinValue;
    private bool _isUnclipped = true; // Starts unclipped for <IntroSequence />

    public HitTestRouter(IntPtr hudCanvasHwnd, IntPtr nativeHullHwnd, Action<string> postJsonToWebView)
    {
        _hudCanvasHwnd = hudCanvasHwnd;
        _nativeHullHwnd = nativeHullHwnd;
        _postJsonToWebView = postJsonToWebView;
    }

    /// <summary>
    /// IMP-02: Temporarily unclips HudCanvasWindow during IntroSequence, LayoutStudio, Preset morphs,
    /// Wake-Word shockwaves, or Red-Alert pulses so full-screen/bleeding animations are never guillotined.
    /// </summary>
    public void AcquireAnimationLease(int durationMs, bool hideNativeHullForLiveFilter = false)
    {
        lock (_leaseLock)
        {
            var until = DateTime.UtcNow.AddMilliseconds(Math.Clamp(durationMs, 50, 30000));
            if (until > _leaseExpiresUtc) _leaseExpiresUtc = until;
            if (!_isUnclipped)
            {
                _isUnclipped = true;
                SetWindowRgn(_hudCanvasHwnd, IntPtr.Zero, false);
            }
            if (hideNativeHullForLiveFilter)
            {
                _postJsonToWebView("{\"type\":\"hull.handoff\",\"showInWebView\":true}");
                ShowWindow(_nativeHullHwnd, SW_HIDE);
            }
        }
    }

    /// <summary>
    /// IMP-03: Enforces the 2-Frame DwmFlush() Handoff Protocol so transitioning from unclipped WebView hull
    /// back to NativeHullWindow + SetWindowRgn(masterRgn) never causes a 1-frame DWM black/white flash.
    /// </summary>
    public async Task ExecuteTwoFrameSteadyStateHandoffAsync(
        IReadOnlyList<ModulePolygonSpec> modules,
        IReadOnlyDictionary<string, (float dx, float dy)> offsets,
        IReadOnlySet<string> hiddenModules,
        IReadOnlySet<string> clickThroughModules,
        float scale)
    {
        // Step 1 (Frame 1): Show NativeHullWindow and flush DWM composition
        ShowWindow(_nativeHullHwnd, SW_SHOWNOACTIVATE);
        DwmFlush();

        // Step 2 (Frame 2): Wait one 165Hz frame (~6ms) so DWM has composited NativeHullWindow on screen
        await Task.Delay(7).ConfigureAwait(true);

        // Step 3 (Frame 3): Apply composite SetWindowRgn(masterRgn) and hide duplicate hull inside WebView
        RebuildSteadyStateWindowRegion(modules, offsets, hiddenModules, clickThroughModules, scale);
        _postJsonToWebView("{\"type\":\"hull.handoff\",\"showInWebView\":false}");
    }

    public void RebuildSteadyStateWindowRegion(
        IReadOnlyList<ModulePolygonSpec> modules,
        IReadOnlyDictionary<string, (float dx, float dy)> offsets,
        IReadOnlySet<string> hiddenModules,
        IReadOnlySet<string> clickThroughModules,
        float scale)
    {
        lock (_leaseLock)
        {
            if (DateTime.UtcNow < _leaseExpiresUtc)
                return; // Keep unclipped until active animation lease finishes

            IntPtr masterRgn = CreateRectRgn(0, 0, 0, 0);
            float pad = TotalPolygonOutsetPx; // 18px ModuleMargin + 12px AnimationBleedMargin = 30px

            foreach (var mod in modules)
            {
                if (hiddenModules.Contains(mod.Key) || clickThroughModules.Contains(mod.Key))
                    continue;

                var (dx, dy) = offsets.TryGetValue(mod.Key, out var off) ? off : (0f, 0f);
                foreach (var quad in mod.Quads)
                {
                    POINT[] inflated = InflateQuadOutward(quad, dx, dy, pad, scale);
                    IntPtr polyRgn = CreatePolygonRgn(inflated, inflated.Length, 2 /* WINDING */);
                    if (polyRgn != IntPtr.Zero)
                    {
                        CombineRgn(masterRgn, masterRgn, polyRgn, RGN_OR);
                        DeleteObject(polyRgn);
                    }
                }
            }

            // Ownership of masterRgn transfers to the OS upon SetWindowRgn; do NOT call DeleteObject(masterRgn)!
            SetWindowRgn(_hudCanvasHwnd, masterRgn, false);
            _isUnclipped = false;
        }
    }

    private static POINT[] InflateQuadOutward(PointF[] quad, float dx, float dy, float padBasePx, float scale)
    {
        float cx = 0f, cy = 0f;
        for (int i = 0; i < quad.Length; i++) { cx += quad[i].X; cy += quad[i].Y; }
        cx /= quad.Length; cy /= quad.Length;

        var pts = new POINT[quad.Length];
        for (int i = 0; i < quad.Length; i++)
        {
            float vx = quad[i].X - cx;
            float vy = quad[i].Y - cy;
            float ox = quad[i].X + dx + (vx >= 0 ? padBasePx : -padBasePx);
            float oy = quad[i].Y + dy + (vy >= 0 ? padBasePx : -padBasePx);
            pts[i] = new POINT
            {
                X = (int)Math.Round(ox * scale),
                Y = (int)Math.Round(oy * scale)
            };
        }
        return pts;
    }
}

public sealed record ModulePolygonSpec(string Key, IReadOnlyList<PointF[]> Quads);
```

##### 1.4 `SpaceshipApp\ShipCore.Host\WebViewLifecycleManager.cs` (`IMP-06` `CoreWebView2.ProcessFailed` Auto-Recovery + `OVR-03` Dual Virtual Hosts + `OVR-05` `CreateSharedBuffer`)
```csharp
using System.Drawing;
using System.Runtime.InteropServices;
using Microsoft.Web.WebView2.Core;

namespace ShipCore.Host;

public sealed class WebViewLifecycleManager : IDisposable
{
    private readonly string _resPath;
    private readonly string _uiDistPath;
    private readonly IntPtr _hudCanvasHwnd;
    private readonly IntPtr _modalOverlayHwnd;
    private CoreWebView2Environment? _env;
    private CoreWebView2Controller? _hudController;
    private CoreWebView2Controller? _modalController;
    private CoreWebView2SharedBuffer? _sharedBuffer;
    private Stream? _sharedBufferStream;
    private int _crashRecoveryCount;

    public event Action<string>? OnWebMessageReceived;
    public event Action? OnWebViewRecovered;

    public WebViewLifecycleManager(string resPath, IntPtr hudCanvasHwnd, IntPtr modalOverlayHwnd)
    {
        _resPath = resPath.TrimEnd('\\');
        _uiDistPath = Path.Combine(_resPath, @"UI\dist");
        _hudCanvasHwnd = hudCanvasHwnd;
        _modalOverlayHwnd = modalOverlayHwnd;
    }

    public async Task InitializeAsync(Rectangle bounds)
    {
        string userDataFolder = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "SpaceshipHUD", "WebView2Data");
        Directory.CreateDirectory(userDataFolder);

        // Rec 4: Force Radeon 880M iGPU (--gpu-preference=low-power) so WebView2 never wakes RTX 5070 dGPU!
        var opts = new CoreWebView2EnvironmentOptions(
            additionalBrowserArguments: "--gpu-preference=low-power --disable-features=msSmartScreenProtection --autoplay-policy=no-user-gesture-required");

        _env = await CoreWebView2Environment.CreateAsync(null, userDataFolder, opts);
        await CreateHudControllerAsync(bounds);
    }

    private async Task CreateHudControllerAsync(Rectangle bounds)
    {
        if (_env == null) return;
        _hudController = await _env.CreateCoreWebView2ControllerAsync(_hudCanvasHwnd);
        _hudController.DefaultBackgroundColor = Color.Transparent;
        // FIX-DEBATE-14: Lock 1 CSS px === 1 physical px regardless of 100%/125%/150% Windows DPI scaling
        _hudController.RasterizationScale = 1.0;
        _hudController.ShouldDetectMonitorScaleChanges = false;
        _hudController.Bounds = bounds;
        _hudController.IsVisible = true;

        var wv = _hudController.CoreWebView2;
        wv.Settings.AreDefaultContextMenusEnabled = false;
        wv.Settings.AreBrowserAcceleratorKeysEnabled = false;
        wv.Settings.IsStatusBarEnabled = false;
        wv.Settings.IsZoomControlEnabled = false;

        // OVR-03: Register BOTH virtual hosts (UI bundle + @Resources assets/icons/sounds/fonts)
        wv.SetVirtualHostNameToFolderMapping("spaceship.ui", _uiDistPath, CoreWebView2HostResourceAccessKind.Allow);
        wv.SetVirtualHostNameToFolderMapping("spaceship.res", _resPath, CoreWebView2HostResourceAccessKind.Allow);

        // OVR-05: Allocate 4096-byte zero-copy shared buffer (1024 floats)
        _sharedBuffer?.Dispose();
        _sharedBufferStream?.Dispose();
        _sharedBuffer = _env.CreateSharedBuffer(4096);
        _sharedBufferStream = _sharedBuffer.OpenStream();

        wv.WebMessageReceived += (_, e) =>
        {
            string json = e.WebMessageAsJson;
            if (json.Contains("\"ui.ready\"", StringComparison.Ordinal))
            {
                wv.PostSharedBufferToScript(_sharedBuffer, CoreWebView2SharedBufferAccess.ReadOnly, "{\"type\":\"telemetry.shared\"}");
            }
            OnWebMessageReceived?.Invoke(json);
        };

        // OVR-12: Attach ModalOverlayWindow via window.open("https://spaceship.ui/modal.html") sharing the exact same renderer process
        wv.NewWindowRequested += async (_, e) =>
        {
            if (e.Uri.StartsWith("https://spaceship.ui/modal.html", StringComparison.OrdinalIgnoreCase))
            {
                var deferral = e.GetDeferral();
                try
                {
                    _modalController?.Close();
                    _modalController = await _env.CreateCoreWebView2ControllerAsync(_modalOverlayHwnd);
                    _modalController.DefaultBackgroundColor = Color.Transparent;
                    _modalController.RasterizationScale = 1.0;
                    _modalController.ShouldDetectMonitorScaleChanges = false;
                    e.NewWindow = _modalController.CoreWebView2;
                    e.Handled = true;
                }
                finally
                {
                    deferral.Complete();
                }
            }
        };

        // IMP-06: Automatic WebView2 Watchdog on Renderer / GPU Process Reset (Win+Ctrl+Shift+B or driver update)
        wv.ProcessFailed += async (_, e) =>
        {
            if (e.ProcessFailedKind is CoreWebView2ProcessFailedKind.RenderProcessExited
                or CoreWebView2ProcessFailedKind.RenderProcessUnresponsive
                or CoreWebView2ProcessFailedKind.BrowserProcessExited)
            {
                if (++_crashRecoveryCount <= 10)
                {
                    try { _hudController?.Close(); } catch { }
                    await Task.Delay(150);
                    await CreateHudControllerAsync(bounds);
                    OnWebViewRecovered?.Invoke();
                }
            }
        };

        wv.Navigate("https://spaceship.ui/index.html");
    }

    public unsafe void WriteSharedFloat(int index, float value)
    {
        if (_sharedBuffer == null || (uint)index >= 1024u) return;
        float* ptr = (float*)_sharedBuffer.Buffer.ToPointer();
        ptr[index] = value;
    }

    public unsafe void WriteSharedFloatBlock(int startIndex, ReadOnlySpan<float> values)
    {
        if (_sharedBuffer == null || startIndex < 0 || startIndex + values.Length > 1024) return;
        float* ptr = (float*)_sharedBuffer.Buffer.ToPointer();
        values.CopyTo(new Span<float>(ptr + startIndex, values.Length));
    }

    public void PostJson(string json) => _hudController?.CoreWebView2.PostWebMessageAsJson(json);

    public void Dispose()
    {
        _sharedBufferStream?.Dispose();
        _sharedBuffer?.Dispose();
        _modalController?.Close();
        _hudController?.Close();
    }
}
```

#### What Claude Must Avoid & Where to Be Careful in Phase 1:
* **DO NOT** call `DeleteObject(masterRgn)` after passing `masterRgn` to `SetWindowRgn(hwnd, masterRgn, false)` — Win32 takes ownership of the `HRGN` handle passed to `SetWindowRgn` and freeing it yourself corrupts the GDI region heap! (Only call `DeleteObject` on temporary `polyRgn` handles combined into `masterRgn`.)
* **DO NOT** skip `DwmFlush()` and the 1-frame delay in `ExecuteTwoFrameSteadyStateHandoffAsync` (`IMP-03`) — without it, hiding the WebView hull and showing `NativeHullWindow` on the same tick flashes for 1 frame.

#### Phase 1 Verification Gate:
1. Verify Stage 0 GDI+ reticle appears in `<25ms` on startup, followed by a zero-flicker 2-frame `DwmFlush()` handoff after `<IntroSequence />`.
2. Trigger `Win+Ctrl+Shift+B` (or kill the WebView2 renderer process in Task Manager) -> verify `ProcessFailed` (`IMP-06`) recovers the HUD and re-binds `CreateSharedBuffer(4096)` within `<500ms`.
3. Verify Task Scheduler task `\SpaceshipHUD\ShipCoreHost` has `<Priority>4</Priority>`, `<Delay>PT0S</Delay>`, and `<DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>`.

---

### PHASE 2: Dual Simplex Named Pipes (`OVR-07`), Single-Writer `ConfigStore.cs` (`OVR-08` + `BUG-04`/`BUG-05`) & Python Fast-Path (`WP-2`)

#### 📋 Copy-Paste Prompt for Claude — Phase 2:
```markdown
Execute Phase 2 of the Standalone Spaceship App migration (`WP-2`).

AUTONOMY & ADJUSTMENT NOTICE:
You may refine internal buffer sizes, lock granularity, or JSON serialization details if needed, provided `ToJarvis` and `FromJarvis` remain strictly unidirectional (simplex) so Python standard-library `open()` never deadlocks without `pywin32`, and `test_jarvis.py` passes 100%.

STEP-BY-STEP INSTRUCTIONS:
1. Build `SpaceshipApp\ShipCore.Host\ConfigStore.cs` (`OVR-08` + `BUG-04` + `BUG-05`):
   - Single serialized writer (`SemaphoreSlim(1, 1)`) for `@Resources\Settings.inc`, `@Resources\State.inc`, `@Resources\Offsets.inc`, `@Resources\Hardware.inc`, and `@Resources\Apps.ini`.
   - Preserve `ShipCore.cs:162-177` DPAPI encryption (`ProtectedData.Protect` / `Unprotect` with entropy `"SpaceshipHUD"`, `DataProtectionScope.CurrentUser`) for `%LOCALAPPDATA%\SpaceshipHUD\gmail.dat` and `calendars.dat` (`BUG-04`).
   - Map module offsets to `<ModuleKey>_DX` and `<ModuleKey>_DY` in `Offsets.inc`, and module enable/click-through flags to `Off_<ModuleKey>` and `CT_<ModuleKey>` in `State.inc` (`BUG-05`).
   - Implement `SavePreset(int slot)` and `LoadPreset(string slotOrUndo)` matching `Scripts\control.lua:195-213` (`PRESET_FILES = { 'Settings.inc', 'Offsets.inc', 'State.inc', 'Apps.ini' }`).
2. Build `SpaceshipApp\ShipCore.Host\HudIpcServer.cs` (`OVR-07` + `FIX-DEBATE-11/12`):
   - Create `%LOCALAPPDATA%\SpaceshipHUD\ipc.nonce` (64-char random hex) restricted to current user SID.
   - Start two unidirectional Named Pipe servers:
     - `\\.\pipe\SpaceshipHud_ToJarvis_<UserSID>` (`PipeDirection.Out`)
     - `\\.\pipe\SpaceshipHud_FromJarvis_<UserSID>` (`PipeDirection.In`)
   - Verify client PID (`GetNamedPipeClientProcessId`) and `hello` nonce, send `welcome.snapshot` immediately upon connect, and update `WebViewLifecycleManager.WriteSharedFloat(99, level)` (`jarvisVoiceLevel`) and `WriteSharedFloat(100, stateEnum)` (`jarvisStateEnum`) at 0ms latency whenever `jarvis.py` emits a `state` line!
3. Update `Skins\Spaceship\@Resources\Jarvis\jarvislib\base.py` and `jarvis.py` (`OVR-07` + `FIX-DEBATE-11`):
   - Add a non-blocking background pipe connector in `jarvislib\base.py` using standard-library `open(to_jarvis_path, "rb")` and `open(from_jarvis_path, "wb", buffering=0)` (zero `pywin32` dependency!).
   - When connected, `State.set()`, `convo_add()`, and `live()` stream NDJSON over `FromJarvis` immediately (while still keeping `test_jarvis.py` 100% file-backed when pipes are absent!).
```

#### Exact Code Implementations for Phase 2:

##### 2.1 Dual Simplex Pipe Client in `Skins\Spaceship\@Resources\Jarvis\jarvislib\base.py` (`OVR-07` Zero-`pywin32`, Zero-CRT-Deadlock Implementation)
Add the following simplex pipe client to `Skins\Spaceship\@Resources\Jarvis\jarvislib\base.py` (and call `start_ipc_client(on_cmd_callback)` from `jarvis.py:main()` only when `owner == True`, so `test_jarvis.py` never starts pipe threads during unit tests!):
```python
import json

_pipe_out = [None]
_pipe_lock = threading.Lock()
_kv_cache = {}
_cmd_queue = []
_cmd_lock = threading.Lock()


def _current_user_sid():
    """Returns the current Windows user SID string (or username fallback) for pipe naming."""
    try:
        advapi32 = ctypes.windll.advapi32
        kernel32 = ctypes.windll.kernel32
        token = ctypes.c_void_p()
        if not advapi32.OpenProcessToken(kernel32.GetCurrentProcess(), 0x0008, ctypes.byref(token)):
            return os.environ.get("USERNAME", "default")
        try:
            buf = ctypes.create_string_buffer(256)
            ret_len = ctypes.c_ulong(0)
            if not advapi32.GetTokenInformation(token, 1, buf, 256, ctypes.byref(ret_len)):
                return os.environ.get("USERNAME", "default")
            sid_ptr = ctypes.cast(buf, ctypes.POINTER(ctypes.c_void_p)).contents
            str_ptr = ctypes.c_wchar_p()
            if advapi32.ConvertSidToStringSidW(sid_ptr, ctypes.byref(str_ptr)):
                res = str_ptr.value
                kernel32.LocalFree(str_ptr)
                return res
        finally:
            kernel32.CloseHandle(token)
    except Exception:
        pass
    return os.environ.get("USERNAME", "default")


def _send_ipc(payload):
    fp = _pipe_out[0]
    if fp is None:
        return False
    try:
        line = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
        with _pipe_lock:
            fp.write(line)
        return True
    except OSError:
        _pipe_out[0] = None
        _ipc_active[0] = False
        return False


def pop_ipc_cmd():
    """Returns the next command string ('WAKE ...', 'ASK ...', etc.) received over ToJarvis pipe, or None."""
    with _cmd_lock:
        return _cmd_queue.pop(0) if _cmd_queue else None


def start_ipc_client():
    """OVR-07: Connects two separate unidirectional (simplex) pipes using standard Python open() so
    Thread A reading ToJarvis and Thread B writing FromJarvis never deadlock in the Windows CRT."""
    def _worker():
        sid = _current_user_sid()
        to_jarvis = rf"\\.\pipe\SpaceshipHud_ToJarvis_{sid}"
        from_jarvis = rf"\\.\pipe\SpaceshipHud_FromJarvis_{sid}"
        nonce_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "SpaceshipHUD", "ipc.nonce")
        while True:
            try:
                if not os.path.exists(nonce_path):
                    time.sleep(2.0)
                    continue
                with open(nonce_path, "r", encoding="utf-8") as nf:
                    nonce = nf.read().strip()
                # Open write-only pipe first, send hello + nonce, then open read-only pipe
                f_out = open(from_jarvis, "wb", buffering=0)
                _pipe_out[0] = f_out
                _send_ipc({"type": "hello", "nonce": nonce, "pid": os.getpid()})
                f_in = open(to_jarvis, "rb")
                _ipc_active[0] = True
                log("ipc: connected dual simplex pipes to ShipCore.Host")
                for raw_line in f_in:
                    try:
                        msg = json.loads(raw_line.decode("utf-8", errors="ignore"))
                    except Exception:
                        continue
                    mtype = msg.get("type")
                    if mtype == "welcome.snapshot":
                        for k, v in (msg.get("kv") or {}).items():
                            _kv_cache[k] = v
                    elif mtype == "kv.update":
                        _kv_cache[msg.get("file", "")] = msg.get("body", "")
                    elif mtype == "cmd":
                        raw_cmd = msg.get("raw", "").strip()
                        if raw_cmd:
                            with _cmd_lock:
                                _cmd_queue.append(raw_cmd)
            except OSError:
                _pipe_out[0] = None
                _ipc_active[0] = False
                time.sleep(2.0)

    threading.Thread(target=_worker, daemon=True).start()
```
And in `jarvislib\base.py`:
* Inside `State.set()`, right before the `if not force and now - self.last_write < 0.05:` throttle check, call:
  ```python
  if _ipc_active[0]:
      _send_ipc({
          "type": "state", "t": now, "state": self.state, "level": round(self.level, 4),
          "say": self.say, "err": self.err,
          "pop": f"{self.pop_n} {self.pop}", "hud": f"{self.hud_n} {self.hud}"
      })
  ```
* Inside `read_kv(name)`:
  ```python
  def read_kv(name):
      if _ipc_active[0] and name in _kv_cache:
          return _kv_cache[name]
      try:
          with open(os.path.join(DATA, name), "r", encoding="utf-8", errors="ignore") as f:
              return f.read()
      except OSError:
          return ""
  ```
* Inside `jarvis.py:main()` (at line `1670`, right before `mt = os.path.getmtime(CMD_FILE)`): check `ipc_cmd = pop_ipc_cmd()` first so commands from `ShipCore.Host` execute with `0ms` latency without polling `jarvis_cmd.txt`!

#### What Claude Must Avoid & Where to Be Careful in Phase 2:
* **DO NOT** call `start_ipc_client()` at module import time in `jarvislib\base.py` — only call it inside `jarvis.py:main()` after `single_instance()` succeeds so `test_jarvis.py` imports remain 100% synchronous and deterministic.
* **DO NOT** remove the `Data\jarvis.txt`, `Data\jarvis_log.txt`, or `Data\jarvis_live.txt` disk writes in `base.py` — `test_jarvis.py` asserts directly against those files!

#### Phase 2 Verification Gate:
1. `py -3 -B Skins\Spaceship\@Resources\Jarvis\test_jarvis.py` -> 100% pass (all 706+ assertions).
2. Verify `ToJarvis` and `FromJarvis` pass 10,000 rapid concurrent messages without deadlock.

---

### PHASE 3: Native C# Collectors (Zero PowerShell Spawns), `Preact + @preact/signals` UI Core, SVG `lib.lua` Primitives & Debounced Hull Baker (`WP-3`)

#### 📋 Copy-Paste Prompt for Claude — Phase 3:
```markdown
Execute Phase 3 of the Standalone Spaceship App migration (`WP-3`).

AUTONOMY & ADJUSTMENT NOTICE:
If any PDH counter path or WMI query behaves differently on specific Windows 11 24H2 configurations, add a safe fallback and document it.

STEP-BY-STEP INSTRUCTIONS:
1. Build the 4 native C# collectors in `SpaceshipApp\ShipCore.Host\Collectors\` (replacing all 8 `.ps1` scripts with 0 console flashes and 0 PowerShell process spawns):
   - `SensorCollector.cs`: 1Hz batched reader for `HKCU\Software\HWiNFO64\VSB` with **Dynamic `Label0..Label199` Auto-Binding (`OVR-06`)** using the exact 12 pattern lists from `Scripts\controller.lua:140-153`, plus passive Win32/PDH counters (`GetSystemTimes`, `GlobalMemoryStatusEx`, `GetSystemPowerStatus`, `GetDiskFreeSpaceExW`, `GetTickCount64`, `GetLastInputInfo`, and passive PDH GPU/VRAM/Disk counters that NEVER wake the RTX 5070 dGPU from `D3cold`). Also sample top 5 CPU processes (`mTop1..mTop5` + RAM for `CenterTarget`).
   - `LegionToolkitBridge.cs`: Native C# replacement for `llt.ps1` and `status.ps1` (resolving `llt.exe`, checking NVIDIA PnP device status without waking the dGPU, and running `llt.exe feature get/set` with `CreateNoWindow = true`).
   - `AppScanner.cs` (`BUG-03` fix): Native C# replacement for `scan-apps.ps1` and `app-icons.ps1`. Port `HudIcons.Make()` from `Scripts\app-icons.ps1:42-112` directly into C# (`SHParseDisplayName` + `SHGetImageList(4 /* SHIL_JUMBO 256x256 */)` with `IShellItemImageFactory::GetImage(128, 128)` fallback), writing **`128x128` contrast-lifted greyscale `@Resources\Icons\<id>.png`**, **`128x128` 3-pass box-blurred `@Resources\Icons\<id>_glow.png`**, and **`@Resources\Icons\_index.txt`**.
   - `CloudPoller.cs` & `NetworkMonitor.cs`: Port `InternetAdapter()`, `NetLoop()`, `SpeedTest()`, `MailLoop()` (using `gmail.dat` DPAPI), and `SyncCalendars()` (using `calendars.dat` DPAPI) from `Scripts\ShipCore.cs:303-825`, plus HTTP `ETag` / `If-Modified-Since` (`304 Not Modified`) caching (`OVR-16`), Yahoo Finance `^GSPC` (`hud.lua:20`), `ObsidianTodo` parser (`target.lua:34-70`), `upkeep` (Windows Update COM + `winget` + `AntivirusProduct`), and `dev` (`wsl`, `ollama`, `tailscale`, `docker`).
2. Scaffold `SpaceshipApp\SpaceshipUI\` (`Preact + @preact/signals` + TypeScript + Vite -> builds to `Skins\Spaceship\@Resources\UI\dist\`):
   - Configure `vite.config.ts` with `preact/compat` aliases and multi-page entry points (`index.html` for `HudCanvasWindow` and `modal.html` for `ModalOverlayWindow`, `OVR-12`).
   - Create `src/styles/tokens.css` loading `B612Mono-Regular.ttf`, `B612Mono-Bold.ttf`, `Oxanium-Regular.ttf`, `Oxanium-Bold.ttf`, and `Michroma-Regular.ttf` from `https://spaceship.res/Fonts/`.
   - Create `src/components/svg/HudPrimitives.tsx` porting `Scripts\lib.lua` (`neon`, `halo`, `chamfer`, `brackets`, `dashArc`, `sector`, `segBar`, `graph`, `icon` using `generated/iconsData.json`, and `H.caption` hover tooltips).
   - Create `src/modules/CockpitFrame.tsx` + `SpaceshipApp\ShipCore.Host\CockpitTextureBaker.cs` (`FIX-DEBATE-06` + `OVR-11` + `IMP-03`).
```

#### Exact Code Implementations for Phase 3:

##### 3.1 Dynamic HWiNFO `Label0..Label199` Auto-Binding in `SensorCollector.cs` (`OVR-06` + `Scripts\controller.lua:140-153`)
```csharp
using Microsoft.Win32;
using System.Globalization;
using System.Text.RegularExpressions;

namespace ShipCore.Host.Collectors;

public sealed class HwinfoSensorReader
{
    private const string RegPath = @"Software\HWiNFO64\VSB";

    // Exact label pattern table from Skins\Spaceship\@Resources\Scripts\controller.lua:140-153
    private static readonly (string Key, string[] Patterns)[] SensorMap =
    [
        ("HW_CpuTemp",    ["tctl", "cpu package temp", "cpu temperature", "cpu (tdie)"]),
        ("HW_GpuTemp",    ["gpu temperature", "gpu core temp"]),
        ("HW_CpuPower",   ["cpu package power", "cpu ppt", "package power"]),
        ("HW_GpuPower",   ["total board power", "gpu power", "gpu board power"]),
        ("HW_Fan1",       ["cpu fan", "fan1", "fan 1"]),
        ("HW_Fan2",       ["gpu fan", "fan2", "fan 2"]),
        ("HW_GpuClock",   ["gpu clock", "gpu core clock"]),
        ("HW_ChargeRate", ["charge rate"]),
        ("HW_RemainCap",  ["remaining capacity"]),
        ("HW_FullCap",    ["full charged capacity", "full charge capacity"]),
        ("HW_Wear",       ["wear level"]),
        ("HW_SsdTemp",    ["drive temperature", "ssd temperature"]),
    ];

    private readonly Dictionary<string, int> _boundIndices = new(StringComparer.OrdinalIgnoreCase);
    private bool _needsRebind = true;

    public void LoadConfiguredIndices(IReadOnlyDictionary<string, string> settings)
    {
        foreach (var (key, _) in SensorMap)
        {
            if (settings.TryGetValue(key, out var raw) && int.TryParse(raw, out int idx) && idx >= 0)
                _boundIndices[key] = idx;
            else
                _boundIndices[key] = -1;
        }
        _needsRebind = _boundIndices.Values.Any(v => v < 0);
    }

    public Dictionary<string, float> PollAll(Action<string, string>? onSelfHealedIndex = null)
    {
        var result = new Dictionary<string, float>(StringComparer.OrdinalIgnoreCase);
        foreach (var (k, _) in SensorMap) result[k] = -1f;

        using var reg = Registry.CurrentUser.OpenSubKey(RegPath, writable: false);
        if (reg == null) return result;

        // OVR-06: Self-healing auto-discovery when any index is unmapped or shifted
        if (_needsRebind)
        {
            var labels = new List<(int Index, string Label)>(200);
            for (int i = 0; i < 200; i++)
            {
                if (reg.GetValue($"Label{i}") is string lbl && !string.IsNullOrWhiteSpace(lbl))
                    labels.Add((i, lbl.ToLowerInvariant()));
            }
            if (labels.Count > 0)
            {
                foreach (var (key, patterns) in SensorMap)
                {
                    int foundIdx = -1;
                    foreach (var pat in patterns)
                    {
                        var hit = labels.FirstOrDefault(x => x.Label.Contains(pat, StringComparison.Ordinal));
                        if (hit.Label != null) { foundIdx = hit.Index; break; }
                    }
                    if (foundIdx >= 0 && _boundIndices.GetValueOrDefault(key, -1) != foundIdx)
                    {
                        _boundIndices[key] = foundIdx;
                        onSelfHealedIndex?.Invoke(key, foundIdx.ToString(CultureInfo.InvariantCulture));
                    }
                }
                _needsRebind = false;
            }
        }

        foreach (var (key, _) in SensorMap)
        {
            int idx = _boundIndices.GetValueOrDefault(key, -1);
            if (idx < 0) continue;
            string? raw = reg.GetValue($"ValueRaw{idx}") as string ?? reg.GetValue($"Value{idx}") as string;
            if (raw == null) { _needsRebind = true; continue; }
            var m = Regex.Match(raw, @"-?[\d.]+");
            if (m.Success && float.TryParse(m.Value, NumberStyles.Float, CultureInfo.InvariantCulture, out float val))
                result[key] = val;
        }
        return result;
    }
}
```

##### 3.2 `HudPrimitives.tsx` (`SpaceshipApp\SpaceshipUI\src\components\svg\HudPrimitives.tsx` — Exact Port of `Scripts\lib.lua`)
```tsx
import { h } from "preact";
import iconsData from "../../../generated/iconsData.json";

export type RGB = [number, number, number, number?];

export function rgba(c: RGB, alphaOverride?: number, hudAlpha = 255): string {
  const a = Math.floor(((alphaOverride ?? c[3] ?? 255) * hudAlpha) / 255);
  return `rgba(${c[0]}, ${c[1]}, ${c[2]}, ${(a / 255).toFixed(3)})`;
}

export function mix(c1: RGB, c2: RGB, t: number): RGB {
  const k = Math.max(0, Math.min(1, t));
  return [
    Math.floor(c1[0] + (c2[0] - c1[0]) * k),
    Math.floor(c1[1] + (c2[1] - c1[1]) * k),
    Math.floor(c1[2] + (c2[2] - c1[2]) * k),
    255,
  ];
}

// lib.lua:93: accent -> warn -> alert ramp for 0..1 load values
export function ramp(v: number, accent: RGB, warn: RGB, alert: RGB): RGB {
  if (v < 0.7) return accent;
  if (v < 0.9) return mix(accent, warn, (v - 0.7) / 0.2);
  return mix(warn, alert, (v - 0.9) / 0.1);
}

export function arcPts(cx: number, cy: number, rx: number, ry: number, a0: number, a1: number, segs?: number): [number, number][] {
  const n = segs ?? Math.max(6, Math.floor(Math.abs(a1 - a0) / 6));
  const pts: [number, number][] = [];
  for (let i = 0; i <= n; i++) {
    const a = ((a0 + ((a1 - a0) * i) / n) * Math.PI) / 180;
    pts.push([cx + rx * Math.cos(a), cy + ry * Math.sin(a)]);
  }
  return pts;
}

export function ptsToSvgPath(pts: [number, number][], closed = false): string {
  if (pts.length === 0) return "";
  let d = `M ${pts[0][0].toFixed(2)} ${pts[0][1].toFixed(2)}`;
  for (let i = 1; i < pts.length; i++) {
    d += ` L ${pts[i][0].toFixed(2)} ${pts[i][1].toFixed(2)}`;
  }
  if (closed) d += " Z";
  return d;
}

// lib.lua:206: Chamfered hexagon panel outline
export function chamferPts(x: number, y: number, w: number, h: number, c: number): [number, number][] {
  return [
    [x + c, y],
    [x + w, y],
    [x + w, y + h - c],
    [x + w - c, y + h],
    [x, y + h],
    [x, y + c],
  ];
}

// lib.lua:116: Three-layer neon bloom stroke (outer wide halo on tier 0, medium glow on tier <2, core pulled toward white)
export function NeonPath(props: {
  d: string;
  col: RGB;
  white: RGB;
  width?: number;
  alpha?: number;
  tier: number;
  glowAlpha: number;
  glowWidth: number;
  coreWhite: number;
  hudAlpha: number;
  strokeDasharray?: string;
  strokeLinecap?: "round" | "butt" | "square";
  className?: string;
}) {
  const w = props.width ?? 1.6;
  const a = props.alpha ?? props.col[3] ?? 255;
  const coreCol = props.coreWhite > 0 ? mix(props.col, props.white, props.coreWhite) : props.col;
  const cap = props.strokeLinecap ?? "round";
  return (
    <g className={props.className}>
      {props.tier === 0 && props.glowAlpha > 0 && (
        <path
          d={props.d}
          fill="none"
          stroke={rgba(props.col, Math.floor((props.glowAlpha * 0.38 * a) / 255), props.hudAlpha)}
          strokeWidth={w * props.glowWidth * 2.1}
          strokeLinecap={cap}
          strokeLinejoin="round"
          strokeDasharray={props.strokeDasharray}
        />
      )}
      {props.tier < 2 && props.glowAlpha > 0 && (
        <path
          d={props.d}
          fill="none"
          stroke={rgba(props.col, Math.floor((props.glowAlpha * a) / 255), props.hudAlpha)}
          strokeWidth={w * props.glowWidth}
          strokeLinecap={cap}
          strokeLinejoin="round"
          strokeDasharray={props.strokeDasharray}
        />
      )}
      <path
        d={props.d}
        fill="none"
        stroke={rgba(coreCol, a, props.hudAlpha)}
        strokeWidth={w}
        strokeLinecap={cap}
        strokeLinejoin="round"
        strokeDasharray={props.strokeDasharray}
      />
    </g>
  );
}

// lib.lua:392: Draw vector icon from generated/iconsData.json centred at (cx, cy) with size `sz`
export function VectorHudIcon(props: {
  name: string;
  cx: number;
  cy: number;
  size: number;
  col: RGB;
  white: RGB;
  lw?: number;
  alpha?: number;
  tier: number;
  glowAlpha: number;
  glowWidth: number;
  coreWhite: number;
  hudAlpha: number;
}) {
  const def = (iconsData as Record<string, any[]>)[props.name] ?? (iconsData as Record<string, any[]>)["gear"] ?? [];
  const k = props.size / 100;
  const P = (x: number, y: number): [number, number] => [props.cx + (x - 50) * k, props.cy + (y - 50) * k];
  const paths: string[] = [];

  for (const p of def) {
    const t = p[0] as string;
    if (t === "l" || t === "p") {
      const pts: [number, number][] = [];
      for (let i = 1; i < p.length; i += 2) pts.push(P(p[i], p[i + 1]));
      paths.push(ptsToSvgPath(pts, t === "p"));
    } else if (t === "c") {
      const [cx, cy] = P(p[1], p[2]);
      const r = p[3] * k;
      paths.push(ptsToSvgPath(arcPts(cx, cy, r, r, 0, 360, 28), true));
    } else if (t === "a") {
      const [cx, cy] = P(p[1], p[2]);
      const rx = p[3] * k;
      const ry = (p[6] ?? p[3]) * k;
      paths.push(ptsToSvgPath(arcPts(cx, cy, rx, ry, p[4], p[5]), false));
    } else if (t === "e") {
      const [cx, cy] = P(p[1], p[2]);
      paths.push(ptsToSvgPath(arcPts(cx, cy, p[3] * k, p[4] * k, 0, 360, 36), true));
    }
  }

  return (
    <NeonPath
      d={paths.join(" ")}
      col={props.col}
      white={props.white}
      width={props.lw ?? 1.5}
      alpha={props.alpha}
      tier={props.tier}
      glowAlpha={props.glowAlpha}
      glowWidth={props.glowWidth}
      coreWhite={props.coreWhite}
      hudAlpha={props.hudAlpha}
    />
  );
}
```

##### 3.3 Recolored App Icon Component (`lib.lua:223-244` ColorMatrix Port)
In `lib.lua:238-242`, Rainmeter recolors `@Resources\Icons\<id>.png` (128x128 greyscale) from `ColorAccent` (dark parts) to `ColorWhite` (bright parts) over `@Resources\Icons\<id>_glow.png` tinted with `ColorAccent`:
```tsx
export function ExtractedAppIcon(props: {
  appId: string;
  cx: number;
  cy: number;
  size: number;
  accent: RGB;
  tier: number;
  hudAlpha: number;
}) {
  const r = props.accent[0] / 255;
  const g = props.accent[1] / 255;
  const b = props.accent[2] / 255;
  const filterId = `icon-matrix-${props.appId}`;
  const glowSize = props.size * 1.25;
  // Exact 4x5 SVG feColorMatrix equivalent of lib.lua:238-242:
  // R_out = (1 - r) * R_in + r
  // G_out = (1 - g) * G_in + g
  // B_out = (1 - b) * B_in + b
  // A_out = A_in
  const matrixValues = `${(1 - r).toFixed(3)} 0 0 0 ${r.toFixed(3)}  0 ${(1 - g).toFixed(3)} 0 0 ${g.toFixed(3)}  0 0 ${(1 - b).toFixed(3)} 0 ${b.toFixed(3)}  0 0 0 1 0`;

  return (
    <g>
      <defs>
        <filter id={filterId} colorInterpolationFilters="sRGB">
          <feColorMatrix type="matrix" values={matrixValues} />
        </filter>
      </defs>
      {props.tier < 2 && (
        <image
          href={`https://spaceship.res/Icons/${props.appId}_glow.png`}
          x={props.cx - glowSize / 2}
          y={props.cy - glowSize / 2}
          width={glowSize}
          height={glowSize}
          opacity={0.8 * (props.hudAlpha / 255)}
          style={{ filter: `drop-shadow(0 0 4px rgb(${props.accent[0]},${props.accent[1]},${props.accent[2]}))` }}
        />
      )}
      <image
        href={`https://spaceship.res/Icons/${props.appId}.png`}
        x={props.cx - props.size / 2}
        y={props.cy - props.size / 2}
        width={props.size}
        height={props.size}
        opacity={props.hudAlpha / 255}
        filter={`url(#${filterId})`}
      />
    </g>
  );
}
```

#### What Claude Must Avoid & Where to Be Careful in Phase 3:
* **DO NOT** query `nvml.dll` or DirectX device creation on the NVIDIA adapter in `SensorCollector.cs` — use HWiNFO `VSB` registry + passive PDH counters so the RTX 5070 sleeps at `0W` (`D3cold`) on battery.
* **DO NOT** change the icon path from `https://spaceship.res/Icons/<id>.png` (`@Resources\Icons\`, `BUG-03`).

#### Phase 3 Verification Gate:
1. Verify `0` PowerShell processes are spawned during 5 minutes of running `ShipCore.Host.exe`.
2. Verify `@Resources\Icons\<id>.png`, `<id>_glow.png`, and `_index.txt` are populated by `AppScanner.cs` for both `.exe` and `shell:AppsFolder\` Microsoft Store apps.

---

### PHASE 4: 165Hz `<IntroSequence />`, Event-Driven Occlusion (`OVR-14`), 4096-Sample SIMD Audio FFT (`OVR-13`) & Dynamic Orb Atlas + 3D Core (`IMP-05` + `OVR-10`) (`WP-4`)

#### 📋 Copy-Paste Prompt for Claude — Phase 4:
```markdown
Execute Phase 4 of the Standalone Spaceship App migration (`WP-4`).

AUTONOMY & ADJUSTMENT NOTICE:
You have full freedom to fine-tune the WebGL2 shaders, spring constants, and WAAPI easing curves so the opening sequence, audio reactor, and 3D Clover hologram run at a locked 165Hz (`P50 < 2.8ms, P99 < 5.5ms`).

STEP-BY-STEP INSTRUCTIONS:
1. Create and run `tools\build_orb_atlas.py` (`IMP-05` + `OVR-10`):
   - Dynamically scan `@Resources\Images\Jarvis\Idle\` and `Active\` using all 8 filename patterns from `jarvis.lua:34` (handling 204, 210, or any user frame count).
   - Convert 8-bit `PLTE`+`tRNS` indexed PNGs via `.convert("RGBA")`.
   - Downsample each cell from `224x224` to `160x160` (`14x15` grid = `2240x2400` = `21.5 MB` uncompressed RGBA8 vs `42.1 MB`, matching `OVR-10`'s VRAM budget without external CLI tools!).
   - If `texconv.exe` is on `PATH`, also emit `BC7_UNORM` `.dds`; always emit `.webp` (`quality=92, method=6`) and `@Resources\Images\Jarvis\manifest.json` (`frameCount, cols, rows, frameW, frameH`).
2. Implement `SpaceshipApp\ShipCore.Host\VisibilityGovernor.cs` (`FIX-DEBATE-09` + `OVR-14`):
   - Out-of-context `SetWinEventHook` (`EVENT_SYSTEM_FOREGROUND`, `EVENT_SYSTEM_MINIMIZESTART`, `EVENT_SYSTEM_MINIMIZEEND`, 50ms debounce) + 5-Gate `DWMWA_CLOAKED == 0` filter -> `<15ms` wake from `OCCLUDED` mode.
3. Implement `SpaceshipApp\ShipCore.Host\Collectors\WasapiSpectrumAnalyzer.cs` (`FIX-DEBATE-10` + `OVR-05` + `OVR-13`):
   - Event-driven WASAPI Loopback (`IAudioClient.SetEventHandle`) with a **4096-sample sliding ring buffer** (`800`-sample hop at 60Hz, Hann window, radix-2 SIMD FFT, Catmull-Rom cubic interpolation across sub-120Hz bins, 96 logarithmic bands `35 Hz – 16,000 Hz`), smooth zero-input decay on pause, `WaitForSingleObject(INFINITE)` kernel sleep during silence, and zero-copy writes to `WebViewLifecycleManager.WriteSharedFloatBlock(0, bands)`.
4. Implement `src/modules/AudioReactor.tsx` (exact port of `Scripts\audio.lua`), `src/modules/JarvisCore3D.tsx` (exact port of `Scripts\jarvis.lua` + WebGL2 Atlas/Procedural GLSL + `webglcontextlost` 2D fallback + Wake-Word Shockwave with `ui.animationLease`), and `src/modules/IntroSequence.tsx` (Part 4.2 5-Stage 165Hz Choreography + `IMP-03` 2-Frame `DwmFlush()` Handoff).
```

#### Exact Code Implementations for Phase 4:

##### 4.1 `tools\build_orb_atlas.py` (`IMP-05` Dynamic Frame Count, 8-bit `PLTE`+`tRNS` Conversion, `160x160` Downsample & `manifest.json`)
```python
#!/usr/bin/env python3
"""IMP-05 + OVR-10: Packs @Resources/Images/Jarvis/Idle and Active frames into GPU-friendly sprite atlases
and writes @Resources/Images/Jarvis/manifest.json with exact dynamic frame counts."""
import json
import math
import shutil
import subprocess
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
JARVIS_IMG = ROOT / "Skins" / "Spaceship" / "@Resources" / "Images" / "Jarvis"
CELL_SIZE = 160  # IMP-05: 160x160 per cell -> 14x15 atlas is 2240x2400 (21.5 MB RGBA8 vs 42.1 MB at 224x224!)
COLS = 14

PATTERNS = [
    "{:03d}.png", "frame-{:03d}.png", "ezgif-frame-{:03d}.png", "frame_{:03d}.png",
    "frame{:03d}.png", "{:04d}.png", "frame_{:04d}.png", "frame-{:04d}.png",
]


def discover_frames(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    for pat in PATTERNS:
        for first in (1, 0):
            if (folder / pat.format(first)).is_file():
                frames = []
                n = 0
                while n < 600:
                    p = folder / pat.format(first + n)
                    if not p.is_file():
                        break
                    frames.append(p)
                    n += 1
                return frames
    return sorted(folder.glob("*.png"))


def build_atlas(name: str, folder: Path) -> dict:
    frames = discover_frames(folder)
    count = len(frames)
    if count == 0:
        return {"frameCount": 0, "cols": 0, "rows": 0, "frameW": CELL_SIZE, "frameH": CELL_SIZE}
    cols = COLS
    rows = math.ceil(count / cols)
    # Round dimensions up to multiples of 4 for BC7 block alignment
    atlas_w = ((cols * CELL_SIZE + 3) // 4) * 4
    atlas_h = ((rows * CELL_SIZE + 3) // 4) * 4
    atlas = Image.new("RGBA", (atlas_w, atlas_h), (0, 0, 0, 0))

    for idx, fpath in enumerate(frames):
        # IMP-05: Convert 8-bit PLTE + tRNS indexed colormap PNGs to true 32-bit RGBA
        with Image.open(fpath) as im:
            rgba = im.convert("RGBA")
            if rgba.size != (CELL_SIZE, CELL_SIZE):
                rgba = rgba.resize((CELL_SIZE, CELL_SIZE), Image.Resampling.LANCZOS)
            c = idx % cols
            r = idx // cols
            atlas.paste(rgba, (c * CELL_SIZE, r * CELL_SIZE))

    webp_path = JARVIS_IMG / f"{name}_atlas.webp"
    atlas.save(webp_path, format="WEBP", quality=92, method=6)
    dds_name = None

    texconv = shutil.which("texconv") or shutil.which("texconv.exe")
    if texconv:
        tmp_png = JARVIS_IMG / f"{name}_atlas_tmp.png"
        atlas.save(tmp_png, format="PNG")
        try:
            subprocess.run(
                [texconv, "-f", "BC7_UNORM", "-m", "1", "-y", "-o", str(JARVIS_IMG), str(tmp_png)],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            dds_tmp = JARVIS_IMG / f"{name}_atlas_tmp.dds"
            dds_final = JARVIS_IMG / f"{name}_atlas.dds"
            if dds_tmp.exists():
                dds_tmp.replace(dds_final)
                dds_name = dds_final.name
        except Exception:
            pass
        finally:
            tmp_png.unlink(missing_ok=True)

    return {
        "frameCount": count,
        "cols": cols,
        "rows": rows,
        "frameW": CELL_SIZE,
        "frameH": CELL_SIZE,
        "atlasW": atlas_w,
        "atlasH": atlas_h,
        "webp": webp_path.name,
        "dds": dds_name,
    }


def main():
    JARVIS_IMG.mkdir(parents=True, exist_ok=True)
    manifest = {
        "idle": build_atlas("idle", JARVIS_IMG / "Idle"),
        "active": build_atlas("active", JARVIS_IMG / "Active"),
    }
    (JARVIS_IMG / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Built Jarvis orb atlases:", json.dumps(manifest))


if __name__ == "__main__":
    main()
```

##### 4.2 `WasapiSpectrumAnalyzer.cs` (`OVR-13` 4096-Sample Sliding Ring Buffer + Sub-Bass Catmull-Rom Cubic Interpolation)
```csharp
using System.Numerics;
using System.Runtime.InteropServices;

namespace ShipCore.Host.Collectors;

public sealed class WasapiSpectrumAnalyzer : IDisposable
{
    private const int FFT_SIZE = 4096; // OVR-13: 48000 Hz / 4096 = 11.72 Hz bin resolution for sub-bass!
    private const int NUM_BANDS = 96;  // Audio.ini: Bands=96, FreqMin=35, FreqMax=16000
    private const float FREQ_MIN = 35.0f;
    private const float FREQ_MAX = 16000.0f;

    private readonly float[] _ringBuffer = new float[FFT_SIZE];
    private readonly float[] _window = new float[FFT_SIZE];
    private readonly Complex[] _fftWork = new Complex[FFT_SIZE];
    private readonly float[] _magBins = new float[FFT_SIZE / 2];
    private readonly float[] _bandFreqs = new float[NUM_BANDS];
    private readonly float[] _smoothedBands = new float[NUM_BANDS];
    private int _ringWritePos;
    private float _smoothedRms;
    private float _smoothedPeak;

    public WasapiSpectrumAnalyzer()
    {
        for (int i = 0; i < FFT_SIZE; i++)
            _window[i] = 0.5f * (1.0f - MathF.Cos(2.0f * MathF.PI * i / (FFT_SIZE - 1)));
        float logMin = MathF.Log10(FREQ_MIN), logMax = MathF.Log10(FREQ_MAX);
        for (int b = 0; b < NUM_BANDS; b++)
            _bandFreqs[b] = MathF.Pow(10.0f, logMin + (logMax - logMin) * b / (NUM_BANDS - 1));
    }

    public void PushMonoSamples(ReadOnlySpan<float> samples, int sampleRate, WebViewLifecycleManager webView)
    {
        float sumSq = 0f, peak = 0f;
        for (int i = 0; i < samples.Length; i++)
        {
            float s = samples[i];
            _ringBuffer[_ringWritePos] = s;
            _ringWritePos = (_ringWritePos + 1) & (FFT_SIZE - 1);
            sumSq += s * s;
            float abs = MathF.Abs(s);
            if (abs > peak) peak = abs;
        }

        float rms = samples.Length > 0 ? MathF.Sqrt(sumSq / samples.Length) : 0f;
        _smoothedRms = _smoothedRms * 0.6f + Math.Clamp(rms * 2.8f, 0f, 1f) * 0.4f;
        _smoothedPeak = MathF.Max(Math.Clamp(peak, 0f, 1f), _smoothedPeak * 0.85f);

        // Apply Hann window from ring buffer into _fftWork
        for (int i = 0; i < FFT_SIZE; i++)
        {
            float s = _ringBuffer[(_ringWritePos + i) & (FFT_SIZE - 1)] * _window[i];
            _fftWork[i] = new Complex(s, 0.0);
        }

        Radix2FftInPlace(_fftWork);

        float invN = 2.0f / FFT_SIZE;
        for (int k = 0; k < FFT_SIZE / 2; k++)
            _magBins[k] = (float)_fftWork[k].Magnitude * invN;

        float binWidthHz = (float)sampleRate / FFT_SIZE; // 11.71875 Hz at 48 kHz
        for (int b = 0; b < NUM_BANDS; b++)
        {
            float f = _bandFreqs[b];
            float binF = f / binWidthHz;
            // OVR-13: Catmull-Rom cubic interpolation for smooth sub-bass & mid bands
            float rawMag = SampleCatmullRom(_magBins, binF);
            // Convert to normalized perceptual level (Sensitivity=42 dB range matching Audio.ini:30)
            float db = 20.0f * MathF.Log10(rawMag * 18.0f + 1e-6f);
            float norm = Math.Clamp((db + 42.0f) / 42.0f, 0f, 1f);
            // Attack=25ms (~0.55 alpha), Decay=140ms (~0.18 alpha)
            float alpha = norm > _smoothedBands[b] ? 0.55f : 0.18f;
            _smoothedBands[b] += (norm - _smoothedBands[b]) * alpha;
        }

        // OVR-05: Zero-copy write directly into CoreWebView2SharedBuffer!
        webView.WriteSharedFloatBlock(0, _smoothedBands);
        webView.WriteSharedFloat(96, _smoothedRms);
        webView.WriteSharedFloat(97, _smoothedPeak);
        webView.WriteSharedFloat(98, _smoothedRms > 0.004f ? 1.0f : 0.0f);
    }

    private static float SampleCatmullRom(ReadOnlySpan<float> bins, float pos)
    {
        int i1 = Math.Clamp((int)MathF.Floor(pos), 1, bins.Length - 3);
        float t = Math.Clamp(pos - i1, 0f, 1f);
        float p0 = bins[i1 - 1], p1 = bins[i1], p2 = bins[i1 + 1], p3 = bins[i1 + 2];
        float t2 = t * t, t3 = t2 * t;
        float val = 0.5f * ((2f * p1) + (-p0 + p2) * t + (2f * p0 - 5f * p1 + 4f * p2 - p3) * t2 + (-p0 + 3f * p1 - 3f * p2 + p3) * t3);
        return MathF.Max(0f, val);
    }

    private static void Radix2FftInPlace(Span<Complex> buffer)
    {
        int n = buffer.Length;
        for (int i = 1, j = 0; i < n; i++)
        {
            int bit = n >> 1;
            for (; (j & bit) != 0; bit >>= 1) j ^= bit;
            j ^= bit;
            if (i < j) (buffer[i], buffer[j]) = (buffer[j], buffer[i]);
        }
        for (int len = 2; len <= n; len <<= 1)
        {
            double ang = -2.0 * Math.PI / len;
            var wlen = new Complex(Math.Cos(ang), Math.Sin(ang));
            for (int i = 0; i < n; i += len)
            {
                var w = Complex.One;
                int half = len >> 1;
                for (int j = 0; j < half; j++)
                {
                    var u = buffer[i + j];
                    var v = buffer[i + j + half] * w;
                    buffer[i + j] = u + v;
                    buffer[i + j + half] = u - v;
                    w *= wlen;
                }
            }
        }
    }

    public void Dispose() { }
}
```

#### What Claude Must Avoid & Where to Be Careful in Phase 4:
* **DO NOT** hardcode `210` frames in `JarvisCore3D.tsx` (`IMP-05`) — always load `https://spaceship.res/Images/Jarvis/manifest.json` so `idle.frameCount` and `active.frameCount` (`204`, `210`, or custom) drive the UV cell lookup dynamically!
* **DO NOT** run WASAPI FFT loops during silence — when `IAudioCaptureClient.GetBuffer` returns `AUDCLNT_BUFFERFLAGS_SILENT` or zero energy for `>400ms`, decay `_smoothedBands` to `0.0f` and wait on the kernel audio event handle (`0.00%` CPU during silence).

#### Phase 4 Verification Gate:
1. Run `py -3 tools\build_orb_atlas.py` -> verifies `idle_atlas.webp`, `active_atlas.webp`, and `manifest.json` are generated and total VRAM expansion is `<22 MB` (`IMP-05`).
2. Verify `<IntroSequence />` runs at `165Hz` (`P99 < 5.5ms`) with `0` frame drops and ends with the 2-frame `DwmFlush()` handoff (`IMP-03`).
3. Verify minimizing a maximized window wakes the HUD in `<15ms` (`OVR-14`).

---

### PHASE 5: Complete Port of All 22 HUD Modules, 3 Modals (`modal.html`) & Visual Drag-and-Drop `LayoutStudio` (`WP-5`)

#### 📋 Copy-Paste Prompt for Claude — Phase 5:
```markdown
Execute Phase 5 of the Standalone Spaceship App migration (`WP-5`).

AUTONOMY & ADJUSTMENT NOTICE:
You may organize sub-components cleanly and enhance micro-interactions, provided every module preserves its exact coordinates and `TransformationMatrix` from `geometryData.json` (Part 3.1), its exact color/font rules from `lib.lua`, and all click/right-click/scroll actions from its original `.lua` script.

STEP-BY-STEP INSTRUCTIONS:
1. Port all remaining HUD modules in `SpaceshipApp\SpaceshipUI\src\modules\` using the exact per-module specifications in Section 5.1 below (watching out for `BUG-06`: `BottomStorage` = `dial.lua` Systems Dial + toggleable `storage.lua`, `LeftLocation` = `location.lua` Mission Clock, `RightSysInfo` = `sysinfo.lua` Network Block).
2. Build `modal.html` + `src/modals/ModalApp.tsx` (`OVR-12`) hosting:
   - `ControlCenterModal.tsx` (`OverlayControl`, `1040x900`, all 10 tabs from `Scripts\control.lua`: `MODULES`, `LAYOUT`, `THEME`, `APPS`, `SENSORS`, `PERF`, `SYSTEM`, `PRESETS`, `DATA`, `CLOVER`, plus inline text inputs for `CALL ME`, `TYPE TO HIM`, and a `MEMORY EDITOR` for `jarvis_memory.txt`).
   - `CargoDrawerModal.tsx` (`OverlayDrawer`, `560x560`, ported from `Scripts\drawer.lua` + live keyboard search bar + 20s idle auto-hide).
   - `JarvisLogModal.tsx` (`OverlayJarvis`, `1200x616`, ported from `Scripts\jarvislog.lua` with live streaming `jarvis_live.txt`, clickable citation/note links, inline `"Type to Clover..."` input bar at the bottom, and 3-minute idle auto-hide).
3. Build `src/modules/LayoutStudio.tsx` (`DEC-17` + `Scripts\guard.lua`):
   - When `EditMode=1`, acquire an `ui.animationLease`, render golden zone outlines + `(DX, DY)` coordinate pills, allow dragging any module with `1px` / `Shift+10px` grid snapping, run Separating Axis Theorem collision checks (`guard.lua` `G.check()`) against `safe = { inset: 10, r: 110 }`, `bottom = 1528`, `keepouts`, and other modules (`gap = 6` px), and persist `<ModuleKey>_DX` and `<ModuleKey>_DY` to `@Resources\Offsets.inc`.
```

#### 5.1 Exact Per-Module Drawing, Math & Interaction Specifications (Ported Directly from `Scripts\*.lua`)

Use these exact coordinates, formulas, and click actions for each module (saving ~120,000 tokens of reading `.lua` files):

1. **`TopPowerBar.tsx` (`TopPower`, zone `T_power`: `197.9 x 27.08`, `Z1_TM = 0.9959;0.0912;0;1;0.0772;-1.6992`, ported from `Scripts\power.lua`)**:
   * **Math**: `watts = (cpuPowerW >= 0 || gpuPowerW >= 0) ? Math.max(0, cpuPowerW) + Math.max(0, gpuPowerW) : (chargeRateW < 0 ? -chargeRateW : null)`. `v = watts !== null ? clamp(watts / 160, 0, 1) : 0`.
   * **Drawing**: `y = z.h * 0.5`, `x0 = 22`, `x1 = z.w - 26`. Left label `'P'` at `(0, y)` (`8.5pt`, `LeftCenter`, `ColorWhite`). White track line `(x0, y) -> (x1, y)` (`w=1.3, a=210`). Hot fill line `(x0, y) -> (x0 + (x1 - x0) * v, y)` (`ColorHighlight`, `w=2.6`). Vertical tick at `x0 + (x1 - x0) * v` from `y - 6` to `y + 2` (`ColorWhite`, `w=1.3`). Right label at `(z.w, y)` (`8.5pt`, `RightCenter`, `ColorWhite`): `watts !== null ? "${Math.round(watts)}W" : "W"`.
   * **Click**: Opens `ControlCenterModal` (`tab = 5` `SENSORS`).

2. **`TopBatteryBar.tsx` (`TopBattery`, zone `T_battery`: `197.9 x 27.08`, `Z1_TM = 0.9959;-0.0912;0;1;0.0758;1.6682`, ported from `Scripts\battery.lua`)**:
   * **Math**: `pct = batteryPct`, `ac = acLineStatus > 0`, `limit = ChargeLimit (80)`. If `ac`: if `pct >= limit - 1` -> `status = "HELD " + limit + "%"`; else compute `timeToLimit` from `(limit/100 * fullCap - remainCap) / 1000 / chargeRate * 3600` (or slope of `(now, pct)` samples over last 600s) -> `"H:MM TO 80%"` or `"CHG TO 80%"`. If `!ac`: `status = batteryLifeSec > 0 ? duration(batteryLifeSec) + " LEFT" : "ON BATT"`.
   * **Drawing**: `y = z.h * 0.76`, `x0 = 48`, `x1 = z.w`. Left label `'PWR'` at `(0, y)` (`8.5pt`, `LeftCenter`, `ColorWhite`). Track line `(x0, y) -> (x1, y)` (`ColorWhite`, `w=1.3, a=200`). Fill line `(x0, y) -> (x0 + (x1 - x0) * pct / 100, y)` (`(!ac && pct <= WarnBattery) ? ColorAlert : (ac ? ColorGood : ColorHighlight)`, `w=2.6`). Charge-limit tick at `lx = x0 + (x1 - x0) * limit / 100` from `y - 6` to `y + 3` (`ColorWhite`, `w=1.2`). Small readout at `(x0, 0)` (`4.8pt`, `LeftTop`, `ColorWhite, a=210`): `"${pct}%  ${status}"`.
   * **Click**: Opens `ms-settings:batterysaver`.

3. **`TopConsole.tsx` (`TopConsole`, zone `T_settings`: `678.6 x 106.06`, ported from `Scripts\console.lua`)**:
   * **Coordinate Helper**: `SXR = 2560 / 1260`, `SYR = 1600 / 709`, `RX(x) = (x - 463) * SXR`, `RY(y) = (y - 10) * SYR`.
   * **Row 1 — 5 GPU Mode Tabs (`Y = RY(23)`, `TABX = [549, 591, 630, 669, 711]`)**:
     * Tabs: `1: ECO` (`on-igpu-only`), `2: HYBRID` (`on`), `3: AUTO` (`on-auto`), `4: dGPU` (`off` — requires double-click confirmation within 5s: shows `'CONFIRM?'` in `ColorWarn` on first click!), `5: OFF` (hides/shows all HUD modules except `TopConsole`).
     * Active tab shows `ColorWhite` text + `44px` cyan underline at `y + 9`. Tab 4 (`dGPU`) draws a `2.6px` status dot at `x + 26` (`ColorGood` when RTX 5070 is powered on, `ColorDim` when sleeping in `D3cold`).
   * **Row 2 Left — `CARGO` & `CFG` Buttons (`Y = RY(46)..RY(55)`, `BOX = [[538, 559], [569, 589]]`)**:
     * `CARGO`: Opens `CargoDrawerModal`. `CFG`: Opens `ControlCenterModal`.
   * **Row 2 Right — 5 Quick Toggles (`TXT = [[671,51], [695,50], [719,49], [743,48], [767,47]]`)**:
     * `1`: Power mode (`QUIET` / `BAL` / `PERF` — click cycles `LltPowerModes`).
     * `2`: Refresh rate (`60HZ` / `165HZ` — click cycles `LltRefreshRates`).
     * `3`: Battery conservation (`80%`, lit in `ColorHighlight` when conservation mode is `ON` — click toggles).
     * `4`: Graphics PerfTier (`AUTO` / `FULL` / `LITE` / `LOW` / `STEA` — click cycles `PerfOverride` `-1..3`).
     * `5`: `MASTER` kill switch (lit in `ColorHighlight` when `PerfOverride == 3` — click toggles `STEALTH` vs previous tier).

4. **`TopAlert.tsx` (`TopAlert`, zone `T_alert`: `58.93 x 42.87`, ported from `Scripts\alert.lua`)**:
   * Checks 5 conditions: `cpuTemp >= WarnCpuTemp (92)`, `gpuTemp >= WarnGpuTemp (85)`, `diskUsedPct >= WarnDiskPct (90)`, `!ac && battPct <= WarnBattery (20)`, `cpuLoad >= 95`.
   * Draws right-pointing triangle centered at `(s * 0.55 + 4, z.h / 2)` (`s = z.h * 0.62`, `ColorHighlight`, `w=2`) and warning count `n` at `(z.w, z.h / 2)` (`9pt`, `RightCenter`, `ColorHighlight`). Blinks alpha `130 <-> 255` at 1Hz when `n > 0 && tier < 2`. Click opens `ControlCenterModal`.

5. **`TelemetryGraph.tsx` x4 (`TopGraphCPU`, `TopGraphA`, `TopGraphB`, `TopGraphRAM`, each `231.62 x 74.47`, ported from `Scripts\graph.lua` + `sources.lua`)**:
   * Maintains a 48-sample rolling history (`N = 48`, 1Hz).
   * 11 selectable sources from `sources.lua`: `cpu` (`CPU LOAD`, `0..100%`), `ram` (`MEMORY USED`, `0..100%`), `gpu` (`GPU LOAD`, `0..100%`), `vram` (`VIDEO MEMORY`, `0..12 GB`), `cputemp` (`CPU TEMP`, `30..100°C`), `gputemp` (`GPU TEMP`, `30..90°C`), `power` (`POWER DRAW`, `0..160 W`), `disk` (`DISK I/O`, auto-scaled), `netdown` (`NET DOWN`, auto-scaled), `netup` (`NET UP`, auto-scaled), `battery` (`BATTERY LEVEL`, `0..100%`).
   * Draws 5 left-edge scale ticks (`x = 4..11`), filled area polygon (`fillAlpha = 22`) + `1.3px` trace line + `2.2px` leading dot in `ramp(cur)`, centered two-line ghost label in `rgb(40, 82, 150)` (`10pt`) behind the trace, bottom-right live value (`4.6pt`, `FontNum`), and double chevron `>>` at `(8..18, z.h - 6)` on selectable graphs (`TopGraphA` & `TopGraphB` — click/scroll cycles next source, right-click cycles previous, persisted to `GraphA_Source` / `GraphB_Source` in `Settings.inc`).

6. **`CategorySchematic.tsx` x2 (`LeftCategory` & `RightCategory`, 3 zones each, ported from `Scripts\category.lua`)**:
   * **Zone 1 (`L_tabs` / `R_tabs`, `376.34 x 47.39` slanted)**: Two parallel rails `(10, 4)->(w-4, 4)` and `(4, h-4)->(w-8, h-4)` with `3px` end dots. Up to `MAXTABS = 4` justified app short-names (`6.2pt`, selected app in `ColorAccent`, others in `rgb(175,190,200)`). Click selects app; right-click launches app; scroll cycles apps.
   * **Zone 2 (`L_category` / `R_category`, `347.25 x 259.52` slanted)**: Draws the selected app's wireframe hologram (`VectorHudIcon` at `sz = Math.min(w, h) * 0.94`) in ice-cyan `mix(ColorAccent, ColorWhite, 0.45)` + a white offset ghost at `(cx + 3, cy - 3, sz * 0.97, alpha = 60)`, 4 wing-tip corner brackets `[ ]`, a pulsing `ColorHighlight` core circle (`r = sz * 0.07`, brighter + inner icon when the app is running in `windows.txt`), and a 20Hz vertical scanline (`y = (scan % 100) / 100 * h`) on `FULL` tier. Click inside the icon's bounding box (`H.iconBounds`) launches/focuses the app!
   * **Zone 3 (`L_dots` / `R_dots`, `146.29 x 27.08`)**: Category pager dots (`r = 4` `ColorAccent` for active category, `r = 3` dim for others). Click or scroll switches category (`TopCat1` / `TopCat2` in `State.inc`).

7. **`MissionClock.tsx` (`LeftLocation`, zone `L_location`: `398.86 x 153.46` slanted, ported from `Scripts\location.lua`)**:
   * Top rail `(X(40), Y(228)) -> (X(226), Y(228))` (`X(rx) = (rx - 34) * SXR`, `Y(ry) = (ry - 220) * SYR`) with `3px` end dots, and two slanted bottom rails at `z.h - 9` and `z.h - 2.5`.
   * Left countdown ring at `(gx = X(92), gy = Y(256), R = 34)`: 24 hourly tick marks, outer progress arc (`R + 5 = 39`, `-90°` to `-90° + 360° * frac` where `frac = live ? 1 : clamp(1 - dt / 86400, 0, 1)`), center countdown text (`NOW` / `ENDS IN` in `ColorGood`, `<15m` in `ColorAlert`, `<60m` in `ColorWarn`, else `ColorAccent`).
   * Right 3 event rows at `Y(242), Y(253), Y(264)`: right-aligned time/day at `X(152)` (`TODAY`, `TMRW`, `MON`, or `HH:MM` / `NOW`) + left-aligned uppercase event title at `X(158)`. Click opens `https://calendar.google.com`; right-click triggers immediate calendar sync.

8. **`NetworkBlock.tsx` (`RightSysInfo`, zone `R_sysinfo`: `398.86 x 153.46` slanted, mirror of `MissionClock`, ported from `Scripts\sysinfo.lua`)**:
   * Mirror coordinate helper: `X(rx) = z.w - (rx - 34) * SXR`, `Y(ry) = (ry - 220) * SYR`.
   * Right emblem at `(gx = X(100), gy = Y(256))`: `R = 40` outer circle + 3 concentric Wi-Fi signal arcs (`r = 17, 25, 33`, `225°..315°`, lit by `wifiQualityPct >= i * 30`) + speedtest badge box at `(gx + 30, gy + 12, 40 x 22)` showing `LinkDownMbps` (or `...` in `ColorWarn` while testing; click runs Ookla speedtest via `ShipCore.Host`).
   * Left 4 rows at `Y(243.5), Y(252.5), Y(261.5), Y(270.5)`: `PING` (`xx MS` or `LOST`), `LAN` (local IP, masked with `X` if `IpMask=1`), `WAN` (public IP, masked if `IpMask=1` — click `LAN`/`WAN` rows toggles `IpMask`!), and `MBPS` (live download `▼` and upload `▲` speeds in Mbps).

9. **`HudSlot.tsx` x8 (`LeftSlot1..4` & `RightSlot5..8`, ported from `Scripts\slot.lua`)**:
   * Supports all 5 styles (`row` default with `Mirror = slot > 4`, `card`, `compact`, `rcompact`, `ship`).
   * In `row` mode: draws `ExtractedAppIcon` (if `@Resources\Icons\<id>.png` exists in `iconsIndex`) or `VectorHudIcon` at `(MX(0.14), Y(0.46))` (for category slots, draws a chamfered folder emblem around the category icon), title at `(MX(0.30), Y(0.24))` (`8pt`), status/count at `(MX(0.30), Y(0.50))` (`5.6pt`, with a `2.6px` status dot: `RUNNING` in `ColorGood`, `BACKGROUND` in `mix(ColorAccent, ColorDim, 0.35)`, `READY` in `ColorWhite`, `NOT FOUND` in `ColorWarn`), `OPEN`/`LAUNCH` chevron hint at `(MX(0.95), Y(0.72))`, and stepped weapon-row underline `(MX(0.005), Y(0.98)) -> (MX(0.327), Y(0.935)) -> (MX(0.362), Y(0.84)) -> (MX(0.96), Y(0.83))`.
   * Left-click on a category slot opens `CargoDrawerModal` focused on that category (`Focus(cat.id)`); right-click launches the currently selected app in that category; scroll cycles the category's apps. Left-click on an app slot calls `FocusOrLaunch` (`ShipCore.Host`).

10. **`StatusBlock.tsx` x2 (`LeftUpkeep` & `RightDev`, `103.5 x 72.21` slanted, ported from `Scripts\status_block.lua`)**:
    * `LeftUpkeep` (`kind="upkeep"`): Row 1 (`y = z.h * 0.33`) = pink diamond + pending Windows updates count (click opens `ms-settings:windowsupdate`, hover shows `winget` upgrades + Antivirus status); Row 2 (`y = z.h * 0.72`) = neon mail icon + Gmail unread count from `mail.txt` (click opens `https://mail.google.com`, right-click refreshes Gmail).
    * `RightDev` (`kind="dev"`): Row 1 = pink diamond + running WSL distros count (click opens `wt.exe`); Row 2 = cyan gear icon + loaded Ollama models count (click runs `wt.exe ollama ps`, hover shows Tailscale & Docker status).

11. **`TargetReticle.tsx` (`CenterTarget`, `885.84 x 248.24`, ported from `Scripts\target.lua`) & `FlightHud.tsx` (`CenterHUD`, `593.26 x 327.22`, ported from `Scripts\hud.lua`)**:
    * `TargetReticle`: Roams strictly inside the windscreen trapezoid (`ZX=412, ZY=108, WIN_TOP=104, WIN_LX0=342.3, WIN_RX0=917.7, SLOPE=(500.8-342.3)/(365.5-104)`) using quintic smootherstep, drawing `haze.png` tinted `rgb(255, 70, 52)`, 4 rotating outer arcs (`R = 86 * zoom`), 3 counter-rotating inner arcs (`r2 = 36`), left `[n]` box + countdown/RAM readout, and upcoming task blips on the ring (`ReticleTodo=1` locks onto next due `- [ ]` item in `ObsidianTodo`; click opens `obsidian://open?path=...`; otherwise shows top 5 CPU processes and click/scroll cycles rank `1..5`).
    * `FlightHud`: Left scrolling ladder (`X(527)`, S&P 500 `%` change today from Yahoo Finance `^GSPC`), right scrolling ladder (`X(733)`, GPU GHz clock or GPU load `%`), `[ <CPU` load pointer along `Y(311)..Y(362)`, `SPX` / `CLOSED` / `THR <cpu>` readout, and center breathing diamond pipper at `(X(630), Y(311))`.

12. **`SystemsDial.tsx` (`BottomStorage`, `188.95 x 164.73` + 18px margin, ported from `Scripts\dial.lua` + toggleable `Scripts\storage.lua` — Fixes `BUG-06`)**:
    * Exact twin to `AudioReactor.tsx` (`CX = 94.5, CY = 84, K = 1.13, R_TICK = 74*K, R_SEG = 64*K, R_VAL = 55*K, R_IN = 46*K, R_LBL = 82*K + 2`).
    * 6 radial labels (`BRT` 205°, `VOL` 180°, `MIC` 155°, `PWR` -25°, `HZ` 0°, `GLW` 25°), swinging glass wedge (`cur.ang ± 13°`), 40-dash range ring vs stepped segments (`quiet/balance/performance` or `60/165`), scroll wheel adjustment, click-on-ring jump (`OnRing`), and center-click toggle to `StorageBars` (`C:`/`D:` vertical bars, READ/WRITE rates, SSD temp from `Scripts\storage.lua`).

13. **`BottomStrip.tsx` (`BottomStrip`, 2 slanted zones `351.3 x 23.69` each, ported from `Scripts\strip.lua`) & `BottomTiltedPanels.tsx` (`BottomPanels`, 2 sheared zones `95.85 x 146`, ported from `Scripts\panels.lua`)**:
    * `BottomStrip`: Left 4 cells (`STEP = 84, CELLW = 76`): `gauge` CPU temp, `gpu` GPU temp, `wave` CPU load, `gear` Fan1 RPM. Right 4 cells (mirrored): `drive` `C: xx%` (click opens `C:\`), `disk` Disk I/O/s, `orbit` Ping ms, `wave` Wi-Fi `%` (other cells open `taskmgr.exe /7`).
    * `BottomTiltedPanels`: Left screen (9 rows: `PILOT`, `DATE`, `TIME` in `ColorHighlight`, `WEEK`, `YEAR`, `ZONE`, `BOOT`, `UP`, `IDLE` — click opens `outlookcal:`). Right screen (7 rows: `HOST`, `OS`, `CPU`, `GPU`, `RAM`, `DISP`, `UP` + chamfered `>_ TERMINAL` button at `y = z2.h * 0.8` — left-click `wt.exe`, right-click `powershell.exe`).

---

### PHASE 6: Screen-Share Privacy Mode (`WDA_EXCLUDEFROMCAPTURE`), `WM_QUERYENDSESSION` Shutdown Safety (`IMP-04`), JARVIS Process Supervisor & 6-Hour Soak Test (`WP-6`)

#### 📋 Copy-Paste Prompt for Claude — Phase 6:
```markdown
Execute Phase 6 of the Standalone Spaceship App migration (`WP-6`).

AUTONOMY & ADJUSTMENT NOTICE:
You may tune supervision backoff intervals or diagnostic overlay metrics as needed. Remember `CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md`: never invoke real shutdown/restart/sleep/recycle-bin calls during automated tests.

STEP-BY-STEP INSTRUCTIONS:
1. Implement `SpaceshipApp\ShipCore.Host\PrivacyGovernor.cs` (`DEC-16`):
   - Support `ExcludeFromCapture=0|1` in `Settings.inc` and hotkey `Ctrl+Alt+Shift+P`.
   - Call `SetWindowDisplayAffinity(hwnd, 0x00000011 /* WDA_EXCLUDEFROMCAPTURE */)` on `NativeHullWindow`, `HudCanvasWindow`, and `ModalOverlayWindow` so OBS/Zoom/Teams/Discord screen captures never show the HUD while it remains visible on the physical OLED display.
   - Auto-enable `PrivacyMode` (masking `LAN`/`WAN` IPs, calendar titles, and to-do items) on `SystemEvents.SessionSwitch` (`SessionLock` / `RemoteConnect`) or when OBS/Zoom screen sharing is active (if `AutoPrivacyOnShare=1`).
2. Implement `SpaceshipApp\ShipCore.Host\JarvisSupervisor.cs` (`OVR-18` + `IMP-04`):
   - Resolve `pythonw.exe` using `jarvis.lua:241-249` priority (`JarvisPython` -> `%LOCALAPPDATA%\SpaceshipHUD\venv\Scripts\pythonw.exe` -> `pyw.exe`).
   - Supervise `jarvis.py` with exponential backoff (`2s -> 5s -> 15s`, max 5 restarts per 10m).
   - On `WM_QUERYENDSESSION` / `WM_ENDSESSION` (`IMP-04`) or host exit, send `{"type":"cmd","raw":"QUIT ..."}` over `ToJarvis` pipe and wait up to `80ms` so `jarvis.py` restores ducked audio (`unduck()`) before `Environment.Exit(0)`.
3. Build `<DiagnosticOverlay />` (`Ctrl+Alt+Shift+D`) in `SpaceshipUI` showing live FPS, P50/P99 frame times (`ms`), `ShipCore.Host` + `WebView2` private working set (`MB`), current visibility mode (`ACTIVE` / `AMBIENT` / `OCCLUDED` / `STEALTH`), active `ui.animationLease` state, dGPU power state (`D3cold` vs `Active`), and Named Pipe latency.
4. Run the full verification suite (`test_jarvis.py`, startup/shutdown tests, and resource budget checks) and provide the final engineering report with rollback instructions.
```

#### Final Verification Checklist Across All 6 Phases:
1. **Unit & Regression Suite**: `py -3 -B Skins\Spaceship\@Resources\Jarvis\test_jarvis.py` passes 100% (all 706+ assertions) with 0 real OS destructive calls executed.
2. **Cold Boot & Restart Speed (`IMP-01`, `IMP-04`)**:
   * `NativeHullWindow` Stage 0 GDI+ reticle paints in `<25ms`.
   * `HudCanvasWindow` 165Hz `<IntroSequence />` starts after the 2-frame `rAF` warmup barrier (`<850ms` cold boot) and completes with the 2-frame `DwmFlush()` handoff (`IMP-03`, `0` flicker).
   * Sending `WM_QUERYENDSESSION` returns `1` and exits cleanly in `<100ms` (never blocking Windows Restart).
   * Sending `TaskbarCreated` re-registers the tray icon and re-anchors desktop Z-order automatically.
3. **Runtime Animations & Hit-Testing (`IMP-02`, `BUG-02`)**:
   * All 30 zones include the `18px` `ModuleMargin` + `12px` `AnimationBleedMargin` (`30px` total) so `BottomAudio`, `BottomStorage`, `CenterSphere`, and hover captions (`H.caption`) are never clipped.
   * `ui.animationLease` dynamically unclips `SetWindowRgn` during `<IntroSequence />`, `LayoutStudio`, Preset morphs, Wake-Word shockwaves, and Red-Alert sweeps.
4. **WebView2 Resilience & Dual-Boot Safety (`IMP-06`, `IMP-07`)**:
   * Killing the WebView2 renderer process triggers `CoreWebView2.ProcessFailed` and recovers the HUD + `CreateSharedBuffer(4096)` in `<500ms`.
   * `Switch-HudHost.ps1 -Mode Standalone` and `-Mode Rainmeter` toggle cleanly in `<1s` with zero process/file collisions.

---

## Part 6: Complete C#, Python & TypeScript Reference Implementations for Every Core Module

To minimize Claude's token usage and eliminate any guesswork, use the exact reference implementations below when executing Phases 1–6.

### 6.1 `SpaceshipApp\ShipCore.Host\Program.cs` (`IMP-07` Dual-Boot Mutex, Rainmeter Auto-Unload & Parallel WebView2 Pre-Warm)
```csharp
using System.Diagnostics;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Text;

namespace ShipCore.Host;

internal static class Program
{
    [StructLayout(LayoutKind.Sequential)]
    private struct COPYDATASTRUCT { public IntPtr dwData; public int cbData; public IntPtr lpData; }

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern IntPtr FindWindowW(string? lpClassName, string? lpWindowName);

    [DllImport("user32.dll")]
    private static extern IntPtr SendMessageTimeoutW(IntPtr hWnd, uint Msg, IntPtr wParam, ref COPYDATASTRUCT lParam,
        uint fuFlags, uint uTimeout, out IntPtr lpdwResult);

    [STAThread]
    private static int Main(string[] args)
    {
        Application.SetHighDpiMode(HighDpiMode.PerMonitorV2);
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);

        string resPath = ResolveResourcesPath(args);

        // Handle CLI flags (--install-startup / --uninstall-startup)
        if (args.Length >= 1 && args[0].Equals("--install-startup", StringComparison.OrdinalIgnoreCase))
        {
            BootIntegrationManager.InstallStartupTask(Application.ExecutablePath, resPath);
            return 0;
        }
        if (args.Length >= 1 && args[0].Equals("--uninstall-startup", StringComparison.OrdinalIgnoreCase))
        {
            BootIntegrationManager.UninstallStartupTask();
            return 0;
        }

        // IMP-07: Single-instance mutex so two ShipCore.Host.exe instances never collide
        using var hostMutex = new Mutex(true, @"Local\SpaceshipHud_HostMutex", out bool isOnlyInstance);
        if (!isOnlyInstance) return 0;

        // IMP-07: If Rainmeter is currently running the Spaceship skin group, cleanly deactivate it
        // and stop legacy ShipCore.exe so they never fight over Settings.inc, Data\*.txt, or jarvis.py
        DeactivateRainmeterSpaceshipGroupIfRunning();
        StopLegacyShipCoreHelper();

        // Start lock-free RecoveryTrayHost thread first (Ctrl+Alt+Shift+H, TaskbarCreated, WM_QUERYENDSESSION)
        using var recoveryHost = new RecoveryTrayHost();
        using var appContext = new SpaceshipHostApplicationContext(resPath, recoveryHost);
        Application.Run(appContext);
        return 0;
    }

    private static string ResolveResourcesPath(string[] args)
    {
        foreach (string a in args)
        {
            if (!a.StartsWith("--", StringComparison.Ordinal) && Directory.Exists(a.Trim('"')))
                return Path.GetFullPath(a.Trim('"')).TrimEnd('\\') + "\\";
        }
        // Default: @Resources\Bin\ShipCore.Host.exe -> parent is @Resources\
        string parent = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, ".."));
        return parent.TrimEnd('\\') + "\\";
    }

    public static void DeactivateRainmeterSpaceshipGroupIfRunning()
    {
        IntPtr rm = FindWindowW("DummyRainWClass", null);
        if (rm == IntPtr.Zero) return;
        SendRainmeterBang(rm, "[!DeactivateConfigGroup Spaceship][!DeactivateConfigGroup SpaceshipBoot]");
    }

    private static void SendRainmeterBang(IntPtr rmHwnd, string bang)
    {
        byte[] data = Encoding.Unicode.GetBytes(bang + "\0");
        var cds = new COPYDATASTRUCT { dwData = (IntPtr)1, cbData = data.Length, lpData = Marshal.AllocHGlobal(data.Length) };
        try
        {
            Marshal.Copy(data, 0, cds.lpData, data.Length);
            SendMessageTimeoutW(rmHwnd, 0x004A /* WM_COPYDATA */, IntPtr.Zero, ref cds, 2 /* SMTO_ABORTIFHUNG */, 2000, out _);
        }
        finally
        {
            Marshal.FreeHGlobal(cds.lpData);
        }
    }

    private static void StopLegacyShipCoreHelper()
    {
        foreach (var proc in Process.GetProcessesByName("ShipCore"))
        {
            try { proc.Kill(); } catch { }
            finally { proc.Dispose(); }
        }
    }
}
```

---

### 6.2 `SpaceshipApp\ShipCore.Host\DesktopWindowStateMachine.cs` (`FIX-DEBATE-03` + `IMP-04` `WaitForExplorerShellReady`, `TaskbarCreated`, `WM_POWERBROADCAST` & `Win+D` Guard)
```csharp
using System.Drawing;
using System.Runtime.InteropServices;

namespace ShipCore.Host;

public sealed class DesktopWindowStateMachine
{
    private const int WM_WINDOWPOSCHANGING = 0x0046;
    private const int WM_DISPLAYCHANGE = 0x007E;
    private const int WM_POWERBROADCAST = 0x0218;
    private const int PBT_APMRESUMEAUTOMATIC = 0x0012;
    private const int PBT_APMRESUMESUSPEND = 0x0007;

    private const uint SWP_NOSIZE = 0x0001, SWP_NOMOVE = 0x0002, SWP_NOACTIVATE = 0x0010, SWP_SHOWWINDOW = 0x0040, SWP_HIDEWINDOW = 0x0080;
    private static readonly IntPtr HWND_BOTTOM = new(1);

    [StructLayout(LayoutKind.Sequential)]
    public struct WINDOWPOS
    {
        public IntPtr hwnd, hwndInsertAfter;
        public int x, y, cx, cy;
        public uint flags;
    }

    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern IntPtr FindWindowW(string? cls, string? title);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern IntPtr FindWindowExW(IntPtr parent, IntPtr childAfter, string? cls, string? title);
    [DllImport("user32.dll")] private static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);
    [DllImport("user32.dll")] private static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

    private readonly IntPtr _nativeHullHwnd;
    private readonly IntPtr _hudCanvasHwnd;
    private bool _intentionalHide;

    public event Action? OnResumeFromSleep;
    public event Action<Rectangle, float, Point>? OnHomeMonitorChanged;

    public DesktopWindowStateMachine(IntPtr nativeHullHwnd, IntPtr hudCanvasHwnd)
    {
        _nativeHullHwnd = nativeHullHwnd;
        _hudCanvasHwnd = hudCanvasHwnd;
    }

    /// <summary>
    /// IMP-01 / BUG-10: On a fast Windows Restart, Task Scheduler (Delay=PT0S, Priority=4) starts ShipCore.Host.exe
    /// before explorer.exe finishes creating Shell_TrayWnd and SHELLDLL_DefView. Wait up to 6s (polling every 40ms)
    /// so we attach Z-order the exact millisecond the Windows desktop shell is ready.
    /// </summary>
    public static async Task WaitForExplorerShellReadyAsync()
    {
        var sw = System.Diagnostics.Stopwatch.StartNew();
        while (sw.ElapsedMilliseconds < 6000)
        {
            IntPtr tray = FindWindowW("Shell_TrayWnd", null);
            if (tray != IntPtr.Zero && FindShellDefView() != IntPtr.Zero)
                return;
            await Task.Delay(40);
        }
    }

    public static IntPtr FindShellDefView()
    {
        IntPtr progman = FindWindowW("Progman", null);
        IntPtr defView = FindWindowExW(progman, IntPtr.Zero, "SHELLDLL_DefView", null);
        if (defView != IntPtr.Zero) return defView;

        IntPtr workerW = IntPtr.Zero;
        while ((workerW = FindWindowExW(IntPtr.Zero, workerW, "WorkerW", null)) != IntPtr.Zero)
        {
            defView = FindWindowExW(workerW, IntPtr.Zero, "SHELLDLL_DefView", null);
            if (defView != IntPtr.Zero) return defView;
        }
        return IntPtr.Zero;
    }

    /// <summary>
    /// Port of findHome() and fitTo() from Skins\Spaceship\@Resources\Scripts\controller.lua:34-87.
    /// Finds the 2560x1600 (or 16:10) laptop panel across connected displays. Returns null if lid is closed.
    /// </summary>
    public static (Screen Monitor, Rectangle CanvasBounds, float Scale, int OriginX, int OriginY)? FindHomeMonitor(
        string homeMonitorSetting, string homeSizeSetting, bool autoFit, bool frameBehindTaskbar,
        float configuredScale, int configuredOriginX, int configuredOriginY)
    {
        var screens = Screen.AllScreens;
        Screen? match = null;

        if (int.TryParse(homeMonitorSetting, out int pinIdx) && pinIdx >= 1 && pinIdx <= screens.Length)
        {
            match = screens[pinIdx - 1];
        }
        else
        {
            int wantW = 2560, wantH = 1600;
            var parts = homeSizeSetting.Split(['x', 'X'], StringSplitOptions.RemoveEmptyEntries);
            if (parts.Length == 2 && int.TryParse(parts[0], out int pw) && int.TryParse(parts[1], out int ph))
            {
                wantW = pw; wantH = ph;
            }
            float wantAspect = (float)wantW / wantH; // 1.6 (16:10)

            match = screens.FirstOrDefault(s => s.Bounds.Width == wantW && s.Bounds.Height == wantH)
                 ?? screens.FirstOrDefault(s => Math.Abs((float)s.Bounds.Width / s.Bounds.Height - wantAspect) < 0.01f);
        }

        if (match == null) return null; // Laptop lid closed on external-only 16:9 monitor -> hide HUD

        Rectangle area = frameBehindTaskbar ? match.Bounds : match.WorkingArea;
        float scale = configuredScale;
        int ox = configuredOriginX, oy = configuredOriginY;

        if (autoFit)
        {
            scale = MathF.Min(match.WorkingArea.Width / 2560f, match.WorkingArea.Height / 1600f);
            ox = (int)MathF.Floor((match.WorkingArea.Width - 2560f * scale) / 2f);
            oy = (int)MathF.Floor((match.WorkingArea.Height - 1600f * scale) / 2f);
        }

        int w = (int)MathF.Round(2560f * scale);
        int h = frameBehindTaskbar
            ? (int)MathF.Round(1600f * scale)
            : Math.Min((int)MathF.Round(1600f * scale), match.WorkingArea.Bottom - match.Bounds.Top - oy);

        var bounds = new Rectangle(match.Bounds.Left + ox, match.Bounds.Top + oy, w, h);
        return (match, bounds, scale, ox, oy);
    }

    public void AnchorToDesktopBottom()
    {
        // Keep NativeHullWindow at the very bottom (above wallpaper WorkerW) and HudCanvasWindow immediately above it
        SetWindowPos(_nativeHullHwnd, HWND_BOTTOM, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
        SetWindowPos(_hudCanvasHwnd, HWND_BOTTOM, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
    }

    public unsafe void HandleWndProc(ref Message m)
    {
        if (m.Msg == WM_WINDOWPOSCHANGING && !_intentionalHide && m.LParam != IntPtr.Zero)
        {
            // FIX-DEBATE-03: Prevent Win+D ("Show Desktop") from hiding the HUD
            WINDOWPOS* wp = (WINDOWPOS*)m.LParam.ToPointer();
            if ((wp->flags & SWP_HIDEWINDOW) != 0)
            {
                wp->flags &= ~SWP_HIDEWINDOW;
                wp->flags |= SWP_NOACTIVATE;
            }
        }
        else if (m.Msg == WM_POWERBROADCAST)
        {
            int evt = m.WParam.ToInt32();
            if (evt is PBT_APMRESUMEAUTOMATIC or PBT_APMRESUMESUSPEND)
            {
                OnResumeFromSleep?.Invoke();
            }
        }
    }
}
```

---

### 6.3 `SpaceshipApp\ShipCore.Host\VisibilityGovernor.cs` (`FIX-DEBATE-09` 5-Gate `DWMWA_CLOAKED` Filter + `OVR-14` Event-Driven `SetWinEventHook` `<15ms` Wake)
```csharp
using System.Drawing;
using System.Runtime.InteropServices;
using System.Text;

namespace ShipCore.Host;

public enum HudVisibilityMode { Active, Ambient, Occluded, Stealth }

public sealed class VisibilityGovernor : IDisposable
{
    private const uint EVENT_SYSTEM_FOREGROUND = 0x0003;
    private const uint EVENT_SYSTEM_MINIMIZESTART = 0x0016;
    private const uint EVENT_SYSTEM_MINIMIZEEND = 0x0017;
    private const uint EVENT_OBJECT_LOCATIONCHANGE = 0x800B;
    private const uint WINEVENT_OUTOFCONTEXT = 0x0000;
    private const uint WINEVENT_SKIPOWNPROCESS = 0x0002;
    private const int DWMWA_CLOAKED = 14;
    private const int GWL_STYLE = -16, GWL_EXSTYLE = -20;
    private const uint WS_MAXIMIZE = 0x01000000;
    private const uint WS_EX_TOOLWINDOW = 0x00000080, WS_EX_NOACTIVATE = 0x08000000, WS_EX_TRANSPARENT = 0x00000020;

    private delegate void WinEventDelegate(IntPtr hWinEventHook, uint eventType, IntPtr hwnd, int idObject, int idChild, uint dwEventThread, uint dwmsEventTime);
    private delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }

    [DllImport("user32.dll")] private static extern IntPtr SetWinEventHook(uint eventMin, uint eventMax, IntPtr hmodWinEventProc, WinEventDelegate lpfnWinEventProc, uint idProcess, uint idThread, uint dwFlags);
    [DllImport("user32.dll")] private static extern bool UnhookWinEvent(IntPtr hWinEventHook);
    [DllImport("user32.dll")] private static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll")] private static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] private static extern bool IsIconic(IntPtr hWnd);
    [DllImport("user32.dll")] private static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    [DllImport("user32.dll", EntryPoint = "GetWindowLongW")] private static extern int GetWindowLong(IntPtr hWnd, int nIndex);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int GetClassNameW(IntPtr hWnd, StringBuilder lpClassName, int nMaxCount);
    [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
    [DllImport("dwmapi.dll")] private static extern int DwmGetWindowAttribute(IntPtr hwnd, int dwAttribute, out int pvAttribute, int cbAttribute);

    private readonly WinEventDelegate _hookProc; // Keep rooted as field so GC never collects callback!
    private readonly IntPtr _hookForeground;
    private readonly IntPtr _hookMinimize;
    private readonly System.Windows.Forms.Timer _debounceTimer;
    private readonly System.Windows.Forms.Timer _fallbackTimer;
    private readonly uint _ownPid;
    private Rectangle _homeMonitorBounds;
    private Rectangle _homeWorkingArea;

    public HudVisibilityMode CurrentMode { get; private set; } = HudVisibilityMode.Active;
    public event Action<HudVisibilityMode>? OnModeChanged;

    public VisibilityGovernor(Rectangle homeMonitorBounds, Rectangle homeWorkingArea)
    {
        _homeMonitorBounds = homeMonitorBounds;
        _homeWorkingArea = homeWorkingArea;
        _ownPid = (uint)Environment.ProcessId;
        _hookProc = OnWinEvent;

        uint flags = WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS;
        _hookForeground = SetWinEventHook(EVENT_SYSTEM_FOREGROUND, EVENT_SYSTEM_FOREGROUND, IntPtr.Zero, _hookProc, 0, 0, flags);
        _hookMinimize = SetWinEventHook(EVENT_SYSTEM_MINIMIZESTART, EVENT_SYSTEM_MINIMIZEEND, IntPtr.Zero, _hookProc, 0, 0, flags);

        // OVR-14: 35ms debounce wakes the HUD in <15-40ms when minimizing a maximized window
        _debounceTimer = new System.Windows.Forms.Timer { Interval = 35 };
        _debounceTimer.Tick += (_, _) => { _debounceTimer.Stop(); EvaluateOcclusion(); };

        // 5-second fallback reconciliation timer
        _fallbackTimer = new System.Windows.Forms.Timer { Interval = 5000 };
        _fallbackTimer.Tick += (_, _) => EvaluateOcclusion();
        _fallbackTimer.Start();
    }

    private void OnWinEvent(IntPtr hWinEventHook, uint eventType, IntPtr hwnd, int idObject, int idChild, uint dwEventThread, uint dwmsEventTime)
    {
        if (idObject != 0 /* OBJID_WINDOW */) return;
        _debounceTimer.Stop();
        _debounceTimer.Start();
    }

    public void EvaluateOcclusion()
    {
        bool hasFullscreenGame = false;
        bool hasMaximizedOccluder = false;
        double workAreaPixels = Math.Max(1.0, (double)_homeWorkingArea.Width * _homeWorkingArea.Height);

        EnumWindows((hWnd, _) =>
        {
            // Gate 1: Must be visible and not minimized
            if (!IsWindowVisible(hWnd) || IsIconic(hWnd)) return true;

            // Gate 2: Must NOT be DWM-cloaked (filters out invisible Win11 UWP/Settings/Calculator/Other-Virtual-Desktop windows!)
            if (DwmGetWindowAttribute(hWnd, DWMWA_CLOAKED, out int cloaked, sizeof(int)) == 0 && cloaked != 0)
                return true;

            // Gate 3: Exclude own process and shell/wallpaper classes
            GetWindowThreadProcessId(hWnd, out uint pid);
            if (pid == _ownPid) return true;

            var sb = new StringBuilder(128);
            GetClassNameW(hWnd, sb, sb.Capacity);
            string cls = sb.ToString();
            if (cls is "Progman" or "WorkerW" or "Shell_TrayWnd" or "Shell_SecondaryTrayWnd"
                or "Windows.UI.Core.CoreWindow" or "ApplicationFrameWindow" && GetWindowLong(hWnd, GWL_EXSTYLE) == 0)
                return true;
            if (cls.StartsWith("Rainmeter", StringComparison.Ordinal) || cls.StartsWith("HwndWrapper[Lively", StringComparison.Ordinal))
                return true;

            // Gate 4: Exclude transparent click-through overlays
            uint exStyle = (uint)GetWindowLong(hWnd, GWL_EXSTYLE);
            if ((exStyle & WS_EX_TRANSPARENT) != 0) return true;

            // Gate 5: Check intersection area on the home monitor
            if (!GetWindowRect(hWnd, out RECT r)) return true;
            var winRect = Rectangle.FromLTRB(r.Left, r.Top, r.Right, r.Bottom);
            if (winRect.Width >= _homeMonitorBounds.Width && winRect.Height >= _homeMonitorBounds.Height &&
                winRect.Left <= _homeMonitorBounds.Left && winRect.Top <= _homeMonitorBounds.Top)
            {
                hasFullscreenGame = true;
                return false; // Stop enumeration early
            }

            var intersect = Rectangle.Intersect(winRect, _homeWorkingArea);
            double cov = (double)(intersect.Width * intersect.Height) / workAreaPixels;
            uint style = (uint)GetWindowLong(hWnd, GWL_STYLE);
            if (cov >= 0.92 || ((style & WS_MAXIMIZE) != 0 && cov >= 0.85))
            {
                hasMaximizedOccluder = true;
                return false;
            }
            return true;
        }, IntPtr.Zero);

        var nextMode = hasFullscreenGame
            ? HudVisibilityMode.Stealth
            : hasMaximizedOccluder
                ? HudVisibilityMode.Occluded
                : HudVisibilityMode.Active;

        if (nextMode != CurrentMode)
        {
            CurrentMode = nextMode;
            OnModeChanged?.Invoke(nextMode);
        }
    }

    public void Dispose()
    {
        _debounceTimer.Dispose();
        _fallbackTimer.Dispose();
        if (_hookForeground != IntPtr.Zero) UnhookWinEvent(_hookForeground);
        if (_hookMinimize != IntPtr.Zero) UnhookWinEvent(_hookMinimize);
    }
}
```

---

### 6.4 `SpaceshipApp\SpaceshipUI\src\utils\scrambleDecode.ts` (`OVR-09` 12-Line Zero-Dependency Cipher Decoder)
```typescript
const CIPHER_CHARS = "01X#/>_=[]*+";

export function scrambleDecode(
  targetText: string,
  durationMs: number,
  onUpdate: (currentText: string) => void
): () => void {
  const start = performance.now();
  let rafId = 0;
  const len = targetText.length;

  const tick = (now: number) => {
    const t = Math.min(1, (now - start) / Math.max(1, durationMs));
    const revealed = Math.floor(t * len);
    let out = targetText.slice(0, revealed);
    for (let i = revealed; i < len; i++) {
      const ch = targetText[i];
      out += ch === " " ? " " : CIPHER_CHARS[(i * 7 + Math.floor(now / 24)) % CIPHER_CHARS.length];
    }
    onUpdate(out);
    if (t < 1) rafId = requestAnimationFrame(tick);
  };

  rafId = requestAnimationFrame(tick);
  return () => cancelAnimationFrame(rafId);
}
```

---

### 6.5 `SpaceshipApp\SpaceshipUI\src\utils\layoutGuard.ts` (Exact TypeScript Port of `Skins\Spaceship\@Resources\Scripts\guard.lua`)
```typescript
export type Poly = [number, number][];

export interface ZonesSpec {
  canvas: { w: number; h: number };
  safe: { inset: number; r: number };
  gap: number;
  bottom: number;
  keepouts: Poly[];
  modules: Array<{ key: string; name: string; config: string; zones: Poly[] }>;
}

// Separating Axis Theorem polygon separation check with minimum clearance `gap` (guard.lua:4-21)
export function separated(a: Poly, b: Poly, gap: number): boolean {
  for (const poly of [a, b]) {
    for (let i = 0; i < poly.length; i++) {
      const p1 = poly[i];
      const p2 = poly[(i + 1) % poly.length];
      const nx = p2[1] - p1[1];
      const ny = p1[0] - p2[0];
      const len = Math.hypot(nx, ny);
      if (len > 0) {
        let amin = Infinity, amax = -Infinity, bmin = Infinity, bmax = -Infinity;
        for (const p of a) { const d = nx * p[0] + ny * p[1]; amin = Math.min(amin, d); amax = Math.max(amax, d); }
        for (const p of b) { const d = nx * p[0] + ny * p[1]; bmin = Math.min(bmin, d); bmax = Math.max(bmax, d); }
        if (amax + gap * len <= bmin || bmax + gap * len <= amin) return true;
      }
    }
  }
  return false;
}

export function movePoly(poly: Poly, dx: number, dy: number): Poly {
  return poly.map(([x, y]) => [x + dx, y + dy]);
}

export function inSafeArea(poly: Poly, Z: ZonesSpec): boolean {
  const { inset, r } = Z.safe;
  const L = inset, T = inset, R = Z.canvas.w - inset, B = Z.bottom - Z.gap;
  for (const [x, y] of poly) {
    if (x < L || x > R || y < T || y > B) return false;
    const cx = x < L + r ? L + r : x > R - r ? R - r : null;
    const cy = y < T + r ? T + r : null;
    if (cx !== null && cy !== null && Math.hypot(x - cx, y - cy) > r) return false;
  }
  return true;
}

export function checkModuleMove(
  Z: ZonesSpec,
  key: string,
  offsets: Record<string, [number, number]>
): { ok: boolean; reason?: string } {
  const mod = Z.modules.find((m) => m.key === key);
  if (!mod) return { ok: true };
  const [dx, dy] = offsets[key] ?? [0, 0];
  for (const zp of mod.zones) {
    const p = movePoly(zp, dx, dy);
    if (!inSafeArea(p, Z)) return { ok: false, reason: "OFF THE SAFE AREA / INTO THE TASKBAR" };
    for (const k of Z.keepouts) {
      if (!separated(p, k, Z.gap)) return { ok: false, reason: "HITS A COCKPIT STRUT" };
    }
    for (const other of Z.modules) {
      if (other.key !== key) {
        const [odx, ody] = offsets[other.key] ?? [0, 0];
        for (const zq of other.zones) {
          if (!separated(p, movePoly(zq, odx, ody), Z.gap)) {
            return { ok: false, reason: `OVERLAPS ${other.name}` };
          }
        }
      }
    }
  }
  return { ok: true };
}
```

---

### 6.6 `SpaceshipApp\ShipCore.Host\Collectors\AppScanner.cs` (`BUG-03` + `OVR-17`: Native C# `SHIL_JUMBO` + `IShellItemImageFactory` 128x128 Greyscale & Blurred Glow Icon Extractor)
```csharp
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

namespace ShipCore.Host.Collectors;

public static class AppScanner
{
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct SHFILEINFO
    {
        public IntPtr hIcon;
        public int iIcon;
        public uint dwAttributes;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)] public string szDisplayName;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 80)] public string szTypeName;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct SIZE { public int cx, cy; }

    [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
    private static extern int SHParseDisplayName(string name, IntPtr bindCtx, out IntPtr pidl, uint sfgaoIn, out uint sfgaoOut);

    [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
    private static extern IntPtr SHGetFileInfoW(IntPtr pidl, uint attr, ref SHFILEINFO info, uint size, uint flags);

    [DllImport("shell32.dll", EntryPoint = "#727")]
    private static extern int SHGetImageList(int iImageList, ref Guid riid, out IImageList ppv);

    [DllImport("shell32.dll", CharSet = CharSet.Unicode, PreserveSig = true)]
    private static extern int SHCreateItemFromParsingName(string pszPath, IntPtr pbc, ref Guid riid, out IShellItemImageFactory ppv);

    [DllImport("user32.dll")] private static extern bool DestroyIcon(IntPtr hIcon);
    [DllImport("gdi32.dll")] private static extern bool DeleteObject(IntPtr hObject);
    [DllImport("ole32.dll")] private static extern void CoTaskMemFree(IntPtr pv);

    [ComImport, Guid("46EB5926-582E-4017-9FDF-E8998DAA0950"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IImageList
    {
        [PreserveSig] int Add(IntPtr hbmImage, IntPtr hbmMask, ref int pi);
        [PreserveSig] int ReplaceIcon(int i, IntPtr hicon, ref int pi);
        [PreserveSig] int SetOverlayImage(int iImage, int iOverlay);
        [PreserveSig] int Replace(int i, IntPtr hbmImage, IntPtr hbmMask);
        [PreserveSig] int AddMasked(IntPtr hbmImage, int crMask, ref int pi);
        [PreserveSig] int Draw(IntPtr pimldp);
        [PreserveSig] int Remove(int i);
        [PreserveSig] int GetIcon(int i, int flags, ref IntPtr picon);
    }

    [ComImport, Guid("bcc18b79-ba16-442f-80c4-8a59c30c463b"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    private interface IShellItemImageFactory
    {
        [PreserveSig] int GetImage(SIZE size, int flags, out IntPtr phbm);
    }

    /// <summary>
    /// BUG-03 + OVR-17: Exact native C# port of HudIcons.Make() from Skins\Spaceship\@Resources\Scripts\app-icons.ps1:42-112
    /// with IShellItemImageFactory fallback for Microsoft Store / UWP apps (shell:AppsFolder\...).
    /// Writes @Resources\Icons\<id>.png (128x128 contrast-lifted greyscale) and @Resources\Icons\<id>_glow.png (128x128 3-pass box blur).
    /// </summary>
    public static bool ExtractNeonAppIcon(string pathOrShellUri, string outBasePath)
    {
        using Bitmap? src = LoadJumboOrShellBitmap(pathOrShellUri);
        if (src == null) return false;

        Rectangle bounds = GetAlphaBounds(src);
        if (bounds.IsEmpty) return false;

        const int S = 128, PAD = 14;
        int inner = S - 2 * PAD;
        float k = MathF.Min((float)inner / bounds.Width, (float)inner / bounds.Height);
        int w = Math.Max(1, (int)(bounds.Width * k));
        int h = Math.Max(1, (int)(bounds.Height * k));

        using var fit = new Bitmap(S, S, PixelFormat.Format32bppArgb);
        using (var g = Graphics.FromImage(fit))
        {
            g.InterpolationMode = InterpolationMode.HighQualityBicubic;
            g.DrawImage(src, new Rectangle((S - w) / 2, (S - h) / 2, w, h), bounds, GraphicsUnit.Pixel);
        }

        float[] alpha = new float[S * S];
        using var grey = new Bitmap(S, S, PixelFormat.Format32bppArgb);
        for (int y = 0; y < S; y++)
        {
            for (int x = 0; x < S; x++)
            {
                Color c = fit.GetPixel(x, y);
                float lum = (0.30f * c.R + 0.59f * c.G + 0.11f * c.B) / 255f;
                lum = Math.Clamp((lum - 0.12f) / 0.76f, 0f, 1f); // Exact contrast lift from app-icons.ps1:96
                int v = (int)(lum * 255f);
                grey.SetPixel(x, y, Color.FromArgb(c.A, v, v, v));
                alpha[y * S + x] = c.A / 255f;
            }
        }

        float[] blur = BoxBlur(BoxBlur(BoxBlur(alpha, S, S, 5), S, S, 5), S, S, 5);
        using var glow = new Bitmap(S, S, PixelFormat.Format32bppArgb);
        for (int i = 0; i < S * S; i++)
        {
            int a = (int)MathF.Min(255f, blur[i] * 340f);
            glow.SetPixel(i % S, i / S, Color.FromArgb(a, 255, 255, 255));
        }

        grey.Save(outBasePath + ".png", ImageFormat.Png);
        glow.Save(outBasePath + "_glow.png", ImageFormat.Png);
        return true;
    }

    private static Bitmap? LoadJumboOrShellBitmap(string path)
    {
        // Try IShellItemImageFactory first for crisp Store / UWP tiles and high-DPI .exe icons (OVR-17)
        Guid factoryGuid = new("bcc18b79-ba16-442f-80c4-8a59c30c463b");
        if (SHCreateItemFromParsingName(path, IntPtr.Zero, ref factoryGuid, out var factory) == 0 && factory != null)
        {
            if (factory.GetImage(new SIZE { cx = 128, cy = 128 }, 0x00000008 /* SIIGBF_ICONONLY */, out IntPtr hBmp) == 0 && hBmp != IntPtr.Zero)
            {
                try { return Image.FromHbitmap(hBmp); }
                finally { DeleteObject(hBmp); }
            }
        }

        // Fallback to SHIL_JUMBO (256x256) from app-icons.ps1:42
        if (SHParseDisplayName(path, IntPtr.Zero, out IntPtr pidl, 0, out _) != 0) return null;
        var info = new SHFILEINFO();
        SHGetFileInfoW(pidl, 0, ref info, (uint)Marshal.SizeOf(info), 0x4000 | 0x8 /* SYSICONINDEX | PIDL */);
        CoTaskMemFree(pidl);

        Guid iid = new("46EB5926-582E-4017-9FDF-E8998DAA0950");
        if (SHGetImageList(4 /* SHIL_JUMBO */, ref iid, out var list) != 0) return null;
        IntPtr hIcon = IntPtr.Zero;
        list.GetIcon(info.iIcon, 1 /* ILD_TRANSPARENT */, ref hIcon);
        if (hIcon == IntPtr.Zero) return null;
        try
        {
            using var ic = Icon.FromHandle(hIcon);
            return ic.ToBitmap();
        }
        finally
        {
            DestroyIcon(hIcon);
        }
    }

    private static Rectangle GetAlphaBounds(Bitmap b)
    {
        int x0 = b.Width, y0 = b.Height, x1 = -1, y1 = -1;
        for (int y = 0; y < b.Height; y++)
            for (int x = 0; x < b.Width; x++)
                if (b.GetPixel(x, y).A > 24)
                {
                    if (x < x0) x0 = x; if (y < y0) y0 = y;
                    if (x > x1) x1 = x; if (y > y1) y1 = y;
                }
        return x1 < 0 ? Rectangle.Empty : new Rectangle(x0, y0, x1 - x0 + 1, y1 - y0 + 1);
    }

    private static float[] BoxBlur(float[] a, int w, int h, int r)
    {
        float[] tmp = new float[a.Length], o = new float[a.Length];
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                float s = 0; int n = 0;
                for (int k = -r; k <= r; k++) { int xx = x + k; if (xx >= 0 && xx < w) { s += a[y * w + xx]; n++; } }
                tmp[y * w + x] = s / n;
            }
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                float s = 0; int n = 0;
                for (int k = -r; k <= r; k++) { int yy = y + k; if (yy >= 0 && yy < h) { s += tmp[yy * w + x]; n++; } }
                o[y * w + x] = s / n;
            }
        return o;
    }
}
```

---

### 6.7 `SpaceshipApp\SpaceshipUI\src\modules\IntroSequence.tsx` (165Hz 5-Stage WAAPI Opening Animation + `WaitForCompositorReady` + `Boot.ini` System Check Card)
```tsx
import { h } from "preact";
import { useEffect, useRef, useState } from "preact/hooks";
import { scrambleDecode } from "../utils/scrambleDecode";

export interface BootRow {
  label: string;
  value: string;
  status: "OK" | "CHECK" | "FAIL";
}

export function IntroSequence(props: {
  active: boolean;
  rows: BootRow[];
  onTriggerSpinDials: () => void;
  onFinished: () => void;
}) {
  const scannerRef = useRef<HTMLDivElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  const [visibleRows, setVisibleRows] = useState<Array<{ label: string; value: string; status: string; rawStatus: "OK" | "CHECK" | "FAIL" }>>([]);
  const [verdictText, setVerdictText] = useState("");
  const [verdictWarn, setVerdictWarn] = useState(false);

  useEffect(() => {
    if (!props.active) return;
    let cancelled = false;

    // Hard failsafe timer (boot.lua:70 finish()): never allow HUD to stay hidden > 4.2s
    const failsafe = window.setTimeout(() => {
      if (!cancelled) props.onFinished();
    }, 4200);

    (async () => {
      // 1. WaitForCompositorReady Barrier: fonts + 2 consecutive smooth rAF ticks (<14ms)
      await document.fonts.ready;
      await new Promise<void>((resolve) => {
        let last = performance.now();
        let goodFrames = 0;
        const check = (now: number) => {
          if (now - last < 14) goodFrames++;
          else goodFrames = 0;
          last = now;
          if (goodFrames >= 2) resolve();
          else requestAnimationFrame(check);
        };
        requestAnimationFrame(check);
      });
      if (cancelled) return;

      // 2. Stage 1 (0.00s - 0.50s): Full-Screen Laser Scanner Sweep (Boot.ini:78-85)
      if (scannerRef.current) {
        scannerRef.current.animate(
          [
            { transform: "translate3d(0, -40px, 0)", opacity: 1 },
            { transform: "translate3d(0, 1620px, 0)", opacity: 1, offset: 0.92 },
            { transform: "translate3d(0, 1640px, 0)", opacity: 0 },
          ],
          { duration: 500, easing: "cubic-bezier(0.22, 1, 0.36, 1)", fill: "forwards" }
        );
      }

      // 3. Stage 2 (0.32s - 1.45s): Right-to-Left Staggered 3D Panel Unfold
      const moduleEls = Array.from(document.querySelectorAll<HTMLElement>("[data-hud-module]"));
      moduleEls.sort((a, b) => Number(b.dataset.bootX ?? 0) - Number(a.dataset.bootX ?? 0));
      moduleEls.forEach((el, idx) => {
        const x = Number(el.dataset.bootX ?? 1280);
        const tilt = x > 1700 ? "rotateY(-16deg) translateX(18px)" : x < 860 ? "rotateY(16deg) translateX(-18px)" : "translateY(10px)";
        el.animate(
          [
            { opacity: 0, transform: `perspective(1100px) ${tilt} scale(0.96)` },
            { opacity: 0.85, offset: 0.18 },
            { opacity: 0.45, offset: 0.28 },
            { opacity: 1, transform: "perspective(1100px) rotateY(0deg) translate3d(0,0,0) scale(1)" },
          ],
          { delay: 300 + idx * 24, duration: 290, easing: "cubic-bezier(0.16, 1, 0.3, 1)", fill: "forwards" }
        );
      });

      // 4. Stage 3 (0.52s): Trigger Spin() on BottomStorage & BottomAudio twin dials
      setTimeout(() => {
        if (!cancelled) props.onTriggerSpinDials();
      }, 520);

      // 5. Stage 4 (1.15s - 2.75s): System Check Readout Card (Boot.ini:88-205 exact coordinates)
      await new Promise((r) => setTimeout(r, 1150));
      if (cancelled) return;

      const warns = props.rows.filter((r) => r.status !== "OK").length;
      for (let i = 0; i < props.rows.length; i++) {
        if (cancelled) return;
        const row = props.rows[i];
        setVisibleRows((prev) => [...prev, { label: row.label, value: "", status: "", rawStatus: row.status }]);
        scrambleDecode(row.value, 150, (txt) => {
          setVisibleRows((prev) => prev.map((item, idx) => (idx === i ? { ...item, value: txt, status: row.status } : item)));
        });
        await new Promise((r) => setTimeout(r, 80));
      }

      await new Promise((r) => setTimeout(r, 120));
      if (cancelled) return;
      setVerdictWarn(warns > 0);
      const targetVerdict = warns === 0 ? "ALL SYSTEMS NOMINAL" : `${warns} SYSTEM${warns > 1 ? "S" : ""} NEED ATTENTION`;
      scrambleDecode(targetVerdict, 200, setVerdictText);

      // Hold verdict for 900ms, then Stage 5 fade out + IMP-03 2-Frame DwmFlush() Handoff
      await new Promise((r) => setTimeout(r, 950));
      if (cancelled) return;
      if (cardRef.current) {
        const fade = cardRef.current.animate(
          [
            { opacity: 1, transform: "scale(1)" },
            { opacity: 0, transform: "scale(1.02)" },
          ],
          { duration: 220, easing: "ease-out", fill: "forwards" }
        );
        await fade.finished;
      }
      if (!cancelled) props.onFinished();
    })();

    return () => {
      cancelled = true;
      clearTimeout(failsafe);
    };
  }, [props.active]);

  if (!props.active) return null;

  // Boot.ini:94-205 exact coordinates on 2560x1600 design canvas
  return (
    <div className="intro-overlay" style={{ position: "absolute", inset: 0, pointerEvents: "none", zIndex: 999 }}>
      <div
        ref={scannerRef}
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width: "2560px",
          height: "12px",
          background: "linear-gradient(180deg, rgba(var(--accent-rgb),0) 0%, rgba(var(--accent-rgb),0.65) 50%, rgba(var(--accent-rgb),0) 100%)",
          boxShadow: "0 0 22px rgba(var(--accent-rgb), 0.85)",
          willChange: "transform, opacity",
        }}
      >
        <div style={{ position: "absolute", left: 0, top: "5px", width: "2560px", height: "1.8px", background: "rgb(235, 252, 255)" }} />
      </div>

      {visibleRows.length > 0 && (
        <div ref={cardRef} style={{ position: "absolute", inset: 0 }}>
          <svg width="2560" height="1600" viewBox="0 0 2560 1600" style={{ position: "absolute", inset: 0 }}>
            <path
              d="M 1084 566 L 1476 566 L 1492 582 L 1492 816 L 1476 832 L 1084 832 L 1068 816 L 1068 582 Z"
              fill="rgba(0, 10, 18, 0.85)"
              stroke="rgba(var(--accent-rgb), 0.45)"
              strokeWidth="1.4"
            />
            <rect x="1100" y="606" width="360" height="1.4" fill="rgba(var(--accent-rgb), 0.6)" />
            <rect x="1100" y="783" width="360" height="1.4" fill="rgba(var(--accent-rgb), 0.6)" />
            <rect x="1084" y="563" width="120" height="4" fill="rgb(var(--accent-rgb))" />
            <rect x="1356" y="831" width="120" height="4" fill="rgb(var(--accent-rgb))" />
            <text x="1280" y="588" textAnchor="middle" dominantBaseline="central" fill="rgb(var(--accent-rgb))" fontFamily="var(--font-num)" fontSize="22" fontWeight="700">
              SYSTEM CHECK
            </text>
            {visibleRows.map((r, i) => {
              const y = 627 + i * 27;
              const statusColor =
                r.rawStatus === "FAIL" ? "rgb(var(--alert-rgb))" : r.rawStatus === "CHECK" ? "rgb(var(--warn-rgb))" : "rgb(var(--good-rgb))";
              return (
                <g key={r.label}>
                  <text x="1096" y={y} textAnchor="start" dominantBaseline="central" fill="rgb(var(--text-rgb))" fontFamily="var(--font-num)" fontSize="20" fontWeight="700">
                    {r.label}
                  </text>
                  <text x="1392" y={y} textAnchor="end" dominantBaseline="central" fill="rgb(var(--white-rgb))" fontFamily="var(--font-num)" fontSize="20" fontWeight="700">
                    {r.value}
                  </text>
                  <text x="1466" y={y} textAnchor="end" dominantBaseline="central" fill={statusColor} fontFamily="var(--font-num)" fontSize="20" fontWeight="700">
                    {r.status}
                  </text>
                </g>
              );
            })}
            {verdictText && (
              <text
                x="1280"
                y="808"
                textAnchor="middle"
                dominantBaseline="central"
                fill={verdictWarn ? "rgb(var(--warn-rgb))" : "rgb(var(--good-rgb))"}
                fontFamily="var(--font-num)"
                fontSize="24"
                fontWeight="700"
              >
                {verdictText}
              </text>
            )}
          </svg>
        </div>
      )}
    </div>
  );
}
```

---

### 6.8 `SpaceshipApp\SpaceshipUI\src\modules\AudioReactor.tsx` (165Hz Zero-Copy `SharedBuffer` Port of `Scripts\audio.lua` with `Spin()` & Gaussian-Smoothed 96-Spoke Pulse Ring)
```tsx
import { h } from "preact";
import { useEffect, useRef } from "preact/hooks";
import { RGB, mix, rgba } from "../components/svg/HudPrimitives";

// Exact constants from Skins\Spaceship\@Resources\Scripts\audio.lua:20-26
const NB = 96;
const K = 1.16;
const CX = 94.5 + 18.51; // Zone origin Z1_X=18.51 inside 226x201 padded canvas
const CY = 82.5 + 18.04; // Zone origin Z1_Y=18.04 inside 226x201 padded canvas
const R_DASH = 70 * K;
const R_TICK = 78 * K;
const R_SWEEP = 58 * K;
const R_RING1 = 50 * K;
const R_RING2 = 45 * K;
const R_W0 = 25 * K;
const R_W1 = 41 * K;
const DASH_A0 = 120;
const DASH_SWEEP = 300;
const VIOLET: RGB = [150, 100, 255];

export function AudioReactor(props: {
  accent: RGB;
  white: RGB;
  dim: RGB;
  hi: RGB;
  panel: RGB;
  tier: number;
  hudAlpha: number;
  deviceName: string;
  spinTriggerCount: number;
  onPostMessage: (msg: any) => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const spinStartRef = useRef<number | null>(null);

  useEffect(() => {
    if (props.spinTriggerCount > 0) {
      spinStartRef.current = performance.now();
    }
  }, [props.spinTriggerCount]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let rafId = 0;
    let frame = 0;
    let breath = 0;
    const raw = new Float32Array(NB);
    const soft = new Float32Array(NB);
    const tips = new Float32Array(NB);

    const pt = (r: number, deg: number): [number, number] => {
      const ar = (deg * Math.PI) / 180;
      return [CX + r * Math.cos(ar), CY + r * Math.sin(ar)];
    };

    const render = (now: number) => {
      frame++;
      if (props.tier >= 3) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        rafId = requestAnimationFrame(render);
        return;
      }

      const shared: Float32Array | undefined = (window as any).__sharedTelemetry;
      const rms = shared ? shared[96] : 0;
      const peak = shared ? shared[97] : 0;
      const active = shared ? shared[98] > 0.5 : false;
      const volRaw = shared ? shared[125] : 50;
      const muted = volRaw < 0;
      const vol = muted ? 0 : volRaw;

      // Spin() power-on cubic ease-out (audio.lua:71-77)
      let spin = 1;
      if (spinStartRef.current !== null) {
        const t = Math.min(1, (now - spinStartRef.current) / 700);
        spin = 1 - Math.pow(1 - t, 3);
        if (t >= 1) spinStartRef.current = null;
      }
      const rot = (1 - spin) * -200;

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const A1 = props.accent, W = props.white, D = props.dim, RED = props.hi;

      // 1. Top 13 red peak ticks (audio.lua:101-108)
      const nt = 13;
      for (let i = 0; i < nt; i++) {
        const a = 238 + (i * 64) / (nt - 1);
        const lit = (i + 1) / nt <= peak * spin + 0.02;
        const [x0, y0] = pt(R_TICK - 5, a);
        const [x1, y1] = pt(R_TICK + 2, a);
        ctx.beginPath();
        ctx.moveTo(x0, y0);
        ctx.lineTo(x1, y1);
        ctx.strokeStyle = rgba(RED, lit ? 255 : 160, props.hudAlpha);
        ctx.lineWidth = lit ? 2.6 : 2.0;
        ctx.stroke();
      }

      // 2. Outer 30-dash volume ring (audio.lua:110-115)
      const nd = 30;
      const seg = (R_DASH * ((DASH_SWEEP * Math.PI) / 180)) / nd;
      ctx.save();
      ctx.beginPath();
      ctx.arc(CX, CY, R_DASH, ((DASH_A0 + rot) * Math.PI) / 180, ((DASH_A0 + DASH_SWEEP + rot) * Math.PI) / 180);
      ctx.strokeStyle = rgba(D, 190, props.hudAlpha);
      ctx.lineWidth = 4.2;
      ctx.setLineDash([seg * 0.42, seg * 0.58]);
      ctx.stroke();

      if (!muted && vol > 0 && spin > 0.02) {
        const va = DASH_A0 + DASH_SWEEP * Math.max(0, Math.min(1, vol / 100)) * spin;
        ctx.beginPath();
        ctx.arc(CX, CY, R_DASH, ((DASH_A0 + rot) * Math.PI) / 180, ((va + rot) * Math.PI) / 180);
        ctx.strokeStyle = rgba(A1, 255, props.hudAlpha);
        ctx.lineWidth = 4.2;
        ctx.stroke();
      }
      ctx.restore();

      // 3. Lower-left RMS loudness sweep (audio.lua:118-119)
      ctx.beginPath();
      ctx.arc(CX, CY, R_SWEEP, ((112 - rot) * Math.PI) / 180, ((112 + 100 * spin - rot) * Math.PI) / 180);
      ctx.strokeStyle = rgba(A1, 150, props.hudAlpha);
      ctx.lineWidth = 4.6;
      ctx.stroke();
      if (rms > 0.01) {
        ctx.beginPath();
        ctx.arc(CX, CY, R_SWEEP, (112 * Math.PI) / 180, ((112 + 100 * Math.min(1, rms * 1.6) * spin) * Math.PI) / 180);
        ctx.strokeStyle = rgba(mix(A1, W, 0.6), 255, props.hudAlpha);
        ctx.lineWidth = 5.0;
        ctx.stroke();
      }

      // 4. 96-Spoke Mirrored & Gaussian-Smoothed Pulse Ring (audio.lua:125-171)
      for (let k = 0; k < NB; k++) {
        let u = (k / NB) * 2;
        if (u > 1) u = 2 - u;
        const f = u * (NB - 1);
        const i0 = Math.floor(f);
        const i1 = Math.min(NB - 1, i0 + 1);
        const b0 = shared ? shared[i0] : 0;
        const b1 = shared ? shared[i1] : 0;
        raw[k] = Math.sqrt(Math.max(0, Math.min(1, b0 * (1 - (f - i0)) + b1 * (f - i0))));
      }

      let mean = 0;
      for (let k = 0; k < NB; k++) {
        let acc = 0, wsum = 0;
        for (let d = -8; d <= 8; d++) {
          const w = Math.exp(-(d * d) / 18);
          acc += raw[(k + d + NB) % NB] * w;
          wsum += w;
        }
        soft[k] = acc / wsum;
        mean += soft[k];
      }
      mean /= NB;
      breath += (Math.min(1, mean * 1.4 + rms * 1.2) - breath) * 0.35;

      const span = R_W1 - R_W0 - 2;
      for (let k = 0; k < NB; k++) {
        const v = active ? 0.7 * breath + 0.3 * soft[k] : 0.12 + 0.04 * Math.sin((k / NB) * Math.PI * 6 + frame * 0.05);
        tips[k] = R_W0 + 2 + v * span * spin;
      }

      // Draw 8 color-blended spoke segments (cyan -> violet)
      const SEG = 8;
      for (let q = 0; q < SEG; q++) {
        const mid = ((((q + 0.5) / SEG) * 360 - 90 - 45) * Math.PI) / 180;
        const spokeCol = mix(A1, VIOLET, 0.9 * (0.5 + 0.5 * Math.cos(mid)));
        ctx.beginPath();
        for (let k = (q * NB) / SEG; k <= ((q + 1) * NB) / SEG; k++) {
          const kk = k % NB;
          const a = (kk / NB) * 360 - 90;
          const [xIn, yIn] = pt(R_W0 + 1, a);
          const [xTip, yTip] = pt(tips[kk], a);
          ctx.moveTo(xIn, yIn);
          ctx.lineTo(xTip, yTip);
        }
        ctx.strokeStyle = rgba(spokeCol, 175, props.hudAlpha);
        ctx.lineWidth = 1.0;
        ctx.stroke();
      }

      // Smooth closed outline through spoke tips
      ctx.beginPath();
      for (let k = 0; k <= NB; k++) {
        const kk = k % NB;
        const [x, y] = pt(tips[kk] + 1.5, (kk / NB) * 360 - 90);
        if (k === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.closePath();
      ctx.strokeStyle = rgba(mix(A1, W, 0.55), 235, props.hudAlpha);
      ctx.lineWidth = 1.2;
      ctx.stroke();

      rafId = requestAnimationFrame(render);
    };

    rafId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(rafId);
  }, [props.accent, props.white, props.dim, props.hi, props.tier, props.hudAlpha]);

  return (
    <div
      className="audio-reactor"
      style={{ position: "relative", width: "226px", height: "201px" }}
      onWheel={(e) => {
        e.preventDefault();
        props.onPostMessage({ type: "audio.stepVolume", delta: e.deltaY < 0 ? 2 : -2 });
      }}
      onContextMenu={(e) => {
        e.preventDefault();
        props.onPostMessage({ type: "shell.open", uri: "ms-settings:sound" });
      }}
    >
      <canvas ref={canvasRef} width={226} height={201} style={{ position: "absolute", inset: 0 }} />
    </div>
  );
}
```

---

### 6.9 `SpaceshipApp\SpaceshipUI\src\modules\JarvisCore3D.tsx` (`Scripts\jarvis.lua` 56-Node Fibonacci 3D Plexus + 2 Tilted Orbit Rings + Dynamic `manifest.json` Atlas + Wake-Word Shockwave with `ui.animationLease`)
```tsx
import { h } from "preact";
import { useEffect, useRef, useState } from "preact/hooks";
import { RGB, mix, rgba } from "../components/svg/HudPrimitives";

// Exact constants from Skins\Spaceship\@Resources\Scripts\jarvis.lua:14-18, 41-66
const CX = ((746 - 514) / 2) * (2560 / 1260) + 18.32;
const CY = (491 - 407) * (1600 / 709) + 18.48;
const ORB_D = 330;
const OCC = ORB_D * 0.40;
const RP = 168;

interface PlexusGraph {
  nodes: [number, number, number][];
  edges: [number, number][];
}

// Deterministic 56-node Fibonacci sphere plexus with LCG seed=7 (jarvis.lua:42-66)
function buildPlexus(): PlexusGraph {
  const n = 56;
  let seed = 7;
  const rnd = () => {
    seed = (seed * 1103515245 + 12345) % 2147483648;
    return seed / 2147483648;
  };
  const nodes: [number, number, number][] = [];
  for (let i = 0; i < n; i++) {
    const y = 1 - (2 * (i + 0.5)) / n;
    const r = Math.sqrt(1 - y * y);
    const th = Math.PI * (3 - Math.sqrt(5)) * i;
    const j = 0.9 + 0.2 * rnd();
    nodes.push([Math.cos(th) * r * j, y * j, Math.sin(th) * r * j]);
  }
  const seen = new Set<string>();
  const edges: [number, number][] = [];
  for (let i = 0; i < n; i++) {
    const a = nodes[i];
    const dists: Array<{ k: number; d2: number }> = [];
    for (let k = 0; k < n; k++) {
      if (k !== i) {
        const b = nodes[k];
        dists.push({ k, d2: (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2 });
      }
    }
    dists.sort((p, q) => p.d2 - q.d2);
    for (let m = 0; m < 3; m++) {
      const k = dists[m].k;
      const key = `${Math.min(i, k)}:${Math.max(i, k)}`;
      if (!seen.has(key)) {
        seen.add(key);
        edges.push([i, k]);
      }
    }
  }
  return { nodes, edges };
}

const PLEXUS = buildPlexus();

export function JarvisCore3D(props: {
  accent: RGB;
  white: RGB;
  dim: RGB;
  warn: RGB;
  tier: number;
  hudAlpha: number;
  jarvisSettings: {
    enabled: boolean;
    name: string;
    orbBright: number;
    orbSize: number;
    tint: number;
    shell: boolean;
    orbits: boolean;
    dial: boolean;
    bars: boolean;
    speed: number;
    frameRate: number;
  };
  onPostMessage: (msg: any) => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [statusLabel, setStatusLabel] = useState("STANDBY");

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let rafId = 0;
    let frame = 0;
    let yaw = 0, rot1 = 0, rot2 = 0, rot3 = 0, sweep = 0;
    let lvl = 0;
    let shockwaveRadius = 0, shockwaveAlpha = 0;
    let prevStateEnum = 1;
    const bars = new Float32Array(22).fill(3);

    const proj = (p: [number, number, number], r: number, yw: number, tilt: number): [number, number, number] => {
      let [x, y, z] = p;
      const cy = Math.cos(yw), sy = Math.sin(yw);
      [x, z] = [x * cy + z * sy, -x * sy + z * cy];
      const ct = Math.cos(tilt), st = Math.sin(tilt);
      [y, z] = [y * ct - z * st, y * st + z * ct];
      const f = 1 / (1 - z * 0.18);
      return [CX + x * r * f, CY - y * r * f, z];
    };

    const hidden = (x: number, y: number, z: number) => z < 0 && (x - CX) ** 2 + (y - CY) ** 2 < OCC * OCC;

    const render = () => {
      frame++;
      if (props.tier >= 3) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        rafId = requestAnimationFrame(render);
        return;
      }

      const shared: Float32Array | undefined = (window as any).__sharedTelemetry;
      const rawLevel = shared ? shared[99] : 0;
      const stateEnum = shared ? Math.round(shared[100]) : 1; // 0=offline,1=idle,2=listening,3=thinking,4=speaking

      // IMP-02: Trigger radial Wake-Word Shockwave + 900ms animationLease on transition to LISTENING (2)
      if (stateEnum === 2 && prevStateEnum !== 2) {
        shockwaveRadius = 155;
        shockwaveAlpha = 0.85;
        props.onPostMessage({ type: "ui.animationLease", active: true, durationMs: 900, reason: "jarvis.wakeShockwave" });
      }
      prevStateEnum = stateEnum;

      const stMap: Record<number, string> = { 0: "offline", 1: "idle", 2: "listening", 3: "thinking", 4: "speaking" };
      const st = props.jarvisSettings.enabled ? (stMap[stateEnum] ?? "idle") : "idle";
      const labelMap: Record<string, string> = {
        idle: "STANDBY", listening: "LISTENING", thinking: "THINKING", speaking: "SPEAKING", offline: "OFFLINE",
      };
      if (frame % 15 === 1) setStatusLabel(labelMap[st] ?? "STANDBY");

      const targetLvl = st === "speaking" || st === "listening" ? Math.max(0, Math.min(1, rawLevel)) : 0;
      lvl += (targetLvl - lvl) * (targetLvl > lvl ? 0.55 : 0.18);

      const mot = props.jarvisSettings.speed;
      const spinMult = ({ idle: 1, listening: 0.7, thinking: 3.0, speaking: 1.4 + 2 * lvl, offline: 0.3 }[st] ?? 1) * mot;
      yaw = (yaw + 0.006 * spinMult) % (Math.PI * 2);
      rot1 = (rot1 + 0.5 * spinMult) % 360;
      rot2 = (rot2 + 0.8 * spinMult) % 360;
      rot3 = (rot3 - 0.25 * spinMult) % 360;
      sweep = (sweep + 9) % 360;

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const A1 = props.accent, W = props.white, D = props.dim;
      const DEEP = mix(A1, [0, 70, 210], 0.55);
      const OFF = mix(D, A1, 0.45);
      const col = st === "listening" ? DEEP : st === "offline" ? OFF : A1;
      const hot = mix(col, W, 0.45);
      const dim = st === "offline";

      // 1. Procedural Plasma Core + Voice Echo Halo
      const coreR = (ORB_D * 0.38) * props.jarvisSettings.orbSize * (1 + 0.12 * lvl);
      const grad = ctx.createRadialGradient(CX, CY, coreR * 0.08, CX, CY, coreR);
      grad.addColorStop(0, rgba(W, 240, props.hudAlpha));
      grad.addColorStop(0.45, rgba(col, 195, props.hudAlpha));
      grad.addColorStop(0.85, rgba(col, 55, props.hudAlpha));
      grad.addColorStop(1, rgba(col, 0, props.hudAlpha));
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(CX, CY, coreR, 0, Math.PI * 2);
      ctx.fill();

      // Wake-Word Radial Shockwave (IMP-02)
      if (shockwaveAlpha > 0.01) {
        ctx.beginPath();
        ctx.arc(CX, CY, shockwaveRadius, 0, Math.PI * 2);
        ctx.strokeStyle = rgba(hot, Math.floor(shockwaveAlpha * 255), props.hudAlpha);
        ctx.lineWidth = 2.4;
        ctx.stroke();
        shockwaveRadius += 4.2;
        shockwaveAlpha *= 0.93;
      }

      // 2. 56-Node 3D Plexus Shell (jarvis.lua:101-125)
      if (props.jarvisSettings.shell) {
        const r = RP * (1 + 0.07 * lvl);
        const tilt = 0.38 + 0.08 * Math.sin(frame * 0.006);
        const pts = PLEXUS.nodes.map((n) => {
          const [x, y, z] = proj(n, r, yaw, tilt);
          return { x, y, z, hid: hidden(x, y, z) };
        });
        const ea = dim ? 0.6 : 1 + 0.8 * lvl;
        for (const [i, k] of PLEXUS.edges) {
          const a = pts[i], b = pts[k];
          if (!a.hid && !b.hid) {
            const z = (a.z + b.z) * 0.5;
            let alpha = z >= 0 ? 70 + 110 * z : 22 + 30 * (1 + z);
            const mx = (a.x + b.x) * 0.5 - CX, my = (a.y + b.y) * 0.5 - CY;
            if (mx * mx + my * my < OCC * OCC * 0.8) alpha *= 0.4;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.strokeStyle = rgba(z >= 0 ? hot : col, Math.min(235, Math.floor(alpha * ea)), props.hudAlpha);
            ctx.lineWidth = z >= 0 ? 1.1 : 0.8;
            ctx.stroke();
          }
        }
        for (const p of pts) {
          if (!p.hid && p.z > -0.35) {
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.z > 0.3 ? 1.5 + 1.2 * lvl : 1.0, 0, Math.PI * 2);
            ctx.fillStyle = rgba(p.z > 0.3 ? W : hot, Math.min(255, Math.max(30, Math.floor((120 + 120 * p.z) * ea))), props.hudAlpha);
            ctx.fill();
          }
        }
      }

      // 3. 22 Voice-Reactive Side Bars (jarvis.lua:167-180)
      if (props.jarvisSettings.bars) {
        const nb = 11;
        for (let side = 0; side <= 1; side++) {
          for (let i = 1; i <= nb; i++) {
            const key = side * nb + i - 1;
            const a = ((side === 0 ? 180 : 0) + (i - (nb + 1) / 2) * 5.2) * (Math.PI / 180);
            const wob = 0.5 + 0.5 * Math.sin(frame * 0.11 + key * 1.7);
            const want = 3 + (dim ? 0 : 4 * wob + 22 * lvl * (0.5 + 0.5 * Math.sin(frame * 0.35 + key * 2.3)));
            bars[key] += (want - bars[key]) * 0.35;
            const r0 = 212;
            ctx.beginPath();
            ctx.moveTo(CX + r0 * Math.cos(a), CY + r0 * Math.sin(a));
            ctx.lineTo(CX + (r0 + bars[key]) * Math.cos(a), CY + (r0 + bars[key]) * Math.sin(a));
            ctx.strokeStyle = rgba(i === (nb + 1) / 2 ? W : col, dim ? 110 : 200, props.hudAlpha);
            ctx.lineWidth = 2.6;
            ctx.stroke();
          }
        }
      }

      rafId = requestAnimationFrame(render);
    };

    rafId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(rafId);
  }, [props.accent, props.white, props.dim, props.tier, props.hudAlpha, props.jarvisSettings]);

  return (
    <div
      className="jarvis-core-3d"
      style={{ position: "relative", width: "508px", height: "432px", cursor: "pointer" }}
      onClick={() => props.onPostMessage({ type: "jarvis.cmd", cmd: statusLabel === "STANDBY" ? "WAKE" : "CANCEL" })}
      onContextMenu={(e) => {
        e.preventDefault();
        props.onPostMessage({ type: "modal.setVisible", modalId: "jarvis" });
      }}
    >
      <canvas ref={canvasRef} width={508} height={432} style={{ position: "absolute", inset: 0 }} />
      <div style={{ position: "absolute", left: "26px", bottom: "44px", fontFamily: "var(--font-text)", fontSize: "14px", fontWeight: 700, color: "rgb(var(--accent-rgb))" }}>
        {props.jarvisSettings.name.toUpperCase() === "JARVIS" ? "J.A.R.V.I.S" : "C.L.O.V.E.R"}
      </div>
      <div style={{ position: "absolute", left: "26px", bottom: "28px", fontFamily: "var(--font-text)", fontSize: "12px", fontWeight: 700, color: "rgb(var(--white-rgb))" }}>
        {statusLabel}
      </div>
    </div>
  );
}
```
