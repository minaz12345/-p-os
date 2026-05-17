-- ============================================================================
-- P-OS v8.0 - Milejczyce Operational Database Schema
-- ============================================================================
-- Purpose: Canonical operational truth for Milejczyce gmina
-- Architecture: Layer 2 - PostgreSQL (operational memory)
-- Design Principles:
--   - Immutable audit chains
--   - Strict FK integrity
--   - UTC-only timestamps
--   - Idempotency keys
--   - Bounded domains
-- ============================================================================

-- Create database (run separately):
-- CREATE DATABASE milejczyce_operational;
-- \c milejczyce_operational

-- Enable UUID extension for idempotency keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- DOMAIN 3: GEOSPATIAL REGISTRY (created first - referenced by others)
-- ============================================================================

CREATE TABLE geospatial_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parcel_number VARCHAR(50) UNIQUE NOT NULL,
    address VARCHAR(255),
    village VARCHAR(100),
    municipality VARCHAR(100) DEFAULT 'Milejczyce',
    
    -- Coordinates (WGS84)
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    
    -- Land use
    land_use_type VARCHAR(50) 
        CHECK (land_use_type IN ('residential', 'agricultural', 'commercial', 'industrial', 'forest', 'water', 'public')),
    area_sqm DECIMAL(12,2),
    
    -- Ownership
    owner_type VARCHAR(50) 
        CHECK (owner_type IN ('private', 'municipal', 'state', 'church', 'cooperative')),
    owner_name VARCHAR(255),
    
    -- Metadata
    zoning_classification VARCHAR(50),
    building_permits_count INT DEFAULT 0,
    
    -- Audit
    created_by VARCHAR(100) NOT NULL,
    updated_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    
    -- Idempotency
    idempotency_key VARCHAR(255) UNIQUE,
    
    -- Hash chain
    previous_hash VARCHAR(64),
    current_hash VARCHAR(64) NOT NULL
);

CREATE INDEX idx_geospatial_registry_parcel ON geospatial_registry(parcel_number);
CREATE INDEX idx_geospatial_registry_village ON geospatial_registry(village);

-- ============================================================================
-- DOMAIN 4: ORGANIZATIONAL STRUCTURE (created second - referenced by staff)
-- ============================================================================

CREATE TABLE org_structure (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    unit_code VARCHAR(50) UNIQUE NOT NULL,
    unit_name VARCHAR(255) NOT NULL,
    unit_type VARCHAR(50) NOT NULL 
        CHECK (unit_type IN ('executive', 'legislative', 'administrative', 'service', 'community')),
    
    -- Hierarchy
    parent_unit_id UUID,
    level INT NOT NULL DEFAULT 1,
    
    -- Contact
    address VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    
    -- Leadership
    head_position VARCHAR(100),
    head_name VARCHAR(255),
    
    -- Staff count
    staff_count INT DEFAULT 0,
    
    -- Audit
    created_by VARCHAR(100) NOT NULL,
    updated_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    
    -- Idempotency
    idempotency_key VARCHAR(255) UNIQUE,
    
    -- Hash chain
    previous_hash VARCHAR(64),
    current_hash VARCHAR(64) NOT NULL,
    
    CONSTRAINT fk_org_structure_parent 
        FOREIGN KEY (parent_unit_id) REFERENCES org_structure(id) ON DELETE SET NULL
);

CREATE INDEX idx_org_structure_type ON org_structure(unit_type);
CREATE INDEX idx_org_structure_parent ON org_structure(parent_unit_id);

-- ============================================================================
-- DOMAIN 1: CITIZEN ENGAGEMENT
-- ============================================================================================================================================

CREATE TABLE citizen_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    citizen_id VARCHAR(50) NOT NULL,
    feedback_type VARCHAR(50) NOT NULL CHECK (feedback_type IN ('complaint', 'suggestion', 'request', 'praise')),
    category VARCHAR(100),
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'submitted' 
        CHECK (status IN ('submitted', 'under_review', 'in_progress', 'resolved', 'closed')),
    priority VARCHAR(20) DEFAULT 'normal' 
        CHECK (priority IN ('low', 'normal', 'high', 'critical')),
    
    -- Location context
    location_id UUID,
    municipality VARCHAR(100) DEFAULT 'Milejczyce',
    
    -- Temporal tracking
    submitted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit chain
    created_by VARCHAR(100) NOT NULL,
    updated_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    
    -- Idempotency
    idempotency_key VARCHAR(255) UNIQUE,
    
    -- Hash chain for immutability
    previous_hash VARCHAR(64),
    current_hash VARCHAR(64) NOT NULL,
    
    CONSTRAINT fk_citizen_feedback_location 
        FOREIGN KEY (location_id) REFERENCES geospatial_registry(id) ON DELETE SET NULL
);

CREATE INDEX idx_citizen_feedback_status ON citizen_feedback(status);
CREATE INDEX idx_citizen_feedback_submitted_at ON citizen_feedback(submitted_at);
CREATE INDEX idx_citizen_feedback_citizen_id ON citizen_feedback(citizen_id);

-- ============================================================================
-- DOMAIN 2: MUNICIPAL PROJECTS
-- ============================================================================

CREATE TABLE municipal_projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    project_type VARCHAR(50) NOT NULL 
        CHECK (project_type IN ('infrastructure', 'social', 'environmental', 'cultural', 'economic')),
    
    -- Financial tracking
    budget_pln DECIMAL(15,2),
    spent_pln DECIMAL(15,2) DEFAULT 0,
    funding_source VARCHAR(100),
    
    -- Timeline
    planned_start DATE,
    planned_end DATE,
    actual_start DATE,
    actual_end DATE,
    
    -- Status
    status VARCHAR(30) NOT NULL DEFAULT 'planning'
        CHECK (status IN ('planning', 'approved', 'in_progress', 'on_hold', 'completed', 'cancelled')),
    
    -- Strategic alignment
    strategic_goal VARCHAR(255),
    noi_ontology_ref VARCHAR(100),  -- Reference to NOI-O1 ontology
    
    -- Location
    location_id UUID,
    
    -- Audit
    created_by VARCHAR(100) NOT NULL,
    updated_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    
    -- Idempotency
    idempotency_key VARCHAR(255) UNIQUE,
    
    -- Hash chain
    previous_hash VARCHAR(64),
    current_hash VARCHAR(64) NOT NULL,
    
    CONSTRAINT fk_municipal_projects_location 
        FOREIGN KEY (location_id) REFERENCES geospatial_registry(id) ON DELETE SET NULL
);

CREATE INDEX idx_municipal_projects_status ON municipal_projects(status);
CREATE INDEX idx_municipal_projects_type ON municipal_projects(project_type);

-- ============================================================================
-- DOMAIN 5: GMINA STAFF
-- ============================================================================

CREATE TABLE gmina_staff (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    position VARCHAR(150) NOT NULL,
    
    -- Organizational assignment
    unit_id UUID NOT NULL,
    
    -- Contact
    email VARCHAR(255),
    phone VARCHAR(50),
    office_location VARCHAR(100),
    
    -- Employment details
    employment_type VARCHAR(50) 
        CHECK (employment_type IN ('full-time', 'part-time', 'contract', 'volunteer')),
    hire_date DATE,
    termination_date DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Provenance tracking (canonical convergence)
    source_system VARCHAR(50) NOT NULL DEFAULT 'sqlite',
    source_table VARCHAR(100) NOT NULL,
    source_primary_key VARCHAR(255),
    source_record_hash VARCHAR(64),
    migration_session_id UUID NOT NULL,
    canonical_person_key VARCHAR(255),  -- For future entity resolution
    
    -- Audit
    created_by VARCHAR(100) NOT NULL,
    updated_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    
    -- Idempotency
    idempotency_key VARCHAR(255) UNIQUE,
    
    -- Hash chain
    previous_hash VARCHAR(64),
    current_hash VARCHAR(64) NOT NULL,
    
    CONSTRAINT fk_gmina_staff_unit 
        FOREIGN KEY (unit_id) REFERENCES org_structure(id) ON DELETE CASCADE,
    CONSTRAINT uq_source_provenance 
        UNIQUE(source_system, source_table, source_primary_key)
);

CREATE INDEX idx_gmina_staff_unit ON gmina_staff(unit_id);
CREATE INDEX idx_gmina_staff_active ON gmina_staff(is_active);

-- ============================================================================
-- DOMAIN 6: NOI CORE ENTITIES (Ontology-backed)
-- ============================================================================

CREATE TABLE noi_core_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL 
        CHECK (entity_type IN ('person', 'historical_event', 'project', 'institution', 'community_organization', 'pain_point', 'strategic_tension')),
    entity_name VARCHAR(255) NOT NULL,
    
    -- NOI-O1 ontology reference
    ontology_class VARCHAR(100) NOT NULL,
    ontology_uri VARCHAR(255),
    
    -- Properties (JSONB for flexibility)
    properties JSONB,
    
    -- Relationships (stored as JSON array for graph projection)
    relationships JSONB DEFAULT '[]'::jsonb,
    
    -- Temporal context
    valid_from TIMESTAMP WITH TIME ZONE,
    valid_to TIMESTAMP WITH TIME ZONE,
    
    -- Audit
    created_by VARCHAR(100) NOT NULL,
    updated_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    
    -- Idempotency
    idempotency_key VARCHAR(255) UNIQUE,
    
    -- Hash chain
    previous_hash VARCHAR(64),
    current_hash VARCHAR(64) NOT NULL
);

CREATE INDEX idx_noi_core_type ON noi_core_entities(entity_type);
CREATE INDEX idx_noi_core_ontology ON noi_core_entities(ontology_class);
CREATE INDEX idx_noi_core_properties ON noi_core_entities USING GIN(properties);

-- ============================================================================
-- DOMAIN 7: SERVICE REQUESTS
-- ============================================================================

CREATE TABLE service_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    request_number VARCHAR(50) UNIQUE NOT NULL,
    requester_id VARCHAR(50),
    service_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    
    -- Status tracking
    status VARCHAR(30) NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'assigned', 'in_progress', 'pending_approval', 'completed', 'cancelled')),
    priority VARCHAR(20) DEFAULT 'normal'
        CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    
    -- Assignment
    assigned_to UUID,  -- gmina_staff.id
    assigned_at TIMESTAMP WITH TIME ZONE,
    
    -- Resolution
    resolution_notes TEXT,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Location
    location_id UUID,
    
    -- Audit
    created_by VARCHAR(100) NOT NULL,
    updated_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    
    -- Idempotency
    idempotency_key VARCHAR(255) UNIQUE,
    
    -- Hash chain
    previous_hash VARCHAR(64),
    current_hash VARCHAR(64) NOT NULL,
    
    CONSTRAINT fk_service_requests_assigned 
        FOREIGN KEY (assigned_to) REFERENCES gmina_staff(id) ON DELETE SET NULL,
    CONSTRAINT fk_service_requests_location 
        FOREIGN KEY (location_id) REFERENCES geospatial_registry(id) ON DELETE SET NULL
);

CREATE INDEX idx_service_requests_status ON service_requests(status);
CREATE INDEX idx_service_requests_type ON service_requests(service_type);

-- ============================================================================
-- AUDIT LOG (Cross-domain immutable audit trail)
-- ============================================================================

CREATE TABLE operational_audit_log (
    id BIGSERIAL PRIMARY KEY,
    correlation_id UUID NOT NULL,
    operation VARCHAR(50) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    
    -- Action type
    action VARCHAR(20) NOT NULL 
        CHECK (action IN ('INSERT', 'UPDATE', 'DELETE', 'MIGRATE', 'PROJECT')),
    
    -- Before/after state (JSONB)
    before_state JSONB,
    after_state JSONB,
    
    -- Hash verification
    source_hash VARCHAR(64),
    target_hash VARCHAR(64),
    
    -- Metadata
    performed_by VARCHAR(100) NOT NULL,
    performed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    ip_address INET,
    user_agent TEXT,
    
    -- Verification
    verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP WITH TIME ZONE,
    verified_by VARCHAR(100)
);

CREATE INDEX idx_operational_audit_correlation ON operational_audit_log(correlation_id);
CREATE INDEX idx_operational_audit_table ON operational_audit_log(table_name);
CREATE INDEX idx_operational_audit_performed_at ON operational_audit_log(performed_at);

-- ============================================================================
-- DATA LINEAGE TRACKING (Migration provenance)
-- ============================================================================

CREATE TABLE data_lineage_tracking (
    id BIGSERIAL PRIMARY KEY,
    migration_id UUID NOT NULL,
    source_system VARCHAR(50) NOT NULL DEFAULT 'sqlite',
    source_table VARCHAR(100) NOT NULL,
    target_table VARCHAR(100) NOT NULL,
    
    -- Record counts
    records_extracted INT,
    records_transformed INT,
    records_loaded INT,
    records_failed INT,
    
    -- Hash verification
    source_hash VARCHAR(64) NOT NULL,
    target_hash VARCHAR(64) NOT NULL,
    hash_match BOOLEAN NOT NULL,
    
    -- Migration metadata
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds DECIMAL(10,2),
    
    -- Status
    status VARCHAR(30) NOT NULL DEFAULT 'in_progress'
        CHECK (status IN ('in_progress', 'completed', 'failed', 'rolled_back')),
    
    -- Error tracking
    error_message TEXT,
    
    -- Performed by
    performed_by VARCHAR(100) NOT NULL
);

CREATE INDEX idx_data_lineage_migration ON data_lineage_tracking(migration_id);
CREATE INDEX idx_data_lineage_status ON data_lineage_tracking(status);

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE citizen_feedback IS 'Citizen engagement and feedback tracking';
COMMENT ON TABLE municipal_projects IS 'Municipal project portfolio management';
COMMENT ON TABLE geospatial_registry IS 'Land parcel and location registry';
COMMENT ON TABLE org_structure IS 'Organizational hierarchy and units';
COMMENT ON TABLE gmina_staff IS 'Staff directory and organizational assignments';
COMMENT ON TABLE noi_core_entities IS 'NOI-O1 ontology-backed entities for semantic layer';
COMMENT ON TABLE service_requests IS 'Public service request tracking';
COMMENT ON TABLE operational_audit_log IS 'Immutable cross-domain audit trail';
COMMENT ON TABLE data_lineage_tracking IS 'Migration provenance and hash verification';

-- ============================================================================
-- SEMANTIC TOKENS TABLE (for NOI semantic layer)
-- ============================================================================

CREATE TABLE semantic_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_id VARCHAR(100) UNIQUE NOT NULL,
    content TEXT,
    layer INTEGER NOT NULL DEFAULT 0,
    
    -- Semantic properties
    type VARCHAR(50),
    weight REAL DEFAULT 1.0,
    weight_max REAL DEFAULT 1.0,
    status VARCHAR(30) DEFAULT 'active',
    tags TEXT,
    validated_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    owner VARCHAR(100),
    
    -- Audit
    created_by VARCHAR(100) NOT NULL,
    updated_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    
    -- Idempotency
    idempotency_key VARCHAR(255) UNIQUE,
    
    -- Hash chain
    previous_hash VARCHAR(64),
    current_hash VARCHAR(64) NOT NULL
);

CREATE INDEX idx_semantic_tokens_token_id ON semantic_tokens(token_id);
CREATE INDEX idx_semantic_tokens_layer ON semantic_tokens(layer);

COMMENT ON TABLE semantic_tokens IS 'Semantic tokens for ontology-backed knowledge representation';

-- ============================================================================
-- TOKEN INGESTION LOG (tracking token ingestion events)
-- ============================================================================

CREATE TABLE token_ingestion_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_id VARCHAR(100) NOT NULL,
    source VARCHAR(100) NOT NULL,
    content TEXT,
    checksum VARCHAR(255) NOT NULL,  -- Increased from 64 to accommodate longer checksums
    ingested_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    
    -- Audit
    created_by VARCHAR(100) NOT NULL,
    updated_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    
    -- Idempotency
    idempotency_key VARCHAR(255) UNIQUE,
    
    -- Hash chain
    previous_hash VARCHAR(64),
    current_hash VARCHAR(64) NOT NULL
);

CREATE INDEX idx_token_ingestion_log_token_id ON token_ingestion_log(token_id);
CREATE INDEX idx_token_ingestion_log_source ON token_ingestion_log(source);
CREATE INDEX idx_token_ingestion_log_ingested_at ON token_ingestion_log(ingested_at);

COMMENT ON TABLE token_ingestion_log IS 'Audit trail for token ingestion events with checksums';

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================

-- ============================================================================
-- ETAP 4: SEMANTIC CANONICALIZATION LAYERS
-- ============================================================================

-- Layer 1: RAW STAGING ZONE (immutable ingestion buffer)
CREATE TABLE staging_raw_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_db VARCHAR(100) NOT NULL,
    source_table VARCHAR(100) NOT NULL,
    source_pk TEXT,
    raw_payload JSONB NOT NULL,
    raw_hash VARCHAR(64) NOT NULL,
    ingested_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    migration_session_id UUID NOT NULL,
    
    -- Audit
    created_by VARCHAR(100) NOT NULL DEFAULT 'migration_pipeline',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX idx_staging_source_db ON staging_raw_records(source_db);
CREATE INDEX idx_staging_source_table ON staging_raw_records(source_table);
CREATE INDEX idx_staging_migration_session ON staging_raw_records(migration_session_id);
CREATE INDEX idx_staging_ingested_at ON staging_raw_records(ingested_at);

COMMENT ON TABLE staging_raw_records IS 'Immutable raw ingestion buffer - zero transformation, pure archival';

-- Layer 2: SEMANTIC RESOLUTION LOG (tracks ontology binding decisions)
CREATE TABLE semantic_resolution_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    staging_record_id UUID NOT NULL REFERENCES staging_raw_records(id) ON DELETE CASCADE,
    
    -- Ontology binding
    ontology_class VARCHAR(100) NOT NULL,  -- e.g., 'executive_actor', 'governance_unit'
    entity_type VARCHAR(100),              -- e.g., 'Wójt', 'Komisja', 'OSP'
    canonical_name VARCHAR(255),           -- Normalized entity name
    
    -- Strategic weight
    strategic_weight REAL DEFAULT 1.0,     -- From O1 ontology (e.g., Wójt = 2.0)
    strategic_class VARCHAR(50),           -- e.g., 'executive_authority', 'resilience_node'
    
    -- Identity resolution
    entity_fingerprint VARCHAR(64) NOT NULL,  -- sha256(normalized_identity + ontology_class)
    canonical_person_key VARCHAR(255),     -- For person entities (NULL for non-person)
    
    -- Resolution metadata
    confidence_score REAL DEFAULT 1.0,
    resolution_method VARCHAR(50),         -- 'exact_match', 'fuzzy_match', 'manual'
    resolved_by VARCHAR(100),
    resolved_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX idx_semantic_resolution_staging ON semantic_resolution_log(staging_record_id);
CREATE INDEX idx_semantic_resolution_ontology_class ON semantic_resolution_log(ontology_class);
CREATE INDEX idx_semantic_resolution_fingerprint ON semantic_resolution_log(entity_fingerprint);

COMMENT ON TABLE semantic_resolution_log IS 'Tracks ontology binding decisions and entity resolution';

-- Layer 3: CANONICAL ENTITIES (O1-aligned knowledge layer)
CREATE TABLE noi_canonical_entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_fingerprint VARCHAR(64) UNIQUE NOT NULL,
    
    -- Core identity
    canonical_name VARCHAR(255) NOT NULL,
    ontology_class VARCHAR(100) NOT NULL,  -- From O1: Agent, Block, Event, etc.
    entity_type VARCHAR(100),              -- Specific type: Wójt, Komisja, OSP, etc.
    
    -- Strategic properties
    strategic_weight REAL DEFAULT 1.0,
    strategic_class VARCHAR(50),
    description TEXT,
    
    -- Temporal validity
    valid_from TIMESTAMP WITH TIME ZONE,
    valid_to TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Source provenance
    source_count INTEGER DEFAULT 1,        -- How many raw records contributed
    first_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    
    -- Metadata
    properties JSONB DEFAULT '{}',
    tags TEXT[],
    
    -- Audit
    created_by VARCHAR(100) NOT NULL DEFAULT 'semantic_resolver',
    updated_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    
    -- Hash chain
    previous_hash VARCHAR(64),
    current_hash VARCHAR(64) NOT NULL
);

CREATE INDEX idx_canonical_fingerprint ON noi_canonical_entities(entity_fingerprint);
CREATE INDEX idx_canonical_ontology_class ON noi_canonical_entities(ontology_class);
CREATE INDEX idx_canonical_entity_type ON noi_canonical_entities(entity_type);
CREATE INDEX idx_canonical_active ON noi_canonical_entities(is_active);

COMMENT ON TABLE noi_canonical_entities IS 'Canonical knowledge entities aligned with NOI-O1 ontology';

-- Layer 4: SEMANTIC RELATIONSHIPS (graph edges between entities)
CREATE TABLE noi_entity_relations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Relationship endpoints
    source_entity_fingerprint VARCHAR(64) NOT NULL REFERENCES noi_canonical_entities(entity_fingerprint) ON DELETE CASCADE,
    target_entity_fingerprint VARCHAR(64) NOT NULL REFERENCES noi_canonical_entities(entity_fingerprint) ON DELETE CASCADE,
    
    -- Relationship type
    relation_type VARCHAR(100) NOT NULL,   -- e.g., 'manages', 'opposes', 'supports', 'located_in'
    relation_weight REAL DEFAULT 1.0,
    
    -- Context
    description TEXT,
    valid_from TIMESTAMP WITH TIME ZONE,
    valid_to TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Provenance
    derived_from_staging UUID REFERENCES staging_raw_records(id),
    confidence_score REAL DEFAULT 1.0,
    
    -- Audit
    created_by VARCHAR(100) NOT NULL DEFAULT 'semantic_resolver',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX idx_relations_source ON noi_entity_relations(source_entity_fingerprint);
CREATE INDEX idx_relations_target ON noi_entity_relations(target_entity_fingerprint);
CREATE INDEX idx_relations_type ON noi_entity_relations(relation_type);
CREATE UNIQUE INDEX idx_relations_unique_pair ON noi_entity_relations(source_entity_fingerprint, target_entity_fingerprint, relation_type);

COMMENT ON TABLE noi_entity_relations IS 'Semantic relationships between canonical entities (graph edges)';

-- Layer 5: STRATEGIC VECTORS (high-level strategic dynamics from O1)
CREATE TABLE strategic_vectors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vector_name VARCHAR(255) NOT NULL,     -- e.g., 'Uzdrowisko', 'Tarcza Ekologiczna'
    vector_type VARCHAR(100) NOT NULL,     -- e.g., 'strategic_initiative', 'legal_process', 'conflict'
    
    -- Strategic properties
    priority REAL DEFAULT 1.0,
    status VARCHAR(50) DEFAULT 'active',   -- active, blocked, completed, abandoned
    phase VARCHAR(50),                     -- e.g., 'Faza A', 'monitoring', 'implementation'
    
    -- Timeline
    initiated_at TIMESTAMP WITH TIME ZONE,
    target_completion DATE,
    actual_completion DATE,
    
    -- Context
    description TEXT,
    challenges TEXT[],
    opportunities TEXT[],
    
    -- Related entities
    related_entities TEXT[],               -- Array of entity_fingerprints
    
    -- Audit
    created_by VARCHAR(100) NOT NULL DEFAULT 'semantic_resolver',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX idx_strategic_vector_type ON strategic_vectors(vector_type);
CREATE INDEX idx_strategic_status ON strategic_vectors(status);

COMMENT ON TABLE strategic_vectors IS 'High-level strategic dynamics and initiatives from O1 ontology';

-- Add comments for new tables
COMMENT ON TABLE staging_raw_records IS 'Layer 1: Immutable raw ingestion buffer';
COMMENT ON TABLE semantic_resolution_log IS 'Layer 2: Ontology binding decisions';
COMMENT ON TABLE noi_canonical_entities IS 'Layer 3: Canonical knowledge entities (O1-aligned)';
COMMENT ON TABLE noi_entity_relations IS 'Layer 4: Semantic relationships (graph edges)';
COMMENT ON TABLE strategic_vectors IS 'Layer 5: Strategic vectors and dynamics';
