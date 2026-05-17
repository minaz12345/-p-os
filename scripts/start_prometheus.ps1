# P-OS Prometheus Startup Script
# Purpose: Start Prometheus with TSDB data in external directory
# Architecture: SOURCE CODE ≠ RUNTIME DATA

param(
    [Parameter(Mandatory=$false)]
    [string]$ConfigFile = "D:\pos7\config\prometheus.yml",
    
    [Parameter(Mandatory=$false)]
    [string]$DataPath = "D:\P-OS-DATA\prometheus",
    
    [Parameter(Mandatory=$false)]
    [int]$Port = 9090
)

Write-Host "=== Starting P-OS Prometheus ===" -ForegroundColor Cyan
Write-Host "Config: $ConfigFile"
Write-Host "Data Path: $DataPath"
Write-Host "Port: $Port`n"

# Verify config exists
if (-not (Test-Path $ConfigFile)) {
    Write-Host "❌ Config file not found: $ConfigFile" -ForegroundColor Red
    exit 1
}

# Create data directory if it doesn't exist
if (-not (Test-Path $DataPath)) {
    Write-Host "Creating data directory: $DataPath"
    New-Item -ItemType Directory -Path $DataPath -Force | Out-Null
}

# Check if Prometheus is already running
$existing = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "⚠️  Prometheus already running on port $Port (PID: $($existing.OwningProcess))" -ForegroundColor Yellow
    Write-Host "Use: Stop-Process -Id $($existing.OwningProcess) -Force to stop it first"
    exit 1
}

# Find prometheus.exe
$prometheusExe = Get-Command prometheus.exe -ErrorAction SilentlyContinue
if (-not $prometheusExe) {
    Write-Host "❌ prometheus.exe not found in PATH" -ForegroundColor Red
    Write-Host "Install Prometheus from: https://prometheus.io/download/"
    Write-Host "Or add to PATH: C:\path\to\prometheus"
    exit 1
}

Write-Host "Starting Prometheus..." -ForegroundColor Green
Write-Host "Executable: $($prometheusExe.Source)`n"

# Start Prometheus with external TSDB path
Start-Process -FilePath $prometheusExe.Source `
    -ArgumentList @(
        "--config.file=$ConfigFile",
        "--storage.tsdb.path=$DataPath",
        "--web.listen-address=:$Port",
        "--log.level=info"
    ) `
    -NoNewWindow `
    -PassThru

Write-Host "`n✅ Prometheus started" -ForegroundColor Green
Write-Host "Web UI: http://localhost:$Port"
Write-Host "Health: http://localhost:$Port/-/healthy"
Write-Host "Metrics: http://localhost:$Port/metrics`n"

Write-Host "To stop Prometheus:" -ForegroundColor Yellow
Write-Host "Get-Process prometheus | Stop-Process -Force`n"
