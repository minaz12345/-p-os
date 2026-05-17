import sqlite3

conn = sqlite3.connect('data/noi_core.db')

# Check semantic_records
cursor = conn.execute("SELECT DISTINCT category FROM semantic_records")
cats = [r[0] for r in cursor.fetchall()]
print('Entity types (category):', cats)

# Count records
cursor = conn.execute("SELECT COUNT(*) FROM semantic_records")
count = cursor.fetchone()[0]
print(f'Total records: {count}')

# Sample some records
cursor = conn.execute("SELECT category, definition, layer, metadata FROM semantic_records LIMIT 3")
rows = cursor.fetchall()
print('\nSample records:')
for row in rows:
    print(f'  category={row[0]}, layer={row[2]}')
    print(f'    definition={str(row[1])[:50]}')
    print(f'    metadata type={type(row[3])}')

conn.close()
