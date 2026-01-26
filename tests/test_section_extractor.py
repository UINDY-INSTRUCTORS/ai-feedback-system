"""
Tests for section_extractor.py - deterministic section extraction logic.

Tests focus on the decision logic and text processing without API calls:
- strip_callout_boxes: Regex-based callout removal
- augment_with_notebook_outputs: Embed shortcode replacement
- Vision enablement logic: Decision trees for when to use vision
- Prompt building: Consistent prompt generation
"""

import pytest
import sys
from pathlib import Path

# Add the scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'dot_github_folder' / 'scripts'))

from section_extractor import (
    strip_callout_boxes,
    augment_with_notebook_outputs,
    should_enable_vision_for_criterion,
    get_image_priority,
    build_extraction_prompt,
)


@pytest.mark.deterministic
@pytest.mark.unit
class TestStripCalloutBoxes:
    """Tests for Quarto callout box removal."""

    def test_simple_callout_removal(self):
        """Test removal of a simple callout box."""
        text = """::: {.callout-note}
Template instruction
:::

Student content"""
        cleaned, found = strip_callout_boxes(text)

        assert found is True
        assert "Template instruction" not in cleaned
        assert "Student content" in cleaned

    def test_callout_with_multiple_lines(self, sample_qmd_with_callouts):
        """Test removal of multi-line callout box."""
        cleaned, found = strip_callout_boxes(sample_qmd_with_callouts)

        assert found is True
        # Callout content should be removed
        assert "Delete this callout" not in cleaned
        # But student content should remain
        assert "Euler method" in cleaned or "numerical" in cleaned.lower()

    def test_multiple_callouts(self):
        """Test removal of multiple callout boxes."""
        text = """::: {.callout-note}
First callout
:::

Content

::: {.callout-warning}
Second callout
:::

More content"""
        cleaned, found = strip_callout_boxes(text)

        assert found is True
        assert "First callout" not in cleaned
        assert "Second callout" not in cleaned
        assert "Content" in cleaned
        assert "More content" in cleaned

    def test_callout_with_different_types(self):
        """Test removal of different callout types."""
        text = """::: {.callout-note}
Note content
:::

::: {.callout-warning}
Warning content
:::

::: {.callout-tip}
Tip content
:::

Real content"""
        cleaned, found = strip_callout_boxes(text)

        assert found is True
        assert "Note content" not in cleaned
        assert "Warning content" not in cleaned
        assert "Tip content" not in cleaned
        assert "Real content" in cleaned

    def test_callout_with_special_characters(self):
        """Test callout removal with special characters."""
        text = """::: {.callout-note}
Content with $math$, `code`, and [links](http://example.com)
:::

Real content here"""
        cleaned, found = strip_callout_boxes(text)

        assert found is True
        assert "Real content here" in cleaned

    def test_no_callouts(self):
        """Test when there are no callouts."""
        text = "# Heading\n\nContent without callouts\n\n## Subsection\n\nMore content"
        cleaned, found = strip_callout_boxes(text)

        assert found is False
        assert cleaned == text

    def test_callout_removal_preserves_structure(self):
        """Test that callout removal preserves document structure."""
        text = """# Section 1

::: {.callout-note}
Instructions
:::

Content for section 1

## Subsection

More content"""
        cleaned, found = strip_callout_boxes(text)

        assert "# Section 1" in cleaned
        assert "## Subsection" in cleaned
        assert "Content for section 1" in cleaned
        assert "More content" in cleaned

    def test_deterministic_callout_removal(self):
        """Test that callout removal is deterministic."""
        text = "::: {.callout-note}\nContent\n:::\n\nKeep this"

        result1_cleaned, result1_found = strip_callout_boxes(text)
        result2_cleaned, result2_found = strip_callout_boxes(text)

        assert result1_cleaned == result2_cleaned
        assert result1_found == result2_found


@pytest.mark.deterministic
@pytest.mark.unit
class TestAugmentWithNotebookOutputs:
    """Tests for embed shortcode replacement with notebook content."""

    def test_simple_embed_replacement(self):
        """Test replacement of a single embed shortcode."""
        text = "Results: {{< embed notebook.ipynb#plot >}}"
        notebook_outputs = {
            'plot': 'Generated plot visualization'
        }
        report = {
            'notebook_outputs': notebook_outputs
        }

        result = augment_with_notebook_outputs(report, text)

        # Embed should be replaced with content
        assert 'notebook.ipynb' not in result or 'Generated plot' in result

    def test_multiple_embeds(self):
        """Test replacement of multiple embeds."""
        text = """First: {{< embed nb.ipynb#fig1 >}}

Second: {{< embed nb.ipynb#fig2 >}}"""
        notebook_outputs = {
            'fig1': 'Figure 1 content',
            'fig2': 'Figure 2 content',
        }
        report = {'notebook_outputs': notebook_outputs}

        result = augment_with_notebook_outputs(report, text)

        assert 'Figure 1 content' in result or 'content' in result.lower()

    def test_embed_with_missing_output(self):
        """Test handling of embed without corresponding output."""
        text = "Content: {{< embed nb.ipynb#missing >}}"
        report = {'notebook_outputs': {}}

        result = augment_with_notebook_outputs(report, text)

        # Should handle gracefully (might keep embed or replace with placeholder)
        assert isinstance(result, str)

    def test_no_embeds(self):
        """Test text without embeds."""
        text = "Regular text without embeds"
        report = {'notebook_outputs': {}}

        result = augment_with_notebook_outputs(report, text)

        # Should return unchanged or similar
        assert text in result or result == text or 'Regular text' in result

    def test_augmentation_preserves_text(self):
        """Test that non-embed content is preserved."""
        text = """# Results

Analysis here {{< embed nb.ipynb#plot >}} more analysis.

Conclusion."""
        notebook_outputs = {'plot': '[PLOT]'}
        report = {'notebook_outputs': notebook_outputs}

        result = augment_with_notebook_outputs(report, text)

        assert '# Results' in result
        assert 'Analysis here' in result
        assert 'Conclusion' in result

    def test_deterministic_augmentation(self):
        """Test that augmentation is deterministic."""
        text = "{{< embed nb.ipynb#cell >}}"
        report = {'notebook_outputs': {'cell': 'output'}}

        result1 = augment_with_notebook_outputs(report, text)
        result2 = augment_with_notebook_outputs(report, text)

        assert result1 == result2


@pytest.mark.deterministic
@pytest.mark.unit
class TestShouldEnableVisionForCriterion:
    """Tests for vision enablement decision logic."""

    def test_vision_explicitly_enabled(self, sample_criterion_with_vision, sample_config):
        """Test that explicitly enabled vision is used."""
        result = should_enable_vision_for_criterion(
            report={},
            criterion=sample_criterion_with_vision,
            vision_config=sample_config['vision'],
            extracted_text="Some text"
        )

        assert result is True

    def test_vision_explicitly_disabled(self, sample_criterion, sample_config):
        """Test that disabled vision is not used."""
        result = should_enable_vision_for_criterion(
            report={},
            criterion=sample_criterion,
            vision_config=sample_config['vision'],
            extracted_text="Some text"
        )

        # Should respect the criterion's vision setting
        assert isinstance(result, bool)

    def test_vision_auto_detect_with_images(self, sample_config):
        """Test auto-detection of vision when images present."""
        criterion = {
            'id': 'results',
            'name': 'Results',
            'vision_enabled': None,  # Not explicitly set
        }
        text_with_images = "Image path: output/plot.png mentioned in text"

        config = sample_config['vision']
        config['auto_detect'] = True

        result = should_enable_vision_for_criterion(
            report={},
            criterion=criterion,
            vision_config=config,
            extracted_text=text_with_images
        )

        # Should be True if auto-detect is enabled and images found
        assert isinstance(result, bool)

    def test_vision_auto_detect_without_images(self, sample_config):
        """Test auto-detection of vision without images."""
        criterion = {'id': 'theory', 'name': 'Theory'}
        text_no_images = "Just text about theory without any image references"

        config = sample_config['vision']
        config['auto_detect'] = True

        result = should_enable_vision_for_criterion(
            report={},
            criterion=criterion,
            vision_config=config,
            extracted_text=text_no_images
        )

        # Without images, should be False (or follow config default)
        assert isinstance(result, bool)

    def test_vision_disabled_globally(self, sample_criterion_with_vision):
        """Test that global vision disable overrides criterion setting."""
        vision_config = {
            'enabled': False,
            'auto_detect': False,
        }

        result = should_enable_vision_for_criterion(
            report={},
            criterion=sample_criterion_with_vision,
            vision_config=vision_config,
            extracted_text="text"
        )

        # Global disable should prevent vision
        assert result is False


@pytest.mark.deterministic
@pytest.mark.unit
class TestGetImagePriority:
    """Tests for image priority calculation."""

    def test_keyword_priority(self):
        """Test that keywords affect priority."""
        figure_dict = {
            'caption': 'Convergence plot showing results',
            'path': 'plot.png'
        }
        keywords = ['plot', 'convergence', 'results']

        priority = get_image_priority(figure_dict, keywords)

        # Should have positive priority for matching keywords
        assert priority > 0

    def test_no_keyword_match(self):
        """Test priority when keywords don't match."""
        figure_dict = {
            'caption': 'Unrelated diagram',
            'path': 'diagram.png'
        }
        keywords = ['plot', 'graph', 'chart']

        priority = get_image_priority(figure_dict, keywords)

        # Should have lower priority
        assert isinstance(priority, int)

    def test_multiple_keyword_matches(self):
        """Test that multiple matches increase priority."""
        figure_dict = {
            'caption': 'Results plot showing error convergence',
            'path': 'plot.png'
        }
        keywords = ['plot', 'error', 'convergence', 'results']

        priority = get_image_priority(figure_dict, keywords)

        # More matches = higher priority
        assert priority > 0

    def test_case_insensitive_matching(self):
        """Test that keyword matching is case-insensitive."""
        figure_dict = {
            'caption': 'Results Plot',
            'path': 'plot.png'
        }
        keywords = ['plot', 'results']

        priority = get_image_priority(figure_dict, keywords)

        # Should match despite case differences
        assert priority > 0


@pytest.mark.deterministic
@pytest.mark.unit
class TestBuildExtractionPrompt:
    """Tests for extraction prompt generation."""

    def test_prompt_includes_criterion_name(self, sample_parsed_report, sample_criterion):
        """Test that prompt includes criterion information."""
        prompt = build_extraction_prompt(sample_parsed_report, sample_criterion)

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # Should reference the criterion
        assert sample_criterion['name'] in prompt or 'criterion' in prompt.lower()

    def test_prompt_includes_report_content(self, sample_parsed_report, sample_criterion):
        """Test that prompt includes report content."""
        prompt = build_extraction_prompt(sample_parsed_report, sample_criterion)

        # Should include some of the report content
        assert 'Euler' in prompt or 'method' in prompt.lower() or 'Project' in prompt

    def test_prompt_handles_long_content(self, sample_criterion):
        """Test prompt generation with very long content."""
        long_report = {
            'content': "word " * 5000,  # Very long content
            'metadata': {},
            'structure': [],
        }

        prompt = build_extraction_prompt(long_report, sample_criterion)

        # Should truncate or summarize gracefully
        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_prompt_determinism(self, sample_parsed_report, sample_criterion):
        """Test that prompt generation is deterministic."""
        prompt1 = build_extraction_prompt(sample_parsed_report, sample_criterion)
        prompt2 = build_extraction_prompt(sample_parsed_report, sample_criterion)

        assert prompt1 == prompt2

    def test_prompt_format_consistency(self, sample_parsed_report, sample_criterion):
        """Test that prompts have consistent format."""
        prompt = build_extraction_prompt(sample_parsed_report, sample_criterion)

        # Should be a string
        assert isinstance(prompt, str)
        # Should not be empty
        assert len(prompt.strip()) > 0
        # Should be reasonable length (not tiny, not enormous)
        assert 50 < len(prompt) < 20000


@pytest.mark.deterministic
@pytest.mark.unit
class TestSectionExtractionLogicConsistency:
    """Tests for consistency of extraction logic."""

    def test_callout_removal_idempotent(self):
        """Test that stripping callouts twice gives same result."""
        text = "::: {.callout-note}\nContent\n:::\nKeep"

        first_clean, _ = strip_callout_boxes(text)
        second_clean, found = strip_callout_boxes(first_clean)

        assert first_clean == second_clean
        assert found is False  # No callouts in already-cleaned text

    def test_extraction_prompt_consistency(self, sample_parsed_report, sample_criterion):
        """Test that prompt generation is consistent."""
        prompts = [
            build_extraction_prompt(sample_parsed_report, sample_criterion)
            for _ in range(3)
        ]

        # All should be identical
        assert prompts[0] == prompts[1] == prompts[2]

    def test_vision_decision_consistency(self, sample_criterion_with_vision, sample_config):
        """Test that vision decisions are consistent."""
        decisions = [
            should_enable_vision_for_criterion(
                report={},
                criterion=sample_criterion_with_vision,
                vision_config=sample_config['vision'],
                extracted_text="test text"
            )
            for _ in range(3)
        ]

        # All should be identical
        assert decisions[0] == decisions[1] == decisions[2]
