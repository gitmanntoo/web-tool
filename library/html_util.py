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
    "favicon.png",
    "favicon.jpg",
    "favicon.gif",
    "favicon.ico",
    "favicon.svg",
]


@dataclass
class RelLink:
    href: str
    cache_key: str = None
    rel: str = None
    sizes: str = None

    resolved_href: str = None
    height: int = 0
    width: int = 0
    image_type: str = None

    def __post_init__(self):
        """Fetch the href and get image details if it is an image."""
        resp = url_util.get_url(self.href)
        self.resolved_href = resp.resolved_url

        if resp.image_width is not None:
            self.image_type = resp.get_type()
            self.width = resp.image_width
            self.height = resp.image_height

    def is_valid(self) -> bool:
        """Return True if the link is valid."""
        return self.resolved_href is not None and self.image_type is not None


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


def get_page_metadata(
    meta: PageMetadata = None,
    max_favicon_links: int = 1,
    favicon_width: int = FAVICON_WIDTH
) -> PageMetadata:
    """Add metadata to PageMetadata object."""

    if meta is None:
        # Get metadata from rueqest parameters.
        meta = PageMetadata(
            title=request.args.get("title", ""),
            url=request.args.get("url", ""),
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
    meta.clean_url = urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

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
    meta.favicons = url_util.sort_favicon_links(
        favicon_links, max_favicon_links, favicon_width)

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
            r = RelLink(favicon, cache_key=s)
            if r.is_valid():
                return r

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
                    r = RelLink(
                        href,
                        rel=rel,
                        sizes=sizes,
                    )
                    if r.is_valid():
                        links.append(r)
                        if include != "all":
                            return links

                        # Wrap .ico and .svg links in a conversion service.
                        if img_util.convert_ico(href) is not None:
                            params = urlencode({"url": href})
                            href = f"http://{request.host}/{ICO_TO_PNG_PATH}?{params}"
                            r = RelLink(
                                href,
                                rel=rel,
                                sizes=sizes,
                            )
                            if r.is_valid():
                                links.append(r)
                        elif img_util.convert_svg(href) is not None:
                            params = urlencode({"url": href})
                            href = f"http://{request.host}/{SVG_TO_PNG_PATH}?{params}"
                            r = RelLink(
                                href,
                                rel=rel,
                                sizes=sizes,
                            )
                            if r.is_valid():
                                links.append(r)

                    break

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
            r = RelLink(href)
            if r.is_valid():
                links.append(r)
                if include != "all":
                    return links

                # Wrap .ico and .svg links in a conversion service.
                if img_util.convert_ico(href) is not None:
                    params = urlencode({"url": href})
                    href = f"http://{request.host}/{ICO_TO_PNG_PATH}?{params}"
                    r = RelLink(href)
                    if r.is_valid():
                        links.append(r)
                elif img_util.convert_svg(href) is not None:
                    params = urlencode({"url": href})
                    href = f"http://{request.host}/{SVG_TO_PNG_PATH}?{params}"
                    r = RelLink(href)
                    if r.is_valid():
                        links.append(r)

    # No favicon links found.
    return links


def get_common_favicon_links(page_url):
    """Get the common favicon links for the page URL."""

    # Build links for the common favicon files.
    links = []
    for f in COMMON_FAVICON_FILES:
        links.append(RelLink(url_util.make_absolute_urls(page_url, f)))

    return links


def sort_favicon_links(
    favicons: list[RelLink], 
    include: str = None
) -> list[RelLink]:
    """Sort favicons to get the largest one with ICO, SVG and conversions last.

    Order of precedence (higher is first):
    999. Cached favicon
    500. Images except for ICO and SVG.
    400. ICO
    300. SVG
    200. ICO conversion
    100. SVG conversion
    """

    if len(favicons) == 0:
        return favicons

    # If the first favicon has a cacheKey, return it immediately.
    if favicons and favicons[0].cache_key:
        if include != "all":
            # Return cache immediately.
            return favicons[:1]
        
    key_precedence = {
        "cache": 999,
        "image": 500,
        "ico": 400,
        "svg": 300,
        "ico-conversion": 200,
        "svg-conversion": 100,
    }

    # Define a key function that returns the sorting key.
    def key_fn(x: RelLink):
        if x.cache_key:
            group_key = key_precedence["cache"]
        elif SVG_TO_PNG_PATH in x.href:
            # SVG conversion
            group_key = key_precedence["svg-conversion"]
        elif ICO_TO_PNG_PATH in x.href:
            # ICO conversion
            group_key = key_precedence["ico-conversion"]
        elif x.image_type == "image/svg":
            # SVG image type
            group_key = key_precedence["svg"]
        elif x.image_type == "image/ico":
            # ICO image type
            group_key = key_precedence["ico"]
        else:
            # All other image types
            group_key = key_precedence["image"]

        # Calculate the area of the image.
        a = 0
        if x.width is not None:
            a = x.width * x.height

        return f"{group_key:03d}_{a}"

    return sorted(favicons, key=lambda x: key_fn(x), reverse=True)
