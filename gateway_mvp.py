# D:\pos7\gateway_mvp.py
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
import os, psycopg2, uuid, json, hashlib, secrets, time
from dotenv import load_dotenv

load_dotenv("D:/pos7/.env.db")

W11_FLAGS_DIR = Path("D:/pos7/flags")

def check_w11() -> list:
    if not W11_FLAGS_DIR.exists():
        return []
    return [f.name for f in W11_FLAGS_DIR.glob("*.flag")]

def get_db():
    return psycopg2.connect(
        host=os.getenv("POSTGRESQL_HOST", "localhost"),
        port=os.getenv("POSTGRESQL_PORT", "5432"),
        dbname=os.getenv("POSTGRESQL_DB", "pos_operational"),
        user=os.getenv("POSTGRESQL_USER", "pos_admin"),
        password=os.getenv("POSTGRESQL_PASSWORD"),
    )

# ============================================================================
# EVENT BUS - Immutable Event Log with Hash Chain
# ============================================================================

def emit_event(action: str, actor_id: str, payload: dict, municipality: str = "milejczyce", risk_score: float = 0.0) -> str:
    """
    Emit immutable event to PostgreSQL events table with hash chain integrity.
    
    Args:
        action: Event type (e.g., 'GDPR_ERASURE_REQUEST', 'CITIZEN_COMPLAINT_SUBMITTED')
        actor_id: Actor identifier (will be converted to UUIDv5)
        payload: Event data as dictionary (stored as JSONB)
        municipality: Municipality name (default: 'milejczyce')
        risk_score: Risk assessment score (0.0-100.0)
    
    Returns:
        event_id (UUID string)
    """
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get the most recent event's hash for this municipality
        cur.execute("""
            SELECT hash FROM events 
            WHERE municipality = %s 
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (municipality,))
        row = cur.fetchone()
        previous_hash = row[0] if row else None
        
        # Generate event ID and actor UUID
        event_id = str(uuid.uuid4())
        actor_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, actor_id)
        
        # Build deterministic record for hashing
        record_json = json.dumps({
            'actor_id': str(actor_uuid),
            'action': action,
            'payload': payload
        }, sort_keys=True)
        
        # Compute SHA-256 hash: hash(record_json + previous_hash)
        raw_input = record_json + (previous_hash or '')
        computed_hash = hashlib.sha256(raw_input.encode()).hexdigest()
        
        # Insert event (triggers will validate hash chain)
        cur.execute("""
            INSERT INTO events (event_id, actor_id, action, payload, previous_hash, hash, municipality, risk_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING event_id
        """, (
            event_id,
            str(actor_uuid),
            action,
            json.dumps(payload),
            previous_hash,
            computed_hash,
            municipality,
            risk_score
        ))
        
        result = cur.fetchone()
        conn.commit()
        
        print(f"✅ Event emitted: {action} (ID: {result[0]})")
        return str(result[0])
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Event emission failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()

# ============================================================================
# RATE LIMITING - In-Memory Sliding Window
# ============================================================================

# Rate limit storage: {ip: [(timestamp, endpoint_category)]}
rate_limit_store = {}

RATE_LIMIT_CONFIG = {
    'public': {'max_requests': 40, 'window_seconds': 60},        # 40 req/min
    'gdpr': {'max_requests': 5, 'window_seconds': 3600},          # 5 req/hr
    'complaints': {'max_requests': 10, 'window_seconds': 3600},   # 10 req/hr
}

def get_endpoint_category(path: str) -> str:
    """Determine rate limit category based on endpoint path."""
    if '/gdpr/erasure' in path:
        return 'gdpr'
    elif '/api/v1/citizen/complaints' in path:
        return 'complaints'
    else:
        return 'public'  # /health, /gdpr/status, etc.

def check_rate_limit(client_ip: str, endpoint_category: str) -> dict:
    """
    Check if request exceeds rate limit using sliding window.
    
    Args:
        client_ip: Client IP address
        endpoint_category: Rate limit category (public/gdpr/complaints)
    
    Returns:
        dict with 'allowed', 'remaining', 'retry_after' keys
    """
    config = RATE_LIMIT_CONFIG.get(endpoint_category, RATE_LIMIT_CONFIG['public'])
    max_requests = config['max_requests']
    window_seconds = config['window_seconds']
    
    current_time = time.time()
    window_start = current_time - window_seconds
    
    # Initialize or clean old entries for this IP
    if client_ip not in rate_limit_store:
        rate_limit_store[client_ip] = []
    
    # Remove expired entries outside the window
    rate_limit_store[client_ip] = [
        (ts, cat) for ts, cat in rate_limit_store[client_ip]
        if ts > window_start
    ]
    
    # Count requests in current window for this category
    recent_requests = [
        ts for ts, cat in rate_limit_store[client_ip]
        if cat == endpoint_category
    ]
    
    request_count = len(recent_requests)
    remaining = max(0, max_requests - request_count)
    
    if request_count >= max_requests:
        # Rate limit exceeded
        oldest_request = min(recent_requests) if recent_requests else current_time
        retry_after = int(oldest_request + window_seconds - current_time) + 1
        
        return {
            'allowed': False,
            'remaining': 0,
            'retry_after': max(1, retry_after),
            'limit': max_requests,
            'window': window_seconds
        }
    
    # Request allowed - record it
    rate_limit_store[client_ip].append((current_time, endpoint_category))
    
    return {
        'allowed': True,
        'remaining': remaining - 1,
        'retry_after': 0,
        'limit': max_requests,
        'window': window_seconds
    }

app = FastAPI(title="P-OS Gateway", version="7.5-mvp")

@app.get("/health")
def health(request: Request):
    # Rate limiting for public endpoints
    client_ip = request.client.host if request.client else "unknown"
    rate_result = check_rate_limit(client_ip, 'public')
    
    flags = check_w11()
    state = "DEGRADED" if flags else "HEALTHY"
    db_ok = False
    try:
        conn = get_db()
        conn.close()
        db_ok = True
    except Exception as e:
        print(f"DB Connection Error: {e}")
        pass
    
    response = {
        "status": state,
        "service": "gdpr-portal-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "w11_flags": flags,
        "database": "ok" if db_ok else "error"
    }
    
    # Add rate limit headers if available
    if not rate_result['allowed']:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {rate_result['limit']} requests per minute",
            headers={
                "Retry-After": str(rate_result['retry_after']),
                "X-RateLimit-Limit": str(rate_result['limit']),
                "X-RateLimit-Remaining": "0"
            }
        )
    
    return response

class ErasureRequest(BaseModel):
    citizen_id: str
    reason: str  # Must be one of: USER_REQUEST, RIGHT_TO_BE_FORGOTTEN, DATA_RETENTION_EXPIRY, LEGAL_ORDER
    operator_id: str = "system_operator"

@app.post("/gdpr/erasure/request")
def request_erasure(request: Request, req: ErasureRequest):
    # 0. Rate Limiting Check
    client_ip = request.client.host if request.client else "unknown"
    rate_result = check_rate_limit(client_ip, 'gdpr')
    
    if not rate_result['allowed']:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {rate_result['limit']} requests per hour",
            headers={
                "Retry-After": str(rate_result['retry_after']),
                "X-RateLimit-Limit": str(rate_result['limit']),
                "X-RateLimit-Remaining": "0"
            }
        )
    
    # 1. W11 Safety Gate
    flags = check_w11()
    if flags:
        raise HTTPException(status_code=503, detail=f"System DEGRADED. Active W11 flags: {flags}")
    
    # 2. Validate reason against production constraints
    allowed_reasons = ["USER_REQUEST", "RIGHT_TO_BE_FORGOTTEN", 
                       "DATA_RETENTION_EXPIRY", "LEGAL_ORDER"]
    if req.reason not in allowed_reasons:
        raise HTTPException(status_code=400, 
            detail=f"Invalid reason. Allowed values: {allowed_reasons}")
    
    # 3. Generate request_id (UUID v4)
    request_id = uuid.uuid4()
    
    # 4. Calculate 72h deadline per GDPR §D5
    deadline = datetime.now(timezone.utc) + timedelta(hours=72)
    
    # 5. Convert citizen_id and operator_id to UUIDs
    # If citizen_id is already a UUID format, use it; otherwise generate UUIDv5 from DNS namespace
    try:
        user_uuid = uuid.UUID(req.citizen_id) if req.citizen_id.count('-') == 4 else uuid.uuid5(uuid.NAMESPACE_DNS, req.citizen_id)
    except ValueError:
        user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, req.citizen_id)
    
    operator_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, req.operator_id)
    
    # 6. Prepare audit log (written AFTER DB commit to ensure atomic truth)
    audit_log = {
        "event": "GDPR_ERASURE_REQUEST",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": str(request_id),
        "user_id": str(user_uuid),
        "operator_id": str(operator_uuid),
        "reason": req.reason,
        "deadline": deadline.isoformat(),
        "status": "PENDING"
    }
    
    log_dir = Path("D:/pos7/logs/gdpr_requests")
    log_dir.mkdir(exist_ok=True)
    
    # 7. Persist to Production PostgreSQL Table FIRST (primary truth)
    db_status = "FAILED"
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO gdpr_erasure_requests 
            (request_id, user_id, requested_by, reason, status, deadline)
            VALUES (%s, %s, %s, %s, 'PENDING', %s)
        """, (
            str(request_id),
            str(user_uuid),
            str(operator_uuid),
            req.reason,
            deadline
        ))
        conn.commit()
        cur.close()
        conn.close()
        db_status = "PERSISTED"
    except Exception as e:
        print(f"Database persistence failed: {e}")
        # DB failed - request never entered reality, no audit trail created
        raise HTTPException(status_code=503, detail=f"Service unavailable: database error")
    
    # 8. ONLY write audit log AFTER successful DB commit (atomic truth boundary)
    try:
        with open(log_dir / f"{request_id}.json", "w") as f:
            json.dump(audit_log, f, indent=2)
    except Exception as e:
        # Audit write failed but DB succeeded - log warning but don't fail request
        # This is acceptable: primary truth (DB) exists, audit is secondary
        print(f"WARNING: Audit log write failed: {e}")
        # Request still valid since DB has the record
    
    # 8. Emit immutable event to hash chain
    try:
        emit_event(
            action="GDPR_ERASURE_REQUEST",
            actor_id=req.operator_id,
            payload={
                "request_id": str(request_id),
                "user_id": str(user_uuid),
                "reason": req.reason,
                "deadline": deadline.isoformat(),
                "status": "PENDING"
            },
            risk_score=25.0  # Medium risk - data deletion request
        )
    except Exception as e:
        print(f"⚠️  Event emission failed (non-critical): {e}")
        # Don't fail the request if event logging fails
    
    return {
        "status": "accepted",
        "request_id": str(request_id),
        "deadline": deadline.isoformat(),
        "message": "Erasure request registered. Deadline: 72h.",
        "persistence": db_status
    }

@app.get("/gdpr/status")
def gdpr_status():
    flags = check_w11()
    return {"w11_active": bool(flags), "flags": flags}

# ============================================================================
# COMPLAINTS ENDPOINT
# ============================================================================

class ComplaintSubmission(BaseModel):
    category: str  # 'complaint' or 'suggestion'
    title: str
    description: str
    citizen_id: str
    priority: str = "medium"  # low, medium, high, urgent
    location_ref: Optional[str] = None

@app.post("/api/v1/citizen/complaints")
def submit_complaint(request: Request, req: ComplaintSubmission):
    """
    Submit a citizen complaint or suggestion
    Stores in PostgreSQL citizen_feedback table
    
    Returns:
        Confirmation with complaint ID and tracking info
    """
    # 0. Rate Limiting Check
    client_ip = request.client.host if request.client else "unknown"
    rate_result = check_rate_limit(client_ip, 'complaints')
    
    if not rate_result['allowed']:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {rate_result['limit']} requests per hour",
            headers={
                "Retry-After": str(rate_result['retry_after']),
                "X-RateLimit-Limit": str(rate_result['limit']),
                "X-RateLimit-Remaining": "0"
            }
        )
    
    # 1. W11 Safety Gate
    flags = check_w11()
    if flags:
        raise HTTPException(status_code=503, detail=f"System DEGRADED. Active W11 flags: {flags}")
    
    # 2. Validate inputs
    if req.category not in ['complaint', 'suggestion']:
        raise HTTPException(status_code=400, detail="Category must be 'complaint' or 'suggestion'")
    
    valid_priorities = ['low', 'medium', 'high', 'urgent']
    if req.priority not in valid_priorities:
        raise HTTPException(status_code=400, detail=f"Priority must be one of: {', '.join(valid_priorities)}")
    
    # 3. Generate complaint ID
    from datetime import datetime as dt
    import secrets
    feedback_id = f"FB-{dt.now().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
    
    # 4. Calculate timestamps
    created_at = datetime.now(timezone.utc)
    
    # 5. Persist to PostgreSQL
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO citizen_feedback 
            (feedback_id, citizen_id, category, title, description, priority, 
             status, location_ref, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, 'new', %s, %s, %s)
            RETURNING feedback_id, created_at
        """, (
            feedback_id,
            req.citizen_id,
            req.category,
            req.title,
            req.description,
            req.priority,
            req.location_ref,
            created_at,
            created_at
        ))
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        db_status = "PERSISTED"
    except Exception as e:
        print(f"Database persistence failed: {e}")
        raise HTTPException(status_code=500, detail=f"DB error: {str(e)}")
    
    # 6. Log to audit trail (file-based)
    audit_log = {
        "event": "COMPLAINT_SUBMITTED",
        "timestamp": created_at.isoformat(),
        "feedback_id": feedback_id,
        "citizen_id": req.citizen_id,
        "category": req.category,
        "priority": req.priority,
    }
    
    log_dir = Path("D:/pos7/logs/complaints")
    log_dir.mkdir(exist_ok=True)
    
    with open(log_dir / f"{feedback_id}.json", "w") as f:
        json.dump(audit_log, f, indent=2)
    
    # 7. Emit immutable event to hash chain
    try:
        emit_event(
            action="CITIZEN_COMPLAINT_SUBMITTED",
            actor_id=req.citizen_id,
            payload={
                "feedback_id": feedback_id,
                "category": req.category,
                "title": req.title,
                "priority": req.priority,
                "location_ref": req.location_ref
            },
            risk_score=5.0  # Low risk - citizen feedback
        )
    except Exception as e:
        print(f"⚠️  Event emission failed (non-critical): {e}")
        # Don't fail the request if event logging fails
    
    return {
        "status": "submitted",
        "message": f"{req.category.capitalize()} submitted successfully",
        "feedback_id": feedback_id,
        "tracking_url": f"/api/v1/citizen/complaints/{feedback_id}/status",
        "estimated_review": "3-5 business days",
        "created_at": created_at.isoformat(),
        "persistence": db_status
    }

@app.get("/api/v1/citizen/complaints/{feedback_id}/status")
def check_complaint_status(feedback_id: str):
    """
    Check status of a submitted complaint/suggestion
    
    Returns:
        Current status and resolution notes
    """
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT feedback_id, category, title, status, priority, 
                   created_at, updated_at, resolution_note
            FROM citizen_feedback
            WHERE feedback_id = %s
        """, (feedback_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Complaint not found")
        
        feedback_data = {
            'feedback_id': result[0],
            'category': result[1],
            'title': result[2],
            'status': result[3],
            'priority': result[4],
            'created_at': result[5].isoformat() if result[5] else None,
            'updated_at': result[6].isoformat() if result[6] else None,
            'resolution_note': result[7] or ''
        }
        
        status_messages = {
            'new': 'Submitted - awaiting review',
            'in_review': 'Under review by municipal staff',
            'resolved': 'Issue resolved',
            'rejected': 'Cannot be actioned (see resolution note)'
        }
        
        return {
            'status': 'success',
            'feedback': {
                **feedback_data,
                'tracking_info': status_messages.get(result[3], 'Unknown status')
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")
