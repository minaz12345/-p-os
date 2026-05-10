@echo off
REM P-OS Sovereign Baseline Measurement Wrapper
REM Ensures execution regardless of PowerShell policy settings
setlocal

echo [P-OS] Initiating Sovereign Baseline Measurement...
echo [P-OS] Security Context: ExecutionPolicy Bypass

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0MEASURE_BASELINE.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo [P-OS] ERROR: Baseline measurement failed with code %ERRORLEVEL%
    pause
) else (
    echo [P-OS] SUCCESS: Forensic baseline captured and sealed.
)

endlocal
