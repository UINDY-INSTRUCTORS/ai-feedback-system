# ⚠️ DO NOT MODIFY THESE FILES

These scripts are part of the automated AI feedback system.

## Important

**Modifying these files will:**
- ❌ Break the AI feedback system
- ❌ Prevent you from receiving feedback on your assignments
- ❌ Cause workflow failures

## If Something Isn't Working

**DO NOT** try to fix it by modifying these files.

Instead:
1. Check that you've pushed your report (`index.qmd` or configured report file)
2. Verify you used the correct tag format: `feedback-v1`, `feedback-v2`, etc.
3. Check the Actions tab for error messages
4. Contact your instructor for help

## Files in This Directory

- `parse_report.py` - Extracts structure from your report
- `section_extractor.py` - Identifies relevant sections using AI
- `ai_feedback_criterion.py` - Generates criterion-based feedback
- `create_issue.py` - Posts feedback as a GitHub Issue

These files work together as a system. The workflow will validate their presence before running.
