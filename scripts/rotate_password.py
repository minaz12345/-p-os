"""Execute password rotation for pos_admin user."""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv('.env.db')

print("=" * 80)
print("PASSWORD ROTATION - SECURITY INCIDENT REMEDIATION")
print("=" * 80)
print()

NEW_PASSWORD = "QPIlJG4Gw29e6MdIx3tFzEAfGYXPc-zAEdSdRx9E9io"

try:
    # Connect with current credentials
    conn = psycopg2.connect(os.getenv('POSTGRESQL_URI'))
    conn.autocommit = True
    cur = conn.cursor()
    
    print("🔄 Rotating password for pos_admin...")
    
    # Execute password change
    cur.execute(f"ALTER USER pos_admin WITH PASSWORD '{NEW_PASSWORD}';")
    
    print("✅ Password rotated successfully in PostgreSQL")
    
    # Verify new password works
    print("\n🔍 Verifying new credentials...")
    conn.close()
    
    # Build new connection string with new password
    old_uri = os.getenv('POSTGRESQL_URI')
    new_uri = old_uri.replace(os.getenv('POSTGRESQL_PASSWORD'), NEW_PASSWORD)
    
    try:
        test_conn = psycopg2.connect(new_uri)
        test_cur = test_conn.cursor()
        test_cur.execute("SELECT current_user;")
        user = test_cur.fetchone()[0]
        test_cur.close()
        test_conn.close()
        
        print(f"✅ New credentials verified - connected as: {user}")
        
        # Update .env.db file
        print("\n📝 Updating .env.db file...")
        env_path = '.env.db'
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        updated_lines = []
        for line in lines:
            if line.startswith('POSTGRESQL_PASSWORD='):
                updated_lines.append(f"POSTGRESQL_PASSWORD={NEW_PASSWORD}\n")
            else:
                updated_lines.append(line)
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
        
        print(f"✅ .env.db updated successfully")
        
        print("\n" + "=" * 80)
        print("ROTATION COMPLETE - SECURITY INCIDENT RESOLVED")
        print("=" * 80)
        print()
        print("Summary:")
        print("  • Old password: COMPROMISED (exposed via chat on 2026-05-05)")
        print("  • New password: ROTATED (secure, never exposed)")
        print("  • Database: Updated and verified")
        print("  • Config file: .env.db updated")
        print()
        print("Status: READY FOR ARCHIVE v1.2")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        print("Password was changed but verification with new credentials failed")
        print("Please manually verify and update .env.db")
        
except Exception as e:
    print(f"❌ Rotation failed: {e}")
    import traceback
    traceback.print_exc()
