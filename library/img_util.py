from io import BytesIO

from PIL import Image
import requests


def convert_image(href: str, to_format: str) -> bytes:
    try:
        # Fetch the ICO file from the URL
        response = requests.get(href)
        response.raise_for_status()  # Raise an error for bad responses

        # Open the ICO image
        ico_image = Image.open(BytesIO(response.content))

        # Convert to PNG and save in memory
        png_buffer = BytesIO()
        ico_image.save(png_buffer, format=to_format)
        return png_buffer.getvalue()
    except Exception:
        return None
