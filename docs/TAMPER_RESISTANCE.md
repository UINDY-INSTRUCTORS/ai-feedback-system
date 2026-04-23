# Tamper Resistance for AI Feedback System

## The Problem

When the AI feedback system is deployed to student repositories via GitHub Classroom, students have write access to their repos. This means they can potentially modify or delete the `.github` folder contents, including:
- Workflow files (`.github/workflows/report-feedback.yml`)
- Scripts (`.github/scripts/*.py`)
- Configuration files (`.github/feedback/*.yml`)
- Validation steps

**Key Challenge:** Anything deployed to a student repo can be modified by the student, including validation workflows themselves.

---

## ⭐ EASIEST: GitHub Classroom Protected Paths (Built-in Detection)

### GitHub Classroom Has This Built In!

**GitHub Classroom includes a "Protected file paths" feature** that makes tamper detection simple:

- Specify `.github/**/*` as a protected path when creating assignment
- Students **can** push changes (won't block them)
- GitHub Classroom **automatically labels** submissions that modify protected files
- Instructor sees "Protected file(s) modified" label on assignment dashboard
- Acts as deterrent and provides easy visibility

### Setup (30 Seconds)

When creating assignment in GitHub Classroom:
1. Find **"Protected file paths"** section in assignment creation form
2. Add pattern: `.github/**/*`
3. Save and create assignment

**That's it!** No additional configuration needed.

### Effect

- ✅ Students can push commits normally
- ✅ Students can create tags (triggers feedback)
- ✅ Workflows run normally
- ✅ Modifications to `.github` are **flagged** on dashboard
- ✅ Easy to review which students modified protected files

### Pros

- **Zero setup overhead** - built into GitHub Classroom
- **Easy visibility** - dashboard shows labeled submissions at a glance
- **No maintenance** - works automatically
- **Students can fix mistakes** - can push reverts if needed
- **Per-assignment** - configure as needed for each assignment

### Cons

- **Detection only** - doesn't prevent modifications
- **Requires review** - instructor must check dashboard
- Students might not realize files are monitored until grading

### When to Use

- **Most educational contexts** - sufficient for typical academic integrity
- You want the simplest possible solution
- Detection/deterrence is adequate for your needs
- You review assignment dashboard before grading

**Full guide:** See `docs/TAMPER_PROTECTION_SETUP.md` for complete instructions and comparison.

---

## MAXIMUM PROTECTION: Organization Rulesets (Automatic Prevention)

### How Organization Rulesets Work

GitHub Organization Rulesets are **repository settings configured at the organization level** that automatically apply to all repositories matching a pattern:

- **Configured once** in organization settings
- **Applies automatically** to all new repos (no scripts needed!)
- **Cannot be bypassed** by students with Write access
- **Instant protection** - active the moment repos are created
- **Centrally managed** - update rules in one place

**Key insight:** Rulesets are managed at the organization level and require **Admin** access to configure. Once set, **Write** users (students) cannot bypass or disable them.

### Setup (One-Time Configuration)

**Full guide:** See `docs/TAMPER_PROTECTION_SETUP.md`

**Quick setup:**

1. Go to your GitHub Classroom organization Settings
2. Navigate to **Rules** → **Rulesets**
3. Click **New ruleset** → **New branch ruleset**
4. Configure:
   ```
   Name: Protect AI Feedback System
   Enforcement: Active
   Target: All repositories (or pattern match)
   Target branch: main

   Branch protections:
   ☑ Require a pull request before merging
   Required approvals: 1
   ☑ Block force pushes
   ```
5. Save ruleset

### Effect

- ✅ Students can push regular commits to `main`
- ✅ Students can create tags (triggers feedback)
- ✅ Workflows run normally
- ❌ Students **cannot** push changes to `.github` on `main` branch
- ❌ Students cannot disable rulesets (requires Admin)

### Pros

- **Zero maintenance** - set once, works forever
- **Automatic** - applies to all new repos instantly
- **No timing window** - protection active immediately
- **True prevention** - not just detection
- **Can't be bypassed** by students
- **No scripts needed**

### Cons

- Requires organization admin access to configure
- Students must use branches/PRs to modify `.github` (which requires instructor review)
- Not available for personal accounts (organization only)

### Testing

See `docs/TAMPER_PROTECTION_SETUP.md` for detailed testing instructions.

---

## Option 1: Checksum Validation (Insufficient Alone)

### Concept
- Generate checksum of `.github` folder
- Store in repository secret (students can't read secrets)
- Workflow validates checksum before running
- If tampered: workflow fails, no feedback provided

### Implementation
```yaml
# Enhancement to existing validation step in report-feedback.yml
- name: Validate system integrity
  env:
    EXPECTED_CHECKSUM: ${{ secrets.GITHUB_FOLDER_CHECKSUM }}
  run: |
    echo "🔍 Validating AI feedback system integrity..."

    # Verify checksum
    ACTUAL_CHECKSUM=$(find .github -type f \( -name "*.py" -o -name "*.yml" -o -name "*.md" \) -exec sha256sum {} \; | sort -k 2 | sha256sum | cut -d' ' -f1)

    if [ "$ACTUAL_CHECKSUM" != "$EXPECTED_CHECKSUM" ]; then
      echo "❌ ERROR: System integrity check failed"
      echo "The .github folder has been modified from its original state."
      echo "⚠️  Feedback system disabled. Contact your instructor."
      exit 1
    fi

    echo "✅ System integrity verified"
```

### Limitation
**Student can delete the validation workflow itself**, so this provides no protection unless combined with other measures.

---

## Option 2: Separate Notification Workflow (Detection Only)

### Concept
- Workflow runs on every push (not just tags)
- Detects if `.github` was modified
- Creates issue to notify instructor
- Doesn't prevent tampering, just makes it visible

### Implementation
```yaml
# New workflow: .github/workflows/detect-tampering.yml
name: Detect .github Modifications

on:
  push:
    branches: ['**']
  pull_request:

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 2

      - name: Check for unauthorized changes
        run: |
          CHANGED=$(git diff --name-only HEAD~1 HEAD 2>/dev/null | grep '^\.github/' || true)

          if [ -n "$CHANGED" ]; then
            echo "⚠️ WARNING: Changes detected in .github folder"
            echo "$CHANGED"
            gh issue create \
              --title "⚠️ Unauthorized .github modification detected" \
              --body "Student modified protected files: $CHANGED" \
              --label "academic-integrity"
          fi
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Limitation
**Reactive, not preventive.** Student can also delete this workflow.

---

## Option 3: Branch Protection (RECOMMENDED)

### How Branch Protection Works

Branch protection rules are **repository settings** that restrict what can be done to specific branches:

- **Require pull request reviews** - Can't directly push to protected branch
- **Require status checks to pass** - Specific workflows must succeed before merge
- **Restrict who can push** - Only specific users/teams can push
- **Prevent force pushes** - Can't rewrite history
- **Prevent deletion** - Branch can't be deleted

**Key insight:** Branch protection requires **Admin** access to configure, but once set, **Write** users cannot bypass it.

### Required Permissions

| Permission Level | What Students Can Do | What They CAN'T Do |
|------------------|---------------------|-------------------|
| **Read** | View code, clone repo | ❌ Push, create issues |
| **Write** ✅ | Push code, create issues, run workflows, create tags | ❌ Change settings, manage branch protection |
| **Admin** | Everything | Change repository settings, bypass protection |

**Our workflow requires:**
- Student: **Write** access (push commits/tags)
- Workflow token: `contents: read`, `issues: write`, `models: read`

**Students do NOT need Admin access for the AI feedback system to work.**

### Setup (Bulk Script for All Repos)

```bash
#!/bin/bash
# bulk_protect_repos.sh
# Run once to protect .github folder in all student repos

ORG="your-classroom-org"

for repo in $(gh api "/orgs/$ORG/repos" --paginate --jq '.[].full_name'); do
  echo "Protecting $repo..."

  gh api -X PUT "/repos/$repo/branches/main/protection" \
    --input - <<EOF
{
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": false
  },
  "enforce_admins": false,
  "required_status_checks": null,
  "restrictions": null
}
EOF
done
```

### Effect
- ✅ Students can push regular commits to `main`
- ✅ Students can create tags (triggers feedback)
- ✅ Workflows run normally
- ❌ Students **cannot** push changes to `.github` on `main` branch
- ❌ Students cannot disable branch protection (requires Admin)

### Pros
- True prevention (not just detection)
- Can't be bypassed by students
- One-time setup per assignment

### Cons
- Requires one-time instructor setup
- Students must use branches/PRs to modify `.github` (which requires instructor review)

---

## Option 4: Instructor-Side Validation

### Concept
Don't validate in student repos - validate when **you** collect/grade them.

### Implementation
```bash
#!/bin/bash
# validate_repos.sh - Instructor runs this to audit all student repos

EXPECTED_CHECKSUM="your-checksum-here"

for repo in student-repos/*; do
  cd "$repo"
  CHECKSUM=$(find .github -type f -exec sha256sum {} \; | sort | sha256sum | cut -d' ' -f1)
  if [ "$CHECKSUM" != "$EXPECTED_CHECKSUM" ]; then
    echo "⚠️ TAMPERING DETECTED: $repo"
  fi
  cd ..
done
```

### When to Run
- Before final grading
- Periodically during semester
- When pulling repos for review

### Pros
- Can't be tampered with (runs on instructor machine)
- Works regardless of student permissions
- Simple to implement

### Cons
- Reactive (detects after the fact)
- Requires instructor action
- Doesn't prevent tampering during semester

---

## Option 5: External Monitoring Service

### Concept
A separate repo/service that monitors student repos from outside.

### Implementation
```yaml
# In YOUR monitoring repo (not student repos)
# .github/workflows/audit-student-repos.yml
name: Audit Student Repos
on:
  schedule:
    - cron: '0 0 * * *'  # Daily
  workflow_dispatch:  # Manual trigger

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - name: Audit all repos
        env:
          GH_TOKEN: ${{ secrets.ORG_ADMIN_TOKEN }}
        run: |
          for repo in $(gh api /orgs/YOUR_ORG/repos --jq '.[].full_name'); do
            gh repo clone "$repo" temp_repo
            CHECKSUM=$(find temp_repo/.github -type f -exec sha256sum {} \; | sort | sha256sum)
            # Compare and report...
          done
```

### Pros
- Can't be tampered with by students
- Automated monitoring

### Cons
- Requires organization access token setup
- More complex infrastructure

---

## Testing with GitHub Classroom

### Strategy
Test with a second GitHub account to simulate student access, but **use actual GitHub Classroom** to create the test assignment/repo.

### Testing Steps

1. **Create test assignment in GitHub Classroom**
   - Use your real classroom
   - Create a simple test assignment
   - Deploy the AI feedback system to the template repo

2. **Accept assignment with test account**
   - Log in with second GitHub account (student account)
   - Accept the classroom assignment
   - GitHub Classroom creates repo with appropriate permissions

3. **Verify permissions**
   ```bash
   # As instructor, check student's permission level
   gh api /repos/OWNER/STUDENT_REPO/collaborators/STUDENT_USERNAME/permission

   # Should return: "permission": "write" (not "admin")
   ```

4. **Test as student**
   - Clone repo
   - Modify a regular file → push successfully ✅
   - Create feedback tag → workflow runs ✅
   - Try to access Settings → Branches (should not see branch protection options)

5. **Test branch protection (as instructor)**
   ```bash
   # Enable branch protection on student's repo
   gh api -X PUT /repos/OWNER/STUDENT_REPO/branches/main/protection \
     --input - <<EOF
   {
     "required_pull_request_reviews": {
       "required_approving_review_count": 1
     },
     "enforce_admins": false
   }
   EOF
   ```

6. **Test tampering (as student)**
   ```bash
   # Try to modify .github
   echo "# tampered" >> .github/workflows/report-feedback.yml
   git add .github
   git commit -m "Test tampering"
   git push  # Should be REJECTED if branch protection works!
   ```

### What to Verify

- [ ] Students have Write (not Admin) access by default
- [ ] Workflows run successfully with Write access
- [ ] Students can create tags and trigger workflows
- [ ] Branch protection blocks pushes to `.github`
- [ ] Students cannot modify branch protection settings
- [ ] Students cannot disable workflows (via Settings)

---

## Recommended Implementation

### For GitHub Classroom (Most Common) - SIMPLE APPROACH ⭐

**Primary: GitHub Classroom Protected Paths** (30 seconds per assignment)
1. When creating assignment, set protected path: `.github/**/*`
2. Before grading: Check dashboard for "Protected file(s) modified" labels
3. (Optional) Run validation script for double-check: `scripts/validate_repos.sh`

**This is sufficient for most educational contexts.**

### For High-Stakes Scenarios - MAXIMUM PROTECTION

If you need absolute prevention (not just detection):

1. **Primary Defense: Organization Rulesets**
   - One-time configuration in organization settings (~10 minutes)
   - Blocks students from pushing `.github` changes
   - Guide: `docs/TAMPER_PROTECTION_SETUP.md`

2. **Secondary Defense: Pre-Grading Validation**
   - Run before final grading to verify integrity
   - Script: `scripts/validate_repos.sh`

### For Individual Repos (Non-GitHub Classroom)

If not using GitHub Classroom:

1. **Repository-Level Branch Protection**
   - Manual setup per repository (or use bulk script)
   - GitHub repository Settings → Branches
   - Script for bulk: `scripts/setup_branch_protection.sh`

2. **Validation Before Grading**
   - Run validation script before grading
   - Script: `scripts/validate_repos.sh`

---

## Implementation Checklist

### Simple Approach (Recommended for Most)

**For GitHub Classroom Instructors:**

- [ ] Deploy AI feedback system to assignment template
- [ ] Create assignment in GitHub Classroom
- [ ] Set protected path: `.github/**/*` (in assignment settings)
- [ ] Before grading: Check dashboard for "Protected file(s) modified" labels
- [ ] (Optional) Run validation script for verification
- [ ] Document for students in assignment README

**Complete setup time:** 30 seconds per assignment

### Maximum Protection (Optional)

**For instructors who need prevention:**

- [ ] Set up organization ruleset (see `docs/TAMPER_PROTECTION_SETUP.md`)
- [ ] Test ruleset with a student account
- [ ] Deploy AI feedback system to assignment template
- [ ] Create assignment in GitHub Classroom
- [ ] (Optional) Run validation script before grading
- [ ] Document protection for students in assignment README

**Complete setup time:** ~10 minutes (one-time for all assignments)

---

## Questions Answered ✅

- ✅ **Do GitHub Classroom repos give students Write or Admin by default?**
  - Answer: **Write access** (confirmed - students do NOT get Admin)

- ✅ **Can workflows run successfully with only Write access?**
  - Answer: **Yes** - workflows run fine with Write access

- ✅ **Does branch protection interfere with normal student workflow?**
  - Answer: **No** - students can push commits and create tags normally

- ✅ **Can branch protection be configured automatically?**
  - Answer: **Yes** - Organization rulesets apply automatically to all repos
