# Configuration Validation Utility

## Overview

The validation utility helps instructors catch configuration errors before deploying the AI feedback system. It validates:

- **config.yml** - System configuration
- **rubric.yml** - Assignment rubric
- **guidance.md** - AI instruction guidance

## Installation

The validator requires PyYAML:

```bash
# Install with pip
pip install pyyaml

# Or with uv (recommended)
uv add pyyaml
```

## Usage

### Basic Validation

```bash
# Validate configs in default location (.github/feedback/)
python .github/scripts/validate_config.py

# Validate configs in custom directory
python .github/scripts/validate_config.py --config-dir /path/to/feedback
```

### Strict Mode

Treat warnings as errors:

```bash
python .github/scripts/validate_config.py --strict
```

### With uv

```bash
uv run python .github/scripts/validate_config.py
```

## What It Validates

### config.yml

**Required Fields:**
- `report_file` or `report.filename` - Student report filename
- `model.primary` - Primary AI model name

**Optional but Recommended:**
- `max_input_tokens` - Token limit for input (warns if missing)
- `max_output_tokens` - Token limit for output (warns if missing)

**Validation Checks:**
- YAML syntax is valid
- Required fields are present
- Model names are known (warns for unknown models)
- Token limits are positive integers
- Timeout values are positive numbers
- Feature flags are booleans
- Debug mode settings are valid

### rubric.yml

**Required Fields:**
- `assignment.name` - Assignment name
- `assignment.course` - Course name
- `assignment.total_points` - Total points possible
- `criteria` - List of at least one criterion

**Per Criterion:**
- `id` - Unique identifier
- `name` - Display name
- `weight` - Point weight (percentage)
- `description` - Criterion description
- `levels` - Performance levels (optional but recommended)

**Validation Checks:**
- YAML syntax is valid
- All required fields present
- Criterion IDs are unique
- Weights are positive numbers
- Weights sum to 100 (warns if not)
- Point ranges are valid (min <= max)
- Total points is positive

### guidance.md

**Validation Checks:**
- File exists
- File is not empty
- File has reasonable length (warns if < 100 characters)

## Exit Codes

- `0` - All valid (or only warnings in non-strict mode)
- `1` - YAML syntax errors
- `2` - Schema validation errors (missing/invalid fields)
- `3` - Logic errors (warnings in strict mode)

## Example Output

### Valid Configuration

```
Validating configuration files in: .github/feedback

Checking config.yml... done
Checking rubric.yml... done
Checking guidance.md... done

============================================================
VALIDATION RESULTS
============================================================

✅ config.yml: Valid
✅ guidance.md: Valid
✅ rubric.yml: Valid
============================================================
Summary: 0 error(s), 0 warning(s)

✅ All configuration files are valid!
============================================================
```

### Configuration with Warnings

```
============================================================
VALIDATION RESULTS
============================================================

⚠️  config.yml: 2 warning(s)
  ⚠️  'max_input_tokens' is not set. Consider adding it for better control over token usage.
  ⚠️  'max_output_tokens' is not set. Consider adding it for better control over token usage.

✅ guidance.md: Valid
✅ rubric.yml: Valid
============================================================
Summary: 0 error(s), 2 warning(s)

⚠️  Warnings found, but no errors
============================================================
```

### Configuration with Errors

```
============================================================
VALIDATION RESULTS
============================================================

❌ config.yml: 1 error(s)
  ❌ Line 8: YAML syntax error at line 8, column 14: expected <block end>, but found '<scalar>'

❌ rubric.yml: 3 error(s)
  ❌ 'assignment.total_points' must be a positive number, got: -50
  ❌ Criterion 2: duplicate id 'criterion1'
  ❌ Criterion 2 (Second Criterion), level 'exemplary': point_range min (100) > max (90)
  ⚠️  Criterion weights sum to 105, expected 100. This may be intentional, but typically weights should sum to 100%.

✅ guidance.md: Valid
============================================================
Summary: 4 error(s), 1 warning(s)

❌ Validation failed
============================================================
```

## Integration with Workflows

### Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
if [[ $(git diff --cached --name-only) =~ .github/feedback/ ]]; then
    echo "Validating feedback configuration..."
    python .github/scripts/validate_config.py || exit 1
fi
```

### GitHub Actions

Add to your workflow:

```yaml
- name: Validate Configuration
  run: |
    uv run python .github/scripts/validate_config.py
```

### CI/CD Pipeline

```bash
# In your CI script
python .github/scripts/validate_config.py --strict
if [ $? -ne 0 ]; then
    echo "Configuration validation failed"
    exit 1
fi
```

## Common Errors and Solutions

### "YAML syntax error"
- **Cause**: Invalid YAML format (missing quotes, wrong indentation, etc.)
- **Solution**: Check the line/column indicated, fix syntax

### "'model.primary' is required but missing"
- **Cause**: No model specified in config
- **Solution**: Add `model:` section with `primary:` field

### "Criterion weights sum to 95, expected 100"
- **Cause**: Rubric criterion weights don't add up to 100%
- **Solution**: Adjust weights or confirm this is intentional

### "Duplicate id 'criterion1'"
- **Cause**: Two criteria have the same ID
- **Solution**: Make criterion IDs unique

### "point_range min (100) > max (90)"
- **Cause**: Point range minimum is greater than maximum
- **Solution**: Fix the range: `[min, max]` where min <= max

## Advanced Usage

### Validate Only Specific File

The validator expects all three files, but you can check individual files by examining the source code in `validation_schemas.py`.

### Custom Validation Rules

Edit `validation_schemas.py` to add custom validation rules specific to your course or institution.

### Integration with IDE

Many IDEs can run Python scripts on file save. Configure your IDE to run the validator automatically when editing config files.

## Files

- `validate_config.py` - Main validation script
- `validation_schemas.py` - Schema definitions and validation logic
- `README_VALIDATION.md` - This file

## Support

If you encounter issues:

1. Check that PyYAML is installed: `python -c "import yaml; print(yaml.__version__)"`
2. Verify Python version: `python --version` (requires Python 3.7+)
3. Check file paths are correct
4. Review error messages carefully - they include line numbers when possible

## Development

To add new validation rules:

1. Edit `validation_schemas.py`
2. Add validation logic to the appropriate schema class
3. Test with valid and invalid configs
4. Update this README with the new validations

Example:

```python
# In ConfigSchema.validate()
if "new_field" in config:
    value = config["new_field"]
    if not isinstance(value, str):
        errors.append(
            ValidationError(
                ValidationError.ERROR,
                "config.yml",
                f"'new_field' must be a string, got: {type(value).__name__}",
            )
        )
```
