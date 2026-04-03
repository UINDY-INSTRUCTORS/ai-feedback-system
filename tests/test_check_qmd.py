"""
Tests for scripts/check_qmd.py - QMD syntax checker.

Tests cover:
- Embed reference checking
- Code fence + hr collision detection
- Unclosed code fences
- Unclosed callout divs
- Ambiguous hr detection
- Shortcode spacing
- Duplicate notebook tags
"""

import pytest
import sys
import json
from pathlib import Path

# Add the scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from check_qmd import (
    parse_embeds,
    check_embeds,
    check_fence_hr_collision,
    check_unclosed_fences,
    check_unclosed_divs,
    check_ambiguous_hr,
    check_shortcode_spacing,
    check_duplicate_notebook_tags,
    check_qmd,
)


# ============================================================================
# Helpers
# ============================================================================

def write_qmd(tmp_path, content, name="test.qmd"):
    """Write a .qmd file and return its Path."""
    p = tmp_path / name
    p.write_text(content)
    return p


def write_notebook(tmp_path, cells, name="notebook.ipynb"):
    """Write a minimal Jupyter notebook and return its Path."""
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {},
        "cells": cells,
    }
    p = tmp_path / name
    p.write_text(json.dumps(nb))
    return p


# ============================================================================
# parse_embeds
# ============================================================================

@pytest.mark.deterministic
@pytest.mark.unit
class TestParseEmbeds:
    """Tests for embed reference parsing."""

    def test_finds_simple_embed(self, tmp_path):
        qmd = write_qmd(tmp_path, "{{< embed notebook.ipynb#plot >}}")
        embeds = parse_embeds(qmd)
        assert len(embeds) == 1
        assert embeds[0]["notebook"] == "notebook.ipynb"
        assert embeds[0]["tag"] == "plot"
        assert embeds[0]["line_num"] == 1

    def test_finds_multiple_embeds(self, tmp_path):
        qmd = write_qmd(tmp_path, "{{< embed a.ipynb#x >}}\n\n{{< embed b.ipynb#y >}}")
        embeds = parse_embeds(qmd)
        assert len(embeds) == 2

    def test_no_embeds(self, tmp_path):
        qmd = write_qmd(tmp_path, "# Just a heading\n\nNo embeds here.")
        embeds = parse_embeds(qmd)
        assert len(embeds) == 0

    def test_embed_with_extra_attributes(self, tmp_path):
        qmd = write_qmd(tmp_path, '{{< embed nb.ipynb#cell echo=true >}}')
        embeds = parse_embeds(qmd)
        assert len(embeds) == 1
        assert embeds[0]["tag"] == "cell"


# ============================================================================
# check_embeds
# ============================================================================

@pytest.mark.unit
class TestCheckEmbeds:
    """Tests for embed reference validation."""

    def test_valid_embed(self, tmp_path):
        write_notebook(tmp_path, [
            {"cell_type": "code", "source": ["x = 1"], "metadata": {"tags": ["plot"]}, "outputs": []},
        ])
        qmd = write_qmd(tmp_path, "{{< embed notebook.ipynb#plot >}}")
        issues = check_embeds(qmd)
        assert len(issues) == 0

    def test_missing_tag(self, tmp_path):
        write_notebook(tmp_path, [
            {"cell_type": "code", "source": ["x = 1"], "metadata": {"tags": ["other"]}, "outputs": []},
        ])
        qmd = write_qmd(tmp_path, "{{< embed notebook.ipynb#missing >}}")
        issues = check_embeds(qmd)
        assert len(issues) == 1
        assert "missing" in issues[0]["issue"]

    def test_missing_notebook(self, tmp_path):
        qmd = write_qmd(tmp_path, "{{< embed nonexistent.ipynb#tag >}}")
        issues = check_embeds(qmd)
        assert len(issues) == 1
        assert "not found" in issues[0]["issue"]

    def test_case_mismatch_hint(self, tmp_path):
        write_notebook(tmp_path, [
            {"cell_type": "code", "source": ["x = 1"], "metadata": {"tags": ["Plot"]}, "outputs": []},
        ])
        qmd = write_qmd(tmp_path, "{{< embed notebook.ipynb#plot >}}")
        issues = check_embeds(qmd)
        assert len(issues) == 1
        assert "case mismatch" in issues[0]["issue"]

    def test_label_in_code_comment(self, tmp_path):
        write_notebook(tmp_path, [
            {"cell_type": "code", "source": ["#| label: my-plot\nimport matplotlib"], "metadata": {}, "outputs": []},
        ])
        qmd = write_qmd(tmp_path, "{{< embed notebook.ipynb#my-plot >}}")
        issues = check_embeds(qmd)
        assert len(issues) == 0


# ============================================================================
# check_fence_hr_collision
# ============================================================================

@pytest.mark.deterministic
@pytest.mark.unit
class TestCheckFenceHrCollision:
    """Tests for code fence + hr collision detection."""

    def test_detects_collision(self, tmp_path):
        qmd = write_qmd(tmp_path, "```python\nx = 1\n```\n---\n")
        issues = check_fence_hr_collision(qmd)
        assert len(issues) == 1

    def test_no_collision_with_blank_line(self, tmp_path):
        qmd = write_qmd(tmp_path, "```python\nx = 1\n```\n\n---\n")
        issues = check_fence_hr_collision(qmd)
        assert len(issues) == 0

    def test_no_collision_no_hr(self, tmp_path):
        qmd = write_qmd(tmp_path, "```python\nx = 1\n```\n\nMore text\n")
        issues = check_fence_hr_collision(qmd)
        assert len(issues) == 0


# ============================================================================
# check_unclosed_fences
# ============================================================================

@pytest.mark.deterministic
@pytest.mark.unit
class TestCheckUnclosedFences:
    """Tests for unclosed code fence detection."""

    def test_detects_unclosed_fence(self, tmp_path):
        qmd = write_qmd(tmp_path, "```python\nx = 1\n# no closing fence\n")
        issues = check_unclosed_fences(qmd)
        assert len(issues) == 1
        assert "never closed" in issues[0]["issue"]

    def test_closed_fence_ok(self, tmp_path):
        qmd = write_qmd(tmp_path, "```python\nx = 1\n```\n")
        issues = check_unclosed_fences(qmd)
        assert len(issues) == 0

    def test_multiple_fences_ok(self, tmp_path):
        qmd = write_qmd(tmp_path, "```python\nx = 1\n```\n\n```r\ny <- 2\n```\n")
        issues = check_unclosed_fences(qmd)
        assert len(issues) == 0

    def test_tilde_fence(self, tmp_path):
        qmd = write_qmd(tmp_path, "~~~\ncode\n~~~\n")
        issues = check_unclosed_fences(qmd)
        assert len(issues) == 0

    def test_unclosed_tilde_fence(self, tmp_path):
        qmd = write_qmd(tmp_path, "~~~\ncode\n")
        issues = check_unclosed_fences(qmd)
        assert len(issues) == 1


# ============================================================================
# check_unclosed_divs
# ============================================================================

@pytest.mark.deterministic
@pytest.mark.unit
class TestCheckUnclosedDivs:
    """Tests for unclosed callout div detection."""

    def test_detects_unclosed_div(self, tmp_path):
        qmd = write_qmd(tmp_path, "::: {.callout-note}\nContent\n")
        issues = check_unclosed_divs(qmd)
        assert len(issues) == 1
        assert "never closed" in issues[0]["issue"]

    def test_closed_div_ok(self, tmp_path):
        qmd = write_qmd(tmp_path, "::: {.callout-note}\nContent\n:::\n")
        issues = check_unclosed_divs(qmd)
        assert len(issues) == 0

    def test_nested_divs(self, tmp_path):
        qmd = write_qmd(tmp_path, "::: {.panel}\n::: {.callout-note}\nInner\n:::\n:::\n")
        issues = check_unclosed_divs(qmd)
        assert len(issues) == 0

    def test_extra_closing_div(self, tmp_path):
        qmd = write_qmd(tmp_path, ":::\n")
        issues = check_unclosed_divs(qmd)
        assert len(issues) == 1
        assert "without a matching" in issues[0]["issue"]


# ============================================================================
# check_ambiguous_hr
# ============================================================================

@pytest.mark.deterministic
@pytest.mark.unit
class TestCheckAmbiguousHr:
    """Tests for ambiguous horizontal rule detection."""

    def test_detects_hr_without_blank_line(self, tmp_path):
        qmd = write_qmd(tmp_path, "---\ntitle: Test\n---\n\nSome text\n---\n")
        issues = check_ambiguous_hr(qmd)
        assert len(issues) == 1

    def test_ok_with_blank_line_before(self, tmp_path):
        qmd = write_qmd(tmp_path, "---\ntitle: Test\n---\n\nSome text\n\n---\n")
        issues = check_ambiguous_hr(qmd)
        assert len(issues) == 0

    def test_ignores_front_matter(self, tmp_path):
        qmd = write_qmd(tmp_path, "---\ntitle: Test\n---\n\nContent\n")
        issues = check_ambiguous_hr(qmd)
        assert len(issues) == 0

    def test_ignores_inside_code_fence(self, tmp_path):
        qmd = write_qmd(tmp_path, "---\ntitle: X\n---\n\n```\nfoo\n---\n```\n")
        issues = check_ambiguous_hr(qmd)
        assert len(issues) == 0


# ============================================================================
# check_shortcode_spacing
# ============================================================================

@pytest.mark.deterministic
@pytest.mark.unit
class TestCheckShortcodeSpacing:
    """Tests for shortcode blank-line spacing."""

    def test_detects_missing_blank_before(self, tmp_path):
        qmd = write_qmd(tmp_path, "---\nt: x\n---\n\nSome text\n{{< embed nb.ipynb#cell >}}\n")
        issues = check_shortcode_spacing(qmd)
        assert any("before" in i["issue"] for i in issues)

    def test_detects_missing_blank_after(self, tmp_path):
        qmd = write_qmd(tmp_path, "---\nt: x\n---\n\n{{< embed nb.ipynb#cell >}}\nMore text\n")
        issues = check_shortcode_spacing(qmd)
        assert any("after" in i["issue"] for i in issues)

    def test_ok_with_blank_lines(self, tmp_path):
        qmd = write_qmd(tmp_path, "---\nt: x\n---\n\nText\n\n{{< embed nb.ipynb#cell >}}\n\nMore\n")
        issues = check_shortcode_spacing(qmd)
        assert len(issues) == 0

    def test_ignores_inline_shortcodes(self, tmp_path):
        """Inline shortcodes (not alone on a line) should not be flagged."""
        qmd = write_qmd(tmp_path, "---\nt: x\n---\n\nSee {{< embed nb.ipynb#cell >}} here\n")
        issues = check_shortcode_spacing(qmd)
        assert len(issues) == 0


# ============================================================================
# check_duplicate_notebook_tags
# ============================================================================

@pytest.mark.unit
class TestCheckDuplicateNotebookTags:
    """Tests for duplicate notebook tag detection."""

    def test_detects_duplicate_tags(self, tmp_path):
        write_notebook(tmp_path, [
            {"cell_type": "code", "source": ["x = 1"], "metadata": {"tags": ["plot"]}, "outputs": []},
            {"cell_type": "code", "source": ["y = 2"], "metadata": {"tags": ["plot"]}, "outputs": []},
        ])
        qmd = write_qmd(tmp_path, "{{< embed notebook.ipynb#plot >}}")
        issues = check_duplicate_notebook_tags(qmd)
        assert len(issues) >= 1
        assert "Duplicate" in issues[0]["issue"]

    def test_no_duplicates(self, tmp_path):
        write_notebook(tmp_path, [
            {"cell_type": "code", "source": ["x = 1"], "metadata": {"tags": ["plot1"]}, "outputs": []},
            {"cell_type": "code", "source": ["y = 2"], "metadata": {"tags": ["plot2"]}, "outputs": []},
        ])
        qmd = write_qmd(tmp_path, "{{< embed notebook.ipynb#plot1 >}}")
        issues = check_duplicate_notebook_tags(qmd)
        assert len(issues) == 0


# ============================================================================
# check_qmd (integration)
# ============================================================================

@pytest.mark.unit
class TestCheckQmd:
    """Integration test for running all checks together."""

    def test_clean_file_no_issues(self, tmp_path):
        qmd = write_qmd(tmp_path, "---\ntitle: Test\n---\n\n# Heading\n\nContent\n")
        issues = check_qmd(qmd)
        assert len(issues) == 0

    def test_multiple_issues_detected(self, tmp_path):
        content = """::: {.callout-note}
Unclosed div

```python
unclosed fence
"""
        qmd = write_qmd(tmp_path, content)
        issues = check_qmd(qmd)
        # Should find at least unclosed fence and unclosed div
        assert len(issues) >= 2
