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


def load_repo_paths(repos_file: Optional[str], repos_dir: Optional[str]) -> list:
    pass


def find_criterion(rubric: dict, name: str) -> Optional[dict]:
    pass


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
