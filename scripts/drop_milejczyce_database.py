"""Drop milejczyce_operational database to restore constitutional compliance."""
import psycopg2
from dotenv import load_dotenv
import os
import sys

load_dotenv('.env.db')

print("=" * 80)
print("CONSTITUTIONAL COMPLIANCE: Dropping unauthorized database")
print("=" * 80)
print()
print("WARNING: This will DROP the milejczyce_operational database")
print("All 16 tables and their data will be permanently deleted.")
print()
print("This is required to restore constitutional compliance.")
print("The 8 authorized tables exist in pos_operational database.")
print()

confirm = input("Type 'DROP DATABASE' to confirm: ")

if confirm.strip() != 'DROP DATABASE':
    print("Aborted. Database not dropped.")
    sys.exit(1)

try:
    # Connect to postgres database to drop milejczyce_operational
    conn = psycopg2.connect(
        host=os.getenv('POSTGRESQL_HOST'),
        port=os.getenv('POSTGRESQL_PORT'),
        user=os.getenv('POSTGRESQL_USER'),
        password=os.getenv('POSTGRESQL_PASSWORD'),
        database='postgres'
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    # Terminate all connections to milejczyce_operational
    print("Terminating active connections...")
    cur.execute("""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = 'milejczyce_operational'
        AND pid <> pg_backend_pid();
    """)
    
    # Drop the database
    print("Dropping milejczyce_operational database...")
    cur.execute("DROP DATABASE IF EXISTS milejczyce_operational")
    
    print("✅ Database dropped successfully")
    print()
    print("Constitutional compliance restored.")
    print("Only pos_operational database remains with 8 authorized tables.")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
