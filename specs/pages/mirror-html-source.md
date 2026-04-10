# Mirror HTML Source — Specification

**Route:** `/mirror-html-source` (GET/POST)
**Template:** `templates/plain_text.html`
**Backend:** `web-tool.py::mirror_html_source()`

---

## Overview

The Mirror HTML Source page displays the HTML content from the clipboard. If the clipboard JSON contains HTML that can be parsed into a BeautifulSoup object, the HTML is prettified with 2-space indentation. Otherwise, it falls back to `mirror_clip()` behavior.

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
User triggers /mirror-html-source
         │
         ▼
web-tool.py::mirror_html_source()
    │
    ├── util.get_page_metadata()
    │       └── reads url, title, batchId, textLength, format,
    │           clipboardError, contentType from request query params
    │       └── loads clipboard via clip_cache or pyperclip
    │       └── mirror_data.html populated
    │
    ├── If metadata.soup exists
    │       └── html_util.prettify_html(str(metadata.soup))
    │       └── language = "html"
    │       └── util.plain_text_response(..., language="html")
    │
    └── Else (no soup) → delegate to mirror_clip()
            │
            ▼
         mirror_clip() behavior (see mirror-clip spec)
```

---

## Backend Template Data

| Variable | Type | Description |
|----------|------|-------------|
| `page_title` | `str` | `"HTML Source"` |
| `page_text` | `str` | Prettified HTML from `metadata.soup` |
| `format` | `str` | From `metadata.output_format` (default `"html"`) |
| `language` | `str` | `"html"` |
| `clip_b64` | `str` | Base64-encoded `page_text` for auto-copy |

---

## URL Parameters

| Param | Source | Description |
|-------|--------|-------------|
| `url` | `metadata.url` | Page URL |
| `title` | `metadata.title` | Page title |
| `batchId` | `metadata.batch_id` | Batch ID for clip cache |
| `textLength` | `metadata.text_length` | Expected clipboard text length |
| `format` | `metadata.output_format` | Output format (`html`, `yaml`, `json`, `text`) |
| `clipboardError` | `metadata.clipboard_error` | Error message if clipboard read failed |
| `contentType` | `metadata.content_type` | HTTP Content-Type of the page |

---

## Edge Cases

| Case | Behavior |
|------|----------|
| `metadata.soup` exists | Prettify HTML via `html_util.prettify_html()`, use `language="html"` |
| `metadata.soup` is None | Fall back to `mirror_clip()` — shows clipboard contents |
| Clipboard JSON has empty `html` field | Fall back to `mirror_clip()` |
| `format=json` and valid JSON HTML | Return `application/json` response |
| `format=yaml` and valid JSON HTML | Return `text/yaml` response |
| `format=text` | Return `text/plain` with no HTML template |
| `format=html` (default) | Render via `plain_text.html` with Prism `language-html` class |
| Empty HTML | Fall back to `mirror_clip()` showing raw clipboard |

---

## Dependencies

- **BeautifulSoup** (`lxml`) — HTML parsing to create `metadata.soup`
- **html_util.prettify_html()** — HTML formatting
- **pyperclip** — clipboard access
- **clip_cache** — batched clipboard chunk storage
- **yaml** — YAML serialization (used by `plain_text_response`)
- **Jinja2** — template rendering (via `plain_text_response`)
