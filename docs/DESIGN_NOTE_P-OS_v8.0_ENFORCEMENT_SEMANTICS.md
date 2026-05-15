# P-OS v8.0 DESIGN NOTE: Constitutional Enforcement Semantics

**Document ID:** DESIGN-NOTE-P-OS-v8.0-ENFORCEMENT-SEMANTICS  
**Date:** 2026-05-11  
**Status:** PROPOSED FOR v8.0  
**Priority:** HIGH - Operational Viability  

---

## CONTEXT

During v7.5 quiet operations period, Constitutional Agent detected historical violations (`[MODIFIED_WITHOUT_VALIDATION]` markers) in repository files unrelated to current PR #8. This caused PR rejection despite PR files being compliant.

**Root Cause:** Agent performs full repository scan and blocks on ANY violation, regardless of whether violation is:
- Historical (pre-existing)
- In files unrelated to PR changes
- Known and documented

---

## PROBLEM STATEMENT

Current enforcement model: **FULL REPOSITORY PURITY**

```text
Any historical violation → Blocks ALL new PRs
```

**Consequences:**
1. **Constitutional Deadlock Risk** - System becomes too pure to operate
2. **Operator Fatigue** - Fighting history instead of building future
3. **Progress Paralysis** - Every PR must fix all historical issues
4. **Governance Theater** - Temptation to bypass increases over time

---

## PROPOSED SOLUTION: HYBRID ENFORCEMENT MODEL

### Core Principle

```text
FULL SCAN + SCOPED ENFORCEMENT
```

Agent continues scanning entire repository for awareness, BUT enforcement scope is limited to:

### What SHOULD Block PRs (New Violations)

1. **Violations in Modified Files** - Changes introduce new non-compliance
2. **Health Score Degradation** - PR makes system less compliant overall
3. **Immutable Section Mutations** - Unauthorized changes to certified sections
4. **Schema Drift Without Migration** - Database changes without documentation

### What Should NOT Block PRs (Historical Violations)

1. **Pre-existing Violations** - Known issues in unchanged files
2. **Documented Exceptions** - Violations with approved waiver
3. **Legacy Artifacts** - Historical files marked for eventual cleanup

### Reporting Strategy

Agent should report ALL violations but categorize them:

```yaml
Violations:
  New (Blocking):
    - List of new violations in changed files
    - Action required: Fix before merge
  
  Historical (Non-blocking):
    - List of pre-existing violations
    - Action recommended: Schedule cleanup in dedicated PR
    - Does NOT block current PR merge
```

---

## IMPLEMENTATION APPROACH

### Phase 1: Violation Classification (v8.0-alpha)

Add metadata tracking to distinguish:
- `violation_type: NEW | HISTORICAL`
- `introduced_in_commit: <commit_hash>`
- `first_detected: <timestamp>`
- `status: ACTIVE | DOCUMENTED_EXCEPTION | SCHEDULED_FIX`

### Phase 2: Scoped Enforcement Logic (v8.0-beta)

Modify Constitutional Agent workflow:

```powershell
# Current logic (v7.5):
if ($violations.Count -gt 0) {
  $verdict = "FAIL"
}

# Proposed logic (v8.0):
$newViolations = $violations | Where-Object { $_.type -eq "NEW" }
$historicalViolations = $violations | Where-Object { $_.type -eq "HISTORICAL" }

if ($newViolations.Count -gt 0) {
  $verdict = "FAIL"
  $report.NewViolations = $newViolations
} else {
  $verdict = "PASS"
  $report.HistoricalViolations = $historicalViolations
  $report.Recommendation = "Consider addressing historical violations in dedicated cleanup PR"
}
```

### Phase 3: Violation Registry (v8.0-rc)

Create `.constitutional/violation_registry.json` to track:
- Known historical violations
- Exception approvals
- Cleanup schedules
- Accountability assignments

---

## BENEFITS

### Operational
- ✅ Prevents constitutional deadlock
- ✅ Reduces operator fatigue
- ✅ Enables forward progress while maintaining awareness
- ✅ Clear separation between blocking vs advisory issues

### Governance
- ✅ Maintains full repository visibility (scan everything)
- ✅ Precise enforcement semantics (block only what matters)
- ✅ Audit trail of all violations (historical + new)
- ✅ Structured path to remediation (scheduled cleanup PRs)

### Philosophical
- ✅ Aligns with boundedness doctrine (precise, not expansive)
- ✅ Preserves sovereignty (no force merges needed)
- ✅ Supports quiet operations (reduced friction)
- ✅ Demonstrates maturity (nuanced enforcement)

---

## RISKS & MITIGATIONS

### Risk 1: Hidden Violations Accumulate
**Mitigation:** Monthly "Constitutional Hygiene" PRs to address historical violations

### Risk 2: Operators Ignore Historical Issues
**Mitigation:** Dashboard showing violation trend over time; alert if count increases

### Risk 3: Complexity Creep in Agent Logic
**Mitigation:** Keep classification simple (NEW vs HISTORICAL); avoid over-engineering

---

## DECISION REQUIRED

**Question for v8.0 planning:** Should P-OS adopt hybrid enforcement model?

**Options:**
1. **Adopt Hybrid Model** (Recommended) - Balanced approach
2. **Maintain Full Purity** - Current v7.5 behavior
3. **Switch to Delta-Only** - Scan only changed files

**Recommendation:** Option 1 - Hybrid model provides best balance of sovereignty and operational viability.

---

## RELATED DOCUMENTS

- `docs/ARCHIVE_P-OS_LAYER9_BOUNDEDNESS_PHILOSOPHY.md` - Boundedness doctrine
- `.github/workflows/constitutional-review.yml` - Current agent implementation
- PR #8 incident report - Trigger for this design note

---

**Next Review:** 2026-06-10 (end of quiet operations period)  
**Owner:** Budowniczy P-OS  
**Status:** Awaiting v8.0 planning decision
