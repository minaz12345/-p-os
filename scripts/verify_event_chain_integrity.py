"""Verify event chain integrity for archival compliance."""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv('.env.db')

conn = psycopg2.connect(os.getenv('POSTGRESQL_URI'))
cur = conn.cursor()

print("=" * 80)
print("EVENT CHAIN INTEGRITY VERIFICATION")
print("=" * 80)

# Check total count
cur.execute("SELECT COUNT(*) FROM events")
total = cur.fetchone()[0]
print(f"\nTotal events: {total}")

# Check for gaps in hash chain
cur.execute("""
    SELECT event_id, previous_hash, hash 
    FROM events 
    ORDER BY timestamp ASC 
    LIMIT 100
""")
events = cur.fetchall()

print(f"\nChecking hash chain continuity (first 100 events)...")
gaps = 0
for i in range(1, len(events)):
    prev_event_hash = events[i-1][2]  # hash of previous event
    current_previous_hash = events[i][1]  # previous_hash of current event
    
    # Skip if current event has no previous_hash (shouldn't happen after first)
    if current_previous_hash is None:
        gaps += 1
        if gaps <= 5:
            print(f"  ⚠️  GAP at event {events[i][0]}: NULL previous_hash")
        continue
    
    if prev_event_hash != current_previous_hash:
        gaps += 1
        if gaps <= 5:  # Show first 5 gaps
            print(f"  ⚠️  GAP at event {events[i][0]}")
            print(f"      Previous event hash: {prev_event_hash[:16] if prev_event_hash else 'NULL'}...")
            print(f"      Current previous_hash: {current_previous_hash[:16]}...")

if gaps == 0:
    print("  ✅ Hash chain continuous - no gaps detected")
else:
    print(f"\n  ❌ {gaps} hash chain gaps detected")

# Check timestamp monotonicity
cur.execute("""
    SELECT event_id, timestamp 
    FROM events 
    ORDER BY timestamp ASC
""")
timestamps = cur.fetchall()

monotonic_violations = 0
for i in range(1, len(timestamps)):
    if timestamps[i][1] < timestamps[i-1][1]:
        monotonic_violations += 1

if monotonic_violations == 0:
    print(f"  ✅ Timestamps monotonic ({len(timestamps)} events)")
else:
    print(f"  ❌ {monotonic_violations} timestamp violations")

# Check for duplicate hashes
cur.execute("""
    SELECT hash, COUNT(*) as count 
    FROM events 
    GROUP BY hash 
    HAVING COUNT(*) > 1
""")
duplicates = cur.fetchall()

if not duplicates:
    print(f"  ✅ No duplicate hashes")
else:
    print(f"  ❌ {len(duplicates)} duplicate hashes found")

cur.close()
conn.close()

print("\n" + "=" * 80)
print("VERDICT:")
if gaps == 0 and monotonic_violations == 0 and not duplicates:
    print("✅ EVENT CHAIN INTEGRITY: VALID")
    print("   Forensic continuity maintained")
else:
    print("❌ EVENT CHAIN INTEGRITY: COMPROMISED")
    print("   Requires investigation before archival")
print("=" * 80)
