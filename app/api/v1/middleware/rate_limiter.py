"""
Rate Limiting Middleware for Citizen Portal
Integrates with scripts/api_rate_limiter.py
"""

from fastapi import Request, HTTPException
from typing import Dict
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from scripts.api_rate_limiter import RateLimiterEngine
except ImportError as e:
    print(f"⚠️  Warning: Could not import rate limiter: {e}")
    # Fallback for development
    class RateLimiterEngine:
        def check_rate_limit(self, *args, **kwargs):
            return {'allowed': True, 'remaining': 1000}


# Initialize rate limiter (singleton)
rate_limiter = RateLimiterEngine()

# Rate limit configuration per endpoint category
RATE_LIMITS = {
    '/api/v1/public/': {'category': 'public', 'limit': 40},
    '/api/v1/citizen/gdpr-export': {'category': 'citizen_portal', 'limit': 5},
    '/api/v1/citizen/gdpr-erase': {'category': 'citizen_portal', 'limit': 2},
    '/api/v1/citizen/complaints': {'category': 'citizen_portal', 'limit': 10},
    '/api/v1/admin/': {'category': 'admin', 'limit': 300},
}


async def rate_limit_check(request: Request):
    """
    Rate limiting middleware - checks if request exceeds rate limits
    
    Args:
        request: FastAPI request object
    
    Raises:
        HTTPException: If rate limit exceeded (429 Too Many Requests)
    """
    # Get client IP
    client_host = request.client.host if request.client else "unknown"
    
    # Get request path
    path = request.url.path
    
    # Determine rate limit category based on path
    rate_config = None
    for prefix, config in RATE_LIMITS.items():
        if path.startswith(prefix):
            rate_config = config
            break
    
    # If no specific config found, use default public limit
    if not rate_config:
        rate_config = {'category': 'public', 'limit': 40}
    
    # Check rate limit
    result = rate_limiter.check_rate_limit(
        ip=client_host,
        endpoint_category=rate_config['category']
    )
    
    if not result['allowed']:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {result['reason']}",
            headers={
                "Retry-After": str(result.get('retry_after', 60)),
                "X-RateLimit-Limit": str(rate_config['limit']),
                "X-RateLimit-Remaining": "0"
            }
        )
    
    # Add rate limit headers to response (will be added by middleware later)
    request.state.rate_limit_remaining = result.get('remaining', rate_config['limit'])
    request.state.rate_limit_limit = rate_config['limit']
    
    return result
