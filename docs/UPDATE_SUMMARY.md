# Update System - Quick Reference

## For Faculty: How to Update Deployed Assignments

### Quick Update (30 seconds)

```bash
# From your assignment repository
bash .github/scripts/update_feedback_system.sh
```

That's it! The script:
- ✅ Creates automatic backup
- ✅ Updates all scripts to latest version
- ✅ Preserves your custom rubric/guidance/config
- ✅ Shows you what changed

### After Update

```bash
# Test it works
docker run --rm -v $PWD:/docs ghcr.io/202420-phys-230/quarto:1 \
  bash -c 'cd /docs && python .github/scripts/parse_report.py'

# If good, commit
git add .github/
git commit -m "Update AI feedback system"
git push
```

---

## What Gets Updated vs Preserved

### Updated (Scripts) ✅
- `parse_report.py`
- `ai_feedback_criterion.py`
- `html_to_markdown.py`
- `rubric_converter.py`
- `section_extractor.py`
- `image_utils.py`
- All other Python scripts
- Documentation files
- GitHub Actions workflow

### Preserved (Your Customizations) ✅
- `.github/feedback/rubric.yml` (or RUBRIC.md)
- `.github/feedback/guidance.md`
- `.github/feedback/config.yml`
- Student work (`index.qmd`, images, notebooks, etc.)

---

## Multiple Strategies Available

1. **Update Script** (Recommended) - Automatic, safe
2. **GitHub Actions** - Auto-checks for updates, creates PRs
3. **Git Subtree** - Advanced, tight integration
4. **Manual Copy** - Simple, full control

See [UPDATING_DEPLOYED_ASSIGNMENTS.md](UPDATING_DEPLOYED_ASSIGNMENTS.md) for details on all strategies.

---

## Version Tracking

```bash
# Check your current version
cat .github/scripts/VERSION

# Check latest available
curl -s https://raw.githubusercontent.com/YOUR-ORG/ai-feedback-system/main/VERSION
```

---

## When to Update

- **Bug fixes (1.0.x → 1.0.y)**: Safe to update anytime
- **New features (1.x → 1.y)**: Update between assignments
- **Major changes (x.0 → y.0)**: Read changelog, test carefully

---

## Batch Update Multiple Assignments

```bash
#!/bin/bash
for repo in assignment-*; do
  cd "$repo"
  bash .github/scripts/update_feedback_system.sh
  git add .github && git commit -m "Update feedback system" && git push
  cd ..
done
```

---

## Rollback If Needed

```bash
# Automatic backup created by update script
ls .github/scripts.backup.*

# Restore from backup
rm -rf .github/scripts
mv .github/scripts.backup.YYYYMMDD-HHMMSS .github/scripts
git add .github/ && git commit -m "Rollback update" && git push
```

---

## Configuration

Set repository URL for updates:

```bash
# One-time setup (optional)
export AI_FEEDBACK_REPO_URL="https://github.com/YOUR-ORG/ai-feedback-system.git"

# Or edit the script directly
vim .github/scripts/update_feedback_system.sh
# Change: REPO_URL="https://github.com/..."
```

---

## Full Documentation

- **[UPDATING_DEPLOYED_ASSIGNMENTS.md](UPDATING_DEPLOYED_ASSIGNMENTS.md)** - Complete guide with all strategies
- **[CHANGELOG.md](../CHANGELOG.md)** - What's new in each version

---

## Support

Having issues? Check:
1. [UPDATING_DEPLOYED_ASSIGNMENTS.md](UPDATING_DEPLOYED_ASSIGNMENTS.md) - Troubleshooting section
2. [CHANGELOG.md](../CHANGELOG.md) - Breaking changes
3. GitHub Issues - Report problems

---

**Bottom line**: Run the update script. It's safe and handles everything for you!
