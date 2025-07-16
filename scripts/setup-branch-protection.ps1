# PowerShell script to set up branch protection rules via GitHub API
# Kenya Crypto-Fiat Payment Processor - Branch Protection Setup

Write-Host "🔒 Setting up Branch Protection Rules for QPESA Repository" -ForegroundColor Green
Write-Host "=========================================================" -ForegroundColor Green

# Repository details
$repoOwner = "KevQPSA"
$repoName = "qpesa"
$githubApi = "https://api.github.com"

# Check if GitHub token is provided
if (-not $env:GITHUB_TOKEN) {
    Write-Host "❌ GITHUB_TOKEN environment variable is required" -ForegroundColor Red
    Write-Host "Please set your GitHub Personal Access Token:" -ForegroundColor Yellow
    Write-Host "`$env:GITHUB_TOKEN = 'your_github_token_here'" -ForegroundColor White
    Write-Host ""
    Write-Host "To create a token:" -ForegroundColor Cyan
    Write-Host "1. Go to https://github.com/settings/tokens" -ForegroundColor White
    Write-Host "2. Click 'Generate new token (classic)'" -ForegroundColor White
    Write-Host "3. Select scopes: repo, admin:repo_hook" -ForegroundColor White
    Write-Host "4. Copy the token and set it as environment variable" -ForegroundColor White
    Write-Host ""
    Write-Host "Then run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host "🔧 Setting up Main Branch Protection..." -ForegroundColor Yellow

# Headers for API requests
$headers = @{
    'Authorization' = "token $env:GITHUB_TOKEN"
    'Accept' = 'application/vnd.github.v3+json'
    'Content-Type' = 'application/json'
}

# Main branch protection rules
$mainProtection = @{
    required_status_checks = @{
        strict = $true
        contexts = @(
            "Backend Tests",
            "Frontend Tests", 
            "Security Scan",
            "JIRA Integration",
            "Code Quality Check",
            "Branch Protection Check"
        )
    }
    enforce_admins = $true
    required_pull_request_reviews = @{
        required_approving_review_count = 2
        dismiss_stale_reviews = $true
        require_code_owner_reviews = $true
        restrict_pushes = $true
    }
    restrictions = $null
    required_linear_history = $true
    allow_force_pushes = $false
    allow_deletions = $false
    block_creations = $false
} | ConvertTo-Json -Depth 4

# Apply main branch protection
Write-Host "📡 Applying main branch protection rules..." -ForegroundColor Cyan
try {
    $mainResponse = Invoke-RestMethod -Uri "$githubApi/repos/$repoOwner/$repoName/branches/main/protection" -Method Put -Headers $headers -Body $mainProtection
    Write-Host "✅ Main branch protection rules applied successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to apply main branch protection" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response: $responseBody" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "🔧 Setting up Develop Branch Protection..." -ForegroundColor Yellow

# Check if develop branch exists
Write-Host "📡 Checking if develop branch exists..." -ForegroundColor Cyan
try {
    $developBranch = Invoke-RestMethod -Uri "$githubApi/repos/$repoOwner/$repoName/branches/develop" -Method Get -Headers $headers
    Write-Host "✅ Develop branch exists" -ForegroundColor Green
} catch {
    Write-Host "📝 Creating develop branch..." -ForegroundColor Yellow
    
    try {
        # Get main branch SHA
        $mainBranch = Invoke-RestMethod -Uri "$githubApi/repos/$repoOwner/$repoName/git/refs/heads/main" -Method Get -Headers $headers
        $mainSha = $mainBranch.object.sha
        
        # Create develop branch
        $createDevelop = @{
            ref = "refs/heads/develop"
            sha = $mainSha
        } | ConvertTo-Json
        
        $developCreateResponse = Invoke-RestMethod -Uri "$githubApi/repos/$repoOwner/$repoName/git/refs" -Method Post -Headers $headers -Body $createDevelop
        Write-Host "✅ Develop branch created successfully" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Could not create develop branch: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# Develop branch protection rules
$developProtection = @{
    required_status_checks = @{
        strict = $true
        contexts = @(
            "Backend Tests",
            "Frontend Tests",
            "JIRA Integration",
            "Branch Protection Check"
        )
    }
    enforce_admins = $false
    required_pull_request_reviews = @{
        required_approving_review_count = 1
        dismiss_stale_reviews = $true
        require_code_owner_reviews = $false
    }
    restrictions = $null
    allow_force_pushes = $false
    allow_deletions = $false
} | ConvertTo-Json -Depth 4

# Apply develop branch protection
Write-Host "📡 Applying develop branch protection rules..." -ForegroundColor Cyan
try {
    $developResponse = Invoke-RestMethod -Uri "$githubApi/repos/$repoOwner/$repoName/branches/develop/protection" -Method Put -Headers $headers -Body $developProtection
    Write-Host "✅ Develop branch protection rules applied successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to apply develop branch protection" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response: $responseBody" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "🎉 Branch Protection Setup Complete!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""
Write-Host "✅ Main Branch Protection:" -ForegroundColor Cyan
Write-Host "   - 2 required reviewers" -ForegroundColor White
Write-Host "   - Code owner reviews required" -ForegroundColor White
Write-Host "   - Status checks required" -ForegroundColor White
Write-Host "   - Linear history enforced" -ForegroundColor White
Write-Host "   - No force pushes allowed" -ForegroundColor White
Write-Host ""
Write-Host "✅ Develop Branch Protection:" -ForegroundColor Cyan
Write-Host "   - 1 required reviewer" -ForegroundColor White
Write-Host "   - Status checks required" -ForegroundColor White
Write-Host "   - No force pushes allowed" -ForegroundColor White
Write-Host ""
Write-Host "🔗 View branch protection settings:" -ForegroundColor Yellow
Write-Host "   https://github.com/$repoOwner/$repoName/settings/branches" -ForegroundColor White
Write-Host ""
Write-Host "🧪 Test the protection by creating a PR:" -ForegroundColor Yellow
Write-Host "   git checkout -b feature/test-branch-protection" -ForegroundColor White
Write-Host "   git commit -m 'Test: Branch protection rules'" -ForegroundColor White
Write-Host "   git push origin feature/test-branch-protection" -ForegroundColor White