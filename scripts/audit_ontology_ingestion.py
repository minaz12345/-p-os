#!/usr/bin/env python3
"""
P-OS v7.5 - Post-Ingestion Topology Audit
Verifies the impact of the NOI-O1 Ontology Ingestion.
"""

from neo4j import GraphDatabase

NEO4J_URI = "bolt+ssc://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "YU54kxF&ahGu@FNQrtNDXlfS%sHkukJD"

def audit_ingestion():
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        
        with driver.session() as session:
            print("=" * 80)
            print("POST-INGESTION TOPOLOGY AUDIT")
            print("=" * 80)
            
            # 1. New Nodes Count
            print("\n[1] NEW NODES CREATED BY ONTOLOGY")
            print("-" * 80)
            new_labels = ['Person', 'HistoricalEvent', 'Project', 'Commission', 'Concept']
            for label in new_labels:
                res = session.run(f"MATCH (n:{label}) RETURN count(n) AS count")
                count = res.single()['count']
                if count > 0:
                    print(f"  {label:<25} : {count}")

            # 2. Relationship Impact
            print("\n[2] NEW RELATIONSHIPS ESTABLISHED")
            print("-" * 80)
            new_rels = ['DELEGATES_TO', 'CHAIRS', 'REQUIRES', 'AIMS_TO_CREATE']
            for rel in new_rels:
                res = session.run(f"MATCH ()-[r:{rel}]->() RETURN count(r) AS count")
                count = res.single()['count']
                if count > 0:
                    print(f"  :{rel:<20} : {count}")

            # 3. Orphan Reduction Check
            print("\n[3] ORPHAN STATUS CHECK")
            print("-" * 80)
            total_res = session.run("MATCH (n) RETURN count(n) AS total")
            total = total_res.single()['total']
            
            conn_res = session.run("MATCH (n)-[r]-() RETURN count(DISTINCT n) AS connected")
            connected = conn_res.single()['connected']
            
            orphaned = total - connected
            pct = round((connected / total * 100), 2)
            
            print(f"  Total Nodes:       {total}")
            print(f"  Connected Nodes:   {connected}")
            print(f"  Orphaned Nodes:    {orphaned}")
            print(f"  Connectivity:      {pct}%")

            # 4. Specific Entity Verification
            print("\n[4] KEY ENTITY VERIFICATION")
            print("-" * 80)
            entities = [
                ("Sebastian Sawicki", "Person"),
                ("Status Uzdrowiska", "Project"),
                ("Bulla Gnieźnieńska", "HistoricalEvent"),
                ("OSP Milejczyce", "CommunityOrganization")
            ]
            for name, label in entities:
                res = session.run(f"MATCH (n:{label} {{name: '{name}'}}) RETURN n")
                if res.single():
                    print(f"  [OK] {name} ({label}) found and indexed.")
                else:
                    print(f"  [MISSING] {name} ({label}) not found!")

            print("\n" + "=" * 80)
            print("AUDIT COMPLETE")
            print("=" * 80)

    finally:
        driver.close()

if __name__ == "__main__":
    audit_ingestion()
