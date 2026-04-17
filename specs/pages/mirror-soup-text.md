# Mirror Soup Text — Specification

**Route:** `/mirror-soup-text` (GET/POST)
**Template:** None (returns `text/plain` directly)
**Backend:** `web-tool.py::get_mirror_soup_text()`

---

## Overview

The Mirror Soup Text page extracts text content from the pasted HTML using BeautifulSoup's built-in `get_text()` method with newline separator. The result is cleaned via `remove_repeated_lines()` to collapse consecutive blank lines. Output is `mimetype="text/plain"` — no template, no auto-copy.

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

## Response

Returns `Response(soup_text, mimetype="text/plain")` directly. No template rendered. No auto-copy.

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
| `metadata.soup` is None | Raises `AttributeError` — `soup.get_text()` called on None |
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
- **pyperclip** — clipboard access via `get_page_metadata()`
- **clip_cache** — batched clipboard chunk storage
