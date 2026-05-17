#!/usr/bin/env python3
"""
Integration Test: W11 Constitutional Validation Gates

Tests that the W11 validator correctly:
1. PASSES valid exports (positive tests)
2. BLOCKS invalid exports (negative/injection tests)

Usage:
    python tests/test_w11_gates.py
"""

import json
import sys
from pathlib import Path
from copy import deepcopy

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from services.w11_validator import W11GateFull


def load_valid_pipeline_results() -> dict:
    """Load known-good pipeline results from Phase 2 test."""
    
    results_path = project_root / "data" / "exports" / "test_integration_20260517" / "pipeline_results.json"
    
    if not results_path.exists():
        print(f"ERROR: Pipeline results not found at {results_path}")
        print("Run Phase 2 integration test first: python tests/test_pipeline_integration.py")
        sys.exit(1)
    
    with open(results_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_r1_immutability_pass():
    """Test R1 passes on valid data."""
    
    print("\n" + "=" * 80)
    print("TEST: R1 Immutability - PASS Scenario")
    print("=" * 80)
    
    results = load_valid_pipeline_results()
    validator = W11GateFull(results, "test_r1_pass")
    
    passed = validator.validate_r1_immutability()
    
    assert passed, "R1 should pass on valid data"
    assert len(validator.violations) == 0, "No violations expected"
    
    print("✅ TEST PASSED: R1 correctly validates intact data")
    return True


def test_r1_immutability_fail_data_loss():
    """Test R1 blocks when messages are lost."""
    
    print("\n" + "=" * 80)
    print("TEST: R1 Immutability - FAIL Scenario (Data Loss)")
    print("=" * 80)
    
    results = load_valid_pipeline_results()
    
    # Inject data loss: reduce metrics count
    results['metrics']['pawel']['message_count'] = 3900  # Lost 10 messages
    
    validator = W11GateFull(results, "test_r1_fail")
    passed = validator.validate_r1_immutability()
    
    assert not passed, "R1 should fail when data is lost"
    assert len(validator.violations) > 0, "Violations should be recorded"
    assert any('R1 VIOLATION' in v for v in validator.violations), "R1 violation message expected"
    
    print("✅ TEST PASSED: R1 correctly detects and blocks data loss")
    print(f"   Violation: {validator.violations[0]}")
    return True


def test_r2_determinism_pass():
    """Test R2 passes when regression validation succeeds."""
    
    print("\n" + "=" * 80)
    print("TEST: R2 Determinism - PASS Scenario")
    print("=" * 80)
    
    results = load_valid_pipeline_results()
    validator = W11GateFull(results, "test_r2_pass")
    
    passed = validator.validate_r2_determinism()
    
    assert passed, "R2 should pass when regression baseline matches"
    
    print("✅ TEST PASSED: R2 correctly validates deterministic output")
    return True


def test_r2_determinism_fail_regression():
    """Test R2 blocks when regression validation fails."""
    
    print("\n" + "=" * 80)
    print("TEST: R2 Determinism - FAIL Scenario (Regression Detected)")
    print("=" * 80)
    
    results = load_valid_pipeline_results()
    
    # Inject regression failure
    results['validation']['passed'] = False
    results['validation']['failures'] = ["total_messages: expected=8779, computed=8780"]
    
    validator = W11GateFull(results, "test_r2_fail")
    passed = validator.validate_r2_determinism()
    
    assert not passed, "R2 should fail when regression detected"
    assert any('R2 VIOLATION' in v for v in validator.violations), "R2 violation message expected"
    
    print("✅ TEST PASSED: R2 correctly detects and blocks non-deterministic results")
    print(f"   Violation: {validator.violations[0]}")
    return True


def test_r3_forensic_continuity_pass():
    """Test R3 passes when all timestamps and hash chain present."""
    
    print("\n" + "=" * 80)
    print("TEST: R3 Forensic Continuity - PASS Scenario")
    print("=" * 80)
    
    results = load_valid_pipeline_results()
    validator = W11GateFull(results, "test_r3_pass")
    
    passed = validator.validate_r3_forensic_continuity()
    
    assert passed, "R3 should pass with complete timestamps and hash chain"
    
    print("✅ TEST PASSED: R3 correctly validates forensic continuity")
    return True


def test_r4_w11_boundaries_pass():
    """Test R4 passes when all stages executed with ASCII_PL enforcement."""
    
    print("\n" + "=" * 80)
    print("TEST: R4 W11 Boundaries - PASS Scenario")
    print("=" * 80)
    
    results = load_valid_pipeline_results()
    validator = W11GateFull(results, "test_r4_pass")
    
    passed = validator.validate_r4_w11_boundaries()
    
    assert passed, "R4 should pass when no bypass attempts detected"
    
    print("✅ TEST PASSED: R4 correctly validates W11 boundary enforcement")
    return True


def test_r4_w11_boundaries_fail_bypass():
    """Test R4 blocks when encoding method is bypassed."""
    
    print("\n" + "=" * 80)
    print("TEST: R4 W11 Boundaries - FAIL Scenario (Encoding Bypass)")
    print("=" * 80)
    
    results = load_valid_pipeline_results()
    
    # Inject bypass: change encoding method
    results['raw']['encoding_method'] = 'heuristic_normalization_v0.1'
    
    validator = W11GateFull(results, "test_r4_fail")
    passed = validator.validate_r4_w11_boundaries()
    
    assert not passed, "R4 should fail when non-standard encoding used"
    assert any('R4 VIOLATION' in v for v in validator.violations), "R4 violation message expected"
    
    print("✅ TEST PASSED: R4 correctly detects and blocks encoding bypass")
    print(f"   Violation: {validator.violations[0]}")
    return True


def test_r5_replay_integrity_pass():
    """Test R5 passes when baseline match confirmed."""
    
    print("\n" + "=" * 80)
    print("TEST: R5 Replay Integrity - PASS Scenario")
    print("=" * 80)
    
    results = load_valid_pipeline_results()
    validator = W11GateFull(results, "test_r5_pass")
    
    passed = validator.validate_r5_replay_integrity()
    
    assert passed, "R5 should pass when replay integrity verified"
    
    print("✅ TEST PASSED: R5 correctly validates replay integrity")
    return True


def test_r6_executable_manifest_pass():
    """Test R6 passes when all result sections present."""
    
    print("\n" + "=" * 80)
    print("TEST: R6 Executable Manifest - PASS Scenario")
    print("=" * 80)
    
    results = load_valid_pipeline_results()
    validator = W11GateFull(results, "test_r6_pass")
    
    passed = validator.validate_r6_executable_manifest()
    
    assert passed, "R6 should pass when all sections present"
    
    print("✅ TEST PASSED: R6 correctly validates manifest completeness")
    return True


def test_r6_executable_manifest_fail_missing():
    """Test R6 blocks when result sections missing."""
    
    print("\n" + "=" * 80)
    print("TEST: R6 Executable Manifest - FAIL Scenario (Missing Sections)")
    print("=" * 80)
    
    results = load_valid_pipeline_results()
    
    # Remove semantic section
    del results['semantic']
    
    validator = W11GateFull(results, "test_r6_fail")
    passed = validator.validate_r6_executable_manifest()
    
    assert not passed, "R6 should fail when sections missing"
    assert any('R6 VIOLATION' in v for v in validator.violations), "R6 violation message expected"
    
    print("✅ TEST PASSED: R6 correctly detects and blocks incomplete manifests")
    print(f"   Violation: {validator.violations[0]}")
    return True


def test_r7_context_minimization_pass():
    """Test R7 passes when only scoped data included."""
    
    print("\n" + "=" * 80)
    print("TEST: R7 Context Minimization - PASS Scenario")
    print("=" * 80)
    
    results = load_valid_pipeline_results()
    validator = W11GateFull(results, "test_r7_pass")
    
    passed = validator.validate_r7_context_minimization()
    
    assert passed, "R7 should pass with properly scoped data"
    
    print("✅ TEST PASSED: R7 correctly validates context minimization")
    return True


def test_all_rules_full_pass():
    """Test complete W11 validation on valid export."""
    
    print("\n" + "=" * 80)
    print("TEST: Full W11 Validation - PASS Scenario (All Rules)")
    print("=" * 80)
    
    results = load_valid_pipeline_results()
    validator = W11GateFull(results, "test_full_pass")
    
    certificate = validator.validate_all_rules()
    
    assert certificate['overall_verdict'] == 'APPROVED', "Export should be approved"
    assert certificate['next_action'] == 'PROCEED_TO_PACKAGING', "Should proceed to packaging"
    
    # Verify all rules passed
    for rule, status in certificate['w11_validation'].items():
        assert status == 'PASS', f"{rule} should pass"
    
    print("\n✅ TEST PASSED: All W11 gates correctly validate compliant export")
    print(f"   Certificate ID: {certificate['certificate_id']}")
    return True


def test_all_rules_full_fail_multiple_violations():
    """Test complete W11 validation blocks export with multiple violations."""
    
    print("\n" + "=" * 80)
    print("TEST: Full W11 Validation - FAIL Scenario (Multiple Violations)")
    print("=" * 80)
    
    results = load_valid_pipeline_results()
    
    # Inject multiple violations
    results['metrics']['pawel']['message_count'] = 3900  # R1 violation
    results['validation']['passed'] = False  # R2 violation
    results['raw']['encoding_method'] = 'manual_override'  # R4 violation
    
    validator = W11GateFull(results, "test_full_fail")
    certificate = validator.validate_all_rules()
    
    assert certificate['overall_verdict'] == 'BLOCKED', "Export should be blocked"
    assert certificate['next_action'] == 'BLOCK_EXPORT_AND_ALERT', "Should block and alert"
    assert len(certificate['violations']) >= 3, "Multiple violations should be detected"
    
    print(f"\n✅ TEST PASSED: W11 correctly blocks export with {len(certificate['violations'])} violations")
    print("   Violations detected:")
    for violation in certificate['violations'][:3]:
        print(f"     - {violation}")
    return True


def main():
    """Run all W11 gate tests."""
    
    print("=" * 80)
    print("W11 CONSTITUTIONAL VALIDATION GATES - INTEGRATION TEST SUITE")
    print("=" * 80)
    print()
    print("Testing both positive (pass) and negative (fail) scenarios...")
    print()
    
    tests = [
        ("R1 Immutability (PASS)", test_r1_immutability_pass),
        ("R1 Immutability (FAIL - Data Loss)", test_r1_immutability_fail_data_loss),
        ("R2 Determinism (PASS)", test_r2_determinism_pass),
        ("R2 Determinism (FAIL - Regression)", test_r2_determinism_fail_regression),
        ("R3 Forensic Continuity (PASS)", test_r3_forensic_continuity_pass),
        ("R4 W11 Boundaries (PASS)", test_r4_w11_boundaries_pass),
        ("R4 W11 Boundaries (FAIL - Bypass)", test_r4_w11_boundaries_fail_bypass),
        ("R5 Replay Integrity (PASS)", test_r5_replay_integrity_pass),
        ("R6 Executable Manifest (PASS)", test_r6_executable_manifest_pass),
        ("R6 Executable Manifest (FAIL - Missing)", test_r6_executable_manifest_fail_missing),
        ("R7 Context Minimization (PASS)", test_r7_context_minimization_pass),
        ("Full W11 Validation (PASS)", test_all_rules_full_pass),
        ("Full W11 Validation (FAIL - Multiple)", test_all_rules_full_fail_multiple_violations),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ TEST FAILED: {test_name}")
            print(f"   Error: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"\n❌ TEST ERROR: {test_name}")
            print(f"   Exception: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()
    
    if failed == 0:
        print("✅ ALL W11 GATE TESTS PASSED")
        print()
        print("Constitutional validation engine is production-ready.")
        print("System correctly:")
        print("  ✓ Approves compliant exports")
        print("  ✓ Blocks exports with constitutional violations")
        print("  ✓ Detects data loss, bypass attempts, and regression failures")
        print("  ✓ Maintains audit trail for all decisions")
        return True
    else:
        print(f"❌ {failed} TEST(S) FAILED")
        print()
        print("W11 validator requires fixes before deployment.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
