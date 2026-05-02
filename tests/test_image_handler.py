"""Tests for src/image_handler.py."""

from io import BytesIO
from unittest.mock import MagicMock, patch

from PIL import Image

from src.image_handler import (
    create_image_collage,
    download_image,
    load_user_image,
)


def _make_image(width: int = 640, height: int = 360, color=(200, 100, 50)) -> Image.Image:
    return Image.new("RGB", (width, height), color=color)


def _image_to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    buf = BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# load_user_image
# ---------------------------------------------------------------------------

def test_load_user_image_valid_png():
    buf = BytesIO(_image_to_bytes(_make_image(100, 100)))
    result = load_user_image(buf)
    assert result is not None
    assert result.mode == "RGB"


def test_load_user_image_valid_jpeg():
    buf = BytesIO(_image_to_bytes(_make_image(200, 150), fmt="JPEG"))
    result = load_user_image(buf)
    assert result is not None
    assert result.mode == "RGB"


def test_load_user_image_invalid_bytes():
    buf = BytesIO(b"not an image at all")
    result = load_user_image(buf)
    assert result is None


# ---------------------------------------------------------------------------
# download_image
# ---------------------------------------------------------------------------

@patch("src.image_handler.requests.get")
def test_download_image_success(mock_get):
    img_bytes = _image_to_bytes(_make_image(320, 180), fmt="JPEG")
    mock_response = MagicMock()
    mock_response.content = img_bytes
    mock_get.return_value = mock_response

    result = download_image("https://example.com/shot.jpg")
    assert result is not None
    assert result.mode == "RGB"


@patch("src.image_handler.requests.get")
def test_download_image_network_error(mock_get):
    mock_get.side_effect = Exception("network failure")

    result = download_image("https://example.com/bad.jpg")
    assert result is None


@patch("src.image_handler.requests.get")
def test_download_image_bad_content(mock_get):
    mock_response = MagicMock()
    mock_response.content = b"garbage bytes"
    mock_get.return_value = mock_response

    result = download_image("https://example.com/corrupt.jpg")
    assert result is None


# ---------------------------------------------------------------------------
# create_image_collage
# ---------------------------------------------------------------------------

def test_create_image_collage_empty_returns_none():
    assert create_image_collage([]) is None


def test_create_image_collage_single_image():
    collage = create_image_collage([_make_image()])
    assert collage is not None
    assert collage.width == 1200
    assert collage.mode == "RGB"


def test_create_image_collage_two_images():
    images = [_make_image(color=c) for c in [(255, 0, 0), (0, 255, 0)]]
    collage = create_image_collage(images)
    assert collage is not None
    assert collage.width == 1200


def test_create_image_collage_four_images():
    images = [_make_image() for _ in range(4)]
    collage = create_image_collage(images, max_images=4)
    assert collage is not None
    assert collage.width == 1200


def test_create_image_collage_respects_max_images():
    images = [_make_image() for _ in range(10)]
    # With max_images=2 only 2 thumbnails should fit in 1 row
    collage = create_image_collage(images, max_images=2)
    assert collage is not None
    # 2 images in one row → height should be smaller than a 2-row layout
    collage_4 = create_image_collage(images, max_images=4)
    assert collage.height <= collage_4.height


def test_create_image_collage_custom_width():
    collage = create_image_collage([_make_image()], target_width=800)
    assert collage is not None
    assert collage.width == 800
