import base64
import json
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from flask import Flask, abort, request, make_response
from jinja2 import Environment, FileSystemLoader
import markdown

from library import util
from library import html_util
from library import img_util
from library import url_util

app = Flask(__name__)

# Initialize template environment.
template_loader = FileSystemLoader(util.TEMPLATE_DIR)
template_env = Environment(loader=template_loader)

@app.route('/')
def read_root():
    """Display the README file."""
    return markdown.markdown(open("README.md").read())


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
    template = template_env.get_template('clip-proxy.html')
    rendered_html = template.render({})

    resp = make_response(rendered_html)
    return resp


@app.route('/clip-collector', methods=['POST'])
def clip_collector():
    """Collect chunks of text by batch ID and chunk number."""

    # Read headers.
    batch_id = request.args.get('batchId')
    chunk_number = int(request.args.get('chunkNum'))

    chunk_dict = util.clip_cache.setdefault(batch_id, {})
    chunk_dict[chunk_number] = request.data.decode()

    return "OK"


@app.route('/mirror-clip', methods=['GET', 'POST'])
def mirror_clip():
    """Display the contents of the clipboard."""

    metadata = util.get_page_metadata()

    # Read clipboard contents.
    clip = metadata["clipboard"]

    # If clip is valid JSON, format it with indentation.
    clip_text = clip
    try:
        clip_json = json.loads(clip)
        clip_text = json.dumps(clip_json, indent=2)
    except json.JSONDecodeError:
        pass

    return util.plain_text_response(
        template_env, "Clipboard Contents", clip_text,
        format=metadata["format"],
        language="json",
    )

@app.route('/mirror-html-source', methods=['GET', 'POST'])
def mirror_html_source():
    """Display the HTML from the clipboard."""

    metadata = util.get_page_metadata()

    # Read clipboard contents.
    clip = metadata["clipboard"]

    # If clip is valid JSON, extract the HTML and prettify it.
    html_text = ""
    try:
        clip_json = json.loads(clip)
        if html_raw := clip_json.get("html"):
            html_text = BeautifulSoup(html_raw, "html.parser").prettify()
    except json.JSONDecodeError:
        pass

    return util.plain_text_response(
        template_env,
        "HTML Source",
        html_text,
        format=metadata["format"],
        language="html",
    )


@app.route("/mirror-favicons", methods=["GET", "POST"])
def get_mirror_favicons():
    """
    Return the favicons for the page.
    """

    metadata = util.get_page_metadata()

    # Set the cache key from the url.
    parsed = urlparse(url_util.get_url_root(metadata["url"]))
    metadata["cache_key"] = f"{parsed.netloc}{parsed.path}"

    # Get the favicons.
    favicons = html_util.get_favicon_links(
        metadata["url"],
        metadata["html"],
        include="all",
    )

    # If the first favicon has a cacheKey, set it aside.
    cache_favicon = None
    if favicons and favicons[0].cache_key:
        cache_favicon = favicons[0]
        favicons = favicons[1:]

    # Get the size of each favicon.
    for favicon in favicons:
        if size := url_util.get_image_size(favicon.href):
            favicon.width = size.width
            favicon.height = size.height

    # Sort favicons by area.
    favicons.sort(key=lambda x: x.width * x.height, reverse=True)

    # Add back the cached favicon at the start.
    if cache_favicon:
        if size := url_util.get_image_size(cache_favicon.href):
            cache_favicon.width = size.width
            cache_favicon.height = size.height
        favicons.insert(0, cache_favicon)
    elif favicons:
        # Add the top favicon as the cached favicon.
        html_util.add_favicon_to_cache(
            metadata["cache_key"],
            favicons[0].href,
        )

    metadata["favicons"] = favicons

    template = template_env.get_template('mirror-favicons.html')
    rendered_html = template.render(metadata)

    resp = make_response(rendered_html)
    return resp


@app.route('/convert-ico-to-png', methods=['GET'])
def convert_ico_to_png():
    ico_url = request.args.get('url')

    if not ico_url:
        return "URL parameter 'url' is required", 400

    png_bytes = img_util.convert_image(ico_url, "PNG")
    if png_bytes is not None:
        # Create a response with PNG bytes
        response = make_response(png_bytes)
        response.headers.set('Content-Type', 'image/png')
        return response
    else:
        return "Failed to convert ICO to PNG", 500


@app.route("/mirror-links", methods=["GET", "POST"])
def get_mirror_links():
    """
    Return the links for the page.
    """
    metadata = util.get_page_metadata()

    favicons = html_util.get_favicon_links(
        metadata["url"],
        metadata["html"],
    )
    if favicons:
        metadata["favicon"] = favicons[0].href

    # build urls
    urls = []
    metadata["urls"] = urls

    for u in (
        metadata["url"],
        metadata["url_clean"],
        metadata["url_root"],
        metadata["url_host"],
    ):
        if urls:
            if u.endswith("/"):
                u = u[:-1]
            if u != urls[-1]:
                urls.append(u)
        else:
            urls.append(u)

    # build links
    links = []
    metadata["links"] = links

    if favicons:
        links.append({
            "header": "Obsidian",
            "html": (
                f'<img src="{metadata["favicon"]}" width="20" />'
                f'<a target="_blank" href="{metadata["url"]}">{metadata["title"]}</a>'
            ),
            "markdown": (
                f'![favicon|20]({metadata["favicon"]}) [{metadata["title"]}]({metadata["url"]})'
            ),
        })

        if metadata["url"] != metadata["url_clean"]:
            links.append({
                "header": "Obsidian - Clean",
                "html": (
                    f'<img src="{metadata["favicon"]}" width="20" />'
                    f'<a target="_blank" href="{metadata["url_clean"]}">{metadata["title"]}</a>'
                ),
                "markdown": (
                    f'![favicon|20]({metadata["favicon"]}) [{metadata["title"]}]({metadata["url_clean"]})'
                ),
            })

    links.append({
        "header": "Markdown",
        "html": (
            f'<a target="_blank" href="{metadata["url"]}">{metadata["title"]}</a>'
        ),
        "markdown": (
            f'[{metadata["title"]}]({metadata["url"]})'
        ),
    })

    if metadata["url"] != metadata["url_clean"]:
        links.append({
            "header": "Markdown - Clean",
            "html": (
                f'<a target="_blank" href="{metadata["url_clean"]}">{metadata["title"]}</a>'
            ),
            "markdown": (
                f'[{metadata["title"]}]({metadata["url_clean"]})'
            ),
        })

    metadata["clip_b64"] = base64.b64encode(links[0]["markdown"].encode()).decode()

    template = template_env.get_template('mirror-links.html')
    rendered_html = template.render(metadata)

    resp = make_response(rendered_html)
    return resp


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8532, debug=True)
