#!/usr/bin/env python3
"""
Criterion-based AI feedback using GitHub Models API.
Analyzes each rubric criterion separately for better quality and no truncation.
"""

import os
import json
import yaml
import requests
import sys
import concurrent.futures
from pathlib import Path
from section_extractor import extract_sections_for_criterion

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
    # For now, return condensed version focusing on this criterion
    criterion_name = criterion['name']
    criterion_id = criterion.get('id', '')

    # Extract relevant parts of guidance
    guidance_lines = []

    # Add general philosophy
    guidance_lines.append("## Feedback Philosophy")
    guidance_lines.append("- Be specific and actionable")
    guidance_lines.append("- Start with strengths before improvements")
    guidance_lines.append("- Reference specific sections, figures, equations")
    guidance_lines.append("- Maintain encouraging, constructive tone\n")

    # Add criterion-specific common mistakes
    if 'common_issues' in criterion:
        guidance_lines.append(f"## Common Issues for '{criterion_name}':")
        for issue in criterion['common_issues']:
            guidance_lines.append(f"- {issue}")

    return "\n".join(guidance_lines)


def build_criterion_prompt(report: dict, criterion: dict, guidance_excerpt: str) -> str:
    """Build focused prompt for analyzing one criterion."""

    # Extract relevant sections for this criterion
    relevant_content = extract_sections_for_criterion(report, criterion)

    # Format criterion details
    criterion_text = f"""### {criterion['name']} ({criterion['weight']}%)
{criterion['description']}

**Performance Levels:**"""

    if 'levels' in criterion:
        for level_name, level_data in criterion['levels'].items():
            points = level_data['point_range']
            criterion_text += f"\n- **{level_name.title()}** ({points[0]}-{points[1]} pts): {level_data['description']}"

    if 'keywords' in criterion:
        criterion_text += f"\n\n**Key concepts**: {', '.join(criterion['keywords'])}"

    # Build focused prompt
    prompt = f"""You are an experienced engineering instructor providing feedback on ONE SPECIFIC CRITERION of a student lab report.

## CRITERION TO ANALYZE
{criterion_text}

## GUIDANCE FOR THIS CRITERION
{guidance_excerpt}

## RELEVANT REPORT SECTIONS
{relevant_content}

## YOUR TASK
Analyze ONLY this criterion. Provide:

1. **Assessment**: Choose performance level (Exemplary/Satisfactory/Developing/Unsatisfactory)

2. **Strengths** (2-4 specific points):
   - What did the student do well for THIS criterion?
   - Reference specific sections, figures, or equations

3. **Areas for Improvement** (2-4 specific suggestions):
   - What's missing or could be better?
   - Give actionable, concrete suggestions
   - Reference where improvements should go

4. **Suggested Rating**: Recommend points (X/{criterion['weight']} points)

Format as:
### {criterion['name']} ({criterion['weight']}%)
**Assessment**: [✅/⚠️/❌] **[Level]**

**Strengths**:
- [specific strength 1]
- [specific strength 2]

**Areas for Improvement**:
- [specific actionable suggestion 1]
- [specific actionable suggestion 2]

**Suggested Rating**: [X]/{criterion['weight']} points

Be specific, constructive, and encouraging. Focus on THIS criterion only."""

    return prompt


def call_github_models(prompt: str, model: str = "gpt-4o", max_tokens: int = 1500) -> str:
    """Call GitHub Models API."""
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
                'content': 'You are an experienced engineering instructor providing focused, constructive feedback.'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ],
        'max_tokens': max_tokens,
        'temperature': 0.7
    }

    try:
        response = requests.post(
            f"{API_BASE}/chat/completions",
            headers=headers,
            json=data,
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']

    except requests.exceptions.HTTPError as e:
        print(f"ERROR: HTTP {e.response.status_code}: {e.response.text}")
        raise
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Request failed: {e}")
        raise


def analyze_criterion(report: dict, criterion: dict, guidance: str, config: dict) -> dict:
    """Analyze a single criterion."""
    print(f"   Analyzing: {criterion['name']} ({criterion['weight']}%)")

    # Build focused prompt
    guidance_excerpt = get_criterion_guidance(guidance, criterion)
    prompt = build_criterion_prompt(report, criterion, guidance_excerpt)

    # Estimate tokens (rough)
    estimated_tokens = len(prompt) // 4
    print(f"      Prompt size: ~{estimated_tokens} tokens")

    # Call API
    try:
        feedback = call_github_models(
            prompt,
            model=config['model']['primary'],
            max_tokens=1500
        )
        print(f"      ✅ Complete")
        return {
            'criterion': criterion,
            'feedback': feedback,
            'success': True
        }
    except Exception as e:
        print(f"      ❌ Failed: {e}")
        return {
            'criterion': criterion,
            'feedback': f"Error analyzing this criterion: {str(e)}",
            'success': False
        }


def combine_feedback(results: list, rubric: dict, report: dict) -> str:
    """Combine individual criterion feedback into complete report."""

    sections = []

    # Header
    assignment_info = rubric.get('assignment', {})
    course = assignment_info.get('course', 'Course')
    assignment_name = assignment_info.get('name', 'Assignment')
    sections.append(f"# AI Feedback Report\n")
    sections.append(f"**Course**: {course}  \n")
    sections.append(f"**Assignment**: {assignment_name}\n\n")

    # Criterion feedback
    sections.append("## Detailed Feedback by Criterion\n")
    for i, result in enumerate(results, 1):
        sections.append(f"{i}. {result['feedback']}\n")
        sections.append("---\n")

    # Overall summary
    sections.append("## Overall Assessment\n")
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    sections.append(f"**Criteria Analyzed**: {len(successful)}/{len(results)}\n")

    if failed:
        sections.append(f"**Note**: {len(failed)} criteria could not be analyzed due to errors.\n")

    # Add summary statistics
    sections.append(f"\n**Report Statistics**:")
    sections.append(f"- Words: {report['stats']['word_count']}")
    sections.append(f"- Code blocks: {report['stats']['code_blocks']}")
    sections.append(f"- Equations: {report['stats']['equations']}")
    sections.append(f"- Figures: {report['stats']['figures']}")
    sections.append(f"- Sections: {report['stats']['sections']}\n")

    # Encouragement
    sections.append("---\n")
    sections.append("### Final Note\n")
    sections.append("This feedback was generated by analyzing each rubric criterion individually. ")
    sections.append("Review the specific suggestions for each criterion and use them to strengthen your report. ")
    sections.append("Great work on completing this lab!")

    return "\n".join(sections)


def main():
    """Main execution - criterion-based analysis."""
    print("🤖 Criterion-Based AI Feedback Generator")
    print("=" * 60)

    # Load configuration
    print("\n📖 Loading configuration...")
    config = load_config()
    rubric = load_rubric()
    guidance = load_guidance()
    report = load_report()

    print(f"\n🔧 Configuration:")
    print(f"   - Model: {config['model']['primary']}")
    print(f"   - Strategy: Analyze each criterion separately")

    # Collect criteria to analyze from simplified rubric format
    criteria = rubric.get('criteria', [])

    print(f"\n📊 Found {len(criteria)} criteria to analyze")
    print(f"   Estimated API calls: {len(criteria)}")
    print(f"   (Note: Enterprise/Education accounts have 5,000 req/hour limit)")
    print(f"   (See .github/feedback/GITHUB_MODELS_SETTINGS.md for details)\n")

    # Analyze each criterion in parallel
    print("🔍 Analyzing criteria in parallel...\n")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # Create a future for each criterion analysis
        future_to_criterion = {executor.submit(analyze_criterion, report, c, guidance, config): c for c in criteria}

        for i, future in enumerate(concurrent.futures.as_completed(future_to_criterion), 1):
            criterion = future_to_criterion[future]
            try:
                result = future.result()
                results.append(result)
                # The print statement from analyze_criterion handles the output
            except Exception as exc:
                print(f"      ❌ Error analyzing {criterion['name']}: {exc}")
                results.append({
                    'criterion': criterion,
                    'feedback': f"Error analyzing this criterion: {str(exc)}",
                    'success': False
                })
    print() # Newline after all criteria are processed

    # Combine results
    print("\n📝 Combining feedback...")
    final_feedback = combine_feedback(results, rubric, report)

    # Save
    try:
        with open('feedback.md', 'w') as f:
            f.write(final_feedback)
        print(f"✅ Feedback saved to feedback.md ({len(final_feedback)} characters)")

        # Show summary
        successful = [r for r in results if r['success']]
        print(f"\n✨ Analysis complete!")
        print(f"   - {len(successful)}/{len(results)} criteria analyzed successfully")
        print(f"   - Total feedback length: {len(final_feedback)} characters")

    except Exception as e:
        print(f"ERROR: Failed to save feedback: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
