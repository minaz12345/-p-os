"""Check unauthorized tables in PostgreSQL."""
import psycopg2
import os

conn_string = f"postgresql://{os.getenv('POSTGRESQL_USER', 'pos_admin')}:{os.getenv('POSTGRESQL_PASSWORD', 'XWBYAqOs03VH1L-gDjGuSpPC1BoN1ZTTtPP2r-OVfG2ZwPUA4ZIE8A')}@{os.getenv('POSTGRESQL_HOST', 'localhost')}:{os.getenv('POSTGRESQL_PORT', '5432')}/pos_operational"

unauthorized_tables = [
    'staging_raw_records',
    'semantic_resolution_log', 
    'noi_canonical_entities',
    'noi_entity_relations',
    'strategic_vectors',
    'data_lineage_tracking',
    'operational_audit_log',
    'org_structure'
]

try:
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()
    
    print("=" * 80)
    print("UNAUTHORIZED TABLES CHECK - milejczyce_operational")
    print("=" * 80)
    
    for table in unauthorized_tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            status = "❌ PRESENT" if count >= 0 else "NOT FOUND"
            print(f"{table:40s} {status} ({count} records)")
        except Exception as e:
            print(f"{table:40s} NOT FOUND")
    
    print("=" * 80)
    conn.close()
except Exception as e:
    print(f"Error: {e}")
