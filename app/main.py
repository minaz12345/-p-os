"""
P-OS v8.0 — Citizen Service Portal API
FastAPI application for citizen-facing services

Endpoints:
- POST /api/v1/citizen/gdpr-export — Personal data export (Art. 15)
- DELETE /api/v1/citizen/gdpr-erase — Account deletion (Art. 17)
- GET /api/v1/public/transparency — Public dashboard (anonymous)
- POST /api/v1/citizen/complaints — Submit complaint/suggestion
- GET /api/v1/public/events — Event calendar

Security:
- JWT authentication for citizen endpoints
- RBAC middleware integration
- Rate limiting (40 req/min public, 5/hr GDPR)
- Audit logging to Neo4j
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Import middleware and utilities
from app.api.v1.middleware.rbac_middleware import rbac_check
from app.api.v1.middleware.rate_limiter import rate_limit_check
from app.api.v1.endpoints import gdpr, public, complaints, federation, event_bus

# Create FastAPI application
app = FastAPI(
    title="P-OS Milejczyce Citizen Portal",
    description="Sovereign digital infrastructure for municipal citizen services",
    version="8.0.0-d3-mvp",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration - RESTRICTED (P-OS v8.0 Security Hardening)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "https://milejczyce.gov.pl,https://portal.milejczyce.gov.pl").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
)

# Security Headers Middleware (P-OS v8.0 Hardening - Days 12-14)
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add comprehensive security headers to all responses"""
    response = await call_next(request)
    
    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # XSS Protection (legacy but still useful)
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # HTTP Strict Transport Security (for HTTPS deployments)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    
    # Referrer Policy - prevent leaking sensitive URLs
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Permissions Policy - restrict browser features
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=(), payment=(), usb=()"
    
    # Content Security Policy (restrictive default)
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    
    # Cache Control for sensitive API responses
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    
    return response

# Include routers
app.include_router(gdpr.router, prefix="/api/v1/citizen", tags=["GDPR Compliance"])
app.include_router(public.router, prefix="/api/v1/public", tags=["Public Services"])
app.include_router(complaints.router, prefix="/api/v1/citizen", tags=["Citizen Feedback"])
app.include_router(federation.router, tags=["Federation Gateway"])
app.include_router(event_bus.router, prefix="/api/v1/sovereign", tags=["Sovereign Event Bus"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "P-OS Citizen Portal",
        "version": "8.0.0-d3-mvp",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check with performance metrics"""
    import time
    from core.db.neo4j_connection import get_neo4j_driver
    
    start_time = time.time()
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {},
        "performance": {}
    }
    
    # Check Neo4j connection
    try:
        neo4j_start = time.time()
        driver = get_neo4j_driver()
        
        query_start = time.time()
        with driver.session() as session:
            result = session.run("RETURN 'connected' AS status")
            status = result.single()['status']
        query_time_ms = (time.time() - query_start) * 1000
        
        neo4j_total_ms = (time.time() - neo4j_start) * 1000
        
        health_status["components"]["neo4j"] = {
            "status": "healthy",
            "connection": status,
            "response_time_ms": round(query_time_ms, 2)
        }
        health_status["performance"]["neo4j_total_ms"] = round(neo4j_total_ms, 2)
    except Exception as e:
        health_status["components"]["neo4j"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    total_time_ms = (time.time() - start_time) * 1000
    health_status["performance"]["total_response_ms"] = round(total_time_ms, 2)
    
    return health_status


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
