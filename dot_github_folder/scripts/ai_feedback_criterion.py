#!/usr/bin/env python3
"""
Criterion-based AI feedback with multi-provider support.

Supports GitHub Models, OpenRouter, Anthropic, Gemini, and OpenAI.
Provider is configured via env vars, ~/.ai-feedback/config.yml, or per-repo config.
"""

import os
import json
import yaml
import requests
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, List, Optional

# Add parent dir to path to allow local imports
sys.path.append(str(Path(__file__).parent))
from section_extractor import extract_sections_for_criterion_ai
from image_utils import encode_image_to_base64, optimize_images_for_payload
from ai_provider import call_ai, resolve_provider_config, print_provider_info

# Load environment variables from .env file if it exists (for local testing)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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
    if os.environ.get('AI_DEBUG'):
        debug_mode = {
            **debug_mode,
            'enabled': True,
            'save_context': True,
            'save_prompts': True,
            'save_responses': True,
            'save_api_metadata': True,
        }
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
        # Save raw feedback text (the model's response before JSON parsing)
        (criterion_dir / "response_raw.txt").write_text(feedback)
    if DEBUG_CONFIG.get('save_api_metadata', False):
        (criterion_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))


def get_criterion_guidance(guidance: str, criterion: dict) -> str:
    """
    Extract relevant guidance for this specific criterion.

    The guidance file has two parts:
    - PART I: GENERAL GUIDANCE (applied to all criteria)
    - PART II: CRITERION-SPECIFIC GUIDANCE (one section per criterion)

    This function extracts:
    - All of Part I
    - The specific criterion section from Part II that matches this criterion's name

    Returns combined guidance, or full guidance if structured format not found.
    """
    criterion_name = criterion.get('name', '')

    # Split guidance into lines for processing
    lines = guidance.split('\n')

    # Extract Part I (General Guidance)
    part1_start = None
    part1_end = None

    for i, line in enumerate(lines):
        line_stripped = line.strip().upper()
        # Only match markdown headers (lines starting with #)
        # Check for Part II first to avoid substring match (Part I is in Part II)
        if line_stripped.startswith('#') and 'PART II' in line_stripped:
            part1_end = i
            break
        elif line_stripped.startswith('#') and 'PART I' in line_stripped:
            part1_start = i

    # If we don't find the structured format, return the whole guidance
    if part1_start is None and part1_end is None:
        return guidance

    # Extract Part I text
    if part1_start is not None and part1_end is not None:
        general_guidance = '\n'.join(lines[part1_start:part1_end])
    elif part1_end is not None:
        # Part I marker not found, but Part II is - take everything before Part II
        general_guidance = '\n'.join(lines[:part1_end])
    else:
        # No Part II found - return all guidance
        return guidance

    # Extract criterion-specific section from Part II
    criterion_section = ""
    criterion_header = f"## CRITERION: {criterion_name}"

    # Find the criterion section
    criterion_start = None
    criterion_end = None

    for i in range(part1_end, len(lines)):
        line = lines[i].strip()

        # Found the start of our criterion section
        if line.startswith('## CRITERION:') and criterion_name in line:
            criterion_start = i

        # Found the start of the next criterion section (end of ours)
        elif criterion_start is not None and line.startswith('## CRITERION:'):
            criterion_end = i
            break

        # Found the end of Part II (could be a major section marker)
        elif criterion_start is not None and line.startswith('# ') and 'CRITERION' not in line:
            criterion_end = i
            break

    # Extract criterion-specific guidance
    if criterion_start is not None:
        if criterion_end is not None:
            criterion_section = '\n'.join(lines[criterion_start:criterion_end])
        else:
            # This is the last criterion section, take until end of file
            criterion_section = '\n'.join(lines[criterion_start:])

    # Combine general + specific guidance
    if criterion_section:
        combined = general_guidance + '\n\n---\n\n' + criterion_section
        return combined
    else:
        # No specific section found for this criterion, just return general guidance
        # (Better than returning nothing - at least we have general context)
        return general_guidance


def build_criterion_prompt(report: dict, criterion: dict, guidance_excerpt: str, config: dict,
                           provider_config: dict = None) -> tuple:
    """Build focused prompt for analyzing one criterion.

    Returns:
        tuple: (prompt, context, image_paths)
    """
    extraction_model = config.get('model', {}).get('extractor', 'gpt-4o-mini')
    relevant_content, image_paths, _ = extract_sections_for_criterion_ai(
        report, criterion, config, model=extraction_model, provider_config=provider_config
    )

    levels_text = ""
    levels = criterion.get('levels', {})
    for level_name, level_info in levels.items():
        point_range = level_info.get('point_range', '[N/A]')
        levels_text += f"- **{level_name.title()}** (Score: {point_range[0]}-{point_range[1]}): {level_info.get('description', '')}\n"

    max_score = criterion.get('weight', 0)

    # Check if levels-only mode is enabled (classify only, no prose feedback)
    levels_only = os.environ.get('LEVELS_ONLY', '').lower() in ('1', 'true', 'yes')

    # Check if numerical scoring is enabled (defaults to false for formative assessment)
    # Env var SCORING_ENABLED overrides config (for batch/local runs)
    scoring_env = os.environ.get('SCORING_ENABLED')
    if scoring_env is not None:
        scoring_enabled = scoring_env.lower() in ('true', '1', 'yes')
    else:
        scoring_enabled = config.get('feedback', {}).get('scoring_enabled', False)

    if levels_only:
        json_schema = '{\n  "overall_assessment": "<The rubric level that best describes this work — use the exact level name from the rubric above>"\n}'
        scoring_instruction = "Return only the level name that best describes the work. Do not include any other fields."
    elif scoring_enabled:
        json_schema = f"""{{
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
}}"""
        scoring_instruction = f"Base your feedback and score on the rubric levels provided. The 'overall_assessment' should correspond to the rubric level that best describes the work. The 'score' must be an integer within the point range specified for that level in the rubric."
    else:
        json_schema = """{
  "summary": "A concise, one-paragraph summary of your overall assessment for this criterion.",
  "strengths": [
    "A list of specific strengths of the student's work on this criterion."
  ],
  "areas_for_improvement": [
    {
      "issue": "A specific, concise description of an area for improvement.",
      "suggestion": "An actionable suggestion for how the student can improve."
    }
  ],
  "overall_assessment": "<The rubric level that best describes this work, e.g., 'Exemplary', 'Satisfactory', 'Developing', 'Unsatisfactory'>"
}"""
        scoring_instruction = "Base your feedback on the rubric levels provided. The 'overall_assessment' should be the exact rubric level name that best describes the work (e.g., 'Exemplary', 'Satisfactory', etc.)."

    prompt = f"""{guidance_excerpt}

## Your Task
Evaluate the following criterion based on the relevant sections extracted from the student's report.

### {criterion['name']} ({max_score}%)
{criterion['description']}

{levels_text}

## Output Format
Your response MUST be a single JSON object. Do not include any text outside of this JSON object.
The JSON object must have the following schema:
{json_schema}

{scoring_instruction}

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


def build_ai_messages(
    prompt: str,
    config: dict,
    image_paths: Optional[List[str]] = None,
    provider_config: dict = None,
) -> list:
    """
    Build the messages list for the AI call, including image optimization.

    Returns:
        list: OpenAI-format messages list
    """
    default_system = "You are an expert instructor providing constructive, specific feedback on student technical reports in JSON format. Be concise — your entire JSON response should be under 400 tokens."
    system_content = (provider_config or {}).get('system_prompt') or default_system
    messages = [
        {"role": "system", "content": system_content},
    ]
    user_content = [{"type": "text", "text": prompt}]

    if image_paths:
        print(f"   Processing {len(image_paths)} image(s) for vision model...")
        # Calculate text payload size for image budget
        text_size_bytes = len(json.dumps({"messages": messages}).encode('utf-8'))
        optimized_images = optimize_images_for_payload(
            image_paths=image_paths,
            text_size_bytes=text_size_bytes,
            config=config
        )
        if optimized_images:
            for img_data in optimized_images:
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": img_data['base64_data']}
                })
        else:
            print(f"   Could not fit images in payload, proceeding with text only")

    messages.append({"role": "user", "content": user_content})
    return messages


def analyze_criterion(report: dict, criterion: dict, guidance: str, config: dict,
                      criterion_index: int = 0, provider_config: dict = None) -> dict:
    """Analyze a single criterion and return feedback."""
    criterion_name = criterion['name']
    criterion_id = criterion.get('id', f'criterion_{criterion_index}')

    if provider_config is None:
        provider_config = resolve_provider_config(config)

    model = provider_config['model']
    print(f"\n Analyzing: {criterion_name}")

    prompt, context, image_paths = "", "", []
    metadata = {
        "criterion_id": criterion_id,
        "criterion_name": criterion_name,
        "criterion_index": criterion_index,
        "timestamp": datetime.now().isoformat(),
        "model_used": model,
        "provider": provider_config['provider'],
        "success": False
    }

    try:
        guidance_excerpt = get_criterion_guidance(guidance, criterion)
        prompt, context, image_paths = build_criterion_prompt(report, criterion, guidance_excerpt, config,
                                                               provider_config=provider_config)
        metadata["image_paths"] = image_paths
        metadata["requested_images"] = len(image_paths)

        messages = build_ai_messages(prompt, config, image_paths=image_paths, provider_config=provider_config)

        start_time = datetime.now().timestamp()
        feedback_json, response_data, request_payload = call_ai(
            messages, model, config,
            provider_config=provider_config,
            json_mode=True,
            fallback_model=provider_config.get('fallback'),
        )
        end_time = datetime.now().timestamp()

        usage = response_data.get('usage', {})
        tokens = {
            'prompt_tokens': usage.get('prompt_tokens', 0),
            'completion_tokens': usage.get('completion_tokens', 0),
            'total_tokens': usage.get('total_tokens', 0)
        }

        # Count images actually sent (for optimization tracking)
        images_in_request = 0
        last_msg = request_payload.get('messages', [{}])[-1] if 'messages' in request_payload else {}
        for content_item in last_msg.get('content', []):
            if isinstance(content_item, dict) and content_item.get('type') == 'image_url':
                images_in_request += 1

        metadata.update({
            "provider": provider_config['provider'],
            "api_base": provider_config['api_base'],
            "request_time_seconds": round(end_time - start_time, 2),
            "tokens": tokens,
            "success": True,
            "context_word_count": len(context.split()),
            "images_included": images_in_request,
        })

        # The actual feedback content is inside the JSON now
        # Strip markdown fences if the model wrapped its response (e.g. ```json ... ```)
        json_text = feedback_json.strip()
        if json_text.startswith('```'):
            lines = json_text.splitlines()
            json_text = '\n'.join(lines[1:-1] if lines[-1].strip().startswith('```') else lines[1:])

        # Save raw response before parsing (for debugging)
        save_debug_criterion_data(metadata, context, prompt, request_payload, response_data, feedback_json)

        # Try to parse JSON, with fallback for unescaped backslashes
        try:
            feedback_content = json.loads(json_text)
        except json.JSONDecodeError as e:
            # If we have an invalid escape error, try to fix common patterns
            # (e.g., unescaped backslashes from file paths or LaTeX)
            if "Invalid \\escape" in str(e) or "invalid escape sequence" in str(e):
                # Escape unescaped backslashes (but not already-escaped ones)
                fixed_json = json_text.replace('\\', '\\\\')
                # But that will double-escape already-escaped sequences, so undo those
                fixed_json = fixed_json.replace('\\\\\\\\', '\\\\')  # \\\\ -> \\
                fixed_json = fixed_json.replace('\\\\"', '\\"')      # \\" -> \"
                fixed_json = fixed_json.replace('\\\\/', '\\/')      # \/ -> /
                fixed_json = fixed_json.replace('\\\\n', '\\n')      # \n -> \n
                fixed_json = fixed_json.replace('\\\\t', '\\t')      # \t -> \t
                try:
                    feedback_content = json.loads(fixed_json)
                except json.JSONDecodeError:
                    raise e  # Re-raise original error if fixing didn't work
            else:
                raise

        return {
            'criterion': criterion_name,
            'feedback': feedback_content,
            'success': True,
            'tokens': tokens,
            '_extracted_text': context,
        }

    except Exception as e:
        print(f"   Failed: {e}")
        metadata["error"] = str(e)
        # Save what we have for debugging (including raw response if available)
        save_debug_criterion_data(metadata, context, prompt,
                                  request_payload if 'request_payload' in locals() else {},
                                  response_data if 'response_data' in locals() else {},
                                  feedback_json if 'feedback_json' in locals() else "")
        return {
            'criterion': criterion_name,
            'feedback': f"Error analyzing this criterion: {e}",
            'success': False,
            'error': str(e),
            'tokens': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0},
            '_extracted_text': context,
        }


def _tokenize(text: str) -> set:
    import re
    return {w for w in re.findall(r'\b[a-z]{3,}\b', text.lower())}


def _jaccard(a: set, b: set) -> float:
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def generate_organization_feedback(
    all_results: list,
    rubric: dict,
    report: dict,
    config: dict,
    provider_config: dict,
) -> dict:
    """
    Compute extraction discrimination metrics across all criteria and ask
    the AI to write a brief organization-quality paragraph for the student.

    Returns a feedback.json-compatible dict with criterion='__organization__'.
    """
    import re

    criteria = rubric.get('criteria', [])
    report_words = report.get('stats', {}).get('word_count', 0)

    # Collect extracted texts keyed by criterion name
    extractions: dict[str, str] = {}
    for result in all_results:
        name = result.get('criterion', '')
        text = result.get('_extracted_text', '') or ''
        if name and text:
            extractions[name] = text

    if not extractions:
        return None

    tokens_by_name = {n: _tokenize(t) for n, t in extractions.items()}

    # Coverage fractions
    def wc(t): return len(re.findall(r'\w+', t))
    coverage = {
        n: (wc(extractions[n]) / report_words if report_words else 0)
        for n in extractions
    }

    # High-overlap pairs (Jaccard > 0.55)
    names = list(extractions.keys())
    high_overlap = []
    for i, a in enumerate(names):
        for b in names[i+1:]:
            j = _jaccard(tokens_by_name[a], tokens_by_name[b])
            if j > 0.55:
                high_overlap.append((a, b, j))
    high_overlap.sort(key=lambda x: -x[2])

    # Low-coverage criteria (< 5%)
    thin = [n for n, cov in coverage.items() if cov < 0.05]

    # Build metrics summary for the AI prompt
    cov_lines = '\n'.join(
        f"  - {n}: {coverage.get(n, 0):.0%} ({wc(extractions.get(n,''))} words)"
        for n in names
    )
    overlap_lines = '\n'.join(
        f"  - '{a}' ↔ '{b}': {j:.0%} overlap"
        for a, b, j in high_overlap[:6]
    ) or '  (none above threshold)'

    thin_line = ', '.join(f"'{n}'" for n in thin) if thin else '(none)'

    assignment_name = config.get('assignment', {}).get('name', 'this assignment')
    course_name = config.get('course', {}).get('name', '')

    prompt = f"""\
You are reviewing a student's technical report for {course_name} — {assignment_name}.

The table below shows what fraction of the report's content is relevant to each rubric criterion,
and which criterion pairs share heavily overlapping content (suggesting those topics were not
clearly separated in the report).

**Content coverage per criterion** (fraction of report words relevant to each):
{cov_lines}

**High-overlap criterion pairs** (Jaccard similarity > 55% — content is blended):
{overlap_lines}

**Criteria with very thin coverage (< 5%):** {thin_line}

Write 3–5 sentences of constructive feedback addressed directly to the student about their
report's *organization* and *structure*. Focus on:
1. Which rubric areas are underrepresented or blended together.
2. Concrete suggestions for how to restructure (e.g., add explicit section headings, separate
   demo programs from simulations, write a distinct conclusion).
Do NOT comment on the technical content — only structure and organization.
Be specific and use the actual criterion names above. Do not use bullet points; write prose.
"""

    messages = [
        {"role": "system", "content": "You are an expert writing instructor. Respond in plain prose, 3-5 sentences."},
        {"role": "user", "content": [{"type": "text", "text": prompt}]},
    ]

    extractor_model = provider_config.get('extractor_model') or provider_config.get('model')
    print(f"\n Generating organization feedback...")
    try:
        org_text, _, _ = call_ai(
            messages, extractor_model, config,
            provider_config=provider_config,
            json_mode=False,
        )
        org_text = org_text.strip()
    except Exception as e:
        print(f"   Organization feedback failed: {e}")
        org_text = None

    # Build the structured payload (coverage table + AI text)
    coverage_rows = [
        {'criterion': n, 'coverage_pct': round(coverage.get(n, 0) * 100, 1),
         'words': wc(extractions.get(n, ''))}
        for n in names
    ]
    overlap_rows = [
        {'criterion_a': a, 'criterion_b': b, 'jaccard': round(j, 2)}
        for a, b, j in high_overlap[:6]
    ]

    return {
        'criterion': '__organization__',
        'success': True,
        'feedback': {
            'summary': org_text or '(organization analysis unavailable)',
            'coverage': coverage_rows,
            'high_overlap': overlap_rows,
            'report_words': report_words,
        },
        'tokens': {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0},
    }


def _run_extract_only(rubric: dict, guidance: str, report: dict,
                      config: dict, provider_config: dict) -> None:
    """Extract relevant sections for each criterion and write a readable report.

    Runs the extraction AI (cheap) but skips the feedback AI (expensive).
    Output is written to extraction.md in the current directory.
    """
    criteria = rubric.get('criteria', [])
    out_path = Path(os.environ.get('EXTRACT_OUTPUT_PATH', 'extraction.md'))
    repo_name = Path.cwd().name

    print(f"\nExtract-only mode: running extraction for {len(criteria)} criteria...\n")

    lines = [
        f'# Extraction Report: {repo_name}',
        f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
        f'Criteria: {len(criteria)}',
        '',
    ]

    for i, criterion in enumerate(criteria, 1):
        name = criterion['name']
        weight = criterion.get('weight', 0)
        keywords = criterion.get('keywords', [])
        print(f"  Extracting [{i}/{len(criteria)}]: {name}")

        try:
            guidance_excerpt = get_criterion_guidance(guidance, criterion)
            _, context, image_paths = build_criterion_prompt(
                report, criterion, guidance_excerpt, config,
                provider_config=provider_config,
            )
        except Exception as e:
            context = f'[EXTRACTION ERROR: {e}]'
            image_paths = []

        lines += [
            f'## {i}. {name} ({weight}%)',
        ]
        if keywords:
            lines.append(f'*Keywords: {", ".join(str(k) for k in keywords)}*')
        if image_paths:
            lines.append(f'*Images found: {len(image_paths)}*')
        lines += ['', '```', context.strip(), '```', '']

    out_path.write_text('\n'.join(lines))
    print(f"\nExtraction report: {out_path}")


def main():
    """Generate AI feedback for all criteria."""
    start_time = datetime.now().timestamp()
    print("\n" + "="*60 + "\nAI Feedback System\n" + "="*60)

    config = load_config()
    rubric = load_rubric()
    guidance = load_guidance()
    report = load_report()

    init_debug_mode(config)

    # Resolve provider configuration
    provider_config = resolve_provider_config(config)
    print(f"\nProvider configuration:")
    print_provider_info(provider_config)

    extract_only = os.environ.get('EXTRACT_ONLY', '').lower() in ('1', 'true', 'yes')

    if extract_only:
        _run_extract_only(rubric, guidance, report, config, provider_config)
        return

    print(f"\nAnalyzing {len(rubric.get('criteria', []))} criteria...\n")

    all_feedback_json = []
    total_tokens = 0

    for i, criterion in enumerate(rubric.get('criteria', []), 1):
        result = analyze_criterion(report, criterion, guidance, config,
                                   criterion_index=i, provider_config=provider_config)
        all_feedback_json.append(result)
        if result['success']:
            total_tokens += result.get('tokens', {}).get('total_tokens', 0)

    # Generate organization section (uses extracted texts collected above)
    org_result = generate_organization_feedback(
        all_feedback_json, rubric, report, config, provider_config
    )
    if org_result:
        all_feedback_json.insert(0, org_result)

    # Strip internal _extracted_text before saving (not needed in output)
    for r in all_feedback_json:
        r.pop('_extracted_text', None)

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
    failed = [r for r in all_feedback_json if not r.get('success')]
    print(f"\n📊 Total tokens: {total_tokens}")
    if failed:
        print(f"⚠️  {len(failed)}/{len(all_feedback_json)} criteria failed: "
              f"{', '.join(r['criterion'] for r in failed)}")
    else:
        print(f"✅ {len(all_feedback_json)} criteria analyzed")
    print(f"⏱️  Total time: {round(end_time - start_time, 2)}s")
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()