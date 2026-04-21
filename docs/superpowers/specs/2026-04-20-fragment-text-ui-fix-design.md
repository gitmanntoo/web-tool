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

## Implementation Details

### Layout (Fragment Text row — final)

```
<div class="variant-row">
    <input type="radio" name="fragment_variant" id="fragment-radio-N" ...>
    <button class="btn-copy" data-html="{{ variant.value|e }}">Copy</button>
    <span class="variant-label"><strong>Fragment Text</strong></span>
    <label for="fragment-radio-N" class="fragment-text-label">
        <span class="fragment-text-readonly">{{ variant.value|e }}</span>
        <input type="text" class="fragment-text-input" ...>
    </label>
</div>
```

- **Radio** is in its own cell (outside label, before label per existing pattern)
- **Copy button** and **label "Fragment Text"** match other fragment rows
- **Label** wraps both:
  - **Read-only span** (`.fragment-text-readonly`): visible by default, hidden when radio checked
  - **Editable input** (`.fragment-text-input`): hidden by default, shown when radio checked

### CSS Behavior

| State | Read-only span | Editable input |
|-------|----------------|----------------|
| Radio NOT checked | `display: inline` | `display: none` |
| Radio checked | `display: none` | `display: inline-block` |

Implemented via `.variant-row:has(input[name="fragment_variant"]:checked)` selectors.

### Why `.variant-row:has()` not `.fragment-text-label:has()`

The radio is a sibling of the label, not a child of it. The `:has()` selector must target `.variant-row` (the common ancestor) to detect the radio's checked state:

```css
.variant-row:has(input[name="fragment_variant"]:checked) .fragment-text-readonly { display: none; }
.variant-row:has(input[name="fragment_variant"]:checked) .fragment-text-input { display: inline-block; }
.variant-row:not(:has(input[name="fragment_variant"]:checked)) .fragment-text-input { display: none; }
```

### Why This Works

- The read-only value is always visible when the radio is NOT selected (it's in the `<span>`, not toggled by JavaScript)
- When radio IS selected, CSS hides the read-only span and shows the editable input
- No JavaScript visibility toggle needed for the read-only/ editable swap
- JavaScript only needs to read the input value on change (already exists at lines 396–404)

## Files Modified

### `templates/mirror-links.html`

**Before (lines 69–80):**
```html
<div class="variant-row ...>
    <input type="radio" ... id="fragment-radio-N">
    <label for="fragment-radio-N" class="fragment-text-label">
        <input type="text" class="fragment-text-input" ... placeholder="{{ variant.value|e }}">
    </label>
</div>
```

**After:**
```html
<div class="variant-row ...>
    <input type="radio" ... id="fragment-radio-N">
    <button class="btn-copy" data-html="{{ variant.value|e }}">Copy</button>
    <span class="variant-label"><strong>Fragment Text</strong></span>
    <label for="fragment-radio-N" class="fragment-text-label">
        <span class="fragment-text-readonly">{{ variant.value|e }}</span>
        <input type="text" class="fragment-text-input" ...>
    </label>
</div>
```

Removed JavaScript lines 407–414 that toggled visibility based on checked radio. Also removed `textInput.style.display` logic from the radio change handler.

### `static/mirror.css`

Added CSS rules using `:has()` on `.variant-row` (not `.fragment-text-label` since the radio is a sibling of the label, not a child):

```css
/* Read-only span visible by default, hidden when radio checked */
.fragment-text-readonly { display: inline; }
.variant-row:has(input[name="fragment_variant"]:checked) .fragment-text-readonly { display: none; }

/* Editable input hidden by default, shown when radio checked */
.variant-row:has(input[name="fragment_variant"]:checked) .fragment-text-input { display: inline-block; }
.variant-row:not(:has(input[name="fragment_variant"]:checked)) .fragment-text-input { display: none; }
```

Note: Browser support for `:has()` is now broad (Chrome 105+, Safari 15.4+, Firefox 121+). The project targets modern browsers via bookmarklet flow, so no IE11 fallback needed.

## Out of Scope

- Changes to Title or other fragment variant rows
- Changes to JavaScript logic for reading fragment text on change (already correct)
- Changes to how fragment text propagates to link formats (already correct)
