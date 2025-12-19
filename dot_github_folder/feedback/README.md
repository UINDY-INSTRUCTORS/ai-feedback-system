# Setting Up AI Feedback for Your Assignment

This directory contains the configuration for AI-powered feedback on student reports.

## Quick Setup (3 Steps)

### 1. Choose Your Starting Point

Pick the appropriate rubric for your assignment type:

**From Examples** (course-specific):
```bash
# For electronics lab
cp examples/eeng-320-lab-example.yml rubric.yml

# For scientific computing assignment
cp examples/phys-280-assignment-example.yml rubric.yml

# For instrumentation lab
cp examples/phys-230-lab-example.yml rubric.yml

# For interfacing/embedded project
cp examples/eeng-340-project-example.yml rubric.yml
```

**From Templates** (generic):
```bash
# For any lab assignment
cp templates/lab-rubric-template.yml rubric.yml

# For programming assignment
cp templates/programming-assignment-rubric-template.yml rubric.yml

# For guidance
cp templates/guidance-template.md guidance.md
```

### 2. Create Config File

```bash
cp config-template.yml config.yml
```

Edit `config.yml`:
```yaml
assignment:
  name: "Lab 1: Your Assignment Name"
  course: "YOUR 123"
  type: "lab"  # or "project", "assignment"

report:
  filename: "index.qmd"  # or "report.md", "notebook.ipynb"
```

### 3. Customize for Your Assignment

**Edit `rubric.yml`**:
- Update assignment name and course
- Adjust criterion weights (must total 100)
- Update keywords to match your domain
- Add assignment-specific `common_issues`

**Create `guidance.md`**:
- Copy from `templates/guidance-template.md`
- Fill in course context
- Add assignment-specific expectations
- Include examples of good work

## File Structure

After setup, you should have:

```
.github/feedback/
  config.yml          ← Your assignment config
  rubric.yml          ← Your custom rubric
  guidance.md         ← Your AI instructions

  templates/          ← Reference (don't edit)
  examples/           ← Reference (don't edit)
  config-template.yml ← Reference
```

## What Each File Does

### `config.yml` (Required)
Basic assignment settings: name, course, report filename, AI model

### `rubric.yml` (Required)
The grading rubric with criteria, weights, performance levels, and keywords

### `guidance.md` (Required)
Instructions for the AI on:
- Course context and learning objectives
- What good work looks like
- Common student mistakes
- Feedback tone and style

## Testing Your Setup

```bash
# From repo root
uv run python scripts/parse_report.py     # Test report parsing
uv run python scripts/ai_feedback_criterion.py  # Test AI feedback (requires GITHUB_TOKEN)
```

## Examples

### Electronics Lab (EENG-320)
Focus: Circuit design → Simulation → Experimentation
```bash
cp examples/eeng-320-lab-example.yml rubric.yml
# Edit: Update assignment name, adjust weights
```

### Scientific Computing (PHYS-280)
Focus: Algorithm correctness → Code quality → Analysis
```bash
cp examples/phys-280-assignment-example.yml rubric.yml
# Edit: Update for your specific algorithm/method
```

### Instrumentation Lab (PHYS-230)
Focus: Experimental design → Calibration → Uncertainty analysis
```bash
cp examples/phys-230-lab-example.yml rubric.yml
# Edit: Update for your specific instrument
```

### Interfacing Project (EENG-340)
Focus: System design → Hardware → Firmware → Testing
```bash
cp examples/eeng-340-project-example.yml rubric.yml
# Edit: Update for your specific interface
```

## Need Help?

See parent directory documentation:
- `../INSTRUCTOR_GUIDE.md` - Complete setup and customization guide
- `../TEMPLATE_SYSTEM.md` - Template system overview
- `../DEPLOYMENT.md` - GitHub Actions deployment details

## Troubleshooting

**"No such file or directory: config.yml"**
→ Copy from `config-template.yml`

**"No such file or directory: rubric.yml"**
→ Copy from `templates/` or `examples/`

**Feedback is too generic**
→ Add more `common_issues` to rubric criteria
→ Make `guidance.md` more specific to your assignment
