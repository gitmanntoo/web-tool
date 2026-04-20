# Mirror Links — Fragment Text Editing

## Context

When a URL contains a fragment (e.g., `#overview`), the mirror links page currently offers three fragment display options via radio buttons:
- **None** — omit the fragment entirely
- **Fragment** — display the raw fragment identifier (e.g., `#overview`)
- **Fragment Text** — display text derived from the page heading or anchor at that fragment

Users cannot currently edit the "Fragment Text" value. This change makes it an editable text field, pre-populated with the derived fragment text from the page, so users can correct or customize it.

---

## UI Changes

### Fragment Panel (templates/mirror-links.html)

The "Fragment Text" radio option's static label becomes an editable `<input>`:

```html
{% if fragment_variants %}
<div class="panel fragment-panel">
  <div class="panel-label">Fragment</div>
  <div class="radio-list" id="fragment-options">
    {% for variant in fragment_variants %}
    {% if variant.label == 'Fragment Text' %}
    <div class="fragment-text-option">
      <input type="radio" name="fragment_variant" value="fragment{{ loop.index0 }}"
        data-text="{{ variant.value|e }}" data-has-text-input="true" id="fragment-radio-{{ loop.index0 }}"
        {% if loop.first %}checked{% endif %}>
      <label for="fragment-radio-{{ loop.index0 }}" class="fragment-text-label">
        <input type="text" class="fragment-text-input"
               value="{{ variant.value|e }}"
               placeholder="{{ variant.value|e }}">
      </label>
    </div>
    {% else %}
    <label class="fragment-label">
      <input type="radio" name="fragment_variant" value="fragment{{ loop.index0 }}"
        data-text="{{ variant.value|e }}" {% if loop.first %}checked{% endif %}>
      <span class="fragment-static">{{ variant.label }}</span>
    </label>
    {% endif %}
    {% endfor %}
  </div>
</div>
{% endif %}
```

**Key changes:**
- Radio group wrapped in `#fragment-options` for delegated event handling
- "Fragment Text" option: radio and label are siblings inside a wrapper div; the text input is inside the label
- Radio uses `id` and label uses `for` to link them without nesting — clicking the input checks the radio without toggle confusion
- Static labels wrapped in `<span class="fragment-static">` for consistent styling
- Default on page load: "None" radio is always selected

---

## JavaScript Event Handling

### Radio change handler (delegated)

```javascript
document.addEventListener('change', (e) => {
  if (e.target.name === 'fragment_variant') {
    const selected = e.target;
    const text = selected.dataset.text; // '' for 'None', '#section' for 'Fragment', 'Text' for 'Fragment Text'
    state.fragmentText = text;

    // Show/hide fragment text input based on selection
    const fragmentOptions = document.getElementById('fragment-options');
    const textInput = fragmentOptions.querySelector('.fragment-text-input');
    if (textInput) {
      textInput.style.display = selected.dataset.hasTextInput ? 'inline-block' : 'none';
    }

    updateLinks();
  }
});
```

### Input event for live editing

```javascript
document.addEventListener('input', (e) => {
  if (e.target.classList.contains('fragment-text-input')) {
    // Use input value as fragment text when user types
    state.fragmentText = e.target.value;
    updateLinks();
  }
});
```

**Key behavior:**
- When user types in the fragment text input, `state.fragmentText` is updated from the input value (not the radio's `data-text`)
- Links update live as the user types (no separate save step)
- When "Fragment Text" radio is first selected, the input pre-populates with derived fragment text from the backend

---

## Backend Data Flow

**routes/mirror_links.py** — no changes needed.

Fragment variants are computed server-side:

```python
fragment_variants_data = [
    ("", "None"),
]
if metadata.parsed_url.fragment:
    fragment_variants_data.append((metadata.parsed_url.fragment, "Fragment"))
if metadata.fragment_text:
    fragment_variants_data.append((metadata.fragment_text, "Fragment Text"))

fragment_variants = util.deduplicate_variants(fragment_variants_data)
```

The derived `fragment_text` is already passed to the template. The "Fragment Text" option's `variant.value` is used as both the input's initial `value` and `placeholder`.

---

## Styling

**static/mirror.css** — new styles for inline input:

```css
.fragment-text-option {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.fragment-text-label {
  display: flex;
  align-items: center;
}

.fragment-text-input {
  border: 1px solid var(--color-border);
  border-radius: 3px;
  padding: 0.125rem 0.25rem;
  font-size: 0.875rem;
  width: 12rem;
  background: var(--color-surface);
  color: var(--color-text);
}

.fragment-text-input:focus {
  outline: 2px solid var(--color-focus);
  outline-offset: 1px;
}
```

The input is shown only when the "Fragment Text" radio is selected.

---

## Behavior Summary

| Action | Result |
|--------|--------|
| Page loads | "None" selected by default |
| User selects "Fragment" | Radio `data-text` used as `state.fragmentText` (e.g., `#overview`) |
| User selects "Fragment Text" | Radio gets checked, input pre-populated with derived text, becomes visible |
| User types in input | `state.fragmentText` updates live from input value; radio stays checked (click stops bubbling) |
| User clears input | Empty fragment text used; input remains visible |
| Links at top | Update in real-time on any change |
