"""Check SQLite table structures for column mapping."""
import sqlite3
from pathlib import Path

data_dir = Path('data')

sqlite_dbs = {
    'citizen_feedback_test.db': 'citizen_feedback',
    'municipal_projects_test.db': 'municipal_projects',
    'geospatial_registry_test.db': 'geospatial_nodes',
    'org_structure_test.db': 'employees',
    'gmina_staff_test.db': 'staff_directory',
    'noi_core.db': 'semantic_records',
    'service_requests_test.db': 'service_requests_backup',
    'token_ingestion_test.db': 'ingested_tokens',
}

print("="*70)
print("SQLITE TABLE SCHEMAS")
print("="*70)

for db_file, table_name in sqlite_dbs.items():
    db_path = data_dir / db_file
    if not db_path.exists():
        print(f"\n⚠️  {db_file} - NOT FOUND")
        continue
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if not cursor.fetchone():
        print(f"\n⚠️  {db_file}.{table_name} - TABLE NOT FOUND")
        conn.close()
        continue
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]
    
    print(f"\n{db_file}.{table_name} ({row_count} rows):")
    
    # Get columns
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]:30} {col[2]:20} {'NOT NULL' if col[3] else 'NULL'}")
    
    conn.close()
