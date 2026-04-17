# Mirror Text Debug — Specification

**Route:** `/mirror-text-debug` (GET/POST)
**Template:** None (returns `text/plain` directly)
**Backend:** `web-tool.py::get_mirror_text_debug()`

---

## Overview

The Mirror Text Debug page extracts text content from the pasted HTML similar to `mirror-text`, but includes verbose per-node debugging information for each `script.String` node. This is useful for understanding how text was classified, filtered, and scored during extraction. Output is `mimetype="text/plain"` — no template, no auto-copy.

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
- **pyperclip** — clipboard access via `get_page_metadata()`
- **clip_cache** — batched clipboard chunk storage
