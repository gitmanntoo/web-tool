from io import BytesIO
from dataclasses import dataclass
from functools import lru_cache
import logging

from PIL import Image
import requests
import tldextract
import urllib.parse
from urllib.parse import urljoin

from library import html_util


DEFAULT_TIMEOUT = 5
# Brave Browser
DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"


@lru_cache(maxsize=2048)
def check_url_exists(url):
    """
    Checks if a URL exists.

    Returns True if the URL exists, False otherwise.
    """

    try:
        print(f"Checking if {url} exists")
        response = requests.head(url, headers={"User-Agent": DEFAULT_USER_AGENT}, timeout=DEFAULT_TIMEOUT)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


@lru_cache(maxsize=128)
def get_url_bytes(url) -> bytes | None:
    """
    Gets the bytes of a URL. Returns None if the URL does not exist.
    """

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException:
        return None


@lru_cache(maxsize=2048)
def get_top_domain_name(url):
    """
    Given a URL, this function extracts the top-level domain (TLD) from the URL.

    Parameters:
        url (str): The URL from which to extract the TLD.

    Returns:
        str: The d

    Raises:
        None

    Example:
        >>> get_top_domain_name("https://www.example.com")
        'example.com'
    """
        
    parsed_url = urllib.parse.urlparse(url)
    subdomain = parsed_url.netloc
    extracted = tldextract.extract(subdomain)

    # Return domain name starting with www if subdomain is 'www'
    if extracted.subdomain == 'www':
        return f'{extracted.subdomain}.{extracted.domain}.{extracted.suffix}'
    else:
        return f'{extracted.domain}.{extracted.suffix}'
    

@dataclass
class ImageSize:
    width: int
    height: int


@lru_cache(maxsize=2048)
def get_image_size(url):
    """
    Gets the width and height of an image.

    Returns a named tuple with width and height if the image exists, None otherwise.
    """

    try:
        print(f"Getting image size for {url}")
        response = requests.get(url, headers={"User-Agent": DEFAULT_USER_AGENT}, timeout=DEFAULT_TIMEOUT)

        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            width, height = image.size
            return ImageSize(width, height)
    except Exception as e:
        # Any exceptions are ignored.
        logging.warning(e)
        pass

    return None


@lru_cache(maxsize=2048)
def get_url_root(url: str) -> str:
    """
    Returns the root URL of the given URL consisting of the scheme, netloc, and first part of path.
    """
    # Parse the URL.
    parsed_url = urllib.parse.urlparse(url)

    # Extract the scheme, netloc, and first part of the path.
    path_part = parsed_url.path
    if path_part.startswith("/"):
        path_part = path_part[1:]
    if len(path_part) > 0:
        path_part = path_part.split("/")[0]

    root_url = urllib.parse.urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            path_part,
            "",
            "",
            "",
        )
    )
    return str(root_url)


@lru_cache(maxsize=2048)
def get_url_host(url: str) -> str:
    """
    Returns the root URL of the given URL consisting of the scheme, netloc.
    """
    # Parse the URL.
    parsed_url = urllib.parse.urlparse(url)

    # Extract the scheme, netloc, and first part of the path.
    host_url = urllib.parse.urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            "",
            "",
            "",
            "",
        )
    )
    return str(host_url)


def sort_favicon_links(
    favicons: list[html_util.RelLink], 
    include: str = None
) -> list[html_util.RelLink]:
    """
    Sort favicon links by size descending. If the first item is from the cache,
    it will remain first.
    """

    if len(favicons) == 0:
        # Empty list, nothing to do.
        return favicons

    # If the first favicon has a cacheKey, set it aside.
    cache_favicon = None
    if favicons and favicons[0].cache_key:
        if include != "all":
            # Return cache immediately.
            return favicons[:1]

        cache_favicon = favicons[0]
        favicons = favicons[1:]

    # Get the size of each favicon.
    for favicon in favicons:
        if size := get_image_size(favicon.href):
            favicon.width = size.width
            favicon.height = size.height

    # Sort favicons by area descending.
    favicons.sort(key=lambda x: x.width * x.height, reverse=True)

    # Add back the cached favicon at the start.
    if cache_favicon:
        if size := get_image_size(cache_favicon.href):
            cache_favicon.width = size.width
            cache_favicon.height = size.height
        favicons.insert(0, cache_favicon)

    if include == "all":
        return favicons

    # Return the first favicon.
    return favicons[:1]


@lru_cache(maxsize=2048)
def make_absolute_urls(page_url, linked_url):
    """Convert relative URLs to absolute URLs."""

    # If the URL is already absolute, return it as is.
    if linked_url.startswith('http://') or linked_url.startswith('https://'):
        return linked_url
    else:
        return str(urljoin(page_url, linked_url))


