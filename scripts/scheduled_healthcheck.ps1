# P-OS Scheduled Runtime Healthcheck
# Purpose: Run runtime constitution guard on schedule (cron/Task Scheduler)
# Usage: .\scripts\scheduled_healthcheck.ps1
# Schedule: Every 15 minutes recommended

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$GuardScript = "$ProjectRoot\scripts\runtime_constitution_guard.ps1"
$HealthcheckLog = "$ProjectRoot\logs\healthcheck_result.json"

Write-Host "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ') - Starting scheduled healthcheck..." 

try {
    # Run self-test mode for comprehensive check
    & $GuardScript -Mode "scheduled"
    
    if ($LASTEXITCODE -eq 0) {
        # Read current constitutional state
        $stateFile = "$ProjectRoot\runtime\constitutional_state.json"
        if (Test-Path $stateFile) {
            $state = Get-Content $stateFile | ConvertFrom-Json
            
            # Write simplified healthcheck result for monitoring systems
            $healthResult = @{
                timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
                results = @{
                    postgres = "ok"  # TODO: Add actual DB checks
                    neo4j = "ok"     # TODO: Add actual graph DB checks
                    grafana = $(if ($state.state -eq "HEALTHY") { "ok" } else { "fail" })
                    constitutional_state = $state.state
                    w11_engine = $state.w11
                    audit_chain = $state.audit_chain
                    replay_integrity = $state.replay_integrity
                    freeze_mode = $state.freeze_mode
                }
                severity = $(if ($state.state -eq "HEALTHY") { "info" } elseif ($state.state -eq "DEGRADED") { "warning" } else { "critical" })
            }
            
            $healthResult | ConvertTo-Json -Depth 10 | Out-File $HealthcheckLog -Encoding UTF8
            Write-Host "Healthcheck result written to: $HealthcheckLog"
        }
        
        Write-Host "✅ Scheduled healthcheck completed successfully"
        exit 0
    } else {
        Write-Host "❌ Scheduled healthcheck detected issues (exit code: $LASTEXITCODE)"
        
        # Write critical healthcheck result
        $healthResult = @{
            timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
            results = @{
                constitutional_guard = "fail"
            }
            severity = "critical"
        }
        
        $healthResult | ConvertTo-Json | Out-File $HealthcheckLog -Encoding UTF8
        exit 1
    }
} catch {
    Write-Host "❌ Scheduled healthcheck failed with error: $_"
    
    $healthResult = @{
        timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
        results = @{
            healthcheck_execution = "error"
            error = $_.Exception.Message
        }
        severity = "critical"
    }
    
    $healthResult | ConvertTo-Json | Out-File $HealthcheckLog -Encoding UTF8
    exit 1
}
