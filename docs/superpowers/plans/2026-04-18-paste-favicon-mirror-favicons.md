# Paste Favicon — Mirror Favicons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Paste Favicon" block to the `/mirror-favicons` page between the cache panel and the Available Favicons list. Pasting an image inserts a favicon-entry-style block that can be added to overrides. The inline checkbox is pre-checked and disabled.

**Architecture:** The paste favicon section is a new panel above the favicon list. Paste handling reuses `paste-favicon.js` utilities (`blobToBase64`, `sendToServer`, `handlePasteFavicon`). A new `addPastedFaviconEntry()` function builds the pasted block dynamically. `handlePasteFavicon` in `paste-favicon.js` is extended to accept an optional `onPasted` callback.

**Tech Stack:** Vanilla JS (no framework), existing `paste-favicon.js` utilities, Flask/Jinja2 template, existing `addOverride()` JS function.

---

## File Map

| File | Action |
|------|--------|
| `templates/mirror-favicons.html` | Modify — add paste panel section, add `addPastedFaviconEntry` JS function and DOMContentLoaded wiring, include `paste-favicon.js` script |
| `static/js/paste-favicon.js` | Modify — extend `handlePasteFavicon` to accept optional `onPasted` callback |
| `static/mirror.css` | No changes needed |

---

## Task 1: Extend `handlePasteFavicon` in `paste-favicon.js` to accept an `onPasted` callback

**Files:**
- Modify: `static/js/paste-favicon.js:200` (signature of `handlePasteFavicon`)

- [ ] **Step 1: Read the current function signature**

Run: `grep -n "async function handlePasteFavicon" static/js/paste-favicon.js`
Expected: `async function handlePasteFavicon(btn, container) {` at line 200

- [ ] **Step 2: Update function signature and add callback invocation**

Change the function signature from:
```javascript
async function handlePasteFavicon(btn, container) {
```
To:
```javascript
async function handlePasteFavicon(btn, container, options = {}) {
```

Inside the `_pasteHandler` async function, after `const data = await sendToServer(rawBase64);` and after the existing `addPastedFavicon` call (around line 249), add:
```javascript
// Call onPasted callback if provided
if (options.onPasted) {
    options.onPasted(data);
}
```

- [ ] **Step 3: Commit**

```bash
git add static/js/paste-favicon.js
git commit -m "feat(paste-favicon): add onPasted callback option to handlePasteFavicon"
```

---

## Task 2: Add paste favicon section to `mirror-favicons.html`

**Files:**
- Modify: `templates/mirror-favicons.html:85-86` (insert paste panel before `<h2>Available Favicons`)

- [ ] **Step 1: Read lines around the insertion point**

Run: `sed -n '80,92p' templates/mirror-favicons.html`
Expected: Line 84 closes the first `</div>` panel, line 86 is `<h2>Available Favicons`

- [ ] **Step 2: Add paste panel section before `<h2>`**

After line 84 (`</div>` closing cache panel) and before line 86 (`<h2>Available Favicons`), insert:

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
```

- [ ] **Step 3: Commit**

```bash
git add templates/mirror-favicons.html
git commit -m "feat(mirror-favicons): add paste favicon panel section"
```

---

## Task 3: Add `addPastedFaviconEntry` JS function and DOMContentLoaded wiring to `mirror-favicons.html`

**Files:**
- Modify: `templates/mirror-favicons.html` (add `<script src="/static/js/paste-favicon.js">` and new JS functions before `</head>`, add DOMContentLoaded wiring)

- [ ] **Step 1: Add script include for paste-favicon.js**

After line 6 (the `</link>` for mirror.css) and before the existing inline `<script>` block, add:
```html
    <script src="/static/js/paste-favicon.js"></script>
```

- [ ] **Step 2: Add helper functions before `</head>` closing script**

After the existing `addOverride` function (line 50), inside the same `<script>` block, add:

```javascript
        function showPasteTooltip(btn, message) {
            const existing = document.body.querySelector('.tooltip');
            if (existing) existing.remove();
            const tooltip = document.createElement('span');
            tooltip.className = 'tooltip';
            tooltip.textContent = message;
            const rect = btn.getBoundingClientRect();
            tooltip.style.left = (rect.left + window.scrollX) + 'px';
            tooltip.style.top = (rect.bottom + window.scrollY + 4) + 'px';
            document.body.appendChild(tooltip);
            setTimeout(() => tooltip.remove(), 2000);
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function addPastedFaviconEntry(data, pageUrl, overrideDomain, overridePathScope, hasPathScope) {
            const container = document.getElementById('paste-favicon-section');
            if (!container) return;
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
                <p>Image Type: image/png | Size: ${data.height || 20}x${data.width || 20}</p>
                <p><img src="${escapedDataUrl}" height="20" alt="20px height preview" /> 20px height preview</p>
                <p><img src="${escapedDataUrl}" alt="Full size" /> Full size (${data.width || 20}x${data.height || 20})</p>
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

Note: All user-controlled values are escaped via `escapeHtml()` before insertion into innerHTML. `showPasteTooltip` is also included for consistency with the paste-favicon.js pattern (used if paste fails).

- [ ] **Step 3: Add DOMContentLoaded wiring**

After the `addOverride` function's closing `}` (line 50), before `</script>` (line 51), add:

```javascript
        document.addEventListener('DOMContentLoaded', () => {
            const pasteBtn = document.getElementById('paste-favicon-btn');
            const faviconSection = document.getElementById('paste-favicon-section');

            if (pasteBtn && faviconSection) {
                pasteBtn.addEventListener('click', () => {
                    handlePasteFavicon(pasteBtn, faviconSection, {
                        onPasted: (data) => {
                            addPastedFaviconEntry(
                                data,
                                '{{ url|e }}',
                                '{{ override_domain }}',
                                '{{ override_path_scope }}',
                                {{ 'true' if url.split('/')|length > 3 and url.split('/')[3] else 'false' }}
                            );
                        }
                    });
                });
            }
        });
```

- [ ] **Step 4: Verify no Jinja2 syntax errors**

Run: `uv run python -c "from jinja2 import Environment, FileSystemLoader; env = Environment(loader=FileSystemLoader('templates')); t = env.get_template('mirror-favicons.html'); print('OK')"`

- [ ] **Step 5: Commit**

```bash
git add templates/mirror-favicons.html
git commit -m "feat(mirror-favicons): wire up paste favicon with addPastedFaviconEntry"
```

---

## Task 4: Test the feature in browser

**Files:**
- None (manual testing)

- [ ] **Step 1: Start the dev server**

Run: `make run`

- [ ] **Step 2: Navigate to mirror-favicons page**

Open: `http://localhost:5000/mirror-favicons` (with appropriate clipboard data)

- [ ] **Step 3: Verify paste button appears**

The "Paste Favicon" button should be visible in the new panel above "Available Favicons"

- [ ] **Step 4: Click paste button**

Button text changes to "Waiting for paste... (Esc to cancel)"

- [ ] **Step 5: Press Esc to cancel**

Button reverts to "Paste Favicon"

- [ ] **Step 6: Paste a real image**

A pasted favicon block appears with PASTED, INLINE, NOT CACHED badges. Inline checkbox is checked and disabled. Domain/path scope radios present.

- [ ] **Step 7: Click "Add to Overrides" on pasted block**

Success message appears, page reloads after 1.5s. Entry appears in `static/favicon-overrides.yml`.

---

## Spec Coverage Check

| Spec Section | Task |
|--------------|------|
| Placement between cache panel and favicon list | Task 2 |
| Paste button + paste panel structure | Task 2 |
| Paste button click → "Waiting for paste..." state | Task 3 (handlePasteFavicon does this) |
| Paste image → pasted block appears | Task 3 |
| Block shows PASTED, INLINE, NOT CACHED badges | Task 3 |
| Inline checkbox pre-checked + disabled | Task 3 |
| Domain/path scope radios | Task 3 |
| "Add to Overrides" → success + reload | Task 3 (uses existing addOverride) |
| Error handling on paste failure | Task 1 (handlePasteFavicon handles) |
| handlePasteFavicon accepts onPasted callback | Task 1 |

All spec items are covered. No gaps.