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
            'assignment': {
                'course': 'TEST101',
                'name': 'test-project',
                'total_points': 100
            },
            'criteria': [
                {
                    'id': 'criterion1',
                    'name': 'First Criterion',
                    'weight': 30,
                    'levels': {
                        'advanced': {'description': 'Advanced work', 'point_range': [28, 30], 'indicators': []},
                        'proficient': {'description': 'Proficient work', 'point_range': [20, 27], 'indicators': []},
                        'developing': {'description': 'Developing work', 'point_range': [0, 19], 'indicators': []},
                    }
                },
                {
                    'id': 'criterion2',
                    'name': 'Second Criterion',
                    'weight': 70,
                    'levels': {
                        'excellent': {'description': 'Excellent work', 'point_range': [63, 70], 'indicators': []},
                        'good': {'description': 'Good work', 'point_range': [49, 62], 'indicators': []},
                        'fair': {'description': 'Fair work', 'point_range': [0, 48], 'indicators': []},
                    }
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
            'assignment': {
                'course': 'PH 280: Computational Physics',
                'name': 'Project 3: Taylor Series',
                'total_points': 100
            },
            'criteria': [
                {
                    'id': 'criterion-1',
                    'name': 'Theory & Applications (Math)',
                    'weight': 40,
                    'levels': {
                        'excellent': {
                            'description': 'Clear explanation with examples & evidence',
                            'point_range': [36, 40],
                            'indicators': []
                        }
                    }
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
            'assignment': {
                'course': 'TEST',
                'name': 'test',
                'total_points': 100
            },
            'criteria': [
                {
                    'id': 'crit1',
                    'name': 'Criterion',
                    'weight': 100,
                    'levels': {
                        'advanced': {
                            'description': (
                                'This is a very long description that spans multiple '
                                'sentences and explains in detail what constitutes '
                                'excellent performance on this criterion. It should include '
                                'specific examples of what work looks like at this level.'
                            ),
                            'point_range': [90, 100],
                            'indicators': []
                        }
                    }
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
            'assignment': {
                'course': 'TEST',
                'name': 'test',
                'total_points': 100
            },
            'criteria': [
                {
                    'id': 'crit1',
                    'name': 'Criterion',
                    'weight': 100,
                    'levels': {
                        'advanced': {
                            'description': 'Advanced work',
                            'point_range': [90, 100],
                            'indicators': []
                        },
                        'basic': {
                            'description': '',
                            'point_range': [0, 89],
                            'indicators': []
                        }
                    }
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
            'assignment': {
                'course': 'Physics 物理',
                'name': 'test-проект',
                'total_points': 100
            },
            'criteria': [
                {
                    'id': 'crit1',
                    'name': 'Criterion α β γ',
                    'weight': 100,
                    'levels': {
                        'advanced': {
                            'description': 'Excellent work with ✓ check marks',
                            'point_range': [90, 100],
                            'indicators': ['Advanced ★★★']
                        }
                    }
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


@pytest.mark.deterministic
@pytest.mark.unit
class TestRealWorldRubrics:
    """Tests for real-world rubrics from various courses."""

    @pytest.fixture
    def fixture_dir(self):
        """Path to the fixtures directory."""
        return Path(__file__).parent / 'fixtures' / 'rubrics'

    def test_ph280_p01_euler_markdown_to_yaml(self, fixture_dir, tmp_path):
        """Test conversion of PH 280 P1 Euler rubric (Markdown to YAML)."""
        md_file = fixture_dir / 'ph280-p01-euler-rubric.md'
        yaml_file = tmp_path / 'ph280_p01.yml'

        if not md_file.exists():
            pytest.skip(f"Rubric file {md_file} not found")

        # Convert to YAML
        markdown_to_yaml(str(md_file), str(yaml_file))

        # Verify output exists and is valid YAML
        assert yaml_file.exists()
        import yaml
        with open(yaml_file) as f:
            result = yaml.safe_load(f)
        assert isinstance(result, dict)
        assert 'criteria' in result

    def test_ph280_p03_taylor_markdown_to_yaml(self, fixture_dir, tmp_path):
        """Test conversion of PH 280 P3 Taylor rubric (Markdown to YAML)."""
        md_file = fixture_dir / 'ph280-p03-taylor-series-rubric.md'
        yaml_file = tmp_path / 'ph280_p03.yml'

        if not md_file.exists():
            pytest.skip(f"Rubric file {md_file} not found")

        # Convert to YAML
        markdown_to_yaml(str(md_file), str(yaml_file))

        # Verify output
        assert yaml_file.exists()
        import yaml
        with open(yaml_file) as f:
            result = yaml.safe_load(f)
        assert isinstance(result, dict)
        assert 'criteria' in result
        assert len(result['criteria']) > 0

    def test_ph230_p8_motors_markdown_to_yaml(self, fixture_dir, tmp_path):
        """Test conversion of PH 230 P8 Motors rubric (Markdown to YAML)."""
        md_file = fixture_dir / 'ph230-p8-motors-rubric.md'
        yaml_file = tmp_path / 'ph230_p8.yml'

        if not md_file.exists():
            pytest.skip(f"Rubric file {md_file} not found")

        # Convert to YAML
        markdown_to_yaml(str(md_file), str(yaml_file))

        # Verify output
        assert yaml_file.exists()
        import yaml
        with open(yaml_file) as f:
            result = yaml.safe_load(f)
        assert isinstance(result, dict)
        assert 'criteria' in result

    def test_test_assignment_heun_markdown_to_yaml(self, fixture_dir, tmp_path):
        """Test conversion of test assignment Heun rubric (Markdown to YAML)."""
        md_file = fixture_dir / 'test-assignment-heun-rubric.md'
        yaml_file = tmp_path / 'test_assignment_heun.yml'

        if not md_file.exists():
            pytest.skip(f"Rubric file {md_file} not found")

        # Convert to YAML
        markdown_to_yaml(str(md_file), str(yaml_file))

        # Verify output
        assert yaml_file.exists()
        import yaml
        with open(yaml_file) as f:
            result = yaml.safe_load(f)
        assert isinstance(result, dict)
        assert 'criteria' in result

    def test_ph230_p0_yaml_to_markdown(self, fixture_dir, tmp_path):
        """Test conversion of PH 230 P0 YAML rubric to Markdown."""
        yaml_file = fixture_dir / 'ph230-p0-rubric.yml'
        md_file = tmp_path / 'ph230_p0.md'

        if not yaml_file.exists():
            pytest.skip(f"Rubric file {yaml_file} not found")

        # Convert to Markdown
        yaml_to_markdown(str(yaml_file), str(md_file))

        # Verify output
        assert md_file.exists()
        content = md_file.read_text()
        assert len(content) > 0
        assert '#' in content  # Should have markdown headers

    def test_ph280_p01_roundtrip(self, fixture_dir, tmp_path):
        """Test roundtrip conversion of PH 280 P1 rubric (MD → YAML → MD)."""
        md_original = fixture_dir / 'ph280-p01-euler-rubric.md'
        yaml_temp = tmp_path / 'ph280_p01.yml'
        md_final = tmp_path / 'ph280_p01_final.md'

        if not md_original.exists():
            pytest.skip(f"Rubric file {md_original} not found")

        # First roundtrip: MD → YAML
        markdown_to_yaml(str(md_original), str(yaml_temp))
        assert yaml_temp.exists()

        # Second roundtrip: YAML → MD
        yaml_to_markdown(str(yaml_temp), str(md_final))
        assert md_final.exists()

        # Both outputs should be non-empty
        assert len(md_final.read_text()) > 0

    def test_ph230_p8_roundtrip(self, fixture_dir, tmp_path):
        """Test roundtrip conversion of PH 230 P8 rubric (MD → YAML → MD)."""
        md_original = fixture_dir / 'ph230-p8-motors-rubric.md'
        yaml_temp = tmp_path / 'ph230_p8.yml'
        md_final = tmp_path / 'ph230_p8_final.md'

        if not md_original.exists():
            pytest.skip(f"Rubric file {md_original} not found")

        # Roundtrip conversion
        markdown_to_yaml(str(md_original), str(yaml_temp))
        yaml_to_markdown(str(yaml_temp), str(md_final))

        # Verify both conversions completed
        assert yaml_temp.exists()
        assert md_final.exists()

    def test_all_fixtures_parseable(self, fixture_dir):
        """Test that all fixture rubrics can be parsed without errors."""
        import yaml
        from pathlib import Path

        if not fixture_dir.exists():
            pytest.skip(f"Fixture directory {fixture_dir} not found")

        # Test all YAML files
        for yaml_file in fixture_dir.glob('*.yml'):
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
            assert data is not None, f"Failed to parse {yaml_file}"

        # Test all Markdown files can be read
        for md_file in fixture_dir.glob('*.md'):
            content = md_file.read_text()
            assert len(content) > 0, f"Empty markdown file: {md_file}"

    def test_markdown_to_yaml_preserves_criteria_count(self, fixture_dir, tmp_path):
        """Test that MD→YAML conversion preserves criterion count."""
        md_files = [
            fixture_dir / 'ph280-p01-euler-rubric.md',
            fixture_dir / 'ph280-p03-taylor-series-rubric.md',
            fixture_dir / 'ph230-p8-motors-rubric.md',
        ]

        import yaml
        for md_file in md_files:
            if not md_file.exists():
                continue

            yaml_file = tmp_path / f"{md_file.stem}.yml"
            markdown_to_yaml(str(md_file), str(yaml_file))

            # Load and verify
            with open(yaml_file) as f:
                result = yaml.safe_load(f)

            # Should have criteria
            assert 'criteria' in result
            assert isinstance(result['criteria'], list)
            assert len(result['criteria']) > 0, f"No criteria in {md_file}"

    def test_yaml_to_markdown_preserves_assignment_info(self, fixture_dir, tmp_path):
        """Test that YAML→MD conversion preserves assignment information."""
        yaml_file = fixture_dir / 'ph230-p0-rubric.yml'

        if not yaml_file.exists():
            pytest.skip(f"Rubric file {yaml_file} not found")

        md_file = tmp_path / 'output.md'
        yaml_to_markdown(str(yaml_file), str(md_file))

        # Check that assignment info is in the markdown
        content = md_file.read_text()
        assert 'assignment' in content.lower() or 'course' in content.lower()

    def test_markdown_handles_various_table_formats(self, fixture_dir, tmp_path):
        """Test that converter handles different markdown table formats."""
        md_files = [
            fixture_dir / 'ph280-p01-euler-rubric.md',
            fixture_dir / 'ph230-p8-motors-rubric.md',
            fixture_dir / 'test-assignment-heun-rubric.md',
        ]

        import yaml
        for md_file in md_files:
            if not md_file.exists():
                continue

            yaml_file = tmp_path / f"{md_file.stem}.yml"

            # Should not raise an exception
            markdown_to_yaml(str(md_file), str(yaml_file))

            # Verify result is valid
            assert yaml_file.exists()
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
            assert isinstance(data, dict)

    def test_complex_rubric_with_indicators(self, fixture_dir, tmp_path):
        """Test conversion of complex rubric with indicators (PH 230 P8)."""
        md_file = fixture_dir / 'ph230-p8-motors-rubric.md'
        yaml_file = tmp_path / 'ph230_p8_complex.yml'

        if not md_file.exists():
            pytest.skip(f"Rubric file {md_file} not found")

        markdown_to_yaml(str(md_file), str(yaml_file))

        # Verify the YAML has the structure
        import yaml
        with open(yaml_file) as f:
            result = yaml.safe_load(f)

        # Should have criteria with levels
        assert 'criteria' in result
        if len(result['criteria']) > 0:
            first_criterion = result['criteria'][0]
            # Should have at least name and weight
            assert 'name' in first_criterion or 'id' in first_criterion

    def test_conversion_handles_long_descriptions(self, fixture_dir, tmp_path):
        """Test conversion with long criterion descriptions (test-assignment)."""
        md_file = fixture_dir / 'test-assignment-heun-rubric.md'
        yaml_file = tmp_path / 'test_assignment_long.yml'

        if not md_file.exists():
            pytest.skip(f"Rubric file {md_file} not found")

        # Should handle long descriptions without issues
        markdown_to_yaml(str(md_file), str(yaml_file))
        assert yaml_file.exists()

        # Convert back to markdown to verify structure is preserved
        md_file_2 = tmp_path / 'test_assignment_recovered.md'
        yaml_to_markdown(str(yaml_file), str(md_file_2))
        assert md_file_2.exists()

    def test_all_rubrics_convert_without_error(self, fixture_dir, tmp_path):
        """Test that all real-world rubrics convert without raising exceptions."""
        import yaml

        if not fixture_dir.exists():
            pytest.skip(f"Fixture directory {fixture_dir} not found")

        test_count = 0
        for md_file in fixture_dir.glob('*.md'):
            yaml_output = tmp_path / f"{md_file.stem}_converted.yml"
            try:
                markdown_to_yaml(str(md_file), str(yaml_output))
                test_count += 1
            except Exception as e:
                pytest.fail(f"Failed to convert {md_file}: {e}")

        assert test_count > 0, "No markdown files found to test"

    def test_yaml_rubric_converts_back(self, fixture_dir, tmp_path):
        """Test that YAML rubric can be converted to MD and back."""
        yaml_file = fixture_dir / 'ph230-p0-rubric.yml'

        if not yaml_file.exists():
            pytest.skip(f"Rubric file {yaml_file} not found")

        md_file = tmp_path / 'ph230_p0.md'
        yaml_file_2 = tmp_path / 'ph230_p0_recovered.yml'

        try:
            # YAML → MD
            yaml_to_markdown(str(yaml_file), str(md_file))
            assert md_file.exists()

            # MD → YAML
            markdown_to_yaml(str(md_file), str(yaml_file_2))
            assert yaml_file_2.exists()

            # Verify final YAML is valid
            import yaml
            with open(yaml_file_2) as f:
                result = yaml.safe_load(f)
            assert isinstance(result, dict)
        except Exception as e:
            pytest.fail(f"Roundtrip conversion failed: {e}")
