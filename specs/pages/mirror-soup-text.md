# Mirror Soup Text — Specification

**Route:** `/mirror-soup-text` (GET/POST)
**Template:** `templates/plain_text.html`
**Backend:** `web-tool.py::get_mirror_soup_text()`

---

## Overview

The Mirror Soup Text page extracts text content from the pasted HTML using BeautifulSoup's built-in `get_text()` method with newline separator. The result is cleaned via `remove_repeated_lines()` to collapse consecutive blank lines.

---

## Shared Pattern: plain_text_response()

All pages using `templates/plain_text.html` share the following behavior:

- **`util.plain_text_response()`** accepts:
  - `template_env` — Jinja2 environment
  - `page_title` — displayed in `<title>`
  - `page_text` — the content to display
  - `format` (default `"html"`) — controls rendering mode
  - `language` (default `None`) — maps to Prism.js class

- **For `format` in `("yaml", "json")`:** parses and re-serializes with appropriate content-type (`text/yaml` or `application/json`). Falls back to `format="text"` if parsing fails.

- **For `format="text"`:** returns plain text directly with `mimetype="text/plain"`.

- **Otherwise:** renders via `plain_text.html` template.

- **`plain_text.html`** template behavior:
  - `page_title` in `<title>`
  - `page_text` in `<pre><code>{{ page_text|e }}</code></pre>` with Prism highlighting via `language_class`
  - `clip_b64` — base64-encoded text, decoded via `atob()` on `DOMContentLoaded` for auto-copy to clipboard
  - Prism.js loaded via `/static/prism-mini.js` and `/static/prism-mini.css`

---

## Data Flow

```
User triggers /mirror-soup-text
         │
         ▼
web-tool.py::get_mirror_soup_text()
    │
    ├── util.get_page_metadata()
    │       └── reads url, title, batchId, textLength, format,
    │           clipboardError, contentType from request query params
    │       └── loads clipboard via clip_cache or pyperclip
    │       └── mirror_data.html → metadata.soup (BeautifulSoup)
    │
    ├── metadata.soup.get_text("\n")
    │       └── BeautifulSoup built-in text extraction with newline separator
    │
    ├── text_util.remove_repeated_lines(soup_text)
    │       └── Collapse repeated blank lines
    │
    └── Response(mimetype="text/plain")
```

---

## Backend Template Data

Note: This endpoint returns a plain `text/plain` Response directly, not via `plain_text_response()`. The text is not rendered through the HTML template.

| Variable | Type | Description |
|----------|------|-------------|
| `page_title` | `str` | `"Mirror Soup Text"` |
| `page_text` | `str` | Extracted text from `soup.get_text("\n")` cleaned |
| `format` | `str` | Not used — returns `text/plain` directly |

---

## URL Parameters

| Param | Source | Description |
|-------|--------|-------------|
| `url` | `metadata.url` | Page URL |
| `title` | `metadata.title` | Page title |
| `batchId` | `metadata.batch_id` | Batch ID for clip cache |
| `textLength` | `metadata.text_length` | Expected clipboard text length |
| `format` | `metadata.output_format` | Output format (not used here — returns text/plain) |
| `clipboardError` | `metadata.clipboard_error` | Error message if clipboard read failed |
| `contentType` | `metadata.content_type` | HTTP Content-Type of the page |

---

## Edge Cases

| Case | Behavior |
|------|----------|
| `metadata.soup` exists | Extract text via `soup.get_text("\n")`, clean repeated lines |
| `metadata.soup` is None | Return empty text (no HTML to parse) |
| Multiple consecutive blank lines | Collapsed via `remove_repeated_lines()` |
| `batch_id` in clip cache | Reassemble chunks from cache |
| `clipboard_error` set | Load page via `url_util.get_url()` |
| Empty HTML | Return empty text |

---

## Differences from mirror-text

| Aspect | `mirror-text` | `mirror-soup-text` |
|--------|---------------|-------------------|
| Text extraction | Tree walker (`walk_soup_tree_strings`) | BeautifulSoup built-in |
| Filtering | Deduplicates script nodes, respects `.keep` flag | No filtering |
| Debug info | None (pure text output) | None |
| Line collapsing | Yes (`remove_repeated_lines`) | Yes (`remove_repeated_lines`) |
| Output format | `text/plain` Response | `text/plain` Response |

---

## Dependencies

- **BeautifulSoup** (`lxml`) — HTML parsing to create `metadata.soup` and `soup.get_text()`
- **text_util.remove_repeated_lines()** — collapses repeated blank lines
- **pyperclip** — clipboard access
- **clip_cache** — batched clipboard chunk storage
