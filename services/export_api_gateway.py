#!/usr/bin/env python3
"""
Phase 4: GDPR Export API Gateway

REST API endpoints for forensic export pipeline.
Integrates Phase 2 (pipeline) + Phase 3 (W11 validation) + queue management.

Endpoints:
    POST   /gdpr/export/request        - Submit new export request
    GET    /gdpr/export/status/{id}    - Check processing status
    GET    /gdpr/export/certificate/{id} - Retrieve W11 certificate
    GET    /gdpr/export/download/{id}  - Download approved export

Usage:
    from services.export_api_gateway import ExportAPIGateway
    
    api = ExportAPIGateway()
    
    # Simulate request submission
    response = api.submit_request({
        'dataset_path': 'Facebook/kasiaju_1977350892357109/message_1.json',
        'data_subject': {'name': 'Kasia Ju', 'email': 'kasia@example.com'}
    })
    
    print(response)  # Returns request_id
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from services.export_queue_manager import ExportQueueManager, RequestStatus
from services.forensic_export_pipeline import ForensicExportPipeline
from services.w11_validator import W11GateFull


class ExportAPIGateway:
    """
    REST API gateway for GDPR forensic exports.
    
    Orchestrates:
    1. Request submission → Queue Manager
    2. Pipeline execution → Phase 2
    3. Constitutional validation → Phase 3
    4. Certificate issuance → Response
    """
    
    def __init__(self):
        self.queue_manager = ExportQueueManager()
        
    def submit_request(self, request_data: Dict) -> Dict:
        """
        POST /gdpr/export/request
        
        Submit new forensic export request.
        
        Request body:
        {
            "dataset_path": "path/to/conversation.json",
            "data_subject": {
                "name": "John Doe",
                "email": "john@example.com"
            },
            "deadline_hours": 72,  // optional, default 72
            "idempotency_key": "unique_key"  // optional, prevents duplicates
        }
        
        Response:
        {
            "request_id": "uuid",
            "status": "PENDING",
            "message": "Request queued for processing"
        }
        """
        
        try:
            # Validate required fields
            if 'dataset_path' not in request_data:
                return {
                    'error': 'Missing required field: dataset_path',
                    'status_code': 400
                }
            
            if 'data_subject' not in request_data:
                return {
                    'error': 'Missing required field: data_subject',
                    'status_code': 400
                }
            
            # Extract parameters
            dataset_path = request_data['dataset_path']
            data_subject = request_data['data_subject']
            deadline_hours = request_data.get('deadline_hours', 72)
            idempotency_key = request_data.get('idempotency_key')
            
            # Validate dataset exists
            dataset_full_path = project_root / dataset_path
            if not dataset_full_path.exists():
                return {
                    'error': f'Dataset not found: {dataset_path}',
                    'status_code': 404
                }
            
            # Submit to queue
            request_id = self.queue_manager.submit_request(
                dataset_path=dataset_path,
                data_subject=data_subject,
                deadline_hours=deadline_hours,
                idempotency_key=idempotency_key
            )
            
            # Process immediately (synchronous for now, async in production)
            result = self._process_request(request_id)
            
            return {
                'request_id': request_id,
                'status': result['status'],
                'message': result['message'],
                'certificate_id': result.get('certificate_id'),
                'status_code': 201
            }
            
        except ValueError as e:
            # Idempotency violation
            return {
                'error': str(e),
                'status_code': 409  # Conflict
            }
        except Exception as e:
            return {
                'error': f'Internal server error: {str(e)}',
                'status_code': 500
            }
    
    def get_status(self, request_id: str) -> Dict:
        """
        GET /gdpr/export/status/{request_id}
        
        Check current status of export request.
        
        Response:
        {
            "request_id": "uuid",
            "status": "COMPLETED|BLOCKED|PENDING|PROCESSING",
            "created_at": "ISO timestamp",
            "deadline_at": "ISO timestamp",
            "time_remaining": "HH:MM:SS",
            "certificate_id": "cert_xyz" (if completed)
        }
        """
        
        status = self.queue_manager.get_status(request_id)
        
        if 'error' in status:
            return {
                **status,
                'status_code': 404
            }
        
        return {
            **status,
            'status_code': 200
        }
    
    def get_certificate(self, request_id: str) -> Dict:
        """
        GET /gdpr/export/certificate/{request_id}
        
        Retrieve W11 constitutional validation certificate.
        
        Response:
        {
            "certificate_id": "cert_xyz",
            "overall_verdict": "APPROVED|BLOCKED",
            "w11_validation": {
                "R1_immutability_no_data_loss": "PASS",
                "R2_determinism_reproducible": "PASS",
                ...
            },
            "hash_chain": [...],
            "issued_at": "ISO timestamp"
        }
        """
        
        # Get request directly from queue manager
        request = self.queue_manager.requests.get(request_id)
        
        if not request:
            return {
                'error': 'Request not found',
                'request_id': request_id,
                'status_code': 404
            }
        
        if request.status not in [RequestStatus.COMPLETED, RequestStatus.BLOCKED]:
            return {
                'error': 'Certificate not available - request still processing',
                'request_id': request_id,
                'current_status': request.status.value,
                'status_code': 400
            }
        
        certificate = request.certificate
        
        if not certificate:
            return {
                'error': 'Certificate not found',
                'request_id': request_id,
                'status_code': 404
            }
        
        return {
            **certificate,
            'status_code': 200
        }
    
    def download_export(self, request_id: str) -> Dict:
        """
        GET /gdpr/export/download/{request_id}
        
        Download approved export package.
        
        Response:
        {
            "download_url": "/exports/{request_id}/package.zip",
            "expires_at": "ISO timestamp",
            "file_size_mb": 1.3
        }
        """
        
        status = self.queue_manager.get_status(request_id)
        
        if 'error' in status:
            return {
                **status,
                'status_code': 404
            }
        
        if status['status'] != 'COMPLETED':
            return {
                'error': 'Export not available - request not approved',
                'request_id': request_id,
                'current_status': status['status'],
                'status_code': 400
            }
        
        # In production, this would generate signed download URL
        # For now, return path to export directory
        export_dir = project_root / "data" / "exports" / request_id
        
        if not export_dir.exists():
            return {
                'error': 'Export files not found',
                'request_id': request_id,
                'status_code': 404
            }
        
        return {
            'request_id': request_id,
            'download_path': str(export_dir),
            'files': [f.name for f in export_dir.glob("*")],
            'expires_at': status.get('deadline_at'),
            'status_code': 200
        }
    
    def _process_request(self, request_id: str) -> Dict:
        """
        Execute complete pipeline: Phase 2 → Phase 3
        
        Internal method called after request submission.
        """
        
        request = self.queue_manager.requests[request_id]
        
        try:
            # Update status to PROCESSING
            self.queue_manager.update_status(request_id, RequestStatus.PROCESSING)
            
            # PHASE 2: Run forensic export pipeline
            print(f"\n[API] Processing request {request_id}")
            print(f"[API] Running Phase 2: Forensic Export Pipeline...")
            
            dataset_path = project_root / request.dataset_path
            pipeline = ForensicExportPipeline(dataset_path, request_id)
            pipeline_results = pipeline.run_pipeline()
            
            # PHASE 3: Run W11 constitutional validation
            print(f"[API] Running Phase 3: W11 Constitutional Validation...")
            
            validator = W11GateFull(pipeline_results, request_id)
            certificate = validator.validate_all_rules()
            
            # Determine final status based on W11 verdict
            if certificate['overall_verdict'] == 'APPROVED':
                self.queue_manager.update_status(
                    request_id, 
                    RequestStatus.COMPLETED, 
                    certificate
                )
                
                # Save certificate to disk
                cert_path = project_root / "data" / "exports" / request_id / "w11_certificate.json"
                with open(cert_path, 'w', encoding='utf-8') as f:
                    json.dump(certificate, f, indent=2, ensure_ascii=False)
                
                return {
                    'status': 'COMPLETED',
                    'message': 'Export approved and ready for download',
                    'certificate_id': certificate['certificate_id']
                }
            else:
                self.queue_manager.update_status(
                    request_id,
                    RequestStatus.BLOCKED,
                    certificate
                )
                
                # Create REGRESSION_DETECTED.flag
                flags_dir = project_root / "flags"
                flags_dir.mkdir(exist_ok=True)
                flag_file = flags_dir / f"REGRESSION_{request_id}.flag"
                with open(flag_file, 'w') as f:
                    json.dump({
                        'request_id': request_id,
                        'timestamp': datetime.now().isoformat(),
                        'violations': certificate['violations']
                    }, f, indent=2)
                
                return {
                    'status': 'BLOCKED',
                    'message': f'Export blocked: {len(certificate["violations"])} constitutional violation(s)',
                    'violations': certificate['violations'][:3]  # First 3 violations
                }
        
        except Exception as e:
            # Handle pipeline failures
            self.queue_manager.update_status(
                request_id,
                RequestStatus.FAILED,
                error_message=str(e)
            )
            
            return {
                'status': 'FAILED',
                'message': f'Pipeline execution failed: {str(e)}'
            }


def main():
    """Test API gateway with sample requests."""
    
    print("=" * 80)
    print("EXPORT API GATEWAY - INTEGRATION TEST")
    print("=" * 80)
    
    api = ExportAPIGateway()
    
    # Test 1: Submit valid request
    print("\n[TEST 1] Submitting valid export request...")
    response = api.submit_request({
        'dataset_path': 'Facebook/kasiaju_1977350892357109/message_1.json',
        'data_subject': {
            'name': 'Kasia Ju',
            'email': 'kasia@example.com'
        },
        'idempotency_key': 'api_test_001'
    })
    
    print(f"Response: {json.dumps(response, indent=2)}")
    
    request_id = response.get('request_id')
    
    if not request_id:
        print("❌ FAIL: Request submission failed")
        return
    
    # Test 2: Get status
    print("\n[TEST 2] Checking request status...")
    status_response = api.get_status(request_id)
    print(f"Status: {status_response.get('status')}")
    
    # Test 3: Get certificate
    print("\n[TEST 3] Retrieving W11 certificate...")
    cert_response = api.get_certificate(request_id)
    
    if 'status_code' in cert_response and cert_response['status_code'] == 200:
        print(f"✅ Certificate retrieved: {cert_response.get('certificate_id')}")
        print(f"   Verdict: {cert_response.get('overall_verdict')}")
        print(f"   Rules passed: {sum(1 for v in cert_response.get('w11_validation', {}).values() if v == 'PASS')}/7")
    else:
        print(f"⚠ Certificate response: {cert_response}")
    
    # Test 4: Download export
    print("\n[TEST 4] Getting download info...")
    download_response = api.download_export(request_id)
    
    if 'status_code' in download_response and download_response['status_code'] == 200:
        print(f"✅ Export ready for download")
        print(f"   Files: {len(download_response.get('files', []))}")
    else:
        print(f"⚠ Download response: {download_response}")
    
    # Test 5: Try duplicate submission
    print("\n[TEST 5] Testing idempotency (duplicate prevention)...")
    dup_response = api.submit_request({
        'dataset_path': 'Facebook/kasiaju_1977350892357109/message_1.json',
        'data_subject': {
            'name': 'Kasia Ju',
            'email': 'kasia@example.com'
        },
        'idempotency_key': 'api_test_001'  # Same key
    })
    
    if dup_response.get('status_code') == 409:
        print(f"✅ PASS: Duplicate request blocked")
        print(f"   Error: {dup_response.get('error')}")
    else:
        print(f"❌ FAIL: Duplicate was not blocked")
    
    print("\n" + "=" * 80)
    print("API GATEWAY TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
