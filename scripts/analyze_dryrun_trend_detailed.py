"""Analyze dry-run adoption trend over time."""
import json
from pathlib import Path
from datetime import datetime

audit_dir = Path('logs/cli_audit')
logs = []

for f in sorted(audit_dir.glob('pos-*.json')):
    try:
        data = json.loads(f.read_text(encoding='utf-8-sig'))
        # Extract date from filename (format: pos-YYYYMMDD-HHMMSS-hash.json)
        stem = f.stem
        parts = stem.split('-')
        if len(parts) >= 2:
            date_part = parts[1]  # YYYYMMDD
            try:
                date = datetime.strptime(date_part, '%Y%m%d').strftime('%Y-%m-%d')
            except:
                date = 'unknown'
        else:
            date = 'unknown'
        
        logs.append({
            'date': date,
            'dry_run': data.get('dry_run', False)
        })
    except Exception as e:
        print(f"Error reading {f}: {e}")
        continue

# Aggregate by date
dry_runs_by_date = {}
for log in logs:
    date = log['date']
    if date not in dry_runs_by_date:
        dry_runs_by_date[date] = {'dry': 0, 'exec': 0}
    
    if log['dry_run']:
        dry_runs_by_date[date]['dry'] += 1
    else:
        dry_runs_by_date[date]['exec'] += 1

print("=" * 80)
print("DRY-RUN ADOPTION TREND ANALYSIS")
print("=" * 80)
print()

print("Daily breakdown:")
print("-" * 80)
for date in sorted(dry_runs_by_date.keys()):
    d = dry_runs_by_date[date]
    total = d['dry'] + d['exec']
    rate = d['dry']/total*100 if total > 0 else 0
    print(f"{date}: dry={d['dry']:2d}, exec={d['exec']:2d}, total={total:3d}, rate={rate:5.1f}%")

print()
print("=" * 80)
print("SUMMARY:")
print("=" * 80)

total_dry = sum(d['dry'] for d in dry_runs_by_date.values())
total_exec = sum(d['exec'] for d in dry_runs_by_date.values())
total = total_dry + total_exec
overall_rate = total_dry/total*100 if total > 0 else 0

print(f"Total dry-run operations: {total_dry}")
print(f"Total execution operations: {total_exec}")
print(f"Total operations: {total}")
print(f"Overall adoption rate: {overall_rate:.1f}%")
print()

# Check for plateau
dates = sorted(dry_runs_by_date.keys())
if len(dates) >= 2:
    first_date = dates[0]
    last_date = dates[-1]
    first_dry = dry_runs_by_date[first_date]['dry']
    last_dry = dry_runs_by_date[last_date]['dry']
    
    print(f"Trend analysis:")
    print(f"  First day ({first_date}): {first_dry} dry-runs")
    print(f"  Last day ({last_date}): {last_dry} dry-runs")
    
    if last_dry <= first_dry * 1.1:  # Less than 10% growth
        print(f"  ⚠️  DRY-RUN COUNT PLATEAUED (growth <10%)")
        print(f"     While execution count grew, dry-run usage remained flat")
        print(f"     This suggests operators stopped using --dry-run as system scaled")
    else:
        print(f"  ✅ Dry-run count growing proportionally")

print("=" * 80)
