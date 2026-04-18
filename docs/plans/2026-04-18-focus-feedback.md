# Focus Feedback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `focus-feedback.py` — a rubric/guidance evaluation tool that runs a single named criterion across many repos and multiple LLM models, producing one aggregated comparison markdown report.

**Architecture:** A standalone script at the repo root that imports `analyze_criterion` and `resolve_provider_config` directly from `dot_github_folder/scripts/`, iterates repos × models in a loop, and writes a single aggregated markdown file. No subprocesses except to run `parse_report.py` when `parsed_report.json` is missing. No modifications to any existing file.

**Tech Stack:** Python 3.11, PyYAML, pytest, existing `ai_feedback_criterion.analyze_criterion`, `ai_provider.resolve_provider_config`

---

## File Structure

| File | Action | Responsibility |
|---|---|---|
| `focus-feedback.py` | Create | All logic: CLI, repo discovery, loading, AI loop, output |
| `tests/test_focus_feedback.py` | Create | Unit tests for all pure and filesystem functions |

No existing files are modified.

---

### Task 1: Bootstrap skeleton and passing smoke test

**Files:**
- Create: `focus-feedback.py`
- Create: `tests/test_focus_feedback.py`

- [ ] **Step 1: Create the test file with one passing smoke test**

```python
# tests/test_focus_feedback.py
"""Tests for focus-feedback.py"""
import sys
from pathlib import Path
from importlib import import_module

sys.path.insert(0, str(Path(__file__).parent.parent))
focus = import_module('focus-feedback')


def test_import():
    """Script imports without error."""
    assert focus is not None
```

- [ ] **Step 2: Create focus-feedback.py skeleton**

```python
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
```

- [ ] **Step 3: Run the smoke test — expect PASS**

```bash
cd /Users/steve/Development/quarto_reports/ai-feedback-system
python -m pytest tests/test_focus_feedback.py::test_import -v
```

Expected output contains: `PASSED`

- [ ] **Step 4: Commit**

```bash
git add focus-feedback.py tests/test_focus_feedback.py
git commit -m "feat: add focus-feedback.py skeleton and test bootstrap"
```

---

### Task 2: Repo discovery

**Files:**
- Modify: `focus-feedback.py` — implement `load_repo_paths` and helpers
- Modify: `tests/test_focus_feedback.py` — add discovery tests

- [ ] **Step 1: Write failing tests**

```python
# Add to tests/test_focus_feedback.py
import io
from unittest.mock import patch


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
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
python -m pytest tests/test_focus_feedback.py -k "repo_path" -v
```

Expected: 4 failures (TypeError or AttributeError since functions return `None`)

- [ ] **Step 3: Implement repo discovery**

Replace the `load_repo_paths` stub and add helpers in `focus-feedback.py`:

```python
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
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
python -m pytest tests/test_focus_feedback.py -k "repo_path" -v
```

Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add focus-feedback.py tests/test_focus_feedback.py
git commit -m "feat: implement repo discovery for focus-feedback"
```

---

### Task 3: Criterion lookup

**Files:**
- Modify: `focus-feedback.py` — implement `find_criterion`
- Modify: `tests/test_focus_feedback.py` — add criterion lookup tests

- [ ] **Step 1: Write failing tests**

```python
# Add to tests/test_focus_feedback.py

def test_find_criterion_exact_match(sample_rubric):
    result = focus.find_criterion(sample_rubric, 'Theory & Explanation')
    assert result is not None
    assert result['name'] == 'Theory & Explanation'


def test_find_criterion_case_insensitive(sample_rubric):
    result = focus.find_criterion(sample_rubric, 'theory & explanation')
    assert result is not None
    assert result['name'] == 'Theory & Explanation'


def test_find_criterion_not_found(sample_rubric):
    result = focus.find_criterion(sample_rubric, 'Nonexistent Criterion')
    assert result is None


def test_find_criterion_exact_takes_priority():
    # If there are two criteria where one matches exactly and one case-insensitively,
    # the exact match should be returned.
    rubric = {
        'criteria': [
            {'name': 'results', 'id': 'lower'},
            {'name': 'Results', 'id': 'upper'},
        ]
    }
    result = focus.find_criterion(rubric, 'Results')
    assert result['id'] == 'upper'
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
python -m pytest tests/test_focus_feedback.py -k "criterion" -v
```

Expected: 4 FAILED

- [ ] **Step 3: Implement find_criterion**

```python
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
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
python -m pytest tests/test_focus_feedback.py -k "criterion" -v
```

Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add focus-feedback.py tests/test_focus_feedback.py
git commit -m "feat: implement criterion lookup for focus-feedback"
```

---

### Task 4: File loading with override precedence

**Files:**
- Modify: `focus-feedback.py` — implement `load_rubric`, `load_guidance`, `load_config`
- Modify: `tests/test_focus_feedback.py` — add loading tests

- [ ] **Step 1: Write failing tests**

```python
# Add to tests/test_focus_feedback.py
import yaml as _yaml


def _write_rubric(path: Path, rubric: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_yaml.dump(rubric))


def test_load_rubric_uses_override(tmp_path, sample_rubric):
    override = tmp_path / 'my-rubric.yml'
    _write_rubric(override, sample_rubric)
    repo = tmp_path / 'repo'
    repo.mkdir()

    rubric, path = focus.load_rubric(override, repo, None)
    assert rubric['criteria'][0]['name'] == 'Theory & Explanation'
    assert path == override


def test_load_rubric_falls_back_to_repo(tmp_path, sample_rubric):
    repo = tmp_path / 'repo'
    repo_rubric = repo / '.github' / 'feedback' / 'rubric.yml'
    _write_rubric(repo_rubric, sample_rubric)

    rubric, path = focus.load_rubric(None, repo, None)
    assert rubric['criteria'][0]['name'] == 'Theory & Explanation'
    assert path == repo_rubric


def test_load_rubric_falls_back_to_instructor(tmp_path, sample_rubric):
    repo = tmp_path / 'repo'
    repo.mkdir()
    instructor = tmp_path / 'instructor'
    inst_rubric = instructor / '.github' / 'feedback' / 'rubric.yml'
    _write_rubric(inst_rubric, sample_rubric)

    rubric, path = focus.load_rubric(None, repo, instructor)
    assert path == inst_rubric


def test_load_rubric_raises_when_not_found(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    import pytest as _pytest
    with _pytest.raises(FileNotFoundError):
        focus.load_rubric(None, repo, None)


def test_load_rubric_raises_on_md_extension(tmp_path):
    md_file = tmp_path / 'RUBRIC.md'
    md_file.write_text('# Rubric')
    repo = tmp_path / 'repo'
    repo.mkdir()
    import pytest as _pytest
    with _pytest.raises(ValueError, match='md-to-yaml'):
        focus.load_rubric(md_file, repo, None)


def test_load_config_falls_back_to_minimal(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    config = focus.load_config(None, repo, None)
    assert config == focus.MINIMAL_CONFIG


def test_load_config_uses_override(tmp_path):
    override = tmp_path / 'config.yml'
    override.write_text(_yaml.dump({'feedback': {'scoring_enabled': True}}))
    repo = tmp_path / 'repo'
    repo.mkdir()
    config = focus.load_config(override, repo, None)
    assert config['feedback']['scoring_enabled'] is True


def test_load_guidance_uses_override(tmp_path):
    override = tmp_path / 'guidance.md'
    override.write_text('# My Guidance')
    repo = tmp_path / 'repo'
    repo.mkdir()
    text, path = focus.load_guidance(override, repo, None)
    assert text == '# My Guidance'
    assert path == override


def test_load_guidance_raises_when_not_found(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()
    import pytest as _pytest
    with _pytest.raises(FileNotFoundError):
        focus.load_guidance(None, repo, None)
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
python -m pytest tests/test_focus_feedback.py -k "load_rubric or load_config or load_guidance" -v
```

Expected: 9 FAILED

- [ ] **Step 3: Implement the three loaders**

```python
def _resolve_path(*candidates) -> Optional[Path]:
    """Return first existing path from candidates (skipping None)."""
    for p in candidates:
        if p is not None and Path(p).exists():
            return Path(p)
    return None


def load_rubric(override: Optional[Path], repo: Path,
                instructor_repo: Optional[Path]):
    """Load rubric.yml with override precedence. Returns (rubric_dict, path_used)."""
    inst_path = (Path(instructor_repo) / '.github' / 'feedback' / 'rubric.yml'
                 if instructor_repo else None)
    path = _resolve_path(
        override,
        repo / '.github' / 'feedback' / 'rubric.yml',
        inst_path,
    )
    if path is None:
        raise FileNotFoundError(
            'No rubric.yml found. Use --rubric or ensure '
            '.github/feedback/rubric.yml exists in the repo or instructor repo.'
        )
    if Path(path).suffix == '.md':
        raise ValueError(
            f'--rubric points to a .md file. Convert it first:\n'
            f'  python dot_github_folder/scripts/rubric_converter.py md-to-yaml {path} rubric.yml'
        )
    with open(path) as f:
        return _yaml.safe_load(f), path


def load_guidance(override: Optional[Path], repo: Path,
                  instructor_repo: Optional[Path]):
    """Load guidance.md with override precedence. Returns (text, path_used)."""
    inst_path = (Path(instructor_repo) / '.github' / 'feedback' / 'guidance.md'
                 if instructor_repo else None)
    path = _resolve_path(
        override,
        repo / '.github' / 'feedback' / 'guidance.md',
        inst_path,
    )
    if path is None:
        raise FileNotFoundError(
            'No guidance.md found. Use --guidance or ensure '
            '.github/feedback/guidance.md exists in the repo or instructor repo.'
        )
    return Path(path).read_text(), path


def load_config(override: Optional[Path], repo: Path,
                instructor_repo: Optional[Path]) -> dict:
    """Load config.yml with override precedence, falling back to MINIMAL_CONFIG."""
    inst_path = (Path(instructor_repo) / '.github' / 'config.yml'
                 if instructor_repo else None)
    path = _resolve_path(
        override,
        repo / '.github' / 'config.yml',
        inst_path,
    )
    if path is None:
        return copy.deepcopy(MINIMAL_CONFIG)
    with open(path) as f:
        return yaml.safe_load(f)
```

Also add `import yaml as _yaml` at the top of `focus-feedback.py` — but actually yaml is already imported as `yaml`, so the loaders can use `yaml.safe_load` directly. Remove the `import yaml as _yaml` from the loader implementations above (it was for the test helper `_write_rubric`, not the script itself).

- [ ] **Step 4: Run tests — expect PASS**

```bash
python -m pytest tests/test_focus_feedback.py -k "load_rubric or load_config or load_guidance" -v
```

Expected: 9 PASSED

- [ ] **Step 5: Commit**

```bash
git add focus-feedback.py tests/test_focus_feedback.py
git commit -m "feat: implement file loading with override precedence"
```

---

### Task 5: Parsed report loading

**Files:**
- Modify: `focus-feedback.py` — implement `load_parsed_report`
- Modify: `tests/test_focus_feedback.py` — add parsed report tests

- [ ] **Step 1: Write failing tests**

```python
# Add to tests/test_focus_feedback.py
from unittest.mock import patch, MagicMock


def test_load_parsed_report_reads_existing(tmp_path, sample_parsed_report):
    repo = tmp_path / 'repo'
    repo.mkdir()
    report_file = repo / 'parsed_report.json'
    report_file.write_text(json.dumps(sample_parsed_report))

    result = focus.load_parsed_report(repo)
    assert result['metadata']['title'] == 'Project 1: Euler Method'


def test_load_parsed_report_runs_parser_when_missing(tmp_path, sample_parsed_report):
    repo = tmp_path / 'repo'
    repo.mkdir()
    report_file = repo / 'parsed_report.json'

    def fake_run(cmd, **kwargs):
        # Simulate parse_report.py writing parsed_report.json
        report_file.write_text(json.dumps(sample_parsed_report))
        result = MagicMock()
        result.returncode = 0
        result.stderr = ''
        return result

    with patch('subprocess.run', side_effect=fake_run):
        result = focus.load_parsed_report(repo)

    assert result['metadata']['title'] == 'Project 1: Euler Method'


def test_load_parsed_report_raises_when_parser_fails(tmp_path):
    repo = tmp_path / 'repo'
    repo.mkdir()

    def fake_run(cmd, **kwargs):
        result = MagicMock()
        result.returncode = 1
        result.stderr = 'parse error'
        return result

    with patch('subprocess.run', side_effect=fake_run):
        import pytest as _pytest
        with _pytest.raises(RuntimeError, match='parse_report.py failed'):
            focus.load_parsed_report(repo)
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
python -m pytest tests/test_focus_feedback.py -k "parsed_report" -v
```

Expected: 3 FAILED

- [ ] **Step 3: Implement load_parsed_report**

```python
def load_parsed_report(repo: Path) -> dict:
    """Load parsed_report.json, running parse_report.py as subprocess if missing."""
    report_path = repo / 'parsed_report.json'
    if not report_path.exists():
        print(f'  parsed_report.json missing — running parse_report.py...')
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / 'parse_report.py')],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f'parse_report.py failed:\n{result.stderr}')
    with open(report_path) as f:
        return json.load(f)
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
python -m pytest tests/test_focus_feedback.py -k "parsed_report" -v
```

Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add focus-feedback.py tests/test_focus_feedback.py
git commit -m "feat: implement parsed report loading with auto-parse fallback"
```

---

### Task 6: Output formatting

**Files:**
- Modify: `focus-feedback.py` — implement formatting functions
- Modify: `tests/test_focus_feedback.py` — add formatting tests

- [ ] **Step 1: Write failing tests**

```python
# Add to tests/test_focus_feedback.py

def _make_result(assessment='Satisfactory', success=True):
    if not success:
        return {'success': False, 'error': 'Test error', 'criterion': 'X'}
    return {
        'success': True,
        'criterion': 'Results',
        'feedback': {
            'overall_assessment': assessment,
            'summary': 'Good overall.',
            'strengths': ['Clear figures', 'Good labels'],
            'areas_for_improvement': [
                {'issue': 'Missing units', 'suggestion': 'Add units to axes'}
            ],
        },
        'tokens': {'total_tokens': 100},
    }


def test_format_criterion_result_success():
    result = _make_result('Exemplary')
    text = focus.format_criterion_result(result)
    assert 'Exemplary' in text
    assert 'Clear figures' in text
    assert 'Missing units' in text
    assert 'Add units to axes' in text


def test_format_criterion_result_error():
    result = _make_result(success=False)
    text = focus.format_criterion_result(result)
    assert 'ERROR' in text or 'Test error' in text


def test_format_summary_table_single_model():
    repo_results = [
        {'repo': 'student-1', 'models': {'gpt-4o': _make_result('Exemplary')}},
        {'repo': 'student-2', 'models': {'gpt-4o': _make_result('Developing')}},
    ]
    table = focus.format_summary_table(repo_results, ['gpt-4o'])
    assert 'student-1' in table
    assert 'student-2' in table
    assert 'Exemplary' in table
    assert 'Developing' in table


def test_format_summary_table_multiple_models():
    repo_results = [
        {'repo': 'student-1', 'models': {
            'gpt-4o': _make_result('Exemplary'),
            'llama-4': _make_result('Satisfactory'),
        }},
    ]
    table = focus.format_summary_table(repo_results, ['gpt-4o', 'llama-4'])
    assert 'gpt-4o' in table
    assert 'llama-4' in table
    assert 'Exemplary' in table
    assert 'Satisfactory' in table


def test_format_summary_table_error_case():
    repo_results = [
        {'repo': 'broken', 'models': {'gpt-4o': {'success': False, 'error': 'oops'}}},
    ]
    table = focus.format_summary_table(repo_results, ['gpt-4o'])
    assert 'ERROR' in table


def test_format_aggregated_report_structure():
    repo_results = [
        {'repo': 'student-1', 'models': {'gpt-4o': _make_result('Satisfactory')}},
    ]
    report = focus.format_aggregated_report(
        repo_results,
        criterion_name='Results & Analysis',
        models=['gpt-4o'],
        rubric_path=Path('/some/rubric.yml'),
        guidance_path=Path('/some/guidance.md'),
    )
    assert '# Focus Feedback: Results & Analysis' in report
    assert 'student-1' in report
    assert 'gpt-4o' in report
    assert 'Summary' in report
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
python -m pytest tests/test_focus_feedback.py -k "format_" -v
```

Expected: 7 FAILED

- [ ] **Step 3: Implement formatting functions**

```python
def _get_assessment(result: dict) -> str:
    """Extract assessment label from a criterion result dict."""
    if not result.get('success'):
        return 'ERROR'
    fb = result.get('feedback', {})
    return fb.get('overall_assessment', 'N/A')


def format_summary_table(repo_results: list, models: list) -> str:
    """Build a markdown summary table: rows=repos, cols=models."""
    header = ['Repo'] + models
    rows = []
    for entry in repo_results:
        row = [entry['repo']]
        for model in models:
            result = entry['models'].get(model, {'success': False, 'error': 'Not run'})
            row.append(_get_assessment(result))
        rows.append(row)

    col_widths = [len(h) for h in header]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    def fmt(cells):
        return '| ' + ' | '.join(str(c).ljust(col_widths[i]) for i, c in enumerate(cells)) + ' |'

    sep = '|' + '|'.join('-' * (w + 2) for w in col_widths) + '|'
    return '\n'.join([fmt(header), sep] + [fmt(row) for row in rows])


def format_criterion_result(result: dict) -> str:
    """Format a single criterion result as markdown."""
    if not result.get('success'):
        return f'> **ERROR:** {result.get("error", "Unknown error")}\n'

    fb = result.get('feedback', {})
    lines = [f'**Assessment:** {fb.get("overall_assessment", "N/A")}\n']

    summary = fb.get('summary', '')
    if summary:
        lines.append(f'**Summary:** {summary}\n')

    strengths = fb.get('strengths', [])
    if strengths:
        lines.append('**Strengths:**')
        lines.extend(f'- {s}' for s in strengths)
        lines.append('')

    improvements = fb.get('areas_for_improvement', [])
    if improvements:
        lines.append('**Areas for Improvement:**')
        for item in improvements:
            if isinstance(item, dict):
                lines.append(
                    f'- **Issue:** {item.get("issue", "")}  '
                    f'**Suggestion:** {item.get("suggestion", "")}'
                )
            else:
                lines.append(f'- {item}')
        lines.append('')

    return '\n'.join(lines)


def format_aggregated_report(repo_results: list, criterion_name: str, models: list,
                              rubric_path: Optional[Path],
                              guidance_path: Optional[Path]) -> str:
    """Build the complete aggregated markdown report."""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    rubric_str = str(rubric_path) if rubric_path else 'default'
    guidance_str = str(guidance_path) if guidance_path else 'default'

    lines = [
        f'# Focus Feedback: {criterion_name}',
        f'Generated: {now}  |  Repos: {len(repo_results)}  |  Models: {", ".join(models)}',
        f'Rubric: {rubric_str}  |  Guidance: {guidance_str}',
        '',
        '## Summary',
        '',
        format_summary_table(repo_results, models),
        '',
    ]

    for entry in repo_results:
        lines += ['---', '', f'## {entry["repo"]}', '']
        for model in models:
            result = entry['models'].get(model, {'success': False, 'error': 'Not run'})
            assessment = _get_assessment(result)
            lines += [f'### {model} — {assessment}', '']
            lines.append(format_criterion_result(result))
            lines.append('')

    return '\n'.join(lines)
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
python -m pytest tests/test_focus_feedback.py -k "format_" -v
```

Expected: 7 PASSED

- [ ] **Step 5: Commit**

```bash
git add focus-feedback.py tests/test_focus_feedback.py
git commit -m "feat: implement output formatting for focus-feedback"
```

---

### Task 7: Core run loop

**Files:**
- Modify: `focus-feedback.py` — implement `run_focus_for_repo`
- Modify: `tests/test_focus_feedback.py` — add run loop tests

- [ ] **Step 1: Write failing tests**

```python
# Add to tests/test_focus_feedback.py
from unittest.mock import patch


def test_run_focus_for_repo_success(tmp_path, sample_parsed_report,
                                    sample_criterion, sample_rubric):
    repo = tmp_path / 'student-1'
    repo.mkdir()
    (repo / 'parsed_report.json').write_text(json.dumps(sample_parsed_report))
    (repo / 'index.qmd').touch()

    fake_result = {
        'criterion': 'Implementation/Code',
        'feedback': {'overall_assessment': 'Satisfactory', 'summary': 'ok',
                     'strengths': [], 'areas_for_improvement': []},
        'success': True,
        'tokens': {'total_tokens': 50},
    }
    provider_config = {'model': 'gpt-4o', 'provider': 'github_models',
                       'api_base': 'https://example.com', 'fallback': 'gpt-4o-mini',
                       'extractor': 'gpt-4o-mini', 'api_key': 'test'}

    with patch.object(focus, 'analyze_criterion', return_value=fake_result):
        entry = focus.run_focus_for_repo(
            repo, sample_criterion, 'guidance text', {},
            models=['gpt-4o'], provider_config_base=provider_config,
        )

    assert entry['repo'] == 'student-1'
    assert entry['models']['gpt-4o']['success'] is True


def test_run_focus_for_repo_multiple_models(tmp_path, sample_parsed_report,
                                             sample_criterion):
    repo = tmp_path / 'student-1'
    repo.mkdir()
    (repo / 'parsed_report.json').write_text(json.dumps(sample_parsed_report))
    (repo / 'index.qmd').touch()

    call_count = {'n': 0}

    def fake_analyze(report, criterion, guidance, config, criterion_index=0,
                     provider_config=None):
        call_count['n'] += 1
        return {
            'criterion': criterion['name'],
            'feedback': {'overall_assessment': f'result-{call_count["n"]}',
                         'summary': '', 'strengths': [], 'areas_for_improvement': []},
            'success': True,
            'tokens': {'total_tokens': 10},
        }

    provider_config = {'model': 'gpt-4o', 'provider': 'github_models',
                       'api_base': 'https://example.com', 'fallback': 'gpt-4o-mini',
                       'extractor': 'gpt-4o-mini', 'api_key': 'test'}

    with patch.object(focus, 'analyze_criterion', side_effect=fake_analyze):
        entry = focus.run_focus_for_repo(
            repo, sample_criterion, 'guidance', {},
            models=['model-a', 'model-b'], provider_config_base=provider_config,
        )

    assert 'model-a' in entry['models']
    assert 'model-b' in entry['models']
    assert call_count['n'] == 2


def test_run_focus_for_repo_parse_failure(tmp_path, sample_criterion):
    repo = tmp_path / 'broken-repo'
    repo.mkdir()
    # No parsed_report.json and parse_report.py will fail

    def fake_run(cmd, **kwargs):
        m = MagicMock()
        m.returncode = 1
        m.stderr = 'failed'
        return m

    provider_config = {'model': 'gpt-4o', 'provider': 'github_models',
                       'api_base': 'https://example.com', 'fallback': 'gpt-4o-mini',
                       'extractor': 'gpt-4o-mini', 'api_key': 'test'}

    with patch('subprocess.run', side_effect=fake_run):
        entry = focus.run_focus_for_repo(
            repo, sample_criterion, 'guidance', {},
            models=['gpt-4o'], provider_config_base=provider_config,
        )

    assert entry['models']['gpt-4o']['success'] is False
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
python -m pytest tests/test_focus_feedback.py -k "run_focus" -v
```

Expected: 3 FAILED

- [ ] **Step 3: Implement run_focus_for_repo**

```python
def run_focus_for_repo(repo: Path, criterion: dict, guidance: str, config: dict,
                       models: list, provider_config_base: dict,
                       disable_json_mode: bool = False,
                       verbose: bool = False) -> dict:
    """Run focus feedback for one repo across all models.

    Returns dict: {'repo': name, 'models': {model_id: result_dict}}
    """
    try:
        report = load_parsed_report(repo)
    except Exception as e:
        error = {'success': False, 'error': str(e)}
        return {'repo': repo.name, 'models': {m: error for m in models}}

    model_results = {}
    original_cwd = Path.cwd()
    try:
        os.chdir(repo)
        if disable_json_mode:
            os.environ['AI_DISABLE_JSON_MODE'] = 'true'
        for model in models:
            print(f'\n  [{repo.name}] Model: {model}')
            pc = copy.deepcopy(provider_config_base)
            pc['model'] = model
            try:
                result = analyze_criterion(
                    report, criterion, guidance, config,
                    criterion_index=0, provider_config=pc,
                )
                model_results[model] = result
            except Exception as e:
                model_results[model] = {'success': False, 'error': str(e)}
    finally:
        os.chdir(original_cwd)
        if disable_json_mode:
            os.environ.pop('AI_DISABLE_JSON_MODE', None)

    return {'repo': repo.name, 'models': model_results}
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
python -m pytest tests/test_focus_feedback.py -k "run_focus" -v
```

Expected: 3 PASSED

- [ ] **Step 5: Run all tests so far — expect all PASS**

```bash
python -m pytest tests/test_focus_feedback.py -v
```

Expected: all PASSED (no regressions)

- [ ] **Step 6: Commit**

```bash
git add focus-feedback.py tests/test_focus_feedback.py
git commit -m "feat: implement core run loop for focus-feedback"
```

---

### Task 8: CLI and main()

**Files:**
- Modify: `focus-feedback.py` — implement `main()` with full argparse

- [ ] **Step 1: Write CLI smoke tests**

```python
# Add to tests/test_focus_feedback.py
import subprocess as _subprocess


def test_help_exits_cleanly():
    result = _subprocess.run(
        [sys.executable, 'focus-feedback.py', '--help'],
        capture_output=True, text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert result.returncode == 0
    assert '--criterion' in result.stdout
    assert '--models' in result.stdout
    assert '--repos' in result.stdout
    assert '--repos-dir' in result.stdout


def test_missing_criterion_exits_with_error():
    result = _subprocess.run(
        [sys.executable, 'focus-feedback.py', '--repos-dir', '/tmp'],
        capture_output=True, text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert result.returncode != 0
```

- [ ] **Step 2: Run tests — expect FAIL (main() is a stub)**

```bash
python -m pytest tests/test_focus_feedback.py -k "help or missing_criterion" -v
```

Expected: 2 FAILED

- [ ] **Step 3: Implement main()**

```python
def main():
    parser = argparse.ArgumentParser(
        description='Run focused AI feedback on one criterion across many repos and models.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Repo source (mutually exclusive)
    repo_group = parser.add_mutually_exclusive_group()
    repo_group.add_argument('--repos', metavar='FILE',
                            help='File of repo paths (one per line). Use - for stdin.')
    repo_group.add_argument('--repos-dir', metavar='DIR',
                            help='Discover all subdirs of DIR that contain index.qmd.')

    # Required
    parser.add_argument('--criterion', required=True,
                        help='Criterion name to evaluate (must match a criterion in rubric.yml).')

    # AI options
    parser.add_argument('--models', nargs='+', metavar='MODEL',
                        help='One or more model IDs to compare. Defaults to configured primary model.')
    parser.add_argument('--provider',
                        choices=['github_models', 'openrouter', 'anthropic', 'gemini', 'openai'],
                        help='AI provider.')
    parser.add_argument('--disable-json-mode', action='store_true',
                        help='Skip JSON response format (for models that do not support it).')

    # Override files
    parser.add_argument('--rubric', metavar='PATH', type=Path,
                        help='Override rubric.yml for all repos.')
    parser.add_argument('--guidance', metavar='PATH', type=Path,
                        help='Override guidance.md for all repos.')
    parser.add_argument('--config', metavar='PATH', type=Path,
                        help='Override config.yml for all repos.')
    parser.add_argument('--instructor-repo', metavar='PATH', type=Path,
                        help='Instructor repo for rubric/guidance/config defaults.')

    # Output
    parser.add_argument('--output', metavar='DIR', type=Path,
                        help='Output directory. Defaults to ./focus-feedback-TIMESTAMP/.')
    parser.add_argument('--verbose', action='store_true',
                        help='Print per-criterion AI call details.')

    args = parser.parse_args()

    # Set provider env var so resolve_provider_config picks it up
    if args.provider:
        os.environ['AI_PROVIDER'] = args.provider

    # Resolve output directory
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    output_dir = args.output or Path(f'focus-feedback-{timestamp}')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load repos
    try:
        repos = load_repo_paths(args.repos, args.repos_dir)
    except Exception as e:
        print(f'ERROR loading repos: {e}', file=sys.stderr)
        sys.exit(1)

    if not repos:
        print('ERROR: No repos found.', file=sys.stderr)
        sys.exit(1)

    print(f'Found {len(repos)} repo(s).')

    # Load rubric from first repo (or override), find criterion
    # We load rubric once globally if an override is given; otherwise per-repo.
    # For simplicity and correct override behavior, load from the first repo
    # to validate the criterion name, then re-load per repo in the loop.
    first_repo = repos[0]
    instructor_repo = args.instructor_repo

    try:
        rubric, rubric_path = load_rubric(args.rubric, first_repo, instructor_repo)
    except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)

    criterion = find_criterion(rubric, args.criterion)
    if criterion is None:
        names = [c.get('name') for c in rubric.get('criteria', [])]
        print(f'ERROR: Criterion "{args.criterion}" not found.', file=sys.stderr)
        print(f'Available criteria: {", ".join(names)}', file=sys.stderr)
        sys.exit(1)

    try:
        guidance, guidance_path = load_guidance(args.guidance, first_repo, instructor_repo)
    except Exception as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)

    config = load_config(args.config, first_repo, instructor_repo)

    # Resolve provider config once; model is overridden per-call
    provider_config_base = resolve_provider_config(config)

    # Determine models
    models = args.models or [provider_config_base['model']]

    print(f'Criterion: {args.criterion}')
    print(f'Models: {", ".join(models)}')
    print(f'Rubric: {rubric_path}')
    print(f'Guidance: {guidance_path}')
    print()

    # Run loop
    all_results = []
    for repo in repos:
        print(f'\n{"="*60}')
        print(f'Repo: {repo.name}')
        print(f'{"="*60}')

        # Per-repo: reload rubric/guidance/config if no override given
        if args.rubric is None or args.guidance is None or args.config is None:
            try:
                r_rubric, _ = load_rubric(args.rubric, repo, instructor_repo)
                r_criterion = find_criterion(r_rubric, args.criterion) or criterion
                r_guidance, _ = load_guidance(args.guidance, repo, instructor_repo)
                r_config = load_config(args.config, repo, instructor_repo)
            except Exception:
                # Fall back to values loaded from first repo
                r_criterion = criterion
                r_guidance = guidance
                r_config = config
        else:
            r_criterion = criterion
            r_guidance = guidance
            r_config = config

        entry = run_focus_for_repo(
            repo, r_criterion, r_guidance, r_config,
            models=models,
            provider_config_base=provider_config_base,
            disable_json_mode=args.disable_json_mode,
            verbose=args.verbose,
        )
        all_results.append(entry)

    # Write output
    output_file = output_dir / f'focus-feedback-{timestamp}.md'
    report_text = format_aggregated_report(
        all_results,
        criterion_name=args.criterion,
        models=models,
        rubric_path=rubric_path,
        guidance_path=guidance_path,
    )
    output_file.write_text(report_text)

    print(f'\n{"="*60}')
    print(f'Done. Report saved to: {output_file}')
    print(f'{"="*60}')
```

- [ ] **Step 4: Run CLI tests — expect PASS**

```bash
python -m pytest tests/test_focus_feedback.py -k "help or missing_criterion" -v
```

Expected: 2 PASSED

- [ ] **Step 5: Run all tests**

```bash
python -m pytest tests/test_focus_feedback.py -v
```

Expected: all PASSED

- [ ] **Step 6: Commit**

```bash
git add focus-feedback.py tests/test_focus_feedback.py
git commit -m "feat: implement CLI and main() for focus-feedback"
```

---

### Task 9: Final integration and cleanup

**Files:**
- Modify: `focus-feedback.py` — make script executable, verify `--help` output

- [ ] **Step 1: Verify --help output reads cleanly**

```bash
python focus-feedback.py --help
```

Expected: clean output showing all flags with descriptions.

- [ ] **Step 2: Verify --list-style invocation works with stdin**

```bash
echo "" | python focus-feedback.py --criterion "Results" 2>&1 | head -5
```

Expected: prints "ERROR: No repos found." (or similar) and exits non-zero. This verifies stdin path is wired correctly even with empty input.

- [ ] **Step 3: Verify criterion-not-found error is helpful**

Create a minimal rubric file and test the error message:

```bash
python -c "
import yaml, tempfile, os
rubric = {'criteria': [{'name': 'Abstract', 'id': 'abstract', 'weight': 10, 'description': 'test', 'levels': {}}]}
with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
    yaml.dump(rubric, f)
    name = f.name
print(name)
" 2>&1
```

Then run:
```bash
echo /nonexistent | python focus-feedback.py --criterion "Nonexistent" --rubric /tmp/<the-yml-file> 2>&1
```

Expected output contains "Available criteria: Abstract".

- [ ] **Step 4: Make the script executable**

```bash
chmod +x focus-feedback.py
```

- [ ] **Step 5: Run the full test suite to confirm nothing is broken**

```bash
python -m pytest tests/test_focus_feedback.py -v
```

Expected: all PASSED

- [ ] **Step 6: Run broader test suite to confirm no regressions**

```bash
python -m pytest tests/ -v --ignore=tests/test_focus_feedback.py 2>&1 | tail -20
```

Expected: same pass/fail counts as before this feature was added.

- [ ] **Step 7: Final commit**

```bash
git add focus-feedback.py
git commit -m "feat: focus-feedback.py — focused rubric/guidance evaluation tool

Runs a single rubric criterion across many repos and multiple LLM models,
producing a single aggregated comparison markdown report for rubric iteration.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Covered by |
|---|---|
| `--repos FILE` reads paths from file, one per line | Task 2 |
| `--repos -` reads from stdin | Task 2 |
| `--repos-dir DIR` discovers subdirs with index.qmd | Task 2 |
| Mutually exclusive `--repos` / `--repos-dir` | Task 8 (argparse `add_mutually_exclusive_group`) |
| `--criterion NAME` required, exact + case-insensitive match | Tasks 3, 8 |
| `--models` one or more model IDs | Task 8 |
| `--provider` | Task 8 |
| `--rubric`, `--guidance`, `--config` overrides | Tasks 4, 8 |
| `--instructor-repo` for defaults | Tasks 4, 8 |
| `--output DIR` | Task 8 |
| `--disable-json-mode` | Tasks 7, 8 |
| `--verbose` | Tasks 7, 8 |
| Override precedence: CLI > repo > instructor > minimal | Task 4 |
| Skip render (always) | Inherent — no render step exists |
| Reuse parsed_report.json, run parser if missing | Task 5 |
| Per-repo × per-model AI call via `analyze_criterion` directly | Task 7 |
| Model override via deep-copy of provider_config | Task 7 |
| Aggregated report: summary table + per-repo per-model sections | Tasks 6, 8 |
| ERROR rows in table and body for failed repos | Tasks 6, 7 |
| `.md` rubric extension detected, helpful error | Task 4 |
| Criterion not found: print available names | Task 8 |
| Output written to `focus-feedback-TIMESTAMP.md` | Task 8 |

No gaps found.

**Placeholder scan:** No TBDs, TODOs, or vague steps. All code blocks are complete.

**Type consistency:** `run_focus_for_repo` returns `{'repo': str, 'models': {model_id: result}}`. `format_summary_table` and `format_aggregated_report` both consume this shape. `format_criterion_result` takes a single result dict (one entry from `models`). Consistent throughout.
