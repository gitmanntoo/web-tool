import base64
import logging
from functools import lru_cache
from io import BytesIO

from cairosvg import svg2png
from magika import Magika
from PIL import Image

from library import url_util

# Initialize the Magika object for image type detection.
mgk = Magika()

# SVG conversion width and height.
SVG_WIDTH = 256
SVG_HEIGHT = 256


@lru_cache(maxsize=64)
def convert_ico(href: str, to_format: str = "PNG") -> bytes | None:
    """Convert an ICO image to another format (default PNG)

    Returns a bytes object containing the converted image.
    - If the href is not an ICO file, return None.
    """
    try:
        # Fetch the ICO file from the URL
        resp = url_util.get_url(href)
        resp.raise_for_status()

        # Check if the response is an ICO image.
        if t := resp.get_type() != "image/ico":
            logging.warning(f"Not an ICO file (magika): {href} {t}")
            return None

        # Open the ICO image
        ico_image = Image.open(BytesIO(resp.content))
        if ico_image.format != "ICO":
            logging.warning(f"Not an ICO file (pillow): {href} {ico_image.format}")
            return None

        # Convert to PNG and save in memory
        png_buffer = BytesIO()
        ico_image.save(png_buffer, format=to_format)
        return png_buffer.getvalue()
    except url_util.SerializedResponseError:
        return None


@lru_cache(maxsize=64)
def convert_svg(href: str, to_format: str = "PNG") -> bytes:
    """Convert an SVG image to another format (default PNG)

    Returns a bytes object containing the converted image.
    - If the href is not an SVG file, return None.
    """
    try:
        # Fetch the SVG file from the URL
        resp = url_util.get_url(href)
        resp.raise_for_status()

        # Check if the response is an SVG image.
        if t := resp.get_type() != "image/svg":
            logging.warning(f"Not an SVG file (magika): {href} {t}")
            return None

        # Convert to PNG and save in memory
        png_buffer = BytesIO()
        svg2png(
            bytestring=resp.content,
            write_to=png_buffer,
            output_height=SVG_HEIGHT,
            output_width=SVG_WIDTH,
        )
        return png_buffer.getvalue()
    except Exception as e:
        logging.warning(f"Not an SVG file: {href} {e}")
        return None


@lru_cache(maxsize=128)
def encode_favicon_inline(href: str, target_height: int = 20) -> str | None:
    """Encode a favicon as a base64 PNG string, resized to target height.

    Fetches the image from href, resizes to target_height preserving aspect
    ratio, and returns base64-encoded PNG data URL. Width is clamped to
    max 20x the target height to prevent huge base64 strings.

    Args:
        href: URL of the favicon image
        target_height: Target height in pixels (default: 20)

    Returns:
        Base64-encoded PNG string (with data URL prefix) or None on failure
    """
    try:
        resp = url_util.get_url(href)
        resp.raise_for_status()

        # Open the image
        img = Image.open(BytesIO(resp.content))

        # Calculate new dimensions preserving aspect ratio
        aspect_ratio = img.width / img.height
        new_height = target_height
        new_width = int(target_height * aspect_ratio)

        # Clamp width to prevent huge base64 strings from very wide images
        # Most favicons have reasonable aspect ratios; limit to 20x the height
        MAX_WIDTH = target_height * 20
        if new_width > MAX_WIDTH:
            new_width = MAX_WIDTH
            new_height = int(MAX_WIDTH / aspect_ratio)

        # Resize using high-quality resampling
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Convert to PNG and encode as base64
        png_buffer = BytesIO()
        resized.save(png_buffer, format="PNG")
        png_bytes = png_buffer.getvalue()

        # Encode as base64 with data URL prefix
        b64 = base64.b64encode(png_bytes).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        logging.warning(f"Failed to encode favicon inline: {href} {e}")
        return None
