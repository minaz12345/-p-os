# Context Buffer Monitor - Quick Reference

## 🎯 Purpose
Automatically monitor and clean temporary files to prevent memory bloat. Triggers cleanup when buffer usage exceeds **80% threshold**.

---

## 📋 Quick Commands

### Check Status
```bash
python scripts/context_buffer_monitor.py
```

### Auto-Clean (if threshold exceeded)
```bash
python scripts/context_buffer_monitor.py --auto-clean
```

### Dry Run (preview only)
```bash
python scripts/context_buffer_monitor.py --dry-run
```

### Custom Threshold
```bash
python scripts/context_buffer_monitor.py --threshold 70
```

---

## 🔧 What Gets Cleaned

| Target | Description | Frequency |
|--------|-------------|-----------|
| `data/temp/` | Temporary processing files | Always |
| `__pycache__/` | Python compiled bytecode (*.pyc) | Always |
| `logs/*.log` | Log files older than 30 days | Age-based |

---

## ⏰ Scheduled Cleanup

### Windows Task Scheduler
```powershell
# Run as Administrator
schtasks /create /tn "P-OS Context Buffer Cleanup" ^
  /tr "D:\pos7\scripts\scheduled_cleanup.bat" ^
  /sc weekly /d MON /st 02:00
```

### Linux/macOS Cron
```bash
crontab -e
# Add this line:
0 2 * * 1 /path/to/pos7/scripts/scheduled_cleanup.sh
# Runs every Monday at 2:00 AM
```

---

## 📊 Monitoring

### Log File
All cleanup actions are logged to:
```
logs/context_buffer_monitor.jsonl
```

### Log Format
```json
{
  "timestamp": "2026-05-17T14:30:00",
  "total_size_mb": 0.59,
  "total_files": 20,
  "usage_percent": 0.12,
  "threshold_percent": 80.0,
  "exceeds_threshold": false,
  "breakdown": {
    "__pycache__": {"size_mb": 0.47, "file_count": 16}
  }
}
```

---

## 🚨 Alert Conditions

| Condition | Action |
|-----------|--------|
| Usage > 80% | Auto-cleanup triggered (if --auto-clean flag) |
| Cleanup fails | Error logged, exit code 1 |
| No cleanup needed | Exit code 0 |

---

## 💡 Best Practices

1. **Run weekly**: Schedule automatic cleanup every Monday at 2 AM
2. **Monitor logs**: Check `logs/context_buffer_monitor.jsonl` for trends
3. **Adjust threshold**: Lower to 70% if system has limited disk space
4. **Dry run first**: Use `--dry-run` to preview before actual cleanup
5. **Manual trigger**: Run `--auto-clean` after large data processing jobs

---

## 🔍 Troubleshooting

### Problem: Cleanup not running automatically
**Solution**: Verify scheduled task/cron job is active
```bash
# Windows
schtasks /query /tn "P-OS Context Buffer Cleanup"

# Linux/macOS
crontab -l
```

### Problem: Threshold constantly exceeded
**Solution**: 
1. Increase estimated capacity in `context_buffer_monitor.py` (line ~50)
2. Lower threshold to 70% for more aggressive cleanup
3. Manually clean large directories outside monitored paths

### Problem: Important files being deleted
**Solution**: Move important temp files outside monitored directories:
- `data/temp/` → `data/preserve/`
- Custom cache → `.cache/` (not monitored)

---

## 📈 Current Status

```
Total size: 0.59 MB
Total files: 20
Usage: 0.12% / 80% threshold
✅ Buffer usage OK
```

**Last checked**: 2026-05-17

---

## 🛠️ Integration with Pipeline

Add to forensic export pipeline:
```bash
# After each ETAP completion
python scripts/forensic_export_raw.py
python scripts/context_buffer_monitor.py --auto-clean  # Clean temp files

python scripts/detect_relationship_phases.py
python scripts/context_buffer_monitor.py --auto-clean  # Clean temp files

python scripts/extract_semantic_patterns.py
python scripts/context_buffer_monitor.py --auto-clean  # Final cleanup
```

This ensures temp files don't accumulate during multi-stage processing.

---

**Version**: 1.0  
**Created**: 2026-05-17  
**Maintainer**: P-OS Engineering Team
