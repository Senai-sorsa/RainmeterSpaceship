@echo off
rem Opens the Jarvis setup in its own PowerShell window (double-click this file, or Control Center > JARVIS > RUN SETUP)
start "Jarvis setup" powershell.exe -NoExit -ExecutionPolicy Bypass -File "%~dp0Setup-Jarvis.ps1"
