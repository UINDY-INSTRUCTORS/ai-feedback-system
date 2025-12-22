# Faculty Quick Start: Using AI Report Feedback

This guide shows faculty how to set up AI-powered feedback for student reports in just 5 minutes.

## Prerequisites

- Your assignment repository on GitHub
- A GitHub education account (recommended for higher rate limits)

## Step 1: Create the Workflow File

Copy this to `.github/workflows/report-feedback.yml` in your assignment repository:

```yaml
name: AI Report Feedback

on:
  push:
    tags:
      - 'feedback-*'
      - 'review-*'

permissions:
  contents: read
  issues: write
  models: read

jobs:
  analyze:
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: UINDY-INSTRUCTORS/ai-feedback-system@main
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

## Step 2: Create Configuration Files

Create these three files in your assignment repository:

### `.github/config.yml`

Copy from the template and customize:

```yaml
# Your course and assignment name
report_file: "index.qmd"           # Student report file (quarto, markdown, jupyter, latex)
report_format: "quarto"

# AI model selection
model:
  primary: "gpt-4o"                # Best quality for detailed feedback
  fallback: "gpt-4o-mini"          # Fallback if rate limited

# Token and output settings
max_input_tokens: 15000
max_output_tokens: 3000

# GitHub Issue settings
issue_label: "ai-feedback"
issue_title_template: "📋 AI Feedback: {tag_name} ({date})"

# Feedback settings
feedback:
  scoring_enabled: false           # false = rubric levels only (formative)
                                   # true = include numerical scores

# Debug mode (optional - captures tokens, prompts, etc.)
debug_mode:
  enabled: false
  upload_artifacts: false
```

### `.github/feedback/RUBRIC.md`

Create a markdown rubric with your criteria:

```markdown
# Your Assignment Rubric

**Course**: YOUR COURSE
**Assignment**: YOUR ASSIGNMENT NAME
**Total Points**: 100

---

## Criterion 1: Description (20%)

Your description here.

### Performance Levels

| Level | Points | Description |
|-------|--------|-------------|
| **Exemplary** | 18-20 | Excellent work - exceeds expectations |
| **Satisfactory** | 14-17 | Good work - meets expectations |
| **Developing** | 10-13 | Needs improvement - partially meets expectations |
| **Unsatisfactory** | 0-9 | Does not meet requirements |

### Exemplary Indicators
- Indicator 1
- Indicator 2

### Common Issues
- Issue 1
- Issue 2

---

## Criterion 2: Analysis (30%)

[Add more criteria as needed...]
```

See examples in `ai-feedback-system/examples/` for complete rubrics.

### `.github/feedback/guidance.md`

Create a guidance file with instructions for the AI:

```markdown
# PART I: GENERAL GUIDANCE

## Course Context
**Course**: Your Course Name
**Assignment**: Your Assignment Name

## Feedback Philosophy
- Be encouraging and specific
- Focus on improvement, not judgment
- Provide actionable suggestions

## Technical Expectations
- Your expectations here
- What tools should they use?
- Any specific report structure?

# PART II: CRITERION-SPECIFIC GUIDANCE

## CRITERION: Criterion 1 Name

### What to Evaluate
- Specific things to look for
- Common student mistakes
- Red flags

### Feedback Suggestions
- **If [condition]**: "[Specific feedback]"

---

## CRITERION: Criterion 2 Name

[Add guidance for each criterion...]
```

See examples in `ai-feedback-system/examples/` for complete guidance files.

## Step 3: Test It Out

Push a tag to trigger the feedback:

```bash
git add .github/
git commit -m "Add AI feedback system"
git tag feedback-test-1
git push origin main --tags
```

The workflow will run, and a GitHub Issue will be created with the AI feedback!

## Generating Feedback for Student Submissions

For each submission, push a new tag:

```bash
git tag feedback-submission-1
git push origin feedback-submission-1
```

The feedback issue will appear in your repository!

## Customization Options

### Change the Model

Use a cheaper/faster model:
```yaml
model:
  primary: "gpt-4o-mini"    # Faster, cheaper
  fallback: "gpt-4o"
```

### Enable Numerical Scores

```yaml
feedback:
  scoring_enabled: true     # Include numerical scores in feedback
```

### Enable Vision/Image Analysis

```yaml
vision:
  enabled: true
  enabled_for_criteria:
    - "*"                   # All criteria
  max_images_per_criterion: 3
  image_token_budget: 2000
```

### Enable Debug Mode

To see extracted text, prompts, token usage:
```yaml
debug_mode:
  enabled: true
  upload_artifacts: true
```

Check GitHub Actions artifacts after the run to see debug output.

## Troubleshooting

### "No such file or directory: config.yml"
→ Make sure `.github/config.yml` exists

### "No such file or directory: RUBRIC.md"
→ Make sure `.github/feedback/RUBRIC.md` exists

### "429 Too Many Requests"
→ You've hit GitHub Models rate limit. Switch to `gpt-4o-mini` or get an education account.

### Feedback is too generic
→ Add more specific `common_issues` to your rubric
→ Make your `guidance.md` more detailed and course-specific

## Getting Help

See documentation in the `ai-feedback-system` repository:
- Complete setup guide: `docs/SETUP_GUIDE.md`
- Rubric examples: `examples/`
- All documentation: `docs/`

## What's Next?

- Customize your rubric to match your course
- Write detailed guidance for better feedback
- Enable debug mode to see what the AI extracts
- Gather feedback from students and iterate!
