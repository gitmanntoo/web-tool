import base64
from dataclasses import dataclass
import fitz
import html
import io
import json
import logging
import psutil
import sys
import time
import tldextract
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from pprint import pprint

from anyascii import anyascii
from bs4 import BeautifulSoup
from flask import abort, request, make_response, Response
from jinja2 import Environment, FileSystemLoader
import jsmin
import pyperclip
import yaml

from library import html_util
from library import url_util
from library.html_util import RelLink


STATIC_DIR = Path("static")
TEMPLATE_DIR = Path("templates")

# Cache for clip collector.
# Structure: {batch_id: {'created_at': timestamp, 'chunks': {chunk_num: data}}}
clip_cache = {}

# Clip cache configuration
CLIP_CACHE_TTL_SECONDS = 600  # 10 minutes
CLIP_CACHE_MAX_BATCHES = 100  # Maximum number of batches to keep
CLIP_CACHE_MAX_CHUNK_NUMBER = 10000  # Maximum chunk number allowed
CLIP_CACHE_MEMORY_LIMIT_PCT = 0.5  # Maximum 50% of available memory


def cleanup_clip_cache():
    """Remove expired batches and enforce size limits on clip_cache.
    
    Removes:
    - Batches older than CLIP_CACHE_TTL_SECONDS
    - Oldest batches if count exceeds CLIP_CACHE_MAX_BATCHES
    - Oldest batches if memory usage exceeds CLIP_CACHE_MEMORY_LIMIT_PCT of available memory
    
    Note: Memory check only happens during cleanup, allowing in-progress operations to complete.
    """
    current_time = time.time()
    
    # Remove expired batches
    expired_batch_ids = [
        batch_id for batch_id, batch_data in clip_cache.items()
        if current_time - batch_data.get('created_at', 0) > CLIP_CACHE_TTL_SECONDS
    ]
    
    for batch_id in expired_batch_ids:
        del clip_cache[batch_id]
        logging.info(f"Removed expired clip_cache batch: {batch_id}")
    
    # Enforce max batch limit by removing oldest
    if len(clip_cache) > CLIP_CACHE_MAX_BATCHES:
        # Sort by creation time and remove oldest
        sorted_batches = sorted(
            clip_cache.items(),
            key=lambda x: x[1].get('created_at', 0)
        )
        
        num_to_remove = len(clip_cache) - CLIP_CACHE_MAX_BATCHES
        for i in range(num_to_remove):
            batch_id = sorted_batches[i][0]
            del clip_cache[batch_id]
            logging.info(f"Removed old clip_cache batch (size limit): {batch_id}")
    
    # Enforce memory limit by removing oldest batches
    try:
        # Get available memory
        memory = psutil.virtual_memory()
        memory_limit = memory.available * CLIP_CACHE_MEMORY_LIMIT_PCT
        
        # Calculate cache size
        cache_size = sys.getsizeof(clip_cache)
        for batch_data in clip_cache.values():
            cache_size += sys.getsizeof(batch_data)
            cache_size += sys.getsizeof(batch_data.get('chunks', {}))
            for chunk in batch_data.get('chunks', {}).values():
                cache_size += sys.getsizeof(chunk)
        
        # Remove oldest batches if over limit
        if cache_size > memory_limit and clip_cache:
            logging.info(
                f"Clip cache size ({cache_size:,} bytes) exceeds memory limit "
                f"({memory_limit:,.0f} bytes). Removing oldest batches."
            )
            
            sorted_batches = sorted(
                clip_cache.items(),
                key=lambda x: x[1].get('created_at', 0)
            )
            
            while cache_size > memory_limit and sorted_batches:
                batch_id = sorted_batches.pop(0)[0]
                del clip_cache[batch_id]
                logging.info(f"Removed old clip_cache batch (memory limit): {batch_id}")
                
                # Recalculate cache size
                cache_size = sys.getsizeof(clip_cache)
                for batch_data in clip_cache.values():
                    cache_size += sys.getsizeof(batch_data)
                    cache_size += sys.getsizeof(batch_data.get('chunks', {}))
                    for chunk in batch_data.get('chunks', {}).values():
                        cache_size += sys.getsizeof(chunk)
    except Exception as e:
        logging.warning(f"Error during memory-based clip_cache cleanup: {e}")


@dataclass
class MirrorData:
    clipboard: str
    url: str = ''
    title: str = ''
    userAgent: str = ''
    cookieString: str = ''
    html: str = ''

    def __post_init__(self):
        """Parse clipboard contents if it's valid JSON and set attributes."""
        if not self.clipboard:
            return

        try:
            data = json.loads(self.clipboard)
            if isinstance(data, dict):
                self.url = data.get('url', '')
                self.title = data.get('title', '')
                self.userAgent = data.get('userAgent', '')
                self.cookieString = data.get('cookieString', '')
                self.html = data.get('html', '')
        except json.JSONDecodeError:
            # If clipboard is not valid JSON, keep it as raw clipboard content
            pass


@dataclass
class PageMetadata:
    """Represents metadata and content for a web page being processed.

    This class handles both the metadata from the request (URL, title, etc.)
    and manages clipboard content loading through the clip cache system.

    Attributes:
        request: The Flask request object containing page metadata
        url: The URL of the page being processed
        title: The page title
        headers: Dictionary of request headers
        batch_id: ID for batched clipboard content
        text_length: Expected length of clipboard content
        output_format: Desired output format (html, etc.)
        clipboard_error: Any error that occurred during clipboard operations
        content_type: Content type of the page
        mirror_data: MirrorData object containing processed clipboard data
    """
    request: request = None
    url: str = ''
    parsed_url: urlparse = None
    clean_url: str = ''
    title: str = ''
    headers: dict = None
    batch_id: str = ''
    text_length: int = 0
    output_format: str = 'html'
    clipboard_error: str = ''
    content_type: str = ''
    mirror_data: MirrorData = None
    soup: BeautifulSoup = None
    fragment_text: str = ''
    favicons: list[RelLink] = None
    page_content: url_util.SerializedResponse = None

    def __post_init__(self):
        """Process request args if request is provided."""
        if not self.request:
            return

        self.url = self.request.args.get("url", "")
        self.parsed_url = urlparse(self.url)
        self.title = self.request.args.get("title", "")
        self.headers = dict(self.request.headers)
        self.batch_id = self.request.args.get('batchId', '')
        self.text_length = int(self.request.args.get("textLength", 0))
        self.output_format = self.request.args.get("format", "html")
        self.clipboard_error = self.request.args.get("clipboardError", "")
        self.content_type = self.request.args.get("contentType", "")

        self.load_clipboard()
        self.parse_html()
        self.resolve_title()
        self.resolve_fragment_text()
        self.resolve_favicons()

    @property
    def url_clean(self) -> str:
        """
        Returns the URL with the without fragment or query string.
        """
        return urlunparse((
            self.parsed_url.scheme,
            self.parsed_url.netloc,
            self.parsed_url.path, '', '', '')).rstrip('/')

    @property
    def url_root(self) -> str:
        """
        Returns the URL with the first path segment.
        """
        path_tokens = self.parsed_url.path.split('/')
        root_path = ''
        if len(path_tokens) > 1:
            root_path = path_tokens[1]

        return urlunparse((
            self.parsed_url.scheme,
            self.parsed_url.netloc,
            root_path, '', '', '')).rstrip('/')

    @property
    def url_host(self) -> str:
        """
        Returns the URL with the host.
        """
        return urlunparse((
            self.parsed_url.scheme,
            self.parsed_url.netloc,
            '', '', '', '')).rstrip('/')

    @property
    def url_domain(self):
        extracted = tldextract.extract(self.parsed_url.netloc)

        # Return domain name starting with www if subdomain is 'www'
        if extracted.subdomain == 'www':
            return f'{extracted.subdomain}.{extracted.domain}.{extracted.suffix}'
        else:
            return f'{extracted.domain}.{extracted.suffix}'

    @property
    def cache_key(self):
        """
        Returns the cache key for the page. Used for favicon caching.
        """
        path_tokens = self.parsed_url.path.split('/')
        root_path = ''
        if len(path_tokens) > 1:
            root_path = path_tokens[1]

        return f'{self.parsed_url.netloc}/{root_path}'


    @property
    def favicon(self):
        return self.favicons[0] if self.favicons else None

    @property
    def favicon_url(self):
        return self.favicon.href if self.favicon else None

    @property
    def favicon_base64(self):
        """Get the favicon as a base64 encoded data URL."""
        if not self.favicon or not self.favicon.content:
            return None
        return f"data:{self.favicon.image_type};base64,{base64.b64encode(self.favicon.content).decode()}"

    @property
    def urls(self) -> list[str]:
        urls = []
        for u in (
            self.url,
            self.url_clean,
            self.url_root,
            self.url_host,
        ):
            if u.endswith('/'):
                u = u[:-1]

            if u not in urls:
                urls.append(u)

        return urls

    def load_clipboard(self):
        """Load clipboard data from clip_cache."""
        if self.clipboard_error:
            # Clipboard error occurred, so we can't load clipboard data.
            self.page_content = url_util.get_url(self.url)
            if not self.page_content.error:
                self.content_type = self.page_content.content_type
            return

        if self.batch_id and self.batch_id in clip_cache:
            # Collect chunks from the cache.
            all_chunks = []
            batch_data = clip_cache[self.batch_id]
            chunks = batch_data.get('chunks', {})
            
            for chunk_number in sorted(chunks.keys()):
                all_chunks.append(chunks[chunk_number])

            del clip_cache[self.batch_id]

            self.mirror_data = MirrorData("".join(all_chunks))
            if len(self.mirror_data.clipboard) != self.text_length:
                logging.warning(
                    "Clipboard length "
                    f"{len(self.mirror_data.clipboard)} does not match text length "
                    f"{self.text_length}"
                )
        else:
            self.mirror_data = MirrorData(pyperclip.paste())

    def parse_html(self):
        """
        Parse HTML from clipboard content.
        """
        if not self.mirror_data or not self.mirror_data.html:
            return

        try:
            self.soup = BeautifulSoup(
                self.mirror_data.html, "html.parser")
        except Exception:
            pass

    def resolve_title(self):
        """
        Resolve the title from the URL.
        """
        if self.title:
            # Title was already set.
            return

        if self.soup:
            # Try to get title from the first H1 tag.
            h1 = self.soup.find("h1")
            h1_text = h1.text.strip() if h1 else ""
            if h1_text:
                self.title = h1_text
            return

        # TODO: Get title from non-HTML content.

        # Fallback to using the URL.
        self.title = self.url

    def resolve_fragment_text(self):
        """
        Resolve the fragment text from the URL. ¶
        """
        if not self.parsed_url.fragment:
            # No fragment in the URL.
            return

        if not self.soup:
            # No HTML content. Just use the fragment.
            self.fragment_text = self.parsed_url.fragment
            return

        # Look for a heading using the fragment as the id.
        heading = self.soup.find(["h1", "h2", "h3", "h4", "h5", "h6"], id=self.parsed_url.fragment)
        if heading:
            if h := heading.text.strip():
                self.fragment_text = h
                return

        # Look for an anchor tag with the fragment as the href.
        anchor = self.soup.find(href=f'#{self.parsed_url.fragment}')
        if not anchor:
            # Look for an anchor tag with the url as the href.
            url_with_fragment = urlunparse((
                self.parsed_url.scheme,
                self.parsed_url.netloc,
                self.parsed_url.path, '', '', self.parsed_url.fragment))
            anchor = self.soup.find(href=url_with_fragment)

        if anchor and (a := anchor.text.strip()):
            self.fragment_text = a
            return

        # If no anchor was found or anchor did not have text, check the previous and next siblings.
        if not anchor:
            return
        # Get the previous sibling element if the anchor has no text.
        prev = anchor.find_previous_sibling()
        if prev and prev.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            if p := prev.text.strip():
                self.fragment_text = p
                return

        # Get the next sibling element if the anchor has no text.
        next = anchor.find_next_sibling()
        if next and next.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            if n := next.text.strip():
                self.fragment_text = n
                return

        # Fallback to the fragment.
        self.fragment_text = self.parsed_url.fragment

    @property
    def fragment_title(self) -> str:
        if f :=self.fragment_text.rstrip('¶'):
            return f'{f} - {self.title}'

        return ''

    def resolve_favicons(self):
        self.favicons = html_util.get_favicon_links(
            self.url,
            self.soup,
        )


def get_javascript_file(filename: str, mode: str, template_env=None, format: str = "html") -> str:
    """Get JavaScript file contents, optionally processing it as a template or minifying it.

    Args:
        filename: Name of the JavaScript file without extension. If starts with 'mirror-',
                 it will be processed as a template using mirror.js.
        mode: Processing mode - 'normal', 'minify', or 'bookmarklet'. Minify will compress
              the code, bookmarklet will both minify and wrap for browser bookmarklet use.
        template_env: Optional Jinja2 environment for template processing. Required if
                     filename starts with 'mirror-'.
        format: Output format for template rendering, defaults to 'html'.

    Returns:
        str: The processed JavaScript code contents.

    Raises:
        abort(404): If the file is not found.
        abort(503): If template_env is required but not provided.
    """

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

    # Replace the default host with current host.
    contents = contents.replace("http://localhost:8532", f"http://{request.host}")

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


def handle_clipboard_error(metadata: PageMetadata):
    """
    Handle cases where there was an error reading from the clipboard.
    This typically happens with non-HTML content like PDFs.

    Args:
        metadata (PageMetadata): Page metadata object

    Returns:
        PageMetadata: Updated metadata with empty text content
    """

    if not metadata.content_type:
        metadata.page_content = url_util.get_url(metadata.url)
        if metadata.page_content.status_code != 200:
            metadata.content_type = 'unknown/unknown'
        else:
            metadata.content_type = metadata.page_content.content_type

    match metadata.content_type:
        case "application/pdf":
            # Load the pdf and get title from metadata.
            pdf_stream = io.BytesIO(metadata.page_content.content)
            doc = fitz.open("pdf", pdf_stream.read())
            pprint(doc.metadata)
            metadata.title = doc.metadata.get('title', '')

    if not metadata.title:
        metadata.title = f'{metadata.content_type} - {metadata.url}'

    return metadata


def get_page_metadata() -> PageMetadata:
    """
    Return the metadata for the page. The page contents are read from the 
    clipboard through the clip_cache.
    - If a clipboard error occurred, the URL may be pointing to a document (e.g. PDF)
        - In this case, attempt to extract information from the document itself.
    - For normal documents, the contents should be in the clip_cache.
    """
    metadata = PageMetadata(request)

    # Load clipboard data.
    if metadata.clipboard_error:
        handle_clipboard_error(metadata)

    # # Try to parse HTML from the clipboard.
    # metadata["soup"] = None
    # try:
    #     metadata["soup"] = BeautifulSoup(metadata["html"], "html.parser")

    #     if not metadata.get("title"):
    #         # Get title from the first H1 tag.
    #         h1 = metadata["soup"].find("h1")
    #         if h1:
    #             metadata["title"] = h1.text

    #     # If URL has a fragment, get the text from the fragment.
    #     metadata["fragment_text"] = get_fragment_text(
    #         metadata["soup"], metadata["url"])
    #     if metadata["fragment_text"]:
    #         metadata["fragment_title"] = (
    #             f'{metadata["fragment_text"]} - {metadata["title"]}')
    # except Exception:
    #     pass

    # # Generate ASCII version of title
    # metadata["title_ascii"] = anyascii(metadata["title"])
    # metadata["fragment_title_ascii"] = anyascii(
    #     metadata.get("fragment_title", ""))

    # # Generate HTML-safe title
    # metadata["title_html"] = html.escape(metadata["title_ascii"])
    # metadata["fragment_title_html"] = html.escape(
    #     metadata.get("fragment_title", ""))

    # # Parse url into variations.
    # parsed = urlparse(metadata.get("url", ""))
    # metadata["url_host"] = urlunparse((
    #     parsed.scheme, parsed.netloc, "", "", "", ""))
    # metadata["url_root"] = url_util.get_url_root(metadata.get("url", ""))
    # metadata["url_clean"] = urlunparse((
    #     parsed.scheme, parsed.netloc, parsed.path, "", "", ""))

    # # Parse the cookie string into a dictionary.
    # metadata["cookies"] = parse_cookie_string(
    #     metadata.get("cookieString", ""), metadata.get("url", "")
    # )

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


def ascii_text(text: str) -> str:
    return anyascii(text)


def html_text(text: str) -> str:
    return html.escape(text)
