# P-OS Week 4 Sovereignty Exam - Test 1: W11 Removal
# Purpose: Induce constitutional failure and verify fail-closed behavior
# Date: 2026-05-09

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$W11Contract = "$ProjectRoot\.lingma\contracts\w11_enforcement_contract.yaml"
$W11Backup = "$W11Contract.backup_week4_test"
$ResultsDir = "$ProjectRoot\archive\week4_sovereignty_exam"

if (-not (Test-Path $ResultsDir)) {
    New-Item -ItemType Directory -Force -Path $ResultsDir | Out-Null
}

Write-Host "`n=== WEEK 4 TEST 1: W11 REMOVAL / CONSTITUTIONAL FAILURE ===" -ForegroundColor Cyan

# Step 1: Capture pre-test state
Write-Host "`n[STEP 1] Capturing baseline state..." -ForegroundColor Yellow
$preState = Get-Content "$ProjectRoot\runtime\constitutional_state.json" | ConvertFrom-Json
Write-Host "  Pre-test state: $($preState.state)" -ForegroundColor Green
$preState | ConvertTo-Json | Out-File "$ResultsDir\test1_pre_state.json" -Encoding UTF8

$startTime = Get-Date

# Step 2: Remove W11 contract (induce failure)
Write-Host "`n[STEP 2] Removing W11 contract to induce constitutional failure..." -ForegroundColor Yellow
if (Test-Path $W11Contract) {
    Rename-Item $W11Contract $W11Backup
    Write-Host "  W11 contract removed (backed up to .backup_week4_test)" -ForegroundColor Green
} else {
    Write-Host "  ERROR: W11 contract not found at $W11Contract" -ForegroundColor Red
    exit 1
}

# Step 3: Trigger runtime guard (should detect failure)
Write-Host "`n[STEP 3] Executing runtime guard (expecting CONSTITUTIONAL_FAILURE)..." -ForegroundColor Yellow
$guardOutput = & "$ProjectRoot\scripts\runtime_constitution_guard.ps1" -Mode deploy-check 2>&1
$exitCode = $LASTEXITCODE

Write-Host "  Runtime guard exit code: $exitCode" -ForegroundColor $(if ($exitCode -ne 0) { "Green" } else { "Red" })
Write-Host "  Expected: Exit code 1 (deployment blocked)"

# Step 4: Verify state transition
Write-Host "`n[STEP 4] Verifying state transition..." -ForegroundColor Yellow
Start-Sleep -Milliseconds 500  # Allow state file to update
$postState = Get-Content "$ProjectRoot\runtime\constitutional_state.json" | ConvertFrom-Json
Write-Host "  Post-removal state: $($postState.state)" -ForegroundColor $(if ($postState.state -eq "CONSTITUTIONAL_FAILURE" -or $postState.state -eq "IMMUTABLE_FREEZE") { "Green" } else { "Red" })
$postState | ConvertTo-Json -Depth 10 | Out-File "$ResultsDir\test1_post_state.json" -Encoding UTF8

$transitionTime = (Get-Date) - $startTime
Write-Host "  Transition time: $($transitionTime.TotalSeconds)s (target: <1s)" -ForegroundColor $(if ($transitionTime.TotalSeconds -lt 1) { "Green" } else { "Yellow" })

# Step 5: Verify deployment blocking
Write-Host "`n[STEP 5] Verifying deployment is blocked..." -ForegroundColor Yellow
if ($exitCode -ne 0) {
    Write-Host "  ✅ PASS: Deployment BLOCKED (exit code $exitCode)" -ForegroundColor Green
    $deploymentBlocked = $true
} else {
    Write-Host "  ❌ FAIL: Deployment NOT blocked (exit code $exitCode)" -ForegroundColor Red
    $deploymentBlocked = $false
}

# Step 6: Check for emergency capsule
Write-Host "`n[STEP 6] Checking for emergency capsule generation..." -ForegroundColor Yellow
$capsules = Get-ChildItem "$ProjectRoot\data\capsules\emergency_*.zip" -ErrorAction SilentlyContinue
if ($capsules.Count -gt 0) {
    $latestCapsule = $capsules | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    Write-Host "  ✅ Emergency capsule generated: $($latestCapsule.Name)" -ForegroundColor Green
    $capsuleGenerated = $true
} else {
    Write-Host "  ⚠️ No emergency capsule found (may be expected if freeze not triggered)" -ForegroundColor Yellow
    $capsuleGenerated = $false
}

# Step 7: Restore W11 contract
Write-Host "`n[STEP 7] Restoring W11 contract..." -ForegroundColor Yellow
if (Test-Path $W11Backup) {
    Rename-Item $W11Backup $W11Contract
    Write-Host "  W11 contract restored" -ForegroundColor Green
} else {
    Write-Host "  ERROR: Backup not found at $W11Backup" -ForegroundColor Red
}

# Step 8: Verify recovery
Write-Host "`n[STEP 8] Verifying recovery to HEALTHY..." -ForegroundColor Yellow
Start-Sleep -Milliseconds 500
$recoveryOutput = & "$ProjectRoot\scripts\runtime_constitution_guard.ps1" -Mode self-test 2>&1
$recoveryState = Get-Content "$ProjectRoot\runtime\constitutional_state.json" | ConvertFrom-Json
Write-Host "  Recovery state: $($recoveryState.state)" -ForegroundColor $(if ($recoveryState.state -eq "HEALTHY") { "Green" } else { "Red" })
$recoveryState | ConvertTo-Json -Depth 10 | Out-File "$ResultsDir\test1_recovery_state.json" -Encoding UTF8

$recoveryTime = (Get-Date) - $startTime
Write-Host "  Total recovery time: $($recoveryTime.TotalSeconds)s (target: <5s)" -ForegroundColor $(if ($recoveryTime.TotalSeconds -lt 5) { "Green" } else { "Yellow" })

# Step 9: Generate test result
Write-Host "`n=== TEST 1 RESULTS ===" -ForegroundColor Cyan

$testResult = @{
    test_name = "W11_Removal_Constitutional_Failure"
    timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    pre_state = $preState.state
    post_state = $postState.state
    recovery_state = $recoveryState.state
    transition_time_seconds = $transitionTime.TotalSeconds
    recovery_time_seconds = $recoveryTime.TotalSeconds
    deployment_blocked = $deploymentBlocked
    emergency_capsule_generated = $capsuleGenerated
    success = ($postState.state -in @("CONSTITUTIONAL_FAILURE", "IMMUTABLE_FREEZE")) -and 
              $deploymentBlocked -and 
              ($recoveryState.state -eq "HEALTHY") -and
              ($recoveryTime.TotalSeconds -lt 5)
}

$testResult | ConvertTo-Json -Depth 10 | Out-File "$ResultsDir\test1_results.json" -Encoding UTF8

if ($testResult.success) {
    Write-Host "✅ TEST 1 PASSED: Constitutional failure induced and recovered successfully" -ForegroundColor Green
    Write-Host "   - State transition: $($preState.state) → $($postState.state) → $($recoveryState.state)" -ForegroundColor Green
    Write-Host "   - Deployment blocked: $deploymentBlocked" -ForegroundColor Green
    Write-Host "   - Recovery time: $($recoveryTime.TotalSeconds)s" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ TEST 1 FAILED: See results for details" -ForegroundColor Red
    Write-Host "   - Success criteria not met" -ForegroundColor Red
    exit 1
}
