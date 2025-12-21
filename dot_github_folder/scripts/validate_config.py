#!/usr/bin/env python3
"""
Validate AI feedback system configuration files.

This utility validates:
- config.yml: System configuration
- rubric.yml: Assignment rubric
- guidance.md: AI instruction guidance

Usage:
    python validate_config.py [--config-dir PATH]

Exit codes:
    0: All valid
    1: YAML syntax errors
    2: Schema validation errors
    3: Logic errors (warnings promoted to errors with --strict)
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

import yaml

from validation_schemas import ConfigSchema, GuidanceSchema, RubricSchema, ValidationError


def load_yaml_file(file_path: Path) -> Tuple[dict, List[ValidationError]]:
    """
    Load and parse a YAML file.

    Returns:
        Tuple of (parsed_dict, errors_list)
    """
    errors = []

    try:
        with open(file_path, "r") as f:
            content = yaml.safe_load(f)
            if content is None:
                errors.append(
                    ValidationError(
                        ValidationError.ERROR,
                        file_path.name,
                        "File is empty or contains only comments",
                    )
                )
                return {}, errors
            return content, errors
    except FileNotFoundError:
        errors.append(
            ValidationError(
                ValidationError.ERROR,
                file_path.name,
                f"File not found: {file_path}",
            )
        )
        return {}, errors
    except yaml.YAMLError as e:
        error_msg = str(e)
        # Try to extract line number from YAML error
        if hasattr(e, "problem_mark"):
            mark = e.problem_mark
            errors.append(
                ValidationError(
                    ValidationError.ERROR,
                    file_path.name,
                    f"YAML syntax error at line {mark.line + 1}, column {mark.column + 1}: {e.problem}",
                    line=mark.line + 1,
                )
            )
        else:
            errors.append(
                ValidationError(
                    ValidationError.ERROR,
                    file_path.name,
                    f"YAML syntax error: {error_msg}",
                )
            )
        return {}, errors
    except Exception as e:
        errors.append(
            ValidationError(
                ValidationError.ERROR,
                file_path.name,
                f"Unexpected error reading file: {e}",
            )
        )
        return {}, errors


def validate_config_file(config_dir: Path) -> List[ValidationError]:
    """Validate config.yml file."""
    config_path = config_dir / "config.yml"
    config, errors = load_yaml_file(config_path)

    if not errors:
        # Only validate schema if YAML parsing succeeded
        schema_errors = ConfigSchema.validate(config)
        errors.extend(schema_errors)

    return errors


def validate_rubric_file(config_dir: Path) -> List[ValidationError]:
    """Validate rubric.yml file."""
    rubric_path = config_dir / "rubric.yml"
    rubric, errors = load_yaml_file(rubric_path)

    if not errors:
        # Only validate schema if YAML parsing succeeded
        schema_errors = RubricSchema.validate(rubric)
        errors.extend(schema_errors)

    return errors


def validate_guidance_file(config_dir: Path) -> List[ValidationError]:
    """Validate guidance.md file."""
    guidance_path = config_dir / "guidance.md"
    return GuidanceSchema.validate(str(guidance_path))


def print_summary(all_errors: dict, strict: bool = False) -> int:
    """
    Print validation summary and return appropriate exit code.

    Args:
        all_errors: Dictionary mapping file names to lists of ValidationError
        strict: If True, treat warnings as errors

    Returns:
        Exit code (0=success, 1=syntax errors, 2=schema errors, 3=logic errors/warnings)
    """
    total_errors = 0
    total_warnings = 0
    has_syntax_errors = False
    has_schema_errors = False

    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60 + "\n")

    # Print results for each file
    for file_name in sorted(all_errors.keys()):
        errors = all_errors[file_name]

        if not errors:
            print(f"✅ {file_name}: Valid")
            continue

        # Count errors and warnings
        file_errors = [e for e in errors if e.severity == ValidationError.ERROR]
        file_warnings = [e for e in errors if e.severity == ValidationError.WARNING]

        total_errors += len(file_errors)
        total_warnings += len(file_warnings)

        # Check for syntax errors (YAML parse failures)
        if any("YAML syntax error" in e.message or "File not found" in e.message for e in file_errors):
            has_syntax_errors = True
        elif file_errors:
            has_schema_errors = True

        # Print file status
        if file_errors:
            print(f"❌ {file_name}: {len(file_errors)} error(s)")
        elif file_warnings:
            print(f"⚠️  {file_name}: {len(file_warnings)} warning(s)")

        # Print each error/warning
        for error in file_errors:
            print(f"  ❌ {error}")

        for warning in file_warnings:
            if strict:
                print(f"  ❌ {warning} [promoted to error in strict mode]")
            else:
                print(f"  ⚠️  {warning}")

        print()

    # Print summary
    print("=" * 60)
    if strict and total_warnings > 0:
        print(f"Summary: {total_errors + total_warnings} error(s), 0 warning(s) [strict mode]")
        exit_code = 2 if has_schema_errors or total_warnings else 1 if has_syntax_errors else 3
    else:
        print(f"Summary: {total_errors} error(s), {total_warnings} warning(s)")

        if total_errors == 0 and total_warnings == 0:
            print("\n✅ All configuration files are valid!")
            exit_code = 0
        elif total_errors == 0:
            print("\n⚠️  Warnings found, but no errors")
            exit_code = 0  # Warnings don't cause failure by default
        else:
            print("\n❌ Validation failed")
            if has_syntax_errors:
                exit_code = 1
            elif has_schema_errors:
                exit_code = 2
            else:
                exit_code = 3

    print("=" * 60 + "\n")
    return exit_code


def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(
        description="Validate AI feedback system configuration files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit codes:
  0: All valid (or only warnings in non-strict mode)
  1: YAML syntax errors
  2: Schema validation errors (missing fields, wrong types)
  3: Logic errors (warnings in strict mode, or other logic issues)

Examples:
  # Validate configs in default location
  python validate_config.py

  # Validate configs in custom directory
  python validate_config.py --config-dir /path/to/feedback

  # Strict mode (treat warnings as errors)
  python validate_config.py --strict
        """,
    )

    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path(".github/feedback"),
        help="Path to feedback configuration directory (default: .github/feedback)",
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )

    args = parser.parse_args()

    # Check if config directory exists
    if not args.config_dir.exists():
        print(f"❌ Error: Configuration directory not found: {args.config_dir}")
        print(f"\nExpected structure:")
        print(f"  {args.config_dir}/")
        print(f"  ├── config.yml")
        print(f"  ├── rubric.yml")
        print(f"  └── guidance.md")
        return 1

    print(f"Validating configuration files in: {args.config_dir}")
    print()

    # Validate each file
    all_errors = {}

    print("Checking config.yml...", end=" ")
    config_errors = validate_config_file(args.config_dir)
    all_errors["config.yml"] = config_errors
    print("done")

    print("Checking rubric.yml...", end=" ")
    rubric_errors = validate_rubric_file(args.config_dir)
    all_errors["rubric.yml"] = rubric_errors
    print("done")

    print("Checking guidance.md...", end=" ")
    guidance_errors = validate_guidance_file(args.config_dir)
    all_errors["guidance.md"] = guidance_errors
    print("done")

    # Print summary and exit
    exit_code = print_summary(all_errors, strict=args.strict)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
