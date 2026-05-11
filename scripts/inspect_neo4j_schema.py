#!/usr/bin/env python3
"""
P-OS v7.5 - Neo4j Schema Inspector
Discovers actual node labels, relationship types, and property names
"""

from neo4j import GraphDatabase
import sys

# Configuration
NEO4J_URI = "bolt+ssc://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "YU54kxF&ahGu@FNQrtNDXlfS%sHkukJD"

def inspect_schema():
    """Inspect Neo4j schema and print detailed report"""
    
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("[OK] Connected to Neo4j successfully\n")
    except Exception as e:
        print(f"[ERROR] Cannot connect to Neo4j: {e}")
        sys.exit(1)
    
    try:
        with driver.session() as session:
            print("=" * 80)
            print("P-OS v7.5 - NEO4J SCHEMA INSPECTION REPORT")
            print("=" * 80)
            print()
            
            # 1. Node Labels
            print("[1] NODE LABELS")
            print("-" * 80)
            result = session.run("CALL db.labels() YIELD label RETURN label ORDER BY label")
            labels = [record['label'] for record in result]
            print(f"Total labels: {len(labels)}\n")
            for label in labels:
                # Count nodes with this label
                count_result = session.run(f"MATCH (n:{label}) RETURN count(n) AS count")
                count = count_result.single()['count']
                
                # Get sample properties
                prop_result = session.run(f"MATCH (n:{label}) RETURN keys(n) AS props LIMIT 1")
                record = prop_result.single()
                props = record['props'] if record else []
                
                print(f"  {label:30s} ({count:4d} nodes)")
                if props:
                    print(f"    Properties: {', '.join(props[:10])}")  # Show first 10
                print()
            
            # 2. Relationship Types
            print("\n[2] RELATIONSHIP TYPES")
            print("-" * 80)
            result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType")
            rel_types = [record['relationshipType'] for record in result]
            print(f"Total relationship types: {len(rel_types)}\n")
            for rel_type in rel_types:
                count_result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS count")
                count = count_result.single()['count']
                print(f"  {rel_type:30s} ({count:4d} relationships)")
            print()
            
            # 3. Property Keys
            print("\n[3] PROPERTY KEYS (Top 50)")
            print("-" * 80)
            result = session.run("CALL db.propertyKeys() YIELD propertyKey RETURN propertyKey ORDER BY propertyKey")
            prop_keys = [record['propertyKey'] for record in result]
            print(f"Total property keys: {len(prop_keys)}\n")
            for key in prop_keys[:50]:  # Show first 50
                print(f"  • {key}")
            if len(prop_keys) > 50:
                print(f"  ... and {len(prop_keys) - 50} more")
            print()
            
            # 4. Focus on Key Labels for Enrichment
            print("\n[4] DETAILED SCHEMA FOR ENRICHMENT TARGETS")
            print("=" * 80)
            
            target_labels = ['Citizen', 'CitizenFeedback', 'LegalBasis', 'LegalArticle', 
                           'Event', 'Location', 'Institution', 'AuditTrail', 'User', 'Risk']
            
            for label in target_labels:
                print(f"\n{label}:")
                print("-" * 40)
                
                # Count
                count_result = session.run(f"MATCH (n:{label}) RETURN count(n) AS count")
                count = count_result.single()['count']
                print(f"  Node count: {count}")
                
                if count > 0:
                    # All unique property keys for this label
                    prop_result = session.run(f"""
                        MATCH (n:{label})
                        UNWIND keys(n) AS key
                        RETURN DISTINCT key
                        ORDER BY key
                    """)
                    props = [record['key'] for record in prop_result]
                    print(f"  Properties: {', '.join(props)}")
                    
                    # Sample data
                    sample_result = session.run(f"MATCH (n:{label}) RETURN n LIMIT 1")
                    sample = sample_result.single()
                    if sample:
                        node = sample['n']
                        print(f"  Sample: {dict(node)}")
            
            # 5. Existing Relationships Between Target Labels
            print("\n\n[5] EXISTING RELATIONSHIPS BETWEEN TARGET LABELS")
            print("=" * 80)
            
            for label1 in target_labels:
                for label2 in target_labels:
                    result = session.run(f"""
                        MATCH (a:{label1})-[r]->(b:{label2})
                        RETURN type(r) AS rel_type, count(r) AS count
                        ORDER BY count DESC
                    """)
                    for record in result:
                        if record['count'] > 0:
                            print(f"  ({label1})-[:{record['rel_type']}]->({label2}): {record['count']}")
            
            print("\n" + "=" * 80)
            print("SCHEMA INSPECTION COMPLETE")
            print("=" * 80)
            
    finally:
        driver.close()

if __name__ == "__main__":
    inspect_schema()
