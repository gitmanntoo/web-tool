# Fragment Text UI Fix — Design Spec

**Date:** 2026-04-20
**Status:** Approved
**Implementation:** CSS `:has()` approach

---

## Problem

For the URL `https://www.crummy.com/software/BeautifulSoup/bs4/doc/#pretty-printing`:

**Expected:** Fragment Text row always shows radio button + text "Fragment Text" + value "Pretty-printing" as read-only. When radio is selected, text becomes editable.

**Actual:** Fragment Text row is empty when radio is not selected — nothing visible next to the radio button. Editable input only appears when radio is selected.

## Root Cause

The Fragment Text row (lines 69–80 in `mirror-links.html`) renders an `<input type="text">` inside a `<label>` linked to the radio via `for`/`id`. The CSS rule (line 403 in `mirror.css`) sets `.fragment-text-input { display: none; }`, and JavaScript at lines 407–414 in `mirror-links.html` toggles visibility based on which radio is checked.

Since nothing is rendered as the read-only display for the non-selected state, the row appears empty.

## Design

### Layout (Fragment Text row)

```
<div class="variant-row">
    <input type="radio" name="fragment_variant" id="fragment-radio-N" ...>
    <label for="fragment-radio-N" class="fragment-text-label">
        <span class="fragment-text-readonly">Pretty-printing</span>
        <input type="text" class="fragment-text-input" ...>
    </label>
</div>
```

- **Radio** is in its own cell (outside label, before label per existing pattern)
- **Label** wraps both:
  - **Read-only span** (`.fragment-text-readonly`): always visible by default, shows the fragment value
  - **Editable input** (`.fragment-text-input`): always visible by default, becomes editable when radio selected

### CSS Behavior

| State | Read-only span | Editable input |
|-------|----------------|----------------|
| Radio NOT checked | `display: inline` | `display: none` |
| Radio checked | `display: none` | `display: inline-block`, `disabled: false` |

Implemented via `.fragment-text-label:has(#fragment-radio-N:checked) .fragment-text-readonly { display: none; }` and similar for `.fragment-text-input`.

### Why This Works

- The read-only value is always visible when the radio is NOT selected (it's in the `<span>`, not toggled by JavaScript)
- When radio IS selected, CSS hides the read-only span and shows the editable input
- No JavaScript visibility toggle needed for the read-only/ editable swap
- JavaScript only needs to read the input value on change (already exists at lines 396–404)

## Files to Modify

### `templates/mirror-links.html`

**Before (lines 69–80):**
```html
<div class="variant-row ...>
    <input type="radio" ... id="fragment-radio-N">
    <label for="fragment-radio-N" class="fragment-text-label">
        <input type="text" class="fragment-text-input" ...>
    </label>
</div>
```

**After:**
```html
<div class="variant-row ...>
    <input type="radio" ... id="fragment-radio-N">
    <label for="fragment-radio-N" class="fragment-text-label">
        <span class="fragment-text-readonly">{{ variant.value|e }}</span>
        <input type="text" class="fragment-text-input" ...>
    </label>
</div>
```

Also remove JavaScript lines 407–414 that toggle visibility based on checked radio.

### `static/mirror.css`

Add CSS rules using `:has()`:

```css
/* Read-only span hidden when radio is checked */
.fragment-text-label:has(input[name="fragment_variant"]:checked) .fragment-text-readonly {
    display: none;
}

/* Editable input shown when radio is checked */
.fragment-text-label:has(input[name="fragment_variant"]:checked) .fragment-text-input {
    display: inline-block;
}
```

Note: Browser support for `:has()` is now broad (Chrome 105+, Safari 15.4+, Firefox 121+). The project targets modern browsers via bookmarklet flow, so no IE11 fallback needed.

## Out of Scope

- Changes to Title or other fragment variant rows
- Changes to JavaScript logic for reading fragment text on change (already correct)
- Changes to how fragment text propagates to link formats (already correct)
