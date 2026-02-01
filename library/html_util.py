from dataclasses import dataclass, field
import json
from pathlib import Path
import time
from urllib.parse import urlparse, urlunparse, urlencode

from bs4 import BeautifulSoup
from flask import request
import pyperclip
import yaml

from library import docker_util
from library import img_util
from library import url_util

FAVICON_WIDTH = 20

# Three-tier favicon cache system:
# 1. User overrides (highest priority) - manual customizations
FAVICON_OVERRIDES = Path("static/favicon-overrides.yml")
# 2. App defaults (medium priority) - curated defaults distributed with app
FAVICON_DEFAULTS = Path("static/favicon.yml")
# 3. Auto-discovered cache (lowest priority) - dynamically discovered favicons

# Local cache of favicon mappings and images.
if docker_util.is_running_in_container():
    # If running in a container, use a file in /data.
    FAVICON_LOCAL_PARENT = Path("/data")
else:
    # If running locally, use a file in the working directory.
    FAVICON_LOCAL_PARENT = Path("local-cache")

FAVICON_LOCAL_PARENT.mkdir(exist_ok=True, parents=True)
FAVICON_LOCAL_CACHE = FAVICON_LOCAL_PARENT / "favicon.yml"

# In-memory cache for YAML files with mtime tracking
# Structure: {file_path: {'data': dict, 'mtime': float, 'loaded_at': float}}
_favicon_yaml_cache = {}
FAVICON_CACHE_TTL = 5  # seconds

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
    _validated: bool = False

    def validate(self) -> bool:
        """Lazily fetch the href and get image details.
        
        Returns True if valid, False otherwise.
        Only makes HTTP request on first call.
        """
        if self._validated:
            return self.is_valid()
        
        self._validated = True
        
        try:
            resp = url_util.get_url(self.href)
            self.resolved_href = resp.resolved_url

            if resp.image_width is not None:
                self.image_type = resp.get_type()
                self.width = resp.image_width
                self.height = resp.image_height
                return True
        except Exception:
            pass
        
        return False

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

    # Extract favicon links from the HTML page sorted by optimal size.
    favicon_links = get_favicon_links(meta.url, meta.html)
    sorted_links = sort_favicon_links(
        favicon_links, favicon_width, max_favicon_links)
    
    # Validate only the top candidates (lazy validation)
    meta.favicons = validate_top_candidates(sorted_links, max_count=max_favicon_links)

    return meta


def _load_yaml_with_cache(file_path: Path) -> dict:
    """Load YAML file with in-memory caching, mtime check, and TTL.
    
    Cache is invalidated if:
    - File modification time (mtime) has changed
    - TTL has expired
    
    Args:
        file_path: Path to YAML file
        
    Returns:
        dict: Loaded YAML data, or empty dict if file doesn't exist
    """
    if not file_path.exists():
        return {}
    
    current_time = time.time()
    file_path_str = str(file_path)
    
    # Get current file mtime
    try:
        current_mtime = file_path.stat().st_mtime
    except OSError:
        return {}
    
    # Check if we have a cached version
    if file_path_str in _favicon_yaml_cache:
        cached = _favicon_yaml_cache[file_path_str]
        cached_mtime = cached.get('mtime', 0)
        loaded_at = cached.get('loaded_at', 0)
        
        # Check if cache is still valid (mtime unchanged and TTL not expired)
        if (cached_mtime == current_mtime and 
            current_time - loaded_at < FAVICON_CACHE_TTL):
            return cached.get('data', {})
    
    # Load fresh data
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
            if not isinstance(data, dict):
                data = {}
    except Exception:
        data = {}
    
    # Update cache
    _favicon_yaml_cache[file_path_str] = {
        'data': data,
        'mtime': current_mtime,
        'loaded_at': current_time
    }
    
    return data


def get_favicon_cache(page_url) -> RelLink:
    """Get the favicon cache for the page URL.
    
    Searches three-tier cache with precedence:
    1. User overrides (favicon-overrides.yml) - highest priority
    2. App defaults (favicon.yml) - medium priority
    3. Auto-discovered (local-cache/favicon.yml) - lowest priority

    Returns:
        RelLink: Cached favicon link, or None if not found
    """

    # Load caches using cached loader (respects mtime and TTL)
    discovered_cache = _load_yaml_with_cache(FAVICON_LOCAL_CACHE)
    defaults_cache = _load_yaml_with_cache(FAVICON_DEFAULTS)
    overrides_cache = _load_yaml_with_cache(FAVICON_OVERRIDES)

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

    # Search in order of precedence: overrides, defaults, discovered
    for cache_dict, cache_name in [
        (overrides_cache, "override"),
        (defaults_cache, "default"),
        (discovered_cache, "discovered")
    ]:
        for s in search_paths:
            if favicon := cache_dict.get(s):
                # Cached favicons are pre-validated, no HTTP check needed
                r = RelLink(favicon, cache_key=s)
                r._validated = True
                r.resolved_href = favicon
                # Mark as valid by setting a reasonable default type
                r.image_type = "image/png"
                return r

    return None


def add_favicon_to_cache(cache_key, favicon_link):
    """Add the favicon link to the auto-discovered cache.
    
    Only writes to local-cache/favicon.yml (auto-discovered cache).
    User overrides should be manually added to static/favicon-overrides.yml.
    Invalidates in-memory cache for local cache file.
    """
    cache = _load_yaml_with_cache(FAVICON_LOCAL_CACHE)

    if cache_key.startswith("www."):
        cache_key = cache_key.replace("www.", "")

    cache[cache_key] = favicon_link

    # Write cache in sorted order.
    with open(FAVICON_LOCAL_CACHE, "w") as f:
        yaml.dump(cache, f, sort_keys=True)
    
    # Invalidate in-memory cache so next load picks up the change
    file_path_str = str(FAVICON_LOCAL_CACHE)
    if file_path_str in _favicon_yaml_cache:
        del _favicon_yaml_cache[file_path_str]


def get_favicon_links(
    page_url: str, soup: BeautifulSoup, include=None
) -> list[RelLink]:
    """Get the favicon links for the page URL.
    
    Discovers native favicon formats first. Only creates ICO/SVG→PNG conversions
    if no other formats (PNG, JPEG, etc.) are available, ensuring compatibility
    with platforms like Obsidian markdown that have trouble with ICO/SVG.
    """

    # Keep track of href already seen.
    seen = set()

    links = []

    if cached_url := get_favicon_cache(page_url):
        links.append(cached_url)
        if include != 'all':
            return links
        seen.add(cached_url.href)

    if not soup:
        return links

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
                if r in FAVICON_REL:
                    r = RelLink(
                        href,
                        rel=rel,
                        sizes=sizes,
                    )
                    links.append(r)
                    if include != "all":
                        return links

                    break

    # Fallback to common favicon files.
    parsed = urlparse(page_url)
    page_host = urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))

    for f in COMMON_FAVICON_FILES:
        # Add common favicon paths (will validate lazily)
        href = url_util.make_absolute_urls(page_host, f)
        if href in seen:
            continue
        seen.add(href)

        r = RelLink(href)
        links.append(r)
        if include != "all":
            return links

    # Check if we have any non-ICO/non-SVG formats available
    has_non_ico_svg = any(
        link.image_type not in ("image/ico", "image/svg")
        for link in links
        if link.image_type
    )
    
    # Only create conversions if ICO/SVG are the only formats available
    # This ensures compatibility with Obsidian markdown which has trouble with ICO/SVG
    if not has_non_ico_svg:
        conversion_links = []
        for link in links:
            if link.image_type == "image/ico":
                # Try ICO→PNG conversion
                if img_util.convert_ico(link.href) is not None:
                    params = urlencode({"url": link.href})
                    conv_href = f"http://{request.host}/{ICO_TO_PNG_PATH}?{params}"
                    r = RelLink(
                        conv_href,
                        rel=link.rel,
                        sizes=link.sizes,
                    )
                    if r.is_valid():
                        conversion_links.append(r)
            elif link.image_type == "image/svg":
                # Try SVG→PNG conversion
                if img_util.convert_svg(link.href) is not None:
                    params = urlencode({"url": link.href})
                    conv_href = f"http://{request.host}/{SVG_TO_PNG_PATH}?{params}"
                    r = RelLink(
                        conv_href,
                        rel=link.rel,
                        sizes=link.sizes,
                    )
                    if r.is_valid():
                        conversion_links.append(r)
        
        # Add conversion links to the result
        links.extend(conversion_links)

    # No favicon links found.
    return links


def validate_top_candidates(links: list[RelLink], max_count: int = 1) -> list[RelLink]:
    """Validate only the top N favicon candidates.
    
    Iterates through sorted links and validates them one at a time until
    we have max_count valid favicons. Stops early to avoid unnecessary HTTP requests.
    
    Args:
        links: Sorted list of favicon links (best first)
        max_count: Maximum number of valid favicons to return
        
    Returns:
        List of validated favicon links (up to max_count)
    """
    validated = []
    
    for link in links:
        # Cached links are always valid (skip validation)
        if link.cache_key:
            validated.append(link)
            if len(validated) >= max_count:
                break
            continue
        
        # Validate this link (makes HTTP request on first call)
        if link.validate():
            validated.append(link)
            if len(validated) >= max_count:
                break
    
    return validated


def get_common_favicon_links(page_url):
    """Get the common favicon links for the page URL."""

    # Build links for the common favicon files.
    links = []
    for f in COMMON_FAVICON_FILES:
        links.append(RelLink(url_util.make_absolute_urls(page_url, f)))

    return links


def sort_favicon_links(
    favicons: list[RelLink],
    favicon_width: int = FAVICON_WIDTH,
    include: str = None
) -> list[RelLink]:
    """Sort favicons to prefer those closest to target size.

    Order of precedence (higher is first):
    999. Cached favicon
    500. Images except for ICO and SVG - sorted by proximity to target size
    400. ICO - sorted by proximity to target size
    300. SVG
    200. ICO conversion
    100. SVG conversion
    
    Within each precedence group, favicons are sorted by distance from target area.
    Slightly larger favicons are preferred over smaller ones (downscaling > upscaling).
    
    Args:
        favicons: List of favicon links to sort
        favicon_width: Target width in pixels (default: 20)
        include: If "all", include all favicons; otherwise return only best match
    
    Returns:
        Sorted list of favicon links
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

    # Target area for optimal favicon size
    target_area = favicon_width * favicon_width

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

        # Calculate distance from target size
        if x.width is not None and x.height is not None:
            area = x.width * x.height
            distance = abs(area - target_area)
            
            # Penalize upscaling (smaller than target) more than downscaling
            if area < target_area:
                distance = int(distance * 1.2)
        else:
            # Unknown size - assign high distance (low priority)
            distance = 999999

        # Return composite key: group (descending), distance (ascending)
        # Format: "999_000000400" for 20x20 cached favicon
        return f"{group_key:03d}_{distance:09d}"

    # Sort by key in reverse (higher group_key first, lower distance first within group)
    return sorted(favicons, key=lambda x: key_fn(x), reverse=True)
