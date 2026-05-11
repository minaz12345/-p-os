# ============================================================================
# P-OS v7.5 - NEO4J CONNECTIVITY ENRICHMENT EXECUTOR
# ============================================================================
# Document ID: ARCHIVE-P-OS-7.5-NEO4J-CONNECTIVITY-IMPROVEMENT-20260511
# Date: 2026-05-11
# Purpose: Execute connectivity enrichment with safety checks
# Mode: Quiet Operations (non-disruptive, with rollback capability)
# ============================================================================

param(
    [string]$Neo4jUri = "neo4j+s://127.0.0.1:7687",
    [string]$Username = "neo4j",
    [switch]$DryRun = $false,
    [switch]$SkipBackup = $false
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "P-OS v7.5 - NEO4J CONNECTIVITY ENRICHMENT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# PHASE 0: PRE-FLIGHT CHECKS
# ============================================================================

Write-Host "[PHASE 0] Pre-flight checks..." -ForegroundColor Yellow

# Check if Cypher script exists
$scriptPath = Join-Path $PSScriptRoot "enrich_connectivity_phase2.cypher"
if (-not (Test-Path $scriptPath)) {
    Write-Host "ERROR: enrich_connectivity_phase2.cypher not found!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Script file found: $scriptPath" -ForegroundColor Green

# Check Neo4j connection
try {
    Write-Host "Testing Neo4j connection to $Neo4jUri..." -ForegroundColor Gray
    
    # Try to get current stats
    $testQuery = "MATCH (n) RETURN count(n) AS node_count"
    $result = cypher-shell -a $Neo4jUri -u $Username -p $env:NEO4J_PASSWORD "$testQuery" 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        throw "Connection failed: $result"
    }
    
    Write-Host "✓ Neo4j connection successful" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Cannot connect to Neo4j" -ForegroundColor Red
    Write-Host "Details: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Ensure:" -ForegroundColor Yellow
    Write-Host "  1. Neo4j is running" -ForegroundColor Yellow
    Write-Host "  2. NEO4J_PASSWORD environment variable is set" -ForegroundColor Yellow
    Write-Host "  3. Connection URI is correct: $Neo4jUri" -ForegroundColor Yellow
    exit 1
}

# ============================================================================
# PHASE 1: BACKUP (unless skipped)
# ============================================================================

if (-not $SkipBackup) {
    Write-Host ""
    Write-Host "[PHASE 1] Creating backup..." -ForegroundColor Yellow
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "data/backups/neo4j_pre_enrichment_$timestamp.dump"
    
    # Create backup directory if needed
    $backupDir = Split-Path $backupFile -Parent
    if (-not (Test-Path $backupDir)) {
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    }
    
    Write-Host "Backup location: $backupFile" -ForegroundColor Gray
    
    if ($DryRun) {
        Write-Host "[DRY RUN] Would create backup at: $backupFile" -ForegroundColor Cyan
    } else {
        try {
            # Neo4j backup command (adjust based on your setup)
            neo4j-admin database dump neo4j --to=$backupFile 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Backup created successfully" -ForegroundColor Green
            } else {
                Write-Host "⚠ WARNING: Backup failed, proceeding with caution" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "⚠ WARNING: Backup error: $_" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host ""
    Write-Host "[PHASE 1] Backup skipped (--SkipBackup flag)" -ForegroundColor Yellow
}

# ============================================================================
# PHASE 2: CAPTURE BASELINE METRICS
# ============================================================================

Write-Host ""
Write-Host "[PHASE 2] Capturing baseline metrics..." -ForegroundColor Yellow

$baselineQuery = @"
MATCH (n) WITH count(n) AS total_nodes
MATCH ()-[r]->() WITH total_nodes, count(r) AS total_rels
MATCH (n) WHERE size((n)--()) = 0 
RETURN 
  total_nodes,
  total_rels,
  count(n) AS orphaned_nodes,
  round(toFloat(total_nodes - count(n)) / total_nodes * 100, 2) AS connectivity_pct
"@

if ($DryRun) {
    Write-Host "[DRY RUN] Would execute baseline query" -ForegroundColor Cyan
} else {
    $baseline = cypher-shell -a $Neo4jUri -u $Username -p $env:NEO4J_PASSWORD --format plain "$baselineQuery" 2>&1
    
    Write-Host "Baseline Metrics:" -ForegroundColor Gray
    Write-Host $baseline -ForegroundColor White
}

# ============================================================================
# PHASE 3: DRY RUN ANALYSIS
# ============================================================================

if ($DryRun) {
    Write-Host ""
    Write-Host "[PHASE 3] DRY RUN MODE - No changes will be made" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To execute for real, run without --DryRun flag:" -ForegroundColor Yellow
    Write-Host "  .\execute_enrichment.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "Script preview (first 50 lines):" -ForegroundColor Gray
    Get-Content $scriptPath | Select-Object -First 50
    exit 0
}

# ============================================================================
# PHASE 4: CONFIRMATION PROMPT
# ============================================================================

Write-Host ""
Write-Host "[PHASE 4] Confirmation Required" -ForegroundColor Yellow
Write-Host ""
Write-Host "This will modify the Neo4j graph by adding relationships." -ForegroundColor Red
Write-Host "Estimated impact:" -ForegroundColor Yellow
Write-Host "  - Target connectivity: 56.1% → 75-85%" -ForegroundColor White
Write-Host "  - Expected new relationships: ~200-300" -ForegroundColor White
Write-Host "  - Irreversible operation (use backup to restore)" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "Type 'ENRICH' to proceed or anything else to cancel"

if ($confirm -ne "ENRICH") {
    Write-Host "Operation cancelled by user." -ForegroundColor Red
    exit 0
}

# ============================================================================
# PHASE 5: EXECUTE ENRICHMENT
# ============================================================================

Write-Host ""
Write-Host "[PHASE 5] Executing enrichment script..." -ForegroundColor Yellow
Write-Host "This may take 1-5 minutes depending on database size..." -ForegroundColor Gray
Write-Host ""

$startTime = Get-Date

try {
    # Execute the Cypher script
    cypher-shell -a $Neo4jUri -u $Username -p $env:NEO4J_PASSWORD --file $scriptPath 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        throw "Cypher execution failed with exit code $LASTEXITCODE"
    }
    
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    Write-Host ""
    Write-Host "✓ Enrichment completed in $([math]::Round($duration, 2)) seconds" -ForegroundColor Green
    
} catch {
    Write-Host ""
    Write-Host "ERROR: Enrichment failed!" -ForegroundColor Red
    Write-Host "Details: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "If needed, restore from backup:" -ForegroundColor Yellow
    Write-Host "  neo4j-admin database load neo4j --from=$backupFile --overwrite-destination=true" -ForegroundColor White
    exit 1
}

# ============================================================================
# PHASE 6: POST-ENRICHMENT VERIFICATION
# ============================================================================

Write-Host ""
Write-Host "[PHASE 6] Post-enrichment verification..." -ForegroundColor Yellow

$verificationQuery = @"
MATCH (n) WITH count(n) AS total_nodes
MATCH ()-[r]->() WITH total_nodes, count(r) AS total_rels
MATCH (n) WHERE size((n)--()) = 0 
RETURN 
  total_nodes,
  total_rels,
  count(n) AS orphaned_nodes,
  round(toFloat(total_nodes - count(n)) / total_nodes * 100, 2) AS connectivity_pct
"@

$postMetrics = cypher-shell -a $Neo4jUri -u $Username -p $env:NEO4J_PASSWORD --format plain "$verificationQuery" 2>&1

Write-Host ""
Write-Host "Post-Enrichment Metrics:" -ForegroundColor Gray
Write-Host $postMetrics -ForegroundColor White

# ============================================================================
# PHASE 7: GENERATE REPORT
# ============================================================================

Write-Host ""
Write-Host "[PHASE 7] Generating report..." -ForegroundColor Yellow

$reportPath = "reports/NEO4J_CONNECTIVITY_ENRICHMENT_$(Get-Date -Format 'yyyyMMdd_HHmmss').md"

$reportContent = @"
# Neo4j Connectivity Enrichment Report

**Date:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  
**Script:** enrich_connectivity_phase2.cypher  
**Mode:** $(if ($DryRun) { "DRY RUN" } else { "LIVE EXECUTION" })

---

## Baseline Metrics

$(if (-not $DryRun) { $baseline })

## Post-Enrichment Metrics

$(if (-not $DryRun) { $postMetrics })

## Summary

- **Status:** $(if ($LASTEXITCODE -eq 0) { "SUCCESS ✅" } else { "FAILED ❌" })
- **Duration:** $([math]::Round($duration, 2)) seconds
- **Backup:** $(if ($SkipBackup) { "Skipped" } else { "Created at $backupFile" })

---

*Generated by P-OS v7.5 Connectivity Enrichment Executor*
"@

$reportContent | Out-File -FilePath $reportPath -Encoding UTF8

Write-Host "✓ Report saved to: $reportPath" -ForegroundColor Green

# ============================================================================
# COMPLETE
# ============================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "ENRICHMENT COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review report: $reportPath" -ForegroundColor White
Write-Host "  2. Verify in Neo4j Browser: http://localhost:7474" -ForegroundColor White
Write-Host "  3. Run sample queries to validate connectivity" -ForegroundColor White
Write-Host ""
