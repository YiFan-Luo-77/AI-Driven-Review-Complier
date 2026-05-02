"""Utilities for downloading, loading, and compositing game screenshots."""

from io import BytesIO
from typing import Any, List, Optional

import requests
from PIL import Image

# Default collage dimensions
_COLLAGE_WIDTH = 1200
_COLLAGE_PADDING = 10
_ASPECT_RATIO = 9 / 16  # height / width for 16:9 thumbnails


def download_image(url: str) -> Optional[Image.Image]:
    """Download an image from *url* and return it as a PIL ``Image``.

    Args:
        url: HTTP(S) URL of the image.

    Returns:
        RGB PIL Image, or *None* if the download or decoding fails.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGB")
    except Exception:
        return None


def load_user_image(file_obj: Any) -> Optional[Image.Image]:
    """Load an image from a file-like object (e.g. a Streamlit ``UploadedFile``).

    Args:
        file_obj: Any file-like object readable by :func:`PIL.Image.open`.

    Returns:
        RGB PIL Image, or *None* if loading or decoding fails.
    """
    try:
        return Image.open(file_obj).convert("RGB")
    except Exception:
        return None


def create_image_collage(
    images: List[Image.Image],
    max_images: int = 4,
    target_width: int = _COLLAGE_WIDTH,
    padding: int = _COLLAGE_PADDING,
) -> Optional[Image.Image]:
    """Arrange up to *max_images* images into a two-column grid collage.

    Args:
        images: List of PIL Images to include.
        max_images: Maximum number of images to use (extras are ignored).
        target_width: Total pixel width of the output canvas.
        padding: Pixel gap between images and around the border.

    Returns:
        Composited RGB PIL Image, or *None* if *images* is empty.
    """
    if not images:
        return None

    images = images[:max_images]
    count = len(images)

    cols = min(2, count)
    rows = (count + cols - 1) // cols

    thumb_width = (target_width - padding * (cols + 1)) // cols
    thumb_height = int(thumb_width * _ASPECT_RATIO)

    canvas_width = target_width
    canvas_height = thumb_height * rows + padding * (rows + 1)

    canvas = Image.new("RGB", (canvas_width, canvas_height), color=(30, 30, 30))

    for idx, img in enumerate(images):
        img_resized = img.resize((thumb_width, thumb_height), Image.LANCZOS)
        row = idx // cols
        col = idx % cols
        x = padding + col * (thumb_width + padding)
        y = padding + row * (thumb_height + padding)
        canvas.paste(img_resized, (x, y))

    return canvas
