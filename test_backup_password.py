import psycopg2
import sys

# Test Backup 2 password (54 chars)
backup2_password = "XWBYAqOs03VH1L-gDjGuSpPC1BoN1ZTTtPP2r-OVfG2ZwPUA4ZIE8A"

print("Testing Backup 2 password (54 chars, from May 13 19:50)...")
try:
    conn = psycopg2.connect(
        host='127.0.0.1',
        port=5432,
        dbname='pos_operational',
        user='pos_admin',
        password=backup2_password
    )
    print("✅ SUCCESS - Backup 2 password WORKS!")
    
    cur = conn.cursor()
    cur.execute("SELECT current_user, now();")
    row = cur.fetchone()
    print(f"   Connected as: {row[0]}")
    print(f"   Server time: {row[1]}")
    
    cur.execute("SELECT COUNT(*) FROM gdpr_erasure_requests;")
    count = cur.fetchone()[0]
    print(f"   Erasure requests in DB: {count}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ FAILED - Backup 2 password does not work")
    print(f"   Error: {str(e)[:100]}")
    sys.exit(1)
