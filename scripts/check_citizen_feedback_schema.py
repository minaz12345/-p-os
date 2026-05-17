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
cursor.execute("""
    SELECT column_name, data_type, is_nullable, column_default 
    FROM information_schema.columns 
    WHERE table_name = 'citizen_feedback' 
    ORDER BY ordinal_position
""")

cols = cursor.fetchall()
print('Table: citizen_feedback')
print('-' * 80)
for c in cols:
    nullable = "NULL" if c[2] == "YES" else "NOT NULL"
    default = c[3] or ""
    print(f"{c[0]:30} {c[1]:25} {nullable:10} {default}")

cursor.close()
conn.close()
