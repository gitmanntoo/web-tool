# Web-Tool — Specification

**File:** `specs/web-tool-spec.md`
**Date:** 2026-04-10
**Status:** Complete

---

## 1. Overview

Web-tool is a browser-based utility for extracting and reformatting page data. It is designed to work with a client-side bookmarklet that copies page metadata (URL, title, HTML, user-agent) to the clipboard. The user pastes that clipboard payload into a web-tool page, which then parses, transforms, and formats the data for copy-back.

Web-tool is used by a single user on their own machine. It runs locally, has no user accounts, and requires no internet connectivity. The primary interface is a web browser.

---

## 2. Architecture

### 2.1 Flask Application

`web-tool.py` is the main entry point. It registers all routes, initializes the Jinja2 template environment, and dispatches to library functions for business logic. The application uses a `before_request` hook to clean up expired `clip_cache` entries before every request.

### 2.2 Library Modules

All business logic lives in `library/`:

| Module | Responsibility |
|--------|----------------|
| `util.py` | Shared utilities: `plain_text_response()`, `get_page_metadata()`, `MirrorData`, `PageMetadata`, `clip_cache` dict, JavaScript file serving |
| `html_util.py` | HTML parsing, link extraction, three-tier favicon cache (`get_favicon_cache()`) |
| `url_util.py` | URL variant generation, URL normalization |
| `img_util.py` | Image encoding (ICO→PNG, SVG→PNG, inline base64), `encode_image_inline()` |
| `text_util.py` | Text extraction from HTML via tree walk |
| `docker_util.py` | Container detection (`is_running_in_container()`) |
| `unicode_util.py` | Unicode text transformations |

### 2.3 Static Assets

`static/` contains JavaScript bookmarklets, CSS, and favicon configuration files:

- `static/favicon-overrides.yml` — User overrides (highest-priority favicon cache)
- `static/favicon.yml` — App-default favicons (medium-priority favicon cache)

### 2.4 Templates

Jinja2 templates live in `templates/`. Pages that return plain text use `templates/plain_text.html`, which renders the text with syntax highlighting and an auto-copy mechanism.

---

## 3. Clipboard-Based Data Flow

The core pattern across all web-tool pages:

```
Bookmarklet (client-side JavaScript)
    │
    ▼
Copies page metadata JSON to clipboard
    │
    ▼
User navigates to a web-tool endpoint
    │
    ▼
Endpoint reads clipboard via pyperclip (or clip_cache for chunked transfers)
    │
    ▼
Business logic in library/ modules parses and transforms the data
    │
    ▼
Template renders response (or plain text via plain_text_response())
    │
    ▼
User copies output back to clipboard
```

### 3.1 Clipboard Payload Format

Pages that accept clipboard input expect a JSON object with this structure:

```json
{
  "url": "https://example.com/page",
  "title": "Page Title",
  "userAgent": "Mozilla/5.0 ...",
  "cookieString": "session=abc123",
  "html": "<html>...",
  "htmlSize": 12345
}
```

### 3.2 Chunked Clipboard Transfer

For large HTML payloads, the clipboard is split into chunks stored in `util.clip_cache`. The module-level `clip_cache` dict (in `library/util.py`) stores batches keyed by `batch_id` (UUID) + `chunk_number`. Chunks are collected via `POST /clip-collector` and reassembled before processing. The cache is in-memory only, cleaned by `cleanup_clip_cache()` on every request, with a 10-minute TTL and size limits (max 100 batches, max 10,000 chunks per batch, max 50% available memory).

### 3.3 Plain Text Auto-Copy

Two pages use `util.plain_text_response()` for auto-copy:

- **`mirror-clip`** — pretty-prints clipboard JSON, auto-copies via `clip_b64`
- **`mirror-html-source`** — prettifies HTML, auto-copies via `clip_b64`

Three pages return raw `text/plain` responses with **no auto-copy**:

- **`mirror-text`** — `Response(txt, mimetype="text/plain")`
- **`mirror-text-debug`** — `Response(txt, mimetype="text/plain")`
- **`mirror-soup-text`** — `Response(soup_text, mimetype="text/plain")`

The `plain_text_response()` function (defined in `library/util.py`) renders `templates/plain_text.html` with `page_title`, `page_text`, `clip_b64` (base64-encoded), and `language_class`. The template's `DOMContentLoaded` handler calls `atob(clip_b64)` and writes to clipboard.

---

## 4. Three-Tier Favicon Cache System

Favicon resolution follows a three-tier precedence hierarchy defined in `library/html_util.py` (via `get_favicon_cache()`):

| Priority | Cache File | Source | Purpose |
|----------|-----------|--------|---------|
| **Highest** | `static/favicon-overrides.yml` | User-maintained manual overrides | Per-domain favicon corrections |
| **Medium** | `static/favicon.yml` | App defaults | Built-in favicons for known sites |
| **Lowest** | `local-cache/favicon.yml` | Auto-discovered at runtime | Favicons found during link extraction |

When resolving a favicon for a URL, the cache is searched from highest to lowest priority. The search matches against the URL root (stripping `www.`), walking up the domain path. Only the first match is returned. The discovered cache is written to `local-cache/favicon.yml` only; user overrides must be manually added to `static/favicon-overrides.yml`.

---

## 5. Shared Patterns

### 5.1 `plain_text_response()`

Defined in `library/util.py`. Renders `templates/plain_text.html` with `page_title`, `page_text`, `clip_b64`, and `language_class`. The `clip_b64` variable (base64-encoded page text) is decoded client-side by the template's `atob()` call and written to clipboard on `DOMContentLoaded`. Used by:
- **`/mirror-clip`** — auto-copies prettified JSON
- **`/mirror-html-source`** — auto-copies prettified HTML
- **`/js/<filename>.js`** — serves minified/bookmarklet JS with Prism highlighting

The three remaining plain-text pages (`mirror-text`, `mirror-text-debug`, `mirror-soup-text`) return raw `Response(mimetype="text/plain")` with no auto-copy.

### 5.2 `pyperclip` Access

Clipboard data flows through `util.get_page_metadata()` which calls `pyperclip.paste()` internally via `MirrorData.clipboard`. Route handlers do not call `pyperclip` directly — they call `get_page_metadata()` and access the result.

### 5.3 `clip_cache` Structure

```python
clip_cache = {
    batch_id: {                     # UUID string
        "created_at": float,       # Unix timestamp
        "chunks": {
            chunk_number: str,     # 1-indexed chunk content
            ...
        }
    },
    ...
}
```

Maintained in `library/util.py`, cleaned by `cleanup_clip_cache()` on every request.

### 5.4 `MirrorData` and `PageMetadata`

These dataclasses in `library/util.py` parse clipboard JSON (`MirrorData`) and aggregate all page metadata (`PageMetadata`) including URL variants, title variants, favicon links, and mirror-data fields (`userAgent`, `htmlSize`, `cookieString`).

---

## 6. Page Spec Index

All template and plain-text pages. API-only routes are listed separately.

### 6.1 Template Pages

| Route | Spec | Purpose |
|-------|------|---------|
| `/mirror-links` | `specs/pages/mirror-links.md` | Interactive link builder with 4 formats (HTML/Markdown/Wiki/Simple) and extracted links browser |
| `/mirror-favicons` | `specs/pages/mirror-favicons.md` | Favicon browser with three-tier cache display and override management |
| `/clip-proxy` | `specs/pages/clip-proxy.md` | Clipboard-to-POST proxy; renders template in container, redirects outside container |
| `/debug/title-variants` | `specs/pages/debug-title-variants.md` | Debug UI for title variant generation |
| `/debug/url-variants` | `specs/pages/debug-url-variants.md` | Debug UI for URL variant generation |
| `/debug/inline-image` | `specs/pages/debug-inline-image.md` | Image-to-base64 inline converter (GET = form, POST = JSON API) |
| `/test-page` | `specs/pages/test-page.md` | Parameterized test page with arbitrary query params |
| `/test-pages-interactive` | `specs/pages/test-pages-interactive.md` | Interactive test page builder with multi-format copy |

### 6.2 Plain-Text Pages

`mirror-clip` and `mirror-html-source` use `util.plain_text_response()` for auto-copy on page load. The other three return raw `text/plain` with no auto-copy.

| Route | Spec | Purpose | Auto-copy |
|-------|------|---------|-----------|
| `/mirror-clip` | `specs/pages/mirror-clip.md` | Clipboard contents as prettified JSON | Yes |
| `/mirror-html-source` | `specs/pages/mirror-html-source.md` | Prettified HTML source with syntax highlighting | Yes |
| `/mirror-text` | `specs/pages/mirror-text.md` | Text extracted via soup tree walk | No |
| `/mirror-text-debug` | `specs/pages/mirror-text-debug.md` | Debug text extraction with per-tag cell display | No |
| `/mirror-soup-text` | `specs/pages/mirror-soup-text.md` | Plain `soup.get_text()` extraction | No |

### 6.3 Debug API Pages

These return JSON or raw inline HTML directly, no Jinja2 template.

| Route | Spec | Purpose |
|-------|------|---------|
| `/debug/favicon-files` | `specs/pages/debug-favicon-files.md` | Favicon cache file status (JSON) |
| `/debug/container` | `specs/pages/debug-container.md` | Container detection result (JSON) |
| `/debug/clip-cache` | `specs/pages/debug-clip-cache.md` | Clipboard cache status (JSON) |
| `/debug/clipboard-proxy` | `specs/pages/debug-clipboard-proxy.md` | Clipboard proxy test page (inline HTML f-string, not JSON) |

### 6.4 API-Only Routes (No Spec)

These routes have no page spec and do not render templates.

| Route | Methods | Purpose |
|-------|---------|---------|
| `/get` | GET | URL fetcher, returns JSON |
| `/clip-collector` | POST | Chunk collector for large clipboard payloads |
| `/add-favicon-override` | POST | Favicon override API (adds to `favicon-overrides.yml`) |
| `/convert-ico-to-png` | GET | ICO to PNG converter |
| `/convert-svg-to-png` | GET | SVG to PNG converter |

---

## 7. Spec Maintenance Policy

### 7.1 Modifying an Existing Page

Update the corresponding page spec **before** changing code. A spec-code mismatch means the spec is out of date and needs updating — or the code change was unauthorized. Review both and decide per case.

### 7.2 Adding a New Page

Create a new page spec in `specs/pages/` before implementing the page. The spec must include: route path, HTTP methods, template file (if any), backend handler, purpose, all template data, all JavaScript state, all interactive elements, CSS classes, error states, and edge cases.

### 7.3 Changing Shared Patterns

If a change affects the clipboard data flow, favicon cache system, `plain_text_response()`, `clip_cache` structure, or any other cross-page pattern, update **this** parent spec first. Then update every affected page spec.

### 7.4 Spec Authority

Specs are the authoritative record of expected behavior. If spec and code disagree and the code is correct (e.g., a new edge case), update the spec. If the spec is correct and the code is wrong, fix the code.

---

## 8. Dependencies

All dependencies are listed in `pyproject.toml` and installed via `uv`.

| Package | Purpose |
|---------|---------|
| `flask` | Web framework and routing |
| `beautifulsoup4` | HTML parsing |
| `lxml` | Fast HTML/XML parser backend for BeautifulSoup |
| `pyperclip` | Cross-platform clipboard access |
| `cairosvg` | SVG to PNG conversion |
| `pillow` | Image processing (ICO handling, resize) |
| `magika` | Content-type detection for favicons |
| `nltk` | Natural language processing for text extraction |
| `anyascii` | Unicode to ASCII transliteration |
| `pyyaml` | YAML parsing for favicon cache files |
| `psutil` | Memory usage measurement for `clip_cache` cleanup |
| `markdown` | README rendering at root `/` route |
| `pymupdf` | PDF metadata extraction in clipboard error handling |
| `jsmin` | JavaScript minification for bookmarklet serving |
| `esprima` | JavaScript AST parsing for bookmarklet serving |
