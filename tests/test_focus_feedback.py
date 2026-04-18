"""Tests for focus-feedback.py"""
import io
import json
import sys
from pathlib import Path
from importlib import import_module
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))
focus = import_module('focus-feedback')


def test_import():
    """Script imports without error."""
    assert focus is not None


def test_load_repo_paths_from_file(tmp_path):
    repo1 = tmp_path / 'student-1'
    repo2 = tmp_path / 'student-2'
    repo1.mkdir(); repo2.mkdir()
    (repo1 / 'index.qmd').touch()
    (repo2 / 'index.qmd').touch()

    repos_file = tmp_path / 'repos.txt'
    repos_file.write_text(f'{repo1}\n{repo2}\n')

    result = focus.load_repo_paths(str(repos_file), None)
    assert result == [repo1, repo2]


def test_load_repo_paths_from_file_skips_blank_lines(tmp_path):
    repo1 = tmp_path / 'student-1'
    repo1.mkdir()
    (repo1 / 'index.qmd').touch()

    repos_file = tmp_path / 'repos.txt'
    repos_file.write_text(f'\n{repo1}\n\n')

    result = focus.load_repo_paths(str(repos_file), None)
    assert result == [repo1]


def test_load_repo_paths_from_dir(tmp_path):
    for name in ['student-1', 'student-2', 'student-3']:
        d = tmp_path / name
        d.mkdir()
        (d / 'index.qmd').touch()
    # This one has no index.qmd — should be excluded
    (tmp_path / 'not-a-repo').mkdir()

    result = focus.load_repo_paths(None, str(tmp_path))
    names = [p.name for p in result]
    assert sorted(names) == ['student-1', 'student-2', 'student-3']


def test_load_repo_paths_from_stdin(tmp_path):
    repo1 = tmp_path / 'student-1'
    repo1.mkdir()
    (repo1 / 'index.qmd').touch()

    with patch('sys.stdin', io.StringIO(f'{repo1}\n')):
        result = focus.load_repo_paths('-', None)
    assert result == [repo1]
