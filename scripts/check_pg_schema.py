"""Check PostgreSQL schema structure."""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv('.env.db')

conn = psycopg2.connect(
    host=os.getenv('POSTGRESQL_HOST'),
    port=os.getenv('POSTGRESQL_PORT'),
    user=os.getenv('POSTGRESQL_USER'),
    password=os.getenv('POSTGRESQL_PASSWORD'),
    database='milejczyce_operational'
)

cursor = conn.cursor()

# List all tables
print("="*70)
print("TABLES IN milejczyce_operational")
print("="*70)
cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
tables = [row[0] for row in cursor.fetchall()]
for table in tables:
    print(f"  - {table}")

# Check columns for each table
print("\n" + "="*70)
print("SCHEMA DETAILS")
print("="*70)

for table in tables:
    print(f"\n{table}:")
    cursor.execute(f"""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = '{table}'
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    for col in columns:
        nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
        default = f" DEFAULT {col[3]}" if col[3] else ""
        print(f"  {col[0]:30} {col[1]:20} {nullable}{default}")

cursor.close()
conn.close()
