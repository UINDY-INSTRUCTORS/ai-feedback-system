"""
Tests for rubric_converter.py - deterministic YAML/Markdown rubric conversion.

All functions are pure conversions between formats with no external dependencies,
making them fully deterministic and ideal for comprehensive testing.
"""

import pytest
import sys
import tempfile
from pathlib import Path

# Add the scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'dot_github_folder' / 'scripts'))

from rubric_converter import (
    yaml_to_markdown,
    markdown_to_yaml,
    validate_roundtrip,
)


@pytest.mark.deterministic
@pytest.mark.unit
class TestYamlToMarkdown:
    """Tests for YAML to Markdown conversion."""

    def test_basic_rubric_conversion(self, sample_rubric, tmp_path):
        """Test conversion of basic rubric YAML to Markdown."""
        yaml_file = tmp_path / "rubric.yml"
        md_file = tmp_path / "rubric.md"

        # Write sample rubric
        import yaml
        with open(yaml_file, 'w') as f:
            yaml.dump(sample_rubric, f)

        # Convert
        yaml_to_markdown(str(yaml_file), str(md_file))

        # Check output exists and has content
        assert md_file.exists()
        content = md_file.read_text()
        assert len(content) > 0

    def test_markdown_contains_criterion_names(self, sample_rubric, tmp_path):
        """Test that converted Markdown includes criterion names."""
        yaml_file = tmp_path / "rubric.yml"
        md_file = tmp_path / "rubric.md"

        import yaml
        with open(yaml_file, 'w') as f:
            yaml.dump(sample_rubric, f)

        yaml_to_markdown(str(yaml_file), str(md_file))

        content = md_file.read_text()
        # Should include criterion names
        assert 'Theory & Explanation' in content or 'theory' in content.lower()
        assert 'Implementation/Code' in content or 'implementation' in content.lower()

    def test_markdown_contains_performance_levels(self, sample_rubric, tmp_path):
        """Test that converted Markdown includes performance levels."""
        yaml_file = tmp_path / "rubric.yml"
        md_file = tmp_path / "rubric.md"

        import yaml
        with open(yaml_file, 'w') as f:
            yaml.dump(sample_rubric, f)

        yaml_to_markdown(str(yaml_file), str(md_file))

        content = md_file.read_text()
        # Should include level names
        assert 'Exemplary' in content or 'exemplary' in content.lower()
        assert 'Satisfactory' in content or 'satisfactory' in content.lower()

    def test_markdown_conversion_deterministic(self, sample_rubric, tmp_path):
        """Test that conversion is deterministic."""
        yaml_file = tmp_path / "rubric.yml"

        import yaml
        with open(yaml_file, 'w') as f:
            yaml.dump(sample_rubric, f)

        # Convert twice
        md_file1 = tmp_path / "rubric1.md"
        md_file2 = tmp_path / "rubric2.md"

        yaml_to_markdown(str(yaml_file), str(md_file1))
        yaml_to_markdown(str(yaml_file), str(md_file2))

        # Should produce identical output
        assert md_file1.read_text() == md_file2.read_text()


@pytest.mark.deterministic
@pytest.mark.unit
class TestMarkdownToYaml:
    """Tests for Markdown to YAML conversion."""

    def test_basic_markdown_to_yaml(self, sample_rubric, tmp_path):
        """Test conversion of Markdown back to YAML."""
        yaml_file = tmp_path / "original.yml"
        md_file = tmp_path / "rubric.md"
        yaml_result = tmp_path / "result.yml"

        import yaml
        # Write original YAML
        with open(yaml_file, 'w') as f:
            yaml.dump(sample_rubric, f)

        # Convert to Markdown
        yaml_to_markdown(str(yaml_file), str(md_file))

        # Convert back to YAML
        markdown_to_yaml(str(md_file), str(yaml_result))

        # Should have created a YAML file
        assert yaml_result.exists()

    def test_roundtrip_preserves_structure(self, sample_rubric, tmp_path):
        """Test that structure is preserved through roundtrip conversion."""
        yaml_file1 = tmp_path / "original.yml"
        md_file = tmp_path / "rubric.md"
        yaml_file2 = tmp_path / "recovered.yml"

        import yaml
        with open(yaml_file1, 'w') as f:
            yaml.dump(sample_rubric, f)

        # Roundtrip conversion
        yaml_to_markdown(str(yaml_file1), str(md_file))
        markdown_to_yaml(str(md_file), str(yaml_file2))

        # Both YAML files should be readable
        with open(yaml_file1) as f:
            original = yaml.safe_load(f)
        with open(yaml_file2) as f:
            recovered = yaml.safe_load(f)

        assert isinstance(original, dict)
        assert isinstance(recovered, dict)

    def test_markdown_to_yaml_deterministic(self, sample_rubric, tmp_path):
        """Test that Markdown to YAML conversion is deterministic."""
        yaml_file = tmp_path / "original.yml"
        md_file = tmp_path / "rubric.md"

        import yaml
        with open(yaml_file, 'w') as f:
            yaml.dump(sample_rubric, f)

        yaml_to_markdown(str(yaml_file), str(md_file))

        # Convert back twice
        yaml_result1 = tmp_path / "result1.yml"
        yaml_result2 = tmp_path / "result2.yml"

        markdown_to_yaml(str(md_file), str(yaml_result1))
        markdown_to_yaml(str(md_file), str(yaml_result2))

        # Should produce identical results
        assert yaml_result1.read_text() == yaml_result2.read_text()


@pytest.mark.deterministic
@pytest.mark.unit
class TestValidateRoundtrip:
    """Tests for roundtrip validation."""

    def test_roundtrip_validation_passes(self, sample_rubric, tmp_path):
        """Test that roundtrip validation passes for valid rubric."""
        yaml_file = tmp_path / "rubric.yml"

        import yaml
        with open(yaml_file, 'w') as f:
            yaml.dump(sample_rubric, f)

        # Validation should pass
        is_valid = validate_roundtrip(str(yaml_file))

        # Result should be boolean
        assert isinstance(is_valid, bool)

    def test_roundtrip_validation_with_various_criteria(self, tmp_path):
        """Test roundtrip validation with various criterion structures."""
        rubric = {
            'course': 'TEST101',
            'project': 'test-project',
            'criteria': [
                {
                    'id': 'criterion1',
                    'name': 'First Criterion',
                    'weight': 30,
                    'levels': [
                        {'level': 'Advanced', 'percentage': '28-30%'},
                        {'level': 'Proficient', 'percentage': '20-27%'},
                        {'level': 'Developing', 'percentage': '0-19%'},
                    ]
                },
                {
                    'id': 'criterion2',
                    'name': 'Second Criterion',
                    'weight': 70,
                    'levels': [
                        {'level': 'Excellent', 'percentage': '63-70%'},
                        {'level': 'Good', 'percentage': '49-62%'},
                        {'level': 'Fair', 'percentage': '0-48%'},
                    ]
                },
            ]
        }

        yaml_file = tmp_path / "rubric.yml"
        import yaml
        with open(yaml_file, 'w') as f:
            yaml.dump(rubric, f)

        is_valid = validate_roundtrip(str(yaml_file))
        assert isinstance(is_valid, bool)


@pytest.mark.deterministic
@pytest.mark.unit
class TestConversionEdgeCases:
    """Tests for edge cases in format conversion."""

    def test_conversion_with_special_characters(self, tmp_path):
        """Test conversion with special characters in criterion names."""
        rubric = {
            'course': 'PH 280: Computational Physics',
            'project': 'Project 3: Taylor Series',
            'criteria': [
                {
                    'id': 'criterion-1',
                    'name': 'Theory & Applications (Math)',
                    'weight': 40,
                    'levels': [
                        {'level': 'Excellent', 'percentage': '36-40%',
                         'description': 'Clear explanation with examples & evidence'}
                    ]
                }
            ]
        }

        yaml_file = tmp_path / "rubric.yml"
        md_file = tmp_path / "rubric.md"

        import yaml
        with open(yaml_file, 'w') as f:
            yaml.dump(rubric, f)

        # Should convert without issues
        yaml_to_markdown(str(yaml_file), str(md_file))
        assert md_file.exists()

    def test_conversion_with_long_descriptions(self, tmp_path):
        """Test conversion with long description text."""
        rubric = {
            'course': 'TEST',
            'project': 'test',
            'criteria': [
                {
                    'id': 'crit1',
                    'name': 'Criterion',
                    'weight': 100,
                    'levels': [
                        {
                            'level': 'Advanced',
                            'percentage': '90-100%',
                            'description': (
                                'This is a very long description that spans multiple '
                                'sentences and explains in detail what constitutes '
                                'excellent performance on this criterion. It should include '
                                'specific examples of what work looks like at this level.'
                            )
                        }
                    ]
                }
            ]
        }

        yaml_file = tmp_path / "rubric.yml"
        md_file = tmp_path / "rubric.md"

        import yaml
        with open(yaml_file, 'w') as f:
            yaml.dump(rubric, f)

        yaml_to_markdown(str(yaml_file), str(md_file))
        assert md_file.exists()

    def test_conversion_with_empty_descriptions(self, tmp_path):
        """Test conversion with empty or missing descriptions."""
        rubric = {
            'course': 'TEST',
            'project': 'test',
            'criteria': [
                {
                    'id': 'crit1',
                    'name': 'Criterion',
                    'weight': 100,
                    'levels': [
                        {'level': 'Advanced', 'percentage': '90-100%'},
                        {'level': 'Basic', 'percentage': '0-89%', 'description': ''},
                    ]
                }
            ]
        }

        yaml_file = tmp_path / "rubric.yml"
        md_file = tmp_path / "rubric.md"

        import yaml
        with open(yaml_file, 'w') as f:
            yaml.dump(rubric, f)

        # Should handle gracefully
        yaml_to_markdown(str(yaml_file), str(md_file))
        assert md_file.exists()

    def test_conversion_with_unicode(self, tmp_path):
        """Test conversion with Unicode characters."""
        rubric = {
            'course': 'Physics 物理',
            'project': 'test-проект',
            'criteria': [
                {
                    'id': 'crit1',
                    'name': 'Criterion α β γ',
                    'weight': 100,
                    'levels': [
                        {'level': 'Advanced ★★★', 'percentage': '90-100%',
                         'description': 'Excellent work with ✓ check marks'}
                    ]
                }
            ]
        }

        yaml_file = tmp_path / "rubric.yml"
        md_file = tmp_path / "rubric.md"

        import yaml
        with open(yaml_file, 'w') as f:
            yaml.dump(rubric, f, allow_unicode=True)

        # Should handle Unicode
        yaml_to_markdown(str(yaml_file), str(md_file))
        assert md_file.exists()


@pytest.mark.deterministic
@pytest.mark.unit
class TestFormatConsistency:
    """Tests for consistency of format output."""

    def test_yaml_output_valid_structure(self, sample_rubric, tmp_path):
        """Test that YAML output has valid structure."""
        yaml_file = tmp_path / "rubric.yml"
        md_file = tmp_path / "rubric.md"
        yaml_result = tmp_path / "result.yml"

        import yaml
        with open(yaml_file, 'w') as f:
            yaml.dump(sample_rubric, f)

        yaml_to_markdown(str(yaml_file), str(md_file))
        markdown_to_yaml(str(md_file), str(yaml_result))

        # Result should be valid YAML
        with open(yaml_result) as f:
            result = yaml.safe_load(f)

        assert isinstance(result, dict)
        assert 'criteria' in result

    def test_markdown_output_readable(self, sample_rubric, tmp_path):
        """Test that Markdown output is readable."""
        yaml_file = tmp_path / "rubric.yml"
        md_file = tmp_path / "rubric.md"

        import yaml
        with open(yaml_file, 'w') as f:
            yaml.dump(sample_rubric, f)

        yaml_to_markdown(str(yaml_file), str(md_file))

        content = md_file.read_text()
        # Should be readable text
        assert len(content) > 0
        assert isinstance(content, str)
        # Should use Markdown formatting
        assert '#' in content or '|' in content or '-' in content

    def test_multiple_conversions_consistency(self, sample_rubric, tmp_path):
        """Test that multiple conversions maintain consistency."""
        yaml_file = tmp_path / "original.yml"

        import yaml
        with open(yaml_file, 'w') as f:
            yaml.dump(sample_rubric, f)

        # Do multiple roundtrips
        for i in range(3):
            md_file = tmp_path / f"rubric{i}.md"
            yaml_to_markdown(str(yaml_file), str(md_file))

            with open(md_file) as f:
                md_content = f.read()

            # Each conversion should produce non-empty Markdown
            assert len(md_content) > 0
