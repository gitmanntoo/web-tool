# Mirror Links: Extracted Links Feature — Design

**Date:** 2026-04-10
**Branch:** `fix/mirror-links-page`

## Problem

The `/mirror-links` page's "Links" section heading is present but no links are shown beneath it. The page correctly displays title, favicon, and URL variants for a pasted page, but does not extract or display any hyperlinks from the pasted HTML content.

## What the User Wants

For a page like ibm.com, the user wants to see a list of all extracted hyperlinks from the pasted HTML. Each link should be selectable, and the top "Links" section should show that link in 4 formats (HTML, Markdown, Wiki-link, Simple) with individual copy buttons. On page load (and whenever link selection changes), the HTML format should auto-copy to clipboard.

## Constraints

- Max ~20 links shown (keep page usable)
- Links section always shows 4 variations: HTML, Markdown, Wiki-link, Simple
- Top section updates on selection
- Auto-copy HTML to clipboard on page load and on selection change

---

## Approach

**Option A: Dual-section architecture (recommended)**
- Keep existing top "Links" section showing 4 format panels (HTML/Markdown/Wiki/Simple) for the currently selected link
- Add a new bottom section "Extracted Links" with all extracted links, each with a radio button to select it
- On page load: default to first link, auto-copy HTML
- On radio change: update top section, auto-copy HTML

**Option B: Inline all formats per link row**
- Each extracted link row shows all 4 formats with copy buttons
- No separate top section
- More vertical space, harder to compare formats across links

**Option C: Popup/expand on click**
- Links shown as a compact list
- Clicking expands to show all 4 formats
- More complex interaction, less visible at a glance

### Decision: Option A

The existing top section already has the 4-format panel infrastructure. Reusing it means less code, consistent UX, and easy comparison across link selections.

---

## Architecture

### Backend (`web-tool.py`)

1. **Extract links from HTML** using BeautifulSoup:
   - Find all `<a>` tags with `href`
   - Skip fragment-only links (`#anchor`)
   - Skip empty hrefs
   - Skip off-site links (optional — decision: keep all for now)
   - Limit to 20 links

2. **Pass to template:**
   - `extracted_links`: list of `{"url": str, "text": str, "html": str}`

3. **Existing `links` variable** (used for static favicon/simple links) is unaffected — it's still built and passed, but the template no longer relies on it for the dynamic link list.

### Frontend (`mirror-links.html`)

**New state:**
```javascript
const state = {
    title: defaultValues.title,
    fragmentText: '',
    url: '',              // URL of selected extracted link
    faviconOption: 'url',
    // ...
    selectedLinkIndex: 0  // index into extracted_links
};
```

**New extracted links section (Jinja2 loop):**
```html
<div class="metadata-panel">
    <h2>Extracted Links</h2>
    <div class="url-list">
        {% for link in extracted_links %}
        <div class="url-item">
            <input type="radio" name="extracted_link"
                   value="{{ loop.index0 }}"
                   data-url="{{ link.url|e }}"
                   data-text="{{ link.text|e }}">
            <button class="copy-btn" data-html="{{ link.html|e }}">Copy</button>
            <span style="min-width: 100px;"><strong>{{ link.text|truncate(40, killwords=True) }}</strong></span>
            <span><a href="{{ link.url|e }}">{{ link.url|truncate(60, killwords=True) }}</a></span>
        </div>
        {% endfor %}
    </div>
</div>
```

**Existing top "Links" section stays as-is** — it shows 4 formats for `state.url` (the selected link's URL).

**Radio change handler (add to existing `change` listener):**
```javascript
} else if (input.name === 'extracted_link') {
    const linkIndex = parseInt(input.value);
    const link = extractedLinks[linkIndex];
    state.url = input.dataset.url;
    state.title = input.dataset.text;
}
```

**Auto-copy behavior (modify existing `render()` call after radio change):**
- After `render()` completes, call `navigator.clipboard.writeText(htmlLink)` if `linksInitialized`

---

## Key Implementation Details

### Link Extraction (BeautifulSoup)

```python
def extract_links(html: str, base_url: str, max_links: int = 20) -> list[dict]:
    soup = BeautifulSoup(html, 'lxml')
    links = []
    for a in soup.find_all('a', href=True):
        href = a.get('href', '')
        # Skip fragment-only
        if href.startswith('#'):
            continue
        text = a.get_text(strip=True)
        if not text:
            text = href  # fallback to URL if no text
        links.append({
            'url': urljoin(base_url, href),
            'text': text[:200],  # truncate long text
            'html': f'<a target="_blank" href="{escape_html(urljoin(base_url, href))}">{escape_html(text)}</a>'
        })
        if len(links) >= max_links:
            break
    return links
```

### HTML-escaping

Use a minimal HTML escaper (replace `&`, `<`, `>`, `"`, `'`). Jinja's `|e` filter handles templates; attribute values need quotes handled too. Python's `html.escape()` covers this.

### Auto-copy

On page load, auto-copy HTML link for the first extracted link (default selection). On every selection change, re-copy the HTML link. Track `linksInitialized` to avoid clipboard storms — only copy after user has had a chance to interact.

---

## Spec Self-Review

1. **Placeholder scan:** No TODOs or TBDs.
2. **Internal consistency:** Top section uses `state.url`; extracted links radio sets `state.url` from `data-url`. ✅
3. **Scope check:** Extraction + template + JS state. Single endpoint. ✅
4. **Ambiguity check:** "Extracted Links" section is new distinct name from existing "Links" section. ✅

---

## Files to Modify

1. **`web-tool.py`** — add `extract_links()` function, call in `get_mirror_links()`, pass `extracted_links` to template
2. **`templates/mirror-links.html`** — add extracted links section, update JS state/render/auto-copy logic
3. **`static/mirror.css`** — only if new CSS classes needed (likely none)

## Test Plan

1. Post HTML containing links to `/mirror-links` — verify links appear
2. Click a link's radio — verify top section updates
3. Verify clipboard auto-copy fires on page load and on selection change
4. Page with no links — section hidden or shows empty state
5. Page with >20 links — only first 20 shown
