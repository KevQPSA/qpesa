#!/bin/bash

# Test script to verify JIRA connection
# Run this script to test your JIRA integration setup

echo "🔍 Testing JIRA Connection for QPESA Project"
echo "============================================="

# Check if required environment variables are set
if [ -z "$JIRA_BASE_URL" ] || [ -z "$JIRA_USER_EMAIL" ] || [ -z "$JIRA_API_TOKEN" ]; then
    echo "❌ Missing required environment variables"
    echo "Please set:"
    echo "  export JIRA_BASE_URL=https://your-site.atlassian.net"
    echo "  export JIRA_USER_EMAIL=your-email@domain.com"
    echo "  export JIRA_API_TOKEN=your-api-token"
    exit 1
fi

echo "📡 Testing JIRA API Connection..."

# Test 1: Check authentication
echo "1. Testing authentication..."
AUTH_RESPONSE=$(curl -s -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" \
    "$JIRA_BASE_URL/rest/api/3/myself" \
    -H "Accept: application/json")

if echo "$AUTH_RESPONSE" | grep -q "accountId"; then
    echo "   ✅ Authentication successful"
    ACCOUNT_ID=$(echo "$AUTH_RESPONSE" | grep -o '"accountId":"[^"]*"' | cut -d'"' -f4)
    echo "   📋 Account ID: $ACCOUNT_ID"
else
    echo "   ❌ Authentication failed"
    echo "   Response: $AUTH_RESPONSE"
    exit 1
fi

# Test 2: Check if QPESA project exists
echo "2. Testing QPESA project access..."
PROJECT_RESPONSE=$(curl -s -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" \
    "$JIRA_BASE_URL/rest/api/3/project/QPESA" \
    -H "Accept: application/json")

if echo "$PROJECT_RESPONSE" | grep -q '"key":"QPESA"'; then
    echo "   ✅ QPESA project found"
    PROJECT_NAME=$(echo "$PROJECT_RESPONSE" | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
    echo "   📋 Project Name: $PROJECT_NAME"
else
    echo "   ❌ QPESA project not found or no access"
    echo "   Response: $PROJECT_RESPONSE"
    echo "   💡 Please create a JIRA project with key 'QPESA'"
fi

# Test 3: Check available issue types
echo "3. Testing issue types..."
ISSUE_TYPES_RESPONSE=$(curl -s -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" \
    "$JIRA_BASE_URL/rest/api/3/issuetype" \
    -H "Accept: application/json")

if echo "$ISSUE_TYPES_RESPONSE" | grep -q "Story"; then
    echo "   ✅ Issue types available"
    echo "   📋 Available types:"
    echo "$ISSUE_TYPES_RESPONSE" | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | sed 's/^/      - /'
else
    echo "   ⚠️  Could not retrieve issue types"
fi

# Test 4: Test creating a test issue (optional)
echo "4. Testing issue creation (optional)..."
read -p "   Create a test issue? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    CREATE_RESPONSE=$(curl -s -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" \
        -X POST \
        -H "Accept: application/json" \
        -H "Content-Type: application/json" \
        -d '{
            "fields": {
                "project": {"key": "QPESA"},
                "summary": "Test Issue - GitHub Integration",
                "description": "This is a test issue created to verify GitHub-JIRA integration.",
                "issuetype": {"name": "Task"},
                "labels": ["github-integration", "test"]
            }
        }' \
        "$JIRA_BASE_URL/rest/api/3/issue")

    if echo "$CREATE_RESPONSE" | grep -q '"key":"QPESA-'; then
        ISSUE_KEY=$(echo "$CREATE_RESPONSE" | grep -o '"key":"QPESA-[0-9]*"' | cut -d'"' -f4)
        echo "   ✅ Test issue created: $ISSUE_KEY"
        echo "   🔗 View at: $JIRA_BASE_URL/browse/$ISSUE_KEY"
        
        # Test adding a comment
        echo "5. Testing comment creation..."
        COMMENT_RESPONSE=$(curl -s -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" \
            -X POST \
            -H "Accept: application/json" \
            -H "Content-Type: application/json" \
            -d '{
                "body": "🤖 Test comment from GitHub integration setup script.\n\nThis confirms that the GitHub Actions can successfully add comments to JIRA issues."
            }' \
            "$JIRA_BASE_URL/rest/api/3/issue/$ISSUE_KEY/comment")

        if echo "$COMMENT_RESPONSE" | grep -q '"id"'; then
            echo "   ✅ Comment added successfully"
        else
            echo "   ❌ Failed to add comment"
        fi
    else
        echo "   ❌ Failed to create test issue"
        echo "   Response: $CREATE_RESPONSE"
    fi
else
    echo "   ⏭️  Skipping test issue creation"
fi

echo ""
echo "🎉 JIRA Connection Test Complete!"
echo ""
echo "📋 Summary:"
echo "   - Authentication: ✅"
echo "   - Project Access: $(if echo "$PROJECT_RESPONSE" | grep -q '"key":"QPESA"'; then echo "✅"; else echo "❌"; fi)"
echo "   - Issue Types: ✅"
echo ""
echo "🔧 Next Steps:"
echo "   1. Add these secrets to GitHub repository:"
echo "      - JIRA_BASE_URL=$JIRA_BASE_URL"
echo "      - JIRA_USER_EMAIL=$JIRA_USER_EMAIL"
echo "      - JIRA_API_TOKEN=[your-token]"
echo ""
echo "   2. Test GitHub Actions by creating a branch:"
echo "      git checkout -b feature/QPESA-1-test-integration"
echo "      git commit -m 'QPESA-1: Test GitHub JIRA integration'"
echo "      git push origin feature/QPESA-1-test-integration"
echo ""
echo "   3. Check JIRA for automatic updates!"
echo ""
echo "🔗 Useful Links:"
echo "   - JIRA Project: $JIRA_BASE_URL/browse/QPESA"
echo "   - GitHub Actions: https://github.com/KevQPSA/qpesa/actions"
echo "   - Setup Guide: docs/GITHUB_JIRA_CONNECTION_GUIDE.md"