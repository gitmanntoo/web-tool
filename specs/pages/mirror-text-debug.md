# Mirror Text Debug — Specification

**Route:** `/mirror-text-debug` (GET/POST)
**Template:** `templates/plain_text.html`
**Backend:** `web-tool.py::get_mirror_text_debug()`

---

## Overview

The Mirror Text Debug page extracts text content from the pasted HTML similar to `mirror-text`, but includes verbose per-node debugging information for each `script.String` node. This is useful for understanding how text was classified, filtered, and scored during extraction.

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
User triggers /mirror-text-debug
         │
         ▼
web-tool.py::get_mirror_text_debug()
    │
    ├── util.get_page_metadata()
    │       └── reads url, title, batchId, textLength, format,
    │           clipboardError, contentType from request query params
    │       └── loads clipboard via clip_cache or pyperclip
    │       └── mirror_data.html → metadata.soup (BeautifulSoup)
    │
    ├── text_util.walk_soup_tree_strings(metadata.soup, rollup=False)
    │       └── returns StringNode objects WITHOUT rollup aggregation
    │
    ├── For each StringNode:
    │       └── If name == 'script.String':
    │               └── Output debug line + text content
    │       └── Else:
    │               └── Output brief line with name + text
    │
    └── Response(mimetype="text/plain")
```

---

## Debug Line Format

For `script.String` nodes:
```
...D KEEP <name> L=<line_count> W=<word_count>/<token_count>/<word_pct> C=<category> D=<min_std_dist>/<max_std_dist> R=<max_longest_run> <magika_type>
<text content>
```

For non-script nodes:
```
...D KEEP <name><text>
```

Where:
- `...D` — indentation dots (`.` repeated `depth` times)
- `depth` — tree depth (3-digit padded)
- `KEEP` — whether node passes filter (or blank)
- `name` — node name (e.g., `script.String`)
- `L` — line count
- `W` — word count / token count / word percentage
- `C` — category string
- `D` — min standard distance / max standard distance
- `R` — max longest run
- `magika_type` — Magika content type classification

---

## Backend Template Data

Note: This endpoint returns a plain `text/plain` Response directly, not via `plain_text_response()`. The text is not rendered through the HTML template.

| Variable | Type | Description |
|----------|------|-------------|
| `page_title` | `str` | `"Mirror Text Debug"` |
| `page_text` | `str` | Debug lines + extracted text |
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
| `metadata.soup` exists | Walk tree with `rollup=False`, output debug lines |
| `metadata.soup` is None | Return empty text (no HTML to parse) |
| `script.String` node | Full debug line with stats + text |
| Non-script node | Brief line with `<name><text>` |
| `batch_id` in clip cache | Reassemble chunks from cache |
| `clipboard_error` set | Load page via `url_util.get_url()` |
| Empty HTML | Return empty text |

---

## Dependencies

- **BeautifulSoup** (`lxml`) — HTML parsing to create `metadata.soup`
- **text_util.walk_soup_tree_strings()** — tree walker (with `rollup=False`)
- **text_util.StringNode** — node class with `.depth`, `.keep`, `.name`, `.text`, etc.
- **text_util.remove_repeated_lines()** — collapses repeated blank lines
- **pyperclip** — clipboard access
- **clip_cache** — batched clipboard chunk storage
