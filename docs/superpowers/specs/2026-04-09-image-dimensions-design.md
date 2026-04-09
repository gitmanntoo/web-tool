# Image Dimensions Design Spec

**Date:** 2026-04-09  
**Branch:** `feat/image-dimensions`

## Summary

Add `width` attributes to all generated `<img>` tags, calculated from the original image's aspect ratio. This ensures browsers reserve exact space upfront, preventing layout shift when images load.

## Current State

All inline image `<img>` tags include only a `height` attribute:

```html
<img src="data:image/png;base64,..." height="20" alt="Favicon" />
```

The browser calculates width automatically, which can cause layout shift if the image loads late or has an unusual aspect ratio.

## Proposed Change

Include both `width` and `height` attributes on all generated `<img>` tags:

```html
<img src="data:image/png;base64,..." height="20" width="32" alt="Favicon" />
```

Width is calculated from the original image's aspect ratio when resizing.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| When to include `width` | Always | Explicit and consistent; makes reserved space unambiguous |
| Scope | Debug page + Mirror links + all templates | Consistency across the app |
| Dimension source | Height-driven (user specifies height, width auto-calculated) | Simple and works well for favicons/thumbnails; existing logic handles edge cases |
| Aspect ratio handling | Preserve original; clamp width to max `20 × height` | Prevents huge base64 strings from very wide images |
| Validation | Both dimensions clamped to min 1 | No zero/negative values |

## Implementation

### 1. `library/img_util.py:_resize_image()`

**Current:** Returns only the resized `Image.Image` object.

**Change:** Return a tuple of `(resized_image, width, height)` to expose calculated dimensions.

```python
def _resize_image(img: Image.Image, target_height: int) -> tuple[Image.Image, int, int]:
    """Resize an image to target_height preserving aspect ratio.
    
    Returns:
        Tuple of (resized_image, width, height)
    """
    # ... existing calculation logic ...
    return resized, new_width, new_height
```

### 2. `library/img_util.py:encode_image_inline()`

**Current:** Calls `_resize_image()` and discards the dimension info.

**Change:** Capture dimensions and include width in the output metadata. Consider returning a structured result:

```python
def encode_image_inline(image_bytes: bytes, target_height: int = 20) -> dict | None:
    """Encode raw image bytes as a base64 PNG string.
    
    Returns:
        Dict with 'data_url', 'width', 'height' keys, or None on failure.
    """
    # ... existing logic ...
    resized, width, height = _resize_image(img, target_height)
    # ... encode to base64 ...
    return {
        'data_url': f"data:image/png;base64,{b64}",
        'width': width,
        'height': height,
    }
```

**Alternative:** Keep string return type for backward compatibility and add a separate function or parameter for metadata. (Preferred: refactor to dict return and update all callers.)

### 3. `web-tool.py:debug_inline_image()`

**Current (line 1184):**
```python
"inline": f'<img src="{inline}" height="{height}" alt="Favicon" />',
```

**Change:** Accept width from the encoded result:
```python
"inline": f'<img src="{inline}" height="{height}" width="{width}" alt="Favicon" />',
```

### 4. `templates/mirror-links.html`

**Current:** JavaScript `buildHtmlLink()` function renders favicon images with only `height`:
```javascript
html += `<img src="${escapeHtml(defaultValues.favicon)}" height="20" alt="Favicon" /> `;
```

**Change:** Include `width` attribute. The width value needs to be passed from the server or calculated client-side from known aspect ratio.

**Approach:** Server includes `width` in the rendered template's favicon data, or JavaScript stores width alongside the favicon URL/inline data.

### 5. `templates/debug-inline-image.html`

**Current:** Only shows height input field.

**Change:** Add a read-only display for the calculated width:
```html
<div class="metadata-panel">
    <h2>Dimensions</h2>
    <div style="display: flex; gap: 10px; align-items: center;">
        <input type="number" id="height-input" value="20" min="1" max="100" ...>
        <span>×</span>
        <input type="number" id="width-display" disabled ...>
        <span>px</span>
    </div>
</div>
```

### 6. `static/js/inline-image.js`

**Change:** Update `updatePreview()` to handle width in the img tag. The server response already includes the complete `<img>` tag, so minimal JS changes needed.

## Files Modified

- `library/img_util.py` — `_resize_image()`, `encode_image_inline()`
- `web-tool.py` — `debug_inline_image()` endpoint
- `templates/mirror-links.html` — JavaScript `buildHtmlLink()` and favicon rendering
- `templates/debug-inline-image.html` — Width display field
- `static/js/inline-image.js` — Handle width in preview update

## Testing

- Verify dimensions are correct for square images (e.g., 20×20)
- Verify dimensions preserve aspect ratio for non-square images
- Verify width clamping for very wide images
- Verify minimum dimension of 1×1 for tiny images
- Update existing tests in `tests/test_img_util.py` to assert on width

## Rollback Plan

Revert the branch if issues arise. The change is backward-compatible (adding attributes doesn't break existing functionality).
