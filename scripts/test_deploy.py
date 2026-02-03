#!/usr/bin/env python3
"""
Pre-deployment validation script for AI Feedback System repos.

Simulates what CI will do when deploying an assignment, catching configuration
issues BEFORE deployment to GitHub Classroom.

Usage:
    python scripts/test_deploy.py <path-to-student-repo>

Example:
    python scripts/test_deploy.py ~/ee340/repos/lab-2-communication-sspickle

Exit codes:
    0: All checks passed
    1: One or more checks failed
"""

import sys
import os
import yaml
import tempfile
from pathlib import Path
from typing import Tuple, List, Dict


class Colors:
    """Terminal color codes"""
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'


def check_file_exists(path: Path, description: str) -> Tuple[bool, str]:
    """Check if a file exists and return status message."""
    if path.exists():
        return True, f"✓ {description}"
    else:
        return False, f"✗ {description} NOT FOUND at {path}"


def validate_config(config_path: Path) -> Tuple[bool, Dict, List[str]]:
    """
    Validate config.yml: required fields (report_file, report_format, model).

    Returns:
        Tuple of (success, config_dict, error_messages)
    """
    issues = []

    if not config_path.exists():
        return False, {}, [f"config.yml not found at {config_path}"]

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)

        if not isinstance(config, dict):
            return False, {}, ["config.yml does not contain a valid YAML dictionary"]

        required_fields = ['report_file', 'report_format', 'model']

        for field in required_fields:
            if field not in config:
                issues.append(f"Missing required field: {field}")

        if issues:
            return False, config, issues

        return True, config, []
    except yaml.YAMLError as e:
        return False, {}, [f"Failed to parse config.yml: {e}"]
    except Exception as e:
        return False, {}, [f"Unexpected error reading config.yml: {e}"]


def validate_rubric(rubric_path: Path) -> Tuple[bool, Dict, List[str]]:
    """
    Validate rubric.yml: every criterion must have name, id, description.

    Returns:
        Tuple of (success, rubric_dict, error_messages)
    """
    issues = []

    if not rubric_path.exists():
        return False, {}, [f"rubric.yml not found at {rubric_path}"]

    try:
        with open(rubric_path) as f:
            rubric = yaml.safe_load(f)

        if not isinstance(rubric, dict):
            return False, {}, ["rubric.yml does not contain a valid YAML dictionary"]

        criteria = rubric.get('criteria', [])
        if not criteria:
            return False, rubric, ["No criteria found in rubric"]

        for i, criterion in enumerate(criteria):
            if 'name' not in criterion:
                issues.append(f"Criterion {i}: missing 'name'")
            if 'id' not in criterion:
                issues.append(f"Criterion {i}: missing 'id'")
            if 'description' not in criterion:
                issues.append(f"Criterion {i}: missing 'description'")

        if issues:
            return False, rubric, issues

        return True, rubric, []
    except yaml.YAMLError as e:
        return False, {}, [f"Failed to parse rubric.yml: {e}"]
    except Exception as e:
        return False, {}, [f"Unexpected error reading rubric.yml: {e}"]


def validate_vision_config(config: Dict, rubric: Dict) -> List[str]:
    """
    Validate vision config references valid criteria.

    Accepts criterion references by:
    - ID (e.g., "code_quality")
    - Name (e.g., "Code Quality")
    - Number/position (e.g., "1" for first criterion, "3" for third)
    - Wildcard (e.g., "*" for all)

    Returns:
        List of error messages (empty if no errors)
    """
    issues = []
    vision_config = config.get('vision', {})

    if not vision_config.get('enabled', False):
        return []  # Vision disabled, nothing to check

    enabled_for = vision_config.get('enabled_for_criteria', [])
    if not enabled_for:
        issues.append("Vision is enabled but 'enabled_for_criteria' is empty")
        return issues

    # Get all valid criterion IDs, names, and positions
    criteria = rubric.get('criteria', [])
    valid_ids = {c.get('id', ''): i for i, c in enumerate(criteria) if c.get('id')}
    valid_names = {c.get('name', ''): i for i, c in enumerate(criteria) if c.get('name')}
    # For position-based references (1-indexed to match rubric table row numbers)
    valid_positions = {str(i+1) for i in range(len(criteria))}

    for criterion_ref in enabled_for:
        if criterion_ref == '*':
            continue  # Wildcard is valid

        is_valid = (
            criterion_ref in valid_ids or
            criterion_ref in valid_names or
            criterion_ref in valid_positions
        )

        if not is_valid:
            issues.append(
                f"Vision enabled for '{criterion_ref}' but no matching criterion found.\n"
                f"      Valid by ID: {', '.join(sorted(valid_ids.keys()))}\n"
                f"      Valid by name: {', '.join(sorted(valid_names.keys()))}\n"
                f"      Valid by position: {', '.join(sorted(valid_positions))}"
            )

    return issues


def convert_rubric_markdown_to_temp(md_path: Path) -> Tuple[bool, str, str]:
    """
    Convert RUBRIC.md to temp rubric.yml using rubric_converter.

    Returns:
        Tuple of (success, temp_file_path, error_message)
    """
    try:
        # Import rubric_converter from dot_github_folder/scripts/
        sys.path.insert(0, str(Path(__file__).parent.parent / "dot_github_folder" / "scripts"))
        from rubric_converter import markdown_to_yaml

        # Create temp file for converted rubric
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            temp_path = f.name

        try:
            markdown_to_yaml(str(md_path), temp_path)
            return True, temp_path, ""
        except Exception as e:
            # Clean up temp file on error
            Path(temp_path).unlink(missing_ok=True)
            return False, "", f"Failed to convert RUBRIC.md: {e}"
    except ImportError as e:
        return False, "", f"Could not import rubric_converter: {e}"
    except Exception as e:
        return False, "", f"Unexpected error during rubric conversion: {e}"


def main():
    """Run all validation checks."""
    # Parse arguments
    if len(sys.argv) != 2:
        print(f"{Colors.BOLD}Usage:{Colors.RESET}")
        print(f"  python scripts/test_deploy.py <path-to-student-repo>\n")
        print(f"{Colors.BOLD}Example:{Colors.RESET}")
        print(f"  python scripts/test_deploy.py ~/ee340/repos/lab-2-communication-sspickle\n")
        return 1

    repo_path = Path(sys.argv[1]).resolve()

    if not repo_path.exists():
        print(f"{Colors.RED}✗ Repository path does not exist: {repo_path}{Colors.RESET}\n")
        return 1

    if not repo_path.is_dir():
        print(f"{Colors.RED}✗ Path is not a directory: {repo_path}{Colors.RESET}\n")
        return 1

    print(f"\n{Colors.BOLD}{Colors.BLUE}Pre-Deployment Validation{Colors.RESET}")
    print(f"{Colors.BOLD}Repo:{Colors.RESET} {repo_path}\n")

    all_passed = True
    temp_rubric_path = None

    try:
        # 1. Check required files
        print(f"{Colors.BOLD}1. Required Files{Colors.RESET}")
        required_files = [
            (repo_path / '.github' / 'config.yml', 'Configuration file'),
            (repo_path / '.github' / 'feedback' / 'RUBRIC.md', 'Rubric (markdown)'),
            (repo_path / '.github' / 'feedback' / 'guidance.md', 'Guidance file'),
        ]

        for filepath, desc in required_files:
            exists, msg = check_file_exists(filepath, desc)
            print(f"   {msg}")
            if not exists:
                all_passed = False

        # 2. Convert RUBRIC.md to temp rubric.yml
        print(f"\n{Colors.BOLD}2. Rubric Conversion{Colors.RESET}")
        md_path = repo_path / '.github' / 'feedback' / 'RUBRIC.md'

        if md_path.exists():
            success, temp_path, error_msg = convert_rubric_markdown_to_temp(md_path)
            if success:
                print(f"   ✓ Converted RUBRIC.md → temporary rubric.yml")
                temp_rubric_path = temp_path
            else:
                print(f"   ✗ {error_msg}")
                all_passed = False
        else:
            print(f"   ✗ RUBRIC.md not found (should exist at {md_path})")
            all_passed = False

        # 3. Validate config.yml
        print(f"\n{Colors.BOLD}3. Configuration Validation{Colors.RESET}")
        config_path = repo_path / '.github' / 'config.yml'
        config_ok, config, config_issues = validate_config(config_path)

        if config_ok:
            print(f"   ✓ config.yml is valid")
        else:
            print(f"   ✗ config.yml validation failed:")
            for issue in config_issues:
                print(f"      - {issue}")
            all_passed = False

        # 4. Validate rubric.yml (using converted temp file)
        print(f"\n{Colors.BOLD}4. Rubric Validation{Colors.RESET}")
        if temp_rubric_path:
            rubric_path = Path(temp_rubric_path)
            rubric_ok, rubric, rubric_issues = validate_rubric(rubric_path)

            if rubric_ok:
                criteria = rubric.get('criteria', [])
                print(f"   ✓ rubric.yml is valid ({len(criteria)} criteria)")
                for criterion in criteria:
                    print(f"      - {criterion['name']} (id: {criterion.get('id', 'NONE')})")
            else:
                print(f"   ✗ rubric.yml validation failed:")
                for issue in rubric_issues:
                    print(f"      - {issue}")
                all_passed = False
        else:
            print(f"   ✗ Cannot validate rubric (conversion failed)")
            rubric_ok = False
            rubric = {}
            all_passed = False

        # 5. Validate vision config
        if config_ok and rubric_ok:
            print(f"\n{Colors.BOLD}5. Vision Configuration{Colors.RESET}")
            vision_issues = validate_vision_config(config, rubric)
            if not vision_issues:
                vision_enabled = config.get('vision', {}).get('enabled', False)
                if vision_enabled:
                    print(f"   ✓ Vision configuration is valid")
                else:
                    print(f"   ⓘ Vision is disabled (this is fine)")
            else:
                for issue in vision_issues:
                    print(f"   ✗ {issue}")
                all_passed = False

        # 6. Report parsing check (skip with note)
        print(f"\n{Colors.BOLD}6. Report Parsing{Colors.RESET}")
        print(f"   ⓘ Report parsing skipped (requires quarto installation)")
        print(f"     This will be validated during actual deployment.")

        # Summary
        print(f"\n{Colors.BOLD}Summary{Colors.RESET}")
        if all_passed:
            print(f"{Colors.GREEN}✓ All checks passed! This repo is ready for deployment.{Colors.RESET}\n")
            return 0
        else:
            print(f"{Colors.RED}✗ Some checks failed. Please fix the issues above before deploying.{Colors.RESET}\n")
            return 1

    finally:
        # Clean up temp rubric file
        if temp_rubric_path:
            Path(temp_rubric_path).unlink(missing_ok=True)


if __name__ == '__main__':
    sys.exit(main())
