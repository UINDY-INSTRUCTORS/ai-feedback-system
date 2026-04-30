#!/usr/bin/env python3
"""
Evaluate section extractor discrimination quality.

For a given debug run directory (containing per-criterion request.json files),
this script measures how well the extractor is isolating content for each criterion
vs. leaking content that belongs to others.

Usage:
    uv run eval-extractor.py <debug-dir> [<debug-dir2> ...]
    uv run eval-extractor.py --find <repo-path>   # auto-find latest debug run

Metrics:
    - Coverage fraction: extracted words / full report words
    - Pairwise Jaccard overlap matrix between all criterion extractions
    - Unique-word fraction: words unique to each criterion (not in any other)
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SECTION_MARKER = '## Report Sections Relevant to This Criterion'


def _tokenize(text: str) -> set[str]:
    """Lowercase word tokens, ignoring punctuation and short tokens."""
    return {w for w in re.findall(r'\b[a-z]{3,}\b', text.lower())}


def _word_count(text: str) -> int:
    return len(re.findall(r'\w+', text))


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def load_criterion_extractions(debug_run_dir: Path) -> dict[str, str]:
    """
    Read all criteria/*/request.json files and return {criterion_name: extracted_text}.
    Extracted text is the part of the user message after SECTION_MARKER.
    """
    criteria_dir = debug_run_dir / 'criteria'
    if not criteria_dir.exists():
        print(f"  No criteria/ subdir in {debug_run_dir}", file=sys.stderr)
        return {}

    extractions = {}
    for crit_dir in sorted(criteria_dir.iterdir()):
        req_file = crit_dir / 'request.json'
        if not req_file.exists():
            continue

        with open(req_file) as f:
            req = json.load(f)

        # Pull out the user message text
        user_msg = next(
            (m for m in req.get('messages', []) if m.get('role') == 'user'), None
        )
        if user_msg is None:
            continue
        content = user_msg.get('content', '')
        if isinstance(content, list):
            text = ' '.join(
                item.get('text', '') for item in content if item.get('type') == 'text'
            )
        else:
            text = str(content)

        idx = text.find(SECTION_MARKER)
        extracted = text[idx + len(SECTION_MARKER):].strip() if idx != -1 else text

        # Strip the criterion name from the dir (e.g. "01_introduction_motivation")
        name = crit_dir.name
        extractions[name] = extracted

    return extractions


def full_report_word_count(debug_run_dir: Path) -> int | None:
    """
    Try to read parsed_report.json from a sibling of the debug dir.
    Falls back to word count from the longest extraction × a rough multiplier.
    """
    # debug dir is typically <repo>/.github/debug/<timestamp>/
    # parsed_report.json lives at <repo>/parsed_report.json
    repo_root = debug_run_dir.parent.parent.parent
    pr = repo_root / 'parsed_report.json'
    if pr.exists():
        with open(pr) as f:
            r = json.load(f)
        return r.get('stats', {}).get('word_count')
    return None


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _bar(value: float, width: int = 30) -> str:
    filled = round(value * width)
    return '█' * filled + '░' * (width - filled)


def _overlap_cell(v: float, width: int, use_color: bool) -> str:
    val = f'{v:.2f}'.rjust(width)
    if not use_color:
        return val
    if v >= 0.7:
        return f'\033[31m{val}\033[0m'   # red: high overlap (bad)
    if v >= 0.4:
        return f'\033[33m{val}\033[0m'   # yellow: moderate
    return f'\033[32m{val}\033[0m'       # green: low overlap (good)


def render_report(debug_run_dir: Path, extractions: dict[str, str], use_color: bool = True):
    names = list(extractions.keys())
    if not names:
        print("  No extractions found.")
        return

    tokens = {n: _tokenize(extractions[n]) for n in names}
    word_counts = {n: _word_count(extractions[n]) for n in names}
    report_words = full_report_word_count(debug_run_dir)

    # Short labels: strip numeric prefix, then truncate for column headers
    def short(name: str) -> str:
        return re.sub(r'^\d+_', '', name)

    shorts = {n: short(n) for n in names}
    max_label = max(len(s) for s in shorts.values())
    # Column header truncation length — wide enough to be readable, narrow enough to fit
    col_hdr_len = min(12, max(6, 60 // max(len(names), 1)))
    col_headers = [shorts[n][:col_hdr_len] for n in names]
    col_w = max(6, col_hdr_len + 1)

    print(f"\n{'='*70}")
    print(f"  Debug run: {debug_run_dir}")
    print(f"{'='*70}")

    # ── Coverage ────────────────────────────────────────────────────────────
    print(f"\n{'─'*70}")
    print(f"  COVERAGE  (extracted words / total report words)")
    print(f"{'─'*70}")

    all_tokens_union: set[str] = set()
    for t in tokens.values():
        all_tokens_union |= t

    # Unique words per criterion (not in any other extraction)
    unique_tokens = {
        n: tokens[n] - set().union(*(tokens[m] for m in names if m != n))
        for n in names
    }

    for n in names:
        wc = word_counts[n]
        cov = wc / report_words if report_words else None
        cov_str = f'{cov:.0%}' if cov is not None else '  ?  '
        uniq = len(unique_tokens[n]) / len(tokens[n]) if tokens[n] else 0
        label = shorts[n].ljust(max_label)
        bar = _bar(cov if cov is not None else 0)
        print(f"  {label}  {cov_str:>5}  [{bar}]  unique={uniq:.0%}  words={wc}")

    if report_words:
        print(f"\n  Full report: {report_words} words")

    # ── Pairwise Jaccard overlap matrix ─────────────────────────────────────
    print(f"\n{'─'*70}")
    print(f"  PAIRWISE OVERLAP (Jaccard similarity — lower is better)")
    print(f"{'─'*70}")

    header_pad = ' ' * (max_label + 2)
    print(f"  {header_pad}" + ''.join(f'{lbl:>{col_w}}' for lbl in col_headers))

    for i, ni in enumerate(names):
        row_label = shorts[ni].ljust(max_label)
        row = f"  {row_label}"
        for j, nj in enumerate(names):
            v = _jaccard(tokens[ni], tokens[nj])
            if i == j:
                cell = '  ──  '.rjust(col_w)
            else:
                cell = _overlap_cell(v, col_w, use_color)
            row += cell
        print(row)

    # ── Summary stats ────────────────────────────────────────────────────────
    off_diag = [
        _jaccard(tokens[ni], tokens[nj])
        for i, ni in enumerate(names)
        for j, nj in enumerate(names)
        if i != j
    ]
    if off_diag:
        avg = sum(off_diag) / len(off_diag)
        mx = max(off_diag)
        print(f"\n  avg overlap={avg:.2f}  max overlap={mx:.2f}")
        if avg < 0.25:
            verdict = '✓ Good discrimination'
        elif avg < 0.45:
            verdict = '⚠ Moderate overlap — extractor may be too broad'
        else:
            verdict = '✗ High overlap — extractor is not discriminating well'
        print(f"  {verdict}")

    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def find_debug_runs(repo_path: Path) -> list[Path]:
    base = repo_path / '.github' / 'debug'
    if not base.exists():
        return []
    return sorted(
        (p for p in base.iterdir() if p.is_dir() and (p / 'criteria').exists()),
        reverse=True,
    )


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate section extractor discrimination from debug request.json files.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        'debug_dirs', nargs='*', metavar='DEBUG_DIR',
        help='One or more debug run directories (containing criteria/)',
    )
    parser.add_argument(
        '--find', metavar='REPO_PATH',
        help='Auto-find all debug runs under REPO_PATH/.github/debug/',
    )
    parser.add_argument(
        '--latest', action='store_true',
        help='With --find, only show the most recent run per repo',
    )
    parser.add_argument(
        '--no-color', action='store_true',
        help='Disable ANSI color in the overlap matrix',
    )
    args = parser.parse_args()

    run_dirs: list[Path] = []

    if args.find:
        repo = Path(args.find).expanduser().resolve()
        found = find_debug_runs(repo)
        if not found:
            print(f'No debug runs found under {repo}/.github/debug/', file=sys.stderr)
            sys.exit(1)
        run_dirs = found[:1] if args.latest else found
    elif args.debug_dirs:
        run_dirs = [Path(d).expanduser().resolve() for d in args.debug_dirs]
    else:
        parser.print_help()
        sys.exit(1)

    for run_dir in run_dirs:
        extractions = load_criterion_extractions(run_dir)
        render_report(run_dir, extractions, use_color=not args.no_color)


if __name__ == '__main__':
    main()
