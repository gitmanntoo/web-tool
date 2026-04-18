# Mirror Links Bug Fixes — Design

**Date:** 2026-04-18
**Type:** Bug fix
**Status:** Approved

## Overview

Three independent UI fixes for the Mirror Links page:

1. **Cookie string wrapping** — long cookie strings overflow the metadata panel
2. **Pasted favicon re-selection** — clicking the pasted favicon radio after switching away never updates state
3. **Non-HTML link previews** — Markdown/Wiki/Simple variants show redundant identical preview + raw text

---

## Fix 1: Cookie String Wrapping

**Location:** `static/mirror.css` line 348, `.metadata-item`

**Problem:** The `.metadata-item` rule has no text-wrapping property. Long strings (cookie strings, URLs, etc.) overflow the panel horizontally.

**Change:**
```css
.metadata-item {
    margin-bottom: var(--space-sm);
    font-size: var(--font-size-sm);
    word-wrap: break-word;
    overflow-wrap: break-word;
}
```

`word-wrap` is the legacy name for `overflow-wrap`; both are included for maximum browser compatibility.

---

## Fix 2: Pasted Favicon Radio Button Event Handling

**Location:** `templates/mirror-links.html` lines 340–354

**Problem:** Radio change listeners are attached via `querySelectorAll` at `DOMContentLoaded` time. The pasted favicon radio is added **dynamically** by `addPastedFavicon()` in `paste-favicon.js` **after** page load, so it never receives a listener. The user can paste and see the pasted favicon initially, but cannot navigate back to it after selecting a different favicon option.

**Solution:** Event delegation on the `#favicon-options` container, which exists at page load:

```javascript
// Old approach (lines 341-354):
document.querySelectorAll('input[type="radio"], input[type="checkbox"]').forEach(input => {
    input.addEventListener('change', () => { ... });
});

// New approach — delegate to #favicon-options:
document.getElementById('favicon-options').addEventListener('change', (e) => {
    if (e.target.name === 'favicon_option') {
        state.faviconOption = e.target.value;
        render();
    }
});
```

This handles the pasted favicon radio (and any future dynamic radios) without any additional code.

---

## Fix 3: Non-HTML Link Variants — Raw Text Only

**Location:** `templates/mirror-links.html` and `static/mirror.css`

**Problem:** All four link format rows show both a "display" preview span and a raw text line below. For HTML, the display shows a rendered link (meaningful). For Markdown, Wiki-link, and Simple, the display is plain text identical to the raw text — purely redundant.

**Solution:** CSS rule hides the display span for non-HTML rows:

```css
/* In .link-format-row__main, the display span is a plain text node
   (not .variant-label or .btn-copy). Hide it for all but the first row. */
.link-format-row:nth-child(n+2) .link-format-row__main > span:not(.variant-label):not(.btn-copy) {
    display: none;
}
```

The first `.link-format-row` (HTML) keeps its visual preview. All subsequent rows (Markdown, Wiki-link, Simple) show only the raw text line below.

---

## Files Changed

| File | Change |
|------|--------|
| `static/mirror.css` | Add `word-wrap` to `.metadata-item`; add `:nth-child` rule to hide non-HTML previews |
| `templates/mirror-links.html` | Replace `querySelectorAll` radio loop with event delegation on `#favicon-options` |