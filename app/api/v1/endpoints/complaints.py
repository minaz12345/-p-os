"""
Citizen Complaint/Suggestion Submission Endpoint
Integrates with CitizenFeedback nodes in Neo4j
"""

from fastapi import APIRouter, Request, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import sys
import hashlib
import secrets
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.db.neo4j_connection import execute_cypher_query
except ImportError as e:
    print(f"⚠️  Warning: Could not import Neo4j modules: {e}")

from app.api.v1.middleware.rbac_middleware import get_current_user
from app.api.v1.middleware.rate_limiter import rate_limit_check
from app.api.v1.utils.audit_logger import log_complaint_submission

router = APIRouter()


# Request models
class ComplaintSubmission(BaseModel):
    category: str  # complaint or suggestion
    title: str
    description: str
    location_ref: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    priority: str = "medium"  # low, medium, high, urgent


@router.post("/complaints")
async def submit_complaint(request: Request, body: ComplaintSubmission, current_user: dict = Depends(get_current_user)):
    """
    Submit a citizen complaint or suggestion
    Creates a CitizenFeedback node in Neo4j
    
    Args:
        category: 'complaint' or 'suggestion'
        title: Short description
        description: Detailed explanation
        location_ref: Reference to Location node (optional)
        latitude/longitude: GPS coordinates (optional)
        priority: low/medium/high/urgent
    
    Returns:
        Confirmation with complaint ID and tracking URL
    """
    # Apply rate limiting
    await rate_limit_check(request)
    
    citizen_id = current_user['username']
    ip_address = request.client.host if request.client else "unknown"
    
    # Validate category
    if body.category not in ['complaint', 'suggestion']:
        raise HTTPException(status_code=400, detail="Category must be 'complaint' or 'suggestion'")
    
    # Validate priority
    valid_priorities = ['low', 'medium', 'high', 'urgent']
    if body.priority not in valid_priorities:
        raise HTTPException(status_code=400, detail=f"Priority must be one of: {', '.join(valid_priorities)}")
    
    try:
        # Generate unique feedback ID
        feedback_id = f"FB-{datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
        
        # Create citizen hash (anonymized identifier)
        citizen_hash = hashlib.sha256(citizen_id.encode()).hexdigest()
        
        # Build Cypher query to create CitizenFeedback node
        query = """
        CREATE (cf:CitizenFeedback {
            feedback_id: $feedback_id,
            citizen_hash: $citizen_hash,
            category: $category,
            title: $title,
            description: $description,
            location_ref: $location_ref,
            status: 'new',
            priority: $priority,
            created_at: datetime(),
            updated_at: datetime(),
            resolution_note: '',
            classification_tier: 'INTERNAL',
            submitted_ip: $ip_address
        })
        RETURN cf.feedback_id AS feedback_id, cf.created_at AS created_at
        """
        
        result = execute_cypher_query(query, {
            'feedback_id': feedback_id,
            'citizen_hash': citizen_hash,
            'category': body.category,
            'title': body.title,
            'description': body.description,
            'location_ref': body.location_ref or '',
            'priority': body.priority,
            'ip_address': ip_address
        })
        
        if not result or not result.get('records'):
            raise HTTPException(status_code=500, detail="Failed to create complaint")
        
        record = result['records'][0]
        
        # If location coordinates provided, create Location node if doesn't exist
        if body.latitude and body.longitude:
            location_id = f"Location_{body.latitude}_{body.longitude}".replace('.', '_')
            
            location_query = """
            MERGE (l:Location {location_id: $location_id})
            ON CREATE SET
                l.name = $name,
                l.latitude = $latitude,
                l.longitude = $longitude,
                l.type = 'citizen_reported',
                l.created_at = datetime(),
                l.classification_tier = 'PUBLIC'
            WITH l
            MATCH (cf:CitizenFeedback {feedback_id: $feedback_id})
            MERGE (cf)-[:LOCATED_AT]->(l)
            """
            
            execute_cypher_query(location_query, {
                'location_id': location_id,
                'name': f"Location ({body.latitude}, {body.longitude})",
                'latitude': body.latitude,
                'longitude': body.longitude,
                'feedback_id': feedback_id
            })
        
        # Log submission to audit trail
        log_complaint_submission(
            citizen_id=citizen_id,
            complaint_id=feedback_id,
            category=body.category,
            ip_address=ip_address
        )
        
        return {
            'status': 'submitted',
            'message': f'{body.category.capitalize()} submitted successfully',
            'feedback_id': feedback_id,
            'tracking_url': f'/api/v1/citizen/complaints/{feedback_id}/status',
            'estimated_review': '3-5 business days',
            'created_at': str(record['created_at']),
            'note': 'You will receive updates on this submission via your citizen portal'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Submission failed: {str(e)}")


@router.get("/complaints/{feedback_id}/status")
async def check_complaint_status(feedback_id: str, request: Request, current_user: dict = Depends(get_current_user)):
    """
    Check status of a submitted complaint/suggestion
    
    Args:
        feedback_id: Feedback identifier
    
    Returns:
        Current status and any resolution notes
    """
    # Apply rate limiting
    await rate_limit_check(request)
    
    citizen_id = current_user['username']
    citizen_hash = hashlib.sha256(citizen_id.encode()).hexdigest()
    
    try:
        # Query for feedback status
        query = """
        MATCH (cf:CitizenFeedback {feedback_id: $feedback_id})
        WHERE cf.citizen_hash = $citizen_hash
        RETURN cf
        """
        
        result = execute_cypher_query(query, {
            'feedback_id': feedback_id,
            'citizen_hash': citizen_hash
        })
        
        if not result or not result.get('records'):
            raise HTTPException(status_code=404, detail="Complaint not found or access denied")
        
        record = result['records'][0]
        feedback_data = dict(record['cf'])
        
        return {
            'status': 'success',
            'feedback': {
                'feedback_id': feedback_data.get('feedback_id'),
                'category': feedback_data.get('category'),
                'title': feedback_data.get('title'),
                'status': feedback_data.get('status'),
                'priority': feedback_data.get('priority'),
                'created_at': str(feedback_data.get('created_at')),
                'updated_at': str(feedback_data.get('updated_at')),
                'resolution_note': feedback_data.get('resolution_note', ''),
                'tracking_info': {
                    'new': 'Submitted - awaiting review',
                    'in_review': 'Under review by municipal staff',
                    'resolved': 'Issue resolved',
                    'rejected': 'Cannot be actioned (see resolution note)'
                }.get(feedback_data.get('status'), 'Unknown status')
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.get("/complaints/my-submissions")
async def get_my_submissions(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Get all submissions by the current citizen
    
    Returns:
        List of all complaints/suggestions submitted by user
    """
    # Apply rate limiting
    await rate_limit_check(request)
    
    citizen_id = current_user['username']
    citizen_hash = hashlib.sha256(citizen_id.encode()).hexdigest()
    
    try:
        query = """
        MATCH (cf:CitizenFeedback)
        WHERE cf.citizen_hash = $citizen_hash
        RETURN cf
        ORDER BY cf.created_at DESC
        """
        
        result = execute_cypher_query(query, {'citizen_hash': citizen_hash})
        
        submissions = []
        if result and result.get('records'):
            for record in result['records']:
                feedback_data = dict(record['cf'])
                submissions.append({
                    'feedback_id': feedback_data.get('feedback_id'),
                    'category': feedback_data.get('category'),
                    'title': feedback_data.get('title'),
                    'status': feedback_data.get('status'),
                    'priority': feedback_data.get('priority'),
                    'created_at': str(feedback_data.get('created_at')),
                    'resolution_note': feedback_data.get('resolution_note', '')
                })
        
        return {
            'status': 'success',
            'total_submissions': len(submissions),
            'submissions': submissions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve submissions: {str(e)}")
