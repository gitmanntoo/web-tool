# Implementation Plan: Paste Favicon / Inline Image

## Overview

Implement a paste-to-inline-favicon feature for mirror-links.html and a standalone debug page `/debug/inline-image` for converting pasted or uploaded images to inline base64 img tags.

---

## Step 1: Add `encode_image_inline()` to `library/img_util.py`

**Files modified:** `library/img_util.py`

Add a new function that takes raw image bytes (instead of a URL) and returns a base64 PNG data URL resized to the target height:

```python
def encode_image_inline(image_bytes: bytes, target_height: int = 20) -> str | None
```

Flow:
1. Detect image type using `Magika` to confirm it's a supported image
2. Open with `PIL.Image`
3. Calculate new dimensions preserving aspect ratio (clamp width to `target_height * 20` to prevent huge base64)
4. Resize using `Image.Resampling.LANCZOS`
5. Save as PNG to `BytesIO` buffer → base64 → data URL

**Note:** Mirrors existing `encode_favicon_inline()` pattern but accepts bytes instead of fetching a URL. The existing function could be refactored to call this new one.

---

## Step 2: Add `POST /debug/inline-image` endpoint

**Files modified:** `web-tool.py`

Add a new route following the pattern of existing debug routes:

```python
@app.route("/debug/inline-image", methods=["POST"])
def debug_inline_image():
    data = request.get_json()
    image_data = data.get("image_data")  # base64 string
    height = data.get("height", 20)

    if not image_data:
        return jsonify({"success": False, "error": "image_data is required"})

    # Decode base64 → encode_image_inline → return
```

Returns:
```json
{"success": true, "inline": "<img src=\"data:image/png;base64,...\" height=\"20\" alt=\"Favicon\" />", "base64": "..."}
```

On error:
```json
{"success": false, "error": "description"}
```

---

## Step 3: Create `static/js/paste-favicon.js`

**Files created:** `static/js/paste-favicon.js`

A small JS module for clipboard image handling:

```javascript
// Reads image/* from clipboard using Navigator.clipboard API
// Returns Blob or null if clipboard empty / no image

// Converts Blob to base64 string

// Adds "Pasted" radio option to the mirror-links favicon section
// and auto-selects it. The base64 image is stored in defaultValues.pastedFavicon.
```

Key functions:
- `readClipboardImage()` → `Promise<Blob | null>`
- `blobToBase64(blob)` → `Promise<string>`
- `addPastedFavicon(base64Image, container)` → injects "Pasted" radio option

Error handling: if clipboard has no image, show tooltip "No image in clipboard" on the Paste button.

---

## Step 4: Create `static/js/inline-image.js`

**Files created:** `static/js/inline-image.js`

JS for the debug page:

```javascript
// handlePaste(): reads clipboard image → blobToBase64 → send to server
// handleFileUpload(file): FileReader → base64 → send to server
// updatePreview(imgTag): renders output <img> in preview area
// copyOutput(): copies generated <img> tag to clipboard with tooltip
```

Sends to `POST /debug/inline-image`, receives inline tag and base64, updates the DOM.

---

## Step 5: Create `templates/debug-inline-image.html`

**Files created:** `templates/debug-inline-image.html`

Following the style of `debug-title-variants.html`:

```html
<h1>Inline Image Generator</h1>

<div class="metadata-panel">
    <h2>Height</h2>
    <input type="number" id="height-input" value="20" min="1" max="100"> px
</div>

<div class="metadata-panel">
    <h2>Image</h2>
    <div id="image-preview" style="min-height: 60px; border: 1px dashed #ccc; padding: 8px;">
        <!-- Preview area -->
    </div>
    <div style="margin-top: 8px;">
        <button id="paste-btn">Paste Image</button>
        <span style="margin: 0 8px; color: #666;">or</span>
        <input type="file" id="file-input" accept="image/*">
    </div>
</div>

<div class="metadata-panel">
    <h2>Output</h2>
    <button class="copy-btn" id="copy-output">Copy</button>
    <div id="output-tag" style="margin-top: 8px;"></div>
    <div id="output-base64" style="margin-top: 8px; font-family: monospace; font-size: 0.85em; word-break: break-all;"></div>
</div>
```

Links to `static/js/inline-image.js`.

---

## Step 6: Update `templates/mirror-links.html`

**Files modified:** `templates/mirror-links.html`

### Change 1: Always show favicon section

Replace `{% if favicon %}...{% endif %}` with unconditional rendering.

### Change 2: Favicon section structure

Always starts with "None" selected. When page has favicons, shows URL and Inline options. Paste Favicon button is always last.

```html
<div class="favicon-section">
    <h2>Favicon</h2>
    <div class="url-list">
        <div class="url-item">
            <input type="radio" name="favicon_option" value="none" checked>
            <span style="min-width: 100px;"><strong>None</strong></span>
        </div>
        {% if favicon %}
        <div class="url-item">
            <input type="radio" name="favicon_option" value="url">
            ...URL option...
        </div>
        {% if favicon_inline %}
        <div class="url-item">
            <input type="radio" name="favicon_option" value="inline">
            ...Inline option...
        </div>
        {% endif %}
        {% endif %}
        <div class="url-item">
            <button id="paste-favicon-btn">Paste Favicon</button>
            <span style="min-width: 100px;"><strong>Paste</strong></span>
        </div>
    </div>
</div>
```

### Change 3: JavaScript state

- Track `pastedFavicon` in `defaultValues` and `state`
- Paste button click → `readClipboardImage()` → `addPastedFavicon()` → inject "Pasted" radio option and auto-select it
- `buildHtmlLink()` handles `faviconOption === 'pasted'` using `defaultValues.pastedFavicon`
- `render()` and radio change listeners updated to handle 'pasted'

### Change 4: Link to `static/js/paste-favicon.js`

Add `<script src="/static/js/paste-favicon.js"></script>` before the closing `</body>`.

---

## Step 7: Tests

**Files created:** `tests/test_img_util.py` (extend existing)

Add tests for `encode_image_inline()`:
- Valid PNG bytes → returns base64 data URL
- Valid JPEG bytes → returns base64 PNG data URL (converted)
- SVG bytes → converts to PNG
- Invalid bytes → returns None
- Various target heights → dimensions correct

---

## Files Summary

| File | Action |
|------|--------|
| `library/img_util.py` | Add `encode_image_inline()` |
| `web-tool.py` | Add `POST /debug/inline-image` |
| `static/js/paste-favicon.js` | Create |
| `static/js/inline-image.js` | Create |
| `templates/debug-inline-image.html` | Create |
| `templates/mirror-links.html` | Modify favicon section |
| `tests/test_img_util.py` | Add tests |

## Dependencies

- `cairosvg`, `PIL/Pillow`, `magika` — already in use by `encode_favicon_inline()`
**Client-side size guard:** `Blob.size` or `File.size` checked before sending — reject if > 5MB. This is free with no image loading required.

**Server-side dimension guard:** When Pillow opens the image, if either dimension > 2000px, return an error. Keeps client JS minimal.
