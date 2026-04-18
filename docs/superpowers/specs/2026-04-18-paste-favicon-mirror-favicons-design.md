# Paste Favicon — Mirror Favicons Page

**Feature:** Add paste favicon functionality to the `/mirror-favicons` page
**Template:** `templates/mirror-favicons.html`
**Supporting JS:** `static/js/paste-favicon.js` (existing)

---

## Overview

Add a "Paste Favicon" block to the Mirror Favicons page, positioned between the cache panel and the "Available Favicons" list. When the user pastes an image from clipboard, a new favicon entry block appears — styled like the existing discovered favicon entries — with an "Add to Overrides" form. The block stays visible after a successful override add, showing a success message before the page reloads.

The pasted block is inline-only (base64 from server), so the `save_inline` checkbox is pre-checked and disabled.

---

## Placement

**Location:** Between the cache panel (`div.panel`) and the `<h2>Available Favicons</h2>` heading.

**Structure:**
```html
<div class="panel">
  <div class="panel-label">Paste Favicon</div>
  <div class="variant-list" id="paste-favicon-section">
    <div class="variant-row">
      <button class="paste-favicon-btn" id="paste-favicon-btn">Paste Favicon</button>
      <span class="variant-label"><strong>&lt;-- Click to paste</strong></span>
    </div>
  </div>
</div>

<h2>Available Favicons (sorted by preference)</h2>
{% for f in favicons %}
<div class="favicon-entry ..."> ... </div>
{% endfor %}
```

---

## JavaScript Flow

### 1. Paste Button

The "Paste Favicon" button arms a one-time paste listener via `handlePasteFavicon(btn, container)` from `paste-favicon.js`. The existing function is reused.

### 2. On Paste

1. `blobToBase64(imageBlob)` — converts clipboard image to raw base64
2. `POST /debug/inline-image {image_data: base64, height: 20}` — sends to server, receives `{inline, base64}`
3. `addPastedFaviconEntry(data, url, overrideDomain, overridePathScope)` — dynamically builds and inserts the pasted block

### 3. Pasted Block Structure

Inserted before the favicon for-loop as a `.favicon-entry.favicon-pasted-entry`. All user-controlled values are escaped via `escapeHtml()` before insertion into innerHTML.

```html
<div class="favicon-entry favicon-pasted-entry">
  <p>
    <a href="data:image/png;base64,...">data:image/png;base64,...</a>
    <span class="badge"><span class="badge-dot badge-dot--muted"></span>NOT CACHED</span>
    <span class="badge"><span class="badge-dot badge-dot--primary"></span>PASTED</span>
    <span class="badge"><span class="badge-dot badge-dot--primary"></span>INLINE</span>
  </p>
  <p>Image Type: image/png | Size: 20x20</p>
  <p>
    <img src="data:image/png;base64,..." height="20" alt="20px height preview" /> 20px height preview
  </p>
  <p>
    <img src="data:image/png;base64,..." alt="Full size" /> Full size (20x20)
  </p>
  <div class="override-form" id="form-pasted-1">
    <strong>Add Override:</strong>
    <label>
      <input type="radio" name="scope" value="domain" checked>
      Domain only ({{ override_domain }})
    </label>
    {% if url.split('/')|length > 3 and url.split('/')[3] %}
    <label>
      <input type="radio" name="scope" value="path">
      Domain + first path ({{ override_path_scope }})
    </label>
    {% endif %}
    <label>
      <input type="checkbox" name="save_inline" checked disabled>
      Save as inline (base64)
    </label>
    <button class="btn-primary" onclick="addOverride('data:image/png;base64,...', '{{ url|e }}', 'form-pasted-1')">
      Add to Overrides
    </button>
    <div class="override-message"></div>
  </div>
</div>
```

### 4. After Override Success

- Block stays visible with success message
- Message shows for 1.5s, then `location.reload()`
- No auto-removal of the block

### 5. Badge Logic for Pasting

| Condition | Badge |
|-----------|-------|
| Always "NOT CACHED" | `.badge-dot--muted` |
| Always "PASTED" | `.badge-dot--primary` |
| Always "INLINE" | `.badge-dot--primary` |

Pasted images come from clipboard and are validated by the server before the block is inserted — no "INVALID" badge needed.

---

## Backend Changes

### `/debug/inline-image` endpoint

Already exists and is used by `paste-favicon.js`. No new endpoint needed.

**Request:**
```json
{
  "image_data": "rawBase64StringNoPrefix",
  "height": 20
}
```

**Response:**
```json
{
  "success": true,
  "inline": "<img src=\"data:image/png;base64,...\" height=\"20\" alt=\"Favicon\" />",
  "base64": "rawBase64String"
}
```

---

## Template Changes

### 1. New section above the favicon list

Add a "Paste Favicon" panel section with a paste button and container for the dynamically inserted block. Include `<script src="/static/js/paste-favicon.js">` if not already present.

### 2. Pasting block insertion point

The pasted block is inserted into `#paste-favicon-section` (the `.variant-list` inside the paste panel).

### 3. Jinja2 badge branch for pasted entries

In the favicon-entry badge section, add a branch for `.favicon-pasted-entry`:

```html
{% if f.cache_source.file == 'override' %}
  <span class="badge">...OVERRIDE...</span>
{% elif f.cache_source.file == 'default' %}
  <span class="badge">...DEFAULT...</span>
{% elif f.cache_source.file == 'discovered' %}
  <span class="badge">...DISCOVERED...</span>
{% else %}
  <span class="badge">...NOT CACHED...</span>
{% endif %}
```

A separate check for `f.cache_source.file == 'pasted'` is not needed since pasted entries are inserted dynamically via JavaScript, not by the Jinja2 for-loop.

---

## JavaScript Changes

### 1. New function: `addPastedFaviconEntry`

Builds the pasted block and inserts it into `#paste-favicon-section`. All user-controlled values escaped via `escapeHtml()` before use in innerHTML.

```javascript
function addPastedFaviconEntry(data, pageUrl, overrideDomain, overridePathScope, hasPathScope) {
    const container = document.getElementById('paste-favicon-section');
    const dataUrl = `data:image/png;base64,${data.base64}`;
    const escapedDataUrl = escapeHtml(dataUrl);
    const escapedPageUrl = escapeHtml(pageUrl);
    const escapedOverrideDomain = escapeHtml(overrideDomain);
    const escapedOverridePathScope = escapeHtml(overridePathScope);

    const pastedDiv = document.createElement('div');
    pastedDiv.className = 'favicon-entry favicon-pasted-entry';
    pastedDiv.innerHTML = `
        <p>
            <a href="${escapedDataUrl}">${escapedDataUrl}</a>
            <span class="badge"><span class="badge-dot badge-dot--muted"></span>NOT CACHED</span>
            <span class="badge"><span class="badge-dot badge-dot--primary"></span>PASTED</span>
            <span class="badge"><span class="badge-dot badge-dot--primary"></span>INLINE</span>
        </p>
        <p>Image Type: image/png | Size: 20x20</p>
        <p><img src="${escapedDataUrl}" height="20" alt="20px height preview" /> 20px height preview</p>
        <p><img src="${escapedDataUrl}" alt="Full size" /> Full size (20x20)</p>
        <div class="override-form" id="form-pasted-1">
            <strong>Add Override:</strong>
            <label>
                <input type="radio" name="scope" value="domain" checked>
                Domain only (${escapedOverrideDomain})
            </label>
            ${hasPathScope ? `
            <label>
                <input type="radio" name="scope" value="path">
                Domain + first path (${escapedOverridePathScope})
            </label>
            ` : ''}
            <label>
                <input type="checkbox" name="save_inline" checked disabled>
                Save as inline (base64)
            </label>
            <button class="btn-primary" onclick="addOverride('${escapedDataUrl}', '${escapedPageUrl}', 'form-pasted-1')">
                Add to Overrides
            </button>
            <div class="override-message"></div>
        </div>
    `;

    container.appendChild(pastedDiv);
}
```

### 2. DOMContentLoaded wiring

After the existing paste button listener setup in `mirror-favicons.html`:

```javascript
document.addEventListener('DOMContentLoaded', () => {
    const pasteBtn = document.getElementById('paste-favicon-btn');
    const faviconSection = document.getElementById('paste-favicon-section');

    if (pasteBtn && faviconSection) {
        // Arm paste listener (reuses paste-favicon.js logic)
        pasteBtn.addEventListener('click', async () => {
            // Reuse existing handlePasteFavicon pattern from paste-favicon.js
            // but with custom onPasted callback
        });
    }
});
```

The `handlePasteFavicon` in `paste-favicon.js` does not currently accept an onPasted callback. A local wrapper or inline implementation in `mirror-favicons.html`'s `<script>` block should be created, copying the paste-favicon.js logic but with an `onPasted` callback that calls `addPastedFaviconEntry`.

---

## CSS Changes

### `.favicon-pasted-entry`

Identical styling to `.favicon-entry`. No new CSS required — the class is added for future extensibility.

---

## Scope Determination

Same logic as existing discovered favicon entries:
- `override_domain` — `netloc` with `www.` stripped, e.g., `example.com`
- `override_path_scope` — `override_domain/first_path_segment`, e.g., `example.com/blog`
- `hasPathScope` — `url.split('/')|length > 3 and url.split('/')[3]`

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| No image in clipboard | Button text → "Paste Failed", tooltip shows "No image in clipboard" |
| Image too large (>5MB) | Button text → "Paste Failed", tooltip shows "Image too large (max 5MB)" |
| Server call fails | Button text → "Paste Failed", tooltip shows error message |
| Override POST fails | Error message shown in `.override-message`, button re-enabled |

---

## Security Notes

- `escapeHtml()` called on all user-controlled values inserted into HTML (`dataUrl`, `pageUrl`, `overrideDomain`, `overridePathScope`)
- `addOverride()` uses the existing template escaping via `|e` filter
- Pasting from clipboard is a user-initiated action with no server-side trust implications

---

## Testing Checklist

- [ ] Click "Paste Favicon" → button changes to "Waiting for paste... (Esc to cancel)"
- [ ] Esc cancels paste mode → button reverts to "Paste Favicon"
- [ ] Paste non-image content → "Paste Failed" tooltip
- [ ] Paste valid image → pasted block appears with correct preview
- [ ] Pasted block shows "PASTED", "INLINE", and "NOT CACHED" badges
- [ ] Inline checkbox is checked and disabled
- [ ] "Add to Overrides" → success message → 1.5s delay → reload
- [ ] "Add to Overrides" with domain scope → correct cache key in response
- [ ] "Add to Overrides" with path scope → cache key includes first path segment
- [ ] Override POST failure → error message shown, button re-enabled
- [ ] Path scope radio hidden when URL has no path segment