"""
Mixed Endpoint Rate Limit Test
Verifies that rate limiting is per-category, not global
Tests: GDPR mutations + health checks + read-only endpoints
"""
import requests
import json
import time
from datetime import datetime
import urllib3

# Disable SSL warnings for self-signed cert
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://localhost:8443"

def send_gdpr_erasure_request(request_num):
    """Send GDPR erasure request (mutating operation)"""
    payload = {
        "citizen_id": f"PESEL-MIXED-TEST-{request_num:02d}",
        "reason": "USER_REQUEST",
        "operator_id": "mixed_test"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/gdpr/erasure/request",
            json=payload,
            verify=False,
            timeout=10
        )
        
        return {
            "type": "GDPR_MUTATION",
            "request_num": request_num,
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "response_preview": response.text[:150] if response.status_code != 200 else "OK"
        }
    except Exception as e:
        return {
            "type": "GDPR_MUTATION",
            "request_num": request_num,
            "status_code": None,
            "success": False,
            "response_preview": f"ERROR: {str(e)[:100]}"
        }

def check_health_endpoint(test_num):
    """Check health endpoint (read-only)"""
    try:
        response = requests.get(
            f"{BASE_URL}/health",
            verify=False,
            timeout=5
        )
        
        return {
            "type": "HEALTH_CHECK",
            "test_num": test_num,
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "response_preview": response.json().get("status", "UNKNOWN") if response.status_code == 200 else response.text[:100]
        }
    except Exception as e:
        return {
            "type": "HEALTH_CHECK",
            "test_num": test_num,
            "status_code": None,
            "success": False,
            "response_preview": f"ERROR: {str(e)[:100]}"
        }

def check_gdpr_status_endpoint(test_num):
    """Check GDPR status endpoint (read-only)"""
    try:
        response = requests.get(
            f"{BASE_URL}/gdpr/status",
            verify=False,
            timeout=5
        )
        
        return {
            "type": "GDPR_STATUS",
            "test_num": test_num,
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "response_preview": "OK" if response.status_code == 200 else response.text[:100]
        }
    except Exception as e:
        return {
            "type": "GDPR_STATUS",
            "test_num": test_num,
            "status_code": None,
            "success": False,
            "response_preview": f"ERROR: {str(e)[:100]}"
        }

def main():
    print("=" * 80)
    print("MIXED ENDPOINT RATE LIMIT TEST")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("Goal: Verify rate limiting is per-category, not global")
    print("=" * 80)
    
    results = []
    
    # Phase 1: Send 5 GDPR mutation requests (should succeed)
    print("\n📤 Phase 1: Sending 5 GDPR erasure requests (within limit)...")
    for i in range(1, 6):
        result = send_gdpr_erasure_request(i)
        results.append(result)
        status = "✅" if result['success'] else "❌"
        print(f"   {status} GDPR #{i}: HTTP {result['status_code']} - {result['response_preview'][:80]}")
        time.sleep(0.1)  # Small delay
    
    # Phase 2: Check health endpoint (should still work)
    print("\n🏥 Phase 2: Checking /health endpoint (should be unaffected)...")
    health_result = check_health_endpoint(1)
    results.append(health_result)
    status = "✅" if health_result['success'] else "❌"
    print(f"   {status} Health: HTTP {health_result['status_code']} - {health_result['response_preview']}")
    
    # Phase 3: Check GDPR status endpoint (should still work)
    print("\n📊 Phase 3: Checking /gdpr/status endpoint (should be unaffected)...")
    status_result = check_gdpr_status_endpoint(1)
    results.append(status_result)
    status = "✅" if status_result['success'] else "❌"
    print(f"   {status} GDPR Status: HTTP {status_result['status_code']} - {status_result['response_preview']}")
    
    # Phase 4: Send 6th GDPR request (should be rejected with 429)
    print("\n🚫 Phase 4: Sending 6th GDPR request (should be rate limited)...")
    result_6 = send_gdpr_erasure_request(6)
    results.append(result_6)
    expected_rejection = result_6['status_code'] == 429
    status = "✅" if expected_rejection else "❌"
    print(f"   {status} GDPR #6: HTTP {result_6['status_code']} - {result_6['response_preview'][:80]}")
    
    # Phase 5: Check health again after rate limit hit
    print("\n🏥 Phase 5: Checking /health again (should still work)...")
    health_result_2 = check_health_endpoint(2)
    results.append(health_result_2)
    status = "✅" if health_result_2['success'] else "❌"
    print(f"   {status} Health: HTTP {health_result_2['status_code']} - {health_result_2['response_preview']}")
    
    # Phase 6: Check GDPR status again
    print("\n📊 Phase 6: Checking /gdpr/status again (should still work)...")
    status_result_2 = check_gdpr_status_endpoint(2)
    results.append(status_result_2)
    status = "✅" if status_result_2['success'] else "❌"
    print(f"   {status} GDPR Status: HTTP {status_result_2['status_code']} - {status_result_2['response_preview']}")
    
    # Analysis
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    # Count successes by type
    gdpr_mutations = [r for r in results if r['type'] == 'GDPR_MUTATION']
    health_checks = [r for r in results if r['type'] == 'HEALTH_CHECK']
    gdpr_status = [r for r in results if r['type'] == 'GDPR_STATUS']
    
    gdpr_accepted = sum(1 for r in gdpr_mutations if r['success'])
    gdpr_rejected = sum(1 for r in gdpr_mutations if r['status_code'] == 429)
    health_ok = sum(1 for r in health_checks if r['success'])
    status_ok = sum(1 for r in gdpr_status if r['success'])
    
    print(f"\nGDPR Mutations:")
    print(f"  ✅ Accepted: {gdpr_accepted}/6 (expected: 5)")
    print(f"  🚫 Rejected (429): {gdpr_rejected}/6 (expected: 1)")
    
    print(f"\nHealth Checks:")
    print(f"  ✅ Successful: {health_ok}/{len(health_checks)} (expected: {len(health_checks)})")
    
    print(f"\nGDPR Status:")
    print(f"  ✅ Successful: {status_ok}/{len(gdpr_status)} (expected: {len(gdpr_status)})")
    
    # Determine if rate limiting is per-category
    print("\n" + "=" * 80)
    print("RATE LIMITING SCOPE VERIFICATION")
    print("=" * 80)
    
    if health_ok == len(health_checks) and status_ok == len(gdpr_status):
        print("\n✅ RATE LIMITING IS PER-CATEGORY (not global)")
        print("   - GDPR mutations blocked after 5 requests")
        print("   - Health checks unaffected")
        print("   - Read-only endpoints unaffected")
        print("   - Gateway remains healthy")
    else:
        print("\n❌ RATE LIMITING MAY BE GLOBAL OR CAUSING SIDE EFFECTS")
        print(f"   - Health checks failed: {len(health_checks) - health_ok}")
        print(f"   - Status checks failed: {len(gdpr_status) - status_ok}")
    
    # Final verdict
    print("\n" + "=" * 80)
    print("FINAL VERDICT")
    print("=" * 80)
    
    all_correct = (
        gdpr_accepted == 5 and
        gdpr_rejected == 1 and
        health_ok == len(health_checks) and
        status_ok == len(gdpr_status)
    )
    
    if all_correct:
        print("\n✅ ALL TESTS PASSED")
        print("\nConfirmed:")
        print("  ✓ Rate limiting works correctly (5/hour for GDPR)")
        print("  ✓ Rate limiting is per-category (not global)")
        print("  ✓ Read-only endpoints unaffected by mutation limits")
        print("  ✓ Gateway stability maintained under rate limiting")
        print("  ✓ Fail-closed behavior for excess mutations")
        exit(0)
    else:
        print("\n⚠️  SOME TESTS FAILED - Review results above")
        exit(1)

if __name__ == "__main__":
    main()
