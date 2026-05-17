"""Investigate schema drift - identify the 41st table."""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv('.env.db', override=True)

print("=" * 80)
print("SCHEMA DRIFT INVESTIGATION - Identifying 41st Table")
print("=" * 80)
print()

conn = psycopg2.connect(os.getenv('POSTGRESQL_URI'))
cur = conn.cursor()

# Get all tables with creation metadata
cur.execute("""
    SELECT 
        table_name,
        (SELECT obj_description(c.oid) 
         FROM pg_class c 
         JOIN pg_namespace n ON n.oid = c.relnamespace 
         WHERE c.relname = t.table_name AND n.nspname = 'public') as description
    FROM information_schema.tables t
    WHERE table_schema = 'public'
    ORDER BY table_name
""")

tables = cur.fetchall()

print(f"Total tables in pos_operational: {len(tables)}")
print()

# List all tables
print("All 41 tables:")
for i, (table_name, description) in enumerate(tables, 1):
    desc_str = f" - {description}" if description else ""
    print(f"  {i:2d}. {table_name}{desc_str}")

print()
print("=" * 80)
print("ANALYSIS:")
print("=" * 80)
print()
print("Baseline (v7.5 certified): 40 tables")
print("Current state: 41 tables")
print("Drift: +1 table")
print()
print("This requires:")
print("  1. Identification of which table was added")
print("  2. Migration documentation explaining why")
print("  3. Constitutional Agent R1a compliance check")
print()
print("Next step: Check git history for schema changes or migration scripts")
print("=" * 80)

cur.close()
conn.close()
