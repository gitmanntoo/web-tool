# Visual Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modernize the visual design of mirror-links, mirror-favicons, and debug pages using a CSS custom property design system with elevated cards, subtle pill buttons, and soft-dot badges — removing all inline styles.

**Architecture:** Replace `mirror.css` with a token-based design system, simplify `default.css`, extract shared `tooltip.js`, and update 5 templates to use new semantic classes. All behavior preserved; only visual presentation changes.

**Tech Stack:** CSS custom properties, vanilla JavaScript, Jinja2 templates, Python/Flask (no changes to routes)

---

## Task 1: Write the new `mirror.css` design system

**Files:**
- Rewrite: `static/mirror.css`

This task creates the complete new CSS file. It does not touch any templates yet — those come in later tasks.

- [ ] **Step 1: Write the new mirror.css**

Replace the entire contents of `static/mirror.css` with:

```css
/* ============================================
   Mirror Design System — Clean Modern
   ============================================ */

:root {
    /* Colors */
    --color-primary: #3b82f6;
    --color-primary-hover: #2563eb;
    --color-success: #22c55e;
    --color-warning: #f59e0b;
    --color-error: #ef4444;
    --color-text: #1e293b;
    --color-text-secondary: #64748b;
    --color-text-muted: #94a3b8;
    --color-bg: #f8fafc;
    --color-surface: #ffffff;
    --color-border: #e2e8f0;
    --color-border-subtle: #f1f5f9;

    /* Spacing */
    --space-xs: 4px;
    --space-sm: 8px;
    --space-md: 16px;
    --space-lg: 24px;

    /* Border radius */
    --radius-sm: 6px;
    --radius-md: 12px;
    --radius-pill: 20px;

    /* Typography */
    --font-sans: system-ui, -apple-system, sans-serif;
    --font-mono: ui-monospace, 'Cascadia Code', 'SF Mono', monospace;
    --font-size-xs: 11px;
    --font-size-sm: 12px;
    --font-size-base: 14px;
    --font-size-md: 16px;
    --font-size-lg: 18px;
}

/* ============================================
   Page Layout
   ============================================ */

body {
    background: var(--color-bg);
    font-family: var(--font-sans);
    color: var(--color-text);
    padding: var(--space-lg);
}

.page-container {
    max-width: 720px;
    margin: 0 auto;
}

h1 {
    color: var(--color-text);
    font-size: var(--font-size-lg);
    margin-bottom: var(--space-md);
}

/* ============================================
   Panel (replaces .metadata-panel, .cache-panel, .favicon-section)
   ============================================ */

.panel {
    background: var(--color-surface);
    border-radius: var(--radius-md);
    box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
    padding: var(--space-lg);
    margin-bottom: var(--space-md);
}

.panel h2 {
    margin-top: 0;
    margin-bottom: var(--space-md);
    font-size: var(--font-size-lg);
    color: var(--color-text);
}

.panel-label {
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
    margin-bottom: var(--space-sm);
}

/* ============================================
   Variant Row (replaces .url-item)
   ============================================ */

.variant-list {
    margin: var(--space-sm) 0;
}

.variant-row {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    padding: var(--space-sm) 0;
    border-bottom: 1px solid var(--color-border-subtle);
    font-size: var(--font-size-base);
}

.variant-row:last-child {
    border-bottom: none;
}

.variant-row--duplicate {
    opacity: 0.45;
}

.variant-row--duplicate,
.variant-row--duplicate * {
    color: var(--color-text-muted);
}

.variant-row input[type="radio"] {
    accent-color: var(--color-primary);
    width: 14px;
    height: 14px;
    flex-shrink: 0;
}

.variant-row a {
    color: var(--color-primary);
    word-break: break-all;
}

.variant-label {
    min-width: 75px;
    font-size: var(--font-size-sm);
    font-weight: 500;
    color: var(--color-text);
    flex-shrink: 0;
}

.variant-value {
    flex: 1;
    min-width: 0;
    word-break: break-all;
}

/* ============================================
   Link Format Row (for mirror-links HTML/MD/Wiki/Simple)
   ============================================ */

.link-format-row {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    padding: var(--space-sm) 0;
    border-bottom: 1px solid var(--color-border-subtle);
}

.link-format-row:last-child {
    border-bottom: none;
}

.link-format-row__main {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    width: 100%;
}

.link-format-row__plain {
    font-family: var(--font-mono);
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    margin-top: var(--space-xs);
    word-break: break-all;
}

/* ============================================
   Copy Button (replaces .copy-btn)
   ============================================ */

.btn-copy {
    display: inline-block;
    padding: 3px 10px;
    background: var(--color-primary);
    color: white;
    border: none;
    border-radius: var(--radius-pill);
    cursor: pointer;
    font-size: var(--font-size-sm);
    font-family: var(--font-sans);
    flex-shrink: 0;
}

.btn-copy:hover {
    background: var(--color-primary-hover);
}

.btn-copy:disabled {
    background: var(--color-text-muted);
    cursor: not-allowed;
}

/* ============================================
   Primary Button
   ============================================ */

.btn-primary {
    display: inline-block;
    padding: 8px 16px;
    background: var(--color-primary);
    color: white;
    border: none;
    border-radius: var(--radius-sm);
    cursor: pointer;
    font-size: var(--font-size-base);
    font-family: var(--font-sans);
}

.btn-primary:hover {
    background: var(--color-primary-hover);
}

.btn-primary:disabled {
    background: var(--color-text-muted);
    cursor: not-allowed;
}

/* ============================================
   Badge (replaces .cache-badge)
   ============================================ */

.badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: var(--font-size-sm);
    color: var(--color-text);
}

.badge-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    flex-shrink: 0;
}

.badge-dot--primary { background: var(--color-primary); }
.badge-dot--success { background: var(--color-success); }
.badge-dot--warning { background: var(--color-warning); }
.badge-dot--muted { background: var(--color-text-muted); }
.badge-dot--error { background: var(--color-error); }

/* ============================================
   Cache Item (replaces .cache-file-item)
   ============================================ */

.cache-item {
    padding: var(--space-sm) var(--space-md);
    margin: var(--space-xs) 0;
    border-left: 3px solid var(--color-text-muted);
    background: var(--color-surface);
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

.cache-item--override { border-left-color: var(--color-primary); }
.cache-item--default { border-left-color: var(--color-success); }
.cache-item--discovered { border-left-color: var(--color-warning); }

.cache-item__name {
    font-weight: 600;
    font-size: var(--font-size-base);
}

.cache-item__path {
    font-family: var(--font-mono);
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
}

.cache-item__stats {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    margin-top: var(--space-xs);
}

/* ============================================
   Favicon Entry
   ============================================ */

.favicon-entry {
    margin-bottom: var(--space-md);
    padding: var(--space-lg);
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
}

.favicon-entry.invalid {
    background: #fffbeb;
    border-color: var(--color-warning);
}

.favicon-entry img {
    flex-shrink: 0;
}

/* ============================================
   Override Form
   ============================================ */

.override-form {
    margin-top: var(--space-sm);
    padding: var(--space-md);
    background: var(--color-bg);
    border-radius: var(--radius-sm);
}

.override-form label {
    display: block;
    margin: var(--space-xs) 0;
    font-size: var(--font-size-sm);
}

.override-form input[type="radio"] {
    margin-right: var(--space-xs);
    accent-color: var(--color-primary);
}

.override-message {
    font-size: var(--font-size-sm);
    margin-top: var(--space-xs);
}

.override-success {
    color: var(--color-success);
}

.override-error {
    color: var(--color-error);
}

/* ============================================
   Metadata Item
   ============================================ */

.metadata-item {
    margin-bottom: var(--space-sm);
    font-size: var(--font-size-sm);
}

.metadata-item strong {
    color: var(--color-text);
}

/* ============================================
   Text Input
   ============================================ */

.text-input {
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    padding: var(--space-sm);
    font-size: var(--font-size-base);
    font-family: var(--font-sans);
    background: var(--color-surface);
}

.text-input:focus {
    border-color: var(--color-primary);
    outline: none;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.15);
}

.text-input:disabled {
    background: var(--color-border-subtle);
    color: var(--color-text-muted);
}

/* ============================================
   Code Block
   ============================================ */

.code-block {
    font-family: var(--font-mono);
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    padding: var(--space-sm) var(--space-md);
    background: var(--color-bg);
    border-radius: var(--radius-sm);
    word-break: break-all;
}

/* ============================================
   Tooltip
   ============================================ */

.tooltip {
    position: absolute;
    background: var(--color-text);
    color: white;
    padding: 4px 8px;
    border-radius: var(--radius-sm);
    font-size: var(--font-size-xs);
    white-space: nowrap;
    z-index: 1000;
    pointer-events: none;
}

/* ============================================
   Paste Favicon Button
   ============================================ */

.paste-favicon-btn {
    padding: 4px 8px;
    font-size: var(--font-size-base);
    background: var(--color-primary);
    color: white;
    border: none;
    border-radius: var(--radius-sm);
    cursor: pointer;
}

.paste-favicon-btn:hover {
    background: var(--color-primary-hover);
}

/* ============================================
   Inline Favicon Preview
   ============================================ */

.favicon-inline-preview {
    font-family: var(--font-mono);
    font-size: 0.85em;
    color: var(--color-text-secondary);
    word-break: break-all;
}

/* ============================================
   Page URL (small text below cache panel)
   ============================================ */

.page-url {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    margin-top: var(--space-sm);
}

/* ============================================
   Form Row (for debug input forms)
   ============================================ */

.form-row {
    display: flex;
    gap: var(--space-sm);
    align-items: center;
}

/* ============================================
   Height Control Row (for debug-inline-image)
   ============================================ */

.height-row {
    display: flex;
    gap: var(--space-sm);
    align-items: center;
}

.height-row input[type="number"] {
    width: 80px;
}

/* ============================================
   Image Input Row (for debug-inline-image)
   ============================================ */

.image-input-row {
    display: flex;
    gap: var(--space-sm);
    align-items: center;
}

.image-input-hint {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    margin-top: var(--space-xs);
}

/* ============================================
   File Input Override
   ============================================ */

#file-input::file-selector-button {
    padding: 8px 16px;
    font-size: var(--font-size-base);
    border: none;
    background: var(--color-primary);
    color: white;
    cursor: pointer;
    border-radius: var(--radius-sm);
    font-family: var(--font-sans);
}

#file-input::file-selector-button:hover {
    background: var(--color-primary-hover);
}

/* ============================================
   Output Section (for debug-inline-image)
   ============================================ */

.output-section {
    margin-top: var(--space-sm);
}

.output-dimensions {
    margin-top: var(--space-sm);
    color: var(--color-text-secondary);
    font-size: var(--font-size-base);
}
```

- [ ] **Step 2: Verify the CSS file was written correctly**

Run: `head -5 static/mirror.css && echo "---" && wc -l static/mirror.css`
Expected: Shows `:root` block start and ~320+ lines

- [ ] **Step 3: Commit**

```bash
git add static/mirror.css
git commit -m "feat: rewrite mirror.css with design token system

Replace flat gray panels with elevated card design system using
CSS custom properties. New component classes: .panel, .variant-row,
.btn-copy, .btn-primary, .badge, .badge-dot, .text-input, .code-block.
Old classes (.metadata-panel, .cache-panel, .url-item, .cache-badge)
removed — templates will be updated in follow-up commits."
```

---

## Task 2: Simplify `default.css`

**Files:**
- Modify: `static/default.css`

- [ ] **Step 1: Replace default.css contents**

Replace the entire contents of `static/default.css` with:

```css
body {
    font-family: system-ui, -apple-system, sans-serif;
    background: #f8fafc;
}
```

This removes the conflicting `.copy-btn` rule (now fully defined in `mirror.css`) and uses literal values so out-of-scope pages (clip-proxy, plain_text) that only load `default.css` still work correctly.

- [ ] **Step 2: Commit**

```bash
git add static/default.css
git commit -m "refactor: simplify default.css to just font-family and bg

Remove .copy-btn rule now defined in mirror.css. Use literal values
instead of custom properties so out-of-scope pages that only load
default.css continue to work."
```

---

## Task 3: Create shared `tooltip.js`

**Files:**
- Create: `static/js/tooltip.js`

- [ ] **Step 1: Write tooltip.js**

Create `static/js/tooltip.js` with the shared tooltip function. The identical function exists in three templates (mirror-lines 291-305, debug-title-variants 38-51, debug-url-variants 38-51).

```javascript
/**
 * Show a temporary tooltip above an element.
 * @param {HTMLElement} element - The element to position the tooltip above
 * @param {string} message - The tooltip text to display
 * @param {number} [duration=1500] - Duration in ms before auto-remove
 */
function showTooltip(element, message, duration) {
    duration = duration || 1500;
    var tooltip = document.createElement('span');
    tooltip.textContent = message;
    tooltip.className = 'tooltip';

    var rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + 'px';
    tooltip.style.top = (rect.top - 30) + 'px';

    document.body.appendChild(tooltip);

    setTimeout(function() {
        tooltip.remove();
    }, duration);
}
```

- [ ] **Step 2: Commit**

```bash
git add static/js/tooltip.js
git commit -m "feat: extract shared showTooltip() into static/js/tooltip.js

Identical showTooltip() was duplicated across mirror-links.html,
debug-title-variants.html, and debug-url-variants.html. Now a single
shared module using the .tooltip CSS class from mirror.css."
```

---

## Task 4: Update `mirror-links.html` template

**Files:**
- Modify: `templates/mirror-links.html`

This is the largest template change. Key transformations:
- Wrap `<body>` content in `<div class="page-container">`
- `.metadata-panel` → `.panel`
- `.url-list` → `.variant-list`
- `.url-item` → `.variant-row`
- `.favicon-section` → `.panel` (with `.panel-label`)
- `.copy-btn` → `.btn-copy`
- All `style=` attributes removed, replaced with semantic classes
- Duplicate `style="opacity: 0.6; background-color: #f5f5f5;"` → `class="variant-row--duplicate"`
- Inline `showTooltip()` removed — replaced with `<script src="/static/js/tooltip.js">`
- `<h2>` section headers → `<div class="panel-label">`

- [ ] **Step 1: Rewrite the template HTML structure**

Replace `templates/mirror-links.html` entirely. The JavaScript logic (defaultValues, state, render, buildHtmlLink, etc.) stays identical — only the HTML structure and class names change. The full template is provided in the spec's template changes section and must be written out completely because every panel and row changes class names.

The key structural changes:
- `<div class="metadata-panel">` → `<div class="panel">`
- `<h2>Links</h2>` → `<div class="panel-label">Links</div>`
- `<div class="url-list">` → `<div class="variant-list">`
- Links section format rows: `<div class="url-item" style="flex-direction: column; align-items: flex-start;">` → `<div class="link-format-row">`
- Inner row: `<div style="display: flex; align-items: center; gap: 8px; width: 100%;">` → `<div class="link-format-row__main">`
- Plain text: `<div style="color: #666; font-family: monospace; font-size: 0.9em; margin-top: 4px;" id="format-html-plain"></div>` → `<div class="link-format-row__plain" id="format-html-plain"></div>`
- Label spans: `<span style="min-width: 100px;"><strong>HTML</strong></span>` → `<span class="variant-label"><strong>HTML</strong></span>`
- Variant rows with conditional duplicate styling: `<div class="url-item"{% if variant.is_duplicate %} style="opacity: 0.6; background-color: #f5f5f5;"{% endif %}>` → `<div class="variant-row{% if variant.is_duplicate %} variant-row--duplicate{% endif %}">`
- Copy buttons: `class="copy-btn"` → `class="btn-copy"`
- Favicon inline preview: `<span style="font-family: monospace; font-size: 0.85em; color: #666; word-break: break-all;">` → `<span class="variant-value favicon-inline-preview">`
- Paste favicon button: `<button class="paste-favicon-btn" id="paste-favicon-btn" style="padding: 4px 8px; font-size: 14px;">` → `<button class="paste-favicon-btn" id="paste-favicon-btn">`
- Duplicate label spans throughout: `<span style="min-width: 100px;"><strong>` → `<span class="variant-label"><strong>`
- Remove inline `showTooltip()` function entirely; add `<script src="/static/js/tooltip.js"></script>` before the paste-favicon script
- In `attachCopyListeners()`: change `document.querySelectorAll('.copy-btn')` → `document.querySelectorAll('.btn-copy')`

- [ ] **Step 2: Run integration tests**

Run: `uv run --python /Users/keith/.local/share/uv/python/cpython-3.14.0-macos-aarch64-none/bin/python3.14 -m pytest tests/test_integration_pages.py -v`

Expected: All existing integration tests pass (they test rendered HTML content, not CSS classes)

- [ ] **Step 3: Commit**

```bash
git add templates/mirror-links.html
git commit -m "feat: redesign mirror-links.html with new design system classes

Replace .metadata-panel/.url-item/.copy-btn with .panel/.variant-row/
.btn-copy. Remove all inline styles. Use .variant-row--duplicate class
instead of inline opacity. Wrap content in .page-container. Replace
inline showTooltip() with shared tooltip.js."
```

---

## Task 5: Update `mirror-favicons.html` template

**Files:**
- Modify: `templates/mirror-favicons.html`

- [ ] **Step 1: Rewrite the template**

Key changes:
- Wrap content in `<div class="page-container">`
- `.cache-panel` → `.panel`
- `<h2>Three-Tier Cache System</h2>` → `<div class="panel-label">Three-Tier Cache System</div>`
- `.cache-file-item.precedence-N` → `.cache-item.cache-item--N` (where N maps: overrides→override, defaults→default, discovered→discovered)
- `.cache-badge.cache-override` → `<span class="badge"><span class="badge-dot badge-dot--primary"></span>OVERRIDE</span>`
- `.cache-badge.cache-default` → `<span class="badge"><span class="badge-dot badge-dot--success"></span>DEFAULT</span>`
- `.cache-badge.cache-discovered` → `<span class="badge"><span class="badge-dot badge-dot--warning"></span>DISCOVERED</span>`
- `.cache-badge.cache-none` → `<span class="badge"><span class="badge-dot badge-dot--muted"></span>NOT CACHED</span>`
- `.cache-badge.cache-invalid` → `<span class="badge"><span class="badge-dot badge-dot--error"></span>INVALID - FAILED TO LOAD</span>`
- `.cache-key-info` → `.cache-item__path`
- `.cache-file-name` → `.cache-item__name`
- `.cache-file-path` → `.cache-item__path`
- `.cache-file-stats` → `.cache-item__stats`
- `.cache-file-list` → `.variant-list`
- `<p style="font-size: 12px; color: #666; margin-top: 10px;">` → `<p class="page-url">`
- Override form button → `class="btn-primary"`
- Override form error/success: `class="override-message override-success"` / `class="override-message override-error"`

- [ ] **Step 2: Run integration tests**

Run: `uv run --python /Users/keith/.local/share/uv/python/cpython-3.14.0-macos-aarch64-none/bin/python3.14 -m pytest tests/ -v`

Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add templates/mirror-favicons.html
git commit -m "feat: redesign mirror-favicons.html with new design system

Replace .cache-panel/.cache-badge/.cache-file-item with .panel/.badge/
.cache-item. Use soft dot badges instead of filled pills. Remove inline
styles. Wrap content in .page-container."
```

---

## Task 6: Update `debug-title-variants.html` and `debug-url-variants.html`

**Files:**
- Modify: `templates/debug-title-variants.html`
- Modify: `templates/debug-url-variants.html`

These two templates are nearly identical. Both need:
- Wrap content in `<div class="page-container">`
- `.metadata-panel` → `.panel`
- `<h2>Input</h2>` → `<div class="panel-label">Input</div>` (and similar for variant headings)
- Inline form styles → `.form-row`, `.text-input`, `.btn-primary`
- `.url-item` → `.variant-row` with `--duplicate` modifier
- `.url-list` → `.variant-list`
- `.copy-btn` → `.btn-copy`
- `<span style="min-width: 100px;"><strong>` → `<span class="variant-label"><strong>`
- Inline `showTooltip()` removed → `<script src="/static/js/tooltip.js">`
- Duplicate conditional: `style="opacity: 0.6; background-color: #f5f5f5;"` → `class="variant-row variant-row--duplicate"`

- [ ] **Step 1: Rewrite debug-title-variants.html**

- [ ] **Step 2: Rewrite debug-url-variants.html**

- [ ] **Step 3: Run integration tests**

Run: `uv run --python /Users/keith/.local/share/uv/python/cpython-3.14.0-macos-aarch64-none/bin/python3.14 -m pytest tests/ -v`

Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add templates/debug-title-variants.html templates/debug-url-variants.html
git commit -m "feat: redesign debug variant templates with new design system

Replace .metadata-panel/.url-item/.copy-btn with .panel/.variant-row/
.btn-copy. Remove inline styles. Replace duplicated showTooltip() with
shared tooltip.js. Use .form-row/.text-input/.btn-primary for forms."
```

---

## Task 7: Update `debug-inline-image.html` template

**Files:**
- Modify: `templates/debug-inline-image.html`

- [ ] **Step 1: Rewrite the template**

Key changes:
- Wrap content in `<div class="page-container">`
- `.metadata-panel` → `.panel`
- `<h2>` → `<div class="panel-label">`
- Remove the `<style>` block for `#file-input::file-selector-button` (now in `mirror.css`)
- Height row: `<div style="display: flex; gap: 10px; align-items: center;">` → `<div class="height-row">`
- Number inputs: `style="padding: 8px; font-size: 14px; width: 80px;"` → `class="text-input"` (+ `style="width: 80px;"` for width override on first input)
- Disabled input: remove `style="...background: #f5f5f5;"` (handled by `.text-input:disabled`)
- Paste button: `style="padding: 8px 16px; font-size: 14px;"` → `class="btn-primary"`
- Image input row: `style="display: flex; gap: 10px; align-items: center;"` → `class="image-input-row"`
- "or" text: `style="color: #666;"` → `style="color: var(--color-text-secondary);"`
- Hint text: `style="font-size: 12px; color: #666; margin-top: 8px;"` → `class="image-input-hint"`
- Copy button: `style="padding: 8px 16px; font-size: 14px;"` → `class="btn-primary"`
- Base64 preview div: remove inline monospace/color styles → `class="code-block"`
- Dimensions text: `style="margin-top: 8px; color: #666; font-size: 14px;"` → `class="output-dimensions"`
- Tag output div: `style="margin-top: 12px;"` → `class="output-section"`

- [ ] **Step 2: Run integration tests**

Run: `uv run --python /Users/keith/.local/share/uv/python/cpython-3.14.0-macos-aarch64-none/bin/python3.14 -m pytest tests/ -v`

Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add templates/debug-inline-image.html
git commit -m "feat: redesign debug-inline-image.html with new design system

Remove all inline styles and <style> block. Use .panel, .text-input,
.btn-primary, .code-block, .height-row, .image-input-row classes.
File selector button styling moved to mirror.css."
```

---

## Task 8: Update `paste-favicon.js` dynamic class references

**Files:**
- Modify: `static/js/paste-favicon.js`

The `addPastedFavicon()` function (line 87) dynamically creates DOM elements with old class names and inline styles. It needs to be updated to use the new design system classes.

- [ ] **Step 1: Update `addPastedFavicon()` DOM creation**

In `static/js/paste-favicon.js`, the `addPastedFavicon` function (starting line 87) creates a div with `className = 'url-item favicon-pasted-option'` and builds inner HTML with inline styles. Change:

- Line 94: `pastedDiv.className = 'url-item favicon-pasted-option'` → `pastedDiv.className = 'variant-row favicon-pasted-option'`
- Line 103: `class="copy-btn"` → `class="btn-copy"`
- Line 104: `<span style="min-width: 100px;">` → `<span class="variant-label">`
- Lines 106-108: Remove `style="font-family: monospace; font-size: 0.85em; color: #666; word-break: break-all;"` and use `class="variant-value favicon-inline-preview"` instead
- Line 126: `container.querySelector('.copy-btn')` → `container.querySelector('.btn-copy')`

Also update `showPasteTooltip()` (line 22) to use the `.tooltip` class instead of inline styles:
- Remove the `tooltip.style.cssText = ...` block
- Set `tooltip.className = 'tooltip'` instead
- Keep the positioning lines (`tooltip.style.left` and `tooltip.style.top`) since those are dynamic values

- [ ] **Step 2: Run integration tests**

Run: `uv run --python /Users/keith/.local/share/uv/python/cpython-3.14.0-macos-aarch64-none/bin/python3.14 -m pytest tests/ -v`

Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add static/js/paste-favicon.js
git commit -m "fix: update paste-favicon.js to use new design system classes

Change dynamic DOM creation from .url-item/.copy-btn to .variant-row/
.btn-copy. Remove inline styles in favor of .variant-label and
.favicon-inline-preview classes. Use .tooltip class for paste tooltip."
```

---

## Task 9: Run full test suite and verify

**Files:** None (verification only)

- [ ] **Step 1: Run the complete test suite**

Run: `uv run --python /Users/keith/.local/share/uv/python/cpython-3.14.0-macos-aarch64-none/bin/python3.14 -m pytest tests/ -v`

Expected: All 328 tests pass

- [ ] **Step 2: Run linting and format checks**

Run: `make check`

Expected: No linting errors

- [ ] **Step 3: Start the dev server and visually verify pages**

Run: `make run` (then open browser to verify each page)

Check each page visually:
- `/mirror-links` — panels should be elevated cards, copy buttons should be pills, badges should be soft dots
- `/mirror-favicons` — cache panel should use new classes, badges should be soft dots
- `/debug/title-variants` — should use panels, variant rows, copy pills
- `/debug/url-variants` — same as title-variants
- `/debug/inline-image` — panels, text inputs, buttons should use new styles

- [ ] **Step 4: Final commit if any fixups needed**

If any issues were found and fixed during visual verification, commit them.

```bash
git add -A
git commit -m "fix: visual redesign adjustments after testing"
```