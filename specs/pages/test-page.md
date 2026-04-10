# Test Page — Specification

**Route:** `/test-page` (GET/POST)
**Template:** `templates/test-page.html`
**Backend:** `web-tool.py::test_page()`

---

## Overview

The Test Page serves a parameterized HTML page for manual and automated testing of edge-case URL, fragment, and title handling. It renders static HTML with conditional sections controlled by query parameters. All state is server-side; no JavaScript runs in this template.

---

## Data Flow

```
User requests /test-page?title=...&fragment=...&...
         │
         ▼
web-tool.py::test_page()
    │
    ├── request.args / request.form — read all params
    │       ├── title (default "Test Page")
    │       ├── fragment
    │       ├── anchor-fragment
    │       ├── wrap-fragment
    │       ├── url-has-parens
    │       ├── url-has-brackets
    │       ├── url-has-space
    │       ├── unicode-content
    │       └── emoji-content
    │
    └── template_env.get_template('test-page.html').render(params)
            │
            ▼
         test-page.html (Jinja2)
```

---

## URL Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `title` | `"Test Page"` | Page title and H1 text |
| `fragment` | `""` | URL fragment identifier for H1 id |
| `anchor-fragment` | `""` | Fragment for anchor-inside-heading test |
| `wrap-fragment` | `""` | Fragment for wrapper-with-id test |
| `url-has-parens` | `""` | If `"yes"`, include links with `()` in href |
| `url-has-brackets` | `""` | If `"yes"`, include links with `[]` in href |
| `url-has-space` | `""` | If `"yes"`, include links with spaces in href |
| `unicode-content` | `""` | If `"yes"`, include Unicode body content |
| `emoji-content` | `""` | If `"yes"`, include emoji body content |

---

## Template Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `title` | `params['title']` | Page title |
| `fragment` | `params['fragment']` | Fragment id on H1 (falls back to `'main'`) |
| `anchor_fragment` | `params['anchor_fragment']` | Fragment for anchor-inside-heading |
| `wrap_fragment` | `params['wrap_fragment']` | Fragment for wrapper-with-id |
| `url_has_parens` | `params['url_has_parens']` | Controls parens link section |
| `url_has_brackets` | `params['url_has_brackets']` | Controls brackets link section |
| `url_has_space` | `params['url_has_space']` | Controls spaces link section |
| `unicode_content` | `params['unicode_content']` | Controls unicode content section |
| `emoji_content` | `params['emoji_content']` | Controls emoji content section |

---

## Page Sections

### 1. Primary Heading (H1)

**Purpose:** Primary page heading with configurable id.

**Content:** `<h1 id="{{ fragment or 'main' }}">{{ title }}</h1>`

**Behavior:**
- `id` attribute is `fragment` if provided, else `"main"`
- Heading text is the `title` parameter

---

### 2. Anchor Fragment (conditional)

**Purpose:** Test anchor-inside-heading fragment handler.

**Shown:** Only when `anchor_fragment` is truthy.

**Content:**
```html
<h2 id="{{ anchor_fragment }}">
    {{ anchor_fragment }} with anchor <a href="#{{ anchor_fragment }}">¶</a>
</h2>
```

---

### 3. Wrapper Fragment (conditional)

**Purpose:** Test wrapper-with-id fragment handler.

**Shown:** Only when `wrap_fragment` is truthy.

**Content:**
```html
<section id="{{ wrap_fragment }}">
    <h2>Wrapped Heading</h2>
    <p>This section's id is "{{ wrap_fragment }}" and contains a heading.</p>
</section>
```

---

### 4. Anchor with Text

**Purpose:** Test anchor-with-text fragment handler.

**Content:**
```html
<h2 id="anchor-with-text-heading">
    <a href="#anchor-with-text">Display Text for Anchor</a>
</h2>
```

---

### 5. Links with Edge-Case URLs

**Purpose:** Test URL handling for special characters in hrefs.

**Content:** A `<div id="links">` containing:

| Section | Shown when | Content |
|---------|------------|---------|
| Parens links | `url_has_parens == 'yes'` | Two links with `()` in path/fragment |
| Brackets links | `url_has_brackets == 'yes'` | One link with `[]` in path |
| Space links | `url_has_space == 'yes'` | One link with spaces in path |
| Normal link | Always | Baseline link with no special chars |

---

### 6. Content Section

**Purpose:** Body content for fragment text resolution.

**Content:**
```html
<div id="content">
    <h2>Content Section</h2>
    <p>This is paragraph content under the main heading.</p>
</div>
```

---

### 7. Unicode Content (conditional)

**Purpose:** Test Unicode text rendering.

**Shown:** Only when `unicode_content == 'yes'`.

**Content:** Four paragraphs with Russian, Chinese, Arabic (RTL), and Japanese text.

---

### 8. Emoji Content (conditional)

**Purpose:** Test emoji character rendering.

**Shown:** Only when `emoji_content == 'yes'`.

**Content:** Two paragraphs with emoji and flag characters.

---

### 9. Sibling Heading After Anchor

**Purpose:** Test anchor-siblings fragment handler.

**Content:**
```html
<h3 id="sibling-heading">Sibling Heading</h3>
<a href="#sibling-heading" id="anchor-sibling">¶</a>
<p>Content after the anchor.</p>
```

---

## Element IDs

| ID | Element |
|----|---------|
| `main` | H1 when no fragment provided |
| `anchor-with-text-heading` | H2 for anchor-with-text test |
| `links` | Container div for edge-case links |
| `content` | Container div for body content |
| `sibling-heading` | H3 for anchor-siblings test |
| `anchor-sibling` | Anchor after sibling-heading |

---

## CSS Classes

| Class | Referenced from |
|-------|----------------|
| `.metadata-panel` | mirror.css |
| `.url-list` | mirror.css |
| `.url-item` | mirror.css |

---

## Backend Details

**Template loading:** Uses `template_env.get_template()` (not `render_template()`).

```python
template = template_env.get_template('test-page.html')
rendered_html = template.render(params)
resp = make_response(rendered_html)
return resp
```

**Dependency:** Jinja2 via `template_env` (application-wide Jinja environment).

---

## Edge Cases

| Case | Behavior |
|------|----------|
| No params | Renders with defaults: title="Test Page", id="main" |
| fragment empty | H1 id defaults to `"main"` |
| All boolean flags empty | Only H1, anchor-with-text-heading, content, sibling-heading sections render |
| url_has_space only | Only normal link + space link shown |

---

## Testing Checklist

- [ ] GET /test-page → renders with defaults
- [ ] ?title=Foo → H1 text is "Foo"
- [ ] ?fragment=baz → H1 id is "baz"
- [ ] ?anchor-fragment=anch → H2 with id="anch" and anchor link renders
- [ ] ?wrap-fragment=wrap → section with id="wrap" renders
- [ ] ?url-has-parens=yes → parens links render
- [ ] ?url-has-brackets=yes → brackets link renders
- [ ] ?url-has-space=yes → space link renders
- [ ] ?unicode-content=yes → Unicode paragraphs render
- [ ] ?emoji-content=yes → Emoji paragraphs render
- [ ] All params combined → all sections render correctly
