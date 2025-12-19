# AI-Based Section Extraction

## Overview

This document explains the new AI-based section extraction approach that replaces the brittle keyword-based extraction system.

## The Problem

The original system (`section_extractor.py`) uses deterministic keyword matching to extract relevant sections:

```python
def extract_simulation_sections(content, structure, keywords):
    # Look for PreLab sections
    prelab_pattern = r'##\s*PreLab.*?(?=##\s*(?:PreLab|Report|Lab|$))'
    # Look for figures with "sim" or "circuit" in filename
    figure_pattern = r'!\[.*?\]\(.*?(?:sim|circuit|schematic).*?\)'
    # ...
```

**Problems with this approach:**
- **Course-specific**: Hardcoded patterns like "PreLab" only work for EENG-320
- **Brittle**: Fails if students use different section names
- **Limited**: Can't understand context, only matches keywords
- **Maintenance burden**: Need different extraction logic for each course
- **Poor generalization**: Doesn't adapt to different report structures

## The Solution: AI-Based Extraction

Instead of hardcoded patterns, use the AI to intelligently extract relevant sections based on the rubric criterion.

### How It Works

1. **Input**: Full report + Rubric criterion (name, description, keywords)
2. **AI Task**: "Extract only the sections relevant to evaluating [criterion]"
3. **Output**: Focused excerpt (1000-2500 words) containing only relevant content
4. **Evaluation**: Use extracted content for the actual rubric evaluation

### Workflow Comparison

**Old (Deterministic):**
```
Report → parse_report.py → Parsed structure
                              ↓
                    section_extractor.py (keyword matching)
                              ↓
                      Extracted sections
                              ↓
                    ai_feedback_criterion.py
                              ↓
                          Feedback
```

**New (AI-Based):**
```
Report → parse_report.py → Parsed structure
                              ↓
              ai_section_extractor.py (AI extraction)
                              ↓
                      Extracted sections
                              ↓
          ai_feedback_criterion_ai_extract.py
                              ↓
                          Feedback
```

## Benefits

### 1. Course-Agnostic
Works with any report structure - no need to know about "PreLab" or "Lab Report" sections.

### 2. Contextual Understanding
AI understands what "background knowledge" or "problem formulation" means, even if those exact words aren't used as section headings.

### 3. Adaptable
Automatically adapts to different writing styles and organizational patterns.

### 4. Maintainable
No need to write custom extraction logic for each course. Just provide the rubric.

### 5. Better Quality
AI can identify subtle relevance that keyword matching misses.

## Implementation Details

### AI Model Used
- **Extraction**: `gpt-4o-mini` (fast, cheap, good enough for extraction)
- **Evaluation**: `gpt-4o` (higher quality for actual feedback)

### Token Management
- **Extraction prompt**: ~2000-4000 tokens (report + instructions)
- **Extraction output**: ~1500-3000 tokens (focused excerpt)
- **Total per criterion**: ~3500-7000 tokens (within 8000 limit)

### API Calls Per Report
With 10 criteria:
- 10 extraction calls (gpt-4o-mini)
- 10 evaluation calls (gpt-4o)
- Total: 20 calls (still well under 150/day limit)

### Prompt Template

```
You are a technical report analyzer. Extract ONLY the sections relevant
to evaluating a specific rubric criterion.

Criterion: [Design Development]
Description: [Student designs solution...]
Keywords: [design, component, circuit, schematic]

Report Structure: [headings list]

Task:
1. Identify relevant sections
2. Extract verbatim (with headings)
3. Be selective - aim for 1000-2500 words
4. Include figure references

Report: [full content]

Extracted Sections:
```

## Usage

### Enable AI Extraction

```bash
# Set environment variable
export USE_AI_EXTRACTION=true

# Run feedback system
python scripts/ai_feedback_criterion_ai_extract.py
```

### Test Extraction Alone

```bash
# Test AI extraction on first criterion
python scripts/ai_section_extractor.py
```

Output saved to `ai_extracted_section.txt` for inspection.

### Compare Methods

```bash
# Run with deterministic extraction
USE_AI_EXTRACTION=false python scripts/ai_feedback_criterion_ai_extract.py

# Run with AI extraction
USE_AI_EXTRACTION=true python scripts/ai_feedback_criterion_ai_extract.py

# Compare feedback.md outputs
```

## Example: Circuit Function Criterion

### Deterministic Extraction (Old)
```python
# Looks for:
- "Lab Report" section heading
- Figures with "photo" or "lab" in filename
- Mentions of "test" or "measure"
- Data files in data/ directory
```

**Result**: May miss relevant content if student uses different naming.

### AI Extraction (New)
```
Prompt: "Extract sections about circuit construction and validation"

AI identifies:
- "Hardware Implementation" section (not called "Lab Report")
- Discussion of test results (even without explicit "test" keyword)
- Photos showing circuit (regardless of filename)
- Validation measurements (understands context)
```

**Result**: Captures all relevant content regardless of naming conventions.

## Testing Results

*To be filled in after testing on real student reports*

### Test 1: PHYS-230 Lab Report
- Extraction time: [TBD]
- Relevant sections identified: [TBD]
- Comparison vs deterministic: [TBD]

### Test 2: PHYS-280 Assignment
- Extraction time: [TBD]
- Code sections extracted: [TBD]
- Comparison vs deterministic: [TBD]

### Test 3: EENG-340 Project
- Extraction time: [TBD]
- Multi-section extraction: [TBD]
- Comparison vs deterministic: [TBD]

## Cost Analysis

### Deterministic (Old)
- 10 evaluation calls × ~2500 tokens = ~25K tokens
- Cost: $0 (within free tier)

### AI-Based (New)
- 10 extraction calls × ~3500 tokens (gpt-4o-mini) = ~35K tokens
- 10 evaluation calls × ~3000 tokens (gpt-4o) = ~30K tokens
- Total: ~65K tokens
- Cost: $0 (within free tier)

**Conclusion**: ~2.5x more tokens but still well within free tier limits and rate limits.

## Migration Path

### Phase 1: Testing (Current)
- Both systems available
- Toggle with `USE_AI_EXTRACTION` flag
- Compare outputs side-by-side

### Phase 2: Soft Launch
- Default to AI extraction
- Keep deterministic as fallback
- Gather feedback from instructors

### Phase 3: Full Migration
- Remove deterministic extraction
- Simplify codebase
- Update documentation

## Files

### New Files
- `ai_section_extractor.py` - AI-based extraction logic
- `ai_feedback_criterion_ai_extract.py` - Modified feedback script with AI extraction
- `AI_EXTRACTION_README.md` - This documentation

### Modified Files
- None yet (keeping old system for comparison)

### Legacy Files (to deprecate)
- `section_extractor.py` - Will be removed after testing
- `ai_feedback_criterion.py` - Will be replaced by AI version

## Next Steps

1. **Test on real student reports** - Run both methods and compare
2. **Measure quality** - Ask instructors which extractions are more relevant
3. **Optimize prompts** - Refine extraction instructions based on results
4. **Add caching** - Cache extractions to avoid re-running
5. **Performance tuning** - Parallelize extraction calls for speed

## Questions & Concerns

### Q: Is AI extraction reliable?
**A**: More reliable than keyword matching because it understands context. Can handle varied writing styles and section names.

### Q: What if extraction misses something?
**A**: The evaluation prompt can still ask for specific aspects. AI extraction is a pre-filter, not a hard constraint.

### Q: Does this increase costs?
**A**: Minimal - still within free tier. Using gpt-4o-mini for extraction keeps costs low.

### Q: Is it slower?
**A**: Slightly (~2x API calls), but can parallelize. Still completes in ~60 seconds for 10 criteria.

### Q: What about rate limits?
**A**: 20 calls per report << 150/day limit. Even with 7 reports/day, only 140 calls.

## Conclusion

AI-based extraction makes the feedback system truly course-agnostic and maintainable. The small increase in API calls is worth the dramatic improvement in flexibility and robustness.
