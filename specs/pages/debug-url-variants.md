# Debug URL Variants — Specification

**Route:** `/debug/url-variants` (GET/POST)
**Template:** `templates/debug-url-variants.html`
**Backend:** `web-tool.py::debug_url_variants()`

---

## Overview

A debug page that accepts a URL via POST and displays the five URL variant forms (Original, With Fragment, Clean, Root, Host) with copy buttons. Used to inspect and verify URL parsing and normalization behavior.

---

## Data Flow

```
User submits form with URL string
         │
         ▼
POST /debug/url-variants
    │
    ▼
web-tool.py::debug_url_variants()
    │
    ├── request.form.get('url') → input_url
    ├── urlparse(input_url) → parsed_url
    ├── urlunparse() to build variants
    ├── url_util.get_url_root()
    ├── url_util.get_url_host()
    │
    ├── build url_variants list with deduplication
    │
    └── template.render({input_url, url_variants})
            │
            ▼
    debug-url-variants.html
```

---

## POST Handler Behavior

1. Extract `url` from `request.form`
2. Parse with `urllib.parse.urlparse()`
3. Build five variants:
   - **Original** — the raw input URL
   - **With Fragment** — `urlunparse((scheme, netloc, path, '', '', fragment))` stripped of trailing `/`
   - **Clean** — `urlunparse((scheme, netloc, path, '', '', ''))` stripped of trailing `/`
   - **Root** — `url_util.get_url_root()`
   - **Host** — `url_util.get_url_host()`
4. Deduplicate by URL value — if a later variant has the same URL as an earlier one, set `is_duplicate: True`
5. Render template with `input_url` and `url_variants`

On GET (no POST data), both variables are empty/empty list.

---

## Template Data

| Variable | Type | Description |
|----------|------|-------------|
| `input_url` | `str` | The URL submitted in the form |
| `url_variants` | `list[dict]` | `[{url, label, is_duplicate}]` |

**`url_variants` structure:**
```python
{
    'url': str,            # the variant URL string
    'label': str,          # 'Original' | 'With Fragment' | 'Clean' | 'Root' | 'Host'
    'is_duplicate': bool  # True if this URL appeared under an earlier label
}
```

---

## Template HTML Structure

```html
<h1>Debug URL Variants</h1>

<div class="metadata-panel">
    <h2>Input</h2>
    <form method="POST">
        <input type="text" name="url" value="{{ input_url|e }}">
        <button type="submit">Generate</button>
    </form>
</div>

{% if url_variants %}
<div class="metadata-panel">
    <h2>URL Variants</h2>
    <div class="url-list">
        {% for variant in url_variants %}
        <div class="url-item"{% if variant.is_duplicate %} style="opacity: 0.6..."{% endif %}>
            <button class="copy-btn" data-html="{{ variant.url|e }}">Copy</button>
            <span><strong>{{ variant.label }}</strong></span>
            <span><a href="{{ variant.url|e }}">{{ variant.url|e }}</a></span>
        </div>
        {% endfor %}
    </div>
</div>
{% endif %}
```

---

## CSS Classes

| Class | Element |
|-------|---------|
| `.metadata-panel` | Form section, results section |
| `.url-list` | Container for variant rows |
| `.url-item` | Each variant row |

---

## JavaScript

Identical to `debug-title-variants.html` — `showTooltip()` + `data-html` copy pattern.

**Copy behavior:**
```javascript
btn.addEventListener('click', () => {
    navigator.clipboard.writeText(btn.dataset.html)
        .then(() => showTooltip(btn, 'Copied!'))
        .catch(console.error);
});
```

---

## Dependencies

- **urllib.parse** — `urlparse`, `urlunparse`
- **url_util** — `get_url_root()`, `get_url_host()`

---

## Testing Checklist

- [ ] GET /debug/url-variants → form renders, no results shown
- [ ] POST "https://example.com/path#section" → 5 variant rows shown
- [ ] Variant with duplicate URL → row has `opacity: 0.6`
- [ ] Click Copy → "Copied!" tooltip appears
- [ ] URL with fragment → "With Fragment" differs from "Clean"
- [ ] Root and Host variants correctly extracted
