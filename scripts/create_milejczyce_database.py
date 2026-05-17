"""
Create Milejczyce Operational Database and Apply Schema
========================================================
Purpose: Create milejczyce_operational database and apply canonical schema
Uses: psycopg2 to connect as pos_admin (from .env.db)
"""

# Windows UTF-8 enforcement
import sys
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv
from pathlib import Path

# Load credentials
load_dotenv('.env.db')

# Connection parameters
conn_params = {
    'host': os.getenv('POSTGRESQL_HOST', 'localhost'),
    'port': os.getenv('POSTGRESQL_PORT', '5432'),
    'user': os.getenv('POSTGRESQL_USER', 'pos_admin'),
    'password': os.getenv('POSTGRESQL_PASSWORD')
}

DB_NAME = 'milejczyce_operational'
SCHEMA_FILE = Path('docs/MILEJCZYCE_POSTGRESQL_SCHEMA.sql')

def create_database():
    """Create milejczyce_operational database."""
    print("="*70)
    print("Step 1: Creating Database")
    print("="*70)
    
    # Connect to default 'postgres' database to create new database
    conn_params_copy = conn_params.copy()
    conn_params_copy['database'] = 'postgres'
    
    try:
        conn = psycopg2.connect(**conn_params_copy)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database already exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (DB_NAME,))
        exists = cursor.fetchone()
        
        if exists:
            print(f"⚠️  Database '{DB_NAME}' already exists.")
            print("Dropping and recreating...")
            cursor.execute(f'DROP DATABASE IF EXISTS "{DB_NAME}"')
            print(f"✅ Database '{DB_NAME}' dropped")
        
        # Create new database
        cursor.execute(f'CREATE DATABASE "{DB_NAME}"')
        print(f"✅ Database '{DB_NAME}' created successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False


def apply_schema():
    """Apply canonical schema to milejczyce_operational database."""
    print("\n" + "="*70)
    print("Step 2: Applying Schema")
    print("="*70)
    
    if not SCHEMA_FILE.exists():
        print(f"❌ Schema file not found: {SCHEMA_FILE}")
        return False
    
    # Connect to the new database
    conn_params_copy = conn_params.copy()
    conn_params_copy['database'] = DB_NAME
    
    try:
        conn = psycopg2.connect(**conn_params_copy)
        cursor = conn.cursor()
        
        # Read schema file
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        print(f"📄 Reading schema from: {SCHEMA_FILE}")
        print(f"   File size: {len(schema_sql)} bytes")
        
        # Execute schema
        cursor.execute(schema_sql)
        conn.commit()
        
        print(f"✅ Schema applied successfully to '{DB_NAME}'")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\n📋 Tables created ({len(tables)} total):")
        for table in tables:
            print(f"   - {table}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error applying schema: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*70)
    print("P-OS v8.0 - Milejczyce Database Setup")
    print("="*70)
    print(f"Target Database: {DB_NAME}")
    print(f"Schema File: {SCHEMA_FILE}")
    print(f"User: {conn_params['user']}")
    print(f"Host: {conn_params['host']}:{conn_params['port']}")
    print("="*70)
    print()
    
    # Step 1: Create database
    if not create_database():
        print("\n❌ Database creation failed. Aborting.")
        return
    
    # Step 2: Apply schema
    if not apply_schema():
        print("\n❌ Schema application failed.")
        return
    
    print("\n" + "="*70)
    print("SETUP COMPLETE")
    print("="*70)
    print(f"✅ Database '{DB_NAME}' created and schema applied")
    print(f"✅ Ready for migration (Etap 3)")
    print()
    print("Next step:")
    print(f"  python scripts/migrate_sqlite_to_postgres.py \\")
    print(f"    --pg-conn \"postgresql://{conn_params['user']}:{conn_params['password']}@{conn_params['host']}:{conn_params['port']}/{DB_NAME}\"")
    print("="*70)


if __name__ == '__main__':
    main()
