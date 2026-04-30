#!/usr/bin/env python3
"""
Benchmark candidate models for the AI feedback system.

For each model: runs one (or all) criteria against a real student repo,
measuring latency, token usage, cost, and output quality. Prints a
comparison table and optionally saves raw results as JSON.

Usage:
    python benchmark_models.py /path/to/student/repo
    python benchmark_models.py /path/to/repo --models google/gemma-4-9b-it meta-llama/llama-4-scout
    python benchmark_models.py /path/to/repo --all-criteria
    python benchmark_models.py /path/to/repo --no-vision
    python benchmark_models.py /path/to/repo --students 60 --reports 11
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).parent / 'dot_github_folder' / 'scripts'
sys.path.insert(0, str(SCRIPT_DIR))

DEFAULT_MODELS = [
    'google/gemma-4-26b-a4b-it',
    'meta-llama/llama-4-scout',
    'meta-llama/llama-4-maverick',
    'google/gemini-2.0-flash-001',
]

# Full run: 5 criteria × (1 extraction call + 1 feedback call)
CALLS_PER_REPORT = 10


# ---------------------------------------------------------------------------
# OpenRouter pricing
# ---------------------------------------------------------------------------

def fetch_openrouter_pricing(api_key: str) -> dict:
    """Return {model_id: {prompt: $/token, completion: $/token}}."""
    try:
        resp = requests.get(
            'https://openrouter.ai/api/v1/models',
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=10,
        )
        resp.raise_for_status()
        result = {}
        for m in resp.json().get('data', []):
            p = m.get('pricing', {})
            result[m['id']] = {
                'prompt': float(p.get('prompt', 0) or 0),
                'completion': float(p.get('completion', 0) or 0),
            }
        return result
    except Exception as e:
        print(f"  Warning: could not fetch OpenRouter pricing: {e}")
        return {}


def cost_for_result(r: dict, pricing: dict, model_id: str):
    p = pricing.get(model_id)
    if not p:
        return None
    return r['prompt_tokens'] * p['prompt'] + r['completion_tokens'] * p['completion']


# ---------------------------------------------------------------------------
# Output quality check
# ---------------------------------------------------------------------------

def strip_json_fences(text: str) -> str:
    text = text.strip()
    if text.startswith('```'):
        lines = text.splitlines()
        text = '\n'.join(lines[1:-1] if lines[-1].strip().startswith('```') else lines[1:])
    return text.strip()


def _extract_first_json_object(text: str) -> str | None:
    """String-aware bracket matcher — skips braces inside quoted strings."""
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
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    try:
        return json.loads(strip_json_fences(text))
    except Exception:
        pass
    try:
        candidate = _extract_first_json_object(text)
        if candidate:
            return json.loads(candidate)
    except Exception:
        pass
    return None


def check_quality(text: str) -> dict:
    """Return quality metrics for a feedback response."""
    out = {
        'json_valid': False,
        'field_score': 0,       # out of 4
        'assessment': '',
    }
    if not text:
        return out
    data = safe_parse_json(text)
    if data:
        out['json_valid'] = True
        required = ['summary', 'strengths', 'areas_for_improvement', 'overall_assessment']
        out['field_score'] = sum(1 for f in required if data.get(f))
        out['assessment'] = str(data.get('overall_assessment', ''))[:25]
    return out


# ---------------------------------------------------------------------------
# Single-model call
# ---------------------------------------------------------------------------

def test_model(model_id: str, messages: list, config: dict,
               provider_config: dict, criterion_name: str = '',
               criterion_index: int = 0, context: str = '', prompt: str = '') -> dict:
    from ai_provider import call_ai
    from ai_feedback_criterion import save_debug_criterion_data

    pc = {**provider_config, 'model': model_id, 'fallback': model_id,
          'extractor': model_id, 'extractor_fallback': model_id}

    start = time.time()
    text = ''
    response_data = {}
    request_payload = {}
    error = None

    try:
        text, response_data, request_payload = call_ai(
            messages, model_id, config,
            provider_config=pc,
            json_mode=True,
        )
    except Exception as e:
        error = str(e)[:100]

    elapsed = time.time() - start
    metadata = {
        'criterion_id': criterion_name,
        'criterion_index': criterion_index,
        'criterion_name': criterion_name,
        'model_used': model_id,
        'provider': pc.get('provider', ''),
        'success': error is None and bool(text),
    }
    if error:
        metadata['error'] = error
    save_debug_criterion_data(metadata, context, prompt, request_payload, response_data, text)
    usage = response_data.get('usage', {})
    prompt_tokens = usage.get('prompt_tokens', 0)
    completion_tokens = usage.get('completion_tokens', 0)
    tps = completion_tokens / elapsed if elapsed > 0 and completion_tokens > 0 else 0

    quality = check_quality(text) if text else {'json_valid': False, 'field_score': 0, 'assessment': ''}

    return {
        'success': error is None and bool(text),
        'elapsed': elapsed,
        'prompt_tokens': prompt_tokens,
        'completion_tokens': completion_tokens,
        'tps': tps,
        'error': error,
        **quality,
    }


# ---------------------------------------------------------------------------
# Aggregate multiple criteria runs
# ---------------------------------------------------------------------------

def aggregate(criterion_results: list) -> dict:
    """Average numeric fields; AND boolean success; collect errors."""
    if not criterion_results:
        return {'success': False, 'error': 'no results'}

    successes = [r for r in criterion_results if r['success']]
    n = len(criterion_results)

    def avg(key):
        vals = [r[key] for r in successes if r.get(key) is not None]
        return sum(vals) / len(vals) if vals else 0

    errors = [r['error'] for r in criterion_results if r.get('error')]

    return {
        'success': len(successes) == n,
        'success_rate': len(successes) / n,
        'n_criteria': n,
        'elapsed': avg('elapsed'),
        'prompt_tokens': avg('prompt_tokens'),
        'completion_tokens': avg('completion_tokens'),
        'tps': avg('tps'),
        'json_valid': all(r.get('json_valid') for r in successes) if successes else False,
        'field_score': avg('field_score'),
        'assessment': successes[0].get('assessment', '') if successes else '',
        'error': '; '.join(errors[:2]) if errors else None,
    }


# ---------------------------------------------------------------------------
# Results table
# ---------------------------------------------------------------------------

def print_table(results: dict, pricing: dict, models: list,
                n_students: int, n_reports: int):
    headers = ['Model', 'OK', 'Fields', 'Assessment', 'Time(s)', 'TPS',
               'OutTok', '$/call', f'$/{n_students}×{n_reports} class']

    rows = []
    for model_id in models:
        r = results.get(model_id)
        if r is None:
            continue
        if not r['success'] and r.get('success_rate', 0) == 0:
            rows.append([model_id, '✗', '-', (r.get('error') or 'failed')[:25],
                         f"{r['elapsed']:.1f}", '-', '-', '-', '-'])
            continue

        ok = ('✓' if r['success'] else
              f"~{r['success_rate']:.0%}")

        cost = cost_for_result(r, pricing, model_id)
        cost_str = f"${cost:.5f}" if cost is not None else '?'

        batch_cost = cost * n_students * n_reports * CALLS_PER_REPORT if cost is not None else None
        batch_str = f"${batch_cost:.2f}" if batch_cost is not None else '?'

        rows.append([
            model_id,
            ok,
            f"{r['field_score']:.1f}/4",
            r['assessment'] or '-',
            f"{r['elapsed']:.1f}",
            f"{r['tps']:.1f}",
            f"{r['completion_tokens']:.0f}",
            cost_str,
            batch_str,
        ])

    # Column widths
    widths = [max(len(str(row[i])) for row in [headers] + rows) for i in range(len(headers))]

    def fmt(row):
        return '  '.join(str(c).ljust(widths[i]) for i, c in enumerate(row))

    sep = '  '.join('-' * w for w in widths)
    print()
    print(fmt(headers))
    print(sep)
    for row in rows:
        print(fmt(row))
    print()
    print(f"Cost projection: {n_students} students × {n_reports} reports × {CALLS_PER_REPORT} calls/report")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Benchmark OpenRouter models for AI feedback',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('repo', nargs='?', help='Path to student repo')
    parser.add_argument('--models', nargs='+', default=DEFAULT_MODELS,
                        help='Models to benchmark (default: built-in list)')
    parser.add_argument('--criterion', type=int, default=0,
                        help='Index of criterion to test (default: 0)')
    parser.add_argument('--all-criteria', action='store_true',
                        help='Test all criteria (slower, more representative)')
    parser.add_argument('--no-vision', action='store_true',
                        help='Skip image attachment')
    parser.add_argument('--students', type=int, default=60,
                        help='Class size for cost projection (default: 60)')
    parser.add_argument('--reports', type=int, default=11,
                        help='Reports per student for cost projection (default: 11)')
    parser.add_argument('--profile',
                        help='Named provider profile from ~/.ai-feedback/config.yml')
    parser.add_argument('--provider',
                        help='AI provider (overrides profile; default: openrouter)')
    parser.add_argument('--extractor', default='meta-llama/llama-4-scout',
                        help='Model to use for text extraction (default: meta-llama/llama-4-scout)')
    parser.add_argument('--session-id',
                        help='OpenRouter session_id for grouping calls in logs')
    parser.add_argument('--extractor-fallback', default='google/gemini-2.0-flash-001',
                        help='Fallback extractor model (default: google/gemini-2.0-flash-001)')
    parser.add_argument('--output', help='Save raw results to this JSON file')
    parser.add_argument('--list-profiles', action='store_true',
                        help='List configured AI profiles and their models, then exit')
    args = parser.parse_args()

    if args.list_profiles:
        from ai_provider import print_configured_profiles
        print_configured_profiles(args.profile)
        return

    if not args.repo:
        parser.error("the following arguments are required: repo")

    repo_path = Path(args.repo).resolve()
    if not (repo_path / 'index.qmd').exists():
        print(f"❌ No index.qmd found in: {repo_path}")
        sys.exit(1)

    original_cwd = Path.cwd()
    os.chdir(repo_path)

    try:
        from ai_provider import resolve_provider_config
        from ai_feedback_criterion import (
            load_config, load_rubric, load_guidance, load_report,
            get_criterion_guidance, build_criterion_prompt, build_ai_messages,
            init_debug_mode, save_debug_criterion_data,
        )

        config = load_config()
        init_debug_mode(config)
        rubric = load_rubric()
        guidance = load_guidance()
        report = load_report()
        criteria = rubric.get('criteria', [])

        if not criteria:
            print("❌ No criteria found in rubric")
            sys.exit(1)

        # Set provider and extractor via env so call_extraction_api picks them up
        if args.profile:
            os.environ['AI_PROFILE'] = args.profile
        if args.provider:
            os.environ['AI_PROVIDER'] = args.provider
        os.environ['AI_EXTRACTOR_MODEL'] = args.extractor
        os.environ['AI_EXTRACTOR_FALLBACK_MODEL'] = args.extractor_fallback
        if args.session_id:
            os.environ['AI_SESSION_ID'] = args.session_id
        provider_config = resolve_provider_config(config, profile=args.profile)

        api_key = provider_config.get('api_key')
        if not api_key:
            print(f"❌ No API key for provider '{args.provider}'")
            sys.exit(1)

        print("Fetching model pricing from OpenRouter...")
        pricing = fetch_openrouter_pricing(api_key) if provider_config.get('provider') == 'openrouter' else {}

        test_criteria = criteria if args.all_criteria else [criteria[args.criterion]]
        print(f"\nBenchmarking {len(args.models)} models"
              f" on {'all' if args.all_criteria else '1'} criterion"
              f" ({'no vision' if args.no_vision else 'vision enabled'})")
        print(f"Repo:      {repo_path.name}")
        print(f"Extractor: {args.extractor}\n")

        # Build prompts once per criterion — extraction is the same for all models
        print("Extracting criterion prompts (once)...")
        criterion_prompts = {}
        criterion_contexts = {}
        for criterion in test_criteria:
            try:
                guidance_excerpt = get_criterion_guidance(guidance, criterion)
                prompt, context, image_paths = build_criterion_prompt(
                    report, criterion, guidance_excerpt, config)
                effective_images = [] if args.no_vision else image_paths
                messages = build_ai_messages(prompt, config, image_paths=effective_images)
                criterion_prompts[criterion['name']] = messages
                criterion_contexts[criterion['name']] = (prompt, context)
                print(f"  ✓ {criterion['name']}")
            except Exception as e:
                print(f"  ✗ {criterion['name']}: {e}")
                criterion_prompts[criterion['name']] = None
                criterion_contexts[criterion['name']] = ('', '')
        print()

        all_results = {}

        for model_id in args.models:
            print(f"── {model_id}")
            criterion_results = []

            for ci, criterion in enumerate(test_criteria):
                cname = criterion['name']
                messages = criterion_prompts.get(cname)
                if messages is None:
                    print(f"   [✗] {cname[:40]:<40}  skipped (extraction failed)")
                    criterion_results.append({
                        'success': False, 'elapsed': 0,
                        'prompt_tokens': 0, 'completion_tokens': 0, 'tps': 0,
                        'error': 'extraction failed', 'json_valid': False,
                        'field_score': 0, 'assessment': '',
                    })
                    continue
                try:
                    ctx_prompt, ctx_context = criterion_contexts.get(cname, ('', ''))
                    r = test_model(model_id, messages, config, provider_config,
                                   criterion_name=cname, criterion_index=ci,
                                   context=ctx_context, prompt=ctx_prompt)
                    criterion_results.append(r)

                    status = '✓' if r['success'] else '✗'
                    tok = r['completion_tokens']
                    print(f"   [{status}] {cname[:40]:<40}  "
                          f"{r['elapsed']:5.1f}s  {tok:4d} tok  {r['tps']:5.1f} tps"
                          + (f"  ⚠ {r['error'][:50]}" if r['error'] else ''))

                except Exception as e:
                    print(f"   [✗] {cname[:40]:<40}  exception: {e}")
                    criterion_results.append({
                        'success': False, 'elapsed': 0,
                        'prompt_tokens': 0, 'completion_tokens': 0, 'tps': 0,
                        'error': str(e), 'json_valid': False, 'field_score': 0,
                        'assessment': '',
                    })

            all_results[model_id] = aggregate(criterion_results)

        print_table(all_results, pricing, args.models, args.students, args.reports)

        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                json.dump({
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'repo': str(repo_path),
                    'models_tested': args.models,
                    'all_criteria': args.all_criteria,
                    'vision': not args.no_vision,
                    'results': all_results,
                }, f, indent=2)
            print(f"Results saved to: {output_path}")

    finally:
        os.chdir(original_cwd)


if __name__ == '__main__':
    main()
