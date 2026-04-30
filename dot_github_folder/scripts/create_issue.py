#!/usr/bin/env python3
"""
Create GitHub issue with AI-generated feedback from structured JSON.
"""

import os
import json
import yaml
import requests
import sys
from datetime import datetime

def create_github_issue(title: str, body: str, label: str):
    """Create a GitHub issue using the API."""
    token = os.environ.get('GITHUB_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    if not token or not repo:
        print("ERROR: GITHUB_TOKEN and GITHUB_REPOSITORY must be set for API calls.", file=sys.stderr)
        sys.exit(1)

    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github.v3+json'}
    data = {'title': title, 'body': body, 'labels': [label]}

    print(f"Creating issue in repository: {repo}...")
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        issue = response.json()
        print(f"✅ Feedback issue created successfully: {issue['html_url']}")
        return issue['html_url'], issue['number']
    except requests.exceptions.HTTPError as e:
        print(f"ERROR: Failed to create issue. HTTP {e.response.status_code}", file=sys.stderr)
        print(f"Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)

def _bar(pct: float, width: int = 20) -> str:
    filled = round(pct / 100 * width)
    return '█' * filled + '░' * (width - filled)


def format_organization_section(org_item: dict) -> str:
    """Render the __organization__ entry as a markdown section."""
    feedback = org_item.get('feedback', {})
    summary = feedback.get('summary', '')
    coverage = feedback.get('coverage', [])
    high_overlap = feedback.get('high_overlap', [])
    report_words = feedback.get('report_words', 0)

    parts = [
        '### 📐 Report Organization\n',
        f'> {summary}\n' if summary else '',
    ]

    if coverage:
        parts.append('\n**Rubric coverage** (fraction of report content found for each criterion):\n')
        parts.append('| Criterion | Coverage | Words |')
        parts.append('|-----------|----------|-------|')
        for row in coverage:
            name = row.get('criterion', '')
            pct = row.get('coverage_pct', 0)
            words = row.get('words', 0)
            bar = _bar(pct)
            flag = ' ⚠' if pct < 5 else ''
            parts.append(f'| {name} | `{bar}` {pct:.0f}%{flag} | {words} |')
        if report_words:
            parts.append(f'\n*Full report: {report_words} words.*')

    if high_overlap:
        parts.append('\n**Sections with blended content** (high Jaccard overlap between criteria):\n')
        for row in high_overlap:
            a = row.get('criterion_a', '')
            b = row.get('criterion_b', '')
            j = row.get('jaccard', 0)
            parts.append(f'- *{a}* ↔ *{b}*: {j:.0%} overlap')

    parts.append('\n---\n')
    return '\n'.join(p for p in parts if p is not None)


def format_feedback_body(feedback_data: list, rubric_data: dict, config: dict) -> str:
    """Formats the list of JSON feedback objects into a Markdown string."""
    body_parts = []
    rubric_criteria = {c['id']: c for c in rubric_data.get('criteria', [])}

    # Check if numerical scoring is enabled (defaults to false for formative assessment)
    # Env var SCORING_ENABLED overrides config (for batch/local runs)
    scoring_env = os.environ.get('SCORING_ENABLED')
    if scoring_env is not None:
        scoring_enabled = scoring_env.lower() in ('true', '1', 'yes')
    else:
        scoring_enabled = config.get('feedback', {}).get('scoring_enabled', False)

    for item in feedback_data:
        criterion_name = item.get('criterion', 'Unknown Criterion')

        # Render organization section before per-criterion feedback
        if criterion_name == '__organization__':
            body_parts.append(format_organization_section(item))
            continue
        body_parts.append(f"### {criterion_name}\n")

        if not item.get('success', False):
            body_parts.append(f"**Error generating feedback:**\n`{item.get('error', 'No details available.')}`\n\n---\n")
            continue

        raw_feedback = item.get('feedback', {})
        feedback = {}

        # Standardize the feedback object, whether it's a string or dict.
        if isinstance(raw_feedback, str):
            try:
                feedback = json.loads(raw_feedback)
            except json.JSONDecodeError:
                body_parts.append(f"**Could not parse AI feedback.**\n\n---\n")
                continue
        elif isinstance(raw_feedback, dict):
            feedback = raw_feedback

        # The AI sometimes nests the actual feedback dict inside a "feedback" key.
        if 'feedback' in feedback and isinstance(feedback['feedback'], dict):
            feedback = feedback['feedback']

        # The AI sometimes nests the actual feedback dict inside a "summary" key.
        # If so, we use the nested dict as our main feedback object.
        if 'summary' in feedback and isinstance(feedback['summary'], dict):
            feedback = feedback['summary']

        rubric_criterion = next((c for c in rubric_criteria.values() if c['name'] == criterion_name), {})
        max_score = rubric_criterion.get('weight', 0)

        level = feedback.get('overall_assessment') or feedback.get('level') or feedback.get('overall_evaluation', 'N/A')

        body_parts.append(f"**Assessment:** `{level}`")

        # Only display numerical score if scoring is enabled
        if scoring_enabled:
            score = feedback.get('score', 'N/A')
            body_parts.append(f"**Score:** `{score} / {max_score}`\n")
        else:
            body_parts.append("")  # Add blank line for spacing

        summary_text = feedback.get('summary') or feedback.get('comments') or feedback.get('feedback') or feedback.get('justification')
        if summary_text and isinstance(summary_text, str):
             body_parts.append(f"> {summary_text}\n")

        def format_list(title, points):
            if not points: return []
            lines = [f"**{title}:**"]
            for point in points:
                if isinstance(point, dict):
                    lines.append(f"- **{point.get('issue', 'Suggestion')}:** {point.get('suggestion', '')}")
                else:
                    lines.append(f"- {point}")
            lines.append("")
            return lines

        body_parts.extend(format_list("Strengths", feedback.get('strengths') or feedback.get('positive')))
        body_parts.extend(format_list("Areas for Improvement", feedback.get('areas_for_improvement') or feedback.get('negative')))
        body_parts.extend(format_list("Image-specific Feedback", feedback.get('image_feedback')))
        body_parts.extend(format_list("Actionable Suggestions", feedback.get('actionable_suggestions')))

        body_parts.append("\n---\n")
        
    return "\n".join(body_parts)

def build_issue_footer(report_stats: dict, config: dict) -> str:
    repo = os.environ.get('GITHUB_REPOSITORY', 'test/repo')
    tag_name = os.environ.get('TAG_NAME', 'local-test')
    model = config.get('model', {}).get('primary', 'gpt-4o')

    # Prefer linking to RUBRIC.md if it exists (more readable for students)
    if os.path.exists('.github/feedback/RUBRIC.md'):
        rubric_file = 'RUBRIC.md'
    else:
        rubric_file = 'rubric.yml'

    rubric_url = f"https://github.com/{repo}/blob/{tag_name}/.github/feedback/{rubric_file}"
    stats_table = f"| Metric | Count |\n|--------|-------|\n| Words | {report_stats.get('word_count', 0)} |\n| Figures | {report_stats.get('figures', 0)} |"
    return f"\n### 📚 Resources\n- [View Rubric]({rubric_url})\n\n### 📋 Report Statistics\n{stats_table}\n\n---\n*🤖 Powered by [GitHub Models](https://github.com/features/models) ({model}).*"

def save_feedback_to_file(feedback_body: str, footer: str, config: dict, output_path: str):
    """Save feedback to a flat file instead of creating a GitHub issue."""
    tag_name = os.environ.get('TAG_NAME', 'feedback')
    date = datetime.now().strftime('%Y-%m-%d')
    time = datetime.now().strftime('%H:%M:%S UTC')
    model = config.get('model', {}).get('primary', 'gpt-4o')

    header = f"## 🤖 AI Report Feedback\n> **Requested**: `{tag_name}` • **Generated**: {date} at {time}\n> **Model**: {model}\n\n---\n\n"
    full_body = header + feedback_body + footer

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_body)
        print(f"✅ Feedback saved to: {output_path}")
        return output_path
    except IOError as e:
        print(f"ERROR: Failed to save feedback to file: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    """Load feedback JSON, format it, and create a GitHub issue or save to file."""
    is_local_test = os.environ.get('LOCAL_TEST', 'false').lower() == 'true'
    output_format = os.environ.get('OUTPUT_FORMAT', 'github_issue').lower()
    output_path = os.environ.get('OUTPUT_PATH', 'feedback-output.md')

    try:
        with open('.github/config.yml', 'r', encoding='utf-8') as f: config = yaml.safe_load(f)
        with open('feedback.json', 'r', encoding='utf-8') as f: feedback_data = json.load(f)
        with open('parsed_report.json', 'r', encoding='utf-8') as f: report_data = json.load(f)
        with open('.github/feedback/rubric.yml', 'r', encoding='utf-8') as f: rubric_data = yaml.safe_load(f)
    except FileNotFoundError as e:
        print(f"ERROR: Missing required file: {e.filename}", file=sys.stderr)
        sys.exit(1)

    feedback_body = format_feedback_body(feedback_data, rubric_data, config)
    footer = build_issue_footer(report_data.get('stats', {}), config)

    # Check config file for output settings (takes precedence over env vars)
    output_config = config.get('output', {})
    if output_config.get('format'):
        output_format = output_config.get('format')
    if output_config.get('path'):
        output_path = output_config.get('path')

    if is_local_test or output_format == 'flat_file' or output_format == 'markdown_file':
        tag_name = os.environ.get('TAG_NAME', 'feedback')
        date = datetime.now().strftime('%Y-%m-%d')
        time = datetime.now().strftime('%H:%M:%S UTC')
        model = config.get('model', {}).get('primary', 'gpt-4o')

        header = f"## 🤖 AI Report Feedback\n> **Requested**: `{tag_name}` • **Generated**: {date} at {time}\n> **Model**: {model}\n\n---\n\n"
        full_body = header + feedback_body + footer

        if is_local_test:
            # Just print to console for quick testing
            print("--- LOCAL TEST: ISSUE BODY PREVIEW ---")
            print(full_body)
            print("--- END PREVIEW ---")
        else:
            # Save to file
            save_feedback_to_file(feedback_body, footer, config, output_path)
            print("\n✨ Done! Feedback saved to file.")
    else:
        # Create GitHub issue (default behavior)
        tag_name = os.environ.get('TAG_NAME', 'feedback')
        date = datetime.now().strftime('%Y-%m-%d')
        title = config.get('issue_title_template', '📋 Feedback: {tag_name} ({date})').format(tag_name=tag_name, date=date)

        time = datetime.now().strftime('%H:%M:%S UTC')
        model = config.get('model', {}).get('primary', 'gpt-4o')
        header = f"## 🤖 AI Report Feedback\n> **Requested**: `{tag_name}` • **Generated**: {date} at {time}\n> **Model**: {model}\n\n---\n\n"

        full_body = header + feedback_body + footer

        create_github_issue(title, full_body, config.get('issue_label', 'ai-feedback'))
        print("\n✨ Done! Students can now view their feedback.")

if __name__ == '__main__':
    main()

