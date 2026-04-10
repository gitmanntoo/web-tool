# Mirror Clip — Specification

**Route:** `/mirror-clip` (GET/POST)
**Template:** `templates/plain_text.html`
**Backend:** `web-tool.py::mirror_clip()`

---

## Overview

The Mirror Clip page displays the raw clipboard contents. If the clipboard contains valid JSON, it is pretty-printed with 2-space indentation. Otherwise, the raw clipboard text is returned as-is.

This page delegates to `/clip-proxy` behavior when the clipboard does not contain JSON.

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
User triggers /mirror-clip
         │
         ▼
web-tool.py::mirror_clip()
    │
    ├── util.get_page_metadata()
    │       └── reads url, title, batchId, textLength, format,
    │           clipboardError, contentType from request query params
    │       └── loads clipboard via clip_cache or pyperclip
    │       └── mirror_data.clipboard populated
    │
    ├── If clipboard is valid JSON → json.dumps(..., indent=2)
    │   Else → raw clipboard text (no formatting)
    │
    └── util.plain_text_response()
            ├── format = metadata.output_format
            ├── language = "json"
            └── page_text = formatted clipboard text
                    │
                    ▼
         plain_text.html
                    │
                    ▼
         Browser auto-copies text via atob(clip_b64)
```

---

## Backend Template Data

| Variable | Type | Description |
|----------|------|-------------|
| `page_title` | `str` | `"Clipboard Contents"` |
| `page_text` | `str` | Pretty-printed JSON or raw clipboard |
| `format` | `str` | From `metadata.output_format` (default `"html"`) |
| `language` | `str` | `"json"` |
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
| Clipboard is valid JSON | Pretty-print with `json.dumps(json, indent=2)` |
| Clipboard is not JSON | Return raw clipboard text as plain text |
| `batch_id` in clip cache | Reassemble chunks from cache and delete batch |
| Clipboard length mismatch | Log warning; still return assembled content |
| `clipboard_error` set | Load page via `url_util.get_url()` instead of clipboard |
| `format=json` and valid JSON | Return `application/json` response |
| `format=yaml` and valid JSON | Return `text/yaml` response (JSON is valid YAML) |
| `format=text` | Return `text/plain` with no HTML template |
| `format=html` (default) | Render via `plain_text.html` with Prism highlighting |
| Empty clipboard | Return empty text |

---

## Dependencies

- **pyperclip** — clipboard access
- **clip_cache** — batched clipboard chunk storage
- **json** — JSON parsing and pretty-printing
- **yaml** — YAML serialization (used by `plain_text_response`)
- **Jinja2** — template rendering (via `plain_text_response`)
