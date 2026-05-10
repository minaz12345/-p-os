# P-OS Branch Protection Automation Script
# Purpose: Enable mandatory Constitutional Agent checks on main branch
# Date: 2026-05-10
# Usage: .\scripts\ENABLE_BRANCH_PROTECTION.ps1
# Prerequisites: GitHub CLI (gh) authenticated with admin rights

param(
    [Parameter(Mandatory=$false)]
    [string]$Repo = "minaz12345/-p-os",
    
    [Parameter(Mandatory=$false)]
    [string]$Branch = "main",
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipConfirmation = $false
)

# ============================================================================
# CONFIGURATION
# ============================================================================

$ColorSuccess = "Green"
$ColorWarning = "Yellow"
$ColorError = "Red"
$ColorInfo = "Cyan"

$RequiredStatusChecks = @(
    "Constitutional Review / 🏛️ Constitutional Compliance Check"
)

$RequiredApprovals = 1
$DismissStaleReviews = $true
$RequireCodeOwnerReviews = $false
$IncludeAdmins = $true
$AllowForcePushes = $false
$AllowDeletions = $false
$RequireLinearHistory = $true
$AllowMergeCommits = $true
$AllowSquashMerging = $true
$AllowRebaseMerging = $false

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

function Test-GitHubCLI {
    Write-Host "Checking GitHub CLI installation... " -NoNewline
    try {
        $version = gh --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "INSTALLED"
            Write-Host "Version: $($version[0])" -ForegroundColor Gray
            return $true
        } else {
            Write-Error-Custom "NOT FOUND"
            return $false
        }
    } catch {
        Write-Error-Custom "ERROR: $_"
        return $false
    }
}

function Test-GitHubAuth {
    Write-Host "Checking GitHub authentication... " -NoNewline
    try {
        $authStatus = gh auth status 2>&1
        if ($authStatus -match "Logged in") {
            Write-Success "AUTHENTICATED"
            $account = ($authStatus | Select-String "github.com") -replace ".*github.com:\s*", ""
            Write-Host "Account: $account" -ForegroundColor Gray
            return $true
        } else {
            Write-Error-Custom "NOT AUTHENTICATED"
            Write-Host "Run: gh auth login" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Error-Custom "ERROR: $_"
        return $false
    }
}

function Test-AdminPermissions {
    Write-Host "Checking admin permissions for $Repo... " -NoNewline
    try {
        $repoInfo = gh repo view $Repo --json viewerPermission 2>&1
        $permission = ($repoInfo | ConvertFrom-Json).viewerPermission
        
        if ($permission -eq "ADMIN") {
            Write-Success "ADMIN ACCESS CONFIRMED"
            return $true
        } else {
            Write-Error-Custom "INSUFFICIENT PERMISSIONS (current: $permission)"
            Write-Host "Admin access required to configure branch protection" -ForegroundColor Yellow
            return $false
        }
    } catch {
        Write-Error-Custom "ERROR: $_"
        return $false
    }
}

function Get-CurrentProtection {
    Write-Step "Fetching current branch protection rules"
    
    try {
        $protection = gh api repos/$Repo/branches/$Branch/protection 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Current protection rules retrieved"
            return ($protection | ConvertFrom-Json)
        } else {
            Write-Warning "No existing protection rules found (or API error)"
            return $null
        }
    } catch {
        Write-Warning "Could not fetch protection rules: $_"
        return $null
    }
}

function Confirm-Action {
    if ($SkipConfirmation) { return $true }
    
    Write-Host "`n" -NoNewline
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor $ColorWarning
    Write-Host "║         BRANCH PROTECTION CONFIGURATION PREVIEW          ║" -ForegroundColor $ColorWarning
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor $ColorWarning
    Write-Host ""
    Write-Host "Repository: $Repo" -ForegroundColor White
    Write-Host "Branch: $Branch" -ForegroundColor White
    Write-Host ""
    Write-Host "Configuration:" -ForegroundColor Cyan
    Write-Host "  Required Status Checks: $($RequiredStatusChecks -join ', ')" -ForegroundColor Gray
    Write-Host "  Required Approvals: $RequiredApprovals" -ForegroundColor Gray
    Write-Host "  Dismiss Stale Reviews: $DismissStaleReviews" -ForegroundColor Gray
    Write-Host "  Include Administrators: $IncludeAdmins" -ForegroundColor Gray
    Write-Host "  Allow Force Pushes: $AllowForcePushes" -ForegroundColor Gray
    Write-Host "  Allow Deletions: $AllowDeletions" -ForegroundColor Gray
    Write-Host "  Require Linear History: $RequireLinearHistory" -ForegroundColor Gray
    Write-Host ""
    Write-Host "⚠️  WARNING: This will enforce Constitutional Agent checks on ALL PRs" -ForegroundColor Yellow
    Write-Host "⚠️  Even administrators will be subject to these rules" -ForegroundColor Yellow
    Write-Host ""
    
    $confirm = Read-Host "Proceed with configuration? (yes/no)"
    return ($confirm -eq "yes" -or $confirm -eq "y")
}

function Invoke-EnableProtection {
    Write-Step "Applying branch protection rules"
    
    # Build JSON payload
    $payload = @{
        required_status_checks = @{
            strict = $true
            contexts = $RequiredStatusChecks
        }
        enforce_admins = $IncludeAdmins
        required_pull_request_reviews = @{
            dismiss_stale_reviews = $DismissStaleReviews
            require_code_owner_reviews = $RequireCodeOwnerReviews
            required_approving_review_count = $RequiredApprovals
        }
        restrictions = $null
        allow_force_pushes = $AllowForcePushes
        allow_deletions = $AllowDeletions
        required_linear_history = $RequireLinearHistory
        allow_auto_merge = $false
        merge_commit_allowed = $AllowMergeCommits
        squash_merge_allowed = $AllowSquashMerging
        rebase_merge_allowed = $AllowRebaseMerging
    } | ConvertTo-Json -Depth 10
    
    if ($DryRun) {
        Write-Warning "DRY RUN MODE - Would execute:"
        Write-Host "gh api repos/$Repo/branches/$Branch/protection -X PUT -F '$payload'" -ForegroundColor Gray
        return $true
    }
    
    try {
        Write-Host "Sending API request to GitHub... " -NoNewline
        $result = gh api repos/$Repo/branches/$Branch/protection `
            --method PUT `
            --input - <<< $payload 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Branch protection enabled successfully"
            return $true
        } else {
            Write-Error-Custom "API request failed"
            Write-Host $result -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Error-Custom "Exception: $_"
        return $false
    }
}

function Invoke-VerifyProtection {
    Write-Step "Verifying branch protection configuration"
    
    try {
        $protection = gh api repos/$Repo/branches/$Branch/protection 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Failed to verify protection rules"
            return $false
        }
        
        $config = $protection | ConvertFrom-Json
        
        Write-Host "`nVerification Results:" -ForegroundColor Cyan
        Write-Host "  Status Checks Enabled: $($config.required_status_checks.enabled)" -ForegroundColor $(if ($config.required_status_checks.enabled) { "Green" } else { "Red" })
        Write-Host "  Contexts: $($config.required_status_checks.contexts -join ', ')" -ForegroundColor Gray
        Write-Host "  Admins Enforced: $($config.enforce_admins.enabled)" -ForegroundColor $(if ($config.enforce_admins.enabled) { "Green" } else { "Red" })
        Write-Host "  Required Reviews: $($config.required_pull_request_reviews.required_approving_review_count)" -ForegroundColor Gray
        Write-Host "  Force Pushes Allowed: $($config.allow_force_pushes.enabled)" -ForegroundColor $(if (-not $config.allow_force_pushes.enabled) { "Green" } else { "Yellow" })
        Write-Host "  Deletions Allowed: $($config.allow_deletions.enabled)" -ForegroundColor $(if (-not $config.allow_deletions.enabled) { "Green" } else { "Yellow" })
        
        # Validate critical settings
        $allCorrect = $true
        
        if (-not $config.required_status_checks.enabled) {
            Write-Error-Custom "CRITICAL: Status checks not enabled"
            $allCorrect = $false
        }
        
        if (-not $config.enforce_admins.enabled) {
            Write-Warning "WARNING: Admin enforcement not enabled"
        }
        
        if ($config.allow_force_pushes.enabled) {
            Write-Warning "WARNING: Force pushes still allowed"
        }
        
        if ($allCorrect) {
            Write-Success "All critical protections verified"
            return $true
        } else {
            Write-Error-Custom "Some protections missing or misconfigured"
            return $false
        }
    } catch {
        Write-Error-Custom "Verification failed: $_"
        return $false
    }
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

function Invoke-BranchProtectionSetup {
    Write-Host "`n" -NoNewline
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor $ColorInfo
    Write-Host "║   P-OS Branch Protection - Constitutional Enforcement    ║" -ForegroundColor $ColorInfo
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor $ColorInfo
    Write-Host ""
    
    # Pre-flight checks
    Write-Step "PHASE 1: Pre-flight Checks"
    
    $checksPassed = $true
    $checksPassed = $checksPassed -and (Test-GitHubCLI)
    $checksPassed = $checksPassed -and (Test-GitHubAuth)
    $checksPassed = $checksPassed -and (Test-AdminPermissions)
    
    if (-not $checksPassed) {
        Write-Error-Custom "Pre-flight checks FAILED. Fix issues before proceeding."
        exit 1
    }
    
    # Show current state
    Write-Step "PHASE 2: Current State Analysis"
    $currentProtection = Get-CurrentProtection
    
    if ($currentProtection) {
        Write-Host "`nCurrent protection is ACTIVE. This will UPDATE existing rules." -ForegroundColor Yellow
    } else {
        Write-Host "`nNo existing protection rules. This will CREATE new rules." -ForegroundColor Green
    }
    
    # Confirmation
    Write-Step "PHASE 3: Configuration Review"
    
    if (-not (Confirm-Action)) {
        Write-Warning "Operation cancelled by user"
        exit 0
    }
    
    # Apply protection
    Write-Step "PHASE 4: Applying Configuration"
    
    if (-not (Invoke-EnableProtection)) {
        Write-Error-Custom "Failed to enable branch protection"
        exit 1
    }
    
    # Verify
    Write-Step "PHASE 5: Verification"
    
    if (-not (Invoke-VerifyProtection)) {
        Write-Error-Custom "Verification failed - manual review required"
        exit 1
    }
    
    # Success summary
    Write-Host "`n" -NoNewline
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor $ColorSuccess
    Write-Host "║       BRANCH PROTECTION SUCCESSFULLY ENABLED             ║" -ForegroundColor $ColorSuccess
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor $ColorSuccess
    Write-Host ""
    Write-Host "Repository: $Repo" -ForegroundColor White
    Write-Host "Branch: $Branch" -ForegroundColor White
    Write-Host ""
    Write-Host "What this means:" -ForegroundColor Cyan
    Write-Host "  ✅ All PRs must pass Constitutional Agent review" -ForegroundColor Green
    Write-Host "  ✅ Minimum 1 approval required" -ForegroundColor Green
    Write-Host "  ✅ Administrators are subject to same rules" -ForegroundColor Green
    Write-Host "  ✅ Force pushes and deletions blocked" -ForegroundColor Green
    Write-Host "  ✅ Linear history enforced" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Create a test PR to verify workflow triggers" -ForegroundColor White
    Write-Host "  2. Confirm Constitutional Agent check appears in PR" -ForegroundColor White
    Write-Host "  3. Attempt merge without passing checks (should be blocked)" -ForegroundColor White
    Write-Host "  4. Document in team onboarding materials" -ForegroundColor White
    Write-Host ""
    
    Write-Success "P-OS MAIN BRANCH IS NOW CONSTITUTIONALLY PROTECTED"
}

# Execute
Invoke-BranchProtectionSetup
