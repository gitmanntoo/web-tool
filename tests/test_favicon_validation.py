"""
Tests for favicon validation functionality.

Tests the get_valid_favicon_links() function and related validation logic.
"""

from unittest.mock import MagicMock, patch

import pytest

from library.html_util import (
    RelLink,
    get_favicon_links,
    get_valid_favicon_links,
    sort_favicon_links,
    validate_top_candidates,
)


class TestGetValidFaviconLinks:
    """Tests for get_valid_favicon_links function."""

    @patch("library.html_util.get_favicon_links")
    @patch("library.html_util.validate_top_candidates")
    @patch("library.html_util.sort_favicon_links")
    def test_returns_validated_links_only(self, mock_sort, mock_validate, mock_get_links):
        """Test that only validated links are returned."""
        mock_links = [RelLink(href="http://example.com/favicon.png")]
        mock_get_links.return_value = mock_links
        mock_sort.return_value = mock_links
        mock_validate.return_value = mock_links

        result = get_valid_favicon_links("http://example.com", None)

        assert result == mock_links
        mock_get_links.assert_called_once_with("http://example.com", None)
        mock_sort.assert_called_once_with(mock_links, 20)
        mock_validate.assert_called_once_with(mock_links, 1)

    @patch("library.html_util.get_favicon_links")
    @patch("library.html_util.validate_top_candidates")
    @patch("library.html_util.sort_favicon_links")
    def test_returns_empty_when_no_valid_favicons(self, mock_sort, mock_validate, mock_get_links):
        """Test that empty list is returned when no valid favicons."""
        mock_links = [RelLink(href="http://example.com/bad.png")]
        mock_get_links.return_value = mock_links
        mock_sort.return_value = mock_links
        mock_validate.return_value = []  # None pass validation

        result = get_valid_favicon_links("http://example.com", None)

        assert result == []

    @patch("library.html_util.get_favicon_links")
    @patch("library.html_util.validate_top_candidates")
    @patch("library.html_util.sort_favicon_links")
    def test_max_count_passed_to_validate(self, mock_sort, mock_validate, mock_get_links):
        """Test that max_count parameter is passed to validate_top_candidates."""
        mock_links = [RelLink(href="http://example.com/favicon.png")]
        mock_get_links.return_value = mock_links
        mock_sort.return_value = mock_links
        mock_validate.return_value = mock_links

        get_valid_favicon_links("http://example.com", None, max_count=5)

        mock_validate.assert_called_once_with(mock_links, 5)

    @patch("library.html_util.get_favicon_links")
    @patch("library.html_util.validate_top_candidates")
    @patch("library.html_util.sort_favicon_links")
    def test_custom_favicon_height_passed_to_sort(self, mock_sort, mock_validate, mock_get_links):
        """Test that custom favicon_height is passed to sort_favicon_links."""
        mock_links = [RelLink(href="http://example.com/favicon.png")]
        mock_get_links.return_value = mock_links
        mock_sort.return_value = mock_links
        mock_validate.return_value = mock_links

        get_valid_favicon_links("http://example.com", None, favicon_height=32)

        mock_sort.assert_called_once_with(mock_links, 32)

    def test_function_signature(self):
        """Test that function exists and has correct signature."""
        import inspect

        sig = inspect.signature(get_valid_favicon_links)
        params = list(sig.parameters.keys())

        assert "page_url" in params
        assert "soup" in params
        assert "max_count" in params
        assert "favicon_height" in params

    @patch("library.html_util.get_favicon_links")
    @patch("library.html_util.validate_top_candidates")
    @patch("library.html_util.sort_favicon_links")
    def test_default_parameters(self, mock_sort, mock_validate, mock_get_links):
        """Test that default parameters work correctly."""
        mock_links = [RelLink(href="http://example.com/favicon.png")]
        mock_get_links.return_value = mock_links
        mock_sort.return_value = mock_links
        mock_validate.return_value = mock_links

        get_valid_favicon_links("http://example.com", None)

        # Check defaults: max_count=1, favicon_height=20
        mock_sort.assert_called_once_with(mock_links, 20)
        mock_validate.assert_called_once_with(mock_links, 1)


class TestValidateTopCandidates:
    """Tests for validate_top_candidates function behavior."""

    def test_returns_empty_for_empty_input(self):
        """Test that empty list returns empty."""
        result = validate_top_candidates([])
        assert result == []

    def test_returns_single_valid_link(self):
        """Test single valid link is returned."""
        link = RelLink(href="http://example.com/favicon.png")
        link.resolved_href = "http://example.com/favicon.png"
        link.image_type = "image/png"
        link._validated = True  # Mark as already validated

        result = validate_top_candidates([link])
        assert len(result) == 1
        assert result[0] == link

    def test_returns_multiple_valid_links_up_to_max_count(self):
        """Test multiple valid links up to max_count."""
        links = []
        for i in range(3):
            link = RelLink(href=f"http://example.com/favicon{i}.png")
            link.resolved_href = link.href
            link.image_type = "image/png"
            link._validated = True  # Mark as already validated
            links.append(link)

        result = validate_top_candidates(links, max_count=2)
        assert len(result) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
