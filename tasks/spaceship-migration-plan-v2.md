# Spaceship standalone migration - plan v2 (supersedes the Gemini plan)

Written 2026-10-20 by Claude from the review in `tasks/migration-review-2026-10-20.md`.
`claude_spaceship_migration_phases.md` (Gemini) stays in the repo as raw source only; its C#/TS snippets are reusable AFTER the fixes in section 4. Where this file and that one disagree, this file wins.
Nothing here is built unless its Status says so. Every phase still needs: goal, scope, non-goals, acceptance, validation, risks, rollback (CLAUDE.md s3), and your word before it starts.

## 1. Principles
1. **Rainmeter stays the default and is never modified or removed.** The standalone app is additive (new `SpaceshipApp/` folder). Switching is explicit, reversible, and never automatic at boot until you opt in.
2. **Test-first, platform-split.** Everything that is logic lives in code that builds and tests on this Ubuntu box. Only a thin Windows shell needs Windows. No claim of "works" without a command and its output.
3. **Measure, then promise.** No performance number in this plan is a target until a baseline exists (CLAUDE.md s4). Gemini's "<25 ms", "<15 ms", "165 Hz P99" are dropped. Budgets are set after the baselines in P-D.
4. **Contract first.** One protocol spec (JSON Schema + fixture vectors) is shared by C#, TypeScript and Python; each side is tested against the same vectors.
5. **Model output never authorizes OS actions.** Power/shell/config actions go through an allowlist and a confirmation, behind interfaces that tests replace with fakes first (CLAUDE-READ-BEFORE-RUNNING-ANYTHING.md).
6. **UI is ported 1:1 first, restyled second.** Parity is measured against the existing skin (rmsim output) before any visual change.

## 2. Architecture (three layers + shared contract)
```
contract/            protocol.schema.json, fixtures/*.json        (shared, tested by all three)
SpaceshipApp/
  ShipCore.Core/            net10.0, NO Windows APIs   -> builds + xUnit on Ubuntu
     Protocol, ConfigStore, HitGeometry, VisibilityPolicy, SpectrumAnalyzer,
     TelemetryLayout, interfaces: IClock IPowerActions IShell ISecretStore IWindowSnapshotSource
  ShipCore.Core.Tests/      xUnit, uses fakes for every interface above
  ShipCore.Host/            net10.0-windows, WinForms+Win32+WebView2, thin: implements the interfaces,
                            owns windows/hooks/pipes. Compile-checked on Ubuntu (EnableWindowsTargeting), RUN only on Windows
  SpaceshipUI/              Preact + @preact/signals + Vite + vitest + Playwright
     src/host/HostBridge.ts   interface; MockHost (dev/test on Ubuntu) and WebView2Host (real)
     src/generated/           output of tools/export_ui_assets.py (git-ignored, regenerated each build)
tools/export_ui_assets.py   zero-token exporter (status: in progress, see section 6 P-A)
```
Rules: Core never references Windows types; Host contains no decisions (it feeds snapshots in and applies results out); the UI talks only to `HostBridge`, so the same bundle runs under MockHost in headless Chromium and under WebView2.

## 3. Test ladder (what can be proven where)
| Level | What | Where | Needs |
|---|---|---|---|
| L0 | Python tools + exporter tests (`python3 -I tools/test_*.py`) | Ubuntu | nothing new |
| L1 | UI unit tests (vitest): layoutGuard, scramble decode, quad inflate, intro barrier at 60 and 165 Hz, signals store | Ubuntu | npm install (approved) |
| L2 | Visual parity: headless Chromium (Playwright) screenshots of the UI under MockHost vs rmsim render and vs `RefrenceImage.png` conventions | Ubuntu | Playwright (approved) |
| L3 | `dotnet test` on ShipCore.Core: protocol vectors, config atomic write, hit geometry, visibility rules, FFT vs reference sine, seq-lock | Ubuntu | `dotnet-sdk-10.0` (apt, needs your sudo) |
| L3b | Real named-pipe/unix-socket round trip C# <-> a Python stub using the contract fixtures | Ubuntu | same |
| L4 | `dotnet build ShipCore.Host` with EnableWindowsTargeting (compile + analyzer errors only) | Ubuntu | same |
| L5 | Windows gates (you run, paste output): transparent window prototype, regions/hit-test, WebView2 hosting, WM_ENDSESSION, schtasks/HKCU Run, Win+D, ProcessFailed, pipes C#<->jarvis.py, `test_jarvis.py` (real ctypes, fakes first), perf baselines | Windows 11 | a short scripted checklist per phase |
Anything only L5 can prove is marked UNVERIFIED in reports until you paste the result.
This VM: 4 CPUs, 3.8 GB RAM (about 1.4 GB free). Run one heavy tool at a time (build, then Playwright, never together).

## 4. Fixes to the Gemini plan (by review finding; all adopted)
Critical
- C1 Transparent window: do NOT use windowed WebView2 on a layered parent. Use a top-level `WS_EX_NOREDIRECTIONBITMAP` window with `CoreWebView2CompositionController` (DirectComposition), mouse via `SendMouseInput`. This is the P-D go/no-go prototype; if it fails, STOP and keep Rainmeter (the plan has no fallback that is worth the risk).
- C2 Pipes: `PipeOptions.CurrentUserOnly`, first-instance flag, session id in the name, nothing written to the host->python pipe until a valid `hello` (nonce + same PID on both pipes). Python writes use a bounded queue and a thread, never a blocking write on the JARVIS main loop.
- C3 WebView messages: accept only from the app origin, cancel other navigation, `DenyCors`. `config.set` is an allowlist of keys per file (Offsets.inc `_DX/_DY`, State.inc `Off_/CT_`, named Settings keys); everything else is refused and logged. Power actions need the existing JARVIS confirmation path and go through `IPowerActions`.
- C4 No automatic destructive start. Switching is only via `Switch-HudHost.ps1`: records the active Rainmeter configs first, deactivates by bang, closes ShipCore gracefully with a timeout (never `Stop-Process -Force` first), and the rollback re-activates exactly the recorded configs.
- C5 Startup: opt-in only. Default is `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` (no admin). A scheduled task is optional, asks first, and the exit code and stderr are checked. No HKLM, no Winlogon, ever.
High
- H6 Visibility: shell classes (Progman, WorkerW, Shell_TrayWnd) are excluded unconditionally; fullscreen = DWM extended frame bounds + `SHQueryUserNotificationState`; auto-hide taskbar overhang tolerated. Pure function in Core, table-tested.
- H7/H8 Z-order: canvas to bottom first, then hull via `SetWindowPos(hull, canvas...)`; remove the Win+D "guard" that strips hide flags; re-assert order on the foreground event.
- H9 Shutdown: return TRUE on `WM_QUERYENDSESSION`; tear down and QUIT jarvis only on `WM_ENDSESSION(wParam=TRUE)`.
- H10 ProcessFailed: handle `RenderProcessExited` (Reload) and `Unresponsive` (wait, then act), `BrowserProcessExited` (new environment); try/catch, retry counter with reset.
- H11 Shared buffer: ReadWrite->ReadOnly decided in P-D; JS must call `releaseBuffer`; seq-lock (even/odd) so readers never see torn frames; frame counter is uint32, not float32; modal controller sets Bounds/IsVisible.
- H12 Regions: delete the region on `SetWindowRgn` failure; leases carry an expiry timer owned by Core; document the 1-bit hard edge instead of calling it "kernel-level hit-testing".
- H13 Icons: `SIIGBF_ICONONLY (0x4)`, copy DIB bits into `Format32bppArgb` (keeps alpha), release the COM factory.
- H14 Publish: ReadyToRun is not AOT; plain folder publish with `WebView2Loader.dll` beside the exe; no self-extract to `%TEMP%`.
Medium: intro barrier driven by measured frame time (works at 60 Hz) with one failsafe constant; FFT in `float`, timeout wait with decay on silence; ONE generated path (`SpaceshipUI/src/generated`); register `SpaceshipHudHostClass` or drop the claim; verify the Chromium GPU flag before use; check `SetWindowDisplayAffinity` return and drop "screen-share detected"; DPAPI entropy is `UTF8("SpaceshipHUD")` (ShipCore.cs:164,173) behind `ISecretStore`; VRAM math restated (about 43 MB for two 160 px atlases) and budgeted after measurement.
Repo-fact fixes: 35 skins / 33 offset keys / 35 zones (not 22/25); re-grep every line number; `export_ui_assets.py` is created, not assumed; BUG-01 change (`rainmeter_running()` also true when the host IPC is live) is made only in P-G, when a host exists.

## 5. Improvements beyond the review
1. **Parity harness**: rmsim (already in tools/) renders the Rainmeter skin; the same layout renders from the exported JSON in Chromium; a pixel-diff report per module is the acceptance test for each port. No module is "done" without it.
2. **Golden exports**: `export_ui_assets.py --check` runs in CI/pre-build; a stale generated dir fails the build. Reproducible output (sorted, no timestamps, source hashes in `_meta.json`).
3. **One command**: `npm run gen` = exporter, then build. `npm run test:all` = L0-L2 in sequence.
4. **MockHost scenarios**: recorded telemetry scripts (idle, gaming spike, alert, wake-word, mic muted, 60 Hz panel) drive the UI deterministically; the same scripts replay on Windows.
5. **Feature flag / kill switch**: a `Standalone` flag in State.inc plus `Switch-HudHost.ps1 -Rollback`, tested with fakes in Core.
6. **Perf baseline kit** (L5): extend `tools/gpu_baseline.ps1` to log CPU/RAM/GPU/disk for Rainmeter mode first, then standalone, same scenarios; budgets come from that.
7. **Security checklist as tests**: origin lock, config allowlist, pipe ACL, secret redaction in exports, power-action fakes. Each is a Core/Host test, not a comment.
8. **Orb atlas**: `build_orb_atlas.py` reads the frame counts from the exporter's `orb.json` (210/210 now), not hard-coded names.

## 6. Phases
Status legend: DONE / IN PROGRESS / NEXT / BLOCKED(needs X).
- **P-0 Checkpoint** DONE: Phase 10B committed as bdfb8fb (tests not re-verified on Windows; run `py -3 -B test_jarvis.py` there).
- **P-A Asset exporter** IN PROGRESS (delegated; `tools/export_ui_assets.py` + test). Acceptance: tests pass, `--check` exits 0 after a run, settings export has no credential-like keys, output deterministic. Rollback: delete the two files and the generated dir.
- **P-B UI scaffold + MockHost** NEXT (needs npm/Playwright; approved). Vite + Preact + signals + vitest + Playwright, design tokens, static HUD from `layout.json`, screenshot test. Acceptance: `npm run test:all` green; first parity image vs rmsim.
- **P-C Contract + Core** BLOCKED(dotnet-sdk-10.0). Schema, fixtures, Core + xUnit, Python stub round trip. Acceptance: `dotnet test` green on Ubuntu.
- **P-D Windows prototype gate (go/no-go)** BLOCKED(you on Windows): 200-line host: NOREDIRECTIONBITMAP + composition WebView2 over the desktop, click-through outside regions, one module drawn, perf baseline numbers. Pass = continue; fail = stop, nothing else is built.
- **P-E Host shell** after P-D: windows, pipes, ConfigStore, visibility, shutdown, ProcessFailed.
- **P-F Module ports** in batches (frame+hull, top, bottom, left, right, center+orb, intro), each with its parity diff.
- **P-G JARVIS integration**: BUG-01 change, pipe client, contract tests.
- **P-H Opt-in cutover**: HKCU Run entry, 6-hour soak, rollback drill. You approve deployment explicitly.

## 7. Visual direction (user ruling 2026-10-20)
- **The Rainmeter app is the source of truth.** Colours, line weights, fonts, glow and behaviour are ported identically from the skin (Settings.inc theme variables, Common.inc, the Lua drawing). The UI reads the theme from the exported settings, so colour themes keep working.
- **RefrenceImage.png is used only for frame and positioning** (the cockpit hull/canopy shape and where modules sit), and only where the Rainmeter skin has no equivalent to transfer. It does NOT supply colours, typography or motifs. The palette sampler (`tools/palette_from_reference.py`) is kept as a diagnostic, not as tokens.
- If something cannot be ported identically (new UI: boot card, Layout Studio, three modals), it is built from the existing skin's own colours and line style first; the reference is consulted for frame/positioning only.
- Acceptance for every ported module is the parity diff against the rmsim render of the real skin, not resemblance to the reference.

## 8. Needs your approval
1. `sudo apt install dotnet-sdk-10.0` (Ubuntu 24.04 candidate 10.0.112) for L3/L4. Without it, C# stays unwritten and unverified.
2. Order after P-B: P-C immediately, or wait until you can run P-D on Windows first (my recommendation: run P-D early; it is the only thing that can kill the project).
3. Whether `generated/` is git-ignored (my choice: yes, regenerated every build).
