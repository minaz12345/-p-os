// ============================================================================
// P-OS v7.5 - NEO4J CONNECTIVITY ENRICHMENT PHASE 2
// ============================================================================
// Document ID: ARCHIVE-P-OS-7.5-NEO4J-CONNECTIVITY-IMPROVEMENT-20260511
// Date: 2026-05-11
// Purpose: Increase graph connectivity from 56.1% to 75-85%+
// Mode: Quiet Operations (non-disruptive, read-only verification)
// Owner: Budowniczy P-OS + p-os-constitution v1.0 [FROZEN]
// ============================================================================

// ============================================================================
// PHASE 0: BASELINE MEASUREMENTS
// ============================================================================

// Capture pre-enrichment statistics
MATCH (n) RETURN count(n) AS total_nodes_before;
MATCH ()-[r]->() RETURN count(r) AS total_relationships_before;
MATCH (n) WHERE size((n)--()) = 0 RETURN count(n) AS orphaned_nodes_before;

// ============================================================================
// PHASE 1: Citizen ↔ CitizenFeedback Linkage (+~35 nodes)
// ============================================================================
// Priority: HIGH (easiest, immediate impact)
// Strategy: Match on citizen name/full_name fields

MATCH (c:Citizen), (f:CitizenFeedback)
WHERE c.name = f.citizen_name 
   OR c.full_name = f.citizen_name
   OR c.imie_nazwisko = f.citizen_name
MERGE (c)-[:PROVIDED_FEEDBACK]->(f)
ON CREATE SET 
  f.linked_at = timestamp(),
  f.link_method = 'name_matching'
RETURN count(*) AS citizen_feedback_links_created;

// Verification
MATCH (c:Citizen)-[:PROVIDED_FEEDBACK]->(f:CitizenFeedback)
RETURN count(DISTINCT c) AS citizens_with_feedback,
       count(DISTINCT f) AS feedback_linked;

// ============================================================================
// PHASE 2: LegalBasis ↔ LegalArticle Linkage (+~50-60 nodes)
// ============================================================================
// Priority: HIGH (governance backbone)
// Strategy: Match on law_name and article_reference

MATCH (lb:LegalBasis), (la:LegalArticle)
WHERE lb.law_name = la.parent_law 
   OR lb.article_reference = la.article_id
   OR lb.reference_number = la.article_id
MERGE (lb)-[:REFERENCES]->(la)
ON CREATE SET 
  lb.linked_at = timestamp(),
  lb.link_method = 'legal_reference_matching'
RETURN count(*) AS legal_basis_links_created;

// Verification
MATCH (lb:LegalBasis)-[:REFERENCES]->(la:LegalArticle)
RETURN count(DISTINCT lb) AS legal_basis_linked,
       count(DISTINCT la) AS articles_referenced;

// ============================================================================
// PHASE 3: Event → Location Linkage (+~40-50 nodes)
// ============================================================================
// Priority: MEDIUM (geographic grounding)
// Strategy: Match on location/municipality fields

MATCH (e:Event), (l:Location)
WHERE e.location = l.name 
   OR e.municipality = l.municipality_id
   OR e.gmina = l.name
MERGE (e)-[:OCCURRED_IN]->(l)
ON CREATE SET 
  e.linked_at = timestamp(),
  e.link_method = 'location_matching'
RETURN count(*) AS event_location_links_created;

// Verification
MATCH (e:Event)-[:OCCURRED_IN]->(l:Location)
RETURN count(DISTINCT e) AS events_with_location,
       count(DISTINCT l) AS locations_with_events;

// ============================================================================
// PHASE 4: Institution → Location Linkage (+~20-30 nodes)
// ============================================================================
// Priority: MEDIUM (institutional geography)
// Strategy: Match on institution location field

MATCH (i:Institution), (l:Location)
WHERE i.location = l.name 
   OR i.address_city = l.name
   OR i.municipality = l.municipality_id
MERGE (i)-[:LOCATED_IN]->(l)
ON CREATE SET 
  i.linked_at = timestamp(),
  i.link_method = 'institution_location_matching'
RETURN count(*) AS institution_location_links_created;

// Verification
MATCH (i:Institution)-[:LOCATED_IN]->(l:Location)
RETURN count(DISTINCT i) AS institutions_with_location,
       count(DISTINCT l) AS locations_with_institutions;

// ============================================================================
// PHASE 5: AuditTrail → Location/Event Linkage (+~30-40 nodes)
// ============================================================================
// Priority: MEDIUM (audit trail completeness)
// Strategy: Match on location_name or event_id

// AuditTrail → Location
MATCH (a:AuditTrail), (l:Location)
WHERE a.location_name = l.name 
   OR a.municipality = l.municipality_id
MERGE (a)-[:AUDITS_LOCATION]->(l)
ON CREATE SET 
  a.linked_at = timestamp(),
  a.link_method = 'audit_location_matching'
RETURN count(*) AS audit_location_links_created;

// AuditTrail → Event (if event_id exists)
MATCH (a:AuditTrail), (e:Event)
WHERE a.event_id = e.event_id 
   OR a.related_event = e.id
MERGE (a)-[:AUDITS_EVENT]->(e)
ON CREATE SET 
  a.linked_at = timestamp(),
  a.link_method = 'audit_event_matching'
RETURN count(*) AS audit_event_links_created;

// Verification
MATCH (a:AuditTrail)-[r]->(target)
WHERE type(r) IN ['AUDITS_LOCATION', 'AUDITS_EVENT']
RETURN count(DISTINCT a) AS audits_with_targets,
       count(DISTINCT target) AS targets_audited;

// ============================================================================
// PHASE 6: User → Institution Linkage (administrative structure)
// ============================================================================
// Priority: LOW (organizational hierarchy)
// Strategy: Match users to their institutions

MATCH (u:User), (i:Institution)
WHERE u.institution = i.name 
   OR u.department = i.name
   OR u.organization = i.institution_id
MERGE (u)-[:WORKS_FOR]->(i)
ON CREATE SET 
  u.linked_at = timestamp(),
  u.link_method = 'user_institution_matching'
RETURN count(*) AS user_institution_links_created;

// Verification
MATCH (u:User)-[:WORKS_FOR]->(i:Institution)
RETURN count(DISTINCT u) AS users_with_institution,
       count(DISTINCT i) AS institutions_with_users;

// ============================================================================
// PHASE 7: Risk → Entity Linkage (risk framework expansion)
// ============================================================================
// Priority: LOW (risk accountability)
// Strategy: Connect existing risk nodes to related entities

MATCH (r:Risk), (u:User)
WHERE r.owner = u.user_id 
   OR r.assigned_to = u.name
MERGE (u)-[:OWNS_RISK]->(r)
ON CREATE SET 
  r.linked_at = timestamp(),
  r.link_method = 'risk_owner_matching';

MATCH (r:Risk), (e:Event)
WHERE r.related_event = e.event_id
MERGE (e)-[:HAS_RISK]->(r)
ON CREATE SET 
  r.linked_at = timestamp(),
  r.link_method = 'risk_event_matching'
RETURN count(*) AS risk_entity_links_created;

// ============================================================================
// PHASE 8: POST-ENRICHMENT VERIFICATION
// ============================================================================

// Final statistics
MATCH (n) RETURN count(n) AS total_nodes_after;
MATCH ()-[r]->() RETURN count(r) AS total_relationships_after;
MATCH (n) WHERE size((n)--()) = 0 RETURN count(n) AS orphaned_nodes_after;

// Connectivity calculation
MATCH (n)
WITH count(n) AS total,
     count(CASE WHEN size((n)--()) > 0 THEN 1 END) AS connected
RETURN 
  total AS total_nodes,
  connected AS connected_nodes,
  round(toFloat(connected) / total * 100, 2) AS connectivity_percentage;

// Relationship type distribution
MATCH ()-[r]->()
RETURN type(r) AS relationship_type, count(r) AS count
ORDER BY count DESC;

// Orphaned node analysis by label
MATCH (n)
WHERE size((n)--()) = 0
RETURN labels(n)[0] AS node_label, count(n) AS orphaned_count
ORDER BY orphaned_count DESC;

// ============================================================================
// PHASE 9: PERFORMANCE INDEXES (Optional - uncomment if needed)
// ============================================================================

// Create indexes for frequently queried properties
// Uncomment these if performance becomes an issue:

// CREATE INDEX event_municipality_idx IF NOT EXISTS FOR (e:Event) ON (e.municipality);
// CREATE INDEX legal_article_parent_idx IF NOT EXISTS FOR (la:LegalArticle) ON (la.parent_law);
// CREATE INDEX audit_node_id_idx IF NOT EXISTS FOR (a:AuditTrail) ON (a.node_id);
// CREATE INDEX feedback_timestamp_idx IF NOT EXISTS FOR (cf:CitizenFeedback) ON (cf.timestamp);
// CREATE INDEX location_municipality_idx IF NOT EXISTS FOR (l:Location) ON (l.municipality_id);

// ============================================================================
// SUMMARY REPORT
// ============================================================================

RETURN "=== CONNECTIVITY ENRICHMENT COMPLETE ===" AS status,
       timestamp() AS completion_timestamp;
