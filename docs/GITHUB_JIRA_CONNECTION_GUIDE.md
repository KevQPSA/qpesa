# GitHub to JIRA Connection Guide

This guide will walk you through connecting your GitHub repository (https://github.com/KevQPSA/qpesa) to JIRA for automated project management.

## 🎯 Overview

We'll set up bidirectional integration between GitHub and JIRA that will:
- Automatically create JIRA issues from GitHub issues
- Update JIRA issue status based on GitHub activity
- Link commits and PRs to JIRA issues
- Manage releases and deployments through JIRA

## 📋 Prerequisites

- GitHub repository: https://github.com/KevQPSA/qpesa ✅
- JIRA Cloud account (or JIRA Server)
- Admin access to both GitHub and JIRA

## 🔧 Step-by-Step Setup

### Step 1: Set Up JIRA Cloud Account

1. **Create JIRA Account** (if you don't have one):
   - Go to https://www.atlassian.com/software/jira
   - Click "Get it free" 
   - Sign up with your email
   - Choose "JIRA Software" for software development

2. **Create Your JIRA Site**:
   - Choose a site name (e.g., `qpesa.atlassian.net`)
   - This will be your JIRA_BASE_URL

### Step 2: Create JIRA Project

1. **Create New Project**:
   - In JIRA, click "Create project"
   - Choose "Scrum" or "Kanban" template
   - Project name: "QPESA - Kenya Crypto-Fiat Payment Processor"
   - Project key: **QPESA** (this is important!)
   - Click "Create"

2. **Configure Issue Types**:
   - Go to Project Settings → Issue Types
   - Ensure you have: Epic, Story, Task, Bug, Sub-task
   - Add "Security Issue" if not present

3. **Set Up Workflow**:
   - Go to Project Settings → Workflows
   - Configure these statuses:
     - **To Do** (initial state)
     - **In Progress** (development started)
     - **Code Review** (PR created)
     - **Testing** (deployed to staging)
     - **Done** (completed)

### Step 3: Generate JIRA API Token

1. **Go to Atlassian Account Settings**:
   - Visit: https://id.atlassian.com/manage-profile/security/api-tokens
   - Click "Create API token"

2. **Create Token**:
   - Label: "GitHub Integration - QPESA"
   - Click "Create"
   - **COPY THE TOKEN IMMEDIATELY** (you won't see it again!)

### Step 4: Configure GitHub Repository Secrets

1. **Go to GitHub Repository Settings**:
   - Visit: https://github.com/KevQPSA/qpesa/settings/secrets/actions
   - Click "New repository secret"

2. **Add These Secrets**:

   **Secret 1: JIRA_BASE_URL**
   ```
   Name: JIRA_BASE_URL
   Value: https://your-site-name.atlassian.net
   ```
   (Replace `your-site-name` with your actual JIRA site)

   **Secret 2: JIRA_USER_EMAIL**
   ```
   Name: JIRA_USER_EMAIL
   Value: your-email@domain.com
   ```
   (Use the email associated with your JIRA account)

   **Secret 3: JIRA_API_TOKEN**
   ```
   Name: JIRA_API_TOKEN
   Value: [paste the API token you copied]
   ```

### Step 5: Install GitHub for JIRA App (Optional but Recommended)

1. **Install the App**:
   - Go to your JIRA site
   - Navigate to Apps → Find new apps
   - Search for "GitHub for Jira"
   - Install the official Atlassian app

2. **Connect Repository**:
   - In JIRA, go to Apps → GitHub
   - Click "Connect GitHub account"
   - Authorize the connection
   - Select your repository: KevQPSA/qpesa

### Step 6: Test the Integration

1. **Create a Test JIRA Issue**:
   - In JIRA, create a new Story
   - Title: "Test GitHub Integration"
   - Note the issue key (e.g., QPESA-1)

2. **Create Test Branch**:
   ```bash
   git checkout -b feature/QPESA-1-test-integration
   git commit -m "QPESA-1: Test GitHub to JIRA integration setup"
   git push origin feature/QPESA-1-test-integration
   ```

3. **Check JIRA Issue**:
   - Go back to your JIRA issue
   - You should see a comment from GitHub Actions
   - The issue status should change to "In Progress"

4. **Create Pull Request**:
   - Create a PR with title: "QPESA-1: Test integration"
   - Check JIRA - status should change to "Code Review"

## 🚀 Usage Examples

### Branch Naming Convention
```bash
# Feature branches
feature/QPESA-123-add-bitcoin-wallet
feature/QPESA-124-mpesa-integration

# Bug fixes
bugfix/QPESA-125-fix-payment-validation

# Hotfixes
hotfix/QPESA-126-security-patch
```

### Commit Messages
```bash
git commit -m "QPESA-123: Add Bitcoin wallet functionality

- Implement wallet creation API
- Add address generation service
- Update database schema
- Add comprehensive tests"
```

### Pull Request Titles
```
QPESA-123: Add Bitcoin wallet functionality
QPESA-124: Integrate M-Pesa STK Push
```

## 🔍 Verification Checklist

After setup, verify these work:

- [ ] GitHub Actions workflows run without errors
- [ ] JIRA issues get comments from GitHub activity
- [ ] Issue status transitions automatically
- [ ] Branch names with JIRA keys are recognized
- [ ] Commit messages with JIRA keys link properly
- [ ] Pull requests update JIRA issues
- [ ] Security scans create JIRA issues when needed

## 🛠️ Troubleshooting

### Common Issues and Solutions

**1. Authentication Errors**
```
Error: 401 Unauthorized
```
**Solution**: 
- Verify JIRA_API_TOKEN is correct
- Check JIRA_USER_EMAIL matches your account
- Ensure JIRA_BASE_URL has no trailing slash

**2. Issue Not Found**
```
Error: Issue does not exist or you do not have permission
```
**Solution**:
- Verify issue key format (QPESA-123)
- Check if issue exists in JIRA
- Ensure project key is "QPESA"

**3. Transition Failed**
```
Error: Transition not found
```
**Solution**:
- Check workflow transitions in JIRA
- Verify transition names match workflow file
- Ensure user has permission to transition

**4. Workflow Not Triggering**
```
GitHub Actions not running
```
**Solution**:
- Check if workflows are enabled in repository
- Verify branch names match trigger patterns
- Check GitHub Actions tab for error logs

### Debug Steps

1. **Check GitHub Actions Logs**:
   - Go to https://github.com/KevQPSA/qpesa/actions
   - Click on failed workflow
   - Review error messages

2. **Test JIRA API Connection**:
   ```bash
   curl -u your-email@domain.com:your-api-token \
     https://your-site.atlassian.net/rest/api/3/myself
   ```

3. **Verify JIRA Project**:
   - Ensure project key is exactly "QPESA"
   - Check if issue types exist
   - Verify workflow transitions

## 📊 Expected Workflow

Once connected, here's what happens automatically:

1. **Developer creates branch**: `feature/QPESA-100-new-feature`
2. **Makes commits**: `QPESA-100: Add new feature implementation`
3. **GitHub Action runs**: Extracts QPESA-100, finds JIRA issue
4. **JIRA updated**: Issue moves to "In Progress", gets comment
5. **Creates PR**: Title includes QPESA-100
6. **JIRA updated**: Issue moves to "Code Review"
7. **Tests run**: JIRA gets test results comment
8. **PR merged**: Issue moves to "Done"
9. **Deploy to production**: JIRA gets deployment notification

## 🎯 Next Steps

After successful connection:

1. **Create your first real JIRA issues** for the crypto-fiat processor
2. **Set up project roadmap** with epics and stories
3. **Configure JIRA dashboards** for project tracking
4. **Train team members** on the workflow
5. **Set up JIRA notifications** for important updates

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review GitHub Actions logs
3. Test JIRA API connection manually
4. Create an issue in the repository with label `jira-integration`

---

**Your integration is now ready!** 🎉

Repository: https://github.com/KevQPSA/qpesa
JIRA Project: https://your-site.atlassian.net/browse/QPESA