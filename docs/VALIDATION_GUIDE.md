# AI Feedback Configuration Validation Guide

## Overview

The AI feedback system now includes a comprehensive validation tool that catches configuration issues **before** running the expensive workflow. This prevents wasted API calls and provides clear diagnostics.

## Issues Solved

### 1. Configuration Mismatches (No Student Repo Edits Needed)
The system now automatically accepts both criterion **names** and **IDs** in the vision config:

```yaml
# Both of these now work:
vision:
  enabled_for_criteria:
    - "results_validation"      # ✓ By ID
    - "Results & Validation"    # ✓ By name (NEW!)
```

### 2. Early Validation (Fail Fast)
The validation runs early in the workflow to catch issues like:
- ✓ Vision enabled for non-existent criteria
- ✓ Missing required files
- ✓ Invalid rubric structure
- ✓ Report parsing failures
- ✓ Figure detection issues

## How to Use

### Local Testing (Recommended Before Triggering Workflow)

Run this in any student repo or assignment repo that uses the feedback system:

```bash
# From the repo root directory
python .github/scripts/validate_feedback_setup.py
```

This will:
1. Check all required files exist
2. Convert RUBRIC.md to rubric.yml (if needed)
3. Validate config.yml syntax
4. Validate rubric structure
5. Check vision config matches criteria
6. Test report parsing and figure detection

Example output:
```
✓ Configuration file
✓ Rubric (markdown)
✓ Guidance file
✓ config.yml is valid
✓ rubric.yml is valid (3 criteria)
   - Methodology & Approach (id: methodology_approach)
   - Results & Validation (id: results_validation)
   - Scientific Communication (id: scientific_communication)
✓ Vision configuration is valid
✓ Report parsed successfully
   Words: 730 | Figures: 7 | Sections: 7

✓ All checks passed! Your feedback setup is ready.
```

### Automatic Workflow Validation

The validation now runs automatically at the start of the feedback workflow:
1. Validates setup before any API calls
2. Fails fast with clear error messages
3. Saves API quota and runtime

## What Gets Validated

### File Checks
- `.github/config.yml` - Required configuration
- `.github/feedback/RUBRIC.md` - Rubric in markdown format
- `.github/feedback/rubric.yml` - Generated from markdown (created if missing)
- `.github/feedback/guidance.md` - AI instruction guidance
- Report file (`.qmd` or `.md`)

### Configuration Checks
- All required config fields present (report_file, model, etc.)
- Vision config criterion references are valid (by ID or name)
- Vision config doesn't reference non-existent criteria

### Rubric Checks
- Rubric has at least one criterion
- Each criterion has required fields: name, id, description
- IDs are properly generated from names (via rubric converter)

### Report Checks
- Report file exists and can be parsed
- Figures are detected correctly
- Statistics extracted (word count, section count, etc.)

## Troubleshooting

### "Vision enabled for 'results_validation' but no matching criterion found"

**Problem:** The vision config references a criterion that doesn't exist in the rubric.

**Solution:** Check that the criterion name/ID in vision config exactly matches the rubric. Use the printed list of valid IDs and names:
```yaml
Valid IDs: methodology_approach, results_validation, scientific_communication
Valid names: Methodology & Approach, Results & Validation, Scientific Communication
```

### "Report file not found (looking for *.qmd or *.md)"

**Problem:** No report file detected.

**Solution:** Make sure you have a report file (`index.qmd`, `report.qmd`, etc.) at the repo root.

### "Failed to parse report"

**Problem:** Report parsing encountered an error.

**Solution:** Check that:
- The report file is valid Quarto/Markdown
- All embedded files (notebooks, data files) exist
- No special characters causing parsing issues

### "Vision is disabled (this is fine)"

**Info:** Vision is explicitly disabled in the config. This is OK if you don't need image analysis.

**To enable:** Set `vision.enabled: true` in `.github/config.yml`

## Key Improvements Made

### Backward Compatibility
- Students/instructors can use either criterion **name** OR **ID** in config
- Rubric converter automatically generates proper IDs
- Existing configs continue to work

### Fail-Fast Design
- Validation runs before expensive API calls
- Clear error messages identify exact issues
- Saves API quota and runtime

### Easy Testing
- Single command to validate entire setup locally
- Integrated into workflow for automatic checking
- No special setup needed

## For New Assignments

When setting up a new assignment with the feedback system:

1. Create `.github/config.yml` and `.github/feedback/RUBRIC.md`
2. Run: `python .github/scripts/validate_feedback_setup.py`
3. Fix any issues reported
4. Trigger workflow when validation passes
5. No need to edit the validation tool for future runs

## Example Validation Output

### Success Case
```
AI Feedback System Configuration Validator

1. Required Files
   ✓ Configuration file
   ✓ Rubric (markdown)
   ✓ Guidance file

2. Rubric Conversion
   ✓ Converted RUBRIC.md → rubric.yml

3. Configuration Validation
   ✓ config.yml is valid

4. Rubric Validation
   ✓ rubric.yml is valid (3 criteria)
      - Methodology & Approach (id: methodology_approach)
      - Results & Validation (id: results_validation)
      - Scientific Communication (id: scientific_communication)

5. Vision Configuration
   ✓ Vision configuration is valid

6. Report Validation
   ✓ Report parsed successfully
      Words: 730 | Figures: 7 | Sections: 7

Summary
✓ All checks passed! Your feedback setup is ready.
```

### Error Case
```
5. Vision Configuration
   ✗ Vision enabled for 'invalid_criterion' but no matching criterion found.
      Valid IDs: methodology_approach, results_validation, scientific_communication
      Valid names: Methodology & Approach, Results & Validation, Scientific Communication

Summary
✗ Some checks failed. Please fix the issues above before running the workflow.
```
