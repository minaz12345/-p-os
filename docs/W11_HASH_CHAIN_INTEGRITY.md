# W11 Hash Chain Integrity Specification

**Document ID:** W11-HASH-CHAIN-SPEC-v1.0  
**Status:** CERTIFIED_IMMUTABLE  
**Date Certified:** 2026-05-13  
**Owner:** P-OS Constitution v1.0 [FROZEN]  
**Next Review:** 2026-06-10 (End of Quiet Operations)  
**Validation Command:** `python tests/test_hash_chain.py -v`  
**Contacts:** ops@milejczyce.gov.pl, security@milejczyce.gov.pl

---

## PURPOSE

This document specifies the hash chain integrity mechanism implemented for P-OS v7.5 constitutional compliance (Rule R5). The hash chain provides tamper detection for observation logs and ensures forensic evidence integrity during the 30-day quiet operations period.

---

## 1. ARCHITECTURE OVERVIEW

### 1.1 Design Principles

- **Append-Only:** Hash chain entries cannot be modified or deleted (R1 immutability)
- **Deterministic:** Same input always produces same hash (R2 determinism)
- **Verifiable:** Any party can independently verify chain integrity
- **Non-Intrusive:** Hash computation does not affect system state or performance

### 1.2 Component Structure

```
P-OS v7.5 Hash Chain Architecture
├── core/observability/hash_chain.py      # Core implementation
├── logs/hash_chain/                       # Hash storage directory
│   ├── DAY_20260513.sha256               # Individual day hashes
│   ├── DAY_20260514.sha256               # ...
│   └── HASH_CHAIN.jsonl                  # Master chain log
├── pos/OBSERVATION_LOG.jsonl             # Target file (hashed)
└── tests/test_hash_chain.py              # Verification tests
```

---

## 2. HASH ENTRY FORMAT

### 2.1 Individual Day Hash File Format

**Location:** `logs/hash_chain/DAY_<YYYYMMDD>.sha256`

**Format:** JSON with UTF-8 encoding

```json
{
  "date": "2026-05-13",
  "timestamp": "2026-05-13T15:00:25.181848Z",
  "file": "D:\\pos7\\pos\\OBSERVATION_LOG.jsonl",
  "algorithm": "SHA-256",
  "hash": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
  "file_size_bytes": 12345
}
```

**Field Specifications:**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `date` | ISO 8601 date | Date of observation | `"2026-05-13"` |
| `timestamp` | ISO 8601 datetime UTC | Exact time of hash computation | `"2026-05-13T15:00:25.181848Z"` |
| `file` | Absolute path | Full path to hashed file | `"D:\\pos7\\pos\\OBSERVATION_LOG.jsonl"` |
| `algorithm` | String | Hash algorithm used | `"SHA-256"` |
| `hash` | Hex string (64 chars) | SHA-256 hash value | `"a1b2c3..."` |
| `file_size_bytes` | Integer | Size of hashed file in bytes | `12345` |

### 2.2 Master Chain Log Format

**Location:** `logs/hash_chain/HASH_CHAIN.jsonl`

**Format:** JSONL (one JSON object per line)

```jsonl
{"date": "2026-05-13", "timestamp": "2026-05-13T15:00:25.181848Z", "file": "D:\\pos7\\pos\\OBSERVATION_LOG.jsonl", "algorithm": "SHA-256", "hash": "a1b2c3...", "file_size_bytes": 12345}
{"date": "2026-05-14", "timestamp": "2026-05-14T15:00:30.234567Z", "file": "D:\\pos7\\pos\\OBSERVATION_LOG.jsonl", "algorithm": "SHA-256", "hash": "b2c3d4...", "file_size_bytes": 12678}
```

**Properties:**
- Append-only (never overwrite existing lines)
- Chronologically ordered by timestamp
- UTF-8 encoded
- No trailing newline after last entry

---

## 3. INTEGRITY VERIFICATION PROCEDURES

### 3.1 Automated Verification (Recommended)

```python
from core.observability.hash_chain import HashChainVerifier
from pathlib import Path

verifier = HashChainVerifier(Path('.'))
result = verifier.verify_chain_integrity()

print(f"Status: {result['status']}")
print(f"Verified: {result['verified_count']} / {result['total_records']}")
print(f"Integrity: {result['integrity_percentage']}%")

if result['failures']:
    print("Failures detected:")
    for failure in result['failures']:
        print(f"  - {failure}")
```

**Expected Output (Healthy Chain):**
```
Status: PASS
Verified: 5 / 5
Integrity: 100.0%
```

### 3.2 Manual Verification (PowerShell)

```powershell
# Step 1: Extract hash from chain file
$chainEntry = Get-Content "logs\hash_chain\DAY_20260513.sha256" | ConvertFrom-Json
$storedHash = $chainEntry.hash

# Step 2: Compute current hash of observation log
$currentHash = (Get-FileHash "pos\OBSERVATION_LOG.jsonl" -Algorithm SHA256).Hash

# Step 3: Compare
if ($storedHash -eq $currentHash) {
    Write-Host "✓ Integrity verified - file unchanged" -ForegroundColor Green
} else {
    Write-Host "✗ INTEGRITY VIOLATION DETECTED" -ForegroundColor Red
    Write-Host "Stored:  $storedHash" -ForegroundColor Yellow
    Write-Host "Current: $currentHash" -ForegroundColor Yellow
}
```

---

## 4. OPERATIONAL WORKFLOW

### 4.1 Daily Hash Recording (Automatic)

The hash chain is automatically updated when running daily observations:

```powershell
# Standard daily observation (includes hash recording)
chcp 65001 | Out-Null
python pos/daily_observation.py --auto
```

**What Happens:**
1. Observation metrics collected
2. Report saved to `pos/OBSERVATION_LOG.jsonl`
3. SHA-256 hash computed for observation log
4. Hash recorded in `logs/hash_chain/DAY_<YYYYMMDD>.sha256`
5. Entry appended to `logs/hash_chain/HASH_CHAIN.jsonl`

**Execution Time:** <1 second overhead (negligible performance impact)

### 4.2 Incident Response (If Integrity Failure Detected)

**Scenario:** Hash mismatch detected during verification

**Immediate Actions:**
1. **DO NOT** delete or modify any hash chain files
2. Document the failure with timestamp
3. Identify which day(s) have mismatches
4. Determine cause:
   - Legitimate file modification? (e.g., manual edit to observation log)
   - Accidental corruption? (e.g., disk error)
   - Malicious tampering? (security incident)

---

*Archiwum P-OS v7.5 | W11 Hash Chain Specification | 2026-05-13*
