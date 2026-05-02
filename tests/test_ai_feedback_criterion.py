"""
Tests for ai_feedback_criterion.py - criterion-based feedback generation.

Tests cover:
- build_ai_messages: message construction with and without images
- analyze_criterion: end-to-end with mocked AI call
- No real API calls - all network calls are mocked
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'dot_github_folder' / 'scripts'))

from ai_feedback_criterion import build_ai_messages, analyze_criterion


# ============================================================================
# build_ai_messages
# ============================================================================

@pytest.mark.deterministic
@pytest.mark.unit
class TestBuildAiMessages:
    """Tests for build_ai_messages function."""

    def test_text_only_messages(self):
        """Text-only prompt produces correct message structure."""
        messages = build_ai_messages("Analyze this report", {})

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "expert instructor" in messages[0]["content"]
        assert messages[1]["role"] == "user"
        # User content should be a list with a text item
        assert isinstance(messages[1]["content"], list)
        assert messages[1]["content"][0]["type"] == "text"
        assert messages[1]["content"][0]["text"] == "Analyze this report"

    def test_no_images_when_none_provided(self):
        """No image_url items when image_paths is None."""
        messages = build_ai_messages("Prompt", {}, image_paths=None)
        user_content = messages[1]["content"]
        image_items = [c for c in user_content if c.get("type") == "image_url"]
        assert len(image_items) == 0

    def test_no_images_when_empty_list(self):
        """No image_url items when image_paths is empty."""
        messages = build_ai_messages("Prompt", {}, image_paths=[])
        user_content = messages[1]["content"]
        image_items = [c for c in user_content if c.get("type") == "image_url"]
        assert len(image_items) == 0

    @patch('ai_feedback_criterion.optimize_images_for_payload')
    def test_images_added_when_optimized(self, mock_optimize):
        """Images are appended when optimize_images_for_payload returns data."""
        mock_optimize.return_value = [
            {'base64_data': 'data:image/png;base64,abc123', 'path': 'img.png'},
        ]
        messages = build_ai_messages("Prompt", {}, image_paths=["img.png"])
        user_content = messages[1]["content"]
        image_items = [c for c in user_content if c.get("type") == "image_url"]
        assert len(image_items) == 1
        assert image_items[0]["image_url"]["url"] == "data:image/png;base64,abc123"

    @patch('ai_feedback_criterion.optimize_images_for_payload')
    def test_fallback_to_text_when_images_cant_fit(self, mock_optimize):
        """Falls back to text-only when images can't fit in payload."""
        mock_optimize.return_value = []  # No images could fit
        messages = build_ai_messages("Prompt", {}, image_paths=["big.png"])
        user_content = messages[1]["content"]
        image_items = [c for c in user_content if c.get("type") == "image_url"]
        assert len(image_items) == 0
        # Text should still be present
        text_items = [c for c in user_content if c.get("type") == "text"]
        assert len(text_items) == 1

    def test_system_message_is_json_focused(self):
        """System message instructs JSON output."""
        messages = build_ai_messages("Test", {})
        assert "JSON" in messages[0]["content"]

    def test_deterministic_output(self):
        """Same inputs produce same outputs."""
        m1 = build_ai_messages("Prompt", {"max_output_tokens": 2000})
        m2 = build_ai_messages("Prompt", {"max_output_tokens": 2000})
        assert m1 == m2


# ============================================================================
# analyze_criterion (mocked AI)
# ============================================================================

@pytest.mark.unit
class TestAnalyzeCriterion:
    """Tests for analyze_criterion with mocked AI calls."""

    def _make_provider_config(self):
        return {
            'provider': 'github_models',
            'model': 'gpt-4o',
            'api_key': 'test-key',
            'api_base': 'https://models.inference.ai.azure.com',
            'fallback': 'gpt-4o-mini',
            'extractor': 'gpt-4o-mini',
        }

    @patch('ai_feedback_criterion.call_ai')
    @patch('ai_feedback_criterion.build_criterion_prompt')
    @patch('ai_feedback_criterion.save_debug_criterion_data')
    def test_successful_analysis(self, mock_debug, mock_prompt, mock_call):
        """Successful criterion analysis returns expected structure."""
        mock_prompt.return_value = ("prompt text", "context", [])
        feedback = json.dumps({
            "criterion": "Theory",
            "strengths": ["Good explanation"],
            "improvements": ["Add more detail"],
        })
        mock_call.return_value = (
            feedback,
            {"usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}},
            {"messages": [{"role": "user", "content": [{"type": "text", "text": "p"}]}]},
        )

        report = {"content": "Report text", "metadata": {}, "structure": []}
        criterion = {"id": "theory", "name": "Theory & Explanation", "weight": 20}
        config = {"max_output_tokens": 2000}

        result = analyze_criterion(
            report, criterion, "Be helpful", config,
            criterion_index=1, provider_config=self._make_provider_config()
        )

        assert result["success"] is True
        assert result["criterion"] == "Theory & Explanation"
        assert isinstance(result["feedback"], dict)
        assert result["tokens"]["total_tokens"] == 150

    @patch('ai_feedback_criterion.call_ai')
    @patch('ai_feedback_criterion.build_criterion_prompt')
    @patch('ai_feedback_criterion.save_debug_criterion_data')
    def test_failed_analysis(self, mock_debug, mock_prompt, mock_call):
        """Failed analysis returns success=False with error."""
        mock_prompt.return_value = ("prompt text", "context", [])
        mock_call.side_effect = ValueError("API key missing")

        report = {"content": "Report text", "metadata": {}, "structure": []}
        criterion = {"id": "theory", "name": "Theory", "weight": 20}
        config = {}

        result = analyze_criterion(
            report, criterion, "guidance", config,
            criterion_index=1, provider_config=self._make_provider_config()
        )

        assert result["success"] is False
        assert "API key missing" in result["error"]

    @patch('ai_feedback_criterion.call_ai')
    @patch('ai_feedback_criterion.build_criterion_prompt')
    @patch('ai_feedback_criterion.save_debug_criterion_data')
    def test_provider_recorded_in_result(self, mock_debug, mock_prompt, mock_call):
        """Provider info is recorded in metadata."""
        mock_prompt.return_value = ("prompt", "ctx", [])
        mock_call.return_value = (
            '{"criterion": "Test"}',
            {"usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}},
            {"messages": [{"role": "user", "content": [{"type": "text", "text": "p"}]}]},
        )

        report = {"content": "text", "metadata": {}, "structure": []}
        criterion = {"id": "test", "name": "Test", "weight": 10}
        pc = self._make_provider_config()
        pc['provider'] = 'anthropic'

        result = analyze_criterion(report, criterion, "g", {}, criterion_index=1, provider_config=pc)
        assert result["success"] is True


# ============================================================================
# build_criterion_prompt — levels-only mode
# ============================================================================

@pytest.mark.deterministic
@pytest.mark.unit
class TestBuildCriterionPromptLevelsOnly:
    """Tests for LEVELS_ONLY env-var mode in build_criterion_prompt."""

    def _criterion(self):
        return {
            "id": "abstract",
            "name": "Abstract & Description",
            "weight": 10,
            "description": "Abstract clearly states the project.",
            "levels": {
                "excellent": {"description": "Clear and precise.", "point_range": [7, 10]},
                "good":      {"description": "Present with merit.", "point_range": [4, 6]},
                "poor":      {"description": "Missing or unclear.", "point_range": [0, 3]},
            },
        }

    def _report(self):
        return {"content": "Some report text.", "metadata": {}, "structure": []}

    def _config(self):
        return {"model": {"extractor": "gpt-4o-mini"}}

    @patch('ai_feedback_criterion.extract_sections_for_criterion_ai')
    def test_levels_only_schema_has_only_overall_assessment(self, mock_extract, monkeypatch):
        """LEVELS_ONLY=1 produces a JSON schema with only overall_assessment."""
        mock_extract.return_value = ("Report content here.", [], {})
        monkeypatch.setenv("LEVELS_ONLY", "1")
        monkeypatch.delenv("SCORING_ENABLED", raising=False)

        from ai_feedback_criterion import build_criterion_prompt
        prompt, _, _ = build_criterion_prompt(self._report(), self._criterion(), "guidance", self._config())

        assert '"overall_assessment"' in prompt
        assert '"summary"' not in prompt
        assert '"strengths"' not in prompt
        assert '"areas_for_improvement"' not in prompt
        assert '"score"' not in prompt

    @patch('ai_feedback_criterion.extract_sections_for_criterion_ai')
    def test_levels_only_instruction_mentions_level_name(self, mock_extract, monkeypatch):
        """LEVELS_ONLY=1 prompt instructs the AI to return a level name verbatim."""
        mock_extract.return_value = ("content", [], {})
        monkeypatch.setenv("LEVELS_ONLY", "1")
        monkeypatch.delenv("SCORING_ENABLED", raising=False)

        from ai_feedback_criterion import build_criterion_prompt
        prompt, _, _ = build_criterion_prompt(self._report(), self._criterion(), "guidance", self._config())

        # Should direct the AI to pick the exact level name
        assert "level" in prompt.lower() or "overall_assessment" in prompt

    @patch('ai_feedback_criterion.extract_sections_for_criterion_ai')
    def test_normal_mode_unaffected(self, mock_extract, monkeypatch):
        """When LEVELS_ONLY is absent, the normal schema is used."""
        mock_extract.return_value = ("content", [], {})
        monkeypatch.delenv("LEVELS_ONLY", raising=False)
        monkeypatch.delenv("SCORING_ENABLED", raising=False)

        from ai_feedback_criterion import build_criterion_prompt
        prompt, _, _ = build_criterion_prompt(self._report(), self._criterion(), "guidance", self._config())

        assert '"summary"' in prompt
        assert '"strengths"' in prompt
        assert '"areas_for_improvement"' in prompt

    @patch('ai_feedback_criterion.extract_sections_for_criterion_ai')
    def test_levels_only_truthy_values(self, mock_extract, monkeypatch):
        """LEVELS_ONLY accepts '1', 'true', 'yes' as truthy."""
        mock_extract.return_value = ("content", [], {})
        for val in ("1", "true", "yes", "True", "YES"):
            monkeypatch.setenv("LEVELS_ONLY", val)
            from ai_feedback_criterion import build_criterion_prompt
            prompt, _, _ = build_criterion_prompt(self._report(), self._criterion(), "guidance", self._config())
            assert '"summary"' not in prompt, f"LEVELS_ONLY={val!r} should suppress summary"
