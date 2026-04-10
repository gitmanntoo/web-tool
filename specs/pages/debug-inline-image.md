# Debug Inline Image — Specification

**Route:** `/debug/inline-image` (GET renders page, POST is JSON API)
**Template:** `templates/debug-inline-image.html`
**Backend (GET):** `web-tool.py::debug_inline_image_page()`
**Backend (POST):** `web-tool.py::debug_inline_image()`

---

## Overview

A debug page that converts a pasted or uploaded image into an inline base64 `<img>` tag. The page provides a UI with a height control, paste/file-upload inputs, and an output area showing the generated tag and base64 string.

---

## GET — Page Render

```
GET /debug/inline-image
         │
         ▼
web-tool.py::debug_inline_image_page()
    │
    └── template.render({})
            │
            ▼
    debug-inline-image.html + inline-image.js
```

The template renders an empty page shell. All interactivity is driven by `static/js/inline-image.js`.

---

## Page Sections

### Height Control

```html
<input type="number" id="height-input" value="20" min="1" max="100">
<input type="number" id="width-display" disabled> <!-- populated after processing -->
```

Width is read-only — it is calculated server-side from the image's aspect ratio.

### Image Input

Two input methods:
1. **Paste button** — clicking "Paste Image" arms a one-time `paste` event listener (5-second timeout, Esc to cancel)
2. **File upload** — `<input type="file" id="file-input" accept="image/*">`

File size limit: 5MB max. Dimension limit: 2000px max in any dimension.

### Output Section

After processing:
- `<div id="output-tag">` — shows the `<img ...>` tag (innerHTML)
- `<div id="output-base64">` — shows raw base64 string
- `<div id="output-dimensions">` — shows "Dimensions: WxHpx"
- Copy button has `data-html` set to the `<img>` tag

---

## POST — JSON API

```
POST /debug/inline-image
Content-Type: application/json

Body: {"image_data": "<base64>", "height": 20}
         │
         ▼
web-tool.py::debug_inline_image()
    │
    ├── validate JSON body
    ├── extract image_data (raw base64 string, no data: prefix)
    ├── extract height (default 20)
    ├── decode base64 → binary image bytes
    ├── open with Pillow → get (width, height)
    ├── calculate width from aspect ratio: width = round(height * (img.width / img.height))
    ├── build base64 data URL
    ├── build inline img tag: <img src="data:image/...;base64,..." height="H" width="W">
    │
    └── JSON response
```

**Success response:**
```json
{
    "success": true,
    "inline": "<img src=\"data:image/png;base64,...\" height=\"20\" width=\"40\">",
    "base64": "iVBORw0KGgo...",
    "width": 40,
    "height": 20
}
```

**Error response (400):**
```json
{"success": false, "error": "error message"}
```

---

## Edge Cases

| Case | Behavior |
|------|----------|
| No JSON body | 400 `{"success": false, "error": "no JSON body"}` |
| No `image_data` | 400 `{"success": false, "error": "missing image_data"}` |
| Invalid base64 | Pillow raises exception → 400 with error message |
| Image > 5MB | Client-side: tooltip "Image too large (max 5MB)" |
| Dimension > 2000px | Client-side: tooltip "Image too large (max 2000px in any dimension)" |
| Non-image MIME type | Pillow may accept it; result depends on Pillow behavior |
| `height` not numeric | Defaults to 20 |

---

## CSS Classes

| Class | Element |
|-------|---------|
| `.metadata-panel` | All three sections (Height, Image, Output) |

---

## Backend Template Data

Template rendered with an empty dict `{}`.

---

## JavaScript (`inline-image.js`)

**Key functions:**
- `handlePaste()` — arms paste listener, captures `clipboardData.items` for image blob
- `handleFileUpload(file)` — reads File as base64, sends to server
- `sendToServer(base64Image, height)` — POSTs to `/debug/inline-image`, updates preview
- `updatePreview(imgTag, base64, width, height)` — populates output elements, sets `data-html`
- `copyOutput()` — copies `data-html` to clipboard
- `disarmPaste(btn)` — removes listeners, clears timer
- `blobToBase64(blob)` — FileReader.readAsDataURL → split and return raw base64
- `fileToBase64(file)` — same for File input

**Paste timeout:** 5000ms. Auto-disarms after timeout or on Esc key.

---

## Dependencies

- **Pillow** — image decoding and dimension reading
- **base64** — decoding
- **docker_util** — not used (this endpoint works in both modes)

---

## Testing Checklist

- [ ] GET /debug/inline-image → page renders with height=20, empty outputs
- [ ] Click Paste Image → tooltip "Waiting for paste..." shown
- [ ] Press Esc → paste disarmed, tooltip "Paste cancelled"
- [ ] Paste an image → output-tag shows `<img>`, base64 shown, width auto-filled
- [ ] Upload a file → same behavior as paste
- [ ] Image > 5MB → error tooltip shown
- [ ] Image > 2000px → error tooltip shown
- [ ] Click Copy output → "Copied!" tooltip
- [ ] POST valid base64 → returns success JSON with inline, base64, width, height
- [ ] POST missing image_data → 400 error
- [ ] POST invalid base64 → 400 error
