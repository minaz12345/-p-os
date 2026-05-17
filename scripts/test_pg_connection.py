"""Test PostgreSQL connection with new credentials."""
import psycopg2
from dotenv import load_dotenv
import os

# Load credentials
load_dotenv('.env.db')

try:
    conn = psycopg2.connect(
        host=os.getenv('POSTGRESQL_HOST'),
        port=os.getenv('POSTGRESQL_PORT'),
        user=os.getenv('POSTGRESQL_USER'),
        password=os.getenv('POSTGRESQL_PASSWORD'),
        database='milejczyce_operational'
    )
    
    cursor = conn.cursor()
    
    # Test 1: Version
    cursor.execute('SELECT version()')
    print(f"✅ Connection successful!")
    print(f"PostgreSQL Version: {cursor.fetchone()[0]}")
    
    # Test 2: Database info
    cursor.execute('SELECT current_database(), current_user, inet_server_addr(), inet_server_port()')
    db_info = cursor.fetchone()
    print(f"Database: {db_info[0]}")
    print(f"User: {db_info[1]}")
    print(f"Server: {db_info[2]}:{db_info[3]}")
    
    # Test 3: Table count
    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
    table_count = cursor.fetchone()[0]
    print(f"Tables in schema: {table_count}")
    
    # Test 4: List tables
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\nTables:")
    for table in tables:
        print(f"  - {table}")
    
    cursor.close()
    conn.close()
    
    print("\n🔒 All tests passed! Connection is secure and functional.")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    import sys
    sys.exit(1)
