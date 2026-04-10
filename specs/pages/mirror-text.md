# Mirror Text — Specification

**Route:** `/mirror-text` (GET/POST)
**Template:** `templates/plain_text.html`
**Backend:** `web-tool.py::get_mirror_text()`

---

## Overview

The Mirror Text page extracts text content from the pasted HTML by walking the BeautifulSoup tree and collecting string nodes. It deduplicates repeated script content and removes multiple blank lines. The output is returned as plain text (`mimetype="text/plain"`).

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
User triggers /mirror-text
         │
         ▼
web-tool.py::get_mirror_text()
    │
    ├── util.get_page_metadata()
    │       └── reads url, title, batchId, textLength, format,
    │           clipboardError, contentType from request query params
    │       └── loads clipboard via clip_cache or pyperclip
    │       └── mirror_data.html → metadata.soup (BeautifulSoup)
    │
    ├── text_util.walk_soup_tree_strings(metadata.soup)
    │       └── returns list of StringNode objects with .keep flag
    │
    ├── Filter to only nodes where .keep is True
    │       └── Deduplicate script.String nodes by .text content
    │
    ├── text_util.remove_repeated_lines("\n".join(texts))
    │
    └── Response(mimetype="text/plain")
```

---

## Backend Template Data

Note: This endpoint returns a plain `text/plain` Response directly, not via `plain_text_response()`. The text is not rendered through the HTML template.

| Variable | Type | Description |
|----------|------|-------------|
| `page_title` | `str` | `"Mirror Text"` |
| `page_text` | `str` | Extracted text strings joined with newlines |
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
| `metadata.soup` exists | Walk tree, collect strings, remove repeated lines |
| `metadata.soup` is None | Return empty text (no HTML to parse) |
| Repeated script content | Deduplicate `script.String` nodes by `.text` content |
| Multiple consecutive blank lines | Collapsed via `remove_repeated_lines()` |
| `batch_id` in clip cache | Reassemble chunks from cache |
| `clipboard_error` set | Load page via `url_util.get_url()` |
| Empty HTML | Return empty text |
| Script nodes without duplicates | Each included as-is |

---

## Dependencies

- **BeautifulSoup** (`lxml`) — HTML parsing to create `metadata.soup`
- **text_util.walk_soup_tree_strings()** — tree walker that returns StringNode objects with `.keep` flag
- **text_util.remove_repeated_lines()** — collapses repeated blank lines
- **pyperclip** — clipboard access
- **clip_cache** — batched clipboard chunk storage
