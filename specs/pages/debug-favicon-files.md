# Debug Favicon Files — Specification

**Route:** `/debug/favicon-files` (GET only, no template)
**Backend:** `web-tool.py::debug_favicon_files()`

---

## Overview

A JSON-only debug endpoint that returns the status of all three tiers of the favicon cache system. Shows file path, existence, size, modification time, entry count, sample entries, and in-memory cache status for each file.

This is an API-only endpoint. No template is rendered.

---

## Response Shape

```json
{
  "cache_files": {
    "overrides": {
      "name": "User Overrides",
      "precedence": 1,
      "path": "<FAVICON_OVERRIDES path>",
      "exists": true,
      "size": 1234,
      "modified": "2024-01-01 12:00:00",
      "in_memory_cache": true,
      "count": 5,
      "samples": [{"domain": "example.com", "data": "..."}]
    },
    "defaults": {
      "name": "App Defaults",
      "precedence": 2,
      "path": "<FAVICON_DEFAULTS path>",
      "exists": true,
      "size": 5678,
      "modified": "2024-01-01 12:00:00",
      "in_memory_cache": true,
      "count": 20,
      "samples": [...]
    },
    "discovered": {
      "name": "Auto-Discovered Cache",
      "precedence": 3,
      "path": "<FAVICON_LOCAL_CACHE path>",
      "exists": false,
      "size": null,
      "modified": null,
      "in_memory_cache": false,
      "count": 0,
      "samples": []
    }
  }
}
```

---

## Cache Tier Precedence

| Tier | Name | Precedence | Source |
|------|------|------------|--------|
| 1 | User Overrides | Highest (1) | `html_util.FAVICON_OVERRIDES` |
| 2 | App Defaults | Medium (2) | `html_util.FAVICON_DEFAULTS` |
| 3 | Auto-Discovered | Lowest (3) | `html_util.FAVICON_LOCAL_CACHE` |

---

## Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Display name for the cache tier |
| `precedence` | `int` | Priority rank (1 = highest) |
| `path` | `str` | Absolute filesystem path to the YAML cache file |
| `exists` | `bool` | Whether the file exists on disk |
| `size` | `int\|null` | File size in bytes, or `null` if not exists |
| `modified` | `str\|null` | Last modification time as `"YYYY-MM-DD HH:MM:SS"`, or `null` |
| `in_memory_cache` | `bool` | Whether this file is cached in `html_util._favicon_cache` |
| `count` | `int` | Number of entries in the YAML file |
| `samples` | `list[dict]` | Up to 3 sample entries from the file |

---

## Backend Implementation

- Reads `html_util.FAVICON_OVERRIDES`, `html_util.FAVICON_DEFAULTS`, `html_util.FAVICON_LOCAL_CACHE` paths
- For each file: checks `os.path.exists()`, `os.path.getsize()`, `os.path.getmtime()`, parses YAML with `yaml.safe_load()`
- In-memory cache status from `html_util._favicon_cache` dict (keyed by path)
- Samples: first 3 entries from the parsed YAML dict

---

## Dependencies

- **html_util** — `FAVICON_OVERRIDES`, `FAVICON_DEFAULTS`, `FAVICON_LOCAL_CACHE` constants
- **html_util._favicon_cache** — in-memory cache dict
- **yaml.safe_load()** — parsing YAML cache files
- **os.path** — filesystem queries

---

## Testing Checklist

- [ ] GET /debug/favicon-files → 200 JSON response
- [ ] Response has `cache_files` with `overrides`, `defaults`, `discovered` keys
- [ ] Each tier has `name`, `precedence`, `path`, `exists`, `count` fields
- [ ] `exists: false` when file does not exist on disk
- [ ] `in_memory_cache` correctly reflects whether file is in `_favicon_cache`
- [ ] `samples` contains up to 3 entries
- [ ] `modified` is null when file does not exist
