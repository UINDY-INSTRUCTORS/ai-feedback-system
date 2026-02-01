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
from typing import Optional, Tuple, List, Dict

# Try to import PIL, but gracefully degrade if not available
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("WARNING: PIL/Pillow not installed. Image resizing disabled.")

# Constants for payload optimization
MAX_PAYLOAD_MB = 2.5  # Conservative limit for 4MB API limit
MIN_RESOLUTION = 256  # Below this, images become illegible
MIN_QUALITY = 65  # Below this, compression artifacts become noticeable
BASE64_OVERHEAD = 1.33  # 33% size increase from base64 encoding
JSON_OVERHEAD_BYTES = 10_000  # ~10KB for JSON structure


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


def encode_image_to_jpeg(img: Image, quality: int = 85) -> bytes:
    """
    Convert any image format to JPEG bytes, handling edge cases.

    Args:
        img: PIL Image object
        quality: JPEG quality (1-100)

    Returns:
        JPEG bytes, or None if conversion fails
    """
    try:
        # Handle RGBA → RGB
        if img.mode == 'RGBA':
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])
            img = rgb_img
        # Handle CMYK → RGB
        elif img.mode == 'CMYK':
            img = img.convert('RGB')
        # Handle grayscale → RGB (for consistency)
        elif img.mode == 'L':
            img = img.convert('RGB')
        # Handle other modes
        elif img.mode not in ('RGB', '1'):
            img = img.convert('RGB')

        # Encode to JPEG
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        return buffer.getvalue()

    except Exception as e:
        print(f"WARNING: Failed to convert image to JPEG: {e}")
        return None


def estimate_jpeg_size(image_path: str, max_dimension: Optional[int] = None, quality: int = 85) -> int:
    """
    Estimate JPEG file size by actually encoding the image.

    Args:
        image_path: Path to the image file
        max_dimension: Optional max width/height (preserves aspect ratio)
        quality: JPEG quality (1-100)

    Returns:
        Estimated size in bytes (including base64 overhead)
    """
    try:
        if not Path(image_path).exists():
            return 0

        if not HAS_PIL:
            # Without PIL, return conservative estimate
            file_size = os.path.getsize(image_path)
            return int(file_size * BASE64_OVERHEAD)

        with Image.open(image_path) as img:
            # Resize if needed
            if max_dimension and (img.width > max_dimension or img.height > max_dimension):
                if img.width > img.height:
                    new_width = max_dimension
                    new_height = int(img.height * (max_dimension / img.width))
                else:
                    new_height = max_dimension
                    new_width = int(img.width * (max_dimension / img.height))
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert to JPEG and measure
            jpeg_bytes = encode_image_to_jpeg(img, quality)
            if jpeg_bytes:
                # Add base64 overhead (33%)
                return int(len(jpeg_bytes) * BASE64_OVERHEAD)
            else:
                return int(os.path.getsize(image_path) * BASE64_OVERHEAD)

    except Exception as e:
        print(f"WARNING: Could not estimate size for {image_path}: {e}")
        # Conservative estimate
        try:
            return int(os.path.getsize(image_path) * BASE64_OVERHEAD)
        except:
            return 100_000  # 100KB fallback


def estimate_total_payload_size(text_size_bytes: int, image_base64_list: List[str]) -> int:
    """
    Calculate total HTTP payload size.

    Args:
        text_size_bytes: Size of text content (including prompt)
        image_base64_list: List of base64-encoded image data URIs

    Returns:
        Total payload size in bytes
    """
    image_size = sum(len(img) for img in image_base64_list)
    return text_size_bytes + image_size + JSON_OVERHEAD_BYTES


def optimize_images_for_payload(
    image_paths: List[str],
    text_size_bytes: int,
    config: Optional[dict] = None,
    max_payload_mb: float = MAX_PAYLOAD_MB
) -> List[Dict[str, any]]:
    """
    Adaptively optimize images to fit within payload limit.

    Applies fallback sequence: Quality → Resolution → Image count
    Priority: Keep all images by reducing quality/resolution first,
    only drop images as last resort.

    Args:
        image_paths: List of image paths
        text_size_bytes: Size of text content in bytes
        config: Optional config dict with vision settings
        max_payload_mb: Maximum payload size in MB

    Returns:
        List of dicts with optimized image data:
        [
            {
                'path': str,
                'base64_data': str (data:image/jpeg;base64,...),
                'size_bytes': int,
                'resolution': int,
                'quality': int
            }
        ]
    """
    if not HAS_PIL or not image_paths:
        return []

    # Get configuration settings
    config = config or {}
    vision_config = config.get('vision', {})
    initial_resolution = vision_config.get('resize_max_dimension', 768)
    initial_quality = 85  # Default quality

    max_payload_bytes = max_payload_mb * 1024 * 1024
    available_bytes = max_payload_bytes - text_size_bytes - JSON_OVERHEAD_BYTES

    # Try different optimization levels
    optimization_steps = [
        {'quality': 85, 'resolution': initial_resolution, 'drop_count': 0, 'description': 'Initial'},
        {'quality': 75, 'resolution': initial_resolution, 'drop_count': 0, 'description': 'Quality→75'},
        {'quality': 65, 'resolution': initial_resolution, 'drop_count': 0, 'description': 'Quality→65'},
        {'quality': 65, 'resolution': 512, 'drop_count': 0, 'description': 'Resolution→512'},
        {'quality': 65, 'resolution': 384, 'drop_count': 0, 'description': 'Resolution→384'},
    ]

    # Try each optimization step, then drop images one by one
    for drop_count in range(len(image_paths)):
        images_to_try = image_paths[:len(image_paths) - drop_count]

        for step in optimization_steps:
            if step['drop_count'] != drop_count:
                step['drop_count'] = drop_count

            # Try to fit images with this configuration
            optimized_images = []
            total_size = 0

            for img_path in images_to_try:
                try:
                    with Image.open(img_path) as img:
                        # Resize if needed
                        resolution = step['resolution']
                        if img.width > resolution or img.height > resolution:
                            if img.width > img.height:
                                new_width = resolution
                                new_height = int(img.height * (resolution / img.width))
                            else:
                                new_height = resolution
                                new_width = int(img.width * (resolution / img.height))
                            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        else:
                            new_width, new_height = img.width, img.height

                        # Convert to JPEG
                        jpeg_bytes = encode_image_to_jpeg(img, step['quality'])
                        if not jpeg_bytes:
                            continue

                        # Encode to base64
                        base64_str = base64.b64encode(jpeg_bytes).decode('utf-8')
                        base64_data = f"data:image/jpeg;base64,{base64_str}"

                        size_with_overhead = len(base64_data)

                        # Check if adding this image stays under budget
                        if total_size + size_with_overhead <= available_bytes:
                            optimized_images.append({
                                'path': img_path,
                                'base64_data': base64_data,
                                'size_bytes': size_with_overhead,
                                'resolution': resolution,
                                'quality': step['quality']
                            })
                            total_size += size_with_overhead
                        # If we can't add this image with current params, stop trying for this config
                        elif optimized_images:
                            break

                except Exception as e:
                    print(f"   WARNING: Could not process {Path(img_path).name}: {e}")
                    continue

            # Check if this configuration fits all requested images
            if len(optimized_images) == len(images_to_try):
                # Success! All images fit with this configuration
                total_payload = text_size_bytes + total_size + JSON_OVERHEAD_BYTES
                final_mb = total_payload / (1024 * 1024)

                if drop_count > 0:
                    print(f"   ⚠️  Optimized: {step['description']}, {len(optimized_images)} images: {final_mb:.2f}MB")
                elif step['quality'] < 85 or step['resolution'] < initial_resolution:
                    print(f"   ⚠️  Optimized: {step['description']}: {final_mb:.2f}MB")
                else:
                    print(f"   ✅ Payload: {final_mb:.2f}MB ({len(optimized_images)} images)")

                return optimized_images

    # If we get here, nothing fit - return empty list (will gracefully degrade)
    print(f"   ❌ Cannot optimize images to fit {max_payload_mb}MB limit")
    return []


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
