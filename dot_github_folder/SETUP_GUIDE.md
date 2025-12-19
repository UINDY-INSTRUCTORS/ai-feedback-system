# Quick Setup Guide for AI Feedback System

## For Instructors: Deploying to Your Class

This guide provides a quick reference for setting up the AI feedback system across all student repositories in your course.

## Prerequisites

✅ GitHub Education account with GitHub Enterprise Cloud access  
✅ Organization admin permissions  
✅ GitHub Classroom set up for your course  

## Step 1: Enable GitHub Models API (5 minutes)

1. Go to your **Organization Settings**
2. Navigate to: **Copilot** → **Models**
3. Enable **"GitHub Models API"**
4. Select access level:
   - ✅ Recommended: "Enable for all repositories"
   - Alternative: "Enable for specific repositories" (select your classroom repos)

5. Choose available models:
   - ✅ `gpt-4o` (best quality)
   - ✅ `gpt-4o-mini` (faster, economical)
   - Optional: `claude-3-5-sonnet-20241022`

## Step 2: Verify Your Rate Limits (2 minutes)

Your education organization should have:
- ✅ **5,000 requests per hour** (not 150/day)
- ✅ **No daily caps**
- ✅ **Enterprise-grade limits**

**To verify**:
1. Go to: Organization Settings → Copilot → Usage
2. Check the "Models API" section
3. Confirm your tier shows "Enterprise" or "Education"

❓ **Not sure?** Contact GitHub Education support to confirm your benefits.

## Step 3: Configure GitHub Classroom Assignment (10 minutes)

### 3.1 Create Template Repository

Your template should include:

```
your-template-repo/
├── .github/
│   ├── workflows/
│   │   └── report-feedback.yml      # Workflow file
│   └── feedback/
│       ├── README.md                 # Documentation index
│       ├── config.yml                # Configuration
│       ├── rubric.yml                # Grading rubric
│       ├── guidance.md               # AI instructions
│       ├── GITHUB_MODELS_SETTINGS.md # Comprehensive settings guide
│       └── SETUP_GUIDE.md            # This quick setup guide
├── scripts/
│   ├── ai_feedback_criterion.py
│   ├── parse_report.py
│   ├── create_issue.py
│   └── section_extractor.py
└── [your assignment files]
```

### 3.2 Configure GitHub Classroom

1. Create new assignment in GitHub Classroom
2. Select your template repository
3. Configure settings:
   - ✅ **Grant students admin access**: Enabled
   - ✅ **Enable feedback pull requests**: Optional
   - ✅ **Deadline**: Set your due date

### 3.3 Test with Pilot Students

Before rolling out to entire class:
1. Invite 2-3 students to test
2. Have them push a `feedback-v1` tag
3. Verify feedback is generated successfully
4. Check feedback quality and turnaround time

## Step 4: Document for Students (5 minutes)

Add to your assignment README:

```markdown
## How to Request AI Feedback

1. Complete your lab report in `index.qmd`
2. Commit and push your changes
3. Request feedback:
   ```bash
   git tag feedback-v1
   git push origin feedback-v1
   ```
4. Wait ~5-10 minutes
5. Check the "Issues" tab for your feedback

### Requesting Updated Feedback

Made improvements? Request new feedback:
```bash
git tag feedback-v2  # increment version
git push origin feedback-v2
```

### Important Notes

- 🤖 AI feedback is **guidance**, not your grade
- ✅ Your instructor makes final grading decisions  
- 🔄 You can request feedback multiple times
- ⏱️ Feedback typically arrives in 5-10 minutes
- 📊 Addresses each rubric criterion individually
```

## Step 5: Monitor Usage (Ongoing)

### Weekly Checks

1. **Usage Dashboard**
   - Go to: Organization Settings → Copilot → Usage
   - Review Models API usage trends
   - Check for any anomalies

2. **Failed Workflows**
   - Monitor student repositories for failed Actions
   - Common issues: token limits, parsing errors
   - Help students debug as needed

3. **Feedback Quality**
   - Spot-check generated feedback
   - Adjust `rubric.yml` or `guidance.md` if needed
   - Update model selection in `config.yml` if appropriate

### Monthly Review

- Survey students on feedback usefulness
- Adjust rubric criteria based on common issues
- Update guidance for better quality feedback
- Optimize configuration for your class size

## Capacity Planning by Class Size

### Small Class (< 30 students)

**Current Config is Optimal:**
```yaml
model:
  primary: "gpt-4o"       # Best quality
  fallback: "gpt-4o-mini"
```

**Expected Load:**
- ~300 API calls if all students request simultaneously
- Completes in: ~5 minutes
- Well within rate limits ✅

### Medium Class (30-100 students)

**Consider Optimization:**
```yaml
model:
  primary: "gpt-4o-mini"  # Faster, still good quality
  fallback: "gpt-4o-mini"
```

**Expected Load:**
- ~1,000 API calls if all students request simultaneously
- Completes in: ~10-12 minutes
- Well within rate limits ✅

### Large Class (> 100 students)

**Recommended Strategy:**

1. Use `gpt-4o-mini` exclusively
2. Set staggered deadlines:
   - Week 1: Students with last name A-M
   - Week 2: Students with last name N-Z
3. Encourage early feedback requests

**Expected Load:**
- ~1,500+ API calls if all students request simultaneously
- Completes in: ~15-20 minutes
- Still within rate limits ✅

## Troubleshooting Quick Reference

### "Rate limit exceeded" errors

**Cause**: Unusual for education accounts  
**Fix**:
1. Verify Models API is enabled in org settings
2. Check that your organization has enterprise tier
3. Contact GitHub Education support

### "Token limit exceeded" errors

**Cause**: Student report is very long  
**Fix**: In `.github/feedback/config.yml`:
```yaml
max_input_tokens: 10000  # Reduce from 15000
truncation_strategy: "smart"  # Enable smart truncation
```

### Workflow times out

**Cause**: Many criteria, slow network, or many students  
**Fix**: In `.github/feedback/config.yml`:
```yaml
workflow_timeout: 15  # Increase from 10 minutes
```

### Incomplete feedback

**Cause**: Parsing errors or missing sections  
**Fix**:
1. Check workflow logs (Actions tab)
2. Download artifacts to see error details
3. Verify student report has proper structure
4. Update `section_extractor.py` if needed

## Support Resources

- 📖 **Detailed Documentation**: [GITHUB_MODELS_SETTINGS.md](./GITHUB_MODELS_SETTINGS.md)
- 🔧 **Configuration Reference**: [config.yml](./config.yml)
- 📋 **Rubric Customization**: [rubric.yml](./rubric.yml)
- 🤖 **AI Instructions**: [guidance.md](./guidance.md)

### Getting Help

1. **GitHub Education Support**: education@github.com
2. **GitHub Models Documentation**: https://docs.github.com/en/github-models
3. **GitHub Classroom**: https://classroom.github.com/help

## Success Checklist

Before going live with all students:

- [ ] GitHub Models API enabled for organization
- [ ] Model access configured (gpt-4o, gpt-4o-mini)
- [ ] Template repository includes all required files
- [ ] GitHub Classroom assignment created
- [ ] Tested with 2-3 pilot students
- [ ] Student documentation added to README
- [ ] Usage monitoring dashboard set up
- [ ] Response plan for common issues
- [ ] Student survey prepared for feedback

## Estimated Time Investment

- **Initial Setup**: 30-45 minutes (one time)
- **Per Assignment**: 15-20 minutes (template customization)
- **Weekly Monitoring**: 10-15 minutes
- **Student Support**: 5-10 minutes per issue (rare)

## Expected Benefits

Based on pilot testing:
- ✅ Students receive detailed, criterion-specific feedback
- ✅ Feedback turnaround: 5-10 minutes (vs. days for manual)
- ✅ Consistent rubric application across all students
- ✅ Students can iterate and improve before final submission
- ✅ Reduces instructor grading time (AI provides first pass)
- ✅ Students learn from specific, actionable suggestions

---

**Ready to deploy?** Start with Step 1 above, or see [GITHUB_MODELS_SETTINGS.md](./GITHUB_MODELS_SETTINGS.md) for comprehensive documentation.
