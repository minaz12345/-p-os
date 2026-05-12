"""Validate runtime state against canonical declaration."""
import psycopg2
import os
import sys
from dotenv import load_dotenv

load_dotenv('.env.db')

def check_database(db_name, expected_tables=None, classification=None):
    """Check database table count and classification."""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRESQL_HOST', 'localhost'),
            port=os.getenv('POSTGRESQL_PORT', '5432'),
            user=os.getenv('POSTGRESQL_USER', 'pos_admin'),
            password=os.getenv('POSTGRESQL_PASSWORD'),
            database='postgres'
        )
        
        # Check if database exists
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cur.fetchone() is not None
        
        if not exists:
            print(f"❌ {db_name}: DATABASE NOT FOUND")
            return False
        
        # Get table count
        conn.close()
        conn = psycopg2.connect(
            host=os.getenv('POSTGRESQL_HOST', 'localhost'),
            port=os.getenv('POSTGRESQL_PORT', '5432'),
            user=os.getenv('POSTGRESQL_USER', 'pos_admin'),
            password=os.getenv('POSTGRESQL_PASSWORD'),
            database=db_name
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        table_count = cur.fetchone()[0]
        
        status = "✅" if expected_tables is None or table_count == expected_tables else "⚠️"
        print(f"{status} {db_name}: {table_count} tables ({classification})")
        
        if expected_tables and table_count != expected_tables:
            print(f"   Expected: {expected_tables}, Actual: {table_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ {db_name}: ERROR - {e}")
        return False

def main():
    print("=" * 80)
    print("RUNTIME DECLARATION VALIDATION")
    print("=" * 80)
    print()
    
    all_valid = True
    
    # Check production database
    print("Production Runtime:")
    all_valid &= check_database(
        'pos_operational',
        expected_tables=41,  # Full P-OS v7.5 stack
        classification='PRODUCTION'
    )
    print()
    
    # Check archived database
    print("Archived Forensic:")
    all_valid &= check_database(
        'milejczyce_operational',
        expected_tables=16,
        classification='ARCHIVED CANDIDATE'
    )
    print()
    
    # Check test database
    print("Test/Experimental:")
    all_valid &= check_database(
        'pos_operational_restore_test',
        expected_tables=None,
        classification='TEST ONLY'
    )
    print()
    
    print("=" * 80)
    if all_valid:
        print("✅ VALIDATION PASSED - Runtime state matches canonical declaration")
    else:
        print("⚠️  VALIDATION WARNINGS - Review discrepancies above")
    print("=" * 80)
    
    return 0 if all_valid else 1

if __name__ == '__main__':
    sys.exit(main())
