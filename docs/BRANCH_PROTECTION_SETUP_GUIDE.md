# Branch Protection Setup Guide - Constitutional Agent

**Purpose:** Enforce mandatory constitutional compliance checks before merging to main  
**Date:** 2026-05-10  
**Priority:** HIGH (Critical Security Enhancement)  

---

## 🎯 Objective

Configure GitHub branch protection rules to ensure **NO pull request can merge to main** without passing the Constitutional Agent review.

---

## 📋 Step-by-Step Instructions

### Step 1: Navigate to Repository Settings

1. Go to: https://github.com/minaz12345/-p-os
2. Click **"Settings"** tab (top navigation bar)
3. Scroll down left sidebar to **"Code and automation"** section
4. Click **"Branches"**

### Step 2: Add Branch Protection Rule

1. Click **"Add rule"** button
2. In **"Branch name pattern"** field, enter: `main`
3. This will protect the main branch from direct pushes and unverified merges

### Step 3: Configure Protection Rules

Enable the following settings (check these boxes):

#### ✅ **Require a pull request before merging**
- ☑️ Require approvals: **1** (minimum)
- ☑️ Dismiss stale pull request approvals when new commits are pushed
- ☑️ Require review from Code Owners (if CODEOWNERS file exists)

#### ✅ **Require status checks to pass before merging** ⭐ CRITICAL
- ☑️ Require branches to be up to date before merging
- **Search for status check:** Type "Constitutional" or "constitutional"
- **Select:** `Constitutional Review / 🏛️ Constitutional Compliance Check`
- This is the GitHub Actions workflow that runs our Constitutional Agent

#### ✅ **Require conversation resolution before merging**
- Ensures all PR comments are addressed before merge

#### ✅ **Include administrators**
- Even repo admins must follow these rules (no bypass)

### Step 4: Optional Advanced Settings

#### Restrict who can push to matching branches
- Add specific users/teams allowed to push directly (usually none for main)
- Recommended: Leave empty to enforce PR-only workflow

#### Allow force pushes
- ☐ Do NOT enable (prevents history rewriting)

#### Allow deletions
- ☐ Do NOT enable (prevents accidental branch deletion)

### Step 5: Save Configuration

1. Scroll to bottom of page
2. Click **"Create"** or **"Save changes"** button
3. Confirm the rule is active (should show in branch protection rules list)

---

## ✅ Verification Steps

After saving, verify the configuration works:

### Test 1: Attempt Direct Push (Should Fail)
```bash
git checkout main
echo "test" >> test.txt
git add test.txt
git commit -m "test: direct push attempt"
git push origin main
```
**Expected Result:** ❌ Rejected by GitHub (branch protection)

### Test 2: Create PR with Violation (Should Block Merge)
1. Create a PR with `[MODIFIED_WITHOUT_VALIDATION]` marker
2. Wait for Constitutional Agent workflow to complete
3. Verify workflow status shows: **FAILING** 🔴
4. Attempt to merge PR
5. **Expected Result:** ❌ Merge button disabled (status check failed)

### Test 3: Create Legitimate PR (Should Allow Merge)
1. Create a PR with safe, compliant changes
2. Wait for Constitutional Agent workflow to complete
3. Verify workflow status shows: **PASSING** 🟢
4. **Expected Result:** ✅ Merge button enabled (all checks passed)

---

## 🔍 Troubleshooting

### Issue: Status check not appearing in dropdown

**Cause:** Workflow hasn't run yet on this branch

**Solution:**
1. Create a test PR to trigger the workflow
2. Wait for workflow to complete (~19 seconds)
3. Refresh the branch protection settings page
4. The status check should now appear in the search results

### Issue: Workflow shows as "pending" indefinitely

**Cause:** GitHub Actions may be queued or experiencing delays

**Solution:**
1. Check GitHub Actions tab for workflow run status
2. Verify no repository-level Actions restrictions
3. Check organization-level Actions permissions
4. Retry after a few minutes

### Issue: Admins can still bypass protection

**Cause:** "Include administrators" option not enabled

**Solution:**
1. Edit the branch protection rule
2. Enable **"Include administrators"** checkbox
3. Save changes

---

## 📊 Expected Behavior After Configuration

| Scenario | Before Protection | After Protection |
|----------|------------------|------------------|
| Direct push to main | ✅ Allowed | ❌ Blocked |
| PR with constitutional violations | ⚠️ Manual review needed | ❌ Merge blocked automatically |
| PR passing all checks | ✅ Manual merge | ✅ Merge allowed |
| Admin override | ✅ Always possible | ❌ Blocked (if "Include admins" enabled) |
| Force push | ✅ Possible | ❌ Blocked |

---

## 🛡️ Security Impact

### Before Branch Protection
- ❌ Anyone with write access could push directly to main
- ❌ Non-compliant PRs could be merged manually
- ❌ No enforcement of constitutional rules
- ❌ Relied on human diligence (error-prone)

### After Branch Protection
- ✅ All changes must go through PR process
- ✅ Constitutional Agent MUST pass before merge
- ✅ Automated enforcement (deterministic)
- ✅ No bypasses (even for admins, if configured)
- ✅ Cryptographically verified compliance

---

## 📞 Support

If you encounter issues during setup:

1. **GitHub Documentation:** https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches
2. **Repository Admin:** Contact repository owner
3. **Technical Support:** ops@milejczyce.gov.pl

---

## ✅ Completion Checklist

- [ ] Navigated to repository Settings → Branches
- [ ] Created branch protection rule for `main`
- [ ] Enabled "Require status checks to pass"
- [ ] Selected "Constitutional Review / 🏛️ Constitutional Compliance Check"
- [ ] Enabled "Include administrators" (recommended)
- [ ] Saved configuration
- [ ] Verified with test PR (violation → blocked)
- [ ] Verified with test PR (compliant → allowed)
- [ ] Documented configuration in team wiki

---

**Status:** READY FOR EXECUTION  
**Estimated Time:** 5-10 minutes  
**Risk Level:** LOW (reversible - can edit/delete rule anytime)  

**Budowniczy, once this is configured, your Constitutional Agent becomes the GATEKEEPER of the main branch!** 🛡️🏛️
