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

## For Instructors: Quick Start (3 Steps)

### Step 1: Add the Workflow

Copy this file to your assignment repository:

```bash
# In your assignment repo, create the workflow directory
mkdir -p .github/workflows

# Copy the workflow from ai-feedback-system
cp ai-feedback-system/examples/workflows/report-feedback-action.yml .github/workflows/report-feedback.yml
```

Or simply create `.github/workflows/report-feedback.yml` with this content:

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

That's it! The action handles everything else.

### Step 2: Create Configuration Files

Create these three files in your assignment repository:

#### `.github/config.yml`

Copy from the template and customize:

```bash
cp ai-feedback-system/templates/config-template.yml .github/config.yml
```

Edit to set:
- Course name and code
- Assignment name
- Report filename (default: `index.qmd`)
- AI model (recommended: `gpt-4o` for quality)

#### `.github/feedback/RUBRIC.md`

**Recommended: Write in Markdown!** (much easier than YAML)

```bash
# Copy a markdown rubric example
cp ai-feedback-system/examples/phys-230-lab-example-RUBRIC.md .github/feedback/RUBRIC.md

# Or copy the generic template
cp ai-feedback-system/templates/lab-rubric-template.md .github/feedback/RUBRIC.md
```

Edit the rubric to match your assignment. It's just markdown with tables and bullet points!

The workflow automatically converts this to YAML for the AI system.

#### `.github/feedback/guidance.md`

```bash
# Copy the template
cp ai-feedback-system/templates/guidance-template.md .github/feedback/guidance.md
```

Edit to include:
- Course context and learning objectives
- What good work looks like
- Common student mistakes
- Feedback tone and expectations

### Step 3: Push and Test

```bash
# Commit and push
git add .github/
git commit -m "Add AI feedback system"
git push

# Create a test tag to trigger feedback
git tag feedback-test-1
git push origin feedback-test-1
```

Watch the GitHub Actions tab to see it run. A feedback issue will appear in your Issues tab!

---

## Available Templates & Examples

**Templates** (generic starting points):
- `templates/config-template.yml` - Configuration template
- `templates/lab-rubric-template.md` - Generic lab rubric (Markdown)
- `templates/programming-assignment-rubric-template.md` - Programming assignment (Markdown)
- `templates/guidance-template.md` - Feedback guidance template

**Examples** (course-specific, ready to customize):
- `examples/eeng-320-lab-example-RUBRIC.md` - Electronics Lab (Markdown)
- `examples/phys-230-lab-example-RUBRIC.md` - Instrumentation Lab (Markdown)
- `examples/phys-280-assignment-example-RUBRIC.md` - Scientific Computing (Markdown)
- `examples/eeng-340-project-example-RUBRIC.md` - Embedded Systems Project (Markdown)
- `examples/workflows/report-feedback-action.yml` - Simple workflow example

**See**:
- **Complete setup guide**: [docs/FACULTY_QUICKSTART.md](docs/FACULTY_QUICKSTART.md)
- **Detailed instructor guide**: [docs/INSTRUCTOR_GUIDE.md](docs/INSTRUCTOR_GUIDE.md)

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

### Comprehensive Notebook Output Extraction
- **Extracts ALL notebook cell outputs** - not just images
- **HTML tables** (pandas DataFrames) → Clean markdown tables
- **Text outputs** (print statements, calculations) → Preserved
- **Markdown and LaTeX** outputs → Included in context
- Analyzes measurement tables, statistical results, computational outputs
- More token-efficient than vision API for tabular data

### Rubric Converter - Write in Markdown!
- **Bidirectional converter** between YAML and Markdown
- **Faculty**: Write rubrics in easy Markdown format
- **Students**: Read beautiful rendered rubrics on GitHub
- **System**: Automatically converts Markdown → YAML for deployment
- Validates round-trip conversion (no data loss)
- Examples for all course types included

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
- **[docs/RUBRIC_CONVERTER.md](docs/RUBRIC_CONVERTER.md)** - How to write rubrics in Markdown instead of YAML
- **[docs/UPDATING_DEPLOYED_ASSIGNMENTS.md](docs/UPDATING_DEPLOYED_ASSIGNMENTS.md)** - How to update deployed assignments with new features
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and release notes
- **[TEMPLATE_SYSTEM.md](TEMPLATE_SYSTEM.md)** - Template system overview and workflow
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Technical deployment details
- **[.github/feedback/README.md](.github/feedback/README.md)** - Quick setup instructions
- **[docs/](docs/)** - Development notes and session summaries

---

## File Structure

**In your assignment repository (what faculty create):**

```
your-assignment-repo/
  .github/
    workflows/
      report-feedback.yml      ← Workflow file (copy from ai-feedback-system)

    config.yml                 ← Your assignment configuration
    feedback/
      RUBRIC.md                ← Your rubric (Markdown - easy to edit!)
      guidance.md              ← Your feedback instructions
      .gitignore               ← Ignores auto-generated rubric.yml

  index.qmd                    ← Student's report (or other filename)
```

**In ai-feedback-system repository (what we provide):**

```
ai-feedback-system/
  action.yml                   ← GitHub Action definition

  templates/                   ← Generic starting points
    config-template.yml
    lab-rubric-template.md
    programming-assignment-rubric-template.md
    guidance-template.md

  examples/
    workflows/
      report-feedback-action.yml   ← Copy this for your workflow

    eeng-320-lab-example-RUBRIC.md     ← Example rubrics
    phys-230-lab-example-RUBRIC.md
    phys-280-assignment-example-RUBRIC.md
    eeng-340-project-example-RUBRIC.md

  dot_github_folder/
    scripts/                   ← Managed by the action (not copied)
    workflows/
    feedback/

  docs/                        ← Full documentation
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
3. **Parse report** into sections, figures, equations, and notebook outputs
   - Extracts text from markdown sections
   - Finds embedded images
   - **Extracts notebook cell outputs** (tables, text, calculations)
   - **Converts HTML tables to markdown** for AI analysis
4. **For each rubric criterion**:
   - Extract relevant sections (text + notebook outputs)
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

### Recommended: GitHub Actions Testing

The easiest way to test is through GitHub Actions:

```bash
# Push your configuration
git add .github/
git commit -m "Test AI feedback system"
git push

# Trigger the workflow with a test tag
git tag feedback-test-1
git push origin feedback-test-1

# Watch the workflow run
# - Go to Actions tab on GitHub
# - Wait 1-3 minutes for it to complete
# - Check the Issues tab for your feedback

# Create additional feedback for iterations
git tag feedback-test-2
git push origin feedback-test-2
```

Each tag creates a separate feedback issue so you can see the progression.

### Debug Mode

Enable debug artifacts in `.github/config.yml` to see detailed information:

```yaml
debug_mode:
  enabled: true
  upload_artifacts: true
  save_context: true       # See extracted text
  save_prompts: true       # See AI prompts
  save_responses: true     # See AI responses
```

Then download the artifacts from the Actions tab to inspect:
- Token usage per criterion
- Extraction results
- Full prompts sent to the AI

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
