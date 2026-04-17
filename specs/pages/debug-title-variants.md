# Debug Title Variants — Specification

**Route:** `/debug/title-variants` (GET/POST)
**Template:** `templates/debug-title-variants.html`
**Backend:** `web-tool.py::debug_title_variants()`

---

## Overview

A debug page that accepts a title string via POST and displays the four `TitleVariants` output variants side-by-side with copy buttons. Used to inspect and verify title normalization behavior.

---

## Data Flow

```
User submits form with title string
         │
         ▼
POST /debug/title-variants
    │
    ▼
web-tool.py::debug_title_variants()
    │
    ├── request.form.get('title') → input_title
    ├── TitleVariants(input_title)
    │       ├── .original
    │       ├── .ascii_and_emojis
    │       ├── .ascii_only
    │       └── .path_safe
    │
    ├── build title_variants list with deduplication
    │
    └── template.render({input_title, title_variants})
            │
            ▼
    debug-title-variants.html
```

---

## POST Handler Behavior

1. Extract `title` from `request.form`
2. Build `TitleVariants` object
3. Iterate the four variants in order: `Original`, `ASCII + Emoji`, `ASCII Only`, `Path Safe`
4. Deduplicate by `value` — if a later variant has the same value as an earlier one, set `is_duplicate: True`
5. Labels are never deduplicated (each label appears at most once)
6. Render template with `input_title` and `title_variants`

On GET (no POST data), `input_title` is empty string and `title_variants` is empty list — the form shows without results.

---

## Template Data

| Variable | Type | Description |
|----------|------|-------------|
| `input_title` | `str` | The title string submitted in the form |
| `title_variants` | `list[dict]` | `[{value, label, is_duplicate}]` |

**`title_variants` structure:**
```python
{
    'value': str,          # the variant string
    'label': str,          # 'Original' | 'ASCII + Emoji' | 'ASCII Only' | 'Path Safe'
    'is_duplicate': bool  # True if this value appeared under an earlier label
}
```

---

## Template HTML Structure

```html
<h1>Debug Title Variants</h1>

<div class="metadata-panel">
    <h2>Input</h2>
    <form method="POST">
        <input type="text" name="title" value="{{ input_title|e }}">
        <button type="submit">Generate</button>
    </form>
</div>

{% if title_variants %}
<div class="metadata-panel">
    <h2>Title Variants</h2>
    <div class="url-list">
        {% for variant in title_variants %}
        <div class="url-item"{% if variant.is_duplicate %} style="opacity: 0.6..."{% endif %}>
            <button class="copy-btn" data-html="{{ variant.value|e }}">Copy</button>
            <span><strong>{{ variant.label }}</strong></span>
            <span>{{ variant.value|e }}</span>
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
| `.url-item` | Each variant row (label + value + copy button) |

---

## JavaScript

**Copy buttons** use `data-html` dataset attribute:
```html
<button class="copy-btn" data-html="{{ variant.value|e }}">Copy</button>
```

**`showTooltip(btn, message)`** — creates a temporary positioned tooltip span on the button, removes it after 1500ms.

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

- **TitleVariants** (`library/util.py`) — title normalization class

---

## Testing Checklist

- [ ] GET /debug/title-variants → form renders, no results shown
- [ ] POST empty title → form re-renders with empty input, no results
- [ ] POST "Hello World" → 4 variant rows shown
- [ ] Variant with duplicate value → row has `opacity: 0.6`
- [ ] Click Copy → "Copied!" tooltip appears
- [ ] Original, ASCII+Emoji, ASCII Only, Path Safe all shown with correct values
