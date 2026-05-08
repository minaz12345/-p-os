# P-OS Workflow Metrics Collection - Quick Reference

**Purpose:** Collect Constitutional Review workflow performance metrics  
**Frequency:** Monthly (next: 2026-06-07)  
**Agent:** p-os-ops v1.0  

---

## 🚀 QUICK START

### Basic Usage (Default Settings)
```powershell
.\scripts\COLLECT_WORKFLOW_METRICS.ps1
```

This collects metrics from the last 30 days and saves report to `reports/WORKFLOW_METRICS_YYYYMMDD.md`

---

## ⚙️ ADVANCED OPTIONS

### Custom Time Period
```powershell
# Last 60 days
.\scripts\COLLECT_WORKFLOW_METRICS.ps1 -DaysBack 60

# Last 7 days
.\scripts\COLLECT_WORKFLOW_METRICS.ps1 -DaysBack 7
```

### With GitHub Token (Higher Rate Limit)
```powershell
.\scripts\COLLECT_WORKFLOW_METRICS.ps1 -Token "ghp_your_token_here"
```

Or set environment variable:
```powershell
$env:GITHUB_TOKEN = "ghp_your_token_here"
.\scripts\COLLECT_WORKFLOW_METRICS.ps1
```

### Custom Repository
```powershell
.\scripts\COLLECT_WORKFLOW_METRICS.ps1 -RepoOwner "your-org" -RepoName "your-repo"
```

---

## 📊 METRICS COLLECTED

| Metric | Description | Threshold |
|--------|-------------|-----------|
| **Total Workflow** | End-to-end execution time | 300s (5 min) |
| **Schema Drift Detection** | Check 1 duration | 60s |
| **W11 Enforcement Integrity** | Check 2 duration | 60s |
| **Determinism Verification** | Check 3 duration | 60s |
| **Audit Trail Completeness** | Check 4 duration | 60s |
| **Documentation Standards** | Check 5 duration | 120s |
| **Hash Chain Integrity** | Check 6 duration | 60s |

### Percentiles Calculated
- **p50 (Median):** 50% of runs faster than this
- **p95:** 95% of runs faster than this
- **p99:** 99% of runs faster than this (critical for SLA)

---

## 📈 INTERPRETING RESULTS

### ✅ PASS Criteria
- p99 value ≤ threshold
- Success rate ≥ 95%
- No critical errors in logs

### ⚠️ WARNING Signs
- p99 approaching threshold (>80%)
- Success rate < 95%
- Increasing trend in execution times

### ❌ FAIL Conditions
- p99 exceeds threshold
- Success rate < 90%
- Workflow failures > 10%

---

## 🔍 TROUBLESHOOTING

### Issue: "No workflow runs found"
**Solution:** 
- Verify workflow name matches: "Constitutional Review"
- Check repository owner/name parameters
- Ensure workflow has run in specified period

### Issue: "Rate limit exceeded"
**Solution:**
- Use GitHub token with `-Token` parameter
- Unauthenticated limit: 60 req/hr
- Authenticated limit: 5,000 req/hr

### Issue: "Workflow not found"
**Solution:**
- Verify workflow file exists: `.github/workflows/constitutional-review.yml`
- Check workflow is enabled in GitHub Actions
- Confirm workflow name in YAML matches script expectation

---

## 📅 SCHEDULED REVIEWS

| Review Date | Command | Notes |
|-------------|---------|-------|
| 2026-06-07 | `.\scripts\COLLECT_WORKFLOW_METRICS.ps1` | First monthly review |
| 2026-07-07 | `.\scripts\COLLECT_WORKFLOW_METRICS.ps1` | Trend analysis |
| 2026-08-07 | `.\scripts\COLLECT_WORKFLOW_METRICS.ps1` | Quarterly assessment |

---

## 📁 OUTPUT FILES

Reports saved to: `reports/WORKFLOW_METRICS_YYYYMMDD.md`

Example filenames:
- `reports/WORKFLOW_METRICS_20260607.md`
- `reports/WORKFLOW_METRICS_20260707.md`
- `reports/WORKFLOW_METRICS_20260807.md`

---

## 🎯 ACTION ITEMS BASED ON RESULTS

### If All Checks PASS ✅
- Document results in monthly operational review
- Archive report for trend analysis
- Continue monitoring

### If Warnings Detected ⚠️
- Investigate slow checks
- Review recent code changes
- Consider optimization opportunities
- Schedule follow-up review in 1 week

### If Failures Detected ❌
- **Immediate:** Investigate root cause
- Check GitHub Actions logs for errors
- Review resource constraints (CPU, memory)
- Contact ops@milejczyce.gov.pl if needed
- Implement fixes before next review

---

## 📞 SUPPORT CONTACTS

| Issue Type | Contact | Response Time |
|------------|---------|---------------|
| Script errors | ops@milejczyce.gov.pl | <24 hours |
| Performance issues | ops@milejczyce.gov.pl | <24 hours |
| Threshold adjustments | security@milejczyce.gov.pl | <4 hours |
| GitHub API issues | ops@milejczyce.gov.pl | <24 hours |

---

## 🔗 RELATED DOCUMENTATION

- Workflow File: `.github/workflows/constitutional-review.yml`
- Validation Script: `scripts/validate_docs.py`
- Deployment Guide: `scripts/DEPLOYMENT_EXECUTION_PACKAGE.md`
- Operational Handbook: `docs/CHAOS_TESTING_OPERATOR_SCHEDULE.md`

---

**Last Updated:** 2026-05-09  
**Next Review:** 2026-06-07  
**Maintained By:** p-os-ops v1.0  
**Classification:** INTERNAL - OPERATIONAL TOOLING
