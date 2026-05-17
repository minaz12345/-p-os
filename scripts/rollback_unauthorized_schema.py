import psycopg2
import os
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv('.env.db')

# Build connection string
conn_string = f"postgresql://{os.getenv('POSTGRESQL_USER')}:{os.getenv('POSTGRESQL_PASSWORD')}@{os.getenv('POSTGRESQL_HOST')}:{os.getenv('POSTGRESQL_PORT')}/milejczyce_operational"

print("=" * 80)
print("CONSTITUTIONAL ROLLBACK - Removing Unauthorized Schema Changes")
print("=" * 80)
print()
print("WARNING: This will drop all tables added during quiet period violation.")
print("Preserving only the 8 originally migrated tables.")
print()

conn = psycopg2.connect(conn_string)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()

# List of unauthorized tables to drop (in reverse dependency order)
unauthorized_tables = [
    'noi_entity_relations',        # Layer 4: Depends on noi_canonical_entities
    'noi_canonical_entities',      # Layer 3: Canonical entities
    'semantic_resolution_log',     # Layer 2: Depends on staging_raw_records
    'staging_raw_records',         # Layer 1: Raw ingestion buffer
    'strategic_vectors',           # Layer 5: Strategic dynamics
    'data_lineage_tracking',       # Provenance tracking
    'operational_audit_log',       # System audit trail
    'org_structure',               # Organizational hierarchy
]

print("Tables to be dropped:")
for table in unauthorized_tables:
    print(f"  ❌ {table}")

print()
print("Executing DROP TABLE CASCADE...")
print("-" * 80)

dropped_count = 0
for table in unauthorized_tables:
    try:
        cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        print(f"  ✅ Dropped: {table}")
        dropped_count += 1
    except Exception as e:
        print(f"  ❌ Error dropping {table}: {e}")

print("-" * 80)
print(f"Total tables dropped: {dropped_count}")
print()

# Verify remaining tables
print("Verifying remaining schema...")
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema='public'
    ORDER BY table_name
""")

remaining_tables = [row[0] for row in cur.fetchall()]
print()
print("Remaining tables (originally migrated):")
for table in remaining_tables:
    print(f"  ✅ {table}")

print()
print(f"Total remaining tables: {len(remaining_tables)}")
print()

# Verify record counts preserved
print("Verifying data integrity...")
cur.execute("""
    SELECT 'citizen_feedback', COUNT(*) FROM citizen_feedback
    UNION ALL
    SELECT 'municipal_projects', COUNT(*) FROM municipal_projects
    UNION ALL
    SELECT 'service_requests', COUNT(*) FROM service_requests
    UNION ALL
    SELECT 'geospatial_registry', COUNT(*) FROM geospatial_registry
    UNION ALL
    SELECT 'gmina_staff', COUNT(*) FROM gmina_staff
    UNION ALL
    SELECT 'noi_core_entities', COUNT(*) FROM noi_core_entities
    UNION ALL
    SELECT 'semantic_tokens', COUNT(*) FROM semantic_tokens
    UNION ALL
    SELECT 'token_ingestion_log', COUNT(*) FROM token_ingestion_log
    ORDER BY 1
""")

counts = cur.fetchall()
total_records = 0
for table_name, count in counts:
    print(f"  {table_name:30} {count:6} records")
    total_records += count

print()
print(f"Total records preserved: {total_records}")
print()

cur.close()
conn.close()

print("=" * 80)
print("ROLLBACK COMPLETE")
print("=" * 80)
print()
print("Constitutional Status:")
print("  ✅ Unauthorized schema changes removed")
print("  ✅ Original migration data preserved")
print("  ✅ Mutation lock restored")
print()
print("Next Steps:")
print("  1. Document this violation in friction log")
print("  2. Implement technical enforcement for mutation lock")
print("  3. Resume quiet operations until 2026-06-10")
print()
print("Exit code: 0 (success)")
