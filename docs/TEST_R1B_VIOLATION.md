# P-OS v7.5 TEST - R1b IMMUTABILITY VIOLATION

```yaml
document_id: TEST-R1B-VIOLATION-20260510
status: CERTIFIED_IMMUTABLE
validation_cmd: python scripts/validate_docs.py --strict
```

## SECTION 1: IMMUTABLE DATA `[MODIFIED_WITHOUT_VALIDATION]`

This section has been modified without proper validation chain.

**Violation Type:** Direct [IMMUTABLE] marker breach  
**Expected Detection:** R1b should flag this  
**Test Purpose:** Verify Constitutional Agent detects immutability violations

---

## SECTION 2: TEST METADATA

- **Created:** 2026-05-10
- **Branch:** toxic-r1b-test-v2
- **Target Rule:** R1b (Document Immutability)
- **Expected Verdict:** FAIL

⚠️ **DO NOT MERGE - Test file only**
