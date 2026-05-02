"""
Tests for levels-only mode threading through run-local-feedback.py
and batch-feedback.py.
"""

import pytest
import sys
import inspect
from pathlib import Path
from importlib import import_module

sys.path.insert(0, str(Path(__file__).parent.parent))

runner = import_module('run-local-feedback')
run_feedback_pipeline = runner.run_feedback_pipeline


# ============================================================================
# Task 2: run_feedback_pipeline accepts levels_only kwarg
# ============================================================================

class TestRunFeedbackPipelineLevelsOnly:

    def test_levels_only_param_exists(self):
        """run_feedback_pipeline has a levels_only keyword argument."""
        sig = inspect.signature(run_feedback_pipeline)
        assert 'levels_only' in sig.parameters

    def test_levels_only_default_is_false(self):
        """levels_only defaults to False."""
        sig = inspect.signature(run_feedback_pipeline)
        assert sig.parameters['levels_only'].default is False

    def test_levels_only_accepted_without_type_error(self, tmp_path):
        """Passing levels_only=True does not raise TypeError."""
        # Repo doesn't exist → validate_repo returns False → early exit.
        # We just need the kwarg to be accepted without TypeError.
        result = run_feedback_pipeline(tmp_path / 'nonexistent', levels_only=True)
        assert isinstance(result, dict)


# ============================================================================
# Task 3: batch-feedback.py exposes --levels-only flag
# ============================================================================

class TestBatchFeedbackLevelsOnlyFlag:

    def _parse_batch(self, args):
        """Parse batch-feedback.py CLI args and return namespace."""
        import importlib.util, argparse
        spec = importlib.util.spec_from_file_location(
            'batch_feedback',
            Path(__file__).parent.parent / 'batch-feedback.py'
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # Re-create the parser using the module's main function source is complex;
        # instead just confirm the attribute exists after import.
        return mod

    def test_batch_module_has_levels_only_support(self):
        """batch-feedback.py imports and run_feedback_pipeline call includes levels_only."""
        batch_path = Path(__file__).parent.parent / 'batch-feedback.py'
        source = batch_path.read_text()
        assert 'levels_only' in source, "batch-feedback.py must reference levels_only"
        assert '--levels-only' in source, "batch-feedback.py must expose --levels-only flag"


# ============================================================================
# Task 4: batch-feedback.py --pdf-dir / --submissions-dir flags
# ============================================================================

class TestBatchFeedbackPdfDiscovery:

    def test_batch_module_has_pdf_dir_flag(self):
        """batch-feedback.py exposes --pdf-dir and --submissions-dir flags."""
        batch_path = Path(__file__).parent.parent / 'batch-feedback.py'
        source = batch_path.read_text()
        assert '--pdf-dir' in source
        assert '--submissions-dir' in source

    def test_load_repo_paths_with_pdf_discovery(self, tmp_path):
        """load_repo_paths delegates to find_repos_from_pdf_dir when pdf_dir supplied."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'batch_feedback_mod',
            Path(__file__).parent.parent / 'batch-feedback.py'
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Create fake submissions dir with one matching repo
        submissions = tmp_path / 'submissions'
        submissions.mkdir()
        repo = submissions / 'p3-amplification-alice'
        repo.mkdir()
        (repo / 'index.qmd').write_text('---\ntitle: test\n---\n')

        # Create fake pdf dir with matching PDF
        pdf_dir = tmp_path / 'ph230-p3-may1-regrade'
        pdf_dir.mkdir()
        (pdf_dir / 'alice-ph230-p3-may1-regrade-20260101.pdf').write_text('')

        repos = mod.load_repo_paths(
            repos_file=None, repos_dir=None,
            pdf_dir=str(pdf_dir), submissions_dir=str(submissions)
        )
        assert len(repos) == 1
        assert repos[0] == repo
