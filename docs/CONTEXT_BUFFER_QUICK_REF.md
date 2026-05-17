# Context Buffer Cleanup - Quick Reference

## 🚀 Quick Start

### Windows (Task Scheduler)
```powershell
# 1. Open Task Scheduler
taskschd.msc

# 2. Create task with these settings:
#    - Trigger: Weekly, Monday 2:00 AM
#    - Action: C:\path\to\pos7\scheduled_cleanup.bat
#    - Run with highest privileges ✓

# 3. Test manually
cd C:\path\to\pos7
.\scheduled_cleanup.bat
```

### Linux/macOS (Cron)
```bash
# 1. Make executable
chmod +x /path/to/pos7/scheduled_cleanup.sh

# 2. Edit crontab
crontab -e

# 3. Add this line:
0 2 * * 1 /path/to/pos7/scheduled_cleanup.sh >> /path/to/pos7/logs/cleanup.log 2>&1

# 4. Test manually
cd /path/to/pos7
./scheduled_cleanup.sh
```

---

## 🔍 Manual Commands

```bash
# Check current buffer status
python scripts/context_buffer_monitor.py

# Dry-run preview (safe - no files removed)
python scripts/context_buffer_monitor.py --dry-run

# Perform cleanup
python scripts/context_buffer_monitor.py --auto-clean

# Custom threshold (default: 80%)
python scripts/context_buffer_monitor.py --threshold 90
```

---

## 📊 What Gets Cleaned

| Target | Safe? | Frequency |
|--------|-------|-----------|
| `data/temp/` | ✅ Yes | Every run |
| `__pycache__/` | ✅ Yes | Every run |
| `*.pyc`, `*.pyo` | ✅ Yes | Every run |
| Old logs (>30 days) | ✅ Yes | Every run |
| Database files | ❌ No | Never |
| Config files | ❌ No | Never |
| Source code | ❌ No | Never |

---

## 📈 Expected Results

**Typical Cleanup**:
- Files removed: 150-300
- Space freed: 50-150 MB
- Execution time: <30 seconds
- Performance impact: Minimal (<5% CPU)

---

## 🔧 Troubleshooting

**Python not found?**
```bash
# Windows
where python

# Linux/macOS
which python3
```

**Permission denied?**
```bash
# Windows: Run Task Scheduler as Administrator
# Linux/macOS: chmod +x scheduled_cleanup.sh
```

**Check logs:**
```bash
# View monitor log
tail -n 20 logs/context_buffer_monitor.jsonl

# View cleanup log (Linux/macOS)
tail -n 20 logs/cleanup.log
```

---

## ⚙️ Configuration

**Change schedule:**
```cron
# Daily at 2 AM
0 2 * * * /path/to/scheduled_cleanup.sh

# Monthly on 1st at 1 AM
0 1 1 * * /path/to/scheduled_cleanup.sh
```

**Adjust threshold:**
Edit `scripts/context_buffer_monitor.py` line 69:
```python
estimated_capacity_mb = 500  # Change to 1000 for 1 GB
```

**Keep logs longer:**
Edit `scripts/context_buffer_monitor.py` line 162:
```python
cutoff_date = datetime.now() - timedelta(days=90)  # 90 days
```

---

## ✅ Verification Checklist

After setup:
- [ ] Script runs manually without errors
- [ ] Dry-run shows expected files
- [ ] Scheduled task appears in Task Scheduler/crontab
- [ ] Task triggers at scheduled time
- [ ] Monitor log records execution
- [ ] No critical files deleted

---

**Full Documentation**: `docs/CONTEXT_BUFFER_CLEANUP_GUIDE.md`  
**Support**: Review troubleshooting section or check logs
