"""Check events table schema."""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv('.env.db')

conn = psycopg2.connect(os.getenv('POSTGRESQL_URI'))
cur = conn.cursor()

cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'events' 
    ORDER BY ordinal_position
""")
cols = cur.fetchall()

print("Events table columns:")
for col_name, data_type in cols:
    print(f"  - {col_name}: {data_type}")

# Check for hash-related columns
hash_cols = [c[0] for c in cols if 'hash' in c[0].lower()]
print(f"\nHash-related columns: {hash_cols}")

cur.close()
conn.close()
