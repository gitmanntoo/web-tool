import base64
import json
import logging
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from flask import abort, request, make_response, Response
from jinja2 import Environment, FileSystemLoader
import jsmin
import pyperclip
import yaml

from library import url_util


STATIC_DIR = Path("static")
TEMPLATE_DIR = Path("templates")

# Cache for clip collector.
clip_cache = {}


def get_javascript_file(filename, mode, template_env=None, format: str = "html"):
    # Read the contents of the file

    # Handle the mirror- pattern. These are built using a template.
    if filename.startswith("mirror-"):
        if template_env is None:
            abort(503)  # Service unavailable if the template environment is not set

        template_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
        template = template_env.get_template('mirror.js')
        contents = template.render(
            path=filename,
            format=format,
        )
    else:
        try:
            with open(STATIC_DIR / "javascript" / f"{filename}.js", "r") as f:
                contents = f.read()
        except FileNotFoundError:
            abort(404)  # Not found if the file does not exist

    # Minify the contents if set.
    if mode in ("minify", "bookmarklet"):
        contents = jsmin.jsmin(contents).strip()

    # Add a bookmarklet if set.
    if mode == "bookmarklet":
        contents = f"javascript:(function(){{{contents}}})();"

    # Return the contents
    return contents


def parse_cookie_string(cookie_string, url):
    """
    Parse a cookie string into a list of dictionaries with keys: name, value, domain, path
    - Ignored: expires, size, httpOnly, secure, sameSite
    """
    cookie_string = cookie_string.strip()
    if not cookie_string:
        return []
    
    parsed_url = urlparse(url)
    domain = parsed_url.netloc

    cookies = []
    for cookie in cookie_string.split(";"):
        tokens = cookie.split("=", 1)
        c = {
            "name": tokens[0].strip(), 
            "value": "",
            "domain": domain,
            "path": "/",
        }
        if len(tokens) > 1:
            c["value"] = tokens[1].strip()
        cookies.append(c)

    return cookies


def get_page_metadata():
    """
    Return the metadata for the page.
    """
    batch_id = request.args.get('batchId')

    metadata = {
        "url": request.args.get("url", ""),
        "title": request.args.get("title", ""),
        "headers": dict(request.headers),
        "batch_id": batch_id,
        "text_length": int(request.args.get("textLength", 0)),
        "format": request.args.get("format", "html"),
    }

    if batch_id and batch_id in clip_cache:
        # Collect chunks from the cache.
        all_chunks = []
        for chunk_number in sorted(clip_cache[batch_id].keys()):
            all_chunks.append(clip_cache[batch_id][chunk_number])

        del clip_cache[batch_id]

        metadata["clipboard"] = "".join(all_chunks)
        if len(metadata["clipboard"]) != metadata["text_length"]:
            logging.warning(
                f"Clipboard length {len(metadata['clipboard'])} does not match text length {metadata['text_length']}"
            )
    else:
        metadata["clipboard"] = pyperclip.paste()

    # If contents are not valid JSON, return error with raw clipboard contents.
    if clip := metadata["clipboard"]:
        try:
            clip_json = json.loads(clip)
            metadata.update(clip_json)
        except json.JSONDecodeError as e:
            metadata["jsonDecodeError"] = str(e)
            metadata["rawClip"] = clip
            return metadata
    
    # Parse url into variations.
    parsed = urlparse(metadata.get("url", ""))
    metadata["url_host"] = urlunparse((
        parsed.scheme, parsed.netloc, "", "", "", ""))
    metadata["url_root"] = url_util.get_url_root(metadata.get("url", ""))
    metadata["url_clean"] = urlunparse((
        parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    
    # Parse the cookie string into a dictionary.
    metadata["cookies"] = parse_cookie_string(
        metadata.get("cookieString", ""), metadata.get("url", "")
    )

    return metadata

# Map from coding language to Prism.js class.
LANGUAGE_TO_PRISM_CLASS = {
    "javascript": "language-javascript",
    "html": "language-html",
    "json": "language-json",
    "yaml": "language-yaml",
}


def plain_text_response(
    template_env: Environment,
    page_title: str,
    page_text: str,
    format: str = "html",
    language: str = None,
):
    """
    Return a "plain text" response.
    - If format is `yaml` or `json`, the page_text is rendered with the 
      appropriate content-type if text matches the format.
        - If text is not valid `yaml` or `json`, the page_text is rendered using `text`.
    - The `html` format wraps the page_text in a `<pre><code>` tag with the 
      appropriate Prism.js class for the `language`.

    Args:
        template_env (jinja2.Environment): The Jinja2 environment.
        page_title (str): The title of the page.
        page_text (str): The text of the page.
        format (str): The format of the page (html, yaml, json, text)
        language (str): The coding language of the text (html, javascript, json, yaml).

    Returns:
        flask.Response: The response.
    """

    if format in ("yaml", "json"):
        try:
            # JSON is YAML, so we can parse both as YAML.
            page_text = yaml.safe_load(page_text)

            # If parsing succeeeds, format with the appropriate format and content-type.
            if format == "yaml":
                return Response(
                    response=yaml.dump(page_text, sort_keys=False),
                    status=200,                    
                    mimetype="text/yaml",
                )
            elif format == "json":
                return Response(
                    response=json.dumps(page_text, indent=2),
                    status=200,
                    mimetype="application/json",
                )
        except Exception:
            # If the text is not valid JSON, render it as plain text.
            format = "text"

    if format == "text":
        return Response(
            response=page_text,
            status=200,
            mimetype="text/plain",
        )

    template = template_env.get_template('plain_text.html')

    # Base64 encode the page text so that it can be safely embedded in the HTML.
    clip_b64 = base64.b64encode(page_text.encode()).decode()

    rendered_html = template.render({
        "page_title": page_title,
        "page_text": page_text,
        "clip_b64": clip_b64,
        "language_class": LANGUAGE_TO_PRISM_CLASS.get(language, ""),
    })

    resp = make_response(rendered_html)
    return resp
