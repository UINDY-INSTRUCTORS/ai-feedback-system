# GitHub Models Enterprise & Education Account Settings

## Overview

This feedback system uses the **GitHub Models API** to provide AI-powered analysis of student lab reports. Understanding rate limits and enterprise settings is crucial for deploying this across all students in a course.

## ⚠️ CRITICAL: Workflow Permissions Required

**IMPORTANT**: Every workflow that uses GitHub Models API must include `models: read` in the permissions block.

```yaml
permissions:
  contents: read
  issues: write
  models: read  # ← REQUIRED for GitHub Models API access
```

**Without this permission, you will get 401 Unauthorized errors**, even if:
- GitHub Models is enabled at the organization level
- The repository has all other correct settings
- Your personal GitHub token works fine

This permission must be added to **ALL workflows** that call the Models API, including:
- `report-feedback.yml`
- `test-extraction-methods.yml`
- Any custom workflows using AI features

## GitHub Models Rate Limits

### Free Tier (Personal Accounts)
- **Rate limit**: 15 requests per minute (RPM)
- **Daily limit**: 150 requests per day
- **Token limits**: Varies by model (typically 4K-128K input tokens)
- **Models available**: GPT-4o, Claude 3.5 Sonnet, Llama 3.1, and others

### GitHub Education Benefits

**Important**: GitHub Education accounts operate on GitHub Enterprise Cloud and receive **significantly higher rate limits** than personal free tier accounts.

#### Education Enterprise Cloud Rate Limits
Based on GitHub Enterprise Cloud tier:
- **Rate limit**: 5,000 requests per hour per organization
- **Per-repository limits**: Much higher than free tier
- **Token limits**: Higher context windows available
- **No daily caps**: Enterprise accounts don't have the 150/day limit

### What You Need to Configure

#### 1. Organization Settings

**Location**: Your GitHub Education organization settings

**Required Configuration**:
1. **Enable GitHub Models ** for your organization
   - Go to: Organization Settings → Copilot → Models
   - Enable "GitHub Models API"
   - Grant access to specific repositories or all repositories

2. **Configure Model Access**
   - Select which AI models are available to your organization
   - Recommended models for this feedback system:
     - `gpt-4o` (primary, best balance of quality and speed)
     - `gpt-4o-mini` (fallback, faster and more economical)
     - `claude-3-5-sonnet-20241022` (alternative, good reasoning)

3. **Set Usage Policies**
   - Configure usage monitoring dashboards
   - Set up alerts for unusual usage patterns
   - Define usage policies for student repositories

#### 2. Repository Configuration

**Location**: Individual lab assignment repositories

**Required Configuration**:

1. **Enable GitHub Actions**
   - Ensure Actions are enabled for the repository
   - Configure Actions permissions:
     - Settings → Actions → General → Workflow permissions
     - Select: "Read and write permissions"
     - Enable: "Allow GitHub Actions to create and approve pull requests"

2. **Configure Secrets** (if needed)
   - The `GITHUB_TOKEN` is automatically provided by Actions
   - No additional secrets needed for GitHub Models API

3. **Workflow Permissions**
   Your `.github/workflows/report-feedback.yml` already has:
   ```yaml
   permissions:
     contents: read
     issues: write
     models: read  # ← This is key for GitHub Models access
   ```

#### 3. Repository Template Settings

For GitHub Classroom assignments:

1. **Template Repository Configuration**
   - Include the `.github/workflows/` directory in your template
   - Include the `.github/feedback/` directory with:
     - `config.yml`
     - `rubric.yml`
     - `guidance.md`
   - Include the `scripts/` directory with feedback generation scripts

2. **GitHub Classroom Settings**
   - Enable "Grant students admin access to their repositories"
   - Enable "Enable feedback pull requests"
   - Configure: "Run autograding tests on pull request"

#### 4. Model Selection Strategy

**Current Configuration** (in `.github/feedback/config.yml`):
```yaml
model:
  primary: "gpt-4o"       # Main model
  fallback: "gpt-4o-mini" # If rate limited
```

**Recommendations for Large Classes**:

For classes with **< 30 students**:
- Primary: `gpt-4o` (best quality)
- Fallback: `gpt-4o-mini`

For classes with **30-100 students**:
- Primary: `gpt-4o-mini` (faster, more economical)
- Fallback: `gpt-4o-mini` (same model, just for consistency)
- Alternative: `claude-3-5-sonnet-20241022` (good balance)

For classes with **> 100 students**:
- Consider staggered feedback generation (process in batches)
- Use `gpt-4o-mini` exclusively
- Monitor organization usage dashboards

## Rate Limit Management

### Current System Design

This feedback system is **designed for enterprise scale**:

1. **Parallel Processing**: Uses `ThreadPoolExecutor` with 2 workers
   - Analyzes multiple criteria simultaneously
   - Reduces overall wall-clock time

2. **Per-Criterion Analysis**: 
   - Each rubric criterion gets a separate API call
   - ~10-15 API calls per student report
   - More resilient to rate limits than single large calls

3. **Request Estimates**:
   - PreLab: ~5 criteria = 5 API calls
   - Lab Report: ~5-6 criteria = 5-6 API calls
   - Total: ~10-11 API calls per complete submission

### Capacity Planning

#### For a Class of 25 Students

**Scenario**: All students push feedback tags simultaneously

```
Students: 25
API calls per student: 10 (average)
Total API calls: 250 calls

Free tier: 150/day limit → ❌ Insufficient
Education Enterprise: 5,000/hour → ✅ Sufficient (completes in < 5 minutes)
```

#### For a Class of 100 Students

```
Students: 100
API calls per student: 10 (average)
Total API calls: 1,000 calls

Free tier: 150/day limit → ❌ Highly insufficient
Education Enterprise: 5,000/hour → ✅ Sufficient (completes in ~12 minutes)
```

### Monitoring Usage

**Organization-Level Monitoring**:
1. Go to: Organization Settings → Copilot → Usage
2. View: Models API usage by repository
3. Set up: Usage alerts and notifications

**Repository-Level Monitoring**:
- Check Actions workflow runs for rate limit errors
- Review workflow logs for retry patterns
- Monitor artifact outputs for incomplete analyses

### Handling Rate Limits

The current implementation **automatically handles rate limits** through:

1. **Fallback Model**: If primary model is rate-limited, switches to fallback
2. **Error Handling**: Continues processing other criteria if one fails
3. **Partial Feedback**: Generates feedback for successfully analyzed criteria

**Configuration to Adjust** (in `.github/feedback/config.yml`):

```yaml
# Token management
max_input_tokens: 15000    # Reduce if hitting token limits
max_output_tokens: 3000    # Reduce to lower cost per request

# Timeout settings
request_timeout: 120       # API request timeout in seconds
workflow_timeout: 10       # Workflow timeout in minutes (increase if needed)
```

## Best Practices for Classroom Use

### 1. Stagger Feedback Requests

**Problem**: All students tag at the same time (e.g., before deadline)

**Solutions**:
- Encourage students to request feedback early and often
- Set multiple "checkpoint" deadlines throughout the project
- Use different tag prefixes for different submissions:
  - `feedback-draft` for early feedback
  - `feedback-final` for final submission

### 2. Configure Workflow Triggers Carefully

**Current Trigger** (in `.github/workflows/report-feedback.yml`):
```yaml
on:
  push:
    tags:
      - 'feedback-*'
      - 'review-*'
```

**Alternative for Rate Limit Control**:
```yaml
on:
  workflow_dispatch:  # Manual trigger only
  push:
    tags:
      - 'feedback-*'
```

### 3. Set Clear Expectations

**Document for Students**:
1. How to request feedback: `git tag feedback-v1 && git push origin feedback-v1`
2. Expected turnaround time: ~5-10 minutes
3. Rate limit policies: "If many students request feedback simultaneously, your request may be queued"
4. Feedback iterations: "You can request feedback multiple times using v2, v3, etc."

### 4. Monitor and Adjust

**Weekly Checks**:
- Review organization usage dashboard
- Check for failed workflow runs
- Identify patterns (e.g., everyone requesting feedback 1 hour before deadline)
- Adjust model selection if needed

## Troubleshooting

### Rate Limit Errors

**Symptom**: Workflow fails with HTTP 429 errors

**Solutions**:
1. Verify organization has Models API enabled
2. Check that repository has `models: read` permission
3. Switch to fallback model in config
4. Reduce `max_workers` in parallel processing (currently 2)

### Token Limit Errors

**Symptom**: Workflow fails with "context length exceeded" errors

**Solutions**:
1. Reduce `max_input_tokens` in config.yml
2. Enable smart truncation: `truncation_strategy: "smart"`
3. Ask students to keep reports concise (focus on quality over quantity)

### Incomplete Feedback

**Symptom**: Feedback issue created but some criteria missing

**Solutions**:
1. Check workflow artifacts for error logs
2. Review timeout settings (may need to increase)
3. Verify report parsing is working correctly
4. Check that required sections exist in student reports

## Cost Considerations

### GitHub Models Pricing

**Education Accounts**: Typically included with GitHub Education benefits
- No per-request charges for education organizations
- Part of GitHub Enterprise Cloud benefits
- Generous rate limits suitable for classroom use

**Important**: Verify with your GitHub Education representative that:
1. Your organization has GitHub Models API enabled
2. Usage is included in your education benefits
3. You understand any usage caps or policies

### Optimizing Costs

Even with free education tier:

1. **Use Efficient Models**:
   - `gpt-4o-mini` for routine feedback
   - `gpt-4o` for final project reviews

2. **Optimize Prompts**:
   - Current system uses focused, criterion-specific prompts
   - Reduces token usage vs. analyzing entire report at once

3. **Cache and Reuse**:
   - Feedback artifacts are stored for 30 days
   - Students can review without re-generating

## Summary Checklist

Before rolling out to all students:

- [ ] **Organization Settings**
  - [ ] Enable GitHub Models API for organization
  - [ ] Configure model access (gpt-4o, gpt-4o-mini)
  - [ ] Set up usage monitoring dashboard
  - [ ] Verify education benefits and rate limits

- [ ] **Repository Template**
  - [ ] Include `.github/workflows/report-feedback.yml`
  - [ ] Include `.github/feedback/` configuration files
  - [ ] Include `scripts/` feedback generation scripts
  - [ ] Test with sample student repository

- [ ] **GitHub Classroom**
  - [ ] Configure assignment template
  - [ ] Enable student admin access
  - [ ] Set up feedback workflow

- [ ] **Documentation for Students**
  - [ ] How to request feedback (git tag + push)
  - [ ] Expected turnaround time
  - [ ] How to interpret AI feedback
  - [ ] Reminder that instructor makes final grading decisions

- [ ] **Testing**
  - [ ] Test with 2-3 pilot students first
  - [ ] Verify feedback quality
  - [ ] Confirm rate limits are adequate
  - [ ] Monitor workflow execution times

- [ ] **Monitoring Plan**
  - [ ] Regular check of usage dashboard
  - [ ] Weekly review of failed workflows
  - [ ] Student feedback survey on usefulness
  - [ ] Plan for scaling if class grows

## Additional Resources

- [GitHub Models Documentation](https://docs.github.com/en/github-models)
- [GitHub Enterprise Cloud Rate Limits](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting)
- [GitHub Education Benefits](https://education.github.com/benefits)
- [GitHub Actions Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)

## Questions?

If you need clarification on any of these settings:
1. Contact GitHub Education Support (they can verify your organization's limits)
2. Review your organization's Models API dashboard for current usage
3. Test with a pilot group before full deployment

## Answer to Original Question

**Q: What settings in the enterprise account would I need to adjust to use this with all my students?**

**A**: You need to:

1. **Enable GitHub Models API** in your organization settings (Organization Settings → Copilot → Models)
2. **Grant model access** to your classroom repositories (or all repositories)
3. **Verify your education benefits** include GitHub Models API access
4. **Set appropriate workflow permissions** (already configured in the workflow file)

**Q: Can we go above the free tier as a benefit of the education enterprise account?**

**A**: **YES!** 

Education accounts on GitHub Enterprise Cloud receive:
- **5,000 requests per hour** (vs. 150/day for free tier)
- **No daily caps** like personal accounts
- **Enterprise-grade rate limits** suitable for classroom use with 100+ students
- **Models API access included** in GitHub Education benefits

The 150/day limit mentioned in the code is for **free tier personal accounts**. Your education organization account has **much higher limits** that are more than adequate for classroom use.

**Recommended**: Contact GitHub Education support to confirm your specific organization's rate limits and ensure Models API is enabled.
