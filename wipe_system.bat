@echo off
title Accessibility Auditor - Total System Purge
echo ========================================================
echo        ENTERPRISE SYSTEM PURGE LAUNCHER
echo ========================================================
echo.
echo Handing over execution to Advanced PowerShell Engine...
echo.

"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -ExecutionPolicy Bypass -NoProfile -File "%~dp0purge_system.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [CRITICAL ERROR] Purge aborted due to a failed system failsafe.
    echo Please review the logs printed above.
    pause
)
