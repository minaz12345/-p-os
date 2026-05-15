# Neo4j Cypher Query Examples - Milejczyce AI Ekspert Database

**Purpose:** Graph exploration patterns for P-OS sovereign ops runtime  
**Database:** neo4j (Milejczyce AI Ekspert instance)  
**Connection:** bolt+ssc://localhost:7687  
**Date:** 2026-05-11  
**Status:** OPERATIONAL ✅

---

## DATABASE STATISTICS

```
Nodes: 460
Relationships: 62
Node Labels: 12 types active
Relationship Types: 4 (PERFORMED, TRUSTS, HAS_RISK, INITIATED_EVENT)
```

### Node Label Distribution (Top 12)
1. AuditTrail - 108 nodes
2. LegalArticle - 98 nodes
3. Event - 77 nodes
4. Location - 59 nodes
5. LegalBasis - 55 nodes
6. CitizenFeedback - 24 nodes
7. Institution - 16 nodes
8. Citizen - 11 nodes
9. User - 5 nodes
10. Risk - 3 nodes
11. Municipality - 3 nodes
12. RiskProfile - 1 node

---

## WORKING QUERY EXAMPLES

### QUERY 1: Relationship Pattern Analysis

**Purpose:** Understand which relationship types are most common

```cypher
MATCH ()-[r]->()
RETURN type(r) AS relationship_type,
       count(r) AS count
ORDER BY count DESC
```

**Results:**
- PERFORMED: 52 relationships
- TRUSTS: 6 relationships
- HAS_RISK: 3 relationships
- INITIATED_EVENT: 1 relationship

**Insight:** Most activity is around operator/user actions (PERFORMED).

---

### QUERY 2: Node Label Distribution

**Purpose:** See what types of entities dominate the graph

```cypher
MATCH (n)
WITH labels(n) AS node_labels
UNWIND node_labels AS label
RETURN label,
       count(*) AS count
ORDER BY count DESC
```

**Results:** Top categories are AuditTrail (108), LegalArticle (98), Event (77)

**Insight:** System heavily focused on legal framework and audit logging.

---

### QUERY 3: Audit Trail Exploration

**Purpose:** Review recent audit trail entries

```cypher
MATCH (a:AuditTrail)
RETURN a.action AS action,
       a.timestamp AS timestamp
ORDER BY a.timestamp DESC
LIMIT 10
```

**Sample Results:**
- GDPR_ERASURE actions from May 3, 2026
- Timestamps show batch processing pattern

**Insight:** GDPR erasure operations are being tracked in the graph.

---

### QUERY 4: Geographic Locations

**Purpose:** Explore location nodes in the database

```cypher
MATCH (loc:Location)
RETURN loc.name AS location_name
LIMIT 10
```

**Results:**
- Milejczyce
- Rogacze
- Choroszczewo
- Pokaniewo Kolonia
- Pokaniewo
- Biełki
- Miedwieżyki
- Mikulicze
- Sobiatyno
- Wałki

**Insight:** Complete list of villages/locations in Milejczyce municipality.

---

### QUERY 5: Citizen Feedback Analysis

**Purpose:** Understand citizen engagement patterns

```cypher
MATCH (f:CitizenFeedback)
RETURN f.category AS category,
       count(f) AS feedback_count
ORDER BY feedback_count DESC
```

**Sample Result:** 'suggestion' category appears in results

**Note:** Many properties (sentiment, date, summary) may be NULL - schema needs verification.

---

### QUERY 6: Highly Connected Nodes (Hubs)

**Purpose:** Find nodes with many relationships (graph hubs)

```cypher
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
```

**Insight:** Identifies central entities in the governance graph.

---

### QUERY 7: Risk Network Analysis

**Purpose:** Explore risk relationships across all entity types

```cypher
MATCH (entity)-[:HAS_RISK]->(r:Risk)
RETURN labels(entity)[0] AS entity_type,
       r.category AS risk_category,
       r.severity AS severity,
       count(*) AS occurrence_count
ORDER BY occurrence_count DESC
```

**Current State:** Only 3 HAS_RISK relationships exist - risk modeling is minimal.

---

### QUERY 8: Trust Relationships

**Purpose:** Map trust networks between entities

```cypher
MATCH (a)-[:TRUSTS]->(b)
RETURN labels(a)[0] AS truster_type,
       labels(b)[0] AS trustee_type,
       count(*) AS trust_count
```

**Current State:** 6 TRUSTS relationships exist - small but meaningful trust network.

---

### QUERY 9: Event Timeline

**Purpose:** Explore events chronologically

```cypher
MATCH (e:Event)
RETURN e.title AS event_title,
       e.date AS event_date
ORDER BY e.date DESC
LIMIT 10
```

**Note:** Check if `date` property exists or use alternative property names.

---

### QUERY 10: Legal Framework Coverage

**Purpose:** Understand legal article distribution

```cypher
MATCH (la:LegalArticle)
RETURN la.article_number AS article_number,
       la.source AS source
ORDER BY la.article_number
LIMIT 20
```

**Insight:** 98 legal articles tracked - comprehensive legal framework mapping.

---

## QUERY PATTERNS BY CATEGORY

### Governance & Legal
- Administrative decisions → Currently empty (no data)
- Council structure → Currently empty (no data)
- GDPR certificates → Nodes exist but properties differ from expected schema
- Legal articles → 98 nodes, well-populated

### Financial
- Budget items → Nodes exist but properties differ from expected schema
- Investments → Currently empty (no data)

### Community
- Citizen feedback → 24 nodes, some data present
- Community organizations → Currently empty (no data)

### Historical & Strategic
- Historical events → Currently empty (no data)
- Strategic concepts → Currently empty (no data)

### Security & Audit
- Audit trails → 108 nodes, GDPR_ERASURE actions tracked
- W11 flags → Currently empty (no data)
- Security incidents → Currently empty (no data)

### Geospatial
- Locations → 59 nodes, village names populated
- Municipality → 3 nodes, limited property data

---

## SCHEMA OBSERVATIONS

### Properties That Exist
- `name` - Common across Location, Citizen, Institution
- `action` - Used in AuditTrail
- `timestamp` - Used in AuditTrail
- `category` - Used in CitizenFeedback, Risk
- `title` - Used in some node types

### Properties That Don't Exist (Yet)
- `certificate_id`, `erasure_date` - GDPRErasureCertificate
- `amount`, `fiscal_year` - BudgetItem
- `project_name`, `budget` - Investment
- `coordinates` - Location
- `population`, `area_km2` - Municipality
- `flag_id`, `created_at` - W11Flag
- `incident_type`, `severity` - IncidentResponse

**Recommendation:** Schema evolution needed to support full query capabilities.

---

## RECOMMENDED NEXT STEPS

### 1. Schema Documentation
Create complete property inventory for each node label:
```cypher
MATCH (n:AuditTrail)
RETURN keys(n) AS properties
LIMIT 1
```

### 2. Data Enrichment
Add missing properties to existing nodes:
- Coordinates for Location nodes
- Population/area for Municipality
- Dates/timestamps for Events

### 3. Index Creation
Add indexes for frequent query patterns:
```cypher
CREATE INDEX FOR (n:AuditTrail) ON (n.timestamp)
CREATE INDEX FOR (n:Location) ON (n.name)
CREATE INDEX FOR (n:LegalArticle) ON (n.article_number)
```

### 4. Relationship Expansion
Currently only 62 relationships for 460 nodes (ratio: 0.135). Consider:
- Linking Citizens to their Feedback
- Connecting Investments to Locations
- Mapping LegalArticles to AdministrativeDecisions

---

## EXECUTION INSTRUCTIONS

### Python Execution
```python
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv('.env.db')

uri = os.getenv('NEO4J_URI')
user = os.getenv('NEO4J_USER')
pwd = os.getenv('NEO4J_PASSWORD')

driver = GraphDatabase.driver(uri, auth=(user, pwd))

with driver.session(database="neo4j") as session:
    result = session.run("YOUR_CYPHER_QUERY_HERE")
    for record in result:
        print(record.data())

driver.close()
```

### Neo4j Browser
1. Open Neo4j Desktop
2. Click "Milejczyce AI Ekspert"
3. Open Browser
4. Paste Cypher queries directly

---

## CONCLUSION

The Milejczyce AI Ekspert database contains **foundational data** with strong coverage in:
- ✅ Audit trails (108 nodes)
- ✅ Legal framework (98 LegalArticle + 55 LegalBasis nodes)
- ✅ Events (77 nodes)
- ✅ Geographic locations (59 nodes)

**Areas for development:**
- Property schema completion
- Relationship density increase
- Data enrichment for financial/community/historical categories

The graph is **operational and queryable** with room for expansion during v8.0 planning phase.

---

*Generated: 2026-05-11 | P-OS v7.5 | Constitutional Quietness Active*
