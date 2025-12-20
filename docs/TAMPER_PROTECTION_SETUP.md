# Tamper Protection Setup Guide

## Overview

This guide shows you how to prevent students from modifying the AI feedback system files (`.github` folder) using **GitHub Organization Rulesets**. This is the recommended approach because:

- ✅ **Automatic** - Applies to all new repos instantly
- ✅ **No scripts needed** - Configured once in organization settings
- ✅ **No timing window** - Protection is active immediately when repos are created
- ✅ **Centrally managed** - Update rules in one place
- ✅ **Can't be bypassed** - Students don't have permission to disable rulesets

---

## Prerequisites

- **Admin access** to your GitHub Classroom organization
- **Students have Write access** to their repos (default for GitHub Classroom)
- Organization rulesets feature enabled (available for most organizations)

---

## Setup Instructions

### Step 1: Access Organization Settings

1. Go to your GitHub Classroom organization (e.g., `https://github.com/your-org`)
2. Click **Settings** (you need admin access)
3. In the left sidebar, look for **Rules** → **Rulesets** (or **Repository rulesets**)

### Step 2: Create New Ruleset

1. Click **New ruleset** → **New branch ruleset**
2. Configure the ruleset:

#### Ruleset Name
```
Protect AI Feedback System
```

#### Enforcement Status
- Select: **Active** (enforced immediately)

#### Target Repositories
Choose one of:

**Option A: All repositories** (recommended)
- Select: **All repositories**
- This protects the `.github` folder in all student repos

**Option B: Dynamic list by targeting pattern** (if you want to be selective)
- Select: **Target: Dynamic list by targeting pattern**
- Repository naming pattern: `assignment-*` or your classroom naming pattern
- This only protects repos matching the pattern

#### Target Branches
- Branch name pattern: `main` (or `master` if you use that)
- Or select **Default branch** to protect whatever branch is default

### Step 3: Configure Protection Rules

Scroll down to **Branch protections** and enable:

#### Required Pull Requests
- ☑ **Require a pull request before merging**
- Required approvals: **1**
- ☐ Dismiss stale pull request approvals when new commits are pushed (leave unchecked)

This means:
- Students **can push** regular commits to `main`
- Students **cannot push** changes to `.github` folder directly to `main`
- To modify `.github`, students must create a branch and PR (which you can review)

#### Additional Settings (Optional but Recommended)
- ☑ **Block force pushes** - Prevents rewriting history
- ☐ **Require status checks to pass** - Leave unchecked (not needed)
- ☐ **Require conversation resolution** - Leave unchecked

### Step 4: Add Path-Based Restrictions (If Available)

Some organization rulesets support path-based rules. If this option is available:

1. Look for **Restrict file paths** or **Restricted file paths**
2. Add pattern: `.github/**/*`
3. This explicitly blocks modifications to any file in `.github` folder

**Note**: This feature may not be available in all organization plans. The pull request requirement alone provides good protection.

### Step 5: Save Ruleset

1. Review your settings
2. Click **Create** or **Save ruleset**
3. The ruleset is now active!

---

## What This Does

### Students CAN:
- ✅ Clone their repository
- ✅ Push commits to `main` branch
- ✅ Modify their report files (`index.qmd`, code, images, etc.)
- ✅ Create tags (`feedback-v1`, `feedback-v2`, etc.)
- ✅ Trigger the AI feedback workflow
- ✅ Create branches
- ✅ Open pull requests

### Students CANNOT:
- ❌ Push changes to `.github` folder on `main` branch
- ❌ Delete or modify `.github/workflows/report-feedback.yml`
- ❌ Modify `.github/scripts/*.py`
- ❌ Change `.github/feedback/rubric.yml` or `guidance.md`
- ❌ Disable the feedback system
- ❌ Bypass the protection (requires admin access)

### What Happens If Student Tries:
```bash
# Student attempts to modify .github
echo "# hacked" >> .github/workflows/report-feedback.yml
git add .github
git commit -m "Try to disable feedback"
git push

# Result:
remote: error: GH006: Protected branch update failed.
remote: error: Required reviews not satisfied.
To github.com:classroom/student-repo.git
 ! [remote rejected] main -> main (protected branch hook declined)
error: failed to push some refs
```

---

## Testing the Setup

### Test 1: Verify Ruleset is Active

1. Go to **Organization Settings** → **Rules** → **Rulesets**
2. Verify your ruleset shows as **Active**
3. Check that it targets the correct repositories

### Test 2: Test with a Student Account (Recommended)

The best way to verify is to create a test assignment:

1. **Create a test assignment** in GitHub Classroom
2. **Accept with a second GitHub account** (simulate student)
3. **Clone the test repo** as the student account
4. **Try to modify .github**:
   ```bash
   cd student-test-repo
   echo "# test" >> .github/workflows/report-feedback.yml
   git add .github
   git commit -m "Test protection"
   git push  # Should be REJECTED
   ```
5. **Try to push normal work**:
   ```bash
   echo "# my work" >> index.qmd
   git add index.qmd
   git commit -m "Add my lab report"
   git push  # Should SUCCEED
   ```
6. **Try to create a tag**:
   ```bash
   git tag feedback-v1
   git push origin feedback-v1  # Should SUCCEED
   ```

### Expected Results:
- ❌ Pushing `.github` changes: **REJECTED**
- ✅ Pushing report changes: **SUCCESS**
- ✅ Creating tags: **SUCCESS**
- ✅ Workflow triggered: **SUCCESS**

---

## Common Issues and Solutions

### Issue 1: Ruleset Not Applying to Existing Repos

**Problem**: Ruleset created after repos already exist

**Solution**: Rulesets apply immediately, but you may need to:
1. Check that repos match the targeting pattern
2. Verify the branch name matches (`main` vs `master`)
3. Wait a few minutes for GitHub to propagate rules

### Issue 2: Students Can't Push Anything

**Problem**: Ruleset too restrictive

**Solution**: Verify you configured:
- **Require pull request**: YES
- **Required approvals**: 1 (not 2+)
- **NOT blocking all pushes** - Only .github folder should be affected

If students still can't push, check:
- Is "Restrict pushes" enabled? (Should be NO)
- Are there other rulesets conflicting?

### Issue 3: Students CAN Still Modify .github

**Problem**: Protection not working

**Checklist**:
- [ ] Ruleset status is **Active** (not Disabled or Evaluate mode)
- [ ] Target repositories includes the student repo
- [ ] Branch name matches (check if repo uses `main` or `master`)
- [ ] Student is pushing to the protected branch (not a different branch)

### Issue 4: Workflows Don't Run

**Problem**: Ruleset blocking workflow execution

**Solution**: This shouldn't happen. Verify:
- Workflow file still exists in `.github/workflows/`
- `GITHUB_TOKEN` has correct permissions in workflow
- Check Actions tab for error messages

---

## Alternative: Repository-Level Branch Protection

If organization rulesets are not available or not working, you can use repository-level branch protection on each repo individually.

**Pros**: More granular control per repo
**Cons**: Must be applied to each repo (can use script)

See `scripts/setup_branch_protection.sh` for bulk setup script.

---

## Maintenance

### Adding New Assignments
**No action needed!** New repos automatically inherit the ruleset.

### Modifying the Feedback System
When you need to update `.github` files across all student repos:

**Option 1: Create PRs for students** (recommended)
```bash
# Use gh CLI to create PRs in all repos
for repo in $(gh repo list YOUR_ORG --limit 1000 --json name -q '.[].name'); do
  # Clone, update .github, push to branch, create PR
  gh pr create --repo "YOUR_ORG/$repo" --title "Update AI feedback system"
done
```

**Option 2: Temporarily disable ruleset**
1. Go to organization rulesets
2. Set enforcement to **Disabled** or **Evaluate**
3. Push updates to all repos
4. Re-enable enforcement to **Active**

### Disabling Protection
If you need to remove protection:
1. Go to **Organization Settings** → **Rules** → **Rulesets**
2. Click your ruleset
3. Change enforcement to **Disabled**
4. Or delete the ruleset entirely

---

## Security Considerations

### What This Protects Against
- ✅ Students accidentally breaking the feedback system
- ✅ Students intentionally disabling workflows
- ✅ Students modifying rubrics or guidance
- ✅ Students deleting feedback scripts

### What This Does NOT Protect Against
- ❌ Determined students creating branches with modified `.github`
  - *Mitigation*: They still can't merge to `main` without your approval
- ❌ Students with admin access (shouldn't happen in Classroom)
  - *Mitigation*: Don't give students admin access
- ❌ Students using local tools to generate fake feedback
  - *Mitigation*: Issues are tracked, audit before grading

### Additional Protections (Optional)

For maximum security, consider adding:

1. **Detection workflow** - Alerts if `.github` modified (even in branches)
   - See TAMPER_RESISTANCE.md Option 2

2. **Pre-grading validation** - Run script before final grading
   - See `scripts/validate_repos.sh`

3. **Audit logs** - Review GitHub audit log for suspicious activity
   - Organization Settings → Audit log

---

## Summary Checklist

Setup checklist for instructors:

- [ ] Access organization settings (admin required)
- [ ] Navigate to Rules → Rulesets
- [ ] Create new branch ruleset
- [ ] Set name: "Protect AI Feedback System"
- [ ] Set enforcement: **Active**
- [ ] Set target: **All repositories** (or pattern)
- [ ] Set target branch: **main** (or default)
- [ ] Enable: **Require pull request before merging**
- [ ] Set required approvals: **1**
- [ ] Optional: Enable **Block force pushes**
- [ ] Save ruleset
- [ ] Test with student account (highly recommended)
- [ ] Verify workflows still run
- [ ] Document for students in assignment instructions

---

## Student Communication

Add this to your assignment instructions:

```markdown
## Important: AI Feedback System Protection

This repository includes an automated AI feedback system in the `.github` folder.

**DO NOT modify any files in the `.github` folder.** These files are protected and
you will not be able to push changes to them. Attempting to modify these files
will result in push failures.

You can freely:
- Modify your report files (`index.qmd`, code, images, etc.)
- Create commits and push to the repository
- Create tags to request feedback (`git tag feedback-v1; git push origin feedback-v1`)

If you need to modify the feedback system for legitimate reasons, contact your
instructor.
```

---

## Next Steps

1. ✅ Set up organization ruleset (following this guide)
2. ✅ Test with a student account
3. ✅ Deploy AI feedback system to your assignment template
4. ✅ Create assignment in GitHub Classroom
5. ✅ Students accept → repos automatically protected
6. ✅ (Optional) Run validation script before grading: `scripts/validate_repos.sh`

---

**Questions or issues?** Check GitHub's documentation on [organization rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets).
