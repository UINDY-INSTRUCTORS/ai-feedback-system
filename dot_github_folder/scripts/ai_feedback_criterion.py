#!/usr/bin/env python3
"""
Criterion-based AI feedback using GitHub Models API with AI-based section extraction.
"""

import os
import json
import yaml
import requests
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, List, Optional

# Add parent dir to path to allow local imports
sys.path.append(str(Path(__file__).parent))
from section_extractor import extract_sections_for_criterion_ai
from image_utils import encode_image_to_base64

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
        with open('.github/config.yml') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Failed to load config: {e}", file=sys.stderr)
        sys.exit(1)


def load_rubric():
    """Load machine-readable rubric."""
    try:
        with open('.github/feedback/rubric.yml') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"ERROR: Failed to load rubric: {e}", file=sys.stderr)
        sys.exit(1)


def load_guidance():
    """Load AI instruction guidance."""
    try:
        with open('.github/feedback/guidance.md') as f:
            return f.read()
    except Exception as e:
        print(f"ERROR: Failed to load guidance: {e}", file=sys.stderr)
        sys.exit(1)


def load_report():
    """Load parsed report content."""
    try:
        with open('parsed_report.json') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: Failed to load parsed report: {e}", file=sys.stderr)
        sys.exit(1)


def init_debug_mode(config: dict):
    """Initialize debug mode if enabled."""
    global DEBUG_CONFIG, DEBUG_SESSION_DIR
    debug_mode = config.get('debug_mode', {})
    if not debug_mode.get('enabled', False):
        return
    DEBUG_CONFIG = debug_mode
    output_dir = Path(debug_mode.get('output_dir', '.github/debug'))
    timestamp = datetime.now().strftime(debug_mode.get('timestamp_format', '%Y%m%d_%H%M%S'))
    tag_name = os.environ.get('TAG_NAME', 'manual-run')
    session_name = f"{timestamp}_{tag_name}"
    DEBUG_SESSION_DIR = output_dir / session_name
    DEBUG_SESSION_DIR.mkdir(parents=True, exist_ok=True)
    print(f"🐛 Debug mode enabled. Output: {DEBUG_SESSION_DIR}")


def save_debug_criterion_data(
    metadata: dict,
    context: str = "",
    prompt: str = "",
    request_payload: dict = None,
    response_data: dict = None,
    feedback: str = ""
):
    """Save debug data for a single criterion analysis."""
    if not DEBUG_CONFIG:
        return

    criterion_id = metadata.get('criterion_id', 'unknown')
    criterion_dir = DEBUG_SESSION_DIR / "criteria" / f"{metadata.get('criterion_index', 0):02d}_{criterion_id}"
    criterion_dir.mkdir(parents=True, exist_ok=True)

    if DEBUG_CONFIG.get('save_context', False):
        (criterion_dir / "context.txt").write_text(context)
    if DEBUG_CONFIG.get('save_prompts', False) and prompt:
        (criterion_dir / "prompt.txt").write_text(prompt)
    if DEBUG_CONFIG.get('save_prompts', False) and request_payload:
        (criterion_dir / "request.json").write_text(json.dumps(request_payload, indent=2))
    if DEBUG_CONFIG.get('save_responses', False) and response_data:
        (criterion_dir / "response.json").write_text(json.dumps(response_data, indent=2))
    if DEBUG_CONFIG.get('save_responses', False) and feedback:
        (criterion_dir / "feedback.md").write_text(feedback)
    if DEBUG_CONFIG.get('save_api_metadata', False):
        (criterion_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))


def get_criterion_guidance(guidance: str, criterion: dict) -> str:
    """Extract relevant guidance for this specific criterion."""
    # This is a placeholder; in a real system, this would extract
    # specific guidance related to the criterion from the main guidance file.
    return guidance # For now, return the whole thing


def build_criterion_prompt(report: dict, criterion: dict, guidance_excerpt: str, config: dict) -> tuple:
    """Build focused prompt for analyzing one criterion.

    Returns:
        tuple: (prompt, context, image_paths)
    """
    extraction_model = config.get('model', {}).get('extractor', 'gpt-4o-mini')
    relevant_content, image_paths = extract_sections_for_criterion_ai(
        report, criterion, config, model=extraction_model
    )

    levels_text = ""
    levels = criterion.get('levels', {})
    for level_name, level_info in levels.items():
        point_range = level_info.get('point_range', '[N/A]')
        levels_text += f"- **{level_name.title()}** (Score: {point_range[0]}-{point_range[1]}): {level_info.get('description', '')}\n"

    max_score = criterion.get('weight', 0)

    prompt = f"""{guidance_excerpt}

## Your Task
Evaluate the following criterion based on the relevant sections extracted from the student's report.

### {criterion['name']} ({max_score}%)
{criterion['description']}

{levels_text}

## Output Format
Your response MUST be a single JSON object. Do not include any text outside of this JSON object.
The JSON object must have the following schema:
{{
  "summary": "A concise, one-paragraph summary of your overall assessment for this criterion.",
  "strengths": [
    "A list of specific strengths of the student's work on this criterion."
  ],
  "areas_for_improvement": [
    {{
      "issue": "A specific, concise description of an area for improvement.",
      "suggestion": "An actionable suggestion for how the student can improve."
    }}
  ],
  "score": <A numerical score from 0 to {max_score}>,
  "overall_assessment": "<One of: 'Excellent', 'Good', 'Poor'>"
}}

Base your feedback and score on the rubric levels provided. The 'overall_assessment' should correspond to the rubric level that best describes the work. The 'score' must be an integer within the point range specified for that level in the rubric.

## Report Sections Relevant to This Criterion
---
{relevant_content}
---
"""

    # Add instructions for analyzing images if they are provided
    if image_paths:
        prompt += f"""
## Images Provided
You have been provided with {len(image_paths)} image(s) related to this criterion.
Please analyze these images and incorporate your visual observations into the feedback:

- For circuit schematics: Verify component values, connections, and proper symbols.
- For simulations: Check if waveforms match expectations, proper scaling, and labeling.
- For lab photos: Check for proper setup, wiring, and equipment configuration.

Reference specific images in your feedback (e.g., "In the schematic 'images/circ1.png'...")
"""
    return prompt, relevant_content, image_paths


def call_github_models_api(
    prompt: str,
    model: str,
    config: dict,
    image_paths: Optional[List[str]] = None
) -> tuple:
    """
    Call GitHub Models API, handling both text and vision requests.

    Returns:
        tuple: (feedback_text, response_data, request_payload)
    """
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable not set")

    endpoint = f"{API_BASE}/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    # --- Build message payload ---
    messages = [
        {"role": "system", "content": "You are an expert instructor providing constructive, specific feedback on student technical reports in JSON format."},
    ]
    user_content = [{"type": "text", "text": prompt}]

    if image_paths:
        print(f"   Encoding {len(image_paths)} image(s) for vision model...")
        resize_dim = config.get('vision', {}).get('resize_max_dimension')
        for img_path in image_paths:
            base64_data = encode_image_to_base64(img_path, max_dimension=resize_dim)
            if base64_data:
                user_content.append({"type": "image_url", "image_url": {"url": base64_data}})
            else:
                print(f"   WARNING: Could not encode image {img_path}, skipping.")
    
    messages.append({"role": "user", "content": user_content})
    # --- End message payload ---

    payload = {
        "model": model,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
        "max_tokens": config.get('max_output_tokens', 2000)
    }

    print(f"   Calling {model} API... (images: {len(image_paths or [])})")
    timeout = config.get('request_timeout', 120)
    response = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()

    result = response.json()
    feedback = result['choices'][0]['message']['content']

    usage = result.get('usage', {})
    print(f"   ✅ Tokens: {usage.get('total_tokens', 0)} (prompt: {usage.get('prompt_tokens', 0)}, completion: {usage.get('completion_tokens', 0)})")

    return feedback, result, payload


def analyze_criterion(report: dict, criterion: dict, guidance: str, config: dict, criterion_index: int = 0) -> dict:
    """Analyze a single criterion and return feedback."""
    criterion_name = criterion['name']
    criterion_id = criterion.get('id', f'criterion_{criterion_index}')
    model = config.get('model', {}).get('primary', 'gpt-4o')
    print(f"\n📊 Analyzing: {criterion_name}")

    prompt, context, image_paths = "", "", []
    metadata = {
        "criterion_id": criterion_id,
        "criterion_name": criterion_name,
        "criterion_index": criterion_index,
        "timestamp": datetime.now().isoformat(),
        "model_used": model,
        "success": False
    }

    try:
        guidance_excerpt = get_criterion_guidance(guidance, criterion)
        prompt, context, image_paths = build_criterion_prompt(report, criterion, guidance_excerpt, config)
        metadata["image_paths"] = image_paths

        start_time = datetime.now().timestamp()
        feedback_json, response_data, request_payload = call_github_models_api(
            prompt, model, config, image_paths=image_paths
        )
        end_time = datetime.now().timestamp()

        usage = response_data.get('usage', {})
        tokens = {
            'prompt_tokens': usage.get('prompt_tokens', 0),
            'completion_tokens': usage.get('completion_tokens', 0),
            'total_tokens': usage.get('total_tokens', 0)
        }
        
        metadata.update({
            "api_endpoint": f"{API_BASE}/chat/completions",
            "request_time_seconds": round(end_time - start_time, 2),
            "tokens": tokens,
            "success": True,
            "context_word_count": len(context.split()),
        })

        # The actual feedback content is inside the JSON now
        feedback_content = json.loads(feedback_json)

        save_debug_criterion_data(metadata, context, prompt, request_payload, response_data, feedback_json)

        return {
            'criterion': criterion_name,
            'feedback': feedback_content, # Return the parsed JSON
            'success': True,
            'tokens': tokens
        }

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        metadata["error"] = str(e)
        save_debug_criterion_data(metadata, context, prompt)
        return {
            'criterion': criterion_name,
            'feedback': f"Error analyzing this criterion: {e}",
            'success': False,
            'error': str(e),
            'tokens': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}
        }


def main():
    """Generate AI feedback for all criteria."""
    start_time = datetime.now().timestamp()
    print("\n" + "="*60 + "\nAI Feedback System\n" + "="*60)

    config = load_config()
    rubric = load_rubric()
    guidance = load_guidance()
    report = load_report()

    init_debug_mode(config)
    
    print(f"\nAnalyzing {len(rubric.get('criteria', []))} criteria...\n")

    all_feedback_json = []
    total_tokens = 0

    for i, criterion in enumerate(rubric.get('criteria', []), 1):
        result = analyze_criterion(report, criterion, guidance, config, criterion_index=i)
        all_feedback_json.append(result)
        if result['success']:
            total_tokens += result.get('tokens', {}).get('total_tokens', 0)

    # --- Create final feedback document ---
    # This part would now format the collected JSON into a nice .md file
    # For now, we'll just dump the raw JSON list.
    final_output_path = "feedback.json"
    print(f"\n\n{'='*60}\nCOMBINED FEEDBACK JSON\n{'='*60}\n")
    try:
        with open(final_output_path, 'w') as f:
            json.dump(all_feedback_json, f, indent=2)
        print(f"✅ Feedback saved to {final_output_path}")
    except Exception as e:
        print(f"ERROR: Failed to save final feedback JSON: {e}", file=sys.stderr)

    if DEBUG_SESSION_DIR:
        debug_feedback_file = DEBUG_SESSION_DIR / "final_feedback.json"
        debug_feedback_file.write_text(json.dumps(all_feedback_json, indent=2))
        print(f"🐛 Combined feedback saved to debug: {debug_feedback_file.name}")

    end_time = datetime.now().timestamp()
    print(f"\n📊 Total tokens: {total_tokens}")
    print(f"✅ {len(all_feedback_json)} criteria analyzed")
    print(f"⏱️  Total time: {round(end_time - start_time, 2)}s")


if __name__ == '__main__':
    main()