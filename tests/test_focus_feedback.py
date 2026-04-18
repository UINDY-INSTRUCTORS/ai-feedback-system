"""Tests for focus-feedback.py"""
import io
import json
import os
import sys
from pathlib import Path
from importlib import import_module
from unittest.mock import patch, MagicMock

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
    rubric = {
        'criteria': [
            {'name': 'results', 'id': 'lower'},
            {'name': 'Results', 'id': 'upper'},
        ]
    }
    result = focus.find_criterion(rubric, 'Results')
    assert result['id'] == 'upper'


import yaml as _yaml


def _write_rubric(path, rubric):
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


def test_run_focus_for_repo_analyze_exception(tmp_path, sample_parsed_report, sample_criterion):
    repo = tmp_path / 'student-1'
    repo.mkdir()
    (repo / 'parsed_report.json').write_text(json.dumps(sample_parsed_report))

    provider_config = {'model': 'gpt-4o', 'provider': 'github_models',
                       'api_base': 'https://example.com', 'fallback': 'gpt-4o-mini',
                       'extractor': 'gpt-4o-mini', 'api_key': 'test'}

    with patch.object(focus, 'analyze_criterion', side_effect=RuntimeError('API error')):
        entry = focus.run_focus_for_repo(
            repo, sample_criterion, 'guidance', {},
            models=['gpt-4o'], provider_config_base=provider_config,
        )

    assert entry['models']['gpt-4o']['success'] is False
    assert 'API error' in entry['models']['gpt-4o']['error']


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


def test_run_focus_for_repo_disable_json_mode(tmp_path, sample_parsed_report, sample_criterion):
    repo = tmp_path / 'student-1'
    repo.mkdir()
    (repo / 'parsed_report.json').write_text(json.dumps(sample_parsed_report))

    seen_env = {}

    def fake_analyze(report, criterion, guidance, config, criterion_index=0,
                     provider_config=None):
        seen_env['during'] = os.environ.get('AI_DISABLE_JSON_MODE')
        return {
            'criterion': criterion['name'],
            'feedback': {'overall_assessment': 'Satisfactory', 'summary': '',
                         'strengths': [], 'areas_for_improvement': []},
            'success': True, 'tokens': {'total_tokens': 10},
        }

    provider_config = {'model': 'gpt-4o', 'provider': 'github_models',
                       'api_base': 'https://example.com', 'fallback': 'gpt-4o-mini',
                       'extractor': 'gpt-4o-mini', 'api_key': 'test'}

    os.environ.pop('AI_DISABLE_JSON_MODE', None)  # ensure clean state
    with patch.object(focus, 'analyze_criterion', side_effect=fake_analyze):
        focus.run_focus_for_repo(
            repo, sample_criterion, 'guidance', {},
            models=['gpt-4o'], provider_config_base=provider_config,
            disable_json_mode=True,
        )

    assert seen_env['during'] == 'true'
    assert 'AI_DISABLE_JSON_MODE' not in os.environ
