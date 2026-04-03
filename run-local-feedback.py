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

def render_quarto_docker(repo_path: Path, docker_image: str = None,
                         docker_quarto: str = None, docker_home: str = 'dhome'):
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
    return subprocess.run(cmd, capture_output=True, text=True, timeout=180)


def render_quarto_local(repo_path: Path, env: dict):
    """Render Quarto report using locally installed quarto."""
    return subprocess.run(
        ['quarto', 'render'],
        capture_output=True, text=True, env=env, timeout=120
    )


def run_feedback_pipeline(repo_path: Path, output_path: Path = None,
                          provider: str = None, model: str = None,
                          use_docker: bool = False, skip_render: bool = False,
                          docker_image: str = None, docker_quarto: str = None):
    """Run the complete feedback pipeline for a repo."""
    repo_path = Path(repo_path).resolve()

    if not validate_repo(repo_path):
        return False

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
        if provider:
            env['AI_PROVIDER'] = provider
        if model:
            env['AI_MODEL'] = model

        if output_path:
            env['OUTPUT_PATH'] = str(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # Step 1: Validate feedback configuration
        print("\n1  Validating feedback configuration...")
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / 'validate_feedback_setup.py')],
            capture_output=True, text=True, env=env
        )
        if result.returncode != 0:
            print(f"Validation failed:\n{result.stderr}")
            return False
        print("✓ Configuration valid")

        # Step 2: Render Quarto report
        if skip_render:
            print("\n2  Skipping Quarto render (--no-render)")
        else:
            print("\n2  Rendering Quarto report...")
            if use_docker:
                result = render_quarto_docker(repo_path, docker_image, docker_quarto)
            else:
                result = render_quarto_local(repo_path, env)

            if result.returncode != 0:
                print(f"Quarto render had issues (continuing):\n{result.stderr[:500]}")
            else:
                print("✓ Report rendered")

        # Step 3: Parse report
        print("\n3️⃣  Parsing report...")
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / 'parse_report.py')],
            capture_output=True, text=True, env=env
        )
        if result.returncode != 0:
            print(f"❌ Parse failed:\n{result.stderr}")
            return False
        print("✓ Report parsed")

        # Step 4: Generate AI feedback
        print("\n4️⃣  Generating AI feedback...")
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / 'ai_feedback_criterion.py')],
            capture_output=True, text=True, env=env, timeout=600
        )
        if result.returncode != 0:
            print(f"❌ Feedback generation failed:\n{result.stderr}")
            return False
        if result.stdout:
            print(result.stdout)
        print("✓ Feedback generated")

        # Step 5: Create issue or save to file
        print("\n5️⃣  Saving feedback...")
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / 'create_issue.py')],
            capture_output=True, text=True, env=env
        )
        if result.returncode != 0:
            print(f"❌ Save failed:\n{result.stderr}")
            return False
        if result.stdout:
            print(result.stdout)
        print("✓ Feedback saved")

        print(f"\n✅ Successfully processed {repo_path.name}")
        return True

    except subprocess.TimeoutExpired:
        print("❌ Process timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        os.chdir(original_cwd)

def main():
    parser = argparse.ArgumentParser(
        description='Run AI feedback locally on student repos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('path', help='Path to student repo or parent directory of repos')
    parser.add_argument('--instructor-repo',
                       default='/Users/steve/Development/quarto_reports/ai-feedback-system',
                       help='Path to instructor repo with rubric/guidance (default: ai-feedback-system)')
    parser.add_argument('--output-dir',
                       help='Directory to save feedback files (defaults to repo/.github)')
    parser.add_argument('--config',
                       help='Path to custom config.yml (instructor repo config used by default)')
    parser.add_argument('--list', action='store_true',
                       help='List available repos and exit')
    parser.add_argument('--batch', action='store_true',
                       help='Process all repos in directory')

    # Provider options
    parser.add_argument('--provider',
                       choices=['github_models', 'openrouter', 'anthropic', 'gemini', 'openai'],
                       help='AI provider (overrides global/repo config)')
    parser.add_argument('--model',
                       help='Model name (overrides global/repo config)')
    parser.add_argument('--init-config', action='store_true',
                       help='Create default global config at ~/.ai-feedback/config.yml and exit')

    # Rendering options
    parser.add_argument('--docker', action='store_true',
                       help='Use Docker container for Quarto rendering (matches codespace env)')
    parser.add_argument('--docker-image', default=DOCKER_IMAGE,
                       help=f'Docker image for rendering (default: {DOCKER_IMAGE})')
    parser.add_argument('--docker-quarto', default=DOCKER_QUARTO,
                       help=f'Quarto path inside container (default: {DOCKER_QUARTO})')
    parser.add_argument('--no-render', action='store_true',
                       help='Skip Quarto rendering (use existing output)')

    args = parser.parse_args()

    if args.init_config:
        from dot_github_folder.scripts.ai_provider import create_default_global_config
        create_default_global_config()
        return

    path = Path(args.path).resolve()
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

            for repo in repos:
                output_path = None
                if args.output_dir:
                    output_dir = Path(args.output_dir) / repo.name
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_path = output_dir / f'feedback.md'

                # Set up feedback config if needed
                if not (repo / '.github' / 'feedback').exists():
                    print(f"\nSetting up feedback config for {repo.name}...")
                    setup_feedback_config(repo, instructor_repo, output_format='flat_file')

                if run_feedback_pipeline(repo, output_path,
                                        provider=args.provider, model=args.model,
                                        use_docker=args.docker, skip_render=args.no_render,
                                        docker_image=args.docker_image,
                                        docker_quarto=args.docker_quarto):
                    successful += 1
                else:
                    failed += 1

            print(f"\n{'='*60}")
            print(f"Summary: {successful} successful, {failed} failed out of {len(repos)}")
            print(f"{'='*60}")
            return

        print(f"Found {len(repos)} repos. Use --batch to process all, or --list to see them.")
        sys.exit(1)

    # Single repo processing
    output_path = None
    if args.output_dir:
        output_dir = Path(args.output_dir) / path.name
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / 'feedback.md'

    # Set up feedback config if needed
    if not (path / '.github' / 'feedback').exists():
        print(f"Setting up feedback config...")
        setup_feedback_config(path, instructor_repo, output_format='flat_file')

    success = run_feedback_pipeline(path, output_path,
                                    provider=args.provider, model=args.model,
                                    use_docker=args.docker, skip_render=args.no_render,
                                    docker_image=args.docker_image,
                                    docker_quarto=args.docker_quarto)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
