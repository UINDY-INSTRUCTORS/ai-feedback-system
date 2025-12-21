# Updating Deployed Assignments

**How to update the AI feedback system in assignments that are already deployed to students**

## The Challenge

You've deployed the AI feedback system to student assignment repositories (via GitHub Classroom). Now we've added new features to the main `ai-feedback-system` repository. How do you update your deployed assignments safely?

## TL;DR - Quick Update

**For most faculty, this is all you need:**

```bash
# 1. Navigate to your assignment repo
cd path/to/your-assignment-repo

# 2. Run the update script
bash .github/scripts/update_feedback_system.sh

# 3. Test it
docker run --rm -v $PWD:/docs ghcr.io/202420-phys-230/quarto:1 \
  bash -c 'cd /docs && python .github/scripts/parse_report.py'

# 4. Commit and push
git add .github/
git commit -m "Update AI feedback system to latest version"
git push
```

**Your custom rubric, guidance, and config files are preserved!**

---

## Update Strategies

### Strategy 1: Update Script (Recommended)

**Best for**: Most faculty, manual control, tested updates

The update script safely updates only the script files while preserving your customizations.

#### What Gets Updated
- ✅ All Python scripts (parse_report.py, ai_feedback_criterion.py, etc.)
- ✅ Documentation (README files)
- ✅ GitHub Actions workflow

#### What Gets Preserved
- ✅ Your custom rubric (.github/feedback/rubric.yml or RUBRIC.md)
- ✅ Your custom guidance (.github/feedback/guidance.md)
- ✅ Your custom config (.github/feedback/config.yml)
- ✅ Student work (index.qmd, images, notebooks, etc.)

#### How to Use

```bash
# Update to latest version
bash .github/scripts/update_feedback_system.sh

# Update to specific version (when available)
bash .github/scripts/update_feedback_system.sh v1.1.0
```

The script will:
1. Create a backup of your current scripts
2. Download the specified version
3. Update only the script files
4. Preserve your custom configuration
5. Show you what changed

---

### Strategy 2: GitHub Actions Auto-Update (Advanced)

**Best for**: Faculty who want hands-free updates, willing to monitor

Set up a GitHub Action that automatically checks for updates and creates pull requests.

#### Setup

Create `.github/workflows/auto-update-feedback-system.yml`:

```yaml
name: Auto-Update Feedback System

on:
  schedule:
    # Check for updates weekly (Sundays at 2am)
    - cron: '0 2 * * 0'
  workflow_dispatch:  # Allow manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Check for updates
        id: check
        run: |
          CURRENT_VERSION=$(cat .github/scripts/VERSION 2>/dev/null || echo "0.0.0")
          LATEST_VERSION=$(curl -s https://raw.githubusercontent.com/YOUR-ORG/ai-feedback-system/main/VERSION)

          echo "current=$CURRENT_VERSION" >> $GITHUB_OUTPUT
          echo "latest=$LATEST_VERSION" >> $GITHUB_OUTPUT

          if [ "$CURRENT_VERSION" != "$LATEST_VERSION" ]; then
            echo "needs_update=true" >> $GITHUB_OUTPUT
          else
            echo "needs_update=false" >> $GITHUB_OUTPUT
          fi

      - name: Run update script
        if: steps.check.outputs.needs_update == 'true'
        run: |
          bash .github/scripts/update_feedback_system.sh

      - name: Create Pull Request
        if: steps.check.outputs.needs_update == 'true'
        uses: peter-evans/create-pull-request@v5
        with:
          commit-message: Update AI feedback system to ${{ steps.check.outputs.latest }}
          title: 'Update AI Feedback System to v${{ steps.check.outputs.latest }}'
          body: |
            Auto-update from v${{ steps.check.outputs.current }} to v${{ steps.check.outputs.latest }}

            ## Changes
            See [CHANGELOG](https://github.com/YOUR-ORG/ai-feedback-system/blob/main/CHANGELOG.md)

            ## Testing
            - [ ] Review changed files
            - [ ] Test parsing: `python .github/scripts/parse_report.py`
            - [ ] Test feedback generation
            - [ ] Verify rubric still works

            ## Safe to Merge?
            Your custom rubric, guidance, and config were preserved.
            Only script files were updated.
          branch: auto-update/feedback-system
          labels: dependencies, automation
```

**Pros**:
- Automatic checking for updates
- Creates pull request for review (safe)
- You can test before merging

**Cons**:
- Requires GitHub Actions setup
- Need to monitor PRs
- More complex

---

### Strategy 3: Git Subtree (Advanced)

**Best for**: Advanced users, tight integration with upstream

Use git subtree to pull updates from the main repository.

#### Initial Setup

```bash
# Add the main repo as a remote
git remote add feedback-system https://github.com/YOUR-ORG/ai-feedback-system.git

# Add as subtree
git subtree add --prefix=.github feedback-system main --squash
```

#### Update

```bash
# Pull latest changes
git subtree pull --prefix=.github feedback-system main --squash

# Resolve any conflicts with your customizations
# Commit and push
```

**Pros**:
- Git-native solution
- Clear history of updates

**Cons**:
- Subtree conflicts can be tricky
- Need to handle customization conflicts manually
- More git knowledge required

---

### Strategy 4: Manual Copy (Simple but Manual)

**Best for**: One-off updates, small number of assignments

#### Steps

1. **Download latest version**:
```bash
git clone https://github.com/YOUR-ORG/ai-feedback-system.git /tmp/latest-feedback
```

2. **Backup your current scripts**:
```bash
cp -r .github/scripts .github/scripts.backup
```

3. **Copy new scripts** (but NOT config/rubric/guidance):
```bash
cp /tmp/latest-feedback/dot_github_folder/scripts/*.py .github/scripts/
cp /tmp/latest-feedback/dot_github_folder/scripts/*.md .github/scripts/
```

4. **Test**:
```bash
docker run --rm -v $PWD:/docs ghcr.io/202420-phys-230/quarto:1 \
  bash -c 'cd /docs && python .github/scripts/parse_report.py'
```

5. **Commit**:
```bash
git add .github/
git commit -m "Update feedback system scripts"
git push
```

---

## Batch Update Multiple Assignments

If you have multiple deployed assignments to update:

### Option A: Script Loop

```bash
#!/bin/bash
# update_all_assignments.sh

ASSIGNMENTS=(
  "assignment-1-repo"
  "assignment-2-repo"
  "assignment-3-repo"
)

for assignment in "${ASSIGNMENTS[@]}"; do
  echo "Updating $assignment..."

  cd "$assignment"
  bash .github/scripts/update_feedback_system.sh

  # Test
  docker run --rm -v $PWD:/docs ghcr.io/202420-phys-230/quarto:1 \
    bash -c 'cd /docs && python .github/scripts/parse_report.py' || {
    echo "❌ Test failed for $assignment"
    continue
  }

  # Commit
  git add .github/
  git commit -m "Update AI feedback system"
  git push

  cd ..
done
```

### Option B: GitHub CLI

```bash
#!/bin/bash
# update_with_gh_cli.sh

# Get all repos with the feedback system
gh repo list YOUR-ORG --limit 1000 --json name --jq '.[].name' | \
  grep "assignment" | \
while read repo; do
  echo "Updating $repo..."

  gh repo clone "YOUR-ORG/$repo" "/tmp/$repo"
  cd "/tmp/$repo"

  bash .github/scripts/update_feedback_system.sh

  git add .github/
  git commit -m "Update AI feedback system"
  git push

  cd -
  rm -rf "/tmp/$repo"
done
```

---

## Version Management

### Semantic Versioning

We use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes (may require rubric updates)
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (safe to update anytime)

### Checking Your Version

```bash
# Check installed version
cat .github/scripts/VERSION

# Check latest available version
curl -s https://raw.githubusercontent.com/YOUR-ORG/ai-feedback-system/main/VERSION
```

### Version Compatibility

| Your Version | Update To | Safe? | Notes |
|-------------|-----------|-------|-------|
| 0.x.x | 1.0.0 | ⚠️ Review | Major update, check changelog |
| 1.0.x | 1.1.x | ✅ Yes | New features, backward compatible |
| 1.1.x | 1.1.y | ✅ Yes | Bug fixes only |

---

## What If Something Breaks?

### Rollback from Backup

The update script creates automatic backups:

```bash
# List backups
ls -la .github/scripts.backup.*

# Restore from backup
rm -rf .github/scripts
mv .github/scripts.backup.20251220-143022 .github/scripts

# Commit rollback
git add .github/
git commit -m "Rollback feedback system update"
git push
```

### Rollback from Git

```bash
# See recent commits
git log --oneline .github/

# Revert to before update
git revert <commit-hash>

# Or hard reset (if not yet pushed)
git reset --hard HEAD~1
```

---

## Testing After Update

Always test before deploying to students:

### 1. Parse Test
```bash
docker run --rm -v $PWD:/docs ghcr.io/202420-phys-230/quarto:1 \
  bash -c 'cd /docs && python .github/scripts/parse_report.py'
```

Expected: `✅ Report parsed successfully`

### 2. Validation Test
```bash
docker run --rm -v $PWD:/docs ghcr.io/202420-phys-230/quarto:1 \
  bash -c 'cd /docs && python .github/scripts/validate_config.py'
```

Expected: `✅ All validations passed`

### 3. Rubric Converter Test (if using)
```bash
docker run --rm -v $PWD:/docs ghcr.io/202420-phys-230/quarto:1 \
  bash -c 'cd /docs && python .github/scripts/rubric_converter.py validate .github/feedback/rubric.yml'
```

Expected: `✅ Validation PASSED`

### 4. Full Workflow Test

Create a test tag and verify feedback generation:

```bash
git tag test-update-v1
git push origin test-update-v1

# Watch in Actions tab
# Check for new issue with feedback
```

---

## Best Practices

### Do's ✅

1. **Always backup** before updating (script does this automatically)
2. **Test locally** before pushing to students
3. **Read the changelog** to understand what changed
4. **Update during off-hours** (weekends, breaks)
5. **Communicate with students** if you update mid-assignment
6. **Keep your customizations** in separate files (rubric.yml, guidance.md)

### Don'ts ❌

1. **Don't update mid-deadline** - Wait until assignment is submitted
2. **Don't skip testing** - Always test before deploying
3. **Don't modify core scripts** - Keep customizations in config files
4. **Don't force-push** - Use normal git workflow
5. **Don't update without reading changelog** - Understand what's changing

---

## Migration Guides

### Upgrading from 0.x to 1.0

**Breaking Changes:**
- None! Version 1.0 is the initial release

**New Features:**
- Notebook output extraction
- Rubric converter
- HTML to markdown

**Migration Steps:**
1. Run update script
2. No rubric changes needed
3. Test with existing assignments

---

## Troubleshooting

### Update Script Fails

**Problem**: "Failed to download version X"

**Solution**:
```bash
# Check available versions
git ls-remote --tags https://github.com/YOUR-ORG/ai-feedback-system.git

# Use a valid version tag
bash .github/scripts/update_feedback_system.sh v1.0.0
```

### Scripts Don't Work After Update

**Problem**: Import errors or missing files

**Solution**:
```bash
# Restore from backup
rm -rf .github/scripts
mv .github/scripts.backup.XXXXXX .github/scripts

# Report issue to ai-feedback-system repo
```

### Rubric Stopped Working

**Problem**: Rubric validation fails after update

**Solution**:
```bash
# Validate rubric
docker run --rm -v $PWD:/docs ghcr.io/202420-phys-230/quarto:1 \
  bash -c 'cd /docs && python .github/scripts/validate_config.py'

# Check changelog for rubric changes
# Usually rubric format is backward compatible
```

---

## FAQ

**Q: Will students see any changes when I update?**

A: Only if you push to repos they can see. The scripts run on GitHub Actions (server-side), so students won't notice unless feedback behavior changes.

**Q: Can I update just one assignment?**

A: Yes! Update scripts work per-repository. Update and test each assignment individually.

**Q: What if I've modified the scripts?**

A: Your modifications will be overwritten. Instead, keep customizations in:
- `config.yml` - Settings
- `guidance.md` - AI instructions
- `rubric.yml` - Grading criteria

**Q: How often should I update?**

A: For bug fixes (PATCH versions): ASAP
For new features (MINOR versions): Between assignments
For major changes (MAJOR versions): Carefully, with testing

**Q: Can I test updates without deploying?**

A: Yes! Clone your assignment repo locally, run update script, test thoroughly, then push when ready.

---

## Support

**Having trouble updating?**

1. Check this guide
2. Check [CHANGELOG.md](../CHANGELOG.md) for breaking changes
3. Search [issues](https://github.com/YOUR-ORG/ai-feedback-system/issues)
4. Open new issue with:
   - Your current version
   - Target version
   - Error message
   - Steps to reproduce

---

## Summary

**Recommended workflow for most faculty:**

1. **Between semesters**: Update all assignments to latest version
2. **During semester**: Only update for critical bug fixes
3. **Use the update script**: It's safe and preserves your customizations
4. **Always test first**: Run local tests before pushing to students
5. **Keep changelog**: Know what changed and why

**The update script handles 95% of cases safely and automatically!**
