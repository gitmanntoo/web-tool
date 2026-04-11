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
  "memory": {
    "percent": 45.2,
    "total": 34359738368,
    "available": 18756345600
  },
  "memory_limit": 9378172800,
  "config": {
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
| `cache_size_bytes` | `int` | Approximate bytes used by `clip_cache` using `sys.getsizeof()` recursively |

### Memory

| Field | Type | Description |
|-------|------|-------------|
| `memory.percent` | `float` | Current system memory usage percentage |
| `memory.total` | `int` | Total physical memory in bytes |
| `memory.available` | `int` | Available memory in bytes |
| `memory_limit` | `int` | Memory limit threshold in bytes (`available * CLIP_CACHE_MEMORY_LIMIT_PCT`) |

### Config

| Field | Type | Source |
|-------|------|--------|
| `config.max_batches` | `int` | `util.CLIP_CACHE_MAX_BATCHES` (100) |
| `config.memory_limit_pct` | `float` | `util.CLIP_CACHE_MEMORY_LIMIT_PCT` (0.5) |

### Per-batch

| Field | Type | Description |
|-------|------|-------------|
| `batches[].batch_id` | `str` | UUID of the batch |
| `batches[].created_at` | `str` | Human-readable creation timestamp |
| `batches[].age_seconds` | `float` | Seconds since batch creation |
| `batches[].chunk_count` | `int` | Number of chunks in this batch |
| `batches[].chunk_numbers` | `list[int]` | Sorted list of chunk numbers in this batch |

---

## Dependencies

- **`util.clip_cache`** — the in-memory dict storing all batches
- **`util.CLIP_CACHE_MAX_BATCHES`** — maximum batches limit
- **`util.CLIP_CACHE_MEMORY_LIMIT_PCT`** — memory limit percentage
- **`sys.getsizeof()`** — recursive size calculation for `cache_size_bytes`
- **`psutil.virtual_memory()`** — memory statistics
