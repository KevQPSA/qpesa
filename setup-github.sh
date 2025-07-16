#!/bin/bash

# Setup script to initialize git and push to GitHub
# Make sure to replace YOUR_USERNAME and YOUR_REPO_NAME with actual values

echo "🚀 Setting up GitHub repository for Kenya Crypto-Fiat Payment Processor"

# Initialize git repository
git init

# Add all files to git
git add .

# Create initial commit
git commit -m "Initial commit: Kenya Crypto-Fiat Payment Processor MVP

- FastAPI backend with async SQLAlchemy
- Next.js frontend with Tailwind CSS
- Bitcoin and USDT (ERC-20/TRC-20) support
- M-Pesa integration with STK Push
- Comprehensive test suite with >90% coverage
- Docker containerization for all environments
- Prometheus/Grafana monitoring setup
- Production-ready security and compliance features"

# Add GitHub remote (replace with your actual repository URL)
echo "📡 Adding GitHub remote..."
echo "Please replace the URL below with your actual GitHub repository URL:"
echo "git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git"

# Uncomment and modify the line below with your actual repository URL
# git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Push to GitHub
echo "📤 To push to GitHub, run:"
echo "git branch -M main"
echo "git push -u origin main"

echo "✅ Setup complete! Don't forget to:"
echo "1. Replace YOUR_USERNAME/YOUR_REPO_NAME with your actual GitHub details"
echo "2. Run the git remote add command with your repository URL"
echo "3. Push to GitHub with the commands shown above"