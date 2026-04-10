# Mirror Favicons Page — Specification

**Route:** `/mirror-favicons` (GET/POST)
**Template:** `templates/mirror-favicons.html`
**Backend:** `web-tool.py::get_mirror_favicons()` (GET), `web-tool.py::add_favicon_override()` (POST API)

---

## Overview

The Mirror Favicons page accepts a clipboard payload (via query params and `pyperclip`) containing page metadata (URL, title, HTML), discovers all available favicon candidates for the page, resolves and validates each one, and renders an interactive UI for browsing the favicon candidates and adding user overrides to the three-tier favicon cache.

---

## Data Flow

```
User pastes clipboard data
         │
         ▼
web-tool.py:get_mirror_favicons()
    │
    ├── html_util.get_page_metadata() — reads query params + pyperclip
    │       └── PageMetadata: url, title, html, soup
    │
    ├── html_util.get_favicon_links(url, soup, include="all")
    │       └── list[RelLink] — all discovered candidates (cached + HTML + common files)
    │
    ├── validate each favicon:
    │       ├── html_util.get_favicon_cache_source(url, href) → cache_source dict
    │       └── url_util.get_image_size(href) → width, height, image_type
    │           (cached favicons that fail to load are still included as "invalid")
    │
    ├── html_util.sort_favicon_links(favicons, include='all')
    │
    ├── auto-cache top favicon if none cached (html_util.add_favicon_to_cache)
    │
    └── template.render()
            ├── url
            ├── cache_key
            ├── cache_files (dict: overrides/defaults/discovered)
            └── favicons (list[RelLink])
                    │
                    ▼
         mirror-favicons.html (Jinja2)
                    │
                    ▼
         addOverride() JavaScript function
```

---

## GET Flow

1. Read clipboard contents via `pyperclip.paste()`
2. Parse JSON payload: `{url, title, html}`
3. Extract page URL and BeautifulSoup-parsed HTML
4. Call `html_util.get_favicon_links(url, soup, include="all")` to get all favicon candidates
5. For each favicon:
   - Call `html_util.get_favicon_cache_source(url, href)` to determine which cache file contains it (if any)
   - Call `url_util.get_image_size(href)` to validate and get dimensions
   - If cached but image fails to load, include it with `image_type = "invalid"` (do not exclude)
   - If not cached and image fails to load, exclude it silently
6. Sort favicons by preference via `html_util.sort_favicon_links(favicons, include='all')`
7. If no favicon is cached and at least one valid favicon exists, auto-cache the top one via `html_util.add_favicon_to_cache()`
8. Load all three cache file manifests (entries count, path, precedence) for the cache-panel display
9. Render template with `url`, `cache_key`, `cache_files`, `favicons`

---

## POST /add-favicon-override

**Route:** `/add-favicon-override`
**Content-Type:** `application/json`

**Request body:**
```json
{
  "favicon_url": "https://example.com/favicon.png",
  "page_url": "https://example.com/path/page",
  "scope": "domain",
  "save_inline": false
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `favicon_url` | `str` | Yes | URL of the favicon to cache |
| `page_url` | `str` | Yes | Page URL to associate the override with |
| `scope` | `str` | No | `"domain"` (default) or `"path"` — controls cache key granularity |
| `save_inline` | `bool` | No | If `true`, fetch and resize favicon to height=20, store as base64 inline data |

**Cache key generation:**
- Parse `page_url` with `urlparse`, strip `www.` prefix from netloc
- `scope = "domain"`: key = netloc (e.g., `example.com`)
- `scope = "path"`: key = `netloc/first_path_segment` (e.g., `example.com/blog`)

**Response (success):**
```json
{
  "success": true,
  "cache_key": "example.com"
}
```

**Response (error):**
```json
{
  "success": false,
  "error": "Missing favicon_url or page_url"
}
```

**Behavior:**
- Preserves header comments in `static/favicon-overrides.yml` when writing
- Invalidates in-memory YAML cache for `FAVICON_OVERRIDES` after write
- `save_inline = true`: stores as `{'url': favicon_url, 'inline_image': inline_data}`
- `save_inline = false`: stores as plain URL string

---

## Page Sections

### 1. Three-Tier Cache System (cache-panel)

Displays a summary of all three favicon cache files in precedence order.

**Visual structure:**
```html
<div class="cache-panel">
  <h2>Three-Tier Cache System</h2>
  <p>Favicons are searched in order of precedence (highest to lowest):</p>
  <div class="cache-file-list">
    <div class="cache-file-item precedence-1">
      <div class="cache-file-name">
        1. User Overrides
        <span class="cache-badge cache-overrides">N entries</span>
      </div>
      <div class="cache-file-path">/absolute/path/to/favicon-overrides.yml</div>
      <div class="cache-file-stats">Manual overrides - highest priority...</div>
    </div>
    ... (precedence-2, precedence-3)
  </div>
  <p><strong>Current URL:</strong> {{ url|e }}</p>
</div>
```

**Cache file info (per tier):**

| Key | Name | File | Precedence |
|-----|------|------|------------|
| `overrides` | User Overrides | `static/favicon-overrides.yml` | 1 (highest) |
| `defaults` | App Defaults | `static/favicon.yml` | 2 |
| `discovered` | Auto-Discovered | `local-cache/favicon.yml` (or `/data/favicon.yml` in container) | 3 (lowest) |

Each `cache-file-item` gets `precedence-N` class where N is 1, 2, or 3.

---

### 2. Available Favicons List

Iterates over `favicons` (sorted by preference) and renders one `.favicon-entry` per favicon.

**Per-entry fields:**
- `f.href` — original href
- `f.resolved_href` — shown only if different from `f.href`
- `f.image_type` — e.g., `"image/png"`, `"image/svg"`, `"image/ico"`, `"invalid"`
- `f.width`, `f.height` — pixel dimensions
- `f.inline_image` — base64 data URL if cached with inline data
- `f.cache_source` — dict with `file` (override/default/discovered/None), `cache_key`, `precedence`

**Cache source badge logic:**
| Condition | Badge |
|-----------|-------|
| `f.cache_source.file == 'override'` | `cache-badge cache-override` with text "OVERRIDE" |
| `f.cache_source.file == 'default'` | `cache-badge cache-default` with text "DEFAULT" |
| `f.cache_source.file == 'discovered'` | `cache-badge cache-discovered` with text "DISCOVERED" |
| `f.inline_image` is set | Additional `cache-badge cache-override` with text "INLINE" |
| `f.cache_source.file` is None | `cache-badge cache-none` with text "NOT CACHED" |
| `f.image_type == 'invalid'` | `cache-badge cache-invalid` with text "INVALID - FAILED TO LOAD" |

**Image preview:**
- If `image_type != 'invalid'`: shows 20px height preview (`<img src="f.href" height="20">`), inline preview if available, and full-size preview
- If `image_type == 'invalid'`: shows error message instead of previews

**Override form:**
- Shown only if `f.cache_source.file` is None or is not `'override'`
- Contains radio buttons for scope (`domain` / `path`), checkbox for `save_inline`
- Button calls `addOverride(f.href, url, 'form-{index}')`
- After POST success: shows success message, reloads page after 1.5s
- After POST failure: shows error message, re-enables button

---

## addOverride() JavaScript Function

```javascript
function addOverride(faviconHref, pageUrl, formId) {
    const form = document.getElementById(formId);
    const scope = form.querySelector('input[name="scope"]:checked').value;
    const saveInline = form.querySelector('input[name="save_inline"]').checked;
    const messageEl = form.querySelector('.override-message');
    const button = form.querySelector('button');

    button.disabled = true;
    messageEl.textContent = 'Adding override...';
    messageEl.className = 'override-success';

    fetch('/add-favicon-override', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            favicon_url: faviconHref,
            page_url: pageUrl,
            scope: scope,
            save_inline: saveInline
        })
    })
    .then(resp => resp.json())
    .then(data => {
        if (data.success) {
            messageEl.textContent = '✓ Override added: ' + data.cache_key;
            messageEl.className = 'override-success';
            setTimeout(() => { location.reload(); }, 1500);
        } else {
            messageEl.textContent = '✗ Error: ' + data.error;
            messageEl.className = 'override-error';
            button.disabled = false;
        }
    })
    .catch(err => {
        messageEl.textContent = '✗ Error: ' + err.message;
        messageEl.className = 'override-error';
        button.disabled = false;
    });
}
```

**Steps:**
1. Read scope radio and save_inline checkbox from the form
2. Disable button, show "Adding override..." message
3. POST JSON to `/add-favicon-override`
4. On success: show success message with cache key, auto-reload after 1.5s
5. On error: show error message, re-enable button

---

## CSS Classes

| Class | Element | Description |
|-------|---------|-------------|
| `.cache-panel` | Outer container | Three-tier cache system section |
| `.cache-file-list` | Container | Wraps all `.cache-file-item` elements |
| `.cache-file-item` | Item wrapper | Each cache tier entry; also gets `precedence-1`, `precedence-2`, or `precedence-3` |
| `.precedence-N` | `.cache-file-item` | N = 1 (overrides), 2 (defaults), 3 (discovered) |
| `.cache-file-name` | Name line | Contains tier name, precedence number, and `.cache-badge` |
| `.cache-badge` | Badge span | Cache source badge; modifier classes below |
| `.cache-override` | Badge modifier | Override badge (red/bold) |
| `.cache-default` | Badge modifier | Default badge |
| `.cache-discovered` | Badge modifier | Discovered badge |
| `.cache-none` | Badge modifier | Not cached badge |
| `.cache-invalid` | Badge modifier | Invalid image badge |
| `.cache-key-info` | Span | Shows "cached as: {cache_key}" |
| `.favicon-entry` | Entry container | Each favicon in the list |
| `.invalid` | `.favicon-entry` modifier | Applied when `image_type == 'invalid'` |
| `.override-form` | Form container | Add Override form per favicon |
| `.override-message` | Message div | Status message area |
| `.override-success` | Message modifier | Success message styling |
| `.override-error` | Message modifier | Error message styling |

---

## Backend Template Data

| Variable | Type | Description |
|----------|------|-------------|
| `url` | `str` | Current page URL |
| `cache_key` | `str` | Domain-level cache key for this URL (e.g., `example.com`) |
| `cache_files` | `dict[str, dict]` | Per-tier cache info: `overrides`, `defaults`, `discovered` |
| `cache_files[key].name` | `str` | Human-readable name |
| `cache_files[key].path` | `str` | Absolute file path |
| `cache_files[key].precedence` | `int` | 1, 2, or 3 |
| `cache_files[key].count` | `int` | Number of entries |
| `cache_files[key].entries` | `dict` | Raw YAML entries (keyed by cache key) |
| `favicons` | `list[RelLink]` | Sorted list of favicon candidates |

**RelLink fields on `favicons`:**

| Field | Type | Description |
|-------|------|-------------|
| `href` | `str` | Original/fetched href |
| `resolved_href` | `str\|None` | Resolved URL after redirects |
| `image_type` | `str\|None` | MIME type or `"invalid"` |
| `width` | `int` | Pixel width (0 if invalid) |
| `height` | `int` | Pixel height (0 if invalid) |
| `inline_image` | `str\|None` | Base64 data URL if stored inline |
| `cache_source.file` | `str\|None` | `"override"`, `"default"`, `"discovered"`, or `None` |
| `cache_source.cache_key` | `str\|None` | Cache key this favicon is stored under |
| `cache_source.precedence` | `int\|None` | 1, 2, 3, or `None` |

---

## Edge Cases

| Case | Behavior |
|------|----------|
| Cached favicon fails to load | Included with `image_type = "invalid"`, shown with error badge and message; override form still shown so user can re-add |
| Non-cached favicon fails to load | Excluded from list silently |
| No favicons found | Renders empty `favicons` list; cache panel still shown |
| Override already exists for key | Overwrites existing entry in `favicon-overrides.yml` |
| `scope = "path"` but URL has no path | Falls back to domain-only key |
| `save_inline = true` but encoding fails | Falls back to storing plain URL |
| `www.` prefix in URL | Stripped from netloc for cache key matching and display |
| HTML clipboard parse fails | `metadata.error` set; page renders without favicons |

---

## Dependencies

- **BeautifulSoup** (`lxml`) — HTML parsing for favicon link extraction from `<head>`
- **pyperclip** — clipboard access for initial page data
- **html_util** — `get_favicon_links()`, `get_favicon_cache_source()`, `sort_favicon_links()`, `add_favicon_to_cache()`, `FAVICON_OVERRIDES`, `FAVICON_DEFAULTS`, `FAVICON_LOCAL_CACHE`, `_load_yaml_with_cache()`
- **img_util** — `encode_favicon_inline()` for inline base64 encoding
- **url_util** — `get_image_size()`, `make_absolute_urls()`
- **Jinja2** — server-side template rendering
- **JavaScript (vanilla)** — `addOverride()` function, no framework

---

## Testing Checklist

- [ ] GET with valid clipboard JSON → renders favicons list and cache panel
- [ ] GET with invalid clipboard JSON → renders with error, cache panel still shown
- [ ] Cached favicon that is valid → shows correct cache badge and source
- [ ] Cached favicon that fails to load → shows `invalid` class and badge, still has override form
- [ ] Non-cached favicon that fails to load → not shown in list
- [ ] Non-cached favicon that is valid → shows "NOT CACHED" badge and override form
- [ ] Add override (domain scope) → POST succeeds, cache key correct, page reloads
- [ ] Add override (path scope) → cache key includes first path segment
- [ ] Add override with `save_inline: true` → stores dict format with `inline_image`
- [ ] Override already exists → overwrites and returns success
- [ ] Cache panel shows correct entry counts for all three tiers
- [ ] Precedence badges shown in correct order (1, 2, 3)
- [ ] Image previews render at correct sizes (20px height, full size)
- [ ] Inline preview shown when `inline_image` is present
- [ ] `addOverride()` shows success message with cache key, then reloads
- [ ] `addOverride()` shows error message on failure, re-enables button
