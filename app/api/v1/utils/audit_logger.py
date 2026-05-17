"""
Audit Logger for Citizen Portal
Logs all API interactions to Neo4j AuditTrail nodes
"""

import hashlib
import json
from datetime import datetime
from typing import Optional, Dict
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.db.neo4j_connection import execute_cypher_query
except ImportError:
    print("⚠️  Warning: Neo4j connection not available for audit logging")
    def execute_cypher_query(*args, **kwargs):
        pass


def log_access_attempt(
    username: str,
    action: str,
    endpoint: str,
    ip_address: str,
    reason: Optional[str] = None,
    tier: Optional[str] = None
):
    """
    Log access attempt to AuditTrail
    
    Args:
        username: User identifier
        action: Action type (ACCESS_GRANTED, ACCESS_DENIED, etc.)
        endpoint: API endpoint accessed
        ip_address: Client IP address
        reason: Reason for denial or additional context
        tier: Data classification tier requested
    """
    try:
        # Generate immutable hash
        canonical_data = json.dumps({
            'username': username,
            'action': action,
            'endpoint': endpoint,
            'timestamp': datetime.now().isoformat()
        }, sort_keys=True)
        audit_hash = hashlib.sha256(canonical_data.encode()).hexdigest()
        
        query = """
        CREATE (audit:AuditTrail {
            event_type: 'API_ACCESS',
            username: $username,
            action: $action,
            endpoint: $endpoint,
            ip_address: $ip_address,
            reason: $reason,
            tier: $tier,
            timestamp: datetime(),
            audit_hash: $audit_hash
        })
        """
        
        execute_cypher_query(query, {
            'username': username,
            'action': action,
            'endpoint': endpoint,
            'ip_address': ip_address,
            'reason': reason or '',
            'tier': tier or '',
            'audit_hash': audit_hash
        })
    except Exception as e:
        print(f"⚠️  Audit logging failed: {e}")


def log_gdpr_action(
    citizen_id: str,
    action_type: str,
    result: str,
    ip_address: str,
    details: Optional[Dict] = None
):
    """
    Log GDPR-related actions (export/erasure)
    
    Args:
        citizen_id: Citizen identifier
        action_type: GDPR_EXPORT or GDPR_ERASURE
        result: SUCCESS or FAILURE
        ip_address: Client IP address
        details: Additional details dictionary
    """
    try:
        # Generate immutable hash
        canonical_data = json.dumps({
            'citizen_id': citizen_id,
            'action': action_type,
            'timestamp': datetime.now().isoformat()
        }, sort_keys=True)
        audit_hash = hashlib.sha256(canonical_data.encode()).hexdigest()
        
        query = """
        CREATE (audit:AuditTrail {
            event_type: 'GDPR_ACTION',
            citizen_id: $citizen_id,
            action: $action_type,
            result: $result,
            ip_address: $ip_address,
            details: $details,
            timestamp: datetime(),
            audit_hash: $audit_hash,
            legal_basis: 'RODO Art. 15/17'
        })
        """
        
        execute_cypher_query(query, {
            'citizen_id': citizen_id,
            'action_type': action_type,
            'result': result,
            'ip_address': ip_address,
            'details': json.dumps(details) if details else '',
            'audit_hash': audit_hash
        })
    except Exception as e:
        print(f"⚠️  GDPR audit logging failed: {e}")


def log_complaint_submission(
    citizen_id: str,
    complaint_id: str,
    category: str,
    ip_address: str
):
    """
    Log complaint submission
    
    Args:
        citizen_id: Citizen identifier
        complaint_id: Generated complaint ID
        category: Complaint category
        ip_address: Client IP address
    """
    try:
        canonical_data = json.dumps({
            'citizen_id': citizen_id,
            'complaint_id': complaint_id,
            'timestamp': datetime.now().isoformat()
        }, sort_keys=True)
        audit_hash = hashlib.sha256(canonical_data.encode()).hexdigest()
        
        query = """
        CREATE (audit:AuditTrail {
            event_type: 'COMPLAINT_SUBMITTED',
            citizen_id: $citizen_id,
            complaint_id: $complaint_id,
            category: $category,
            ip_address: $ip_address,
            timestamp: datetime(),
            audit_hash: $audit_hash
        })
        """
        
        execute_cypher_query(query, {
            'citizen_id': citizen_id,
            'complaint_id': complaint_id,
            'category': category,
            'ip_address': ip_address,
            'audit_hash': audit_hash
        })
    except Exception as e:
        print(f"⚠️  Complaint audit logging failed: {e}")
