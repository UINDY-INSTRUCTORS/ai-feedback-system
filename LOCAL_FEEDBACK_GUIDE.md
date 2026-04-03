# Local Feedback Testing Guide

The ai-feedback-system now supports running feedback locally without creating GitHub issues. This enables:

- **Testing** feedback on your machine before deploying to GitHub
- **Batch processing** all student repos at once
- **Debugging** with flat-file output instead of GitHub issues
- **Reusing** instructor rubrics and guidance across all student repos

## Installation

```bash
cd /path/to/ai-feedback-system

# Ensure dependencies are installed
pip install pyyaml requests Pillow jupyter nbformat quarto

# Make the script executable
chmod +x run-local-feedback.py
```

## Usage

### Single Repo Testing

Run feedback on one student repo and save output to a file:

```bash
python run-local-feedback.py /path/to/student/repo
```

This will:
1. Create `.github/feedback/` in the student repo
2. Copy the instructor's `rubric.yml` and `guidance.md`
3. Run the entire feedback pipeline
4. Save feedback to `feedback-TIMESTAMP.md` in the repo root

### Batch Processing

Process all student repos in a directory:

```bash
python run-local-feedback.py /path/to/student/repos --batch --output-dir ./feedback-results
```

Example structure:
```
student/repos/
├── student-1/
│   ├── index.qmd
│   └── ...
├── student-2/
│   ├── index.qmd
│   └── ...
└── student-3/
    ├── index.qmd
    └── ...
```

Each repo's feedback will be saved to:
```
./feedback-results/student-1/feedback.md
./feedback-results/student-2/feedback.md
./feedback-results/student-3/feedback.md
```

### List Available Repos

Before batch processing, see what repos will be processed:

```bash
python run-local-feedback.py /path/to/student/repos --list
```

Output:
```
Found 3 student repos in /path/to/student/repos:
  ✓ student-1
  ✓ student-2
  ✓ student-3
```

### Custom Output Directory

Save all feedback to a specific directory:

```bash
python run-local-feedback.py /path/to/repo --output-dir /path/to/feedback-output
```

The feedback file will be saved to:
```
/path/to/feedback-output/repo-name/feedback.md
```

## Configuration

The tool automatically uses the instructor repo's `rubric.yml` and `guidance.md` from:
```
ai-feedback-system/.github/feedback/
```

Each student repo gets its own `.github/config.yml` (created automatically) that:
- Points to the correct rubric/guidance
- Sets output format to `flat_file`
- Uses the same AI model settings

You can override the instructor repo path:

```bash
python run-local-feedback.py /path/to/repo \
  --instructor-repo /path/to/custom/feedback-system
```

## Output Files

Each feedback output is a Markdown file containing:

```markdown
## 🤖 AI Report Feedback
> **Requested**: `local-test` • **Generated**: 2025-04-03 at 15:30:45 UTC
> **Model**: gpt-4o

---

### Criterion 1
**Assessment**: `Exemplary`

> Summary of feedback

**Strengths:**
- Point 1
- Point 2

**Areas for Improvement:**
- Point 1

...

### 📚 Resources
- [View Rubric](...)

### 📋 Report Statistics
| Metric | Count |
|--------|-------|
| Words  | 1234  |
| Figures| 5     |
```

## Workflow Examples

### Example 1: Quick Local Test

Test feedback on a single repo before deploying:

```bash
# Clone a student repo locally
git clone https://github.com/student/assignment.git student-test

# Run feedback locally
python run-local-feedback.py student-test

# Review feedback-TIMESTAMP.md in student-test/
```

### Example 2: Batch Review Before Deployment

Process all submissions, review them, then deploy to GitHub:

```bash
# Batch process all repos to flat files
python run-local-feedback.py ~/student-repos --batch --output-dir ./feedback-review

# Review all feedback
ls ./feedback-review/*/feedback.md | xargs less

# Once satisfied, deploy (push tags to GitHub to trigger GitHub Actions)
```

### Example 3: Debugging Individual Repo

If a repo's feedback fails, debug it step-by-step:

```bash
# Run with verbose output
cd /path/to/student/repo
python /path/to/ai-feedback-system/dot_github_folder/scripts/parse_report.py
cat parsed_report.json | jq .  # Inspect parsed content

python /path/to/ai-feedback-system/dot_github_folder/scripts/ai_feedback_criterion.py
cat feedback.json | jq .  # Inspect AI response

# Check the config
cat .github/config.yml
```

## Troubleshooting

### "Missing required file: .github/feedback/rubric.yml"

The instructor repo path is incorrect. Make sure you have the right path:

```bash
python run-local-feedback.py /path/to/repo \
  --instructor-repo /Users/steve/Development/quarto_reports/ai-feedback-system
```

### "Quarto render had issues"

If the student's report has syntax errors, the script continues anyway (Quarto errors don't block feedback). Check:

```bash
cd /path/to/student/repo
quarto render index.qmd  # See the full error
```

### "Feedback generation failed"

This could be:
1. **API authentication** - Missing or invalid GitHub token (if using GitHub Models)
2. **Network issues** - Check your connection
3. **Rate limiting** - Wait a moment and retry
4. **Large report** - If the report is huge, it might exceed token limits

Check the error message for details:

```bash
cat feedback.json  # See what feedback was generated
cat .github/debug/  # If debug mode is enabled
```

### "No images found in repo"

This is a warning, not an error. The feedback script couldn't locate images referenced in the report. This is usually fine—feedback still generates without them.

## Integration with Your Workflow

### Option 1: Local Testing Only

Use this for testing feedback before deploying to students:

```bash
# In your instructor repo
python run-local-feedback.py ~/p4-circuit-math-alconp --output-dir ./test-feedback

# Review test-feedback/p4-circuit-math-alconp/feedback.md
# If good, push to GitHub to trigger the real feedback workflow
```

### Option 2: Hybrid - GitHub Actions + Local Override

Deploy normally to GitHub Actions (which creates issues), but also keep local feedback files for your records:

```bash
# Deploy via GitHub (normal workflow)
cd ~/student-repo && ./get-feedback.sh

# Create local backup
python /path/to/ai-feedback-system/run-local-feedback.py ~/student-repo \
  --output-dir ~/my-feedback-backups
```

### Option 3: Pre-Deployment Batch Check

Before opening a classroom to students, batch-test all repos:

```bash
# Set up all student repos locally
for student in students-2025-spring/*; do
  git clone $student ~/test-repos/$(basename $student)
done

# Batch process all
python run-local-feedback.py ~/test-repos --batch --output-dir ./batch-review

# Review feedback/correctness before students get access

# Remove test repos and deploy to GitHub
```

## Environment Variables

You can also control behavior via environment variables:

```bash
# Force local test mode (just print, don't save)
LOCAL_TEST=true python run-local-feedback.py /path/to/repo

# Set output path explicitly
OUTPUT_PATH=/custom/path/feedback.md python run-local-feedback.py /path/to/repo

# Use specific model
MODEL_PRIMARY=gpt-4o-mini python run-local-feedback.py /path/to/repo
```

## Next Steps

- [Back to README](./README.md)
- [See AI Feedback System Documentation](./dot_github_folder/)
- [Review Rubric Template](./templates/)
