#!/usr/bin/env python3
"""
Image utilities for vision-enabled AI feedback.
Handles image encoding, resizing, and format conversion.
"""

import base64
import io
import os
import mimetypes
from pathlib import Path
from typing import Optional, Tuple, List

# Try to import PIL, but gracefully degrade if not available
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("WARNING: PIL/Pillow not installed. Image resizing disabled.")


def encode_image_simple(image_path: str) -> Optional[str]:
    """
    Simple base64 encoding without resizing (no PIL required).

    Args:
        image_path: Path to the image file

    Returns:
        Base64-encoded string with data URI, or None if encoding fails
    """
    try:
        path = Path(image_path)
        if not path.exists():
            return None

        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type or not mime_type.startswith('image/'):
            mime_type = 'image/png'  # Default

        # Read and encode
        with open(image_path, 'rb') as f:
            img_data = f.read()
            base64_str = base64.b64encode(img_data).decode('utf-8')
            return f"data:{mime_type};base64,{base64_str}"

    except Exception as e:
        print(f"WARNING: Failed to encode image {image_path}: {e}")
        return None


def encode_image_to_base64(image_path: str, max_dimension: Optional[int] = None, quality: int = 85) -> Optional[str]:
    """
    Encode an image to base64, optionally resizing it first.

    Args:
        image_path: Path to the image file
        max_dimension: Maximum width or height (preserves aspect ratio)
        quality: JPEG quality (1-100) for compression

    Returns:
        Base64-encoded string with data URI, or None if encoding fails
    """
    try:
        # Check if file exists
        if not Path(image_path).exists():
            print(f"WARNING: Image not found: {image_path}")
            return None

        # If PIL is not available or no resizing needed, use simple encoding
        if not HAS_PIL or max_dimension is None:
            return encode_image_simple(image_path)

        # Open and optionally resize image
        with Image.open(image_path) as img:
            # Convert RGBA to RGB if needed (for JPEG compatibility)
            if img.mode == 'RGBA':
                # Create white background
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                img = rgb_img
            elif img.mode not in ('RGB', 'L'):  # L is grayscale
                img = img.convert('RGB')

            # Resize if needed
            if max_dimension and (img.width > max_dimension or img.height > max_dimension):
                # Calculate new size preserving aspect ratio
                if img.width > img.height:
                    new_width = max_dimension
                    new_height = int(img.height * (max_dimension / img.width))
                else:
                    new_height = max_dimension
                    new_width = int(img.width * (max_dimension / img.height))

                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"   Resized {Path(image_path).name}: {img.width}x{img.height}")

            # Encode to base64
            buffer = io.BytesIO()

            # Determine format from file extension
            file_ext = Path(image_path).suffix.lower()
            if file_ext in ['.jpg', '.jpeg']:
                img.save(buffer, format='JPEG', quality=quality, optimize=True)
                mime_type = 'image/jpeg'
            elif file_ext == '.png':
                img.save(buffer, format='PNG', optimize=True)
                mime_type = 'image/png'
            elif file_ext == '.gif':
                img.save(buffer, format='GIF')
                mime_type = 'image/gif'
            else:
                # Default to PNG
                img.save(buffer, format='PNG')
                mime_type = 'image/png'

            # Encode to base64
            img_data = buffer.getvalue()
            base64_str = base64.b64encode(img_data).decode('utf-8')

            # Return as data URI
            return f"data:{mime_type};base64,{base64_str}"

    except Exception as e:
        print(f"WARNING: Failed to encode image {image_path}: {e}")
        return None


def get_image_info(image_path: str) -> dict:
    """
    Get metadata about an image without encoding it.

    Args:
        image_path: Path to the image file

    Returns:
        Dictionary with width, height, format, size
    """
    try:
        if not Path(image_path).exists():
            return {'exists': False}

        with Image.open(image_path) as img:
            file_size = Path(image_path).stat().st_size
            return {
                'exists': True,
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode,
                'size_bytes': file_size,
                'size_kb': round(file_size / 1024, 2)
            }
    except Exception as e:
        return {'exists': False, 'error': str(e)}


def estimate_image_tokens(image_path: str, max_dimension: Optional[int] = None) -> int:
    """
    Estimate token cost for an image in GPT-4V.

    OpenAI's vision models use ~765 tokens per 512x512 image tile.
    Images are scaled to fit within 2048x2048, then divided into 512x512 tiles.

    Args:
        image_path: Path to the image file
        max_dimension: If provided, estimate after resizing

    Returns:
        Estimated token count
    """
    try:
        if not Path(image_path).exists():
            return 0

        # Without PIL, return a conservative estimate based on file size
        if not HAS_PIL:
            file_size = os.path.getsize(image_path)
            # Rough estimate: ~1 token per 500 bytes of image data
            return 85 + (file_size // 500)

        with Image.open(image_path) as img:
            width, height = img.size

            # Apply resizing if specified
            if max_dimension and (width > max_dimension or height > max_dimension):
                if width > height:
                    width = max_dimension
                    height = int(img.height * (max_dimension / img.width))
                else:
                    height = max_dimension
                    width = int(img.width * (max_dimension / img.height))

            # Scale to fit within 2048x2048 (GPT-4V limit)
            if width > 2048 or height > 2048:
                if width > height:
                    height = int(height * (2048 / width))
                    width = 2048
                else:
                    width = int(width * (2048 / height))
                    height = 2048

            # Calculate number of 512x512 tiles
            tiles_wide = (width + 511) // 512  # Ceiling division
            tiles_high = (height + 511) // 512
            num_tiles = tiles_wide * tiles_high

            # Base token cost + per-tile cost
            base_tokens = 85  # Base cost for any image
            tile_tokens = num_tiles * 170  # Cost per tile

            return base_tokens + tile_tokens

    except Exception as e:
        print(f"WARNING: Could not estimate tokens for {image_path}: {e}")
        return 500  # Conservative estimate


def filter_images_by_token_budget(
    image_paths: List[str],
    max_tokens: int,
    max_dimension: Optional[int] = None
) -> Tuple[List[str], int]:
    """
    Select images that fit within a token budget.

    Args:
        image_paths: List of image paths
        max_tokens: Maximum token budget for images
        max_dimension: Optional resize dimension

    Returns:
        Tuple of (selected_image_paths, total_estimated_tokens)
    """
    selected = []
    total_tokens = 0

    for img_path in image_paths:
        img_tokens = estimate_image_tokens(img_path, max_dimension)
        if total_tokens + img_tokens <= max_tokens:
            selected.append(img_path)
            total_tokens += img_tokens
        else:
            print(f"   Skipping {Path(img_path).name} (would exceed token budget)")
            break

    return selected, total_tokens


def validate_image_file(image_path: str, supported_formats: List[str] = None) -> bool:
    """
    Validate that an image file exists and is in a supported format.

    Args:
        image_path: Path to image file
        supported_formats: List of supported extensions (e.g., ['png', 'jpg'])

    Returns:
        True if valid, False otherwise
    """
    if supported_formats is None:
        supported_formats = ['png', 'jpg', 'jpeg', 'gif', 'webp']

    path = Path(image_path)

    # Check existence
    if not path.exists():
        return False

    # Check format
    ext = path.suffix.lower().lstrip('.')
    if ext not in supported_formats:
        print(f"WARNING: Unsupported image format: {ext} (supported: {supported_formats})")
        return False

    # Try to open it with PIL if available, otherwise just check existence (already done above)
    if HAS_PIL:
        try:
            with Image.open(image_path) as img:
                img.verify()
            return True
        except Exception as e:
            print(f"WARNING: Invalid image file {image_path}: {e}")
            return False
    else:
        # Without PIL, just verify the file exists and has correct extension
        # (existence already checked above, format already checked above)
        return True
