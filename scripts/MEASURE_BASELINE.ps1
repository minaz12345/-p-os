# P-OS Baseline Metrics Collection Script
# Purpose: Establish pre-chaos testing performance baseline
# Date: 2026-05-07
# Usage: .\scripts\MEASURE_BASELINE.ps1
# Output: metrics/baseline_YYYYMMDD_HHMMSS.json

param(
    [Parameter(Mandatory=$false)]
    [string]$OutputDir = "metrics",
    
    [Parameter(Mandatory=$false)]
    [int]$HealthCheckSamples = 10,
    
    [Parameter(Mandatory=$false)]
    [switch]$Verbose = $false
)

# ============================================================================
# CONFIGURATION
# ============================================================================

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$MetricsDir = "$ProjectRoot\$OutputDir"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutputFile = "$MetricsDir\baseline_$Timestamp.json"
$CorrelationId = [guid]::NewGuid().ToString()

# Health check endpoint
$HealthCheckUrl = "https://localhost:8443/health"

# Database connection (from environment)
$PostgresUri = $env:POSTGRESQL_URI

# Color codes
$ColorSuccess = "Green"
$ColorWarning = "Yellow"
$ColorError = "Red"
$ColorInfo = "Cyan"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

function Write-Step {
    param([string]$Message)
    Write-Host "`n=== $Message ===" -ForegroundColor $ColorInfo
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor $ColorSuccess
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor $ColorWarning
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor $ColorError
}

function Test-ServiceAvailability {
    param(
        [string]$ServiceName,
        [scriptblock]$Check
    )
    
    Write-Host "Checking $ServiceName... " -NoNewline
    try {
        $result = & $Check
        if ($result) {
            Write-Success "AVAILABLE"
            return $true
        } else {
            Write-Warning "UNAVAILABLE"
            return $false
        }
    } catch {
        Write-Error-Custom "ERROR: $_"
        return $false
    }
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

function Invoke-BaselineMeasurement {
    Write-Host "`n" -NoNewline
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor $ColorInfo
    Write-Host "║     P-OS v7.5 BASELINE METRICS COLLECTION               ║" -ForegroundColor $ColorInfo
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor $ColorInfo
    Write-Host ""
    Write-Host "Correlation ID: $CorrelationId" -ForegroundColor $ColorInfo
    Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')" -ForegroundColor $ColorInfo
    Write-Host ""
    
    # Create output directory
    if (-not (Test-Path $MetricsDir)) {
        New-Item -ItemType Directory -Force -Path $MetricsDir | Out-Null
        Write-Success "Created metrics directory: $MetricsDir"
    }
    
    $baseline = @{
        timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
        correlation_id = $CorrelationId
        hostname = $env:COMPUTERNAME
        operator = $env:USERNAME
    }
    
    # =========================================================================
    # Metric 1: Health Check Latency
    # =========================================================================
    
    Write-Step "METRIC 1: Health Check Latency ($HealthCheckSamples samples)"
    
    $latencies = @()
    $successCount = 0
    $failureCount = 0
    
    for ($i = 1; $i -le $HealthCheckSamples; $i++) {
        try {
            $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
            $response = Invoke-WebRequest -Uri $HealthCheckUrl -Method GET -SkipCertificateCheck -TimeoutSec 5
            $stopwatch.Stop()
            
            if ($response.StatusCode -eq 200) {
                $latencies += $stopwatch.ElapsedMilliseconds
                $successCount++
                if ($Verbose) {
                    Write-Host "  Sample $i`: $($stopwatch.ElapsedMilliseconds)ms ✅"
                }
            } else {
                $failureCount++
                Write-Warning "  Sample $i`: HTTP $($response.StatusCode)"
            }
        } catch {
            $failureCount++
            Write-Warning "  Sample $i`: $($_.Exception.Message)"
        }
        
        # Small delay between samples to avoid overwhelming service
        Start-Sleep -Milliseconds 100
    }
    
    if ($latencies.Count -gt 0) {
        $sortedLatencies = $latencies | Sort-Object
        $p50Index = [math]::Floor($sortedLatencies.Count * 0.5)
        $p95Index = [math]::Floor($sortedLatencies.Count * 0.95)
        $p99Index = [math]::Floor($sortedLatencies.Count * 0.99)
        
        # Ensure indices are within bounds
        $p50Index = [math]::Min($p50Index, $sortedLatencies.Count - 1)
        $p95Index = [math]::Min($p95Index, $sortedLatencies.Count - 1)
        $p99Index = [math]::Min($p99Index, $sortedLatencies.Count - 1)
        
        $p50 = $sortedLatencies[$p50Index]
        $p95 = $sortedLatencies[$p95Index]
        $p99 = $sortedLatencies[$p99Index]
        $avg = [math]::Round(($latencies | Measure-Object -Average).Average)
        $min = ($latencies | Measure-Object -Minimum).Minimum
        $max = ($latencies | Measure-Object -Maximum).Maximum
        
        Write-Host ""
        Write-Host "Health Check Latency Results:" -ForegroundColor $ColorInfo
        Write-Host "  Samples: $($latencies.Count)/$HealthCheckSamples successful" -ForegroundColor $ColorInfo
        Write-Host "  p50: ${p50}ms" -ForegroundColor $ColorSuccess
        Write-Host "  p95: ${p95}ms" -ForegroundColor $ColorSuccess
        Write-Host "  p99: ${p99}ms" -ForegroundColor $ColorSuccess
        Write-Host "  avg: ${avg}ms" -ForegroundColor $ColorInfo
        Write-Host "  min: ${min}ms / max: ${max}ms" -ForegroundColor $ColorInfo
        
        $baseline.health_check_latency_ms = @{
            p50 = $p50
            p95 = $p95
            p99 = $p99
            average = $avg
            min = $min
            max = $max
            samples_total = $HealthCheckSamples
            samples_successful = $successCount
            samples_failed = $failureCount
        }
    } else {
        Write-Error-Custom "Health check failed all samples!"
        $baseline.health_check_latency_ms = @{
            error = "All samples failed"
            samples_total = $HealthCheckSamples
            samples_successful = 0
            samples_failed = $failureCount
        }
    }
    
    # =========================================================================
    # Metric 2: Gateway Memory Usage
    # =========================================================================
    
    Write-Step "METRIC 2: API Gateway Memory Usage"
    
    try {
        # Find Python process running uvicorn
        $gatewayProcess = Get-Process -Name python -ErrorAction SilentlyContinue | 
            Where-Object { 
                try {
                    $_.CommandLine -match "uvicorn"
                } catch {
                    $false
                }
            } | Select-Object -First 1
        
        if ($gatewayProcess) {
            $memBytes = $gatewayProcess.WorkingSet64
            $memMB = [math]::Round($memBytes / 1MB, 2)
            $memGB = [math]::Round($memBytes / 1GB, 3)
            
            Write-Host "Gateway Process Found:" -ForegroundColor $ColorInfo
            Write-Host "  PID: $($gatewayProcess.Id)" -ForegroundColor $ColorInfo
            Write-Host "  Memory: ${memMB} MB (${memGB} GB)" -ForegroundColor $ColorSuccess
            Write-Host "  CPU: $($gatewayProcess.CPU) seconds" -ForegroundColor $ColorInfo
            Write-Host "  Threads: $($gatewayProcess.Threads.Count)" -ForegroundColor $ColorInfo
            
            $baseline.gateway_memory = @{
                pid = $gatewayProcess.Id
                memory_mb = $memMB
                memory_gb = $memGB
                cpu_seconds = $gatewayProcess.CPU
                thread_count = $gatewayProcess.Threads.Count
                process_name = $gatewayProcess.ProcessName
            }
        } else {
            Write-Warning "Gateway process not found (is it running?)"
            $baseline.gateway_memory = @{
                error = "Process not found"
                status = "stopped"
            }
        }
    } catch {
        Write-Error-Custom "Failed to measure gateway memory: $_"
        $baseline.gateway_memory = @{
            error = $_.Exception.Message
        }
    }
    
    # =========================================================================
    # Metric 3: Database Size
    # =========================================================================
    
    Write-Step "METRIC 3: PostgreSQL Database Size"
    
    if ($PostgresUri) {
        try {
            # Extract database name from URI
            $dbName = ($PostgresUri -split '/')[-1] -split '\?' | Select-Object -First 1
            
            $dbSizeQuery = @"
SELECT 
    pg_database.datname AS database_name,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size_pretty,
    pg_database_size(pg_database.datname) AS size_bytes
FROM pg_database
WHERE datname = '$dbName';
"@
            
            # Execute query using psql
            $psqlOutput = psql $PostgresUri -t -A -c $dbSizeQuery 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                $parts = $psqlOutput -split '\|'
                if ($parts.Count -ge 3) {
                    $dbSizePretty = $parts[1].Trim()
                    $dbSizeBytes = [long]$parts[2].Trim()
                    $dbSizeMB = [math]::Round($dbSizeBytes / 1MB, 2)
                    $dbSizeGB = [math]::Round($dbSizeBytes / 1GB, 3)
                    
                    Write-Host "Database: $dbName" -ForegroundColor $ColorInfo
                    Write-Host "  Size: $dbSizePretty ($dbSizeMB MB / $dbSizeGB GB)" -ForegroundColor $ColorSuccess
                    
                    $baseline.database_size = @{
                        database_name = $dbName
                        size_pretty = $dbSizePretty
                        size_bytes = $dbSizeBytes
                        size_mb = $dbSizeMB
                        size_gb = $dbSizeGB
                    }
                    
                    # Save to text file for easy reference
                    $dbSizeFile = "$MetricsDir\baseline_db_size.txt"
                    "Database: $dbName" | Out-File $dbSizeFile -Encoding UTF8
                    "Size: $dbSizePretty ($dbSizeMB MB)" | Out-File $dbSizeFile -Append -Encoding UTF8
                    "Measured: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')" | Out-File $dbSizeFile -Append -Encoding UTF8
                    
                    Write-Success "Database size saved to: $dbSizeFile"
                } else {
                    Write-Warning "Unexpected query output format"
                    $baseline.database_size = @{
                        error = "Query output parsing failed"
                        raw_output = $psqlOutput
                    }
                }
            } else {
                Write-Error-Custom "psql command failed (exit code: $LASTEXITCODE)"
                $baseline.database_size = @{
                    error = "psql execution failed"
                    exit_code = $LASTEXITCODE
                }
            }
        } catch {
            Write-Error-Custom "Failed to measure database size: $_"
            $baseline.database_size = @{
                error = $_.Exception.Message
            }
        }
    } else {
        Write-Warning "POSTGRESQL_URI environment variable not set"
        $baseline.database_size = @{
            error = "Environment variable POSTGRESQL_URI not configured"
        }
    }
    
    # =========================================================================
    # Metric 4: Active Flags Status
    # =========================================================================
    
    Write-Step "METRIC 4: W11 Active Flags"
    
    $flagsDir = "$ProjectRoot\flags"
    if (Test-Path $flagsDir) {
        $activeFlags = Get-ChildItem -Path $flagsDir -Filter "*.flag" -ErrorAction SilentlyContinue
        $flagCount = $activeFlags.Count
        
        Write-Host "Active Flags: $flagCount" -ForegroundColor $(if ($flagCount -eq 0) { $ColorSuccess } else { $ColorWarning })
        
        if ($flagCount -gt 0) {
            Write-Host "Flag Files:" -ForegroundColor $ColorInfo
            foreach ($flag in $activeFlags) {
                Write-Host "  - $($flag.Name)" -ForegroundColor $ColorWarning
            }
        } else {
            Write-Success "No active flags (HEALTHY state)"
        }
        
        $baseline.w11_flags = @{
            active_count = $flagCount
            expected_count = 0
            status = $(if ($flagCount -eq 0) { "healthy" } else { "degraded" })
            flag_files = ($activeFlags | ForEach-Object { $_.Name })
        }
    } else {
        Write-Warning "Flags directory not found: $flagsDir"
        $baseline.w11_flags = @{
            error = "Flags directory not found"
            path = $flagsDir
        }
    }
    
    # =========================================================================
    # Metric 5: Port Listening Status
    # =========================================================================
    
    Write-Step "METRIC 5: Network Port Status"
    
    $portsToCheck = @(8443, 5432, 7474, 7687)  # HTTPS, PostgreSQL, Neo4j HTTP, Neo4j Bolt
    $portStatus = @{}
    
    foreach ($port in $portsToCheck) {
        try {
            $connection = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
            $isListening = ($connection -ne $null)
            
            $serviceName = switch ($port) {
                8443 { "API Gateway (HTTPS)" }
                5432 { "PostgreSQL" }
                7474 { "Neo4j Browser (HTTP)" }
                7687 { "Neo4j Bolt" }
                default { "Unknown" }
            }
            
            Write-Host "Port $port ($serviceName): $(if ($isListening) { 'LISTENING ✅' } else { 'NOT LISTENING ⚠️' })" -ForegroundColor $(if ($isListening) { $ColorSuccess } else { $ColorWarning })
            
            $portStatus["port_$port"] = @{
                port = $port
                service = $serviceName
                listening = $isListening
            }
        } catch {
            Write-Warning "Port $port: Check failed - $_"
            $portStatus["port_$port"] = @{
                port = $port
                error = $_.Exception.Message
            }
        }
    }
    
    $baseline.network_ports = $portStatus
    
    # =========================================================================
    # Metric 6: Git Repository State
    # =========================================================================
    
    Write-Step "METRIC 6: Git Repository State"
    
    try {
        Set-Location $ProjectRoot
        
        $currentBranch = git rev-parse --abbrev-ref HEAD 2>&1
        $currentCommit = git rev-parse HEAD 2>&1
        $commitMessage = git log -1 --format=%s 2>&1
        $dirtyFiles = git status --porcelain 2>&1
        $isDirty = ($dirtyFiles -ne "")
        
        Write-Host "Branch: $currentBranch" -ForegroundColor $ColorInfo
        Write-Host "Commit: $($currentCommit.Substring(0, 8))" -ForegroundColor $ColorInfo
        Write-Host "Message: $commitMessage" -ForegroundColor $ColorInfo
        Write-Host "Working Directory: $(if ($isDirty) { 'DIRTY ⚠️' } else { 'CLEAN ✅' })" -ForegroundColor $(if ($isDirty) { $ColorWarning } else { $ColorSuccess })
        
        if ($isDirty) {
            Write-Host "Uncommitted Changes:" -ForegroundColor $ColorWarning
            $dirtyFiles | ForEach-Object { Write-Host "  $_" -ForegroundColor $ColorWarning }
        }
        
        $baseline.git_state = @{
            branch = $currentBranch
            commit_hash = $currentCommit
            commit_message = $commitMessage
            is_dirty = $isDirty
            uncommitted_changes = $(if ($isDirty) { $dirtyFiles -split "`n" } else { @() })
        }
    } catch {
        Write-Error-Custom "Failed to get git state: $_"
        $baseline.git_state = @{
            error = $_.Exception.Message
        }
    }
    
    # =========================================================================
    # Metric 7: System Resources
    # =========================================================================
    
    Write-Step "METRIC 7: System Resources"
    
    try {
        # CPU usage
        $cpuUsage = Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 1 -MaxSamples 1
        $cpuPercent = [math]::Round($cpuUsage.CounterSamples.CookedValue, 2)
        
        # Memory usage
        $osMemory = Get-CimInstance Win32_OperatingSystem
        $totalMemoryGB = [math]::Round($osMemory.TotalVisibleMemorySize / 1MB, 2)
        $freeMemoryGB = [math]::Round($osMemory.FreePhysicalMemory / 1MB, 2)
        $usedMemoryGB = [math]::Round($totalMemoryGB - $freeMemoryGB, 2)
        $memoryPercent = [math]::Round(($usedMemoryGB / $totalMemoryGB) * 100, 2)
        
        # Disk usage (C: drive)
        $disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
        $diskTotalGB = [math]::Round($disk.Size / 1GB, 2)
        $diskFreeGB = [math]::Round($disk.FreeSpace / 1GB, 2)
        $diskUsedGB = [math]::Round($diskTotalGB - $diskFreeGB, 2)
        $diskPercent = [math]::Round(($diskUsedGB / $diskTotalGB) * 100, 2)
        
        Write-Host "CPU Usage: ${cpuPercent}%" -ForegroundColor $ColorInfo
        Write-Host "Memory: ${usedMemoryGB}GB / ${totalMemoryGB}GB (${memoryPercent}%)" -ForegroundColor $ColorInfo
        Write-Host "Disk C:: ${diskUsedGB}GB / ${diskTotalGB}GB (${diskPercent}%)" -ForegroundColor $ColorInfo
        
        $baseline.system_resources = @{
            cpu_usage_percent = $cpuPercent
            memory = @{
                total_gb = $totalMemoryGB
                used_gb = $usedMemoryGB
                free_gb = $freeMemoryGB
                usage_percent = $memoryPercent
            }
            disk_c = @{
                total_gb = $diskTotalGB
                used_gb = $diskUsedGB
                free_gb = $diskFreeGB
                usage_percent = $diskPercent
            }
        }
    } catch {
        Write-Error-Custom "Failed to measure system resources: $_"
        $baseline.system_resources = @{
            error = $_.Exception.Message
        }
    }
    
    # =========================================================================
    # Export Baseline
    # =========================================================================
    
    Write-Step "EXPORTING BASELINE METRICS"
    
    try {
        $jsonContent = $baseline | ConvertTo-Json -Depth 10
        $jsonContent | Out-File $OutputFile -Encoding UTF8
        
        Write-Success "Baseline metrics exported to: $OutputFile"
        Write-Host ""
        Write-Host "File Size: $((Get-Item $OutputFile).Length) bytes" -ForegroundColor $ColorInfo
        Write-Host "Correlation ID: $CorrelationId" -ForegroundColor $ColorInfo
        Write-Host ""
        
        # Also create human-readable summary
        $summaryFile = "$MetricsDir\baseline_summary_$Timestamp.md"
        $summary = @"
# P-OS v7.5 Baseline Metrics Summary

**Timestamp:** $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')  
**Correlation ID:** $CorrelationId  
**Operator:** $env:USERNAME  
**Hostname:** $env:COMPUTERNAME

---

## Key Metrics

### Health Check Latency
$(if ($baseline.health_check_latency_ms.p50) { "- **p50:** $($baseline.health_check_latency_ms.p50)ms" } else { "- Status: FAILED")
$(if ($baseline.health_check_latency_ms.p95) { "- **p95:** $($baseline.health_check_latency_ms.p95)ms" } else { "" })
$(if ($baseline.health_check_latency_ms.p99) { "- **p99:** $($baseline.health_check_latency_ms.p99)ms" } else { "" })

### API Gateway Memory
$(if ($baseline.gateway_memory.memory_mb) { "- **Memory:** $($baseline.gateway_memory.memory_mb) MB" } else { "- Status: NOT RUNNING")

### Database Size
$(if ($baseline.database_size.size_pretty) { "- **Size:** $($baseline.database_size.size_pretty)" } else { "- Status: UNKNOWN")

### W11 Active Flags
- **Count:** $($baseline.w11_flags.active_count) (expected: 0)
- **Status:** $($baseline.w11_flags.status)

### Network Ports
$(foreach ($port in $baseline.network_ports.PSObject.Properties) {
    "- Port $($port.Value.port): $(if ($port.Value.listening) { 'LISTENING ✅' } else { 'NOT LISTENING ⚠️' })"
})

### Git State
- **Branch:** $($baseline.git_state.branch)
- **Commit:** $($baseline.git_state.commit_hash.Substring(0, 8))
- **Working Directory:** $(if ($baseline.git_state.is_dirty) { 'DIRTY ⚠️' } else { 'CLEAN ✅' })

### System Resources
- **CPU:** $($baseline.system_resources.cpu_usage_percent)%
- **Memory:** $($baseline.system_resources.memory.used_gb)GB / $($baseline.system_resources.memory.total_gb)GB ($($baseline.system_resources.memory.usage_percent)%)
- **Disk C:** $($baseline.system_resources.disk_c.used_gb)GB / $($baseline.system_resources.disk_c.total_gb)GB ($($baseline.system_resources.disk_c.usage_percent)%)

---

**Full JSON data:** $(Split-Path $OutputFile -Leaf)

*Generated by MEASURE_BASELINE.ps1*
"@
        
        $summary | Out-File $summaryFile -Encoding UTF8
        Write-Success "Human-readable summary: $summaryFile"
        
        Write-Host ""
        Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor $ColorSuccess
        Write-Host "║         BASELINE METRICS COLLECTION COMPLETE            ║" -ForegroundColor $ColorSuccess
        Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor $ColorSuccess
        Write-Host ""
        
        return $true
    } catch {
        Write-Error-Custom "Failed to export baseline: $_"
        return $false
    }
}

# Execute baseline measurement
Invoke-BaselineMeasurement
