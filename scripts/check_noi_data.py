import sqlite3

conn = sqlite3.connect('data/noi_core_test.db')

# List tables
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print('Tables:', tables)

# Check semantic_records if it exists
if 'semantic_records' in tables:
    cursor = conn.execute('SELECT DISTINCT category FROM semantic_records')
    cats = [r[0] for r in cursor.fetchall()]
    print('\nEntity types (category):', cats)
else:
    print('\nsemantic_records table not found')
    
    # Try to find what table has the data
    for table in tables:
        cursor = conn.execute(f"PRAGMA table_info({table})")
        cols = [r[1] for r in cursor.fetchall()]
        if 'category' in cols or 'entity_type' in cols:
            print(f'\n{table} has relevant columns: {cols}')
            cursor = conn.execute(f"SELECT DISTINCT {cols[0]} FROM {table} LIMIT 5")
            vals = [r[0] for r in cursor.fetchall()]
            print(f'  Sample values: {vals}')

conn.close()
