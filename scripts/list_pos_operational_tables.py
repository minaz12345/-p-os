"""List tables in pos_operational database."""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv('.env.db')

conn = psycopg2.connect(
    host=os.getenv('POSTGRESQL_HOST'),
    port=os.getenv('POSTGRESQL_PORT'),
    user=os.getenv('POSTGRESQL_USER'),
    password=os.getenv('POSTGRESQL_PASSWORD'),
    database='pos_operational'
)

cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
tables = [row[0] for row in cur.fetchall()]

print(f"Tables in pos_operational ({len(tables)}):")
for table in tables:
    print(f"  - {table}")

conn.close()
