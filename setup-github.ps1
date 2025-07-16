# PowerShell script to setup GitHub repository
# Kenya Crypto-Fiat Payment Processor

Write-Host "🚀 Setting up GitHub repository for Kenya Crypto-Fiat Payment Processor" -ForegroundColor Green

# Check if git is installed
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git is not installed. Please install Git first: https://git-scm.com/download/win" -ForegroundColor Red
    exit 1
}

# Initialize git repository
Write-Host "📁 Initializing Git repository..." -ForegroundColor Yellow
git init

# Add all files to git
Write-Host "📝 Adding files to Git..." -ForegroundColor Yellow
git add .

# Create initial commit
Write-Host "💾 Creating initial commit..." -ForegroundColor Yellow
git commit -m "Initial commit: Kenya Crypto-Fiat Payment Processor MVP

- FastAPI backend with async SQLAlchemy
- Next.js frontend with Tailwind CSS
- Bitcoin and USDT (ERC-20/TRC-20) support
- M-Pesa integration with STK Push
- Comprehensive test suite with >90% coverage
- Docker containerization for all environments
- Prometheus/Grafana monitoring setup
- Production-ready security and compliance features"

Write-Host "✅ Git repository initialized successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📡 Next steps:" -ForegroundColor Cyan
Write-Host "1. Create a new repository on GitHub.com"
Write-Host "2. Copy your repository URL"
Write-Host "3. Run these commands with your actual repository URL:"
Write-Host ""
Write-Host "git remote add origin YOUR_GITHUB_URL_HERE" -ForegroundColor White
Write-Host "git branch -M main" -ForegroundColor White
Write-Host "git push -u origin main" -ForegroundColor White
Write-Host ""
Write-Host "🔐 If you haven't set up GitHub authentication, you may need to:" -ForegroundColor Yellow
Write-Host "- Use GitHub CLI: gh auth login"
Write-Host "- Or set up SSH keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh"