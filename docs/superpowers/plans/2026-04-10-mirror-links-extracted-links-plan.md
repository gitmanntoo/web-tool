# Mirror Links — Extracted Links Feature — Implementation Plan

**Branch:** `fix/mirror-links-page`
**Spec:** `specs/mirror-links-spec.md` §7, `docs/superpowers/specs/2026-04-10-mirror-links-extracted-links-design.md`

---

## Overview

Add a new **Extracted Links** section to the `/mirror-links` page that extracts all hyperlinks from the pasted HTML and lets the user select one, updating the top "Links" section (HTML/Markdown/Wiki/Simple formats) with that link's data. Auto-copy HTML to clipboard on page load and on selection change.

---

## Files to Modify

| File | Changes |
|------|---------|
| `web-tool.py` | Add `extract_links()` function; call in `get_mirror_links()`; pass `extracted_links` to template |
| `templates/mirror-links.html` | Add extracted links section; update JS state, render, change-listener, auto-copy |

No CSS changes needed — existing `.metadata-panel`, `.url-list`, `.url-item`, `.copy-btn` classes handle the new section.

---

## Step 1 — Backend: Link Extraction (`web-tool.py`)

**Add import** at top of file (already present):
```python
from urllib.parse import urljoin
import html
```

**Add `extract_links()` function** near the top of the file, after imports:

```python
def extract_links(html_text: str, base_url: str, max_links: int = 20) -> list[dict]:
    """Extract all <a> tags with href from html_text, resolve against base_url.

    Skips fragment-only links (#anchor) and empty hrefs after resolution.
    Limits to max_links. Each returned dict has url, text, html.
    """
    soup = BeautifulSoup(html_text, 'lxml')
    links = []
    for a in soup.find_all('a', href=True):
        href = a.get('href', '')
        if href.startswith('#'):
            continue
        resolved_url = urljoin(base_url, href)
        if not resolved_url:
            continue
        text = a.get_text(strip=True)
        if not text:
            text = resolved_url
        truncated_text = text[:200]
        links.append({
            'url': resolved_url,
            'text': html.escape(truncated_text),
            'html': (
                f'<a target="_blank" href="{html.escape(resolved_url)}">'
                f'{html.escape(truncated_text)}</a>'
            ),
        })
        if len(links) >= max_links:
            break
    return links
```

**Call in `get_mirror_links()`** — after building `url_variants` and before building `links`:

```python
# Extract links from the pasted HTML
extracted_links = []
if metadata.html:
    extracted_links = extract_links(metadata.html, metadata.url, max_links=20)
```

**Pass to template** — add `extracted_links` to `template.render()` dict:

```python
rendered_html = template.render({
    ...
    'extracted_links': extracted_links,
})
```

**Verify `links` variable still passed** (legacy, template doesn't use it but doesn't break):

```python
'links': links,
```

---

## Step 2 — Frontend: State + Extracted Links Array (`mirror-links.html`)

**Add `extractedLinks` constant** — after `defaultValues` and before the `state` block:

```javascript
// All extracted links from the pasted HTML, populated by Jinja2.
const extractedLinks = {{ extracted_links|tojson }};
```

**Update `state`** — add `selectedLinkIndex` (note: `url` and `title` are NOT pre-populated from extractedLinks; they default to `defaultValues` which reflects the page-level URL/title):

```javascript
const state = {
    title: defaultValues.title,
    fragmentText: '',
    url: defaultValues.url,
    faviconOption: 'url',
    faviconWidth: defaultValues.faviconWidth,
    faviconHeight: defaultValues.faviconHeight,
    selectedLinkIndex: 0   // index into extractedLinks[]; 0 = first link
};
```

---

## Step 3 — Frontend: Extracted Links Section (`mirror-links.html`)

**Insert after the closing `</div>` of the Favicon section and before the Metadata section.** Use the same `.metadata-panel` / `.url-list` / `.url-item` pattern as other sections:

```html
{% if extracted_links %}
<div class="metadata-panel">
    <h2>Extracted Links</h2>
    <div class="url-list">
        {% for link in extracted_links %}
        <div class="url-item">
            <input type="radio" name="extracted_link"
                   value="{{ loop.index0 }}"
                   data-url="{{ link.url|e }}"
                   data-text="{{ link.text|e }}"
                   {% if loop.first %}checked{% endif %}>
            <button class="copy-btn" data-html="{{ link.html|e }}">Copy</button>
            <span style="min-width: 100px;"><strong>{{ link.text|truncate(40, killwords=True) }}</strong></span>
            <span><a href="{{ link.url|e }}">{{ link.url|truncate(60, killwords=True) }}</a></span>
        </div>
        {% endfor %}
    </div>
</div>
{% endif %}
```

The `{% if extracted_links %}` guard hides the section entirely when no links are found (per spec §7: "empty state: section hidden if `extracted_links` is empty").

The first radio is checked by default (`{% if loop.first %}checked{% endif %}`), which selects the first link on page load.

---

## Step 4 — Frontend: Change Listener Update (`mirror-links.html`)

**Find the existing `change` event listener** (inside `DOMContentLoaded`):

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

**Add the `extracted_link` branch:**

```javascript
} else if (input.name === 'extracted_link') {
    state.url = input.dataset.url;
    state.title = input.dataset.text;
}
```

No need to track `selectedLinkIndex` explicitly — `state.url` and `state.title` are what the format builders use.

---

## Step 5 — Frontend: Render Function (`mirror-links.html`)

The existing `render()` function already drives all 4 format displays from `state.url`, `state.title`, and `state.fragmentText`. **No changes needed to `render()` itself** — when `state.url` and `state.title` are updated via the `extracted_link` radio change, the next `render()` call naturally rebuilds all 4 formats for the newly selected link.

The auto-copy logic in `render()` also needs no changes:

```javascript
// Auto-copy HTML to clipboard on selection changes
if (linksInitialized) {
    navigator.clipboard.writeText(htmlLink).then(() => {
        console.log('HTML link copied to clipboard');
    });
}
```

This already fires on every `render()` call after `linksInitialized` is set.

---

## Step 6 — Initial Auto-Copy on Page Load (`mirror-links.html`)

**Existing code** (inside `DOMContentLoaded`, after the `setTimeout` block):

```javascript
// Initial auto-copy HTML
setTimeout(() => {
    const initialLink = document.getElementById('copy-html').dataset.html;
    if (initialLink) {
        navigator.clipboard.writeText(initialLink).then(() => {
            console.log('Initial HTML link copied to clipboard');
            linksInitialized = true;
        });
    }
}, 100);
```

**No changes needed.** On page load, the first radio (first extracted link, or URL variant radio if no extracted links) is already checked. The `render()` call at page load uses `state.url = defaultValues.url = url_variants[0].url` (the page-level URL), not an extracted link URL — unless extracted links exist and the first one is checked.

**To ensure auto-copy uses the first extracted link** when `extractedLinks` is non-empty: after the `DOMContentLoaded` change-listener sets initial state, check if `extractedLinks.length > 0` and auto-select the first extracted link's URL/title before the initial `render()`.

Add at the end of `DOMContentLoaded` (after change listener setup, before `attachPasteListeners`):

```javascript
// If extracted links exist, default to first extracted link
if (extractedLinks.length > 0) {
    const first = extractedLinks[0];
    state.url = first.url;
    state.title = first.text;
    render();
}
```

This replaces the initial `render()` output with the first extracted link's formats, so the initial auto-copy fires for that link.

---

## Step 7 — Verify Import for `urljoin` and `html`

Check that `web-tool.py` already imports `urljoin`. It uses `from urllib.parse import urlparse` but not `urljoin`. **Add to existing import line:**

```python
from urllib.parse import urlparse, urljoin
```

---

## Verification

After implementing each step, run:

```bash
make testv
```

Specifically, add a test in `tests/test_integration_pages.py` or a new `tests/test_extracted_links.py`:

```python
def test_extracted_links_basic():
    """Verify extracted links section appears and populates from HTML."""
    # POST HTML with 3 links to /mirror-links
    resp = client.post('/mirror-links', data={
        'url': 'https://example.com',
        'title': 'Example',
        'html': '<html><body><a href="/page1">Page 1</a><a href="/page2">Page 2</a><a href="https://other.com">External</a></body></html>',
        'text': 'body text'
    })
    html = resp.get_data(as_text=True)
    assert 'Extracted Links' in html
    assert 'Page 1' in html
    assert 'Page 2' in html
    assert 'https://example.com/page1' in html
    assert 'https://example.com/page2' in html
    # External link preserved
    assert 'https://other.com' in html
    # Max 20 enforced (3 links << 20, no truncation)

def test_extracted_links_skips_fragment_only():
    """Fragment-only anchors are not extracted."""
    resp = client.post('/mirror-links', data={
        'url': 'https://example.com',
        'title': 'Example',
        'html': '<html><body><a href="#section">Skip</a><a href="/page">Real</a></body></html>',
        'text': 'body'
    })
    html = resp.get_data(as_text=True)
    assert '#section' not in html or 'Skip' not in html
    assert '/page' in html

def test_extracted_links_empty():
    """No <a> tags → section hidden."""
    resp = client.post('/mirror-links', data={
        'url': 'https://example.com',
        'title': 'Example',
        'html': '<html><body><p>No links here</p></body></html>',
        'text': 'body'
    })
    html = resp.get_data(as_text=True)
    assert 'Extracted Links' not in html
```

Run with: `uv run pytest tests/test_extracted_links.py -v`

---

## File Summary

| File | Action |
|------|--------|
| `web-tool.py` | Add `urljoin` import; add `extract_links()`; call and pass `extracted_links` |
| `templates/mirror-links.html` | Add `extractedLinks` JS array; update `state`; add section HTML; add change-listener branch |
| `tests/test_extracted_links.py` | New file — 3 test cases above |
| `specs/mirror-links-spec.md` | Already complete; no changes needed |
| `docs/superpowers/specs/2026-04-10-mirror-links-extracted-links-design.md` | Already complete; no changes needed |
