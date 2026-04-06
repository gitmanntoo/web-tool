"""
Tests for library/html_util.py

Tests HTML parsing, favicon discovery, and metadata extraction.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from library.html_util import (
    COMMON_FAVICON_FILES,
    FAVICON_REL,
    FAVICON_HEIGHT,
    ICO_TO_PNG_PATH,
    SVG_TO_PNG_PATH,
    RelLink,
)


class TestRelLink:
    """Tests for RelLink dataclass."""

    def test_initialization(self):
        """Test basic initialization of RelLink."""
        link = RelLink(href="http://example.com/favicon.ico")
        assert link.href == "http://example.com/favicon.ico"
        assert link.rel is None
        assert link.width == 0
        assert link.height == 0

    def test_initialization_with_all_fields(self):
        """Test initialization with all fields."""
        link = RelLink(
            href="http://example.com/favicon.ico",
            rel="icon",
            sizes="16x16",
            cache_key="example.com",
            height=16,
            width=16,
            image_type="image/x-icon",
        )
        assert link.href == "http://example.com/favicon.ico"
        assert link.rel == "icon"
        assert link.sizes == "16x16"
        assert link.width == 16
        assert link.height == 16

    def test_is_valid_default_false(self):
        """Test that is_valid() returns False by default."""
        link = RelLink(href="http://example.com/favicon.ico")
        assert link.is_valid() is False

    def test_is_valid_when_resolved(self):
        """Test is_valid when link has been resolved."""
        link = RelLink(href="http://example.com/favicon.ico")
        link.resolved_href = "http://example.com/favicon.ico"
        link.image_type = "image/x-icon"
        assert link.is_valid() is True

    def test_validate_not_called_twice(self):
        """Test that validate caches result (_validated flag)."""
        link = RelLink(href="http://example.com/favicon.ico")
        # Mark as validated without actually validating
        link._validated = True
        # Should return result based on current state
        assert link.is_valid() is False


class TestFaviconConstants:
    """Tests for favicon-related constants."""

    def test_favicon_rel_values(self):
        """Test that FAVICON_REL contains expected values."""
        assert "icon" in FAVICON_REL
        assert "apple-touch-icon" in FAVICON_REL
        assert "shortcut icon" in FAVICON_REL

    def test_favicon_rel_is_list(self):
        """Test that FAVICON_REL is a list."""
        assert isinstance(FAVICON_REL, list)

    def test_common_favicon_files(self):
        """Test that COMMON_FAVICON_FILES has expected values."""
        assert "favicon.png" in COMMON_FAVICON_FILES
        assert "favicon.ico" in COMMON_FAVICON_FILES
        assert "favicon.svg" in COMMON_FAVICON_FILES

    def test_common_favicon_files_is_list(self):
        """Test that COMMON_FAVICON_FILES is a list."""
        assert isinstance(COMMON_FAVICON_FILES, list)

    def test_favicon_height_is_positive(self):
        """Test that FAVICON_HEIGHT is positive."""
        assert FAVICON_HEIGHT > 0

    def test_ico_to_png_path_is_string(self):
        """Test that ICO_TO_PNG_PATH is a string."""
        assert isinstance(ICO_TO_PNG_PATH, str)
        assert len(ICO_TO_PNG_PATH) > 0

    def test_svg_to_png_path_is_string(self):
        """Test that SVG_TO_PNG_PATH is a string."""
        assert isinstance(SVG_TO_PNG_PATH, str)
        assert len(SVG_TO_PNG_PATH) > 0


class TestFaviconCacheStructure:
    """Tests for favicon cache paths and structure."""

    def test_favicon_overrides_path_exists(self):
        """Test that favicon overrides path is defined."""
        from library.html_util import FAVICON_OVERRIDES

        assert FAVICON_OVERRIDES is not None
        assert isinstance(FAVICON_OVERRIDES, Path)

    def test_favicon_defaults_path_exists(self):
        """Test that favicon defaults path is defined."""
        from library.html_util import FAVICON_DEFAULTS

        assert FAVICON_DEFAULTS is not None
        assert isinstance(FAVICON_DEFAULTS, Path)

    def test_favicon_local_cache_path_exists(self):
        """Test that favicon local cache path is defined."""
        from library.html_util import FAVICON_LOCAL_CACHE

        assert FAVICON_LOCAL_CACHE is not None
        assert isinstance(FAVICON_LOCAL_CACHE, Path)


class TestRelLinkValidation:
    """Tests for RelLink validation methods."""

    def test_validate_method_exists(self):
        """Test that validate method exists."""
        link = RelLink(href="http://example.com/favicon.ico")
        assert callable(link.validate)

    def test_is_valid_method_exists(self):
        """Test that is_valid method exists."""
        link = RelLink(href="http://example.com/favicon.ico")
        assert callable(link.is_valid)

    def test_resolved_href_can_differ_from_href(self):
        """Test that resolved_href can be different from href."""
        link = RelLink(href="http://example.com/favicon.ico")
        link.resolved_href = "http://cdn.example.com/favicon.ico"
        assert link.href != link.resolved_href

    def test_image_dimensions_default_to_zero(self):
        """Test that image dimensions default to zero."""
        link = RelLink(href="http://example.com/favicon.ico")
        assert link.width == 0
        assert link.height == 0

    def test_image_type_default_to_none(self):
        """Test that image_type defaults to None."""
        link = RelLink(href="http://example.com/favicon.ico")
        assert link.image_type is None


class TestRelLinkComparison:
    """Tests for comparing RelLink objects."""

    def test_two_links_with_same_href(self):
        """Test comparing two links with same href."""
        link1 = RelLink(href="http://example.com/favicon.ico")
        link2 = RelLink(href="http://example.com/favicon.ico")
        assert link1.href == link2.href

    def test_two_links_with_different_href(self):
        """Test comparing two links with different href."""
        link1 = RelLink(href="http://example.com/favicon.ico")
        link2 = RelLink(href="http://example.com/apple-touch-icon.png")
        assert link1.href != link2.href

    def test_two_links_with_different_cache_keys(self):
        """Test comparing cache keys."""
        link1 = RelLink(href="http://example.com/favicon.ico", cache_key="example.com")
        link2 = RelLink(href="http://example.com/favicon.ico", cache_key="www.example.com")
        assert link1.cache_key != link2.cache_key


class TestRelLinkInlineImage:
    """Tests for RelLink inline_image field."""

    def test_inline_image_defaults_to_none(self):
        """Test that inline_image defaults to None."""
        link = RelLink(href="http://example.com/favicon.ico")
        assert link.inline_image is None

    def test_inline_image_can_be_set(self):
        """Test that inline_image can be set."""
        link = RelLink(href="http://example.com/favicon.ico")
        link.inline_image = "data:image/png;base64,abc123"
        assert link.inline_image == "data:image/png;base64,abc123"

    def test_inline_image_with_all_fields(self):
        """Test initialization with inline_image."""
        inline_data = "data:image/png;base64,xyz789"
        link = RelLink(
            href="http://example.com/favicon.ico",
            cache_key="example.com",
            height=20,
            width=20,
            image_type="image/png",
            inline_image=inline_data,
        )
        assert link.inline_image == inline_data


class TestGetFaviconCacheDictFormat:
    """Tests for get_favicon_cache handling dict-format cache entries."""

    @patch("library.html_util._load_yaml_with_cache")
    def test_get_favicon_cache_with_string_entry(self, mock_load_cache):
        """Test that string-format cache entries work correctly."""
        from library.html_util import get_favicon_cache

        # Setup mock to return string-format entry
        mock_load_cache.side_effect = [
            {},  # overrides_cache
            {},  # defaults_cache
            {"example.com": "http://example.com/favicon.ico"},  # discovered_cache
        ]

        result = get_favicon_cache("http://example.com/some/path")

        assert result is not None
        assert result.href == "http://example.com/favicon.ico"
        assert result.inline_image is None

    @patch("library.html_util._load_yaml_with_cache")
    def test_get_favicon_cache_with_dict_entry(self, mock_load_cache):
        """Test that dict-format cache entries with inline data work correctly."""
        from library.html_util import get_favicon_cache

        inline_data = "data:image/png;base64,abc123"
        # Setup mock to return dict-format entry with inline
        mock_load_cache.side_effect = [
            {
                "example.com": {"url": "http://example.com/favicon.png", "inline": inline_data}
            },  # overrides_cache
            {},  # defaults_cache
            {},  # discovered_cache
        ]

        result = get_favicon_cache("http://example.com/some/path")

        assert result is not None
        assert result.href == "http://example.com/favicon.png"
        assert result.inline_image == inline_data

    @patch("library.html_util._load_yaml_with_cache")
    def test_get_favicon_cache_with_dict_entry_no_inline(self, mock_load_cache):
        """Test that dict-format entry without inline sets inline_image to None."""
        from library.html_util import get_favicon_cache

        # Setup mock to return dict-format entry without inline
        mock_load_cache.side_effect = [
            {"example.com": {"url": "http://example.com/favicon.png"}},  # overrides_cache
            {},  # defaults_cache
            {},  # discovered_cache
        ]

        result = get_favicon_cache("http://example.com/some/path")

        assert result is not None
        assert result.href == "http://example.com/favicon.png"
        assert result.inline_image is None


class TestGetFaviconCacheSource:
    """Tests for get_favicon_cache_source handling dict-format cache entries."""

    @patch("library.html_util._load_yaml_with_cache")
    def test_get_favicon_cache_source_with_string_entry(self, mock_load_cache):
        """Test that string-format cache entries work correctly."""
        from library.html_util import get_favicon_cache_source

        # Function calls loaders in order: discovered, defaults, overrides
        mock_load_cache.side_effect = [
            {"example.com": "http://example.com/favicon.ico"},  # discovered_cache (called 1st)
            {},  # defaults_cache (called 2nd)
            {},  # overrides_cache (called 3rd)
        ]

        result = get_favicon_cache_source(
            "http://example.com/path", "http://example.com/favicon.ico"
        )

        assert result["file"] == "discovered"
        assert result["precedence"] == 3

    @patch("library.html_util._load_yaml_with_cache")
    def test_get_favicon_cache_source_with_dict_entry(self, mock_load_cache):
        """Test that dict-format cache entries match correctly."""
        from library.html_util import get_favicon_cache_source

        # Function calls loaders in order: discovered, defaults, overrides
        mock_load_cache.side_effect = [
            {},  # discovered_cache (called 1st)
            {},  # defaults_cache (called 2nd)
            {
                "example.com": {"url": "http://example.com/favicon.png", "inline": "data:xxx"}
            },  # overrides_cache (called 3rd)
        ]

        result = get_favicon_cache_source(
            "http://example.com/path", "http://example.com/favicon.png"
        )

        assert result["file"] == "override"
        assert result["precedence"] == 1
        assert result["cache_key"] == "example.com"

    @patch("library.html_util._load_yaml_with_cache")
    def test_get_favicon_cache_source_returns_not_found_for_mismatch(self, mock_load_cache):
        """Test that get_favicon_cache_source returns not found when URL doesn't match."""
        from library.html_util import get_favicon_cache_source

        # Function calls loaders in order: discovered, defaults, overrides
        mock_load_cache.side_effect = [
            {},  # discovered_cache (called 1st)
            {},  # defaults_cache (called 2nd)
            {
                "example.com": {"url": "http://example.com/favicon.png", "inline": "data:xxx"}
            },  # overrides_cache (called 3rd)
        ]

        result = get_favicon_cache_source("http://example.com/path", "http://other.com/favicon.ico")

        assert result["file"] is None
        assert result["precedence"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
