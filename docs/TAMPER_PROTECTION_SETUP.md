# Tamper Protection Setup Guide

## Overview

This guide shows you how to protect the AI feedback system files (`.github` folder) from student modifications. There are two approaches:

1. **GitHub Classroom Protected Paths** (Easiest) - Built-in detection feature
2. **Organization Rulesets** (Maximum Protection) - Prevents modifications entirely

---

## ⭐ Option 1: GitHub Classroom Protected Paths (RECOMMENDED FOR MOST CASES)

GitHub Classroom has a **built-in feature** that makes this simple!

### How It Works

When creating an assignment, you can specify "protected file paths" that GitHub Classroom will monitor:
- Students **can** push changes to protected files (won't fail)
- GitHub Classroom **automatically labels** submissions that modify protected files
- You see "Protected file(s) modified" label on assignment dashboard
- Acts as **deterrent** and provides **easy visibility**

### Setup (30 Seconds)

When creating your assignment in GitHub Classroom:

1. In the assignment creation form, find **"Protected file paths"** section
2. Add this path pattern:
   ```
   .github/**/*
   ```
3. Save and create assignment

That's it! No additional setup needed.

### What Happens

**Student modifies .github folder:**
```bash
echo "# modified" >> .github/workflows/report-feedback.yml
git add .github
git commit -m "Try to change workflow"
git push  # ✅ Push succeeds (no error)
```

**On your assignment dashboard:**
- Student's submission shows: 🏷️ **"Protected file(s) modified"**
- Click to see which files were changed
- Can deduct points or ask student to revert

### Pros
- ✅ **Built into GitHub Classroom** - no extra setup
- ✅ **Easy visibility** - see labeled submissions at a glance
- ✅ **No scripts needed** - automatic detection
- ✅ **Students can fix mistakes** - push reverts if needed
- ✅ **Simple workflow** - one setting per assignment

### Cons
- ⚠️ **Detection only** - doesn't prevent modifications
- ⚠️ **Requires manual review** - need to check dashboard
- ⚠️ Students might not realize files are protected until grading

### When to Use This
- **Most educational contexts** - detection is sufficient deterrent
- You want simple, no-maintenance solution
- You're comfortable reviewing labeled submissions
- Academic integrity policy covers this scenario

---

## Option 2: Organization Rulesets (MAXIMUM PROTECTION)

For situations where you need to **prevent** modifications entirely (not just detect them), use organization rulesets.

### How It Works

Organization Rulesets are **repository settings configured at the organization level** that automatically apply to all repositories:

- **Configured once** in organization settings
- **Applies automatically** to all new repos instantly
- **Prevents** students from pushing `.github` changes (push fails)
- **Cannot be bypassed** - students don't have permission to disable rulesets

### Prerequisites

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

## Comparison: Which Approach Should I Use?

| Feature | GitHub Classroom Protected Paths | Organization Rulesets |
|---------|----------------------------------|----------------------|
| **Setup Time** | 30 seconds per assignment | 10 minutes (one-time) |
| **Applies To** | Per assignment | All repos in organization |
| **Protection Type** | Detection (labels submissions) | Prevention (blocks pushes) |
| **Student Experience** | Can push, sees no error | Push fails with error message |
| **Visibility** | Dashboard labels | N/A (blocked entirely) |
| **Maintenance** | None | None |
| **Complexity** | Very simple | Moderate |
| **Best For** | Most educational use cases | High-stakes or automated grading |

### Recommendation

**For most instructors:** Start with **GitHub Classroom Protected Paths**
- Simpler setup
- Built-in feature
- Sufficient deterrent for honest mistakes
- Easy to see and address violations

**Consider Organization Rulesets if:**
- You're using automated grading based on feedback
- You want absolute certainty that files aren't modified
- Your academic integrity policy requires prevention
- You have time for initial setup

**Belt and suspenders approach:**
- Use GitHub Classroom Protected Paths (built-in)
- Run validation script before final grading: `scripts/validate_repos.sh`
- This gives you detection + verification with minimal effort

---

## Summary Checklists

### Option 1: GitHub Classroom Protected Paths (Recommended)

When creating assignment in GitHub Classroom:
- [ ] Find "Protected file paths" section
- [ ] Add pattern: `.github/**/*`
- [ ] Save and create assignment
- [ ] Before grading: Check dashboard for "Protected file(s) modified" labels
- [ ] (Optional) Run validation script: `scripts/validate_repos.sh`

**Setup time:** 30 seconds per assignment

### Option 2: Organization Rulesets (Maximum Protection)

One-time setup:
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

**Setup time:** 10 minutes (one-time for all assignments)

---

## Student Communication

### For GitHub Classroom Protected Paths

Add this to your assignment instructions:

```markdown
## Important: AI Feedback System

This repository includes an automated AI feedback system in the `.github` folder.

**DO NOT modify any files in the `.github` folder.** These files contain the
automated feedback system and are monitored. Modifications will be flagged on
the assignment dashboard and may result in point deductions.

You can freely:
- Modify your report files (`index.qmd`, code, images, etc.)
- Create commits and push to the repository
- Create tags to request feedback (`git tag feedback-v1; git push origin feedback-v1`)

If you need to modify the feedback system for legitimate reasons, contact your
instructor before making changes.
```

### For Organization Rulesets

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

### Using GitHub Classroom Protected Paths (Recommended)

1. ✅ Deploy AI feedback system to your assignment template repo
2. ✅ Create assignment in GitHub Classroom
3. ✅ Set protected path: `.github/**/*`
4. ✅ Students accept assignment
5. ✅ Before grading: Check dashboard for "Protected file(s) modified" labels
6. ✅ (Optional) Run validation script before final grading

### Using Organization Rulesets (Optional)

1. ✅ Set up organization ruleset (one-time, ~10 minutes)
2. ✅ Test with a student account
3. ✅ Deploy AI feedback system to your assignment template
4. ✅ Create assignment in GitHub Classroom
5. ✅ Students accept → repos automatically protected
6. ✅ (Optional) Run validation script before grading

---

**More information:**
- [GitHub Classroom Protected Paths](https://docs.github.com/en/education/manage-coursework-with-github-classroom/teach-with-github-classroom/monitor-students-progress-with-the-assignment-dashboard)
- [Organization Rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
