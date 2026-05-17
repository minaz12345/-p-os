# Windows UTF-8 enforcement
import sys
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Execute migration event using credentials from .env.db.
import subprocess
from dotenv import load_dotenv
import os

# Load credentials from .env.db (never expose in command line)
load_dotenv('.env.db')

pg_host = os.getenv('POSTGRESQL_HOST', 'localhost')
pg_port = os.getenv('POSTGRESQL_PORT', '5432')
pg_user = os.getenv('POSTGRESQL_USER', 'pos_admin')
pg_password = os.getenv('POSTGRESQL_PASSWORD')
pg_database = 'milejczyce_operational'

# Construct connection string securely
pg_conn_string = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"

print("="*70)
print("EXECUTING FORENSIC MIGRATION EVENT")
print("="*70)
print(f"Database: {pg_database}")
print(f"User: {pg_user}")
print(f"Host: {pg_host}:{pg_port}")
print("="*70)
print()

# Execute migration script
result = subprocess.run(
    ['python', 'scripts/migrate_sqlite_to_postgres.py', '--pg-conn', pg_conn_string],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='replace'
)

# Print output (with UTF-8 encoding)
print(result.stdout)

if result.stderr:
    print("\nSTDERR:")
    print(result.stderr)

# Show last 20 lines as requested
lines = result.stdout.strip().split('\n')
if len(lines) > 20:
    print("\n" + "="*70)
    print("LAST 20 LINES (MIGRATION SUMMARY)")
    print("="*70)
    for line in lines[-20:]:
        print(line)
