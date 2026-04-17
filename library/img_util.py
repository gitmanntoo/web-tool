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
        if (t := resp.get_type()) != "image/ico":
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
def convert_svg(href: str, to_format: str = "PNG") -> bytes | None:
    """Convert an SVG image to another format (default PNG)

    Returns a bytes object containing the converted image.
    - If the href is not an SVG file, return None.
    """
    try:
        # Fetch the SVG file from the URL
        resp = url_util.get_url(href)
        resp.raise_for_status()

        # Check if the response is an SVG image.
        if (t := resp.get_type()) != "image/svg":
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


def _resize_image(img: Image.Image, target_height: int) -> tuple[Image.Image, int, int]:
    """Resize an image to target_height preserving aspect ratio.

    Width is clamped to max 20x the target height to prevent huge base64
    strings from very wide images.

    Returns:
        Tuple of (resized_image, width, height)
    """
    if target_height < 1:
        raise ValueError(f"target_height must be >= 1, got {target_height}")
    aspect_ratio = img.width / img.height
    new_height = target_height
    new_width = int(target_height * aspect_ratio)

    max_width = target_height * 20
    if new_width > max_width:
        new_width = max_width
        new_height = int(max_width / aspect_ratio)

    # Clamp to at least 1 to prevent Pillow raising on non-positive dimensions.
    new_width = max(1, new_width)
    new_height = max(1, new_height)

    return img.resize((new_width, new_height), Image.Resampling.LANCZOS), new_width, new_height


def encode_image_inline(image_bytes: bytes, target_height: int = 20) -> dict | None:
    """Encode raw image bytes as a base64 PNG string, resized to target height.

    Detects the image type using Magika, opens with Pillow, resizes to
    target_height preserving aspect ratio (width clamped to 20x target_height
    to prevent huge base64 strings), and returns a base64-encoded PNG data URL.

    Args:
        image_bytes: Raw bytes of the image file
        target_height: Target height in pixels (default: 20)

    Returns:
        Dict with keys "data_url", "width", "height" or None on failure
    """
    try:
        # Detect image type
        result = mgk.identify_bytes(image_bytes)
        image_type = result.output.label
        logging.debug(f"encode_image_inline: detected type={image_type}")

        # Handle SVG — convert to PNG first
        if image_type == "image/svg":
            png_buffer = BytesIO()
            svg2png(
                bytestring=image_bytes,
                write_to=png_buffer,
                output_height=SVG_HEIGHT,
                output_width=SVG_WIDTH,
            )
            image_bytes = png_buffer.getvalue()
            image_type = "image/png"

        # Check dimensions before loading into Pillow
        temp_img = Image.open(BytesIO(image_bytes))
        if temp_img.width > 2000 or temp_img.height > 2000:
            logging.warning(
                f"encode_image_inline: image too large {temp_img.width}x{temp_img.height}"
            )
            return None

        # Open the image
        img = Image.open(BytesIO(image_bytes))

        # Resize preserving aspect ratio
        resized, width, height = _resize_image(img, target_height)

        # Convert to PNG and encode as base64
        png_buffer = BytesIO()
        resized.save(png_buffer, format="PNG")
        png_bytes = png_buffer.getvalue()

        b64 = base64.b64encode(png_bytes).decode("ascii")
        return {"data_url": f"data:image/png;base64,{b64}", "width": width, "height": height}
    except Exception as e:
        logging.warning(f"Failed to encode image inline: {e}")
        return None


@lru_cache(maxsize=128)
def encode_favicon_inline(href: str, target_height: int = 20) -> dict | None:
    """Encode a favicon as a base64 PNG string, resized to target height.

    Fetches the image from href, resizes to target_height preserving aspect
    ratio, and returns base64-encoded PNG data URL. Width is clamped to
    max 20x the target height to prevent huge base64 strings.

    Args:
        href: URL of the favicon image
        target_height: Target height in pixels (default: 20)

    Returns:
        Dict with keys "data_url", "width", "height" or None on failure
    """
    try:
        resp = url_util.get_url(href)
        resp.raise_for_status()

        return encode_image_inline(resp.content, target_height)
    except Exception as e:
        logging.warning(f"Failed to encode favicon inline: {href} {e}")
        return None
