# Debug Clip Cache — Specification

**Route:** `/debug/clip-cache` (GET only, no template)
**Backend:** `web-tool.py::debug_clip_cache()`

---

## Overview

A JSON-only debug endpoint that reports the current state of the in-memory `clip_cache`. Returns batch counts, cache size, memory usage, configuration, and per-batch details including chunk counts and chunk numbers.

This is an API-only endpoint. No template is rendered.

---

## Response Shape

```json
{
  "batch_count": 2,
  "cache_size_bytes": 12345,
  "cache_size_mb": 0.01,
  "memory_percent": 45.2,
  "memory_total_gb": 32.0,
  "memory_available_gb": 17.5,
  "config": {
    "ttl_seconds": 300,
    "max_batches": 100,
    "memory_limit_pct": 0.5
  },
  "batches": [
    {
      "batch_id": "uuid-string",
      "created_at": "2024-01-01 12:00:00",
      "age_seconds": 123.4,
      "chunk_count": 3,
      "chunk_numbers": [1, 2, 3]
    }
  ]
}
```

---

## Field Descriptions

### Top-level stats

| Field | Type | Description |
|-------|------|-------------|
| `batch_count` | `int` | Number of batches in `clip_cache` |
| `cache_size_bytes` | `int` | Approximate bytes used by `clip_cache` using `sys.getsizeof()` |
| `cache_size_mb` | `float` | `cache_size_bytes` converted to MB, rounded to 2 decimal places |
| `memory_percent` | `float` | Current system memory usage percentage |
| `memory_total_gb` | `float` | Total physical memory in GB |
| `memory_available_gb` | `float` | Available memory in GB (from `psutil.virtual_memory()`) |

### Config

| Field | Type | Source |
|-------|------|--------|
| `ttl_seconds` | `int` | `util.CLIP_CACHE_TTL_SECONDS` |
| `max_batches` | `int` | `util.CLIP_CACHE_MAX_BATCHES` |
| `memory_limit_pct` | `float` | `util.CLIP_CACHE_MEMORY_LIMIT_PCT` |

### Batches

Each entry in `batches` corresponds to a batch in `clip_cache`. Sorted by `age_seconds` descending (oldest first).

| Field | Type | Description |
|-------|------|-------------|
| `batch_id` | `str` | UUID key from `clip_cache` |
| `created_at` | `str` | Formatted as `"YYYY-MM-DD HH:MM:SS"` from `time.localtime()` |
| `age_seconds` | `float` | Seconds elapsed since `created_at`, rounded to 1 decimal |
| `chunk_count` | `int` | Number of chunks stored for this batch |
| `chunk_numbers` | `list[int]` | Sorted list of chunk numbers received |

---

## Cache Size Calculation

```python
cache_size = sys.getsizeof(util.clip_cache)
for batch_data in util.clip_cache.values():
    cache_size += sys.getsizeof(batch_data)
    cache_size += sys.getsizeof(batch_data.get('chunks', {}))
    for chunk in batch_data.get('chunks', {}).values():
        cache_size += sys.getsizeof(chunk)
```

Uses `sys.getsizeof()` recursively to estimate memory usage.

---

## Dependencies

- **sys.getsizeof()** — per-object size estimation
- **psutil.virtual_memory()** — system memory info
- **time.time() / time.localtime()** — age calculation and formatting
- **util.clip_cache** — the in-memory batch storage dict
- **util.CLIP_CACHE_TTL_SECONDS**, **CLIP_CACHE_MAX_BATCHES**, **CLIP_CACHE_MEMORY_LIMIT_PCT** — config constants

---

## Testing Checklist

- [ ] GET /debug/clip-cache → 200 JSON response
- [ ] Response has all top-level fields: batch_count, cache_size_bytes, cache_size_mb, memory_percent, memory_total_gb, memory_available_gb, config, batches
- [ ] `config` reflects actual util constants
- [ ] `batches` sorted oldest-first by age_seconds descending
- [ ] `chunk_numbers` is a sorted list
- [ ] With no batches → batch_count: 0, batches: []
- [ ] After a clip-collector POST → new batch appears in batches list
