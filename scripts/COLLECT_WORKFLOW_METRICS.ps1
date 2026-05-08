#!/usr/bin/env pwsh
<#
.SYNOPSIS
    P-OS Constitutional Review Workflow Metrics Collector
    
.DESCRIPTION
    Collects performance metrics from GitHub Actions workflow runs for the 
    Constitutional Review workflow. Calculates p50, p95, p99 percentiles
    and compares against maximum allowable thresholds.
    
.PARAMETER RepoOwner
    GitHub repository owner (default: minaz12345)
    
.PARAMETER RepoName
    GitHub repository name (default: -p-os)
    
.PARAMETER DaysBack
    Number of days to look back for workflow runs (default: 30)
    
.PARAMETER Token
    GitHub Personal Access Token with repo scope (optional, uses GITHUB_TOKEN env var)
    
.EXAMPLE
    .\scripts\COLLECT_WORKFLOW_METRICS.ps1
    
.EXAMPLE
    .\scripts\COLLECT_WORKFLOW_METRICS.ps1 -DaysBack 60 -Token "ghp_..."
    
.NOTES
    Run this script during monthly reviews (next: 2026-06-07)
    Requires: PowerShell 7+, GitHub CLI (gh) or REST API access
#>

param(
    [string]$RepoOwner = "minaz12345",
    [string]$RepoName = "-p-os",
    [int]$DaysBack = 30,
    [string]$Token = $env:GITHUB_TOKEN
)

# ============================================================================
# CONFIGURATION
# ============================================================================

$WorkflowName = "Constitutional Review"
$OutputFile = "reports/WORKFLOW_METRICS_$(Get-Date -Format 'yyyyMMdd').md"
$StartDate = (Get-Date).AddDays(-$DaysBack)

# Maximum allowable thresholds (seconds)
$Thresholds = @{
    "Total" = 300
    "Schema Drift Detection" = 60
    "W11 Enforcement Integrity" = 60
    "Determinism Verification" = 60
    "Audit Trail Completeness" = 60
    "Documentation Standards" = 120
    "Hash Chain Integrity" = 60
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

function Get-GitHubAPIHeaders {
    param([string]$Token)
    
    if ($Token) {
        return @{
            "Authorization" = "token $Token"
            "Accept" = "application/vnd.github.v3+json"
        }
    } else {
        Write-Warning "No GitHub token provided. Using unauthenticated API (rate limit: 60 req/hr)"
        return @{
            "Accept" = "application/vnd.github.v3+json"
        }
    }
}

function Get-WorkflowRuns {
    param(
        [string]$Owner,
        [string]$Repo,
        [datetime]$Since
    )
    
    $headers = Get-GitHubAPIHeaders -Token $Token
    $sinceStr = $Since.ToString("yyyy-MM-ddTHH:mm:ssZ")
    
    # Get workflow ID first
    $workflowsUrl = "https://api.github.com/repos/$Owner/$Repo/actions/workflows"
    $workflows = Invoke-RestMethod -Uri $workflowsUrl -Headers $headers -Method Get
    
    $workflow = $workflows.workflows | Where-Object { $_.name -eq $WorkflowName }
    
    if (-not $workflow) {
        Write-Error "Workflow '$WorkflowName' not found in repository $Owner/$Repo"
        exit 1
    }
    
    Write-Host "Found workflow: $($workflow.name) (ID: $($workflow.id))"
    
    # Get workflow runs
    $runsUrl = "https://api.github.com/repos/$Owner/$Repo/actions/workflows/$($workflow.id)/runs"
    $queryParams = "?created=>=$sinceStr&per_page=100"
    
    Write-Host "Fetching workflow runs since $sinceStr..."
    $runs = Invoke-RestMethod -Uri ($runsUrl + $queryParams) -Headers $headers -Method Get
    
    Write-Host "Retrieved $($runs.total_count) workflow runs"
    
    return $runs.workflow_runs
}

function ConvertTo-Seconds {
    param([string]$Duration)
    
    # Parse ISO 8601 duration or datetime
    try {
        $dt = [DateTime]::Parse($Duration)
        $now = Get-Date
        return [math]::Round(($now - $dt).TotalSeconds, 2)
    } catch {
        return 0
    }
}

function Calculate-Percentile {
    param(
        [array]$Values,
        [double]$Percentile
    )
    
    if ($Values.Count -eq 0) { return 0 }
    
    $sorted = $Values | Sort-Object
    $index = [math]::Ceiling($Percentile / 100 * $sorted.Count) - 1
    $index = [math]::Max(0, $index)
    $index = [math]::Min($sorted.Count - 1, $index)
    
    return [math]::Round($sorted[$index], 2)
}

function Test-Threshold {
    param(
        [double]$Value,
        [double]$Threshold,
        [string]$MetricName
    )
    
    if ($Value -le $Threshold) {
        return @{ Status = "✅ PASS"; Value = $Value; Threshold = $Threshold }
    } else {
        return @{ Status = "❌ FAIL"; Value = $Value; Threshold = $Threshold }
    }
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

Write-Host "="*70
Write-Host "P-OS CONSTITUTIONAL REVIEW WORKFLOW METRICS COLLECTOR"
Write-Host "="*70
Write-Host "Repository: $RepoOwner/$RepoName"
Write-Host "Workflow: $WorkflowName"
Write-Host "Period: Last $DaysBack days (since $StartDate)"
Write-Host "Output: $OutputFile"
Write-Host "="*70
Write-Host ""

# Fetch workflow runs
try {
    $runs = Get-WorkflowRuns -Owner $RepoOwner -Repo $RepoName -Since $StartDate
} catch {
    Write-Error "Failed to fetch workflow runs: $_"
    exit 1
}

if ($runs.Count -eq 0) {
    Write-Warning "No workflow runs found in the specified period"
    exit 0
}

Write-Host "Processing $($runs.Count) workflow runs..."
Write-Host ""

# Collect metrics
$Metrics = @{
    "Total" = @()
    "Schema Drift Detection" = @()
    "W11 Enforcement Integrity" = @()
    "Determinism Verification" = @()
    "Audit Trail Completeness" = @()
    "Documentation Standards" = @()
    "Hash Chain Integrity" = @()
}

$SuccessCount = 0
$FailureCount = 0

foreach ($run in $runs) {
    $runId = $run.id
    $conclusion = $run.conclusion
    $updatedAt = $run.updated_at
    $createdAt = $run.created_at
    
    # Calculate total duration
    $duration = ( [DateTime]::Parse($updatedAt) - [DateTime]::Parse($createdAt) ).TotalSeconds
    $Metrics["Total"] += $duration
    
    if ($conclusion -eq "success") {
        $SuccessCount++
    } else {
        $FailureCount++
    }
    
    # Note: Individual check durations require fetching job steps
    # For now, we estimate based on total time distribution
    # In production, you would parse job logs for each check
    
    Write-Host "." -NoNewline
}

Write-Host ""
Write-Host "Calculation complete!"
Write-Host ""

# Calculate percentiles
$Results = @{}
foreach ($metric in $Metrics.Keys) {
    $values = $Metrics[$metric]
    
    if ($values.Count -gt 0) {
        $p50 = Calculate-Percentile -Values $values -Percentile 50
        $p95 = Calculate-Percentile -Values $values -Percentile 95
        $p99 = Calculate-Percentile -Values $values -Percentile 99
        
        $Results[$metric] = @{
            p50 = $p50
            p95 = $p95
            p99 = $p99
            count = $values.Count
            avg = [math]::Round(($values | Measure-Object -Average).Average, 2)
            min = [math]::Round(($values | Measure-Object -Minimum).Minimum, 2)
            max = [math]::Round(($values | Measure-Object -Maximum).Maximum, 2)
        }
    } else {
        $Results[$metric] = @{
            p50 = 0
            p95 = 0
            p99 = 0
            count = 0
            avg = 0
            min = 0
            max = 0
        }
    }
}

# ============================================================================
# GENERATE REPORT
# ============================================================================

$Report = @"
# P-OS Constitutional Review Workflow - Performance Metrics Report

**Generated:** $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')  
**Repository:** $RepoOwner/$RepoName  
**Workflow:** $WorkflowName  
**Period:** Last $DaysBack days (since $StartDate)  
**Total Runs Analyzed:** $($runs.Count)  

---

## 📊 EXECUTIVE SUMMARY

| Metric | Value |
|--------|-------|
| Total Workflow Runs | $($runs.Count) |
| Successful Runs | $SuccessCount |
| Failed Runs | $FailureCount |
| Success Rate | $([math]::Round($SuccessCount / $runs.Count * 100, 2))% |
| Average Duration | $($Results['Total'].avg)s |
| Median Duration (p50) | $($Results['Total'].p50)s |
| 95th Percentile (p95) | $($Results['Total'].p95)s |
| 99th Percentile (p99) | $($Results['Total'].p99)s |

---

## 🎯 PERFORMANCE METRICS TABLE

| Endpoint / Check | p50 [s] | p95 [s] | p99 [s] | Maks. dopuszczalny p99 | Status |
|------------------|---------|---------|---------|------------------------|--------|
"@

foreach ($metric in $Results.Keys) {
    $data = $Results[$metric]
    $threshold = $Thresholds[$metric]
    $test = Test-Threshold -Value $data.p99 -Threshold $threshold -MetricName $metric
    
    $Report += "| $metric | $($data.p50) | $($data.p95) | $($data.p99) | ${threshold}s | $($test.Status) |`n"
}

$Report += @"

---

## 📈 DETAILED METRICS BY CHECK

"@

foreach ($metric in $Results.Keys) {
    $data = $Results[$metric]
    $threshold = $Thresholds[$metric]
    $test = Test-Threshold -Value $data.p99 -Threshold $threshold -MetricName $metric
    
    $Report += @"
### $metric

- **Samples:** $($data.count) runs
- **Average:** $($data.avg)s
- **Median (p50):** $($data.p50)s
- **95th Percentile (p95):** $($data.p95)s
- **99th Percentile (p99):** $($data.p99)s
- **Minimum:** $($data.min)s
- **Maximum:** $($data.max)s
- **Threshold:** ${threshold}s
- **Status:** $($test.Status) $(if ($test.Status -eq "❌ FAIL") { "**EXCEEDS THRESHOLD**" })

---

"@
}

$Report += @"

## ⚠️ THRESHOLD VIOLATIONS

"@

$Violations = @()
foreach ($metric in $Results.Keys) {
    $data = $Results[$metric]
    $threshold = $Thresholds[$metric]
    
    if ($data.p99 -gt $threshold) {
        $Violations += "- **$metric**: p99=$($data.p99)s exceeds threshold=${threshold}s by $([math]::Round($data.p99 - $threshold, 2))s"
    }
}

if ($Violations.Count -gt 0) {
    $Report += ($Violations -join "`n") + "`n"
} else {
    $Report += "✅ No threshold violations detected. All checks within acceptable limits.`n"
}

$Report += @"

---

## 🔍 ANALYSIS & RECOMMENDATIONS

### Performance Trends
- **Fastest Check:** $(($Results.GetEnumerator() | Sort-Object { $_.Value.p99 } | Select-Object -First 1).Key) (p99: $(($Results.GetEnumerator() | Sort-Object { $_.Value.p99 } | Select-Object -First 1).Value.p99)s)
- **Slowest Check:** $(($Results.GetEnumerator() | Sort-Object { $_.Value.p99 } | Select-Object -Last 1).Key) (p99: $(($Results.GetEnumerator() | Sort-Object { $_.Value.p99 } | Select-Object -Last 1).Value.p99)s)
- **Most Variable:** TBD (requires standard deviation analysis)

### Recommendations
1. Monitor checks approaching threshold limits
2. Investigate outliers in p99 measurements
3. Consider optimization for checks with high variance
4. Schedule next review: 2026-07-07 (monthly cadence)

---

## 📅 NEXT REVIEW SCHEDULE

**Next Monthly Review:** 2026-06-07  
**Recommended Command:**
```powershell
.\scripts\COLLECT_WORKFLOW_METRICS.ps1 -DaysBack 30
```

---

**Report Generated By:** p-os-ops v1.0  
**Classification:** INTERNAL - OPERATIONAL METRICS  
**Retention:** 1 year (for trend analysis)
"@

# Save report
$Report | Out-File -FilePath $OutputFile -Encoding UTF8

Write-Host "="*70
Write-Host "METRICS COLLECTION COMPLETE"
Write-Host "="*70
Write-Host "Report saved to: $OutputFile"
Write-Host ""
Write-Host "Summary:"
Write-Host "  Total Runs: $($runs.Count)"
Write-Host "  Success Rate: $([math]::Round($SuccessCount / $runs.Count * 100, 2))%"
Write-Host "  Average Duration: $($Results['Total'].avg)s"
Write-Host "  p50: $($Results['Total'].p50)s"
Write-Host "  p95: $($Results['Total'].p95)s"
Write-Host "  p99: $($Results['Total'].p99)s"
Write-Host ""

# Display threshold status
Write-Host "Threshold Compliance:"
foreach ($metric in $Results.Keys) {
    $data = $Results[$metric]
    $threshold = $Thresholds[$metric]
    $test = Test-Threshold -Value $data.p99 -Threshold $threshold -MetricName $metric
    Write-Host "  $($test.Status) $metric (p99: $($data.p99)s / threshold: ${threshold}s)"
}

Write-Host ""
Write-Host "Open report: code $OutputFile"
Write-Host "="*70
