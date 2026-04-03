"""
Tests for create_issue.py - feedback formatting and output.

Tests cover:
- save_feedback_to_file: file creation and content
- Output format routing (github_issue vs flat_file)
- No real GitHub API calls
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch

# Add the scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'dot_github_folder' / 'scripts'))

from create_issue import save_feedback_to_file


# ============================================================================
# save_feedback_to_file
# ============================================================================

@pytest.mark.unit
class TestSaveFeedbackToFile:
    """Tests for the save_feedback_to_file function."""

    def test_creates_file(self, tmp_path):
        """Creates a feedback file at the specified path."""
        output = tmp_path / "feedback.md"
        save_feedback_to_file("Body text", "\n---\nFooter", {}, str(output))

        assert output.exists()
        content = output.read_text()
        assert "Body text" in content
        assert "Footer" in content

    def test_includes_header(self, tmp_path):
        """Output includes the AI Report Feedback header."""
        output = tmp_path / "feedback.md"
        save_feedback_to_file("Body", "Footer", {}, str(output))

        content = output.read_text()
        assert "AI Report Feedback" in content

    def test_includes_model_from_config(self, tmp_path):
        """Header includes the model name from config."""
        output = tmp_path / "fb.md"
        config = {'model': {'primary': 'claude-sonnet'}}
        save_feedback_to_file("Body", "Footer", config, str(output))

        content = output.read_text()
        assert "claude-sonnet" in content

    def test_creates_parent_directories(self, tmp_path):
        """Creates parent directories if they don't exist."""
        output = tmp_path / "deep" / "nested" / "feedback.md"
        save_feedback_to_file("Body", "Footer", {}, str(output))

        assert output.exists()

    def test_default_model_fallback(self, tmp_path):
        """Falls back to gpt-4o when model not in config."""
        output = tmp_path / "fb.md"
        save_feedback_to_file("Body", "Footer", {}, str(output))

        content = output.read_text()
        assert "gpt-4o" in content

    def test_returns_output_path(self, tmp_path):
        """Returns the path where feedback was saved."""
        output = tmp_path / "fb.md"
        result = save_feedback_to_file("Body", "Footer", {}, str(output))
        assert result == str(output)

    def test_tag_name_from_env(self, tmp_path):
        """Uses TAG_NAME from environment in header."""
        output = tmp_path / "fb.md"
        with patch.dict(os.environ, {'TAG_NAME': 'v2.0-feedback'}):
            save_feedback_to_file("Body", "Footer", {}, str(output))

        content = output.read_text()
        assert "v2.0-feedback" in content
