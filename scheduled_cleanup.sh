#!/bin/bash
# ============================================================================
# P-OS Context Buffer Scheduled Cleanup - Linux/macOS Cron Job
# ============================================================================
# 
# This script performs automatic cleanup of context buffer (temp files, caches)
# Designed to run weekly via cron job
#
# Setup Instructions:
# 1. Make script executable:
#    chmod +x /path/to/pos7/scheduled_cleanup.sh
#
# 2. Edit crontab:
#    crontab -e
#
# 3. Add this line for weekly execution (Monday at 2:00 AM):
#    0 2 * * 1 /path/to/pos7/scheduled_cleanup.sh >> /path/to/pos7/logs/cleanup.log 2>&1
#
# Manual Test:
#   cd /path/to/pos7
#   ./scheduled_cleanup.sh
# ============================================================================

set -e  # Exit on error

# Set working directory to script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "P-OS Context Buffer Cleanup"
echo "$(date)"
echo "========================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found in PATH"
    exit 1
fi

# Perform dry-run first to show what would be cleaned
echo ""
echo "[STEP 1] Dry-run preview..."
python3 scripts/context_buffer_monitor.py --dry-run || {
    echo "WARNING: Dry-run encountered issues"
}

# Perform actual cleanup
echo ""
echo "[STEP 2] Performing cleanup..."
python3 scripts/context_buffer_monitor.py --auto-clean
if [ $? -ne 0 ]; then
    echo "ERROR: Cleanup failed with exit code $?"
    exit 1
fi

echo ""
echo "========================================"
echo "Cleanup completed successfully"
echo "$(date)"
echo "========================================"

exit 0
