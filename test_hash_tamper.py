"""Hash Chain Tamper Test"""
import sys
sys.path.insert(0, 'D:/pos7')

from core.observability.hash_chain import HashChainVerifier
from pathlib import Path

print("=== HASH CHAIN TAMPER TEST ===\n")

# Step 1: Baseline
print("Step 1: Baseline hash chain status")
v = HashChainVerifier()
result = v.verify_chain_integrity()
print(f"Status: {result['status']}")
print(f"Verified: {result['verified_count']}/{result['total_records']}")
print(f"Integrity: {result['integrity_percentage']}%\n")

# Step 2: Tamper
print("Step 2: Tampering with OBSERVATION_LOG.jsonl (adding 'X')")
log_file = Path("D:/pos7/pos/OBSERVATION_LOG.jsonl")
original_content = log_file.read_text(encoding="utf-8")
tampered_content = original_content + "X"
log_file.write_text(tampered_content, encoding="utf-8")
print("Tampered!\n")

# Step 3: Detect tampering
print("Step 3: Verify chain detects tampering")
result = v.verify_chain_integrity()
print(f"Status: {result['status']}")
print(f"Failures: {result['failed_count']}")
if result['failures']:
    print(f"Failure details:")
    for failure in result['failures'][:1]:  # Show first failure
        print(f"  - Date: {failure.get('date', 'N/A')}")
        print(f"  - Expected: {failure.get('expected', 'N/A')[:20]}...")
        print(f"  - Actual: {failure.get('actual', 'N/A')[:20]}...")
print()

# Step 4: Restore
print("Step 4: Restoring original content")
log_file.write_text(original_content, encoding="utf-8")
print("Restored!\n")

# Step 5: Verify recovery
print("Step 5: Verify chain recovers")
result = v.verify_chain_integrity()
print(f"Status: {result['status']}")
print(f"Integrity: {result['integrity_percentage']}%")
print(f"\n{'='*60}")
print("TEST COMPLETE")
