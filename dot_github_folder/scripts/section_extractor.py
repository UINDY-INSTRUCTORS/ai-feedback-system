#!/usr/bin/env python3
"""
AI-based section extraction for criterion-based analysis.
This script intelligently extracts relevant text sections and images
for a given rubric criterion.
"""

import os
import json
import re
import requests
import sys
import time
from pathlib import Path
from typing import Dict, Any, Tuple, List

# Local script imports
sys.path.append(str(Path(__file__).parent))
from image_utils import filter_images_by_token_budget, validate_image_file

API_BASE = "https://models.inference.ai.azure.com"

def extract_sections_for_criterion_ai(
    report: Dict[str, Any],
    criterion: Dict[str, Any],
    config: Dict[str, Any],
    model: str = "gpt-4o-mini"
) -> Tuple[str, List[str]]:
    """
    Use AI to extract relevant text, then find associated images and notebook outputs.
    """
    # 1. Extract relevant text sections using an AI model
    full_content = report.get('content', '')
    if len(full_content) < 500:
        extracted_text = full_content
    else:
        try:
            prompt = build_extraction_prompt(report, criterion)
            extracted_text = call_extraction_api(prompt, model)
        except Exception as e:
            print(f"WARNING: AI text extraction failed for {criterion['name']}: {e}", file=sys.stderr)
            extracted_text = full_content[:8000]

    # 2. Augment extracted text with notebook outputs
    extracted_text = augment_with_notebook_outputs(report, extracted_text)

    # 3. Extract relevant images based on the extracted text
    image_paths = []
    vision_config = config.get('vision', {})
    if vision_config.get('enabled', False):
        enabled_for = vision_config.get('enabled_for_criteria', [])
        criterion_id = criterion.get('id', '')
        criterion_name = criterion.get('name', '')

        # Check if vision is enabled for this criterion (by ID or name)
        vision_enabled = (
            '*' in enabled_for or
            criterion_id in enabled_for or
            criterion_name in enabled_for
        )

        if vision_enabled:
            print(f"   Vision enabled for '{criterion_name}', extracting images...")
            image_paths = extract_relevant_images(
                report, criterion, vision_config, extracted_text
            )
        else:
            print(f"   Vision disabled for '{criterion_name}'.")

    return extracted_text, image_paths

def augment_with_notebook_outputs(report: Dict[str, Any], extracted_text: str) -> str:
    """
    Replace embed shortcodes with their corresponding notebook outputs.
    This prevents the AI from seeing raw {{< embed ... >}} syntax.

    - If the output has text content (tables, markdown, text), replace with content
    - If the output is image-only, replace with a descriptor like "(Figure: Plot data)"
    - This way the AI knows figures are present even if vision isn't enabled

    For example:
    - {{< embed P01-Euler.ipynb#raw_data_table >}} → actual table content
    - {{< embed P01-Euler.ipynb#plot >}} → "(Figure: Comparison plot)"
    """
    # Find all embed shortcodes in the extracted text
    embed_pattern = r'\{\{<\s*embed\s+([^\s]+)\s*>\}\}'
    embeds_found = re.findall(embed_pattern, extracted_text)

    if not embeds_found:
        return extracted_text

    # Get notebook outputs from the report
    notebook_outputs = report.get('notebook_outputs', [])
    if not notebook_outputs:
        return extracted_text

    # Build a map of embed references to their formatted content
    embed_replacements = {}

    for nb_output in notebook_outputs:
        embed_ref = nb_output.get('embed', '')
        if embed_ref in embeds_found:
            outputs = nb_output.get('outputs', {})
            cell_id = nb_output.get('cell_id', 'unknown')

            # Try to build content from text outputs
            output_text = ""

            # Add HTML tables (converted to markdown)
            if 'html_as_markdown' in outputs and outputs['html_as_markdown']:
                output_text += f"\n**[Embedded Output from {cell_id}]**\n\n"
                for table in outputs['html_as_markdown']:
                    output_text += f"{table}\n\n"

            # Add markdown outputs
            if 'markdown' in outputs and outputs['markdown']:
                if not output_text:
                    output_text = f"\n**[Embedded Output from {cell_id}]**\n\n"
                for md in outputs['markdown']:
                    output_text += f"{md}\n\n"

            # Add text outputs
            if 'text' in outputs and outputs['text']:
                if not output_text:
                    output_text = f"\n**[Embedded Output from {cell_id}]**\n\n"
                for text in outputs['text']:
                    output_text += f"```\n{text}\n```\n\n"

            # Add LaTeX outputs
            if 'latex' in outputs and outputs['latex']:
                if not output_text:
                    output_text = f"\n**[Embedded Output from {cell_id}]**\n\n"
                for latex in outputs['latex']:
                    output_text += f"{latex}\n\n"

            # If NO text content found but this is an embedded cell,
            # use a descriptor (the actual figure will be passed via vision)
            if not output_text:
                # Clean up cell_id for better readability
                cell_label = cell_id.replace('_', ' ').title()
                output_text = f"\n**[Figure: {cell_label}]**\n"

            # Store the replacement (shortcode pattern -> actual content or descriptor)
            embed_replacements[embed_ref] = output_text.strip()

    # Replace all embed shortcodes with their actual content or descriptors
    if embed_replacements:
        augmented_text = extracted_text
        for embed_ref, content in embed_replacements.items():
            # Build the exact shortcode pattern to replace
            shortcode_pattern = r'\{\{<\s*embed\s+' + re.escape(embed_ref) + r'\s*>\}\}'
            augmented_text = re.sub(shortcode_pattern, content, augmented_text)

        print(f"   Replaced {len(embed_replacements)} embed shortcode(s)")
        return augmented_text

    return extracted_text

def extract_relevant_images(
    report: Dict[str, Any],
    criterion: Dict[str, Any],
    vision_config: Dict[str, Any],
    extracted_text: str
) -> List[str]:
    """
    Extract and filter images relevant to the provided text section.
    
    This uses a hybrid strategy:
    1.  **Precise Mapping:** Finds images from notebook embeds (`{{< embed >}}`)
        that are present in the `extracted_text`.
    2.  **Keyword Fallback:** For manually linked images, falls back to matching
        criterion keywords against the image caption.
    """
    all_figures = report.get('figures', {}).get('details', [])
    relevant_images = {}

    # Strategy 1: Find images from embed shortcodes within the extracted text
    embeds_in_text = set(re.findall(r'\{\{<\s*embed\s+(.*?)\s*>\}\}', extracted_text))
    for fig in all_figures:
        if fig['source'] in embeds_in_text:
            if validate_image_file(fig['path']):
                priority = get_image_priority(fig, vision_config.get('image_priority', []))
                relevant_images[fig['path']] = priority
            else:
                print(f"   Skipping invalid/missing image from embed: {fig['path']}")

    # Strategy 2: Include unmapped generated images (these are generated by Quarto but not explicitly embedded)
    for fig in all_figures:
        if fig['source'] == 'generated:unmapped' and fig['path'] not in relevant_images:
            if validate_image_file(fig['path']):
                priority = get_image_priority(fig, vision_config.get('image_priority', []))
                relevant_images[fig['path']] = priority
            else:
                print(f"   Skipping invalid/missing generated image: {fig['path']}")

    # Strategy 3: Fallback to keyword matching for manual markdown images
    search_terms = set(criterion.get('keywords', []))
    search_terms.update(re.findall(r'\w+', criterion.get('name', '').lower()))

    for fig in all_figures:
        # Only apply to manual images that aren't already found
        if fig['source'].startswith('markdown:') and fig['path'] not in relevant_images:
            search_text = fig['caption'].lower()
            if any(term.lower() in search_text for term in search_terms):
                if validate_image_file(fig['path']):
                    priority = get_image_priority(fig, vision_config.get('image_priority', []))
                    relevant_images[fig['path']] = priority
                else:
                    print(f"   Skipping invalid/missing manual image: {fig['path']}")

    # --- Prioritize and filter the collected images ---
    sorted_paths = sorted(relevant_images.keys(), key=lambda p: relevant_images[p])
    
    max_images = vision_config.get('max_images_per_criterion', 3)
    limited_paths = sorted_paths[:max_images]

    token_budget = vision_config.get('image_token_budget', 2000)
    resize_dim = vision_config.get('resize_max_dimension')
    final_paths, tokens_used = filter_images_by_token_budget(
        limited_paths, token_budget, resize_dim
    )

    if final_paths:
        print(f"   Selected {len(final_paths)} image(s) using ~{tokens_used} tokens.")
    return final_paths

def get_image_priority(figure: Dict[str, Any], priority_list: List[str]) -> int:
    """Determines image priority based on keywords in its path or caption."""
    search_text = f"{Path(figure['path']).name} {figure['caption']}".lower()
    for i, keyword in enumerate(priority_list):
        if keyword.lower() in search_text:
            return i
    return len(priority_list)

def build_extraction_prompt(report: Dict[str, Any], criterion: Dict[str, Any]) -> str:
    """Builds the prompt for the AI to extract relevant text sections.

    Adapts comprehensiveness based on document size to manage token usage:
    - Small docs (< 5000 words): Be comprehensive, extract all relevant content
    - Medium docs (5000-10000 words): Be comprehensive but focus on most relevant
    - Large docs (> 10000 words): Be selective, prioritize most directly relevant
    """
    criterion_name = criterion.get('name', 'Unknown')
    criterion_desc = criterion.get('description', '')
    keywords = criterion.get('keywords', [])
    structure = report.get('structure', [])
    heading_list = "\n".join([f"{'  '*(h['level']-1)}- {h['text']}" for h in structure[:20]])
    full_content = report.get('content', '')

    # Calculate document size and adapt extraction strategy
    content_word_count = len(full_content.split())

    if content_word_count > 10000:
        comprehensiveness_guidance = (
            "3.  IMPORTANT: Focus on content directly relevant to this criterion. "
            "If content is marginally relevant, you may skip it to stay concise. "
            "Prioritize substance over comprehensiveness given the large document size."
        )
        max_content_note = "\n\nNOTE: This is a large document. Be selective to manage context size."
    elif content_word_count > 5000:
        comprehensiveness_guidance = (
            "3.  IMPORTANT: Content relevant to this criterion may be scattered throughout the report. "
            "Extract all clearly relevant content, but focus on the most important sections."
        )
        max_content_note = ""
    else:
        comprehensiveness_guidance = (
            "3.  IMPORTANT: Content relevant to this criterion may be scattered throughout the report in multiple locations. "
            "You MUST extract all relevant content, even if it appears in different sections. "
            "Be comprehensive - it's better to include too much relevant content than to miss important details."
        )
        max_content_note = ""

    return f"""You are a technical report analyzer. Your task is to extract sections of a student report that are relevant to evaluating a specific rubric criterion.

**Rubric Criterion to Evaluate:**
**{criterion_name}**
{criterion_desc}

**Keywords:** {', '.join(keywords)}

**Report Structure:**
{heading_list}

**Your Task:**
1.  Read the full report below carefully.
2.  Identify and extract sections (text, headings, and any `{{< embed >}}` shortcodes) that are relevant to this criterion.
{comprehensiveness_guidance}
4.  Return the extracted sections verbatim, preserving headings and formatting.
5.  If multiple sections are relevant, separate them with "---".

**Full Report:**
---
{full_content}
---

**Extracted Sections (relevant to "{criterion_name}"){max_content_note}:"""

def call_extraction_api(prompt: str, model: str, max_retries: int = 3) -> str:
    """Calls the GitHub Models API for text extraction with exponential backoff retry."""
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable not set")

    endpoint = f"{API_BASE}/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    # Estimate tokens before making the API call (rough: ~4 chars per token)
    estimated_prompt_tokens = len(prompt) // 4
    estimated_total_tokens = estimated_prompt_tokens + 4000  # 4000 = max_tokens for response

    if estimated_total_tokens > 15000:
        print(f"   ⚠️  HIGH TOKEN USAGE: Estimated ~{estimated_total_tokens} tokens (prompt: {estimated_prompt_tokens}, output: 4000)")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a thorough document analyzer. Extract relevant sections verbatim. Balance comprehensiveness with conciseness based on document size."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 4000
    }

    # Retry loop with exponential backoff
    last_error = None

    for attempt in range(max_retries):
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=90)
            response.raise_for_status()
            result = response.json()
            extracted = result['choices'][0]['message']['content'].strip()

            usage = result.get('usage', {})
            print(f"   Extraction tokens: {usage.get('total_tokens', 0)} (prompt: {usage.get('prompt_tokens', 0)}, completion: {usage.get('completion_tokens', 0)})")

            # Log rate limit info if available
            remaining = response.headers.get('x-ratelimit-remaining')
            if remaining:
                print(f"   Rate limit remaining: {remaining}")

            return extracted

        except requests.exceptions.HTTPError as e:
            last_error = e
            if e.response.status_code == 429:
                # Rate limited - implement backoff
                if attempt < max_retries - 1:
                    # Check for Retry-After header
                    retry_after = e.response.headers.get('Retry-After')
                    if retry_after:
                        try:
                            wait_time = int(retry_after)
                        except (ValueError, TypeError):
                            wait_time = 2 ** attempt
                    else:
                        # Exponential backoff: 1s, 2s, 4s, 8s, etc.
                        wait_time = 2 ** attempt

                    print(f"   ⚠️  Extraction rate limited (429). Waiting {wait_time}s before retry {attempt + 1}/{max_retries - 1}...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"   ❌ Extraction rate limited after {max_retries} attempts. Giving up.")
                    raise
            else:
                # Not a rate limit error - raise immediately
                raise

    # Should not reach here, but just in case
    if last_error:
        raise last_error

if __name__ == '__main__':
    # A simple test function can be added here if needed
    print("This script is intended to be called from ai_feedback_criterion.py")
