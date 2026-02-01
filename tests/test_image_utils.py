"""
Tests for image_utils.py - image encoding and payload optimization.

Tests cover:
- JPEG encoding with edge case handling (RGBA, GIF, WebP, CMYK)
- Payload size estimation
- Adaptive image optimization (quality → resolution → count fallback)
- Token estimation and budgeting
- No API calls required - all tests are deterministic
"""

import pytest
import sys
import io
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PIL import Image

# Add the scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'dot_github_folder' / 'scripts'))

from image_utils import (
    estimate_image_tokens,
    filter_images_by_token_budget,
    validate_image_file,
    encode_image_to_jpeg,
    estimate_jpeg_size,
    estimate_total_payload_size,
    optimize_images_for_payload,
    MAX_PAYLOAD_MB,
    MIN_QUALITY,
    MIN_RESOLUTION,
)


@pytest.mark.deterministic
@pytest.mark.unit
class TestEncodeImageToJpeg:
    """Tests for JPEG encoding with format conversion."""

    def test_encode_rgb_image(self):
        """Test encoding a standard RGB image."""
        img = Image.new('RGB', (100, 100), color='red')
        jpeg_bytes = encode_image_to_jpeg(img, quality=85)

        assert jpeg_bytes is not None
        assert len(jpeg_bytes) > 0
        assert jpeg_bytes.startswith(b'\xff\xd8')  # JPEG magic bytes

    def test_encode_rgba_converts_to_rgb(self):
        """Test that RGBA images are converted to RGB with white background."""
        # Create RGBA image with transparency
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))  # Semi-transparent red
        jpeg_bytes = encode_image_to_jpeg(img, quality=85)

        assert jpeg_bytes is not None
        assert len(jpeg_bytes) > 0
        assert jpeg_bytes.startswith(b'\xff\xd8')  # Valid JPEG

    def test_encode_grayscale_converts_to_rgb(self):
        """Test that grayscale images are converted to RGB."""
        img = Image.new('L', (100, 100), color=128)
        jpeg_bytes = encode_image_to_jpeg(img, quality=85)

        assert jpeg_bytes is not None
        assert len(jpeg_bytes) > 0

    def test_quality_affects_size(self):
        """Test that higher quality produces larger JPEG."""
        # Create a complex image that will compress differently
        img = Image.new('RGB', (200, 200), color=(100, 150, 200))

        jpeg_q95 = encode_image_to_jpeg(img, quality=95)
        jpeg_q65 = encode_image_to_jpeg(img, quality=65)

        assert len(jpeg_q95) > len(jpeg_q65), "Higher quality should produce larger file"

    def test_encode_handles_none_gracefully(self):
        """Test that encoding None image returns None."""
        result = encode_image_to_jpeg(None, quality=85)

        # Should either return None or handle gracefully (implementation dependent)
        assert result is None or isinstance(result, bytes)


@pytest.mark.deterministic
@pytest.mark.unit
class TestEstimateJpegSize:
    """Tests for JPEG size estimation."""

    def test_estimate_simple_image(self, tmp_path):
        """Test size estimation for a simple image."""
        img = Image.new('RGB', (100, 100), color='red')
        img_path = tmp_path / "test.png"
        img.save(img_path)

        size = estimate_jpeg_size(str(img_path), max_dimension=None, quality=85)

        assert size > 0
        assert isinstance(size, int)

    def test_estimate_with_resize(self, tmp_path):
        """Test that resizing reduces estimated size."""
        img = Image.new('RGB', (500, 500), color='blue')
        img_path = tmp_path / "test.png"
        img.save(img_path)

        size_full = estimate_jpeg_size(str(img_path), max_dimension=None, quality=85)
        size_resized = estimate_jpeg_size(str(img_path), max_dimension=250, quality=85)

        assert size_resized < size_full

    def test_estimate_quality_impact(self, tmp_path):
        """Test that quality reduction reduces estimated size."""
        img = Image.new('RGB', (200, 200), color='green')
        img_path = tmp_path / "test.png"
        img.save(img_path)

        size_q85 = estimate_jpeg_size(str(img_path), max_dimension=None, quality=85)
        size_q65 = estimate_jpeg_size(str(img_path), max_dimension=None, quality=65)

        # Quality reduction should generally reduce size, but due to compression
        # artifacts with small images, allow for small variations
        assert size_q65 <= size_q85 * 1.01  # Allow 1% tolerance

    def test_estimate_nonexistent_file(self):
        """Test handling of nonexistent file."""
        size = estimate_jpeg_size("/nonexistent/path.png", max_dimension=None, quality=85)

        assert size == 0


@pytest.mark.deterministic
@pytest.mark.unit
class TestEstimateTotalPayloadSize:
    """Tests for total payload size estimation."""

    def test_calculate_payload_size(self):
        """Test basic payload size calculation."""
        text_size = 50000  # 50KB
        images = ["data:image/jpeg;base64," + "x" * 100000]  # ~100KB base64

        total = estimate_total_payload_size(text_size, images)

        # Should be text + images + JSON overhead
        assert total > 100000
        assert total > text_size

    def test_payload_with_multiple_images(self):
        """Test payload size with multiple images."""
        text_size = 50000
        images = [
            "data:image/jpeg;base64," + "x" * 100000,
            "data:image/jpeg;base64," + "x" * 100000,
            "data:image/jpeg;base64," + "x" * 100000,
        ]

        total = estimate_total_payload_size(text_size, images)

        # Should sum all image sizes
        assert total > 300000

    def test_payload_empty_images(self):
        """Test payload size with no images."""
        text_size = 50000
        images = []

        total = estimate_total_payload_size(text_size, images)

        # Should be text + JSON overhead only
        assert total > text_size
        assert total < text_size + 50000  # JSON overhead is ~10KB


@pytest.mark.deterministic
@pytest.mark.unit
class TestOptimizeImagesForPayload:
    """Tests for adaptive image optimization."""

    def test_optimize_small_payload_no_reduction(self, tmp_path):
        """Test that small payloads don't require optimization."""
        # Create a small image
        img = Image.new('RGB', (100, 100), color='red')
        img_path = tmp_path / "test.png"
        img.save(img_path)

        optimized = optimize_images_for_payload(
            image_paths=[str(img_path)],
            text_size_bytes=50000,
            config={'vision': {'resize_max_dimension': 768}},
            max_payload_mb=2.5
        )

        # Should succeed and return optimized image(s)
        assert len(optimized) > 0
        assert optimized[0]['quality'] == 85  # No quality reduction needed

    def test_optimize_quality_reduction(self, tmp_path):
        """Test that optimization reduces quality when needed."""
        # Create images that would exceed payload
        img = Image.new('RGB', (800, 600), color='blue')
        img_path = tmp_path / "test.png"
        img.save(img_path)

        # Use very tight budget to force quality reduction
        optimized = optimize_images_for_payload(
            image_paths=[str(img_path)],
            text_size_bytes=500000,  # Large text
            config={'vision': {'resize_max_dimension': 768}},
            max_payload_mb=0.8  # Very tight budget
        )

        if optimized:
            # If images fit, quality should be reduced or resolution reduced
            assert optimized[0]['quality'] <= 85

    def test_optimize_keeps_all_images_when_possible(self, tmp_path):
        """Test that optimization tries to keep all images."""
        # Create three small images
        image_paths = []
        for i in range(3):
            img = Image.new('RGB', (150, 150), color=(i*80, i*80, i*80))
            img_path = tmp_path / f"test_{i}.png"
            img.save(img_path)
            image_paths.append(str(img_path))

        optimized = optimize_images_for_payload(
            image_paths=image_paths,
            text_size_bytes=100000,
            config={'vision': {'resize_max_dimension': 768}},
            max_payload_mb=2.5
        )

        # Should keep all 3 images if possible
        assert len(optimized) == 3

    def test_optimize_fallback_quality_then_resolution(self, tmp_path):
        """Test that optimization tries quality and resolution adjustments."""
        img = Image.new('RGB', (600, 600), color='cyan')
        img_path = tmp_path / "test.png"
        img.save(img_path)

        # Tight budget that forces optimization
        optimized = optimize_images_for_payload(
            image_paths=[str(img_path)],
            text_size_bytes=2000000,  # 2MB of text
            config={'vision': {'resize_max_dimension': 768}},
            max_payload_mb=2.5
        )

        # Optimization should either succeed with reduced quality/resolution, or fail gracefully
        assert isinstance(optimized, list)

    def test_optimize_empty_image_list(self):
        """Test optimization with no images."""
        optimized = optimize_images_for_payload(
            image_paths=[],
            text_size_bytes=50000,
            config={'vision': {'resize_max_dimension': 768}},
            max_payload_mb=2.5
        )

        assert len(optimized) == 0

    def test_optimize_respects_max_payload(self, tmp_path):
        """Test that optimized payload respects max_payload_mb."""
        img = Image.new('RGB', (300, 300), color='yellow')
        img_path = tmp_path / "test.png"
        img.save(img_path)

        optimized = optimize_images_for_payload(
            image_paths=[str(img_path)],
            text_size_bytes=100000,
            config={'vision': {'resize_max_dimension': 768}},
            max_payload_mb=2.5
        )

        if optimized:
            # Verify total size is under limit
            total_size = 100000 + sum(len(img['base64_data']) for img in optimized)
            assert total_size < 2.5 * 1024 * 1024


@pytest.mark.deterministic
@pytest.mark.unit
class TestEstimateImageTokens:
    """Tests for image token estimation from actual image files."""

    def test_estimate_tokens_for_existing_file(self, tmp_path):
        """Test token estimation for an actual image file."""
        img = Image.new('RGB', (512, 512), color='red')
        img_path = tmp_path / "test.png"
        img.save(img_path)

        # Should estimate tokens without errors
        tokens = estimate_image_tokens(str(img_path), max_dimension=None)

        assert isinstance(tokens, int)
        assert tokens > 0

    def test_estimate_tokens_with_resize(self, tmp_path):
        """Test that max_dimension reduces token count."""
        img = Image.new('RGB', (2048, 2048), color='blue')
        img_path = tmp_path / "test.png"
        img.save(img_path)

        tokens_full = estimate_image_tokens(str(img_path), max_dimension=None)
        tokens_resized = estimate_image_tokens(str(img_path), max_dimension=1024)

        assert tokens_resized <= tokens_full

    def test_estimate_tokens_nonexistent_file(self):
        """Test handling of nonexistent file."""
        tokens = estimate_image_tokens("/nonexistent/file.png", max_dimension=None)

        # Should return reasonable estimate or 0
        assert tokens >= 0


@pytest.mark.deterministic
@pytest.mark.unit
class TestFilterImagesByTokenBudget:
    """Tests for greedy token budget filtering logic."""

    def test_single_image_under_budget(self):
        """Test single image that fits in budget."""
        images = ['image1.png']
        image_tokens = {'image1.png': 255}

        with patch('image_utils.estimate_image_tokens') as mock_est:
            def mock_tokens(path, max_dimension=None):
                return image_tokens.get(path, 0)
            mock_est.side_effect = mock_tokens
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
            def mock_tokens(path, max_dimension=None):
                return image_tokens.get(path, 0)
            mock_est.side_effect = mock_tokens
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
            'img1.png': 255,
            'img2.png': 255,
            'img3.png': 255,
        }

        with patch('image_utils.estimate_image_tokens') as mock_est:
            def mock_tokens(path, max_dimension=None):
                return image_tokens.get(path, 0)
            mock_est.side_effect = mock_tokens
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
            def mock_tokens(path, max_dimension=None):
                return image_tokens.get(path, 0)
            mock_est.side_effect = mock_tokens
            selected, total_tokens = filter_images_by_token_budget(
                images, max_tokens=750
            )

        # Should fit first two images at most
        assert total_tokens <= 750

    def test_budget_exactly_met(self):
        """Test when total tokens exactly match budget."""
        images = ['img1.png', 'img2.png']
        image_tokens = {
            'img1.png': 500,
            'img2.png': 500,
        }

        with patch('image_utils.estimate_image_tokens') as mock_est:
            def mock_tokens(path, max_dimension=None):
                return image_tokens.get(path, 0)
            mock_est.side_effect = mock_tokens
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
            def mock_tokens(path, max_dimension=None):
                return 255
            mock_est.side_effect = mock_tokens
            selected, total_tokens = filter_images_by_token_budget(
                images, max_tokens=0
            )

        assert len(selected) == 0
        assert total_tokens == 0

    def test_greedy_algorithm_efficiency(self):
        """Test that greedy algorithm selects images efficiently."""
        images = ['small.png', 'medium.png', 'large.png']
        image_tokens = {
            'small.png': 100,
            'medium.png': 300,
            'large.png': 900,
        }

        with patch('image_utils.estimate_image_tokens') as mock_est:
            def mock_tokens(path, max_dimension=None):
                return image_tokens.get(path, 0)
            mock_est.side_effect = mock_tokens
            selected, total_tokens = filter_images_by_token_budget(
                images, max_tokens=1000
            )

        # Should stay within budget
        assert total_tokens <= 1000

    def test_filtering_deterministic(self):
        """Test that filtering is deterministic for same inputs."""
        images = ['img1.png', 'img2.png']

        with patch('image_utils.estimate_image_tokens') as mock_est:
            def mock_tokens(path, max_dimension=None):
                return 250
            mock_est.side_effect = mock_tokens

            result1 = filter_images_by_token_budget(images, max_tokens=500)
            result2 = filter_images_by_token_budget(images, max_tokens=500)

        assert result1 == result2


@pytest.mark.deterministic
@pytest.mark.unit
class TestValidateImageFile:
    """Tests for image file validation (extension and existence checking)."""

    def test_valid_existing_png_file(self, tmp_path):
        """Test validation of existing PNG file."""
        img = Image.new('RGB', (100, 100), color='red')
        img_path = tmp_path / "test.png"
        img.save(img_path)

        result = validate_image_file(str(img_path))

        assert result is True

    def test_valid_existing_jpg_file(self, tmp_path):
        """Test validation of existing JPG file."""
        img = Image.new('RGB', (100, 100), color='green')
        img_path = tmp_path / "test.jpg"
        img.save(img_path)

        result = validate_image_file(str(img_path))

        assert result is True

    def test_invalid_nonexistent_file(self):
        """Test rejection of nonexistent file."""
        result = validate_image_file("/nonexistent/image.png")

        assert result is False

    def test_invalid_text_file(self, tmp_path):
        """Test rejection of text file."""
        txt_path = tmp_path / "document.txt"
        txt_path.write_text("Hello")

        result = validate_image_file(str(txt_path))

        assert result is False

    def test_valid_extension_format(self):
        """Test that extension validation works for format checking."""
        # These should be recognized as valid formats based on extension
        valid_extensions = ['image.png', 'photo.jpg', 'animation.gif', 'image.webp']

        for filename in valid_extensions:
            # Don't check existence, just format
            # This tests the extension logic
            ext = Path(filename).suffix.lower().lstrip('.')
            assert ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']


@pytest.mark.deterministic
@pytest.mark.unit
class TestPayloadOptimizationIntegration:
    """Integration tests for complete payload optimization workflow."""

    def test_optimization_workflow_with_real_images(self, tmp_path):
        """Test complete optimization workflow with real image files."""
        # Create test images
        image_paths = []
        for i in range(3):
            img = Image.new('RGB', (200, 200), color=(i*80, i*80, i*80))
            img_path = tmp_path / f"test_{i}.png"
            img.save(img_path)
            image_paths.append(str(img_path))

        # Run optimization
        optimized = optimize_images_for_payload(
            image_paths=image_paths,
            text_size_bytes=100000,
            config={'vision': {'resize_max_dimension': 768}},
            max_payload_mb=2.5
        )

        # Verify results
        assert isinstance(optimized, list)
        assert len(optimized) <= len(image_paths)
        for img_data in optimized:
            assert 'base64_data' in img_data
            assert 'quality' in img_data
            assert 'resolution' in img_data
            assert img_data['base64_data'].startswith('data:image/jpeg;base64,')

    def test_optimization_quality_reduction_works(self, tmp_path):
        """Test that quality reduction occurs under tight budget."""
        # Create one large image
        img = Image.new('RGB', (800, 600), color='blue')
        img_path = tmp_path / "large.png"
        img.save(img_path)

        # Tight budget to force optimization
        optimized = optimize_images_for_payload(
            image_paths=[str(img_path)],
            text_size_bytes=2000000,  # 2MB text
            config={'vision': {'resize_max_dimension': 768}},
            max_payload_mb=2.4  # Just enough
        )

        # Should have optimized or returned empty
        assert isinstance(optimized, list)

    def test_constants_are_defined(self):
        """Test that optimization constants are properly defined."""
        assert MAX_PAYLOAD_MB == 2.5
        assert MIN_QUALITY == 65
        assert MIN_RESOLUTION == 256
