"""
P-OS v8.0 - Ontology Binder (Semantic Resolution Layer)
========================================================
Purpose: Bind raw SQLite records to NOI-O1 ontology classes
Architecture: Layer 2 semantic mediation between staging and canonical entities

Key Properties:
- Ontology-driven: Uses O1 definitions to classify entities
- Fingerprint-based: SHA-256 identity for canonical entities
- Strategic weighting: Assigns weights from O1 (e.g., Wójt = 2.0)
- Relationship extraction: Identifies semantic relationships between entities

Usage:
    python scripts/ontology_binder.py --staging-db <connection_string>
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import psycopg2
from dotenv import load_dotenv
import os

# Load credentials
load_dotenv('.env.db')


class OntologyBinder:
    """Binds raw staging records to NOI-O1 ontology classes."""
    
    def __init__(self, pg_conn_string: str):
        self.pg_conn_string = pg_conn_string
        
        # O1 Ontology Class Definitions
        self.ontology_classes = {
            # Executive Authority
            'executive_actor': {
                'patterns': ['wójt', 'zastępca wójta', 'sekretarz', 'skarbnik'],
                'strategic_weight': 2.0,
                'strategic_class': 'executive_authority'
            },
            
            # Governance Units
            'governance_unit': {
                'patterns': ['rada gminy', 'komisja', 'przewodniczący', 'wiceprzewodniczący'],
                'strategic_weight': 1.8,
                'strategic_class': 'governance_body'
            },
            
            # Operational Agents
            'operational_agent': {
                'patterns': ['kierownik', 'inspektor', 'referent', 'konserwator'],
                'strategic_weight': 1.2,
                'strategic_class': 'operational_role'
            },
            
            # Resilience Nodes
            'resilience_node': {
                'patterns': ['osp', 'straż pożarna', 'gops', 'szkoła', 'biblioteka'],
                'strategic_weight': 1.5,
                'strategic_class': 'community_resilience'
            },
            
            # Strategic Vectors
            'strategic_vector': {
                'patterns': ['uzdrowisko', 'tarcza', 'fundusz sołecki', 'kreatywna wieś'],
                'strategic_weight': 2.5,
                'strategic_class': 'strategic_initiative'
            },
            
            # Historical Entities
            'historical_entity': {
                'patterns': ['1136', '1516', '1566', 'herb', 'bullą gnieźnieńska'],
                'strategic_weight': 1.0,
                'strategic_class': 'historical_legitimacy'
            },
            
            # Social Actors
            'social_actor': {
                'patterns': ['mieszkaniec', 'radny', 'sołtys', 'aktywista'],
                'strategic_weight': 0.8,
                'strategic_class': 'civic_participation'
            },
            
            # Infrastructure
            'infrastructure_asset': {
                'patterns': ['droga', 'wodociąg', 'oczyszczalnia', 'świetlica', 'remiza'],
                'strategic_weight': 1.3,
                'strategic_class': 'critical_infrastructure'
            },
            
            # Default
            'unknown': {
                'patterns': [],
                'strategic_weight': 0.5,
                'strategic_class': 'unclassified'
            }
        }
        
        # Known entity mappings from O1
        self.known_entities = {
            # Executive
            'sebastian sawicki': {'type': 'Wójt', 'weight': 2.0, 'class': 'executive_actor'},
            'bogumiła dietrich': {'type': 'Sekretarz', 'weight': 1.8, 'class': 'executive_actor'},
            'joanna': {'type': 'Skarbnik', 'weight': 1.8, 'class': 'executive_actor'},
            'piotr hryniewicki': {'type': 'Zastępca Wójta', 'weight': 1.9, 'class': 'executive_actor'},
            
            # Council
            'tomasz nesterowicz': {'type': 'Przewodniczący Rady', 'weight': 1.9, 'class': 'governance_unit'},
            'aleksander oniśkiewicz': {'type': 'Wiceprzewodniczący Rady', 'weight': 1.8, 'class': 'governance_unit'},
            
            # Operational
            'piotr robert molski': {'type': 'Kierownik GOPS', 'weight': 1.3, 'class': 'operational_agent'},
            'urszula molska': {'type': 'Dyrektor SP', 'weight': 1.4, 'class': 'operational_agent'},
            'katarzyna wysocka': {'type': 'Kierownik Biblioteki', 'weight': 1.2, 'class': 'operational_agent'},
            'dominik dobrowolski': {'type': 'Prezes OSP', 'weight': 1.5, 'class': 'resilience_node'},
            'adam okoczuk': {'type': 'Konserwator Wodociągu', 'weight': 1.6, 'class': 'operational_agent'},
            
            # Organizations
            'osp milejczyce': {'type': 'OSP', 'weight': 1.5, 'class': 'resilience_node'},
            'gops milejczyce': {'type': 'GOPS', 'weight': 1.3, 'class': 'resilience_node'},
            'sp milejczyce': {'type': 'Szkoła Podstawowa', 'weight': 1.4, 'class': 'resilience_node'},
            'biblioteka gminna': {'type': 'Biblioteka', 'weight': 1.2, 'class': 'resilience_node'},
            'gok': {'type': 'GOK', 'weight': 1.2, 'class': 'resilience_node'},
            
            # Strategic
            'uzdrowisko': {'type': 'Status Uzdrowiskowy', 'weight': 2.5, 'class': 'strategic_vector'},
            'tarcza ekologiczna': {'type': 'Tarcza Ekologiczna', 'weight': 2.3, 'class': 'strategic_vector'},
            'fundusz sołecki': {'type': 'Fundusz Sołecki', 'weight': 1.8, 'class': 'strategic_vector'},
            'kreatywna wieś': {'type': 'Program Grantowy', 'weight': 1.8, 'class': 'strategic_vector'},
            
            # Conflicts
            'wipasz': {'type': 'Ferma Przemysłowa', 'weight': 2.0, 'class': 'strategic_vector'},
        }
    
    def compute_entity_fingerprint(self, name: str, ontology_class: str) -> str:
        """Compute deterministic fingerprint for entity identity.
        
        Formula: sha256(normalized_name + ontology_class)
        """
        normalized = name.lower().strip()
        identity_string = f"{normalized}|{ontology_class}"
        return hashlib.sha256(identity_string.encode('utf-8')).hexdigest()
    
    def classify_record(self, raw_payload: Dict) -> Tuple[str, Dict]:
        """Classify a raw record into an O1 ontology class.
        
        Returns: (ontology_class, metadata)
        """
        # Convert payload to searchable text
        searchable_text = json.dumps(raw_payload, default=str).lower()
        
        # Check known entities first (exact match)
        for known_name, metadata in self.known_entities.items():
            if known_name in searchable_text:
                return metadata['class'], {
                    'entity_type': metadata['type'],
                    'canonical_name': known_name.title(),
                    'strategic_weight': metadata['weight'],
                    'strategic_class': metadata['class'],
                    'confidence': 0.95,
                    'method': 'exact_match'
                }
        
        # Pattern matching for ontology classes
        best_match = 'unknown'
        best_score = 0
        
        for ontology_class, config in self.ontology_classes.items():
            if ontology_class == 'unknown':
                continue
            
            score = 0
            for pattern in config['patterns']:
                if pattern in searchable_text:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = ontology_class
        
        # Build metadata for matched class
        config = self.ontology_classes[best_match]
        
        # Try to extract canonical name
        canonical_name = self._extract_canonical_name(raw_payload)
        
        return best_match, {
            'entity_type': canonical_name or best_match.replace('_', ' ').title(),
            'canonical_name': canonical_name or 'Unknown',
            'strategic_weight': config['strategic_weight'],
            'strategic_class': config['strategic_class'],
            'confidence': min(0.3 + (best_score * 0.15), 0.9),
            'method': 'pattern_match' if best_score > 0 else 'default'
        }
    
    def _extract_canonical_name(self, payload: Dict) -> Optional[str]:
        """Extract canonical name from payload."""
        # Try common name fields
        for field in ['name', 'full_name', 'first_name', 'last_name', 
                     'project_name', 'unit_name', 'node_name', 'requester_name']:
            if field in payload and payload[field]:
                return str(payload[field])
        
        return None
    
    def ingest_to_staging(self, source_db: str, source_table: str, 
                         source_pk: str, raw_payload: Dict, 
                         migration_session_id: str) -> str:
        """Ingest raw record to staging_raw_records table.
        
        Returns: staging_record_id (UUID)
        """
        conn = psycopg2.connect(self.pg_conn_string)
        cursor = conn.cursor()
        
        try:
            # Compute hash of raw payload
            raw_hash = hashlib.sha256(
                json.dumps(raw_payload, sort_keys=True, default=str).encode('utf-8')
            ).hexdigest()
            
            # Insert into staging
            cursor.execute("""
                INSERT INTO staging_raw_records (
                    source_db, source_table, source_pk, raw_payload,
                    raw_hash, migration_session_id, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                source_db,
                source_table,
                source_pk,
                json.dumps(raw_payload, default=str),
                raw_hash,
                migration_session_id,
                'ontology_binder'
            ))
            
            staging_id = cursor.fetchone()[0]
            conn.commit()
            
            return str(staging_id)
        
        finally:
            cursor.close()
            conn.close()
    
    def resolve_semantic(self, staging_id: str, ontology_class: str, 
                        metadata: Dict) -> str:
        """Create semantic resolution log entry.
        
        Returns: entity_fingerprint
        """
        conn = psycopg2.connect(self.pg_conn_string)
        cursor = conn.cursor()
        
        try:
            # Compute fingerprint
            fingerprint = self.compute_entity_fingerprint(
                metadata['canonical_name'],
                ontology_class
            )
            
            # Insert resolution log
            cursor.execute("""
                INSERT INTO semantic_resolution_log (
                    staging_record_id, ontology_class, entity_type,
                    canonical_name, strategic_weight, strategic_class,
                    entity_fingerprint, canonical_person_key,
                    confidence_score, resolution_method, resolved_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                staging_id,
                ontology_class,
                metadata['entity_type'],
                metadata['canonical_name'],
                metadata['strategic_weight'],
                metadata['strategic_class'],
                fingerprint,
                metadata.get('canonical_person_key'),
                metadata['confidence'],
                metadata['method'],
                'ontology_binder'
            ))
            
            conn.commit()
            
            return fingerprint
        
        finally:
            cursor.close()
            conn.close()
    
    def upsert_canonical_entity(self, fingerprint: str, ontology_class: str,
                               metadata: Dict, properties: Dict = None) -> str:
        """Upsert canonical entity (create or update).
        
        Returns: entity_id (UUID)
        """
        conn = psycopg2.connect(self.pg_conn_string)
        cursor = conn.cursor()
        
        try:
            # Compute current hash
            entity_data = {
                'fingerprint': fingerprint,
                'name': metadata['canonical_name'],
                'class': ontology_class,
                'properties': properties or {}
            }
            current_hash = hashlib.sha256(
                json.dumps(entity_data, sort_keys=True, default=str).encode('utf-8')
            ).hexdigest()
            
            # Upsert
            cursor.execute("""
                INSERT INTO noi_canonical_entities (
                    entity_fingerprint, canonical_name, ontology_class,
                    entity_type, strategic_weight, strategic_class,
                    description, properties, is_active,
                    created_by, current_hash
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (entity_fingerprint) DO UPDATE SET
                    canonical_name = EXCLUDED.canonical_name,
                    entity_type = EXCLUDED.entity_type,
                    strategic_weight = EXCLUDED.strategic_weight,
                    strategic_class = EXCLUDED.strategic_class,
                    description = COALESCE(EXCLUDED.description, noi_canonical_entities.description),
                    properties = CASE 
                        WHEN EXCLUDED.properties IS NOT NULL 
                        THEN noi_canonical_entities.properties || EXCLUDED.properties
                        ELSE noi_canonical_entities.properties
                    END,
                    last_updated = NOW() AT TIME ZONE 'UTC',
                    updated_by = EXCLUDED.created_by,
                    previous_hash = noi_canonical_entities.current_hash,
                    current_hash = EXCLUDED.current_hash,
                    source_count = noi_canonical_entities.source_count + 1
                RETURNING id
            """, (
                fingerprint,
                metadata['canonical_name'],
                ontology_class,
                metadata['entity_type'],
                metadata['strategic_weight'],
                metadata['strategic_class'],
                None,  # description
                json.dumps(properties or {}, default=str),
                True,  # is_active
                'ontology_binder',
                current_hash
            ))
            
            entity_id = cursor.fetchone()[0]
            conn.commit()
            
            return str(entity_id)
        
        finally:
            cursor.close()
            conn.close()
    
    def process_staging_batch(self, migration_session_id: str, limit: int = 100):
        """Process a batch of staging records through semantic resolution.
        
        This is the main orchestration method:
        1. Fetch unprocessed staging records
        2. Classify each record
        3. Create resolution log
        4. Upsert canonical entity
        """
        conn = psycopg2.connect(self.pg_conn_string)
        cursor = conn.cursor()
        
        try:
            # Fetch unprocessed staging records
            cursor.execute("""
                SELECT id, source_db, source_table, source_pk, raw_payload
                FROM staging_raw_records
                WHERE migration_session_id = %s
                AND id NOT IN (
                    SELECT staging_record_id FROM semantic_resolution_log
                )
                LIMIT %s
            """, (migration_session_id, limit))
            
            records = cursor.fetchall()
            print(f"Processing {len(records)} staging records...")
            
            processed = 0
            for record in records:
                staging_id, source_db, source_table, source_pk, raw_payload = record
                
                # Step 1: Classify
                ontology_class, metadata = self.classify_record(raw_payload)
                
                # Step 2: Resolve semantic
                fingerprint = self.resolve_semantic(staging_id, ontology_class, metadata)
                
                # Step 3: Upsert canonical entity
                self.upsert_canonical_entity(fingerprint, ontology_class, metadata)
                
                processed += 1
                
                if processed % 10 == 0:
                    print(f"  Processed {processed}/{len(records)} records")
            
            print(f"✅ Batch complete: {processed} records semantically resolved")
            return processed
        
        finally:
            cursor.close()
            conn.close()


def main():
    """Main execution for ontology binding."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ontology Binder - Semantic Resolution Layer')
    parser.add_argument('--pg-conn', required=True, help='PostgreSQL connection string')
    parser.add_argument('--session-id', required=True, help='Migration session ID to process')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for processing')
    
    args = parser.parse_args()
    
    binder = OntologyBinder(args.pg_conn)
    
    print("="*70)
    print("P-OS v8.0 - ONTOLOGY BINDER (Semantic Resolution Layer)")
    print("="*70)
    print(f"Session ID: {args.session_id}")
    print(f"Batch Size: {args.batch_size}")
    print("="*70)
    
    processed = binder.process_staging_batch(args.session_id, args.batch_size)
    
    print(f"\n✅ Ontology binding complete: {processed} entities resolved")


if __name__ == '__main__':
    main()
