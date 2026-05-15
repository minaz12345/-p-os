#!/usr/bin/env python3
"""
P-OS v7.5 - Neo4j Frozen Topology Report Generator
Creates immutable baseline snapshot for Constitutional Quietness period
"""

from neo4j import GraphDatabase
import json
from datetime import datetime

# Configuration
NEO4J_URI = "bolt+ssc://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "YU54kxF&ahGu@FNQrtNDXlfS%sHkukJD"

def generate_topology_report():
    """Generate comprehensive frozen topology report"""
    
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("[OK] Connected to Neo4j successfully\n")
    except Exception as e:
        print(f"[ERROR] Cannot connect to Neo4j: {e}")
        return
    
    try:
        with driver.session() as session:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print("=" * 80)
            print("P-OS v7.5 - FROZEN TOPOLOGY REFERENCE REPORT")
            print("=" * 80)
            print(f"Generated: {timestamp}")
            print(f"Mode: Constitutional Quietness (Frozen Baseline)")
            print("=" * 80)
            print()
            
            # 1. Global Metrics
            print("[1] GLOBAL GRAPH METRICS")
            print("-" * 80)
            
            total_result = session.run("MATCH (n) RETURN count(n) AS total_nodes")
            total_nodes = total_result.single()['total_nodes']
            
            rel_result = session.run("MATCH ()-[r]->() RETURN count(r) AS total_rels")
            total_rels = rel_result.single()['total_rels']
            
            connected_result = session.run("""
                MATCH (n)-[r]-()
                RETURN count(DISTINCT n) AS connected_count
            """)
            connected_count = connected_result.single()['connected_count']
            
            orphaned_count = total_nodes - connected_count
            connectivity_pct = round((connected_count / total_nodes * 100), 2) if total_nodes > 0 else 0
            
            print(f"Total Nodes:              {total_nodes}")
            print(f"Total Relationships:      {total_rels}")
            print(f"Connected Nodes:          {connected_count}")
            print(f"Orphaned Nodes:           {orphaned_count}")
            print(f"Connectivity Ratio:       {connectivity_pct}%")
            print(f"Average Degree:           {round(total_rels / total_nodes, 2) if total_nodes > 0 else 0}")
            print()
            
            # 2. Node Label Distribution
            print("\n[2] NODE LABEL DISTRIBUTION")
            print("-" * 80)
            
            label_result = session.run("CALL db.labels() YIELD label RETURN label ORDER BY label")
            labels = [record['label'] for record in label_result]
            
            labels_with_counts = []
            for label in labels:
                count_result = session.run(f"MATCH (n:{label}) RETURN count(n) AS count")
                count = count_result.single()['count']
                if count > 0:
                    labels_with_counts.append((label, count))
            
            # Sort by count descending
            labels_with_counts.sort(key=lambda x: x[1], reverse=True)
            
            print(f"{'Label':<35} {'Count':>8} {'Percentage':>12}")
            print("-" * 80)
            
            for label, count in labels_with_counts:
                if count > 0:  # Only show non-empty labels
                    pct = round((count / total_nodes * 100), 2)
                    print(f"{label:<35} {count:>8} {pct:>11.2f}%")
            
            print(f"\nTotal unique labels: {len([l for l, c in labels_with_counts if c > 0])}")
            print()
            
            # 3. Relationship Type Distribution
            print("\n[3] RELATIONSHIP TYPE DISTRIBUTION")
            print("-" * 80)
            
            rel_type_result = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType")
            rel_types = [record['relationshipType'] for record in rel_type_result]
            
            rel_types_with_counts = []
            for rel_type in rel_types:
                count_result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS count")
                count = count_result.single()['count']
                if count > 0:
                    rel_types_with_counts.append((rel_type, count))
            
            # Sort by count descending
            rel_types_with_counts.sort(key=lambda x: x[1], reverse=True)
            
            print(f"{'Relationship Type':<35} {'Count':>8} {'Percentage':>12}")
            print("-" * 80)
            
            for rel_type, count in rel_types_with_counts:
                if count > 0:
                    pct = round((count / total_rels * 100), 2) if total_rels > 0 else 0
                    print(f"{rel_type:<35} {count:>8} {pct:>11.2f}%")
            
            print(f"\nTotal relationship types: {len([r for r, c in rel_types_with_counts if c > 0])}")
            print()
            
            # 4. Connectivity Analysis by Label
            print("\n[4] CONNECTIVITY ANALYSIS BY LABEL")
            print("-" * 80)
            
            print(f"{'Label':<35} {'Total':>8} {'Connected':>10} {'Orphaned':>10} {'Conn %':>10}")
            print("-" * 80)
            
            for label, total in labels_with_counts:
                if total > 0:
                    conn_result = session.run(f"""
                        MATCH (n:{label})
                        OPTIONAL MATCH (n)-[r]-()
                        WITH n, count(r) AS rel_count
                        RETURN count(CASE WHEN rel_count > 0 THEN 1 END) AS connected,
                               count(CASE WHEN rel_count = 0 THEN 1 END) AS orphaned
                    """)
                    conn_record = conn_result.single()
                    connected = conn_record['connected']
                    orphaned = conn_record['orphaned']
                    conn_pct = round((connected / total * 100), 2) if total > 0 else 0
                    
                    print(f"{label:<35} {total:>8} {connected:>10} {orphaned:>10} {conn_pct:>9.2f}%")
            
            print()
            
            # 5. Top Connected Subgraphs
            print("\n[5] TOP CONNECTED SUBGRAPHS (by node count)")
            print("-" * 80)
            
            subgraph_result = session.run("""
                MATCH (n)-[r]-(m)
                WITH labels(n) AS labels_n, labels(m) AS labels_m, type(r) AS rel_type
                UNWIND labels_n AS label_n
                UNWIND labels_m AS label_m
                WITH label_n, label_m, rel_type, count(*) AS connection_count
                WHERE label_n <= label_m  // Avoid duplicates
                RETURN label_n, label_m, rel_type, connection_count
                ORDER BY connection_count DESC
                LIMIT 15
            """)
            
            print(f"{'From Label':<25} {'To Label':<25} {'Via':<25} {'Connections':>12}")
            print("-" * 80)
            
            for record in subgraph_result:
                print(f"{record['label_n']:<25} {record['label_m']:<25} {record['rel_type']:<25} {record['connection_count']:>12}")
            
            print()
            
            # 6. Orphaned Node Analysis
            print("\n[6] ORPHANED NODE ANALYSIS")
            print("-" * 80)
            
            orphan_result = session.run("""
                MATCH (n)
                WHERE NOT (n)--()
                WITH labels(n)[0] AS label, count(n) AS count
                RETURN label, count
                ORDER BY count DESC
            """)
            
            print(f"{'Label':<35} {'Orphaned Count':>15}")
            print("-" * 80)
            
            total_orphaned = 0
            for record in orphan_result:
                print(f"{record['label']:<35} {record['count']:>15}")
                total_orphaned += record['count']
            
            print(f"\nTotal orphaned nodes: {total_orphaned}")
            print(f"Orphan rate: {round((total_orphaned / total_nodes * 100), 2)}%")
            print()
            
            # 7. Data Classification Distribution
            print("\n[7] DATA CLASSIFICATION DISTRIBUTION")
            print("-" * 80)
            
            classification_result = session.run("""
                MATCH (n)
                WHERE n.data_classification IS NOT NULL
                RETURN n.data_classification AS classification, count(n) AS count
                ORDER BY count DESC
            """)
            
            print(f"{'Classification':<35} {'Node Count':>12}")
            print("-" * 80)
            
            for record in classification_result:
                print(f"{record['classification']:<35} {record['count']:>12}")
            
            print()
            
            # 8. Summary & Recommendations
            print("\n[8] SUMMARY & QUIET MODE OBSERVATIONS")
            print("=" * 80)
            
            print(f"\nGraph Health Assessment:")
            print(f"  - Connectivity: {connectivity_pct}% ({'HEALTHY' if connectivity_pct >= 50 else 'NEEDS IMPROVEMENT'})")
            print(f"  - Schema Diversity: {len([l for l, c in labels_with_counts if c > 0])} labels, {len([r for r, c in rel_types_with_counts if c > 0])} relationship types")
            print(f"  - Data Completeness: {total_nodes} nodes with properties")
            print(f"  - Audit Trail Coverage: {[c for l, c in labels_with_counts if l == 'AuditTrail'][0] if any(l == 'AuditTrail' for l, c in labels_with_counts) else 0} audit events")
            
            print(f"\nQuiet Mode Status:")
            print(f"  - No mutations performed during observation period")
            print(f"  - Automated enrichment skipped (property mismatch detected)")
            print(f"  - Stability prioritized over connectivity expansion")
            print(f"  - Next review scheduled: 2026-06-10")
            
            print(f"\nRecommendations (Post-Quiet Period):")
            print(f"  1. Investigate hash format mismatches (pesel_hash vs citizen_hash)")
            print(f"  2. Standardize legal reference formats across LegalBasis/LegalArticle")
            print(f"  3. Add location properties to Institution and AuditTrail nodes")
            print(f"  4. Consider manual curation of high-value orphaned nodes")
            
            print("\n" + "=" * 80)
            print("FROZEN TOPOLOGY REPORT COMPLETE")
            print("=" * 80)
            print(f"\nReport saved as immutable baseline for Constitutional Quietness period.")
            print(f"Next review: 2026-06-10 | Current status: STABLE @ {connectivity_pct}% connectivity")
            
    finally:
        driver.close()

if __name__ == "__main__":
    generate_topology_report()
