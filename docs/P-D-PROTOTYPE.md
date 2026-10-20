# P-D prototype: go / no-go (run this on Windows)

Project: `SpaceshipApp/ShipCore.Proto`. It compiles on the Ubuntu VM (`dotnet build`, 0 errors) but has **never been run**: no Windows, no WebView2 here. Treat every behaviour below as a hypothesis until you run it.

## What it tests
One borderless top-level window with `WS_EX_NOREDIRECTIONBITMAP`, hosting a composition-mode WebView2 through DirectComposition, with a transparent page background, a spinning ring (CSS animation), a click counter, and click-through everywhere except one 360x220 box. Never topmost (it sits at the bottom of the z-order). A tray icon has Refresh / Switch to Rainmeter / Quit. It answers `WM_QUERYENDSESSION` with TRUE and tears down once on `WM_ENDSESSION`. It logs host CPU, host memory and the page's frames per second every 5 s to `%TEMP%\spaceship-pd\perf-*.csv`.

## Run
```
cd SpaceshipApp
dotnet run --project ShipCore.Proto
```
Needs the .NET 10 SDK and the WebView2 runtime (already present on Windows 11). Quit from the tray icon.

## Checklist (write the result next to each line)
1. Window appears with the desktop visible through it (no black or white rectangle). PASS / FAIL
2. The ring animates smoothly; the CSV `js_fps` is close to your monitor refresh rate. Number: ___
3. Clicking the button changes the counter (mouse forwarding works). PASS / FAIL
4. Clicking anywhere outside the box reaches the desktop and the apps under it. PASS / FAIL
5. Other windows stay on top of it; it never covers a maximised app. PASS / FAIL
6. Open your lockdown browser: the prototype does not break it. (The exam-process suspend logic is in Core and unit-tested, but this prototype does not call it yet.) PASS / FAIL
7. Tray > Quit exits and leaves no `msedgewebview2.exe` children for this app. PASS / FAIL
8. Sign out / restart with it running: Windows does not wait for it. PASS / FAIL
9. Baselines, with Rainmeter running the same skin vs this prototype, 5 minutes each, idle desktop: CPU % and GPU % in Task Manager (include every `msedgewebview2.exe`), plus the existing `tools/gpu_baseline.ps1`. Numbers: ___

## Decision
- 1-5, 7 and 8 pass and 9 is not worse than Rainmeter: GO. Continue with P-E (host shell).
- Anything in 1-4 fails, or CPU/GPU is clearly worse: NO-GO. Stop and keep Rainmeter (plan v2, C1). Send me the CSV and the failing item and I will say whether a fix is plausible.

## Known gaps in the prototype
Cursor shape is not forwarded; keyboard input is not forwarded; only one hit rectangle; one monitor; the host's CPU number excludes WebView2's own processes (read those in Task Manager); the shared-memory buffer (plan H11) is not exercised.
