import sqlite3

conn = sqlite3.connect('data/noi_core.db')
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print('Tables in noi_core.db:')
for t in tables:
    print(f'  {t}')

# Check semantic_records columns
print('\nsemantic_records columns:')
cursor.execute("PRAGMA table_info(semantic_records)")
for col in cursor.fetchall():
    print(f'  {col[1]:30} {col[2]}')

# Check tokens table (if exists)
if 'tokens' in tables:
    print('\ntokens columns:')
    cursor.execute("PRAGMA table_info(tokens)")
    for col in cursor.fetchall():
        print(f'  {col[1]:30} {col[2]}')

conn.close()
