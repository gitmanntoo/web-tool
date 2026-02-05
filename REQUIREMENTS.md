# Web-Tool Product Requirements Document

## Overview

Web-tool is a web utility service that captures information from web pages through bookmarklets, processes clipboard data, and provides various endpoints for content extraction, transformation, and caching. The application follows a capture-and-process pattern where bookmarklets collect page data client-side and POST it to server endpoints for analysis.

**Base URL:** `http://localhost:8532` (default port shown; configurable via `-p` parameter)

---

## Architecture

### Data Flow

1. **Capture Phase**: Browser bookmarklets capture page metadata (URL, title, HTML, cookies, user agent)
2. **Transmission Phase**: Captured data is split into chunks and sent to the clipboard collection system
3. **Processing Phase**: Server endpoints retrieve and process the data from the clipboard cache
4. **Output Phase**: Results are returned in multiple formats (HTML, JSON, plain text)

### Clipboard System

The application uses a batch-based clipboard cache system to handle large data payloads that exceed practical clipboard size limits. See [Clipboard System](#clipboard-system) section below.

---

## Bookmarklets

A bookmarklet is a browser bookmark containing JavaScript code that executes on the current page. Web-tool provides several bookmarklets that capture different types of content from web pages.

**How to use:**
1. Click the bookmarklet link below to open it in a new page
2. Copy the JavaScript code from the page
3. Create a new bookmark in your browser and paste the JavaScript as the URL
4. Click the bookmark on any web page to execute it

**Dynamic Host Configuration**: The host in bookmarklets automatically matches the port used when running web-tool. If the port is changed, bookmarklets are automatically updated.

### Available Bookmarklets

#### `links` Bookmarklet
**URL:** [`/js/mirror-links.js?mode=bookmarklet`](http://localhost:8532/js/mirror-links.js?mode=bookmarklet)

**Purpose:** Generates links for the current page in multiple formats (Obsidian with favicon, standard markdown)

**Captures:**
- Page URL (with variants: original, clean, root, host)
- Page title (with variants: original, ASCII+emoji, ASCII-only, path-safe)
- First available favicon
- Fragment identifiers if present

**Processing:** Captures the page URL, title, HTML, and favicon information. Generates multiple link formats from a single capture. The first link variant is automatically copied to the clipboard.

**Implementation:** [templates/mirror.js](templates/mirror.js) with mode=`mirror-links`

---

#### `favicons` Bookmarklet
**URL:** [`/js/mirror-favicons.js?mode=bookmarklet`](http://localhost:8532/js/mirror-favicons.js?mode=bookmarklet)

**Purpose:** Discovers and caches all available favicons for the current page

**Captures:**
- All favicon URLs found in page metadata
- MIME types and image dimensions
- Domain information for cache key generation

**Processing:** Queries the favicon system to find all available favicons for the page domain. Returns results in the format `<page_url_root>: <favicon_url>`, matching the favicon cache format.

**Implementation:** [templates/mirror.js](templates/mirror.js) with mode=`mirror-favicons`

---

#### `text` Bookmarklet
**URL:** [`/js/mirror-text.js?mode=bookmarklet`](http://localhost:8532/js/mirror-text.js?mode=bookmarklet)

**Purpose:** Extracts human-readable text from the page using NLP techniques

**Captures:**
- Full HTML content
- Page metadata (URL, title, user agent, cookies)
- Script tag contents (via NLP analysis)

**Processing:** Uses Natural Language Toolkit (NLTK) to analyze HTML and extract text that appears to be content. Intelligently includes snippets from `<script>` tags that contain readable text.

**Implementation:** [templates/mirror.js](templates/mirror.js) with mode=`mirror-text`

---

#### `soup-text` Bookmarklet
**URL:** [`/js/mirror-soup-text.js?mode=bookmarklet`](http://localhost:8532/js/mirror-soup-text.js?mode=bookmarklet)

**Purpose:** Extracts text using BeautifulSoup's simple text extraction method

**Captures:**
- Full HTML content
- Page metadata (URL, title, user agent, cookies)

**Processing:** Uses BeautifulSoup's `get_text()` method for text extraction. This method is simpler than NLP-based extraction and excludes `<script>` tag contents. Useful when script content causes issues.

**Implementation:** [templates/mirror.js](templates/mirror.js) with mode=`mirror-soup-text`

---

#### `html-source` Bookmarklet
**URL:** [`/js/mirror-html-source.js?mode=bookmarklet`](http://localhost:8532/js/mirror-html-source.js?mode=bookmarklet)

**Purpose:** Displays the page's HTML source with syntax highlighting

**Captures:**
- Full HTML content
- Page URL for context

**Processing:** Retrieves HTML from clipboard and displays it with Prism.js syntax highlighting for readability. Note: May fail on very large or complex pages due to rendering overhead.

**Implementation:** [templates/mirror.js](templates/mirror.js) with mode=`mirror-html-source`

---

#### `html-source-text` Bookmarklet
**URL:** [`/js/mirror-html-source.js?mode=bookmarklet&format=text`](http://localhost:8532/js/mirror-html-source.js?mode=bookmarklet&format=text)

**Purpose:** Displays page HTML source as plain text without formatting

**Captures:**
- Full HTML content
- Page URL for context

**Processing:** Returns raw HTML as plain text without syntax highlighting. More reliable than the formatted version for large or complex pages.

**Implementation:** [templates/mirror.js](templates/mirror.js) with mode=`mirror-html-source` with format=`text`

---

## Endpoints

### Core Infrastructure Endpoints

#### `GET /` — Display Application Home Page

**Purpose:** Serves the application homepage with README content and links to bookmarklets

**Response:**
- **Format:** HTML
- **Content:** Rendered README.md with dynamic host substitution
- **HTTP Status:** 200 OK

**Implementation:** [web-tool.py](web-tool.py) - `read_root()` function

---

#### `GET /js/<filename>.js` — Serve JavaScript Files

**Purpose:** Serves JavaScript files with optional transformations (minification, bookmarklet wrapping)

**Request Parameters:**
- `filename` (path): JavaScript file name without extension (e.g., `mirror-links`, `mirror-text`)
- `mode` (query): Processing mode - `normal` (default), `minify`, or `bookmarklet`
- `format` (query): Output format - `html` (default) or `text`

**Response Variations:**
- **format=html:**
  - Returns HTML page with JavaScript displayed in `<pre><code>` tag with Prism.js syntax highlighting
  - Useful for copying code or reviewing bookmarklet contents
  - MIME type: `text/html`

- **format=text:**
  - Returns plain JavaScript code wrapped in HTML language container
  - MIME type: `text/html`

- **mode=bookmarklet:**
  - Minifies JavaScript code
  - Wraps in IIFE: `javascript:(function(){...})()`
  - Automatically substitutes `localhost:8532` with the current request host
  - Returns as displayable HTML page

**Error Handling:**
- 404 Not Found: File does not exist
- 503 Service Unavailable: Template environment not configured (internal error)

**Implementation:** [web-tool.py](web-tool.py) - `serve_js()` function; [library/util.py](library/util.py) - `get_javascript_file()` function

---

### Clipboard System Endpoints

#### `GET /clip-proxy` — Clipboard Proxy Entrypoint

**Purpose:** Provides a bridge between clipboard captures and POST endpoints. In non-container environments, redirects to target endpoint. In container environments, serves an interactive proxy page.

**Request Parameters:**
- `target` (query): Name of the endpoint to redirect to (e.g., `mirror-clip`)

**Response:**
- **Non-container installations:** HTTP 302 redirect to the target endpoint with all query parameters preserved (except `target`)
- **Container installations:** HTML page containing an embedded iframe/proxy for clipboard access via `clip-collector` and `mirror-clip` endpoints
- **MIME type:** `text/html`

**Use Case:** Bookmarklets cannot directly access the system clipboard in containers, so they use this proxy to collect clipboard data in chunks.

**Implementation:** [web-tool.py](web-tool.py) - `clip_to_post()` function; [templates/clip-proxy.html](templates/clip-proxy.html)

---

#### `POST /clip-collector` — Collect Clipboard Data Chunks

**Purpose:** Collects large clipboard data split into numbered chunks and stores in batch cache

**Request Parameters (Query String):**
- `batchId` (required): UUID identifying the clipboard batch
- `chunkNum` (required): Positive integer indicating chunk sequence number

**Request Body:**
- Raw text data (UTF-8 encoded) representing one chunk of the full clipboard content

**Response:**
- **Success:** HTTP 200 OK with plain text message "OK"
- **Validation Errors:** HTTP 400 Bad Request with descriptive error messages:
  - Missing or invalid `batchId` (must be valid UUID)
  - Missing or invalid `chunkNum` (must be positive integer)
  - `chunkNum` exceeds maximum allowed value (10000)

**Data Storage:**
- Stores chunk data in [`clip_cache`](library/util.py) with structure: `{batchId: {created_at: timestamp, chunks: {chunkNum: data}}}`
- Cache is subject to TTL (10 minutes) and memory limits
- Cleanup happens automatically before each request

**Implementation:** [web-tool.py](web-tool.py) - `clip_collector()` function; [library/util.py](library/util.py) - `cleanup_clip_cache()` function

---

#### `GET|POST /mirror-clip` — Display Clipboard Contents

**Purpose:** Retrieves and displays the captured clipboard data in JSON or plain text format

**Request Parameters:**
- `batchId` (query, optional): UUID referencing chunks stored in `clip_cache`
- `textLength` (query, optional): Expected total length of clipboard content (for validation)
- `format` (query, optional): Output format - `html` (default), `json`, `yaml`, or `text`
- `url` (query, optional): Page URL (passed through from bookmarklet)
- `title` (query, optional): Page title (passed through from bookmarklet)
- Other page metadata query parameters (see [PageMetadata](library/util.py))

**Data Source:**
- If `batchId` provided: Reconstructs clipboard from chunks stored in `clip_cache`
- Otherwise: Reads clipboard using `pyperclip.paste()` (local clipboard access)

**Response Variations:**

- **format=html (default):**
  - If content is valid JSON: Displays formatted JSON in HTML page with Prism.js highlighting
  - Otherwise: Displays raw clipboard text with syntax highlighting
  - MIME type: `text/html`

- **format=json:**
  - Parses clipboard as JSON (if valid) and returns formatted JSON
  - Falls back to plain text if invalid JSON
  - MIME type: `application/json`

- **format=yaml:**
  - Parses clipboard as YAML (if valid) and returns formatted YAML
  - Falls back to plain text if invalid
  - MIME type: `text/yaml`

- **format=text:**
  - Returns raw clipboard content without formatting
  - MIME type: `text/plain`

**Data Processing:**
The clipboard content is parsed by [MirrorData](library/util.py) which extracts structured fields:
- `url`: Page URL captured from bookmarklet
- `title`: Page title captured from bookmarklet
- `userAgent`: Browser user agent string
- `cookieString`: Semicolon-separated cookie list
- `html`: Full HTML page content (if captured)
- `htmlSize`: Size of HTML content in bytes

**Error Handling:**
- If `batchId` provided but not found in cache: Falls back to local clipboard
- If clipboard is empty or invalid: Returns empty response or error message

**Implementation:** [web-tool.py](web-tool.py) - `mirror_clip()` function; [library/util.py](library/util.py) - `PageMetadata` class, `MirrorData` class

---

### Content Extraction Endpoints

#### `GET|POST /mirror-text` — Extract Page Text with NLP

**Purpose:** Extracts human-readable text from captured HTML using NLTK-based analysis

**Request Parameters:**
- Standard page metadata (see [PageMetadata](library/util.py)): `url`, `title`, `format`, `batchId`, `textLength`, etc.

**Response Variations:**

- **format=html (default):**
  - Displays extracted text in HTML page with plain text formatting
  - MIME type: `text/html`

- **format=text:**
  - Returns extracted text as plain UTF-8 text
  - MIME type: `text/plain`

**Processing Details:**
- Uses [text_util.walk_soup_tree_strings()](library/text_util.py) to traverse HTML tree and extract text segments
- Intelligently filters content using word count, token analysis, and content type detection (via Magika)
- **Includes** text from `<script>` tags if detected as human-readable content
- Removes repeated consecutive blank lines
- Deduplicates text segments from script contexts

**Implementation:** [web-tool.py](web-tool.py) - `get_mirror_text()` function; [library/text_util.py](library/text_util.py) - `walk_soup_tree_strings()` function

---

#### `GET|POST /mirror-text-debug` — Debug Page Text Extraction

**Purpose:** Provides detailed analysis of text extraction process for troubleshooting

**Request Parameters:**
- Standard page metadata (see [PageMetadata](library/util.py))

**Response:**
- Plain text output showing analysis details for each extracted text segment
- MIME type: `text/plain`

**Output Format:**
For each segment, displays:
- Depth level in HTML tree (indentation)
- KEEP/DROP indicator (whether segment passes content filters)
- HTML tag name
- Line count, word count, token count
- Word percentage analysis
- Content category classification
- Standard deviation metrics (min/max)
- Magika content type detection result
- Actual text content

**Use Case:** Debugging why certain text is or isn't being extracted

**Implementation:** [web-tool.py](web-tool.py) - `get_mirror_text_debug()` function; [library/text_util.py](library/text_util.py) - `walk_soup_tree_strings()` function

---

#### `GET|POST /mirror-soup-text` — Extract Text Using BeautifulSoup

**Purpose:** Extracts text from HTML using BeautifulSoup's built-in text extraction

**Request Parameters:**
- Standard page metadata (see [PageMetadata](library/util.py))

**Response:**
- Plain text output extracted from HTML
- Newlines preserved as found by BeautifulSoup's `get_text("\n")` method
- MIME type: `text/plain`

**Differences from /mirror-text:**
- Simpler extraction without NLP analysis
- **Excludes** text from `<script>` and `<style>` tags
- Faster processing
- More consistent but potentially less comprehensive results

**Implementation:** [web-tool.py](web-tool.py) - `get_mirror_soup_text()` function; [library/text_util.py](library/text_util.py) - `remove_repeated_lines()` function

---

#### `GET|POST /mirror-html-source` — Display HTML Source

**Purpose:** Retrieves and displays the HTML source from captured clipboard

**Request Parameters:**
- Standard page metadata (see [PageMetadata](library/util.py)): `url`, `format`, `batchId`, etc.

**Response Variations:**

- **format=html (default):**
  - Prettified HTML displayed in HTML page with Prism.js syntax highlighting
  - MIME type: `text/html`

- **format=text:**
  - Returns plain HTML without prettification or syntax highlighting
  - MIME type: `text/html`

**Processing:**
- Parses captured HTML using BeautifulSoup
- Prettifies output for readability
- Falls back to clipboard contents if HTML parsing fails

**Error Handling:**
- Large or complex HTML may fail to prettify gracefully
- Graceful fallback to raw clipboard content

**Implementation:** [web-tool.py](web-tool.py) - `mirror_html_source()` function

---

### Link Generation Endpoint

#### `GET|POST /mirror-links` — Generate Links in Multiple Formats

**Purpose:** Generates copy-ready links in multiple formats with variants for different use cases

**Request Parameters:**
- Standard page metadata (see [PageMetadata](library/util.py)): `url`, `title`, `format`, `batchId`, etc.

**Response:**
- HTML page displaying multiple link variants
- Each link variant is displayed as a clickable HTML link with visual formatting
- MIME type: `text/html`

**Link Variants Generated:**

**URL Variants:**
- **Original:** Full URL as captured (includes query string)
- **With Fragment:** Original URL including anchor fragment
- **Clean:** URL with fragment and query string removed
- **Root:** First path segment only (e.g., `https://example.com/docs`)
- **Host:** Domain and protocol only (e.g., `https://example.com`)

**Title Variants:**
- **Original:** Exact title as captured from page
- **ASCII + Emoji:** Unicode converted to ASCII but emoji characters preserved
- **ASCII Only:** Full ASCII conversion; emoji converted to ASCII equivalents
- **Path Safe:** Title converted to valid filename (removes invalid characters, converts unicode)

**Link Formats Generated (if favicon available):**
- **Favicon link:** Image with favicon and fragment title combined with original URL
- **Favicon Clean link:** Image with favicon and title combined with clean URL
- **Simple link:** Just text link with fragment title and original URL
- **Simple Clean link:** Just text link with title and clean URL

**Favicon Discovery:**
- Automatically retrieves first cached favicon for the page domain
- If no favicon cached: Automatically caches the top favicon for future use
- Uses [favicon cache system](#favicon-system) with three-tier priority

**Implementation:** [web-tool.py](web-tool.py) - `get_mirror_links()` function; [library/util.py](library/util.py) - `TitleVariants` class; [library/url_util.py](library/url_util.py) - URL parsing functions

---

### Favicon Management Endpoints

#### Favicon System Overview

The favicon system uses a three-tier hierarchical cache:

1. **User Overrides** (`static/favicon-overrides.yml`) — Highest priority
   - Manual customizations edited by users
   - Domain-level: `example.com: https://example.com/favicon.ico`
   - Path-level: `example.com/docs: https://example.com/docs/favicon.ico`

2. **App Defaults** (`static/favicon.yml`) — Medium priority
   - Pre-configured favicons distributed with the application
   - Same format as overrides

3. **Auto-Discovered Cache** (`local-cache/favicon.yml` or `/data/favicon.yml` in container) — Lowest priority
   - Dynamically discovered on first access
   - Automatically cached for subsequent requests

**Cache Key Rules:**
- **Domain only** (`example.com`): Applies to all pages on domain
- **Domain + path** (`example.com/docs`): Applies to specific section (first path segment)
- `www` prefix is automatically normalized (`www.example.com` → `example.com`)
- More specific cache keys take precedence (path > domain)

**Cache TTL:** In-memory cache reloads from disk every 300 seconds (configurable)

---

#### `GET|POST /mirror-favicons` — Discover and Manage Favicons

**Purpose:** Discovers all available favicons for a page, displays them with metadata, manages user overrides

**Request Parameters:**
- Standard page metadata (see [PageMetadata](library/util.py)): `url`, etc.

**Response:**
- HTML page displaying:
  - Currently cached favicon for the domain (if exists)
  - All discovered favicons from page metadata
  - Favicon dimensions (width, height)
  - Favicon image type (png, ico, svg, etc.)
  - Current cached favicon status and source file
  - Three-tier cache file status and contents
  - "Add to Overrides" buttons for each favicon

**Processing Details:**
- Queries page HTML for favicon link tags
- Retrieves favicon dimensions and type using image analysis
- Determines which cache file (if any) contains each favicon
- Auto-caches the top favicon if none currently cached
- Displays cache precedence and file information

**Cache Source Detection:**
Each favicon shows which cache file it comes from:
- `User Overrides` (file path: `static/favicon-overrides.yml`)
- `App Defaults` (file path: `static/favicon.yml`)
- `Auto-Discovered` (file path: `local-cache/favicon.yml` or `/data/favicon.yml` in container)
- `None` (not in any cache)

**User Interface Elements:**
- "Add to Overrides" button available for each favicon
- Scope selector: Domain-level or Path-level override
- Real-time cache update feedback

**Implementation:** [web-tool.py](web-tool.py) - `get_mirror_favicons()` function; [library/html_util.py](library/html_util.py) - `get_favicon_links()`, `sort_favicon_links()`, `add_favicon_to_cache()` functions

---

#### `POST /add-favicon-override` — Save Favicon Override

**Purpose:** Adds or updates a favicon override in the user overrides file

**Request Body (JSON):**
- `favicon_url` (required): URL of the favicon to cache
- `page_url` (required): URL of the page (used to determine cache key)
- `scope` (optional, default: `domain`): Cache scope - `domain` or `path`

**Response (JSON):**

**Success (HTTP 200):**
```json
{
  "success": true,
  "cache_key": "example.com" or "example.com/docs"
}
```

**Error (HTTP 400 or 500):**
```json
{
  "success": false,
  "error": "Error message describing the problem"
}
```

**Processing:**
- Parses `page_url` to extract domain (and path if scope=`path`)
- Normalizes domain by removing `www.` prefix
- Loads existing overrides from `static/favicon-overrides.yml`
- Adds/updates the new override
- Writes file back, preserving header comments and YAML formatting
- Invalidates in-memory cache to force reload on next request

**Error Handling:**
- 400 Bad Request: Missing required parameters
- 500 Internal Server Error: File write errors or parsing issues

**Implementation:** [web-tool.py](web-tool.py) - `add_favicon_override()` function; [library/html_util.py](library/html_util.py) - cache management functions

---

### Image Conversion Endpoints

#### `GET /convert-ico-to-png` — Convert ICO to PNG

**Purpose:** Converts ICO format favicon images to PNG for broader compatibility

**Request Parameters:**
- `url` (required): URL of the ICO file to convert

**Response:**
- **Success:** Binary PNG image data
  - MIME type: `image/png`
  - HTTP Status: 200 OK

**Error Handling:**
- 400 Bad Request: Missing `url` parameter
- 500 Internal Server Error: Conversion failed (ICO file invalid, network error, etc.)

**Processing:**
- Downloads ICO file from provided URL
- Converts to PNG using CairoSVG/Pillow pipeline
- Returns binary PNG data

**Implementation:** [web-tool.py](web-tool.py) - `convert_ico_to_png()` function; [library/img_util.py](library/img_util.py) - `convert_ico()` function

---

#### `GET /convert-svg-to-png` — Convert SVG to PNG

**Purpose:** Converts SVG format images to PNG for compatibility with favicon systems

**Request Parameters:**
- `url` (required): URL of the SVG file to convert

**Response:**
- **Success:** Binary PNG image data
  - MIME type: `image/png`
  - HTTP Status: 200 OK

**Error Handling:**
- 400 Bad Request: Missing `url` parameter
- 500 Internal Server Error: Conversion failed (SVG file invalid, network error, etc.)

**Processing:**
- Downloads SVG file from provided URL
- Converts to PNG using CairoSVG
- Returns binary PNG data

**Implementation:** [web-tool.py](web-tool.py) - `convert_svg_to_png()` function; [library/img_util.py](library/img_util.py) - `convert_svg()` function

---

### URL Utility Endpoints

#### `GET /get` — Fetch URL Content

**Purpose:** Retrieves and returns the contents of a URL with metadata

**Request Parameters:**
- `url` (required): URL to retrieve

**Response:**
- JSON object containing:
  - `status_code`: HTTP status code from the URL
  - `content_type`: MIME type of the response
  - `content`: Response body (raw bytes or decoded text)
  - `error`: Error message if request failed
  - Additional metadata fields (see [SerializedResponse](library/url_util.py))

**MIME type:** `application/json`

**Error Handling:**
- 400 Bad Request: Missing `url` parameter
- 500 Internal Server Error: URL fetch failed

**Processing:**
- Uses [url_util.get_url()](library/url_util.py) which handles:
  - HTTP/HTTPS protocols
  - Redirects
  - Content encoding
  - Error handling and timeouts

**Implementation:** [web-tool.py](web-tool.py) - `get_url_response()` function; [library/url_util.py](library/url_util.py) - `get_url()` function

---

#### `GET|POST /debug/url-variants` — Test URL Variant Generation

**Purpose:** Interactive test page for URL variant generation; useful for validating URL parsing logic

**Request Parameters:**
- `POST` request with form data: `url` (the URL to parse)

**Response:**
- HTML page displaying generated URL variants for the input URL
- Shows all 5 variant types: Original, With Fragment, Clean, Root, Host
- Highlights duplicate variants with visual indicator

**Processing:**
- Parses input URL using Python's `urlparse`
- Generates all variant types as done by [PageMetadata](library/util.py)
- Deduplicates variants
- Returns interactive form for testing

**Implementation:** [web-tool.py](web-tool.py) - `debug_url_variants()` function

---

#### `GET|POST /debug/title-variants` — Test Title Variant Generation

**Purpose:** Interactive test page for title variant generation; validates title transformation logic

**Request Parameters:**
- `POST` request with form data: `title` (the title to transform)

**Response:**
- HTML page displaying generated title variants for the input title
- Shows all 4 variant types: Original, ASCII + Emoji, ASCII Only, Path Safe
- Highlights duplicate variants with visual indicator

**Processing:**
- Generates title variants using [TitleVariants](library/util.py) class:
  - **Original:** Input title unchanged
  - **ASCII + Emoji:** Unicode converted to ASCII but emoji preserved
  - **ASCII Only:** All unicode converted to ASCII (emoji → ASCII equivalents)
  - **Path Safe:** Converted to valid filename (invalid chars removed, unicode converted, spaces normalized)

**Implementation:** [web-tool.py](web-tool.py) - `debug_title_variants()` function; [library/util.py](library/util.py) - `TitleVariants` class, `text_with_ascii_and_emojis()`, `text_ascii_only()`, `path_safe_filename()` functions

---

### Debug / Diagnostic Endpoints

#### `GET /debug/container` — Check Container Status

**Purpose:** Returns whether the application is running in a Docker container

**Response (JSON):**
```
{
  "running_in_container": boolean
}
```

**HTTP Status:** 200 OK

**Use Case:** Determines which code paths to execute (e.g., clipboard proxy behavior differs in containers)

**Implementation:** [web-tool.py](web-tool.py) - `debug_container()` function; [library/docker_util.py](library/docker_util.py) - `is_running_in_container()` function

---

#### `GET /debug/clip-cache` — Inspect Clipboard Cache State

**Purpose:** Returns detailed information about current clipboard cache usage, metrics, and configuration

**Response (JSON):**
```
{
  "batch_count": number,
  "cache_size_bytes": number,
  "cache_size_mb": number,
  "memory_available_mb": number,
  "memory_limit_mb": number,
  "memory_usage_pct": number (0-100),
  "config": {
    "ttl_seconds": number,
    "max_batches": number,
    "max_chunk_number": number,
    "memory_limit_pct": number
  },
  "batches": [
    {
      "batch_id": UUID string,
      "created_at": ISO timestamp string,
      "age_seconds": number,
      "chunk_count": number,
      "chunk_numbers": [array of chunk numbers]
    }
  ]
}
```

**Information Provided:**
- **batch_count:** Number of currently stored clipboard batches
- **cache_size:** Actual memory used by all batches and metadata
- **memory_available:** System memory available
- **memory_limit:** Calculated limit based on `CLIP_CACHE_MEMORY_LIMIT_PCT`
- **memory_usage_pct:** How close cache is to memory limit
- **config:** Current clipboard cache configuration settings
- **batches:** Detailed info for each batch (sorted by age, oldest first)

**Use Case:** Monitoring cache health, troubleshooting clipboard system issues, preventing memory exhaustion

**Implementation:** [web-tool.py](web-tool.py) - `debug_clip_cache()` function; [library/util.py](library/util.py) - `cleanup_clip_cache()` function

---

#### `GET /debug/clipboard-proxy` — Test Clipboard Proxy

**Purpose:** Interactive test page for verifying clipboard proxy functionality

**Response:**
- HTML page containing:
  - Pre-populated test data representing a captured page
  - Submit button to send test data through the proxy system
  - Result display area showing success/failure

**Testing Process:**
1. Submit button sends test JSON data to `/clip-collector` with a random batchId and chunkNum=1
2. System confirms chunk storage
3. User is redirected to `/mirror-clip` with the batchId to retrieve and display the test data
4. Result confirmation shows if the proxy system is working correctly

**Use Case:** Verifying clipboard proxy setup before using bookmarklets, troubleshooting clipboard collection issues

**Implementation:** [web-tool.py](web-tool.py) - `debug_clipboard_proxy()` function; [templates/clip-proxy.html](templates/clip-proxy.html)

---

#### `GET /debug/favicon-files` — Inspect Favicon Cache Files

**Purpose:** Returns detailed information about all three favicon cache files in precedence order

**Response (JSON):**
```
{
  "cache_files": [
    {
      "name": "User Overrides",
      "precedence": 1,
      "description": "...",
      "absolute_path": "/path/to/file",
      "exists": boolean,
      "size_bytes": number,
      "modified_at": ISO timestamp string,
      "entry_count": number,
      "in_memory_cache": {
        "cached": boolean,
        "cached_mtime": number,
        "loaded_at": ISO timestamp string,
        "age_seconds": number,
        "is_fresh": boolean
      },
      "sample_entries": [
        {"url": "example.com", "favicon": "https://..."}
      ]
    }
  ],
  "cache_ttl_seconds": number
}
```

**Information Provided:**
- **File status:** Path, existence, size, modification time
- **Precedence:** Priority order for cache lookup (1=highest)
- **Entry count:** Number of favicon mappings in each file
- **In-memory cache:** Whether file is loaded in memory, age, freshness
- **Sample entries:** First 5 entries from each cache file for inspection

**Use Case:** Debugging favicon not found issues, checking cache file status, verifying cache precedence, monitoring cache sizes

**Implementation:** [web-tool.py](web-tool.py) - `debug_favicon_files()` function; [library/html_util.py](library/html_util.py) - cache file management functions

---

## Request/Response Format Standards

### Page Metadata Query Parameters

All mirror endpoints accept the following optional query parameters to customize processing:

| Parameter | Type | Purpose |
|-----------|------|---------|
| `url` | string | Page URL from bookmarklet |
| `title` | string | Page title from bookmarklet |
| `batchId` | UUID | Clock batch ID for clipboard chunks |
| `textLength` | integer | Expected total length of clipboard data |
| `format` | string | Output format: `html`, `json`, `yaml`, `text` |
| `clipboardError` | string | Error message if clipboard capture failed |
| `contentType` | string | Content type of the page (e.g., `application/pdf`) |

See [library/util.py](library/util.py) - `PageMetadata` class for implementation details.

---

### Response Format Options

All endpoints support multiple response formats through query parameters:

**HTML Format (default for most endpoints):**
- Wraps content in HTML with Prism.js syntax highlighting
- MIME type: `text/html`
- Safe for displaying in browsers
- Suitable for code/text visualization

**Plain Text Format:**
- Raw content without HTML wrapping
- MIME type: `text/plain`
- Suitable for CLI tools, piping to files
- Fastest response time

**JSON Format:**
- Structured data with `application/json` MIME type
- Supports programmatic access
- Validates JSON structure before returning

**YAML Format:**
- Structured data with `text/yaml` MIME type
- Human-readable hierarchical format
- Falls back to text if content is not valid YAML

---

## Error Handling Summary

### HTTP Status Codes Used

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | OK | Successful request |
| 302 | Redirect | `/clip-proxy` redirecting to target endpoint |
| 400 | Bad Request | Missing/invalid query parameters, malformed JSON |
| 404 | Not Found | JavaScript file doesn't exist |
| 500 | Internal Server Error | Conversion failures, file system issues, processing errors |
| 503 | Service Unavailable | Template environment not initialized |

### Common Error Scenarios

| Scenario | Endpoint | HTTP Code | Response |
|----------|----------|-----------|----------|
| Missing `url` parameter | `/get` | 400 | Text message: "URL parameter 'url' is required" |
| Invalid `batchId` format | `/clip-collector` | 400 | Text message: "Invalid batchId format: must be a valid UUID" |
| Missing `chunkNum` | `/clip-collector` | 400 | Text message: "Missing required parameter: chunkNum" |
| `chunkNum` exceeds maximum | `/clip-collector` | 400 | Text message: "Invalid chunkNum: exceeds maximum allowed value (10000)" |
| ICO conversion fails | `/convert-ico-to-png` | 500 | Text message: "Failed to convert ICO to PNG" |
| SVG conversion fails | `/convert-svg-to-png` | 500 | Text message: "Failed to convert SVG to PNG" |
| No JavaScript file found | `/js/<filename>.js` | 404 | HTTP 404 status |
| URL retrieval fails | `/get` | 500 | Text message: "Failed to retrieve URL" |

### Graceful Degradation

- **Missing favicon:** Endpoints continue to work; favicon-related fields are empty
- **Invalid JSON in clipboard:** Endpoints fall back to plain text display
- **HTML parse failures:** Endpoints use raw clipboard content
- **Large HTML:** HTML prettification may be skipped; raw content returned
- **Invalid YAML/JSON:** Format falls back to plain text rendering

---

## Data Processing Details

### Clipboard Cache Cleanup

The clipboard cache automatically manages memory and batch limits:

**Automatic cleanup happens before each request and removes:**
1. Batches older than TTL (10 minutes, configurable via `CLIP_CACHE_TTL_SECONDS`)
2. Oldest batches if count exceeds limit (100 batches max, configurable via `CLIP_CACHE_MAX_BATCHES`)
3. Oldest batches if memory usage exceeds 50% of available memory (configurable via `CLIP_CACHE_MEMORY_LIMIT_PCT`)

See [library/util.py](library/util.py) - `cleanup_clip_cache()` function

---

### Fragment Text Extraction

When a URL contains a fragment (anchor), the system uses multiple strategies to find the associated content:

1. Heading element with matching `id` attribute
2. Anchor tag inside a heading
3. Element with matching `id`/`name` before a heading
4. Wrapper section/div/article with matching `id` containing a heading
5. Anchor tag with text content
6. Sibling heading of anchor tag
7. Fallback to fragment text itself

See [library/util.py](library/util.py) - `PageMetadata.resolve_fragment_text()` function

---

### Favicon Cache System

**Three-tier lookup priority:**
1. User Overrides (edited manually by user)
2. App Defaults (shipped with application)
3. Auto-Discovered Cache (dynamically cached on first access)

**Cache key matching strategy:**
- Exact match: `domain/path` (most specific)
- Fallback: `domain` (less specific)
- Auto-normalize: `www.domain.com` → `domain.com`

See [library/html_util.py](library/html_util.py) for full implementation

---

## Configuration

Application behavior is controlled via environment variables and configuration constants:

| Setting | Default | Purpose |
|---------|---------|---------|
| `CLIP_CACHE_TTL_SECONDS` | 600 | Batch expiration time in seconds |
| `CLIP_CACHE_MAX_BATCHES` | 100 | Maximum number of cached batches |
| `CLIP_CACHE_MAX_CHUNK_NUMBER` | 10000 | Maximum allowed chunk number |
| `CLIP_CACHE_MEMORY_LIMIT_PCT` | 0.5 | Max cache as % of available memory |
| `FAVICON_CACHE_TTL` | 300 | Favicon in-memory cache revalidation time |
| Port | 8532 (default) | Web server port (configurable via `-p` flag) |

Container installations store persistent data at `/data/`; local installations use `./local-cache/`

---

## Implementation References

| Component | Location | Purpose |
|-----------|----------|---------|
| Core Flask app | [web-tool.py](web-tool.py) | All endpoint definitions and routing |
| Utilities | [library/util.py](library/util.py) | PageMetadata, MirrorData, TitleVariants, clipboard cache management |
| HTML utilities | [library/html_util.py](library/html_util.py) | Favicon system, HTML parsing, link generation |
| Text utilities | [library/text_util.py](library/text_util.py) | Text extraction, NLP-based content filtering |
| URL utilities | [library/url_util.py](library/url_util.py) | URL parsing, fetching, image size detection |
| Image utilities | [library/img_util.py](library/img_util.py) | ICO/SVG to PNG conversion |
| Docker utilities | [library/docker_util.py](library/docker_util.py) | Container detection |
| Templates | [templates/](templates/) | Bookmarklet JS, HTML pages |
| Static files | [static/](static/) | CSS, Prism.js, favicon cache YAML files |

---

## Dependencies

Key external libraries and their roles:

| Library | Purpose |
|---------|---------|
| [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) | HTML parsing, text extraction |
| [NLTK](https://www.nltk.org/) | Natural language processing for intelligent text filtering |
| [Pillow](https://pillow.readthedocs.io/) | Image processing, ICO format handling |
| [CairoSVG](https://cairosvg.org/) | SVG to PNG conversion |
| [Magika](https://google.github.io/magika/) | Content type detection for text filtering |
| [PyYAML](https://pyyaml.org/) | YAML parsing for favicon cache files |
| [Prism.js](https://prismjs.com/) | Client-side code syntax highlighting |
| [Flask](https://flask.palletsprojects.com/) | Web framework, routing, request handling |
| [Jinja2](https://jinja.palletsprojects.com/) | Template rendering for bookmarklets and pages |
| [pyperclip](https://pypi.org/project/pyperclip/) | Local clipboard access (non-container) |
| [psutil](https://psutil.readthedocs.io/) | System memory monitoring |
| [tldextract](https://github.com/John-Lin/tldextract) | Domain parsing for favicon cache keys |

