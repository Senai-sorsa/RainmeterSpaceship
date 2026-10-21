# Standalone app: vision and port plan (2026-10-20)

Supersedes the phase F parts of `tasks/standalone-app-architecture.md` and section D of `tasks/full-plan-2026-10-20.md`.

## 1. Vision (the user's words, 2026-10-20)
A standalone app that does everything the Rainmeter skin does, in a design the user controls, with smoother animation, more tools, and easy adjustment. **No Rainmeter anywhere in the new app.** That means no `Rainmeter.exe`, no `SKIN:Bang`, no `.ini` parsing at run time, no Rainmeter plugins, and no fallback to the skin.

Rainmeter is still used as a reference in two places, and neither ships:
- The skin's Lua and ini files are the spec for each module (what it shows, colours, timings).
- `rmsim` (under `tools/`) renders the skin for pixel comparison. It is a dev-only oracle.

## 2. What this changes in the current plan
| Current plan | Problem against the vision | Change |
|---|---|---|
| Settings live in the skin's `Settings.inc` / `State.inc` / `Offsets.inc` (`ConfigStore`) | Keeps the app tied to the Rainmeter file format | Own store: `%LOCALAPPDATA%\Spaceship\settings.json`, versioned. One-time import tool reads the skin's files (dry run first). `ConfigStore` stays only until import is done. |
| Tray menu item "Switch to Rainmeter" (`Lifecycle.cs`), `Proto` launches `Rainmeter.exe` | Rainmeter inside the app | Remove the item and the launch call. Keep the teardown. Recovery from a bad config is "reset to defaults", not a skin. |
| Phase F = "port the 35 skin modules" with rmsim parity as acceptance | Parity with the skin is the floor, not the goal | Keep parity as the floor, then add the vision's extras per module: smoother animation budget, adjustable per module, and tools. |
| Visual source = the skin (`RefrenceImage.png` for frame only) | Correct, but the user wants custom design | Keep: the skin's look is the starting theme. Add a theme layer (tokens in `settings.json`, editable in Control Center). Themes are data, not code. |
| Animation: "the same as the skin" | The user wants smoother | Animation rate and easing become settings, with a 60/165 Hz cap. Each change is measured on Windows (P-D checklist) before it is called smoother. |
| P-D go/no-go failed (2026-10-21), decision pending | Blocks everything that touches the desktop | See section 5. |
| Phase 4 of `claude_spaceship_migration_phases.md` (superseded doc) | Its budgets (165 Hz, `<15 ms` wake, `DwmFlush`) are unmeasured | Not used as written. The parts needed (orb, audio analyzer, intro) are ported under F. |

## 3. Rainmeter dependencies that must go (inventory)
- `ShipCore.App/Program.cs:109` and `ShipCore.Proto/Program.cs:49`: Rainmeter launch on switch. Remove.
- `ShipCore.Core/Lifecycle.cs`: `TrayCommand.SwitchToRainmeter` and its test. Remove.
- `ShipCore.Core/ConfigStore.cs`: reads `Settings.inc`. Replace after import (section 4, step F0).
- `ShipCore.App/Program.cs:186`: picks the display matching `HomeSize` in `Settings.inc`. Move to `settings.json`.
- `SpaceshipUI/src/lib/theme.ts`: parses `r,g,b` colour strings. The format is fine as data; rename the comment to not say Rainmeter.
- Comments that say "like Rainmeter" (`ConfigStore.cs:46,97`, `Program.cs:155`): reword.
- `Apps.ini`: the app list. Move into `settings.json`.

## 4. Module port (phase F), with the vision added

### Data sources: each becomes a native C# collector behind an interface, with a fake for tests
| Rainmeter plugin | Used by | Native replacement | Notes |
|---|---|---|---|
| AudioLevel | Audio, Storage | WASAPI loopback analyser (Phase 4 item, the FFT part) | Needed. Event-driven, zero work during silence. |
| UsageMonitor | GraphA/B/CPU/RAM, Strip, Target | `PerformanceCounter` or `GetSystemTimes` / `GlobalMemoryStatusEx` | Measure cost before choosing. |
| Process | Target, Sphere (radar) | `System.Diagnostics.Process` | Sample at the performance tier rate. |
| PowerPlugin | Battery, Power | `GetSystemPowerStatus` | Pure read. |
| SysInfo | SysInfo, Panels | `Environment`, `NetworkInterface`, `GetTickCount64` | Pure read. |
| RunCommand | Console, Storage, Dev, Upkeep, Right slots | Each command is a named action in an allowlist | Model output never triggers one. See section 5. |
| WebParser | Location (calendar), Sphere (ISS), SysInfo (WAN IP, speed test) | One fetch policy (decided, `standalone-app-architecture.md`) | https only, 30 s timeout, failures counted, no secrets in logs. |
| HWiNFO (`HWiNFO.inc`) | Power, Strip, HUD temperatures | HWiNFO shared memory, with a Windows fallback when HWiNFO is not running | Decision 5.2. Not Rainmeter. |

### Modules, in the skin's order (36 ini files, 40 Lua scripts)
Every module: data source behind an interface, fake-data test, rmsim parity diff (recorded, not gating for the vision extras), feature flag default off, and per-module settings in `settings.json`.

- **F1 Frame and Controller** (`Frame`, `Controller`): the frame must be exact. Controller becomes the performance tier and kill switch.
- **F2 Top** (`Alert`, `Battery`, `Console`, `GraphA`, `GraphB`, `GraphCPU`, `GraphRAM`, `Power`): Console's GPU-mode and power-mode tabs are OS actions. They go through the action gate and need a confirm.
- **F3 Bottom** (`Audio`, `Panels`, `Storage`, `Strip`): Audio needs the WASAPI analyser. Storage's dial sets brightness, volume, mic, power mode, refresh rate, glow. Each is an action with validation and a confirm where it changes the system.
- **F4 Left** (`Category`, `Location`, `Slot1-4`, `Upkeep`): Location is the calendar (fake feed now, real feed after the fetch slice). Upkeep runs `winget` and antivirus checks in the background.
- **F5 Right** (`Category`, `Dev`, `Slot5-8`, `SysInfo`): Dev runs WSL, Ollama, Tailscale and Docker queries. SysInfo has the speed test (a user-clicked action).
- **F6 Center** (`HUD`, `Sphere`, `Target`): Sphere is the Clover hologram (frame animation, orb atlas) with the ISS plot. Target is the orange lock.
- **F7 Overlay** (`Boot`, `Control`, `Drawer`, `Jarvis`): Boot is the intro (the 165 Hz budget is measured, not assumed). Control is the tools panel (becomes the Control Center). Drawer is the category list. Jarvis is the log viewer.

Ported Lua logic goes into TypeScript for drawing and state, and into C# for collectors and actions. Nothing runs Lua.

### Extras the vision asks for (added per module, after parity)
1. **Animation:** frame rate and easing as settings; each change measured on Windows.
2. **Design:** colours, fonts, glow and frame style from the theme tokens; editable in Control Center with a live preview.
3. **Tools:** undo for every setting (C3), test buttons for voice, wake and alert (C4), layout editing (phase 5 Layout Studio), import and export of `settings.json`.
4. **Adjustment:** every module can be moved, resized, turned off, or set to a tier without editing files.

## 5. Decisions and defaults
I'm taking these defaults unless you say otherwise:
1. **Settings store:** `%LOCALAPPDATA%\Spaceship\settings.json` with a one-time import from the skin's files (dry run first, then a copy-run, never in place).
2. **HWiNFO:** read its shared memory when HWiNFO runs, with a Windows fallback. This is not Rainmeter, but it needs HWiNFO running on your PC. Reading it live needs your go.
3. **OS actions** (power mode, GPU mode, brightness, volume, mic, refresh rate, charge limit, glow, launching apps, `winget`, Docker, Tailscale): each is a named action in an allowlist. Validated arguments, a confirm for any change to the system, real exit codes checked. Nothing from model output triggers one (`CLAUDE.md` rule 5).
4. **Web data** (ISS, WAN IP, speed test, calendar): one fetch policy for all of them.
5. **P-D:** the App already has the UI-thread fix the prototype lacked (`ShipCore.App/Program.cs:210`), and you tested transparency on it. The performance checklist (FPS, CPU, GPU, RAM) has not been run. I treat P-D as passed for coding, and keep the performance items as a gate before cutover.

## 6. Order of work (no live runs without your go)
- **F0 Foundations:** `settings.json` store with schema and tests; import tool (dry run); remove the Rainmeter switch and launch; fake collectors and the interface.
- **F1 Collectors** (C#, tests with fakes): system metrics, power, processes, network, WASAPI analyser.
- **F2 Modules in the order of section 4**, each: UI port (fake data), its collector, its action gate, its tests, its parity diff.
- **Extras** per module after its parity.
- **Live steps** (need your go): real collectors on your PC, the parity runs on Windows, the performance baseline, the 6-hour soak, cutover.

## 7. Verification
Each slice: `npm test` (vitest + the Playwright specs), `dotnet test`, and the fake-data tests, with exit codes checked. No claim of smoothness or performance without a Windows measurement. Rollback: each slice is one commit, `git revert` by hash.

## 8. Not done by this plan (yet)
- F0 to F7 are not started. This document is the plan.
- No live run, no `-Apply`, no HKCU Run change, no deploy.
- The fetch slice for the calendar is not built.
