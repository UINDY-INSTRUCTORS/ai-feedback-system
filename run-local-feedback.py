#!/usr/bin/env python3
"""
Local feedback runner for testing and batch processing student reports.

This tool allows you to:
1. Run feedback on a single student repo locally
2. Batch process multiple repos
3. Save output to files instead of creating GitHub issues
4. Reuse the instructor's rubric/guidance files

Usage:
    # Single repo
    python run-local-feedback.py /path/to/student/repo

    # Batch process
    python run-local-feedback.py /path/to/student/repo --output-dir ./feedback-results

    # With custom config
    python run-local-feedback.py /path/to/student/repo --config /path/to/config.yml

    # List available repos in a directory
    python run-local-feedback.py /path/to/repos --list
"""

import os
import sys
import json
import csv
import yaml
import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# Add scripts directory to path so we can import feedback modules
SCRIPT_DIR = Path(__file__).parent / 'dot_github_folder' / 'scripts'
sys.path.insert(0, str(SCRIPT_DIR))

# Default Docker image and quarto path for rendering
DOCKER_IMAGE = 'ghcr.io/202420-phys-230/novnc:4'
DOCKER_QUARTO = '/root/miniconda3/envs/phenv/bin/quarto'

def find_student_repos(parent_dir: Path) -> list:
    """Find all student repos in a parent directory (looks for index.qmd)."""
    repos = []
    for item in parent_dir.iterdir():
        if item.is_dir() and (item / 'index.qmd').exists():
            repos.append(item)
    return sorted(repos)


def find_repos_from_pdf_dir(pdf_dir: Path, submissions_dir: Path) -> list:
    """Find student repos in submissions_dir corresponding to PDFs in pdf_dir.

    PDF filenames follow: {username}-{label}-{date}.pdf or {username}-{label}.pdf
    where label == pdf_dir.name.

    Repos in submissions_dir follow: {project-prefix}-{username}
    """
    label = pdf_dir.name
    usernames = set()

    for pdf_file in pdf_dir.glob('*.pdf'):
        stem = pdf_file.stem  # e.g. "AlejandroMR-24-ph230-p4-chk-4.4-20260321"
        idx = stem.find(f'-{label}')
        if idx > 0:
            usernames.add(stem[:idx])

    if not usernames:
        print(f"No PDFs matching label '{label}' found in {pdf_dir}")
        return []

    repos = []
    found_names = set()
    for item in sorted(submissions_dir.iterdir()):
        if not item.is_dir():
            continue
        for username in usernames:
            if item.name.endswith(f'-{username}') or item.name == username:
                repos.append(item)
                found_names.add(username)
                break

    missing = usernames - found_names
    if missing:
        print(f"Warning: no repos found for usernames: {', '.join(sorted(missing))}")

    return repos

def validate_repo(repo_path: Path) -> bool:
    """Check if repo has required files."""
    required_files = ['index.qmd']
    missing = [f for f in required_files if not (repo_path / f).exists()]
    if missing:
        print(f"❌ {repo_path.name}: Missing {missing}")
        return False
    return True

def setup_feedback_config(repo_path: Path, instructor_path: Path, output_format: str = 'flat_file'):
    """Set up .github/feedback directory in student repo with instructor's rubric/guidance."""
    feedback_dir = repo_path / '.github' / 'feedback'
    instructor_feedback_dir = instructor_path / '.github' / 'feedback'

    # Create .github directory structure
    feedback_dir.mkdir(parents=True, exist_ok=True)
    (repo_path / '.github').mkdir(exist_ok=True)

    # Copy or link rubric and guidance from instructor repo
    files_to_copy = ['rubric.yml', 'RUBRIC.md', 'guidance.md']
    for file in files_to_copy:
        src = instructor_feedback_dir / file
        dst = feedback_dir / file
        if src.exists() and not dst.exists():
            print(f"  Copying {file}...")
            shutil.copy2(src, dst)

    # Create a student-specific config.yml
    config_path = repo_path / '.github' / 'config.yml'
    if not config_path.exists():
        config = {
            'report_file': 'index.qmd',
            'report_format': 'quarto',
            'model': {
                'primary': 'gpt-4o',
                'fallback': 'gpt-4o-mini'
            },
            'feedback': {
                'scoring_enabled': False
            },
            'output': {
                'format': output_format,
                'path': f'feedback-{datetime.now().strftime("%Y%m%d-%H%M%S")}.md'
            },
            'issue_label': 'ai-feedback'
        }
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        print(f"  Created {config_path}")

    return feedback_dir

def _run_subprocess(cmd, env=None, timeout=120, verbose=False):
    """Run a subprocess. In verbose mode, stream stdout+stderr live; otherwise capture."""
    if verbose:
        verbose_env = dict(env) if env else os.environ.copy()
        verbose_env['PYTHONUNBUFFERED'] = '1'
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=verbose_env,
        )
        stdout_lines = []
        for line in proc.stdout:
            print(line, end='', flush=True)
            stdout_lines.append(line)
        proc.wait()

        class _Result:
            def __init__(self, returncode, stdout):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = ''
        return _Result(proc.returncode, ''.join(stdout_lines))
    else:
        return subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=timeout)


def render_quarto_docker(repo_path: Path, docker_image: str = None,
                         docker_quarto: str = None, docker_home: str = 'dhome',
                         verbose: bool = False):
    """Render Quarto report using Docker container matching the codespace environment."""
    image = docker_image or DOCKER_IMAGE
    quarto = docker_quarto or DOCKER_QUARTO

    cmd = [
        'docker', 'run', '--rm',
        '-v', f'{repo_path}:/docs',
        '-v', f'{docker_home}:/home/vscode',
        '-w', '/docs',
        image,
        quarto, 'render', 'index.qmd'
    ]
    print(f"   Docker: {image}")
    print(f"   Quarto: {quarto}")
    return _run_subprocess(cmd, timeout=180, verbose=verbose)


def render_quarto_local(repo_path: Path, env: dict, verbose: bool = False):
    """Render Quarto report using locally installed quarto."""
    return _run_subprocess(['quarto', 'render'], env=env, timeout=120, verbose=verbose)


def run_feedback_pipeline(repo_path: Path, output_path: Path = None,
                          profile: str = None, provider: str = None, model: str = None,
                          use_docker: bool = False, skip_render: bool = False,
                          docker_image: str = None, docker_quarto: str = None,
                          scoring: bool = None, disable_json_mode: bool = False,
                          force_qmd: bool = False, debug: bool = False,
                          verbose: bool = False, levels_only: bool = False,
                          extract_only: bool = False):
    """Run the complete feedback pipeline for a repo.

    Returns:
        dict with 'success' bool and 'scores' from extract_scores_from_feedback,
        or False on validation failure.
    """
    repo_path = Path(repo_path).resolve()
    if output_path is not None:
        output_path = Path(output_path).resolve()

    if not validate_repo(repo_path):
        return {'success': False, 'scores': {'repo': repo_path.name, 'criteria': {}, 'error': 'Validation failed'}}

    print(f"\n{'='*60}")
    print(f"Processing: {repo_path.name}")
    print(f"{'='*60}")

    # Save current directory
    original_cwd = Path.cwd()

    try:
        os.chdir(repo_path)
        print("✓ Changed to repo directory")

        # Set environment variables for the feedback scripts
        env = os.environ.copy()
        env['TAG_NAME'] = 'local-test'
        env['OUTPUT_FORMAT'] = 'flat_file'

        # Pass provider/model overrides via env vars
        if profile:
            env['AI_PROFILE'] = profile
        if provider:
            env['AI_PROVIDER'] = provider
        if model:
            env['AI_MODEL'] = model
        if disable_json_mode:
            env['AI_DISABLE_JSON_MODE'] = 'true'
        if debug:
            env['AI_DEBUG'] = '1'
        if force_qmd:
            env['PARSE_SOURCE'] = 'qmd'
        if extract_only:
            env['EXTRACT_ONLY'] = '1'
            out = output_path or Path('extraction.md')
            env['EXTRACT_OUTPUT_PATH'] = str(out.parent / 'extraction.md') if output_path else 'extraction.md'
        if levels_only:
            env['LEVELS_ONLY'] = '1'
            env['SCORING_ENABLED'] = 'false'  # levels-only implies no numerical scores
        elif scoring is not None:
            env['SCORING_ENABLED'] = 'true' if scoring else 'false'

        if output_path:
            env['OUTPUT_PATH'] = str(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # Step 1: Validate feedback configuration
        print("\n1  Validating feedback configuration...")
        result = _run_subprocess(
            [sys.executable, str(SCRIPT_DIR / 'validate_feedback_setup.py')],
            env=env, verbose=verbose
        )
        if result.returncode != 0:
            if not verbose:
                print(f"Validation failed:\n{result.stderr}")
            return {'success': False, 'scores': {'repo': repo_path.name, 'criteria': {}, 'error': 'Validation failed'}}
        print("✓ Configuration valid")

        # Step 2: Render Quarto report
        if skip_render:
            print("\n2  Skipping Quarto render (--no-render)")
        else:
            print("\n2  Rendering Quarto report...")
            if use_docker:
                result = render_quarto_docker(repo_path, docker_image, docker_quarto, verbose=verbose)
            else:
                result = render_quarto_local(repo_path, env, verbose=verbose)

            if result.returncode != 0:
                if not verbose:
                    print(f"Quarto render had issues (continuing):\n{result.stderr[:500]}")
                else:
                    print("⚠️  Quarto render had issues (continuing)")
            else:
                print("✓ Report rendered")

        # Step 3: Parse report
        print("\n3️⃣  Parsing report...")
        result = _run_subprocess(
            [sys.executable, str(SCRIPT_DIR / 'parse_report.py')],
            env=env, verbose=verbose
        )
        if result.returncode != 0:
            if not verbose:
                print(f"❌ Parse failed:\n{result.stderr}")
            return {'success': False, 'scores': {'repo': repo_path.name, 'criteria': {}, 'error': 'Parse failed'}}
        print("✓ Report parsed")

        # Step 4: Generate AI feedback
        print("\n4️⃣  Generating AI feedback...")
        result = _run_subprocess(
            [sys.executable, str(SCRIPT_DIR / 'ai_feedback_criterion.py')],
            env=env, timeout=1800, verbose=verbose
        )
        if result.returncode != 0:
            if not verbose:
                print(f"❌ Feedback generation failed:\n{result.stderr}")
            # Recover partial scores from feedback.json if any criteria succeeded
            partial = extract_scores_from_feedback(repo_path)
            if partial.get('criteria'):
                return {'success': False, 'scores': partial}
            return {'success': False, 'scores': {'repo': repo_path.name, 'criteria': {}, 'error': 'Feedback generation failed'}}
        if result.stdout and not verbose:
            print(result.stdout)
        print("✓ Feedback generated")

        # Extract-only: skip create_issue, return extraction path
        if extract_only:
            extract_path = Path(env.get('EXTRACT_OUTPUT_PATH', 'extraction.md'))
            if not extract_path.is_absolute():
                extract_path = repo_path / extract_path
            print(f"\n✅ Extraction complete: {extract_path}")
            return {'success': True, 'scores': {'repo': repo_path.name, 'criteria': {}},
                    'extraction_path': str(extract_path)}

        # Step 5: Create issue or save to file
        print("\n5️⃣  Saving feedback...")
        result = _run_subprocess(
            [sys.executable, str(SCRIPT_DIR / 'create_issue.py')],
            env=env, verbose=verbose
        )
        if result.returncode != 0:
            if not verbose:
                print(f"❌ Save failed:\n{result.stderr}")
            return {'success': False, 'scores': {'repo': repo_path.name, 'criteria': {}, 'error': 'Save failed'}}
        if result.stdout and not verbose:
            print(result.stdout)
        print("✓ Feedback saved")

        print(f"\n✅ Successfully processed {repo_path.name}")
        scores = extract_scores_from_feedback(repo_path)
        return {'success': True, 'scores': scores}

    except subprocess.TimeoutExpired:
        print("❌ Process timed out")
        return {'success': False, 'scores': {'repo': repo_path.name, 'criteria': {}, 'error': 'Timed out'}}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {'success': False, 'scores': {'repo': repo_path.name, 'criteria': {}, 'error': str(e)}}
    finally:
        os.chdir(original_cwd)

def extract_scores_from_feedback(repo_path: Path) -> dict:
    """
    Read feedback.json from a repo and extract per-criterion scores.

    Returns dict like:
      {
        'repo': 'student-repo-name',
        'criteria': {
            'Theory & Explanation': {'score': 18, 'max': 20, 'pct': 90.0, 'assessment': 'Exemplary'},
            'Implementation/Code':  {'score': 30, 'max': 40, 'pct': 75.0, 'assessment': 'Satisfactory'},
            ...
        }
      }

    When numerical scoring is disabled, score/pct will be None and only
    assessment is populated.
    """
    feedback_path = repo_path / 'feedback.json'
    if not feedback_path.exists():
        return {'repo': repo_path.name, 'criteria': {}, 'error': 'No feedback.json'}

    # Also load the rubric so we know max scores (weights)
    rubric_path = repo_path / '.github' / 'feedback' / 'rubric.yml'
    rubric_weights = {}
    if rubric_path.exists():
        try:
            with open(rubric_path) as f:
                rubric = yaml.safe_load(f)
            for c in rubric.get('criteria', []):
                rubric_weights[c['name']] = c.get('weight', 0)
        except Exception:
            pass

    try:
        with open(feedback_path) as f:
            feedback_data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return {'repo': repo_path.name, 'criteria': {}, 'error': 'Invalid feedback.json'}

    criteria = {}
    for item in feedback_data:
        name = item.get('criterion', 'Unknown')
        if not item.get('success', False):
            criteria[name] = {'score': None, 'max': None, 'pct': None,
                              'assessment': 'ERROR'}
            continue

        fb = item.get('feedback', {})
        if isinstance(fb, str):
            try:
                fb = json.loads(fb)
            except json.JSONDecodeError:
                fb = {}

        # Handle nested feedback dict
        if 'feedback' in fb and isinstance(fb['feedback'], dict):
            fb = fb['feedback']

        assessment = (fb.get('overall_assessment')
                      or fb.get('level')
                      or fb.get('overall_evaluation', 'N/A'))
        score = fb.get('score')
        max_score = rubric_weights.get(name, 0)

        pct = None
        if score is not None and max_score > 0:
            try:
                pct = round(float(score) / max_score * 100, 1)
            except (ValueError, TypeError):
                pass

        criteria[name] = {
            'score': score,
            'max': max_score,
            'pct': pct,
            'assessment': assessment,
        }

    return {'repo': repo_path.name, 'criteria': criteria}


def build_summary_table(all_scores: list, output_dir: Path, scoring: bool = None):
    """
    Build and save a summary table from collected batch scores.

    Args:
        all_scores: list of dicts from extract_scores_from_feedback
        output_dir: directory to write summary.md and summary.csv
        scoring: True = show percentages, False = show rubric levels,
                 None = auto-detect from data

    Produces:
      - summary.md  (markdown table)
      - summary.csv (spreadsheet-friendly)

    Prints the table to stdout as well.
    """
    if not all_scores:
        print("No scores to summarize.")
        return

    # Collect all criterion names in order (from first successful repo)
    criterion_names = []
    for entry in all_scores:
        if entry['criteria']:
            criterion_names = list(entry['criteria'].keys())
            break

    if not criterion_names:
        print("No criterion data found in any repo.")
        return

    # Determine display mode:
    #   --scoring    -> percentages
    #   --no-scoring -> rubric levels
    #   neither      -> auto-detect from whether scores exist in the data
    if scoring is True:
        show_pct = True
    elif scoring is False:
        show_pct = False
    else:
        # Auto-detect: show percentages if any repo has numerical scores
        show_pct = any(
            entry['criteria'].get(cn, {}).get('score') is not None
            for entry in all_scores
            for cn in criterion_names
        )

    # Build header
    if show_pct:
        header = ['Repo'] + [f'{cn} (%)' for cn in criterion_names] + ['Overall (%)']
    else:
        header = ['Repo'] + criterion_names

    # Build rows
    rows = []
    for entry in all_scores:
        repo_name = entry['repo']
        if entry.get('error'):
            row = [repo_name] + [entry['error']] + [''] * (len(criterion_names) - 1)
            if show_pct:
                row.append('')
            rows.append(row)
            continue

        row = [repo_name]
        pcts = []
        for cn in criterion_names:
            info = entry['criteria'].get(cn, {})
            if show_pct:
                pct = info.get('pct')
                if pct is not None:
                    row.append(f'{pct}')
                    pcts.append(pct)
                else:
                    # No numerical score available — show assessment as fallback
                    row.append(info.get('assessment', 'N/A'))
            else:
                row.append(info.get('assessment', 'N/A'))

        if show_pct:
            if pcts:
                overall = round(sum(pcts) / len(pcts), 1)
                row.append(f'{overall}')
            else:
                row.append('N/A')

        rows.append(row)

    # Print to stdout
    _print_markdown_table(header, rows)

    # Save files
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Markdown
    md_path = output_dir / 'summary.md'
    with open(md_path, 'w') as f:
        f.write(f'# Batch Feedback Summary\n\n')
        f.write(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
        _write_markdown_table(f, header, rows)
    print(f"\nSummary table saved to: {md_path}")

    # CSV
    csv_path = output_dir / 'summary.csv'
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"CSV saved to: {csv_path}")


def _print_markdown_table(header: list, rows: list):
    """Print a markdown table to stdout with aligned columns."""
    col_widths = [len(h) for h in header]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))

    def fmt_row(cells):
        return '| ' + ' | '.join(str(c).ljust(col_widths[i]) for i, c in enumerate(cells)) + ' |'

    separator = '|' + '|'.join('-' * (w + 2) for w in col_widths) + '|'

    print()
    print(fmt_row(header))
    print(separator)
    for row in rows:
        print(fmt_row(row))
    print()


def _write_markdown_table(f, header: list, rows: list):
    """Write a markdown table to a file object."""
    col_widths = [len(h) for h in header]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))

    def fmt_row(cells):
        return '| ' + ' | '.join(str(c).ljust(col_widths[i]) for i, c in enumerate(cells)) + ' |\n'

    separator = '|' + '|'.join('-' * (w + 2) for w in col_widths) + '|\n'

    f.write(fmt_row(header))
    f.write(separator)
    for row in rows:
        f.write(fmt_row(row))


def main():
    parser = argparse.ArgumentParser(
        description='Run AI feedback locally on student repos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('path', nargs='?',
                       help='Path to student repo or parent directory of repos')
    parser.add_argument('--instructor-repo',
                       help='Path to instructor repo with rubric/guidance (overrides student repo config)')
    parser.add_argument('--output-dir',
                       help='Directory to save feedback files (defaults to repo/.github)')
    parser.add_argument('--config',
                       help='Path to custom config.yml (instructor repo config used by default)')
    parser.add_argument('--list', action='store_true',
                       help='List available repos and exit')
    parser.add_argument('--batch', action='store_true',
                       help='Process all repos in directory')
    parser.add_argument('--from-pdf-dir',
                       help='Process repos that produced PDFs in this directory (path = submissions dir)')

    # Provider options
    parser.add_argument('--profile',
                       help='Named provider profile from ~/.ai-feedback/config.yml')
    parser.add_argument('--provider',
                       help='AI provider (overrides profile and global/repo config)')
    parser.add_argument('--model',
                       help='Model name (overrides global/repo config)')
    parser.add_argument('--disable-json-mode', action='store_true',
                       help='Skip JSON response format (for models that don\'t support it)')
    parser.add_argument('--init-config', action='store_true',
                       help='Create default global config at ~/.ai-feedback/config.yml and exit')
    parser.add_argument('--list-profiles', action='store_true',
                       help='List configured AI profiles and their models, then exit')

    # Rendering options
    parser.add_argument('--docker', action='store_true',
                       help='Use Docker container for Quarto rendering (matches codespace env)')
    parser.add_argument('--docker-image', default=DOCKER_IMAGE,
                       help=f'Docker image for rendering (default: {DOCKER_IMAGE})')
    parser.add_argument('--docker-quarto', default=DOCKER_QUARTO,
                       help=f'Quarto path inside container (default: {DOCKER_QUARTO})')
    parser.add_argument('--no-render', action='store_true',
                       help='Skip Quarto rendering (use existing output)')
    parser.add_argument('--force-qmd', action='store_true',
                       help='Parse .qmd source directly, ignoring rendered HTML output')

    # Scoring options
    scoring_group = parser.add_mutually_exclusive_group()
    scoring_group.add_argument('--scoring', action='store_true', default=None,
                               help='Enable numerical scoring (overrides repo config)')
    scoring_group.add_argument('--no-scoring', dest='scoring', action='store_false',
                               help='Disable numerical scoring, show rubric levels (overrides repo config)')

    parser.add_argument('--levels-only', action='store_true',
                        help='Classify rubric level only — skip prose feedback (faster, cheaper)')

    # Diagnostics
    parser.add_argument('--verbose', action='store_true',
                       help='Stream subprocess output live (shows per-criterion progress, tokens, timing)')
    parser.add_argument('--debug', action='store_true',
                       help='Save prompts, responses, and metadata to .github/debug/ for each criterion')

    # Model listing
    parser.add_argument('--list-models', nargs='?', const='http://localhost:1234/v1',
                       help='Query an OpenAI-compatible endpoint for available models '
                            '(default: http://localhost:1234/v1 for LM Studio)')

    args = parser.parse_args()

    if args.init_config:
        from dot_github_folder.scripts.ai_provider import create_default_global_config
        create_default_global_config()
        return

    if args.list_profiles:
        from dot_github_folder.scripts.ai_provider import print_configured_profiles
        print_configured_profiles(args.profile)
        return

    if args.list_models:
        from dot_github_folder.scripts.ai_provider import list_openai_compatible_models
        try:
            models = list_openai_compatible_models(args.list_models)
            if models:
                print(f"\nAvailable models from {args.list_models}:\n")
                for model in models:
                    print(f"  {model}")
                print()
            else:
                print("No models found.")
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
        return

    # --from-pdf-dir: find repos that produced PDFs in the given directory
    if args.from_pdf_dir:
        if not args.path:
            print("❌ A submissions directory (path) is required with --from-pdf-dir")
            sys.exit(1)
        pdf_dir = Path(args.from_pdf_dir).resolve()
        submissions_dir = Path(args.path).resolve()
        if not pdf_dir.exists():
            print(f"❌ PDF directory not found: {pdf_dir}")
            sys.exit(1)
        if not submissions_dir.exists():
            print(f"❌ Submissions directory not found: {submissions_dir}")
            sys.exit(1)


        instructor_repo = None
        if args.instructor_repo:
            instructor_repo = Path(args.instructor_repo).resolve()
            if not instructor_repo.exists():
                print(f"❌ Instructor repo not found: {instructor_repo}")
                sys.exit(1)

        repos = find_repos_from_pdf_dir(pdf_dir, submissions_dir)
        if not repos:
            print("No matching repos found.")
            sys.exit(1)

        if args.list:
            print(f"Found {len(repos)} repos for PDFs in {pdf_dir}:")
            for repo in repos:
                status = "✓" if validate_repo(repo) else "✗"
                print(f"  {status} {repo.name}")
            return

        print(f"Processing {len(repos)} repos from {pdf_dir.name}...\n")
        successful = 0
        failed = 0
        all_scores = []

        for repo in repos:
            output_path = None
            if args.output_dir:
                repo_output_dir = Path(args.output_dir) / repo.name
                repo_output_dir.mkdir(parents=True, exist_ok=True)
                output_path = repo_output_dir / 'feedback.md'

            if instructor_repo:
                setup_feedback_config(repo, instructor_repo, output_format='flat_file')

            result = run_feedback_pipeline(repo, output_path,
                                           profile=args.profile,
                                           provider=args.provider, model=args.model,
                                           use_docker=args.docker, skip_render=args.no_render,
                                           docker_image=args.docker_image,
                                           docker_quarto=args.docker_quarto,
                                           scoring=args.scoring,
                                           disable_json_mode=args.disable_json_mode,
                                           force_qmd=args.force_qmd,
                                           debug=args.debug,
                                           verbose=args.verbose,
                                           levels_only=args.levels_only)
            if result and result.get('success'):
                successful += 1
            else:
                failed += 1
            if result:
                all_scores.append(result['scores'])

        print(f"\n{'='*60}")
        print(f"Summary: {successful} successful, {failed} failed out of {len(repos)}")
        print(f"{'='*60}")

        summary_dir = Path(args.output_dir) if args.output_dir else pdf_dir
        build_summary_table(all_scores, summary_dir, scoring=args.scoring)
        return

    if not args.path:
        print("❌ A path argument or --from-pdf-dir is required.")
        sys.exit(1)

    path = Path(args.path).resolve()
    instructor_repo = None
    if args.instructor_repo:
        instructor_repo = Path(args.instructor_repo).resolve()
        if not instructor_repo.exists():
            print(f"❌ Instructor repo not found: {instructor_repo}")
            sys.exit(1)

    if not path.exists():
        print(f"❌ Path not found: {path}")
        sys.exit(1)

    # Check if path is a parent directory (contains multiple repos)
    if path.is_dir() and not (path / 'index.qmd').exists():
        repos = find_student_repos(path)

        if args.list:
            print(f"Found {len(repos)} student repos in {path}:")
            for repo in repos:
                status = "✓" if validate_repo(repo) else "✗"
                print(f"  {status} {repo.name}")
            return

        if args.batch:
            print(f"Processing {len(repos)} repos...\n")
            successful = 0
            failed = 0
            all_scores = []

            for repo in repos:
                output_path = None
                if args.output_dir:
                    repo_output_dir = Path(args.output_dir) / repo.name
                    repo_output_dir.mkdir(parents=True, exist_ok=True)
                    output_path = repo_output_dir / f'feedback.md'

                # Override feedback config from instructor repo if specified
                if instructor_repo:
                    setup_feedback_config(repo, instructor_repo, output_format='flat_file')

                result = run_feedback_pipeline(repo, output_path,
                                               profile=args.profile,
                                               provider=args.provider, model=args.model,
                                               use_docker=args.docker, skip_render=args.no_render,
                                               docker_image=args.docker_image,
                                               docker_quarto=args.docker_quarto,
                                               scoring=args.scoring,
                                               disable_json_mode=args.disable_json_mode,
                                               force_qmd=args.force_qmd,
                                               debug=args.debug,
                                               verbose=args.verbose,
                                               levels_only=args.levels_only)
                if result['success']:
                    successful += 1
                else:
                    failed += 1
                all_scores.append(result['scores'])

            print(f"\n{'='*60}")
            print(f"Summary: {successful} successful, {failed} failed out of {len(repos)}")
            print(f"{'='*60}")

            # Build and save summary table
            summary_dir = Path(args.output_dir) if args.output_dir else path
            build_summary_table(all_scores, summary_dir, scoring=args.scoring)
            return

        print(f"Found {len(repos)} repos. Use --batch to process all, or --list to see them.")
        sys.exit(1)

    # Single repo processing
    output_path = None
    if args.output_dir:
        output_dir = Path(args.output_dir) / path.name
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / 'feedback.md'

    # Override feedback config from instructor repo if specified
    if instructor_repo:
        setup_feedback_config(path, instructor_repo, output_format='flat_file')

    result = run_feedback_pipeline(path, output_path,
                                    profile=args.profile,
                                    provider=args.provider, model=args.model,
                                    use_docker=args.docker, skip_render=args.no_render,
                                    docker_image=args.docker_image,
                                    docker_quarto=args.docker_quarto,
                                    scoring=args.scoring,
                                    disable_json_mode=args.disable_json_mode,
                                    force_qmd=args.force_qmd,
                                    verbose=args.verbose,
                                    levels_only=args.levels_only)
    sys.exit(0 if result['success'] else 1)

if __name__ == '__main__':
    main()
