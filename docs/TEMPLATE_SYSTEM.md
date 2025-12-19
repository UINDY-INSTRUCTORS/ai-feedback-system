# AI Feedback Template System - Overview

## What's New

The feedback system is now **template-based and assignment-specific**. Each assignment repo contains its own complete feedback configuration - no external dependencies!

### Key Improvements

1. **Self-contained**: Each assignment has everything it needs in `.github/feedback/`
2. **Easy to customize**: Copy a template, adjust for your assignment, done!
3. **Shareable**: Other instructors can use your templates
4. **Multi-course ready**: Same system works for any course

---

## Quick Start for Instructors

### Option 1: Start from Template (Recommended)

```bash
# Navigate to your assignment repo
cd lab-1-amplifiers

# Copy appropriate template
cp .github/feedback/templates/lab-rubric-template.yml .github/feedback/rubric.yml
cp .github/feedback/templates/guidance-template.md .github/feedback/guidance.md

# Customize for your assignment
# - Edit rubric.yml: change criteria, weights, keywords
# - Edit guidance.md: add course context, common mistakes
# - Edit config.yml: set assignment name, course, etc.

# Test it
uv run python scripts/parse_report.py
uv run python scripts/ai_feedback_criterion.py
```

### Option 2: Start from Course Example

```bash
# Copy example for your course type
cp .github/feedback/examples/eeng-320-lab-example.yml .github/feedback/rubric.yml

# Customize for this specific assignment
# - Adjust weights based on what you emphasize
# - Update keywords to match your domain
# - Add assignment-specific common_issues
```

---

## File Structure

### Your Assignment Repo

```
lab-1-amplifiers/              # Your assignment repo
  .github/
    feedback/
      config.yml               # ← Edit: Assignment name, settings
      rubric.yml               # ← Edit: YOUR rubric for this assignment
      guidance.md              # ← Edit: YOUR guidance for this assignment

      templates/               # ← Reference: Templates to start from
        lab-rubric-template.yml
        programming-assignment-rubric-template.yml
        guidance-template.md

      examples/                # ← Reference: Example rubrics by course
        eeng-320-lab-example.yml
        phys-280-assignment-example.yml
        phys-230-lab-example.yml
        eeng-340-project-example.yml

    workflows/
      feedback.yml             # ← Usually don't edit

  scripts/                     # ← Usually don't edit
    parse_report.py
    section_extractor.py
    ai_feedback_criterion.py
    create_issue.py

  index.qmd                    # ← Student's report
```

### What to Edit vs. What to Copy As-Is

**Always edit** (customize per assignment):
- `.github/feedback/config.yml`
- `.github/feedback/rubric.yml`
- `.github/feedback/guidance.md`

**Copy as-is** (standard across all):
- `.github/workflows/feedback.yml`
- `scripts/*.py`


**Use as reference** (don't edit, copy from):
- `.github/feedback/templates/*`
- `.github/feedback/examples/*`

---

## Available Templates

### 1. Lab Rubric Template
**File**: `templates/lab-rubric-template.yml`

**Use for**: Traditional lab assignments with experimental work

**Structure**:
- Problem formulation
- Methodology/approach
- Execution/data collection
- Analysis/interpretation
- Communication

**Example courses**: EENG 320, PHYS 230

### 2. Programming Assignment Rubric Template
**File**: `templates/programming-assignment-rubric-template.yml`

**Use for**: Computational/coding assignments

**Structure**:
- Algorithm correctness
- Code quality & style
- Documentation
- Efficiency/performance
- Analysis & validation

**Example courses**: PHYS 280

### 3. Guidance Template
**File**: `templates/guidance-template.md`

**Use for**: Any assignment type

**Sections to fill in**:
- Course context
- Assignment description
- Feedback philosophy
- Criterion-specific guidance
- Common student mistakes
- Examples of excellent work

---

## Course-Specific Examples

### EENG 320 - Electronics
**Example**: `examples/eeng-320-lab-example.yml`

**Focus**: Circuit design → Simulation → Experimentation → Analysis

**Keywords**: schematic, LTspice, oscilloscope, frequency response, impedance

**Typical artifacts**: `schematics/*.png`, `data/*.csv`, `*.asc`

**Common issues**:
- Missing component justifications
- No theory/sim/measurement comparison
- Poor error analysis

---

### PHYS/ENGR 280 - Scientific Computing
**Example**: `examples/phys-280-assignment-example.yml`

**Focus**: Algorithm → Code quality → Performance → Validation

**Keywords**: NumPy, vectorization, complexity, matplotlib, convergence

**Typical artifacts**: `*.py`, `*.ipynb`, `figures/*.png`

**Common issues**:
- Nested loops instead of vectorization
- No timing/performance discussion
- Missing docstrings
- Plots without units

---

### PHYS/MENG 230 - Laboratory Instrumentation
**Example**: `examples/phys-230-lab-example.yml`

**Focus**: Experimental design → Calibration → Data acquisition → Uncertainty

**Keywords**: calibration, uncertainty, oscilloscope, standard deviation, precision

**Typical artifacts**: `calibration/*.csv`, `data/*.txt`, `images/*.png`

**Common issues**:
- No calibration performed
- Missing uncertainty estimates
- No error bars
- Instrument settings not documented

---

### EENG 340 - Interfacing Laboratory
**Example**: `examples/eeng-340-project-example.yml`

**Focus**: System design → Hardware → Firmware → Testing

**Keywords**: microcontroller, GPIO, interrupt, UART, SPI, firmware, timing

**Typical artifacts**: `firmware/*.c`, `schematics/*.png`, `timing_diagrams/*.png`

**Common issues**:
- No timing diagrams
- Polling instead of interrupts
- Missing error handling
- Hardware-software interface unclear

---

## Customization Workflow

### Step 1: Choose Starting Point

**If first time in this course**:
```bash
cp examples/[your-course]-example.yml rubric.yml
```

**If you've used this before**:
```bash
cp ../previous-lab/.github/feedback/rubric.yml rubric.yml
# Then adjust weights, update common_issues
```

**If completely new assignment type**:
```bash
cp templates/lab-rubric-template.yml rubric.yml
# Build from scratch
```

### Step 2: Customize Rubric

Edit `rubric.yml`:

1. **Update header**:
   ```yaml
   assignment:
     name: "Lab 3: Op-Amp Circuits"  # ← Your assignment
     course: "EENG 320"
     total_points: 120
   ```

2. **Adjust criteria weights**:
   ```yaml
   - id: simulations
     weight: 20  # ← Emphasize this more
   ```

3. **Update keywords** to match what students actually write:
   ```yaml
   keywords: [BJT, transistor, common-emitter, gain, bias]  # ← Assignment-specific
   ```

4. **Add assignment-specific common issues**:
   ```yaml
   common_issues:
     - "Forgot to check transistor is in active region"  # ← Specific to BJT lab
     - "Ignored Early effect in gain calculation"
   ```

### Step 3: Customize Guidance

Edit `guidance.md`:

1. Fill in `[bracketed]` sections
2. Add criterion-specific guidance
3. Include examples of excellent work (from past students)
4. List common mistakes you've observed
5. Adjust tone for student level

### Step 4: Update Config

Edit `config.yml`:

```yaml
assignment:
  name: "Lab 3: Op-Amp Circuits"  # Match rubric
  course: "EENG 320"

report:
  filename: "index.qmd"  # Or whatever your students use
```

### Step 5: Test

```bash
# Test with a sample report
uv run python scripts/ai_feedback_criterion.py

# Review feedback
cat feedback.md

# Iterate on rubric/guidance until satisfied
```

---

## Tips for Effective Rubrics

### 1. Keep Criteria Count Reasonable
- **Optimal**: 5-7 criteria
- **Too few** (<4): Feedback lacks detail
- **Too many** (>10): Takes longer, may hit rate limits

### 2. Make Keywords Specific
❌ Bad: `keywords: [good, analysis, results]`
✅ Good: `keywords: [Bode plot, cutoff frequency, gain margin, phase margin]`

### 3. Include Real Common Issues
Based on actual student mistakes, not hypothetical:
```yaml
common_issues:
  - "Used 5V logic level with 3.3V GPIO (check Lab 2 setup!)"  # ← Real issue
  - "Didn't add pull-up resistor for I2C (see datasheet page 12)"  # ← Specific
```

### 4. Reference Specific Resources
```yaml
- "Missing comparison to LM358 datasheet Figure 1 (gain vs frequency)"
- "Should reference Sedra & Smith Section 5.3 for bias calculation"
```

### 5. Adjust Weights to Match Emphasis
If you spend 3 weeks on uncertainty analysis:
```yaml
- id: uncertainty_analysis
  weight: 30  # ← Higher weight reflects importance
```

---

## Testing Strategy

### Local Testing (Before Deploying)

1. **Get sample student report** from previous semester
2. **Copy to your repo** as `index.qmd`
3. **Run parser**:
   ```bash
   uv run python scripts/parse_report.py
   cat parsed_report.json  # Check sections extracted
   ```
4. **Run AI feedback**:
   ```bash
   uv run python scripts/ai_feedback_criterion.py
   ```
5. **Review feedback**:
   ```bash
   cat feedback.md
   ```
6. **Iterate**: Adjust rubric/guidance based on feedback quality

### GitHub Actions Testing

1. Push to a test assignment repo
2. Create tag: `git tag test-feedback && git push origin test-feedback`
3. Watch Actions tab
4. Review created issue

---

## Sharing with Other Instructors

### To share your rubric:

1. Copy from your assignment repo:
   ```bash
   cp .github/feedback/rubric.yml eeng-320-lab3-rubric.yml
   cp .github/feedback/guidance.md eeng-320-lab3-guidance.md
   ```

2. Share files with notes on:
   - Assignment type and level (freshman, senior, etc.)
   - What worked well
   - What you'd adjust next time
   - Student feedback on AI feedback quality

### To use someone else's rubric:

1. Copy to your repo and customize:
   ```bash
   cp shared-rubric.yml .github/feedback/rubric.yml
   # Edit to match your specific assignment
   ```

2. Adjust:
   - Keywords (different terminology?)
   - Weights (different emphasis?)
   - Common issues (different student population?)

---

## Troubleshooting

### Feedback is too generic

**Fix 1**: Add more `common_issues` to each criterion
**Fix 2**: Make `keywords` more specific
**Fix 3**: Add examples to `guidance.md`

### Feedback misses important aspects

**Fix**: Check `parsed_report.json` to see what sections were extracted
- If section is there: Add relevant keywords to criterion
- If section is missing: Student didn't include it (good to catch!)

### Token limit errors

**Rare** with new system, but if it happens:
- Reduce verbosity in `guidance.md`
- Split a heavy criterion into two lighter ones

### Students confused by feedback

**Fix**: Adjust tone in `guidance.md`:
```markdown
## Tone and Approach
- Use simple language (students are learning!)
- Always be encouraging
- Give concrete, actionable suggestions
```

---

## Next Steps

1. **Pick an upcoming assignment**
2. **Copy appropriate template** to `.github/feedback/rubric.yml`
3. **Customize for your assignment**
4. **Test with a sample report**
5. **Deploy to students!**

**Questions?** See `INSTRUCTOR_GUIDE.md` for comprehensive documentation.

---

## Summary: What Makes This System Powerful

✅ **Per-assignment customization**: Each assignment gets exactly the feedback it needs

✅ **Template-based**: Don't start from scratch, build on proven examples

✅ **Course-agnostic**: Works for circuits, programming, instrumentation, embedded systems

✅ **Criterion-focused**: Analyzes each rubric item separately for detailed feedback

✅ **Instructor-friendly**: Copy, customize, test, deploy

✅ **Student-friendly**: Specific, actionable feedback that helps them improve

✅ **Free**: No cost with GitHub education account

**Ready to transform your feedback process?** Start with `INSTRUCTOR_GUIDE.md`!
