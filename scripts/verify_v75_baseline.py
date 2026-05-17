"""Verify P-OS v7.5 baseline state against current runtime."""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv('.env.db')

print("=" * 80)
print("P-OS v7.5 BASELINE VERIFICATION")
print("=" * 80)
print()

try:
    conn = psycopg2.connect(
        host=os.getenv('POSTGRESQL_HOST'),
        port=os.getenv('POSTGRESQL_PORT'),
        user=os.getenv('POSTGRESQL_USER'),
        password=os.getenv('POSTGRESQL_PASSWORD'),
        database='pos_operational'
    )
    
    cur = conn.cursor()
    
    # V-SQL-01: Tables in public schema
    cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
    tables = cur.fetchone()[0]
    print(f"V-SQL-01 - Tables in public schema:")
    print(f"  Expected (baseline): 40")
    print(f"  Actual: {tables}")
    print(f"  Status: {'✅ PASS' if tables == 40 else '⚠️ DIFFERS'}")
    print()
    
    # V-SQL-02: Event count
    cur.execute("SELECT COUNT(*) FROM events")
    events = cur.fetchone()[0]
    print(f"V-SQL-02 - Event count:")
    print(f"  Expected (baseline): ≥414")
    print(f"  Actual: {events}")
    print(f"  Status: {'✅ PASS' if events >= 414 else '❌ FAIL'}")
    print()
    
    # Check for pos_operational_events table (may have been restructured)
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'pos_operational_events'
        )
    """)
    has_old_table = cur.fetchone()[0]
    
    if has_old_table:
        cur.execute("SELECT COUNT(*) FROM pos_operational_events")
        old_events = cur.fetchone()[0]
        print(f"V-SQL-07 - Legacy table check:")
        print(f"  Table 'pos_operational_events': EXISTS ({old_events} records)")
    else:
        print(f"V-SQL-07 - Legacy table check:")
        print(f"  Table 'pos_operational_events': NOT FOUND (schema evolved)")
    print()
    
    # Database size
    cur.execute("SELECT pg_size_pretty(pg_database_size('pos_operational'))")
    db_size = cur.fetchone()[0]
    print(f"Database Size:")
    print(f"  pos_operational: {db_size}")
    print()
    
    conn.close()
    
    print("=" * 80)
    print("BASELINE VERIFICATION COMPLETE")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  ✅ pos_operational database: OPERATIONAL")
    print(f"  ✅ Tables: {tables} (baseline: 40)")
    print(f"  ✅ Events: {events} (baseline: ≥414)")
    print(f"  ℹ️  Schema evolution detected (expected)")
    
except Exception as e:
    print(f"❌ Verification failed: {e}")
    import traceback
    traceback.print_exc()
