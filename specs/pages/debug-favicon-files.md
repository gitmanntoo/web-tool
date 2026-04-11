# Debug Favicon Files — Specification

**Route:** `/debug/favicon-files` (GET only, no template)
**Backend:** `web-tool.py::debug_favicon_files()`

---

## Overview

A JSON-only debug endpoint that returns the status of all three tiers of the favicon cache system. Shows file path, existence, size, modification time, entry count, sample entries, and in-memory YAML cache status for each file.

This is an API-only endpoint. No template is rendered.

---

## Response Shape

```json
{
  "cache_files": [
    {
      "name": "User Overrides",
      "precedence": 1,
      "description": "Manual customizations - highest priority",
      "absolute_path": "/path/to/static/favicon-overrides.yml",
      "exists": true,
      "size_bytes": 1234,
      "modified_at": "2024-01-01 12:00:00",
      "mtime": 1704110400.0,
      "in_memory_cache": {
        "cached": true,
        "cached_mtime": 1704110400.0,
        "loaded_at": "2024-01-01 12:00:00",
        "age_seconds": 0.0,
        "is_fresh": true
      },
      "entry_count": 5,
      "sample_entries": [
        {"url": "example.com", "favicon": "https://example.com/favicon.ico"}
      ],
      "has_more_entries": false
    },
    { ... },
    { ... }
  ],
  "cache_ttl_seconds": 86400,
  "note": "Files are listed in precedence order (highest to lowest)"
}
```

`cache_files` is a **list** of objects (not a dict keyed by tier name). Each object has:

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Human-readable tier name |
| `precedence` | `int` | 1 (highest) to 3 (lowest) |
| `description` | `str` | Tier description |
| `absolute_path` | `str` | Absolute path to the cache file |
| `exists` | `bool` | Whether the file exists on disk |
| `size_bytes` | `int\|null` | File size in bytes (null if file doesn't exist) |
| `modified_at` | `str\|null` | Human-readable modification time (null if file doesn't exist) |
| `mtime` | `float\|null` | Unix timestamp of modification time |
| `in_memory_cache` | `dict` | `{"cached": false}` if not loaded; if loaded: `{cached, cached_mtime, loaded_at, age_seconds, is_fresh}` |
| `entry_count` | `int\|null` | Number of entries in the YAML file (null if file doesn't exist) |
| `sample_entries` | `list` | Up to 5 `{url, favicon}` entries |
| `has_more_entries` | `bool` | True if there are more than 5 entries |

### Top-level fields

| Field | Type | Description |
|-------|------|-------------|
| `cache_ttl_seconds` | `int` | TTL for the YAML cache in seconds |
| `note` | `str` | Static note about precedence ordering |

---

## Dependencies

- **html_util** — `FAVICON_OVERRIDES`, `FAVICON_DEFAULTS`, `FAVICON_LOCAL_CACHE`, `FAVICON_CACHE_TTL`, `_favicon_yaml_cache`
- **yaml.safe_load()** — YAML parsing of cache files
- **psutil** — not used in this endpoint
