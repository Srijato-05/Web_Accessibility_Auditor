@echo off
title Web Accessibility Auditor - Orchestrator
echo ========================================================
echo        ENTERPRISE ORCHESTRATOR LAUNCHER
echo ========================================================
echo.
echo Handing over execution to Advanced PowerShell Engine...
echo.

"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -ExecutionPolicy Bypass -NoProfile -File "%~dp0orchestrator.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [CRITICAL ERROR] Orchestrator aborted due to a failed system failsafe.
    echo Please review the logs printed above.
    pause
)
