# SECURITY ADVISORY: Environment Secrets in Repository

**Date:** 2026-05-17  
**Severity:** HIGH  
**Status:** ACTION REQUIRED  

---

## 🚨 Critical Finding

During Phase 5 cleanup review, the following environment secret files were found **tracked in Git**:

```
.env.auth      ← Contains JWT secrets, encryption keys
.env.db        ← Contains database credentials
.env.grafana   ← Contains monitoring credentials
.env.runtime   ← Contains runtime secrets
```

These files contain **actual secrets** (passwords, API keys, tokens) and should **NEVER** be committed to version control.

---

## ✅ Immediate Actions Taken

### 1. Updated `.gitignore`

Added explicit ignore rules for secret files:

```gitignore
# Environment secrets (keep .env.example templates, ignore actual secrets)
!.env.example
.env.auth
.env.db
.env.grafana
.env.runtime
*.key
*.pem
```

### 2. Preserved Safe Files

The following files remain tracked (safe):
- ✅ `.env.example` - Template with placeholder values
- ✅ `.env.auth.sha` - Integrity hash (not the secret itself)
- ✅ `.env.db.sha` - Integrity hash
- ✅ `.env.runtime.sha` - Integrity hash
- ✅ `config/.env.example` - Configuration template

---

## 🔧 Required Operator Actions

### Step 1: Remove Secret Files from Git History

⚠️ **WARNING**: This will rewrite git history. Ensure all team members are notified.

```powershell
# Remove from git tracking (but keep local files)
git rm --cached .env.auth .env.db .env.grafana .env.runtime

# Commit the removal
git commit -m "security: Remove environment secrets from git tracking

Removed actual secret files from version control:
- .env.auth (JWT secrets, encryption keys)
- .env.db (database credentials)
- .env.grafana (monitoring credentials)
- .env.runtime (runtime secrets)

Kept safe artifacts:
- .env.example (template with placeholders)
- *.sha files (integrity hashes)

Updated .gitignore to prevent future accidental commits."

# Push to remote
git push origin feature/day9-operations
```

### Step 2: Verify Removal

```powershell
# Check that files are no longer tracked
git ls-files | Select-String -Pattern "^\.env\.(auth|db|grafana|runtime)$"

# Should return empty result

# Verify .gitignore is working
git check-ignore -v .env.auth
# Should output: .gitignore:XX:.env.auth    .env.auth
```

### Step 3: Rotate Compromised Secrets

Since these secrets were in git history, they should be considered **compromised**:

1. **JWT Secrets** (`.env.auth`)
   - Generate new JWT signing keys
   - Invalidate existing tokens
   - Update `.env.auth` with new values

2. **Database Credentials** (`.env.db`)
   - Change database passwords
   - Update connection strings
   - Revoke old credentials

3. **Grafana Credentials** (`.env.grafana`)
   - Rotate API keys
   - Update authentication tokens

4. **Runtime Secrets** (`.env.runtime`)
   - Review and rotate all contained secrets

### Step 4: Add to Deployment Documentation

Update deployment guide to include:

```markdown
## Security Setup

1. Copy `.env.example` to `.env.auth`, `.env.db`, etc.
2. Fill in actual secrets (never commit these files)
3. Run integrity check: `python scripts/verify_env_integrity.py`
4. Deploy with secrets loaded from environment variables
```

---

## 📋 Prevention Measures

### 1. Pre-commit Hooks

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Prevent committing secret files

SECRET_FILES=".env.auth .env.db .env.grafana .env.runtime"

for file in $SECRET_FILES; do
    if git diff --cached --name-only | grep -q "^$file$"; then
        echo "ERROR: Attempting to commit secret file: $file"
        echo "This file contains sensitive credentials and must not be tracked."
        exit 1
    fi
done
```

### 2. CI/CD Security Scanning

Add to GitHub Actions workflow:

```yaml
- name: Check for secrets in repository
  run: |
    if git ls-files | grep -E '^\.env\.(auth|db|grafana|runtime)$'; then
      echo "::error::Secret files found in repository!"
      exit 1
    fi
```

### 3. Team Training

Ensure all operators understand:
- ✅ `.env.example` files = OK to commit (templates)
- ✅ `.env.*.sha` files = OK to commit (integrity hashes)
- ❌ `.env.auth`, `.env.db`, etc. = NEVER commit (actual secrets)
- ❌ `*.key`, `*.pem` = NEVER commit (private keys)

---

## 🔍 Audit Trail

### Files Found Tracked (INSECURE)

```bash
$ git ls-files | Select-String -Pattern "^\.env\.(auth|db|grafana|runtime)$"

.env.auth      # ← CONTAINS SECRETS
.env.db        # ← CONTAINS SECRETS
.env.grafana   # ← CONTAINS SECRETS
.env.runtime   # ← CONTAINS SECRETS
```

### Files Properly Ignored (SECURE)

```bash
$ git check-ignore -v .env.auth
.gitignore:XX:.env.auth    .env.auth  # ← NOW IGNORED
```

### Safe Files (OK TO TRACK)

```bash
$ git ls-files | Select-String -Pattern "\.env\.(example|sha)"

.env.auth.sha           # ← Integrity hash (safe)
.env.db.sha             # ← Integrity hash (safe)
.env.example            # ← Template (safe)
.env.grafana            # ← Will be ignored after fix
.env.runtime            # ← Will be ignored after fix
.env.runtime.sha        # ← Integrity hash (safe)
config/.env.example     # ← Template (safe)
```

---

## 📊 Risk Assessment

| Risk Factor | Severity | Impact |
|-------------|----------|--------|
| Secrets in git history | HIGH | Anyone with repo access can view secrets |
| Public repository exposure | CRITICAL | If repo becomes public, secrets are leaked |
| Backup/sync services | HIGH | Secrets may sync to cloud backups |
| Developer laptops | MEDIUM | Local clones contain secrets |

**Overall Risk Level:** HIGH - Immediate action required

---

## ✅ Verification Checklist

After completing remediation:

- [ ] Secret files removed from git tracking (`git rm --cached`)
- [ ] `.gitignore` updated to prevent future commits
- [ ] All secrets rotated (JWT, DB, Grafana, Runtime)
- [ ] `.env.example` templates updated with new structure
- [ ] Team members notified of secret rotation
- [ ] Pre-commit hooks installed
- [ ] CI/CD security scanning configured
- [ ] Deployment documentation updated
- [ ] Git history cleaned (optional: `git filter-branch` or BFG Repo-Cleaner)

---

## 🎯 Recommendation

**Immediate Priority:** Remove secret files from git tracking and rotate all compromised credentials.

**Secondary Priority:** Implement pre-commit hooks and CI/CD scanning to prevent recurrence.

**Long-term Priority:** Consider using a secrets management solution (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault) instead of `.env` files.

---

**Classification:** INTERNAL — SECURITY SENSITIVE  
**Distribution:** Operator Nadzorca Wielki Elektronik only  
**Next Review:** After secret rotation complete
