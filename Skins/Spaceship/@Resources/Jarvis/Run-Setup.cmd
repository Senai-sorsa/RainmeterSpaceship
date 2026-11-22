@echo off
rem Opens the Clover setup in its own PowerShell window (double-click this file, or Control Center > CLOVER > RUN SETUP)
start "Clover setup" powershell.exe -NoExit -ExecutionPolicy Bypass -File "%~dp0Setup-Jarvis.ps1"
