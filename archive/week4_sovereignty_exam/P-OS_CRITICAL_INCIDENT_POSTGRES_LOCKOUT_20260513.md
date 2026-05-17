# P-OS v7.5 CRITICAL INCIDENT: PostgreSQL Lockout
document_id: INCIDENT-P-OS-7.5-POSTGRES-LOCKOUT-20260513
status: CRITICAL - SERVICE DEGRADED
timestamp: 2026-05-13T20:00:00Z
severity: HIGH
owner: Budowniczy P-OS + Database Administrator

---

## EXECUTIVE SUMMARY

**CRITICAL INCIDENT:** PostgreSQL pos_admin account is LOCKED OUT after failed credential rotation attempts.

**Current Status:** 
- ❌ Old password (`MD1Gzyz9uZnTMyp6pMZBUtboe4iSTqgmUpKK3olR4wzH9`) - REJECTED
- ❌ First rotation attempt (`t@KddNQflHKXXEg75QNB2HfUjetl$Dij`) - FAILED (special character issues)
- ❌ All services requiring database access - NON-FUNCTIONAL
- ✅ PostgreSQL service - RUNNING but inaccessible

**Impact:** 
- morning.py - FAILS
- daily_observation.py - FAILS  
- All database operations - BLOCKED
- System health: DEGRADED

---

## TIMELINE

| Time | Event | Status |
|------|-------|--------|
| 18:42 | Credentials exposed in forensic document | 🔴 EXPOSURE |
| 19:00 | Password redacted from document | ✅ MITIGATED |
| 19:37 | Old password verified working | ✅ CONFIRMED |
| 19:45 | First rotation attempt via psql | ⚠️ UNCLEAR |
| 19:50 | Second rotation attempt via Python | ❌ FAILED |
| 19:55 | Connection test with old password | ❌ REJECTED |
| 20:00 | Lockout confirmed | 🔴 CRITICAL |

---

## ROOT CAUSE ANALYSIS

### What Happened:

1. **Initial ALTER USER command executed:**
   ```sql
   ALTER USER pos_admin WITH PASSWORD 't@KddNQflHKXXEg75QNB2HfUjetl$Dij';
   ```
   - Command appeared to execute (no error shown)
   - But special characters (`$`, `@`) may have caused issues

2. **Password change partially applied:**
   - Old password no longer works
   - New password with special characters also fails
   - Likely cause: Shell escaping or encoding issue with special characters

3. **Result:**
   - Account locked with unknown/invalid password state
   - No valid credentials available
   - PostgreSQL service running but inaccessible

---

## IMMEDIATE RECOVERY OPTIONS

### Option 1: Use Windows Authentication (RECOMMENDED)

If PostgreSQL was installed with Windows authentication:

```powershell
# Try connecting with Windows integrated auth
psql -h localhost -U pos_admin -d pos_operational

# Or as postgres superuser
psql -h localhost -U postgres -d postgres
```

---

### Option 2: Reset via pg_hba.conf (Requires Service Restart)

**Step 1: Locate pg_hba.conf**
```powershell
# Find data directory
Get-ChildItem "C:\Program Files\PostgreSQL\" -Recurse -Filter "pg_hba.conf" | Select-Object FullName
```

**Step 2: Temporarily allow trust authentication**
```
# Edit pg_hba.conf, change:
# FROM: host  all  all  127.0.0.1/32  md5
# TO:   host  all  all  127.0.0.1/32  trust
```

**Step 3: Restart PostgreSQL**
```powershell
Restart-Service postgresql-x64-18
```

**Step 4: Connect without password and reset**
```powershell
psql -h localhost -U pos_admin -d pos_operational -c "ALTER USER pos_admin WITH PASSWORD 'NewSecurePassword123!';"
```

**Step 5: Revert pg_hba.conf and restart**
```
# Change back to md5 authentication
Restart-Service postgresql-x64-18
```

---

### Option 3: Use Docker (If Available)

If PostgreSQL is also running in Docker:

```powershell
# Connect to container
docker exec -it <postgres_container_name> psql -U postgres

# Reset password
ALTER USER pos_admin WITH PASSWORD 'NewSecurePassword123!';
```

---

### Option 4: Contact System Administrator

If none of the above work:
- Escalate to IT infrastructure team
- May require full PostgreSQL reinstallation
- Data backup/restore may be necessary

---

## CURRENT SYSTEM STATE

### Services Affected:
- ❌ morning.py - Cannot connect to databases
- ❌ daily_observation.py - Fails on database checks
- ❌ Any CLI commands requiring DB access
- ✅ Neo4j - Still operational (separate system)
- ✅ File system operations - Working

### Data Integrity:
- ✅ No data loss
- ✅ Database files intact
- ❌ Access blocked temporarily

---

## PREVENTION FOR FUTURE

### Lessons Learned:

1. **Never rotate passwords without verified backup access**
   - Always test new password BEFORE invalidating old one
   - Have superuser access ready as fallback

2. **Avoid special characters in initial rotation**
   - Use alphanumeric + limited symbols first
   - Test thoroughly before using complex passwords

3. **Document recovery procedures**
   - pg_hba.conf reset process
   - Superuser credentials stored securely
   - Backup authentication methods

4. **Use proper secret management**
   - Windows Credential Manager
   - HashiCorp Vault
   - Avoid plaintext passwords in scripts

---

## ACTION ITEMS

### Immediate (Next 15 minutes):
- [ ] Attempt Windows authentication connection
- [ ] Locate pg_hba.conf file
- [ ] Prepare trust authentication workaround
- [ ] Generate safe password (alphanumeric + basic symbols)

### Short-term (Next hour):
- [ ] Execute pg_hba.conf reset procedure
- [ ] Reset pos_admin password
- [ ] Update .env.db with new credentials
- [ ] Test all services
- [ ] Verify morning.py and daily_observation.py work

### Medium-term (Today):
- [ ] Document final working password in secure vault
- [ ] Create PowerShell profile with secure credential retrieval
- [ ] Implement automated credential rotation script with proper error handling
- [ ] Test recovery procedure end-to-end

---

## CONTACTS

- **Primary:** Budowniczy P-OS
- **Escalation:** IT Infrastructure Team
- **Emergency:** ops@milejczyce.gov.pl

---

**Status:** 🔴 CRITICAL - Requires immediate intervention to restore database access
