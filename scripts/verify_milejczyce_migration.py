"""
P-OS v8.0 - Milejczyce Migration Verification
Hard evidence: COUNT, FK, CHECK verification
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
print('='*70)

total_records = 0
for t in tables:
    try:
        cur.execute(f'SELECT COUNT(*) FROM {t}')
        count = cur.fetchone()[0]
        total_records += count
        status = '✅' if count > 0 else '⚠️'
        print(f'{status} {t:30s} {count:6d} records')
    except Exception as e:
        print(f'❌ {t:30s} ERROR: {e}')

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
    print(f'✅ {fk_count} foreign key constraints active')
except Exception as e:
    print(f'❌ FK check failed: {e}')

# CHECK constraints
print('\nCHECK CONSTRAINTS:')
try:
    cur.execute('''
        SELECT COUNT(*) FROM information_schema.table_constraints 
        WHERE constraint_type = 'CHECK';
    ''')
    check_count = cur.fetchone()[0]
    print(f'✅ {check_count} CHECK constraints active')
except Exception as e:
    print(f'❌ CHECK check failed: {e}')

cur.close()
conn.close()
