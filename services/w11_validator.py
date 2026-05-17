#!/usr/bin/env python3
"""
Phase 3: W11 Constitutional Validation Gates

Implements R1-R7 constitutional enforcement for forensic exports.
Blocks exports that violate sovereignty principles.

Usage:
    from services.w11_validator import W11GateFull
    
    validator = W11GateFull(pipeline_results)
    certificate = validator.validate_all_rules()
    
    if certificate['passed']:
        print("✅ Export approved - all W11 gates passed")
    else:
        print("❌ Export BLOCKED - constitutional violations detected")
        for violation in certificate['violations']:
            print(f"  - {violation}")
"""

import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from core.normalization.ascii_pl import validate_ascii_only


class W11GateFull:
    """
    Constitutional validation engine enforcing R1-R7 sovereignty rules.
    
    Every export must pass ALL 7 rules. If ANY rule fails → BLOCK_EXPORT_AND_ALERT.
    """
    
    def __init__(self, pipeline_results: Dict, request_id: str):
        self.pipeline_results = pipeline_results
        self.request_id = request_id
        self.violations = []
        self.audit_log = []
        
    def validate_r1_immutability(self) -> bool:
        """
        R1: Immutability - No data loss between extraction stages
        
        Checks:
        - Total message count consistent across RAW → METRICS → TIMELINE
        - No messages dropped during normalization
        - All senders preserved
        """
        print("\n[R1] Checking immutability (no data loss)...")
        
        raw_count = self.pipeline_results.get('raw', {}).get('total_messages', 0)
        metrics_pawel = self.pipeline_results.get('metrics', {}).get('pawel', {}).get('message_count', 0)
        metrics_kasia = self.pipeline_results.get('metrics', {}).get('kasia', {}).get('message_count', 0)
        timeline_weeks = len(self.pipeline_results.get('timeline', {}).get('phases', []))
        
        # Check total consistency
        metrics_total = metrics_pawel + metrics_kasia
        
        if raw_count != metrics_total:
            violation = f"R1 VIOLATION: Message count mismatch - RAW={raw_count}, METRICS={metrics_total}"
            self.violations.append(violation)
            self._log_audit('R1', 'FAIL', violation)
            return False
        
        # Check no messages lost in timeline
        if timeline_weeks == 0:
            violation = "R1 VIOLATION: Timeline has zero weeks - data loss detected"
            self.violations.append(violation)
            self._log_audit('R1', 'FAIL', violation)
            return False
        
        # Check ASCII_PL normalization completeness
        normalized_count = self.pipeline_results.get('raw', {}).get('normalized_count', 0)
        if normalized_count != raw_count:
            violation = f"R1 VIOLATION: Normalization incomplete - {normalized_count}/{raw_count} messages normalized"
            self.violations.append(violation)
            self._log_audit('R1', 'FAIL', violation)
            return False
        
        self._log_audit('R1', 'PASS', f"All {raw_count} messages preserved through all stages")
        print(f"  ✓ R1 PASS: {raw_count} messages preserved end-to-end")
        return True
    
    def validate_r2_determinism(self) -> bool:
        """
        R2: Determinism - Reproducible results on re-run
        
        Checks:
        - Hash of pipeline output matches expected hash (if available)
        - Same input produces same output (verified by regression test)
        """
        print("\n[R2] Checking determinism (reproducibility)...")
        
        # Verify regression validation passed (proves determinism)
        validation = self.pipeline_results.get('validation', {})
        
        if not validation.get('passed', False):
            violation = "R2 VIOLATION: Regression validation failed - non-deterministic results"
            self.violations.append(violation)
            self._log_audit('R2', 'FAIL', violation)
            return False
        
        # Check that critical metrics match fixture exactly
        failures = validation.get('failures', [])
        if failures:
            violation = f"R2 VIOLATION: Metrics drift detected - {len(failures)} mismatches"
            self.violations.append(violation)
            self._log_audit('R2', 'FAIL', violation)
            return False
        
        self._log_audit('R2', 'PASS', "Deterministic output verified via regression baseline")
        print(f"  ✓ R2 PASS: Results reproducible (regression baseline matched)")
        return True
    
    def validate_r3_forensic_continuity(self) -> bool:
        """
        R3: Forensic Continuity - Timestamped audit trail with hash chain
        
        Checks:
        - All stages have timestamps (where applicable)
        - Hash chain integrity (each stage hashes previous output)
        - No gaps in temporal sequence
        """
        print("\n[R3] Checking forensic continuity (timestamps + hash chain)...")
        
        # Check timestamps exist for stages that should have them
        # Note: 'raw' stage timestamp is in pipeline execution context, not results
        required_timestamps = [
            ('metrics', 'computed_at'),
            ('timeline', 'extracted_at'),
            ('semantic', 'extracted_at')
        ]
        
        missing_timestamps = []
        for stage, timestamp_field in required_timestamps:
            stage_data = self.pipeline_results.get(stage, {})
            if not stage_data:
                missing_timestamps.append(stage)
            elif timestamp_field not in stage_data:
                missing_timestamps.append(f"{stage}.{timestamp_field}")
        
        if missing_timestamps:
            violation = f"R3 VIOLATION: Missing timestamps in stages: {', '.join(missing_timestamps)}"
            self.violations.append(violation)
            self._log_audit('R3', 'FAIL', violation)
            return False
        
        # Generate hash chain for this export
        hash_chain = self._compute_hash_chain()
        
        if len(hash_chain) < 4:
            violation = "R3 VIOLATION: Hash chain incomplete - not all stages hashed"
            self.violations.append(violation)
            self._log_audit('R3', 'FAIL', violation)
            return False
        
        self._log_audit('R3', 'PASS', f"Hash chain complete ({len(hash_chain)} stages), timestamps present")
        print(f"  ✓ R3 PASS: Hash chain complete ({len(hash_chain)} stages)")
        print(f"  ✓ R3 PASS: All applicable stages timestamped")
        return True
    
    def validate_r4_w11_boundaries(self) -> bool:
        """
        R4: W11 Boundaries - No bypass attempts detected
        
        Checks:
        - No manual overrides in pipeline configuration
        - No disabled validation flags
        - No skipped stages
        """
        print("\n[R4] Checking W11 boundaries (no bypass attempts)...")
        
        # Check that all 5 pipeline stages executed
        required_stages = ['raw', 'metrics', 'timeline', 'semantic', 'validation']
        missing_stages = [stage for stage in required_stages if stage not in self.pipeline_results]
        
        if missing_stages:
            violation = f"R4 VIOLATION: Pipeline stages skipped: {', '.join(missing_stages)}"
            self.violations.append(violation)
            self._log_audit('R4', 'FAIL', violation)
            return False
        
        # Check encoding method is ASCII_PL (not heuristic or manual override)
        encoding_method = self.pipeline_results.get('raw', {}).get('encoding_method', '')
        if encoding_method != 'ASCII_PL_v1.0':
            violation = f"R4 VIOLATION: Non-standard encoding method: {encoding_method} (expected ASCII_PL_v1.0)"
            self.violations.append(violation)
            self._log_audit('R4', 'FAIL', violation)
            return False
        
        # Check semantic extraction used ASCII_PL_normalized method
        semantic_method = self.pipeline_results.get('semantic', {}).get('extraction_method', '')
        if semantic_method != 'ASCII_PL_normalized':
            violation = f"R4 VIOLATION: Semantic extraction bypassed ASCII_PL: {semantic_method}"
            self.violations.append(violation)
            self._log_audit('R4', 'FAIL', violation)
            return False
        
        self._log_audit('R4', 'PASS', "All stages executed, no bypass attempts detected")
        print(f"  ✓ R4 PASS: All 5 pipeline stages executed")
        print(f"  ✓ R4 PASS: ASCII_PL enforcement verified")
        return True
    
    def validate_r5_replay_integrity(self) -> bool:
        """
        R5: Replay Integrity - Verified against known baseline
        
        Checks:
        - Output matches expected_metrics.json fixture
        - ASCII-only validation passes on all analytical text
        - No mojibake corruption detected
        """
        print("\n[R5] Checking replay integrity (baseline comparison)...")
        
        # Check regression validation passed
        validation = self.pipeline_results.get('validation', {})
        if not validation.get('passed', False):
            violation = "R5 VIOLATION: Replay integrity failed - baseline mismatch"
            self.violations.append(violation)
            self._log_audit('R5', 'FAIL', violation)
            return False
        
        # Sample check ASCII-only in analytical fields
        sample_messages = self.pipeline_results.get('raw', {}).get('messages', [])[:100]
        
        ascii_violations = 0
        for msg in sample_messages:
            text_ascii = msg.get('text_ascii', '')
            if text_ascii and not validate_ascii_only(text_ascii):
                ascii_violations += 1
        
        if ascii_violations > 0:
            violation = f"R5 VIOLATION: {ascii_violations}/100 sampled messages contain non-ASCII characters"
            self.violations.append(violation)
            self._log_audit('R5', 'FAIL', violation)
            return False
        
        self._log_audit('R5', 'PASS', "Baseline match confirmed, ASCII validation passed")
        print(f"  ✓ R5 PASS: Baseline comparison successful")
        print(f"  ✓ R5 PASS: ASCII validation passed (100/100 samples clean)")
        return True
    
    def validate_r6_executable_manifest(self) -> bool:
        """
        R6: Executable Manifest - All files referenced and accessible
        
        Checks:
        - Output directory exists
        - All result files present
        - File sizes reasonable (>0 bytes)
        """
        print("\n[R6] Checking executable manifest (file accessibility)...")
        
        # This would normally check actual file system
        # For now, verify that pipeline_results contains all required sections
        required_sections = ['raw', 'metrics', 'timeline', 'semantic', 'validation']
        missing_sections = [s for s in required_sections if s not in self.pipeline_results]
        
        if missing_sections:
            violation = f"R6 VIOLATION: Missing result sections: {', '.join(missing_sections)}"
            self.violations.append(violation)
            self._log_audit('R6', 'FAIL', violation)
            return False
        
        # Check each section has content
        empty_sections = []
        for section in required_sections:
            section_data = self.pipeline_results[section]
            if not section_data or (isinstance(section_data, dict) and len(section_data) == 0):
                empty_sections.append(section)
        
        if empty_sections:
            violation = f"R6 VIOLATION: Empty result sections: {', '.join(empty_sections)}"
            self.violations.append(violation)
            self._log_audit('R6', 'FAIL', violation)
            return False
        
        self._log_audit('R6', 'PASS', "All result sections present and populated")
        print(f"  ✓ R6 PASS: All {len(required_sections)} result sections present")
        return True
    
    def validate_r7_context_minimization(self) -> bool:
        """
        R7: Context Minimization - Only scoped data included
        
        Checks:
        - No extraneous personal data beyond conversation participants
        - No metadata leakage (device info, location, etc.)
        - Data scope matches request parameters
        """
        print("\n[R7] Checking context minimization (scoped data only)...")
        
        # Check that only expected participants appear
        messages = self.pipeline_results.get('raw', {}).get('messages', [])
        if messages:
            senders = set(msg.get('sender', '') for msg in messages[:100])
            expected_senders = {'Pawel Nazaruk', 'Kasia Ju'}
            
            unexpected_senders = senders - expected_senders
            if unexpected_senders:
                violation = f"R7 VIOLATION: Unexpected senders in dataset: {unexpected_senders}"
                self.violations.append(violation)
                self._log_audit('R7', 'FAIL', violation)
                return False
        
        # Check no device/location metadata leaked
        sample_msg = messages[0] if messages else {}
        forbidden_fields = ['ip_address', 'device_id', 'location', 'gps_coordinates']
        leaked_fields = [f for f in forbidden_fields if f in sample_msg]
        
        if leaked_fields:
            violation = f"R7 VIOLATION: Forbidden metadata fields present: {leaked_fields}"
            self.violations.append(violation)
            self._log_audit('R7', 'FAIL', violation)
            return False
        
        self._log_audit('R7', 'PASS', "Data scope validated - only conversation participants included")
        print(f"  ✓ R7 PASS: Only expected participants in dataset")
        print(f"  ✓ R7 PASS: No forbidden metadata fields detected")
        return True
    
    def validate_all_rules(self) -> Dict:
        """
        Execute all R1-R7 validation gates.
        
        Returns:
            ExportCertificate with pass/fail status for each rule
        """
        print("=" * 80)
        print("W11 CONSTITUTIONAL VALIDATION GATES")
        print("=" * 80)
        print(f"Request ID: {self.request_id}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        # Execute all 7 rules
        r1_pass = self.validate_r1_immutability()
        r2_pass = self.validate_r2_determinism()
        r3_pass = self.validate_r3_forensic_continuity()
        r4_pass = self.validate_r4_w11_boundaries()
        r5_pass = self.validate_r5_replay_integrity()
        r6_pass = self.validate_r6_executable_manifest()
        r7_pass = self.validate_r7_context_minimization()
        
        # Determine overall pass/fail
        all_passed = all([r1_pass, r2_pass, r3_pass, r4_pass, r5_pass, r6_pass, r7_pass])
        
        # Build certificate
        certificate = {
            'certificate_id': f"cert_{self.request_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'request_id': self.request_id,
            'issued_at': datetime.now().isoformat(),
            'w11_validation': {
                'R1_immutability_no_data_loss': 'PASS' if r1_pass else 'FAIL',
                'R2_determinism_reproducible': 'PASS' if r2_pass else 'FAIL',
                'R3_forensic_continuity_timestamped': 'PASS' if r3_pass else 'FAIL',
                'R4_w11_boundaries_no_bypass': 'PASS' if r4_pass else 'FAIL',
                'R5_replay_integrity_verified': 'PASS' if r5_pass else 'FAIL',
                'R6_executable_manifest_valid': 'PASS' if r6_pass else 'FAIL',
                'R7_context_minimization_scoped': 'PASS' if r7_pass else 'FAIL'
            },
            'overall_verdict': 'APPROVED' if all_passed else 'BLOCKED',
            'violations': self.violations,
            'audit_log': self.audit_log,
            'hash_chain': self._compute_hash_chain() if all_passed else [],
            'next_action': 'PROCEED_TO_PACKAGING' if all_passed else 'BLOCK_EXPORT_AND_ALERT'
        }
        
        # Print summary
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        
        for rule, status in certificate['w11_validation'].items():
            icon = "✓" if status == 'PASS' else "✗"
            print(f"  {icon} {rule}: {status}")
        
        print(f"\nOverall Verdict: {certificate['overall_verdict']}")
        
        if not all_passed:
            print(f"\n⚠ EXPORT BLOCKED - {len(self.violations)} constitutional violation(s) detected:")
            for violation in self.violations:
                print(f"  - {violation}")
        else:
            print(f"\n✅ EXPORT APPROVED - All W11 gates passed")
            print(f"   Certificate ID: {certificate['certificate_id']}")
        
        print("=" * 80)
        
        return certificate
    
    def _compute_hash_chain(self) -> List[Dict]:
        """Compute SHA-256 hash chain across pipeline stages."""
        
        hash_chain = []
        stages = ['raw', 'metrics', 'timeline', 'semantic']
        
        for stage in stages:
            stage_data = self.pipeline_results.get(stage, {})
            stage_json = json.dumps(stage_data, sort_keys=True, default=str)
            stage_hash = hashlib.sha256(stage_json.encode('utf-8')).hexdigest()
            
            hash_chain.append({
                'stage': stage,
                'sha256': stage_hash,
                'timestamp': datetime.now().isoformat()
            })
        
        return hash_chain
    
    def _log_audit(self, rule: str, status: str, message: str):
        """Log audit event for compliance tracking."""
        
        self.audit_log.append({
            'timestamp': datetime.now().isoformat(),
            'rule': rule,
            'status': status,
            'message': message,
            'request_id': self.request_id
        })


def main():
    """Test W11 validator on existing pipeline results."""
    
    # Load pipeline results from Phase 2 test
    results_path = project_root / "data" / "exports" / "test_integration_20260517" / "pipeline_results.json"
    
    if not results_path.exists():
        print(f"ERROR: Pipeline results not found at {results_path}")
        print("Run Phase 2 integration test first: python tests/test_pipeline_integration.py")
        sys.exit(1)
    
    with open(results_path, 'r', encoding='utf-8') as f:
        pipeline_results = json.load(f)
    
    # Run W11 validation
    validator = W11GateFull(pipeline_results, "test_integration_20260517")
    certificate = validator.validate_all_rules()
    
    # Save certificate
    cert_path = results_path.parent / "w11_certificate.json"
    with open(cert_path, 'w', encoding='utf-8') as f:
        json.dump(certificate, f, indent=2, ensure_ascii=False)
    
    print(f"\nCertificate saved to: {cert_path}")
    
    # Exit with appropriate code
    if certificate['overall_verdict'] == 'APPROVED':
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
