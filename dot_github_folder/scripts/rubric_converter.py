#!/usr/bin/env python3
"""
Bidirectional converter between YAML rubric format and Markdown.

Usage:
    # Convert YAML to Markdown (for faculty/students to read)
    python rubric_converter.py yaml-to-md rubric.yml RUBRIC.md

    # Convert Markdown to YAML (for deployment)
    python rubric_converter.py md-to-yaml RUBRIC.md rubric.yml

    # Validate round-trip conversion
    python rubric_converter.py validate rubric.yml
"""

import yaml
import re
import sys
from pathlib import Path
from typing import Dict, List, Any


def yaml_to_markdown(yaml_file: str, md_file: str) -> None:
    """
    Convert YAML rubric to beautiful Markdown format.

    Args:
        yaml_file: Path to input YAML file
        md_file: Path to output Markdown file
    """
    with open(yaml_file, 'r') as f:
        rubric = yaml.safe_load(f)

    # Build markdown content
    md = []

    # Header
    assignment = rubric.get('assignment', {})
    course = assignment.get('course', 'Course')
    name = assignment.get('name', 'Assignment')
    total_points = assignment.get('total_points', 100)

    md.append(f"# {course} - {name} Rubric\n")
    md.append(f"**Course**: {course}  ")
    md.append(f"**Assignment**: {name}  ")
    if assignment.get('type'):
        md.append(f"**Type**: {assignment['type']}  ")
    md.append(f"**Total Points**: {total_points}\n")
    md.append("---\n")

    # Criteria
    criteria = rubric.get('criteria', [])
    for i, criterion in enumerate(criteria, 1):
        criterion_name = criterion.get('name', 'Unnamed Criterion')
        weight = criterion.get('weight', 0)
        description = criterion.get('description', '').strip()

        md.append(f"## Criterion {i}: {criterion_name} ({weight}%)\n")

        if description:
            md.append(f"{description}\n")

        # Performance levels table
        levels = criterion.get('levels', {})
        if levels:
            md.append("### Performance Levels\n")
            md.append("| Level | Points | Description |")
            md.append("|-------|--------|-------------|")

            # Order: excellent, good, poor (or whatever levels exist)
            level_order = ['excellent', 'good', 'satisfactory', 'poor', 'unsatisfactory']
            sorted_levels = []
            for level_key in level_order:
                if level_key in levels:
                    sorted_levels.append((level_key, levels[level_key]))
            # Add any other levels not in the standard order
            for level_key, level_data in levels.items():
                if level_key not in level_order:
                    sorted_levels.append((level_key, level_data))

            for level_key, level_data in sorted_levels:
                level_name = level_key.replace('_', ' ').title()
                point_range = level_data.get('point_range', [0, 0])
                desc = level_data.get('description', '').strip().replace('\n', ' ')
                md.append(f"| **{level_name}** | {point_range[0]}-{point_range[1]} | {desc} |")

            md.append("")

            # Indicators for each level
            for level_key, level_data in sorted_levels:
                level_name = level_key.replace('_', ' ').title()
                indicators = level_data.get('indicators', [])
                if indicators:
                    md.append(f"### {level_name} Indicators")
                    for indicator in indicators:
                        md.append(f"- {indicator}")
                    md.append("")

        # Keywords
        keywords = criterion.get('keywords', [])
        if keywords:
            md.append("### Keywords")
            md.append(", ".join(keywords))
            md.append("")

        # Common issues
        common_issues = criterion.get('common_issues', [])
        if common_issues:
            md.append("### Common Issues")
            for issue in common_issues:
                md.append(f"- {issue}")
            md.append("")

        md.append("---\n")

    # Write to file
    with open(md_file, 'w') as f:
        f.write('\n'.join(md))

    print(f"✅ Converted {yaml_file} → {md_file}")
    print(f"   {len(criteria)} criteria converted")


def markdown_to_yaml(md_file: str, yaml_file: str) -> None:
    """
    Convert Markdown rubric back to YAML format.

    Args:
        md_file: Path to input Markdown file
        yaml_file: Path to output YAML file
    """
    with open(md_file, 'r') as f:
        content = f.read()

    # Parse markdown
    rubric = {
        'assignment': {},
        'criteria': []
    }

    # Extract header information
    header_pattern = r'\*\*(.+?)\*\*:\s*(.+?)(?:\s\s|\n)'
    headers = re.findall(header_pattern, content)

    for key, value in headers:
        key_lower = key.lower()
        if key_lower == 'course':
            rubric['assignment']['course'] = value.strip()
        elif key_lower == 'assignment':
            rubric['assignment']['name'] = value.strip()
        elif key_lower == 'type':
            rubric['assignment']['type'] = value.strip()
        elif key_lower == 'total points':
            rubric['assignment']['total_points'] = int(value.strip())

    # Extract criteria
    criteria_pattern = r'##\s+Criterion\s+\d+:\s+(.+?)\s+\((\d+)%\)(.*?)(?=##\s+Criterion|\Z)'
    criteria_matches = re.findall(criteria_pattern, content, re.DOTALL)

    for match in criteria_matches:
        criterion_name = match[0].strip()
        weight = int(match[1])
        criterion_content = match[2]

        # Generate ID from name
        criterion_id = re.sub(r'[^a-z0-9]+', '_', criterion_name.lower()).strip('_')

        criterion = {
            'id': criterion_id,
            'name': criterion_name,
            'weight': weight,
            'levels': {},
            'keywords': [],
            'common_issues': []
        }

        # Extract description (text before "### Performance Levels")
        desc_match = re.search(r'^(.*?)(?=###|$)', criterion_content, re.DOTALL)
        if desc_match:
            description = desc_match.group(1).strip()
            if description:
                criterion['description'] = description

        # Extract performance levels table
        table_pattern = r'\|\s*\*\*(.+?)\*\*\s*\|\s*(\d+)-(\d+)\s*\|\s*(.+?)\s*\|'
        table_matches = re.findall(table_pattern, criterion_content)

        for level_name, min_points, max_points, description in table_matches:
            level_key = level_name.lower().replace(' ', '_')
            criterion['levels'][level_key] = {
                'description': description.strip(),
                'point_range': [int(min_points), int(max_points)],
                'indicators': []
            }

        # Extract indicators for each level
        indicator_pattern = r'###\s+(.+?)\s+Indicators\n((?:- .+\n?)+)'
        indicator_matches = re.findall(indicator_pattern, criterion_content)

        for level_name, indicators_text in indicator_matches:
            level_key = level_name.lower().replace(' ', '_')
            if level_key in criterion['levels']:
                indicators = re.findall(r'-\s+(.+)', indicators_text)
                criterion['levels'][level_key]['indicators'] = [ind.strip() for ind in indicators]

        # Extract keywords
        keywords_match = re.search(r'###\s+Keywords\n(.+?)(?=\n###|\n---|\Z)', criterion_content, re.DOTALL)
        if keywords_match:
            keywords_text = keywords_match.group(1).strip()
            criterion['keywords'] = [k.strip() for k in keywords_text.split(',')]

        # Extract common issues
        issues_match = re.search(r'###\s+Common Issues\n((?:- .+\n?)+)', criterion_content)
        if issues_match:
            issues = re.findall(r'-\s+(.+)', issues_match.group(1))
            criterion['common_issues'] = [issue.strip() for issue in issues]

        rubric['criteria'].append(criterion)

    # Write to YAML file
    with open(yaml_file, 'w') as f:
        # Add comment at top
        f.write(f"# {rubric['assignment'].get('course', 'Course')} - {rubric['assignment'].get('name', 'Assignment')} Rubric\n")
        f.write("# Auto-generated from Markdown. Edit the .md file and regenerate.\n\n")
        yaml.dump(rubric, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"✅ Converted {md_file} → {yaml_file}")
    print(f"   {len(rubric['criteria'])} criteria converted")


def validate_roundtrip(yaml_file: str) -> bool:
    """
    Validate that YAML → MD → YAML preserves all information.

    Args:
        yaml_file: Path to original YAML file

    Returns:
        True if round-trip preserves data, False otherwise
    """
    import tempfile

    print(f"Validating round-trip conversion for {yaml_file}...")

    # Read original
    with open(yaml_file, 'r') as f:
        original = yaml.safe_load(f)

    # Create temp files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as md_temp:
        md_temp_path = md_temp.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as yaml_temp:
        yaml_temp_path = yaml_temp.name

    try:
        # Convert YAML → MD → YAML
        yaml_to_markdown(yaml_file, md_temp_path)
        markdown_to_yaml(md_temp_path, yaml_temp_path)

        # Read converted
        with open(yaml_temp_path, 'r') as f:
            converted = yaml.safe_load(f)

        # Compare key fields
        errors = []

        # Check assignment info
        if original.get('assignment') != converted.get('assignment'):
            errors.append("Assignment metadata mismatch")

        # Check criteria count
        if len(original.get('criteria', [])) != len(converted.get('criteria', [])):
            errors.append(f"Criteria count mismatch: {len(original.get('criteria', []))} vs {len(converted.get('criteria', []))}")

        # Check each criterion
        for i, (orig_crit, conv_crit) in enumerate(zip(original.get('criteria', []), converted.get('criteria', []))):
            if orig_crit.get('name') != conv_crit.get('name'):
                errors.append(f"Criterion {i+1} name mismatch")
            if orig_crit.get('weight') != conv_crit.get('weight'):
                errors.append(f"Criterion {i+1} weight mismatch")
            if len(orig_crit.get('keywords', [])) != len(conv_crit.get('keywords', [])):
                errors.append(f"Criterion {i+1} keywords count mismatch")

        if errors:
            print("❌ Validation FAILED:")
            for error in errors:
                print(f"   - {error}")
            return False
        else:
            print("✅ Validation PASSED")
            print("   All data preserved through round-trip conversion")
            return True

    finally:
        # Cleanup
        Path(md_temp_path).unlink(missing_ok=True)
        Path(yaml_temp_path).unlink(missing_ok=True)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == 'yaml-to-md':
        if len(sys.argv) != 4:
            print("Usage: rubric_converter.py yaml-to-md <input.yml> <output.md>")
            sys.exit(1)
        yaml_to_markdown(sys.argv[2], sys.argv[3])

    elif command == 'md-to-yaml':
        if len(sys.argv) != 4:
            print("Usage: rubric_converter.py md-to-yaml <input.md> <output.yml>")
            sys.exit(1)
        markdown_to_yaml(sys.argv[2], sys.argv[3])

    elif command == 'validate':
        if len(sys.argv) != 3:
            print("Usage: rubric_converter.py validate <rubric.yml>")
            sys.exit(1)
        success = validate_roundtrip(sys.argv[2])
        sys.exit(0 if success else 1)

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
