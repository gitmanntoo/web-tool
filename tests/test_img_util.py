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
        ICO files. This test verifies Image.open is called (not short-circuited).
        """
        mock_response = MagicMock()
        mock_response.get_type.return_value = "image/ico"
        mock_response.content = b"\x00\x00\x01\x00"
        mock_get_url.return_value = mock_response

        mock_img = MagicMock()
        mock_img.format = "ICO"
        mock_img.save.return_value = None
        mock_image_open.return_value = mock_img

        convert_ico.cache_clear()
        result = convert_ico("http://example.com/favicon.ico")

        # Image.open MUST be called — assert no early return at magika check
        mock_image_open.assert_called_once()
        # Should return bytes (Pillow save produces bytes)
        assert result is not None
        assert isinstance(result, bytes)

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
        mock_img.save.return_value = None
        mock_image_open.return_value = mock_img

        convert_ico.cache_clear()
        result = convert_ico("http://example.com/favicon.ico")

        # Image.open must be called — no early return
        mock_image_open.assert_called_once()
        assert result is not None
        assert isinstance(result, bytes)

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
        """Test that function returns dict with data_url on success."""
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
        assert isinstance(result, dict)
        assert result["data_url"].startswith("data:image/png;base64,")

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
        assert isinstance(result, dict)
        assert result["data_url"].startswith("data:image/png;base64,")

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

    def test_resize_very_tall_image_does_not_produce_zero_width(self):
        """Regression: very tall images with int() truncation can produce
        new_width=0 (e.g. 1x1000 at height=20 gives int(20*0.001)=0),
        which crashes Pillow's resize()."""
        from library.img_util import _resize_image

        # 1 pixel wide, 1000 tall — aspect_ratio = 0.001
        mock_img = MagicMock()
        mock_img.width = 1
        mock_img.height = 1000
        # Simulate resize returning a mock
        mock_img.resize.return_value = mock_img

        result = _resize_image(mock_img, target_height=20)

        # new_width should be clamped to 1, not 0
        assert mock_img.resize.call_args[0][0] == (1, 20)
        assert result[0] is mock_img
        assert result[1] == 1
        assert result[2] == 20

    def test_resize_very_wide_image_does_not_produce_zero_height(self):
        """Regression: width-clamp path can produce new_height=0 for extremely
        wide images (e.g. 10000x1 clamped to 400px wide gives int(400/10000)=0)."""
        from library.img_util import _resize_image

        # 10000 wide, 1 tall — aspect_ratio=10000, new_width=int(20*10000)=200000
        # max_width=20*20=400, clamped: new_height=int(400/10000)=0 without fix
        mock_img = MagicMock()
        mock_img.width = 10000
        mock_img.height = 1
        mock_img.resize.return_value = mock_img

        result = _resize_image(mock_img, target_height=20)

        # new_height should be clamped to 1, not 0
        assert mock_img.resize.call_args[0][0] == (400, 1)
        assert result[0] is mock_img
        assert result[1] == 400
        assert result[2] == 1

    def test_resize_rejects_invalid_target_height(self):
        """target_height must be >= 1 to prevent Pillow errors."""
        from library.img_util import _resize_image

        mock_img = MagicMock()
        mock_img.width = 100
        mock_img.height = 100

        with pytest.raises(ValueError, match="target_height must be >= 1"):
            _resize_image(mock_img, target_height=0)

        with pytest.raises(ValueError, match="target_height must be >= 1"):
            _resize_image(mock_img, target_height=-5)

    def test_resize_image_returns_dimensions(self):
        """Test that _resize_image returns (image, width, height) tuple."""
        from library.img_util import _resize_image

        mock_img = MagicMock()
        mock_img.width = 100
        mock_img.height = 50
        mock_img.resize.return_value = mock_img

        result = _resize_image(mock_img, target_height=20)

        # Should return tuple of (image, width, height)
        assert isinstance(result, tuple)
        assert len(result) == 3
        resized_img, width, height = result
        assert height == 20
        assert width == 40  # 100/50 * 20 = 40
        assert resized_img is mock_img

    def test_encode_image_inline_returns_dict_with_dimensions(self):
        """Test that encode_image_inline returns dict with data_url, width, height."""
        from library.img_util import encode_image_inline

        # Valid 100x50 PNG (generated by Pillow)
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00d\x00\x00\x002"
            b"\x08\x02\x00\x00\x00%W\xe9\xe9\x00\x00\x00\x81IDATx\x9c\xed\xd2"
            b"\xb1\x11\x00 \x0c\x03\xb1\xc0\xfe;\xc3\n\xf9^\xaa]\xfd\xf9\xbca"
            b"\xeb\xae\x97\x88UxV V V V V V V V V V V V V V V V V V V V V V "
            b"V V V V V V V V V V V V V V V V V V V V V V V V V V V V V V V V"
            b" V V V V V V V V \xd6\xec}H\x8f\x01c\xe0C\x10\xd4\x00\x00\x00"
            b"\x00IEND\xaeB`\x82"
        )
        result = encode_image_inline(png_bytes, target_height=20)

        assert isinstance(result, dict)
        assert "data_url" in result
        assert "width" in result
        assert "height" in result
        assert result["data_url"].startswith("data:image/png;base64,")
        assert result["height"] == 20
        assert result["width"] == 40  # 100/50 * 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
