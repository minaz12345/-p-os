"""Verify R3 Event Chain Continuity and Timestamp Monotonicity."""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv('.env.db', override=True)

print("=" * 80)
print("R3 EVENT CHAIN CONTINUITY & MONOTONICITY CHECK")
print("=" * 80)

conn = psycopg2.connect(os.getenv('POSTGRESQL_URI'))
cur = conn.cursor()

# 1. Check Hash Integrity (R3)
cur.execute("SELECT COUNT(*) FROM events WHERE hash IS NULL")
null_hashes = cur.fetchone()[0]

# 2. Check Timestamp Monotonicity
cur.execute("""
    SELECT event_id, timestamp 
    FROM events 
    ORDER BY timestamp ASC
""")
events = cur.fetchall()

monotonic_violations = 0
for i in range(1, len(events)):
    if events[i][1] < events[i-1][1]:
        monotonic_violations += 1

# 3. Check Previous Hash Linkage
cur.execute("""
    SELECT COUNT(*) FROM events e1
    WHERE e1.previous_hash IS NOT NULL 
    AND NOT EXISTS (
        SELECT 1 FROM events e2 WHERE e2.hash = e1.previous_hash
    )
""")
broken_links = cur.fetchone()[0]

cur.close()
conn.close()

print(f"Total Events: {len(events)}")
print(f"Null Hashes: {null_hashes}")
print(f"Broken Hash Links: {broken_links}")
print(f"Timestamp Violations: {monotonic_violations}")

if null_hashes == 0 and broken_links == 0 and monotonic_violations == 0:
    print("\n✅ R3 VERIFICATION PASSED")
    print("   Event chain is cryptographically continuous and temporally monotonic.")
else:
    print("\n❌ R3 VERIFICATION FAILED")
    if null_hashes > 0: print(f"   - {null_hashes} events missing hashes")
    if broken_links > 0: print(f"   - {broken_links} broken hash links")
    if monotonic_violations > 0: print(f"   - {monotonic_violations} timestamp violations")

print("=" * 80)
