# CLAUDE-READ-BEFORE-RUNNING-ANYTHING

Read this file at the start of every session, and again before running any test or script.
Added 2026-10-15 after one test run called the real `SHEmptyRecycleBinW` and may have emptied the user's recycle bin.

## 1. Fake first
Any test that touches a destructive Windows call installs its fake BEFORE importing or running the code under test.
A test must fail if the real function is still reachable (assert the fake is the one installed).

## 2. Dry run first
Before running a new test or script that touches system actions, check what it calls WITHOUT executing it.
Read it and grep it for the real recycle bin, power, shutdown, sleep, hibernate, Bluetooth, Wi-Fi, service,
registry, process-kill and file-deletion calls (including through `shell32`, `ctypes`, `subprocess`, `os.remove`,
`shutil.rmtree`, `powercfg`, `rundll32`, `Stop-Computer`).

## 3. No real destructive calls in tests
Never run a test that could reach the real recycle bin, shutdown, sleep or file deletion. Those get fakes only.
If a run must touch the real thing, tell the user first and do not run it without an explicit yes.
