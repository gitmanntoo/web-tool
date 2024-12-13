from dataclasses import dataclass, field
import json
from pathlib import Path
from urllib.parse import urlparse, urlunparse, urlencode

from bs4 import BeautifulSoup
from flask import request
import pyperclip
import yaml

from library import docker_util
from library import img_util
from library import url_util

FAVICON_WIDTH = 20

# Static favicon mapping distributed with the web-tool.
FAVICON_CACHE = Path("static/favicon.yml")

# Local cache of favicon mappings and images.
if docker_util.is_running_in_container():
    # If running in a container, use a file in /data.
    FAVICON_LOCAL_PARENT = Path("/data")
else:
    # If running locally, use a file in the working directory.
    FAVICON_LOCAL_PARENT = Path("local-cache")

FAVICON_LOCAL_PARENT.mkdir(exist_ok=True, parents=True)
FAVICON_LOCAL_CACHE = FAVICON_LOCAL_PARENT / "favicon.yml"

ICO_TO_PNG_PATH = "convert-ico-to-png"
SVG_TO_PNG_PATH = "convert-svg-to-png"

# List of link rel values for favicons.
FAVICON_REL = [
    "icon",
    "apple-touch-icon",
    "shortcut icon",
]

COMMON_FAVICON_FILES = [
    "favicon.ico",
    "favicon.png",
    "favicon.svg",
    "favicon.jpg",
    "favicon.gif",
]


@dataclass
class RelLink:
    href: str
    rel: str = None
    sizes: str = None
    height: int = 0
    width: int = 0
    image_type: str = ""
    cache_key: str = None

    def __post_init__(self):
        if self.sizes:
            size_parts = self.sizes.split('x')
            if len(size_parts) == 2:
                self.width = int(size_parts[0])
                self.height = int(size_parts[1])


@dataclass
class PageMetadata:
    # Passed in parameters
    title: str
    url: str
    html: str = None
    # Derived values.
    clean_url: str = None
    host_url: str = None
    host: str = None
    favicons: list[RelLink] = field(default_factory=list)
    error: str = None


def get_page_metadata(meta: PageMetadata = None, max_favicon_links: int=1, favicon_width: int=FAVICON_WIDTH) -> PageMetadata:
    """Add metadata to PageMetadata object."""

    if meta is None:
        # Get metadata from rueqest parameters.
        meta = PageMetadata(
            title=request.args.get("title",""),
            url=request.args.get("url",""),
        )

        # Read clipboard contents.
        clip = pyperclip.paste()

        # If contents are not valid JSON, return plain text.
        try:
            clip_json = json.loads(clip)
            meta.html = clip_json.get("html", "")
        except json.JSONDecodeError as e:
            meta.error = str(e)

    # Reconstruct the URL without the query and fragment.
    parsed = urlparse(meta.url)
    meta.clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

    # Get the host from the URL
    meta.host_url = f'{parsed.scheme}://{parsed.netloc}'
    meta.host = parsed.netloc

    # If an error occurred, do not attempt to parse the HTML.
    if meta.error is not None:
        return meta

    # Prettify HTML
    if meta.html:
        soup = BeautifulSoup(meta.html, 'html.parser')
        meta.html = soup.prettify()

    # Extract favicon links from the HTML page in descending order by size.
    favicon_links = get_favicon_links(meta.url, meta.html)
    meta.favicons =url_util.sort_favicon_links(favicon_links, max_favicon_links, favicon_width)

    return meta


def get_favicon_cache(page_url) -> RelLink:
    """Get the favicon cache for the page URL.

    Returns:
        dict: A dictionary of favicon links, keyed by the URL of the page.
    """

    cache = {}

    # Load the cache each time to ensure it is up to date.
    if FAVICON_CACHE.exists():
        with open(FAVICON_CACHE, "r") as f:
            tmp = yaml.safe_load(f)
            if isinstance(tmp, dict):
                cache.update(tmp)

    if FAVICON_LOCAL_CACHE.exists():
        with open(FAVICON_LOCAL_CACHE, "r") as f:
            tmp = yaml.safe_load(f)
            if isinstance(tmp, dict):
                cache.update(tmp)

    # Search for matches from url_root to top level domain.
    search_paths = []
    parsed = urlparse(page_url)

    # Get the first part of the path.
    path_part = parsed.path
    if path_part.startswith("/"):
        path_part = path_part[1:]
    if len(path_part) > 0:
        path_part = path_part.split("/")[0]
        search_paths.append(f"{parsed.netloc}/{path_part}")

    # Split the netloc into parts and add paths until there are just two parts.
    tokens = parsed.netloc.split(".")
    while len(tokens) > 1:
        search_paths.append(".".join(tokens))
        tokens.pop(0)

    for s in search_paths:
        print(f"favicon cache search: {s}")
        if favicon := cache.get(s):
            return RelLink(href=favicon,  cache_key=s)

    return None


def add_favicon_to_cache(cache_key, favicon_link):
    """Add the favicon link to the cache."""
    cache = {}

    if FAVICON_LOCAL_CACHE.exists():
        with open(FAVICON_LOCAL_CACHE, "r") as f:
            tmp = yaml.safe_load(f)
            if isinstance(tmp, dict):
                cache.update(tmp)

    if cache_key.startswith("www."):
        cache_key = cache_key.replace("www.", "")

    cache[cache_key] = favicon_link

    # Write cache in sorted order.
    with open(FAVICON_LOCAL_CACHE, "w") as f:
        yaml.dump(cache, f, sort_keys=True)


def get_favicon_links(page_url, html_string, include=None):
    """Get the favicon links for the page URL."""

    # Keep track of href already seen.
    seen = set()

    links = []

    if cached_url := get_favicon_cache(page_url):
        links.append(cached_url)
        if include != 'all':
            return links
        seen.add(cached_url.href)

    soup = BeautifulSoup(html_string, 'html.parser')
    head = soup.find('head')

    # Try to find links in <head>.
    if head:
        for link in head.find_all('link'):
            href = link.get('href')
            if not href:
                continue

            href = str(url_util.make_absolute_urls(page_url, href))
            if href in seen:
                continue
            seen.add(href)

            sizes = link.get('sizes')
            rel = link.get('rel')

            # Make sure rel is a list.
            if not isinstance(rel, list):
                rel = [rel]

            for r in rel:
                if r in FAVICON_REL and url_util.check_url_exists(href):
                    links.append(RelLink(href, rel, sizes))

                    # Wrap .ico and .svg links in a conversion service.
                    if img_util.convert_ico(href) is not None:
                        params = {"url": href}
                        href = f"http://{request.host}/{ICO_TO_PNG_PATH}?{urlencode(params)}"
                        links.append(RelLink(href, rel, sizes))
                    elif img_util.convert_svg(href) is not None:
                        params = {"url": href}
                        href = f"http://{request.host}/{SVG_TO_PNG_PATH}?{urlencode(params)}"
                        links.append(RelLink(href, rel, sizes))

                    break

        if links and include != "all":
            return links

    # Fallback to common favicon files.
    parsed = urlparse(page_url)
    page_host = urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))

    for f in COMMON_FAVICON_FILES:
        # Check if the file exists.
        href = url_util.make_absolute_urls(page_host, f)
        if href in seen:
            continue
        seen.add(href)

        if url_util.check_url_exists(href):
            links.append(RelLink(href))

            # Wrap .ico and .svg links in a conversion service.
            if img_util.convert_ico(href) is not None:
                params = {"url": href}
                href = f"http://{request.host}/{ICO_TO_PNG_PATH}?{urlencode(params)}"
                links.append(RelLink(href, rel, sizes))
            elif img_util.convert_svg(href) is not None:
                params = {"url": href}
                href = f"http://{request.host}/{SVG_TO_PNG_PATH}?{urlencode(params)}"
                links.append(RelLink(href, rel, sizes))

            if include != "all":
                return links

    # No favicon links found.
    return links


def get_common_favicon_links(page_url):
    """Get the common favicon links for the page URL."""

    # Build links for the common favicon files.
    links = []
    for f in COMMON_FAVICON_FILES:
        links.append(RelLink(url_util.make_absolute_urls(page_url, f)))

    return links
