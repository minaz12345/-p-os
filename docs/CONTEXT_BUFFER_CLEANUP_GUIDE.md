# P-OS Context Buffer Scheduled Cleanup System

**Document Type:** OPERATIONAL GUIDE  
**Classification:** INTERNAL — OPERATOR USE ONLY  
**Date:** 2026-05-17  
**Author:** Paweł Nazaruk, Operator Nadzorca Wielki Elektronik  
**Version:** 1.0  

---

## 🎯 Overview

The **Context Buffer Monitor & Auto-Cleanup System** prevents memory bloat from accumulated temporary files, Python caches, and old log files. It runs automatically on a weekly schedule to maintain optimal system performance.

### Key Features

- ✅ **Threshold Monitoring**: Alerts when buffer usage exceeds 80% capacity
- ✅ **Dry-Run Preview**: Shows what would be cleaned without removing files
- ✅ **Automatic Cleanup**: Removes temp files, caches, and old logs safely
- ✅ **Scheduled Execution**: Weekly automation via Task Scheduler (Windows) or Cron (Linux/macOS)
- ✅ **Audit Logging**: All operations logged to `logs/context_buffer_monitor.jsonl`

---

## 📋 Components

### 1. Core Script: `scripts/context_buffer_monitor.py`

**Purpose**: Monitor buffer usage and perform cleanup operations

**Usage**:
```bash
# Check current buffer status
python scripts/context_buffer_monitor.py

# Dry-run preview (shows what would be cleaned)
python scripts/context_buffer_monitor.py --dry-run

# Automatic cleanup when threshold exceeded
python scripts/context_buffer_monitor.py --auto-clean

# Custom threshold (default: 80%)
python scripts/context_buffer_monitor.py --threshold 90
```

**What Gets Cleaned**:
| Target | Description | Safety |
|--------|-------------|--------|
| `data/temp/` | Temporary processing files | ✅ Safe to remove |
| `__pycache__/` | Python compiled bytecode | ✅ Regenerated automatically |
| `*.pyc`, `*.pyo` | Cache files | ✅ Regenerated automatically |
| Old log files (>30 days) | Archived operational logs | ✅ Backed up before removal |

---

### 2. Windows Scheduler: `scheduled_cleanup.bat`

**Purpose**: Automated cleanup via Windows Task Scheduler

**Setup Instructions**:

#### Step 1: Open Task Scheduler
```powershell
# Press Win+R, type:
taskschd.msc
```

#### Step 2: Create Basic Task
1. Click **"Create Basic Task"** in right panel
2. Name: `P-OS Context Buffer Cleanup`
3. Description: `Weekly cleanup of temp files and caches for P-OS system`
4. Click **Next**

#### Step 3: Configure Trigger
1. Trigger: **Weekly**
2. Start: Next Monday at **2:00 AM**
3. Recur every: **1 week**
4. Days: Check **Monday** only
5. Click **Next**

#### Step 4: Configure Action
1. Action: **Start a program**
2. Program/script: `C:\path\to\pos7\scheduled_cleanup.bat`
   - Replace with actual path to your pos7 directory
3. Start in: `C:\path\to\pos7`
   - Same path as above
4. Click **Next**

#### Step 5: Final Configuration
1. Check **"Open the Properties dialog for this task when I click Finish"**
2. Click **Finish**

#### Step 6: Advanced Settings
In Properties dialog:
1. **General Tab**:
   - ☑ Run whether user is logged on or not
   - ☑ Run with highest privileges
   - Configure for: Windows 10/11

2. **Conditions Tab**:
   - ☑ Start the task only if the computer is idle (optional)
   - ☐ Stop if the computer ceases to be idle
   - ☑ Wake the computer to run this task

3. **Settings Tab**:
   - ☑ Allow task to be run on demand
   - ☑ Run task as soon as possible after a scheduled start is missed
   - ☑ If the task fails, restart every: 5 minutes
   - Attempt to restart up to: 3 times

4. Click **OK**
5. Enter administrator password if prompted

#### Manual Test
```powershell
cd C:\path\to\pos7
.\scheduled_cleanup.bat
```

Expected output:
```
========================================
P-OS Context Buffer Cleanup
2026-05-17 02:00:00
========================================

[STEP 1] Dry-run preview...
================================================================================
CONTEXT BUFFER AUTO-CLEANUP
================================================================================

[CLEANING] data\temp...
   Would remove 42 files (15.23 MB)

[CLEANING] __pycache__...
   Would remove 128 .pyc files from various directories

[CLEANING] Old log files (>30 days)...
   Would remove healthcheck.log (2.45 MB, 2026-04-10)

================================================================================
CLEANUP SUMMARY
================================================================================
Files removed: 170
Space freed: 17.68 MB
Directories cleaned: 0

ℹ️  DRY RUN MODE - No files were actually removed

[STEP 2] Performing cleanup...
... (actual cleanup proceeds) ...

========================================
Cleanup completed successfully
2026-05-17 02:00:15
========================================
```

---

### 3. Linux/macOS Cron Job: `scheduled_cleanup.sh`

**Purpose**: Automated cleanup via cron scheduler

**Setup Instructions**:

#### Step 1: Make Script Executable
```bash
chmod +x /path/to/pos7/scheduled_cleanup.sh
```

#### Step 2: Edit Crontab
```bash
crontab -e
```

#### Step 3: Add Cron Entry
Add this line to crontab file:
```cron
# P-OS Context Buffer Cleanup - Every Monday at 2:00 AM
0 2 * * 1 /path/to/pos7/scheduled_cleanup.sh >> /path/to/pos7/logs/cleanup.log 2>&1
```

**Cron Schedule Breakdown**:
```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-7, Sunday=0 or 7)
│ │ │ │ │
0 2 * * 1
```
- **Minute**: 0 (top of the hour)
- **Hour**: 2 (2:00 AM)
- **Day of month**: * (every day)
- **Month**: * (every month)
- **Day of week**: 1 (Monday)

**Alternative Schedules**:
```cron
# Daily at 2:00 AM
0 2 * * * /path/to/pos7/scheduled_cleanup.sh >> /path/to/pos7/logs/cleanup.log 2>&1

# Every Sunday at 3:00 AM
0 3 * * 0 /path/to/pos7/scheduled_cleanup.sh >> /path/to/pos7/logs/cleanup.log 2>&1

# First day of every month at 1:00 AM
0 1 1 * * /path/to/pos7/scheduled_cleanup.sh >> /path/to/pos7/logs/cleanup.log 2>&1
```

#### Step 4: Verify Cron Job
```bash
# List all cron jobs
crontab -l

# Expected output:
# P-OS Context Buffer Cleanup - Every Monday at 2:00 AM
0 2 * * 1 /path/to/pos7/scheduled_cleanup.sh >> /path/to/pos7/logs/cleanup.log 2>&1
```

#### Manual Test
```bash
cd /path/to/pos7
./scheduled_cleanup.sh
```

---

## 🔍 Monitoring & Verification

### Check Last Cleanup Status

**View Monitor Log**:
```bash
# Linux/macOS
tail -n 20 logs/context_buffer_monitor.jsonl

# Windows PowerShell
Get-Content logs\context_buffer_monitor.jsonl -Tail 20
```

**Sample Log Entry**:
```json
{
  "timestamp": "2026-05-17T02:00:00.123456",
  "total_size_mb": 45.67,
  "total_files": 234,
  "usage_percent": 9.13,
  "threshold_percent": 80.0,
  "exceeds_threshold": false,
  "breakdown": {
    "data/temp": {"size_mb": 12.34, "file_count": 42},
    "__pycache__": {"size_mb": 28.91, "file_count": 128},
    "logs/*.log": {"size_mb": 4.42, "file_count": 64}
  }
}
```

### Check Cleanup Log (Linux/macOS)
```bash
# View recent cleanup executions
tail -n 50 logs/cleanup.log
```

### Check Task Scheduler History (Windows)
1. Open Task Scheduler (`taskschd.msc`)
2. Navigate to: **Task Scheduler Library → P-OS Context Buffer Cleanup**
3. Click **History** tab
4. Review last run status and duration

---

## ⚙️ Configuration Options

### Adjust Threshold

Edit `scripts/context_buffer_monitor.py` line 69:
```python
# Default: 500 MB estimated capacity
estimated_capacity_mb = 500

# Increase for larger systems:
estimated_capacity_mb = 1000  # 1 GB
```

Or use command-line argument:
```bash
python scripts/context_buffer_monitor.py --threshold 90
```

### Exclude Directories from Cleanup

Edit `scripts/context_buffer_monitor.py` line 30-33:
```python
self.temp_dirs = [
    self.base_dir / "data" / "temp",
    self.base_dir / "__pycache__",
    # Add more directories here if needed:
    # self.base_dir / "some" / "other" / "temp",
]
```

### Adjust Log Retention Period

Edit `scripts/context_buffer_monitor.py` line 162:
```python
# Default: 30 days
cutoff_date = datetime.now() - timedelta(days=30)

# Keep logs longer:
cutoff_date = datetime.now() - timedelta(days=90)  # 90 days
```

---

## 🚨 Troubleshooting

### Problem: Cleanup Fails with "Permission Denied"

**Windows**:
- Ensure Task Scheduler runs with **highest privileges**
- Right-click task → Properties → General → ☑ Run with highest privileges

**Linux/macOS**:
```bash
# Check file permissions
ls -la scheduled_cleanup.sh

# Fix permissions
chmod +x scheduled_cleanup.sh
chmod -R u+w data/temp/
```

### Problem: Python Not Found

**Windows**:
```powershell
# Check Python installation
where python

# If not found, add to PATH or use full path:
C:\Python39\python.exe scripts\context_buffer_monitor.py --dry-run
```

**Linux/macOS**:
```bash
# Check Python installation
which python3

# If not found, install:
sudo apt-get install python3  # Ubuntu/Debian
brew install python3          # macOS
```

### Problem: Cleanup Runs But Doesn't Remove Files

Check if dry-run mode is accidentally enabled:
```bash
# Verify script content
grep "dry_run" scheduled_cleanup.bat  # Windows
grep "dry_run" scheduled_cleanup.sh   # Linux/macOS
```

Ensure `--auto-clean` flag is present (not just `--dry-run`).

### Problem: Cron Job Not Running

```bash
# Check cron service status
sudo systemctl status cron      # Linux
sudo launchctl list | grep cron # macOS

# Check cron logs
grep CRON /var/log/syslog       # Linux
grep cron /var/log/system.log   # macOS

# Verify crontab syntax
crontab -l
```

---

## 📊 Performance Impact

### Typical Cleanup Results

| Metric | Before Cleanup | After Cleanup | Improvement |
|--------|---------------|---------------|-------------|
| Temp files | 150-300 | 0-10 | ~95% reduction |
| Cache files | 200-500 | 0 | 100% reduction |
| Old logs | 20-50 | 5-10 | ~80% reduction |
| Total size | 50-150 MB | 5-15 MB | ~90% reduction |

### Execution Time

| Operation | Duration |
|-----------|----------|
| Dry-run scan | 2-5 seconds |
| Actual cleanup | 5-15 seconds |
| Total execution | <30 seconds |

### Resource Usage

- **CPU**: Minimal (<5% during execution)
- **Memory**: ~50 MB peak
- **Disk I/O**: Moderate (file deletion operations)
- **Network**: None (local operations only)

---

## 🔒 Security Considerations

### What Is NOT Deleted

✅ **Protected**:
- Active database files (`*.db`, `*.sqlite`)
- Configuration files (`.env`, `.yaml`, `.json`)
- Source code (`*.py`, `*.js`, etc.)
- Documentation (`*.md`, `*.txt`)
- Recent log files (<30 days old)
- User data and exports

❌ **Deleted** (safe to remove):
- Temporary processing files
- Python bytecode caches
- Old archived logs (>30 days)
- Empty directories

### Audit Trail

All cleanup operations are logged to:
- `logs/context_buffer_monitor.jsonl` (structured JSON)
- `logs/cleanup.log` (human-readable, Linux/macOS only)

Review logs periodically to verify correct operation:
```bash
# Check for errors
grep "ERROR" logs/context_buffer_monitor.jsonl

# View cleanup history
cat logs/cleanup.log | grep "Cleanup completed"
```

---

## 📅 Maintenance Schedule

### Recommended Frequency

| Environment | Frequency | Rationale |
|-------------|-----------|-----------|
| Development | Weekly (Monday 2 AM) | Regular maintenance, low activity period |
| Staging | Weekly (Sunday 3 AM) | Pre-week readiness check |
| Production | Bi-weekly (1st & 15th) | Less frequent, monitored closely |

### Seasonal Adjustments

**High Activity Periods** (e.g., product launches):
- Increase frequency to twice weekly
- Monitor buffer usage daily

**Low Activity Periods** (e.g., holidays):
- Reduce frequency to monthly
- Perform manual verification

---

## ✅ Verification Checklist

After initial setup, verify:

- [ ] Script executes manually without errors
- [ ] Dry-run shows expected files for cleanup
- [ ] Actual cleanup removes files successfully
- [ ] Monitor log records each execution
- [ ] Scheduled task appears in Task Scheduler/crontab
- [ ] Task triggers at scheduled time (verify next morning)
- [ ] No critical files were accidentally deleted
- [ ] System performance improved post-cleanup

---

## 🎓 Best Practices

1. **Always test with `--dry-run` first** before enabling automatic cleanup
2. **Monitor logs weekly** to ensure cleanup is working correctly
3. **Adjust thresholds** based on actual system usage patterns
4. **Keep recent logs** (30 days minimum) for troubleshooting
5. **Backup important data** before major cleanup operations
6. **Document custom exclusions** if you modify the script
7. **Test after OS updates** to ensure Python paths remain valid

---

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Review monitor logs for error details
3. Test with `--dry-run` to diagnose issues
4. Contact system administrator if problems persist

---

**Last Updated**: 2026-05-17  
**Next Review**: 2026-06-17  
**Status**: OPERATIONAL ✅
