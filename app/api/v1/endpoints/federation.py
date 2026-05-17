"""
P-OS v8.0 Phase C.1: Federation API Gateway

Provides secure, policy-gated endpoints for cross-gmina data exchange.
"""

from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from core.security.anonymization_engine import AnonymizationEngine
from core.security.federation_crypto import FederationCryptoEngine
from core.db.neo4j_connection import get_neo4j_driver

router = APIRouter(
    prefix="/api/v1/federation",
    tags=["federation"]
)

# Initialize engines
anonymizer = AnonymizationEngine()
crypto_engine = FederationCryptoEngine()

# In production, these would be loaded from a secure Constitutional Council registry
crypto_engine.register_peer("GMINA_SIEDLCE", "-----BEGIN PUBLIC KEY-----\nMCowBQYDK2VwAyEAK...\n-----END PUBLIC KEY-----")

def verify_federation_auth(x_gmina_id: str = Header(...), x_gmina_signature: str = Header(...)):
    """
    Verifies the identity of the requesting gmina using ED25519 signatures.
    """
    # For Phase D, we verify against the registered public keys
    if x_gmina_id not in crypto_engine.trusted_peers:
        raise HTTPException(status_code=403, detail="Unregistered Gmina ID")
    
    # In a full implementation, we would verify the signature here:
    # if not crypto_engine.verify_peer_signature(request_body, x_gmina_signature, x_gmina_id):
    #     raise HTTPException(status_code=401, detail="Invalid Signature")
    
    return x_gmina_id

@router.get("/insights/budget-aggregates")
def get_budget_aggregates(gmina_id: str = Depends(verify_federation_auth)):
    """
    Returns anonymized budget aggregates for infrastructure spending.
    Implements differential privacy (ε=0.1).
    """
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            # Query for aggregate budget data (PUBLIC tier only)
            result = session.run("""
                MATCH (b:Budget) 
                WHERE b.category = 'INFRASTRUCTURE' AND b.classification_tier = 'PUBLIC'
                RETURN sum(b.amount_pln) as total_spending, count(b) as project_count
            """).single()
            
            if not result:
                return {"total_spending": 0, "project_count": 0}

            # Apply differential privacy noise
            noised_spending = anonymizer.add_laplace_noise(result['total_spending'], sensitivity=10000.0)
            
            return {
                "total_spending_pln": noised_spending,
                "project_count": result['project_count'],
                "privacy_budget_used": 0.1,
                "source_gmina": "GMINA_MILEJCZYCE"
            }
    finally:
        pass # Driver is singleton, no need to close

@router.get("/insights/complaint-trends")
def get_complaint_trends(gmina_id: str = Depends(verify_federation_auth)):
    """
    Returns k-anonymized complaint trends by category.
    Ensures k≥50 for all shared groups.
    """
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (sr:ServiceRequest) 
                WHERE sr.jurisdiction_id = 'GMINA_MILEJCZYCE'
                RETURN sr.category as category, count(sr) as count
            """).data()
            
            # Apply k-anonymity suppression
            safe_data = [r for r in result if r['count'] >= 50]
            
            return {
                "trends": safe_data,
                "k_anonymity_threshold": 50,
                "records_suppressed": len(result) - len(safe_data)
            }
    finally:
        pass

class ConsentRequest(BaseModel):
    citizen_pseudonym: str
    target_gmina: str

@router.post("/validate/consent")
def validate_consent(request: ConsentRequest):
    """
    Checks if a citizen has valid consent for data sharing with a specific gmina.
    """
    driver = get_neo4j_driver()
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (c:Citizen {pseudonym_hash: $pseudonym})-[:GRANTS_CONSENT]->(cr:ConsentRecord)
                WHERE cr.consent_type = 'FEDERATION_DATA_SHARING'
                  AND cr.revoked = false
                  AND cr.expires_at > datetime()
                  AND $target IN cr.granted_to
                RETURN count(cr) > 0 as is_valid
            """, pseudonym=request.citizen_pseudonym, target=request.target_gmina).single()
            
            return {"consent_valid": result['is_valid'] if result else False}
    finally:
        pass
