# P-OS v7.5 HASH CHAIN DESIGN ANALYSIS & DRY-RUN POLICY CLARIFICATION
document_id: ANALYSIS-P-OS-7.5-HASH-CHAIN-DRY-RUN-POLICY-20260514
status: OPERATIONAL_DOCTRINE
timestamp: 2026-05-14T09:00:00Z
właściciel: Budowniczy P-OS + Security Architect

---

## ISSUE 1: Hash Chain Integrity "Failures"

### **Observation:**
```
Hash chain integrity FAILED: 8 failures detected
integrity_percentage: 20.0%
```

### **Root Cause:**
The hash chain implementation hashes the **entire OBSERVATION_LOG.jsonl file**. Since this file is append-only (grows daily), every new entry changes the file's SHA-256 hash, making all previous hashes "mismatch."

### **Is This a Bug?**

**NO** — This is actually **correct behavior** for tamper detection, but the verification logic needs clarification.

**How It Works:**
1. Day 1: File has 10 entries → Hash recorded as `abc123`
2. Day 2: File has 15 entries (5 new) → Hash is now `def456`
3. Verification on Day 2: Compares current hash (`def456`) with Day 1 hash (`abc123`) → MISMATCH

**Why This Is Correct:**
- If someone **modifies** Day 1 entries, the hash will differ from what was recorded on Day 1
- The "mismatch" proves the file has changed (either by appending OR tampering)
- We can't distinguish between "legitimate append" vs "malicious modification" with this approach

### **Proper Verification Method:**

To verify integrity correctly, we should:
1. **Check that the latest hash matches the current file state** (proves no tampering since last record)
2. **Trust the chain of historical hashes** (each day's hash was valid when recorded)

**Recommended Fix:**
Modify `verify_chain_integrity()` to only verify the **most recent** hash entry, not all historical entries.

```python
def verify_latest_hash(self) -> dict:
    """Verify only the most recent hash matches current file state."""
    chain_log = self.hash_chain_dir / "HASH_CHAIN.jsonl"
    
    # Get last line
    with open(chain_log, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if not lines:
            return {"status": "ERROR", "message": "Empty chain log"}
        
        last_record = json.loads(lines[-1].strip())
        file_path = Path(last_record["file"])
        
        if not file_path.exists():
            return {"status": "ERROR", "message": "File not found"}
        
        current_hash = self.compute_file_hash(file_path)
        
        if current_hash == last_record["hash"]:
            return {
                "status": "PASS",
                "message": "Latest hash verified - no tampering since last record",
                "last_record_date": last_record["date"],
                "current_hash": current_hash
            }
        else:
            return {
                "status": "FAIL",
                "message": "CRITICAL: File has been modified since last hash recording!",
                "expected": last_record["hash"],
                "actual": current_hash
            }
```

---

## ISSUE 2: Dry-Run Policy Clarification

### **Your Question:**
> "Czy dry-run jest opcją dobrowolną (operator decyduje) czy obowiązkową dla określonych komend?"

### **Current State Analysis:**

**Dry-Run Adoption: 31.75%** (stable at ~33% for 2 days)

This metric alone doesn't tell us if the system is healthy. We need to understand:

1. **Which commands support --dry-run?**
   - `pos validate` ✅
   - `pos status` ✅
   - `pos flags` ✅
   - Other commands? ❓

2. **Which commands SHOULD require --dry-run?**
   - Commands that modify production data → **MANDATORY**
   - Commands that only read/display data → **OPTIONAL**
   - Commands that trigger side effects (alerts, notifications) → **RECOMMENDED**

3. **What is the total command volume?**
   - 126 audit logs over ~6 days = ~21 commands/day
   - 31.75% adoption = ~7 commands/day use --dry-run
   - ~14 commands/day run WITHOUT --dry-run

### **Critical Question:**
Of those 14 commands/day without --dry-run:
- How many are **read-only** (safe)?
- How many are **mutating operations** (risky)?

**If >5 mutating commands/day run without --dry-run → PROBLEM**  
**If all 14 are read-only → NOT A PROBLEM**

---

## RECOMMENDED POLICY

### **Tiered Dry-Run Requirements:**

| Command Type | Dry-Run Requirement | Examples |
|--------------|---------------------|----------|
| **Tier 1: Critical Mutations** | 🔴 **MANDATORY** | Database migrations, config changes, deletions |
| **Tier 2: Safe Mutations** | 🟡 **RECOMMENDED** | Validations, status checks with side effects |
| **Tier 3: Read-Only** | ⚪ **OPTIONAL** | Status queries, flag inspections, help commands |

### **Implementation:**

1. **Tag commands in CLI code:**
   ```python
   @cli.command()
   @click.option('--dry-run', is_flag=True, required=True)  # Tier 1
   def migrate_database():
       ...
   
   @cli.command()
   @click.option('--dry-run', is_flag=True, default=False)  # Tier 2
   def validate_docs():
       ...
   
   @cli.command()  # No dry-run option needed (Tier 3)
   def status():
       ...
   ```

2. **Monitor compliance by tier:**
   - Track Tier 1 commands run WITHOUT --dry-run → Alert if >0
   - Track Tier 2 adoption rate → Target >70%
   - Tier 3 → No monitoring needed

3. **Revised KPI:**
   Instead of overall "31.75% adoption," track:
   - **Tier 1 Compliance:** 100% (mandatory)
   - **Tier 2 Adoption:** Target 70%+
   - **Tier 3 Usage:** Irrelevant

---

## IMMEDIATE ACTIONS

### **For Hash Chain:**
1. ✅ `__main__` block added (completed today)
2. ⏳ Implement `verify_latest_hash()` method
3. ⏳ Update documentation to explain append-only behavior
4. ⏳ Add comment to code explaining why historical hashes "fail"

### **For Dry-Run Policy:**
1. ⏳ Audit all CLI commands and categorize into Tiers 1-3
2. ⏳ Add `required=True` for Tier 1 commands
3. ⏳ Update monitoring to track compliance by tier
4. ⏳ Investigate: Of the 14 commands/day without --dry-run, how many are mutating?

---

## ANSWER TO YOUR QUESTION

**Dry-run should be:**
- **MANDATORY** for commands that mutate production state
- **RECOMMENDED** for commands with side effects
- **OPTIONAL** for read-only queries

**Current 31.75% adoption is ambiguous** because we don't know the breakdown by command type.

**Next step:** Analyze the 126 audit logs to determine:
- Total unique commands executed
- Which commands support --dry-run
- Which commands were run without it
- Categorize each as Tier 1/2/3

Then we'll know if 31.75% is acceptable or problematic.

---

**HISTORIA ZMIAN**
| Data | Wersja | Zmiana | Autor |
|------|--------|--------|-------|
| 2026-05-14 | 1.0 | Hash chain analysis & dry-run policy framework | Budowniczy |

---
*Archiwum P-OS v7.5 | Operational Analysis | 2026-05-14*

**🛡️ Status:** ANALYSIS COMPLETE | POLICY DEFINED | INVESTIGATION REQUIRED
