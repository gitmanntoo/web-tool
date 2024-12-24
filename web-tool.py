import base64
import json
import logging
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from flask import Flask, abort, request, make_response, redirect, Response
from jinja2 import Environment, FileSystemLoader
import markdown

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
            new_url = f"http://{request.host}/{target}?{request.query_string.decode()}"
            return redirect(new_url)

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
            favicon.image_type = size.image_type

    # Sort favicons.
    favicons = html_util.sort_favicon_links(favicons, include='all')

    # Add back the cached favicon at the start.
    if cache_favicon:
        if size := url_util.get_image_size(cache_favicon.href):
            cache_favicon.width = size.width
            cache_favicon.height = size.height
            cache_favicon.image_type = size.image_type
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
        if u.endswith('/'):
            u = u[:-1]

        if u not in urls:
            urls.append(u)

    # build links
    links = []
    metadata["links"] = links

    # Set a default title so links are not blank.
    if metadata["title"] == "":
        metadata["title"] = "link"

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


@app.route("/mirror-text", methods=["GET", "POST"])
def get_mirror_text():
    """
    Return the raw strings for the page.
    """
    metadata = util.get_page_metadata()

    # Parse the HTML.
    soup = BeautifulSoup(metadata["html"], "html.parser")
    extracted_text = text_util.walk_soup_tree_strings(soup)

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
    soup = BeautifulSoup(metadata["html"], "html.parser")
    extracted_text = text_util.walk_soup_tree_strings(soup, rollup=False)

    txt = []
    for idx, x in enumerate(extracted_text):
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
    soup = BeautifulSoup(metadata["html"], "html.parser")
    soup_text = text_util.remove_repeated_lines(soup.get_text("\n"))

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


if __name__ == "__main__":
    if docker_util.is_running_in_container():
        port = 8532
        debug_flag = False
    else:
        port = 8535
        debug_flag = True

    app.run(host="0.0.0.0", port=port, debug=debug_flag)
