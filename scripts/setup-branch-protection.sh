#!/bin/bash

# Script to set up branch protection rules via GitHub API
# Kenya Crypto-Fiat Payment Processor - Branch Protection Setup

echo "🔒 Setting up Branch Protection Rules for QPESA Repository"
echo "========================================================="

# Repository details
REPO_OWNER="KevQPSA"
REPO_NAME="qpesa"
GITHUB_API="https://api.github.com"

# Check if GitHub token is provided
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN environment variable is required"
    echo "Please set your GitHub Personal Access Token:"
    echo "export GITHUB_TOKEN=your_github_token_here"
    echo ""
    echo "To create a token:"
    echo "1. Go to https://github.com/settings/tokens"
    echo "2. Click 'Generate new token (classic)'"
    echo "3. Select scopes: repo, admin:repo_hook"
    echo "4. Copy the token and set it as environment variable"
    exit 1
fi

echo "🔧 Setting up Main Branch Protection..."

# Main branch protection rules
MAIN_PROTECTION='{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "Backend Tests",
      "Frontend Tests", 
      "Security Scan",
      "JIRA Integration",
      "Code Quality Check",
      "Branch Protection Check"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 2,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "restrict_pushes": true
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false
}'

# Apply main branch protection
echo "📡 Applying main branch protection rules..."
MAIN_RESPONSE=$(curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d "$MAIN_PROTECTION" \
  "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/branches/main/protection")

if echo "$MAIN_RESPONSE" | grep -q '"url"'; then
    echo "✅ Main branch protection rules applied successfully"
else
    echo "❌ Failed to apply main branch protection"
    echo "Response: $MAIN_RESPONSE"
fi

echo ""
echo "🔧 Setting up Develop Branch Protection..."

# Create develop branch if it doesn't exist
echo "📡 Checking if develop branch exists..."
DEVELOP_EXISTS=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/branches/develop" | grep -q '"name": "develop"' && echo "true" || echo "false")

if [ "$DEVELOP_EXISTS" = "false" ]; then
    echo "📝 Creating develop branch..."
    
    # Get main branch SHA
    MAIN_SHA=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
      "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/git/refs/heads/main" | \
      grep -o '"sha": "[^"]*"' | cut -d'"' -f4)
    
    # Create develop branch
    CREATE_DEVELOP='{
      "ref": "refs/heads/develop",
      "sha": "'$MAIN_SHA'"
    }'
    
    DEVELOP_CREATE_RESPONSE=$(curl -s -X POST \
      -H "Authorization: token $GITHUB_TOKEN" \
      -H "Accept: application/vnd.github.v3+json" \
      -d "$CREATE_DEVELOP" \
      "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/git/refs")
    
    if echo "$DEVELOP_CREATE_RESPONSE" | grep -q '"ref"'; then
        echo "✅ Develop branch created successfully"
    else
        echo "⚠️ Could not create develop branch: $DEVELOP_CREATE_RESPONSE"
    fi
fi

# Develop branch protection rules
DEVELOP_PROTECTION='{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "Backend Tests",
      "Frontend Tests",
      "JIRA Integration",
      "Branch Protection Check"
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}'

# Apply develop branch protection
echo "📡 Applying develop branch protection rules..."
DEVELOP_RESPONSE=$(curl -s -X PUT \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d "$DEVELOP_PROTECTION" \
  "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/branches/develop/protection")

if echo "$DEVELOP_RESPONSE" | grep -q '"url"'; then
    echo "✅ Develop branch protection rules applied successfully"
else
    echo "❌ Failed to apply develop branch protection"
    echo "Response: $DEVELOP_RESPONSE"
fi

echo ""
echo "🎉 Branch Protection Setup Complete!"
echo "=================================="
echo ""
echo "✅ Main Branch Protection:"
echo "   - 2 required reviewers"
echo "   - Code owner reviews required"
echo "   - Status checks required"
echo "   - Linear history enforced"
echo "   - No force pushes allowed"
echo ""
echo "✅ Develop Branch Protection:"
echo "   - 1 required reviewer"
echo "   - Status checks required"
echo "   - No force pushes allowed"
echo ""
echo "🔗 View branch protection settings:"
echo "   https://github.com/$REPO_OWNER/$REPO_NAME/settings/branches"
echo ""
echo "🧪 Test the protection by creating a PR:"
echo "   git checkout -b feature/test-branch-protection"
echo "   git commit -m 'Test: Branch protection rules'"
echo "   git push origin feature/test-branch-protection"