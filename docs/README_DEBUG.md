# Debug Mode for AI Feedback System

## Overview

Debug mode captures detailed information about the feedback generation process, including:
- Full prompts sent to the AI
- AI responses (raw JSON)
- Extracted context sections
- Token usage and timing
- API request/response data

This is invaluable for:
- Understanding what context the AI sees for each criterion
- Debugging why feedback quality varies
- Optimizing prompts and context extraction
- Monitoring token usage
- Troubleshooting failures

## Enabling Debug Mode

### In config.yml

Edit `.github/feedback/config.yml`:

```yaml
debug_mode:
  enabled: true                    # Set to true to enable debug logging
  save_prompts: true               # Save full prompts sent to AI
  save_responses: true             # Save AI responses
  save_context: true               # Save extracted context/sections
  save_api_metadata: true          # Save token counts, model used, timing
  output_dir: ".github/debug"      # Where to save debug files
  timestamp_format: "%Y%m%d_%H%M%S"  # Timestamp format for session directories
  prettify_json: true              # Pretty-print JSON for readability

  # ⚠️  WARNING: Artifacts contain student work and grading prompts!
  upload_artifacts: false          # Upload to GitHub Actions artifacts
```

### Security Warning

**CRITICAL**: Debug artifacts contain sensitive information:
- **Student report content** (full text in context.txt)
- **Grading prompts** (rubric details, performance levels)
- **AI responses** (raw feedback before instructor review)

**Only enable `upload_artifacts: true` for:**
- Instructor-controlled test repositories
- Specific troubleshooting in private repos
- Research/development environments

**NEVER enable in:**
- Student-facing GitHub Classroom repos
- Repositories where students have admin/read access
- Production deployments

### Granular Control

You can enable/disable specific types of debug output:

```yaml
debug_mode:
  enabled: true
  save_prompts: true      # Only save prompts
  save_responses: false   # Don't save responses
  save_context: true      # Save context
  save_api_metadata: true # Save metadata
```

## Debug Output Structure

When debug mode is enabled, the system creates:

```
.github/debug/
├── 20251220_143022_feedback-v1/          # Timestamped session directory
│   ├── session_info.json                 # Overall session metadata
│   ├── combined_feedback.md              # Final combined feedback
│   ├── criteria/
│   │   ├── 01_problem_formulation/
│   │   │   ├── context.txt               # Extracted sections for this criterion
│   │   │   ├── prompt.txt                # Full prompt sent to AI
│   │   │   ├── request.json              # API request payload
│   │   │   ├── response.json             # API response (full)
│   │   │   ├── feedback.md               # Extracted feedback text
│   │   │   └── metadata.json             # Tokens, timing, model, etc.
│   │   ├── 02_design_development/
│   │   │   └── ...
│   │   └── ...
└── latest -> 20251220_143022_feedback-v1 # Symlink to most recent
```

## File Descriptions

### session_info.json

Overall session metadata:

```json
{
  "timestamp": "2025-12-20T14:30:22Z",
  "tag_name": "feedback-v1",
  "model_primary": "gpt-4o",
  "model_fallback": "gpt-4o-mini",
  "total_criteria": 10,
  "successful_criteria": 9,
  "failed_criteria": 1,
  "total_time_seconds": 62.4,
  "total_api_calls": 9,
  "total_tokens_prompt": 12847,
  "total_tokens_completion": 8932,
  "total_tokens": 21779,
  "report_file": "index.qmd",
  "report_word_count": 1287
}
```

### Per-Criterion Files

**context.txt** - The extracted sections relevant to this criterion:
```
Introduction (lines 12-45)

This lab explores the behavior of BJT transistors...

Figure: objectives.png
[Image description would be here if images were included]

Objectives (lines 46-78)
- Design a common-emitter amplifier
- Measure gain and frequency response
```

**prompt.txt** - The complete prompt sent to the AI:
```
You are an expert instructor providing feedback on a student report.

## Feedback Philosophy
- Be specific and actionable
- Start with strengths before improvements
...

## Your Task

Evaluate the following criterion based on the relevant sections...
```

**request.json** - The API request payload (without auth token):
```json
{
  "model": "gpt-4o",
  "messages": [
    {
      "role": "system",
      "content": "You are an expert instructor..."
    },
    {
      "role": "user",
      "content": "..."
    }
  ],
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**response.json** - The full API response:
```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "created": 1703097622,
  "model": "gpt-4o",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "### Problem Formulation\n**Assessment**: Satisfactory\n\n..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 1243,
    "completion_tokens": 892,
    "total_tokens": 2135
  }
}
```

**feedback.md** - The extracted feedback text (message content only)

**metadata.json** - Analysis metadata:
```json
{
  "criterion_id": "problem_formulation",
  "criterion_name": "Problem Formulation",
  "criterion_index": 1,
  "timestamp": "2025-12-20T14:30:25Z",
  "model_used": "gpt-4o",
  "api_endpoint": "https://models.inference.ai.azure.com/chat/completions",
  "request_time_seconds": 3.2,
  "tokens": {
    "prompt_tokens": 1243,
    "completion_tokens": 892,
    "total_tokens": 2135
  },
  "success": true,
  "error": null,
  "context_word_count": 487,
  "context_estimated_tokens": 1156
}
```

## Using Debug Output

### Check What Context Was Extracted

```bash
# View context for a specific criterion
cat .github/debug/latest/criteria/01_problem_formulation/context.txt

# Check context for all criteria
for dir in .github/debug/latest/criteria/*/; do
    echo "=== $(basename $dir) ==="
    head -20 "$dir/context.txt"
    echo
done
```

### Analyze Token Usage

```bash
# Check token usage per criterion
jq '.tokens' .github/debug/latest/criteria/*/metadata.json

# Total tokens used
jq '.total_tokens' .github/debug/latest/session_info.json

# Average tokens per criterion
jq '.total_tokens / .total_api_calls' .github/debug/latest/session_info.json
```

### View Actual Prompts

```bash
# See what prompt was sent for a criterion
cat .github/debug/latest/criteria/01_problem_formulation/prompt.txt

# Compare prompts across criteria
diff .github/debug/latest/criteria/01_*/prompt.txt \
     .github/debug/latest/criteria/02_*/prompt.txt
```

### Debug Context Extraction Issues

If feedback quality is poor for a specific criterion:

1. **Check extracted context**:
   ```bash
   cat .github/debug/latest/criteria/02_design_development/context.txt
   ```

2. **Verify the right sections were extracted**:
   - Does it include relevant parts of the report?
   - Are important figures/tables included?
   - Is context too long or too short?

3. **Review the prompt**:
   ```bash
   cat .github/debug/latest/criteria/02_design_development/prompt.txt
   ```
   - Is the criterion description clear?
   - Are the performance levels well-defined?
   - Is the guidance helpful?

4. **Check the AI response**:
   ```bash
   cat .github/debug/latest/criteria/02_design_development/feedback.md
   ```

### Monitor Performance

```bash
# Time spent per criterion
jq -r '"\(.criterion_name): \(.request_time_seconds)s"' \
  .github/debug/latest/criteria/*/metadata.json

# Identify slow criteria
jq -r 'select(.request_time_seconds > 5) | "\(.criterion_name): \(.request_time_seconds)s"' \
  .github/debug/latest/criteria/*/metadata.json
```

## Accessing Debug Output

### Local Testing

Debug files are saved to `.github/debug/latest/`:

```bash
cd .github/debug/latest
ls -la
```

### GitHub Actions

Debug artifacts are **only uploaded when explicitly enabled**:

**To enable artifact upload:**

1. Edit `.github/feedback/config.yml`:
   ```yaml
   debug_mode:
     enabled: true
     upload_artifacts: true  # ⚠️  Enable with caution!
   ```

2. Commit and push the change (or test in a branch)

3. Trigger feedback generation (git tag)

4. Access artifacts:
   - Go to **Actions** tab in your repository
   - Click on the workflow run
   - Scroll to **Artifacts** section
   - Download `feedback-debug-<run-number>`
   - Extract and explore the files

**Recommended workflow for instructors:**
1. Keep `upload_artifacts: false` in student repos
2. Create a **separate test repository** under your control
3. Enable `upload_artifacts: true` in the test repo only
4. Test and debug there, then apply fixes to student template

## Security Considerations

**CRITICAL**: Debug output contains sensitive information:

- **Student report content** - Full text and extracted sections
- **Prompts** - May reveal grading strategies and rubric details
- **API responses** - Student-specific feedback before review

### Safety Measures

1. **`.github/debug/` is in `.gitignore`** - Debug files are never committed
2. **API tokens are filtered** - `GITHUB_TOKEN` is never saved to disk
3. **Artifacts are opt-in** - `upload_artifacts` must be explicitly enabled
4. **Artifacts expire** - GitHub Actions artifacts deleted after 30 days
5. **Local-only by default** - Debug files stay on your machine during local testing
6. **Validator warns** - Validation tool warns if `upload_artifacts: true`

### Best Practices

- **DO NOT commit debug files** to git
- **DO NOT enable `upload_artifacts` in student repos** - Students can download artifacts!
- **DO NOT share debug artifacts** publicly
- **Review debug output** before sharing with others
- **Use separate test repo** for debugging with artifacts enabled
- **Disable debug mode** in production (set `enabled: false`)
- **Use debug mode temporarily** for troubleshooting, then disable

### Risk Scenarios

**Scenario 1: Student Access**
```
Problem: Student has admin access to their GitHub Classroom repo
         upload_artifacts: true is set
         Student triggers feedback, downloads artifact
Result:  Student can see:
         - Exact prompts and rubric performance levels
         - How context extraction works
         - Internal grading criteria
```
**Solution**: Never enable `upload_artifacts` in student-accessible repos

**Scenario 2: Public Repository**
```
Problem: Repository is public
         Artifacts are uploaded
Result:  Anyone can download artifacts containing student work
```
**Solution**: Only use in private, instructor-controlled repos

**Scenario 3: Data Retention**
```
Problem: Artifacts stored for 30 days
         Multiple students' work accumulates
Result:  Potential privacy violation if repo access changes
```
**Solution**: Use `upload_artifacts` sparingly, clean up when done

## Common Use Cases

### 1. Optimizing Context Extraction

**Problem**: AI feedback mentions "insufficient information" for a criterion

**Debug Approach**:
1. Check `context.txt` - is the right content extracted?
2. Review `section_extractor.py` logic for that criterion
3. Adjust keywords or extraction strategy
4. Re-run with debug mode to verify improvement

### 2. Improving Prompt Quality

**Problem**: Feedback is too generic or doesn't follow the desired format

**Debug Approach**:
1. Read `prompt.txt` - is the guidance clear?
2. Check criterion description in rubric
3. Review `guidance.md` for that criterion type
4. Refine prompts and re-test

### 3. Token Budget Analysis

**Problem**: Hitting token limits or want to optimize costs

**Debug Approach**:
1. Check `session_info.json` for total token usage
2. Review per-criterion `metadata.json` to find expensive criteria
3. Identify if context extraction is too verbose
4. Adjust `max_input_tokens` in config.yml

### 4. Troubleshooting Failures

**Problem**: Feedback generation fails for specific criteria

**Debug Approach**:
1. Check `metadata.json` for error messages
2. Review `request.json` for malformed input
3. Check `response.json` for API error details
4. Examine `context.txt` for problematic content

## Disabling Debug Mode

To disable debug mode:

```yaml
debug_mode:
  enabled: false  # Set to false
```

Or remove the entire `debug_mode` section from config.yml.

**Note**: Debug files from previous runs are preserved even when debug mode is disabled.

## Cleanup

### Remove All Debug Output

```bash
# Local
rm -rf .github/debug/

# GitHub Actions artifacts expire automatically after 30 days
```

### Remove Specific Session

```bash
rm -rf .github/debug/20251220_143022_feedback-v1/
```

## FAQ

### Q: Does debug mode slow down feedback generation?

**A**: Negligibly. Debug mode adds < 0.1s per criterion for file I/O. The AI API calls dominate execution time.

### Q: How much disk space does debug output use?

**A**: Typically 1-5 MB per feedback session, depending on report length and number of criteria.

### Q: Can I use debug mode in production?

**A**: You can use `enabled: true` to save debug files locally, but keep `upload_artifacts: false` in student-facing deployments. This gives you debug output on your machine without exposing it via artifacts.

### Q: Why not just always upload artifacts?

**A**: Students in GitHub Classroom often have admin access to their repos. They can download workflow artifacts, which would expose:
- Your grading prompts and rubric internals
- How the system extracts context
- Evaluation criteria you may not want to reveal

Keep `upload_artifacts: false` in student repos to prevent this.

### Q: How do I debug student issues then?

**A**:
1. Create a separate instructor-controlled test repo
2. Copy the student's report to your test repo
3. Enable `upload_artifacts: true` in the test repo
4. Run feedback and download artifacts
5. Investigate and fix the issue
6. Apply the fix to the student template

### Q: What if symlinks don't work on my system?

**A**: The symlink to `latest/` is optional. If it fails, you can still access debug output by timestamp.

### Q: Can I change the output directory?

**A**: Yes, set `debug_mode.output_dir` in config.yml. Ensure the directory is in `.gitignore`.

### Q: How do I debug without saving everything?

**A**: Use granular control:
```yaml
debug_mode:
  enabled: true
  save_prompts: false
  save_responses: false
  save_context: true      # Only save context
  save_api_metadata: true # And metadata
```

## Advanced: Programmatic Analysis

### Python Script to Analyze Debug Output

```python
import json
from pathlib import Path

debug_dir = Path('.github/debug/latest')

# Load session info
with open(debug_dir / 'session_info.json') as f:
    session = json.load(f)

print(f"Session: {session['tag_name']}")
print(f"Total tokens: {session['total_tokens']}")
print(f"Success rate: {session['successful_criteria']}/{session['total_criteria']}")
print()

# Analyze each criterion
for criterion_dir in sorted((debug_dir / 'criteria').iterdir()):
    with open(criterion_dir / 'metadata.json') as f:
        meta = json.load(f)

    print(f"{meta['criterion_name']}:")
    print(f"  Tokens: {meta['tokens']['total_tokens']}")
    print(f"  Time: {meta['request_time_seconds']}s")
    print(f"  Context: {meta['context_word_count']} words")
    print()
```

## Support

If you encounter issues with debug mode:

1. Verify `debug_mode.enabled: true` in config.yml
2. Check file permissions on `.github/debug/`
3. Ensure sufficient disk space
4. Review error messages in console output
5. Check GitHub Actions logs if using workflows

For questions about interpreting debug output, consult the implementation plan or ask your instructor.
