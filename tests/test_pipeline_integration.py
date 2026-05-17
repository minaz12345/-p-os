#!/usr/bin/env python3
"""
Integration Test: Relationship Dataset Through Complete Pipeline

Tests that the 8,779-message relationship dataset passes through
the entire forensic export pipeline with zero regression failures.

Usage:
    python tests/test_pipeline_integration.py
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from services.forensic_export_pipeline import ForensicExportPipeline


def test_relationship_dataset_pipeline():
    """
    Integration test: Run complete pipeline on relationship dataset
    
    Expected results (from tests/fixtures/relationship_expected_metrics.json):
    - Total messages: 8,779
    - Paweł messages: 3,910
    - Kasia messages: 4,869
    - HIGH_INTENSITY weeks: 6
    - All W11 gates pass
    - Zero regression failures
    """
    
    print("=" * 80)
    print("INTEGRATION TEST: Relationship Dataset Pipeline")
    print("=" * 80)
    print()
    
    # Setup
    dataset_path = project_root / "Facebook" / "kasiaju_1977350892357109" / "message_1.json"
    request_id = "test_integration_20260517"
    
    if not dataset_path.exists():
        print(f"❌ FAIL: Dataset not found at {dataset_path}")
        print("   Please ensure Facebook conversation data is available.")
        return False
    
    print(f"Dataset: {dataset_path}")
    print(f"Request ID: {request_id}")
    print()
    
    # Load expected metrics
    fixture_path = project_root / "tests" / "fixtures" / "relationship_expected_metrics.json"
    with open(fixture_path, 'r', encoding='utf-8') as f:
        fixture = json.load(f)
    
    expected_metrics = fixture['expected_metrics']
    expected_timeline = fixture['expected_timeline']
    expected_semantic = fixture['expected_semantic']
    
    print("Expected Metrics (from fixture):")
    print(f"  - Total messages: {expected_metrics['total_messages']}")
    print(f"  - Paweł messages: {expected_metrics['pawel_messages']}")
    print(f"  - Kasia messages: {expected_metrics['kasia_messages']}")
    print(f"  - Questions total: {expected_semantic['questions_total']}")
    print(f"  - HIGH_INTENSITY weeks: {expected_timeline['high_intensity_weeks']}")
    print(f"  - Third-party entity: {expected_semantic.get('third_party_entity_candidate', 'N/A')}")
    print()
    
    # Run pipeline
    print("Running pipeline...")
    print("-" * 80)
    
    try:
        pipeline = ForensicExportPipeline(dataset_path, request_id)
        results = pipeline.run_pipeline()
    except Exception as e:
        print(f"\n❌ PIPELINE FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # Validate results
    print("=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print()
    
    all_passed = True
    
    # Check 1: Total messages
    computed_total = results['raw']['total_messages']
    expected_total = expected_metrics['total_messages']
    if computed_total == expected_total:
        print(f"✓ Total messages: {computed_total} (expected {expected_total})")
    else:
        print(f"✗ Total messages: {computed_total} (expected {expected_total}) ❌")
        all_passed = False
    
    # Check 2: Per-person message counts
    pawel_count = results['metrics']['pawel']['message_count']
    kasia_count = results['metrics']['kasia']['message_count']
    
    if pawel_count == expected_metrics['pawel_messages']:
        print(f"✓ Paweł messages: {pawel_count} (expected {expected_metrics['pawel_messages']})")
    else:
        print(f"✗ Paweł messages: {pawel_count} (expected {expected_metrics['pawel_messages']}) ❌")
        all_passed = False
    
    if kasia_count == expected_metrics['kasia_messages']:
        print(f"✓ Kasia messages: {kasia_count} (expected {expected_metrics['kasia_messages']})")
    else:
        print(f"✗ Kasia messages: {kasia_count} (expected {expected_metrics['kasia_messages']}) ❌")
        all_passed = False
    
    # Check 3: Questions count (warning if not exact - heuristic-based)
    questions_total = results['metrics']['pawel']['questions_count'] + results['metrics']['kasia']['questions_count']
    if questions_total == expected_semantic['questions_total']:
        print(f"✓ Questions total: {questions_total} (expected {expected_semantic['questions_total']})")
    else:
        diff = abs(questions_total - expected_semantic['questions_total'])
        pct_diff = (diff / expected_semantic['questions_total']) * 100
        if pct_diff < 15:  # Allow up to 15% variance for heuristic-based question detection
            print(f"⚠ Questions total: {questions_total} (expected {expected_semantic['questions_total']}, {pct_diff:.1f}% diff)")
            print(f"   Note: Question detection uses simple '?' heuristic - may miss edge cases")
        else:
            print(f"✗ Questions total: {questions_total} (expected {expected_semantic['questions_total']}) ❌")
            all_passed = False
    
    # Check 4: Timeline phases
    high_intensity_weeks = len(results['timeline']['high_intensity_weeks'])
    if high_intensity_weeks == expected_timeline['high_intensity_weeks']:
        print(f"✓ HIGH_INTENSITY weeks: {high_intensity_weeks} (expected {expected_timeline['high_intensity_weeks']})")
    else:
        print(f"✗ HIGH_INTENSITY weeks: {high_intensity_weeks} (expected {expected_timeline['high_intensity_weeks']}) ❌")
        all_passed = False
    
    # Check 5: ASCII_PL normalization
    normalized_count = results['raw']['normalized_count']
    if normalized_count == expected_total:
        print(f"✓ ASCII_PL normalization: {normalized_count}/{expected_total} messages normalized")
    else:
        print(f"✗ ASCII_PL normalization: {normalized_count}/{expected_total} messages normalized ❌")
        all_passed = False
    
    # Check 6: Encoding method
    encoding_method = results['raw']['encoding_method']
    if encoding_method == 'ASCII_PL_v1.0':
        print(f"✓ Encoding method: {encoding_method}")
    else:
        print(f"✗ Encoding method: {encoding_method} (expected ASCII_PL_v1.0) ❌")
        all_passed = False
    
    # Check 7: Regression validation
    if results['validation']['passed']:
        print(f"✓ Regression validation: PASSED (zero tolerance)")
    else:
        print(f"✗ Regression validation: FAILED")
        for failure in results['validation']['failures']:
            print(f"    - {failure}")
        all_passed = False
    
    # Check 8: Semantic extraction
    entities = [e['entity'] for e in results['semantic']['entities']]
    expected_entity = expected_semantic.get('third_party_entity_candidate')
    if expected_entity and expected_entity in entities:
        print(f"✓ Third-party entity detected: '{expected_entity}' found in top entities")
    elif expected_entity:
        print(f"⚠ Third-party entity '{expected_entity}' not in top 10 entities (may still be present)")
    
    print()
    
    # Final verdict
    print("=" * 80)
    if all_passed:
        print("✅ INTEGRATION TEST PASSED")
        print("=" * 80)
        print()
        print("All critical metrics match expected values with zero tolerance.")
        print("Pipeline is ready for Phase 3 (W11 Gate) implementation.")
        print()
        print(f"Results saved to: {pipeline.output_dir}")
        return True
    else:
        print("❌ INTEGRATION TEST FAILED")
        print("=" * 80)
        print()
        print("One or more critical metrics do not match expected values.")
        print("Debug required before proceeding to Phase 3.")
        print()
        return False


if __name__ == "__main__":
    success = test_relationship_dataset_pipeline()
    sys.exit(0 if success else 1)
