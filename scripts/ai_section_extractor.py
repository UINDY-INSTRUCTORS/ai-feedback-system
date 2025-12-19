#!/usr/bin/env python3
"""
AI-based section extraction for criterion-based analysis.
Uses the GitHub Models API to intelligently extract relevant sections
based on rubric criteria, replacing brittle keyword-based extraction.
"""

import os
import json
import requests
import sys
from typing import Dict, Any

# Load environment variables from .env file if it exists (for local testing)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# GitHub Models API endpoint
API_BASE = "https://models.inference.ai.azure.com"


def extract_sections_for_criterion_ai(
    report: Dict[str, Any],
    criterion: Dict[str, Any],
    model: str = "gpt-4o-mini"
) -> str:
    """
    Use AI to extract relevant sections from report for a specific criterion.

    Args:
        report: Parsed report with content, structure, metadata
        criterion: Rubric criterion with name, description, keywords, etc.
        model: Model to use for extraction (default: gpt-4o-mini for speed/cost)

    Returns:
        Focused text containing only relevant sections for this criterion
    """

    # Get full report content
    full_content = report.get('content', '')

    # If content is too short, just return it
    if len(full_content) < 500:
        return full_content

    # Build extraction prompt
    prompt = build_extraction_prompt(report, criterion)

    # Call API
    try:
        extracted_text = call_extraction_api(prompt, model)
        return extracted_text
    except Exception as e:
        print(f"WARNING: AI extraction failed for {criterion['name']}: {e}")
        print("Falling back to returning full report content...")
        # Fallback: return full content (truncated if needed)
        return full_content[:6000]


def build_extraction_prompt(report: Dict[str, Any], criterion: Dict[str, Any]) -> str:
    """Build prompt for AI to extract relevant sections."""

    criterion_name = criterion.get('name', 'Unknown')
    criterion_desc = criterion.get('description', '')
    keywords = criterion.get('keywords', [])

    # Get report metadata for context
    structure = report.get('structure', [])
    heading_list = "\n".join([
        f"{'  ' * (h['level']-1)}- {h['text']}"
        for h in structure[:20]  # Limit to first 20 headings
    ])

    full_content = report.get('content', '')

    prompt = f"""You are a technical report analyzer. Your task is to extract ONLY the sections of a student report that are relevant to evaluating a specific rubric criterion.

**Rubric Criterion to Evaluate:**
**{criterion_name}**
{criterion_desc}

**Keywords that may indicate relevant sections:** {', '.join(keywords[:10])}

**Report Structure (headings):**
{heading_list}

**Your Task:**
1. Read through the report below
2. Identify which sections are relevant to evaluating the "{criterion_name}" criterion
3. Extract those sections verbatim (include headings, text, and references to figures/equations)
4. Return ONLY the relevant content - be selective to keep the extraction focused
5. If multiple sections are relevant, separate them with "---"
6. Aim for 1000-2500 words of extracted content (not the whole report!)

**IMPORTANT:**
- Include section headings to provide context
- Include references to figures/equations if they're in relevant sections
- Do NOT include sections that aren't relevant to this specific criterion
- Do NOT summarize or paraphrase - extract verbatim
- If a section is only partially relevant, extract just the relevant paragraphs

**Full Report:**

{full_content}

**Extracted Sections (relevant to "{criterion_name}"):**"""

    return prompt


def call_extraction_api(prompt: str, model: str) -> str:
    """Call GitHub Models API to perform extraction."""

    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable not set")

    endpoint = f"{API_BASE}/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # Use a smaller model for extraction (faster and cheaper)
    # gpt-4o-mini is good for this task
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a precise document analyzer. Extract only the requested sections verbatim. Be selective and focused."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1,  # Low temperature for consistency
        "max_tokens": 3000   # Limit extraction length
    }

    response = requests.post(endpoint, headers=headers, json=payload)
    response.raise_for_status()

    result = response.json()
    extracted = result['choices'][0]['message']['content'].strip()

    # Log token usage
    usage = result.get('usage', {})
    print(f"   Extraction tokens: {usage.get('total_tokens', 0)} (prompt: {usage.get('prompt_tokens', 0)}, completion: {usage.get('completion_tokens', 0)})")

    return extracted


def test_extraction():
    """Test the AI-based extraction on a sample report."""
    import yaml

    # Load parsed report
    try:
        with open('parsed_report.json') as f:
            report = json.load(f)
    except Exception as e:
        print(f"ERROR: Could not load parsed_report.json: {e}")
        sys.exit(1)

    # Load rubric
    try:
        with open('.github/feedback/rubric.yml') as f:
            rubric = yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Could not load rubric: {e}")
        sys.exit(1)

    # Get criteria
    criteria = rubric.get('criteria', [])
    if not criteria:
        print("ERROR: No criteria found in rubric")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"Testing AI-based section extraction")
    print(f"{'='*60}\n")
    print(f"Report: {report['stats']['word_count']} words, {report['stats']['sections']} sections")
    print(f"Testing with first criterion: {criteria[0]['name']}\n")

    # Test extraction for first criterion
    criterion = criteria[0]
    print(f"Extracting sections for: {criterion['name']}")
    print(f"Description: {criterion['description'][:100]}...")
    print()

    extracted = extract_sections_for_criterion_ai(report, criterion)

    print(f"\n{'='*60}")
    print(f"EXTRACTED CONTENT ({len(extracted.split())} words):")
    print(f"{'='*60}\n")
    print(extracted[:2000])  # Print first 2000 chars
    if len(extracted) > 2000:
        print(f"\n... [truncated, {len(extracted) - 2000} more characters]")

    # Save to file for inspection
    output_file = 'ai_extracted_section.txt'
    with open(output_file, 'w') as f:
        f.write(f"Criterion: {criterion['name']}\n")
        f.write(f"{'='*60}\n\n")
        f.write(extracted)

    print(f"\n✅ Full extraction saved to: {output_file}")


if __name__ == '__main__':
    test_extraction()
