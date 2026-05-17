"""
GDPR Compliance Endpoints
Implements RODO Art. 15 (Right of Access) and Art. 17 (Right to Erasure)
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from scripts.gdpr_erasure import GDPRDataErasure
    from core.db.neo4j_connection import execute_cypher_query
except ImportError as e:
    print(f"⚠️  Warning: Could not import GDPR modules: {e}")

from app.api.v1.middleware.rbac_middleware import get_current_user, rbac_check
from app.api.v1.utils.audit_logger import log_gdpr_action

router = APIRouter()


# Request models
class GDPRExportRequest(BaseModel):
    citizen_id: str
    format: str = "json"  # json or csv
    include_related: bool = True


class GDPRERequest(BaseModel):
    citizen_id: str
    reason: str
    anonymize_feedback: bool = True


@router.post("/gdpr-export")
async def gdpr_export(request: Request, body: GDPRExportRequest, current_user: dict = Depends(get_current_user)):
    """
    GDPR Art. 15 - Right of Access
    Export all personal data for a citizen
    
    Args:
        citizen_id: Citizen identifier
        format: Output format (json/csv)
        include_related: Include related entities
    
    Returns:
        JSON/CSV file with all citizen data
    """
    citizen_id = body.citizen_id
    ip_address = request.client.host if request.client else "unknown"
    
    # RBAC check - citizen can only access their own data
    if current_user['role'] == 'citizen' and current_user['username'] != citizen_id:
        log_gdpr_action(
            citizen_id=citizen_id,
            action_type="GDPR_EXPORT",
            result="FAILURE_UNAUTHORIZED",
            ip_address=ip_address,
            details={'reason': 'Citizen attempted to access another citizen\'s data'}
        )
        raise HTTPException(status_code=403, detail="Access denied: Can only export own data")
    
    try:
        # Query Neo4j for citizen data
        query = """
        MATCH (c:Citizen {citizen_id: $citizen_id})
        OPTIONAL MATCH (c)-[r]-(related)
        RETURN c AS citizen, collect(DISTINCT related) AS related_nodes
        """
        
        result = execute_cypher_query(query, {'citizen_id': citizen_id})
        
        if not result or not result.get('records'):
            log_gdpr_action(
                citizen_id=citizen_id,
                action_type="GDPR_EXPORT",
                result="FAILURE_NOT_FOUND",
                ip_address=ip_address
            )
            raise HTTPException(status_code=404, detail=f"Citizen {citizen_id} not found")
        
        record = result['records'][0]
        citizen_data = dict(record['citizen']) if record['citizen'] else None
        
        if not citizen_data:
            raise HTTPException(status_code=404, detail="Citizen data not found")
        
        # Build export data
        export_data = {
            'export_metadata': {
                'citizen_id': citizen_id,
                'export_date': datetime.now().isoformat(),
                'legal_basis': 'RODO Art. 15 - Right of Access',
                'format': body.format,
                'requested_by': current_user['username']
            },
            'personal_data': citizen_data,
            'related_entities': []
        }
        
        # Add related entities if requested
        if body.include_related and record.get('related_nodes'):
            for node in record['related_nodes']:
                if node:  # Skip None values
                    export_data['related_entities'].append(dict(node))
        
        # Log successful export
        log_gdpr_action(
            citizen_id=citizen_id,
            action_type="GDPR_EXPORT",
            result="SUCCESS",
            ip_address=ip_address,
            details={
                'format': body.format,
                'entity_count': len(export_data['related_entities'])
            }
        )
        
        return {
            'status': 'success',
            'message': f'Data exported successfully ({len(export_data["related_entities"])} related entities)',
            'data': export_data,
            'download_url': f'/api/v1/citizen/gdpr-export/{citizen_id}/download',  # Future: generate actual file
            'expires_at': datetime.now().replace(hour=23, minute=59, second=59).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_gdpr_action(
            citizen_id=citizen_id,
            action_type="GDPR_EXPORT",
            result="FAILURE_ERROR",
            ip_address=ip_address,
            details={'error': str(e)}
        )
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.delete("/gdpr-erase")
async def gdpr_erase(request: Request, body: GDPRERequest, current_user: dict = Depends(get_current_user)):
    """
    GDPR Art. 17 - Right to Erasure ("Right to be Forgotten")
    Delete citizen account and all associated personal data
    
    Args:
        citizen_id: Citizen identifier
        reason: Legal basis for erasure
        anonymize_feedback: If True, anonymize feedback instead of deleting (preserve statistics)
    
    Returns:
        Erasure confirmation with certificate ID
    """
    citizen_id = body.citizen_id
    ip_address = request.client.host if request.client else "unknown"
    
    # RBAC check - citizen can only delete their own account (or admin)
    if current_user['role'] == 'citizen' and current_user['username'] != citizen_id:
        log_gdpr_action(
            citizen_id=citizen_id,
            action_type="GDPR_ERASURE",
            result="FAILURE_UNAUTHORIZED",
            ip_address=ip_address,
            details={'reason': 'Citizen attempted to delete another citizen\'s account'}
        )
        raise HTTPException(status_code=403, detail="Access denied: Can only delete own account")
    
    try:
        # Initialize GDPR erasure engine
        erasure_engine = GDPRDataErasure()
        
        if not erasure_engine.connect():
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        # Execute cascade delete with anonymization
        result = erasure_engine.execute_cascade_delete(
            citizen_id=citizen_id,
            reason=body.reason,
            operator=current_user['username'],
            anonymize_feedback=body.anonymize_feedback
        )
        
        erasure_engine.disconnect()
        
        if 'error' in result:
            log_gdpr_action(
                citizen_id=citizen_id,
                action_type="GDPR_ERASURE",
                result="FAILURE",
                ip_address=ip_address,
                details={'error': result['error']}
            )
            raise HTTPException(status_code=400, detail=result['error'])
        
        # Log successful erasure
        log_gdpr_action(
            citizen_id=citizen_id,
            action_type="GDPR_ERASURE",
            result="SUCCESS",
            ip_address=ip_address,
            details={
                'nodes_deleted': result.get('nodes_deleted', 0),
                'relationships_deleted': result.get('relationships_deleted', 0),
                'anonymize_feedback': body.anonymize_feedback
            }
        )
        
        return {
            'status': 'success',
            'message': 'Citizen data erased successfully',
            'erasure_id': result['erasure_id'],
            'certificate': result.get('certificate', {}),
            'nodes_deleted': result.get('nodes_deleted', 0),
            'relationships_deleted': result.get('relationships_deleted', 0),
            'legal_notice': 'This operation is irreversible. Data has been permanently deleted in compliance with RODO Art. 17.'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log_gdpr_action(
            citizen_id=citizen_id,
            action_type="GDPR_ERASURE",
            result="FAILURE_ERROR",
            ip_address=ip_address,
            details={'error': str(e)}
        )
        raise HTTPException(status_code=500, detail=f"Erasure failed: {str(e)}")


@router.get("/gdpr-status/{citizen_id}")
async def gdpr_status(citizen_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    """
    Check GDPR data status for a citizen
    
    Returns:
        Summary of citizen's data in the system
    """
    ip_address = request.client.host if request.client else "unknown"
    
    # RBAC check
    if current_user['role'] == 'citizen' and current_user['username'] != citizen_id:
        raise HTTPException(status_code=403, detail="Access denied: Can only view own data status")
    
    try:
        # Query for citizen and related data count
        query = """
        MATCH (c:Citizen {citizen_id: $citizen_id})
        OPTIONAL MATCH (c)-[r]-(related)
        RETURN c AS citizen, count(DISTINCT related) AS related_count
        """
        
        result = execute_cypher_query(query, {'citizen_id': citizen_id})
        
        if not result or not result.get('records') or not result['records'][0].get('citizen'):
            raise HTTPException(status_code=404, detail=f"Citizen {citizen_id} not found")
        
        record = result['records'][0]
        citizen_data = dict(record['citizen'])
        related_count = record['related_count']
        
        # Remove sensitive fields from summary
        safe_summary = {
            'citizen_id': citizen_data.get('citizen_id'),
            'account_created': citizen_data.get('created_at'),
            'last_updated': citizen_data.get('updated_at'),
            'related_entities_count': related_count,
            'data_categories': ['personal_info', 'feedback', 'interactions']
        }
        
        return {
            'status': 'active',
            'summary': safe_summary,
            'rights': {
                'export_available': True,
                'erasure_available': True,
                'legal_basis': 'RODO Art. 15 & 17'
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")
