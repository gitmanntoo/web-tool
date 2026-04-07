"""
Tests for Markdown link escaping in mirror-links.html.

The JavaScript escaping functions map directly to Python string operations,
so we test the logic in Python here.
"""

import re
import pytest


# Python equivalents of the JS functions from mirror-links.html

MARKDOWN_URL_SAFE_WRAP_CHARS = re.compile(r"[()[\] <]")


def escape_markdown_text(text: str) -> str:
    """Escape [ and \ for Markdown link text portion.

    Only [ needs escaping — it starts the link text delimiter.
    ] only needs escaping when it has no matching opening [.
    Backslash must be escaped first to avoid double-escaping.
    """
    return text.replace("\\", "\\\\").replace("[", "\\[")


def build_markdown_link(title: str, fragment_text: str, url: str) -> str:
    """Build a Markdown link, applying escaping rules."""
    link_text = escape_markdown_text(fragment_text + " - " + title if fragment_text else title)
    wrapped_url = f"<{url}>" if MARKDOWN_URL_SAFE_WRAP_CHARS.search(url) else url
    return f"[{link_text}]({wrapped_url})"


class TestEscapeMarkdownText:
    """Tests for escapeMarkdownText function (Python equivalent)."""

    def test_plain_text_unchanged(self):
        """Plain text with no special chars passes through unchanged."""
        assert escape_markdown_text("Hello World") == "Hello World"

    def test_backslash_escaped(self):
        """Backslashes are escaped to \\\\."""
        assert escape_markdown_text("foo\\bar") == "foo\\\\bar"

    def test_multiple_backslashes(self):
        """Multiple consecutive backslashes are each escaped."""
        assert escape_markdown_text("a\\b\\c") == "a\\\\b\\\\c"

    def test_open_bracket_escaped(self):
        """Left brackets are escaped to \\[."""
        assert escape_markdown_text("foo[bar") == "foo\\[bar"

    def test_close_bracket_unchanged_when_matched(self):
        """Matched ] is NOT escaped — only unmatched closing brackets need escaping."""
        assert escape_markdown_text("[foo]") == "\\[foo]"   # ] unchanged (closes the pair)
        assert escape_markdown_text("[foo]bar[baz]") == "\\[foo]bar\\[baz]"

    def test_unmatched_close_bracket_unchanged(self):
        """Unmatched ] is NOT escaped — JS escapeMarkdownText only escapes [ and \\."""
        assert escape_markdown_text("]foo") == "]foo"

    def test_backslash_before_open_bracket_escaped_first(self):
        """Backslash is escaped first so the bracket that follows isn't double-escaped."""
        # Node confirms: JSON.stringify(escapeMarkdownText("\\[")) = "\\[\\"
        # That is 4 chars: \ [ \ \  → Python: '\\\\\\['
        result = escape_markdown_text("\\[")
        assert result == "\\\\\\["

    def test_backslash_escape_prevents_double_escaping(self):
        """Without escaping \ first, subsequent passes would double-escape."""
        assert escape_markdown_text("\\") == "\\\\"

    def test_mixed_brackets_and_backslashes(self):
        """Text with [ and \ is fully escaped."""
        # [bar]: [ escaped → \\[bar] (] not escaped since it's matched)
        assert escape_markdown_text("foo[bar]baz\\qux") == "foo\\[bar]baz\\\\qux"


class TestMarkdownUrlWrapping:
    """Tests for URL angle-bracket wrapping logic.

    URLs containing ( ) [ ] < or space must be wrapped in < > so the Markdown
    parser treats them as literal URI content rather than link delimiters.
    """

    def test_clean_url_unwrapped(self):
        """URL with no special chars stays unwrapped."""
        assert MARKDOWN_URL_SAFE_WRAP_CHARS.search("https://example.com") is None

    def test_url_with_open_paren_wrapped(self):
        """URL containing ( is wrapped in angle brackets."""
        assert MARKDOWN_URL_SAFE_WRAP_CHARS.search("https://example.com/foo(bar)") is not None

    def test_url_with_close_paren_wrapped(self):
        """URL containing ) is wrapped in angle brackets."""
        assert MARKDOWN_URL_SAFE_WRAP_CHARS.search("https://example.com/foo)bar") is not None

    def test_url_with_both_parens_wrapped(self):
        """URL containing balanced () is wrapped."""
        assert MARKDOWN_URL_SAFE_WRAP_CHARS.search("https://example.com/foo(bar)baz") is not None

    def test_url_with_square_brackets_wrapped(self):
        """URL containing [ or ] is wrapped."""
        assert MARKDOWN_URL_SAFE_WRAP_CHARS.search("https://example.com/foo[bar]") is not None
        assert MARKDOWN_URL_SAFE_WRAP_CHARS.search("https://example.com/foo]bar") is not None

    def test_url_with_space_wrapped(self):
        """URL containing space is wrapped."""
        assert MARKDOWN_URL_SAFE_WRAP_CHARS.search("https://example.com/foo bar") is not None

    def test_url_with_angle_bracket_less_than_wrapped(self):
        """URL containing < is wrapped; > is not in the wrapping regex."""
        assert MARKDOWN_URL_SAFE_WRAP_CHARS.search("https://example.com/foo<bar") is not None
        assert MARKDOWN_URL_SAFE_WRAP_CHARS.search("https://example.com/foo>bar") is None

    def test_fragment_with_parens_gets_wrapped(self):
        """URL with fragment containing parens (common with JS method names) is wrapped."""
        url = "https://example.com/page#section(method)"
        assert MARKDOWN_URL_SAFE_WRAP_CHARS.search(url) is not None


class TestBuildMarkdownLink:
    """Tests for buildMarkdownLink function (Python equivalent)."""

    def test_simple_link(self):
        """Simple title and URL produces clean Markdown link."""
        result = build_markdown_link("Example", "", "https://example.com")
        assert result == "[Example](https://example.com)"

    def test_text_with_parens_not_escaped(self):
        """Parens in text are fine — Markdown text portion doesn't interpret them."""
        result = build_markdown_link("Foo (bar)", "", "https://example.com")
        assert result == "[Foo (bar)](https://example.com)"

    def test_text_with_brackets_escaped(self):
        """Open brackets in text are escaped; matched close brackets are not."""
        # Node confirms: JSON.stringify(escapeMarkdownText("Foo [bar]")) = "Foo \\[bar]"
        result = build_markdown_link("Foo [bar]", "", "https://example.com")
        assert result == "[Foo \\[bar]](https://example.com)"

    def test_text_with_backslash_escaped(self):
        """Backslash in text is escaped."""
        result = build_markdown_link("foo\\bar", "", "https://example.com")
        assert result == "[foo\\\\bar](https://example.com)"

    def test_url_with_parens_wrapped(self):
        """URL containing ( ) is wrapped in angle brackets."""
        result = build_markdown_link("Example", "", "https://example.com/page(method)")
        assert result == "[Example](<https://example.com/page(method)>)"

    def test_url_with_fragment_parens_wrapped(self):
        """URL fragment with parens triggers wrapping."""
        result = build_markdown_link(
            "Example", "", "https://pydantic.com/api/pydantic.json_schema#build_schema_type_to_method()"
        )
        assert result == "[Example](<https://pydantic.com/api/pydantic.json_schema#build_schema_type_to_method()>)"

    def test_fragment_prefixes_title(self):
        """Non-empty fragment_text is prepended to title."""
        result = build_markdown_link("Example", "See also", "https://example.com")
        assert result == "[See also - Example](https://example.com)"

    def test_both_text_brackets_and_url_parens(self):
        """Text brackets and URL parens are both handled correctly."""
        result = build_markdown_link("Foo [bar]", "", "https://example.com/page(method)")
        # Text: [ escaped → Foo \[bar]  (] not escaped)
        # URL: wrapped in <>
        assert result == "[Foo \\[bar]](<https://example.com/page(method)>)"

    def test_wiki_link_format_unchanged(self):
        """Wiki-link format [text|url] has no special escaping (for reference)."""
        def build_wiki_link(title, fragment_text, url):
            link_text = fragment_text + " - " + title if fragment_text else title
            return f"[{link_text}|{url}]"

        result = build_wiki_link("Example", "", "https://example.com")
        assert result == "[Example|https://example.com]"

        # Wiki links don't interpret () or [] specially
        result = build_wiki_link("Foo [bar]", "", "https://example.com/page(method)")
        assert result == "[Foo [bar]|https://example.com/page(method)]"


class TestRealWorldExamples:
    """Tests with real-world data patterns from the codebase."""

    def test_pydantic_json_schema_url(self):
        """Real URL pattern from the codebase — fragment with dots and parens."""
        url = "https://pydantic.com.cn/en/api/json_schema/#pydantic.json_schema.GenerateJsonSchema.build_schema_type_to_method"
        title = "JSON Schema - Pydantic documentation (en)"
        result = build_markdown_link(title, "", url)
        # URL has no parens, brackets, spaces, or angle brackets — no wrapping needed
        assert result == "[JSON Schema - Pydantic documentation (en)](https://pydantic.com.cn/en/api/json_schema/#pydantic.json_schema.GenerateJsonSchema.build_schema_type_to_method)"

    def test_url_with_space_in_fragment(self):
        """URL with space in fragment section is wrapped."""
        url = "https://example.com/page#section name"
        result = build_markdown_link("Example", "", url)
        assert result == "[Example](<https://example.com/page#section name>)"

    def test_fragment_prefixes_title_real_pattern(self):
        """Fragment text prepending title — real build_schema_type_to_method pattern."""
        url = "https://pydantic.com/api/pydantic.json_schema#build_schema_type_to_method"
        result = build_markdown_link("GenerateJsonSchema", "build_schema_type_to_method", url)
        assert result == "[build_schema_type_to_method - GenerateJsonSchema](https://pydantic.com/api/pydantic.json_schema#build_schema_type_to_method)"

    def test_fragment_prefixes_title_with_brackets_in_text(self):
        """Fragment prepending title where title itself has brackets."""
        result = build_markdown_link("Foo [bar]", "baz", "https://example.com")
        assert result == "[baz - Foo \\[bar]](https://example.com)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
