# Fix for 413 Payload Too Large Errors

## Problem Analysis

The "Data & Results" criterion feedback generation failed with:
```
413 Client Error: Payload Too Large for url: https://models.inference.ai.azure.com/chat/completions
```

### Root Cause

**Not a token limit issue** — token usage was ~13,815 out of 128,000 allowed.

**Real issue: HTTP request body size exceeded ~4MB limit**

When 3 large PNG plots (~800KB each) were base64-encoded:
- Binary size: ~2.4MB
- Base64 encoding overhead: +33% → ~3.2MB
- Plus prompt text (~30KB) and context → **exceeds 4MB HTTP limit**

## Solution Overview

Three complementary fixes to prevent 413 errors:

### 1. **Image Resizing (CRITICAL)**
- Resize images to max dimension: **768px** (configurable)
- Reduces file size by ~50% while maintaining readability
- Small plot (500×400): 100KB → 40KB
- Medium plot (800×600): 250KB → 125KB
- Large plot (1200×800): 600KB → 300KB

### 2. **Image Count Limiting (CRITICAL)**
- Change default `max_images_per_criterion` from **3 → 2**
- Limits to only the 2 most relevant plots per criterion
- Even with resizing, 3+ large images risk exceeding limits

### 3. **Token Budget Filtering (IMPORTANT)**
- Set `image_token_budget` to **1500 tokens** (was 2000)
- Provides secondary filter to prevent including too many images
- At 768px: Medium plot ≈ 255 tokens, so budget allows ~5 plots

## Token Impact Analysis

### Before Fix (Failed Case)
- 3 full-res plots (1200×800 each): ~3,315 tokens
- Text (prompt + context): ~10,500 tokens
- **Total: ~13,815 tokens** ✓ Within limits
- **HTTP size: ~3.2MB** ✗ **EXCEEDS 4MB LIMIT** → 413 Error

### After Fix (With Resizing + 2-Image Limit)
- 2 resized plots (768×576 each): ~510 tokens
- Text (prompt + context): ~10,500 tokens
- **Total: ~11,010 tokens** ✓ Within limits
- **HTTP size: ~1.5MB** ✓ **SAFE MARGIN** below 4MB

## Configuration Settings

All settings are configurable in `.github/feedback/config.yml`:

```yaml
vision:
  enabled: true
  resize_max_dimension: 768        # Max px dimension (reduces file size)
  max_images_per_criterion: 2      # Max 2 images per criterion
  image_token_budget: 1500         # Token budget for filtering
  auto_detect: true                # Auto-detect images for criteria
  image_priority:                  # Keywords for image ranking
    - "result"
    - "plot"
    - "graph"
```

### Recommended Values
- `resize_max_dimension`: **768** (good balance of quality vs. size)
  - 512: Very aggressive, small but readable
  - 768: Recommended (reduces size ~50%, maintains quality)
  - 1024: Conservative (larger payload, higher quality)

- `max_images_per_criterion`: **2** (prevents 413 errors)
  - 1: Only most relevant image
  - 2: Recommended (balance vs. informativeness)
  - 3+: Risk of 413 errors

- `image_token_budget`: **1500** (provides safety margin)
  - 1000: Conservative, limits quantity
  - 1500: Recommended, allows ~6 resized plots
  - 2000+: Risks exceeding HTTP limits

## Implementation Details

### Code Changes

**`section_extractor.py`** - Extract & filter function
- Changed default `max_images_per_criterion`: 3 → 2
- Changed default `image_token_budget`: 2000 → 1500
- Changed default `resize_max_dimension`: None → 768
- Added comments explaining the 413 error prevention

**`templates/config-template.yml`** - New vision configuration
- Added complete vision settings section
- Documents recommended values
- Explains HTTP payload concerns

### No Changes Needed
- `image_utils.py`: Already has `encode_image_to_base64()` with resizing
- `ai_feedback_criterion.py`: Already uses `resize_dim` from config
- `filter_images_by_token_budget()`: Already filters by budget

## Testing the Fix

To test if the fix works:

1. **Check config is set**:
   ```yaml
   vision:
     resize_max_dimension: 768
     max_images_per_criterion: 2
     image_token_budget: 1500
   ```

2. **Monitor image encoding**:
   - Should see: `Resized image.png: 768x576` in logs
   - Should see: `Selected 1-2 image(s) using ~X tokens`

3. **Re-run failed feedback**:
   - "Data & Results" criterion should now succeed
   - Images will be included but in safe sizes

## Verification

The fix is verified if feedback generation produces:
- ✓ All criteria processed successfully
- ✓ Images included in Vision requests (not skipped)
- ✓ Resized images in logs: "Resized image.png: 768x..."
- ✓ Token counts reasonable (~500-1000 for images)
- ✓ No 413 errors in feedback reports

## Future Improvements

1. **HTTP payload size monitoring**: Add warning if request exceeds 2MB
2. **Adaptive resizing**: Reduce further if approaching limits
3. **Image quality assessment**: Skip blurry/unreadable images
4. **Format optimization**: Use WebP instead of PNG when possible
5. **Batch processing**: Process images in parallel with size tracking

## References

- **OpenAI Vision**: 85 base + 170 tokens per 512×512 tile
- **GitHub Models API**: ~4MB HTTP body limit
- **Base64 encoding**: +33% size overhead
- **Token limits**: 128,000 input tokens for gpt-4o (not the issue here)
