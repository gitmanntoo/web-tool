"""Debug and test page routes."""

import base64
import json
import logging
import time
from urllib.parse import urlparse, urlunparse

from flask import Blueprint, current_app, make_response, request

from library import docker_util, html_util, util

from . import json_response

bp = Blueprint("debug", __name__)


@bp.route(
    "/debug/container",
    methods=[
        "GET",
    ],
)
def debug_container():
    """Return container detection status."""
    return {
        "running_in_container": docker_util.is_running_in_container(),
    }


@bp.route(
    "/debug/clip-cache",
    methods=[
        "GET",
    ],
)
def debug_clip_cache():
    """Return current clip_cache state for debugging."""
    import sys

    import psutil

    # Calculate cache size
    cache_size = sys.getsizeof(util.clip_cache)
    for batch_data in util.clip_cache.values():
        cache_size += sys.getsizeof(batch_data)
        cache_size += sys.getsizeof(batch_data.get("chunks", {}))
        for chunk in batch_data.get("chunks", {}).values():
            cache_size += sys.getsizeof(chunk)

    # Get memory info
    memory = psutil.virtual_memory()
    memory_limit = memory.available * util.CLIP_CACHE_MEMORY_LIMIT_PCT

    # Build batch details
    batches = []
    for batch_id, batch_data in util.clip_cache.items():
        created_at = batch_data.get("created_at", 0)
        age_seconds = time.time() - created_at
        chunks = batch_data.get("chunks", {})

        batch_info = {
            "batch_id": batch_id,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_at)),
            "age_seconds": round(age_seconds, 1),
            "chunk_count": len(chunks),
            "chunk_numbers": sorted(chunks.keys()),
        }
        batches.append(batch_info)

    # Sort by creation time (oldest first)
    batches.sort(key=lambda x: x["age_seconds"], reverse=True)

    return {
        "batch_count": len(util.clip_cache),
        "cache_size_bytes": cache_size,
        "cache_size_mb": round(cache_size / 1024 / 1024, 2),
        "memory_available_mb": round(memory.available / 1024 / 1024, 2),
        "memory_limit_mb": round(memory_limit / 1024 / 1024, 2),
        "memory_usage_pct": round(cache_size / memory_limit * 100, 1) if memory_limit > 0 else 0,
        "config": {
            "ttl_seconds": util.CLIP_CACHE_TTL_SECONDS,
            "max_batches": util.CLIP_CACHE_MAX_BATCHES,
            "max_chunk_number": util.CLIP_CACHE_MAX_CHUNK_NUMBER,
            "memory_limit_pct": util.CLIP_CACHE_MEMORY_LIMIT_PCT,
        },
        "batches": batches,
    }


@bp.route(
    "/debug/clipboard-proxy",
    methods=[
        "GET",
    ],
)
def debug_clipboard_proxy():
    """Test the clipboard proxy functionality.

    This endpoint simulates what happens when a bookmarklet successfully
    captures clipboard data and sends it through the proxy.

    Returns a test page that submits clipboard data to /mirror-clip
    so you can verify the proxy is working.
    """
    template_env = current_app.template_env

    test_data = {
        "url": "http://example.com",
        "title": "Test Page",
        "userAgent": request.headers.get("User-Agent", "Unknown"),
        "cookieString": "",
        "html": "<html><body><h1>Test Content</h1><p>This is test content.</p></body></html>",
    }

    template = template_env.get_template("debug-clipboard-proxy.html")
    rendered_html = template.render(
        {
            "test_data_json": json.dumps(test_data, indent=2),
            "test_data_js": json.dumps(json.dumps(test_data)),
        }
    )

    return rendered_html


@bp.route(
    "/debug/favicon-files",
    methods=[
        "GET",
    ],
)
def debug_favicon_files():
    """Show favicon cache files in precedence order.

    Displays the three-tier favicon cache system:
    1. User overrides (highest priority)
    2. App defaults (medium priority)
    3. Auto-discovered cache (lowest priority)

    For each file, shows:
    - Precedence level
    - File path
    - File existence
    - File size
    - Last modification time
    - Number of entries
    - In-memory cache status
    - Sample entries
    """

    files_info = []

    # Define files in precedence order (highest to lowest)
    cache_files = [
        {
            "name": "User Overrides",
            "precedence": 1,
            "path": html_util.FAVICON_OVERRIDES,
            "description": "Manual customizations - highest priority",
        },
        {
            "name": "App Defaults",
            "precedence": 2,
            "path": html_util.FAVICON_DEFAULTS,
            "description": "Curated defaults distributed with app",
        },
        {
            "name": "Auto-Discovered Cache",
            "precedence": 3,
            "path": html_util.FAVICON_LOCAL_CACHE,
            "description": "Dynamically discovered favicons - lowest priority",
        },
    ]

    for cache_file in cache_files:
        path = cache_file["path"]
        path_str = str(path)

        info = {
            "name": cache_file["name"],
            "precedence": cache_file["precedence"],
            "description": cache_file["description"],
            "absolute_path": str(path.absolute()),
            "exists": path.exists(),
        }

        if path.exists():
            stat = path.stat()
            info["size_bytes"] = stat.st_size
            info["modified_at"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
            info["mtime"] = stat.st_mtime

            # Check in-memory cache status
            cache_entry = html_util._favicon_yaml_cache.get(path_str)
            if cache_entry:
                cached_mtime = cache_entry.get("mtime", 0)
                loaded_at = cache_entry.get("loaded_at", 0)
                age_seconds = time.time() - loaded_at

                info["in_memory_cache"] = {
                    "cached": True,
                    "cached_mtime": cached_mtime,
                    "loaded_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(loaded_at)),
                    "age_seconds": round(age_seconds, 1),
                    "is_fresh": (
                        cached_mtime == stat.st_mtime and age_seconds < html_util.FAVICON_CACHE_TTL
                    ),
                }
            else:
                info["in_memory_cache"] = {"cached": False}

            # Load the file contents
            try:
                data = html_util._load_yaml_with_cache(path) or {}

                info["entry_count"] = len(data)

                # Get sample entries (first 5)
                sample_entries = []
                for i, (url, favicon_data) in enumerate(data.items()):
                    if i >= 5:
                        break
                    sample_entries.append(
                        {
                            "url": url,
                            "favicon": favicon_data,
                        }
                    )

                info["sample_entries"] = sample_entries
                info["has_more_entries"] = len(data) > 5

            except Exception as e:
                info["error"] = str(e)

        files_info.append(info)

    return {
        "cache_files": files_info,
        "cache_ttl_seconds": html_util.FAVICON_CACHE_TTL,
        "note": "Files are listed in precedence order (highest to lowest)",
    }


@bp.route("/debug/inline-image", methods=["GET"])
def debug_inline_image_page():
    """Debug page for converting pasted or uploaded images to inline base64."""
    template_env = current_app.template_env
    template = template_env.get_template("debug-inline-image.html")
    rendered_html = template.render({})
    return make_response(rendered_html)


@bp.route("/debug/inline-image", methods=["POST"])
def debug_inline_image():
    """Convert raw image bytes to an inline base64 img tag.

    Accepts JSON body with:
      - image_data: base64-encoded image bytes
      - height: target height in pixels (default 20)

    Returns JSON with:
      - success: true/false
      - inline: <img> tag with data URL, height, and width (on success)
      - base64: raw base64 string (on success)
      - width: calculated width in pixels (on success)
      - height: calculated height in pixels (on success)
      - error: error message (on failure)
    """
    try:
        data = request.get_json()
        if not data:
            return json_response({"success": False, "error": "no JSON body"}, 400)

        image_data = data.get("image_data")
        height = int(data.get("height", 20))

        if not image_data:
            return json_response({"success": False, "error": "image_data is required"}, 400)

        if not (1 <= height <= 200):
            return json_response(
                {"success": False, "error": "height must be between 1 and 200"},
                400,
            )

        # Decode base64 to raw bytes
        try:
            image_bytes = base64.b64decode(image_data, validate=True)
        except Exception:
            return json_response({"success": False, "error": "invalid base64 data"}, 400)

        max_image_bytes = 5 * 1024 * 1024  # 5 MB
        if len(image_bytes) > max_image_bytes:
            limit_mb = max_image_bytes // 1024 // 1024
            return json_response(
                {"success": False, "error": f"image exceeds {limit_mb}MB limit"},
                400,
            )

        # Process image
        from library.img_util import encode_image_inline

        result = encode_image_inline(image_bytes, target_height=height)
        if result is None:
            return json_response(
                {
                    "success": False,
                    "error": "image too large (>2000px in any dimension) or unsupported format",
                },
                400,
            )

        # Extract base64 portion for separate display
        base64_part = result["data_url"].split(",", 1)[1]

        return json_response(
            {
                "success": True,
                "inline": (
                    f'<img src="{result["data_url"]}" '
                    f'height="{result["height"]}" '
                    f'width="{result["width"]}" alt="Favicon" />'
                ),
                "base64": base64_part,
                "width": result["width"],
                "height": result["height"],
                "width_orig": result["width_orig"],
                "height_orig": result["height_orig"],
            }
        )
    except Exception:
        logging.exception("debug_inline_image failed")
        return json_response({"success": False, "error": "internal server error"}, 500)


@bp.route("/debug/title-variants", methods=["GET", "POST"])
def debug_title_variants():
    """
    Debug endpoint to test title variant generation.
    """
    template_env = current_app.template_env
    title_variant_list = []
    input_title = ""

    if request.method == "POST":
        input_title = request.form.get("title", "")

        if input_title:
            # Generate title variants
            title_obj = util.TitleVariants(input_title)

            title_variants_data = [
                (title_obj.original, "Original"),
                (title_obj.ascii_and_emojis, "ASCII + Emoji"),
                (title_obj.ascii_only, "ASCII Only"),
                (title_obj.path_safe, "Path Safe"),
            ]
            title_variant_list = util.deduplicate_variants(title_variants_data)

    template = template_env.get_template("debug-title-variants.html")
    rendered_html = template.render(
        {
            "input_title": input_title,
            "title_variants": title_variant_list,
        }
    )

    resp = make_response(rendered_html)
    return resp


@bp.route("/debug/url-variants", methods=["GET", "POST"])
def debug_url_variants():
    """
    Debug endpoint to test URL variant generation.
    """
    from library import url_util as url_util_mod

    template_env = current_app.template_env
    url_variant_list = []
    input_url = ""

    if request.method == "POST":
        input_url = request.form.get("url", "")

        if input_url:
            # Parse the URL
            parsed_url = urlparse(input_url)

            # Generate URL variants similar to metadata properties
            url_original = input_url

            url_with_fragment = urlunparse(
                (parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "", parsed_url.fragment)
            ).rstrip("/")

            url_clean = urlunparse(
                (parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "", "")
            ).rstrip("/")

            url_root = url_util_mod.get_url_root(input_url)
            url_host = url_util_mod.get_url_host(input_url)

            url_variants_data = [
                (url_original, "Original"),
                (url_with_fragment, "With Fragment"),
                (url_clean, "Clean"),
                (url_root, "Root"),
                (url_host, "Host"),
            ]
            url_variants_filtered = [(url, label) for url, label in url_variants_data if url]
            url_variant_list = [
                {"url": item["value"], "label": item["label"], "is_duplicate": item["is_duplicate"]}
                for item in util.deduplicate_variants(url_variants_filtered)
            ]

    template = template_env.get_template("debug-url-variants.html")
    rendered_html = template.render(
        {
            "input_url": input_url,
            "url_variants": url_variant_list,
        }
    )

    resp = make_response(rendered_html)
    return resp


@bp.route("/test-page", methods=["GET", "POST"])
def test_page():
    """
    Serve a test page with configurable edge-case content for manual and
    automated testing of URL, fragment, and title handling.

    Query/Form params:
    - title: page title and H1 text
    - fragment: URL fragment identifier
    - anchor-fragment: fragment for anchor-inside-heading test
    - wrap-fragment: fragment for wrapper-with-id test
    - url-has-parens: if "yes", include links with () in href
    - url-has-brackets: if "yes", include links with [] in href
    - url-has-space: if "yes", include links with spaces in href
    - unicode-content: if "yes", include Unicode body content
    - emoji-content: if "yes", include emoji body content
    """
    template_env = current_app.template_env
    params = {}

    if request.method == "POST":
        params = {
            "title": request.form.get("title", "Test Page"),
            "fragment": request.form.get("fragment", ""),
            "anchor_fragment": request.form.get("anchor-fragment", ""),
            "wrap_fragment": request.form.get("wrap-fragment", ""),
            "url_has_parens": request.form.get("url-has-parens", ""),
            "url_has_brackets": request.form.get("url-has-brackets", ""),
            "url_has_space": request.form.get("url-has-space", ""),
            "unicode_content": request.form.get("unicode-content", ""),
            "emoji_content": request.form.get("emoji-content", ""),
        }
    else:
        params = {
            "title": request.args.get("title", "Test Page"),
            "fragment": request.args.get("fragment", ""),
            "anchor_fragment": request.args.get("anchor-fragment", ""),
            "wrap_fragment": request.args.get("wrap-fragment", ""),
            "url_has_parens": request.args.get("url-has-parens", ""),
            "url_has_brackets": request.args.get("url-has-brackets", ""),
            "url_has_space": request.args.get("url-has-space", ""),
            "unicode_content": request.args.get("unicode-content", ""),
            "emoji_content": request.args.get("emoji-content", ""),
        }

    template = template_env.get_template("test-page.html")
    rendered_html = template.render(params)

    resp = make_response(rendered_html)
    return resp


@bp.route("/test-pages-interactive", methods=["GET"])
def test_pages_interactive():
    """
    Interactive page for building test page URLs with configurable parameters.
    """
    template_env = current_app.template_env
    template = template_env.get_template("test-pages-interactive.html")
    rendered_html = template.render({})
    return make_response(rendered_html)
