"""Check constraint integrity in milejczyce_operational."""
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv('.env.db')

conn = psycopg2.connect(
    host=os.getenv('POSTGRESQL_HOST'),
    port=os.getenv('POSTGRESQL_PORT'),
    user=os.getenv('POSTGRESQL_USER'),
    password=os.getenv('POSTGRESQL_PASSWORD'),
    database='milejczyce_operational'
)

cur = conn.cursor()

# Count foreign key constraints
cur.execute("""
    SELECT COUNT(*) 
    FROM information_schema.table_constraints 
    WHERE constraint_schema = 'public' 
    AND constraint_type = 'FOREIGN KEY'
""")
fk_count = cur.fetchone()[0]

# Count CHECK constraints
cur.execute("""
    SELECT COUNT(*) 
    FROM information_schema.check_constraints 
    WHERE constraint_schema = 'public'
""")
check_count = cur.fetchone()[0]

print("=" * 80)
print("CONSTRAINT INTEGRITY CHECK - milejczyce_operational")
print("=" * 80)
print(f"Foreign Key Constraints: {fk_count}")
print(f"CHECK Constraints: {check_count}")
print("=" * 80)

conn.close()
