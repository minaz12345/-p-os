"""
P-OS Event Bus & Constraint Engine API Endpoints
Phase E Block 4: Sovereign Audit Trail Integration

Provides REST API for:
- Creating immutable events
- Evaluating policy decisions
- Verifying hash chain integrity
- Retrieving user risk profiles
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import uuid
import os

from core.engine.sovereign_event_bus import SovereignEventBus
from core.engine.constraint_engine import ConstraintEngine, ConstraintViolation, register_default_constraints

router = APIRouter(
    prefix="/events",
    tags=["Sovereign Event Bus"],
    responses={404: {"description": "Not found"}}
)


# Dependency injection for event bus
def get_event_bus() -> SovereignEventBus:
    """Create and yield event bus instance"""
    postgres_uri = os.getenv("POSTGRESQL_URI")
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687").replace("bolt+ssc://", "bolt://")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    municipality = os.getenv("MUNICIPALITY", "milejczyce")
    
    if not postgres_uri or not neo4j_password:
        raise HTTPException(
            status_code=500,
            detail="Database configuration missing. Check environment variables."
        )
    
    bus = SovereignEventBus(
        postgres_uri=postgres_uri,
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password,
        municipality=municipality
    )
    
    try:
        yield bus
    finally:
        bus.close()


def get_constraint_engine(bus: SovereignEventBus = Depends(get_event_bus)) -> ConstraintEngine:
    """Create constraint engine with default policies"""
    engine = ConstraintEngine(bus)
    register_default_constraints(engine)
    return engine


# Request/Response Models
class CreateEventRequest(BaseModel):
    actor_id: str = Field(..., description="UUID of the user/system triggering the event")
    action: str = Field(..., description="Action type (e.g., BUDGET_ALLOCATION)")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event-specific data")
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Risk score (0.00-1.00)")


class CreateEventResponse(BaseModel):
    event_id: str
    hash: str
    timestamp: str
    status: str = "created"


class EvaluatePolicyRequest(BaseModel):
    actor_id: str = Field(..., description="UUID of the user/system")
    action: str = Field(..., description="Action to evaluate")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")


class PolicyDecisionResponse(BaseModel):
    decision: str  # ALLOW, REJECT, REQUIRE_APPROVAL
    reason: str
    constraint_violated: Optional[str] = None
    risk_score: float
    event_hash: str


class EnforcePolicyRequest(BaseModel):
    actor_id: str
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class EnforcePolicyResponse(BaseModel):
    allowed: bool
    event_hash: str
    risk_score: float


# API Endpoints

@router.post("/create", response_model=CreateEventResponse)
async def create_event(
    request: CreateEventRequest,
    bus: SovereignEventBus = Depends(get_event_bus)
):
    """
    Create an immutable event with hash chain enforcement.
    
    This endpoint:
    1. Computes deterministic SHA-256 hash
    2. Validates hash chain continuity
    3. Inserts into PostgreSQL (append-only)
    4. Syncs to Neo4j graph
    5. Returns event hash for verification
    
    **Example:**
    ```json
    {
        "actor_id": "user-uuid-here",
        "action": "BUDGET_ALLOCATION",
        "payload": {"amount": 500000, "recipient": "Infrastructure Dept"},
        "risk_score": 0.3
    }
    ```
    """
    try:
        hash_value = bus.create_event(
            actor_id=request.actor_id,
            action=request.action,
            payload=request.payload,
            risk_score=request.risk_score
        )
        
        # Get event details (last inserted)
        from sqlalchemy import text
        with bus.pg_engine.connect() as conn:
            result = conn.execute(
                text("SELECT event_id, timestamp FROM events WHERE hash = :hash LIMIT 1"),
                {"hash": hash_value}
            ).fetchone()
        
        return CreateEventResponse(
            event_id=str(result[0]),
            hash=hash_value,
            timestamp=result[1].isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Event creation failed: {str(e)}")


@router.post("/evaluate-policy", response_model=PolicyDecisionResponse)
async def evaluate_policy(
    request: EvaluatePolicyRequest,
    engine: ConstraintEngine = Depends(get_constraint_engine)
):
    """
    Evaluate policy constraints without enforcing (read-only).
    
    Returns ALLOW/REJECT decision but does NOT block execution.
    All decisions are logged as immutable POLICY_DECISION events.
    
    **Use case:** Preview decision before taking action.
    """
    try:
        decision = engine.evaluate(
            actor_id=request.actor_id,
            action=request.action,
            payload=request.payload
        )
        
        return PolicyDecisionResponse(
            decision=decision.decision.value,
            reason=decision.reason,
            constraint_violated=decision.constraint_violated,
            risk_score=decision.risk_score,
            event_hash="logged_as_event"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy evaluation failed: {str(e)}")


@router.post("/enforce-policy", response_model=EnforcePolicyResponse)
async def enforce_policy(
    request: EnforcePolicyRequest,
    engine: ConstraintEngine = Depends(get_constraint_engine)
):
    """
    Enforce policy constraints (fail-fast).
    
    If policy is violated:
    - Raises HTTP 403 Forbidden
    - Rejection is logged as immutable event
    - Action is blocked
    
    If policy allows:
    - Returns success with event hash
    - Decision is logged for audit trail
    """
    try:
        allowed = engine.enforce(
            actor_id=request.actor_id,
            action=request.action,
            payload=request.payload
        )
        
        # Get last event hash (the decision log)
        last_hash = engine.event_bus.get_last_hash()
        
        return EnforcePolicyResponse(
            allowed=allowed,
            event_hash=last_hash or "unknown",
            risk_score=0.0
        )
        
    except ConstraintViolation as e:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Policy violation",
                "constraint": e.constraint_name,
                "message": e.message,
                "risk_score": e.risk_score
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy enforcement failed: {str(e)}")


@router.get("/verify-chain")
async def verify_hash_chain(bus: SovereignEventBus = Depends(get_event_bus)):
    """
    Verify integrity of the entire hash chain.
    
    Returns:
    - valid: True if chain is intact, False if tampered
    - total_events: Number of events in chain
    - message: Human-readable status
    
    **Use case:** Periodic integrity checks, incident response.
    """
    try:
        is_valid = bus.verify_chain_integrity()
        
        # Count events
        from sqlalchemy import text
        with bus.pg_engine.connect() as conn:
            count_result = conn.execute(
                text("SELECT COUNT(*) FROM events WHERE municipality = :municipality"),
                {"municipality": bus.municipality}
            ).fetchone()
        
        return {
            "valid": is_valid,
            "total_events": count_result[0],
            "municipality": bus.municipality,
            "message": "Hash chain is INTACT" if is_valid else "HASH CHAIN BROKEN - TAMPERING DETECTED!"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chain verification failed: {str(e)}")


@router.get("/risk-profile/{user_id}")
async def get_risk_profile(
    user_id: str,
    engine: ConstraintEngine = Depends(get_constraint_engine)
):
    """
    Get aggregated risk profile for a user.
    
    Returns:
    - current_risk_score: Current risk level (0.00-1.00)
    - max_score: Historical maximum
    - last_updated: Timestamp of last update
    
    **Use case:** Monitor high-risk users, trigger alerts.
    """
    try:
        profile = engine.get_user_risk_profile(user_id)
        
        return {
            "user_id": user_id,
            **profile
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk profile retrieval failed: {str(e)}")


@router.get("/summary")
async def get_event_summary(bus: SovereignEventBus = Depends(get_event_bus)):
    """
    Get event statistics by municipality.
    
    Returns:
    - total_events: Total number of events
    - unique_actors: Number of unique users
    - unique_actions: Number of unique action types
    - first_event: Timestamp of first event
    - last_event: Timestamp of most recent event
    """
    try:
        from sqlalchemy import text
        with bus.pg_engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM events_summary WHERE municipality = :municipality"),
                {"municipality": bus.municipality}
            ).fetchone()
        
        if result:
            return {
                "municipality": result[0],
                "total_events": result[1],
                "first_event": result[2].isoformat() if result[2] else None,
                "last_event": result[3].isoformat() if result[3] else None,
                "unique_actors": result[4],
                "unique_actions": result[5]
            }
        else:
            return {
                "municipality": bus.municipality,
                "total_events": 0,
                "message": "No events recorded yet"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary retrieval failed: {str(e)}")
