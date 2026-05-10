# Manual Branch Protection Setup - Constitutional Agent

**Purpose:** Step-by-step manual configuration via GitHub web interface  
**Date:** 2026-05-10  
**Prerequisites:** Admin access to repository  

---

## 🎯 Quick Start (5 Minutes)

### Step 1: Navigate to Settings
1. Go to: **https://github.com/minaz12345/-p-os**
2. Click **"Settings"** tab (top navigation bar)
3. Scroll down left sidebar → **"Code and automation"** section
4. Click **"Branches"**

---

### Step 2: Add Branch Protection Rule

1. Click **"Add rule"** button (green button)
2. In **"Branch name pattern"** field, type: `main`
3. This protects the main branch from direct pushes

---

### Step 3: Configure Required Settings

#### ✅ Section 1: Protect matching branches

Check these boxes:

- ☑️ **Require a pull request before merging**
  - When this is enabled, all commits must be made to a non-default branch and merged via pull requests
  - **Required approvals:** `1`
  - ☑️ Dismiss stale pull request approvals when new commits are pushed
  - ☐ Require review from Code Owners (optional - only if you have CODEOWNERS file)

- ☑️ **Require status checks to pass before merging** ⭐ **CRITICAL**
  - When this is enabled, all required status checks must pass before merging
  - ☑️ **Require branches to be up to date before merging**
  - **Status checks:** Search for "Constitutional" or scroll to find:
    - ✅ Select: `Constitutional Review / 🏛️ Constitutional Compliance Check`
  
  > **Note:** If you don't see this check yet, create a test PR first to trigger the workflow, then come back here.

- ☑️ **Require conversation resolution before merging**
  - All conversations must be resolved before merging

---

#### ✅ Section 2: Additional settings

Check these boxes:

- ☑️ **Include administrators**
  - Even repository admins must follow these rules
  - **This is critical for governance integrity**

- ☐ **Restrict who can push to matching branches**
  - Leave unchecked unless you want specific users/teams only

- ☐ **Allow force pushes** 
  - **DO NOT CHECK** - prevents history rewriting

- ☐ **Allow deletions**
  - **DO NOT CHECK** - prevents accidental branch deletion

- ☑️ **Require linear history**
  - Prevents merge commits, keeps history clean

---

### Step 4: Merge Strategy Settings

At the bottom of the page:

- ☑️ **Allow merge commits** - Enabled
- ☑️ **Allow squash merging** - Enabled  
- ☐ **Allow rebase merging** - Disabled (keeps history cleaner)

---

### Step 5: Save Configuration

1. Scroll to bottom of page
2. Click **"Create"** or **"Save changes"** button
3. You should see confirmation message
4. The rule now appears in the branch protection rules list

---

## ✅ Verification Steps

### Test 1: Verify Protection is Active

1. Try to push directly to main:
   ```bash
   git checkout main
   echo "test" >> test.txt
   git add test.txt
   git commit -m "test: direct push"
   git push origin main
   ```
   
   **Expected Result:** ❌ Rejected by GitHub with error message about branch protection

2. Clean up:
   ```bash
   git reset --hard HEAD~1
   rm test.txt
   ```

### Test 2: Create Test PR

1. Create a feature branch:
   ```bash
   git checkout -b test-protection
   echo "# Test" >> TEST_PROTECTION.md
   git add TEST_PROTECTION.md
   git commit -m "test: verify branch protection"
   git push origin test-protection
   ```

2. Create PR on GitHub:
   - Go to: https://github.com/minaz12345/-p-os/pull/new/test-protection
   - Title: "TEST: Branch Protection Verification"
   - Create pull request

3. Wait for Constitutional Agent workflow (~19 seconds)

4. Verify:
   - ✅ Workflow runs automatically
   - ✅ Status check appears in PR
   - ✅ Merge button shows required checks
   - ✅ Cannot merge until checks pass

5. Clean up:
   ```bash
   git checkout main
   git branch -D test-protection
   git push origin --delete test-protection
   rm TEST_PROTECTION.md
   ```

---

## 🔍 Troubleshooting

### Issue: "Constitutional Review" check not appearing in dropdown

**Cause:** Workflow hasn't run on any PR yet

**Solution:**
1. Create a test PR (any change)
2. Wait for workflow to complete
3. Refresh branch protection settings page
4. The check should now appear in search results

---

### Issue: Workflow shows as "pending" indefinitely

**Cause:** GitHub Actions may be queued or restricted

**Solution:**
1. Check Actions tab: https://github.com/minaz12345/-p-os/actions
2. Verify no organization-level restrictions
3. Check if Actions are enabled in repository settings
4. Retry after a few minutes

---

### Issue: Can still merge without checks passing

**Cause:** "Require status checks to pass" not enabled

**Solution:**
1. Edit branch protection rule
2. Ensure "Require status checks to pass before merging" is checked
3. Verify correct status check is selected
4. Save changes

---

### Issue: Admins can bypass protection

**Cause:** "Include administrators" not checked

**Solution:**
1. Edit branch protection rule
2. Enable "Include administrators" checkbox
3. Save changes

---

## 📊 Expected Behavior After Setup

| Action | Before Protection | After Protection |
|--------|------------------|------------------|
| Direct push to main | ✅ Allowed | ❌ Blocked |
| PR without approval | ⚠️ Can merge | ❌ Blocked |
| PR with failing checks | ⚠️ Can merge | ❌ Blocked |
| PR passing all checks | ✅ Can merge | ✅ Can merge |
| Admin override | ✅ Always works | ❌ Blocked (if "Include admins" enabled) |
| Force push | ✅ Possible | ❌ Blocked |
| Delete branch | ✅ Possible | ❌ Blocked |

---

## 🛡️ Security Impact

### What This Prevents:

❌ Accidental direct pushes to main  
❌ Merging unreviewed code  
❌ Bypassing Constitutional Agent checks  
❌ Schema drift without detection  
❌ Non-compliant changes reaching production  
❌ History rewriting (force pushes)  
❌ Accidental branch deletion  

### What This Enforces:

✅ All changes go through PR process  
✅ Constitutional Agent MUST pass  
✅ Minimum 1 human approval  
✅ Linear, clean git history  
✅ Consistent governance for everyone (including admins)  

---

## 📞 Support

If you encounter issues:

1. **GitHub Documentation:** https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
2. **Repository Admin:** Contact repository owner
3. **Technical Support:** ops@milejczyce.gov.pl

---

## ✅ Completion Checklist

- [ ] Navigated to Settings → Branches
- [ ] Created branch protection rule for `main`
- [ ] Enabled "Require a pull request before merging"
- [ ] Set required approvals to 1
- [ ] Enabled "Require status checks to pass"
- [ ] Selected "Constitutional Review / 🏛️ Constitutional Compliance Check"
- [ ] Enabled "Require branches to be up to date"
- [ ] Enabled "Include administrators"
- [ ] Disabled "Allow force pushes"
- [ ] Disabled "Allow deletions"
- [ ] Enabled "Require linear history"
- [ ] Saved configuration
- [ ] Verified with test PR (violation → blocked)
- [ ] Verified with test PR (compliant → allowed)
- [ ] Documented configuration in team wiki

---

**Status:** READY FOR EXECUTION  
**Estimated Time:** 5-10 minutes  
**Risk Level:** LOW (reversible - can edit/delete rule anytime)  

**Budowniczy, once this is configured, your Constitutional Agent becomes the GATEKEEPER of the main branch!** 🛡️🏛️

()()(())()()(())()()(())()()(())()()
