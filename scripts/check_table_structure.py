import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('.env.db')

conn = psycopg2.connect(
    host=os.getenv('POSTGRESQL_HOST', 'localhost'),
    dbname='milejczyce_operational',
    user=os.getenv('POSTGRESQL_USER', 'pos_admin'),
    password=os.getenv('POSTGRESQL_PASSWORD', '')
)

cur = conn.cursor()

cur.execute("""
    SELECT table_name, 
           (SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name=t.table_name) as column_count
    FROM information_schema.tables t 
    WHERE table_schema='public' 
    ORDER BY table_name
""")

results = cur.fetchall()

print("=" * 80)
print("DATABASE SCHEMA INVENTORY - milejczyce_operational")
print("=" * 80)
print(f"{'Table Name':<35} {'Column Count':>15}")
print("-" * 80)

for table_name, column_count in results:
    print(f"{table_name:<35} {column_count:>15}")

print("-" * 80)
print(f"Total tables: {len(results)}")
print("=" * 80)

cur.close()
conn.close()
