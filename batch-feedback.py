#!/usr/bin/env python3
"""
Run the full AI feedback pipeline on a list of repos and produce a markdown
summary table with one row per repo and one column per rubric criterion.

Usage:
    uv run batch-feedback.py --repos repos.txt
    uv run batch-feedback.py --repos-dir /path/to/submissions
    uv run batch-feedback.py --repos repos.txt --profile anthropic --no-render --verbose

Output:
    batch-feedback-<timestamp>/
        batch-feedback-<timestamp>.md   (summary table + per-repo details)
        batch-feedback-<timestamp>.csv  (spreadsheet-friendly)
"""

import argparse
import copy
import csv
import importlib.util
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap: import run-local-feedback.py (hyphen prevents normal import)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_RLF_PATH = _HERE / 'run-local-feedback.py'
_spec = importlib.util.spec_from_file_location('run_local_feedback', _RLF_PATH)
_rlf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rlf)

run_feedback_pipeline        = _rlf.run_feedback_pipeline
extract_scores_from_feedback = _rlf.extract_scores_from_feedback
find_repos_from_pdf_dir      = _rlf.find_repos_from_pdf_dir

SCRIPT_DIR = _HERE / 'dot_github_folder' / 'scripts'
sys.path.insert(0, str(SCRIPT_DIR))


# ---------------------------------------------------------------------------
# Rubric injection (--rubric-dir)
# ---------------------------------------------------------------------------

def _inject_rubric(repo_path: Path, rubric_dir: Path) -> dict:
    """Copy rubric files into repo/.github/feedback/, backing up originals.

    Returns a backup dict {filename: original_bytes | None} used by _restore_rubric.
    """
    feedback_dir = repo_path / '.github' / 'feedback'
    feedback_dir.mkdir(parents=True, exist_ok=True)
    backups = {}
    for src in rubric_dir.iterdir():
        if not src.is_file():
            continue
        dst = feedback_dir / src.name
        backups[src.name] = dst.read_bytes() if dst.exists() else None
        shutil.copy2(src, dst)
    return backups


def _restore_rubric(repo_path: Path, backups: dict) -> None:
    """Undo _inject_rubric — restore originals or remove injected files."""
    feedback_dir = repo_path / '.github' / 'feedback'
    for fname, original in backups.items():
        dst = feedback_dir / fname
        if original is None:
            dst.unlink(missing_ok=True)
        else:
            dst.write_bytes(original)


# ---------------------------------------------------------------------------
# Repo discovery
# ---------------------------------------------------------------------------

def _load_repos_from_file(path: str) -> list[Path]:
    if path == '-':
        lines = sys.stdin.read().splitlines()
    else:
        lines = Path(path).read_text().splitlines()
    return [Path(l.strip()).expanduser().resolve()
            for l in lines if l.strip() and not l.strip().startswith('#')]


def _find_repos_in_dir(directory: Path) -> list[Path]:
    return sorted(p for p in directory.iterdir()
                  if p.is_dir() and (p / 'index.qmd').exists())


def load_repo_paths(repos_file, repos_dir,
                    pdf_dir=None, submissions_dir=None) -> list[Path]:
    if repos_file:
        return _load_repos_from_file(repos_file)
    if pdf_dir is not None:
        if submissions_dir is None:
            raise ValueError('--submissions-dir is required when --pdf-dir is specified')
        return find_repos_from_pdf_dir(Path(pdf_dir), Path(submissions_dir))
    return _find_repos_in_dir(Path(repos_dir).resolve())


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def _col_widths(header, rows):
    widths = [len(str(h)) for h in header]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))
    return widths


def _md_table_lines(header, rows) -> list[str]:
    widths = _col_widths(header, rows)
    fmt = lambda cells: '| ' + ' | '.join(str(c).ljust(widths[i]) for i, c in enumerate(cells)) + ' |'
    sep = '|' + '|'.join('-' * (w + 2) for w in widths) + '|'
    return [fmt(header), sep] + [fmt(r) for r in rows]


def _write_csv(path: Path, header, rows):
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def build_table(all_scores: list, show_pct: bool | None = None):
    """
    Returns (header, rows) for the summary table.
    show_pct=None auto-detects from whether any score is numeric.
    """
    criterion_names = []
    for entry in all_scores:
        if entry.get('criteria'):
            criterion_names = list(entry['criteria'].keys())
            break

    if show_pct is None:
        show_pct = any(
            entry.get('criteria', {}).get(cn, {}).get('score') is not None
            for entry in all_scores
            for cn in criterion_names
        )

    if show_pct:
        header = ['Repo'] + ([f'{cn} (%)' for cn in criterion_names] if criterion_names else ['Error']) + ['Overall (%)']
    else:
        header = ['Repo'] + (criterion_names if criterion_names else ['Error'])

    rows = []
    for entry in all_scores:
        repo = entry['repo']
        if entry.get('error') and not entry.get('criteria'):
            row = [repo] + [entry['error']] + [''] * max(0, len(criterion_names) - 1)
            if show_pct:
                row.append('')
            rows.append(row)
            continue

        row = [repo]
        pcts = []
        for cn in criterion_names:
            info = entry.get('criteria', {}).get(cn, {})
            if show_pct:
                pct = info.get('pct')
                if pct is not None:
                    row.append(str(pct))
                    pcts.append(pct)
                else:
                    row.append(info.get('assessment', 'N/A'))
            else:
                row.append(info.get('assessment', 'N/A'))

        if show_pct:
            row.append(f'{round(sum(pcts)/len(pcts), 1)}' if pcts else 'N/A')

        rows.append(row)

    return header, rows


def format_report(all_scores: list, repos: list[Path], profile: str | None,
                  scoring: bool | None) -> str:
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    header, rows = build_table(all_scores, show_pct=scoring)
    table_lines = _md_table_lines(header, rows)

    lines = [
        f'# Batch Feedback Summary',
        f'Generated: {now}  |  Repos: {len(repos)}  |  Profile: {profile or "default"}',
        '',
        '## Summary',
        '',
    ] + table_lines + ['']

    # Per-repo detail blocks
    lines += ['---', '', '## Details', '']
    for entry in all_scores:
        repo_name = entry['repo']
        lines += [f'### {repo_name}', '']
        if entry.get('error') and not entry.get('criteria'):
            lines += [f'> **ERROR:** {entry["error"]}', '']
            continue
        for cname, info in entry.get('criteria', {}).items():
            assessment = info.get('assessment', 'N/A')
            score_str = ''
            if info.get('score') is not None and info.get('max'):
                score_str = f' ({info["score"]}/{info["max"]})'
            lines += [f'- **{cname}:** {assessment}{score_str}']
        lines.append('')

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Run AI feedback pipeline on a list of repos and produce a summary table.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    repo_group = parser.add_mutually_exclusive_group(required=True)
    repo_group.add_argument('--repos', metavar='FILE',
                            help='File of repo paths (one per line). Use - for stdin.')
    repo_group.add_argument('--repos-dir', metavar='DIR',
                            help='Discover all subdirs of DIR that contain index.qmd.')
    repo_group.add_argument('--pdf-dir', metavar='DIR',
                            help='Directory of student PDFs; pairs with --submissions-dir.')

    parser.add_argument('--submissions-dir', metavar='DIR',
                        help='Directory of submission repos (required with --pdf-dir).')

    parser.add_argument('--profile', metavar='NAME',
                        help='Named provider profile from ~/.ai-feedback/config.yml')
    parser.add_argument('--provider', help='AI provider override')
    parser.add_argument('--model', help='Model name override')
    parser.add_argument('--disable-json-mode', action='store_true')

    parser.add_argument('--no-render', action='store_true',
                        help='Skip Quarto rendering (use existing output)')
    parser.add_argument('--force-qmd', action='store_true',
                        help='Parse .qmd source directly, ignoring rendered HTML output')
    parser.add_argument('--verbose', action='store_true',
                        help='Stream subprocess output live')
    parser.add_argument('--debug', action='store_true',
                        help='Save prompts, responses, and metadata to .github/debug/ for each criterion')

    parser.add_argument('--docker', action='store_true',
                        help='Use Docker for Quarto rendering')
    parser.add_argument('--docker-image', default=_rlf.DOCKER_IMAGE)
    parser.add_argument('--docker-quarto', default=_rlf.DOCKER_QUARTO)

    scoring_group = parser.add_mutually_exclusive_group()
    scoring_group.add_argument('--scoring', dest='scoring', action='store_true', default=None,
                               help='Show numerical scores in summary table')
    scoring_group.add_argument('--no-scoring', dest='scoring', action='store_false',
                               help='Show rubric levels in summary table (default)')

    parser.add_argument('--levels-only', action='store_true',
                        help='Classify rubric level only — skip prose feedback (faster, cheaper)')
    parser.add_argument('--extract-only', action='store_true',
                        help='Run extraction step only — write per-repo extraction.md, no AI feedback calls')

    parser.add_argument('--rubric-dir', metavar='DIR',
                        help='Directory containing rubric.yml / RUBRIC.md / guidance.md to inject '
                             'into each repo before processing (originals are restored after).')

    parser.add_argument('--output', metavar='DIR',
                        help='Output directory (default: batch-feedback-<timestamp>/)')

    args = parser.parse_args()

    if args.pdf_dir and not args.submissions_dir:
        parser.error('--submissions-dir is required when --pdf-dir is specified')

    repos = load_repo_paths(
        repos_file=args.repos,
        repos_dir=args.repos_dir,
        pdf_dir=args.pdf_dir,
        submissions_dir=args.submissions_dir,
    )
    if not repos:
        print('No repos found.', file=sys.stderr)
        sys.exit(1)

    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    out_dir = Path(args.output) if args.output else Path(f'batch-feedback-{timestamp}')
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f'Found {len(repos)} repo(s).')
    print(f'Output: {out_dir}/')
    if args.profile:
        print(f'Profile: {args.profile}')
    print()

    rubric_dir = Path(args.rubric_dir).resolve() if args.rubric_dir else None
    if rubric_dir and not rubric_dir.is_dir():
        print(f'--rubric-dir not found: {rubric_dir}', file=sys.stderr)
        sys.exit(1)

    all_scores = []
    ok = 0
    failed = 0

    for repo in repos:
        backups = _inject_rubric(repo, rubric_dir) if rubric_dir else {}
        try:
          result = run_feedback_pipeline(
              repo,
              output_path=out_dir / repo.name / 'feedback.md',
              profile=args.profile,
              provider=args.provider,
              model=args.model,
              use_docker=args.docker,
              skip_render=args.no_render,
              docker_image=args.docker_image,
              docker_quarto=args.docker_quarto,
              scoring=args.scoring,
              disable_json_mode=args.disable_json_mode,
              force_qmd=args.force_qmd,
              debug=args.debug,
              verbose=args.verbose,
              levels_only=args.levels_only,
              extract_only=args.extract_only,
          )
        finally:
            if rubric_dir:
                _restore_rubric(repo, backups)

        if result and result.get('success'):
            ok += 1
        else:
            failed += 1
        if result:
            all_scores.append(result['scores'])

    print(f'\n{"="*60}')
    print(f'Done: {ok} succeeded, {failed} failed out of {len(repos)}')
    print(f'{"="*60}\n')

    if not all_scores:
        print('No results to summarize.')
        sys.exit(1)

    report = format_report(all_scores, repos, args.profile, args.scoring)

    stem = f'batch-feedback-{timestamp}'
    md_path = out_dir / f'{stem}.md'
    csv_path = out_dir / f'{stem}.csv'

    md_path.write_text(report)
    print(f'Report: {md_path}')

    header, rows = build_table(all_scores, show_pct=args.scoring)
    _write_csv(csv_path, header, rows)
    print(f'CSV:    {csv_path}')

    # Print the summary table to stdout
    print()
    for line in _md_table_lines(header, rows):
        print(line)
    print()


if __name__ == '__main__':
    main()
