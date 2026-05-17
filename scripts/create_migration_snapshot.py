"""
P-OS v8.0 - Migration Hash Snapshot Generator
===============================================
Purpose: Create forensic hash snapshots before migration
Output: Snapshot file with SHA-256 hashes, row counts, schema signatures

This ensures forensic reproducibility of the migration event.
"""

import sqlite3
import hashlib
from pathlib import Path
import json
from datetime import datetime, timezone


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of entire file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_table_schema_signature(db_path: Path, table_name: str) -> str:
    """Get schema signature for a table (column names and types)."""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    # Create deterministic signature
    schema_sig = '|'.join([f"{col[1]}:{col[2]}" for col in sorted(columns, key=lambda x: x[1])])
    conn.close()
    
    return hashlib.md5(schema_sig.encode()).hexdigest()[:16]


def snapshot_database(db_path: Path):
    """Create forensic snapshot of a SQLite database."""
    print(f"\n{'='*70}")
    print(f"Snapshotting: {db_path.name}")
    print(f"{'='*70}")
    
    snapshot = {
        'database': db_path.name,
        'file_path': str(db_path),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'file_hash_sha256': compute_file_hash(db_path),
        'file_size_bytes': db_path.stat().st_size,
        'tables': {}
    }
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table_name in tables:
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            # Get schema signature
            schema_sig = get_table_schema_signature(db_path, table_name)
            
            # Get sample hash (hash of first 10 rows for quick verification)
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 10")
            rows = cursor.fetchall()
            sample_hash = hashlib.md5(str(rows).encode()).hexdigest()[:16] if rows else 'empty'
            
            snapshot['tables'][table_name] = {
                'row_count': row_count,
                'schema_signature': schema_sig,
                'sample_hash_first_10': sample_hash
            }
        
        conn.close()
        
        print(f"  File Hash (SHA-256): {snapshot['file_hash_sha256'][:32]}...")
        print(f"  File Size: {snapshot['file_size_bytes']} bytes")
        print(f"  Tables: {len(tables)}")
        
        for table_name, info in snapshot['tables'].items():
            print(f"    - {table_name}: {info['row_count']} rows (schema: {info['schema_signature']})")
        
        return snapshot
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None


def main():
    print("="*70)
    print("P-OS v8.0 - Migration Hash Snapshot Generator")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("="*70)
    
    # Define databases to snapshot
    db_files = [
        'citizen_feedback_test.db',
        'municipal_projects_test.db',
        'geospatial_registry_test.db',
        'org_structure_test.db',
        'gmina_staff_test.db',
        'noi_core.db',
        'service_requests_test.db',
        'semantic_tokens_test.db',
        'token_ingestion_test.db',
    ]
    
    snapshots = []
    
    for db_file in db_files:
        db_path = Path('data') / db_file
        
        if not db_path.exists():
            print(f"\n⚠️  Skipping {db_file}: File not found")
            continue
        
        snapshot = snapshot_database(db_path)
        if snapshot:
            snapshots.append(snapshot)
    
    # Save snapshot to file
    snapshot_file = Path('data/migration_snapshot.json')
    with open(snapshot_file, 'w', encoding='utf-8') as f:
        json.dump(snapshots, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*70)
    print("SNAPSHOT SUMMARY")
    print("="*70)
    print(f"Total databases snapshotted: {len(snapshots)}")
    print(f"Snapshot saved to: {snapshot_file}")
    print(f"\nThis snapshot serves as forensic evidence for:")
    print(f"  - Source data integrity verification")
    print(f"  - Post-migration equivalence validation")
    print(f"  - Audit trail in data_lineage_tracking")
    print("="*70)


if __name__ == '__main__':
    main()
