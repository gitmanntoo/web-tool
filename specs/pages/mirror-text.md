# Mirror Text — Specification

**Route:** `/mirror-text` (GET/POST)
**Template:** None (returns `text/plain` directly)
**Backend:** `web-tool.py::get_mirror_text()`

---

## Overview

The Mirror Text page extracts text content from the pasted HTML by walking the BeautifulSoup tree and collecting string nodes. It deduplicates repeated script content and removes multiple blank lines. The output is returned as plain text (`mimetype="text/plain"`) — no template, no auto-copy.

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

## Response

Returns `Response(txt, mimetype="text/plain")` directly. No template rendered. No auto-copy.

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
| `metadata.soup` is None | Raises `AttributeError` — no None check in handler |
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
- **pyperclip** — clipboard access via `get_page_metadata()`
- **clip_cache** — batched clipboard chunk storage
