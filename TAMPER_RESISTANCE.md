# Tamper Resistance for AI Feedback System

## The Problem

When the AI feedback system is deployed to student repositories via GitHub Classroom, students have write access to their repos. This means they can potentially modify or delete the `.github` folder contents, including:
- Workflow files (`.github/workflows/report-feedback.yml`)
- Scripts (`.github/scripts/*.py`)
- Configuration files (`.github/feedback/*.yml`)
- Validation steps

**Key Challenge:** Anything deployed to a student repo can be modified by the student, including validation workflows themselves.

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

**Combination Approach:**

1. **Primary Defense: Branch Protection (Option 3)**
   - One-time bulk setup after deploying to all student repos
   - Provides true prevention
   - Script: `bulk_protect_repos.sh`

2. **Secondary Defense: Instructor-Side Audit (Option 4)**
   - Run before final grading to catch any edge cases
   - Script: `validate_repos.sh`

3. **Optional: Notification Workflow (Option 2)**
   - Additional visibility if a student somehow bypasses
   - Low overhead, easy to add

4. **Document the Approach**
   - Explain to instructors why branch protection matters
   - Provide clear setup instructions
   - Include troubleshooting for common issues

---

## Next Steps

1. ✅ Test with GitHub Classroom using second account
2. ⏳ Verify student permission levels
3. ⏳ Confirm branch protection blocks `.github` modifications
4. ⏳ Confirm workflows still run with Write access
5. ⏳ Build bulk setup script for instructors
6. ⏳ Build validation script for pre-grading audit
7. ⏳ Document in INSTRUCTOR_GUIDE.md

---

## Open Questions

- [ ] Do GitHub Classroom repos give students Write or Admin by default?
- [ ] Can workflows run successfully with only Write access?
- [ ] Does branch protection interfere with normal student workflow?
- [ ] Can branch protection be configured via GitHub Classroom settings?
