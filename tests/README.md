# AI Feedback System Test Suite

Comprehensive pytest suite for deterministic components of the ai-feedback-system.

## Overview

This test suite focuses on **deterministic testing** - testing the pure functions and logic components that don't require API calls, external services, or actual file I/O.

### Coverage

- **~70-80% of system functionality** can be tested deterministically
- **HTML/Markdown conversion**: 100% testable
- **Report parsing logic**: 90% testable (regex extraction, structure analysis)
- **Section extraction logic**: 80% testable (decision trees, prompt generation)
- **Image token calculation**: 100% testable (pure math)
- **Configuration validation**: 70% testable (schema validation)
- **Rubric conversion**: 100% testable (format conversion)

### What's NOT Tested Here

These require integration testing, mocking, or external systems:
- GitHub Models API calls
- GitHub issue creation
- Actual image file processing (PIL operations)
- Notebook JSON parsing and execution
- File I/O dependencies

## Running the Tests

### Prerequisites

```bash
# Install pytest
pip install pytest

# Or with your environment manager:
uv pip install pytest
```

### Basic Usage

```bash
# Run all deterministic tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_html_to_markdown.py -v

# Run specific test class
pytest tests/test_html_to_markdown.py::TestHtmlTableToMarkdown -v

# Run specific test
pytest tests/test_html_to_markdown.py::TestHtmlTableToMarkdown::test_simple_table -v
```

### Filtering by Markers

```bash
# Run only deterministic tests (all tests here)
pytest tests/ -m deterministic

# Run only unit tests
pytest tests/ -m unit

# Run only slow tests
pytest tests/ -m slow

# Run all except slow tests
pytest tests/ -m "not slow"
```

### Coverage Report

```bash
# Install coverage plugin
pip install pytest-cov

# Run with coverage
pytest tests/ --cov=dot_github_folder/scripts --cov-report=html

# View coverage in browser
open htmlcov/index.html
```

## Test Structure

```
tests/
├── conftest.py                      # Shared fixtures (sample data)
├── pytest.ini                       # Pytest configuration
├── README.md                        # This file
├── test_html_to_markdown.py         # HTML/Markdown conversion (100% deterministic)
├── test_parse_report.py             # Report parsing (90% deterministic)
├── test_section_extractor.py        # Section extraction logic (80% deterministic)
├── test_image_utils.py              # Image token calculation (100% deterministic)
├── test_rubric_converter.py         # Rubric format conversion (100% deterministic)
└── test_validate_feedback_setup.py  # Configuration validation (70% deterministic)
```

## Test Fixtures

### Sample Data Fixtures (conftest.py)

All fixtures are defined in `conftest.py` for reuse across test files:

#### Configuration Fixtures
- `sample_config` - Complete course configuration with model, vision, and budget settings
- `sample_rubric` - Example rubric with criteria and performance levels
- `sample_criterion` - Single criterion configuration
- `sample_criterion_with_vision` - Criterion with vision enabled

#### Report Content Fixtures
- `sample_qmd_complete` - Full realistic Quarto document
- `sample_qmd_with_callouts` - Quarto with template callout boxes
- `sample_qmd_with_embeds` - Quarto with notebook embeds
- `sample_qmd_with_figures` - Quarto with images
- `sample_parsed_report` - Pre-parsed report structure (what parse_report.py produces)

#### HTML Fixtures
- `sample_html_table_simple` - Basic HTML table
- `sample_html_table_complex` - Complex table with headers and multiple rows
- `sample_html_list_unordered` - HTML unordered list
- `sample_html_list_ordered` - HTML ordered list
- `sample_html_nested_lists` - Nested list structures
- `sample_html_mixed_content` - Tables, lists, and paragraphs

#### Utility Fixtures
- `image_dimensions_samples` - Dictionary of image dimensions for token calculation
- `temp_test_dir` - Temporary directory for test files
- `fixture_dir` - Path to fixtures directory

## Writing New Tests

### Example: Testing a Pure Function

```python
@pytest.mark.deterministic
@pytest.mark.unit
class TestMyFunction:
    """Tests for my deterministic function."""

    def test_basic_functionality(self):
        """Test basic behavior."""
        result = my_function("input")
        assert result == "expected"

    def test_edge_case(self):
        """Test edge case handling."""
        result = my_function("")
        assert result is not None

    def test_deterministic(self):
        """Test that function is deterministic."""
        result1 = my_function("input")
        result2 = my_function("input")
        assert result1 == result2
```

### Using Fixtures

```python
def test_with_fixture(self, sample_rubric, sample_config):
    """Test using fixtures."""
    # sample_rubric and sample_config are automatically injected
    assert sample_rubric is not None
    assert sample_config['model'] is not None
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("table", 255),
    ("medium", 765),
    ("large", 2805),
])
def test_multiple_cases(self, input, expected):
    """Test multiple input/output pairs."""
    result = estimate_image_tokens("test.png", dimensions=DIMS[input])
    assert result == expected
```

## Test Markers

All tests are marked with:
- `@pytest.mark.deterministic` - Pure functions, no external dependencies
- `@pytest.mark.unit` - Unit test (not integration)

Additional markers you can add:
- `@pytest.mark.slow` - For slow tests (not run by default)
- `@pytest.mark.integration` - For integration tests (requires more setup)

## Troubleshooting

### Import Errors

If tests fail with import errors, ensure:
1. You're running pytest from the ai-feedback-system root directory
2. The `dot_github_folder/scripts/` directory exists and contains the Python modules
3. Python path is correctly configured in `conftest.py`

### Missing Dependencies

Some tests require optional dependencies. Install them:
```bash
pip install pyyaml pillow  # For YAML and image handling
```

### Fixture Issues

If fixtures are not found:
```bash
# List all available fixtures
pytest --fixtures tests/

# Verify fixtures are loaded
pytest tests/ -v --setup-show
```

## Continuous Integration

To run tests in CI/CD:

```bash
# Run all tests and generate report
pytest tests/ -v --tb=short --junit-xml=test-results.xml

# With coverage
pytest tests/ --cov=dot_github_folder/scripts --cov-report=xml --cov-report=term
```

## Performance

Most tests run quickly (<100ms each). Total test suite completes in seconds.

For performance testing:
```bash
# Time each test
pytest tests/ -v --durations=10

# Run only fast tests
pytest tests/ -m "not slow"
```

## Future Test Coverage

Potential areas for additional tests (requiring mocking or fixtures):
- Image file validation with actual image fixtures
- Notebook JSON parsing with sample notebooks
- File system operations with temporary test directories
- Configuration loading from YAML/JSON files
- Integration tests combining multiple components

## Contributing

When adding new tests:
1. Use the existing test structure as a template
2. Add the `@pytest.mark.deterministic` and `@pytest.mark.unit` markers
3. Include docstrings explaining what's being tested
4. Add fixtures to `conftest.py` if needed
5. Use descriptive assertion messages
6. Test edge cases and error conditions

Example:
```python
def test_something_meaningful(self, sample_fixture):
    """Test that demonstrates an important behavior."""
    result = some_function(sample_fixture)

    assert result is not None, "Result should not be None"
    assert "expected" in result, "Result should contain 'expected'"
```

## Questions?

For questions about the test suite, refer to:
- Individual test file docstrings
- `conftest.py` fixture documentation
- Pytest documentation: https://docs.pytest.org/
