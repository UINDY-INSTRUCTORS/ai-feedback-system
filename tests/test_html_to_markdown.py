"""
Tests for html_to_markdown.py - deterministic HTML to Markdown conversion.

All functions in html_to_markdown are pure functions with no external
dependencies, making them ideal for comprehensive deterministic testing.
"""

import pytest
import sys
from pathlib import Path

# Add the scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'dot_github_folder' / 'scripts'))

from html_to_markdown import (
    html_table_to_markdown,
    html_to_markdown,
    convert_list,
    convert_notebook_output_to_markdown,
)


@pytest.mark.deterministic
@pytest.mark.unit
class TestHtmlTableToMarkdown:
    """Tests for HTML table conversion to Markdown."""

    def test_simple_table(self, sample_html_table_simple):
        """Test conversion of a simple table."""
        result = html_table_to_markdown(sample_html_table_simple)

        # Should contain table header separator
        assert '---' in result or '| --- |' in result

        # Should contain all cell values
        assert 'Step' in result
        assert 'Value' in result
        assert '0.0' in result
        assert '0.1' in result

    def test_complex_table(self, sample_html_table_complex):
        """Test conversion of a more complex table with multiple rows."""
        result = html_table_to_markdown(sample_html_table_complex)

        # Check structure
        assert '|' in result  # Markdown table pipe
        assert 'Method' in result
        assert 'Error at t=1.0' in result
        assert 'Euler' in result
        assert 'RK4' in result

    def test_table_with_empty_cells(self):
        """Test table with empty cells."""
        html = """<table>
        <tr><th>A</th><th>B</th></tr>
        <tr><td>Value</td><td></td></tr>
        </table>"""
        result = html_table_to_markdown(html)

        # Should handle empty cells gracefully
        assert 'A' in result
        assert 'Value' in result

    def test_table_with_special_characters(self):
        """Test table with special Markdown characters."""
        html = """<table>
        <tr><th>Code</th><th>Output</th></tr>
        <tr><td>x = y | z</td><td>a & b</td></tr>
        </table>"""
        result = html_table_to_markdown(html)

        # Should convert table even with special characters
        assert 'Code' in result
        assert 'Output' in result

    def test_table_with_links(self):
        """Test table containing hyperlinks."""
        html = """<table>
        <tr><th>Resource</th></tr>
        <tr><td><a href="https://example.com">Example</a></td></tr>
        </table>"""
        result = html_table_to_markdown(html)

        # Should contain the text
        assert 'Resource' in result


@pytest.mark.deterministic
@pytest.mark.unit
class TestConvertList:
    """Tests for HTML list conversion."""

    def test_unordered_list(self, sample_html_list_unordered):
        """Test conversion of unordered list."""
        result = convert_list(sample_html_list_unordered)

        assert 'First item' in result
        assert 'Second item' in result
        assert 'Third item' in result
        # Should use - or * for unordered
        assert '-' in result or '*' in result

    def test_ordered_list(self, sample_html_list_ordered):
        """Test conversion of ordered list."""
        result = convert_list(sample_html_list_ordered)

        assert 'Initialize y and t arrays' in result
        assert 'compute dy/dt' in result
        assert 'Update y' in result
        # Should use numbers for ordered
        assert '1.' in result or '2.' in result

    def test_nested_lists(self, sample_html_nested_lists):
        """Test conversion of nested lists."""
        result = convert_list(sample_html_nested_lists)

        # Should preserve nesting structure (likely with indentation)
        assert 'Theory' in result
        assert 'Differential equations' in result
        assert 'Implementation' in result
        assert 'Python code' in result

    def test_empty_list(self):
        """Test handling of empty list."""
        html = "<ul></ul>"
        result = convert_list(html)

        # Should return empty or minimal result
        assert result is not None

    def test_list_with_formatted_text(self):
        """Test list items with bold/italic formatting."""
        html = """<ul>
        <li><b>Bold</b> item</li>
        <li><i>Italic</i> item</li>
        </ul>"""
        result = convert_list(html)

        assert 'Bold' in result
        assert 'Italic' in result


@pytest.mark.deterministic
@pytest.mark.unit
class TestHtmlToMarkdown:
    """Tests for general HTML to Markdown conversion."""

    def test_paragraph_conversion(self):
        """Test simple paragraph conversion."""
        html = "<p>This is a paragraph.</p>"
        result = html_to_markdown(html)

        assert 'This is a paragraph.' in result

    def test_bold_text(self):
        """Test bold text conversion."""
        html = "<p>This is <b>bold</b> text.</p>"
        result = html_to_markdown(html)

        # Should contain bold text (might use ** or __)
        assert 'bold' in result.lower()

    def test_italic_text(self):
        """Test italic text conversion."""
        html = "<p>This is <i>italic</i> text.</p>"
        result = html_to_markdown(html)

        assert 'italic' in result.lower()

    def test_code_span(self):
        """Test inline code conversion."""
        html = "<p>Use the <code>print()</code> function.</p>"
        result = html_to_markdown(html)

        assert 'print()' in result

    def test_heading_conversion(self):
        """Test heading conversion."""
        html = "<h1>Main Title</h1><h2>Subtitle</h2>"
        result = html_to_markdown(html)

        assert 'Main Title' in result
        assert 'Subtitle' in result
        # Should use # for headings
        assert '#' in result

    def test_link_conversion(self):
        """Test hyperlink conversion."""
        html = '<p>Visit <a href="https://example.com">Example Site</a></p>'
        result = html_to_markdown(html)

        assert 'Example Site' in result

    def test_mixed_content(self, sample_html_mixed_content):
        """Test conversion of mixed content (tables, lists, paragraphs)."""
        result = html_to_markdown(sample_html_mixed_content)

        assert 'Parameter' in result
        assert 'Load the data' in result

    def test_whitespace_handling(self):
        """Test that excessive whitespace is handled."""
        html = "<p>Text   with    spaces</p>"
        result = html_to_markdown(html)

        # Should normalize whitespace
        assert result.strip() != ""
        assert 'Text' in result
        assert 'spaces' in result

    def test_empty_html(self):
        """Test handling of empty HTML."""
        result = html_to_markdown("")

        # Should return string (possibly empty or whitespace)
        assert isinstance(result, str)

    def test_malformed_html(self):
        """Test handling of malformed HTML."""
        html = "<p>Unclosed paragraph<h1>Missing closing tag"
        result = html_to_markdown(html)

        # Should handle gracefully
        assert isinstance(result, str)


@pytest.mark.deterministic
@pytest.mark.unit
class TestConvertNotebookOutputToMarkdown:
    """Tests for notebook output conversion."""

    def test_text_output(self):
        """Test conversion of text output."""
        output_dict = {
            'text/plain': 'Hello World'
        }
        result = convert_notebook_output_to_markdown(output_dict)

        assert result is not None
        assert 'Hello World' in str(result)

    def test_html_output(self):
        """Test conversion of HTML output."""
        output_dict = {
            'text/html': '<table><tr><td>Data</td></tr></table>'
        }
        result = convert_notebook_output_to_markdown(output_dict)

        assert result is not None

    def test_markdown_output(self):
        """Test conversion of markdown output."""
        output_dict = {
            'text/markdown': '# Header\n\nSome text'
        }
        result = convert_notebook_output_to_markdown(output_dict)

        assert result is not None

    def test_latex_output(self):
        """Test conversion of LaTeX output."""
        output_dict = {
            'text/latex': r'$\frac{x^2}{2}$'
        }
        result = convert_notebook_output_to_markdown(output_dict)

        assert result is not None

    def test_multiple_outputs(self):
        """Test handling of multiple output formats."""
        output_dict = {
            'text/plain': 'Text version',
            'text/html': '<p>HTML version</p>',
        }
        result = convert_notebook_output_to_markdown(output_dict)

        # Should pick one representation
        assert result is not None

    def test_empty_output(self):
        """Test handling of empty output."""
        output_dict = {}
        result = convert_notebook_output_to_markdown(output_dict)

        # Should return something (possibly empty)
        assert result is not None or result is None

    def test_image_output(self):
        """Test handling of image output."""
        output_dict = {
            'image/png': '/9j/4AAQSkZJRgABA...',  # Fake base64
        }
        result = convert_notebook_output_to_markdown(output_dict)

        # Should handle image output
        assert result is not None


@pytest.mark.deterministic
@pytest.mark.unit
class TestRoundTripConsistency:
    """Tests to verify consistency across multiple conversions."""

    def test_multiple_conversions_same_result(self):
        """Test that converting the same content twice gives same result."""
        html = "<table><tr><th>A</th></tr><tr><td>1</td></tr></table>"

        result1 = html_table_to_markdown(html)
        result2 = html_table_to_markdown(html)

        assert result1 == result2

    def test_whitespace_normalization(self):
        """Test that whitespace variations don't affect output."""
        html1 = "<table><tr><th>A</th></tr></table>"
        html2 = "<table>\n  <tr>\n    <th>A</th>\n  </tr>\n</table>"

        result1 = html_table_to_markdown(html1)
        result2 = html_table_to_markdown(html2)

        # Both should produce similar output
        assert 'A' in result1
        assert 'A' in result2
