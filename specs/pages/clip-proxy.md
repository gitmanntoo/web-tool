# Clip Proxy Page — Specification

**Route:** `/clip-proxy` (GET only)
**Template:** `templates/clip-proxy.html`
**Backend:** `web-tool.py::clip_to_post()`

---

## Overview

The Clip Proxy page reads clipboard text, splits it into chunks, POSTs each chunk to the `clip-collector` endpoint, then submits a form to the target URL with an `X-Batch-Id` header. It is the server-side component of the clipboard bookmarklet flow.

The page behaves differently depending on whether the app is running inside a Docker container.

---

## Runtime Mode Detection

```
Request arrives at /clip-proxy
         │
         ▼
docker_util.is_running_in_container()?
    │
    ├── FALSE: 302 redirect to target param URL (passthrough mode)
    │
    └── TRUE:  render clip-proxy.html (proxy mode)
```

---

## Passthrough Mode (Not in Container)

When `is_running_in_container()` returns `false`, the handler extracts the `target` query parameter and issues a 302 redirect to `http://{host}/{target}` with all other query parameters preserved.

```
GET /clip-proxy?target=mirror-links&batchId=abc123
         │
         ▼ (not in container)
302 → http://{host}/mirror-links?batchId=abc123
```

All query parameters except `target` are forwarded. The `target` parameter itself is stripped and used as the new path.

---

## Proxy Mode (In Container)

When running inside a container, the page renders `clip-proxy.html` and performs the clipboard chunking workflow.

---

## Client-Side Workflow

```
Page loads (in container)
         │
         ▼
navigator.clipboard.readText()
    │
    ├── SUCCESS: processClipboard(text)
    │
    └── FAILURE: show error + manual fallback textarea
```

**`processClipboard(text)`:**
1. Split text into 2 MiB chunks (`chunkSize = 2 << 20`)
2. Generate a `batchId = crypto.randomUUID()`
3. POST each chunk to `/clip-collector?batchId=<uuid>&chunkNum=<n>` with `Content-Type: text/plain`
4. After all chunks succeed, build a form targeting the URL from `?target=` param, with a hidden input `<input name="X-Batch-Id" value="<batchId>">`
5. Submit the form as POST

**Chunk POST timing:** Each chunk is sent with a `chunkNum * 10ms` delay to prevent resource exhaustion.

**Manual fallback:** If clipboard read fails, a textarea is shown allowing the user to paste content manually, which then runs through `processClipboard()`.

---

## Error Handling

| Error | UI Response |
|-------|-------------|
| `clipboardError` query param set | Shows error message + retry button + manual fallback |
| `navigator.clipboard.readText()` fails | Shows error + manual fallback textarea |
| Chunk POST fails | Promise.all rejects, shows "Error processing chunks" |

---

## CSS Classes

| Class | Element |
|-------|---------|
| `.metadata-panel` | Page wrapper sections (not used in this page) |

---

## Backend Template Data

The template is rendered with an empty dict `{}`. No server-side data is passed to the template.

---

## Dependencies

- **docker_util** — `is_running_in_container()` for mode detection
- **clip_to_post()** backend — handles redirect or template rendering
- **clip_collector** endpoint — receives chunked POSTs
- **Client-side JavaScript** — clipboard reading, chunking, form submission

---

## Testing Checklist

- [ ] Not in container → GET /clip-proxy?target=mirror-links returns 302 redirect
- [ ] In container → page renders clip-proxy.html
- [ ] Clipboard read succeeds → chunks posted, form submitted
- [ ] Clipboard read fails → error shown with manual fallback
- [ ] Manual paste → works same as clipboard read
- [ ] Chunk POST failures → error displayed
- [ ] Form submission includes X-Batch-Id header via hidden input
