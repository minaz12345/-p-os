@echo off
REM Scheduled Context Buffer Cleanup
REM Add to Windows Task Scheduler for weekly execution
REM 
REM To schedule (run as Administrator):
REM schtasks /create /tn "P-OS Context Buffer Cleanup" /tr "D:\pos7\scripts\scheduled_cleanup.bat" /sc weekly /d MON /st 02:00

cd /d "%~dp0.."
python scripts\context_buffer_monitor.py --auto-clean --threshold 80

if %errorlevel% equ 0 (
    echo [%date% %time%] Cleanup completed successfully >> logs\scheduled_cleanup.log
) else (
    echo [%date% %time%] Cleanup failed or threshold exceeded >> logs\scheduled_cleanup.log
)
