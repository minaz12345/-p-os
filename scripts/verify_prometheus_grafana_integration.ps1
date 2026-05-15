# P-OS v7.5 Integration Verification Script (PowerShell)
# Purpose: Validate Prometheus + Grafana pipeline for friction metrics
# Compliance: Read-only checks, no mutations

Write-Host "🛡️  P-OS Integration Verification Starting..." -ForegroundColor Cyan
Write-Host "---------------------------------------------"

# 1. Check Exporter
Write-Host "1. Checking Friction Exporter (Port 8000)..."
try {
    $metrics = Invoke-RestMethod -Uri "http://localhost:8000/metrics" -ErrorAction Stop
    if ($metrics -match "pos_epistemic_health_score") {
        Write-Host "   ✅ Exporter is active and exposing metrics." -ForegroundColor Green
    } else {
        Write-Host "   ❌ Exporter check failed." -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Could not connect to exporter on port 8000." -ForegroundColor Red
}

# 2. Check Prometheus
Write-Host "2. Checking Prometheus (Port 9090)..."
try {
    $targets = Invoke-RestMethod -Uri "http://localhost:9090/api/v1/targets" -ErrorAction Stop
    $frictionTarget = $targets.data.activeTargets | Where-Object { $_.labels.job -eq "pos_friction_metrics" }
    if ($frictionTarget.health -eq "up") {
        Write-Host "   ✅ Prometheus is scraping pos_friction_metrics successfully." -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Prometheus target status: $($frictionTarget.health)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Could not connect to Prometheus on port 9090." -ForegroundColor Red
}

# 3. Check Queryability
Write-Host "3. Checking Metric Queryability..."
try {
    $queryResult = Invoke-RestMethod -Uri "http://localhost:9090/api/v1/query?query=pos_epistemic_health_score" -ErrorAction Stop
    if ($queryResult.data.result.Count -gt 0) {
        $score = $queryResult.data.result[0].value[1]
        Write-Host "   ✅ Epistemic Health Score query successful: $score" -ForegroundColor Green
    } else {
        Write-Host "   ❌ No data returned for health score query." -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Failed to query metrics from Prometheus." -ForegroundColor Red
}

# 4. Check Grafana Health & Datasource
Write-Host "4. Checking Grafana Integration (Port 3000)..."
try {
    # First check if Grafana is alive
    $health = Invoke-RestMethod -Uri "http://localhost:3000/api/health" -ErrorAction Stop
    if ($health.database -eq "ok") {
        Write-Host "   ✅ Grafana server is healthy." -ForegroundColor Green
        
        # Now check datasource using session auth
        $body = @{user="admin"; password="admin"} | ConvertTo-Json
        $session = Invoke-WebRequest -Uri "http://localhost:3000/login" -SessionVariable ws
        Invoke-WebRequest -Uri "http://localhost:3000/login" -WebSession $ws -Method Post -Body $body -ContentType "application/json" | Out-Null
        
        $datasources = Invoke-RestMethod -Uri "http://localhost:3000/api/datasources" -WebSession $ws -ErrorAction Stop
        $ds = $datasources | Where-Object { $_.type -eq "prometheus" }
        if ($ds) {
            Write-Host "   ✅ Prometheus datasource configured in Grafana." -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  No Prometheus datasource found in Grafana." -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ❌ Grafana health check failed." -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Could not connect to Grafana on port 3000. Error: $_" -ForegroundColor Red
}

Write-Host "---------------------------------------------"
Write-Host "🛡️  Verification Complete. Tarcza w górze." -ForegroundColor Cyan
