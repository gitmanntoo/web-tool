# Implementation Plan: Fragment Text Editing

## Context
Mirror Links page needs an editable text field for fragment text. When URL has a fragment, user can select "Fragment Text" and edit the derived text inline.

## Tasks

### Task 1: Update fragment panel HTML
**Files:** `templates/mirror-links.html` (lines 64-80)

Modify the fragment panel to use a radio + label with embedded text input for the "Fragment Text" option:

```html
{% if fragment_variants %}
<div class="panel">
    <div class="panel-label">Fragment</div>
    <div class="variant-list" id="fragment-options">
        {% for variant in fragment_variants %}
            {% if variant.label == 'Fragment Text' %}
            <div class="variant-row">
                <input type="radio" name="fragment_variant" value="fragment{{ loop.index0 }}"
                  data-text="{{ variant.value|e }}" data-has-text-input="true"
                  id="fragment-radio-{{ loop.index0 }}"
                  {% if loop.first %}checked{% endif %}>
                <label for="fragment-radio-{{ loop.index0 }}" class="fragment-text-label">
                    <input type="text" class="fragment-text-input"
                           value="{{ variant.value|e }}"
                           placeholder="{{ variant.value|e }}">
                </label>
            </div>
            {% else %}
            <div class="variant-row">
                <input type="radio" name="fragment_variant" value="fragment{{ loop.index0 }}"
                  data-text="{{ variant.value|e }}"
                  {% if loop.first %}checked{% endif %}>
                <span class="variant-label"><strong>{{ variant.label }}</strong></span>
                {% if variant.value %}<span>{{ variant.value|e }}</span>{% endif %}
            </div>
            {% endif %}
        {% endfor %}
    </div>
</div>
{% endif %}
```

Key changes:
- Wrapped fragment options in `id="fragment-options"` for delegated events
- "Fragment Text" uses radio + label structure with embedded text input
- Radio uses `id` and label uses `for` to link them
- Other options (None, Fragment) use original static style
- `data-has-text-input="true"` on Fragment Text radio to mark it

**Verify:** `git diff templates/mirror-links.html` shows only fragment panel changes.

---

### Task 2: Add CSS styles
**Files:** `static/mirror.css`

Add new styles after existing `.text-input` styles:

```css
/* ============================================
   Fragment Text Input
   ============================================ */

.fragment-text-label {
    display: inline-flex;
    align-items: center;
}

.fragment-text-input {
    border: 1px solid var(--color-border);
    border-radius: 3px;
    padding: 0.125rem 0.25rem;
    font-size: var(--font-size-sm);
    width: 10rem;
    background: var(--color-surface);
    color: var(--color-text);
}

.fragment-text-input:focus {
    border-color: var(--color-primary);
    outline: none;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.15);
}

.fragment-text-input[disabled] {
    background: var(--color-border-subtle);
    color: var(--color-text-muted);
}
```

**Verify:** CSS applies correctly when Fragment Text radio is selected.

---

### Task 3: JavaScript event handlers
**Files:** `templates/mirror-links.html` (lines ~357-378)

Modify the existing radio change listener to handle Fragment Text selection:

1. In the existing `querySelectorAll` listener for static radios (line 357), update the fragment_variant handling to detect `data-has-text-input`:

```javascript
} else if (input.name === 'fragment_variant') {
    if (input.dataset.hasTextInput) {
        // Fragment Text selected — use the input's value
        const textInput = document.querySelector('.fragment-text-input');
        state.fragmentText = textInput ? textInput.value : input.dataset.text;
    } else {
        state.fragmentText = input.dataset.text;
    }
}
```

2. Add delegated input listener for live editing (add after the existing listeners block):

```javascript
// Fragment text input — live update on typing
document.getElementById('fragment-options').addEventListener('input', (e) => {
    if (e.target.classList.contains('fragment-text-input')) {
        state.fragmentText = e.target.value;
        render();
    }
});
```

3. The input should be hidden by default (CSS) and shown only when Fragment Text is selected. Add this to the radio change handler:

```javascript
} else if (input.name === 'fragment_variant') {
    const textInput = document.querySelector('.fragment-text-input');
    if (textInput) {
        textInput.style.display = input.dataset.hasTextInput ? 'inline-block' : 'none';
    }
    if (input.dataset.hasTextInput) {
        state.fragmentText = textInput ? textInput.value : input.dataset.text;
    } else {
        state.fragmentText = input.dataset.text;
    }
}
```

**Verify:** Typing in fragment text input updates links in real-time.

---

### Task 4: Test
**Command:** `make testv`

Run existing test suite to verify no regressions. Key test files:
- `tests/test_markdown_escaping.py` — link building logic
- `tests/test_url_util.py` — URL fragment handling

**Verify:** All 273 tests pass.
