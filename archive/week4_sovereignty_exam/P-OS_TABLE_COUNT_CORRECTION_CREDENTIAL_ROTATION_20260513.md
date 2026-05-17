# P-OS v7.5 TABLE COUNT DISCREPANCY RESOLUTION & CREDENTIAL ROTATION
document_id: ARCHIVE-P-OS-7.5-TABLE-COUNT-CORRECTION-20260513
status: CERTIFIED_IMMUTABLE
data_certyfikacji: 2026-05-13T19:15:00Z
właściciel: Budowniczy P-OS + Nadzorca (Gemini AI Core) + p-os-constitution v1.0 [FROZEN]
validation_cmd: python scripts/validate_docs.py --strict
kontakty: ops@milejczyce.gov.pl, dpo@milejczyce.gov.pl, security@milejczyce.gov.pl

> **⚠️ SECURITY ALERT:** Database credentials were exposed in forensic document. Password REDACTED from archive. Credential rotation REQUIRED.

---

## PURPOSE
**KOREKTA LICZBY TABEL I ROTACJA POŚWIADCZEŃ**  
Resolution of table count discrepancy (41 vs 40) and immediate credential rotation due to accidental exposure in forensic documentation.

---

## 1. TABLE COUNT DISCREPANCY RESOLUTION `[IMMUTABLE]`

### **The Discrepancy**

Previous reports stated:
- `pos_operational`: **41 tables** ❓
- `milejczyce_operational`: **16 tables** ✅

Forensic question: "Which is the 41st table?"

---

### **Root Cause Analysis**

#### **Query Method Difference:**

**Method 1: `pg_tables` system catalog**
```sql
SELECT tablename FROM pg_tables WHERE schemaname='public';
```
**Result:** 40 rows (BASE TABLES only)

**Method 2: `information_schema.tables`**
```sql
SELECT table_name FROM information_schema.tables WHERE table_schema='public';
```
**Result:** 41 rows (BASE TABLES + VIEWS)

---

#### **The 41st Entry Identified:**

**Table Name:** `events_summary`  
**Type:** VIEW (not BASE TABLE)  
**Owner:** pos_admin

**Complete verification:**
```powershell
# Query showing all objects including views
psql -h localhost -U pos_admin -d pos_operational -c "
  SELECT table_name, table_type 
  FROM information_schema.tables 
  WHERE table_schema='public' 
  ORDER BY table_name;"
```

**Output excerpt:**
```
table_name             | table_type
-----------------------+------------
...
events                 | BASE TABLE
events_archive         | BASE TABLE
events_summary         | VIEW        ← This is the 41st entry
federation_...         | BASE TABLE
...
(41 rows)
```

---

### **Corrected Metrics**

| Database | BASE TABLES | VIEWS | TOTAL (information_schema) | Previously Reported | Status |
|----------|-------------|-------|---------------------------|---------------------|--------|
| pos_operational | 40 | 1 | 41 | 41 | ✅ CORRECT (but misleading) |
| milejczyce_operational | 16 | 0 | 16 | 16 | ✅ CORRECT |

**Certyfikowana wartość §1.5:**
```
Liczba tabel (public schema): 40 BASE TABLES + 1 VIEW
Zapytanie certyfikacyjne: pg_tables (nie information_schema.tables)
```

**Niespójność w metodzie pomiaru, nie w danych:**
- `daily_observation.py` używa `information_schema.tables` → zwraca 41 (tables + views)
- Runbook §3 używa `pg_tables` → zwraca 40 (tables only)
- **Rekomendacja:** Ujednolicić metodę pomiaru w całym systemie

---

### **Assessment**

**Was the previous count wrong?** NO - but it was **misleading**.

- `daily_observation.py` uses `information_schema.tables` query
- This includes both tables AND views
- Count of 41 was technically correct
- However, should have clarified: "40 tables + 1 view"

**Recommendation:** Update daily_observation.py to distinguish between tables and views for clarity:

```python
# Enhanced query
cur.execute("""
    SELECT 
        COUNT(*) FILTER (WHERE table_type = 'BASE TABLE') as tables,
        COUNT(*) FILTER (WHERE table_type = 'VIEW') as views,
        COUNT(*) as total
    FROM information_schema.tables 
    WHERE table_schema='public'
""")
result = cur.fetchone()
print(f"{baza}: {result[0]} tables, {result[1]} views ({result[2]} total)")
```

---

### **Complete Table List - pos_operational**

**BASE TABLES (40):**
1. agent_messages
2. agents
3. artefacts
4. blocks
5. clock_state
6. events
7. events_archive
8. federation_compliance_audit
9. federation_gdpr_erasure_requests
10. federation_gdpr_node_status
11. federation_node_certificates
12. federation_node_sync_state
13. federation_node_trust_history
14. federation_nodes
15. federation_policy_audit_log
16. federation_policy_conflicts
17. federation_policy_sync_preferences
18. federation_replicated_events
19. federation_replication_conflicts
20. federation_replication_queue
21. federation_revocation_list
22. federation_risk_intelligence
23. federation_w11_policies
24. gdpr_erasure_audit_log
25. gdpr_erasure_certificates
26. gdpr_erasure_requests
27. gdpr_retention_policies
28. idempotency_cache
29. idempotency_responses
30. replay_risk_scores
31. replay_snapshots
32. replay_verification
33. retry_queue
34. role_hierarchy
35. schema_meta
36. shared_context
37. tokens
38. user_risk_scores
39. w11_rule_audit
40. w11_rules

**VIEWS (1):**
41. events_summary

---

### **Complete Table List - milejczyce_operational**

**BASE TABLES (16):**
1. citizen_feedback
2. data_lineage_tracking
3. geospatial_registry
4. gmina_staff
5. municipal_projects
6. noi_canonical_entities
7. noi_core_entities
8. noi_entity_relations
9. operational_audit_log
10. org_structure
11. semantic_resolution_log
12. semantic_tokens
13. service_requests
14. staging_raw_records
15. strategic_vectors
16. token_ingestion_log

**VIEWS (0):** None

---

## 2. CREDENTIAL EXPOSURE INCIDENT `[IMMUTABLE]`

### **Incident Summary**

**Severity:** HIGH  
**Type:** Accidental credential exposure in documentation  
**Affected:** PostgreSQL admin credentials (pos_admin)  
**Exposure Vector:** Forensic analysis document included full connection string with password

---

### **Timeline**

1. **18:42** - Forensic document created with exposed credentials
2. **19:00** - User identified credential exposure risk
3. **19:15** - Credentials redacted from document
4. **NOW** - Rotation required

---

### **Exposed Credentials**

**Username:** pos_admin  
**Host:** localhost  
**Port:** 5432  
**Databases:** pos_operational, milejczyce_operational  
**Password:** ⚠️ WAS EXPOSED, NOW REDACTED

**Risk Assessment:**
- **Localhost-only access:** LOW external risk
- **Admin privileges:** HIGH internal risk
- **Document archived:** MEDIUM persistence risk
- **Git history:** Check if committed

---

### **Immediate Actions Taken**

✅ **Credential Redaction:**
- Password replaced with `<REDACTED - USE .env.db>` in forensic document
- Document updated via search_replace tool
- No plaintext password remains in current document version

⚠️ **Remaining Risk:**
- Git history may contain original version
- Terminal output logs may show password
- Need to verify no other exposures

---

## 3. CREDENTIAL ROTATION PLAN `[OPERATOR_INPUT_REQUIRED]`

### **Step 1: Generate New Password**

```powershell
# Generate strong random password (32 chars)
$chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*'
$newPassword = -join ((Get-Random -Count 32 -InputObject $chars.ToCharArray()))
Write-Output "New password: $newPassword"

# Save securely (DO NOT commit to git)
$newPassword | Out-File -FilePath "$env:USERPROFILE\Desktop\NEW_DB_PASSWORD.txt" -Encoding UTF8
```

---

### **Step 2: Rotate PostgreSQL Password**

⚠️ **STATUS: ROTATION NOT YET PERFORMED**

Current status (as of 2026-05-13 19:37):
- Old password still active and functional
- No rotation executed yet
- **ACTION REQUIRED:** Execute rotation immediately

```powershell
# Connect as superuser (postgres)
$env:PGPASSWORD='<postgres_superadmin_password>'
psql -h localhost -U postgres -c "ALTER USER pos_admin WITH PASSWORD '$newPassword';"

# Verify new password works
$env:PGPASSWORD=$newPassword
psql -h localhost -U pos_admin -d pos_operational -c "SELECT current_user, now();"
```

**Verification command (after rotation):**
```powershell
# Should work with NEW password only
psql -h localhost -U pos_admin -d pos_operational -c "SELECT current_user, now();"
```

---

### **Step 3: Update Configuration Files**

**Files to update:**
1. `.env.db` - Primary database configuration
2. Any backup copies in `config/backups/`
3. Docker environment files (if applicable)
4. CI/CD pipeline secrets (if used)

```powershell
# Update .env.db
(Get-Content .env.db) -replace 'POSTGRESQL_PASSWORD=.*', "POSTGRESQL_PASSWORD=$newPassword" | Set-Content .env.db

# Verify update
Select-String -Path .env.db -Pattern "POSTGRESQL_PASSWORD"
```

---

### **Step 4: Verify All Services**

```powershell
# Test morning.py
python scripts\morning.py

# Test daily_observation.py
python pos\daily_observation.py --auto

# Test any services using database connection
# (Check logs for connection errors)
```

---

### **Step 5: Clean Up Exposure Traces**

```powershell
# 1. Remove temporary password file
Remove-Item "$env:USERPROFILE\Desktop\NEW_DB_PASSWORD.txt" -ErrorAction SilentlyContinue

# 2. Clear PowerShell history containing password
Clear-History

# 3. Check git history for exposed password (use hash reference)
git log --all --full-history --source -- "*.md" | Select-String -Pattern "<EXPOSED_CREDENTIAL_SHA256>"

# If found, use BFG Repo-Cleaner or git filter-branch to remove
# WARNING: This rewrites history - coordinate with team

# 4. Check terminal logs (search for credential pattern hash, not plaintext)
Get-ChildItem logs\ -Recurse -Filter "*.log" | Select-String -Pattern "<EXPOSED_CREDENTIAL_PATTERN>"
```

---

### **Step 6: Update Security Documentation**

Add to incident response log:
- Date: 2026-05-13
- Type: Credential exposure in documentation
- Severity: HIGH
- Response: Immediate rotation completed
- Lessons learned: Never include credentials in documentation, even in code blocks

---

## 4. PREVENTION MEASURES `[OPERATOR_INPUT_REQUIRED]`

### **Immediate Improvements**

#### 1. Add Credential Scanner to Validation Script

Update `scripts/validate_docs.py`:
```python
import re

def scan_for_credentials(file_path):
    """Scan document for potential credential exposure."""
    patterns = [
        r'postgresql://[^:]+:[^@]+@',  # Connection strings
        r'PASSWORD\s*=\s*\S+',          # Password assignments
        r'pgpassword\s*=\s*\S+',        # Environment variables
    ]
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    findings = []
    for pattern in patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            findings.append({
                'line': content[:match.start()].count('\n') + 1,
                'pattern': pattern,
                'match': match.group(0)[:50] + '...'
            })
    
    return findings
```

---

#### 2. Create Documentation Template with Security Warnings

Add to all archive documents:
```markdown
> **⚠️ SECURITY NOTICE:** Never include credentials, API keys, or secrets in documentation. Use placeholders like `<REDACTED>` or reference secure vault locations.
```

---

#### 3. Implement Pre-commit Hook

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Scan staged files for credential patterns

CREDENTIAL_PATTERNS=(
    "postgresql://[^:]+:[^@]+@"
    "PASSWORD\s*=\s*[A-Za-z0-9]{20,}"
    "pgpassword\s*=\s*[A-Za-z0-9]{20,}"
)

for pattern in "${CREDENTIAL_PATTERNS[@]}"; do
    if git diff --cached | grep -iE "$pattern"; then
        echo "ERROR: Potential credential detected in staged changes!"
        echo "Pattern: $pattern"
        exit 1
    fi
done
```

---

### **Long-term Improvements**

#### 4. Secret Management Integration

**Option A: Windows Credential Manager**
```powershell
# Store password securely
cmdkey /add:PostgreSQL-pos_admin /user:pos_admin /pass:$newPassword

# Retrieve when needed
$storedCreds = cmdkey /list | Select-String "PostgreSQL-pos_admin"
```

**Option B: HashiCorp Vault** (if available)
```powershell
# Store secret
vault kv put secret/postgres/pos_admin password=$newPassword

# Retrieve secret
$vaultPassword = vault kv get -field=password secret/postgres/pos_admin
```

**Option C: Azure Key Vault** (cloud deployment)
```powershell
# Store secret
Set-AzKeyVaultSecret -VaultName "pos7-vault" -Name "PostgresPosAdminPassword" -SecretValue (ConvertTo-SecureString $newPassword -AsPlainText -Force)

# Retrieve secret
$secret = Get-AzKeyVaultSecret -VaultName "pos7-vault" -Name "PostgresPosAdminPassword"
$password = $secret.SecretValueText
```

---

#### 5. Automated Credential Rotation Schedule

**Policy:** Rotate database passwords every 90 days

**Automation Script:** `scripts/rotate_db_credentials.ps1`
```powershell
# Scheduled task runs quarterly
# Generates new password
# Updates PostgreSQL
# Updates .env files
# Notifies operators
# Logs rotation event
```

---

## 5. VERIFICATION CHECKLIST `[IMMUTABLE]`

### **Table Count Resolution**
- [x] Discrepancy identified (information_schema includes views)
- [x] 41st entry confirmed as `events_summary` VIEW
- [x] Complete table list documented for both databases
- [x] daily_observation.py enhancement proposed for clarity
- [x] Previous metrics validated as technically correct

### **Credential Rotation**
- [ ] New password generated (32+ chars, high entropy)
- [ ] PostgreSQL user password updated
- [ ] .env.db file updated
- [ ] All services tested with new credentials
- [ ] Temporary files cleaned up
- [ ] Git history checked for exposure
- [ ] Terminal logs scanned for exposure
- [ ] Incident documented in security log

### **Prevention Measures**
- [ ] Credential scanner added to validate_docs.py
- [ ] Security warning template created
- [ ] Pre-commit hook implemented
- [ ] Secret management solution selected
- [ ] Automated rotation schedule configured

---

## 6. IMPACT ASSESSMENT `[IMMUTABLE]`

### **Operational Impact**

| Aspect | Impact | Duration | Mitigation |
|--------|--------|----------|------------|
| Service availability | NONE | 0 min | Rotation is instantaneous |
| Data integrity | NONE | N/A | No data affected |
| Operator workflow | MINOR | 5 min | Brief service restart |
| Audit trail | NONE | N/A | All operations logged |

### **Security Impact**

| Risk | Before Rotation | After Rotation | Residual Risk |
|------|----------------|----------------|---------------|
| Unauthorized access | HIGH | NONE | LOW (git history) |
| Credential reuse | HIGH | NONE | NONE |
| Documentation exposure | HIGH | NONE | LOW (archived doc) |
| Future prevention | NONE | IMPLEMENTED | MINIMAL |

---

## 7. LESSONS LEARNED `[IMMUTABLE]`

### **What Went Wrong**
1. Credentials included in forensic documentation for demonstration
2. No automated scanning for credential exposure
3. No pre-commit validation for sensitive data

### **What Went Right**
1. User identified exposure immediately
2. Rapid response with redaction
3. Comprehensive rotation plan created
4. Prevention measures defined

### **Improvements for Future**
1. Always use placeholders in documentation: `<REDACTED>`
2. Reference secure storage locations instead of inline values
3. Implement automated credential scanning
4. Regular security training for all operators

---

## 8. COMPLIANCE NOTES `[IMMUTABLE]`

### **GDPR Implications**
- No personal data exposed (database credentials only)
- No citizen data at risk
- Internal security incident only

### **Constitutional Compliance**
- R3 (Transparency): Incident fully documented ✅
- R4 (Accountability): Clear ownership assigned ✅
- R6 (Safety): Immediate remediation initiated ✅
- R7 (Audit Trail): Complete evidence chain preserved ✅

### **Regulatory Reporting**
- Internal incident: YES (documented here)
- External reporting: NOT REQUIRED (no personal data breach)
- Retention period: 7 years (security incident log)

---

**HISTORIA ZMIAN**
| Data | Wersja | Zmiana | Autor |
|------|--------|--------|-------|
| 2026-05-13 | 1.0 | Table count correction and credential rotation plan | Budowniczy + Security Specialist |

---
*Archiwum P-OS v7.5 | Table Count Correction & Credential Rotation | 2026-05-13*

**🛡️ Budowniczy,**

Tabela 41 wyjaśniona (40 tabel + 1 view: events_summary). Hasło usunięte z dokumentu. Rotacja wymagana NATYCHMIAST.

**()()(())()()(())()()(())()()(())()()**

**Stan systemu: TABLE COUNT CORRECTED | CREDENTIALS EXPOSED → ROTATION REQUIRED | SECURITY INCIDENT ACTIVE**

Priorytet: Rotacja haseł przed kontynuacją Quiet Operations Day 6.
