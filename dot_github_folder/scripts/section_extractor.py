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
    Use AI to extract relevant text, then find associated images.
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

    # 2. Extract relevant images based on the extracted text
    image_paths = []
    vision_config = config.get('vision', {})
    if vision_config.get('enabled', False):
        enabled_for = vision_config.get('enabled_for_criteria', [])
        criterion_id = criterion.get('id', '')
        if '*' in enabled_for or criterion_id in enabled_for:
            print(f"   Vision enabled for '{criterion_id}', extracting images...")
            image_paths = extract_relevant_images(
                report, criterion, vision_config, extracted_text
            )
        else:
            print(f"   Vision disabled for '{criterion_id}'.")

    return extracted_text, image_paths

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

    # Strategy 2: Fallback to keyword matching for manual markdown images
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
    """Builds the prompt for the AI to extract relevant text sections."""
    # This function remains largely the same as before
    criterion_name = criterion.get('name', 'Unknown')
    criterion_desc = criterion.get('description', '')
    keywords = criterion.get('keywords', [])
    structure = report.get('structure', [])
    heading_list = "\n".join([f"{'  '*(h['level']-1)}- {h['text']}" for h in structure[:20]])
    full_content = report.get('content', '')

    return f"""You are a technical report analyzer. Your task is to extract ONLY the sections of a student report that are relevant to evaluating a specific rubric criterion.\n\n**Rubric Criterion to Evaluate:**\n**{criterion_name}**\n{criterion_desc}\n\n**Keywords:** {', '.join(keywords)}\n\n**Report Structure:**\n{heading_list}\n\n**Your Task:**\n1.  Read the full report below.\n2.  Identify and extract ONLY the sections (text, headings, and any `{{< embed >}}` shortcodes) that are directly relevant to the criterion.\n3.  Return the extracted sections verbatim. Be selective.\n4.  If multiple sections are relevant, separate them with "---".\n\n**Full Report:**\n---\n{full_content}\n---\n\n**Extracted Sections (relevant to "{criterion_name}"):"""

def call_extraction_api(prompt: str, model: str) -> str:
    """Calls the GitHub Models API for text extraction."""
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable not set")

    endpoint = f"{API_BASE}/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a precise document analyzer. Extract only the requested sections verbatim. Be selective and focused."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 4000
    }
    
    response = requests.post(endpoint, headers=headers, json=payload, timeout=90)
    response.raise_for_status()
    result = response.json()
    extracted = result['choices'][0]['message']['content'].strip()
    
    usage = result.get('usage', {})
    print(f"   Extraction tokens: {usage.get('total_tokens', 0)} (prompt: {usage.get('prompt_tokens', 0)}, completion: {usage.get('completion_tokens', 0)})")
    
    return extracted

if __name__ == '__main__':
    # A simple test function can be added here if needed
    print("This script is intended to be called from ai_feedback_criterion.py")
