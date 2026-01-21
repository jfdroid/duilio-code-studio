# Branch Protection Rules Setup

This guide explains how to set up branch protection rules for the DuilioCode Studio repository.

## Why Branch Protection?

- Prevent direct pushes to `master`
- Require code reviews before merging
- Ensure CI passes before merging
- Maintain code quality

## Setup Instructions

### Step 1: Go to Repository Settings

1. Navigate to your repository: https://github.com/jfdroid/duilio-code-studio
2. Click **Settings** tab
3. In the left sidebar, click **Branches**

### Step 2: Add Branch Protection Rule

Click **"Add branch protection rule"**

### Step 3: Configure the Rule

#### Branch name pattern
```
master
```

#### Protection Settings (Recommended)

✅ **Require a pull request before merging**
  - ✅ Require approvals: `1`
  - ✅ Dismiss stale pull request approvals when new commits are pushed
  - ✅ Require review from Code Owners (optional)

✅ **Require status checks to pass before merging** (if you have CI)
  - ✅ Require branches to be up to date before merging

✅ **Require conversation resolution before merging**

✅ **Do not allow bypassing the above settings**

❌ **Allow force pushes** - Keep disabled
❌ **Allow deletions** - Keep disabled

### Step 4: Bypass List (Optional)

If you want to allow yourself (jfdroid) to push directly in emergencies:

1. Under "Restrict who can push to matching branches"
2. Add `jfdroid` to the allowed list

**Note:** This is not recommended for open source projects as it reduces accountability.

### Step 5: Save

Click **"Create"** or **"Save changes"**

## Code Owners (Optional)

Create a `CODEOWNERS` file to automatically request reviews:

```
# .github/CODEOWNERS

# Default owner for everything
* @jfdroid

# Specific paths
/src/ @jfdroid
/web/ @jfdroid
```

## Result

After setup:
- All changes must go through Pull Requests
- PRs from external contributors require your approval
- Direct pushes to `master` are blocked
- Code quality is maintained

## Quick Setup via GitHub CLI

If you have GitHub CLI installed:

```bash
gh api repos/jfdroid/duilio-code-studio/branches/master/protection \
  --method PUT \
  --field required_pull_request_reviews='{"required_approving_review_count":1}' \
  --field enforce_admins=false \
  --field restrictions=null
```

---

For more information, see [GitHub's documentation on branch protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).
