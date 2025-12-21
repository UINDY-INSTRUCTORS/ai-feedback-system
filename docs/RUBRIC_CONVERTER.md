# Rubric Converter Guide

**Bidirectional converter between YAML rubrics (for the AI system) and Markdown rubrics (for humans)**

## Why This Tool?

**The Problem:**
- YAML rubrics are machine-readable but challenging for faculty to write
- YAML syntax is error-prone (indentation, colons, quotes)
- Students can't easily read/understand YAML files

**The Solution:**
- **Faculty**: Write rubrics in Markdown (easy, familiar format)
- **Students**: Read beautiful rendered Markdown on GitHub
- **System**: Uses YAML (converted from Markdown before deployment)

---

## Quick Start

### For Faculty: Write a New Rubric

1. **Start with Markdown** (it's easier!):

```bash
# Copy a template or example
cp examples/phys-230-lab-example-RUBRIC.md .github/feedback/RUBRIC.md

# Edit in any text editor or GitHub web interface
# The markdown format is intuitive - just edit the tables and lists
```

2. **Convert to YAML** when ready to deploy:

```bash
# Using Docker (recommended)
docker run --rm -v $PWD:/work -w /work ghcr.io/202420-phys-230/quarto:1 \
  python3 .github/scripts/rubric_converter.py md-to-yaml \
  .github/feedback/RUBRIC.md \
  .github/feedback/rubric.yml

# Or locally (if you have pyyaml installed)
python3 .github/scripts/rubric_converter.py md-to-yaml \
  .github/feedback/RUBRIC.md \
  .github/feedback/rubric.yml
```

3. **Deploy** the YAML file:

```bash
git add .github/feedback/rubric.yml
git commit -m "Update rubric from markdown"
git push
```

### For Students: Read the Rubric

Just open `RUBRIC.md` on GitHub - it renders beautifully with:
- Clear headings for each criterion
- Tables showing point ranges
- Bullet lists of what makes work excellent, good, or poor
- Keywords the AI will look for
- Common mistakes to avoid

---

## Markdown Format

### Header Section

```markdown
# PHYS/MENG 230 - Lab Report Rubric

**Course**: PHYS/MENG 230
**Assignment**: Lab Report
**Type**: lab
**Total Points**: 100
```

### Each Criterion

```markdown
## Criterion 1: Abstract & Description (10%)

Brief description of what this criterion evaluates.

### Performance Levels

| Level | Points | Description |
|-------|--------|-------------|
| **Excellent** | 7-10 | What makes it excellent |
| **Good** | 4-6 | What makes it good |
| **Poor** | 0-3 | What makes it poor |

### Excellent Indicators
- Specific thing to look for
- Another excellent quality
- Yet another indicator

### Good Indicators
- Acceptable but not perfect
- Meets basic requirements

### Poor Indicators
- Missing key elements
- Incorrect or unclear

### Keywords
keyword1, keyword2, keyword3

### Common Issues
- Common mistake students make
- Another frequent problem
```

---

## Usage Examples

### Convert YAML to Markdown (for reading/editing)

```bash
# Generate student-readable version
docker run --rm -v $PWD:/work -w /work ghcr.io/202420-phys-230/quarto:1 \
  python3 .github/scripts/rubric_converter.py yaml-to-md \
  .github/feedback/rubric.yml \
  .github/feedback/RUBRIC.md

# Share RUBRIC.md with students (renders beautifully on GitHub)
```

### Convert Markdown to YAML (for deployment)

```bash
# After editing RUBRIC.md, generate the YAML for the system
docker run --rm -v $PWD:/work -w /work ghcr.io/202420-phys-230/quarto:1 \
  python3 .github/scripts/rubric_converter.py md-to-yaml \
  .github/feedback/RUBRIC.md \
  .github/feedback/rubric.yml
```

### Validate Round-Trip Conversion

```bash
# Ensure YAML → MD → YAML preserves all data
docker run --rm -v $PWD:/work -w /work ghcr.io/202420-phys-230/quarto:1 \
  python3 .github/scripts/rubric_converter.py validate \
  .github/feedback/rubric.yml
```

---

## Workflow Recommendations

### Option 1: Markdown as Source of Truth (Recommended for Most)

**Best for**: Faculty who prefer writing in Markdown

1. Write/edit rubric in `RUBRIC.md`
2. Convert to `rubric.yml` before deployment
3. Commit both files
4. **Important**: Always edit the Markdown, then regenerate YAML

```bash
# Edit RUBRIC.md in your text editor
vim .github/feedback/RUBRIC.md

# Convert to YAML
docker run --rm -v $PWD:/work -w /work ghcr.io/202420-phys-230/quarto:1 \
  python3 .github/scripts/rubric_converter.py md-to-yaml \
  .github/feedback/RUBRIC.md \
  .github/feedback/rubric.yml

# Commit both
git add .github/feedback/RUBRIC.md .github/feedback/rubric.yml
git commit -m "Update rubric"
git push
```

### Option 2: YAML as Source of Truth

**Best for**: Faculty comfortable with YAML, advanced users

1. Write/edit rubric in `rubric.yml`
2. Generate `RUBRIC.md` for students to read
3. Commit both files
4. **Important**: Always edit the YAML, then regenerate Markdown

```bash
# Edit rubric.yml
vim .github/feedback/rubric.yml

# Generate student-readable version
docker run --rm -v $PWD:/work -w /work ghcr.io/202420-phys-230/quarto:1 \
  python3 .github/scripts/rubric_converter.py yaml-to-md \
  .github/feedback/rubric.yml \
  .github/feedback/RUBRIC.md

# Commit both
git add .github/feedback/rubric.yml .github/feedback/RUBRIC.md
git commit -m "Update rubric"
git push
```

### Option 3: Markdown-Only Workflow

**Best for**: Maximum simplicity

1. Only commit `RUBRIC.md` to version control
2. Generate `rubric.yml` on-the-fly during deployment
3. Add `rubric.yml` to `.gitignore`

```bash
# Add to .gitignore
echo ".github/feedback/rubric.yml" >> .gitignore

# In your deployment script or GitHub Actions workflow
docker run --rm -v $PWD:/work -w /work ghcr.io/202420-phys-230/quarto:1 \
  python3 .github/scripts/rubric_converter.py md-to-yaml \
  .github/feedback/RUBRIC.md \
  .github/feedback/rubric.yml
```

---

## Tips for Writing Rubrics

### For Faculty

1. **Start from an example**: Copy a similar rubric and modify
2. **Use clear language**: Students will read this
3. **Be specific in indicators**: Vague indicators = vague feedback
4. **Include common issues**: Helps the AI give targeted feedback
5. **Keywords matter**: The AI uses these to find relevant sections

### Markdown Best Practices

1. **Keep descriptions short**: Long paragraphs don't render well in tables
2. **Use bullet points**: More readable than long paragraphs
3. **Test the rendering**: View the markdown on GitHub to see how it looks
4. **Consistent formatting**: Follow the examples for best results

### Point Ranges

```markdown
| **Excellent** | 7-10 | ... |  # 10% criterion = 0-10 points
| **Good** | 4-6 | ... |
| **Poor** | 0-3 | ... |
```

Points should:
- Cover the full range (0 to criterion weight)
- Not overlap
- Add up to the criterion weight

---

## Common Questions

### Can I add custom performance levels?

Yes! The converter supports any level names:

```markdown
| **Outstanding** | 9-10 | ... |
| **Excellent** | 7-8 | ... |
| **Satisfactory** | 5-6 | ... |
| **Needs Improvement** | 3-4 | ... |
| **Unsatisfactory** | 0-2 | ... |
```

### What if I forget a section?

The converter is forgiving:
- Missing indicators? No problem (criterion still works)
- Missing keywords? AI will use criterion description
- Missing common issues? AI uses general knowledge

Only required fields:
- Criterion name and weight
- At least one performance level with points

### Can I edit the YAML directly?

Yes, but:
- ✅ Fine if you're comfortable with YAML syntax
- ⚠️ Indentation must be exact (use spaces, not tabs)
- ⚠️ Colons and quotes can be tricky
- 💡 Regenerate the Markdown for students after editing

### How do I share the rubric with students?

**Option 1**: Include in assignment README
```markdown
See [RUBRIC.md](.github/feedback/RUBRIC.md) for grading criteria.
```

**Option 2**: Add to assignment description in GitHub Classroom

**Option 3**: Post the rendered HTML version

The markdown renders beautifully on GitHub - students can just click and read!

---

## Examples

See the `examples/` directory for complete rubrics:
- `phys-230-lab-example-RUBRIC.md` - Lab instrumentation (5 criteria)
- `phys-280-assignment-example-RUBRIC.md` - Computational assignment (5 criteria)
- `eeng-320-lab-example-RUBRIC.md` - Electronics lab (6 criteria)
- `eeng-340-project-example-RUBRIC.md` - Embedded systems project (9 criteria)

---

## Troubleshooting

### Validation fails after round-trip

**Cause**: Usually formatting issues in the Markdown

**Fix**: Check that:
- Tables have exactly 3 columns
- Point ranges are formatted as `min-max` (e.g., `7-10`)
- No extra spacing in headers
- Level names are consistent (e.g., always "Excellent" not "excellent")

### Conversion produces empty YAML

**Cause**: Markdown doesn't match expected format

**Fix**:
- Start from a working example
- Check that criterion headers match: `## Criterion N: Name (X%)`
- Ensure performance levels table is present

### Keywords not converting properly

**Cause**: Markdown format issue

**Fix**: Keywords should be comma-separated on one line:
```markdown
### Keywords
keyword1, keyword2, keyword3
```

Not:
```markdown
### Keywords
- keyword1
- keyword2
```

---

## Advanced Usage

### Batch Convert Multiple Rubrics

```bash
#!/bin/bash
# convert_all.sh

for yaml in *.yml; do
  md="${yaml%.yml}-RUBRIC.md"
  echo "Converting $yaml → $md"
  docker run --rm -v $PWD:/work -w /work ghcr.io/202420-phys-230/quarto:1 \
    python3 .github/scripts/rubric_converter.py yaml-to-md "$yaml" "$md"
done
```

### Pre-commit Hook

Automatically regenerate YAML when Markdown changes:

```bash
#!/bin/bash
# .git/hooks/pre-commit

if git diff --cached --name-only | grep -q "RUBRIC.md"; then
  docker run --rm -v $PWD:/work -w /work ghcr.io/202420-phys-230/quarto:1 \
    python3 .github/scripts/rubric_converter.py md-to-yaml \
    .github/feedback/RUBRIC.md \
    .github/feedback/rubric.yml

  git add .github/feedback/rubric.yml
fi
```

### Integration with CI/CD

GitHub Actions workflow to validate rubrics:

```yaml
name: Validate Rubric
on: [push]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate rubric round-trip
        run: |
          docker run --rm -v $PWD:/work -w /work \
            ghcr.io/202420-phys-230/quarto:1 \
            python3 .github/scripts/rubric_converter.py validate \
            .github/feedback/rubric.yml
```

---

## Support

**Issues?**
- Check the examples in `examples/`
- Validate your rubric: `rubric_converter.py validate rubric.yml`
- Start from a working example and modify incrementally

**Contributing:**
- Improvements to the converter welcome!
- Share your rubrics as examples
- Report bugs or formatting issues

---

## Summary

✅ **Faculty**: Write in Markdown (easy, familiar)
✅ **Students**: Read beautiful Markdown on GitHub
✅ **System**: Uses YAML (auto-converted)
✅ **Everyone wins**: Better rubrics, less work

**Next Steps:**
1. Copy an example rubric to `RUBRIC.md`
2. Edit it for your assignment
3. Convert to `rubric.yml`
4. Deploy and test!
