"""Execute passive observation queries on milejczyce_operational database."""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv('.env.db')

# Connect to milejczyce_operational database
base_uri = os.getenv('POSTGRESQL_URI')
milejczyce_uri = base_uri.replace('pos_operational', 'milejczyce_operational')

conn = psycopg2.connect(milejczyce_uri)
cur = conn.cursor()

print("=" * 100)
print("QUERY A: CITIZEN FEEDBACK FRICTION MAP")
print("=" * 100)

try:
    cur.execute("""
        SELECT category, status, COUNT(*) as volume
        FROM citizen_feedback
        GROUP BY category, status
        ORDER BY volume DESC
        LIMIT 10
    """)
    
    rows = cur.fetchall()
    
    print(f"\n{'Category':<35} {'Status':<20} {'Volume':>10}")
    print("-" * 100)
    
    for row in rows:
        category = row[0] if row[0] else "NULL"
        status = row[1] if row[1] else "NULL"
        volume = row[2]
        print(f"{category:<35} {status:<20} {volume:>10}")
    
    print(f"\nTotal categories returned: {len(rows)}")
    
except Exception as e:
    print(f"❌ Query failed: {e}")

print("\n" + "=" * 100)
print("QUERY B: SERVICE REQUESTS OPERATIONAL LOAD")
print("=" * 100)

try:
    cur.execute("""
        SELECT service_type, priority, status, COUNT(*) as request_count
        FROM service_requests
        GROUP BY service_type, priority, status
        ORDER BY request_count DESC
        LIMIT 10
    """)
    
    rows = cur.fetchall()
    
    print(f"\n{'Service Type':<30} {'Priority':<12} {'Status':<15} {'Count':>10}")
    print("-" * 100)
    
    for row in rows:
        service_type = row[0] if row[0] else "NULL"
        priority = row[1] if row[1] else "NULL"
        status = row[2] if row[2] else "NULL"
        count = row[3]
        print(f"{service_type:<30} {priority:<12} {status:<15} {count:>10}")
    
    print(f"\nTotal service types returned: {len(rows)}")
    
except Exception as e:
    print(f"❌ Query failed: {e}")

cur.close()
conn.close()

print("\n" + "=" * 100)
print("OBSERVATION COMPLETE - RAW DATA EXTRACTED")
print("=" * 100)
