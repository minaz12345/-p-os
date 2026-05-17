"""
RBAC Middleware for Citizen Portal
Integrates with scripts/rbac_enforcement.py for role-based access control
"""

from fastapi import Request, HTTPException, Depends
from typing import Optional
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from scripts.rbac_enforcement import RBACEnforcementEngine
    from scripts.session_manager import SessionManagerEngine
except ImportError as e:
    print(f"⚠️  Warning: Could not import security modules: {e}")
    # Fallback for development
    class RBACEnforcementEngine:
        def check_access(self, *args, **kwargs):
            return {'allowed': True, 'permitted_tiers': ['PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED']}
    
    class SessionManagerEngine:
        def verify_token(self, token: str):
            return {'valid': True, 'username': 'dev_user', 'role': 'admin'}


# Initialize engines (singleton pattern)
rbac_engine = RBACEnforcementEngine()
session_engine = SessionManagerEngine()


async def get_current_user(request: Request) -> dict:
    """Extract and verify user from JWT token"""
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide valid JWT token."
        )
    
    token = auth_header.split(" ")[1]
    
    # Verify token
    verification = session_engine.verify_token(token)
    
    if not verification['valid']:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or expired token: {verification['reason']}"
        )
    
    # Return user context
    return {
        'username': verification['username'],
        'role': verification.get('role', 'citizen'),
        'token_type': verification.get('type', 'access')
    }


async def rbac_check(request: Request, required_tier: str = "PUBLIC", current_user: dict = Depends(get_current_user)):
    """
    RBAC middleware - checks if user has access to requested data tier
    
    Args:
        request: FastAPI request object
        required_tier: Minimum classification tier required (PUBLIC/INTERNAL/CONFIDENTIAL/RESTRICTED)
        current_user: User context from JWT token
    
    Raises:
        HTTPException: If user lacks required permissions
    """
    username = current_user['username']
    user_role = current_user['role']
    
    # Check RBAC permissions
    access_check = rbac_engine.check_access(username, required_tier)
    
    if not access_check['allowed']:
        # Log denied access attempt
        from app.api.v1.utils.audit_logger import log_access_attempt
        log_access_attempt(
            username=username,
            action="ACCESS_DENIED",
            endpoint=str(request.url.path),
            reason=access_check['reason'],
            ip_address=request.client.host if request.client else "unknown"
        )
        
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: {access_check['reason']}"
        )
    
    # Log successful access
    from app.api.v1.utils.audit_logger import log_access_attempt
    log_access_attempt(
        username=username,
        action="ACCESS_GRANTED",
        endpoint=str(request.url.path),
        tier=required_tier,
        ip_address=request.client.host if request.client else "unknown"
    )
    
    # Add user context to request state for downstream use
    request.state.user = current_user
    request.state.permitted_tiers = access_check.get('permitted_tiers', ['PUBLIC'])
    
    return current_user


# Dependency functions for different access levels
async def require_citizen(request: Request, current_user: dict = Depends(get_current_user)):
    """Require citizen role (minimum authentication)"""
    if current_user['role'] not in ['citizen', 'analyst', 'admin', 'auditor']:
        raise HTTPException(status_code=403, detail="Citizen account required")
    return current_user


async def require_analyst(request: Request, current_user: dict = Depends(get_current_user)):
    """Require analyst role or higher"""
    if current_user['role'] not in ['analyst', 'admin']:
        raise HTTPException(status_code=403, detail="Analyst role required")
    return current_user


async def require_admin(request: Request, current_user: dict = Depends(get_current_user)):
    """Require admin role"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin role required")
    return current_user


async def require_auditor(request: Request, current_user: dict = Depends(get_current_user)):
    """Require auditor or admin role"""
    if current_user['role'] not in ['auditor', 'admin']:
        raise HTTPException(status_code=403, detail="Auditor role required")
    return current_user
