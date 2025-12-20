# AI Feedback System - Instructor Quick-Start Guide

## Overview

This system provides automated, criterion-based AI feedback on student lab reports, programming assignments, and projects. It uses GitHub Models API (free for education accounts) to analyze student work against your custom rubric and provide detailed, actionable feedback.

### Key Features
- ✅ **Assignment-specific rubrics**: Each assignment has its own customized rubric
- ✅ **Criterion-based analysis**: Analyzes each rubric criterion separately for detailed feedback
- ✅ **Automatic GitHub Issues**: Posts feedback as a GitHub Issue when students request it
- ✅ **Works with any course**: Easily customizable for different disciplines
- ✅ **Quarto/Markdown/Jupyter support**: Analyzes student reports in multiple formats
- ✅ **Free tier friendly**: Designed to work within GitHub Models rate limits

---

## Quick Start (5 Minutes)

### 1. Copy Template Files to Your Assignment Repo

```bash
# In your GitHub Classroom assignment template repo:
# Copy and rename dot_github_folder to .github
cp -r ai-feedback-system/dot_github_folder .github

# Note: Dockerfile no longer needed - workflow uses python:3.11-slim directly
```

### 2. Customize the Rubric

Edit `.github/feedback/rubric.yml`:

```yaml
assignment:
  name: "Lab 1: Introduction to Circuits"
  course: "EENG 320"
  total_points: 100

criteria:
  - id: problem_formulation
    name: "Problem Formulation & Objectives"
    weight: 20
    description: "Student identifies objectives and requirements clearly"

    levels:
      exemplary:
        description: "Clear, specific objectives"
        point_range: [18, 20]
      # ... more levels

    keywords: [objective, goal, requirement]
    common_issues:
      - "Objectives too vague"
      - "Missing success criteria"

  # ... more criteria
```

Use the templates in `.github/feedback/templates/` as starting points!

### 3. Customize the Guidance

Edit `.github/feedback/guidance.md` to tell the AI:
- What students are learning in this assignment
- Common mistakes to watch for
- What excellent work looks like
- Your feedback style preferences

### 4. Test It

```bash
cd your-assignment-repo

# Make sure you have a GitHub token with repo access
export GITHUB_TOKEN="your_token_here"

# Parse a sample student report
uv run python .github/scripts/parse_report.py

# Generate AI feedback
uv run python .github/scripts/ai_feedback_criterion.py

# Review feedback.md
cat feedback.md
```

### 5. Deploy to Students

When students push to GitHub, they can request feedback with:

```bash
git tag feedback-v1
git push origin feedback-v1
```

The system automatically analyzes their report and posts feedback as a GitHub Issue!

---

## Protecting the Feedback System from Tampering

**Important:** When deployed to student repos, students have write access and could potentially modify or delete the `.github` folder (workflows, scripts, rubrics). To prevent this:

### Recommended: Organization Rulesets (Automatic Protection)

If you're using GitHub Classroom (with an organization), set up organization rulesets once to automatically protect all student repos:

1. Go to your organization Settings → Rules → Rulesets
2. Create a new branch ruleset:
   - Name: "Protect AI Feedback System"
   - Target: All repositories
   - Branch: `main`
   - Enable: "Require pull request before merging" (1 approval)

**Result:** Students can push their work normally, but cannot modify the `.github` folder.

**Full setup guide:** See `docs/TAMPER_PROTECTION_SETUP.md`

### Validation Script (Optional but Recommended)

Before final grading, run the validation script to verify no tampering occurred:

```bash
# Generate expected checksum from your template
cd ai-feedback-system
./scripts/validate_repos.sh --generate

# Before grading, validate all student repos
export GITHUB_CLASSROOM_ORG="your-org-name"
./scripts/validate_repos.sh
```

This creates a report showing which repos (if any) have modified `.github` folders.

**For more details:** See `TAMPER_RESISTANCE.md` for the full analysis and alternative approaches.

---

## System Architecture

### How It Works

```
Student pushes + creates tag
    ↓
GitHub Actions workflow triggered
    ↓
Parse student report (index.qmd)
    ↓
For each rubric criterion:
  - Extract relevant sections
  - Send to GitHub Models API
  - Get detailed feedback
    ↓
Combine all feedback
    ↓
Post as GitHub Issue
```

### File Structure

```
your-assignment-repo/
  .github/
    feedback/
      config.yml          ← Assignment settings
      rubric.yml          ← YOUR CUSTOM RUBRIC
      guidance.md         ← YOUR CUSTOM GUIDANCE
      templates/          ← Rubric templates to start from
        lab-rubric-template.yml
        programming-assignment-rubric-template.yml
        guidance-template.md
    workflows/
      feedback.yml        ← GitHub Actions workflow (rarely edit)

 /
    parse_report.py               ← Parses student report
    section_extractor.py          ← Extracts relevant sections per criterion
    ai_feedback_criterion.py      ← Main AI analysis script
    create_issue.py               ← Posts feedback to GitHub

  index.qmd             ← Student's report (or specify in config.yml)
  README.md             ← Assignment instructions
```

---

## Customization Guide

### Step 1: Choose a Rubric Template

Start with the appropriate template from `.github/feedback/templates/`:

- **`lab-rubric-template.yml`**: For lab assignments (methodology → execution → analysis)
- **`programming-assignment-rubric-template.yml`**: For coding assignments (correctness → code quality → testing)
- **`project-rubric-template.yml`**: For larger projects (planning → implementation → documentation)

Copy to `.github/feedback/rubric.yml` and customize.

### Step 2: Customize Rubric Criteria

For each criterion, update:

1. **`id`**: Unique identifier (lowercase, underscores)
2. **`name`**: Display name (shown to students)
3. **`weight`**: Percentage of total grade
4. **`description`**: What you're looking for
5. **`levels`**: Performance levels (exemplary → unsatisfactory)
6. **`keywords`**: Terms the AI should look for in student report
7. **`common_issues`**: Mistakes you see often (helps AI spot them)
8. **`artifacts`** (optional): File patterns to check (e.g., `"data/*.csv"`)

**Example - Customizing for a Programming Assignment**:

```yaml
- id: code_quality
  name: "Code Quality & Style"
  weight: 20
  description: "Code is readable, follows PEP8, uses appropriate data structures"

  levels:
    exemplary:
      description: "Clean, idiomatic Python code"
      point_range: [18, 20]
    satisfactory:
      description: "Readable with minor style issues"
      point_range: [14, 17]
    developing:
      description: "Works but hard to read"
      point_range: [10, 13]
    unsatisfactory:
      description: "Poor code quality"
      point_range: [0, 9]

  keywords: [PEP8, function, variable names, docstring, readability]

  common_issues:
    - "Inconsistent naming (camelCase mixed with snake_case)"
    - "Functions doing too many things"
    - "Magic numbers instead of named constants"
    - "Poor variable names like 'x', 'temp', 'data'"
```

### Step 3: Customize Guidance

The `guidance.md` file tells the AI:
- Course context and learning objectives
- What excellent work looks like
- Common student mistakes
- Feedback tone and style

**Key sections to customize**:

1. **Course Context**: What are students learning?
2. **Criterion-Specific Guidance**: For each criterion, what should AI look for?
3. **Common Mistakes**: What do students typically struggle with?
4. **Examples**: Show what good work looks like

**Pro tip**: Include actual examples from past student work (anonymized)!

### Step 4: Adjust Config Settings

Edit `.github/feedback/config.yml`:

```yaml
assignment:
  name: "Lab 1: Circuit Analysis"  # Shown in feedback
  course: "EENG 320"
  type: "lab"  # or "project", "assignment"

report:
  filename: "index.qmd"  # Where is student's report?
  format: "quarto"       # or "markdown", "jupyter"

model:
  primary: "gpt-4o"
  max_concurrent_requests: 2  # Based on your rate limits

issue:
  enabled: true
  label: "ai-feedback"
  title: "AI Feedback: {assignment_name}"
```

---

## Examples for Different Course Types

### Example 1: EENG 320 (Electronics Lab)

**Rubric focus**: Design → Simulation → Experimentation → Analysis

**Keywords**: circuit, schematic, LTspice, oscilloscope, datasheet, impedance, frequency response

**Common issues**:
- Missing component justifications
- No comparison between theory/sim/measured
- Poor error analysis

**Artifacts to check**: `schematics/*.png`, `data/*.csv`, `*.asc`

### Example 2: PHYS/ENGR 280 (Scientific Computing)

**Rubric focus**: Algorithm correctness → Code quality → Performance → Analysis

**Keywords**: NumPy, vectorization, algorithm, complexity, visualization, matplotlib

**Common issues**:
- Nested loops instead of vectorization
- No timing or performance discussion
- Missing docstrings
- Plots without labels/units

**Artifacts to check**: `*.py`, `*.ipynb`, `data/*.csv`

### Example 3: PHYS/MENG 230 (Laboratory Instrumentation)

**Rubric focus**: Experimental design → Calibration → Data acquisition → Uncertainty analysis

**Keywords**: calibration, uncertainty, standard deviation, precision, accuracy, instrument

**Common issues**:
- No calibration procedure
- Missing uncertainty estimates
- No error bars on plots
- Poor description of measurement technique

**Artifacts to check**: `calibration/*.csv`, `data/*.txt`, `images/*.png`

### Example 4: EENG 340 (Interfacing Laboratory)

**Rubric focus**: Hardware design → Firmware → Testing → Documentation

**Keywords**: microcontroller, GPIO, interrupt, timer, communication protocol, sensor

**Common issues**:
- Missing hardware-software interface description
- No timing diagrams
- Insufficient testing of edge cases
- Poor code documentation

**Artifacts to check**: `firmware/**/*.{c,h}`, `schematics/*.png`, `data/*.csv`

---

## Advanced Customization

### Adding New Criteria

1. Add to `rubric.yml`:
```yaml
- id: new_criterion
  name: "Your New Criterion"
  weight: 15
  description: "What you're evaluating"
  levels: {...}
  keywords: [...]
  common_issues: [...]
```

2. Add guidance in `guidance.md`:
```markdown
### Your New Criterion

**What to look for**:
- [specific thing 1]
- [specific thing 2]

**Common mistakes**:
- [mistake 1]
- [mistake 2]
```

### Assignment-Specific vs. Course-Wide Rubrics

**Option 1: Assignment-specific** (recommended)
- Each assignment has its own `.github/feedback/` directory
- Completely customized rubric per assignment
- Best for varied assignment types

**Option 2: Course-wide with variations**
- Keep base rubric in a template repo
- Copy and tweak weights/descriptions per assignment
- Good if assignments are similar structure

### Multi-Part Assignments

For assignments with multiple phases:

```yaml
criteria:
  # Phase 1 criteria
  - id: proposal
    name: "Project Proposal"
    weight: 20
    # ...

  # Phase 2 criteria
  - id: implementation
    name: "Implementation"
    weight: 40
    # ...

  # Phase 3 criteria
  - id: final_report
    name: "Final Documentation"
    weight: 40
    # ...
```

Students can request feedback at each phase with different tags:
```bash
git tag phase-1-feedback
git tag phase-2-feedback
git tag final-feedback
```

---

## Testing and Validation

### Test Locally Before Deploying

```bash
# 1. Get a GitHub token (Settings → Developer settings → Personal access tokens)
export GITHUB_TOKEN="your_token"

# 2. Copy a sample student report to your repo as index.qmd

# 3. Test parsing
uv run python .github/scripts/parse_report.py
# Should create parsed_report.json

# 4. Test AI feedback generation
uv run python .github/scripts/ai_feedback_criterion.py
# Should create feedback.md

# 5. Review the feedback
cat feedback.md
```

### Common Testing Issues

**"ERROR: Failed to load rubric"**
- Check that `.github/feedback/rubric.yml` exists
- Validate YAML syntax: `yamllint .github/feedback/rubric.yml`

**"ERROR: GITHUB_TOKEN not found"**
- Set token: `export GITHUB_TOKEN="your_token"`
- Or create `.env` file: `GITHUB_TOKEN=your_token`

**"Token limit exceeded"**
- Your criterion extracted too much content
- Simplify criterion keywords or adjust section_extractor.py

**Feedback is too generic**
- Add more `common_issues` to rubric
- Make guidance more specific
- Add examples to guidance.md

---

## Rate Limits and Costs

### GitHub Models Free Tier (Education)

**Per repository**:
- 5,000 requests/hour
- 50,000 requests/day
- Input: Up to 15,000 tokens/request (varies by account)
- Output: Up to 4,000 tokens/request

**This system's usage**:
- ~10 API requests per student report (one per criterion)
- ~600-3000 tokens per request
- Can handle 500 students/day easily

**Cost**: $0 (completely free for education accounts)

### Staying Within Limits

The system is designed to stay well within limits:
- **Criterion-based analysis**: Only sends relevant content per criterion
- **Concurrency limit**: Max 2 concurrent requests (configurable)
- **Smart extraction**: section_extractor.py minimizes token usage

If you hit limits:
- Reduce `max_concurrent_requests` in config.yml
- Limit feedback requests (e.g., max 2 per student per assignment)
- Ask students to request feedback during off-hours

---

## Troubleshooting

### Students Can't Trigger Feedback

**Check workflow**:
- `.github/workflows/feedback.yml` exists?
- Workflow file has correct permissions?
- Tag pattern matches (default: `feedback-*` or `review-*`)?

**GitHub Actions logs**:
- Go to repo → Actions tab
- Click on the failed workflow run
- Check logs for errors

### Feedback Quality Issues

**Too generic**:
- Add more detail to `guidance.md`
- Include specific examples of good work
- Add more `common_issues` to rubric

**Missing content**:
- Check if `keywords` match what students actually write
- Review `section_extractor.py` logic for that criterion
- Look at `parsed_report.json` to see what was extracted

**Wrong tone**:
- Adjust guidance.md feedback philosophy section
- Add examples of desired feedback tone

### Technical Issues

**Workflow doesn't run**:
- Check `.github/workflows/feedback.yml` syntax
- Verify `GITHUB_TOKEN` is available in Actions (should be automatic)

**Scripts fail**:
- Check Python dependencies: `uv sync`
- Verify file paths match (report filename in config.yml)
- Check parsed_report.json exists and is valid

---

## FAQ

**Q: Can I use this for group projects?**
A: Yes! Just have one student from each group push and tag for feedback.

**Q: What if my assignment doesn't use Quarto?**
A: Update `report.filename` in config.yml. Supports `.qmd`, `.md`, `.ipynb`, `.tex`.

**Q: Can students request feedback multiple times?**
A: Yes! They can create multiple tags: `feedback-v1`, `feedback-v2`, etc.

**Q: How do I disable feedback for an assignment?**
A: Remove `.github/workflows/feedback.yml` or set `issue.enabled: false` in config.yml.

**Q: Can I grade based on AI feedback?**
A: The AI provides *suggestions*, not final grades. Always review before grading.

**Q: What if AI makes a mistake?**
A: The feedback is a starting point. You have final say on grades.

**Q: Can I customize the AI model?**
A: Yes! Set `model.primary` in config.yml. Options: `gpt-4o`, `gpt-4o-mini`, others.

**Q: Does this work for non-English courses?**
A: Yes, but you'll need to write guidance.md in your target language.

---

## Next Steps

1. **Try it**: Copy to a test assignment, customize rubric, test with a sample report
2. **Iterate**: Refine rubric and guidance based on feedback quality
3. **Deploy**: Add to your GitHub Classroom template for next semester
4. **Share**: Adapt for colleagues teaching different courses

---

## Support and Resources

**Template files**:
- Lab rubric: `.github/feedback/templates/lab-rubric-template.yml`
- Programming rubric: `.github/feedback/templates/programming-assignment-rubric-template.yml`
- Guidance: `.github/feedback/templates/guidance-template.md`

**Documentation**:
- `README.md`: Student-facing guide
- `DEPLOYMENT.md`: Technical deployment details
- `CLAUDE.md`: Development session notes

**GitHub Models docs**:
- https://docs.github.com/en/github-models

---

**Ready to start?** Copy the template files and customize your first rubric!
