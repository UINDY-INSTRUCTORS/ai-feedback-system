# Testing AI Extraction in Enterprise Environment

This guide explains how to test the AI-based section extraction in your GitHub Enterprise environment with a real student report.

## Prerequisites

1. A student repository with a completed lab report (`index.qmd`)
2. Enterprise GitHub account with access to GitHub Models API
3. Appropriate permissions to push workflows

## Setup Steps

### 1. Choose a Test Repository

Pick a student repo with a substantial report (500+ words). For example:
```bash
cd lab-3-submissions/lab-3-student-123/
```

### 2. Copy Feedback System Files

```bash
# From the feedback-system-test directory, copy to student repo
cp -r /path/to/feedback-system-test/.github .
cp -r /path/to/feedback-system-test/scripts .

# Verify files are there
ls -la .github/feedback/
ls -la scripts/
```

### 3. Add New Scripts

Make sure these new files are included:
```bash
ls scripts/ai_section_extractor.py
ls scripts/ai_feedback_criterion_ai_extract.py
ls .github/workflows/test-extraction-methods.yml
```

### 4. Commit and Push

```bash
git add .github scripts
git commit -m "Add AI extraction testing system"
git push
```

### 5. Trigger the Test

Create a test tag to trigger the workflow:
```bash
git tag test-extraction-v1
git push origin test-extraction-v1
```

### 6. Monitor Progress

Watch the workflow run:
1. Go to GitHub repo → Actions tab
2. Look for "Test AI Extraction Methods" workflow
3. Click on the running workflow to see progress

### 7. Review Results

The workflow will:
- ✅ Parse the report
- ✅ Run deterministic extraction (keyword-based)
- ✅ Run AI extraction (LLM-based)
- ✅ Create comparison issue with results
- ✅ Upload artifacts for detailed inspection

**Check the issue** created by the workflow with label `extraction-comparison` for the comparison report.

**Download artifacts** from the workflow run to inspect:
- `feedback_deterministic.md` - Output from keyword method
- `feedback_ai.md` - Output from AI method
- `deterministic_output.log` - Execution log
- `ai_output.log` - Execution log with token counts
- `comparison_report.md` - Side-by-side comparison

## What to Look For

### Quality Indicators

1. **Relevant Section Detection**
   - Did AI extraction find sections the deterministic method missed?
   - Did AI extraction ignore irrelevant sections?
   - Are the extractions more focused with AI?

2. **Generalization**
   - Does AI work with non-standard section names?
   - Does it handle different report structures?
   - Would it work for PHYS-280 or EENG-340 reports?

3. **Token Efficiency**
   - Compare token usage between methods
   - Is AI extraction staying under 8000 token limit?
   - Check extraction call tokens vs evaluation call tokens

4. **Feedback Quality**
   - Is feedback more specific with AI extraction?
   - Does feedback reference the right parts of the report?
   - Any hallucinations or irrelevant comments?

### Expected Outcomes

**Deterministic Extraction:**
- Works well for EENG-320 reports with standard structure
- May miss content with non-standard naming
- Fast and predictable
- ~2500 tokens per criterion on average

**AI Extraction:**
- Works with any report structure
- Finds relevant content regardless of section names
- More focused extractions
- ~3500 tokens per criterion (extraction + evaluation)
- Extra 10 API calls per report

## Testing Different Courses

### Test PHYS-280 Report (Scientific Computing)

The deterministic extractor is tuned for EENG-320 circuits. Test with a PHYS-280 computational physics report to see how AI extraction handles different structure:

```bash
cd phys-280-student-repo/
# Copy files as above
git tag test-extraction-phys280-v1
git push origin test-extraction-phys280-v1
```

Expected: AI extraction should work, deterministic may fail.

### Test PHYS-230 Report (Lab Instrumentation)

```bash
cd phys-230-student-repo/
# Copy files as above
git tag test-extraction-phys230-v1
git push origin test-extraction-phys230-v1
```

Expected: Both may work if structure similar to EENG-320, but AI should be more robust.

### Test EENG-340 Report (Interfacing Lab)

```bash
cd eeng-340-student-repo/
# Copy files as above
git tag test-extraction-eeng340-v1
git push origin test-extraction-eeng340-v1
```

Expected: AI extraction should adapt to different criterion structure (9 criteria vs 10).

## Interpreting Token Usage

### Example Output

```
Deterministic Method:
  Extraction: 0 tokens (no AI calls)
  Evaluation: 2500 tokens/criterion
  Total: 25,000 tokens for 10 criteria

AI Method:
  Extraction: 3500 tokens/criterion (gpt-4o-mini)
  Evaluation: 2000 tokens/criterion (gpt-4o)
  Total: 55,000 tokens for 10 criteria
```

**Analysis:**
- AI uses ~2.2x more tokens
- Still well under rate limits (150 calls/day)
- Extra cost negligible in free tier

### Enterprise Token Limits

With enterprise/education account:
- 5,000 requests/hour (vs 15/min personal)
- Higher per-request limits
- Can easily handle 20 calls per report

## Rate Limit Monitoring

Check rate limit usage after test:
```bash
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://models.inference.ai.azure.com/rate_limit_status
```

## Troubleshooting

### Issue: "AI extraction failed"

**Check:**
1. GITHUB_TOKEN has correct permissions
2. GitHub Models API is accessible from Actions
3. Model `gpt-4o-mini` is available
4. Report parsed successfully (check `parsed_report.json`)

**Solution:**
Look at `ai_output.log` in artifacts for error details.

### Issue: "Both methods produced similar output"

**Possible reasons:**
1. Report already uses standard EENG-320 structure
2. Test with more diverse report structures
3. Try a report with unconventional section names

### Issue: "Workflow didn't run"

**Check:**
1. Tag name starts with `test-extraction-`
2. Workflow file is in `.github/workflows/`
3. Repository has Actions enabled
4. You have push permissions

## Success Criteria

Consider AI extraction successful if:

- ✅ Works with reports from multiple courses
- ✅ Extracts relevant sections consistently
- ✅ Stays within token limits (< 8000 per call)
- ✅ Produces equal or better quality feedback
- ✅ Handles non-standard section naming
- ✅ Completes within 90 seconds for 10 criteria

## Next Steps After Testing

1. **Review with instructors** - Show comparison reports
2. **Gather feedback** - Is extracted content appropriate?
3. **Optimize prompts** - Refine extraction instructions
4. **Decision point** - Deploy AI extraction as default?
5. **Update documentation** - If adopting, update main README
6. **Remove legacy code** - Deprecate `section_extractor.py`

## Rollback Plan

If AI extraction doesn't work well:

1. Keep deterministic as default
2. Use AI extraction only for specific courses
3. Create hybrid approach (AI for unsupported courses)
4. Investigate prompt improvements

## Cost Projection

Assuming 5 reports/day × 3 days/week × 12 weeks:
- Reports per semester: ~180
- API calls with AI extraction: 3,600
- Well under free tier limits
- Cost: $0

## Questions?

See `scripts/AI_EXTRACTION_README.md` for detailed technical documentation.
