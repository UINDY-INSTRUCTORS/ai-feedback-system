#!/usr/bin/env python3
"""
Generic Quarto/Markdown report parser.
Extracts content, structure, and metadata for AI analysis.
"""

import json
import yaml
import re
import sys
from pathlib import Path

def parse_quarto(file_path):
    """Parse a Quarto (.qmd) document."""
    try:
        with open(file_path) as f:
            content = f.read()
    except FileNotFoundError:
        print(f"ERROR: Report file not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to read report file: {e}")
        sys.exit(1)

    # Extract YAML frontmatter
    yaml_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    metadata = {}
    body_start = 0

    if yaml_match:
        try:
            metadata = yaml.safe_load(yaml_match.group(1))
        except yaml.YAMLError as e:
            print(f"WARNING: Failed to parse YAML frontmatter: {e}")
            metadata = {}
        body_start = yaml_match.end()

    body = content[body_start:]

    # Extract structure (headings)
    headings = re.findall(r'^(#{1,6})\s+(.+)$', body, re.MULTILINE)
    structure = [
        {'level': len(h[0]), 'text': h[1].strip()}
        for h in headings
    ]

    # Count elements
    code_blocks = len(re.findall(r'```\{python\}.*?```', body, re.DOTALL))
    equations = len(re.findall(r'\$\$.*?\$\$|\$[^$]+\$', body, re.DOTALL))
    figures = len(re.findall(r'!\[.*?\]\(.*?\)', body))

    # Extract figure references for checking
    figure_refs = re.findall(r'!\[(.*?)\]\((.*?)\)', body)
    figure_captions = [ref[0] for ref in figure_refs]
    figure_paths = [ref[1] for ref in figure_refs]

    # Word count (approximate - exclude code blocks and LaTeX)
    text_only = re.sub(r'```.*?```', '', body, flags=re.DOTALL)  # Remove code blocks
    text_only = re.sub(r'\$\$.*?\$\$', '', text_only, flags=re.DOTALL)  # Remove display math
    text_only = re.sub(r'\$[^$]+\$', '', text_only)  # Remove inline math
    words = len(re.findall(r'\w+', text_only))

    # Check for supplementary files
    supplementary_status = check_supplementary_files()

    return {
        'content': content,
        'metadata': metadata,
        'structure': structure,
        'figures': {
            'count': figures,
            'captions': figure_captions,
            'paths': figure_paths
        },
        'stats': {
            'word_count': words,
            'code_blocks': code_blocks,
            'equations': equations,
            'figures': figures,
            'sections': len(structure)
        },
        'supplementary': supplementary_status
    }

def check_supplementary_files():
    """Check for existence of supplementary files mentioned in config."""
    try:
        with open('.github/feedback/config.yml') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"WARNING: Could not load config for supplementary file check: {e}")
        return {}

    supplementary_files = config.get('supplementary_files', [])
    status = {}

    for pattern in supplementary_files:
        # Use glob to check for files matching pattern
        matches = list(Path('.').glob(pattern))
        status[pattern] = {
            'exists': len(matches) > 0,
            'count': len(matches),
            'files': [str(m) for m in matches[:5]]  # Limit to first 5 for brevity
        }

    return status

def main():
    """Parse report and save results."""
    # Load config to get report file path
    try:
        with open('.github/feedback/config.yml') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("ERROR: Configuration file not found at .github/feedback/config.yml")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        sys.exit(1)

    report_file = config.get('report_file', 'index.qmd')

    print(f"Parsing {report_file}...")
    parsed = parse_quarto(report_file)

    # Save parsed report
    try:
        with open('parsed_report.json', 'w') as f:
            json.dump(parsed, f, indent=2)
    except Exception as e:
        print(f"ERROR: Failed to save parsed report: {e}")
        sys.exit(1)

    # Print summary
    print(f"✅ Parsed successfully:")
    print(f"   - {parsed['stats']['word_count']} words")
    print(f"   - {parsed['stats']['code_blocks']} code blocks")
    print(f"   - {parsed['stats']['equations']} equations")
    print(f"   - {parsed['stats']['figures']} figures")
    print(f"   - {parsed['stats']['sections']} sections")

    # Print supplementary file status
    print(f"\n📂 Supplementary files:")
    for pattern, status in parsed['supplementary'].items():
        if status['exists']:
            print(f"   ✅ {pattern}: {status['count']} file(s) found")
        else:
            print(f"   ⚠️  {pattern}: not found")

if __name__ == '__main__':
    main()
