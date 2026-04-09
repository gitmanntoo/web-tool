import base64
import json
import logging
import time
import uuid
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from flask import Flask, abort, request, make_response, redirect, Response
from jinja2 import Environment, FileSystemLoader
import markdown
import yaml

from library import util
from library import docker_util
from library import html_util
from library import img_util
from library import text_util
from library import url_util

app = Flask(__name__)

# Initialize template environment.
template_loader = FileSystemLoader(util.TEMPLATE_DIR)
template_env = Environment(loader=template_loader)


@app.before_request
def before_request_cleanup():
    """Clean up expired clip_cache entries before each request."""
    util.cleanup_clip_cache()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


@app.route('/')
def read_root():
    """Display the README file replacing instances of `http://localhost:8532`
    with the current host."""

    current_host = f"http://{request.host}"
    with open("README.md") as f:
        content = f.read()
        content = content.replace("http://localhost:8532", current_host)
        html = markdown.markdown(content)
        return f'<html><head><link rel="stylesheet" href="/static/default.css"></head><body>{html}</body></html>'


@app.route('/js/<filename>.js')
def serve_js(filename):
    """
    Serves javascript files from the static directory.
    Mode controls the output format:
    - "minify": minified javascript
    - "bookmarklet": a bookmarklet from minified javascript
    - default: unmodified javascript
    """
    # Ensure the filename does not contain path traversals
    if '..' in filename or filename.startswith('/'):
        abort(404)  # Not found

    # Read options
    mode = request.args.get("mode", "")
    format = request.args.get("format", "html")

    # Return the contents
    outStr = util.get_javascript_file(
        filename, mode, template_env=template_env,
        format=format,
    )

    return util.plain_text_response(
        template_env, 
        f"{filename}.js",
        outStr,
        format="html",
        language="javascript",
    )


@app.route('/clip-proxy', methods=['GET'])
def clip_to_post():
    """Copy the contents of a the clipboard into a POST request."""

    if not docker_util.is_running_in_container():
        # Redirect to the web-tool.py endpoint given in the target query parameter.
        target = request.args.get("target")
        if target:
            # Build URL without the target parameter
            from urllib.parse import urlencode
            
            # Get all query params except 'target'
            params = {k: v for k, v in request.args.items() if k != 'target'}
            query_string = urlencode(params, doseq=True) if params else ''
            
            new_url = f"http://{request.host}/{target}"
            if query_string:
                new_url += f"?{query_string}"
            
            return redirect(new_url)

    template = template_env.get_template('clip-proxy.html')
    rendered_html = template.render({})

    resp = make_response(rendered_html)
    return resp


@app.route('/clip-collector', methods=['POST'])
def clip_collector():
    """Collect chunks of text by batch ID and chunk number."""

    # Validate batchId
    batch_id = request.args.get('batchId')
    if not batch_id:
        return "Missing required parameter: batchId", 400
    
    try:
        uuid.UUID(batch_id)
    except (ValueError, AttributeError):
        return "Invalid batchId format: must be a valid UUID", 400
    
    # Validate chunkNum
    chunk_num_str = request.args.get('chunkNum')
    if not chunk_num_str:
        return "Missing required parameter: chunkNum", 400
    
    try:
        chunk_number = int(chunk_num_str)
    except (ValueError, TypeError):
        return "Invalid chunkNum: must be an integer", 400
    
    if chunk_number < 1:
        return "Invalid chunkNum: must be positive", 400
    
    if chunk_number > util.CLIP_CACHE_MAX_CHUNK_NUMBER:
        return f"Invalid chunkNum: exceeds maximum allowed value ({util.CLIP_CACHE_MAX_CHUNK_NUMBER})", 400

    # Initialize batch if it doesn't exist
    if batch_id not in util.clip_cache:
        util.clip_cache[batch_id] = {
            'created_at': time.time(),
            'chunks': {}
        }
    
    util.clip_cache[batch_id]['chunks'][chunk_number] = request.data.decode()

    return "OK"


@app.route('/mirror-clip', methods=['GET', 'POST'])
def mirror_clip():
    """Display the contents of the clipboard."""

    metadata = util.get_page_metadata()

    # Read clipboard contents.
    clip = metadata.mirror_data.clipboard

    # If clip is valid JSON, format it with indentation.
    clip_text = clip
    try:
        clip_json = json.loads(clip)
        clip_text = json.dumps(clip_json, indent=2)
    except json.JSONDecodeError:
        pass

    return util.plain_text_response(
        template_env, "Clipboard Contents", clip_text,
        format=metadata.output_format,
        language="json",
    )


@app.route('/mirror-html-source', methods=['GET', 'POST'])
def mirror_html_source():
    """Display the HTML from the clipboard."""

    metadata = util.get_page_metadata()

    # If clip is valid JSON, extract the HTML and prettify it.
    html_text = ""
    if metadata.soup:
        html_text = html_util.prettify_html(str(metadata.soup))
        return util.plain_text_response(
            template_env,
            "HTML Source",
            html_text,
            format=metadata.output_format,
            language="html",
        )

    return mirror_clip()


@app.route("/mirror-favicons", methods=["GET", "POST"])
def get_mirror_favicons():
    """
    Return the favicons for the page.
    """

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
    valid_favicons = []
    for favicon in favicons:
        # Determine which cache file (if any) contains this favicon
        favicon.cache_source = html_util.get_favicon_cache_source(
            metadata.url,
            favicon.href
        )
        
        # Try to get image size
        if size := url_util.get_image_size(favicon.href):
            favicon.width = size.width
            favicon.height = size.height
            favicon.image_type = size.image_type
            valid_favicons.append(favicon)
        elif favicon.cache_source['file'] is not None:
            # Cached favicon but failed to load - include it anyway
            # so users can see invalid cache entries
            favicon.width = 0
            favicon.height = 0
            favicon.image_type = "invalid"
            valid_favicons.append(favicon)
        # else: non-cached favicon that doesn't exist - exclude it
    
    favicons = valid_favicons

    # Sort favicons.
    favicons = html_util.sort_favicon_links(favicons, include='all')

    # Add back the cached favicon at the start.
    if cache_favicon:
        cache_favicon.cache_source = html_util.get_favicon_cache_source(
            metadata.url,
            cache_favicon.href
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
        'overrides': {
            'name': 'User Overrides',
            'path': str(html_util.FAVICON_OVERRIDES.absolute()),
            'precedence': 1,
            'entries': html_util._load_yaml_with_cache(html_util.FAVICON_OVERRIDES),
        },
        'defaults': {
            'name': 'App Defaults',
            'path': str(html_util.FAVICON_DEFAULTS.absolute()),
            'precedence': 2,
            'entries': html_util._load_yaml_with_cache(html_util.FAVICON_DEFAULTS),
        },
        'discovered': {
            'name': 'Auto-Discovered',
            'path': str(html_util.FAVICON_LOCAL_CACHE.absolute()),
            'precedence': 3,
            'entries': html_util._load_yaml_with_cache(html_util.FAVICON_LOCAL_CACHE),
        }
    }
    
    # Add entry counts
    for cache_info in cache_files.values():
        cache_info['count'] = len(cache_info['entries'])

    template = template_env.get_template('mirror-favicons.html')
    rendered_html = template.render({
        'favicons': favicons,
        'url': metadata.url,
        'cache_key': metadata.cache_key,
        'cache_files': cache_files,
    })

    resp = make_response(rendered_html)
    return resp


@app.route('/add-favicon-override', methods=['POST'])
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
        favicon_url = data.get('favicon_url')
        page_url = data.get('page_url')
        scope = data.get('scope', 'domain')
        save_inline = data.get('save_inline', False)

        if not favicon_url or not page_url:
            return json.dumps({
                'success': False,
                'error': 'Missing favicon_url or page_url'
            }), 400, {'Content-Type': 'application/json'}

        # Parse the URL to determine cache key
        parsed = urlparse(page_url)

        # Normalize netloc: always remove www. prefix for consistency
        netloc = parsed.netloc
        if netloc.startswith("www."):
            netloc = netloc[4:]

        if scope == 'path':
            # Use domain + first path segment
            path_part = parsed.path
            if path_part.startswith("/"):
                path_part = path_part[1:]
            if len(path_part) > 0:
                path_part = path_part.split("/")[0]
                cache_key = f"{netloc}/{path_part}"
            else:
                cache_key = netloc
        else:
            # Use domain only
            cache_key = netloc

        # Read current file to preserve header comments
        header_lines = []
        if html_util.FAVICON_OVERRIDES.exists():
            with open(html_util.FAVICON_OVERRIDES, 'r') as f:
                for line in f:
                    if line.strip().startswith('#') or line.strip() == '':
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
                overrides[cache_key] = {'url': favicon_url, 'inline_image': inline_data}
            else:
                # Fallback to URL if encoding fails
                overrides[cache_key] = favicon_url
        else:
            overrides[cache_key] = favicon_url

        # Write back to file with preserved header
        with open(html_util.FAVICON_OVERRIDES, "w") as f:
            # Write header comments first
            for line in header_lines:
                f.write(line)
            # Write YAML data in sorted order
            yaml.dump(overrides, f, sort_keys=True)

        # Invalidate in-memory cache
        file_path_str = str(html_util.FAVICON_OVERRIDES)
        if file_path_str in html_util._favicon_yaml_cache:
            del html_util._favicon_yaml_cache[file_path_str]

        return json.dumps({
            'success': True,
            'cache_key': cache_key
        }), 200, {'Content-Type': 'application/json'}

    except Exception as e:
        return json.dumps({
            'success': False,
            'error': str(e)
        }), 500, {'Content-Type': 'application/json'}


@app.route('/convert-ico-to-png', methods=['GET'])
def convert_ico_to_png():
    """Convert """
    ico_url = request.args.get('url')

    if not ico_url:
        return "URL parameter 'url' is required", 400

    png_bytes = img_util.convert_ico(ico_url)
    if png_bytes is not None:
        # Create a response with PNG bytes
        response = make_response(png_bytes)
        response.headers.set('Content-Type', 'image/png')
        return response
    else:
        return "Failed to convert ICO to PNG", 500


@app.route('/convert-svg-to-png', methods=['GET'])
def convert_svg_to_png():
    """Convert """
    ico_url = request.args.get('url')

    if not ico_url:
        return "URL parameter 'url' is required", 400

    png_bytes = img_util.convert_svg(ico_url)
    if png_bytes is not None:
        # Create a response with PNG bytes
        response = make_response(png_bytes)
        response.headers.set('Content-Type', 'image/png')
        return response
    else:
        return "Failed to convert SVG to PNG", 500


@app.route("/mirror-links", methods=["GET", "POST"])
def get_mirror_links():
    """
    Return the links for the page.
    """
    metadata = util.get_page_metadata()

    # build fragment variants with duplicate detection
    fragment_variants = []
    fragment_variants_data = [
        ('', 'None'),
    ]
    if metadata.parsed_url.fragment:
        fragment_variants_data.append((metadata.parsed_url.fragment, 'Fragment'))
    if metadata.fragment_text:
        fragment_variants_data.append((metadata.fragment_text, 'Fragment Text'))

    seen_values = set()
    for fragment_value, label in fragment_variants_data:
        # For 'None', use empty string as the value
        value = fragment_value if label != 'None' else ''
        is_duplicate = value in seen_values and label != 'None'
        fragment_variants.append({
            'value': value,
            'label': label,
            'is_duplicate': is_duplicate
        })
        seen_values.add(value)

    # build urls with labels - always start with Original
    url_variants = []
    url_variants_data = [
        (metadata.url, 'Original'),
        (metadata.url_with_fragment, 'With Fragment'),
        (metadata.url_clean, 'Clean'),
        (metadata.url_root, 'Root'),
        (metadata.url_host, 'Host'),
    ]

    seen_labels = set()
    seen_values = set()
    for url, label in url_variants_data:
        if url:
            if label not in seen_labels:
                is_duplicate = url in seen_values
                url_variants.append({
                    'url': url,
                    'label': label,
                    'is_duplicate': is_duplicate
                })
                seen_labels.add(label)
                seen_values.add(url)

    # build links
    links = []

    # Set a default title so links are not blank.
    if not metadata.title:
        metadata.title = "link"

    # Generate title variants - always start with Original
    title_obj = util.TitleVariants(metadata.title)
    
    title_variant_list = []
    title_variants_data = [
        (title_obj.original, 'Original'),
        (title_obj.ascii_and_emojis, 'ASCII + Emoji'),
        (title_obj.ascii_only, 'ASCII Only'),
        (title_obj.path_safe, 'Path Safe'),
    ]
    
    seen_labels = set()
    seen_values = set()
    for title_value, label in title_variants_data:
        if label not in seen_labels:
            is_duplicate = title_value in seen_values
            title_variant_list.append({
                'value': title_value,
                'label': label,
                'is_duplicate': is_duplicate
            })
            seen_labels.add(label)
            seen_values.add(title_value)

    # Get inline base64 favicon (from cache or generate on-the-fly)
    favicon_inline = None
    favicon_width = None
    favicon_height = None
    if metadata.favicons:
        # Use cached inline if available
        if metadata.favicons[0].inline_image:
            favicon_inline = metadata.favicons[0].inline_image
        # Otherwise generate inline version from the favicon URL
        elif metadata.favicon_url:
            favicon_result = img_util.encode_favicon_inline(metadata.favicon_url, html_util.FAVICON_HEIGHT)
            if favicon_result:
                favicon_inline = favicon_result.get('data_url')
                favicon_width = favicon_result.get('width')
                favicon_height = favicon_result.get('height')

        if metadata.fragment_title:
            links.append({
                "header": "Favicon",
                "html": (
                    f'<img src="{metadata.favicon_url}" '
                    f'height="{html_util.FAVICON_HEIGHT}" /> '
                    f'<a target="_blank" href="{metadata.url}">'
                    f'{util.html_text(util.ascii_text(metadata.fragment_title))}</a>'
                ),
            })

        links.append({
            "header": "Favicon - Clean",
            "html": (
                f'<img src="{metadata.favicon_url}" '
                f'height="{html_util.FAVICON_HEIGHT}" /> '
                f'<a target="_blank" href="{metadata.url_clean}">'
                f'{util.html_text(util.ascii_text(metadata.title))}</a>'
            ),
        })

    if metadata.fragment_title:
        links.append({
            "header": "Simple",
            "html": (
                f'<a target="_blank" href="{metadata.url}">'
                f'{util.html_text(util.ascii_text(metadata.fragment_title))}</a>'
            ),
        })

    links.append({
        "header": "Simple - Clean",
        "html": (
            f'<a target="_blank" href="{metadata.url_clean}">'
            f'{util.html_text(util.ascii_text(metadata.title))}</a>'
        ),
    })

    template = template_env.get_template('mirror-links.html')
    rendered_html = template.render({
        'title': metadata.title,
        'title_variants': title_variant_list,
        'fragment': metadata.parsed_url.fragment if metadata.parsed_url else '',
        'fragment_text': metadata.fragment_text,
        'fragment_variants': fragment_variants,
        'content_type': metadata.content_type,
        'clipboard_error': metadata.clipboard_error,
        'user_agent': metadata.mirror_data.userAgent if metadata.mirror_data else '',
        'cookie_string': metadata.mirror_data.cookieString if metadata.mirror_data else '',
        'html_size': metadata.mirror_data.htmlSize if metadata.mirror_data else 0,
        'url_variants': url_variants,
        'links': links,
        'favicon': metadata.favicon_url,
        'favicon_inline': favicon_inline,
        'favicon_width': favicon_width,
        'favicon_height': favicon_height,
    })

    resp = make_response(rendered_html)
    return resp


@app.route("/debug/title-variants", methods=["GET", "POST"])
def debug_title_variants():
    """
    Debug endpoint to test title variant generation.
    """
    title_variant_list = []
    input_title = ""
    
    if request.method == "POST":
        input_title = request.form.get('title', '')
        
        if input_title:
            # Generate title variants
            title_obj = util.TitleVariants(input_title)
            
            title_variants_data = [
                (title_obj.original, 'Original'),
                (title_obj.ascii_and_emojis, 'ASCII + Emoji'),
                (title_obj.ascii_only, 'ASCII Only'),
                (title_obj.path_safe, 'Path Safe'),
            ]
            
            seen_labels = set()
            seen_values = set()
            for title_value, label in title_variants_data:
                if label not in seen_labels:
                    is_duplicate = title_value in seen_values
                    title_variant_list.append({
                        'value': title_value,
                        'label': label,
                        'is_duplicate': is_duplicate
                    })
                    seen_labels.add(label)
                    seen_values.add(title_value)
    
    template = template_env.get_template('debug-title-variants.html')
    rendered_html = template.render({
        'input_title': input_title,
        'title_variants': title_variant_list,
    })
    
    resp = make_response(rendered_html)
    return resp


@app.route("/debug/url-variants", methods=["GET", "POST"])
def debug_url_variants():
    """
    Debug endpoint to test URL variant generation.
    """
    url_variant_list = []
    input_url = ""
    
    if request.method == "POST":
        input_url = request.form.get('url', '')
        
        if input_url:
            # Parse the URL
            from urllib.parse import urlparse, urlunparse
            parsed_url = urlparse(input_url)
            
            # Generate URL variants similar to metadata properties
            url_original = input_url
            
            url_with_fragment = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path, '', '', parsed_url.fragment)).rstrip('/')
            
            url_clean = urlunparse((
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path, '', '', '')).rstrip('/')
            
            url_root = url_util.get_url_root(input_url)
            url_host = url_util.get_url_host(input_url)
            
            url_variants_data = [
                (url_original, 'Original'),
                (url_with_fragment, 'With Fragment'),
                (url_clean, 'Clean'),
                (url_root, 'Root'),
                (url_host, 'Host'),
            ]
            
            seen_labels = set()
            seen_values = set()
            for url_value, label in url_variants_data:
                if url_value:
                    if label not in seen_labels:
                        is_duplicate = url_value in seen_values
                        url_variant_list.append({
                            'url': url_value,
                            'label': label,
                            'is_duplicate': is_duplicate
                        })
                        seen_labels.add(label)
                        seen_values.add(url_value)
    
    template = template_env.get_template('debug-url-variants.html')
    rendered_html = template.render({
        'input_url': input_url,
        'url_variants': url_variant_list,
    })
    
    resp = make_response(rendered_html)
    return resp


@app.route("/mirror-text", methods=["GET", "POST"])
def get_mirror_text():
    """
    Return the raw strings for the page.
    """
    metadata = util.get_page_metadata()

    # Parse the HTML.
    extracted_text = text_util.walk_soup_tree_strings(metadata.soup)

    seen_text = set()
    txt = []
    for idx, x in enumerate(extracted_text):
        if x.keep:
            if x.name == 'script.String':
                if x.text in seen_text:
                    continue
                seen_text.add(x.text)

            # Avoid multiple blank lines.
            txt.append(x.text)

    # Remove multiple blank lines.
    txt = text_util.remove_repeated_lines("\n".join(txt))

    return Response(
        response=txt,
        status=200,
        mimetype="text/plain",
    )


@app.route("/mirror-text-debug", methods=["GET", "POST"])
def get_mirror_text_debug():
    """
    Return debugging info and strings for the page.
    """
    metadata = util.get_page_metadata()

    # Parse the HTML.
    extracted_text = text_util.walk_soup_tree_strings(
        metadata.soup, rollup=False)

    txt = []
    for x in extracted_text:
        if x.name == 'script.String':
            out = (
                f"{'.' * x.depth}{x.depth:3d} "
                f"{'KEEP' if x.keep else '':4s} "
                f"<{x.get_name()}> "
                f"L={x.line_count()} "
                f"W={x.word_count}/{x.token_count}/{x.word_pct():.2f} "
                f"C={x.category_str()} "
                f"D={text_util.nvl(x.min_standard_dist, -999.0):.2f}/"
                f"{text_util.nvl(x.max_standard_dist, -999.0):.2f} "
                f"R={x.max_longest_run} "
                f"{x.magika_type}"
            )
            txt.append(out)
            txt.append(x.text)
        else:
            out = (
                f"{'.' * x.depth}{x.depth:3d} "
                f"{'KEEP' if x.keep else '':4s} "
                f"<{x.get_name()}>{x.text}"
            )
            txt.append(out)

    txt = "\n".join(txt)

    return Response(
        response=txt,
        status=200,
        mimetype="text/plain",
    )


@app.route("/mirror-soup-text", methods=["GET", "POST"])
def get_mirror_soup_text():
    """Return text from BeautifulSoup."""

    metadata = util.get_page_metadata()

    # Parse the HTML.
    soup_text = text_util.remove_repeated_lines(metadata.soup.get_text("\n"))

    return Response(
        response=soup_text,
        status=200,
        mimetype="text/plain",
    )


@app.route("/get", methods=["GET", ])
def get_url_response():
    """Use the get_url method to retrieve a URL.
    """
    url = request.args.get("url")
    if not url:
        return "URL parameter 'url' is required", 400

    # Get the URL response
    resp = url_util.get_url(url)
    if not resp:
        return "Failed to retrieve URL", 500

    return resp.as_dict()


@app.route("/debug/container", methods=["GET", ])
def debug_container():
    """Return container detection status."""
    return {
        "running_in_container": docker_util.is_running_in_container(),
    }


@app.route("/debug/clip-cache", methods=["GET", ])
def debug_clip_cache():
    """Return current clip_cache state for debugging."""
    import sys
    import psutil
    
    # Calculate cache size
    cache_size = sys.getsizeof(util.clip_cache)
    for batch_data in util.clip_cache.values():
        cache_size += sys.getsizeof(batch_data)
        cache_size += sys.getsizeof(batch_data.get('chunks', {}))
        for chunk in batch_data.get('chunks', {}).values():
            cache_size += sys.getsizeof(chunk)
    
    # Get memory info
    memory = psutil.virtual_memory()
    memory_limit = memory.available * util.CLIP_CACHE_MEMORY_LIMIT_PCT
    
    # Build batch details
    batches = []
    for batch_id, batch_data in util.clip_cache.items():
        created_at = batch_data.get('created_at', 0)
        age_seconds = time.time() - created_at
        chunks = batch_data.get('chunks', {})
        
        batch_info = {
            'batch_id': batch_id,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(created_at)),
            'age_seconds': round(age_seconds, 1),
            'chunk_count': len(chunks),
            'chunk_numbers': sorted(chunks.keys()),
        }
        batches.append(batch_info)
    
    # Sort by creation time (oldest first)
    batches.sort(key=lambda x: x['age_seconds'], reverse=True)
    
    return {
        'batch_count': len(util.clip_cache),
        'cache_size_bytes': cache_size,
        'cache_size_mb': round(cache_size / 1024 / 1024, 2),
        'memory_available_mb': round(memory.available / 1024 / 1024, 2),
        'memory_limit_mb': round(memory_limit / 1024 / 1024, 2),
        'memory_usage_pct': round(cache_size / memory_limit * 100, 1) if memory_limit > 0 else 0,
        'config': {
            'ttl_seconds': util.CLIP_CACHE_TTL_SECONDS,
            'max_batches': util.CLIP_CACHE_MAX_BATCHES,
            'max_chunk_number': util.CLIP_CACHE_MAX_CHUNK_NUMBER,
            'memory_limit_pct': util.CLIP_CACHE_MEMORY_LIMIT_PCT,
        },
        'batches': batches,
    }


@app.route("/debug/clipboard-proxy", methods=["GET", ])
def debug_clipboard_proxy():
    """Test the clipboard proxy functionality.
    
    This endpoint simulates what happens when a bookmarklet successfully
    captures clipboard data and sends it through the proxy.
    
    Returns a test page that submits clipboard data to /mirror-clip
    so you can verify the proxy is working.
    """
    test_data = {
        "url": "http://example.com",
        "title": "Test Page",
        "userAgent": request.headers.get("User-Agent", "Unknown"),
        "cookieString": "",
        "html": "<html><body><h1>Test Content</h1><p>This is test content.</p></body></html>",
    }
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Clipboard Proxy Debug</title>
        <link rel="stylesheet" href="/static/default.css">
    </head>
    <body>
        <h1>Clipboard Proxy Debug Test</h1>
        <p>This page tests the clipboard proxy by submitting test data to /mirror-clip.</p>
        <p><strong>Test Data:</strong></p>
        <pre>{json.dumps(test_data, indent=2)}</pre>
        <button onclick="submitTest()">Submit Test Data</button>
        <div id="result" style="margin-top: 20px;"></div>
        
        <script>
            function submitTest() {{
                const testData = {json.dumps(json.dumps(test_data))};
                const batchId = crypto.randomUUID();
                
                // POST the test data to clip-collector
                fetch('/clip-collector?batchId=' + batchId + '&chunkNum=1', {{
                    method: 'POST',
                    body: testData,
                    headers: {{'Content-Type': 'text/plain'}}
                }})
                .then(resp => {{
                    if (resp.ok) {{
                        document.getElementById('result').innerHTML = 
                            '<p style="color: #5cb85c;">✓ Chunk submitted. Opening /mirror-clip...</p>';
                        // Redirect to mirror-clip with the batch ID
                        window.location.href = '/mirror-clip?batchId=' + batchId + '&textLength=' + testData.length;
                    }} else {{
                        document.getElementById('result').innerHTML = 
                            '<p style="color: #d9534f;">✗ Failed to submit chunk: ' + resp.statusText + '</p>';
                    }}
                }})
                .catch(err => {{
                    document.getElementById('result').innerHTML = 
                        '<p style="color: #d9534f;">✗ Error: ' + err.message + '</p>';
                }});
            }}
        </script>
    </body>
    </html>
    """
    
    return html


@app.route("/test-page", methods=["GET", "POST"])
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
    params = {}

    if request.method == "POST":
        params = {
            'title': request.form.get('title', 'Test Page'),
            'fragment': request.form.get('fragment', ''),
            'anchor_fragment': request.form.get('anchor-fragment', ''),
            'wrap_fragment': request.form.get('wrap-fragment', ''),
            'url_has_parens': request.form.get('url-has-parens', ''),
            'url_has_brackets': request.form.get('url-has-brackets', ''),
            'url_has_space': request.form.get('url-has-space', ''),
            'unicode_content': request.form.get('unicode-content', ''),
            'emoji_content': request.form.get('emoji-content', ''),
        }
    else:
        params = {
            'title': request.args.get('title', 'Test Page'),
            'fragment': request.args.get('fragment', ''),
            'anchor_fragment': request.args.get('anchor-fragment', ''),
            'wrap_fragment': request.args.get('wrap-fragment', ''),
            'url_has_parens': request.args.get('url-has-parens', ''),
            'url_has_brackets': request.args.get('url-has-brackets', ''),
            'url_has_space': request.args.get('url-has-space', ''),
            'unicode_content': request.args.get('unicode-content', ''),
            'emoji_content': request.args.get('emoji-content', ''),
        }

    template = template_env.get_template('test-page.html')
    rendered_html = template.render(params)

    resp = make_response(rendered_html)
    return resp


@app.route("/debug/favicon-files", methods=["GET", ])
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
    from library import html_util
    
    files_info = []
    
    # Define files in precedence order (highest to lowest)
    cache_files = [
        {
            'name': 'User Overrides',
            'precedence': 1,
            'path': html_util.FAVICON_OVERRIDES,
            'description': 'Manual customizations - highest priority',
        },
        {
            'name': 'App Defaults',
            'precedence': 2,
            'path': html_util.FAVICON_DEFAULTS,
            'description': 'Curated defaults distributed with app',
        },
        {
            'name': 'Auto-Discovered Cache',
            'precedence': 3,
            'path': html_util.FAVICON_LOCAL_CACHE,
            'description': 'Dynamically discovered favicons - lowest priority',
        },
    ]
    
    for cache_file in cache_files:
        path = cache_file['path']
        path_str = str(path)
        
        info = {
            'name': cache_file['name'],
            'precedence': cache_file['precedence'],
            'description': cache_file['description'],
            'absolute_path': str(path.absolute()),
            'exists': path.exists(),
        }
        
        if path.exists():
            stat = path.stat()
            info['size_bytes'] = stat.st_size
            info['modified_at'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
            info['mtime'] = stat.st_mtime
            
            # Check in-memory cache status
            cache_entry = html_util._favicon_yaml_cache.get(path_str)
            if cache_entry:
                cached_mtime = cache_entry.get('mtime', 0)
                loaded_at = cache_entry.get('loaded_at', 0)
                age_seconds = time.time() - loaded_at
                
                info['in_memory_cache'] = {
                    'cached': True,
                    'cached_mtime': cached_mtime,
                    'loaded_at': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(loaded_at)),
                    'age_seconds': round(age_seconds, 1),
                    'is_fresh': (cached_mtime == stat.st_mtime and age_seconds < html_util.FAVICON_CACHE_TTL),
                }
            else:
                info['in_memory_cache'] = {'cached': False}
            
            # Load the file contents
            try:
                with open(path, 'r') as f:
                    data = yaml.safe_load(f) or {}
                
                info['entry_count'] = len(data)
                
                # Get sample entries (first 5)
                sample_entries = []
                for i, (url, favicon_data) in enumerate(data.items()):
                    if i >= 5:
                        break
                    sample_entries.append({
                        'url': url,
                        'favicon': favicon_data,
                    })
                
                info['sample_entries'] = sample_entries
                info['has_more_entries'] = len(data) > 5
                
            except Exception as e:
                info['error'] = str(e)
        
        files_info.append(info)
    
    return {
        'cache_files': files_info,
        'cache_ttl_seconds': html_util.FAVICON_CACHE_TTL,
        'note': 'Files are listed in precedence order (highest to lowest)',
    }


@app.route("/debug/inline-image", methods=["GET"])
def debug_inline_image_page():
    """Debug page for converting pasted or uploaded images to inline base64."""
    template = template_env.get_template("debug-inline-image.html")
    rendered_html = template.render({})
    return make_response(rendered_html)


@app.route("/debug/inline-image", methods=["POST"])
def debug_inline_image():
    """Convert raw image bytes to an inline base64 img tag.

    Accepts JSON body with:
      - image_data: base64-encoded image bytes
      - height: target height in pixels (default 20)

    Returns JSON with:
      - success: true/false
      - inline: <img> tag with data URL (on success)
      - base64: raw base64 string (on success)
      - error: error message (on failure)
    """
    try:
        data = request.get_json()
        if not data:
            return json.dumps({"success": False, "error": "no JSON body"}), 400, {"Content-Type": "application/json"}

        image_data = data.get("image_data")
        height = int(data.get("height", 20))

        if not image_data:
            return json.dumps({"success": False, "error": "image_data is required"}), 400, {"Content-Type": "application/json"}

        if not (1 <= height <= 200):
            return json.dumps({"success": False, "error": "height must be between 1 and 200"}), 400, {"Content-Type": "application/json"}

        # Decode base64 to raw bytes
        try:
            image_bytes = base64.b64decode(image_data, validate=True)
        except Exception:
            return json.dumps({"success": False, "error": "invalid base64 data"}), 400, {"Content-Type": "application/json"}

        MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB
        if len(image_bytes) > MAX_IMAGE_BYTES:
            return json.dumps({"success": False, "error": f"image exceeds {MAX_IMAGE_BYTES // 1024 // 1024}MB limit"}), 400, {"Content-Type": "application/json"}

        # Process image
        from library.img_util import encode_image_inline

        result = encode_image_inline(image_bytes, target_height=height)
        if result is None:
            return json.dumps({
                "success": False,
                "error": "image too large (>2000px in any dimension) or unsupported format",
            }), 400, {"Content-Type": "application/json"}

        # Extract base64 portion for separate display
        base64_part = result["data_url"].split(",", 1)[1]

        return json.dumps({
            "success": True,
            "inline": f'<img src="{result["data_url"]}" height="{result["height"]}" width="{result["width"]}" alt="Favicon" />',
            "base64": base64_part,
            "width": result["width"],
            "height": result["height"],
        }), 200, {"Content-Type": "application/json"}
    except Exception as e:
        logging.exception("debug_inline_image failed")
        return json.dumps({"success": False, "error": "internal server error"}), 500, {"Content-Type": "application/json"}


@app.route("/test-pages-interactive", methods=["GET"])
def test_pages_interactive():
    """
    Interactive page for building test page URLs with configurable parameters.
    """
    template = template_env.get_template("test-pages-interactive.html")
    rendered_html = template.render({})
    return make_response(rendered_html)


if __name__ == "__main__":
    if docker_util.is_running_in_container():
        port = 8532
        debug_flag = False
    else:
        port = 8535
        debug_flag = True

    app.run(host="0.0.0.0", port=port, debug=debug_flag)
