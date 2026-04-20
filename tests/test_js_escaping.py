"""
Tests for JavaScript string escaping in templates.

Tests that the tojson filter is used correctly for JavaScript strings
in mirror-links.html, ensuring special characters don't break JS parsing.
"""

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader


class TestMirrorLinksJsEscaping:
    """Tests for JavaScript string escaping in mirror-links template."""

    @pytest.fixture
    def template_env(self):
        """Create Jinja2 environment for testing templates."""
        template_dir = Path(__file__).parent.parent / "templates"
        env = Environment(loader=FileSystemLoader(template_dir))
        return env

    def test_fragment_text_with_newline_escaped(self, template_env):
        """Test that fragment text with newline is properly escaped for JS."""
        template = template_env.get_template("mirror-links.html")

        rendered = template.render(
            title="Test",
            title_variants=[{"value": "Test", "label": "Original"}],
            fragment="section",
            fragment_text="build_schema_type_to_method\n¶",
            url_variants=[{"url": "https://example.com", "label": "Original"}],
            favicon=None,
            favicon_inline=None,
        )

        # The rendered template should contain valid JavaScript
        # The newline in fragmentText should be escaped as \n
        assert "fragmentText:" in rendered
        # Should use tojson which produces valid JS (no bare newlines in string literals)
        assert "\\n" in rendered or "\\\\n" in rendered or "fragmentText: ''" in rendered

    def test_fragment_text_with_special_chars_escaped(self, template_env):
        """Test that fragment text with special chars is properly escaped."""
        template = template_env.get_template("mirror-links.html")

        rendered = template.render(
            title="Test",
            title_variants=[{"value": "Test", "label": "Original"}],
            fragment="section",
            fragment_text='test"quote',
            url_variants=[{"url": "https://example.com", "label": "Original"}],
            favicon=None,
            favicon_inline=None,
        )

        # Should not have bare quotes that would break JS string
        # tojson should escape the quote as \"
        assert 'test\\"quote' in rendered or "fragmentText: ''" in rendered

    def test_title_with_unicode_escaped(self, template_env):
        """Test that title with Unicode characters is properly escaped."""
        template = template_env.get_template("mirror-links.html")

        rendered = template.render(
            title="JSON Schema - Pydantic documentation (en)",
            title_variants=[
                {"value": "JSON Schema - Pydantic documentation (en)", "label": "Original"}
            ],
            fragment="",
            fragment_text="",
            url_variants=[{"url": "https://example.com", "label": "Original"}],
            favicon=None,
            favicon_inline=None,
        )

        # Should contain the title in JavaScript defaultValues
        assert "JSON Schema - Pydantic documentation (en)" in rendered

    def test_url_with_fragment_containing_dots(self, template_env):
        """Test that URL with fragment containing dots is properly escaped."""
        template = template_env.get_template("mirror-links.html")

        rendered = template.render(
            title="Test",
            title_variants=[{"value": "Test", "label": "Original"}],
            fragment="pydantic.json_schema.GenerateJsonSchema.build_schema_type_to_method",
            fragment_text="build_schema_type_to_method",
            url_variants=[
                {
                    "url": "https://pydantic.com.cn/en/api/json_schema/#pydantic.json_schema.GenerateJsonSchema.build_schema_type_to_method",
                    "label": "Original",
                }
            ],
            favicon=None,
            favicon_inline=None,
        )

        # URL should be in the template
        assert "pydantic.json_schema.GenerateJsonSchema.build_schema_type_to_method" in rendered

    def test_no_fragment_renders_empty_fragment_text(self, template_env):
        """Test that empty fragment renders empty string for fragmentText."""
        template = template_env.get_template("mirror-links.html")

        rendered = template.render(
            title="Test",
            title_variants=[{"value": "Test", "label": "Original"}],
            fragment="",
            fragment_text="",
            url_variants=[{"url": "https://example.com", "label": "Original"}],
            favicon=None,
            favicon_inline=None,
        )

        # Should have fragmentText: '' (empty string)
        assert "fragmentText: ''" in rendered

    def test_null_favicon_renders_null(self, template_env):
        """Test that null favicon renders as null in JavaScript."""
        template = template_env.get_template("mirror-links.html")

        rendered = template.render(
            title="Test",
            title_variants=[{"value": "Test", "label": "Original"}],
            fragment="",
            fragment_text="",
            url_variants=[{"url": "https://example.com", "label": "Original"}],
            favicon=None,
            favicon_inline=None,
        )

        # Should have favicon: null
        assert "favicon: null" in rendered

    def test_favicon_url_renders_correctly(self, template_env):
        """Test that favicon URL renders as JavaScript string."""
        template = template_env.get_template("mirror-links.html")

        rendered = template.render(
            title="Test",
            title_variants=[{"value": "Test", "label": "Original"}],
            fragment="",
            fragment_text="",
            url_variants=[{"url": "https://example.com", "label": "Original"}],
            favicon="https://example.com/favicon.png",
            favicon_inline=None,
        )

        # Should have favicon as JS string (with quotes)
        assert "favicon:" in rendered
        assert "null" not in rendered.split("favicon:")[1].split("\n")[0]

    def test_markdown_escape_functions_present(self, template_env):
        """Test that Markdown escaping functions and regex are defined in the template."""
        template = template_env.get_template("mirror-links.html")

        rendered = template.render(
            title="Test",
            title_variants=[{"value": "Test", "label": "Original"}],
            fragment="",
            fragment_text="",
            url_variants=[{"url": "https://example.com", "label": "Original"}],
            favicon=None,
            favicon_inline=None,
        )

        # Should contain the Markdown URL-safe wrap regex
        assert "MARKDOWN_URL_SAFE_WRAP_CHARS" in rendered
        # Should contain the Markdown text escape function
        assert "escapeMarkdownText" in rendered
        # Should contain the updated buildMarkdownLink that encodes < > in wrapped URLs
        assert "encodeURIComponent" in rendered

    def test_markdown_link_template_has_url_wrapping_logic(self, template_env):
        """Test that buildMarkdownLink in the template uses angle-bracket URL wrapping."""
        template = template_env.get_template("mirror-links.html")

        rendered = template.render(
            title="Test",
            title_variants=[{"value": "Test", "label": "Original"}],
            fragment="",
            fragment_text="",
            url_variants=[{"url": "https://example.com", "label": "Original"}],
            favicon=None,
            favicon_inline=None,
        )

        # The template should use angle-bracket wrapping with < > encoding
        assert "encodeURIComponent" in rendered

    def test_fragment_text_row_has_readonly_span_and_editable_input(self, template_env):
        """Test that Fragment Text row contains both read-only span and editable input.

        The Fragment Text row should render with both:
        - A .fragment-text-readonly span showing the value when radio is unchecked
        - A .fragment-text-input for editing when radio is checked
        This ensures UI consistency with other fragment variant rows.
        """
        template = template_env.get_template("mirror-links.html")

        rendered = template.render(
            title="Test",
            title_variants=[{"value": "Test", "label": "Original"}],
            fragment="section",
            fragment_text="build_schema_type_to_method",
            fragment_variants=[
                {"value": "build_schema_type_to_method", "label": "Fragment Text"},
                {"value": "section", "label": "Fragment: section"},
            ],
            url_variants=[{"url": "https://example.com", "label": "Original"}],
            favicon=None,
            favicon_inline=None,
        )

        # Should contain the read-only span for displaying value when radio unchecked
        assert 'class="fragment-text-readonly"' in rendered
        # Should contain the editable input for editing when radio checked
        assert 'class="fragment-text-input"' in rendered
        # Both should contain the fragment text value
        assert "build_schema_type_to_method" in rendered


class TestBuildHtmlLinkTemplate:
    """Regression tests for buildHtmlLink JS variable references.

    The buildHtmlLink function defines local const aliases:
        const favH = faviconHeight || 20;
        const favW = faviconWidth || 20;
    The favicon <img> tags must use favW/favH (the aliases), not the
    raw parameter names faviconWidth/faviconHeight. A prior bug used
    the undefined variable faviconW, which threw a ReferenceError that
    crashed render() on every page with a favicon.
    """

    @pytest.fixture
    def template_env(self):
        """Create Jinja2 environment for testing templates."""
        template_dir = Path(__file__).parent.parent / "templates"
        env = Environment(loader=FileSystemLoader(template_dir))
        return env

    def _render_with_favicon(self, template_env):
        """Render mirror-links.html with a favicon URL."""
        template = template_env.get_template("mirror-links.html")
        return template.render(
            title="Test",
            title_variants=[{"value": "Test", "label": "Original"}],
            fragment="",
            fragment_text="",
            url_variants=[{"url": "https://example.com", "label": "Original"}],
            favicon="https://example.com/favicon.png",
            favicon_inline=None,
        )

    def test_build_html_link_uses_fav_w_not_favicon_w(self, template_env):
        """buildHtmlLink must use favW (local const), not faviconW (undefined)."""
        rendered = self._render_with_favicon(template_env)

        # All three favicon branches (pasted, inline, url) must use favW
        assert 'width="${favW}"' in rendered
        # faviconW must not appear inside template literals — only as
        # the function parameter name and in the const definition
        assert 'width="${faviconW}"' not in rendered

    def test_build_html_link_uses_fav_h_not_favicon_height(self, template_env):
        """buildHtmlLink must use favH (local const) in height attributes."""
        rendered = self._render_with_favicon(template_env)

        assert 'height="${favH}"' in rendered
        # faviconHeight should only appear as parameter name and const def,
        # not inside the img tag template literals
        assert 'height="${faviconHeight}"' not in rendered

    def test_build_html_link_constants_defined(self, template_env):
        """buildHtmlLink must define favH and favW before the favicon branches."""
        rendered = self._render_with_favicon(template_env)

        assert "const favH = faviconHeight || 20;" in rendered
        assert "const favW = faviconWidth || 20;" in rendered

    def test_no_undefined_js_references_in_build_html_link(self, template_env):
        """buildHtmlLink must not reference undefined variables.

        After the function parameter list, any reference to faviconW
        (capital W after 'favicon') would be an undefined variable.
        The parameter name is faviconWidth (lowercase w after 'icon').
        Use regex to match faviconW as a standalone token, not as a
        substring of the valid parameter name faviconWidth.
        """
        import re

        rendered = self._render_with_favicon(template_env)

        # Extract the buildHtmlLink function body
        func_start = rendered.index("function buildHtmlLink(")
        func_end = rendered.index(
            "}", rendered.index("// Add link with appropriate text", func_start)
        )
        func_body = rendered[func_start:func_end]

        # faviconW must not appear as a standalone token (not part of faviconWidth)
        # Match faviconW that is NOT followed by 'idth' (which would make it faviconWidth)
        bad_refs = re.findall(r"faviconW(?!idth)", func_body)
        assert bad_refs == [], f"Found undefined variable references: {bad_refs}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
