"""
Tests for batch summary table generation in run-local-feedback.py.

Tests cover:
- extract_scores_from_feedback: reading feedback.json and rubric
- build_summary_table: markdown + CSV output in both scoring modes
- Scoring override logic (--scoring / --no-scoring)
"""

import pytest
import sys
import json
import csv
import yaml
from pathlib import Path

# Add project root to path so we can import the runner
sys.path.insert(0, str(Path(__file__).parent.parent))

from importlib import import_module
runner = import_module('run-local-feedback')

extract_scores_from_feedback = runner.extract_scores_from_feedback
build_summary_table = runner.build_summary_table


# ============================================================================
# Helpers
# ============================================================================

def make_rubric(criteria):
    """Create a rubric.yml dict with the given criteria list."""
    return {
        'assignment': {'name': 'test'},
        'criteria': criteria,
    }


def make_feedback(items):
    """Create a feedback.json list from simplified items.

    Each item: (name, success, score_or_assessment)
    If score_or_assessment is a number, it's a score; otherwise it's an assessment string.
    """
    result = []
    for name, success, value in items:
        if success:
            fb = {'summary': 'Good work.'}
            if isinstance(value, (int, float)):
                fb['score'] = value
                fb['overall_assessment'] = 'Satisfactory'
            else:
                fb['overall_assessment'] = value
            result.append({
                'criterion': name,
                'success': True,
                'feedback': fb,
                'tokens': {'total_tokens': 100},
            })
        else:
            result.append({
                'criterion': name,
                'success': False,
                'error': 'API error',
            })
    return result


def setup_repo(tmp_path, criteria_weights, feedback_items):
    """Set up a fake repo with rubric and feedback files."""
    repo = tmp_path / 'student-repo'
    repo.mkdir()
    (repo / 'index.qmd').write_text('# Report')

    feedback_dir = repo / '.github' / 'feedback'
    feedback_dir.mkdir(parents=True)

    rubric_criteria = [
        {'id': f'c{i}', 'name': name, 'weight': weight}
        for i, (name, weight) in enumerate(criteria_weights)
    ]
    with open(feedback_dir / 'rubric.yml', 'w') as f:
        yaml.dump(make_rubric(rubric_criteria), f)

    with open(repo / 'feedback.json', 'w') as f:
        json.dump(make_feedback(feedback_items), f)

    return repo


# ============================================================================
# extract_scores_from_feedback
# ============================================================================

@pytest.mark.unit
class TestExtractScoresFromFeedback:
    """Tests for score extraction from feedback.json."""

    def test_numerical_scores(self, tmp_path):
        """Extracts numerical scores and computes percentages."""
        repo = setup_repo(tmp_path,
            criteria_weights=[('Theory', 20), ('Code', 40)],
            feedback_items=[
                ('Theory', True, 18),
                ('Code', True, 30),
            ])

        result = extract_scores_from_feedback(repo)

        assert result['repo'] == 'student-repo'
        assert result['criteria']['Theory']['score'] == 18
        assert result['criteria']['Theory']['max'] == 20
        assert result['criteria']['Theory']['pct'] == 90.0
        assert result['criteria']['Code']['pct'] == 75.0

    def test_assessment_only(self, tmp_path):
        """Extracts assessment levels when scoring is disabled."""
        repo = setup_repo(tmp_path,
            criteria_weights=[('Theory', 20), ('Code', 40)],
            feedback_items=[
                ('Theory', True, 'Exemplary'),
                ('Code', True, 'Satisfactory'),
            ])

        result = extract_scores_from_feedback(repo)

        assert result['criteria']['Theory']['assessment'] == 'Exemplary'
        assert result['criteria']['Theory']['score'] is None
        assert result['criteria']['Theory']['pct'] is None
        assert result['criteria']['Code']['assessment'] == 'Satisfactory'

    def test_failed_criterion(self, tmp_path):
        """Failed criteria are marked as ERROR."""
        repo = setup_repo(tmp_path,
            criteria_weights=[('Theory', 20)],
            feedback_items=[('Theory', False, None)])

        result = extract_scores_from_feedback(repo)

        assert result['criteria']['Theory']['assessment'] == 'ERROR'

    def test_missing_feedback_json(self, tmp_path):
        """Returns error when feedback.json doesn't exist."""
        repo = tmp_path / 'empty-repo'
        repo.mkdir()

        result = extract_scores_from_feedback(repo)

        assert result['error'] == 'No feedback.json'
        assert result['criteria'] == {}

    def test_missing_rubric(self, tmp_path):
        """Works without rubric (max scores unknown, no percentages)."""
        repo = tmp_path / 'no-rubric'
        repo.mkdir()
        (repo / 'feedback.json').write_text(json.dumps(
            make_feedback([('Theory', True, 15)])
        ))

        result = extract_scores_from_feedback(repo)

        assert result['criteria']['Theory']['score'] == 15
        # No rubric -> max is 0 -> pct is None
        assert result['criteria']['Theory']['pct'] is None

    def test_nested_feedback_dict(self, tmp_path):
        """Handles feedback nested inside a 'feedback' key."""
        repo = tmp_path / 'nested'
        repo.mkdir()
        feedback = [{
            'criterion': 'Theory',
            'success': True,
            'feedback': {
                'feedback': {
                    'overall_assessment': 'Good',
                    'summary': 'Fine.',
                }
            },
        }]
        (repo / 'feedback.json').write_text(json.dumps(feedback))

        result = extract_scores_from_feedback(repo)

        assert result['criteria']['Theory']['assessment'] == 'Good'


# ============================================================================
# build_summary_table
# ============================================================================

@pytest.mark.unit
class TestBuildSummaryTable:
    """Tests for summary table generation."""

    def _make_scores(self, repos_data):
        """Build all_scores list from simplified data.

        repos_data: list of (repo_name, {criterion: (score, max, pct, assessment)})
        """
        result = []
        for repo_name, criteria in repos_data:
            entry = {'repo': repo_name, 'criteria': {}}
            for cn, (score, mx, pct, assessment) in criteria.items():
                entry['criteria'][cn] = {
                    'score': score, 'max': mx, 'pct': pct, 'assessment': assessment,
                }
            result.append(entry)
        return result

    def test_scoring_mode_csv(self, tmp_path):
        """Generates CSV with percentage columns when scoring=True."""
        scores = self._make_scores([
            ('repo-a', {'Theory': (18, 20, 90.0, 'Exemplary'), 'Code': (30, 40, 75.0, 'Satisfactory')}),
            ('repo-b', {'Theory': (10, 20, 50.0, 'Developing'), 'Code': (20, 40, 50.0, 'Developing')}),
        ])

        build_summary_table(scores, tmp_path, scoring=True)

        csv_path = tmp_path / 'summary.csv'
        assert csv_path.exists()
        with open(csv_path) as f:
            reader = csv.reader(f)
            header = next(reader)
        assert header[0] == 'Repo'
        assert 'Theory (%)' in header
        assert 'Code (%)' in header
        assert 'Overall (%)' in header

    def test_no_scoring_mode_csv(self, tmp_path):
        """Generates CSV with assessment columns when scoring=False."""
        scores = self._make_scores([
            ('repo-a', {'Theory': (None, 20, None, 'Exemplary'), 'Code': (None, 40, None, 'Satisfactory')}),
        ])

        build_summary_table(scores, tmp_path, scoring=False)

        csv_path = tmp_path / 'summary.csv'
        with open(csv_path) as f:
            reader = csv.reader(f)
            header = next(reader)
            row = next(reader)
        # No (%) in headers, no Overall column
        assert 'Theory' in header
        assert 'Overall (%)' not in header
        assert row[1] == 'Exemplary'

    def test_markdown_file_created(self, tmp_path):
        """Creates summary.md with markdown table."""
        scores = self._make_scores([
            ('repo-a', {'Theory': (None, 20, None, 'Good')}),
        ])

        build_summary_table(scores, tmp_path, scoring=False)

        md_path = tmp_path / 'summary.md'
        assert md_path.exists()
        content = md_path.read_text()
        assert '# Batch Feedback Summary' in content
        assert 'repo-a' in content
        assert 'Good' in content

    def test_auto_detect_scoring(self, tmp_path):
        """Auto-detects scoring mode from data when scoring=None."""
        # Data has numerical scores -> should produce percentage columns
        scores = self._make_scores([
            ('repo-a', {'Theory': (18, 20, 90.0, 'Exemplary')}),
        ])

        build_summary_table(scores, tmp_path, scoring=None)

        with open(tmp_path / 'summary.csv') as f:
            header = next(csv.reader(f))
        assert 'Theory (%)' in header

    def test_auto_detect_no_scoring(self, tmp_path):
        """Auto-detects rubric-level mode when no scores present."""
        scores = self._make_scores([
            ('repo-a', {'Theory': (None, 20, None, 'Good')}),
        ])

        build_summary_table(scores, tmp_path, scoring=None)

        with open(tmp_path / 'summary.csv') as f:
            header = next(csv.reader(f))
        assert 'Theory' in header
        assert 'Overall (%)' not in header

    def test_error_repo_in_table(self, tmp_path):
        """Repos with errors show error message in the row."""
        scores = [
            {'repo': 'broken-repo', 'criteria': {}, 'error': 'Timed out'},
            self._make_scores([
                ('good-repo', {'Theory': (None, 20, None, 'Good')}),
            ])[0],
        ]

        build_summary_table(scores, tmp_path, scoring=False)

        with open(tmp_path / 'summary.csv') as f:
            rows = list(csv.reader(f))
        # Find the broken repo row
        broken_row = [r for r in rows if r[0] == 'broken-repo'][0]
        assert 'Timed out' in broken_row[1]

    def test_empty_scores_no_crash(self, tmp_path):
        """Empty scores list doesn't crash."""
        build_summary_table([], tmp_path)
        assert not (tmp_path / 'summary.csv').exists()

    def test_mixed_scoring_fallback(self, tmp_path):
        """When scoring=True but a criterion has no score, falls back to assessment."""
        scores = self._make_scores([
            ('repo-a', {
                'Theory': (18, 20, 90.0, 'Exemplary'),
                'Code': (None, 40, None, 'Satisfactory'),
            }),
        ])

        build_summary_table(scores, tmp_path, scoring=True)

        with open(tmp_path / 'summary.csv') as f:
            rows = list(csv.reader(f))
        data_row = rows[1]
        assert data_row[1] == '90.0'           # Theory has percentage
        assert data_row[2] == 'Satisfactory'    # Code falls back to assessment
