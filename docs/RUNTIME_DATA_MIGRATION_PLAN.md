# Runtime Data Migration Plan

**Date**: 2026-05-17  
**Objective**: Move runtime data from `D:\pos7\data\` to `D:\P-OS-DATA\` to reduce repository size from 1.5GB to ~30MB  
**Status**: PLANNED

---

## 📊 **Current State Analysis**

### **Repository Size Breakdown:**
```
Total: 1,494 MB (1.5 GB)

By Directory:
  data/           1,494 MB  (99.5%) ← MUST MOVE
  core/               2.55 MB
  logs/               1.11 MB
  Facebook/           0.83 MB
  scripts/            0.80 MB
  __pycache__/        0.47 MB
  docs/               0.45 MB
  reports/            0.39 MB
  pos/                0.28 MB
  archive/            0.27 MB
  tests/              0.20 MB
  Others:             <0.20 MB

Target after migration: ~30 MB (code + docs only)
```

### **Data Directory Contents:**
```
data/
├── exports/          ~1,485 MB (340 export directories, 4.36MB each) ← RUNTIME DATA
├── backups/          ? MB (database backups) ← RUNTIME DATA
├── snapshots/        ? MB (state snapshots) ← RUNTIME DATA
├── prometheus/       ? MB (metrics TSDB) ← ALREADY MOVED TO D:\P-OS-DATA
├── capsules/         ? MB (archival capsules) ← RUNTIME DATA
├── export_queue/     ? MB (pending exports) ← RUNTIME DATA
├── forensic_export/  ? MB (forensic data) ← RUNTIME DATA
├── temp/             ? MB (temporary files) ← CAN DELETE
├── temp_pg_5433/     ? MB (temp PostgreSQL) ← CAN DELETE
├── emergency_backups/? MB (emergency backups) ← RUNTIME DATA
├── backup_tests/     ? MB (test artifacts) ← CAN DELETE
├── *.db files        ~1 MB (test databases) ← KEEP (tests need them)
└── *.json files      <0.01 MB (test results) ← KEEP (test artifacts)
```

---

## 🎯 **Migration Strategy**

### **Phase 1: Identify What to Move vs Keep**

#### **MOVE to D:\P-OS-DATA (Runtime Data):**
- ✅ `exports/` - GDPR export results (1,485 MB)
- ✅ `backups/` - Database backups
- ✅ `snapshots/` - State snapshots
- ✅ `capsules/` - Archival capsules
- ✅ `export_queue/` - Pending export queue
- ✅ `forensic_export/` - Forensic export data
- ✅ `emergency_backups/` - Emergency backup files
- ✅ `prometheus/` - Already moved (128 MB in D:\P-OS-DATA)

#### **DELETE (Temporary/Cache):**
- 🗑️ `temp/` - Temporary files
- 🗑️ `temp_pg_5433/` - Temporary PostgreSQL data
- 🗑️ `backup_tests/` - Test artifacts (can regenerate)

#### **KEEP in Repository (Test Fixtures):**
- 📦 `*.db` test databases (~1 MB total) - Required for integration tests
- 📦 `*.json` test results (<0.01 MB) - Test artifacts for validation
- 📦 `baselines/` - Test baselines for regression testing

---

## 🔧 **Execution Plan**

### **Step 1: Create Directory Structure in D:\P-OS-DATA**

```powershell
# Create target directories
New-Item -ItemType Directory -Path "D:\P-OS-DATA\exports" -Force
New-Item -ItemType Directory -Path "D:\P-OS-DATA\backups" -Force
New-Item -ItemType Directory -Path "D:\P-OS-DATA\snapshots" -Force
New-Item -ItemType Directory -Path "D:\P-OS-DATA\capsules" -Force
New-Item -ItemType Directory -Path "D:\P-OS-DATA\export_queue" -Force
New-Item -ItemType Directory -Path "D:\P-OS-DATA\forensic_export" -Force
New-Item -ItemType Directory -Path "D:\P-OS-DATA\emergency_backups" -Force

Write-Host "✅ Directory structure created in D:\P-OS-DATA"
```

---

### **Step 2: Move Runtime Data**

```powershell
# Move exports (largest: ~1,485 MB)
Write-Host "Moving exports/..."
Move-Item -Path "D:\pos7\data\exports\*" -Destination "D:\P-OS-DATA\exports\" -Force

# Move backups
Write-Host "Moving backups/..."
Move-Item -Path "D:\pos7\data\backups\*" -Destination "D:\P-OS-DATA\backups\" -Force

# Move snapshots
Write-Host "Moving snapshots/..."
Move-Item -Path "D:\pos7\data\snapshots\*" -Destination "D:\P-OS-DATA\snapshots\" -Force

# Move capsules
Write-Host "Moving capsules/..."
Move-Item -Path "D:\pos7\data\capsules\*" -Destination "D:\P-OS-DATA\capsules\" -Force

# Move export_queue
Write-Host "Moving export_queue/..."
Move-Item -Path "D:\pos7\data\export_queue\*" -Destination "D:\P-OS-DATA\export_queue\" -Force

# Move forensic_export
Write-Host "Moving forensic_export/..."
Move-Item -Path "D:\pos7\data\forensic_export\*" -Destination "D:\P-OS-DATA\forensic_export\" -Force

# Move emergency_backups
Write-Host "Moving emergency_backups/..."
Move-Item -Path "D:\pos7\data\emergency_backups\*" -Destination "D:\P-OS-DATA\emergency_backups\" -Force

Write-Host "✅ Runtime data moved to D:\P-OS-DATA"
```

---

### **Step 3: Delete Temporary Files**

```powershell
# Delete temporary directories
Write-Host "Deleting temp/..."
Remove-Item -Path "D:\pos7\data\temp" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Deleting temp_pg_5433/..."
Remove-Item -Path "D:\pos7\data\temp_pg_5433" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Deleting backup_tests/..."
Remove-Item -Path "D:\pos7\data\backup_tests" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "✅ Temporary files deleted"
```

---

### **Step 4: Update .gitignore**

Add to `.gitignore`:

```gitignore
# ============================================================================
# Runtime Data (stored externally in D:\P-OS-DATA)
# ============================================================================
data/exports/
data/backups/
data/snapshots/
data/capsules/
data/export_queue/
data/forensic_export/
data/emergency_backups/
data/temp/
data/temp_pg_*/

# Keep test fixtures
!data/*.db
!data/*.json
!data/baselines/
```

---

### **Step 5: Update Application Configuration**

Update environment files to point to external data directory:

**.env.runtime** (create or update):
```env
# Runtime Data Directory
P_OS_DATA_DIR=D:\P-OS-DATA

# Export paths
EXPORT_DIR=D:\P-OS-DATA\exports
EXPORT_QUEUE_DIR=D:\P-OS-DATA\export_queue

# Backup paths
BACKUP_DIR=D:\P-OS-DATA\backups
SNAPSHOT_DIR=D:\P-OS-DATA\snapshots

# Capsule archival
CAPSULE_DIR=D:\P-OS-DATA\capsules

# Forensic exports
FORENSIC_EXPORT_DIR=D:\P-OS-DATA\forensic_export

# Emergency backups
EMERGENCY_BACKUP_DIR=D:\P-OS-DATA\emergency_backups

# Prometheus metrics (already configured)
PROMETHEUS_DATA_DIR=D:\P-OS-DATA\prometheus
```

**Update application code** to read these environment variables instead of hardcoded paths.

---

### **Step 6: Verify Migration**

```powershell
# Check new data directory size
$externalSize = (Get-ChildItem D:\P-OS-DATA -Recurse -File | Measure-Object -Property Length -Sum).Sum
Write-Host "External data size: $([math]::Round($externalSize/1MB, 2)) MB"

# Check repository size (should be ~30 MB now)
$repoSize = (Get-ChildItem D:\pos7 -Recurse -File -Exclude @('node_modules', '.git') | Measure-Object -Property Length -Sum).Sum
Write-Host "Repository size: $([math]::Round($repoSize/1MB, 2)) MB"

# Verify test databases still exist
if (Test-Path "D:\pos7\data\noi_core_test.db") {
    Write-Host "✅ Test databases preserved"
} else {
    Write-Host "❌ ERROR: Test databases missing!"
}

# Verify exports moved
$exportCount = (Get-ChildItem D:\P-OS-DATA\exports -Directory).Count
Write-Host "Exports migrated: $exportCount directories"
```

**Expected Output:**
```
External data size: ~1,600 MB
Repository size: ~30 MB
✅ Test databases preserved
Exports migrated: 340 directories
```

---

### **Step 7: Clean Git Cache**

```powershell
# Remove cached data files from git index
git rm -r --cached data/exports/
git rm -r --cached data/backups/
git rm -r --cached data/snapshots/
git rm -r --cached data/capsules/
git rm -r --cached data/export_queue/
git rm -r --cached data/forensic_export/
git rm -r --cached data/emergency_backups/
git rm -r --cached data/temp/
git rm -r --cached data/temp_pg_*/

# Commit .gitignore changes
git add .gitignore .env.runtime
git commit -m "chore: Move runtime data to D:\P-OS-DATA, update .gitignore"

# Verify clean state
git status --short
```

---

## 📊 **Expected Results**

### **Before Migration:**
```
Repository Size: 1,494 MB
├── Code + Docs: ~30 MB (2%)
└── Runtime Data: 1,464 MB (98%)
```

### **After Migration:**
```
Repository Size: ~30 MB (100% code + docs)
External Data: ~1,600 MB (D:\P-OS-DATA)
├── Exports: 1,485 MB
├── Prometheus: 128 MB
├── Backups/Snapshots/Capsules: ~50 MB
└── Other runtime: ~10 MB
```

**Reduction**: 1,464 MB → 30 MB (**98% reduction**)

---

## ⚠️ **Important Notes**

### **What This Changes:**

1. **Git Repository**: Now contains only source code, documentation, and test fixtures
2. **Runtime Data**: All generated data stored externally in `D:\P-OS-DATA`
3. **Backups**: Can backup code (git) and data (D:\P-OS-DATA) separately
4. **Deployment**: Need to configure `P_OS_DATA_DIR` environment variable

### **What This DOES NOT Change:**

1. **Test Suite**: All integration tests still work (test databases kept in repo)
2. **API Functionality**: Exports still work, just stored in different location
3. **GDPR Compliance**: Data integrity maintained, just relocated
4. **Constitutional Governance**: R1-R7 rules still apply

---

## 🔐 **Security Considerations**

### **Backup Strategy:**

```yaml
Code Repository (git):
  - Frequency: Continuous (git push)
  - Location: GitHub private repo
  - Size: ~30 MB
  - Contains: Source code, docs, test fixtures

Runtime Data (D:\P-OS-DATA):
  - Frequency: Daily incremental, weekly full
  - Location: External backup drive / cloud storage
  - Size: ~1.6 GB (growing)
  - Contains: User data, exports, backups, metrics
  - Encryption: REQUIRED (contains personal data)
```

### **Access Control:**

- `D:\pos7\` - Development team access
- `D:\P-OS-DATA\` - Restricted access (only runtime services + backup system)
- Never commit runtime data to git (enforced by .gitignore + pre-commit hooks)

---

## 📝 **Post-Migration Checklist**

- [ ] Directory structure created in `D:\P-OS-DATA`
- [ ] All runtime data moved successfully
- [ ] Temporary files deleted
- [ ] `.gitignore` updated
- [ ] `.env.runtime` created with external paths
- [ ] Application code updated to use `P_OS_DATA_DIR`
- [ ] Tests still pass (verify test databases intact)
- [ ] Git cache cleaned
- [ ] Repository size verified (~30 MB)
- [ ] External data backup configured
- [ ] Documentation updated (README references external data)

---

## 🚀 **Next Steps After Migration**

1. **Update README.md** to document external data directory
2. **Create backup script** for `D:\P-OS-DATA`
3. **Configure monitoring** for external data disk space
4. **Document deployment procedure** with external data configuration
5. **Add health check** to verify `P_OS_DATA_DIR` is accessible

---

**Migration prepared by**: Paweł Nazaruk (Operator Wielki Elektronik)  
**Date**: 2026-05-17  
**Status**: Ready for execution (manual PowerShell sequence required)
