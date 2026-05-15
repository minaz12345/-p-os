# Constitutional Review - Operator Quick Reference

**Status:** 🧊 FROZEN (Observation Phase)  
**Last Updated:** 2026-05-11  

---

## How It Works

The constitutional review workflow automatically runs on every PR to `main` or `release/*` branches.

### What Gets Checked (R1-R7)

| Rule | Check | Severity |
|------|-------|----------|
| **R1a** | Schema drift detection (SQL + migration docs) | ❌ FAIL if violated |
| **R1b** | Document immutability (CERTIFIED_IMMUTABLE markers) | ❌ FAIL if violated |
| **R2** | Determinism verification (no random.* without seed) | ⚠️ WARNING if detected |
| **R3** | Audit trail completeness (emit_audit calls) | ⚠️ WARNING if missing |
| **R4** | W11 boundaries (contract file exists) | ⚠️ WARNING if missing |
| **R5** | Hash chain integrity (drift detection SQL) | ⚠️ WARNING if missing |
| **R6** | Documentation standards (validate_docs.py) | ⚠️ WARNING if fails |
| **R7** | Context minimization (no docs >1MB) | ⚠️ WARNING if oversized |

---

## Verdict Meanings

### ✅ PASS
- **Meaning:** Clean compliance state
- **Action:** Merge allowed immediately
- **Frequency Goal:** >80% of PRs

### ⚠️ CONDITIONAL_PASS
- **Meaning:** Historical warnings exist, but this PR doesn't make it worse
- **Action:** Merge allowed, but schedule remediation
- **Report Shows:** List of historical warnings + confirmation no new violations
- **Frequency Goal:** <20% of PRs (if higher, technical debt accumulating)

### ❌ FAIL
- **Meaning:** New violation introduced
- **Action:** Merge blocked until fixed
- **Report Shows:** Specific violations that must be resolved
- **Frequency Goal:** Rare (indicates active governance)

---

## Where to Find Reports

### 1. PR Comments (Automatic)
- Constitutional review report is posted as a comment on every PR
- Shows verdict, violations, warnings, and recommendations
- **No action needed** - just read the comment

### 2. GitHub Actions Tab
- Full workflow run details
- Click on "Constitutional Compliance Check" job
- View console output for detailed check results

### 3. Artifacts
- Download `constitutional_review_report.md` from workflow artifacts
- Contains formatted markdown report
- Useful for sharing or archival

---

## Common Scenarios

### Scenario 1: PR Gets CONDITIONAL_PASS
```
⚠️ CONDITIONAL PASS - Historical debt detected, merge allowed

Historical Warnings:
- R2: Found 3 potential non-deterministic patterns
- R3: Found 2 state changes without audit

This PR:
- ✅ Does not introduce new violations
- ⚠️ Does not resolve existing debt

Recommendation: Merge now, schedule remediation sprint for historical warnings.
```

**What to do:**
1. ✅ Safe to merge
2. 📝 Note the historical warnings
3. 🗓️ Schedule time to fix them (not urgent, but don't ignore forever)

---

### Scenario 2: PR Gets FAIL
```
❌ FAIL - Blocking merge

Violations:
- R1: SQL changes without migration document

Fix Required:
1. Create migration document in docs/migrations/
2. Document schema changes
3. Resubmit PR
```

**What to do:**
1. ❌ Cannot merge yet
2. 🔧 Fix the specific violation(s) listed
3. 🔄 Push fix to PR branch
4. ⏳ Wait for re-check (automatic)

---

### Scenario 3: False Positive
If you believe a warning is incorrect:

1. **Don't override** - there's no override mechanism by design
2. **Document it** - note the false positive in PR discussion
3. **Report it** - mention in weekly ops sync
4. **Track it** - if false positive rate >5%, we'll adjust the rule

---

## Troubleshooting

### Workflow Not Running
**Check:**
- Is PR targeting `main` or `release/*`?
- Are there workflow errors in Actions tab?
- Contact: ops@milejczyce.gov.pl

### PR Comment Not Appearing
**Check:**
- Workflow completed successfully?
- Check Actions tab for errors in "Post Constitutional Report to PR" step
- Comment should appear within 1 minute of workflow completion

### Confused About Verdict
**Read:**
- The PR comment explains everything
- Look at "Violations" section (❌ = must fix)
- Look at "Warnings" section (⚠️ = awareness only)
- If still unclear, ask in PR discussion

---

## Branch Protection Verification

To verify constitutional review cannot be bypassed:

```powershell
.\scripts\verify_branch_protection.ps1
```

**Run this:**
- Monthly (operational hygiene)
- After any GitHub settings changes
- If you suspect configuration issues

**Expected output:**
```
✅ Constitutional Compliance Check - ENABLED
✅ Force pushes: BLOCKED
✅ Branch deletion: BLOCKED
✅ BRANCH PROTECTION VERIFIED
```

---

## Key Principles

1. **No Overrides:** By design, there's no way to bypass constitutional review
2. **Transparency:** All checks and verdicts are visible in PR comments
3. **Awareness Without Blockade:** CONDITIONAL_PASS allows progress while tracking debt
4. **Simplicity:** If it's confusing, that's a bug - report it
5. **Trust Through Consistency:** Same rules for everyone, including admins

---

## Contacts

- **Technical Issues:** ops@milejczyce.gov.pl
- **Architectural Questions:** Review `docs/CONSTITUTIONAL_REVIEW_STABILIZATION_DECISION.md`
- **False Positives:** Document in PR, discuss in weekly ops sync

---

## Observation Phase Metrics (Being Tracked)

We're measuring (but not displaying publicly yet):

- ⏱️ Time from PR open → review complete (goal: <2 min)
- 📊 CONDITIONAL_PASS ratio (goal: <20%)
- ⚠️ False positive rate (goal: <5%)
- 😤 Operator complaints (goal: minimal)
- 🔄 Workaround attempts (goal: zero)

If these metrics show problems, we'll adjust. If they're healthy, we maintain the freeze.

---

**Remember:** This system is designed to be **bounded, enforced, and simple**. If it feels otherwise, that's valuable feedback - please share it.

**Status:** 🧊 FROZEN - No new features, observation only  
**Next Evaluation:** 2026-06-08
