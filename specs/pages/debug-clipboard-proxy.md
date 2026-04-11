# Debug Clipboard Proxy — Specification

**Route:** `/debug/clipboard-proxy` (GET only, no template)
**Backend:** `web-tool.py::debug_clipboard_proxy()`

---

## Overview

A debug page for testing the clipboard proxy flow. It renders an inline HTML test page (not a template file) containing a form that POSTs test data to `/clip-collector` and then redirects to `/mirror-clip`.

This is an API/debug page. No Jinja2 template is used.

---

## Response

Returns an HTML string (f-string) directly from the handler, wrapped in a `make_response()`.

**Content-Type:** `text/html`

---

## Page Content

The rendered page contains:
1. A heading: "Clipboard Proxy Debug Test"
2. A description paragraph
3. A `<pre>` block showing the test data as formatted JSON
4. A "Submit Test Data" button
5. A `<div id="result">` for status output

**Test data hardcoded in handler:**
```python
test_data = {
    "url": "http://example.com",
    "title": "Test Page",
    "userAgent": request.headers.get("User-Agent", "Unknown"),
    "cookieString": "",
    "html": "<html><body><h1>Test Content</h1><p>This is test content.</p></body></html>",
}
```

---

## Client-Side Flow

```
User clicks "Submit Test Data"
         │
         ▼
submitTest() JavaScript function
    │
    ├── Generate batchId = crypto.randomUUID()
    ├── fetch('/clip-collector?batchId=<uuid>&chunkNum=1', {
    │       method: 'POST',
    │       body: JSON.stringify(test_data)
    │   })
    │
    ├── On success → window.location = '/mirror-clip?batchId=<uuid>&textLength=<length>'
    │
    └── On error → show error in #result div
```

---

## Dependencies

- **json.dumps()** — for serializing test data into the HTML/JS
- **clip_collector** endpoint — receives the test POST
- **mirror_clip** endpoint — redirect target

---

## Testing Checklist

- [ ] GET /debug/clipboard-proxy → HTML page rendered inline (no template file)
- [ ] Page shows test data in `<pre>` block
- [ ] Click "Submit Test Data" → POST to /clip-collector
- [ ] After POST success → redirect to /mirror-clip with batchId
- [ ] On POST failure → error shown in #result div
