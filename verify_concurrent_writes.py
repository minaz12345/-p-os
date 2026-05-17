from dotenv import load_dotenv
import os
import psycopg2

load_dotenv('D:/pos7/.env.db')

conn = psycopg2.connect(
    host='127.0.0.1',
    port=5432,
    dbname='pos_operational',
    user='pos_admin',
    password=os.getenv('POSTGRESQL_PASSWORD')
)

cur = conn.cursor()

# Check ALL recent requests (last 10 minutes)
cur.execute("""
    SELECT COUNT(*) 
    FROM gdpr_erasure_requests 
    WHERE deadline > NOW() - INTERVAL '72 hours'
""")

count = cur.fetchone()[0]
print(f"✅ Total recent requests (last 72h): {count}")

# Show last 15 requests
cur.execute("""
    SELECT request_id, user_id, status, deadline
    FROM gdpr_erasure_requests 
    ORDER BY deadline DESC
    LIMIT 15
""")

rows = cur.fetchall()
print(f"\n📋 Details:")
for row in rows:
    print(f"  {row[0]} | {row[1]} | {row[2]} | {row[3]}")

cur.close()
conn.close()
