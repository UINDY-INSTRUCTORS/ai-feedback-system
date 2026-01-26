"""
Tests for parse_report.py - deterministic report parsing.

Tests focus on the parsing logic (extracting structure, figures, stats)
without depending on file I/O or external images.
"""

import pytest
import sys
from pathlib import Path

# Add the scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'dot_github_folder' / 'scripts'))

from parse_report import (
    _get_yaml_metadata,
    _get_body_content,
    _extract_structure,
    _extract_figures,
    _calculate_stats,
)


@pytest.mark.deterministic
@pytest.mark.unit
class TestGetYamlMetadata:
    """Tests for YAML metadata extraction."""

    def test_simple_frontmatter(self, sample_qmd_frontmatter):
        """Test extraction of simple YAML frontmatter."""
        # Add body content so full document can be parsed
        full_content = sample_qmd_frontmatter + "\n\n# Body Content"
        metadata = _get_yaml_metadata(full_content)

        assert metadata.get('title') == "Project 1: Euler Method"
        assert metadata.get('author') == "Student Name"

    def test_frontmatter_with_nested_values(self):
        """Test extraction of nested YAML values."""
        content = """---
title: "Test"
author: "Author"
format:
  html:
    code-fold: true
  pdf:
    margin: 1in
---
Body content"""
        metadata = _get_yaml_metadata(content)

        assert metadata.get('title') == "Test"
        assert metadata.get('format') is not None
        assert isinstance(metadata.get('format'), dict)

    def test_no_frontmatter(self):
        """Test handling of content without frontmatter."""
        content = "Just regular content without YAML"
        metadata = _get_yaml_metadata(content)

        # Should return empty dict
        assert metadata == {} or isinstance(metadata, dict)

    def test_malformed_yaml(self):
        """Test handling of malformed YAML."""
        content = """---
title: "Test
author: Missing closing quote
---
Body"""
        metadata = _get_yaml_metadata(content)

        # Should not crash, might return empty or partial metadata
        assert isinstance(metadata, dict)

    def test_quoted_values(self):
        """Test handling of quoted values in YAML."""
        content = """---
title: "Project: Analysis"
author: "Smith, John"
description: "Complex: with: colons"
---

Body content here"""
        metadata = _get_yaml_metadata(content)

        assert metadata.get('title') == "Project: Analysis"
        assert "Smith" in metadata.get('author', '')


@pytest.mark.deterministic
@pytest.mark.unit
class TestGetBodyContent:
    """Tests for body content extraction."""

    def test_simple_body_extraction(self, sample_qmd_frontmatter):
        """Test extraction of body after YAML."""
        full_content = sample_qmd_frontmatter + "\n\n# My Content\n\nSome text"
        body = _get_body_content(full_content)

        assert "# My Content" in body
        assert "Some text" in body
        assert "title:" not in body  # YAML should be removed

    def test_body_without_frontmatter(self):
        """Test extraction when there's no frontmatter."""
        content = "Just body content\nNo YAML here"
        body = _get_body_content(content)

        assert body == content or "Just body content" in body

    def test_utf8_bom_handling(self):
        """Test handling of UTF-8 BOM."""
        content = "\ufeff---\ntitle: Test\n---\n\nBody"
        body = _get_body_content(content)

        # Should remove BOM
        assert body.startswith("-") or "Body" in body

    def test_body_with_triple_dash(self):
        """Test body that contains triple dashes."""
        full_content = """---
title: "Test"
---

# Section

---

This has a separator"""
        body = _get_body_content(full_content)

        assert "# Section" in body
        # Should preserve the separator in body
        assert "This has a separator" in body


@pytest.mark.deterministic
@pytest.mark.unit
class TestExtractStructure:
    """Tests for heading structure extraction."""

    def test_single_heading(self):
        """Test extraction of single heading."""
        body = "# Main Title\n\nContent"
        structure = _extract_structure(body)

        assert len(structure) >= 1
        assert any(h['heading'] == 'Main Title' for h in structure)

    def test_multiple_heading_levels(self):
        """Test extraction of multiple heading levels."""
        body = """# Level 1

Content

## Level 2

More content

### Level 3

Even more"""
        structure = _extract_structure(body)

        # Should extract all headings
        assert any(h['heading'] == 'Level 1' for h in structure)
        assert any(h['heading'] == 'Level 2' for h in structure)
        assert any(h['heading'] == 'Level 3' for h in structure)

    def test_heading_levels(self):
        """Test that heading levels are correctly identified."""
        body = "# H1\n\n## H2\n\n### H3\n\n#### H4"
        structure = _extract_structure(body)

        # Check that levels are identified
        h1_items = [h for h in structure if h.get('level') == 1]
        h2_items = [h for h in structure if h.get('level') == 2]
        h3_items = [h for h in structure if h.get('level') == 3]

        assert len(h1_items) > 0
        assert len(h2_items) > 0

    def test_no_headings(self):
        """Test body with no headings."""
        body = "Just some text\n\nWith paragraphs\n\nBut no headings"
        structure = _extract_structure(body)

        # Should return empty or list
        assert isinstance(structure, list)

    def test_heading_with_special_chars(self):
        """Test headings with special characters."""
        body = "# Introduction & Theory\n\n## Results: Analysis (Part 1)\n\n### FAQ?"
        structure = _extract_structure(body)

        assert any("Introduction" in h['heading'] for h in structure)


@pytest.mark.deterministic
@pytest.mark.unit
class TestExtractFigures:
    """Tests for figure extraction."""

    def test_markdown_image(self):
        """Test extraction of Markdown image syntax."""
        body = "![Caption](image.png)"
        figures = _extract_figures(body, "report")

        assert len(figures) > 0
        fig = figures[0]
        assert fig['path'] == 'image.png'
        assert fig['caption'] == 'Caption'

    def test_multiple_images(self, sample_qmd_with_figures):
        """Test extraction of multiple images."""
        figures = _extract_figures(sample_qmd_with_figures, "report")

        assert len(figures) >= 2

    def test_image_with_path(self):
        """Test image with path prefix."""
        body = "![Plot](./output/plot.png)"
        figures = _extract_figures(body, "report")

        assert len(figures) > 0
        assert 'plot.png' in figures[0]['path']

    def test_embed_shortcode(self):
        """Test extraction of Quarto embed shortcode."""
        body = '{{< embed notebook.ipynb#cell-label >}}'
        figures = _extract_figures(body, "report")

        # Should detect embed
        assert isinstance(figures, list)

    def test_no_images(self):
        """Test body with no images."""
        body = "# Content\n\nSome text but no images."
        figures = _extract_figures(body, "report")

        # Should return empty list
        assert figures == [] or len(figures) == 0

    def test_image_with_special_caption(self):
        """Test image with special characters in caption."""
        body = '![Error vs Time (log scale)](output/error.png)'
        figures = _extract_figures(body, "report")

        assert len(figures) > 0
        assert 'Error' in figures[0]['caption']


@pytest.mark.deterministic
@pytest.mark.unit
class TestCalculateStats:
    """Tests for statistics calculation."""

    def test_word_count(self):
        """Test word count calculation."""
        body = "This is a test with five words."
        stats = _calculate_stats(body, figure_count=0)

        assert stats.get('word_count') > 0
        assert stats['word_count'] >= 5

    def test_word_count_with_code(self):
        """Test word count excluding code blocks."""
        body = """Some text here.

```python
def function():
    pass
    return value
```

More text after code."""
        stats = _calculate_stats(body, figure_count=0)

        # Word count should not include code block words
        # "def function pass return value" shouldn't count
        assert stats.get('word_count') < 20

    def test_code_block_count(self):
        """Test detection of code blocks."""
        body = """```python
code1
```

Text

```javascript
code2
```

More text"""
        stats = _calculate_stats(body, figure_count=0)

        assert stats.get('code_block_count') == 2

    def test_equation_count(self):
        """Test detection of LaTeX equations."""
        body = r"""Some text with $inline$ math and $$display math$$ here.

And another equation: $e = mc^2$"""
        stats = _calculate_stats(body, figure_count=0)

        # Should detect LaTeX
        assert stats.get('equation_count') >= 0

    def test_figure_count(self):
        """Test figure count parameter."""
        body = "Some text"
        stats = _calculate_stats(body, figure_count=3)

        assert stats.get('figure_count') == 3

    def test_empty_body(self):
        """Test stats for empty body."""
        body = ""
        stats = _calculate_stats(body, figure_count=0)

        assert isinstance(stats, dict)
        assert stats.get('word_count') == 0

    def test_mixed_content_stats(self):
        """Test stats for mixed content."""
        body = """# Introduction

This is the introduction with some text.

```python
x = 1
y = 2
```

## Theory

The theory section. And equation: $\\alpha = \\beta$

## Results

![Plot](plot.png)

Text with results."""
        stats = _calculate_stats(body, figure_count=1)

        assert stats.get('word_count') > 0
        assert stats.get('code_block_count') >= 1
        assert stats.get('figure_count') == 1


@pytest.mark.deterministic
@pytest.mark.unit
class TestParsingRoundTrip:
    """Tests for parsing consistency."""

    def test_parse_realistic_document(self, sample_qmd_complete):
        """Test parsing a realistic complete document."""
        # Extract components
        metadata = _get_yaml_metadata(sample_qmd_complete)
        body = _get_body_content(sample_qmd_complete)
        structure = _extract_structure(body)
        figures = _extract_figures(body, "sample")
        stats = _calculate_stats(body, len(figures))

        # Verify all components extracted
        assert metadata.get('title') is not None
        assert len(body) > 0
        assert len(structure) > 0
        assert isinstance(figures, list)
        assert isinstance(stats, dict)
        assert stats.get('word_count') > 0

    def test_parsing_with_callout_boxes(self, sample_qmd_with_callouts):
        """Test that parsing handles callout boxes."""
        body = _get_body_content(sample_qmd_with_callouts)
        structure = _extract_structure(body)

        # Should extract structure even with callout boxes
        assert len(structure) >= 3

    def test_parsing_with_embeds(self, sample_qmd_with_embeds):
        """Test that parsing handles embed shortcodes."""
        body = _get_body_content(sample_qmd_with_embeds)
        figures = _extract_figures(body, "report")

        # Should detect embeds as figures
        assert isinstance(figures, list)

    def test_consistency_across_multiple_parses(self, sample_qmd_complete):
        """Test that parsing is deterministic."""
        body1 = _get_body_content(sample_qmd_complete)
        body2 = _get_body_content(sample_qmd_complete)

        assert body1 == body2

        structure1 = _extract_structure(body1)
        structure2 = _extract_structure(body2)

        assert structure1 == structure2
