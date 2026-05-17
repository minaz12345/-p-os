"""Check Neo4j graph data."""
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv('.env.db')

uri = os.getenv('NEO4J_URI', 'bolt+ssc://localhost:7687')
user = os.getenv('NEO4J_USER', 'neo4j')
password = os.getenv('NEO4J_PASSWORD')

print("=" * 80)
print("NEO4J GRAPH DATA INSPECTION")
print("=" * 80)
print()

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    with driver.session(database='neo4j') as session:
        # Count all nodes
        node_count = session.run("MATCH (n) RETURN count(n) AS count").single()['count']
        print(f"Total Nodes: {node_count}")
        
        # Count all relationships
        rel_count = session.run("MATCH ()-[r]->() RETURN count(r) AS count").single()['count']
        print(f"Total Relationships: {rel_count}")
        
        # Get node labels
        labels_result = session.run("CALL db.labels() YIELD label RETURN collect(label) AS labels")
        labels = labels_result.single()['labels']
        print(f"\nNode Labels ({len(labels)}):")
        for label in sorted(labels):
            count = session.run(f"MATCH (n:{label}) RETURN count(n) AS count").single()['count']
            print(f"   - {label}: {count} nodes")
        
        # Get relationship types
        rel_types_result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) AS types")
        rel_types = rel_types_result.single()['types']
        print(f"\nRelationship Types ({len(rel_types)}):")
        for rel_type in sorted(rel_types):
            count = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS count").single()['count']
            print(f"   - {rel_type}: {count} relationships")
        
        # Sample nodes (first 5)
        if node_count > 0:
            print(f"\nSample Nodes (first 5):")
            sample = session.run("MATCH (n) RETURN labels(n) AS labels, properties(n) AS props LIMIT 5")
            for record in sample:
                print(f"   Labels: {record['labels']}")
                print(f"   Properties: {dict(list(record['props'].items())[:3])}...")  # Show first 3 props
                print()
    
    driver.close()
    print("=" * 80)
    print("✅ NEO4J GRAPH INSPECTION COMPLETE")
    print("=" * 80)
    
except Exception as e:
    print(f"❌ Inspection failed: {e}")
    import traceback
    traceback.print_exc()
    print("=" * 80)
    print("❌ NEO4J GRAPH INSPECTION FAILED")
    print("=" * 80)
