#!/bin/bash
# Scheduled Context Buffer Cleanup
# Add to crontab for weekly execution:
# 
# To schedule:
# crontab -e
# Add line: 0 2 * * 1 /path/to/pos7/scripts/scheduled_cleanup.sh
# (Runs every Monday at 2:00 AM)

cd "$(dirname "$0")/.."

python scripts/context_buffer_monitor.py --auto-clean --threshold 80

if [ $? -eq 0 ]; then
    echo "[$(date)] Cleanup completed successfully" >> logs/scheduled_cleanup.log
else
    echo "[$(date)] Cleanup failed or threshold exceeded" >> logs/scheduled_cleanup.log
fi
