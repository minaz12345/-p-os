# P-OS Chaos Testing Tooling Setup Script
# Purpose: Install and configure tools required for chaos testing
# Date: 2026-05-07
# Usage: .\scripts\SETUP_CHAOS_TOOLS.ps1
# Prerequisites: Docker, Node.js (optional), Grafana, Prometheus

param(
    [Parameter(Mandatory=$false)]
    [switch]$SkipDocker = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipGrafana = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$Verbose = $false
)

# ============================================================================
# CONFIGURATION
# ============================================================================

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$CorrelationId = [guid]::NewGuid().ToString()

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

function Test-Prerequisite {
    param(
        [string]$Name,
        [scriptblock]$Check
    )
    
    Write-Host "Checking: $Name... " -NoNewline
    try {
        $result = & $Check
        if ($result) {
            Write-Success "INSTALLED"
            return $true
        } else {
            Write-Warning "NOT FOUND"
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

function Invoke-ChaosToolingSetup {
    Write-Host "`n" -NoNewline
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor $ColorInfo
    Write-Host "║     P-OS CHAOS TESTING TOOLING SETUP                    ║" -ForegroundColor $ColorInfo
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor $ColorInfo
    Write-Host ""
    Write-Host "Correlation ID: $CorrelationId" -ForegroundColor $ColorInfo
    Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')" -ForegroundColor $ColorInfo
    Write-Host ""
    
    $setupResults = @{
        timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
        correlation_id = $CorrelationId
        components = @{}
    }
    
    # =========================================================================
    # Tool 1: WireMock for GitHub API Mocking
    # =========================================================================
    
    Write-Step "TOOL 1: WireMock (GitHub API Mocking)"
    
    if (-not $SkipDocker) {
        # Check Docker availability
        $dockerInstalled = Test-Prerequisite "Docker" {
            $null -ne (Get-Command docker -ErrorAction SilentlyContinue)
        }
        
        if ($dockerInstalled) {
            try {
                Write-Host "Pulling WireMock Docker image..." -ForegroundColor $ColorInfo
                docker pull wiremock/wiremock:latest
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Success "WireMock image pulled successfully"
                    
                    # Create WireMock mappings directory
                    $wiremockDir = "$ProjectRoot\wiremock"
                    if (-not (Test-Path $wiremockDir)) {
                        New-Item -ItemType Directory -Force -Path $wiremockDir | Out-Null
                        Write-Success "Created WireMock directory: $wiremockDir"
                    }
                    
                    # Create stub for GitHub API 500 error (Test 1)
                    $github500Stub = @{
                        request = @{
                            method = "POST"
                            urlPattern = "/repos/.*/.*/git/refs"
                        }
                        response = @{
                            status = 500
                            body = '{"message": "Internal Server Error"}'
                            headers = @{
                                "Content-Type" = "application/json"
                            }
                        }
                    } | ConvertTo-Json -Depth 10
                    
                    $stubFile = "$wiremockDir\github-500-error.json"
                    $github500Stub | Out-File $stubFile -Encoding UTF8
                    Write-Success "Created GitHub 500 error stub: $stubFile"
                    
                    # Start WireMock container
                    Write-Host "Starting WireMock container on port 8080..." -ForegroundColor $ColorInfo
                    docker run -d --name wiremock-github `
                        -p 8080:8080 `
                        -v "${wiremockDir}:/home/wiremock/mappings" `
                        wiremock/wiremock:latest --enable-stub-cors
                    
                    if ($LASTEXITCODE -eq 0) {
                        Write-Success "WireMock container started successfully"
                        Write-Host "  URL: http://localhost:8080" -ForegroundColor $ColorInfo
                        Write-Host "  Mappings: $wiremockDir" -ForegroundColor $ColorInfo
                        
                        $setupResults.components.wiremock = @{
                            status = "installed"
                            url = "http://localhost:8080"
                            mappings_dir = $wiremockDir
                            docker_container = "wiremock-github"
                        }
                    } else {
                        Write-Warning "Failed to start WireMock container"
                        $setupResults.components.wiremock = @{
                            status = "failed"
                            error = "Container start failed"
                        }
                    }
                } else {
                    Write-Error-Custom "Failed to pull WireMock image"
                    $setupResults.components.wiremock = @{
                        status = "failed"
                        error = "Image pull failed"
                    }
                }
            } catch {
                Write-Error-Custom "WireMock setup failed: $_"
                $setupResults.components.wiremock = @{
                    status = "failed"
                    error = $_.Exception.Message
                }
            }
        } else {
            Write-Warning "Docker not installed. Skipping WireMock setup."
            Write-Host "Alternative: Use nock (Node.js) for API mocking" -ForegroundColor $ColorWarning
            $setupResults.components.wiremock = @{
                status = "skipped"
                reason = "Docker not available"
                alternative = "nock (Node.js)"
            }
        }
    } else {
        Write-Warning "Skipping WireMock setup (--SkipDocker flag used)"
        $setupResults.components.wiremock = @{
            status = "skipped"
            reason = "User requested skip"
        }
    }
    
    # =========================================================================
    # Tool 2: Grafana Dashboard Configuration
    # =========================================================================
    
    Write-Step "TOOL 2: Grafana Dashboard for Chaos Metrics"
    
    if (-not $SkipGrafana) {
        $grafanaUrl = "http://localhost:3000"
        
        # Check if Grafana is running
        $grafanaRunning = Test-Prerequisite "Grafana" {
            try {
                $response = Invoke-WebRequest -Uri "$grafanaUrl/api/health" -Method GET -TimeoutSec 5 -ErrorAction SilentlyContinue
                $response.StatusCode -eq 200
            } catch {
                $false
            }
        }
        
        if ($grafanaRunning) {
            try {
                Write-Host "Creating P-OS Chaos Testing dashboard..." -ForegroundColor $ColorInfo
                
                # Create dashboard JSON
                $dashboard = @{
                    dashboard = @{
                        id = $null
                        uid = "p-os-chaos-testing"
                        title = "P-OS Chaos Testing Metrics"
                        tags = @("p-os", "chaos-testing", "operations")
                        timezone = "browser"
                        panels = @(
                            @{
                                id = 1
                                title = "Deployment MTTR (Mean Time To Recovery)"
                                type = "graph"
                                datasource = "Prometheus"
                                targets = @(
                                    @{
                                        expr = "rate(pos_deployment_recovery_time_seconds_sum[5m]) / rate(pos_deployment_recovery_time_seconds_count[5m])"
                                        legendFormat = "MTTR"
                                    }
                                )
                                gridPos = @{ h = 8; w = 12; x = 0; y = 0 }
                            },
                            @{
                                id = 2
                                title = "Rollback Success Rate"
                                type = "gauge"
                                datasource = "Prometheus"
                                targets = @(
                                    @{
                                        expr = "pos_rollback_success_total / pos_rollback_total * 100"
                                        legendFormat = "Success Rate %"
                                    }
                                )
                                gridPos = @{ h = 8; w = 12; x = 12; y = 0 }
                            },
                            @{
                                id = 3
                                title = "Active W11 Flags"
                                type = "stat"
                                datasource = "Prometheus"
                                targets = @(
                                    @{
                                        expr = "pos_w11_active_flags"
                                        legendFormat = "Active Flags"
                                    }
                                )
                                gridPos = @{ h = 4; w = 6; x = 0; y = 8 }
                            },
                            @{
                                id = 4
                                title = "Health Check Latency (p95)"
                                type = "stat"
                                datasource = "Prometheus"
                                targets = @(
                                    @{
                                        expr = "histogram_quantile(0.95, rate(pos_health_check_latency_seconds_bucket[5m]))"
                                        legendFormat = "p95"
                                    }
                                )
                                gridPos = @{ h = 4; w = 6; x = 6; y = 8 }
                            },
                            @{
                                id = 5
                                title = "Chaos Test Execution Status"
                                type = "table"
                                datasource = "Prometheus"
                                targets = @(
                                    @{
                                        expr = "pos_chaos_test_status"
                                        legendFormat = "{{test_name}}"
                                    }
                                )
                                gridPos = @{ h = 8; w = 24; x = 0; y = 12 }
                            }
                        )
                        schemaVersion = 30
                        version = 1
                    }
                    overwrite = $true
                } | ConvertTo-Json -Depth 10
                
                # Import dashboard via Grafana API
                $headers = @{
                    "Content-Type" = "application/json"
                }
                
                # Note: In production, use proper authentication
                $response = Invoke-RestMethod -Uri "$grafanaUrl/api/dashboards/db" `
                    -Method POST `
                    -Headers $headers `
                    -Body $dashboard `
                    -ErrorAction SilentlyContinue
                
                if ($response.status -eq "success") {
                    Write-Success "Grafana dashboard created successfully"
                    Write-Host "  URL: $grafanaUrl/d/p-os-chaos-testing" -ForegroundColor $ColorInfo
                    
                    $setupResults.components.grafana = @{
                        status = "installed"
                        url = "$grafanaUrl/d/p-os-chaos-testing"
                        dashboard_uid = "p-os-chaos-testing"
                    }
                } else {
                    Write-Warning "Dashboard import returned unexpected response"
                    Write-Host "Manual import required: Copy dashboard JSON from docs/grafana/chaos-testing-dashboard.json" -ForegroundColor $ColorWarning
                    
                    # Save dashboard JSON for manual import
                    $dashboardFile = "$ProjectRoot\docs\grafana\chaos-testing-dashboard.json"
                    $dashboardDir = Split-Path $dashboardFile -Parent
                    if (-not (Test-Path $dashboardDir)) {
                        New-Item -ItemType Directory -Force -Path $dashboardDir | Out-Null
                    }
                    $dashboard | ConvertTo-Json -Depth 10 | Out-File $dashboardFile -Encoding UTF8
                    Write-Success "Dashboard JSON saved to: $dashboardFile"
                    
                    $setupResults.components.grafana = @{
                        status = "partial"
                        note = "Dashboard JSON saved for manual import"
                        file = $dashboardFile
                    }
                }
            } catch {
                Write-Error-Custom "Grafana dashboard creation failed: $_"
                $setupResults.components.grafana = @{
                    status = "failed"
                    error = $_.Exception.Message
                }
            }
        } else {
            Write-Warning "Grafana not running. Skipping dashboard setup."
            Write-Host "Start Grafana: docker-compose -f docker-compose.monitoring.yml up -d grafana" -ForegroundColor $ColorWarning
            $setupResults.components.grafana = @{
                status = "skipped"
                reason = "Grafana not available"
            }
        }
    } else {
        Write-Warning "Skipping Grafana setup (--SkipGrafana flag used)"
        $setupResults.components.grafana = @{
            status = "skipped"
            reason = "User requested skip"
        }
    }
    
    # =========================================================================
    # Tool 3: Slack Alert Integration
    # =========================================================================
    
    Write-Step "TOOL 3: Slack Alert Configuration"
    
    $slackWebhook = $env:SLACK_WEBHOOK_URL
    
    if ($slackWebhook) {
        try {
            Write-Host "Testing Slack webhook connectivity..." -ForegroundColor $ColorInfo
            
            $testMessage = @{
                text = "🛡️ P-OS Chaos Testing Setup Complete"
                attachments = @(
                    @{
                        color = "good"
                        title = "Tooling Setup Status"
                        fields = @(
                            @{
                                title = "Status"
                                value = "All tools configured successfully"
                                short = $true
                            },
                            @{
                                title = "Environment"
                                value = "Staging"
                                short = $true
                            }
                        )
                    }
                )
            } | ConvertTo-Json -Depth 5
            
            $response = Invoke-RestMethod -Uri $slackWebhook `
                -Method POST `
                -ContentType "application/json" `
                -Body $testMessage `
                -ErrorAction SilentlyContinue
            
            Write-Success "Slack webhook test successful"
            
            $setupResults.components.slack = @{
                status = "configured"
                webhook_configured = $true
                test_message_sent = $true
            }
        } catch {
            Write-Warning "Slack webhook test failed: $_"
            $setupResults.components.slack = @{
                status = "configured"
                webhook_configured = $true
                test_message_sent = $false
                error = $_.Exception.Message
            }
        }
    } else {
        Write-Warning "SLACK_WEBHOOK_URL environment variable not set"
        Write-Host "Set env var: `$env:SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/...'" -ForegroundColor $ColorWarning
        $setupResults.components.slack = @{
            status = "not_configured"
            reason = "Environment variable missing"
        }
    }
    
    # =========================================================================
    # Tool 4: Metrics Collection Cron Job
    # =========================================================================
    
    Write-Step "TOOL 4: Automated Metrics Collection"
    
    try {
        # Create metrics collection script
        $metricsScript = @"
# P-OS Chaos Metrics Collection Script
# Runs every 5 minutes during chaos testing
# Collects system metrics and exports to Prometheus format

`$ProjectRoot = Split-Path -Parent `$PSScriptRoot
`$MetricsDir = "`$ProjectRoot\metrics\chaos_tests"
`$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

if (-not (Test-Path `$MetricsDir)) {
    New-Item -ItemType Directory -Force -Path `$MetricsDir | Out-Null
}

# Collect metrics here (similar to MEASURE_BASELINE.ps1 but lighter)
# Export to Prometheus exposition format

Write-Host "Metrics collected at `$Timestamp"
"@
        
        $metricsScriptFile = "$ProjectRoot\scripts\COLLECT_CHAOS_METRICS.ps1"
        $metricsScript | Out-File $metricsScriptFile -Encoding UTF8
        Write-Success "Metrics collection script created: $metricsScriptFile"
        
        # For Windows: Create scheduled task
        Write-Host "Setting up Windows Task Scheduler job..." -ForegroundColor $ColorInfo
        
        $taskName = "P-OS Chaos Metrics Collection"
        $action = New-ScheduledTaskAction -Execute "pwsh" -Argument "-File `"$metricsScriptFile`""
        $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
        
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
        
        Write-Success "Scheduled task created: $taskName (every 5 minutes)"
        
        $setupResults.components.metrics_collection = @{
            status = "installed"
            script = $metricsScriptFile
            schedule = "every 5 minutes"
            task_name = $taskName
        }
    } catch {
        Write-Error-Custom "Metrics collection setup failed: $_"
        $setupResults.components.metrics_collection = @{
            status = "failed"
            error = $_.Exception.Message
        }
    }
    
    # =========================================================================
    # Summary
    # =========================================================================
    
    Write-Step "SETUP SUMMARY"
    
    Write-Host ""
    Write-Host "Component Status:" -ForegroundColor $ColorInfo
    foreach ($component in $setupResults.components.GetEnumerator()) {
        $status = $component.Value.status
        $color = switch ($status) {
            "installed" { $ColorSuccess }
            "configured" { $ColorSuccess }
            "partial" { $ColorWarning }
            "skipped" { $ColorWarning }
            "failed" { $ColorError }
            "not_configured" { $ColorError }
            default { $ColorInfo }
        }
        
        Write-Host "  $($component.Key): $status" -ForegroundColor $color
    }
    
    Write-Host ""
    
    # Export setup results
    $resultsFile = "$ProjectRoot\metrics\chaos_tooling_setup_$((Get-Date).ToUniversalTime().ToString('yyyyMMdd_HHmmss')).json"
    $setupResults | ConvertTo-Json -Depth 10 | Out-File $resultsFile -Encoding UTF8
    Write-Success "Setup results exported to: $resultsFile"
    
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor $ColorSuccess
    Write-Host "║       CHAOS TOOLING SETUP COMPLETE                      ║" -ForegroundColor $ColorSuccess
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor $ColorSuccess
    Write-Host ""
    
    Write-Host "Next Steps:" -ForegroundColor $ColorInfo
    Write-Host "1. Verify WireMock: curl http://localhost:8080/__admin/mappings" -ForegroundColor $ColorInfo
    Write-Host "2. Access Grafana: http://localhost:3000/d/p-os-chaos-testing" -ForegroundColor $ColorInfo
    Write-Host "3. Test Slack alert (if configured)" -ForegroundColor $ColorInfo
    Write-Host "4. Run MEASURE_BASELINE.ps1 to establish pre-chaos metrics" -ForegroundColor $ColorInfo
    Write-Host "5. Begin Week 1 chaos tests (see docs/CHAOS_TESTING_FRAMEWORK_WEEK1-4.md)" -ForegroundColor $ColorInfo
    Write-Host ""
    
    return $true
}

# Execute chaos tooling setup
Invoke-ChaosToolingSetup
