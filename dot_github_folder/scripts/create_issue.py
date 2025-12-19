#!/usr/bin/env python3
"""
Create GitHub issue with AI-generated feedback.
"""

import os
import json
import yaml
import requests
import sys
from datetime import datetime

# Load environment variables from .env file if it exists (for local testing)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available (e.g., in GitHub Actions), that's OK

def create_issue(title, body, label):
    """Create a GitHub issue using GitHub API."""
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("ERROR: GITHUB_TOKEN not found in environment")
        sys.exit(1)

    repo = os.environ.get('GITHUB_REPOSITORY')
    if not repo:
        print("ERROR: GITHUB_REPOSITORY not found in environment")
        print("This script should be run in GitHub Actions context")
        sys.exit(1)

    url = f"https://api.github.com/repos/{repo}/issues"

    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json',
        'X-GitHub-Api-Version': '2022-11-28'
    }

    data = {
        'title': title,
        'body': body,
        'labels': [label]
    }

    print(f"Creating issue in repository: {repo}")
    print(f"Issue title: {title}")

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()

        issue = response.json()
        return issue['html_url'], issue['number']

    except requests.exceptions.HTTPError as e:
        print(f"ERROR: Failed to create issue. HTTP {e.response.status_code}")
        print(f"Response: {e.response.text}")
        sys.exit(1)

    except requests.exceptions.RequestException as e:
        print(f"ERROR: Request failed: {e}")
        sys.exit(1)

def label_previous_issues(repo, token, current_issue_number):
    """Add 'superseded' label to previous feedback issues."""
    try:
        with open('.github/feedback/config.yml') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"WARNING: Could not load config for labeling: {e}")
        return

    if not config.get('label_previous_issues', False):
        return

    # Search for previous feedback issues
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

    params = {
        'labels': config.get('issue_label', 'ai-feedback'),
        'state': 'open'
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        issues = response.json()

        for issue in issues:
            if issue['number'] != current_issue_number:
                # Add superseded label
                label_url = f"https://api.github.com/repos/{repo}/issues/{issue['number']}/labels"
                label_data = {'labels': ['superseded']}
                requests.post(label_url, headers=headers, json=label_data, timeout=30)
                print(f"   Labeled issue #{issue['number']} as superseded")

    except Exception as e:
        print(f"WARNING: Failed to label previous issues: {e}")

def main():
    """Create feedback issue."""
    print("📝 Creating GitHub Issue with AI Feedback")
    print("=" * 50)

    # Load config
    try:
        with open('.github/feedback/config.yml') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Failed to load config: {e}")
        sys.exit(1)

    # Load feedback
    try:
        with open('feedback.md') as f:
            feedback_body = f.read()
    except Exception as e:
        print(f"ERROR: Failed to load feedback: {e}")
        sys.exit(1)

    # Load parsed report for stats
    try:
        with open('parsed_report.json') as f:
            report = json.load(f)
    except Exception as e:
        print(f"ERROR: Failed to load parsed report: {e}")
        sys.exit(1)

    # Get environment variables
    tag_name = os.environ.get('TAG_NAME', 'feedback')
    repo = os.environ.get('GITHUB_REPOSITORY')
    date = datetime.now().strftime('%Y-%m-%d')
    time = datetime.now().strftime('%H:%M:%S UTC')

    # Format title
    title = config.get('issue_title_template', '📋 Feedback: {tag_name} ({date})').format(
        tag_name=tag_name,
        date=date
    )

    # Construct full issue body
    model = config.get('model', {}).get('primary', 'gpt-4o')

    header = f"""## 🤖 AI Report Feedback

> **Requested**: `{tag_name}` • **Generated**: {date} at {time}
> **Model**: {model} • **Word count**: {report['stats']['word_count']}

---

"""

    # Construct resource URLs
    rubric_url = f"https://github.com/{repo}/blob/{tag_name}/.github/feedback/rubric.yml"
    guidance_url = f"https://github.com/{repo}/blob/{tag_name}/.github/feedback/guidance.md"

    footer = f"""

---

### 📚 Resources
- [View Rubric]({rubric_url}) - Grading criteria and performance levels
- [Feedback Guidelines]({guidance_url}) - How this feedback was generated

### 📋 Report Statistics
| Metric | Count |
|--------|-------|
| Words | {report['stats']['word_count']} |
| Code blocks | {report['stats']['code_blocks']} |
| Equations | {report['stats']['equations']} |
| Figures | {report['stats']['figures']} |
| Sections | {report['stats']['sections']} |

### 🔄 Request Updated Feedback
If you make improvements to your report, request new feedback:
```bash
git tag {tag_name.split('-')[0]}-v2  # or v3, v4, etc.
git push origin {tag_name.split('-')[0]}-v2
```

---

*🤖 Powered by [GitHub Models](https://github.com/features/models) ({model})*
*This feedback is AI-generated and should be used as guidance. Your instructor makes final grading decisions.*
"""

    full_body = header + feedback_body + footer

    # Create issue
    issue_url, issue_number = create_issue(
        title=title,
        body=full_body,
        label=config.get('issue_label', 'ai-feedback')
    )

    print(f"✅ Feedback issue created successfully!")
    print(f"   URL: {issue_url}")
    print(f"   Issue #{issue_number}")

    # Label previous issues if configured
    token = os.environ.get('GITHUB_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    if token and repo:
        print(f"\n🏷️  Checking for previous feedback issues...")
        label_previous_issues(repo, token, issue_number)

    print("\n✨ Done! Students can now view their feedback.")

if __name__ == '__main__':
    main()
