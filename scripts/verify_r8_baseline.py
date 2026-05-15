"""Verify R8 Baseline integrity against live runtime state."""
import psycopg2
import hashlib
import yaml
import sys
from dotenv import load_dotenv
import os

load_dotenv('.env.db', override=True)

def verify_baseline(baseline_path):
    print("=" * 80)
    print("R8 BASELINE VERIFICATION - LIVE RUNTIME CHECK")
    print("=" * 80)
    
    # 1. Load Baseline Document
    with open(baseline_path, 'r', encoding='utf-8') as f:
        baseline = yaml.safe_load(f)
    
    expected_hash = baseline['schema_fingerprint']['hash']
    expected_tables = [t['name'] for t in baseline['enumeration']['tables']]
    
    # 2. Query Live Runtime State
    conn = psycopg2.connect(os.getenv('POSTGRESQL_URI'))
    cur = conn.cursor()
    
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """)
    live_tables = [row[0] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    # 3. Calculate Live Hash
    live_schema_string = "\n".join(live_tables)
    live_hash = hashlib.sha256(live_schema_string.encode('utf-8')).hexdigest()
    
    # 4. Compare
    print(f"Baseline Hash: {expected_hash}")
    print(f"Live Hash:     {live_hash}")
    print(f"Baseline Tables: {len(expected_tables)}")
    print(f"Live Tables:     {len(live_tables)}")
    
    if expected_hash == live_hash and set(expected_tables) == set(live_tables):
        print("\n✅ R8 VERIFICATION PASSED")
        print("   Runtime state matches cryptographic baseline exactly.")
        return True
    else:
        print("\n❌ R8 VERIFICATION FAILED")
        print("   ⚠️  Schema drift detected!")
        
        added = set(live_tables) - set(expected_tables)
        removed = set(expected_tables) - set(live_tables)
        
        if added:
            print(f"   + Added tables: {added}")
        if removed:
            print(f"   - Removed tables: {removed}")
            
        return False

if __name__ == "__main__":
    baseline_file = sys.argv[1] if len(sys.argv) > 1 else "archive/baselines/baseline_v75_reconstructed_20260513.yaml"
    success = verify_baseline(baseline_file)
    sys.exit(0 if success else 1)
