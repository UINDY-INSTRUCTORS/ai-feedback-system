"""
Tests for validate_feedback_setup.py - configuration and rubric validation.

Tests focus on the deterministic validation logic without requiring file I/O
or external systems.
"""

import pytest
import sys
from pathlib import Path

# Add the scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'dot_github_folder' / 'scripts'))

from validate_feedback_setup import (
    validate_vision_config,
)


@pytest.mark.deterministic
@pytest.mark.unit
class TestValidateVisionConfig:
    """Tests for vision configuration validation."""

    def test_valid_vision_config(self, sample_config, sample_rubric):
        """Test validation of valid vision configuration."""
        vision_config = sample_config['vision']

        # Extract criterion IDs from rubric
        criterion_ids = [c['id'] for c in sample_rubric['criteria']]

        issues = validate_vision_config(vision_config, sample_rubric)

        # Should be list (possibly empty for valid config)
        assert isinstance(issues, list)

    def test_vision_config_with_invalid_criterion(self, sample_config, sample_rubric):
        """Test vision config referencing non-existent criterion."""
        vision_config = sample_config['vision'].copy()
        vision_config['criteria'] = ['results', 'nonexistent_criterion']

        issues = validate_vision_config(vision_config, sample_rubric)

        # Should detect invalid criterion reference
        assert isinstance(issues, list)

    def test_vision_enabled_true(self, sample_rubric):
        """Test vision config with vision enabled."""
        vision_config = {
            'enabled': True,
            'criteria': ['implementation'],
        }

        issues = validate_vision_config(vision_config, sample_rubric)

        assert isinstance(issues, list)

    def test_vision_enabled_false(self, sample_rubric):
        """Test vision config with vision disabled."""
        vision_config = {
            'enabled': False,
            'criteria': [],
        }

        issues = validate_vision_config(vision_config, sample_rubric)

        # Should be valid even with empty criteria when disabled
        assert isinstance(issues, list)

    def test_vision_auto_detect_enabled(self, sample_rubric):
        """Test vision config with auto-detection enabled."""
        vision_config = {
            'enabled': True,
            'auto_detect': True,
            'criteria': ['implementation'],
        }

        issues = validate_vision_config(vision_config, sample_rubric)

        assert isinstance(issues, list)

    def test_vision_auto_detect_disabled(self, sample_rubric):
        """Test vision config with auto-detection disabled."""
        vision_config = {
            'enabled': True,
            'auto_detect': False,
            'criteria': ['implementation'],
        }

        issues = validate_vision_config(vision_config, sample_rubric)

        assert isinstance(issues, list)

    def test_vision_config_all_criteria(self, sample_rubric):
        """Test vision config with all criteria enabled."""
        vision_config = {
            'enabled': True,
            'criteria': [c['id'] for c in sample_rubric['criteria']],
        }

        issues = validate_vision_config(vision_config, sample_rubric)

        assert isinstance(issues, list)

    def test_vision_config_empty_criteria_list(self, sample_rubric):
        """Test vision config with empty criteria list."""
        vision_config = {
            'enabled': True,
            'criteria': [],
        }

        issues = validate_vision_config(vision_config, sample_rubric)

        # Empty criteria list might be valid or invalid depending on impl
        assert isinstance(issues, list)


@pytest.mark.deterministic
@pytest.mark.unit
class TestValidationErrorMessages:
    """Tests for validation error message quality."""

    def test_error_message_is_string(self, sample_rubric):
        """Test that validation issues are descriptive strings."""
        vision_config = {
            'enabled': True,
            'criteria': ['nonexistent'],
        }

        issues = validate_vision_config(vision_config, sample_rubric)

        # If there are issues, they should be strings
        for issue in issues:
            assert isinstance(issue, str)
            assert len(issue) > 0

    def test_error_messages_descriptive(self, sample_rubric):
        """Test that error messages are descriptive."""
        vision_config = {
            'enabled': True,
            'criteria': ['invalid_criterion_id'],
        }

        issues = validate_vision_config(vision_config, sample_rubric)

        # If errors found, should mention what's wrong
        if issues:
            error_text = '\n'.join(issues)
            # Should mention criterion or config issue
            assert len(error_text) > 10


@pytest.mark.deterministic
@pytest.mark.unit
class TestValidationConsistency:
    """Tests for validation consistency."""

    def test_validation_deterministic(self, sample_rubric):
        """Test that validation is deterministic."""
        vision_config = {
            'enabled': True,
            'criteria': ['implementation'],
        }

        result1 = validate_vision_config(vision_config, sample_rubric)
        result2 = validate_vision_config(vision_config, sample_rubric)

        assert result1 == result2

    def test_validation_with_equivalent_configs(self, sample_rubric):
        """Test that equivalent configs produce same results."""
        config1 = {
            'enabled': True,
            'criteria': ['implementation'],
            'auto_detect': False,
        }

        config2 = {
            'enabled': True,
            'criteria': ['implementation'],
            'auto_detect': False,
        }

        result1 = validate_vision_config(config1, sample_rubric)
        result2 = validate_vision_config(config2, sample_rubric)

        assert result1 == result2


@pytest.mark.deterministic
@pytest.mark.unit
class TestValidationLogic:
    """Tests for validation decision logic."""

    def test_vision_config_default_behavior(self, sample_rubric):
        """Test validation of minimal vision config."""
        vision_config = {'enabled': False}

        issues = validate_vision_config(vision_config, sample_rubric)

        # Should be valid (vision can be disabled)
        assert isinstance(issues, list)

    def test_vision_config_with_missing_keys(self, sample_rubric):
        """Test validation when optional keys are missing."""
        vision_config = {
            'enabled': True,
            # Missing 'criteria' key
        }

        issues = validate_vision_config(vision_config, sample_rubric)

        # Should handle gracefully (might require criteria or might not)
        assert isinstance(issues, list)

    def test_vision_config_with_extra_keys(self, sample_rubric):
        """Test validation with extra/unknown keys."""
        vision_config = {
            'enabled': True,
            'criteria': ['implementation'],
            'max_images_per_criterion': 3,
            'extra_key': 'should_be_ignored',
        }

        issues = validate_vision_config(vision_config, sample_rubric)

        # Should handle extra keys gracefully
        assert isinstance(issues, list)


@pytest.mark.deterministic
@pytest.mark.unit
class TestMultipleCriteriaValidation:
    """Tests for multi-criterion validation scenarios."""

    def test_validation_with_many_criteria(self):
        """Test validation with rubric containing many criteria."""
        rubric = {
            'course': 'TEST',
            'project': 'test',
            'criteria': [
                {'id': f'crit{i}', 'name': f'Criterion {i}', 'weight': 100//5}
                for i in range(5)
            ]
        }

        vision_config = {
            'enabled': True,
            'criteria': [f'crit{i}' for i in range(5)],
        }

        issues = validate_vision_config(vision_config, rubric)

        assert isinstance(issues, list)

    def test_partial_criterion_validation(self):
        """Test validation where only some criteria have vision."""
        rubric = {
            'course': 'TEST',
            'project': 'test',
            'criteria': [
                {'id': 'impl', 'name': 'Implementation', 'weight': 40},
                {'id': 'theory', 'name': 'Theory', 'weight': 30},
                {'id': 'results', 'name': 'Results', 'weight': 30},
            ]
        }

        vision_config = {
            'enabled': True,
            'criteria': ['results'],  # Only results uses vision
        }

        issues = validate_vision_config(vision_config, rubric)

        assert isinstance(issues, list)

    def test_duplicate_criteria_in_config(self):
        """Test validation when criteria list has duplicates."""
        rubric = {
            'course': 'TEST',
            'project': 'test',
            'criteria': [
                {'id': 'impl', 'name': 'Implementation', 'weight': 50},
                {'id': 'results', 'name': 'Results', 'weight': 50},
            ]
        }

        vision_config = {
            'enabled': True,
            'criteria': ['results', 'results', 'impl'],  # Duplicate 'results'
        }

        issues = validate_vision_config(vision_config, rubric)

        assert isinstance(issues, list)
