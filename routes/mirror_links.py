"""Mirror links, text, and clipboard routes."""

import json
import time
import uuid

from flask import Blueprint, Response, current_app, make_response, request

from library import html_util, img_util, text_util, url_util, util

bp = Blueprint("mirror_links", __name__)


@bp.route("/")
def read_root():
    """Display the README file replacing instances of `http://localhost:8532`
    with the current host."""

    import markdown

    current_host = f"http://{request.host}"
    with open("README.md") as f:
        content = f.read()
        content = content.replace("http://localhost:8532", current_host)
        html = markdown.markdown(content)
        return (
            f'<html><head><link rel="stylesheet" '
            f'href="/static/default.css"></head>'
            f"<body>{html}</body></html>"
        )


@bp.route("/mirror-links", methods=["GET", "POST"])
def get_mirror_links():
    """
    Return the links for the page.
    """
    template_env = current_app.template_env
    metadata = util.get_page_metadata()

    # build fragment variants with duplicate detection
    fragment_variants_data = [
        ("", "None"),
    ]
    if metadata.parsed_url.fragment:
        fragment_variants_data.append((metadata.parsed_url.fragment, "Fragment"))
    if metadata.fragment_text:
        fragment_variants_data.append((metadata.fragment_text, "Fragment Text"))

    fragment_variants = util.deduplicate_variants(fragment_variants_data)

    # build urls with labels - always start with Original
    url_variants = []
    url_variants_data = [
        (metadata.url, "Original"),
        (metadata.url_with_fragment, "With Fragment"),
        (metadata.url_clean, "Clean"),
        (metadata.url_root, "Root"),
        (metadata.url_host, "Host"),
    ]

    url_variants_filtered = [(url, label) for url, label in url_variants_data if url]
    url_variants = [
        {"url": item["value"], "label": item["label"], "is_duplicate": item["is_duplicate"]}
        for item in util.deduplicate_variants(url_variants_filtered)
    ]

    # build links
    links = []

    # Set a default title so links are not blank.
    if not metadata.title:
        metadata.title = "link"

    # Generate title variants - always start with Original
    title_obj = util.TitleVariants(metadata.title)

    title_variant_list = []
    title_variants_data = [
        (title_obj.original, "Original"),
        (title_obj.ascii_and_emojis, "ASCII + Emoji"),
        (title_obj.ascii_only, "ASCII Only"),
        (title_obj.path_safe, "Path Safe"),
    ]

    title_variant_list = util.deduplicate_variants(title_variants_data)

    # Get inline base64 favicon (from cache or generate on-the-fly)
    favicon_inline = None
    favicon_width = None
    favicon_height = None
    if metadata.favicons:
        # Use cached inline if available
        if metadata.favicons[0].inline_image:
            inline = metadata.favicons[0].inline_image
            if isinstance(inline, dict):
                favicon_inline = inline.get("data_url")
                favicon_width = inline.get("width", html_util.FAVICON_HEIGHT)
                favicon_height = inline.get("height", html_util.FAVICON_HEIGHT)
            else:
                favicon_inline = inline
                favicon_width = html_util.FAVICON_HEIGHT
                favicon_height = html_util.FAVICON_HEIGHT
        # Otherwise generate inline version from the favicon URL
        elif metadata.favicon_url:
            favicon_result = img_util.encode_favicon_inline(
                metadata.favicon_url, html_util.FAVICON_HEIGHT
            )
            if favicon_result:
                favicon_inline = favicon_result.get("data_url")
                favicon_width = favicon_result.get("width")
                favicon_height = favicon_result.get("height")

        if metadata.fragment_title:
            links.append(
                {
                    "header": "Favicon",
                    "html": (
                        f'<img src="{metadata.favicon_url}" '
                        f'height="{html_util.FAVICON_HEIGHT}" /> '
                        f'<a target="_blank" href="{metadata.url}">'
                        f"{util.html_text(util.ascii_text(metadata.fragment_title))}</a>"
                    ),
                }
            )

        links.append(
            {
                "header": "Favicon - Clean",
                "html": (
                    f'<img src="{metadata.favicon_url}" '
                    f'height="{html_util.FAVICON_HEIGHT}" /> '
                    f'<a target="_blank" href="{metadata.url_clean}">'
                    f"{util.html_text(util.ascii_text(metadata.title))}</a>"
                ),
            }
        )

    if metadata.fragment_title:
        links.append(
            {
                "header": "Simple",
                "html": (
                    f'<a target="_blank" href="{metadata.url}">'
                    f"{util.html_text(util.ascii_text(metadata.fragment_title))}</a>"
                ),
            }
        )

    links.append(
        {
            "header": "Simple - Clean",
            "html": (
                f'<a target="_blank" href="{metadata.url_clean}">'
                f"{util.html_text(util.ascii_text(metadata.title))}</a>"
            ),
        }
    )

    template = template_env.get_template("mirror-links.html")
    rendered_html = template.render(
        {
            "title": metadata.title,
            "title_variants": title_variant_list,
            "fragment": metadata.parsed_url.fragment if metadata.parsed_url else "",
            "fragment_text": metadata.fragment_text,
            "fragment_variants": fragment_variants,
            "content_type": metadata.content_type,
            "clipboard_error": metadata.clipboard_error,
            "user_agent": metadata.mirror_data.userAgent if metadata.mirror_data else "",
            "cookie_string": metadata.mirror_data.cookieString if metadata.mirror_data else "",
            "html_size": metadata.mirror_data.htmlSize if metadata.mirror_data else 0,
            "url_variants": url_variants,
            "links": links,
            "favicon": metadata.favicon_url,
            "favicon_inline": favicon_inline,
            "favicon_width": favicon_width,
            "favicon_height": favicon_height,
        }
    )

    resp = make_response(rendered_html)
    return resp


@bp.route("/mirror-text", methods=["GET", "POST"])
def get_mirror_text():
    """
    Return the raw strings for the page.
    """
    metadata = util.get_page_metadata()

    # Parse the HTML.
    extracted_text = text_util.walk_soup_tree_strings(metadata.soup)

    seen_text = set()
    txt = []
    for x in extracted_text:
        if x.keep:
            if x.name == "script.String":
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


@bp.route("/mirror-text-debug", methods=["GET", "POST"])
def get_mirror_text_debug():
    """
    Return debugging info and strings for the page.
    """
    metadata = util.get_page_metadata()

    # Parse the HTML.
    extracted_text = text_util.walk_soup_tree_strings(metadata.soup, rollup=False)

    txt = []
    for x in extracted_text:
        if x.name == "script.String":
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


@bp.route("/mirror-soup-text", methods=["GET", "POST"])
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


@bp.route(
    "/get",
    methods=[
        "GET",
    ],
)
def get_url_response():
    """Use the get_url method to retrieve a URL."""
    url = request.args.get("url")
    if not url:
        return "URL parameter 'url' is required", 400

    # Get the URL response
    resp = url_util.get_url(url)
    if not resp:
        return "Failed to retrieve URL", 500

    return resp.as_dict()


@bp.route("/mirror-clip", methods=["GET", "POST"])
def mirror_clip():
    """Display the contents of the clipboard."""

    template_env = current_app.template_env
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
        template_env,
        "Clipboard Contents",
        clip_text,
        format=metadata.output_format,
        language="json",
    )


@bp.route("/mirror-html-source", methods=["GET", "POST"])
def mirror_html_source():
    """Display the HTML from the clipboard."""

    template_env = current_app.template_env
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


@bp.route("/clip-proxy", methods=["GET"])
def clip_to_post():
    """Copy the contents of a the clipboard into a POST request."""

    from library import docker_util

    template_env = current_app.template_env

    if not docker_util.is_running_in_container():
        # Redirect to the web-tool.py endpoint given in the target query parameter.
        target = request.args.get("target")
        if target:
            # Build URL without the target parameter
            from urllib.parse import urlencode

            from flask import redirect

            # Get all query params except 'target'
            params = {k: v for k, v in request.args.items() if k != "target"}
            query_string = urlencode(params, doseq=True) if params else ""

            new_url = f"http://{request.host}/{target}"
            if query_string:
                new_url += f"?{query_string}"

            return redirect(new_url)

    template = template_env.get_template("clip-proxy.html")
    rendered_html = template.render({})

    resp = make_response(rendered_html)
    return resp


@bp.route("/clip-collector", methods=["POST"])
def clip_collector():
    """Collect chunks of text by batch ID and chunk number."""

    # Validate batchId
    batch_id = request.args.get("batchId")
    if not batch_id:
        return "Missing required parameter: batchId", 400

    try:
        uuid.UUID(batch_id)
    except (ValueError, AttributeError):
        return "Invalid batchId format: must be a valid UUID", 400

    # Validate chunkNum
    chunk_num_str = request.args.get("chunkNum")
    if not chunk_num_str:
        return "Missing required parameter: chunkNum", 400

    try:
        chunk_number = int(chunk_num_str)
    except (ValueError, TypeError):
        return "Invalid chunkNum: must be an integer", 400

    if chunk_number < 1:
        return "Invalid chunkNum: must be positive", 400

    if chunk_number > util.CLIP_CACHE_MAX_CHUNK_NUMBER:
        max_val = util.CLIP_CACHE_MAX_CHUNK_NUMBER
        return (
            f"Invalid chunkNum: exceeds maximum allowed value ({max_val})",
            400,
        )

    # Initialize batch if it doesn't exist
    if batch_id not in util.clip_cache:
        util.clip_cache[batch_id] = {"created_at": time.time(), "chunks": {}}

    util.clip_cache[batch_id]["chunks"][chunk_number] = request.data.decode()

    return "OK"
