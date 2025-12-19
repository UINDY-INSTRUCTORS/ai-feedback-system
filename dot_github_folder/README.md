# ⚠️ DO NOT MODIFY FILES IN THIS DIRECTORY

This `.github/` directory contains the automated AI feedback system for your assignments.

## What's In Here

- `workflows/` - GitHub Actions that run when you request feedback
- `feedback/` - Rubric and configuration (customized for this assignment)
- `scripts/` - Python scripts that analyze your report and generate feedback

## Important Warning

**DO NOT modify, delete, or rename any files in this directory.**

The feedback system validates these files before running. If any are missing or modified, you will see an error like:

```
❌ ERROR: Required feedback system files are missing or modified
⚠️  DO NOT modify files in the .github/ directory.
```

## How to Request Feedback

1. Complete your assignment in `index.qmd` (or your configured report file)
2. Commit and push your changes
3. Create and push a tag:
   ```bash
   git tag feedback-v1
   git push origin feedback-v1
   ```
4. Wait 5-10 minutes for feedback to appear in the Issues tab

## Need Help?

If the feedback system isn't working:

1. ✅ Check the Actions tab for workflow runs and error messages
2. ✅ Verify your report file exists and is named correctly
3. ✅ Make sure you used the correct tag format (`feedback-*`)
4. ✅ Contact your instructor - **do not modify these files**

---

**For Instructors**: See `SETUP_GUIDE.md` and `GITHUB_MODELS_SETTINGS.md` in this directory for configuration details.
