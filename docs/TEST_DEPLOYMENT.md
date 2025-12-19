# Testing AI Feedback System in GitHub Actions

## Quick Test Deployment

### 1. Choose a Test Repository

Pick one of these for testing:
- **Option A**: Existing EENG-340 student submission (already has a report)
- **Option B**: Create new test repo with sample report
- **Option C**: Use a GitHub Classroom assignment template

**Recommended**: Use an existing student submission repo to test with real data.

### 2. Copy System Files

From `ai-feedback-system/`, copy to your test repo:

```bash
# Navigate to test repo
cd /path/to/test-repo

# Copy feedback system files
cp -r /path/to/ai-feedback-system/dot_github_folder .github
cp -r /path/to/ai-feedback-system/scripts/
# Dockerfile no longer needed - workflow uses python:3.11-slim directly
```

### 3. Customize for This Assignment

Edit `.github/feedback/`:
- `config.yml` - Update assignment name/course
- `rubric.yml` - Use appropriate rubric (EENG-340, PHYS-280, etc.)
- `guidance.md` - Use appropriate guidance

**For quick test**: The EENG-340 curve tracer config is already set up!

### 4. Commit and Push

```bash
git add .github
git commit -m "Add AI feedback system"
git push
```

### 5. Trigger Feedback

Create a tag to trigger the workflow:

```bash
git tag feedback-test-1
git push origin feedback-test-1
```

### 6. Monitor Execution

1. Go to repository → **Actions** tab
2. Watch the workflow run
3. Check for errors in the logs

### 7. Review Feedback

Once complete:
1. Go to repository → **Issues** tab
2. Find issue labeled `ai-feedback`
3. Review the feedback quality

---

## What to Check

### ✅ Workflow Runs Successfully
- All steps complete without errors
- Python dependencies install
- Scripts execute

### ✅ Feedback Quality
- Specific to this assignment
- References actual sections/figures from report
- Actionable suggestions
- Appropriate tone

### ✅ Token Usage
- Check Actions logs for token usage per criterion
- Should be ~600-3000 tokens per request
- All criteria analyzed successfully

---

## Expected Behavior

### For EENG-340 Curve Tracer (6 criteria):
- ~6 API requests (one per criterion)
- ~10-15 seconds total (with concurrency limit of 2)
- Feedback should be ~15-20K characters
- Issue created with detailed feedback

### Success Indicators:
```
🔍 Analyzing criteria in parallel...
   Analyzing: System Architecture & Design (15%)
      Prompt size: ~2400 tokens
      ✅ Complete
   Analyzing: Hardware Design & Implementation (20%)
      Prompt size: ~2800 tokens
      ✅ Complete
   ...
✨ Analysis complete!
   - 6/6 criteria analyzed successfully
   - Total feedback length: 18543 characters
```

---

## Troubleshooting

### Workflow doesn't trigger
- Check `.github/workflows/report-feedback.yml` exists
- Verify tag pattern matches (default: `feedback-*`)
- Check Actions tab is enabled for repo

### Workflow fails
- Check Actions logs for specific error
- Common issues:
  - Missing `index.qmd` (check `config.yml` for correct filename)
  - Invalid YAML in rubric/config
  - Python dependency issues (check)

### No issue created
- Check if workflow completed successfully
- Look for errors in `create_issue.py` step
- Verify `GITHUB_TOKEN` permissions (should be automatic)

### Feedback is too generic
- Review `guidance.md` - add more specifics
- Update `common_issues` in rubric criteria
- Add assignment-specific examples

---

## Quick Test Repos

### Test with EENG-340 Curve Tracer

```bash
# Copy to an existing EENG-340 submission
cd /Users/steve/Development/courses/eeng/eeng340/202420/repos/p1-curve-tracer-submissions/p1-curve-tracer-irfultz

# Copy feedback system (already configured for this assignment!)
cp -r /path/to/ai-feedback-system/dot_github_folder .github
cp -r /Users/steve/Development/courses/eeng/eeng320/202510/repos/ai-feedback-system/scripts/
# Dockerfile no longer needed - workflow uses python:3.11-slim directly

# Commit and test
git add .github
git commit -m "Test AI feedback system"
git push

# Trigger
git tag feedback-test
git push origin feedback-test

# Watch in Actions tab!
```

### Test with PHYS-280 Assignment

```bash
# Find a PHYS-280 submission
cd /Users/steve/Development/courses/ph-misc/ph280/202320/repos/[some-submission]

# Copy system
cp -r /path/to/ai-feedback-system/dot_github_folder .github
cp -r /path/to/ai-feedback-system/scripts .

# Update config
cd .github/feedback
# Use phys-280-assignment-example.yml as rubric.yml
# Create appropriate guidance.md

# Commit, push, tag
```

---

## After Testing

### If it works:
1. Note what feedback quality was like
2. Adjust rubric/guidance based on results
3. Deploy to GitHub Classroom template

### If issues:
1. Check Actions logs for specific errors
2. Verify rubric/config/guidance syntax
3. Test locally with actual `GITHUB_TOKEN` from GitHub Actions

### Iterate:
1. Adjust rubric keywords based on what student actually wrote
2. Add more `common_issues` that the AI should catch
3. Refine guidance for better feedback tone

---

## Ready to Deploy?

**Files needed in assignment repo**:
- ✅ `.github/workflows/report-feedback.yml` (workflow)
- ✅ `.github/feedback/config.yml` (assignment config)
- ✅ `.github/feedback/rubric.yml` (assignment rubric)
- ✅ `.github/feedback/guidance.md` (AI instructions)
- ✅ `scripts/parse_report.py`
- ✅ `scripts/section_extractor.py`
- ✅ `scripts/ai_feedback_criterion.py`
- ✅ `scripts/create_issue.py`


All these files are in `ai-feedback-system/` and ready to copy!

**Next step**: Choose a test repo and deploy!
