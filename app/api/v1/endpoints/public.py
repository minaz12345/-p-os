"""
Public Endpoints - No authentication required
Transparency Dashboard and Event Calendar
"""

from fastapi import APIRouter, Request, HTTPException
from typing import Optional
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from core.db.neo4j_connection import get_neo4j_driver
except ImportError as e:
    print(f"⚠️  Warning: Could not import Neo4j modules: {e}")

from app.api.v1.middleware.rate_limiter import rate_limit_check

router = APIRouter()


@router.get("/transparency")
async def transparency_dashboard(request: Request):
    """
    Public Transparency Dashboard
    Displays aggregated municipal statistics (PUBLIC classification only)
    
    Query Parameters:
        category: Filter by category (budget, projects, complaints, all)
        year: Filter by year (default: current year)
    
    Returns:
        Aggregated municipal statistics
    """
    # Apply rate limiting
    await rate_limit_check(request)
    
    try:
        # Use singleton driver pattern for optimal performance (Day 1 fix)
        driver = get_neo4j_driver()
        
        # Optimized query using specific labels to leverage per-label classification_tier indexes
        # This avoids full graph scan by using indexed label-specific queries
        with driver.session() as session:
            result = session.run("""
                WITH
                    count { MATCH (event:Event) WHERE event.classification_tier = 'PUBLIC' } AS total_events,
                    count { MATCH (location:Location) WHERE location.classification_tier = 'PUBLIC' } AS total_locations,
                    count { MATCH (institution:Institution) WHERE institution.classification_tier = 'PUBLIC' } AS total_institutions,
                    count { MATCH (feedback:CitizenFeedback) WHERE feedback.classification_tier = 'PUBLIC' AND feedback.status IN ['resolved', 'in_review'] } AS public_feedback_count
                RETURN
                    (total_events + total_locations + total_institutions + public_feedback_count) AS total_nodes,
                    total_events,
                    total_locations,
                    total_institutions,
                    public_feedback_count
            """).single()
            
            total_nodes = result['total_nodes'] if result else 0
            total_events = result['total_events'] if result else 0
            total_locations = result['total_locations'] if result else 0
            total_institutions = result['total_institutions'] if result else 0
            public_feedback_count = result['public_feedback_count'] if result else 0
        
        dashboard_data = {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'municipal_overview': {
                'total_public_records': total_nodes,
                'active_events': total_events,
                'locations_mapped': total_locations,
                'public_institutions': total_institutions,
                'citizen_feedback_resolved': public_feedback_count
            },
            'transparency_metrics': {
                'data_classification': 'PUBLIC only',
                'last_updated': datetime.now().isoformat(),
                'update_frequency': 'Real-time',
                'compliance': 'RODO compliant - no personal data exposed'
            }
        }
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard data retrieval failed: {str(e)}")


@router.get("/events")
async def event_calendar(
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    page: int = 1,
    per_page: int = 20
):
    """
    Public Event Calendar
    Browse upcoming municipal events
    
    Query Parameters:
        start_date: Filter events from date (YYYY-MM-DD)
        end_date: Filter events until date (YYYY-MM-DD)
        category: Filter by category (cultural, administrative, community, etc.)
        page: Page number for pagination
        per_page: Items per page (default: 20)
    
    Returns:
        List of public events with pagination
    """
    # Apply rate limiting
    await rate_limit_check(request)
    
    try:
        # Build Cypher query with filters
        where_clauses = ["e.classification_tier = 'PUBLIC'"]
        params = {}
        
        if start_date:
            where_clauses.append("e.date >= date($start_date)")
            params['start_date'] = start_date
        
        if end_date:
            where_clauses.append("e.date <= date($end_date)")
            params['end_date'] = end_date
        
        if category:
            where_clauses.append("e.category = $category")
            params['category'] = category
        
        where_clause = " AND ".join(where_clauses)
        
        # Count total events
        count_query = f"""
        MATCH (e:Event)
        WHERE {where_clause}
        RETURN count(e) AS total
        """
        
        count_result = execute_cypher_query(count_query, params)
        total_events = count_result[0]['total'] if count_result and len(count_result) > 0 else 0
        
        # Get paginated events
        offset = (page - 1) * per_page
        query = f"""
        MATCH (e:Event)
        WHERE {where_clause}
        RETURN e
        ORDER BY e.date ASC
        SKIP $offset LIMIT $limit
        """
        
        params['offset'] = offset
        params['limit'] = per_page
        
        result = execute_cypher_query(query, params)
        
        events = []
        if result and len(result) > 0:
            for record in result:
                event_node = dict(record['e']) if hasattr(record, 'keys') else record.get('e', {})
                events.append({
                    'event_id': event_node.get('event_id'),
                    'title': event_node.get('title'),
                    'date': str(event_node.get('date')),
                    'time': event_node.get('time', 'TBD'),
                    'location': event_node.get('location', 'TBD'),
                    'category': event_node.get('category', 'general'),
                    'description': event_node.get('description', ''),
                    'registration_required': event_node.get('registration_required', False)
                })
        
        return {
            'status': 'success',
            'events': events,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_events': total_events,
                'total_pages': (total_events + per_page - 1) // per_page
            },
            'filters_applied': {
                'start_date': start_date,
                'end_date': end_date,
                'category': category
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Event calendar retrieval failed: {str(e)}")


@router.get("/statistics")
async def municipal_statistics(request: Request):
    """
    Additional Municipal Statistics
    Provides detailed breakdowns for transparency
    
    Returns:
        Detailed statistics by category
    """
    # Apply rate limiting
    await rate_limit_check(request)
    
    try:
        # Budget statistics (if available)
        budget_query = """
        MATCH (b:Budget)
        WHERE b.classification_tier = 'PUBLIC'
        RETURN 
            sum(b.allocated) AS total_allocated,
            sum(b.spent) AS total_spent,
            count(b) AS budget_items
        """
        
        budget_result = execute_cypher_query(budget_query)
        budget_data = None
        
        if budget_result and len(budget_result) > 0:
            record = budget_result[0]
            if record.get('total_allocated'):
                budget_data = {
                    'total_allocated': record['total_allocated'],
                    'total_spent': record['total_spent'],
                    'utilization_rate': round((record['total_spent'] / record['total_allocated']) * 100, 2) if record['total_allocated'] > 0 else 0,
                    'budget_items': record['budget_items']
                }
        
        # Complaint resolution statistics
        complaint_query = """
        MATCH (cf:CitizenFeedback)
        WHERE cf.classification_tier IN ['PUBLIC', 'INTERNAL']
          AND cf.category = 'complaint'
        RETURN 
            count(cf) AS total_complaints,
            count(CASE WHEN cf.status = 'resolved' THEN 1 END) AS resolved,
            count(CASE WHEN cf.status = 'in_review' THEN 1 END) AS in_review,
            count(CASE WHEN cf.status = 'new' THEN 1 END) AS new
        """
        
        complaint_result = execute_cypher_query(complaint_query)
        complaint_stats = None
        
        if complaint_result and len(complaint_result) > 0:
            record = complaint_result[0]
            complaint_stats = {
                'total_complaints': record.get('total_complaints', 0),
                'resolved': record.get('resolved', 0),
                'in_review': record.get('in_review', 0),
                'new': record.get('new', 0),
                'resolution_rate': round((record.get('resolved', 0) / record.get('total_complaints', 1)) * 100, 2)
            }
        
        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'budget': budget_data,
            'complaints': complaint_stats,
            'note': 'All data is anonymized and aggregated for privacy compliance'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Statistics retrieval failed: {str(e)}")
