#!/usr/bin/env python3
"""
Phase 4: GDPR Export Request Queue Manager

Manages asynchronous processing of forensic export requests.
Handles queue management, deadline enforcement (72h GDPR limit),
and idempotency for retry scenarios.

Usage:
    from services.export_queue_manager import ExportQueueManager
    
    manager = ExportQueueManager()
    request_id = manager.submit_request(dataset_path, data_subject)
    status = manager.get_status(request_id)
"""

import json
import sys
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from enum import Enum

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


class RequestStatus(Enum):
    """Export request lifecycle states."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class ExportRequest:
    """Represents a single GDPR export request."""
    
    def __init__(self, dataset_path: str, data_subject: Dict, deadline_hours: int = 72):
        self.request_id = str(uuid.uuid4())
        self.dataset_path = dataset_path
        self.data_subject = data_subject
        self.deadline_hours = deadline_hours
        self.created_at = datetime.now()
        self.deadline_at = self.created_at + timedelta(hours=deadline_hours)
        self.status = RequestStatus.PENDING
        self.certificate = None
        self.error_message = None
        self.idempotency_key = None
        
    def is_expired(self) -> bool:
        """Check if request has exceeded 72-hour GDPR deadline."""
        return datetime.now() > self.deadline_at
    
    def to_dict(self) -> Dict:
        """Serialize request to dictionary."""
        return {
            'request_id': self.request_id,
            'dataset_path': self.dataset_path,
            'data_subject': self.data_subject,
            'deadline_hours': self.deadline_hours,
            'created_at': self.created_at.isoformat(),
            'deadline_at': self.deadline_at.isoformat(),
            'status': self.status.value,
            'certificate': self.certificate,
            'error_message': self.error_message,
            'idempotency_key': self.idempotency_key
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ExportRequest':
        """Deserialize request from dictionary."""
        req = cls(data['dataset_path'], data['data_subject'], data['deadline_hours'])
        req.request_id = data['request_id']
        req.created_at = datetime.fromisoformat(data['created_at'])
        req.deadline_at = datetime.fromisoformat(data['deadline_at'])
        req.status = RequestStatus(data['status'])
        req.certificate = data.get('certificate')
        req.error_message = data.get('error_message')
        req.idempotency_key = data.get('idempotency_key')
        return req


class ExportQueueManager:
    """
    Manages GDPR export request queue with deadline enforcement.
    
    Features:
    - Idempotent request submission (prevents duplicates)
    - 72-hour GDPR deadline monitoring
    - Automatic expiration of overdue requests
    - Audit trail for all operations
    """
    
    def __init__(self, queue_dir: Path = None):
        self.queue_dir = queue_dir or (project_root / "data" / "export_queue")
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing queue
        self.requests: Dict[str, ExportRequest] = {}
        self._load_queue()
        
    def submit_request(self, dataset_path: str, data_subject: Dict, 
                      deadline_hours: int = 72, idempotency_key: str = None) -> str:
        """
        Submit new export request to queue.
        
        Args:
            dataset_path: Path to conversation dataset
            data_subject: Dict with name, email, etc.
            deadline_hours: GDPR deadline (default 72h)
            idempotency_key: Optional key to prevent duplicate submissions
            
        Returns:
            request_id (UUID string)
            
        Raises:
            ValueError: If idempotency_key already used
        """
        
        # Check idempotency
        if idempotency_key:
            existing = self._find_by_idempotency_key(idempotency_key)
            if existing:
                raise ValueError(f"Duplicate request: idempotency_key '{idempotency_key}' already used for request {existing.request_id}")
        
        # Create request
        request = ExportRequest(dataset_path, data_subject, deadline_hours)
        request.idempotency_key = idempotency_key
        
        # Add to queue
        self.requests[request.request_id] = request
        self._save_request(request)
        
        # Log audit event
        self._log_audit("REQUEST_SUBMITTED", request.request_id, 
                       f"Dataset: {dataset_path}, Subject: {data_subject.get('name')}")
        
        print(f"[QUEUE] Request submitted: {request.request_id}")
        print(f"        Deadline: {request.deadline_at.isoformat()} ({deadline_hours}h)")
        
        return request.request_id
    
    def get_status(self, request_id: str) -> Dict:
        """
        Get current status of export request.
        
        Returns:
            Dict with status, progress, certificate info
        """
        
        request = self.requests.get(request_id)
        
        if not request:
            return {'error': 'Request not found', 'request_id': request_id}
        
        # Check if expired
        if request.status == RequestStatus.PENDING and request.is_expired():
            request.status = RequestStatus.EXPIRED
            request.error_message = f"GDPR deadline exceeded ({request.deadline_hours}h)"
            self._save_request(request)
            self._log_audit("REQUEST_EXPIRED", request_id, "72-hour deadline exceeded")
        
        result = {
            'request_id': request.request_id,
            'status': request.status.value,
            'created_at': request.created_at.isoformat(),
            'deadline_at': request.deadline_at.isoformat(),
            'time_remaining': str(request.deadline_at - datetime.now()) if request.status in [RequestStatus.PENDING, RequestStatus.PROCESSING] else None,
            'data_subject': request.data_subject,
            'certificate_id': request.certificate.get('certificate_id') if request.certificate else None
        }
        
        if request.error_message:
            result['error_message'] = request.error_message
        
        return result
    
    def update_status(self, request_id: str, status: RequestStatus, 
                     certificate: Dict = None, error_message: str = None):
        """
        Update request status after pipeline processing.
        
        Args:
            request_id: UUID of request
            status: New status (COMPLETED, BLOCKED, FAILED)
            certificate: W11 certificate if approved
            error_message: Error details if failed
        """
        
        request = self.requests.get(request_id)
        
        if not request:
            raise ValueError(f"Request not found: {request_id}")
        
        request.status = status
        request.certificate = certificate
        request.error_message = error_message
        
        self._save_request(request)
        
        # Log audit event
        action = f"STATUS_{status.value}"
        self._log_audit(action, request_id, 
                       f"Certificate: {certificate.get('certificate_id') if certificate else 'N/A'}")
        
        print(f"[QUEUE] Request {request_id}: {status.value}")
        if certificate:
            print(f"         Certificate: {certificate['certificate_id']}")
            print(f"         Verdict: {certificate['overall_verdict']}")
    
    def get_pending_requests(self) -> List[ExportRequest]:
        """Get all pending requests ready for processing."""
        
        pending = []
        for req in self.requests.values():
            if req.status == RequestStatus.PENDING and not req.is_expired():
                pending.append(req)
        
        # Sort by creation time (oldest first)
        pending.sort(key=lambda r: r.created_at)
        
        return pending
    
    def get_all_requests(self) -> List[Dict]:
        """Get summary of all requests."""
        
        return [req.to_dict() for req in self.requests.values()]
    
    def _find_by_idempotency_key(self, key: str) -> Optional[ExportRequest]:
        """Find request by idempotency key."""
        
        for req in self.requests.values():
            if req.idempotency_key == key:
                return req
        return None
    
    def _save_request(self, request: ExportRequest):
        """Save request to disk for persistence."""
        
        request_file = self.queue_dir / f"{request.request_id}.json"
        with open(request_file, 'w', encoding='utf-8') as f:
            json.dump(request.to_dict(), f, indent=2, ensure_ascii=False)
    
    def _load_queue(self):
        """Load existing requests from disk."""
        
        for request_file in self.queue_dir.glob("*.json"):
            try:
                with open(request_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                request = ExportRequest.from_dict(data)
                self.requests[request.request_id] = request
            except Exception as e:
                print(f"[WARNING] Failed to load {request_file}: {e}")
    
    def _log_audit(self, action: str, request_id: str, message: str):
        """Log audit event for compliance tracking."""
        
        audit_file = self.queue_dir / "audit_log.jsonl"
        
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'request_id': request_id,
            'message': message
        }
        
        with open(audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(audit_entry) + '\n')


def main():
    """Test queue manager functionality."""
    
    print("=" * 80)
    print("EXPORT QUEUE MANAGER - TEST")
    print("=" * 80)
    
    manager = ExportQueueManager()
    
    # Test 1: Submit request
    print("\n[TEST 1] Submitting export request...")
    request_id = manager.submit_request(
        dataset_path="Facebook/kasiaju_1977350892357109/message_1.json",
        data_subject={'name': 'Kasia Ju', 'email': 'kasia@example.com'},
        deadline_hours=72,
        idempotency_key="test_key_001"
    )
    
    # Test 2: Get status
    print("\n[TEST 2] Checking request status...")
    status = manager.get_status(request_id)
    print(f"Status: {status['status']}")
    print(f"Deadline: {status['deadline_at']}")
    print(f"Time remaining: {status['time_remaining']}")
    
    # Test 3: Try duplicate submission (should fail)
    print("\n[TEST 3] Testing idempotency (duplicate prevention)...")
    try:
        manager.submit_request(
            dataset_path="Facebook/kasiaju_1977350892357109/message_1.json",
            data_subject={'name': 'Kasia Ju', 'email': 'kasia@example.com'},
            idempotency_key="test_key_001"  # Same key
        )
        print("❌ FAIL: Duplicate request was accepted!")
    except ValueError as e:
        print(f"✅ PASS: Duplicate blocked - {str(e)}")
    
    # Test 4: Get pending requests
    print("\n[TEST 4] Getting pending requests...")
    pending = manager.get_pending_requests()
    print(f"Pending requests: {len(pending)}")
    
    # Test 5: Update status
    print("\n[TEST 5] Simulating completion...")
    mock_certificate = {
        'certificate_id': 'cert_test_123',
        'overall_verdict': 'APPROVED'
    }
    manager.update_status(request_id, RequestStatus.COMPLETED, mock_certificate)
    
    status = manager.get_status(request_id)
    print(f"Updated status: {status['status']}")
    print(f"Certificate ID: {status['certificate_id']}")
    
    print("\n" + "=" * 80)
    print("QUEUE MANAGER TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
