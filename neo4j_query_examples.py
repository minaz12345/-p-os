#!/usr/bin/env python3
"""
Neo4j Cypher Query Examples for Milejczyce AI Ekspert Database

Purpose: Demonstrate graph exploration patterns across all major categories
Database: neo4j (Milejczyce AI Ekspert instance)
Connection: bolt+ssc://localhost:7687
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv('.env.db')

uri = os.getenv('NEO4J_URI')
user = os.getenv('NEO4J_USER')
pwd = os.getenv('NEO4J_PASSWORD')

class Neo4jQueryExamples:
    """Collection of Cypher query examples for graph exploration."""
    
    def __init__(self):
        self.driver = GraphDatabase.driver(uri, auth=(user, pwd))
    
    def execute_query(self, query, params=None):
        """Execute a Cypher query and return results."""
        with self.driver.session(database="neo4j") as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]
    
    def print_section(self, title):
        """Print formatted section header."""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)
    
    def print_results(self, results, limit=10):
        """Print query results with limit."""
        if not results:
            print("  No results found.")
            return
        
        count = min(len(results), limit)
        print(f"\n  Showing {count} of {len(results)} results:\n")
        
        for i, record in enumerate(results[:limit], 1):
            print(f"  {i}. {record}")
        
        if len(results) > limit:
            print(f"\n  ... and {len(results) - limit} more results")
    
    # =========================================================================
    # CATEGORY 1: GOVERNANCE & LEGAL EXPLORATION
    # =========================================================================
    
    def query_administrative_decisions(self):
        """Explore administrative decisions and their legal basis."""
        self.print_section("QUERY 1: Administrative Decisions")
        
        query = """
        MATCH (d:AdministrativeDecision)
        OPTIONAL MATCH (d)-[:HAS_RISK]->(r:Risk)
        RETURN d.title AS decision_title,
               d.date AS decision_date,
               r.description AS risk_description
        ORDER BY d.date DESC
        LIMIT 10
        """
        
        results = self.execute_query(query)
        self.print_results(results)
    
    def query_council_structure(self):
        """Explore council members and committees."""
        self.print_section("QUERY 2: Council Structure")
        
        query = """
        MATCH (m:CouncilMember)
        OPTIONAL MATCH (m)-[:PERFORMED]->(e:Event)
        RETURN m.name AS member_name,
               m.role AS role,
               count(e) AS events_participated
        ORDER BY events_participated DESC
        LIMIT 10
        """
        
        results = self.execute_query(query)
        self.print_results(results)
    
    def query_gdpr_compliance(self):
        """Explore GDPR erasure certificates and consent records."""
        self.print_section("QUERY 3: GDPR Compliance Records")
        
        query = """
        MATCH (cert:GDPRErasureCertificate)
        RETURN cert.certificate_id AS certificate_id,
               cert.erasure_date AS erasure_date,
               cert.status AS status
        ORDER BY cert.erasure_date DESC
        LIMIT 10
        """
        
        results = self.execute_query(query)
        self.print_results(results)
    
    # =========================================================================
    # CATEGORY 2: FINANCIAL FLOW ANALYSIS
    # =========================================================================
    
    def query_budget_items(self):
        """Explore budget items and funding sources."""
        self.print_section("QUERY 4: Budget Items")
        
        query = """
        MATCH (b:BudgetItem)
        RETURN b.category AS category,
               b.amount AS amount,
               b.fiscal_year AS fiscal_year
        ORDER BY b.amount DESC
        LIMIT 10
        """
        
        results = self.execute_query(query)
        self.print_results(results)
    
    def query_investments(self):
        """Explore municipal investments."""
        self.print_section("QUERY 5: Municipal Investments")
        
        query = """
        MATCH (i:Investment)
        OPTIONAL MATCH (i)-[:HAS_RISK]->(r:Risk)
        RETURN i.project_name AS project,
               i.budget AS budget,
               i.status AS status,
               r.description AS associated_risk
        ORDER BY i.budget DESC
        LIMIT 10
        """
        
        results = self.execute_query(query)
        self.print_results(results)
    
    # =========================================================================
    # CATEGORY 3: COMMUNITY & CITIZEN ENGAGEMENT
    # =========================================================================
    
    def query_citizen_feedback(self):
        """Explore citizen feedback patterns."""
        self.print_section("QUERY 6: Citizen Feedback")
        
        query = """
        MATCH (f:CitizenFeedback)
        RETURN f.category AS category,
               f.sentiment AS sentiment,
               f.date AS date,
               f.summary AS summary
        ORDER BY f.date DESC
        LIMIT 10
        """
        
        results = self.execute_query(query)
        self.print_results(results)
    
    def query_community_organizations(self):
        """Explore community organizations and their activities."""
        self.print_section("QUERY 7: Community Organizations")
        
        query = """
        MATCH (org:CommunityOrganization)
        OPTIONAL MATCH (org)-[:INITIATED_EVENT]->(e:Event)
        RETURN org.name AS organization,
               org.type AS type,
               count(e) AS events_initiated
        ORDER BY events_initiated DESC
        LIMIT 10
        """
        
        results = self.execute_query(query)
        self.print_results(results)
    
    # =========================================================================
    # CATEGORY 4: HISTORICAL & STRATEGIC INSIGHTS
    # =========================================================================
    
    def query_historical_events(self):
        """Explore historical events and figures."""
        self.print_section("QUERY 8: Historical Events")
        
        query = """
        MATCH (e:HistoricalEvent)
        OPTIONAL MATCH (figure:HistoricalFigure)-[:INITIATED_EVENT]->(e)
        RETURN e.title AS event_title,
               e.date AS event_date,
               figure.name AS historical_figure
        ORDER BY e.date DESC
        LIMIT 10
        """
        
        results = self.execute_query(query)
        self.print_results(results)
    
    def query_strategic_concepts(self):
        """Explore strategic concepts and their relationships."""
        self.print_section("QUERY 9: Strategic Concepts")
        
        query = """
        MATCH (s:StrategicConcept)
        RETURN s.name AS concept,
               s.domain AS domain,
               s.priority AS priority
        ORDER BY 
            CASE s.priority
                WHEN 'HIGH' THEN 1
                WHEN 'MEDIUM' THEN 2
                WHEN 'LOW' THEN 3
                ELSE 4
            END
        LIMIT 10
        """
        
        results = self.execute_query(query)
        self.print_results(results)
    
    # =========================================================================
    # CATEGORY 5: SECURITY & AUDIT TRAILS
    # =========================================================================
    
    def query_audit_trails(self):
        """Explore audit trail entries."""
        self.print_section("QUERY 10: Audit Trails")
        
        query = """
        MATCH (a:AuditTrail)
        RETURN a.action AS action,
               a.timestamp AS timestamp,
               a.actor AS actor,
               a.result AS result
        ORDER BY a.timestamp DESC
        LIMIT 10
        """
        
        results = self.execute_query(query)
        self.print_results(results)
    
    def query_w11_flags(self):
        """Explore W11 governance flags."""
        self.print_section("QUERY 11: W11 Governance Flags")
        
        query = """
        MATCH (flag:W11Flag)
        RETURN flag.flag_id AS flag_id,
               flag.status AS status,
               flag.created_at AS created_at,
               flag.reason AS reason
        ORDER BY flag.created_at DESC
        LIMIT 10
        """
        
        results = self.execute_query(query)
        self.print_results(results)
    
    def query_security_incidents(self):
        """Explore security incidents and breach responses."""
        self.print_section("QUERY 12: Security Incidents")
        
        query = """
        MATCH (incident:IncidentResponse)
        OPTIONAL MATCH (incident)-[:HAS_RISK]->(r:Risk)
        RETURN incident.incident_type AS type,
               incident.severity AS severity,
               incident.date AS date,
               r.description AS associated_risk
        ORDER BY incident.date DESC
        LIMIT 10
        """
        
        results = self.execute_query(query)
        self.print_results(results)
    
    # =========================================================================
    # CATEGORY 6: GEOSPATIAL QUERIES
    # =========================================================================
    
    def query_locations(self):
        """Explore geographic locations and properties."""
        self.print_section("QUERY 13: Geographic Locations")
        
        query = """
        MATCH (loc:Location)
        RETURN loc.name AS location_name,
               loc.type AS type,
               loc.coordinates AS coordinates
        LIMIT 10
        """
        
        results = self.execute_query(query)
        self.print_results(results)
    
    def query_municipality_data(self):
        """Explore municipality-level data."""
        self.print_section("QUERY 14: Municipality Data")
        
        query = """
        MATCH (m:Municipality)
        RETURN m.name AS municipality,
               m.population AS population,
               m.area_km2 AS area_km2
        LIMIT 10
        """
        
        results = self.execute_query(query)
        self.print_results(results)
    
    # =========================================================================
    # CATEGORY 7: GRAPH STRUCTURE ANALYSIS
    # =========================================================================
    
    def query_relationship_patterns(self):
        """Analyze relationship patterns in the graph."""
        self.print_section("QUERY 15: Relationship Pattern Analysis")
        
        query = """
        MATCH ()-[r]->()
        RETURN type(r) AS relationship_type,
               count(r) AS count
        ORDER BY count DESC
        """
        
        results = self.execute_query(query)
        self.print_results(results, limit=20)
    
    def query_node_label_distribution(self):
        """Analyze node label distribution."""
        self.print_section("QUERY 16: Node Label Distribution")
        
        query = """
        MATCH (n)
        WITH labels(n) AS node_labels
        UNWIND node_labels AS label
        RETURN label,
               count(*) AS count
        ORDER BY count DESC
        """
        
        results = self.execute_query(query)
        self.print_results(results, limit=20)
    
    def query_connected_components(self):
        """Find highly connected nodes (hubs)."""
        self.print_section("QUERY 17: Highly Connected Nodes (Hubs)")
        
        query = """
        MATCH (n)
        WHERE size((n)--()) > 2
        WITH n, size((n)--()) AS connection_count
        RETURN labels(n)[0] AS node_type,
               CASE 
                   WHEN n.name IS NOT NULL THEN n.name
                   WHEN n.title IS NOT NULL THEN n.title
                   ELSE toString(id(n))
               END AS identifier,
               connection_count
        ORDER BY connection_count DESC
        LIMIT 10
        """
        
        results = self.execute_query(query)
        self.print_results(results)
    
    # =========================================================================
    # CATEGORY 8: RISK ANALYSIS
    # =========================================================================
    
    def query_risk_network(self):
        """Explore risk relationships across entities."""
        self.print_section("QUERY 18: Risk Network Analysis")
        
        query = """
        MATCH (entity)-[:HAS_RISK]->(r:Risk)
        RETURN labels(entity)[0] AS entity_type,
               r.category AS risk_category,
               r.severity AS severity,
               count(*) AS occurrence_count
        ORDER BY occurrence_count DESC
        LIMIT 10
        """
        
        results = self.execute_query(query)
        self.print_results(results)
    
    # =========================================================================
    # EXECUTION
    # =========================================================================
    
    def run_all_examples(self):
        """Execute all query examples."""
        print("\n" + "=" * 70)
        print("  NEO4J CYPHER QUERY EXAMPLES")
        print("  Milejczyce AI Ekspert Database")
        print(f"  Generated: {datetime.now().isoformat()}")
        print("=" * 70)
        
        # Category 1: Governance & Legal
        self.query_administrative_decisions()
        self.query_council_structure()
        self.query_gdpr_compliance()
        
        # Category 2: Financial
        self.query_budget_items()
        self.query_investments()
        
        # Category 3: Community
        self.query_citizen_feedback()
        self.query_community_organizations()
        
        # Category 4: Historical & Strategic
        self.query_historical_events()
        self.query_strategic_concepts()
        
        # Category 5: Security & Audit
        self.query_audit_trails()
        self.query_w11_flags()
        self.query_security_incidents()
        
        # Category 6: Geospatial
        self.query_locations()
        self.query_municipality_data()
        
        # Category 7: Graph Structure
        self.query_relationship_patterns()
        self.query_node_label_distribution()
        self.query_connected_components()
        
        # Category 8: Risk Analysis
        self.query_risk_network()
        
        print("\n" + "=" * 70)
        print("  ALL QUERY EXAMPLES COMPLETED")
        print("=" * 70 + "\n")
    
    def close(self):
        """Close database connection."""
        self.driver.close()


def main():
    """Main execution function."""
    explorer = Neo4jQueryExamples()
    
    try:
        explorer.run_all_examples()
    except Exception as e:
        print(f"\n❌ Error executing queries: {e}")
        import traceback
        traceback.print_exc()
    finally:
        explorer.close()


if __name__ == "__main__":
    main()
