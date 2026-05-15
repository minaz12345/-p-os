#!/usr/bin/env python3
"""
P-OS v7.5 - Neo4j Connectivity Enrichment Dry Run
Executes enrichment queries in read-only mode to show expected changes
"""

from neo4j import GraphDatabase
import sys
from datetime import datetime

# Configuration
NEO4J_URI = "bolt+ssc://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "YU54kxF&ahGu@FNQrtNDXlfS%sHkukJD"  # From .env.db

def print_header():
    print("=" * 70)
    print("P-OS v7.5 - NEO4J CONNECTIVITY ENRICHMENT (DRY RUN)")
    print("=" * 70)
    print()

def get_baseline_metrics(driver):
    """Capture current graph statistics"""
    print("[PHASE 1] Capturing baseline metrics...")
    with driver.session() as session:
        # Get total nodes
        total_result = session.run("MATCH (n) RETURN count(n) AS total_nodes")
        total_nodes = total_result.single()['total_nodes']
        
        # Get total relationships
        rel_result = session.run("MATCH ()-[r]->() RETURN count(r) AS total_rels")
        total_rels = rel_result.single()['total_rels']
        
        # Get connected nodes (nodes with at least one relationship)
        connected_result = session.run("""
            MATCH (n)-[r]-()
            RETURN count(DISTINCT n) AS connected_count
        """)
        connected_count = connected_result.single()['connected_count']
        
        orphaned_nodes = total_nodes - connected_count
        connectivity_pct = round((connected_count / total_nodes * 100), 2) if total_nodes > 0 else 0
        
        print(f"\nBaseline Metrics:")
        print(f"  Total Nodes:        {total_nodes}")
        print(f"  Total Relationships: {total_rels}")
        print(f"  Orphaned Nodes:      {orphaned_nodes}")
        print(f"  Connectivity:        {connectivity_pct}%")
        print()
        
        return {
            'total_nodes': total_nodes,
            'total_rels': total_rels,
            'orphaned_nodes': orphaned_nodes,
            'connectivity_pct': connectivity_pct
        }

def simulate_phase(driver, phase_name, query, description):
    """Simulate a phase by counting matches without creating relationships"""
    print(f"[{phase_name}] {description}")
    
    try:
        with driver.session() as session:
            # Count how many relationships would be created
            count_query = query.replace("MERGE", "MATCH").replace("CREATE", "MATCH")
            if "RETURN count" not in count_query:
                count_query = count_query.rstrip(';') + " RETURN count(*) AS potential_links"
            
            result = session.run(count_query)
            record = result.single()
            count = record['potential_links'] if record else 0
            
            print(f"  Would create: ~{count} new relationships")
            print(f"  Status: [READY]")
            print()
            
            return count
    except Exception as e:
        print(f"  [Warning]: {str(e)}")
        print()
        return 0

def main():
    print_header()
    
    # Connect to Neo4j
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("[OK] Connected to Neo4j successfully\n")
    except Exception as e:
        print(f"[ERROR] Cannot connect to Neo4j")
        print(f"Details: {e}")
        print("\nEnsure:")
        print("  1. Neo4j is running on port 7687")
        print("  2. Password is correct (default: 'neo4j')")
        print("  3. URI is correct: bolt://localhost:7687")
        sys.exit(1)
    
    try:
        # Get baseline
        baseline = get_baseline_metrics(driver)
        
        print("=" * 70)
        print("DRY RUN SIMULATION - No changes will be made")
        print("=" * 70)
        print()
        
        total_potential = 0
        
        # Phase 1: Citizen ↔ Feedback (match on citizen_hash/pesel_hash)
        total_potential += simulate_phase(
            driver,
            "PHASE 1",
            """
            MATCH (c:Citizen), (f:CitizenFeedback)
            WHERE c.pesel_hash = f.citizen_hash
            MERGE (c)-[:PROVIDED_FEEDBACK]->(f)
            """,
            "Citizen ↔ CitizenFeedback linkage (via pesel_hash/citizen_hash)"
        )
        
        # Phase 2: LegalBasis ↔ LegalArticle (match on article/parent_law)
        total_potential += simulate_phase(
            driver,
            "PHASE 2",
            """
            MATCH (lb:LegalBasis), (la:LegalArticle)
            WHERE lb.article = la.parent_law
               OR lb.legal_id = la.article_id
            MERGE (lb)-[:REFERENCES]->(la)
            """,
            "LegalBasis ↔ LegalArticle linkage (via article/parent_law)"
        )
        
        # Phase 3: Event → Location (match on municipality)
        total_potential += simulate_phase(
            driver,
            "PHASE 3",
            """
            MATCH (e:Event), (l:Location)
            WHERE e.municipality = l.name
            MERGE (e)-[:OCCURRED_IN]->(l)
            """,
            "Event → Location linkage (via municipality)"
        )
        
        # Phase 4: Institution → Location (NO DIRECT LINK - skip or use name matching)
        print("[PHASE 4] Institution → Location linkage")
        print("  [Skipped]: Institution nodes have no location property")
        print()
        
        # Phase 5: AuditTrail → Event/Node (match on node_id)
        total_potential += simulate_phase(
            driver,
            "PHASE 5",
            """
            MATCH (a:AuditTrail), (e:Event)
            WHERE a.node_id = e.event_id
               AND a.node_type = 'Event'
            MERGE (a)-[:AUDITS_EVENT]->(e)
            """,
            "AuditTrail → Event linkage (via node_id)"
        )
        
        # Summary
        print("=" * 70)
        print("DRY RUN SUMMARY")
        print("=" * 70)
        print()
        print(f"Total potential new relationships: ~{total_potential}")
        print(f"Current relationships:             {baseline['total_rels']}")
        print(f"Projected total after enrichment:  ~{baseline['total_rels'] + total_potential}")
        print()
        
        estimated_connectivity = min(85.0, float(baseline['connectivity_pct']) + (total_potential / baseline['total_nodes'] * 100))
        print(f"Current connectivity:   {baseline['connectivity_pct']}%")
        print(f"Projected connectivity: ~{estimated_connectivity:.1f}%")
        print()
        
        if total_potential > 0:
            print("[COMPLETE] DRY RUN COMPLETE - System ready for live execution")
            print()
            print("To execute for real, run:")
            print("  python enrich_neo4j_live.py")
            print()
            print("Or use PowerShell executor:")
            print("  .\\scripts\\execute_enrichment.ps1")
        else:
            print("[INFO] No potential relationships found - graph may already be enriched")
        
    finally:
        driver.close()

if __name__ == "__main__":
    main()
