from io import BytesIO
from functools import lru_cache
import logging

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
def convert_svg(href: str, to_format: str = 'PNG') -> bytes:
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
