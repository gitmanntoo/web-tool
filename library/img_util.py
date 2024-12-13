from io import BytesIO
from functools import lru_cache

from cairosvg import svg2png
from magika import Magika
from PIL import Image
import requests

# Initialize the Magika object for image type detection.
mgk = Magika()


@lru_cache(maxsize=128)
def convert_ico(href: str, to_format: str = "PNG") -> bytes | None:
    """Convert an ICO image to another format (default PNG)

    Returns a bytes object containing the converted image.
    - If the href is not an ICO file, return None.
    """
    if not href.lower().endswith(".ico"):
        return None

    try:
        # Fetch the ICO file from the URL
        response = requests.get(href)
        response.raise_for_status()  # Raise an error for bad responses

        # Open the ICO image
        ico_image = Image.open(BytesIO(response.content))
        if ico_image.format != "ICO":
            print(f"Not an ICO file: {href} {ico_image.format}")
            return None

        # Convert to PNG and save in memory
        png_buffer = BytesIO()
        ico_image.save(png_buffer, format=to_format)
        return png_buffer.getvalue()
    except Exception:
        return None


@lru_cache(maxsize=128)
def convert_svg(href: str, to_format: str = 'PNG') -> bytes:
    """Convert an SVG image to another format (default PNG)

    Returns a bytes object containing the converted image.
    - If the href is not an SVG file, return None.
    """
    if not href.lower().endswith(".svg"):
        return None

    try:
        # Fetch the SVG file from the URL
        response = requests.get(href)
        response.raise_for_status()  # Raise an error for bad responses

        # Use Magika to identify the content directly
        m = mgk.identify_bytes(response.content)
        if m.output.ct_label != 'svg':
            raise Exception(f"file type is {m.output.group}/{m.output.ct_label}")

        # Convert to PNG and save in memory
        png_buffer = BytesIO()
        svg2png(bytestring=response.content, write_to=png_buffer)
        return png_buffer.getvalue()
    except Exception as e:
        print(f"Not an SVG file: {href} {e}")
        return None


def get_image_type(image: Image) -> str:
    """
    Get the image type from the image bytes.
    """
    try:
        return image.format
    except Exception:
        return "unknown image type"
