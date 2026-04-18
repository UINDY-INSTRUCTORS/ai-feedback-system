#!/usr/bin/env python3
"""
Focused rubric/guidance evaluation tool.

Runs a single criterion across many repos and multiple LLM models,
producing a single aggregated comparison markdown report.

Usage:
    # From a repos file (one path per line):
    python focus-feedback.py --repos repos.txt --criterion "Results & Analysis"

    # From stdin:
    cat repos.txt | python focus-feedback.py --criterion "Results & Analysis"

    # From a directory:
    python focus-feedback.py --repos-dir ~/ph230/repos --criterion "Results"

    # Multiple models:
    python focus-feedback.py --repos repos.txt --criterion "Results" \\
        --models gpt-4o meta-llama/llama-4-scout --provider openrouter
"""

import copy
import json
import os
import subprocess
import sys
import yaml
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

SCRIPT_DIR = Path(__file__).parent / 'dot_github_folder' / 'scripts'
sys.path.insert(0, str(SCRIPT_DIR))

from ai_feedback_criterion import analyze_criterion
from ai_provider import resolve_provider_config

MINIMAL_CONFIG = {
    'feedback': {'scoring_enabled': False},
    'vision': {'enabled': False},
    'request_timeout': 120,
}


def _load_paths_from_file(file_path: str) -> list:
    """Read repo paths from a file or stdin ('-'), one per line."""
    if file_path == '-':
        lines = sys.stdin.read().splitlines()
    else:
        lines = Path(file_path).read_text().splitlines()
    return [Path(line.strip()) for line in lines if line.strip()]


def _find_repos_in_dir(directory: Path) -> list:
    """Discover subdirectories of directory that contain index.qmd."""
    return sorted(
        p for p in Path(directory).iterdir()
        if p.is_dir() and (p / 'index.qmd').exists()
    )


def load_repo_paths(repos_file: Optional[str], repos_dir: Optional[str]) -> list:
    """Return list of repo Paths. repos_file and repos_dir are mutually exclusive."""
    if repos_file is not None:
        return _load_paths_from_file(repos_file)
    elif repos_dir is not None:
        return _find_repos_in_dir(Path(repos_dir))
    else:
        return _load_paths_from_file('-')


def find_criterion(rubric: dict, name: str) -> Optional[dict]:
    """Find criterion by exact name, then case-insensitive. Returns None if not found."""
    criteria = rubric.get('criteria', [])
    for c in criteria:
        if c.get('name') == name:
            return c
    name_lower = name.lower()
    for c in criteria:
        if c.get('name', '').lower() == name_lower:
            return c
    return None


def load_rubric(override: Optional[Path], repo: Path, instructor_repo: Optional[Path]):
    pass


def load_guidance(override: Optional[Path], repo: Path, instructor_repo: Optional[Path]):
    pass


def load_config(override: Optional[Path], repo: Path, instructor_repo: Optional[Path]) -> dict:
    pass


def load_parsed_report(repo: Path) -> dict:
    pass


def format_summary_table(repo_results: list, models: list) -> str:
    pass


def format_criterion_result(result: dict) -> str:
    pass


def format_aggregated_report(repo_results: list, criterion_name: str, models: list,
                              rubric_path: Optional[Path], guidance_path: Optional[Path]) -> str:
    pass


def run_focus_for_repo(repo: Path, criterion: dict, guidance: str, config: dict,
                       models: list, provider_config_base: dict,
                       disable_json_mode: bool = False, verbose: bool = False) -> dict:
    pass


def main():
    pass


if __name__ == '__main__':
    main()
