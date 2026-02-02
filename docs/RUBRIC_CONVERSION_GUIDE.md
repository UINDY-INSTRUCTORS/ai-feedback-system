# Rubric Conversion Guide

The feedback system uses a **two-format rubric approach**:

1. **RUBRIC.md** (Human-readable, for students and instructors)
   - Markdown format with tabular performance levels
   - Easy to edit and understand
   - Shows percentage ranges: 65-100%, 35-65%, 0-35%

2. **rubric.yml** (Machine-readable, for the AI feedback system)
   - Auto-generated YAML during workflow
   - Extracted from RUBRIC.md by `rubric_converter.py`
   - Provides structured data with level names extracted from markdown

## Tabular Format (for RUBRIC.md)

The markdown rubric should use this performance levels table format:

```markdown
### Performance Levels

| Level | Range | Description |
|-------|-------|-------------|
| **Excellent** | 65-100% | Clear explanation with examples... |
| **Good** | 35-65% | Reasonable approach with examples... |
| **Developing** | 0-35% | Missing key elements... |
```

**Key requirements:**
- Column headers: `Level | Range | Description` (exactly these names)
- Level names in bold: `**Excellent**`, `**Good**`, `**Developing**`, etc.
- Percentage ranges: `65-100%`, `35-65%`, `0-35%`
- Descriptions can span multiple lines (markdown table handling)

## How Conversion Works

### Markdown → YAML (During Workflow)

```bash
python rubric_converter.py md-to-yaml RUBRIC.md rubric.yml
```

**What happens:**
1. Parses RUBRIC.md markdown table
2. Extracts level names: "Excellent", "Good", "Developing"
3. Extracts percentage ranges: [65, 100], [35, 65], [0, 35]
4. Creates rubric.yml with structured criterion data
5. **Level names are now available to the AI feedback system**

### YAML → Markdown (For regeneration)

```bash
python rubric_converter.py yaml-to-md rubric.yml RUBRIC.md
```

This reverses the process. Useful if you want to maintain rubric.yml as source and regenerate markdown.

## Testing Locally

### Test conversion on your assignment:

```bash
cd /path/to/your/assignment
python .github/scripts/rubric_converter.py md-to-yaml .github/feedback/RUBRIC.md .github/feedback/rubric.yml
```

### Verify the generated rubric.yml:

```bash
cat .github/feedback/rubric.yml
```

Look for:
- Criterion names and weights
- Level keys: `excellent`, `good`, `developing`
- Point ranges: `[65, 100]`, `[35, 65]`, `[0, 35]`

### Validate round-trip conversion:

```bash
python .github/scripts/rubric_converter.py validate .github/feedback/rubric.yml
```

This ensures:
- RUBRIC.md → rubric.yml → RUBRIC.md preserves all data
- No information loss in conversion

## Why This Matters for AI Feedback

The **rubric_converter.py extracts level names dynamically** from RUBRIC.md, so:

✅ **Before**: AI had hardcoded level names ("Exemplary", "Satisfactory")
❌ If rubric.yml couldn't be generated, hardcoded names were used

✅ **Now**: Level names come directly from your RUBRIC.md
✅ If RUBRIC.md changes, level names automatically update
✅ Different rubrics can use different level names (3 levels, 4 levels, custom names)
✅ No more hardcoded terminology mismatches

## Example: Test Assignment

The test-assignment-sspickle now uses:

```markdown
| **Excellent** | 65-100% | [description] |
| **Good** | 35-65% | [description] |
| **Developing** | 0-35% | [description] |
```

When the workflow runs:
1. `rubric_converter.py md-to-yaml` parses this table
2. Extracts level names: "Excellent", "Good", "Developing"
3. Writes to rubric.yml with these level names
4. AI feedback system reads rubric.yml and uses correct terminology

## Troubleshooting

### Level names not being extracted?

**Check RUBRIC.md format:**
- Table header: `| Level | Range | Description |`
- Level names in bold: `**Excellent**`
- Percentage ranges: `65-100%`
- All rows separated by `|`

**Test conversion:**
```bash
python rubric_converter.py md-to-yaml RUBRIC.md test.yml
cat test.yml  # Check for 'excellent', 'good', 'developing' keys
```

### Validation fails?

Run the validate command to see what's mismatched:
```bash
python rubric_converter.py validate rubric.yml
```

This shows whether the markdown → YAML → markdown round-trip preserves data.

## Adding Criteria

When adding a new criterion to RUBRIC.md:

1. Use the header format: `### Criterion N: Name (X%)`
2. Include performance levels table with `| Level | Range | Description |`
3. List all criteria in order
4. Run conversion: `python rubric_converter.py md-to-yaml RUBRIC.md rubric.yml`
5. Verify: `cat rubric.yml` shows your new criterion with correct level names

## Customizing Level Names

You can use any level names you want:

```markdown
| Level | Range | Description |
|-------|-------|-------------|
| **Exceeds Expectations** | 65-100% | ... |
| **Meets Expectations** | 35-65% | ... |
| **Does Not Yet Meet** | 0-35% | ... |
```

The converter extracts whatever names you use, so the AI will use "Exceeds Expectations", "Meets Expectations", "Does Not Yet Meet" in feedback.

---

**Last Updated**: February 2, 2026
**Tool**: `rubric_converter.py`
**Format**: Markdown ↔ YAML bidirectional conversion
