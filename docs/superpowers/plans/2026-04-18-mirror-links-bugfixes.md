# Mirror Links Bug Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 3 UI bugs on the Mirror Links page: cookie string wrapping, pasted favicon re-selection via radio buttons, and redundant previews for non-HTML link formats.

**Architecture:** Two-file change — `static/mirror.css` (CSS fixes) and `templates/mirror-links.html` (JS event delegation). All changes are isolated and minimal.

**Tech Stack:** Vanilla CSS, vanilla JavaScript (no framework).

---

## Files Modified

| File | Responsibility |
|------|---------------|
| `static/mirror.css` | Add `word-wrap` to `.metadata-item`; add `:nth-child` rule to hide non-HTML previews |
| `templates/mirror-links.html` | Replace `querySelectorAll` radio loop with event delegation on `#favicon-options` |

---

## Task 1: Cookie String Wrapping

**Files:**
- Modify: `static/mirror.css:348-355`

- [ ] **Step 1: Read the current `.metadata-item` rule**

Locate lines 348-355 in `static/mirror.css`.

- [ ] **Step 2: Add `word-wrap: break-word` and `overflow-wrap: break-word`**

Replace the current rule with:

```css
.metadata-item {
    margin-bottom: var(--space-sm);
    font-size: var(--font-size-sm);
    word-wrap: break-word;
    overflow-wrap: break-word;
}

.metadata-item strong {
    color: var(--color-text);
}
```

- [ ] **Step 3: Commit**

```bash
git add static/mirror.css
git commit -m "fix: enable word-wrap for metadata-item strings"
```

---

## Task 2: Pasted Favicon Radio Event Delegation

**Files:**
- Modify: `templates/mirror-links.html:340-354`

- [ ] **Step 1: Read the radio change listener block (lines 340-354)**

The current code loops over all radios with `querySelectorAll` at `DOMContentLoaded` time.

- [ ] **Step 2: Replace the radio/checkbox listener with event delegation**

Remove the `querySelectorAll` loop for favicon_option. Instead, add a delegated listener on `#favicon-options` inside the `DOMContentLoaded` handler.

Find the existing listener block around line 341:
```javascript
document.querySelectorAll('input[type="radio"], input[type="checkbox"]').forEach(input => {
    input.addEventListener('change', () => {
        if (input.name === 'title_variant') {
            state.title = input.dataset.text;
        } else if (input.name === 'fragment_variant') {
            state.fragmentText = input.dataset.text;
        } else if (input.name === 'url_variant') {
            state.url = input.dataset.text;
        } else if (input.name === 'favicon_option') {
            state.faviconOption = input.value;
        }
        render();
    });
});
```

Replace with: Keep the `title_variant`, `fragment_variant`, and `url_variant` individual listeners (they're static and already work). Add a new delegated listener for `favicon_option` only:

```javascript
// Delegated listener — handles dynamically added pasted favicon radio
document.getElementById('favicon-options').addEventListener('change', (e) => {
    if (e.target.name === 'favicon_option') {
        state.faviconOption = e.target.value;
        render();
    }
});

// Individual listeners for static radios
document.querySelectorAll('input[name="title_variant"], input[name="fragment_variant"], input[name="url_variant"]').forEach(input => {
    input.addEventListener('change', () => {
        if (input.name === 'title_variant') {
            state.title = input.dataset.text;
        } else if (input.name === 'fragment_variant') {
            state.fragmentText = input.dataset.text;
        } else if (input.name === 'url_variant') {
            state.url = input.dataset.text;
        }
        render();
    });
});
```

- [ ] **Step 3: Commit**

```bash
git add templates/mirror-links.html
git commit -m "fix: delegate favicon_option change events to #favicon-options"
```

---

## Task 3: Hide Redundant Non-HTML Previews

**Files:**
- Modify: `static/mirror.css`

- [ ] **Step 1: Read the `link-format-row__plain` section of mirror.css**

Locate the `.link-format-row__plain` rule around line 170.

- [ ] **Step 2: Add CSS rule to hide display spans for non-HTML link rows**

Add this rule after `.link-format-row__plain`:

```css
/* Only HTML link (first row) shows a visual preview.
   Markdown/Wiki/Simple show only the raw text line. */
.link-format-row:nth-child(n+2) .link-format-row__main > span:not(.variant-label):not(.btn-copy):not(.link-format-row__plain) {
    display: none;
}
```

Wait — `link-format-row__plain` is a sibling of `.link-format-row__main`, not a child. The selector needs to be simpler. The display span in each row is the `id="format-{format}-display"` span that is a direct child of `.link-format-row__main` alongside the button and label. These spans are plain text nodes.

Better selector — use the `id` pattern or just target any span that is a direct child of `link-format-row__main` but is NOT the label or button:

```css
/* Hide the display preview for non-HTML link formats.
   The first .link-format-row (HTML) shows a rendered link preview.
   Markdown/Wiki/Simple show only the raw text line (in .link-format-row__plain below). */
.link-format-row:nth-child(n+2) .link-format-row__main > span:not(.variant-label):not(.btn-copy) {
    display: none;
}
```

The selector `nth-child(n+2)` targets all `.link-format-row` elements from the 2nd onward. Within those, any plain `<span>` (not `.variant-label` and not `.btn-copy`) in the main row is hidden. The HTML row (1st) keeps its visual preview.

- [ ] **Step 3: Commit**

```bash
git add static/mirror.css
git commit -m "fix: hide redundant preview spans for non-HTML link formats"
```

---

## Verification

After all tasks, test manually:

1. **Cookie wrapping:** Navigate to Mirror Links, paste HTML with a very long cookie string (`Cookie: 0x1234567890...` with 200+ chars). The string should wrap within the metadata panel rather than overflowing horizontally.

2. **Pasted favicon:** Click "Paste Favicon", paste an image, verify the pasted favicon appears and is selected in the Links preview. Then click "URL", "None", or any other favicon option. Click the pasted favicon radio again — it should now properly switch back to pasted and update the link preview.

3. **Non-HTML previews:** Observe the Links panel — only the HTML row should show a preview span above its raw text line. Markdown, Wiki-link, and Simple rows should show only the raw text line.

Run: `make testv` to confirm no tests are broken.