import sqlite3
from pathlib import Path

dbs = [
    'geospatial_registry_test.db',
    'org_structure_test.db', 
    'gmina_staff_test.db',
    'noi_core.db',
    'service_requests_test.db',
    'token_ingestion_test.db'
]

for db_name in dbs:
    db_path = Path('data') / db_name
    print(f"\n{db_name}:")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        if tables:
            for table in tables:
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  - {table}: {count} rows")
        else:
            print("  (no tables found)")
        
        conn.close()
    except Exception as e:
        print(f"  ERROR: {e}")
