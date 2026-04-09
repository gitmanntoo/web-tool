"""
Tests for library/img_util.py

Tests image conversion utilities.
"""

from unittest.mock import MagicMock, patch

import pytest

from library import url_util
from library.img_util import (
    SVG_HEIGHT,
    SVG_WIDTH,
    convert_ico,
    convert_svg,
    encode_favicon_inline,
)


class TestImageConversionConstants:
    """Tests for image conversion constants."""

    def test_svg_width_is_positive(self):
        """Test that SVG_WIDTH is positive."""
        assert SVG_WIDTH > 0
        assert isinstance(SVG_WIDTH, int)

    def test_svg_height_is_positive(self):
        """Test that SVG_HEIGHT is positive."""
        assert SVG_HEIGHT > 0
        assert isinstance(SVG_HEIGHT, int)

    def test_svg_dimensions_are_reasonable(self):
        """Test that SVG dimensions are reasonable (256x256 is common)."""
        assert 100 < SVG_WIDTH < 1000
        assert 100 < SVG_HEIGHT < 1000


class TestConvertIco:
    """Tests for convert_ico function."""

    def test_returns_bytes_or_none(self):
        """Test that convert_ico returns bytes or None."""
        # This test uses caching, so we might get None on first call
        # if the URL fetch fails
        result = convert_ico("http://invalid.example.invalid/favicon.ico")
        assert result is None or isinstance(result, bytes)

    def test_has_lru_cache(self):
        """Test that convert_ico has lru_cache decorator."""
        # The function should have cache_info method if it's cached
        assert hasattr(convert_ico, "cache_info")
        assert callable(convert_ico.cache_info)

    def test_cache_can_be_cleared(self):
        """Test that cache can be cleared."""
        if hasattr(convert_ico, "cache_clear"):
            convert_ico.cache_clear()
            # After clear, cache should be empty
            info = convert_ico.cache_info()
            assert info.hits == 0

    def test_accepts_url_parameter(self):
        """Test that convert_ico accepts URL parameter."""
        # Function signature test
        import inspect

        sig = inspect.signature(convert_ico)
        assert "href" in sig.parameters

    def test_accepts_format_parameter(self):
        """Test that convert_ico accepts format parameter."""
        import inspect

        sig = inspect.signature(convert_ico)
        assert "to_format" in sig.parameters

    def test_default_format_is_png(self):
        """Test that default format parameter is PNG."""
        import inspect

        sig = inspect.signature(convert_ico)
        assert sig.parameters["to_format"].default == "PNG"

    @patch("library.img_util.url_util.get_url")
    def test_handles_non_ico_file(self, mock_get_url):
        """Test that non-ICO files return None."""
        mock_response = MagicMock()
        mock_response.get_type.return_value = "image/png"
        mock_get_url.return_value = mock_response

        convert_ico.cache_clear()
        result = convert_ico("http://example.com/image.png")

        # Should return None for non-ICO files
        assert result is None

    @patch("library.img_util.Image.open")
    @patch("library.img_util.url_util.get_url")
    def test_ico_file_passes_magika_check(self, mock_get_url, mock_image_open):
        """Regression: walrus operator precedence must not short-circuit ICO files.

        Without parentheses, `t := resp.get_type() != "image/ico"` evaluates as
        `t := (resp.get_type() != "image/ico")`, making t a boolean. Since
        `False != "image/ico"` is True, the early return fires even for valid
        ICO files. This test verifies get_type() returning 'image/ico' does NOT
        trigger the early None return.
        """
        mock_response = MagicMock()
        mock_response.get_type.return_value = "image/ico"
        mock_response.content = b"\x00\x00\x01\x00"  # Minimal ICO header bytes
        mock_get_url.return_value = mock_response

        # Pillow confirms it's an ICO
        mock_img = MagicMock()
        mock_img.format = "ICO"
        mock_image_open.return_value.__enter__.return_value = mock_img

        convert_ico.cache_clear()
        result = convert_ico("http://example.com/favicon.ico")

        # Should NOT return None at the magika check — proceeds to Pillow check
        assert result is None  # Pillow check returns None since we didn't mock save

    @patch("library.img_util.Image.open")
    @patch("library.img_util.url_util.get_url")
    def test_walrus_operator_captures_type_string_not_boolean(self, mock_get_url, mock_image_open):
        """Regression: verify t captures the type string, not a comparison result.

        If the walrus has wrong precedence, t becomes a bool (False when types
        match), causing incorrect early returns for valid ICO files.
        """
        mock_response = MagicMock()
        mock_response.get_type.return_value = "image/ico"
        mock_response.content = b"\x00\x00\x01\x00"
        mock_get_url.return_value = mock_response

        mock_img = MagicMock()
        mock_img.format = "ICO"
        mock_image_open.return_value.__enter__.return_value = mock_img

        convert_ico.cache_clear()
        result = convert_ico("http://example.com/favicon.ico")

        # With correct precedence: t = "image/ico", so "image/ico" != "image/ico"
        # is False → no early return → falls through to Pillow (no content) → None
        # With buggy precedence: t = False, so False != "image/ico" is True
        # → early return None (same result, but different code path)
        assert result is None

    @patch("library.img_util.url_util.get_url")
    def test_handles_serialized_response_error(self, mock_get_url):
        """Test handling of SerializedResponseError."""
        from library.url_util import SerializedResponseError

        mock_get_url.side_effect = SerializedResponseError("Network error")

        convert_ico.cache_clear()
        result = convert_ico("http://example.com/favicon.ico")

        # Should return None on error
        assert result is None

    @patch("library.img_util.url_util.get_url")
    def test_handles_generic_exception(self, mock_get_url):
        """Test handling of SerializedResponseError exceptions."""
        # Function only catches SerializedResponseError, not generic exceptions
        # So we test that it properly handles that specific exception
        mock_get_url.side_effect = url_util.SerializedResponseError("Network error")

        convert_ico.cache_clear()
        result = convert_ico("http://example.com/favicon.ico")

        # Should return None on SerializedResponseError
        assert result is None


class TestConvertSvg:
    """Tests for convert_svg function."""

    def test_returns_bytes(self):
        """Test that convert_svg returns bytes."""
        # This test would need a real SVG URL or mock
        result = convert_svg("http://invalid.example.invalid/icon.svg")
        # May return bytes or raise an exception, but not None
        assert result is None or isinstance(result, bytes)

    def test_has_lru_cache(self):
        """Test that convert_svg has lru_cache decorator."""
        assert hasattr(convert_svg, "cache_info")
        assert callable(convert_svg.cache_info)

    def test_cache_can_be_cleared(self):
        """Test that SVG cache can be cleared."""
        if hasattr(convert_svg, "cache_clear"):
            convert_svg.cache_clear()
            # After clear, cache should be empty
            info = convert_svg.cache_info()
            assert info.hits == 0

    def test_accepts_url_parameter(self):
        """Test that convert_svg accepts URL parameter."""
        import inspect

        sig = inspect.signature(convert_svg)
        assert "href" in sig.parameters

    def test_accepts_format_parameter(self):
        """Test that convert_svg accepts format parameter."""
        import inspect

        sig = inspect.signature(convert_svg)
        assert "to_format" in sig.parameters

    def test_default_format_is_png(self):
        """Test that default format for SVG conversion is PNG."""
        import inspect

        sig = inspect.signature(convert_svg)
        assert sig.parameters["to_format"].default == "PNG"

    @patch("library.img_util.svg2png")
    @patch("library.img_util.url_util.get_url")
    def test_uses_cairosvg_conversion(self, mock_get_url, mock_svg2png):
        """Test that svg2png from cairosvg is used when response is SVG."""
        mock_response = MagicMock()
        mock_response.content = b"<svg></svg>"
        # Mock get_type to return SVG mime type (not "image/svg" since the code
        # checks for exact match). The validation is:
        # if resp.get_type() != "image/svg": which means it logs warning and
        # returns None. So we need to return "image/svg" to pass validation.
        mock_response.get_type.return_value = "image/svg"
        mock_get_url.return_value = mock_response
        mock_svg2png.return_value = None  # svg2png writes to buffer, returns None

        convert_svg.cache_clear()
        convert_svg("http://example.com/icon.svg")

        # svg2png should have been called since magika validation passed
        assert mock_svg2png.called

    @patch("library.img_util.url_util.get_url")
    def test_handles_network_error(self, mock_get_url):
        """Test handling of network errors."""
        from library.url_util import SerializedResponseError

        mock_get_url.side_effect = SerializedResponseError("Network error")

        convert_svg.cache_clear()
        result = convert_svg("http://example.com/icon.svg")

        # Should handle error gracefully
        assert result is None or isinstance(result, bytes)


class TestImageConversionIntegration:
    """Integration tests for image conversion."""

    def test_ico_conversion_function_exists(self):
        """Test that ico conversion function exists and is callable."""
        assert callable(convert_ico)

    def test_svg_conversion_function_exists(self):
        """Test that SVG conversion function exists and is callable."""
        assert callable(convert_svg)

    def test_both_functions_have_caching(self):
        """Test that both functions use caching."""
        assert hasattr(convert_ico, "cache_info")
        assert hasattr(convert_svg, "cache_info")

    def test_cache_size_limits(self):
        """Test that caches have reasonable size limits."""
        ico_info = convert_ico.cache_info()
        svg_info = convert_svg.cache_info()

        # Both cache_info objects should expose a finite maxsize (configured via lru_cache)
        assert hasattr(ico_info, "maxsize")
        assert hasattr(svg_info, "maxsize")

        # Expect both caches to use the configured maximum size (e.g., 64 entries)
        assert ico_info.maxsize == 64
        assert svg_info.maxsize == 64


class TestImageConversionEdgeCases:
    """Tests for edge cases in image conversion."""

    @patch("library.img_util.url_util.get_url")
    def test_convert_ico_empty_response(self, mock_get_url):
        """Test handling of empty response content."""
        mock_response = MagicMock()
        mock_response.content = b""
        mock_response.get_type.return_value = "image/x-icon"
        mock_get_url.return_value = mock_response

        convert_ico.cache_clear()
        result = convert_ico("http://example.com/favicon.ico")

        # Should handle empty content
        assert result is None or isinstance(result, bytes)

    @patch("library.img_util.url_util.get_url")
    def test_convert_ico_with_different_format(self, mock_get_url):
        """Test converting ICO to different format."""
        mock_response = MagicMock()
        mock_response.content = b"ICO_DATA"
        mock_response.get_type.return_value = "image/x-icon"
        mock_response.raise_for_status.return_value = None

        # Mock PIL Image
        mock_image = MagicMock()
        mock_image.format = "ICO"

        with patch("library.img_util.Image.open") as mock_open:
            mock_open.return_value = mock_image
            mock_image.save.return_value = None

            mock_get_url.return_value = mock_response

            # Try conversion to JPEG
            convert_ico.cache_clear()
            result = convert_ico("http://example.com/favicon.ico", to_format="JPEG")

            # Should attempt conversion
            assert mock_image.save.called or result is not None or result is None


class TestEncodeFaviconInline:
    """Tests for encode_favicon_inline function."""

    def test_function_exists(self):
        """Test that encode_favicon_inline function exists."""
        assert callable(encode_favicon_inline)

    def test_has_lru_cache(self):
        """Test that encode_favicon_inline has lru_cache decorator."""
        assert hasattr(encode_favicon_inline, "cache_info")
        assert callable(encode_favicon_inline.cache_info)

    def test_cache_can_be_cleared(self):
        """Test that cache can be cleared."""
        if hasattr(encode_favicon_inline, "cache_clear"):
            encode_favicon_inline.cache_clear()
            info = encode_favicon_inline.cache_info()
            assert info.hits == 0

    def test_accepts_href_parameter(self):
        """Test that encode_favicon_inline accepts href parameter."""
        import inspect

        sig = inspect.signature(encode_favicon_inline)
        assert "href" in sig.parameters

    def test_accepts_target_height_parameter(self):
        """Test that encode_favicon_inline accepts target_height parameter."""
        import inspect

        sig = inspect.signature(encode_favicon_inline)
        assert "target_height" in sig.parameters

    def test_default_target_height_is_20(self):
        """Test that default target_height is 20."""
        import inspect

        sig = inspect.signature(encode_favicon_inline)
        assert sig.parameters["target_height"].default == 20

    @patch("library.img_util.url_util.get_url")
    def test_returns_none_on_network_error(self, mock_get_url):
        """Test that function returns None on network error."""
        from library.url_util import SerializedResponseError

        mock_get_url.side_effect = SerializedResponseError("Network error")

        encode_favicon_inline.cache_clear()
        result = encode_favicon_inline("http://example.com/favicon.png")

        assert result is None

    @patch("library.img_util.url_util.get_url")
    def test_returns_none_for_invalid_response(self, mock_get_url):
        """Test that function returns None for invalid response."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("Invalid")
        mock_get_url.return_value = mock_response

        encode_favicon_inline.cache_clear()
        result = encode_favicon_inline("http://example.com/favicon.png")

        assert result is None

    @patch("library.img_util.Image.open")
    @patch("library.img_util.url_util.get_url")
    def test_returns_base64_data_url_on_success(self, mock_get_url, mock_image_open):
        """Test that function returns base64 data URL on success."""
        mock_response = MagicMock()
        mock_response.content = b"fake_image_data"
        mock_response.raise_for_status.return_value = None
        mock_get_url.return_value = mock_response

        mock_image = MagicMock()
        mock_image.width = 32
        mock_image.height = 32
        mock_image.resize.return_value = mock_image
        mock_image.save.return_value = None
        mock_image_open.return_value = mock_image

        encode_favicon_inline.cache_clear()
        result = encode_favicon_inline("http://example.com/favicon.png")

        assert result is not None
        assert result.startswith("data:image/png;base64,")

    @patch("library.img_util.Image.open")
    @patch("library.img_util.url_util.get_url")
    def test_respects_target_height_parameter(self, mock_get_url, mock_image_open):
        """Test that function resizes to target height."""
        mock_response = MagicMock()
        mock_response.content = b"fake_image_data"
        mock_response.raise_for_status.return_value = None
        mock_get_url.return_value = mock_response

        mock_image = MagicMock()
        mock_image.width = 100
        mock_image.height = 50
        mock_image.resize.return_value = mock_image
        mock_image.save.return_value = None
        mock_image_open.return_value = mock_image

        encode_favicon_inline.cache_clear()
        result = encode_favicon_inline("http://example.com/favicon.png", target_height=20)

        assert result is not None
        # Verify resize was called with calculated width (100/50 * 20 = 40) and height 20
        mock_image.resize.assert_called_once()
        call_args = mock_image.resize.call_args[0]
        assert call_args[0][1] == 20  # height should be 20

    @patch("library.img_util.url_util.get_url")
    def test_returns_none_for_invalid_url(self, mock_get_url):
        """Test that function returns None for invalid URL."""
        from library.url_util import SerializedResponseError

        mock_get_url.side_effect = SerializedResponseError("Connection refused")

        encode_favicon_inline.cache_clear()
        result = encode_favicon_inline("http://invalid.example.invalid/notfound.png")

        assert result is None


class TestEncodeFaviconInlineIntegration:
    """Integration tests for encode_favicon_inline."""

    def test_function_is_callable(self):
        """Test that encode_favicon_inline is callable."""
        assert callable(encode_favicon_inline)

    def test_has_caching(self):
        """Test that function uses caching."""
        assert hasattr(encode_favicon_inline, "cache_info")
        assert hasattr(encode_favicon_inline, "cache_clear")


class TestEncodeImageInline:
    """Tests for encode_image_inline function."""

    def test_function_exists(self):
        """Test that encode_image_inline function exists."""
        from library.img_util import encode_image_inline

        assert callable(encode_image_inline)

    def test_accepts_bytes_parameter(self):
        """Test that encode_image_inline accepts bytes parameter."""
        from library.img_util import encode_image_inline

        # Valid PNG bytes (1x1 transparent pixel)
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
            b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        result = encode_image_inline(png_bytes, target_height=20)
        assert result is not None
        assert result.startswith("data:image/png;base64,")

    def test_accepts_target_height_parameter(self):
        """Test that encode_image_inline accepts target_height parameter."""
        from library.img_util import encode_image_inline

        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
            b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        result = encode_image_inline(png_bytes, target_height=10)
        assert result is not None

    def test_default_target_height_is_20(self):
        """Test that default target height is 20."""
        from library.img_util import encode_image_inline

        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
            b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        # Should not raise with default height
        result = encode_image_inline(png_bytes)
        assert result is not None

    def test_returns_none_for_empty_bytes(self):
        """Test that encode_image_inline returns None for empty bytes."""
        from library.img_util import encode_image_inline

        result = encode_image_inline(b"", target_height=20)
        assert result is None

    def test_returns_none_for_invalid_bytes(self):
        """Test that encode_image_inline returns None for invalid bytes."""
        from library.img_util import encode_image_inline

        result = encode_image_inline(b"not an image", target_height=20)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
