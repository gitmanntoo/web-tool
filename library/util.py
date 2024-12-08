import json
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from flask import abort, request
from jinja2 import Environment, FileSystemLoader
import jsmin
import pyperclip

from library import url_util


STATIC_DIR = Path("static")
TEMPLATE_DIR = Path("templates")

# Cache for clip collector.
clip_cache = {}


def get_javascript_file(filename, mode, template_env=None):
    # Read the contents of the file

    # Handle the mirror- pattern. These are built using a template.
    if filename.startswith("mirror-"):
        if template_env is None:
            abort(503)  # Service unavailable if the template environment is not set

        template_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
        template = template_env.get_template('mirror.js')
        contents = template.render(path=filename)
    else:
        try:
            with open(STATIC_DIR / "javascript" / f"{filename}.js", "r") as f:
                contents = f.read()
        except FileNotFoundError:
            abort(404)  # Not found if the file does not exist

    # Minify the contents if set.
    if mode in ("minify","bookmarklet"):
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
    }

    if batch_id and batch_id in clip_cache:
        # Collect chunks from the cache.
        all_chunks = []
        for chunk_number in sorted(clip_cache[batch_id].keys()):
            all_chunks.append(clip_cache[batch_id][chunk_number])

        del clip_cache[batch_id]

        metadata["clipboard"] = "".join(all_chunks)
        if len(metadata["clipboard"]) != metadata["text_length"]:
            print(
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
