# Mirror Links Page — Specification

**Route:** `/mirror-links` (GET/POST)
**Template:** `templates/mirror-links.html`
**Backend:** `web-tool.py::get_mirror_links()`

---

## Overview

The Mirror Links page accepts a clipboard payload (via query params and `pyperclip`) containing page metadata (URL, title, HTML, etc.) and renders an interactive UI for building and copying link text in multiple formats. The page has a dual intended purpose:

1. **Per-page link builder** — builds a single link from the pasted page's URL/title with format variants
2. **Extracted links browser** — intended to extract all hyperlinks from the pasted HTML and let the user browse/copy them

**Note:** The extracted links browser is NOT YET implemented. The `get_mirror_links()` handler does not extract links from HTML, and `mirror-links.html` has no "Extracted Links" section. This spec documents the current behavior only.

All state is client-side. The server is stateless except for reading the clipboard on initial load.

---

## Data Flow

```
User pastes clipboard data
         │
         ▼
web-tool.py:get_mirror_links()
    │
    ├── util.get_page_metadata() — reads query params + pyperclip
    │       ├── url, title, html from clipboard JSON
    │       ├── parsed_url, fragment, fragment_text
    │       ├── favicon_url, favicons[]
    │       └── mirror_data (userAgent, htmlSize, etc.)
    │
    └── template.render()
            ├── title_variants[]
            ├── url_variants[]
            ├── fragment_variants[]
            ├── favicon (url, inline, width, height)
            └── mirror_data fields
                    │
                    ▼
         mirror-links.html (Jinja2)
                    │
                    ▼
         JavaScript state management + render()
```

---

## Page Sections

### 1. Links (Top) — Per-Page Link Builder

**Purpose:** Build a single link from the pasted page's URL and selected title, with 4 format options.

**Content:** Four static format rows — HTML, Markdown, Wiki-link, Simple — showing the currently selected link in each format.

**Behavior:**
- Displayed unconditionally (always shows something)
- `state.url` drives what URL is used
- `state.title` drives what link text used
- `state.fragmentText` appends to title when present (format: `fragmentText - title`)
- Each row has a **Copy** button copying that format's output
- **Auto-copy:** On page load (100ms after) and on every selection change, the HTML format is written to clipboard automatically

**Format builders (JavaScript):**

| Format | Function | Output example |
|--------|----------|----------------|
| HTML | `buildHtmlLink()` | `<img src="..." height="20" /> <a target="_blank" href="...">text</a>` |
| Markdown | `buildMarkdownLink()` | `[text](url)` or `[text](<url>)` if URL has `()[] <` |
| Wiki-link | `buildWikiLink()` | `[text\|url]` |
| Simple | `buildSimpleLink()` | `url text` |

**Display fields (per row):**
- `<span id="format-{format}-display">` — live rendered output
- `<span id="format-{format}-plain">` — plain text fallback for user verification
- `<button class="copy-btn" id="copy-{format}">` — copies `data-html`

---

### 2. Title

**Purpose:** Let the user pick which title variant to use as link text.

**Content:** Radio list of title variants. Duplicates are shown with `opacity: 0.6`.

**Variants (in order):**
| Label | Source |
|-------|--------|
| Original | `metadata.title` |
| ASCII + Emoji | `TitleVariants.ascii_and_emojis` |
| ASCII Only | `TitleVariants.ascii_only` |
| Path Safe | `TitleVariants.path_safe` |

**Behavior:** Radio `change` event → `state.title = input.dataset.text` → `render()` → auto-copy HTML

---

### 3. Fragment (conditional)

**Purpose:** Show fragment/anchor options for the page URL.

**Shown:** Only when `metadata.parsed_url.fragment` or `metadata.fragment_text` is truthy.

**Content:** Radio list of fragment variants. Duplicates grayed out.
| Label | Value |
|-------|-------|
| None | `""` |
| Fragment | `metadata.parsed_url.fragment` |
| Fragment Text | `metadata.fragment_text` |

**Behavior:** Radio `change` → `state.fragmentText = input.dataset.text` → `render()`

---

### 4. URL

**Purpose:** Let the user pick which URL variant to link to.

**Content:** Radio list. Default is `Clean` variant.
| Label | Source |
|-------|--------|
| Original | `metadata.url` |
| With Fragment | `metadata.url_with_fragment` |
| Clean | `metadata.url_clean` |
| Root | `metadata.url_root` |
| Host | `metadata.url_host` |

Duplicates hidden/grayed via `is_duplicate`.

**Behavior:** Radio `change` → `state.url = input.dataset.text` → `render()`

---

### 5. Favicon

**Purpose:** Choose favicon flavor (none, URL, inline, pasted) for the HTML format.

**Content:**
- Radio options: None, URL, Inline (if available), Pasted (if user has pasted)
- Each option shows a preview and Copy button

**Options (in order):**
| Value | Condition | Copy data |
|-------|-----------|-----------|
| `none` | Always | — |
| `url` | `metadata.favicon_url` truthy | `<img src="favicon_url" ...>` |
| `inline` | `favicon_inline` truthy | `<img src="favicon_inline" ...>` |
| `pasted` | User has pasted | `<img src="data:..." ...>` |

**Paste Favicon button:** Opens a 5-second paste window. After paste, adds a `pasted` radio option and selects it automatically.

**Behavior:**
- `state.faviconOption = checked radio value`
- `state.faviconWidth`, `state.faviconHeight` from cached/generated dimensions
- `render()` rebuilds HTML format with selected favicon

---

### 6. Metadata

**Purpose:** Debug/info panel showing raw page metadata.

**Fields shown:**
- HTML Size (bytes) — from `metadata.mirror_data.htmlSize`
- Content-Type — from `metadata.content_type`
- User Agent — from `metadata.mirror_data.userAgent`
- Cookie String — from `metadata.mirror_data.cookieString`
- Clipboard Error — shown only if `metadata.clipboard_error` is set

**Behavior:** Display only. No interactivity.

---

## JavaScript State

```javascript
const defaultValues = {
    title: "{{ title_variants[0].value|tojson }}",
    fragmentText: {% if fragment %}{{ fragment_text|tojson }}{% else %}''{% endif %},
    url: "{{ url_variants[0].url|tojson }}",
    favicon: {% if favicon %}{{ favicon|tojson }}{% else %}null{% endif %},
    faviconInline: {% if favicon_inline %}{{ favicon_inline|tojson }}{% else %}null{% endif %},
    pastedFavicon: null,
    faviconWidth: {% if favicon_width %}{{ favicon_width|tojson }}{% else %}null{% endif %},
    faviconHeight: {% if favicon_height %}{{ favicon_height|tojson }}{% else %}null{% endif %}
};

const state = {
    title: defaultValues.title,
    fragmentText: '',
    url: defaultValues.url,
    faviconOption: 'url',   // overridden from DOM on load
    faviconWidth: defaultValues.faviconWidth,
    faviconHeight: defaultValues.faviconHeight
};
```

**Note:** There is no `extractedLinks` array and no `selectedLinkIndex`. Extracted links are not implemented.

**`render()` function:**
1. Build HTML format using `buildHtmlLink(...)` with current state
2. Update `#format-html-display` innerHTML, `#format-html-plain` textContent
3. Build Markdown format, update display/plain
4. Build Wiki-link format, update display/plain
5. Build Simple format, update display/plain
6. Update each copy button's `data-html` dataset
7. Auto-copy HTML to clipboard if `linksInitialized` is true

**`linksInitialized` flag:**
- Set to `true` after the 100ms timeout initial copy completes
- Prevents clipboard spam during initial render

---

## Auto-Copy Behavior

| Event | Action |
|-------|--------|
| Page load (100ms after) | Copy HTML link for the current selection |
| Any radio change | Copy HTML link for currently selected link |
| Paste Favicon | No auto-copy — user must click Copy |

**Implementation:**
- After `render()`, check `if (linksInitialized)` then `navigator.clipboard.writeText(htmlLink)`
- On initial page load, set `linksInitialized = true` after the 100ms timeout copy completes

---

## Link Text Building

```
buildLinkText(title, fragmentText):
    return fragmentText ? `${fragmentText} - ${title}` : title
```

The fragment text prepends the title when present (e.g., `#install → "Installation - IBM - United States"`).

---

## HTML Format Builder

```javascript
function buildHtmlLink(title, fragmentText, url, faviconOption, faviconWidth, faviconHeight) {
    let html = '';
    const favH = faviconHeight || 20;
    const favW = faviconWidth || 20;
    if (faviconOption === 'pasted' && defaultValues.pastedFavicon) {
        html += `<img src="${escapeHtml(defaultValues.pastedFavicon)}" height="${favH}" width="${favW}" alt="Favicon" /> `;
    } else if (faviconOption === 'inline' && defaultValues.faviconInline) {
        html += `<img src="${escapeHtml(defaultValues.faviconInline)}" height="${favH}" width="${favW}" alt="Favicon" /> `;
    } else if (faviconOption === 'url' && defaultValues.favicon) {
        html += `<img src="${escapeHtml(defaultValues.favicon)}" height="${favH}" width="${favW}" alt="Favicon" /> `;
    }
    const linkText = buildLinkText(title, fragmentText);
    html += `<a target="_blank" href="${escapeHtml(url)}">${escapeHtml(linkText)}</a>`;
    return html;
}
```

---

## Markdown Escaping

```javascript
// Characters requiring URL wrapping in angle brackets
const MARKDOWN_URL_SAFE_WRAP_CHARS = /[()[\] <]/;

function escapeMarkdownText(text) {
    return text.replace(/\\/g, '\\\\').replace(/\[/g, '\\[').replace(/\]/g, '\\]');
}

function buildMarkdownLink(title, fragmentText, url) {
    const linkText = escapeMarkdownText(buildLinkText(title, fragmentText));
    if (MARKDOWN_URL_SAFE_WRAP_CHARS.test(url)) {
        const encoded = url.replace(/[<>]/g, (c) => encodeURIComponent(c));
        return `[${linkText}](<${encoded}>)`;
    }
    return `[${linkText}](${url})`;
}
```

**Rules:**
- Backslash `\` escaped first as `\\`
- Brackets `[` `]` escaped as `\[` `\]`
- URLs with `(`, `)`, `[`, `]`, `<`, `>`, or space → wrapped in `<>` with `<` `>` URI-encoded as `%3C` `%3E`

---

## Wiki-link Format

```javascript
function buildWikiLink(title, fragmentText, url) {
    const linkText = buildLinkText(title, fragmentText);
    return `[${linkText}|${url}]`;
}
```

No escaping — wiki-link syntax is different from Markdown.

---

## Simple Format

```javascript
function buildSimpleLink(title, fragmentText, url) {
    const linkText = buildLinkText(title, fragmentText);
    return `${url} ${linkText}`;
}
```

Plain `url text` output — URL first, then link text.

---

## CSS Classes

**`mirror.css` key classes:**
| Class | Used on |
|-------|---------|
| `.metadata-panel` | Title, URL, Fragment, Metadata sections |
| `.url-list` | Container for `.url-item` rows |
| `.url-item` | Each radio/copy row in Title, URL, Fragment |
| `.copy-btn` | All Copy buttons |
| `.favicon-section` | Favicon panel (outer wrapper) |

**`url-item` duplicate state:**
```html
<div class="url-item" style="opacity: 0.6; background-color: #f5f5f5;">
```
Set when `is_duplicate: true` in variant data.

---

## Backend Template Data

| Variable | Type | Description |
|----------|------|-------------|
| `title` | `str` | Page title |
| `title_variants` | `list[dict]` | `[{value, label, is_duplicate}]` |
| `fragment` | `str` | Raw URL fragment (`#anchor`) |
| `fragment_text` | `str` | Resolved fragment text from HTML |
| `fragment_variants` | `list[dict]` | `[{value, label, is_duplicate}]` |
| `url_variants` | `list[dict]` | `[{url, label, is_duplicate}]` |
| `links` | `list[dict]` | Legacy static links (Favicon, Simple) — passed but unused in template |
| `favicon` | `str\|None` | Favicon URL |
| `favicon_inline` | `str\|None` | Base64 inline favicon data URL |
| `favicon_width` | `int\|None` | Favicon pixel width |
| `favicon_height` | `int\|None` | Favicon pixel height |
| `content_type` | `str` | HTTP Content-Type |
| `user_agent` | `str` | User-Agent string used |
| `cookie_string` | `str` | Cookie string |
| `html_size` | `int` | HTML body size in bytes |
| `clipboard_error` | `str\|None` | Error message if clipboard parse failed |

**Note:** There is no `extracted_links` variable passed to the template.

---

## Edge Cases

| Case | Behavior |
|------|----------|
| No title | `metadata.title` defaults to `"link"` before title variant generation |
| Title variant duplicate | Row shown with `opacity: 0.6`, still selectable |
| URL variant duplicate | Row hidden (`is_duplicate: true`) |
| Fragment but no fragment text | Only "None" and "Fragment" options shown |
| Fragment but no fragment | Section not rendered |
| Clipboard parse error | `clipboard_error` shown in Metadata section; page still renders |
| `pyperclip` fails | `metadata.error` set; template handles `clipboard_error` |
| Favicon URL fails to load | `favicon_inline` not generated; URL favicon still available |
| Very long URL | Displayed as link, `word-break: break-all` handles wrapping |
| No HTML pasted | Page renders normally with available metadata |

---

## Paste Favicon Flow

```
User clicks "Paste Favicon"
         │
         ▼
handlePasteFavicon() arms one-time 'paste' listener
         │
         ▼
5-second timeout OR user presses Esc → disarm
         │
         ▼
User pastes image (Ctrl/Cmd+V)
         │
         ▼
'paste' event fires → preventDefault → extract image blob
         │
         ▼
blobToBase64(blob) → raw base64
         │
         ▼
POST /debug/inline-image {image_data, height: 20}
         │
         ▼
Response: {success, base64, inline}
         │
         ▼
addPastedFavicon(base64, container) →
    • Insert "Pasted" radio option before paste button
    • Set defaultValues.pastedFavicon = data URL
    • Set state.faviconOption = 'pasted'
    • Check the pasted radio
    • render()
```

---

## Dependencies

- **pyperclip** — clipboard access for initial page data
- **Jinja2** — server-side template rendering
- **JavaScript (vanilla)** — client-side state, no framework

**Note:** BeautifulSoup is not used by `get_mirror_links()` — link extraction is not implemented.

---

## Testing Checklist

- [ ] Paste page data → Links section shows all 4 format rows
- [ ] Title variant change updates all 4 format displays
- [ ] URL variant change updates all 4 format displays
- [ ] Fragment section appears when URL has a fragment
- [ ] HTML format includes favicon when favicon option is set
- [ ] Markdown format escapes `[`, `]`, `\` in link text
- [ ] Markdown format wraps URL in `<>` when URL contains `()[] <`
- [ ] Auto-copy HTML fires on page load (100ms after)
- [ ] Auto-copy HTML fires on radio selection change
- [ ] Paste favicon → pasted option appears and is selectable
- [ ] Copy button per format row copies correct HTML
- [ ] Metadata panel shows correct HTML size, content-type, user-agent
- [ ] No clipboard data → page renders with `clipboard_error` shown
