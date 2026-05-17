import sqlite3

conn = sqlite3.connect('data/geospatial_registry_test.db')

# Check for empty strings in numeric fields
cursor = conn.execute("SELECT COUNT(*) FROM geospatial_nodes WHERE area_m2 = '' OR location_lat = '' OR location_lon = ''")
count = cursor.fetchone()[0]
print(f'Records with empty strings in numeric fields: {count}')

# Check all columns for any data issues
cursor = conn.execute("PRAGMA table_info(geospatial_nodes)")
columns = cursor.fetchall()
print('\nColumns:')
for col in columns:
    print(f'  {col[1]} ({col[2]})')

# Sample some records to see if there are any issues
cursor = conn.execute("SELECT * FROM geospatial_nodes LIMIT 3")
rows = cursor.fetchall()
print('\nSample records:')
for row in rows:
    print(f'  {row}')

conn.close()
