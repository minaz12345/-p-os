# ETAP 4 - SEMANTIC CANONICALIZATION ARCHITECTURE

**Date:** 2026-05-12  
**Status:** ✅ ARCHITECTURE DESIGNED | IMPLEMENTATION READY  
**Mode:** Constitutional Quietness (Day 2 of 30)  

---

## EXECUTIVE SUMMARY

The NOI-O1 Milejczyce Core Ontology has revealed that P-OS is not a traditional ERP system, but a **sovereign semantic operating system for municipal cognition**. 

The previous migration approach (relational ETL) was fundamentally misaligned with this reality. This document defines the new **Semantic Canonicalization Architecture** that properly implements O1 ontology-driven knowledge ingestion.

### Paradigm Shift

| Old Model (Failed) | New Model (O1-Aligned) |
|-------------------|------------------------|
| SQLite → PostgreSQL (1:1 table mapping) | SQLite → Staging → Semantic Resolution → Canonical Entities |
| Data → Data | **Data → Knowledge** |
| Relational schema-first | **Ontology-first (O1-driven)** |
| Column alignment | **Entity binding & relationship mapping** |
| HR records | **Strategic agents with weights** |
| Foreign keys | **Semantic relationships in graph** |

---

## ARCHITECTURAL LAYERS

### Layer 1: RAW STAGING ZONE (Immutable Ingestion Buffer)

**Purpose:** Zero-transformation archival of all source data

```sql
CREATE TABLE staging_raw_records (
    id UUID PRIMARY KEY,
    source_db VARCHAR(100),      -- e.g., 'org_structure_test.db'
    source_table VARCHAR(100),   -- e.g., 'employees'
    source_pk TEXT,              -- Original primary key
    raw_payload JSONB NOT NULL,  -- Complete record as JSON
    raw_hash VARCHAR(64),        -- SHA-256 of raw payload
    ingested_at TIMESTAMPTZ,
    migration_session_id UUID
);
```

**Key Properties:**
- ✅ Immutable (append-only)
- ✅ No business logic
- ✅ Preserves original data exactly
- ✅ Full provenance tracking

---

### Layer 2: SEMANTIC RESOLUTION LOG (Ontology Binding Decisions)

**Purpose:** Track how raw records are classified and bound to O1 ontology

```sql
CREATE TABLE semantic_resolution_log (
    id UUID PRIMARY KEY,
    staging_record_id UUID REFERENCES staging_raw_records(id),
    
    -- Ontology binding
    ontology_class VARCHAR(100),     -- e.g., 'executive_actor'
    entity_type VARCHAR(100),        -- e.g., 'Wójt'
    canonical_name VARCHAR(255),     -- Normalized name
    
    -- Strategic weight
    strategic_weight REAL,           -- From O1 (e.g., Wójt = 2.0)
    strategic_class VARCHAR(50),     -- e.g., 'executive_authority'
    
    -- Identity resolution
    entity_fingerprint VARCHAR(64),  -- sha256(name + class)
    canonical_person_key VARCHAR(255),
    
    -- Metadata
    confidence_score REAL,
    resolution_method VARCHAR(50),   -- 'exact_match', 'pattern_match'
    resolved_by VARCHAR(100)
);
```

**Key Properties:**
- ✅ Tracks every classification decision
- ✅ Preserves uncertainty (confidence scores)
- ✅ Supports multiple resolution methods
- ✅ Audit trail for ontology binding

---

### Layer 3: CANONICAL ENTITIES (O1-Aligned Knowledge Layer)

**Purpose:** Unified knowledge entities aligned with NOI-O1 ontology

```sql
CREATE TABLE noi_canonical_entities (
    id UUID PRIMARY KEY,
    entity_fingerprint VARCHAR(64) UNIQUE,
    
    -- Core identity
    canonical_name VARCHAR(255),
    ontology_class VARCHAR(100),     -- Agent, Block, Event, etc.
    entity_type VARCHAR(100),        -- Wójt, Komisja, OSP, etc.
    
    -- Strategic properties
    strategic_weight REAL,
    strategic_class VARCHAR(50),
    description TEXT,
    
    -- Temporal validity
    valid_from TIMESTAMPTZ,
    valid_to TIMESTAMPTZ,
    is_active BOOLEAN,
    
    -- Provenance
    source_count INTEGER,            -- How many raw records contributed
    first_seen TIMESTAMPTZ,
    last_updated TIMESTAMPTZ,
    
    -- Metadata
    properties JSONB,
    tags TEXT[]
);
```

**Key Properties:**
- ✅ Fingerprint-based identity (not UUID)
- ✅ Merges multiple sources into single entity
- ✅ Strategic weighting from O1
- ✅ Temporal validity tracking

---

### Layer 4: SEMANTIC RELATIONSHIPS (Graph Edges)

**Purpose:** Capture relationships between entities (pre-Neo4j projection)

```sql
CREATE TABLE noi_entity_relations (
    id UUID PRIMARY KEY,
    
    -- Relationship endpoints
    source_entity_fingerprint VARCHAR(64) REFERENCES noi_canonical_entities,
    target_entity_fingerprint VARCHAR(64) REFERENCES noi_canonical_entities,
    
    -- Relationship type
    relation_type VARCHAR(100),      -- 'manages', 'opposes', 'supports'
    relation_weight REAL,
    
    -- Context
    description TEXT,
    valid_from TIMESTAMPTZ,
    valid_to TIMESTAMPTZ,
    is_active BOOLEAN,
    
    -- Provenance
    derived_from_staging UUID REFERENCES staging_raw_records,
    confidence_score REAL
);
```

**Key Properties:**
- ✅ Explicit relationship types
- ✅ Bidirectional support
- ✅ Weighted edges
- ✅ Temporal validity

---

### Layer 5: STRATEGIC VECTORS (High-Level Dynamics)

**Purpose:** Track strategic initiatives and conflicts from O1

```sql
CREATE TABLE strategic_vectors (
    id UUID PRIMARY KEY,
    vector_name VARCHAR(255),        -- 'Uzdrowisko', 'Tarcza Ekologiczna'
    vector_type VARCHAR(100),        -- 'strategic_initiative', 'conflict'
    
    -- Strategic properties
    priority REAL,
    status VARCHAR(50),              -- active, blocked, completed
    phase VARCHAR(50),               -- 'Faza A', 'monitoring'
    
    -- Timeline
    initiated_at TIMESTAMPTZ,
    target_completion DATE,
    actual_completion DATE,
    
    -- Context
    description TEXT,
    challenges TEXT[],
    opportunities TEXT[],
    
    -- Related entities
    related_entities TEXT[]          -- Array of fingerprints
);
```

**Examples from O1:**
- `Uzdrowisko` (priority: 2.5, phase: 'Faza A')
- `Tarcza Ekologiczna` (priority: 2.3, status: 'active')
- `Fundusz Sołecki` (priority: 1.8, status: 'restored_2026')
- `Konflikt Wipasz` (priority: 2.0, status: 'blocked')

---

## ONTOLOGY CLASSIFIER

The `ontology_binder.py` module implements intelligent classification:

### O1 Ontology Classes

| Class | Strategic Weight | Examples |
|-------|-----------------|----------|
| `executive_actor` | 2.0 | Wójt, Sekretarz, Skarbnik |
| `governance_unit` | 1.8 | Rada Gminy, Komisje |
| `operational_agent` | 1.2 | Kierownik, Inspektor |
| `resilience_node` | 1.5 | OSP, GOPS, Szkoła |
| `strategic_vector` | 2.5 | Uzdrowisko, Tarcza |
| `historical_entity` | 1.0 | Bulla Gnieźnieńska, Herb |
| `social_actor` | 0.8 | Mieszkaniec, Radny |
| `infrastructure_asset` | 1.3 | Droga, Wodociąg |

### Classification Methods

1. **Exact Match** (confidence: 0.95)
   - Matches known entities from O1 (e.g., "Sebastian Sawicki" → Wójt)

2. **Pattern Match** (confidence: 0.3-0.9)
   - Keyword matching against ontology patterns
   - Multiple pattern matches increase confidence

3. **Default** (confidence: 0.5)
   - Unclassified entities marked as 'unknown'

### Entity Fingerprint Formula

```python
fingerprint = sha256(normalized_name + "|" + ontology_class)
```

Example:
```
sha256("sebastian sawicki|executive_actor") 
= "a3f2b8c1d4e5..."
```

This ensures:
- ✅ Deterministic identity
- ✅ Same entity always gets same fingerprint
- ✅ Different classes create different fingerprints

---

## IMPLEMENTATION STATUS

### Completed Today ✅

1. **Schema Design** - All 5 layers defined in `MILEJCZYCE_POSTGRESQL_SCHEMA.sql`
2. **Ontology Binder Module** - `scripts/ontology_binder.py` implemented
3. **Classification Logic** - Pattern matching + exact match working
4. **Fingerprint System** - SHA-256 deterministic identity
5. **Strategic Weights** - O1 weights integrated

### Pending Implementation ⏸️

1. **Database Recreation** - Apply new schema to PostgreSQL
2. **Raw Ingestion Pipeline** - Modify migration script to use staging layer
3. **Batch Processing** - Test ontology binder on staging data
4. **Relationship Extraction** - Implement relationship detection logic
5. **Strategic Vector Population** - Manual seeding of O1 vectors

---

## MIGRATION WORKFLOW (NEW)

### Phase 1: Raw Ingestion

```bash
# Step 1: Extract from SQLite to staging (zero transformation)
python scripts/migrate_sqlite_to_postgres.py \
  --mode staging \
  --pg-conn "postgresql://..."
```

**Result:** All SQLite records stored as JSONB in `staging_raw_records`

---

### Phase 2: Semantic Resolution

```bash
# Step 2: Bind staging records to O1 ontology
python scripts/ontology_binder.py \
  --pg-conn "postgresql://..." \
  --session-id <migration_session_id> \
  --batch-size 100
```

**Result:** Each staging record classified and canonical entities created

---

### Phase 3: Relationship Extraction

```bash
# Step 3: Detect relationships between entities
python scripts/relationship_extractor.py \
  --pg-conn "postgresql://..." \
  --session-id <migration_session_id>
```

**Result:** Semantic relationships populated in `noi_entity_relations`

---

### Phase 4: Strategic Vector Seeding

```bash
# Step 4: Manually seed strategic vectors from O1
python scripts/seed_strategic_vectors.py \
  --pg-conn "postgresql://..." \
  --ontology-file docs/NOI-O1-MILEJCZYC-CORE.md
```

**Result:** High-level strategic dynamics tracked

---

## EXAMPLE: EMPLOYEE → EXECUTIVE ACTOR

### Old Approach (Failed)

```
SQLite: employees.full_name = "Sebastian Sawicki"
  ↓ (direct column mapping)
PostgreSQL: gmina_staff.first_name = "Sebastian", last_name = "Sawicki"
  ❌ Lost semantic meaning (just HR record)
```

### New Approach (O1-Aligned)

```
SQLite: employees.full_name = "Sebastian Sawicki"
  ↓ (raw ingestion)
Staging: raw_payload = {"full_name": "Sebastian Sawicki", ...}
  ↓ (semantic resolution)
Resolution: ontology_class = "executive_actor"
            entity_type = "Wójt"
            strategic_weight = 2.0
            fingerprint = sha256("sebastian sawicki|executive_actor")
  ↓ (canonical entity)
Canonical: entity_fingerprint = "a3f2b8c1..."
           canonical_name = "Sebastian Sawicki"
           ontology_class = "executive_actor"
           strategic_weight = 2.0
  ↓ (relationships)
Relations: ("Sebastian Sawicki") -[MANAGES]-> ("Urząd Gminy")
           ("Sebastian Sawicki") -[INITIATED]-> ("Uzdrowisko")
```

**Result:** Sebastian is now a **strategic agent** with weight 2.0, not just an HR record.

---

## COMPARISON WITH OLD SCHEMA

### What Changes

| Old Table | New Treatment |
|-----------|--------------|
| `citizen_feedback` | → Staging → Classified as `social_actor` interactions |
| `municipal_projects` | → Staging → Classified as `infrastructure_asset` or `strategic_vector` |
| `geospatial_registry` | → Staging → Classified as `infrastructure_asset` locations |
| `gmina_staff` | → Staging → Classified as `executive_actor` or `operational_agent` |
| `noi_core_entities` | → Merged with `noi_canonical_entities` (O1-aligned) |
| `service_requests` | → Staging → Classified as `social_actor` interactions |
| `semantic_tokens` | → Kept as-is (already semantic) |
| `token_ingestion_log` | → Kept as-is (audit trail) |

### What's Added

- ✅ `staging_raw_records` - Immutable buffer
- ✅ `semantic_resolution_log` - Classification audit trail
- ✅ `noi_canonical_entities` - O1-aligned knowledge layer
- ✅ `noi_entity_relations` - Graph edges
- ✅ `strategic_vectors` - High-level dynamics

---

## STRATEGIC IMPLICATIONS

### Why This Matters

The old approach treated P-OS as a **database system**. The new approach treats it as a **cognitive system**:

| Aspect | Database System | Cognitive System |
|--------|----------------|------------------|
| Primary Unit | Record | Entity |
| Identity | UUID | Fingerprint |
| Relationships | Foreign Keys | Semantic Edges |
| Meaning | Implicit | Explicit (O1) |
| Intelligence | None | Ontology-driven |
| Purpose | Storage | Cognition |

### What This Enables

1. **Strategic Reasoning**
   - System can answer: "What is the strategic impact of blocking Uzdrowisko?"
   - Not just: "Show me projects with status='blocked'"

2. **Entity Resolution**
   - System knows "Sebastian Sawicki" (from employees) = "Wójt" (from O1) = "Inicjator Uzdrowiska" (from projects)
   - Single canonical entity with multiple facets

3. **Relationship Discovery**
   - System can detect: "Wójt opposes Ferma Wipasz" from multiple data sources
   - Not just: "Show me service requests about farms"

4. **Temporal Dynamics**
   - System tracks: "Uzdrowisko initiative evolved from proposal (2024) → approval (2026) → monitoring (2026+)"
   - Not just: "Show me current project status"

---

## NEXT STEPS (Post-Quietness)

### Week 1: Infrastructure Setup (June 11-17)

1. Recreate PostgreSQL database with new 5-layer schema
2. Implement raw ingestion pipeline (SQLite → staging)
3. Test ontology binder on sample data
4. Validate fingerprint generation

### Week 2: Semantic Resolution (June 18-24)

1. Process all staging records through ontology binder
2. Review classification accuracy
3. Adjust patterns and weights
4. Populate initial canonical entities

### Week 3: Relationship Extraction (June 25 - July 1)

1. Implement relationship detection logic
2. Extract relationships from staging data
3. Populate `noi_entity_relations`
4. Validate relationship quality

### Week 4: Strategic Vector Seeding (July 2-8)

1. Manually seed strategic vectors from O1
2. Link vectors to canonical entities
3. Define vector timelines and phases
4. Create strategic dashboard queries

### Week 5: Neo4j Projection (July 9-15)

1. Design batch projection pipeline
2. Project canonical entities → Neo4j nodes
3. Project relationships → Neo4j edges
4. Validate graph integrity

---

## LESSONS LEARNED

### Key Insights

1. **Ontology Reveals True Architecture**
   - O1 showed us we're building a cognitive system, not a database
   - Previous failures were architectural, not technical

2. **Semantic Mediation is Critical**
   - Cannot map tables 1:1 when moving from data to knowledge
   - Need explicit ontology binding layer

3. **Identity Must Be Semantic**
   - UUIDs are technical, not meaningful
   - Fingerprints based on normalized identity + class are sovereign

4. **Strategic Weighting Changes Everything**
   - Not all entities are equal (Wójt = 2.0, Mieszkaniec = 0.8)
   - Enables prioritization and reasoning

5. **Relationships Are First-Class Citizens**
   - Foreign keys are implementation details
   - Semantic relationships are knowledge

---

## CONCLUSION

The NOI-O1 ontology has transformed P-OS from a **municipal database** into a **sovereign semantic operating system**.

This architecture properly implements:
- ✅ Immutable raw ingestion (Layer 1)
- ✅ Ontology-driven classification (Layer 2)
- ✅ Canonical knowledge entities (Layer 3)
- ✅ Semantic relationships (Layer 4)
- ✅ Strategic dynamics tracking (Layer 5)

The system is now ready to become what it was always meant to be:

> **A civic digital twin for institutional memory and strategic cognition**

---

**Stan: ETAP 4 ARCHITECTURE COMPLETE | SEMANTIC CANONICALIZATION DESIGNED | READY FOR IMPLEMENTATION** 🏛️🧭🛡️
