# Test Pages Interactive — Specification

**Route:** `/test-pages-interactive` (GET only)
**Template:** `templates/test-pages-interactive.html`
**Backend:** `web-tool.py::test_pages_interactive()`

---

## Overview

The Test Pages Interactive page provides a client-side UI for building test page URLs with configurable parameters. It generates URLs for the `/test-page` endpoint by collecting form inputs and rendering the resulting query string. All state is client-side JavaScript; the backend renders a static template with no dynamic template data.

---

## Data Flow

```
User loads /test-pages-interactive
         │
         ▼
web-tool.py::test_pages_interactive()
    │
    └── template_env.get_template('test-pages-interactive.html').render({})
            │
            ▼
         test-pages-interactive.html
            │
            ▼
         JavaScript state management
                  │
                  ▼
         /test-page?{query-string}
```

---

## Page Sections

### 1. Page Content Panel

**Purpose:** Form inputs for building test page URLs.

**Content:** A `.metadata-panel` containing:

- **Title input** — text input for the `title` parameter
- **Fragment Options** — three text inputs:
  - Fragment (id on h1)
  - Anchor Fragment
  - Wrapper Fragment
- **Content Flags** — five checkboxes:
  - URL has parens
  - URL has brackets
  - URL has spaces
  - Unicode content
  - Emoji content
- **Action buttons:**
  - Load Test Page — navigates to `/test-page?...`
  - Copy URL — copies full URL to clipboard
  - Copy status span — shows "Copied!" for 2 seconds

---

### 2. Generated URL Panel

**Purpose:** Display the currently built query string URL.

**Content:** A `.metadata-panel` containing a `<pre>` element showing the current `/test-page?...` URL. Updates live on any input change.

---

### 3. Preset Configurations Panel

**Purpose:** One-click presets for common test configurations.

**Content:** A `.metadata-panel` containing six preset buttons in a responsive grid.

| Preset | Title | Fragment | Anchor Fragment | Wrap Fragment | URL Parens | URL Brackets | URL Space | Unicode | Emoji |
|--------|-------|----------|-----------------|---------------|------------|--------------|-----------|---------|--------|
| `unicode` | 日本語タイトル — Русский | — | — | — | — | — | — | yes | — |
| `emoji` | Hello 🌍 World 🚀 | — | — | — | — | — | — | — | yes |
| `fragment` | Fragment Test Page | main-section | anchor-frag | wrapper-frag | — | — | — | — | — |
| `special-chars` | File: Name [v1].txt (copy) | — | — | — | — | — | — | — | — |
| `url-edge-cases` | URL Edge Cases | — | — | — | yes | yes | yes | — | — |
| `all` | 日本語 🚀 [v1] | main-section | anchor-frag | wrapper-frag | yes | yes | — | yes | yes |

---

### 4. Navigation Links

**Purpose:** Quick links to other test/debug pages.

**Content:**
```html
<a href="/test-page?title=Basic+Test&fragment=basic-section">Basic test page</a> |
<a href="/debug/title-variants">Title variants debug</a> |
<a href="/debug/url-variants">URL variants debug</a>
```

---

## JavaScript State

```javascript
// Form element values read on demand via buildQueryString()
function buildQueryString() {
    const params = new URLSearchParams();

    const title = document.getElementById('title').value.trim();
    if (title) params.set('title', title);

    const fragment = document.getElementById('fragment').value.trim();
    if (fragment) params.set('fragment', fragment);

    const anchorFragment = document.getElementById('anchor-fragment').value.trim();
    if (anchorFragment) params.set('anchor-fragment', anchorFragment);

    const wrapFragment = document.getElementById('wrap-fragment').value.trim();
    if (wrapFragment) params.set('wrap-fragment', wrapFragment);

    if (document.getElementById('url-has-parens').checked) params.set('url-has-parens', 'yes');
    if (document.getElementById('url-has-brackets').checked) params.set('url-has-brackets', 'yes');
    if (document.getElementById('url-has-space').checked) params.set('url-has-space', 'yes');
    if (document.getElementById('unicode-content').checked) params.set('unicode-content', 'yes');
    if (document.getElementById('emoji-content').checked) params.set('emoji-content', 'yes');

    return params.toString();
}
```

**`updateGeneratedUrl()` — updates the displayed URL:**
```javascript
function updateGeneratedUrl() {
    const qs = buildQueryString();
    const url = '/test-page' + (qs ? '?' + qs : '');
    document.getElementById('generated-url').textContent = url;
    return url;
}
```

**`loadTestPage()` — navigates to the constructed URL:**
```javascript
function loadTestPage() {
    const qs = buildQueryString();
    const url = '/test-page' + (qs ? '?' + qs : '');
    window.location.href = url;
}
```

**`copyUrl()` — copies full URL to clipboard:**
```javascript
function copyUrl() {
    const qs = buildQueryString();
    const url = '/test-page' + (qs ? '?' + qs : '');
    navigator.clipboard.writeText(window.location.origin + url).then(() => {
        document.getElementById('copy-status').textContent = 'Copied!';
        setTimeout(() => {
            document.getElementById('copy-status').textContent = '';
        }, 2000);
    });
}
```

**`loadPreset(preset)` — resets form and applies preset values, then loads:**
```javascript
function loadPreset(preset) {
    // Reset all fields first
    // ... reset logic ...

    switch (preset) {
        case 'unicode':    // sets title, checks unicode-content
        case 'emoji':      // sets title, checks emoji-content
        case 'fragment':   // sets title and all fragment fields
        case 'special-chars': // sets title
        case 'url-edge-cases': // checks parens, brackets, space
        case 'all':        // sets all fields
    }

    updateGeneratedUrl();
    loadTestPage();
}
```

**Auto-update on input change:**
```javascript
document.querySelectorAll('input').forEach(input => {
    input.addEventListener('input', updateGeneratedUrl);
    input.addEventListener('change', updateGeneratedUrl);
});
```

**Initialization:**
```javascript
updateGeneratedUrl();  // Show initial URL on page load
```

---

## Form Elements

| Element ID | Type | Parameter | Default |
|------------|------|-----------|---------|
| `title` | text | `title` | `"Test Page"` |
| `fragment` | text | `fragment` | `""` |
| `anchor-fragment` | text | `anchor-fragment` | `""` |
| `wrap-fragment` | text | `wrap-fragment` | `""` |
| `url-has-parens` | checkbox | `url-has-parens` | unchecked |
| `url-has-brackets` | checkbox | `url-has-brackets` | unchecked |
| `url-has-space` | checkbox | `url-has-space` | unchecked |
| `unicode-content` | checkbox | `unicode-content` | unchecked |
| `emoji-content` | checkbox | `emoji-content` | unchecked |

---

## CSS Classes

| Class | Referenced from |
|-------|----------------|
| `.metadata-panel` | mirror.css |

---

## Backend Details

**Template loading:** Uses `template_env.get_template()` (not `render_template()`).

```python
template = template_env.get_template("test-pages-interactive.html")
rendered_html = template.render({})
return make_response(rendered_html)
```

**Template data:** Empty dict `{}` — no server-side data; all configuration is client-side.

**Dependency:** Jinja2 via `template_env` (application-wide Jinja environment).

---

## Edge Cases

| Case | Behavior |
|------|----------|
| All inputs empty | URL is just `/test-page` |
| Title with special chars | URL-encoded via `URLSearchParams` |
| Checkbox unchecked | Parameter omitted entirely |
| Copy fails | No error shown to user (silent) |

---

## Testing Checklist

- [ ] GET /test-pages-interactive → page loads with empty form
- [ ] Typing in title → Generated URL updates
- [ ] Checking checkboxes → Generated URL updates
- [ ] Click "Load Test Page" → navigates to /test-page with correct params
- [ ] Click "Copy URL" → clipboard contains full URL with origin
- [ ] Click "Unicode" preset → loads test page with Russian/CJK title
- [ ] Click "Emoji" preset → loads test page with emoji title
- [ ] Click "Fragment" preset → loads test page with all fragment fields set
- [ ] Click "URL Edge Cases" preset → loads test page with parens/brackets/space links
- [ ] Click "All" preset → loads test page with all options enabled
- [ ] Generated URL shows correct query string encoding
