#!/usr/bin/env python3
"""
HTML to Markdown converter for notebook outputs.
Converts HTML tables and formatted content to clean markdown for AI analysis.
"""

import re
from html.parser import HTMLParser
from typing import List, Tuple


class TableToMarkdown(HTMLParser):
    """Converts HTML tables to markdown format."""

    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_header = False
        self.in_cell = False
        self.rows = []
        self.current_row = []
        self.current_cell = []
        self.header_rows = []

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.in_table = True
            self.rows = []
        elif tag == 'tr':
            self.in_row = True
            self.current_row = []
        elif tag == 'th':
            self.in_cell = True
            self.in_header = True
            self.current_cell = []
        elif tag == 'td':
            self.in_cell = True
            self.current_cell = []

    def handle_endtag(self, tag):
        if tag == 'table':
            self.in_table = False
        elif tag == 'tr':
            self.in_row = False
            if self.current_row:
                if self.in_header:
                    self.header_rows.append(self.current_row[:])
                else:
                    self.rows.append(self.current_row[:])
                self.current_row = []
        elif tag in ('th', 'td'):
            self.in_cell = False
            cell_text = ''.join(self.current_cell).strip()
            self.current_row.append(cell_text)
            self.current_cell = []
            if tag == 'th':
                self.in_header = False

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell.append(data)

    def get_markdown(self) -> str:
        """Convert collected table data to markdown format."""
        if not self.rows and not self.header_rows:
            return ""

        lines = []

        # Add header rows
        for header_row in self.header_rows:
            lines.append('| ' + ' | '.join(header_row) + ' |')
            # Add separator after each header
            lines.append('| ' + ' | '.join(['---'] * len(header_row)) + ' |')

        # If no header, but we have data, use the first row as header
        if not self.header_rows and self.rows:
            first_row = self.rows[0]
            lines.append('| ' + ' | '.join(first_row) + ' |')
            lines.append('| ' + ' | '.join(['---'] * len(first_row)) + ' |')
            self.rows = self.rows[1:]

        # Add data rows
        for row in self.rows:
            lines.append('| ' + ' | '.join(row) + ' |')

        return '\n'.join(lines)


def html_table_to_markdown(html: str) -> str:
    """
    Convert HTML table to markdown table format.

    Args:
        html: HTML string containing table(s)

    Returns:
        Markdown formatted table(s)
    """
    parser = TableToMarkdown()
    parser.feed(html)
    return parser.get_markdown()


def html_to_markdown(html: str) -> str:
    """
    Convert HTML to markdown, handling common notebook output formats.

    Handles:
    - Tables (convert to markdown tables)
    - Bold/italic (preserve formatting)
    - Links (preserve as markdown links)
    - Code blocks (preserve as code)
    - Lists (convert to markdown lists)

    Args:
        html: HTML string

    Returns:
        Markdown formatted string
    """
    if not html or not html.strip():
        return ""

    # Remove style tags and their contents (pandas DataFrames include CSS)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Remove script tags and their contents
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Remove div wrappers (pandas uses <div> around tables)
    html = re.sub(r'<div[^>]*>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'</div>', '', html, flags=re.IGNORECASE)

    # First, check if it's primarily a table
    if '<table' in html.lower():
        # Extract and convert tables
        table_pattern = r'<table[^>]*>.*?</table>'
        tables = re.findall(table_pattern, html, re.DOTALL | re.IGNORECASE)

        result = html
        for table_html in tables:
            table_md = html_table_to_markdown(table_html)
            result = result.replace(table_html, f'\n{table_md}\n')

        html = result

    # Convert common HTML formatting to markdown
    conversions = [
        # Headers
        (r'<h1[^>]*>(.*?)</h1>', r'# \1'),
        (r'<h2[^>]*>(.*?)</h2>', r'## \1'),
        (r'<h3[^>]*>(.*?)</h3>', r'### \1'),
        (r'<h4[^>]*>(.*?)</h4>', r'#### \1'),

        # Text formatting
        (r'<strong[^>]*>(.*?)</strong>', r'**\1**'),
        (r'<b[^>]*>(.*?)</b>', r'**\1**'),
        (r'<em[^>]*>(.*?)</em>', r'*\1*'),
        (r'<i[^>]*>(.*?)</i>', r'*\1*'),
        (r'<code[^>]*>(.*?)</code>', r'`\1`'),

        # Links
        (r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', r'[\2](\1)'),

        # Line breaks and paragraphs
        (r'<br\s*/?>', '\n'),
        (r'<p[^>]*>(.*?)</p>', r'\1\n\n'),

        # Lists
        (r'<ul[^>]*>(.*?)</ul>', lambda m: convert_list(m.group(1), ordered=False)),
        (r'<ol[^>]*>(.*?)</ol>', lambda m: convert_list(m.group(1), ordered=True)),

        # Code blocks
        (r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', r'\n```\n\1\n```\n'),
        (r'<pre[^>]*>(.*?)</pre>', r'\n```\n\1\n```\n'),
    ]

    text = html
    for pattern, replacement in conversions:
        if callable(replacement):
            text = re.sub(pattern, replacement, text, flags=re.DOTALL | re.IGNORECASE)
        else:
            text = re.sub(pattern, replacement, text, flags=re.DOTALL | re.IGNORECASE)

    # Remove remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Clean up excessive whitespace
    text = re.sub(r'\n\n\n+', '\n\n', text)
    text = text.strip()

    return text


def convert_list(html: str, ordered: bool = False) -> str:
    """Convert HTML list items to markdown list."""
    items = re.findall(r'<li[^>]*>(.*?)</li>', html, re.DOTALL | re.IGNORECASE)

    result = []
    for i, item in enumerate(items):
        # Remove nested tags from item
        item_text = re.sub(r'<[^>]+>', '', item).strip()

        if ordered:
            result.append(f"{i+1}. {item_text}")
        else:
            result.append(f"- {item_text}")

    return '\n' + '\n'.join(result) + '\n'


def convert_notebook_output_to_markdown(output_data: dict) -> dict:
    """
    Convert various notebook output formats to markdown.

    Args:
        output_data: Dict with keys like 'html', 'text', 'markdown', 'latex'

    Returns:
        Dict with all outputs converted to markdown format
    """
    converted = {}

    # HTML -> Markdown
    if output_data.get('html'):
        converted['html_as_markdown'] = []
        for html in output_data['html']:
            md = html_to_markdown(html)
            if md:
                converted['html_as_markdown'].append(md)

    # Text -> keep as-is (it's already plain)
    if output_data.get('text'):
        converted['text'] = output_data['text']

    # Markdown -> keep as-is
    if output_data.get('markdown'):
        converted['markdown'] = output_data['markdown']

    # LaTeX -> keep as-is (models understand LaTeX)
    if output_data.get('latex'):
        converted['latex'] = output_data['latex']

    return converted


if __name__ == '__main__':
    # Test with sample HTML table
    sample_html = """
    <table>
        <tr>
            <th>Measurement</th>
            <th>Expected</th>
            <th>Actual</th>
            <th>Error %</th>
        </tr>
        <tr>
            <td>Voltage</td>
            <td>5.0V</td>
            <td>4.98V</td>
            <td>0.4%</td>
        </tr>
        <tr>
            <td>Current</td>
            <td>100mA</td>
            <td>102mA</td>
            <td>2.0%</td>
        </tr>
    </table>
    """

    print("HTML to Markdown Table Conversion Test:")
    print("=" * 50)
    print(html_table_to_markdown(sample_html))
    print("\n")

    sample_formatted = """
    <h3>Analysis Results</h3>
    <p>The circuit performed <strong>within specifications</strong>.</p>
    <ul>
        <li>Voltage error: 0.4%</li>
        <li>Current error: 2.0%</li>
    </ul>
    """

    print("HTML to Markdown Formatting Test:")
    print("=" * 50)
    print(html_to_markdown(sample_formatted))
