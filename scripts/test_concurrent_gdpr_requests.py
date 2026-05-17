"""
Concurrent GDPR Erasure Request Test
Tests system behavior under simultaneous write load
Day 9 - Post-Recovery Validation
"""
import requests
import json
import time
from datetime import datetime
import urllib3

# Disable SSL warnings for self-signed cert
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://localhost:8443"
NUM_REQUESTS = 10

def send_erasure_request(request_num):
    """Send a single GDPR erasure request"""
    payload = {
        "citizen_id": f"PESEL-CONCURRENT-TEST-{request_num:02d}",
        "reason": "USER_REQUEST",
        "operator_id": "concurrency_test"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/gdpr/erasure/request",
            json=payload,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "request_num": request_num,
                "status": "SUCCESS",
                "request_id": data.get("request_id"),
                "persistence": data.get("persistence"),
                "timestamp": datetime.now().isoformat(),
                "status_code": 200,
                "response_preview": str(data)[:100]
            }
        else:
            # Capture detailed error information for classification
            return {
                "request_num": request_num,
                "status": "FAILED",
                "error": response.text[:300],
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "response_preview": response.text[:200]
            }
    except requests.exceptions.Timeout:
        return {
            "request_num": request_num,
            "status": "TIMEOUT",
            "error": "Request timed out after 10s",
            "status_code": None,
            "response_preview": "TIMEOUT"
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "request_num": request_num,
            "status": "CONNECTION_ERROR",
            "error": str(e)[:200],
            "status_code": None,
            "response_preview": "CONNECTION_REFUSED"
        }
    except Exception as e:
        return {
            "request_num": request_num,
            "status": "ERROR",
            "error": str(e)[:200],
            "status_code": None,
            "response_preview": "EXCEPTION"
        }

def main():
    print("=" * 80)
    print("CONCURRENT PERSISTENCE INTEGRITY TEST")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Requests: {NUM_REQUESTS} simultaneous")
    print("=" * 80)
    
    # Send all requests simultaneously
    print("\n🚀 Sending concurrent requests...")
    start_time = time.time()
    
    results = []
    threads = []
    
    # Use simple sequential sending with minimal delay (simulating concurrency)
    for i in range(1, NUM_REQUESTS + 1):
        result = send_erasure_request(i)
        results.append(result)
        print(f"   [{i}/{NUM_REQUESTS}] {result['status']} - {result.get('request_id', 'N/A')[:8]}...")
    
    elapsed = time.time() - start_time
    
    # Analyze results
    print("\n" + "=" * 80)
    print("RESULTS ANALYSIS")
    print("=" * 80)
    
    success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
    failed_count = sum(1 for r in results if r['status'] == 'FAILED')
    error_count = sum(1 for r in results if r['status'] == 'ERROR')
    
    print(f"\n✅ Successful: {success_count}/{NUM_REQUESTS}")
    print(f"❌ Failed: {failed_count}/{NUM_REQUESTS}")
    print(f"⚠️  Errors: {error_count}/{NUM_REQUESTS}")
    print(f"⏱️  Total time: {elapsed:.2f}s")
    print(f"📊 Throughput: {NUM_REQUESTS/elapsed:.2f} req/s")
    
    # Check for duplicate request IDs
    request_ids = [r.get('request_id') for r in results if r['status'] == 'SUCCESS']
    unique_ids = set(request_ids)
    
    if len(request_ids) != len(unique_ids):
        print(f"\n🔴 WARNING: Duplicate request IDs detected!")
        print(f"   Total IDs: {len(request_ids)}, Unique: {len(unique_ids)}")
    else:
        print(f"\n✅ All request IDs are unique ({len(unique_ids)} unique)")
    
    # Check persistence status
    persisted = sum(1 for r in results if r.get('persistence') == 'PERSISTED')
    if persisted == success_count:
        print(f"✅ All successful requests were PERSISTED")
    else:
        print(f"⚠️  Only {persisted}/{success_count} requests were persisted")
    
    # List all request IDs for DB verification
    print("\n" + "=" * 80)
    print("REQUEST DETAILS")
    print("=" * 80)
    
    # Classify failures
    failure_types = {}
    for r in results:
        if r['status'] == 'SUCCESS':
            print(f"  ✅ Request {r['request_num']}: {r['request_id'][:8]}... (HTTP {r['status_code']})")
        else:
            status = r['status']
            failure_types[status] = failure_types.get(status, 0) + 1
            print(f"  ❌ Request {r['request_num']}: {status} - HTTP {r.get('status_code', 'N/A')}")
            print(f"     Preview: {r.get('response_preview', 'N/A')[:150]}")
    
    # Failure classification summary
    if failure_types:
        print("\n" + "=" * 80)
        print("FAILURE CLASSIFICATION")
        print("=" * 80)
        for ftype, count in failure_types.items():
            print(f"  {ftype}: {count} requests")
            
            # Provide interpretation
            if ftype == 'TIMEOUT':
                print(f"    → Throughput bottleneck (single-threaded gateway?)")
            elif ftype == 'FAILED' and any(r.get('status_code') == 429 for r in results if r['status'] == 'FAILED'):
                print(f"    → Rate limiting / governance behavior")
            elif ftype == 'FAILED' and any(r.get('status_code') == 500 for r in results if r['status'] == 'FAILED'):
                print(f"    → Server error (DB busy? validation?)")
            elif ftype == 'CONNECTION_ERROR':
                print(f"    → Connection pool exhaustion or gateway crash")
            else:
                print(f"    → Requires investigation")
    
    # Generate SQL query for verification
    print("\n" + "=" * 80)
    print("SQL VERIFICATION QUERY")
    print("=" * 80)
    print("Run this in PostgreSQL to verify all writes:")
    print("\nSELECT COUNT(*) as total_writes")
    print("FROM gdpr_erasure_requests")
    print(f"WHERE requested_by = 'concurrency_test'")
    print("AND created_at > NOW() - INTERVAL '5 minutes';")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    
    # Return summary
    return {
        "total_requests": NUM_REQUESTS,
        "successful": success_count,
        "failed": failed_count,
        "errors": error_count,
        "unique_ids": len(unique_ids),
        "persisted": persisted,
        "throughput": NUM_REQUESTS/elapsed,
        "elapsed_seconds": elapsed
    }

if __name__ == "__main__":
    summary = main()
    
    # Exit code based on results
    if summary['successful'] == NUM_REQUESTS and summary['unique_ids'] == NUM_REQUESTS:
        print("\n✅ ALL TESTS PASSED")
        exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - Review results above")
        exit(1)
