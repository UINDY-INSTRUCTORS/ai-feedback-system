#!/usr/bin/env python3
"""
Validation tool for AI Feedback system configuration.
Run this BEFORE submitting feedback to catch configuration issues.

Usage:
  python validate_feedback_setup.py

This script will:
  1. Check for required files (.github/config.yml, rubric, report, guidance)
  2. Convert rubric.md to rubric.yml if needed
  3. Validate config.yml syntax and required fields
  4. Check vision configuration against actual criteria
  5. Test report parsing
  6. Validate image extraction would work
  7. Report all issues with clear error messages
"""

import sys
import yaml
import json
from pathlib import Path
from typing import List, Dict, Tuple

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))
from rubric_converter import markdown_to_yaml
from parse_report import parse_quarto


class Colors:
    """Terminal color codes"""
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'


def check_file_exists(path: str, description: str) -> Tuple[bool, str]:
    """Check if a file exists and return status message."""
    p = Path(path)
    if p.exists():
        return True, f"✓ {description}"
    else:
        return False, f"✗ {description} NOT FOUND"


def validate_config() -> Tuple[bool, Dict]:
    """Validate config.yml exists and has required fields."""
    config_path = Path('.github/config.yml')

    if not config_path.exists():
        return False, {"error": "config.yml not found"}

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)

        issues = []
        required_fields = ['report_file', 'report_format', 'model']

        for field in required_fields:
            if field not in config:
                issues.append(f"Missing required field: {field}")

        if issues:
            return False, {"error": "Config validation failed", "issues": issues}

        return True, config
    except Exception as e:
        return False, {"error": f"Failed to parse config.yml: {e}"}


def validate_vision_config(config: Dict, rubric: Dict) -> List[str]:
    """Check if vision config references valid criteria."""
    issues = []
    vision_config = config.get('vision', {})

    if not vision_config.get('enabled', False):
        return []  # Vision disabled, nothing to check

    enabled_for = vision_config.get('enabled_for_criteria', [])
    if not enabled_for:
        issues.append("Vision is enabled but 'enabled_for_criteria' is empty")
        return issues

    # Get all valid criterion IDs and names
    criteria = rubric.get('criteria', [])
    valid_ids = {c.get('id', '') for c in criteria if c.get('id')}
    valid_names = {c.get('name', '') for c in criteria if c.get('name')}

    for criterion_ref in enabled_for:
        if criterion_ref == '*':
            continue  # Wildcard is valid

        if criterion_ref not in valid_ids and criterion_ref not in valid_names:
            issues.append(
                f"Vision enabled for '{criterion_ref}' but no matching criterion found.\n"
                f"      Valid IDs: {', '.join(sorted(valid_ids))}\n"
                f"      Valid names: {', '.join(sorted(valid_names))}"
            )

    return issues


def convert_rubric_if_needed() -> Tuple[bool, str]:
    """Convert RUBRIC.md to rubric.yml if markdown version exists."""
    md_path = Path('.github/feedback/RUBRIC.md')
    yml_path = Path('.github/feedback/rubric.yml')

    if not md_path.exists():
        return True, "No RUBRIC.md to convert"

    try:
        markdown_to_yaml(str(md_path), str(yml_path))
        return True, f"Converted RUBRIC.md → rubric.yml"
    except Exception as e:
        return False, f"Failed to convert rubric: {e}"


def validate_rubric() -> Tuple[bool, Dict]:
    """Validate rubric.yml exists and has valid structure."""
    rubric_path = Path('.github/feedback/rubric.yml')

    if not rubric_path.exists():
        return False, {"error": "rubric.yml not found"}

    try:
        with open(rubric_path) as f:
            rubric = yaml.safe_load(f)

        criteria = rubric.get('criteria', [])
        if not criteria:
            return False, {"error": "No criteria found in rubric"}

        issues = []
        for i, criterion in enumerate(criteria):
            if 'name' not in criterion:
                issues.append(f"Criterion {i}: missing 'name'")
            if 'id' not in criterion:
                issues.append(f"Criterion {i}: missing 'id'")
            if 'description' not in criterion:
                issues.append(f"Criterion {i}: missing 'description'")

        if issues:
            return False, {"error": "Rubric validation failed", "issues": issues}

        return True, rubric
    except Exception as e:
        return False, {"error": f"Failed to parse rubric.yml: {e}"}


def validate_report() -> Tuple[bool, str]:
    """Validate that report file exists and can be parsed."""
    import os
    original_cwd = os.getcwd()

    try:
        # Find report file
        report_file = None
        for name in ['index.qmd', 'report.qmd', 'index.md', 'report.md']:
            if Path(name).exists():
                report_file = name
                break

        if not report_file:
            return False, "Report file not found (looking for *.qmd or *.md)"

        # Try to parse
        report = parse_quarto(report_file)

        word_count = report.get('stats', {}).get('word_count', 0)
        figure_count = report.get('figures', {}).get('count', 0)
        section_count = report.get('stats', {}).get('sections', 0)

        msg = (
            f"Report parsed successfully\n"
            f"      Words: {word_count} | Figures: {figure_count} | Sections: {section_count}"
        )
        return True, msg
    except Exception as e:
        return False, f"Failed to parse report: {e}"
    finally:
        import os
        os.chdir(original_cwd)


def main():
    """Run all validation checks."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}AI Feedback System Configuration Validator{Colors.RESET}\n")

    all_passed = True

    # 1. Check required files
    print(f"{Colors.BOLD}1. Required Files{Colors.RESET}")
    required_files = [
        ('.github/config.yml', 'Configuration file'),
        ('.github/feedback/RUBRIC.md', 'Rubric (markdown)'),
        ('.github/feedback/guidance.md', 'Guidance file'),
    ]

    for filepath, desc in required_files:
        exists, msg = check_file_exists(filepath, desc)
        print(f"   {msg}")
        if not exists and desc.startswith('Configuration'):
            all_passed = False

    # 2. Convert rubric if needed
    print(f"\n{Colors.BOLD}2. Rubric Conversion{Colors.RESET}")
    success, msg = convert_rubric_if_needed()
    print(f"   {'✓' if success else '✗'} {msg}")
    if not success:
        all_passed = False

    # 3. Validate config
    print(f"\n{Colors.BOLD}3. Configuration Validation{Colors.RESET}")
    config_ok, config_result = validate_config()
    if config_ok:
        print(f"   ✓ config.yml is valid")
        config = config_result
    else:
        print(f"   ✗ {config_result.get('error')}")
        if 'issues' in config_result:
            for issue in config_result['issues']:
                print(f"      - {issue}")
        all_passed = False
        config = None

    # 4. Validate rubric
    print(f"\n{Colors.BOLD}4. Rubric Validation{Colors.RESET}")
    rubric_ok, rubric_result = validate_rubric()
    if rubric_ok:
        rubric = rubric_result
        criteria = rubric.get('criteria', [])
        print(f"   ✓ rubric.yml is valid ({len(criteria)} criteria)")
        for criterion in criteria:
            print(f"      - {criterion['name']} (id: {criterion.get('id', 'NONE')})")
    else:
        print(f"   ✗ {rubric_result.get('error')}")
        if 'issues' in rubric_result:
            for issue in rubric_result['issues']:
                print(f"      - {issue}")
        all_passed = False
        rubric = None

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

    # 6. Validate report
    print(f"\n{Colors.BOLD}6. Report Validation{Colors.RESET}")
    report_ok, report_msg = validate_report()
    if report_ok:
        print(f"   ✓ {report_msg}")
    else:
        print(f"   ✗ {report_msg}")
        all_passed = False

    # Summary
    print(f"\n{Colors.BOLD}Summary{Colors.RESET}")
    if all_passed:
        print(f"{Colors.GREEN}✓ All checks passed! Your feedback setup is ready.{Colors.RESET}\n")
        return 0
    else:
        print(f"{Colors.RED}✗ Some checks failed. Please fix the issues above before running the workflow.{Colors.RESET}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
