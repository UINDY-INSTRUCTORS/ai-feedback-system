# AI-Powered Report Feedback System

Automated, AI-driven feedback system for student lab reports and assignments using GitHub Models and GitHub Actions.

## Overview

This system provides detailed, criterion-based feedback on student work by:
- Analyzing reports against custom rubrics
- Generating specific, actionable suggestions
- Posting feedback as GitHub Issues
- Supporting multiple courses and assignment types

**Free** for GitHub education accounts • **Template-based** for easy customization • **Multi-course ready**

---

## For Instructors: Quick Start

### 1. Copy to Your Assignment Repo

```bash
# Copy the feedback system to your GitHub Classroom template
cp -r ai-feedback-system/{.github,scripts} your-assignment-repo/
cd your-assignment-repo
```

### 2. Customize for Your Assignment

```bash
cd your-assignment-repo/.github/feedback

# Option A: Copy from template (recommended for first-time setup)
cp /path/to/ai-feedback-system/templates/config-template.yml config.yml
cp /path/to/ai-feedback-system/templates/lab-rubric-template.yml rubric.yml
cp /path/to/ai-feedback-system/templates/guidance-template.md guidance.md

# Option B: Copy from a course example (if similar assignment exists)
cp /path/to/ai-feedback-system/examples/eeng-320-lab-example.yml rubric.yml
cp /path/to/ai-feedback-system/templates/config-template.yml config.yml
cp /path/to/ai-feedback-system/templates/guidance-template.md guidance.md

# Then customize each file:
# - Edit config.yml: Set assignment name, course, report filename
# - Edit rubric.yml: Adjust criteria, weights, keywords
# - Edit guidance.md: Add course context, common mistakes, examples
```

**Available:**
- **Templates** (in `templates/`): Generic starting points
- **Examples** (in `examples/`): Course-specific examples from EENG-320, PHYS-280, PHYS-230, EENG-340

### 3. Customize & Test

Edit `.github/feedback/rubric.yml`:
- Update assignment name and course
- Adjust criterion weights (must total 100)
- Update keywords to match your domain
- Add assignment-specific common issues

Test locally:
```bash
export GITHUB_TOKEN="your_github_token"
uv run python scripts/parse_report.py
uv run python scripts/ai_feedback_criterion.py
cat feedback.md  # Review the generated feedback
```

### 4. Deploy to Students

```bash
git add .github scripts
git commit -m "Add AI feedback system"
git push
```

Students can now request feedback by tagging their commits!

**See**: [INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md) for complete documentation.

---

## For Students: How to Get Feedback

### 1. Complete Your Report

Write your report in `index.qmd` (or whatever file your instructor specified):
- Follow the assignment requirements
- Include all sections, figures, and analysis
- Commit your work regularly

### 2. Request Feedback

When ready for feedback:

```bash
# Make sure your latest work is committed
git add .
git commit -m "Complete assignment"
git push

# Create a feedback tag
git tag feedback-v1
git push origin feedback-v1
```

### 3. Wait for Feedback (1-3 minutes)

- A GitHub Action will automatically run
- AI will analyze your report against the rubric
- A new GitHub Issue will be created with detailed feedback
- You'll get a notification when it's ready

### 4. Review and Improve

The feedback issue will include:
- **Assessment** for each rubric criterion
- **Strengths** - what you did well
- **Areas for Improvement** - specific, actionable suggestions
- **Suggested Rating** - points for each criterion

Use this feedback to improve your work before the final deadline!

### Can I Get Feedback Multiple Times?

Yes! Just create a new tag:
```bash
git tag feedback-v2
git push origin feedback-v2
```

Each feedback request creates a separate issue so you can track your progress.

---

## System Features

### Template-Based Architecture
- **Generic templates** for different assignment types
- **Course-specific examples** for electronics, computing, instrumentation, embedded systems
- **Easy customization** per assignment

### Criterion-Based Analysis
- Analyzes each rubric criterion separately
- Sends only relevant report sections to AI
- Provides focused, detailed feedback per criterion
- Works within GitHub Models token limits

### Multi-Course Support
Four course examples included:
- **EENG-320** (Electronics) - Circuit design, simulation, experimentation
- **PHYS-280** (Scientific Computing) - Algorithms, code quality, performance
- **PHYS-230** (Lab Instrumentation) - Calibration, measurements, uncertainty
- **EENG-340** (Interfacing Lab) - Hardware, firmware, testing

### GitHub Models Integration
- Uses free GitHub Models API (education tier)
- Enterprise limits: 5,000 requests/hour
- Automatic authentication via GitHub Actions
- No external API keys needed

---

## Documentation

- **[INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md)** - Complete setup, customization, and troubleshooting guide
- **[TEMPLATE_SYSTEM.md](TEMPLATE_SYSTEM.md)** - Template system overview and workflow
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Technical deployment details
- **[.github/feedback/README.md](.github/feedback/README.md)** - Quick setup instructions
- **[docs/](docs/)** - Development notes and session summaries

---

## File Structure

```
your-assignment-repo/
  .github/
    feedback/
      config.yml               ← Your assignment config
      rubric.yml               ← Your custom rubric
      guidance.md              ← Your AI instructions

      templates/               ← Generic templates
        lab-rubric-template.yml
        programming-assignment-rubric-template.yml
        guidance-template.md

      examples/                ← Course-specific examples
        eeng-320-lab-example.yml
        phys-280-assignment-example.yml
        phys-230-lab-example.yml
        eeng-340-project-example.yml

    workflows/
      report-feedback.yml      ← GitHub Actions workflow

  scripts/
    parse_report.py            ← Parse student report
    section_extractor.py       ← Extract relevant sections per criterion
    ai_feedback_criterion.py   ← Generate AI feedback
    create_issue.py            ← Post feedback as GitHub Issue

  index.qmd                    ← Student's report
```

---

## Requirements

### For Instructors (Setup)
- GitHub education account (for free GitHub Models access)
- Python 3.11+ with uv (for local testing)
- GitHub Classroom repo (recommended)

### For Students (Usage)
- Git and GitHub basics
- Nothing else - the system runs automatically!

---

## How It Works

1. **Student tags commit** for feedback (e.g., `feedback-v1`)
2. **GitHub Actions triggers** workflow
3. **Parse report** into sections, figures, equations
4. **For each rubric criterion**:
   - Extract relevant sections
   - Send to GitHub Models API
   - Get focused feedback
5. **Combine feedback** from all criteria
6. **Post as GitHub Issue** with detailed suggestions

**Parallel processing** (2 concurrent requests) • **10-15 seconds** for typical report • **Free** with education account

---

## Customization Examples

### Electronics Lab
Focus: Circuit design → Simulation → Experimentation
```bash
cp examples/eeng-320-lab-example.yml .github/feedback/rubric.yml
```

### Programming Assignment
Focus: Correctness → Code quality → Performance
```bash
cp examples/phys-280-assignment-example.yml .github/feedback/rubric.yml
```

### Instrumentation Lab
Focus: Calibration → Measurements → Uncertainty
```bash
cp examples/phys-230-lab-example.yml .github/feedback/rubric.yml
```

### Embedded Systems Project
Focus: Hardware → Firmware → Testing
```bash
cp examples/eeng-340-project-example.yml .github/feedback/rubric.yml
```

Then customize criteria weights, keywords, and common issues for your specific assignment.

---

## Testing

### Local Testing (Without GitHub Actions)

```bash
# Set up environment
export GITHUB_TOKEN="your_github_token"
cd your-assignment-repo

# Test report parsing
uv run python scripts/parse_report.py
# Creates: parsed_report.json

# Test AI feedback generation
uv run python scripts/ai_feedback_criterion.py
# Creates: feedback.md

# Review feedback
cat feedback.md
```

### GitHub Actions Testing

```bash
# Push to test repo
git add .github scripts
git commit -m "Test AI feedback system"
git push

# Trigger workflow
git tag test-feedback
git push origin test-feedback

# Watch in Actions tab
# Check Issues tab for feedback
```

---

## Support

### Getting Help
- See [INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md) for detailed documentation
- Check [Troubleshooting](INSTRUCTOR_GUIDE.md#troubleshooting) section
- Review [examples/](.github/feedback/examples/) for working configurations

### Contributing
This is a template repository. Feel free to:
- Customize for your courses
- Share improved rubrics with colleagues
- Adapt for new disciplines

### Credits
Built with GitHub Models API and Claude Code.

---

**Ready to start?** See [INSTRUCTOR_GUIDE.md](INSTRUCTOR_GUIDE.md) for the complete setup guide!
