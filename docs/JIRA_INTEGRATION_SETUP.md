# JIRA Integration Setup Guide

This guide will help you set up automated workflows between your GitHub repository and JIRA for the Kenya Crypto-Fiat Payment Processor project.

## 🎯 Overview

The integration provides:
- **Automated issue tracking** between GitHub and JIRA
- **CI/CD pipeline integration** with JIRA status updates
- **Release management** with automatic version creation
- **Smart branch and commit linking** to JIRA issues
- **Automated status transitions** based on development workflow

## 🔧 Prerequisites

1. **JIRA Cloud instance** (or JIRA Server with API access)
2. **GitHub repository** with admin access
3. **JIRA project** set up (recommended project key: `QPESA`)

## 📋 Setup Steps

### Step 1: Create JIRA API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **"Create API token"**
3. Give it a name: `GitHub Integration - QPESA`
4. Copy the generated token (you won't see it again!)

### Step 2: Configure GitHub Secrets

In your GitHub repository, go to **Settings → Secrets and variables → Actions** and add:

```
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_USER_EMAIL=your-email@domain.com
JIRA_API_TOKEN=your-api-token-from-step-1
```

### Step 3: Set Up JIRA Project

1. Create a new JIRA project with key `QPESA`
2. Set up these issue types:
   - **Epic** - Major features
   - **Story** - User stories
   - **Task** - Development tasks
   - **Bug** - Bug fixes
   - **Sub-task** - Subtasks

3. Configure workflow states:
   - **To Do** - Initial state
   - **In Progress** - Development started
   - **Code Review** - Pull request created
   - **Testing** - Deployed to staging
   - **Done** - Completed and deployed

### Step 4: Branch Naming Convention

Use this naming pattern to automatically link branches to JIRA issues:

```bash
# Feature branches
feature/QPESA-123-add-bitcoin-wallet
feature/QPESA-124-mpesa-integration

# Bug fix branches
bugfix/QPESA-125-fix-payment-validation

# Hotfix branches
hotfix/QPESA-126-critical-security-fix
```

### Step 5: Commit Message Format

Include JIRA issue keys in commit messages:

```bash
git commit -m "QPESA-123: Add Bitcoin wallet functionality

- Implement wallet creation
- Add address generation
- Update database schema"
```

## 🚀 Automated Workflows

### 1. **JIRA Integration Workflow** (`jira-integration.yml`)

**Triggers:**
- Push to any branch
- Pull request creation/updates
- GitHub issue creation

**Actions:**
- Extracts JIRA issue keys from branch names, commits, or PR titles
- Transitions JIRA issues based on GitHub events:
  - **Push to feature branch** → Transition to "In Progress"
  - **PR created** → Transition to "Code Review"
  - **PR merged** → Transition to "Done"
- Adds comments to JIRA issues with GitHub activity updates
- Creates JIRA issues from GitHub bug reports

### 2. **CI/CD Pipeline with JIRA** (`ci-cd-jira.yml`)

**Triggers:**
- Push to `main` or `develop`
- Pull requests

**Actions:**
- Runs comprehensive backend tests (Python)
- Runs frontend build and linting (Node.js)
- Updates JIRA issues with test results
- Deploys to staging (develop branch) or production (main branch)
- Transitions issues through workflow states

### 3. **Release Management** (`jira-release-management.yml`)

**Triggers:**
- GitHub release published
- Manual workflow dispatch

**Actions:**
- Creates JIRA version for the release
- Finds all JIRA issues included in the release
- Updates issues with release information
- Generates release reports
- Marks JIRA version as released

## 📝 Usage Examples

### Creating a Feature

1. **Create JIRA Issue**: Create a story in JIRA (e.g., `QPESA-200`)
2. **Create Branch**: 
   ```bash
   git checkout -b feature/QPESA-200-add-usdt-support
   ```
3. **Develop**: Make commits with JIRA key:
   ```bash
   git commit -m "QPESA-200: Add USDT ERC-20 support"
   ```
4. **Create PR**: Title should include `QPESA-200`
5. **Automatic Updates**: JIRA issue automatically transitions to "Code Review"

### Bug Fix Workflow

1. **Bug Reported**: Create bug in JIRA (`QPESA-201`)
2. **Fix Branch**:
   ```bash
   git checkout -b bugfix/QPESA-201-fix-mpesa-callback
   ```
3. **Commit Fix**:
   ```bash
   git commit -m "QPESA-201: Fix M-Pesa callback validation

   - Add proper phone number validation
   - Handle edge cases in callback processing"
   ```
4. **Deploy**: Merge triggers automatic deployment and JIRA updates

### Release Process

1. **Create Release**: Use GitHub releases with semantic versioning
2. **Automatic Processing**: 
   - JIRA version created automatically
   - All related issues updated
   - Release notes generated
   - Issues marked as released

## 🔍 Monitoring and Troubleshooting

### Check Workflow Status

1. Go to **Actions** tab in GitHub repository
2. Look for workflow runs and their status
3. Check logs for any JIRA API errors

### Common Issues

**Authentication Errors:**
- Verify JIRA API token is correct
- Check if email matches JIRA account
- Ensure base URL is correct (no trailing slash)

**Issue Not Found:**
- Verify JIRA issue key format (PROJECT-NUMBER)
- Check if issue exists in the specified project
- Ensure project key matches configuration

**Transition Failures:**
- Verify workflow transitions exist in JIRA
- Check if user has permission to transition issues
- Ensure issue is in correct state for transition

## 🎛️ Customization

### Modify Workflow States

Edit the workflow files to match your JIRA workflow:

```yaml
# In jira-integration.yml
- name: Transition JIRA Issue on PR
  uses: atlassian/gajira-transition@v3
  with:
    issue: ${{ steps.find-issue.outputs.issue }}
    transition: "Your Custom State"
```

### Add Custom Fields

Update JIRA issue creation with custom fields:

```yaml
fields: |
  {
    "labels": ["github-integration", "automated"],
    "priority": {"name": "High"},
    "customfield_10001": "Custom Value"
  }
```

### Project-Specific Configuration

Change the project key from `QPESA` to your project:

```yaml
with:
  project: YOUR_PROJECT_KEY
```

## 📊 Benefits

✅ **Automated Status Updates** - No manual JIRA updates needed
✅ **Full Traceability** - Complete audit trail from code to deployment
✅ **Release Management** - Automated version creation and tracking
✅ **Team Visibility** - Everyone sees real-time progress
✅ **Compliance** - Proper documentation for financial regulations
✅ **Efficiency** - Reduced manual work and context switching

## 🔗 Additional Resources

- [Atlassian GitHub Actions](https://github.com/atlassian/gajira)
- [JIRA REST API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

**Need Help?** Create an issue in the repository with the `jira-integration` label for assistance with setup or troubleshooting.