@echo off
REM Double-click or run from cmd. Arguments are passed on to the PowerShell script.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0fetch_all.ps1" %*
if "%~1"=="" pause
