# Live test: standalone app (not run yet)

Nothing here has been run on the desktop. Each step needs your go. Steps 1 and 2 are read-only.

## Before you start

- Branch `feature/standalone-host`. Build: `dotnet build SpaceshipApp\ShipCore.App`.
- Rainmeter should be closed for the test. If it is open, the two HUDs overlap.
- Close any open exam browser or lock-down app. The app hides itself over them (`contract/exam-browsers.json`).

## 1. Preflight (read-only)

    powershell -ExecutionPolicy Bypass -File tools\windows\Live-Preflight.ps1

Expected: all `[PASS]` lines, exit code 0. `WARN` lines are advice only.

## 2. Live-check dry run (changes nothing)

    powershell -ExecutionPolicy Bypass -File tools\windows\Live-Check.ps1

Prints the steps. Exit code 0.

## 3. Live run (needs your go)

    powershell -ExecutionPolicy Bypass -File tools\windows\Live-Check.ps1 -Run

The script starts the app and samples it for 60 s. Then it waits up to 2 min for you to press **Ctrl+Alt+Shift+1**. It sends no keys and never kills anything.

Pass: `APP_EXITED_AFTER_CHORD=True`, `DESCENDANTS_STILL_ALIVE=0`, `RESULT=PASS`.

If it fails: note the `still alive` lines, then close the leftover processes yourself (Task Manager). Send the output to me.

## 4. Things to look at during the run

- The HUD appears on the desktop, under the windows, and clicks pass through outside its box.
- The settings file: `%LOCALAPPDATA%\Spaceship\settings.json` exists after the first run and has `"version": 1`.
- Crash guard: while the app runs, `%LOCALAPPDATA%\Spaceship\running.marker` exists. It is gone after Quit or the chord. If you end the app from Task Manager, the next start shows "The last run did not exit cleanly".
- Hotkey conflict: if Ctrl+Alt+Shift+1 is taken, a balloon tip says the kill switch is off. Quit from the tray still works.
- Tray: Start, Stop (hides), Start with Windows (off by default), Quit.
- CPU and memory: the perf CSV in `%TEMP%\spaceship-app\` has one row every 5 s. Those are host-process numbers only, not WebView2's.

## Rollback

- Stop: Ctrl+Alt+Shift+1, or tray Quit.
- Last resort: Task Manager, end `ShipCore.App` (this ends the whole tree).
- Remove the marker: delete `%LOCALAPPDATA%\Spaceship\running.marker` if it is left behind.
- Reset the settings: delete `%LOCALAPPDATA%\Spaceship\settings.json`. The next start re-imports the skin's values.
- Autostart: off unless you turn on "Start with Windows". It writes only `HKCU\...\Run\Spaceship`.
- The Rainmeter cutover (`tools\windows\Switch-HudHost.ps1 -Apply`) is NOT part of this test. It stays off until you approve it.

## Not covered by this test

- Real module parity with the Rainmeter skin: the modules are not ported yet.
- HWiNFO values: not built.
- Performance numbers: the perf CSV is written, but no baseline has been measured or compared.
