# Vision Support Implementation TODO

## Status: Foundation Complete, Implementation Pending

### Completed ✅
1. **Image utilities** (`image_utils.py`)
   - Base64 encoding with/without PIL
   - Image resizing for token efficiency
   - Token estimation for images
   - Image validation
   - Filter images by token budget

2. **Vision configuration** (`.github/config.yml`)
   - Enable/disable flag
   - Max images per criterion
   - Resize settings
   - Token budget
   - Image priority keywords

3. **Existing infrastructure**
   - `parse_report.py` already extracts image references:
     ```python
     figure_refs = re.findall(r'!\[(.*?)\]\((.*?)\)', body)
     figure_paths = [ref[1] for ref in figure_refs]
     ```

### Remaining Implementation

#### 1. Modify `section_extractor.py`

**Current**: Returns only text content for each criterion

**Needed**: Also return relevant image paths

```python
def extract_sections_for_criterion_ai(...) -> tuple:
    """
    Returns:
        tuple: (text_content, image_paths)
    """
    # ... existing text extraction ...

    # NEW: Extract relevant images
    if vision_enabled:
        relevant_images = extract_relevant_images(
            report,
            criterion,
            config['vision']
        )
    else:
        relevant_images = []

    return extracted_text, relevant_images


def extract_relevant_images(report, criterion, vision_config):
    """
    Extract images relevant to a criterion.

    Logic:
    1. Get all images referenced in report (from parse_report.py output)
    2. Filter by criterion keywords (match caption or filename)
    3. Apply priority ordering (schematics > simulations > photos)
    4. Limit by max_images_per_criterion
    5. Check token budget

    IMPORTANT: Only use images that are in report['figures']['paths']
               Don't scan filesystem for unreferenced images
    """
    all_figure_paths = report.get('figures', {}).get('paths', [])
    all_captions = report.get('figures', {}).get('captions', [])

    # Match images to criterion
    relevant = []
    for path, caption in zip(all_figure_paths, all_captions):
        if is_image_relevant(path, caption, criterion, vision_config):
            relevant.append(path)

    # Apply priority and limits
    relevant = prioritize_images(relevant, vision_config['image_priority'])
    relevant = relevant[:vision_config['max_images_per_criterion']]

    # Check token budget
    relevant, tokens = filter_images_by_token_budget(
        relevant,
        vision_config['image_token_budget'],
        vision_config.get('resize_max_dimension')
    )

    return relevant
```

#### 2. Modify `ai_feedback_criterion.py`

**Current**: Sends only text to API

**Needed**: Include images in API call

```python
def build_criterion_prompt(report, criterion, guidance_excerpt):
    """
    Returns:
        tuple: (prompt, context_text, image_paths)  # ADD image_paths
    """
    # ... existing code ...

    # NEW: Extract images if vision enabled
    if vision_enabled:
        prompt, context, images = build_criterion_prompt_with_vision(...)
    else:
        images = []

    return prompt, context, images


def call_github_models_api(prompt, model, images=None):
    """
    Modified to handle vision requests.

    If images provided, format message content as array:
    {
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": base64_data}},
            {"type": "image_url", "image_url": {"url": base64_data}},
            ...
        ]
    }
    """
    if images:
        # Encode images to base64
        encoded_images = []
        for img_path in images:
            base64_data = encode_image_to_base64(
                img_path,
                max_dimension=config['vision'].get('resize_max_dimension')
            )
            if base64_data:
                encoded_images.append(base64_data)

        # Build vision message
        content = [{"type": "text", "text": prompt}]
        for img_data in encoded_images:
            content.append({
                "type": "image_url",
                "image_url": {"url": img_data}
            })

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": content}  # Array format
            ],
            ...
        }
    else:
        # Standard text-only request (current code)
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}  # String format
            ],
            ...
        }
```

#### 3. Update Prompts for Visual Analysis

**When images included**, add to prompt:

```python
if images:
    prompt += """

## Images Provided

You have been provided with {len(images)} image(s) related to this criterion.
Please analyze these images and incorporate your visual observations into the feedback:

- For circuit schematics: Verify component values, connections, proper symbols
- For simulations: Check waveforms match expectations, proper scaling, labeling
- For oscilloscope screenshots: Verify measurements, trigger settings, signal quality
- For lab photos: Check proper setup, wiring, equipment configuration

Reference specific images in your feedback (e.g., "In the schematic shown...")
"""
```

#### 4. Update Debug Mode

Save image paths and metadata in debug output:

```json
{
  "criterion_id": "circuit_design",
  "images_included": [
    "images/circ111.png",
    "images/sim111.png"
  ],
  "image_tokens_used": 850,
  "image_metadata": [
    {"path": "images/circ111.png", "tokens": 425, "size": "800x600"},
    {"path": "images/sim111.png", "tokens": 425, "size": "1024x768"}
  ]
}
```

### Testing Plan

1. **Test with vision disabled** (default) - should work as before
2. **Enable vision, test with simple report** (1-2 images)
3. **Test image filtering** - verify only referenced images used
4. **Test priority ordering** - schematics preferred over photos
5. **Test token budget** - large images properly limited
6. **Test resize** - images reduced to save tokens
7. **Verify quality** - does AI provide useful visual feedback?

### Implementation Priority

1. **High Priority**:
   - Circuit schematics analysis (most valuable for EENG courses)
   - Simulation screenshot analysis

2. **Medium Priority**:
   - Oscilloscope screenshot analysis
   - Image token management

3. **Low Priority**:
   - Lab photo analysis (quality varies greatly)
   - Hand-drawn diagram analysis

### Dependencies

**Required packages** (add to workflow):
```yaml
- name: Install dependencies
  run: |
    pip install pyyaml requests pillow  # Add pillow for image resizing
```

**Optional** (graceful degradation without PIL):
- If PIL not available, skip resizing
- Use `encode_image_simple()` instead

### Known Limitations

1. **Token costs**: Images expensive (500-1000 tokens each)
2. **API limits**: GPT-4V max 10 images per request (we limit to 3)
3. **Quality variance**: AI vision better at diagrams than photos
4. **False positives**: May hallucinate details not present

### Recommendation

Start with **schematics only**:
1. Enable vision for criteria related to circuit design
2. Limit to 1-2 schematics per criterion
3. Monitor feedback quality and token usage
4. Expand to simulations if successful

### Example Use Case

**Criterion**: "Circuit Design and Component Selection"

**Without vision**:
- AI reads text: "We used a 2.2kΩ resistor..."
- Cannot verify schematic matches description

**With vision**:
- AI sees schematic image
- Verifies: "The schematic shows a 2.2kΩ resistor at R1, correctly connected..."
- Catches: "However, the capacitor value in the schematic (0.22µF) differs from the text (0.25µF)"

This is the killer feature for engineering lab reports!
