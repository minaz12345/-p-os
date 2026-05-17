# Verify Branch Protection Configuration
# Purpose: Ensure constitutional review cannot be bypassed
# Usage: .\scripts\verify_branch_protection.ps1

Write-Host "=== BRANCH PROTECTION VERIFICATION ===" -ForegroundColor Cyan
Write-Host ""

# Check if GitHub CLI is available
try {
    $ghVersion = gh --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ ERROR: GitHub CLI (gh) not found or not authenticated" -ForegroundColor Red
        Write-Host "Install from: https://cli.github.com/" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✅ GitHub CLI available" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Cannot execute gh command" -ForegroundColor Red
    exit 1
}

# Get current repository info
try {
    $repoInfo = gh repo view --json nameWithOwner -q '.nameWithOwner' 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ ERROR: Not in a GitHub repository or not authenticated" -ForegroundColor Red
        exit 1
    }
    Write-Host "Repository: $repoInfo" -ForegroundColor Cyan
} catch {
    Write-Host "❌ ERROR: Cannot determine repository" -ForegroundColor Red
    exit 1
}

# Check main branch protection
Write-Host ""
Write-Host "Checking main branch protection..." -ForegroundColor Yellow

try {
    $protection = gh api repos/$repoInfo/branches/main/protection 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ CRITICAL: Cannot retrieve branch protection settings" -ForegroundColor Red
        Write-Host "Error: $protection" -ForegroundColor Red
        exit 1
    }
    
    # Parse JSON response
    $protectionJson = $protection | ConvertFrom-Json
    
    # Check required status checks
    if ($protectionJson.required_status_checks) {
        $contexts = $protectionJson.required_status_checks.contexts
        
        Write-Host ""
        Write-Host "Required Status Checks:" -ForegroundColor Cyan
        
        if ($contexts -contains "Constitutional Compliance Check") {
            Write-Host "  ✅ Constitutional Compliance Check - ENABLED" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Constitutional Compliance Check - MISSING" -ForegroundColor Red
            Write-Host ""
            Write-Host "CRITICAL: Branch protection is not enforcing constitutional review!" -ForegroundColor Red
            Write-Host ""
            Write-Host "To fix, run:" -ForegroundColor Yellow
            Write-Host "  gh api repos/$repoInfo/branches/main/protection \`" -ForegroundColor White
            Write-Host "    --method PUT \`" -ForegroundColor White
            Write-Host "    -F required_status_checks='{\""contexts\"":[\""Constitutional Compliance Check\""],\""strict\"":true}'" -ForegroundColor White
            exit 1
        }
        
        # List all required checks
        foreach ($context in $contexts) {
            if ($context -ne "Constitutional Compliance Check") {
                Write-Host "  • $context" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "  ❌ CRITICAL: No required status checks configured" -ForegroundColor Red
        Write-Host ""
        Write-Host "Branch protection does not require any status checks!" -ForegroundColor Red
        exit 1
    }
    
    # Check other protection settings
    Write-Host ""
    Write-Host "Additional Protection Settings:" -ForegroundColor Cyan
    
    if ($protectionJson.required_pull_request_reviews) {
        $requiredReviews = $protectionJson.required_pull_request_reviews.required_approving_review_count
        Write-Host "  ✅ Required approvals: $requiredReviews" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  No required pull request reviews" -ForegroundColor Yellow
    }
    
    if ($protectionJson.enforce_admins) {
        Write-Host "  ✅ Admin enforcement: ENABLED" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Admin enforcement: DISABLED (admins can bypass)" -ForegroundColor Yellow
    }
    
    if ($protectionJson.allow_force_pushes) {
        Write-Host "  ❌ Force pushes: ALLOWED (security risk)" -ForegroundColor Red
    } else {
        Write-Host "  ✅ Force pushes: BLOCKED" -ForegroundColor Green
    }
    
    if ($protectionJson.allow_deletions) {
        Write-Host "  ❌ Branch deletion: ALLOWED (security risk)" -ForegroundColor Red
    } else {
        Write-Host "  ✅ Branch deletion: BLOCKED" -ForegroundColor Green
    }
    
} catch {
    Write-Host "❌ ERROR: Exception during branch protection check" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "✅ BRANCH PROTECTION VERIFIED" -ForegroundColor Green
Write-Host "Constitutional review enforcement is active" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

exit 0
