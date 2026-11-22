@echo off
rem The JARVIS gate (see tools\gate.sh). HEAVY: about 10 minutes of one CPU core. Runs on a scratch copy, never the live folder.
rem Needs Git for Windows (bash). Usage: tools\gate.cmd [label]
where bash >nul 2>nul || (echo bash not found - install Git for Windows & exit /b 9)
bash "%~dp0gate.sh" %*
