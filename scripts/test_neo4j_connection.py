"""Test Neo4j connection."""
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv('.env.db')

uri = os.getenv('NEO4J_URI', 'bolt+ssc://localhost:7687')
user = os.getenv('NEO4J_USER', 'neo4j')
password = os.getenv('NEO4J_PASSWORD')

print("=" * 80)
print("NEO4J CONNECTION TEST")
print("=" * 80)
print(f"URI: {uri}")
print(f"User: {user}")
print()

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    with driver.session() as session:
        result = session.run("RETURN 'Neo4j is connected!' AS message")
        record = result.single()
        print(f"✅ Connection successful!")
        print(f"   Message: {record['message']}")
        
        # Check databases
        db_result = session.run("SHOW DATABASES")
        databases = [record['name'] for record in db_result]
        print(f"\n📊 Available Databases ({len(databases)}):")
        for db in databases:
            print(f"   - {db}")
    
    driver.close()
    print("\n" + "=" * 80)
    print("✅ NEO4J VERIFICATION PASSED")
    print("=" * 80)
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\n" + "=" * 80)
    print("❌ NEO4J VERIFICATION FAILED")
    print("=" * 80)
