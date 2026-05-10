# Visual Identity Ornament Compliance Checker
# Purpose: Verify MAX_DENSITY_POLICY compliance across documentation
# Usage: .\scripts\check_ornament_compliance.ps1

param(
    [Parameter(Mandatory=$false)]
    [string]$DocsPath = "docs",
    
    [Parameter(Mandatory=$false)]
    [switch]$FixViolations = $false
)

$Pattern = "()()(())()()(())()()(())()()(())()()"
$WarningThreshold = 15  # 1 ornament per 15 lines
$CriticalThreshold = 10  # 1 ornament per 10 lines
$MinSpacing = 5  # minimum lines between ornaments

Write-Host "`n=== ORNAMENT COMPLIANCE CHECKER ===" -ForegroundColor Cyan
Write-Host "Pattern: $Pattern" -ForegroundColor Gray
Write-Host "Warning Threshold: 1:$WarningThreshold" -ForegroundColor Yellow
Write-Host "Critical Threshold: 1:$CriticalThreshold" -ForegroundColor Red
Write-Host ""

$files = Get-ChildItem -Path $DocsPath -Filter "*.md" -Recurse
$totalFiles = $files.Count
$compliantFiles = 0
$violationFiles = 0

$results = @()

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw
    $lines = $content -split "`n"
    $totalLines = $lines.Count
    
    # Count ornaments (excluding those in code blocks)
    $inCodeBlock = $false
    $ornamentCount = 0
    $ornamentLineNumbers = @()
    
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i].Trim()
        
        # Track code block state
        if ($line -match '^```') {
            $inCodeBlock = -not $inCodeBlock
            continue
        }
        
        # Skip if in code block
        if ($inCodeBlock) { continue }
        
        # Check for ornament
        if ($line -eq $Pattern) {
            $ornamentCount++
            $ornamentLineNumbers += ($i + 1)
        }
    }
    
    # Calculate density ratio
    if ($ornamentCount -gt 0) {
        $ratio = [math]::Floor($totalLines / $ornamentCount)
    } else {
        $ratio = 999
    }
    
    # Check for violations
    $violations = @()
    
    # 1. Check density
    if ($ratio -lt $CriticalThreshold) {
        $violations += "CRITICAL: Density ratio 1:$ratio exceeds critical threshold (1:$CriticalThreshold)"
    } elseif ($ratio -lt $WarningThreshold) {
        $violations += "WARNING: Density ratio 1:$ratio below warning threshold (1:$WarningThreshold)"
    }
    
    # 2. Check spacing between ornaments
    for ($j = 1; $j -lt $ornamentLineNumbers.Count; $j++) {
        $spacing = $ornamentLineNumbers[$j] - $ornamentLineNumbers[$j-1] - 1
        if ($spacing -lt $MinSpacing) {
            $violations += "VIOLATION: Ornaments on lines $($ornamentLineNumbers[$j-1]) and $($ornamentLineNumbers[$j]) have only $spacing lines between them (min: $MinSpacing)"
        }
    }
    
    # 3. Check for inline ornaments (ornament not alone on line)
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ($line -match "\S.*$([regex]::Escape($Pattern))" -or $line -match "$([regex]::Escape($Pattern)).*\S") {
            # Exclude code blocks
            $inCodeBlockCheck = $false
            for ($k = 0; $k -le $i; $k++) {
                if ($lines[$k].Trim() -match '^```') {
                    $inCodeBlockCheck = -not $inCodeBlockCheck
                }
            }
            if (-not $inCodeBlockCheck) {
                $violations += "VIOLATION: Inline ornament detected on line $($i+1)"
            }
        }
    }
    
    # Determine status
    if ($violations.Count -eq 0) {
        $status = "✅ COMPLIANT"
        $compliantFiles++
    } else {
        $status = "❌ VIOLATIONS"
        $violationFiles++
    }
    
    $results += @{
        File = $file.Name
        Ornaments = $ornamentCount
        Lines = $totalLines
        Ratio = "1:$ratio"
        Status = $status
        Violations = $violations
    }
}

# Display results
Write-Host "=== FILE-BY-FILE RESULTS ===`n" -ForegroundColor Cyan

foreach ($result in $results) {
    Write-Host "File: $($result.File)" -ForegroundColor White
    Write-Host "  Ornaments: $($result.Ornaments) | Lines: $($result.Lines) | Ratio: $($result.Ratio)" -ForegroundColor Gray
    
    if ($result.Status -eq "✅ COMPLIANT") {
        Write-Host "  Status: $($result.Status)" -ForegroundColor Green
    } else {
        Write-Host "  Status: $($result.Status)" -ForegroundColor Red
        foreach ($violation in $result.Violations) {
            Write-Host "    → $violation" -ForegroundColor Yellow
        }
    }
    Write-Host ""
}

# Summary
Write-Host "=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "Total Files Checked: $totalFiles" -ForegroundColor White
Write-Host "Compliant: $compliantFiles" -ForegroundColor Green
Write-Host "Violations: $violationFiles" -ForegroundColor $(if ($violationFiles -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($violationFiles -eq 0) {
    Write-Host "🎉 ALL FILES COMPLIANT WITH MAX_DENSITY_POLICY" -ForegroundColor Green
    exit 0
} else {
    Write-Host "⚠️  VIOLATIONS DETECTED - Review required" -ForegroundColor Red
    Write-Host ""
    Write-Host "Recommended Actions:" -ForegroundColor Yellow
    Write-Host "1. Remove excess ornaments from high-density files" -ForegroundColor Yellow
    Write-Host "2. Ensure minimum 5-line spacing between ornaments" -ForegroundColor Yellow
    Write-Host "3. Move inline ornaments to their own lines" -ForegroundColor Yellow
    Write-Host "4. Re-run this script after fixes" -ForegroundColor Yellow
    exit 1
}
