"""Mirror favicons and favicon override routes."""

import json

import yaml
from flask import Blueprint, current_app, make_response, request

from library import html_util, img_util, url_util, util

bp = Blueprint("mirror_favicons", __name__)


def json_response(data: dict, status: int = 200) -> tuple:
    """Create a Flask JSON response tuple."""
    return json.dumps(data), status, {"Content-Type": "application/json"}


def validate_favicons(favicons: list, url: str) -> list:
    """Validate favicon links, keeping cached ones even if they fail to load.

    For each favicon, determines cache source and image size. Non-cached
    favicons that don't load are excluded.
    """
    valid_favicons = []
    for favicon in favicons:
        favicon.cache_source = html_util.get_favicon_cache_source(url, favicon.href)

        if size := url_util.get_image_size(favicon.href):
            favicon.width = size.width
            favicon.height = size.height
            favicon.image_type = size.image_type
            valid_favicons.append(favicon)
        elif favicon.cache_source["file"] is not None:
            # Cached favicon but failed to load - include it anyway
            # so users can see invalid cache entries
            favicon.width = 0
            favicon.height = 0
            favicon.image_type = "invalid"
            valid_favicons.append(favicon)

    return valid_favicons


def save_favicon_override(overrides: dict, header_lines: list[str]) -> None:
    """Write overrides back to the YAML file, preserving header comments."""
    with open(html_util.FAVICON_OVERRIDES, "w") as f:
        for line in header_lines:
            f.write(line)
        yaml.dump(overrides, f, sort_keys=True)

    # Invalidate in-memory cache
    file_path_str = str(html_util.FAVICON_OVERRIDES)
    if file_path_str in html_util._favicon_yaml_cache:
        del html_util._favicon_yaml_cache[file_path_str]


@bp.route("/mirror-favicons", methods=["GET", "POST"])
def get_mirror_favicons():
    """
    Return the favicons for the page.
    """
    template_env = current_app.template_env

    metadata = util.get_page_metadata()

    # Get the favicons.
    favicons = html_util.get_favicon_links(
        metadata.url,
        metadata.soup,
        include="all",
    )

    # If the first favicon has a cacheKey, set it aside.
    cache_favicon = None
    if favicons and favicons[0].cache_key:
        cache_favicon = favicons[0]
        favicons = favicons[1:]

    # Get the size of each favicon and determine cache source.
    # Keep cached favicons even if they fail to load (to show invalid cache entries).
    # Filter out only non-cached favicons that don't exist.
    favicons = validate_favicons(favicons, metadata.url)

    # Sort favicons.
    favicons = html_util.sort_favicon_links(favicons, include="all")

    # Add back the cached favicon at the start.
    if cache_favicon:
        cache_favicon.cache_source = html_util.get_favicon_cache_source(
            metadata.url, cache_favicon.href
        )

        # Try to get image size, but include even if it fails
        if size := url_util.get_image_size(cache_favicon.href):
            cache_favicon.width = size.width
            cache_favicon.height = size.height
            cache_favicon.image_type = size.image_type
        else:
            # Cached favicon failed to load - mark as invalid but include it
            cache_favicon.width = 0
            cache_favicon.height = 0
            cache_favicon.image_type = "invalid"

        favicons.insert(0, cache_favicon)

    # Note: inline_image is only set for favicons that were stored with inline data in cache.
    # We do NOT compute inline on-the-fly here - that would defeat the purpose of
    # storing inline data in the cache to avoid recomputation.

    # Auto-cache the top favicon if none is cached and we have valid favicons
    if not cache_favicon and favicons:
        # Add the top favicon as the cached favicon.
        html_util.add_favicon_to_cache(
            metadata.cache_key,
            favicons[0].href,
        )

    # Load cache file data for display
    cache_files = {
        "overrides": {
            "name": "User Overrides",
            "path": str(html_util.FAVICON_OVERRIDES.absolute()),
            "precedence": 1,
            "entries": html_util._load_yaml_with_cache(html_util.FAVICON_OVERRIDES),
        },
        "defaults": {
            "name": "App Defaults",
            "path": str(html_util.FAVICON_DEFAULTS.absolute()),
            "precedence": 2,
            "entries": html_util._load_yaml_with_cache(html_util.FAVICON_DEFAULTS),
        },
        "discovered": {
            "name": "Auto-Discovered",
            "path": str(html_util.FAVICON_LOCAL_CACHE.absolute()),
            "precedence": 3,
            "entries": html_util._load_yaml_with_cache(html_util.FAVICON_LOCAL_CACHE),
        },
    }

    # Add entry counts
    for cache_info in cache_files.values():
        cache_info["count"] = len(cache_info["entries"])

    template = template_env.get_template("mirror-favicons.html")
    rendered_html = template.render(
        {
            "favicons": favicons,
            "url": metadata.url,
            "cache_key": metadata.cache_key,
            "override_domain": metadata.override_domain,
            "override_path_scope": metadata.override_path_scope,
            "cache_files": cache_files,
        }
    )

    resp = make_response(rendered_html)
    return resp


@bp.route("/add-favicon-override", methods=["POST"])
def add_favicon_override():
    """Add a favicon override to the user override file.

    Accepts JSON with:
    - favicon_url: The URL of the favicon to cache
    - page_url: The URL of the page
    - scope: 'domain' or 'path'
    - save_inline: If true, store as inline base64 instead of URL

    Returns JSON with:
    - success: bool
    - cache_key: The key used (if successful)
    - error: Error message (if failed)
    """
    try:
        data = request.get_json()
        favicon_url = data.get("favicon_url")
        page_url = data.get("page_url")
        scope = data.get("scope", "domain")
        save_inline = data.get("save_inline", False)

        if not favicon_url or not page_url:
            return json_response(
                {"success": False, "error": "Missing favicon_url or page_url"}, 400
            )

        # Parse the URL to determine cache key
        netloc = url_util.normalize_netloc(page_url)

        if scope == "path":
            # Use domain + first path segment
            path_segment = url_util.get_first_path_segment(page_url)
            if path_segment:
                cache_key = f"{netloc}/{path_segment}"
            else:
                cache_key = netloc
        else:
            # Use domain only
            cache_key = netloc

        # Read current file to preserve header comments
        header_lines = []
        if html_util.FAVICON_OVERRIDES.exists():
            with open(html_util.FAVICON_OVERRIDES) as f:
                for line in f:
                    if line.strip().startswith("#") or line.strip() == "":
                        header_lines.append(line)
                    else:
                        # Stop when we hit the first non-comment, non-empty line
                        break

        # Load current overrides
        overrides = html_util._load_yaml_with_cache(html_util.FAVICON_OVERRIDES)

        # Add the new override
        if save_inline:
            # Encode favicon inline (resized to height=20) and store as dict
            inline_data = img_util.encode_favicon_inline(favicon_url, html_util.FAVICON_HEIGHT)
            if inline_data:
                overrides[cache_key] = {"url": favicon_url, "inline_image": inline_data}
            else:
                # Fallback to URL if encoding fails
                overrides[cache_key] = favicon_url
        else:
            overrides[cache_key] = favicon_url

        # Write back to file with preserved header
        save_favicon_override(overrides, header_lines)

        return json_response({"success": True, "cache_key": cache_key})

    except Exception as e:
        return json_response({"success": False, "error": str(e)}, 500)


@bp.route("/convert-ico-to-png", methods=["GET"])
def convert_ico_to_png():
    """Convert an ICO favicon to PNG format."""
    ico_url = request.args.get("url")

    if not ico_url:
        return "URL parameter 'url' is required", 400

    png_bytes = img_util.convert_ico(ico_url)
    if png_bytes is not None:
        # Create a response with PNG bytes
        response = make_response(png_bytes)
        response.headers.set("Content-Type", "image/png")
        return response
    else:
        return "Failed to convert ICO to PNG", 500


@bp.route("/convert-svg-to-png", methods=["GET"])
def convert_svg_to_png():
    """Convert an SVG favicon to PNG format."""
    svg_url = request.args.get("url")

    if not svg_url:
        return "URL parameter 'url' is required", 400

    png_bytes = img_util.convert_svg(svg_url)
    if png_bytes is not None:
        # Create a response with PNG bytes
        response = make_response(png_bytes)
        response.headers.set("Content-Type", "image/png")
        return response
    else:
        return "Failed to convert SVG to PNG", 500
