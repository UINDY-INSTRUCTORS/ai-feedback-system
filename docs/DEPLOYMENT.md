# AI Feedback System - Deployment Guide

## What We've Built

A complete AI-powered feedback system for student lab reports with:

✅ **AI Analysis Engine** - Uses GitHub Models API (GPT-4o) to analyze reports
✅ **Rubric-Based Evaluation** - Machine-readable rubric from RUBRICS.md
✅ **Automated Workflow** - GitHub Actions triggered by git tags
✅ **GitHub Issue Feedback** - Students receive detailed feedback as issues
✅ **Zero Configuration** - Uses built-in `GITHUB_TOKEN`, no API keys needed

## Project Structure

```
ai-feedback-system/
├── .github/
│   ├── workflows/
│   │   └── report-feedback.yml     # GitHub Actions workflow
│   └── feedback/
│       ├── rubric.yml              # Machine-readable rubric (EENG 320)
│       ├── guidance.md             # AI instruction manual
│       └── config.yml              # Technical configuration
├── scripts/
│   ├── parse_report.py             # Extract report structure
│   ├── ai_feedback.py              # Call GitHub Models API
│   └── create_issue.py             # Post feedback as issue
├── # Container uses python:3.11-slim image directly
├── pyproject.toml                  # Python dependencies (uv)
├── README.md                       # Student documentation
└── DEPLOYMENT.md                   # This file
```

## How It Works

### Student Workflow
1. Student writes report in `index.qmd`
2. Student commits and pushes: `git push`
3. Student requests feedback: `git tag feedback-v1 && git push origin feedback-v1`
4. GitHub Action runs automatically (2-3 minutes)
5. AI analyzes report against rubric
6. Feedback posted as GitHub Issue

### System Flow
```
Tag pushed → GitHub Actions → Docker Container → Parse Report
                                                      ↓
                                                  Load Rubric + Guidance
                                                      ↓
                                                  Call GitHub Models API
                                                      ↓
                                                  AI Analysis (GPT-4o)
                                                      ↓
                                                  Create GitHub Issue
```

### Technology Stack
- **GitHub Models**: Free AI inference (GPT-4o, Claude, etc.)
- **GitHub Actions**: Automated workflow execution
- **Docker**: Consistent Python 3.11 environment
- **Python**: Report parsing and API integration
- **Quarto**: Student report format

## Deployment Steps for Next Semester

### Option 1: Add to Existing GitHub Classroom Template

1. **Copy files to template repo**:
   ```bash
   cd your-classroom-template/
   cp -r ai-feedback-system/dot_github_folder .github
   cp -r ai-feedback-system/scripts .
   # Dockerfile no longer needed - workflow uses python:3.11-slim directly
   ```

2. **Update README for students**:
   - Add section on "Getting AI Feedback"
   - Explain tag-based workflow
   - Link to rubric and guidance

3. **Test the template**:
   - Create a test repo from template
   - Add sample `index.qmd`
   - Tag with `feedback-v1`
   - Verify workflow runs and issue is created

4. **Deploy to students**:
   - GitHub Classroom automatically provisions repos
   - Students get feedback system in every repo

### Option 2: Add to Existing Student Repos (This Semester)

If you want to test with current students:

```bash
# For each student repo
cd lab-N-submissions/lab-N-username/

# Copy feedback system
cp -r /path/to/ai-feedback-system/dot_github_folder .github
cp -r /path/to/ai-feedback-system/scripts .

# Commit and push
git commit -m "Add AI feedback system"
git push

# Test
git tag feedback-test
git push origin feedback-test
```

## Configuration per Course/Lab

### For Different Labs (Same Course)
No changes needed! The rubric is comprehensive for all EENG 320 labs.

### For Different Courses
Edit these three files:

1. **`.github/feedback/rubric.yml`**
   - Change criteria, weights, point values
   - Update keywords and common_issues
   - Adjust to your course's rubric

2. **`.github/feedback/guidance.md`**
   - Describe your course context
   - Explain your feedback philosophy
   - List course-specific common mistakes

3. **`.github/feedback/config.yml`**
   - Change `report_file` if not `index.qmd`
   - Adjust AI model (GPT-4o vs Claude vs others)
   - Modify token limits if needed

## Testing Locally

We've set up a `uv` environment for local testing:

```bash
cd ai-feedback-system/

# Parse a report
uv run python scripts/parse_report.py

# Generate AI feedback (requires GITHUB_TOKEN with models access)
export GITHUB_TOKEN="your-github-token"
uv run python scripts/ai_feedback.py

# The scripts will create:
# - parsed_report.json (report structure)
# - feedback.md (AI-generated feedback)
```

**Note**: You need a GitHub personal access token with `models:read` scope to test AI feedback locally. In GitHub Actions, `GITHUB_TOKEN` is provided automatically.

## GitHub Models Setup

### For Students (No Setup Needed)
- Students don't need API keys
- GitHub Actions uses built-in `GITHUB_TOKEN`
- Works automatically when tag is pushed

### For Instructors (Optional Local Testing)
1. Go to https://github.com/settings/tokens
2. Create Personal Access Token (classic)
3. Grant `models:read` permission
4. Use for local testing: `export GITHUB_TOKEN="ghp_..."`

### Rate Limits (Free Tier)
- **150 requests/day** per repository
- **15 requests/minute**
- **8000 tokens in / 4000 tokens out** per request

This is plenty for typical usage:
- ~10-15 feedback requests per student per lab
- Works for 10-100 students with free tier

## Docker Setup

### GitHub Actions Container
Workflow uses `python:3.11-slim` container:
- Lightweight (downloads in ~10 seconds)
- Includes Python 3.11 + pip
- Dependencies installed during workflow run

Uses your existing `ghcr.io/202420-phys-230/novnc:3` image:
- Includes Quarto, Python, Jupyter
- Adds pyyaml + requests for feedback scripts
- Students can run scripts locally if needed

### Custom Docker Image (Optional)
If you want a pre-built image with dependencies:

```bash
cd ai-feedback-system/

# Build
docker build -t eeng320-feedback:latest .

# Push to GitHub Container Registry
docker tag eeng320-feedback:latest ghcr.io/your-org/eeng320-feedback:latest
docker push ghcr.io/your-org/eeng320-feedback:latest

# Update workflow to use it
# In .github/workflows/report-feedback.yml:
# container:
#   image: ghcr.io/your-org/eeng320-feedback:latest
```

## Customization Examples

### Use Claude Instead of GPT-4o
Edit `.github/feedback/config.yml`:
```yaml
model:
  primary: "claude-3-5-sonnet-20241022"  # Claude Sonnet 3.5
  fallback: "gpt-4o-mini"
```

### Adjust Feedback Tone
Edit `.github/feedback/guidance.md`:
- Make more/less encouraging
- More/less specific
- More/less technical

### Add Course-Specific Checks
Edit `scripts/parse_report.py` to add:
- Required section validation
- File format checking
- Citation counting
- Code quality analysis

### Change Trigger Pattern
Edit `.github/workflows/report-feedback.yml`:
```yaml
on:
  push:
    tags:
      - 'review-*'  # Use 'review' instead of 'feedback'
      - 'check-*'   # Or 'check'
```

## Troubleshooting

### Workflow Fails to Run
- Check GitHub Actions is enabled in repo settings
- Verify tag pattern matches workflow trigger
- Check Actions tab for error logs

### "GITHUB_TOKEN doesn't have models access"
- GitHub Models requires GITHUB_TOKEN with models:read
- This should work automatically in GitHub Actions
- If not, wait a few days (feature may be rolling out)
- Fallback: use personal access token in repo secrets

### AI Feedback is Generic/Incorrect
- Review `guidance.md` - add more specific instructions
- Check `rubric.yml` - ensure criteria are clear
- Try Claude model instead of GPT-4o
- Add more examples in guidance.md

### Report Truncated Warning
- Reports >7000 tokens are truncated
- Increase `max_input_tokens` in config.yml
- Or use smarter chunking (future enhancement)

### No Issue Created
- Check permissions in workflow (needs `issues: write`)
- Verify `GITHUB_REPOSITORY` environment variable is set
- Check for errors in Actions logs

## Cost Analysis

### Free Tier (Current Setup)
- **GitHub Models**: Free tier sufficient for 150 feedback requests/day
- **GitHub Actions**: 2000 minutes/month free (each run ~3 min)
- **Storage**: Minimal (~10MB per repo)

**Total Monthly Cost**: $0

### If You Scale Beyond Free Tier
- GitHub Models paid tier: $0.0003/token (very cheap)
- GitHub Actions: $0.008/minute after free tier
- For 100 students × 10 requests/semester:
  - 1000 requests × 3 minutes = 3000 minutes
  - Cost: ~$8 for GitHub Actions
  - Models API: ~$5-10 for tokens
  - **Total: ~$15-20 per semester**

## Future Enhancements

Ideas for improvement:
- [ ] **Plagiarism hints**: Flag suspiciously similar reports
- [ ] **Cohort analysis**: Weekly summary of common issues
- [ ] **Gradebook integration**: Auto-populate suggested scores
- [ ] **Multi-file support**: Analyze Python scripts, data files
- [ ] **Comparative feedback**: "Your design is in the top 25%"
- [ ] **Progressive feedback**: Different criteria for early vs late labs
- [ ] **LaTeX support**: Parse LaTeX reports, not just Quarto
- [ ] **Voice feedback**: Generate audio summary with ElevenLabs

## Security Considerations

### Data Privacy
- Student reports sent to GitHub Models API
- GitHub's infrastructure (same as Copilot)
- Data not used for training models
- Remains within GitHub ecosystem

### Access Control
- Feedback system requires repo access
- Students can't see other students' feedback
- Issues are private to repository
- Instructor has full access to all feedback

### API Token Security
- `GITHUB_TOKEN` is ephemeral (expires after job)
- No long-lived credentials stored
- No risk of token leakage

## Support and Documentation

### For Students
- See `README.md` in their repos
- GitHub Docs: https://docs.github.com/en/github-models

### For Instructors
- This file (DEPLOYMENT.md)
- GitHub Models Docs: https://github.com/features/models
- GitHub Actions Docs: https://docs.github.com/en/actions

### Questions?
- Check Issues tab for common problems
- Review Actions logs for specific errors
- Test locally with `uv run` commands

---

**Built with**: GitHub Models, GitHub Actions, Python 3.11, Docker
**Tested on**: EENG 320 Lab 3 (Fall 2024)
**Ready for**: Spring 2025 deployment
