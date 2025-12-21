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
from datetime import datetime
from section_extractor import extract_sections_for_criterion_ai

# Load environment variables from .env file if it exists (for local testing)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# GitHub Models API endpoint
API_BASE = "https://models.inference.ai.azure.com"

# Global debug configuration (set in main())
DEBUG_CONFIG = None
DEBUG_SESSION_DIR = None


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


def init_debug_mode(config: dict):
    """Initialize debug mode if enabled."""
    global DEBUG_CONFIG, DEBUG_SESSION_DIR

    debug_mode = config.get('debug_mode', {})
    if not debug_mode.get('enabled', False):
        DEBUG_CONFIG = None
        DEBUG_SESSION_DIR = None
        return

    DEBUG_CONFIG = debug_mode

    # Create session directory with timestamp
    output_dir = Path(debug_mode.get('output_dir', '.github/debug'))
    timestamp_format = debug_mode.get('timestamp_format', '%Y%m%d_%H%M%S')
    timestamp = datetime.now().strftime(timestamp_format)

    # Include tag name if available
    tag_name = os.environ.get('TAG_NAME', 'manual-run')
    session_name = f"{timestamp}_{tag_name}"

    DEBUG_SESSION_DIR = output_dir / session_name
    DEBUG_SESSION_DIR.mkdir(parents=True, exist_ok=True)

    # Create symlink to latest
    latest_link = output_dir / "latest"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    try:
        latest_link.symlink_to(session_name)
    except OSError:
        pass  # Symlinks may not work on all systems

    print(f"🐛 Debug mode enabled. Output: {DEBUG_SESSION_DIR}")


def save_debug_session_info(config: dict, rubric: dict, report: dict, start_time: float, end_time: float, all_feedback: list):
    """Save overall session metadata."""
    if not DEBUG_CONFIG or not DEBUG_CONFIG.get('save_api_metadata', False):
        return

    total_criteria = len(all_feedback)
    successful_criteria = sum(1 for f in all_feedback if f.get('success', False))
    total_tokens_prompt = sum(f.get('tokens', {}).get('prompt_tokens', 0) for f in all_feedback if f.get('success', False))
    total_tokens_completion = sum(f.get('tokens', {}).get('completion_tokens', 0) for f in all_feedback if f.get('success', False))
    total_tokens = total_tokens_prompt + total_tokens_completion

    session_info = {
        "timestamp": datetime.now().isoformat(),
        "tag_name": os.environ.get('TAG_NAME', 'manual-run'),
        "model_primary": config.get('model', {}).get('primary', 'unknown'),
        "model_fallback": config.get('model', {}).get('fallback', 'unknown'),
        "total_criteria": total_criteria,
        "successful_criteria": successful_criteria,
        "failed_criteria": total_criteria - successful_criteria,
        "total_time_seconds": round(end_time - start_time, 2),
        "total_api_calls": successful_criteria,
        "total_tokens_prompt": total_tokens_prompt,
        "total_tokens_completion": total_tokens_completion,
        "total_tokens": total_tokens,
        "report_file": config.get('report_file', config.get('report', {}).get('filename', 'unknown')),
        "report_word_count": len(str(report).split()),
    }

    session_file = DEBUG_SESSION_DIR / "session_info.json"
    with open(session_file, 'w') as f:
        if DEBUG_CONFIG.get('prettify_json', True):
            json.dump(session_info, f, indent=2)
        else:
            json.dump(session_info, f)

    print(f"🐛 Session info saved: {session_file.name}")


def save_debug_criterion_data(criterion_id: str, criterion_name: str, context: str,
                               prompt: str, request_payload: dict, response_data: dict,
                               feedback: str, metadata: dict):
    """Save debug data for a single criterion analysis."""
    if not DEBUG_CONFIG:
        return

    # Create criterion directory
    criterion_dir = DEBUG_SESSION_DIR / "criteria" / f"{metadata.get('criterion_index', 0):02d}_{criterion_id}"
    criterion_dir.mkdir(parents=True, exist_ok=True)

    # Save context
    if DEBUG_CONFIG.get('save_context', False):
        context_file = criterion_dir / "context.txt"
        with open(context_file, 'w') as f:
            f.write(context)

    # Save prompt
    if DEBUG_CONFIG.get('save_prompts', False):
        prompt_file = criterion_dir / "prompt.txt"
        with open(prompt_file, 'w') as f:
            f.write(prompt)

        # Save request payload (with filtered auth token)
        request_file = criterion_dir / "request.json"
        # Deep copy to avoid modifying original
        filtered_payload = json.loads(json.dumps(request_payload))
        # Don't save the actual request since headers contain token
        # Just save the payload
        with open(request_file, 'w') as f:
            if DEBUG_CONFIG.get('prettify_json', True):
                json.dump(filtered_payload, f, indent=2)
            else:
                json.dump(filtered_payload, f)

    # Save response
    if DEBUG_CONFIG.get('save_responses', False):
        response_file = criterion_dir / "response.json"
        with open(response_file, 'w') as f:
            if DEBUG_CONFIG.get('prettify_json', True):
                json.dump(response_data, f, indent=2)
            else:
                json.dump(response_data, f)

        feedback_file = criterion_dir / "feedback.md"
        with open(feedback_file, 'w') as f:
            f.write(feedback)

    # Save metadata
    if DEBUG_CONFIG.get('save_api_metadata', False):
        metadata_file = criterion_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            if DEBUG_CONFIG.get('prettify_json', True):
                json.dump(metadata, f, indent=2)
            else:
                json.dump(metadata, f)


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


def build_criterion_prompt(report: dict, criterion: dict, guidance_excerpt: str) -> tuple:
    """Build focused prompt for analyzing one criterion.

    Returns:
        tuple: (prompt, context) where context is the extracted sections
    """

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

    return prompt, relevant_content


def analyze_criterion(report: dict, criterion: dict, guidance: str, model: str, criterion_index: int = 0) -> dict:
    """Analyze a single criterion and return feedback."""

    criterion_name = criterion['name']
    criterion_id = criterion.get('id', f'criterion_{criterion_index}')
    print(f"\n📊 Analyzing: {criterion_name}")

    # Build prompt and get context
    guidance_excerpt = get_criterion_guidance(guidance, criterion)
    prompt, context = build_criterion_prompt(report, criterion, guidance_excerpt)

    # Call API
    try:
        start_time = datetime.now().timestamp()
        feedback, response_data, request_payload = call_github_models_api(prompt, model)
        end_time = datetime.now().timestamp()

        # Get actual token usage from response
        usage = response_data.get('usage', {})
        tokens = {
            'prompt_tokens': usage.get('prompt_tokens', 0),
            'completion_tokens': usage.get('completion_tokens', 0),
            'total_tokens': usage.get('total_tokens', 0)
        }

        # Save debug info
        metadata = {
            "criterion_id": criterion_id,
            "criterion_name": criterion_name,
            "criterion_index": criterion_index,
            "timestamp": datetime.now().isoformat(),
            "model_used": model,
            "api_endpoint": f"{API_BASE}/chat/completions",
            "request_time_seconds": round(end_time - start_time, 2),
            "tokens": tokens,
            "success": True,
            "error": None,
            "context_word_count": len(context.split()),
            "context_estimated_tokens": int(len(context.split()) * 1.3),
        }

        save_debug_criterion_data(
            criterion_id, criterion_name, context,
            prompt, request_payload, response_data,
            feedback, metadata
        )

        return {
            'criterion': criterion_name,
            'feedback': feedback,
            'success': True,
            'tokens': tokens
        }

    except Exception as e:
        print(f"   ❌ Failed: {e}")

        # Save debug info for failure
        metadata = {
            "criterion_id": criterion_id,
            "criterion_name": criterion_name,
            "criterion_index": criterion_index,
            "timestamp": datetime.now().isoformat(),
            "model_used": model,
            "success": False,
            "error": str(e),
        }

        save_debug_criterion_data(
            criterion_id, criterion_name, context if 'context' in locals() else '',
            prompt if 'prompt' in locals() else '', {}, {},
            f"Error: {e}", metadata
        )

        return {
            'criterion': criterion_name,
            'feedback': f"Error analyzing this criterion: {e}",
            'success': False,
            'error': str(e),
            'tokens': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
        }


def call_github_models_api(prompt: str, model: str) -> tuple:
    """Call GitHub Models API with a prompt.

    Returns:
        tuple: (feedback_text, response_data, request_payload)
    """

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

    return feedback, result, payload


def main():
    """Generate AI feedback for all criteria."""
    start_time = datetime.now().timestamp()

    print("\n" + "="*60)
    print("AI Feedback System")
    print("="*60)

    # Load everything
    config = load_config()
    rubric = load_rubric()
    guidance = load_guidance()
    report = load_report()

    # Initialize debug mode
    init_debug_mode(config)

    model = config.get('model', {}).get('primary', 'gpt-4o')
    print(f"\nUsing model: {model}")

    # Get criteria
    criteria = rubric.get('criteria', [])
    print(f"Analyzing {len(criteria)} criteria...\n")

    # Analyze each criterion
    all_feedback = []
    total_tokens = 0

    for i, criterion in enumerate(criteria, 1):
        result = analyze_criterion(report, criterion, guidance, model, criterion_index=i)
        all_feedback.append(result)

        if result['success']:
            # Use actual token count from API response
            total_tokens += result.get('tokens', {}).get('total_tokens', 0)

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

    # Save combined feedback to debug directory
    if DEBUG_SESSION_DIR:
        debug_feedback_file = DEBUG_SESSION_DIR / "combined_feedback.md"
        with open(debug_feedback_file, 'w') as f:
            f.write(combined_text)
        print(f"🐛 Combined feedback saved to debug: {debug_feedback_file.name}")

    end_time = datetime.now().timestamp()

    # Save debug session info
    save_debug_session_info(config, rubric, report, start_time, end_time, all_feedback)

    print(f"\n✅ Feedback saved to feedback.md")
    print(f"📊 Total tokens: {total_tokens}")
    if len(criteria) > 0:
        print(f"📊 Average tokens per criterion: {total_tokens // len(criteria)}")
    print(f"✅ {len(all_feedback)} criteria analyzed")
    print(f"⏱️  Total time: {round(end_time - start_time, 2)}s")


if __name__ == '__main__':
    main()
