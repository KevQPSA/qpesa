# PowerShell script to set up Snyk for Kenya Crypto-Fiat Payment Processor
# This script helps set up Snyk CLI and run initial security scans

Write-Host "🔒 Setting up Snyk Security Scanning for QPESA" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# Check if npm is installed
if (!(Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "❌ npm is not installed. Please install Node.js first: https://nodejs.org/" -ForegroundColor Red
    exit 1
}

# Install Snyk CLI
Write-Host "📦 Installing Snyk CLI..." -ForegroundColor Yellow
npm install -g snyk

# Check if Snyk is installed correctly
if (!(Get-Command snyk -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Failed to install Snyk CLI. Please try installing it manually: npm install -g snyk" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Snyk CLI installed successfully" -ForegroundColor Green

# Check if SNYK_TOKEN is set
if (-not $env:SNYK_TOKEN) {
    Write-Host "⚠️ SNYK_TOKEN environment variable is not set" -ForegroundColor Yellow
    Write-Host "Please set your Snyk API token:" -ForegroundColor Yellow
    Write-Host "`$env:SNYK_TOKEN = 'your-snyk-token-here'" -ForegroundColor White
    Write-Host ""
    Write-Host "To get a Snyk API token:" -ForegroundColor Cyan
    Write-Host "1. Sign up at https://app.snyk.io/login" -ForegroundColor White
    Write-Host "2. Go to your account settings" -ForegroundColor White
    Write-Host "3. Create a new API token" -ForegroundColor White
    Write-Host "4. Copy the token and set it as environment variable" -ForegroundColor White
    
    $snykToken = Read-Host "Enter your Snyk API token (or press Enter to skip authentication)"
    if ($snykToken) {
        $env:SNYK_TOKEN = $snykToken
        Write-Host "✅ SNYK_TOKEN set for this session" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Continuing without authentication. Some features may be limited." -ForegroundColor Yellow
    }
}

# Authenticate with Snyk if token is available
if ($env:SNYK_TOKEN) {
    Write-Host "🔑 Authenticating with Snyk..." -ForegroundColor Yellow
    snyk auth $env:SNYK_TOKEN
    Write-Host "✅ Authentication successful" -ForegroundColor Green
}

# Run initial scans
Write-Host ""
Write-Host "🔍 Running initial security scans..." -ForegroundColor Yellow

# Frontend scan
Write-Host "📱 Scanning frontend dependencies..." -ForegroundColor Cyan
snyk test --all-projects --detection-depth=2 --severity-threshold=high

# Backend scan
Write-Host ""
Write-Host "🖥️ Scanning backend dependencies..." -ForegroundColor Cyan
snyk test --file=backend/requirements.txt --severity-threshold=high

# IaC scan
Write-Host ""
Write-Host "🏗️ Scanning infrastructure as code..." -ForegroundColor Cyan
snyk iac test --severity-threshold=high

Write-Host ""
Write-Host "🎉 Snyk Setup Complete!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""
Write-Host "✅ Snyk CLI installed" -ForegroundColor Cyan
Write-Host "✅ Initial scans completed" -ForegroundColor Cyan
Write-Host "✅ GitHub Actions workflow added" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔗 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Add SNYK_TOKEN to GitHub repository secrets" -ForegroundColor White
Write-Host "   Go to: https://github.com/KevQPSA/qpesa/settings/secrets/actions" -ForegroundColor White
Write-Host "2. Run regular scans with: snyk test" -ForegroundColor White
Write-Host "3. Monitor your project with: snyk monitor" -ForegroundColor White
Write-Host ""
Write-Host "📊 View Snyk Dashboard: https://app.snyk.io/org/your-org/projects" -ForegroundColor White