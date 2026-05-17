@echo off
REM ============================================================================
REM P-OS Context Buffer Scheduled Cleanup - Windows Task Scheduler
REM ============================================================================
REM 
REM This script performs automatic cleanup of context buffer (temp files, caches)
REM Designed to run weekly via Windows Task Scheduler
REM
REM Setup Instructions:
REM 1. Open Task Scheduler (taskschd.msc)
REM 2. Create Basic Task → Name: "P-OS Context Buffer Cleanup"
REM 3. Trigger: Weekly → Monday → 2:00 AM
REM 4. Action: Start a program
REM    - Program: C:\path\to\pos7\scheduled_cleanup.bat
REM    - Start in: C:\path\to\pos7
REM 5. Configure: Run whether user is logged on or not
REM               Run with highest privileges
REM
REM Manual Test:
REM   cd C:\path\to\pos7
REM   scheduled_cleanup.bat
REM ============================================================================

REM Set working directory to script location
cd /d "%~dp0"

echo ========================================
echo P-OS Context Buffer Cleanup
echo %date% %time%
echo ========================================

REM Check if Python is available
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found in PATH
    exit /b 1
)

REM Perform dry-run first to show what would be cleaned
echo.
echo [STEP 1] Dry-run preview...
python scripts\context_buffer_monitor.py --dry-run
if %errorlevel% neq 0 (
    echo WARNING: Dry-run encountered issues
)

REM Perform actual cleanup
echo.
echo [STEP 2] Performing cleanup...
python scripts\context_buffer_monitor.py --auto-clean
if %errorlevel% neq 0 (
    echo ERROR: Cleanup failed with exit code %errorlevel%
    exit /b %errorlevel%
)

echo.
echo ========================================
echo Cleanup completed successfully
echo %date% %time%
echo ========================================

exit /b 0
