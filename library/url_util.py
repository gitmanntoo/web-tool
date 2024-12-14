from io import BytesIO
from dataclasses import dataclass
from functools import lru_cache
import logging
import time

from flask import request
from magika import Magika
from PIL import Image
import requests
import tldextract
import urllib.parse
from urllib.parse import urljoin

from library import url_util

DEFAULT_TIMEOUT = 5

# Brave Browser
DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

# Initialize Magika for response type detection.
mgk = Magika()


def get_user_agent() -> str:
    """
    Gets the user agent from the request. If that does not work, uses the default user agent.
    """
    try:
        return request.user_agent.string
    except Exception:
        return DEFAULT_USER_AGENT


class SerializedResponseError(Exception):
    """SerializedResponseError is raised when a SerializedResponse object has the error attribute set."""
    pass


@dataclass
class SerializedResponse:
    """SerializedResponse is a wrapper around a requests.Response."""

    # Source URL.
    source_url: str

    # Parmaeters from requests.Response object.
    resolved_url: str = None
    status_code: int = None
    status_reason: str = None

    headers: dict = None
    cookies: dict = None
    content: bytes = None
    encoding: str = None
    
    # Common headers.
    content_type: str = None
    content_length: int = None

    # Results from Magika.
    m_group: str = None
    m_label: str = None
    m_mime_type: str = None

    # Size for images.
    image_width: int = None
    image_height: int = None

    # Exception if request failed.
    error: str = None

    def from_response(self, resp: requests.Response) -> "SerializedResponse":
        """Initialize from a requests.Response object."""
        self.resolved_url = resp.url
        self.status_code = resp.status_code
        self.status_reason = resp.reason

        self.headers = dict(resp.headers)
        self.cookies = resp.cookies.get_dict()
        self.content = bytes(resp.content)
        self.encoding = resp.encoding

        self.content_type = resp.headers.get("Content-Type")
        self.content_length = resp.headers.get("Content-Length")

        # Run Magika if response has content.
        if self.content:
            try:
                if m := mgk.identify_bytes(self.content):
                    self.m_group = m.output.group
                    self.m_label = m.output.ct_label
                    self.m_mime_type = m.output.mime_type
            except Exception as e:
                self.error = str(e)

        # Get image size.
        if s := self.image_size():
            self.image_width = s[0]
            self.image_height = s[1]

        logging.debug(f"SerializedResponse: {self.as_dict()}")
        return self

    def get_text(self) -> str:
        """Returns the response data as a string."""
        return self.data.decode()

    def as_dict(self) -> dict:
        """Returns the response as a dictionary without the data."""
        out = {"source_url": self.source_url}

        if self.error:
            out["error"] = self.error

        if self.resolved_url:
            out["resolved_url"] = self.resolved_url
            out["status_code"] =  self.status_code
            out["headers"] =  self.headers
            out["content_type"] =  self.content_type
            out["content_length"] =  self.content_length

        if self.m_group:
            out["m_group"] = self.m_group
            out["m_label"] = self.m_label
            out["m_mime_type"] = self.m_mime_type

        if self.image_width is not None:
            out["image_width"] = self.image_width
            out["image_height"] = self.image_height

        return out

    def get_type(self) -> str:
        """Returns the response type as a string."""

        # Use Magika if available.
        if self.m_group:
            return f"{self.m_group}/{self.m_label}"

        # Otherwise, use the content type from the response.
        return self.content_type

    def image_size(self) -> tuple[int, int] | None:
        """Returns the image size as a tuple of (width, height).

        Returns None if the response is not an image.
        """

        # Check if the response is an image.
        if self.m_group and self.m_group != "image":
            return None

        if self.m_label == "svg":
            # SVG has no size since it is a vector image.
            return (0, 0)

        # Convert content into an image and return the size.
        try:
            img = Image.open(BytesIO(self.content))
            return img.size
        except Exception as e:
            logging.warning(e)
            return None

    def raise_for_status(self) -> None:
        """Raises an exception if the error attribute is set."""
        if self.error:
            raise SerializedResponseError(self.error)


@lru_cache(maxsize=64)
def get_url(url: str) -> SerializedResponse | None:
    """
    Gets a URL. Returns None if the URL does not exist.
    """
    logging.info(f"get_url START: {url}")
    start_time = time.time()

    out = SerializedResponse(source_url=url)
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": get_user_agent()},
            timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        out.from_response(resp)
    except requests.exceptions.RequestException as e:
        out.error = str(e)

    logging.info(f"get_url END: {time.time() - start_time:.3f}s {url}")
    return out


@lru_cache(maxsize=64)
def check_url_exists(url: str) -> bool:
    """
    Checks if a URL exists.

    Returns True if the URL exists, False otherwise.
    """

    resp = get_url(url)
    return resp.status_code == 200


def get_url_bytes(url: str) -> bytes | None:
    """
    Gets the bytes of a URL. Returns None if the URL does not exist.
    """

    resp = get_url(url)
    return resp.content


@lru_cache(maxsize=64)
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
    image_type: str


@lru_cache(maxsize=64)
def get_image_size(url):
    """
    Gets the width and height of an image.

    Returns a named tuple with width and height if the image exists, None otherwise.
    """

    try:
        print(f"Getting image size for {url}")
        resp = url_util.get_url(url)
        if resp.status_code == 200:
            return ImageSize(
                resp.image_width,
                resp.image_height,
                resp.get_type())
    except Exception as e:
        # Any exceptions are ignored.
        logging.warning(e)
        pass

    return None


@lru_cache(maxsize=64)
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


@lru_cache(maxsize=64)
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


@lru_cache(maxsize=64)
def make_absolute_urls(page_url, linked_url):
    """Convert relative URLs to absolute URLs."""

    # If the URL is already absolute, return it as is.
    if linked_url.startswith('http://') or linked_url.startswith('https://'):
        return linked_url
    else:
        return str(urljoin(page_url, linked_url))


