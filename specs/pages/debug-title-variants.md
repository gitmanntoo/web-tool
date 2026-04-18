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
<div class="page-container">
    <h1>Debug Title Variants</h1>

    <div class="panel">
        <div class="panel-label">Input</div>
        <form method="POST">
            <div class="form-row">
                <input type="text" name="title" value="{{ input_title|e }}" class="text-input" style="flex: 1;">
                <button type="submit" class="btn-primary">Generate</button>
            </div>
        </form>
    </div>

    {% if title_variants %}
    <div class="panel">
        <div class="panel-label">Title Variants</div>
        <div class="variant-list">
            {% for variant in title_variants %}
            <div class="variant-row{% if variant.is_duplicate %} variant-row--duplicate{% endif %}">
                <button class="btn-copy" data-html="{{ variant.value|e }}">Copy</button>
                <span class="variant-label"><strong>{{ variant.label }}</strong></span>
                <span>{{ variant.value|e }}</span>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}
</div>

<script src="/static/js/tooltip.js"></script>
```

---

## CSS Classes

| Class | Element |
|-------|---------|
| `.page-container` | Outer wrapper for centered layout |
| `.panel` | Form section, results section (elevated card) |
| `.panel-label` | Section header text (e.g., "Input", "Title Variants") |
| `.form-row` | Flex container for form input + button |
| `.text-input` | Text input field with focus states |
| `.btn-primary` | Generate button (primary action style) |
| `.variant-list` | Container for variant rows |
| `.variant-row` | Each variant row (label + value + copy button) |
| `.variant-row--duplicate` | Modifier for duplicate variants (grays out row) |
| `.variant-label` | Label column (e.g., "Original", "ASCII Only") |
| `.btn-copy` | Copy button (pill style) |

---

## JavaScript

**Copy buttons** use `data-html` dataset attribute:
```html
<button class="btn-copy" data-html="{{ variant.value|e }}">Copy</button>
```

**`showTooltip(btn, message)`** — shared function from `/static/js/tooltip.js`. Creates a temporary tooltip using the `.tooltip` CSS class, removes it after 1500ms.

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
- [ ] Variant with duplicate value → row has `.variant-row--duplicate` class
- [ ] Click Copy → "Copied!" tooltip appears
- [ ] Original, ASCII+Emoji, ASCII Only, Path Safe all shown with correct values
