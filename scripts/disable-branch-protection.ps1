# PowerShell script to temporarily disable branch protection
# Kenya Crypto-Fiat Payment Processor - Temporary Protection Disable

Write-Host "Temporarily Disabling Branch Protection for Setup" -ForegroundColor Yellow
Write-Host "=================================================" -ForegroundColor Yellow

# Repository details
$repoOwner = "KevQPSA"
$repoName = "qpesa"
$githubApi = "https://api.github.com"

# Check if GitHub token is provided
if (-not $env:GITHUB_TOKEN) {
    Write-Host "GITHUB_TOKEN environment variable is required" -ForegroundColor Red
    exit 1
}

# Headers for API requests
$headers = @{
    Authorization = "token $env:GITHUB_TOKEN"
    Accept = "application/vnd.github.v3+json"
}

Write-Host "Disabling main branch protection..." -ForegroundColor Cyan
try {
    # Delete main branch protection
    Invoke-RestMethod -Uri "$githubApi/repos/$repoOwner/$repoName/branches/main/protection" -Method Delete -Headers $headers
    Write-Host "Main branch protection disabled" -ForegroundColor Green
} catch {
    Write-Host "Failed to disable main branch protection: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "Disabling develop branch protection..." -ForegroundColor Cyan
try {
    # Delete develop branch protection  
    Invoke-RestMethod -Uri "$githubApi/repos/$repoOwner/$repoName/branches/develop/protection" -Method Delete -Headers $headers
    Write-Host "Develop branch protection disabled" -ForegroundColor Green
} catch {
    Write-Host "Failed to disable develop branch protection: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Branch protection temporarily disabled!" -ForegroundColor Green
Write-Host "You can now push directly to main and develop branches" -ForegroundColor Yellow
Write-Host ""
Write-Host "IMPORTANT: Re-enable protection after merging by running:" -ForegroundColor Red
Write-Host ".\scripts\setup-branch-protection.ps1" -ForegroundColor White