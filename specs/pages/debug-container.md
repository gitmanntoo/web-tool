# Debug Container — Specification

**Route:** `/debug/container` (GET only, no template)
**Backend:** `web-tool.py::debug_container()`

---

## Overview

A JSON-only debug endpoint that reports whether the application is currently running inside a Docker container. This is used internally to switch between passthrough and proxy modes (see `clip-proxy.md`).

This is an API-only endpoint. No template is rendered.

---

## Response

```json
{
  "running_in_container": true
}
```

Or when not in a container:

```json
{
  "running_in_container": false
}
```

**Content-Type:** `application/json`

---

## Backend Implementation

```python
return {
    "running_in_container": docker_util.is_running_in_container(),
}
```

---

## Dependencies

- **docker_util** — `is_running_in_container()`

---

## Testing Checklist

- [ ] GET /debug/container → 200 JSON response
- [ ] Response has `running_in_container: true` when in container
- [ ] Response has `running_in_container: false` when not in container
