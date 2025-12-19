#!/usr/bin/env python3
"""
GitHub Models API integration for AI-powered report feedback.
Uses GITHUB_TOKEN for authentication (no API keys needed).
"""

import os
import json
import yaml
import requests
import sys
from pathlib import Path

# Load environment variables from .env file if it exists (for local testing)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available (e.g., in GitHub Actions), that's OK

# GitHub Models API endpoint (OpenAI-compatible)
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

def format_rubric_for_prompt(rubric):
    """Convert rubric YAML to readable text for AI."""
    output = []

    for section_name, section_data in rubric.items():
        if section_name in ['course', 'semester', 'type']:
            continue

        if section_name == 'final_project':
            # Final project uses references to other criteria
            output.append(f"## {section_name.upper().replace('_', ' ')}")
            output.append(f"Total Points: {section_data['total_points']}")
            output.append(f"Description: {section_data.get('description', '')}\n")
            continue

        output.append(f"## {section_name.upper()}")
        output.append(f"Total Points: {section_data['total_points']}\n")

        for criterion in section_data['criteria']:
            output.append(f"### {criterion['name']} ({criterion['weight']}%)")

            if 'abet_outcome' in criterion:
                output.append(f"ABET Outcome: {criterion['abet_outcome']}")

            output.append(f"{criterion['description']}\n")

            # Only show levels if they exist (not a reference)
            if 'levels' in criterion:
                output.append("**Performance Levels:**")
                for level_name, level_data in criterion['levels'].items():
                    points = level_data['point_range']
                    output.append(f"- **{level_name.title()}** ({points[0]}-{points[1]} pts): {level_data['description']}")

            if 'keywords' in criterion:
                output.append(f"\n**Key concepts to look for**: {', '.join(criterion['keywords'])}")

            if 'artifacts' in criterion:
                output.append(f"\n**Expected artifacts**: {', '.join(criterion['artifacts'])}")

            if 'common_issues' in criterion:
                output.append("\n**Common student mistakes to watch for:**")
                for issue in criterion['common_issues']:
                    output.append(f"  - {issue}")

            output.append("")

    return "\n".join(output)

def truncate_report_if_needed(report_content, max_tokens=7000):
    """
    Truncate report if it's too long for the API.
    Uses smart truncation to keep structure.
    """
    # Rough estimate: 1 token ≈ 4 characters
    estimated_tokens = len(report_content) / 4

    if estimated_tokens <= max_tokens:
        return report_content, False

    print(f"⚠️  Report is long (~{int(estimated_tokens)} tokens). Truncating to fit {max_tokens} token budget...")

    # Keep first part (usually has important structure)
    max_chars = max_tokens * 4
    truncated = report_content[:max_chars]

    # Try to cut at a reasonable boundary (paragraph or section)
    last_paragraph = truncated.rfind('\n\n')
    if last_paragraph > max_chars * 0.8:  # If we can keep 80%+ by cutting at paragraph
        truncated = truncated[:last_paragraph]

    truncated += "\n\n[... Report truncated for length. Analysis based on first ~{} words ...]".format(
        len(truncated.split())
    )

    return truncated, True

def construct_prompt(report, rubric, guidance, config):
    """Build the complete prompt for AI analysis."""
    rubric_text = format_rubric_for_prompt(rubric)

    # Truncate report if needed
    # Reserve tokens for rubric + guidance + prompt structure
    max_tokens = config.get('max_input_tokens', 15000)
    reserved_tokens = min(3500, max_tokens // 3)  # Reserve up to 1/3 for overhead
    report_content, was_truncated = truncate_report_if_needed(
        report['content'],
        max_tokens=max_tokens - reserved_tokens
    )

    prompt = f"""You are an experienced engineering instructor providing feedback on a student lab report for {rubric.get('course', 'EENG 320')}.

## RUBRIC
{rubric_text}

## GUIDANCE
{guidance}

## STUDENT REPORT
{report_content}

## REPORT STATISTICS
- Word count: {report['stats']['word_count']}
- Code blocks: {report['stats']['code_blocks']}
- Equations: {report['stats']['equations']}
- Figures: {report['stats']['figures']}
- Sections: {report['stats']['sections']}

## TASK
Analyze the report against each rubric criterion. For each criterion:
1. Assess performance level (Exemplary/Satisfactory/Developing/Unsatisfactory)
2. Provide specific, actionable feedback with section/figure references
3. Highlight strengths (what's working well)
4. Identify areas for improvement (specific, actionable suggestions)
5. Suggest a point value based on the rubric levels

Format your response as structured markdown suitable for a GitHub Issue.
Use this structure for EACH criterion:

### 1️⃣ [Criterion Name] ([Weight]%)
**Assessment**: [✅/⚠️/❌] **[Level]**

**Strengths**:
- [specific good things with references to sections/figures]

**Areas for Improvement**:
- [specific actionable suggestions]

**Suggested Rating**: [X]/[Y] points

---

After analyzing all criteria, provide:
- **Overall Assessment Summary** (2-3 sentences)
- **Top 3-5 Action Items** (prioritized, specific, actionable)
- **Encouraging Note** (positive reinforcement, acknowledge effort)

IMPORTANT:
- Be specific with references (section names, figure numbers, line areas)
- Balance criticism with positive reinforcement
- Focus on learning and improvement, not just pointing out flaws
- Provide actionable next steps, not just identification of problems
- Maintain an encouraging, supportive tone
"""

    if was_truncated:
        prompt += "\n\nNOTE: The report was truncated due to length. Focus analysis on the content provided."

    return prompt

def call_github_models(prompt, model="gpt-4o", max_tokens=3000):
    """Call GitHub Models API using GITHUB_TOKEN."""
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("ERROR: GITHUB_TOKEN not found in environment")
        sys.exit(1)

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    data = {
        'model': model,
        'messages': [
            {
                'role': 'system',
                'content': 'You are an experienced electrical engineering instructor providing constructive, encouraging feedback on student lab reports. Focus on helping students learn and improve.'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ],
        'max_tokens': max_tokens,
        'temperature': 0.7
    }

    print(f"Calling GitHub Models API with model: {model}")
    print(f"Request size: ~{len(prompt)/4:.0f} tokens")

    try:
        response = requests.post(
            f"{API_BASE}/chat/completions",
            headers=headers,
            json=data,
            timeout=120
        )

        response.raise_for_status()
        result = response.json()

        if 'choices' not in result or len(result['choices']) == 0:
            print(f"ERROR: Unexpected API response format: {result}")
            sys.exit(1)

        return result['choices'][0]['message']['content']

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print(f"ERROR: Rate limited by GitHub Models API. Try again in a few minutes.")
            print(f"Response: {e.response.text}")
        elif e.response.status_code == 401:
            print(f"ERROR: Authentication failed. GITHUB_TOKEN may not have models access.")
            print(f"Response: {e.response.text}")
        else:
            print(f"ERROR: HTTP error {e.response.status_code}: {e.response.text}")
        sys.exit(1)

    except requests.exceptions.Timeout:
        print(f"ERROR: API request timed out after 120 seconds")
        sys.exit(1)

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Request failed: {e}")
        sys.exit(1)

def main():
    """Main execution function."""
    print("🤖 AI Feedback Generator for EENG 320")
    print("=" * 50)

    print("\n📖 Loading configuration...")
    config = load_config()
    rubric = load_rubric()
    guidance = load_guidance()
    report = load_report()

    print(f"\n🔧 Configuration:")
    print(f"   - Primary model: {config['model']['primary']}")
    print(f"   - Fallback model: {config['model']['fallback']}")
    print(f"   - Max input tokens: {config.get('max_input_tokens', 7000)}")

    print(f"\n🤖 Generating feedback using {config['model']['primary']}...")
    prompt = construct_prompt(report, rubric, guidance, config)

    try:
        feedback = call_github_models(
            prompt,
            model=config['model']['primary'],
            max_tokens=config.get('max_output_tokens', 3000)
        )
        print("✅ Feedback generated successfully!")

    except Exception as e:
        print(f"\n⚠️  Primary model failed, trying fallback model {config['model']['fallback']}...")
        try:
            feedback = call_github_models(
                prompt,
                model=config['model']['fallback'],
                max_tokens=config.get('max_output_tokens', 3000)
            )
            print("✅ Feedback generated successfully with fallback model!")
        except Exception as e2:
            print(f"ERROR: Both models failed. {e2}")
            sys.exit(1)

    # Save feedback for issue creation
    try:
        with open('feedback.md', 'w') as f:
            f.write(feedback)
        print(f"💾 Feedback saved to feedback.md ({len(feedback)} characters)")
    except Exception as e:
        print(f"ERROR: Failed to save feedback: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
