#!/usr/bin/env python3
"""
Criterion-based AI feedback using GitHub Models API with AI-based section extraction.
"""

import os
import json
import yaml
import requests
import sys
import concurrent.futures
from pathlib import Path
from section_extractor import extract_sections_for_criterion_ai

# Load environment variables from .env file if it exists (for local testing)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# GitHub Models API endpoint
API_BASE = "https://models.inference.ai.azure.com"


def load_config():
    """Load course-specific configuration."""
    try:
        with open('.github/feedback/config.yml') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Failed to load config: {e}")
        sys.exit(1)


def load_rubric():
    """Load machine-readable rubric."""
    try:
        with open('.github/feedback/rubric.yml') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Failed to load rubric: {e}")
        sys.exit(1)


def load_guidance():
    """Load AI instruction guidance."""
    try:
        with open('.github/feedback/guidance.md') as f:
            return f.read()
    except Exception as e:
        print(f"ERROR: Failed to load guidance: {e}")
        sys.exit(1)


def load_report():
    """Load parsed report content."""
    try:
        with open('parsed_report.json') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Failed to load parsed report: {e}")
        sys.exit(1)


def get_criterion_guidance(guidance: str, criterion: dict) -> str:
    """Extract relevant guidance for this specific criterion."""
    criterion_name = criterion['name']
    criterion_id = criterion.get('id', '')

    guidance_lines = []
    guidance_lines.append("## Feedback Philosophy")
    guidance_lines.append("- Be specific and actionable")
    guidance_lines.append("- Start with strengths before improvements")
    guidance_lines.append("- Reference specific sections, figures, equations")
    guidance_lines.append("- Maintain encouraging, constructive tone\n")

    if 'common_issues' in criterion:
        guidance_lines.append(f"## Common Issues for '{criterion_name}':")
        for issue in criterion['common_issues']:
            guidance_lines.append(f"- {issue}")

    return "\n".join(guidance_lines)


def build_criterion_prompt(report: dict, criterion: dict, guidance_excerpt: str) -> str:
    """Build focused prompt for analyzing one criterion."""

    # Extract relevant sections using AI
    relevant_content = extract_sections_for_criterion_ai(report, criterion, model="gpt-4o-mini")

    # Format criterion details
    criterion_text = f"""### {criterion['name']} ({criterion['weight']}%)
{criterion['description']}

**Performance Levels:**
"""

    # Add level descriptions
    levels = criterion.get('levels', {})
    for level_name, level_info in levels.items():
        point_range = level_info.get('point_range', [0, 0])
        description = level_info.get('description', '')
        criterion_text += f"- **{level_name.title()}** ({point_range[0]}-{point_range[1]} points): {description}\n"

    # Build full prompt
    prompt = f"""You are an expert instructor providing feedback on a student report.

{guidance_excerpt}

## Your Task

Evaluate the following criterion based on the relevant sections extracted from the student's report:

{criterion_text}

## Report Sections Relevant to This Criterion

{relevant_content}

## Your Feedback

Provide feedback in this format:

### {criterion['name']}
**Assessment**: [Exemplary/Satisfactory/Developing/Unsatisfactory]

**Strengths:**
- [Specific strength with reference to section/figure/equation]
- [Another strength]

**Areas for Improvement:**
- [Specific, actionable suggestion]
- [Another suggestion with example]

**Suggested Rating**: [X/{criterion['weight']} points]

Keep feedback specific, constructive, and reference specific parts of the report.
"""

    return prompt


def analyze_criterion(report: dict, criterion: dict, guidance: str, model: str) -> dict:
    """Analyze a single criterion and return feedback."""

    criterion_name = criterion['name']
    print(f"\n📊 Analyzing: {criterion_name}")

    # Build prompt
    guidance_excerpt = get_criterion_guidance(guidance, criterion)
    prompt = build_criterion_prompt(report, criterion, guidance_excerpt)

    # Call API
    try:
        feedback = call_github_models_api(prompt, model)

        # Get token count estimate
        token_count = len(prompt.split()) * 1.3  # Rough estimate

        return {
            'criterion': criterion_name,
            'feedback': feedback,
            'success': True,
            'tokens_estimated': int(token_count)
        }

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return {
            'criterion': criterion_name,
            'feedback': f"Error analyzing this criterion: {e}",
            'success': False,
            'error': str(e)
        }


def call_github_models_api(prompt: str, model: str) -> str:
    """Call GitHub Models API with a prompt."""

    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable not set")

    endpoint = f"{API_BASE}/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are an expert instructor providing constructive, specific feedback on student technical reports."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }

    response = requests.post(endpoint, headers=headers, json=payload)
    response.raise_for_status()

    result = response.json()
    feedback = result['choices'][0]['message']['content']

    # Print token usage
    usage = result.get('usage', {})
    print(f"   ✅ Tokens: {usage.get('total_tokens', 0)} (prompt: {usage.get('prompt_tokens', 0)}, completion: {usage.get('completion_tokens', 0)})")

    return feedback


def main():
    """Generate AI feedback for all criteria."""
    print("\n" + "="*60)
    print("AI Feedback System")
    print("="*60)

    # Load everything
    config = load_config()
    rubric = load_rubric()
    guidance = load_guidance()
    report = load_report()

    model = config.get('model', {}).get('primary', 'gpt-4o')
    print(f"\nUsing model: {model}")

    # Get criteria
    criteria = rubric.get('criteria', [])
    print(f"Analyzing {len(criteria)} criteria...\n")

    # Analyze each criterion
    all_feedback = []
    total_tokens = 0

    for i, criterion in enumerate(criteria, 1):
        result = analyze_criterion(report, criterion, guidance, model)
        all_feedback.append(result)

        if result['success']:
            total_tokens += result.get('tokens_estimated', 0)

    # Combine feedback
    print("\n" + "="*60)
    print("COMBINED FEEDBACK")
    print("="*60 + "\n")

    combined = []
    combined.append(f"# Feedback on {rubric.get('assignment', {}).get('name', 'Report')}\n")

    for result in all_feedback:
        if result['success']:
            combined.append(result['feedback'])
            combined.append("\n---\n")

    combined_text = "\n".join(combined)
    print(combined_text)

    # Save feedback
    with open('feedback.md', 'w') as f:
        f.write(combined_text)

    print(f"\n✅ Feedback saved to feedback.md")
    print(f"📊 Total estimated tokens: {total_tokens}")
    print(f"📊 Average tokens per criterion: {total_tokens // len(criteria)}")
    print(f"✅ {len(all_feedback)} criteria analyzed")


if __name__ == '__main__':
    main()
