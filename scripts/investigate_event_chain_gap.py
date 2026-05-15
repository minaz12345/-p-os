"""Forensic investigation of event chain gap at SECRET_EXPOSURE_DETECTED."""
import psycopg2
from dotenv import load_dotenv
import os
import json

load_dotenv('.env.db')

conn = psycopg2.connect(os.getenv('POSTGRESQL_URI'))
cur = conn.cursor()

print("=" * 80)
print("FORENSIC INVESTIGATION: EVENT CHAIN GAP")
print("Target: a12a7fff-2750-4f2e-a6f9-380b80af8db0 (SECRET_EXPOSURE_DETECTED)")
print("=" * 80)

# Get the target event
cur.execute("""
    SELECT event_id, timestamp, actor_id, action, payload, previous_hash, hash
    FROM events 
    WHERE event_id = %s
""", ('a12a7fff-2750-4f2e-a6f9-380b80af8db0',))

target = cur.fetchone()
if not target:
    print("❌ Target event not found!")
    cur.close()
    conn.close()
    exit(1)

print(f"\n🎯 TARGET EVENT:")
print(f"  Event ID: {target[0]}")
print(f"  Timestamp: {target[1]}")
print(f"  Actor: {target[2]}")
print(f"  Action: {target[3]}")
print(f"  Previous Hash: {target[5]}")
print(f"  Current Hash: {target[6]}")
print(f"  Payload: {json.dumps(target[4], indent=4) if target[4] else 'NULL'}")

# Get events chronologically around the target
cur.execute("""
    SELECT event_id, timestamp, action, previous_hash, hash
    FROM events
    WHERE timestamp BETWEEN %s - INTERVAL '2 hours' AND %s + INTERVAL '2 hours'
    ORDER BY timestamp ASC
""", (target[1], target[1]))

surrounding_events = cur.fetchall()

print(f"\n📅 CHRONOLOGICAL CONTEXT (±2 hours):")
print("-" * 80)
for i, evt in enumerate(surrounding_events):
    marker = " <<< TARGET" if evt[0] == target[0] else ""
    prev_hash_status = "NULL ⚠️" if evt[3] is None else f"{evt[3][:16]}..."
    print(f"{i+1}. [{evt[1].strftime('%H:%M:%S')}] {evt[2]:40s} | prev_hash: {prev_hash_status}{marker}")
    print(f"   ID: {evt[0]}")

# Find the event immediately before target
print(f"\n🔍 PRECEDING EVENT ANALYSIS:")
print("-" * 80)
target_idx = None
for i, evt in enumerate(surrounding_events):
    if evt[0] == target[0]:
        target_idx = i
        break

if target_idx and target_idx > 0:
    prev_event = surrounding_events[target_idx - 1]
    print(f"Event before target:")
    print(f"  Event ID: {prev_event[0]}")
    print(f"  Timestamp: {prev_event[1]}")
    print(f"  Action: {prev_event[2]}")
    print(f"  Hash: {prev_event[4][:32] if prev_event[4] else 'NULL'}...")
    print(f"  Time difference: {(target[1] - prev_event[1]).total_seconds():.0f} seconds")
    
    # Check if target's previous_hash should match preceding event's hash
    if prev_event[4]:
        expected_prev_hash = prev_event[4]
        actual_prev_hash = target[5]
        
        print(f"\n  🔗 HASH CHAIN VALIDATION:")
        print(f"    Expected previous_hash: {expected_prev_hash[:32]}...")
        print(f"    Actual previous_hash:   {actual_prev_hash}")
        
        if actual_prev_hash is None:
            print(f"    ❌ CHAIN BROKEN: Target has NULL previous_hash")
            print(f"    💡 HYPOTHESIS: Chain was intentionally severed during security incident")
        elif actual_prev_hash == expected_prev_hash:
            print(f"    ✅ Chain intact")
        else:
            print(f"    ❌ Chain mismatch - possible tampering or data corruption")
else:
    print("  ⚠️  No preceding event found within 2-hour window")
    print("  💡 This might be near the beginning of the event log")

# Check for other NULL previous_hash events
print(f"\n🔍 ALL EVENTS WITH NULL PREVIOUS_HASH:")
print("-" * 80)
cur.execute("""
    SELECT event_id, timestamp, action, actor_id
    FROM events
    WHERE previous_hash IS NULL
    ORDER BY timestamp ASC
""")

null_events = cur.fetchall()
for evt in null_events:
    print(f"  • {evt[0]}")
    print(f"    Time: {evt[1]}")
    print(f"    Action: {evt[2]}")
    print(f"    Actor: {evt[3]}")
    print()

print(f"Total events with NULL previous_hash: {len(null_events)}")

# Analysis conclusion
print(f"\n{'=' * 80}")
print(f"FORENSIC CONCLUSION:")
print(f"{'=' * 80}")

if len(null_events) == 1:
    print("✅ Single NULL (genesis block) - ACCEPTABLE")
elif len(null_events) == 2:
    print("⚠️  Two NULLs detected:")
    print("  1. Genesis block (expected)")
    print("  2. SECRET_EXPOSURE_DETECTED (ANOMALY)")
    print()
    print("  LIKELY SCENARIO:")
    print("  - Security incident triggered automatic chain severance")
    print("  - System isolated compromised state from forensic record")
    print("  - OR: Manual intervention attempted to cover tracks")
    print()
    print("  RECOMMENDATION:")
    print("  - Document as 'Defensive Chain Severance' in archive")
    print("  - Verify no data was lost during the gap")
    print("  - Confirm this was intentional fail-safe behavior")
else:
    print(f"❌ CRITICAL: {len(null_events)} NULL previous_hash events")
    print("  Multiple chain breaks indicate systemic failure or attack")

print(f"{'=' * 80}")

cur.close()
conn.close()
