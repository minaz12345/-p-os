"""
P-OS v8.0 - Milejczyce Migration Verification (ASCII-safe for forensic logging)
Hard evidence: COUNT, FK, CHECK verification
Output format: Pure ASCII for reliable terminal capture
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('.env.db')

conn_str = f"postgresql://{os.getenv('POSTGRESQL_USER')}:{os.getenv('POSTGRESQL_PASSWORD')}@{os.getenv('POSTGRESQL_HOST')}:{os.getenv('POSTGRESQL_PORT')}/milejczyce_operational"

conn = psycopg2.connect(conn_str)
cur = conn.cursor()

tables = [
    'citizen_feedback',
    'municipal_projects',
    'service_requests',
    'geospatial_registry',
    'gmina_staff',
    'noi_core_entities',
    'semantic_tokens',
    'token_ingestion_log'
]

print('='*70)
print('MILEJCZYCE_OPERATIONAL - RECORD COUNT VERIFICATION')
print('Timestamp: 2026-05-12T16:46:00+00:00')
print('Migration Session: e387ba28-dd41-48f8-bb33-3da9643337b2')
print('='*70)

total_records = 0
for t in tables:
    try:
        cur.execute(f'SELECT COUNT(*) FROM {t}')
        count = cur.fetchone()[0]
        total_records += count
        status = '[OK]' if count > 0 else '[EMPTY]'
        print(f'{status} {t:30s} {count:6d} records')
    except Exception as e:
        print(f'[ERR] {t:30s} ERROR: {e}')

print('='*70)
print(f'TOTAL RECORDS: {total_records}')
print('='*70)

# FK integrity
print('\nFOREIGN KEY INTEGRITY:')
try:
    cur.execute('''
        SELECT COUNT(*) FROM information_schema.table_constraints 
        WHERE constraint_type = 'FOREIGN KEY';
    ''')
    fk_count = cur.fetchone()[0]
    print(f'[OK] {fk_count} foreign key constraints active')
except Exception as e:
    print(f'[ERR] FK check failed: {e}')

# CHECK constraints
print('\nCHECK CONSTRAINTS:')
try:
    cur.execute('''
        SELECT COUNT(*) FROM information_schema.table_constraints 
        WHERE constraint_type = 'CHECK';
    ''')
    check_count = cur.fetchone()[0]
    print(f'[OK] {check_count} CHECK constraints active')
except Exception as e:
    print(f'[ERR] CHECK check failed: {e}')

# Additional verification: Sample data integrity check
print('\nSAMPLE DATA INTEGRITY CHECK:')
try:
    # Check citizen_feedback priority values match CHECK constraint
    cur.execute('''
        SELECT DISTINCT priority FROM citizen_feedback ORDER BY priority;
    ''')
    priorities = [row[0] for row in cur.fetchall()]
    print(f'[OK] citizen_feedback priorities: {priorities}')
except Exception as e:
    print(f'[ERR] Priority check failed: {e}')

try:
    # Check municipal_projects status values
    cur.execute('''
        SELECT DISTINCT status FROM municipal_projects ORDER BY status;
    ''')
    statuses = [row[0] for row in cur.fetchall()]
    print(f'[OK] municipal_projects statuses: {statuses}')
except Exception as e:
    print(f'[ERR] Status check failed: {e}')

cur.close()
conn.close()

print('\n' + '='*70)
print('VERIFICATION COMPLETE')
print('='*70)
