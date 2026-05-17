#!/usr/bin/env python3
"""
Integration Test: Phase 4 API Gateway + Queue System

Tests complete end-to-end flow:
1. Request submission via API
2. Queue management with idempotency
3. Pipeline execution (Phase 2)
4. W11 validation (Phase 3)
5. Certificate issuance
6. Download availability

Usage:
    python tests/test_api_gateway.py
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from services.export_api_gateway import ExportAPIGateway
from services.export_queue_manager import ExportQueueManager


def test_submit_valid_request(api):
    """Test submitting a valid export request."""
    
    print("\n" + "=" * 80)
    print("TEST 1: Submit Valid Export Request")
    print("=" * 80)
    
    # Use timestamp-based unique key to avoid conflicts
    from datetime import datetime
    unique_key = f"test_valid_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    response = api.submit_request({
        'dataset_path': 'Facebook/kasiaju_1977350892357109/message_1.json',
        'data_subject': {
            'name': 'Kasia Ju',
            'email': 'kasia@example.com'
        },
        'idempotency_key': unique_key
    })
    
    assert response['status_code'] == 201, f"Expected 201, got {response['status_code']}"
    assert 'request_id' in response, "Response missing request_id"
    assert response['status'] in ['COMPLETED', 'BLOCKED'], f"Unexpected status: {response['status']}"
    
    print(f"✅ Request submitted: {response['request_id']}")
    print(f"   Status: {response['status']}")
    print(f"   Message: {response['message']}")
    
    return response['request_id']


def test_get_status(api, request_id):
    """Test retrieving request status."""
    
    print("\n" + "=" * 80)
    print("TEST 2: Get Request Status")
    print("=" * 80)
    
    status = api.get_status(request_id)
    
    assert status['status_code'] == 200, f"Expected 200, got {status['status_code']}"
    assert status['request_id'] == request_id, "Request ID mismatch"
    assert 'status' in status, "Status field missing"
    
    print(f"✅ Status retrieved: {status['status']}")
    print(f"   Created: {status['created_at']}")
    print(f"   Deadline: {status['deadline_at']}")
    
    if status.get('certificate_id'):
        print(f"   Certificate: {status['certificate_id']}")


def test_get_certificate(api, request_id):
    """Test retrieving W11 certificate."""
    
    print("\n" + "=" * 80)
    print("TEST 3: Retrieve W11 Certificate")
    print("=" * 80)
    
    cert = api.get_certificate(request_id)
    
    assert cert['status_code'] == 200, f"Expected 200, got {cert['status_code']}"
    assert 'certificate_id' in cert, "Certificate ID missing"
    assert 'overall_verdict' in cert, "Overall verdict missing"
    assert 'w11_validation' in cert, "W11 validation results missing"
    
    # Verify all 7 rules present
    rules = cert['w11_validation']
    assert len(rules) == 7, f"Expected 7 rules, got {len(rules)}"
    
    passed_count = sum(1 for v in rules.values() if v == 'PASS')
    
    print(f"✅ Certificate retrieved: {cert['certificate_id']}")
    print(f"   Verdict: {cert['overall_verdict']}")
    print(f"   Rules passed: {passed_count}/7")
    
    for rule, status in rules.items():
        icon = "✓" if status == 'PASS' else "✗"
        print(f"     {icon} {rule}: {status}")
    
    return cert


def test_download_export(api, request_id):
    """Test getting download information."""
    
    print("\n" + "=" * 80)
    print("TEST 4: Get Download Information")
    print("=" * 80)
    
    download = api.download_export(request_id)
    
    assert download['status_code'] == 200, f"Expected 200, got {download['status_code']}"
    assert 'download_path' in download, "Download path missing"
    assert 'files' in download, "Files list missing"
    
    print(f"✅ Export ready for download")
    print(f"   Path: {download['download_path']}")
    print(f"   Files: {len(download['files'])}")
    for filename in download['files']:
        print(f"     - {filename}")


def test_idempotency_prevention():
    """Test that duplicate requests are blocked."""
    
    print("\n" + "=" * 80)
    print("TEST 5: Idempotency Prevention (Duplicate Blocking)")
    print("=" * 80)
    
    api = ExportAPIGateway()
    
    # First submission
    response1 = api.submit_request({
        'dataset_path': 'Facebook/kasiaju_1977350892357109/message_1.json',
        'data_subject': {
            'name': 'Test User',
            'email': 'test@example.com'
        },
        'idempotency_key': 'idem_test_key'
    })
    
    assert response1['status_code'] == 201, "First submission should succeed"
    
    # Second submission with same key (should fail)
    response2 = api.submit_request({
        'dataset_path': 'Facebook/kasiaju_1977350892357109/message_1.json',
        'data_subject': {
            'name': 'Test User',
            'email': 'test@example.com'
        },
        'idempotency_key': 'idem_test_key'  # Same key
    })
    
    assert response2['status_code'] == 409, f"Expected 409 (Conflict), got {response2['status_code']}"
    assert 'error' in response2, "Error message missing"
    
    print(f"✅ Duplicate request blocked")
    print(f"   First request: {response1['request_id']}")
    print(f"   Error: {response2['error']}")


def test_invalid_dataset_path():
    """Test handling of non-existent dataset."""
    
    print("\n" + "=" * 80)
    print("TEST 6: Invalid Dataset Path Handling")
    print("=" * 80)
    
    api = ExportAPIGateway()
    
    response = api.submit_request({
        'dataset_path': 'nonexistent/dataset.json',
        'data_subject': {
            'name': 'Test User',
            'email': 'test@example.com'
        }
    })
    
    assert response['status_code'] == 404, f"Expected 404, got {response['status_code']}"
    assert 'error' in response, "Error message missing"
    
    print(f"✅ Invalid dataset rejected")
    print(f"   Error: {response['error']}")


def test_missing_required_fields():
    """Test validation of required fields."""
    
    print("\n" + "=" * 80)
    print("TEST 7: Missing Required Fields Validation")
    print("=" * 80)
    
    api = ExportAPIGateway()
    
    # Missing dataset_path
    response1 = api.submit_request({
        'data_subject': {'name': 'Test'}
    })
    
    assert response1['status_code'] == 400, f"Expected 400, got {response1['status_code']}"
    
    # Missing data_subject
    response2 = api.submit_request({
        'dataset_path': 'some/path.json'
    })
    
    assert response2['status_code'] == 400, f"Expected 400, got {response2['status_code']}"
    
    print(f"✅ Missing fields properly validated")
    print(f"   Missing dataset_path: {response1['error']}")
    print(f"   Missing data_subject: {response2['error']}")


def test_certificate_not_available_for_pending():
    """Test that certificate is not available for pending requests."""
    
    print("\n" + "=" * 80)
    print("TEST 8: Certificate Availability Check")
    print("=" * 80)
    
    manager = ExportQueueManager()
    
    # Create a pending request manually
    from services.export_queue_manager import ExportRequest
    req = ExportRequest(
        dataset_path="test.json",
        data_subject={'name': 'Test'}
    )
    manager.requests[req.request_id] = req
    manager._save_request(req)
    
    api = ExportAPIGateway()
    cert_response = api.get_certificate(req.request_id)
    
    assert cert_response['status_code'] == 400, f"Expected 400, got {cert_response['status_code']}"
    assert 'error' in cert_response, "Error message missing"
    
    print(f"✅ Certificate correctly unavailable for pending request")
    print(f"   Status: {cert_response['current_status']}")
    print(f"   Error: {cert_response['error']}")


def test_end_to_end_flow():
    """Complete end-to-end test: submit → process → certificate → download."""
    
    print("\n" + "=" * 80)
    print("TEST 9: End-to-End Flow (Complete Lifecycle)")
    print("=" * 80)
    
    api = ExportAPIGateway()
    
    # Use unique key
    from datetime import datetime
    unique_key = f"e2e_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Step 1: Submit
    print("\n[Step 1] Submitting request...")
    submit_response = api.submit_request({
        'dataset_path': 'Facebook/kasiaju_1977350892357109/message_1.json',
        'data_subject': {
            'name': 'Kasia Ju',
            'email': 'kasia@example.com'
        },
        'idempotency_key': unique_key
    })
    
    assert submit_response['status_code'] == 201
    request_id = submit_response['request_id']
    print(f"   ✓ Submitted: {request_id}")
    
    # Step 2: Check status
    print("\n[Step 2] Checking status...")
    status = api.get_status(request_id)
    assert status['status_code'] == 200
    print(f"   ✓ Status: {status['status']}")
    
    # Step 3: Get certificate
    print("\n[Step 3] Retrieving certificate...")
    cert = api.get_certificate(request_id)
    assert cert['status_code'] == 200
    print(f"   ✓ Certificate: {cert['certificate_id']}")
    print(f"   ✓ Verdict: {cert['overall_verdict']}")
    
    # Step 4: Download
    print("\n[Step 4] Getting download info...")
    download = api.download_export(request_id)
    assert download['status_code'] == 200
    print(f"   ✓ Files available: {len(download['files'])}")
    
    print("\n✅ END-TO-END FLOW COMPLETE")
    print(f"   Request: {request_id}")
    print(f"   Status: {submit_response['status']}")
    print(f"   Certificate: {cert['certificate_id']}")
    print(f"   Files: {len(download['files'])}")


def main():
    """Run all API gateway integration tests."""
    
    print("=" * 80)
    print("PHASE 4: API GATEWAY INTEGRATION TEST SUITE")
    print("=" * 80)
    print()
    print("Testing complete GDPR export API lifecycle...")
    
    # Create single API instance to maintain state
    api = ExportAPIGateway()
    
    tests_passed = 0
    tests_failed = 0
    request_id = None
    
    try:
        # Run individual tests
        request_id = test_submit_valid_request(api)
        tests_passed += 1
        
        if request_id:
            test_get_status(api, request_id)
            tests_passed += 1
            
            test_get_certificate(api, request_id)
            tests_passed += 1
            
            test_download_export(api, request_id)
            tests_passed += 1
        
        test_idempotency_prevention()
        tests_passed += 1
        
        test_invalid_dataset_path()
        tests_passed += 1
        
        test_missing_required_fields()
        tests_passed += 1
        
        test_certificate_not_available_for_pending()
        tests_passed += 1
        
        test_end_to_end_flow()
        tests_passed += 1
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        tests_failed += 1
    except Exception as e:
        print(f"\n❌ TEST ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        tests_failed += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {tests_passed + tests_failed}")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    print()
    
    if tests_failed == 0:
        print("✅ ALL API GATEWAY TESTS PASSED")
        print()
        print("Production-ready API endpoints:")
        print("  ✓ POST /gdpr/export/request - Submit export request")
        print("  ✓ GET /gdpr/export/status/{id} - Check processing status")
        print("  ✓ GET /gdpr/export/certificate/{id} - Retrieve W11 certificate")
        print("  ✓ GET /gdpr/export/download/{id} - Download approved export")
        print()
        print("Features validated:")
        print("  ✓ Idempotency enforcement (duplicate prevention)")
        print("  ✓ Input validation (required fields, dataset existence)")
        print("  ✓ Complete pipeline execution (Phase 2 + Phase 3)")
        print("  ✓ Certificate generation and retrieval")
        print("  ✓ Download availability after approval")
        return True
    else:
        print(f"❌ {tests_failed} TEST(S) FAILED")
        print()
        print("API gateway requires fixes before deployment.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
