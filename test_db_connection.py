from dotenv import load_dotenv
import os
import psycopg2

load_dotenv('D:/pos7/.env.db')

password = os.getenv('POSTGRESQL_PASSWORD')
print(f"Password length: {len(password)}")
print(f"First 10 chars: {password[:10]}...")

try:
    conn = psycopg2.connect(
        host='127.0.0.1',
        port=5432,
        dbname='pos_operational',
        user='pos_admin',
        password=password
    )
    print("✅ Connection successful!")
    
    cur = conn.cursor()
    
    # Test 1: Table count
    cur.execute("SELECT schemaname, count(*) FROM pg_tables WHERE schemaname='public' GROUP BY schemaname;")
    tables = cur.fetchall()
    print(f"\nTest 1 - Tables in public schema:")
    for row in tables:
        print(f"  {row[0]}: {row[1]} tables")
    
    # Test 2: Events count
    cur.execute("SELECT COUNT(*) as events_in_db FROM events;")
    events = cur.fetchone()
    print(f"\nTest 2 - Events in DB: {events[0]}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
