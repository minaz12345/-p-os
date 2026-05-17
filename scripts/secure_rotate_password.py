"""Secure password rotation for pos_admin user.

This script rotates the PostgreSQL password without exposing credentials in logs.
It reads the OLD password from stdin (secure input) and generates a new one.
"""
import psycopg2
import secrets
import string
import sys
from getpass import getpass

def rotate_password():
    print("=" * 80)
    print("SECURE PASSWORD ROTATION - P-OS v7.5")
    print("=" * 80)
    print()
    
    # Get old password securely (not echoed to terminal)
    print("Enter CURRENT PostgreSQL password for pos_admin:")
    old_password = getpass("Current password: ")
    
    if not old_password:
        print("❌ No password provided. Aborting.")
        return False
    
    # Generate new secure password
    new_password = ''.join(secrets.choice(string.ascii_letters + string.digits + "-_.~") for _ in range(48))
    
    print(f"\n🔄 Attempting to connect with current credentials...")
    
    try:
        # Connect with current credentials
        conn = psycopg2.connect(
            host='127.0.0.1',  # Use IP instead of localhost to avoid SSL issues
            port=5432,
            dbname='pos_operational',
            user='pos_admin',
            password=old_password
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        print("✅ Connected successfully")
        print(f"🔄 Rotating password...")
        
        # Execute password change
        cur.execute("ALTER USER pos_admin WITH PASSWORD %s;", (new_password,))
        
        print("✅ Password rotated successfully in PostgreSQL")
        
        # Verify new password works
        print("\n🔍 Verifying new credentials...")
        conn.close()
        
        try:
            test_conn = psycopg2.connect(
                host='127.0.0.1',
                port=5432,
                dbname='pos_operational',
                user='pos_admin',
                password=new_password
            )
            test_cur = test_conn.cursor()
            test_cur.execute("SELECT current_user;")
            user = test_cur.fetchone()[0]
            test_cur.close()
            test_conn.close()
            
            print(f"✅ New credentials verified - connected as: {user}")
            
            # Update .env.db file
            print("\n📝 Updating .env.db file...")
            env_path = 'd:/pos7/.env.db'
            
            with open(env_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            updated_lines = []
            for line in lines:
                if line.startswith('POSTGRESQL_PASSWORD='):
                    updated_lines.append(f"POSTGRESQL_PASSWORD={new_password}\n")
                elif line.startswith('POSTGRESQL_URI='):
                    # Update URI with new password (URL-encode if needed)
                    from urllib.parse import quote
                    encoded_password = quote(new_password, safe='')
                    updated_lines.append(f"POSTGRESQL_URI=postgresql://pos_admin:{encoded_password}@localhost:5432/pos_operational\n")
                else:
                    updated_lines.append(line)
            
            with open(env_path, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
            
            print(f"✅ .env.db updated successfully")
            
            print("\n" + "=" * 80)
            print("ROTATION COMPLETE")
            print("=" * 80)
            print()
            print("Summary:")
            print("  • Database: Password updated and verified")
            print("  • Config file: .env.db updated")
            print("  • New password: Generated (48 chars, never exposed)")
            print()
            print("⚠️  IMPORTANT: Restart any running services (e.g., gateway_mvp.py)")
            print("=" * 80)
            
            return True
            
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            print("Password was changed but verification with new credentials failed")
            print("Please manually verify and update .env.db")
            return False
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        print("\nPossible causes:")
        print("  • Wrong current password")
        print("  • PostgreSQL service not running")
        print("  • Network/firewall blocking connection")
        return False
    except Exception as e:
        print(f"❌ Rotation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = rotate_password()
    sys.exit(0 if success else 1)
