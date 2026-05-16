# P-OS v7.5 - PostgreSQL Password Recovery Procedure
# EMERGENCY: Current pos_admin password is unknown/lost

## Problem Statement
- Multiple password rotation attempts failed
- No working credentials available for pos_admin user
- Gateway MVP cannot connect to database
- System is currently inoperable for DB operations

## Solution: Temporary Trust Authentication

### Step 1: Backup pg_hba.conf
```powershell
Copy-Item "C:\Program Files\PostgreSQL\18\data\pg_hba.conf" "C:\Program Files\PostgreSQL\18\data\pg_hba.conf.backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
```

### Step 2: Edit pg_hba.conf
Open `C:\Program Files\PostgreSQL\18\data\pg_hba.conf` in Notepad (as Administrator)

Find these lines:
```
local   all             all                                     scram-sha-256
host    all             all             127.0.0.1/32            scram-sha-256
host    all             all             ::1/128                 scram-sha-256
```

Change `scram-sha-256` to `trust`:
```
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
```

Save the file.

### Step 3: Restart PostgreSQL Service
```powershell
Restart-Service postgresql-x64-18
Start-Sleep -Seconds 3
```

### Step 4: Connect Without Password and Reset It
```powershell
# Generate a new secure password
$NEW_PASSWORD = -join ((65..90) + (97..122) + (48..57) + (33..33) + (63..63) | Get-Random -Count 48 | ForEach-Object {[char]$_})

# Connect without password (trust mode) and set new password
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h 127.0.0.1 -U pos_admin -d pos_operational -c "ALTER USER pos_admin WITH PASSWORD '$NEW_PASSWORD';"

# Verify it works
$env:PGPASSWORD = $NEW_PASSWORD
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h 127.0.0.1 -U pos_admin -d pos_operational -c "SELECT current_user, now();"
Remove-Item Env:\PGPASSWORD

Write-Host "New password: $NEW_PASSWORD" -ForegroundColor Green
Write-Host "SAVE THIS PASSWORD SECURELY!" -ForegroundColor Yellow
```

### Step 5: Update .env.db
Manually edit `D:\pos7\.env.db` and replace:
- `POSTGRESQL_PASSWORD=` with the new password from Step 4
- `POSTGRESQL_URI=` with the URI containing the new password (URL-encode special chars if needed)

Or use PowerShell:
```powershell
$NEW_PASSWORD = "<PASTE_NEW_PASSWORD_HERE>"
$env_content = Get-Content "D:\pos7\.env.db"
$env_content = $env_content -replace '^POSTGRESQL_PASSWORD=.*', "POSTGRESQL_PASSWORD=$NEW_PASSWORD"

# URL-encode the password for URI
$encoded_pass = [System.Web.HttpUtility]::UrlEncode($NEW_PASSWORD)
$env_content = $env_content -replace '^POSTGRESQL_URI=postgresql://pos_admin:.*@localhost', "POSTGRESQL_URI=postgresql://pos_admin:${encoded_pass}@localhost"

$env_content | Set-Content "D:\pos7\.env.db" -Encoding UTF8
```

### Step 6: Restore pg_hba.conf Security
Open `C:\Program Files\PostgreSQL\18\data\pg_hba.conf` again

Change `trust` back to `scram-sha-256`:
```
local   all             all                                     scram-sha-256
host    all             all             127.0.0.1/32            scram-sha-256
host    all             all             ::1/128                 scram-sha-256
```

Save the file.

### Step 7: Restart PostgreSQL Again
```powershell
Restart-Service postgresql-x64-18
Start-Sleep -Seconds 3
```

### Step 8: Test Connection with New Password
```powershell
$env:PGPASSWORD = "<NEW_PASSWORD_FROM_STEP_4>"
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h 127.0.0.1 -U pos_admin -d pos_operational -c "SELECT current_user, now();"
Remove-Item Env:\PGPASSWORD
```

### Step 9: Restart Gateway MVP
```powershell
cd D:\pos7
python -m uvicorn gateway_mvp:app --host 0.0.0.0 --port 8443 --ssl-keyfile D:\pos7\certs\key.pem --ssl-certfile D:\pos7\certs\cert.pem
```

### Step 10: Verify Gateway Health
```powershell
Invoke-RestMethod -Uri https://localhost:8443/health -SkipCertificateCheck | ConvertTo-Json
```

## Security Notes
- The trust authentication window should be as short as possible (< 5 minutes)
- Never leave pg_hba.conf in trust mode in production
- Store the new password in a secure vault or password manager
- Consider enabling pg_hba.conf file monitoring/alerting

## Alternative: Use rotate_password.py Script
After completing Steps 1-4, you can use the secure rotation script:
```powershell
python scripts/secure_rotate_password.py
```
But you'll need to enter the password you set in Step 4 as the "current" password.
