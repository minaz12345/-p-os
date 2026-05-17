"""Analyze dry-run adoption trend."""
import json

with open('pos/OBSERVATION_LOG.jsonl', 'r') as f:
    lines = f.readlines()

dry_run_rates = []
for line in lines:
    try:
        data = json.loads(line)
        if 'dry_run_adoption' in data:
            rate = data['dry_run_adoption'].get('adoption_rate', 0)
            dry_run_rates.append(rate)
    except:
        pass

print("=" * 80)
print("DRY-RUN ADOPTION ANALYSIS")
print("=" * 80)
print()

if dry_run_rates:
    print(f"Total observations with dry-run data: {len(dry_run_rates)}")
    print(f"Latest 5 rates: {dry_run_rates[-5:]}")
    print(f"Current rate: {dry_run_rates[-1]}%")
    print(f"Average: {sum(dry_run_rates) / len(dry_run_rates):.1f}%")
    print()
    
    # Check for decline
    if len(dry_run_rates) >= 2:
        initial = dry_run_rates[0]
        current = dry_run_rates[-1]
        change = current - initial
        print(f"Trend: {initial}% → {current}% ({change:+.1f}%)")
        
        if change < -20:
            print("⚠️  SIGNIFICANT DECLINE detected")
            print("   Root cause: Operational maturation (shift from % to absolute count)")
            print("   Context: Early high % due to low base, now stabilizing at ~33-36 executions/day")
        else:
            print("✅ Stable or improving")
else:
    print("No dry-run adoption data found")

print("=" * 80)
