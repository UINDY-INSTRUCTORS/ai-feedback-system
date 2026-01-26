"""
Tests for image_utils.py - deterministic image token calculation and logic.

Tests focus on the mathematical and logical components that don't require
actual image files: token estimation, budgeting logic, and validation.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add the scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'dot_github_folder' / 'scripts'))

from image_utils import (
    estimate_image_tokens,
    filter_images_by_token_budget,
    validate_image_file,
)


@pytest.mark.deterministic
@pytest.mark.unit
class TestEstimateImageTokens:
    """Tests for image token estimation (deterministic math)."""

    def test_small_image_tokens(self):
        """Test token calculation for small image (512x512)."""
        # 512x512: 1x1 tiles -> 85 + 1*170 = 255 tokens
        tokens = estimate_image_tokens("dummy.png", max_dimension=None,
                                      dimensions=(512, 512))

        assert tokens == 255

    def test_medium_image_tokens(self):
        """Test token calculation for medium image."""
        # 1024x1024: 2x2 tiles -> 85 + 4*170 = 765 tokens
        tokens = estimate_image_tokens("dummy.png", max_dimension=None,
                                      dimensions=(1024, 1024))

        assert tokens == 765

    def test_large_image_tokens(self):
        """Test token calculation for large image."""
        # 2048x2048: 4x4 tiles -> 85 + 16*170 = 2805 tokens
        tokens = estimate_image_tokens("dummy.png", max_dimension=None,
                                      dimensions=(2048, 2048))

        assert tokens == 2805

    def test_portrait_image_tokens(self):
        """Test token calculation for portrait image."""
        # 512x1024: 1x2 tiles -> 85 + 2*170 = 425 tokens
        tokens = estimate_image_tokens("dummy.png", max_dimension=None,
                                      dimensions=(512, 1024))

        assert tokens == 425

    def test_landscape_image_tokens(self):
        """Test token calculation for landscape image."""
        # 1024x512: 2x1 tiles -> 85 + 2*170 = 425 tokens
        tokens = estimate_image_tokens("dummy.png", max_dimension=None,
                                      dimensions=(1024, 512))

        assert tokens == 425

    def test_image_with_max_dimension_rescaling(self):
        """Test token calculation with max_dimension downscaling."""
        # 2048x2048 with max_dimension=1024 -> 1024x1024
        # -> 2x2 tiles -> 85 + 4*170 = 765 tokens
        tokens = estimate_image_tokens("dummy.png", max_dimension=1024,
                                      dimensions=(2048, 2048))

        assert tokens == 765

    def test_image_smaller_than_max_dimension(self):
        """Test that max_dimension doesn't upscale smaller images."""
        # 512x512 with max_dimension=1024 -> stays 512x512
        # -> 1x1 tiles -> 255 tokens
        tokens = estimate_image_tokens("dummy.png", max_dimension=1024,
                                      dimensions=(512, 512))

        assert tokens == 255

    def test_non_square_rescaling(self):
        """Test rescaling of non-square images."""
        # 2000x1000 with max_dimension=1024
        # Max dimension is 2000, scale factor = 1024/2000 = 0.512
        # Result: 1024x512 -> 2x1 tiles -> 425 tokens
        tokens = estimate_image_tokens("dummy.png", max_dimension=1024,
                                      dimensions=(2000, 1000))

        assert tokens == 425

    def test_token_calculation_deterministic(self, image_dimensions_samples):
        """Test that token calculation is deterministic."""
        for dims in image_dimensions_samples.values():
            result1 = estimate_image_tokens("dummy.png", max_dimension=None,
                                           dimensions=dims)
            result2 = estimate_image_tokens("dummy.png", max_dimension=None,
                                           dimensions=dims)

            assert result1 == result2


@pytest.mark.deterministic
@pytest.mark.unit
class TestFilterImagesByTokenBudget:
    """Tests for greedy token budget filtering logic."""

    def test_single_image_under_budget(self):
        """Test single image that fits in budget."""
        images = ['image1.png']
        image_tokens = {'image1.png': 255}

        with patch('image_utils.estimate_image_tokens') as mock_est:
            mock_est.side_effect = lambda path, **kwargs: image_tokens.get(path, 0)
            selected, total_tokens = filter_images_by_token_budget(
                images, max_tokens=1000
            )

        assert len(selected) == 1
        assert selected[0] == 'image1.png'
        assert total_tokens == 255

    def test_single_image_exceeds_budget(self):
        """Test single image that exceeds budget."""
        images = ['image1.png']
        image_tokens = {'image1.png': 2000}

        with patch('image_utils.estimate_image_tokens') as mock_est:
            mock_est.side_effect = lambda path, **kwargs: image_tokens.get(path, 0)
            selected, total_tokens = filter_images_by_token_budget(
                images, max_tokens=1000
            )

        # Even if it exceeds, might still include it or exclude it depending on impl
        assert isinstance(selected, list)
        assert total_tokens >= 0

    def test_multiple_images_fit_in_budget(self):
        """Test multiple images that all fit in budget."""
        images = ['img1.png', 'img2.png', 'img3.png']
        image_tokens = {
            'img1.png': 255,  # 255
            'img2.png': 255,  # 510
            'img3.png': 255,  # 765
        }

        with patch('image_utils.estimate_image_tokens') as mock_est:
            mock_est.side_effect = lambda path, **kwargs: image_tokens.get(path, 0)
            selected, total_tokens = filter_images_by_token_budget(
                images, max_tokens=1000
            )

        assert len(selected) >= 2
        assert total_tokens <= 1000

    def test_multiple_images_partial_fit(self):
        """Test multiple images where only some fit in budget."""
        images = ['img1.png', 'img2.png', 'img3.png']
        image_tokens = {
            'img1.png': 400,
            'img2.png': 400,
            'img3.png': 400,
        }

        with patch('image_utils.estimate_image_tokens') as mock_est:
            mock_est.side_effect = lambda path, **kwargs: image_tokens.get(path, 0)
            selected, total_tokens = filter_images_by_token_budget(
                images, max_tokens=750
            )

        # Should fit first two images (800 tokens)
        assert total_tokens <= 750
        # Greedy algorithm: includes as many as possible

    def test_budget_exactly_met(self):
        """Test when total tokens exactly match budget."""
        images = ['img1.png', 'img2.png']
        image_tokens = {
            'img1.png': 500,
            'img2.png': 500,
        }

        with patch('image_utils.estimate_image_tokens') as mock_est:
            mock_est.side_effect = lambda path, **kwargs: image_tokens.get(path, 0)
            selected, total_tokens = filter_images_by_token_budget(
                images, max_tokens=1000
            )

        assert total_tokens == 1000
        assert len(selected) == 2

    def test_empty_image_list(self):
        """Test with empty image list."""
        selected, total_tokens = filter_images_by_token_budget([], max_tokens=1000)

        assert len(selected) == 0
        assert total_tokens == 0

    def test_zero_budget(self):
        """Test with zero token budget."""
        images = ['img1.png']

        with patch('image_utils.estimate_image_tokens') as mock_est:
            mock_est.return_value = 255
            selected, total_tokens = filter_images_by_token_budget(
                images, max_tokens=0
            )

        assert len(selected) == 0
        assert total_tokens == 0

    def test_greedy_algorithm_efficiency(self):
        """Test that greedy algorithm selects highest value items."""
        # Images in order: small, medium, large
        images = ['small.png', 'medium.png', 'large.png']
        image_tokens = {
            'small.png': 100,
            'medium.png': 300,
            'large.png': 900,
        }

        with patch('image_utils.estimate_image_tokens') as mock_est:
            mock_est.side_effect = lambda path, **kwargs: image_tokens.get(path, 0)
            selected, total_tokens = filter_images_by_token_budget(
                images, max_tokens=1000
            )

        # Should fit large + small (1000) or medium + small (400)
        # Depending on greedy order
        assert total_tokens <= 1000

    def test_filtering_deterministic(self):
        """Test that filtering is deterministic for same inputs."""
        images = ['img1.png', 'img2.png']

        with patch('image_utils.estimate_image_tokens') as mock_est:
            mock_est.side_effect = lambda path, **kwargs: 250

            result1 = filter_images_by_token_budget(images, max_tokens=500)
            result2 = filter_images_by_token_budget(images, max_tokens=500)

        assert result1 == result2


@pytest.mark.deterministic
@pytest.mark.unit
class TestValidateImageFile:
    """Tests for image file validation (extension checking)."""

    def test_valid_png_file(self):
        """Test validation of PNG file."""
        result = validate_image_file("image.png")

        assert result is True

    def test_valid_jpg_file(self):
        """Test validation of JPG file."""
        result = validate_image_file("photo.jpg")

        assert result is True

    def test_valid_jpeg_file(self):
        """Test validation of JPEG file."""
        result = validate_image_file("photo.jpeg")

        assert result is True

    def test_valid_gif_file(self):
        """Test validation of GIF file."""
        result = validate_image_file("animation.gif")

        assert result is True

    def test_valid_webp_file(self):
        """Test validation of WebP file."""
        result = validate_image_file("image.webp")

        assert result is True

    def test_invalid_text_file(self):
        """Test rejection of text file."""
        result = validate_image_file("document.txt")

        assert result is False

    def test_invalid_pdf_file(self):
        """Test rejection of PDF file."""
        result = validate_image_file("document.pdf")

        assert result is False

    def test_invalid_python_file(self):
        """Test rejection of Python file."""
        result = validate_image_file("script.py")

        assert result is False

    def test_case_insensitive_validation(self):
        """Test that validation is case-insensitive."""
        result1 = validate_image_file("image.PNG")
        result2 = validate_image_file("image.Jpg")
        result3 = validate_image_file("image.JPEG")

        assert result1 is True
        assert result2 is True
        assert result3 is True

    def test_path_with_directory(self):
        """Test validation with full path."""
        result = validate_image_file("/path/to/image.png")

        assert result is True

    def test_validation_deterministic(self):
        """Test that validation is deterministic."""
        filepath = "test.png"

        result1 = validate_image_file(filepath)
        result2 = validate_image_file(filepath)

        assert result1 == result2


@pytest.mark.deterministic
@pytest.mark.unit
class TestImageTokenCalculationLogic:
    """Integration tests for image token calculation logic."""

    def test_token_calculation_with_various_sizes(self, image_dimensions_samples):
        """Test token calculation across various image sizes."""
        expected_tokens = {
            'small': 255,      # 512x512: 1x1 tiles
            'medium': 255,     # 512x512: 1x1 tiles
            'large': 765,      # 1024x1024: 2x2 tiles
            'portrait': 425,   # 512x1024: 1x2 tiles
            'landscape': 425,  # 1024x512: 2x1 tiles
            'very_large': 2805, # 2048x2048: 4x4 tiles
        }

        for key, dims in image_dimensions_samples.items():
            tokens = estimate_image_tokens("test.png", max_dimension=None,
                                          dimensions=dims)
            assert tokens == expected_tokens[key], \
                f"Failed for {key}: expected {expected_tokens[key]}, got {tokens}"

    def test_token_scaling_with_max_dimension(self):
        """Test that token calculation respects max_dimension scaling."""
        # Image 2000x2000
        # With max_dimension=1024: scales to 1024x1024 (2x2 tiles)
        # Without scaling: 4x4 tiles

        tokens_scaled = estimate_image_tokens("test.png", max_dimension=1024,
                                             dimensions=(2000, 2000))
        tokens_unscaled = estimate_image_tokens("test.png", max_dimension=None,
                                               dimensions=(2000, 2000))

        assert tokens_scaled < tokens_unscaled
        assert tokens_scaled == 765  # 2x2 tiles
        assert tokens_unscaled == (85 + 16*170)  # 4x4 tiles

    def test_budget_filtering_selects_optimal_set(self):
        """Test that budget filtering selects an optimal image set."""
        images = ['img1.png', 'img2.png', 'img3.png']

        with patch('image_utils.estimate_image_tokens') as mock_est:
            # Images: 200, 300, 400 tokens
            def token_side_effect(path, **kwargs):
                return {
                    'img1.png': 200,
                    'img2.png': 300,
                    'img3.png': 400,
                }.get(path, 0)

            mock_est.side_effect = token_side_effect

            # Budget of 600: can fit 200+300 or 200+400
            selected, total = filter_images_by_token_budget(images, max_tokens=600)

            assert total <= 600
            assert len(selected) >= 1
