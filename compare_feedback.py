#!/usr/bin/env python3
"""
Run the full AI feedback pipeline with multiple models and compare quality.

For each model: runs all criteria, then generates a side-by-side comparison
document. Optionally uses an LLM judge to score each model's feedback on
Accuracy, Specificity, and Actionability.

Usage:
    python compare_feedback.py /path/to/student/repo
    python compare_feedback.py /path/to/repo --models meta-llama/llama-4-scout google/gemini-2.0-flash-001
    python compare_feedback.py /path/to/repo --judge meta-llama/llama-4-maverick
    python compare_feedback.py /path/to/repo --output-dir ./comparison-results
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from datetime import datetime

import requests

SCRIPT_DIR = Path(__file__).parent / 'dot_github_folder' / 'scripts'
sys.path.insert(0, str(SCRIPT_DIR))

DEFAULT_MODELS = [
    'google/gemma-4-26b-a4b-it',
    'meta-llama/llama-4-scout',
    'meta-llama/llama-4-maverick',
    'google/gemini-2.0-flash-001',
]

DEFAULT_EXTRACTOR = 'meta-llama/llama-4-scout'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def strip_json_fences(text: str) -> str:
    text = text.strip()
    if text.startswith('```'):
        lines = text.splitlines()
        text = '\n'.join(lines[1:-1] if lines[-1].strip().startswith('```') else lines[1:])
    return text.strip()


def _extract_first_json_object(text: str) -> str | None:
    """Extract the first complete JSON object using a string-aware bracket matcher.

    Unlike a naive depth counter, this skips over characters inside quoted
    strings (including escape sequences), so braces like {"x": "formula {y}"}
    don't trip it up.
    """
    start = text.find('{')
    if start < 0:
        return None
    depth = 0
    in_string = False
    escape = False
    for i, ch in enumerate(text[start:], start):
        if escape:
            escape = False
            continue
        if ch == '\\' and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def safe_parse_json(text: str):
    """Parse JSON from model output, handling fences and surrounding prose."""
    if not text:
        return None
    # 1. Direct parse
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    # 2. Strip markdown fences
    try:
        return json.loads(strip_json_fences(text))
    except Exception:
        pass
    # 3. String-aware bracket extraction (handles unbalanced braces in strings,
    #    trailing prose, preambles, etc.)
    try:
        candidate = _extract_first_json_object(text)
        if candidate:
            return json.loads(candidate)
    except Exception:
        pass
    return None


def model_short(model_id: str) -> str:
    """e.g. google/gemini-2.0-flash-001 -> gemini-2.0-flash"""
    name = model_id.split('/')[-1]
    return re.sub(r'-\d{3}$', '', name)   # strip trailing version like -001


# ---------------------------------------------------------------------------
# Run one model across all criteria
# ---------------------------------------------------------------------------

def run_model(model_id: str, criterion_messages: dict, config: dict,
              provider_config: dict) -> dict:
    """
    Run feedback for all criteria with the given model.

    Returns {criterion_name: {success, feedback, elapsed, tokens, error}}
    """
    from ai_provider import call_ai

    pc = {**provider_config, 'model': model_id, 'fallback': model_id,
          'extractor': model_id, 'extractor_fallback': model_id}

    results = {}
    for name, messages in criterion_messages.items():
        if messages is None:
            results[name] = {'success': False, 'error': 'extraction failed',
                             'feedback': None, 'elapsed': 0, 'tokens': {}}
            continue

        start = time.time()
        text = ''
        response_data = {}
        error = None

        try:
            text, response_data, _ = call_ai(
                messages, model_id, config,
                provider_config=pc,
                json_mode=True,
            )
        except Exception as e:
            error = str(e)

        elapsed = time.time() - start
        usage = response_data.get('usage', {})
        feedback = safe_parse_json(text) if text else None
        parse_failed = text and not feedback and not error

        status = '✓' if (feedback and not error) else '✗'
        tok = usage.get('completion_tokens', 0)
        tps = tok / elapsed if elapsed > 0 and tok > 0 else 0
        suffix = f"  ⚠ {error[:40]}" if error else ("  ⚠ JSON parse failed" if parse_failed else '')
        print(f"   [{status}] {name[:45]:<45}  {elapsed:5.1f}s  {tok:4d} tok  {tps:5.1f} tps{suffix}")

        results[name] = {
            'success': feedback is not None and error is None,
            'feedback': feedback,
            'elapsed': elapsed,
            'tokens': usage,
            'raw_text': text[:2000] if parse_failed else None,
            'error': error,
        }

    return results


# ---------------------------------------------------------------------------
# Automated quality metrics
# ---------------------------------------------------------------------------

def auto_metrics(feedback: dict) -> dict:
    """Compute simple quality metrics from a parsed feedback dict."""
    if not feedback:
        return {}

    summary_words = len(feedback.get('summary', '').split())
    strengths = feedback.get('strengths', [])
    improvements = feedback.get('areas_for_improvement', [])

    # Suggestion concreteness: avg word count of suggestion texts
    suggestion_texts = []
    for item in improvements:
        if isinstance(item, dict):
            suggestion_texts.append(item.get('suggestion', ''))
        elif isinstance(item, str):
            suggestion_texts.append(item)
    avg_suggestion_len = (
        sum(len(s.split()) for s in suggestion_texts) / len(suggestion_texts)
        if suggestion_texts else 0
    )

    return {
        'assessment': feedback.get('overall_assessment', ''),
        'summary_words': summary_words,
        'n_strengths': len(strengths),
        'n_improvements': len(improvements),
        'avg_suggestion_words': round(avg_suggestion_len, 1),
        'has_score': 'score' in feedback,
        'score': feedback.get('score'),
    }


# ---------------------------------------------------------------------------
# LLM judge
# ---------------------------------------------------------------------------

JUDGE_SYSTEM = """You are an expert evaluator of AI-generated academic feedback.
You will be given a rubric criterion, a student's report excerpt, and feedback
written by an AI model. Rate the feedback on three dimensions (1–5 each):

- Accuracy (1–5): Does the feedback correctly identify the quality of the work
  relative to the rubric? Does the overall assessment seem right?
- Specificity (1–5): Does the feedback cite specific evidence from the report
  (equations, figures, measurements, section names)? Or is it generic?
- Actionability (1–5): Are the improvement suggestions concrete and achievable?
  Could the student act on them without guessing what to do?

Return ONLY a JSON object with keys: accuracy, specificity, actionability, rationale
(rationale is one sentence explaining your scores)."""


def judge_feedback(criterion_name: str, criterion_desc: str, rubric_levels: str,
                   report_excerpt: str, model_id: str, feedback: dict,
                   judge_model: str, config: dict, provider_config: dict) -> dict:
    from ai_provider import call_ai

    feedback_text = json.dumps(feedback, indent=2)
    user_msg = f"""## Criterion: {criterion_name}
{criterion_desc}

### Rubric levels:
{rubric_levels}

### Report excerpt (relevant sections):
{report_excerpt[:3000]}

### AI feedback to evaluate (from model: {model_short(model_id)}):
{feedback_text}"""

    messages = [
        {'role': 'system', 'content': JUDGE_SYSTEM},
        {'role': 'user', 'content': user_msg},
    ]

    pc = {**provider_config, 'model': judge_model, 'fallback': judge_model}

    try:
        text, _, _ = call_ai(messages, judge_model, config,
                              provider_config=pc, json_mode=True)
        scores = safe_parse_json(text)
        if scores and all(k in scores for k in ('accuracy', 'specificity', 'actionability')):
            return scores
        return {'accuracy': None, 'specificity': None, 'actionability': None,
                'rationale': 'parse error', 'raw': text[:200]}
    except Exception as e:
        return {'accuracy': None, 'specificity': None, 'actionability': None,
                'rationale': str(e)[:100]}


# ---------------------------------------------------------------------------
# Comparison document
# ---------------------------------------------------------------------------

def rubric_levels_text(criterion: dict) -> str:
    levels = criterion.get('levels', {})
    lines = []
    for level_name, info in levels.items():
        pr = info.get('point_range', ['?', '?'])
        lines.append(f"- **{level_name.title()}** ({pr[0]}–{pr[1]}): {info.get('description', '')}")
    return '\n'.join(lines)


def write_judge_briefing(output_path: Path, repo_name: str, models: list,
                         criteria: list, all_results: dict,
                         criterion_contexts: dict):
    """Write a self-contained briefing file for LLM judge evaluation."""
    short = {m: model_short(m) for m in models}

    lines = [
        f"# Judge Briefing: {repo_name}",
        f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "\n## Your Task",
        "\nEvaluate the quality of AI-generated feedback on a student physics lab report.",
        "For each criterion, you will see what the student wrote and what each model said.",
        "\nRate each model's feedback on three dimensions (1–5):",
        "- **Accuracy**: Does the assessment correctly reflect the quality of the student's work relative to the rubric?",
        "- **Specificity**: Does it cite specific evidence from the report (equations, figures, measurements)?",
        "- **Actionability**: Are the improvement suggestions concrete and achievable?",
        "\nAlso note any cases where a model seems clearly wrong, hallucinated, or missed something important.",
        "\n## Models Under Evaluation\n",
    ]
    for m in models:
        lines.append(f"- `{m}`")

    lines.append("\n---\n")

    for criterion in criteria:
        name = criterion['name']
        lines += [
            f"## Criterion: {name}\n",
            f"**Description:** {criterion.get('description', '')}\n",
            f"**Rubric levels:**\n{rubric_levels_text(criterion)}\n",
            f"**What the student wrote (extracted context):**\n",
            "```",
            criterion_contexts.get(name, '(not available)'),
            "```\n",
        ]

        for model_id in models:
            r = all_results.get(model_id, {}).get(name, {})
            fb = r.get('feedback')
            lines.append(f"### Feedback from `{short[model_id]}`")

            if not r.get('success') or not fb:
                lines.append(f"*Failed — no feedback available*\n")
                continue

            assessment = fb.get('overall_assessment', '—')
            score = fb.get('score')
            score_str = f" (score: {score})" if score is not None else ''
            lines.append(f"**Assessment:** {assessment}{score_str}\n")

            summary = fb.get('summary', '')
            if summary:
                lines.append(f"**Summary:** {summary}\n")

            strengths = fb.get('strengths', [])
            if strengths:
                lines.append("**Strengths:**")
                for s in strengths:
                    lines.append(f"- {s}")
                lines.append('')

            improvements = fb.get('areas_for_improvement', [])
            if improvements:
                lines.append("**Areas for improvement:**")
                for item in improvements:
                    if isinstance(item, dict):
                        lines.append(f"- *{item.get('issue', '')}* — {item.get('suggestion', '')}")
                    else:
                        lines.append(f"- {item}")
                lines.append('')

        lines.append('---\n')

    lines += [
        "## Suggested Prompt",
        "\nCopy and paste this to your LLM of choice:\n",
        "```",
        f"I've shared a judge briefing file for a student physics lab report ({repo_name}).",
        "Please read it carefully and for each criterion, rate each model's feedback on:",
        "  - Accuracy (1-5): Does it correctly assess the student's work?",
        "  - Specificity (1-5): Does it cite specific evidence?",
        "  - Actionability (1-5): Are suggestions concrete and achievable?",
        "",
        "Then give an overall recommendation: which model produced the best feedback",
        "for this report, and why? Note any cases where a model was clearly wrong or",
        "hallucinated something not in the student's work.",
        "```",
    ]

    output_path.write_text('\n'.join(lines))
    print(f"Judge briefing:      {output_path}")


def write_comparison_doc(output_path: Path, repo_name: str, models: list,
                         criteria: list, all_results: dict,
                         judge_scores: dict, scoring_enabled: bool):
    """Write a Markdown comparison document."""
    short = {m: model_short(m) for m in models}

    lines = [
        f"# Feedback Quality Comparison: {repo_name}",
        f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"\nModels compared: {', '.join(short[m] for m in models)}",
        "\n---\n",
        "## Summary Table\n",
    ]

    # Assessment matrix
    header = '| Criterion | ' + ' | '.join(short[m] for m in models) + ' |'
    sep    = '|---' * (len(models) + 1) + '|'
    lines += [header, sep]

    for criterion in criteria:
        name = criterion['name']
        cells = []
        for model_id in models:
            r = all_results.get(model_id, {}).get(name, {})
            fb = r.get('feedback') or {}
            assessment = fb.get('overall_assessment', '—') if r.get('success') else '✗'
            score = fb.get('score')
            if scoring_enabled and score is not None:
                cells.append(f"{assessment} ({score})")
            else:
                cells.append(assessment)
        lines.append(f"| {name} | " + ' | '.join(cells) + ' |')

    # Automated metrics table
    lines += ["\n## Automated Metrics\n",
              "*(summary words / # strengths / # improvements / avg suggestion length)*\n"]
    header2 = '| Criterion | ' + ' | '.join(short[m] for m in models) + ' |'
    lines += [header2, sep]

    for criterion in criteria:
        name = criterion['name']
        cells = []
        for model_id in models:
            r = all_results.get(model_id, {}).get(name, {})
            m = auto_metrics(r.get('feedback')) if r.get('success') else {}
            if m:
                cells.append(f"{m['summary_words']}w / {m['n_strengths']}s / "
                             f"{m['n_improvements']}i / {m['avg_suggestion_words']}w/sug")
            else:
                cells.append('—')
        lines.append(f"| {name} | " + ' | '.join(cells) + ' |')

    # Judge scores table (if available)
    if judge_scores:
        judge_model = judge_scores.get('_judge_model', 'judge')
        lines += [f"\n## LLM Judge Scores (model: {judge_model})\n",
                  "*(accuracy / specificity / actionability, each 1–5)*\n"]
        header3 = '| Criterion | ' + ' | '.join(short[m] for m in models) + ' |'
        lines += [header3, sep]
        for criterion in criteria:
            name = criterion['name']
            cells = []
            for model_id in models:
                s = judge_scores.get(model_id, {}).get(name, {})
                acc = s.get('accuracy')
                spe = s.get('specificity')
                act = s.get('actionability')
                if acc is not None:
                    avg = round((acc + spe + act) / 3, 1)
                    cells.append(f"{acc}/{spe}/{act} (avg {avg})")
                else:
                    cells.append('—')
            lines.append(f"| {name} | " + ' | '.join(cells) + ' |')

    # Per-criterion detail
    lines.append("\n---\n\n## Criterion-by-Criterion Detail\n")

    for criterion in criteria:
        name = criterion['name']
        lines += [f"### {name}\n",
                  f"**Description:** {criterion.get('description', '')}\n",
                  f"**Rubric levels:**\n{rubric_levels_text(criterion)}\n"]

        for model_id in models:
            r = all_results.get(model_id, {}).get(name, {})
            fb = r.get('feedback')
            lines.append(f"\n#### {short[model_id]}")

            if not r.get('success') or not fb:
                lines.append(f"*Failed: {r.get('error', 'unknown')}*\n")
                continue

            assessment = fb.get('overall_assessment', '—')
            score = fb.get('score')
            score_str = f" (score: {score})" if score is not None else ''
            lines.append(f"**Assessment:** {assessment}{score_str}\n")

            summary = fb.get('summary', '')
            if summary:
                lines.append(f"**Summary:** {summary}\n")

            strengths = fb.get('strengths', [])
            if strengths:
                lines.append("**Strengths:**")
                for s in strengths:
                    lines.append(f"- {s}")
                lines.append('')

            improvements = fb.get('areas_for_improvement', [])
            if improvements:
                lines.append("**Areas for improvement:**")
                for item in improvements:
                    if isinstance(item, dict):
                        lines.append(f"- *{item.get('issue', '')}* — {item.get('suggestion', '')}")
                    else:
                        lines.append(f"- {item}")
                lines.append('')

            # Judge rationale
            if judge_scores and model_id in judge_scores:
                s = judge_scores[model_id].get(name, {})
                if s.get('rationale'):
                    lines.append(f"*Judge: {s['rationale']}*\n")

        lines.append('\n---\n')

    output_path.write_text('\n'.join(lines))
    print(f"\nComparison document: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Compare AI feedback quality across models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('repo', help='Path to student repo')
    parser.add_argument('--models', nargs='+', default=DEFAULT_MODELS,
                        help='Models to compare')
    parser.add_argument('--extractor', default=DEFAULT_EXTRACTOR,
                        help=f'Model for text extraction (default: {DEFAULT_EXTRACTOR})')
    parser.add_argument('--extractor-fallback', default='google/gemini-2.0-flash-001',
                        help='Fallback extractor model (default: google/gemini-2.0-flash-001)')
    parser.add_argument('--judge',
                        help='Model to use as LLM judge (optional, e.g. meta-llama/llama-4-maverick)')
    parser.add_argument('--scoring', action='store_true',
                        help='Enable numerical scoring')
    parser.add_argument('--provider', default='openrouter')
    parser.add_argument('--session-id',
                        help='OpenRouter session_id for grouping calls in logs')
    parser.add_argument('--output-dir', default='.',
                        help='Directory to save comparison output (default: .)')
    parser.add_argument('--skip-extraction', action='store_true',
                        help='Reuse cached prompts from a previous run (saved in output-dir)')
    args = parser.parse_args()

    repo_path = Path(args.repo).resolve()
    if not (repo_path / 'index.qmd').exists():
        print(f"❌ No index.qmd in: {repo_path}")
        sys.exit(1)

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    original_cwd = Path.cwd()
    os.chdir(repo_path)

    try:
        from ai_provider import resolve_provider_config
        from ai_feedback_criterion import (
            load_config, load_rubric, load_guidance, load_report,
            get_criterion_guidance, build_criterion_prompt, build_ai_messages,
        )

        config = load_config()
        rubric = load_rubric()
        guidance = load_guidance()
        report = load_report()
        criteria = rubric.get('criteria', [])

        if not criteria:
            print("❌ No criteria in rubric")
            sys.exit(1)

        os.environ['AI_PROVIDER'] = args.provider
        os.environ['AI_EXTRACTOR_MODEL'] = args.extractor
        os.environ['AI_EXTRACTOR_FALLBACK_MODEL'] = args.extractor_fallback
        if args.session_id:
            os.environ['AI_SESSION_ID'] = args.session_id
        if args.scoring:
            os.environ['SCORING_ENABLED'] = 'true'
        provider_config = resolve_provider_config(config)

        api_key = provider_config.get('api_key')
        if not api_key:
            print(f"❌ No API key for '{args.provider}'")
            sys.exit(1)

        # ── Extract prompts (or load from cache) ─────────────────────────
        prompts_cache = (output_dir / 'criterion_prompts.json').resolve()

        if args.skip_extraction and prompts_cache.exists():
            print(f"\nLoading cached prompts from {prompts_cache.name}...")
            with open(prompts_cache) as f:
                cached = json.load(f)
            criterion_messages = cached['messages']
            criterion_contexts = cached['contexts']
            for name in criterion_messages:
                print(f"  ✓ {name}")
        else:
            print(f"\nExtracting prompts with {args.extractor}...")
            criterion_messages = {}
            criterion_contexts = {}
            for criterion in criteria:
                try:
                    guidance_excerpt = get_criterion_guidance(guidance, criterion)
                    prompt, context, image_paths = build_criterion_prompt(
                        report, criterion, guidance_excerpt, config)
                    messages = build_ai_messages(prompt, config, image_paths=image_paths)
                    criterion_messages[criterion['name']] = messages
                    criterion_contexts[criterion['name']] = context
                    print(f"  ✓ {criterion['name']}")
                except Exception as e:
                    print(f"  ✗ {criterion['name']}: {e}")
                    criterion_messages[criterion['name']] = None
                    criterion_contexts[criterion['name']] = ''

            with open(prompts_cache, 'w') as f:
                json.dump({'messages': criterion_messages,
                           'contexts': criterion_contexts}, f)
            print(f"  (prompts cached to {prompts_cache.name})")

        # ── Run each model ────────────────────────────────────────────────
        all_results = {}
        for model_id in args.models:
            print(f"\n── {model_id}")
            all_results[model_id] = run_model(
                model_id, criterion_messages, config, provider_config)

            # Save this model's feedback.json
            safe_name = model_short(model_id)
            fb_path = (output_dir / f'feedback-{safe_name}.json').resolve()
            with open(fb_path, 'w') as f:
                json.dump(all_results[model_id], f, indent=2)

        # ── LLM judge ────────────────────────────────────────────────────
        judge_scores = {}
        if args.judge:
            print(f"\n── LLM Judge: {args.judge}")
            judge_scores['_judge_model'] = model_short(args.judge)
            for model_id in args.models:
                judge_scores[model_id] = {}
                for criterion in criteria:
                    name = criterion['name']
                    r = all_results.get(model_id, {}).get(name, {})
                    if not r.get('success') or not r.get('feedback'):
                        judge_scores[model_id][name] = {
                            'accuracy': None, 'specificity': None,
                            'actionability': None, 'rationale': 'no feedback to judge'}
                        continue
                    print(f"  Judging {model_short(model_id)} / {name[:40]}...", end='', flush=True)
                    scores = judge_feedback(
                        name,
                        criterion.get('description', ''),
                        rubric_levels_text(criterion),
                        criterion_contexts.get(name, ''),
                        model_id,
                        r['feedback'],
                        args.judge,
                        config,
                        provider_config,
                    )
                    judge_scores[model_id][name] = scores
                    acc = scores.get('accuracy', '?')
                    spe = scores.get('specificity', '?')
                    act = scores.get('actionability', '?')
                    extra = f"  ⚠ {scores['rationale'][:60]}" if acc is None and scores.get('rationale') else ''
                    print(f" acc={acc} spe={spe} act={act}{extra}")

        # ── Write comparison document and judge briefing ─────────────────
        doc_path = (output_dir / f'comparison-{repo_path.name}.md').resolve()
        write_comparison_doc(doc_path, repo_path.name, args.models,
                             criteria, all_results, judge_scores, args.scoring)

        briefing_path = (output_dir / f'judge-briefing-{repo_path.name}.md').resolve()
        write_judge_briefing(briefing_path, repo_path.name, args.models,
                             criteria, all_results, criterion_contexts)

        # ── Print summary ─────────────────────────────────────────────────
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)

        header = f"{'Model':<30} {'OK':>4}  " + "  ".join(
            f"{c['name'][:12]:>12}" for c in criteria)
        print(header)
        print('-' * len(header))

        for model_id in args.models:
            results = all_results.get(model_id, {})
            ok = sum(1 for r in results.values() if r.get('success'))
            n = len(criteria)
            assessments = []
            for criterion in criteria:
                r = results.get(criterion['name'], {})
                fb = r.get('feedback') or {}
                assessments.append((fb.get('overall_assessment') or '—')[:12])
            row = f"{model_short(model_id):<30} {ok}/{n}  " + "  ".join(
                f"{a:>12}" for a in assessments)
            print(row)

        if judge_scores and '_judge_model' not in judge_scores or True:
            if args.judge:
                print(f"\nJudge averages (acc/spe/act):")
                for model_id in args.models:
                    scores_list = [s for s in judge_scores.get(model_id, {}).values()
                                   if s.get('accuracy') is not None]
                    if scores_list:
                        avg_acc = sum(s['accuracy'] for s in scores_list) / len(scores_list)
                        avg_spe = sum(s['specificity'] for s in scores_list) / len(scores_list)
                        avg_act = sum(s['actionability'] for s in scores_list) / len(scores_list)
                        print(f"  {model_short(model_id):<30} {avg_acc:.1f} / {avg_spe:.1f} / {avg_act:.1f}")

        print(f"\nOutputs saved to: {output_dir}")

    finally:
        os.chdir(original_cwd)


if __name__ == '__main__':
    main()
