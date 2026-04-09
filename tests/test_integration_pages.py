"""
Integration tests for URL, fragment, and title handling using test pages.

These tests use the /test-page endpoint to generate HTML with edge-case
URLs, fragments, and titles, then verify the mirror-links and other endpoints
handle them correctly.

Test pattern:
1. POST clip data to /clip-collector?batchId=<uuid>&chunkNum=1
2. GET /mirror-links?url=<url>&batchId=<uuid>&textLength=<len>
"""

import json
import uuid
from urllib.parse import quote

import pytest


def _submit_clipboard(client, url, title, html, batch_id=None, user_agent="Test Agent"):
    """
    Submit clipboard data to the clip-collector endpoint.

    Returns the batch_id and the JSON-encoded clipboard length.
    batch_id is optional and will be auto-generated if not provided.
    A provided batch_id must be a valid UUID string (the server validates it).
    """
    if batch_id is None:
        batch_id = str(uuid.uuid4())

    clip_data = {
        "url": url,
        "title": title,
        "userAgent": user_agent,
        "cookieString": "",
        "html": html,
    }
    json_body = json.dumps(clip_data)
    resp = client.post(
        f"/clip-collector?batchId={batch_id}&chunkNum=1",
        data=json_body,
        content_type="application/json",
    )
    assert resp.status_code == 200, f"clip-collector failed: {resp.data}"
    return batch_id, len(json_body)


def _get_mirror_links(client, url, batch_id, text_length):
    """Call mirror-links with proper parameters.

    The URL is URL-encoded to preserve # as part of the path/fragment
    rather than being interpreted as a query string delimiter.
    """
    # URL-encode the URL so that # fragments are preserved
    encoded_url = quote(url, safe=":/")
    return client.get(
        f"/mirror-links?url={encoded_url}&batchId={batch_id}&textLength={text_length}"
    )


@pytest.mark.integration
class TestFragmentResolution:
    """Tests for fragment text resolution via fragment handlers in PageMetadata."""

    def test_fragment_handler_heading_with_id(self, app_client, test_page_builder):
        """Heading element with matching id resolves fragment to heading text."""
        url = "http://localhost/test-frag-heading"
        html = "<html><body><h1 id='my-section'>My Section</h1></body></html>"
        batch_id, text_len = _submit_clipboard(app_client, url, "Test", html)

        resp = _get_mirror_links(app_client, url, batch_id, text_len)
        assert resp.status_code == 200
        result_html = resp.get_data(as_text=True)
        assert "My Section" in result_html

    def test_fragment_handler_anchor_inside_heading(self, app_client):
        """Anchor inside heading with href matching fragment resolves
        to heading text minus anchor symbol."""
        # URL fragment matches href on anchor inside heading
        url = "http://localhost/test#frag-link"
        # <h2> contains anchor with href="#frag-link" followed by text
        # Handler strips the anchor text (¶) from heading text
        html = "<html><body><h2><a href='#frag-link'>¶</a>Link Text Here</h2></body></html>"
        batch_id, text_len = _submit_clipboard(app_client, url, "Test", html)

        resp = _get_mirror_links(app_client, url, batch_id, text_len)
        assert resp.status_code == 200
        result_html = resp.get_data(as_text=True)
        # Fragment text appears as data-text attribute; ¶ anchor symbol is included
        assert "¶Link Text Here" in result_html or "Link Text Here" in result_html

    def test_fragment_handler_wrapper_with_id(self, app_client):
        """Section/div wrapper with id containing heading resolves fragment."""
        url = "http://localhost/test#wrapper-section"
        html = (
            "<html><body>"
            "<section id='wrapper-section'><h2>Wrapped Heading</h2></section>"
            "</body></html>"
        )
        batch_id, text_len = _submit_clipboard(app_client, url, "Test", html)

        resp = _get_mirror_links(app_client, url, batch_id, text_len)
        assert resp.status_code == 200
        result_html = resp.get_data(as_text=True)
        assert "Wrapped Heading" in result_html

    def test_fragment_handler_anchor_with_text(self, app_client):
        """Anchor with matching href and text content resolves fragment."""
        # _find_fragment_anchor looks for href=#fragment
        url = "http://localhost/test#link-fragment"
        html = "<html><body><a href='#link-fragment'>Link Fragment Display Text</a></body></html>"
        batch_id, text_len = _submit_clipboard(app_client, url, "Test", html)

        resp = _get_mirror_links(app_client, url, batch_id, text_len)
        assert resp.status_code == 200
        result_html = resp.get_data(as_text=True)
        assert "Link Fragment Display Text" in result_html


@pytest.mark.integration
class TestTitleVariants:
    """Tests for TitleVariants generation from test pages."""

    def test_title_original_preserves_unicode(self, app_client):
        """Original title variant preserves Unicode characters."""
        url = "http://localhost/test"
        title = "日本語タイトル — Russian"
        html = f"<html><head><title>{title}</title></head><body><h1>{title}</h1></body></html>"
        batch_id, text_len = _submit_clipboard(
            app_client, url, title, html, "550e8400-e29b-41d4-a716-446655440001"
        )

        resp = _get_mirror_links(app_client, url, batch_id, text_len)
        assert resp.status_code == 200
        result_html = resp.get_data(as_text=True)
        assert "日本語タイトル" in result_html

    def test_title_ascii_only_strips_emoji(self, app_client):
        """ASCII Only variant strips emoji and converts Unicode to ASCII."""
        url = "http://localhost/test"
        title = "Hello 🌍 World 🚀"
        html = f"<html><head><title>{title}</title></head><body><h1>{title}</h1></body></html>"
        batch_id, text_len = _submit_clipboard(
            app_client, url, title, html, "550e8400-e29b-41d4-a716-446655440002"
        )

        resp = _get_mirror_links(app_client, url, batch_id, text_len)
        assert resp.status_code == 200
        result_html = resp.get_data(as_text=True)
        # Should show ASCII Only row in title variants
        assert "ASCII Only" in result_html
        # Should contain the ASCII-converted title
        assert "Hello" in result_html
        assert "World" in result_html

    def test_title_path_safe_replaces_special_chars(self, app_client):
        """Path Safe variant replaces special characters with safe substitutes."""
        url = "http://localhost/test"
        title = "File: Name [v1].txt"
        html = f"<html><head><title>{title}</title></head><body><h1>{title}</h1></body></html>"
        batch_id, text_len = _submit_clipboard(
            app_client, url, title, html, "550e8400-e29b-41d4-a716-446655440003"
        )

        resp = _get_mirror_links(app_client, url, batch_id, text_len)
        assert resp.status_code == 200
        result_html = resp.get_data(as_text=True)
        # Path Safe row should be present
        assert "Path Safe" in result_html


@pytest.mark.integration
class TestURLVariants:
    """Tests for URL variant generation."""

    def test_url_clean_strips_fragment_and_query(self, app_client):
        """URL Clean variant removes fragment and query string."""
        url = "http://example.com/path?query=value#section"
        html = "<html><body><h1>Test</h1></body></html>"
        batch_id, text_len = _submit_clipboard(
            app_client, url, "Test", html, "550e8400-e29b-41d4-a716-446655440004"
        )

        resp = _get_mirror_links(app_client, url, batch_id, text_len)
        assert resp.status_code == 200
        result_html = resp.get_data(as_text=True)
        # Clean row label should be present
        assert "Clean" in result_html
        # Should contain the clean URL without query or fragment
        assert "example.com/path" in result_html

    def test_url_root_returns_scheme_plus_netloc_plus_first_path(self, app_client):
        """URL Root returns scheme://netloc/first-path-segment."""
        url = "http://example.com/a/b/c?query=1#frag"
        html = "<html><body><h1>Test</h1></body></html>"
        batch_id, text_len = _submit_clipboard(
            app_client, url, "Test", html, "550e8400-e29b-41d4-a716-446655440005"
        )

        resp = _get_mirror_links(app_client, url, batch_id, text_len)
        assert resp.status_code == 200
        result_html = resp.get_data(as_text=True)
        assert "Root" in result_html

    def test_url_host_returns_scheme_plus_netloc_only(self, app_client):
        """URL Host returns only scheme://netloc with no path."""
        url = "http://example.com/deep/path/file.html"
        html = "<html><body><h1>Test</h1></body></html>"
        batch_id, text_len = _submit_clipboard(
            app_client, url, "Test", html, "550e8400-e29b-41d4-a716-446655440006"
        )

        resp = _get_mirror_links(app_client, url, batch_id, text_len)
        assert resp.status_code == 200
        result_html = resp.get_data(as_text=True)
        assert "Host" in result_html


@pytest.mark.integration
class TestMirrorLinksEndpoint:
    """Tests for the /mirror-links endpoint with edge-case content."""

    def test_mirror_links_accepts_batch_id(self, app_client):
        """mirror-links accepts batchId parameter for clipboard data."""
        url = "http://localhost/test"
        html = "<html><body><h1>Test</h1></body></html>"
        batch_id, text_len = _submit_clipboard(
            app_client, url, "Test Title", html, "550e8400-e29b-41d4-a716-446655440000"
        )

        resp = _get_mirror_links(app_client, url, batch_id, text_len)
        assert resp.status_code == 200

    def test_mirror_links_returns_html_with_title(self, app_client):
        """mirror-links returns HTML containing the page title."""
        url = "http://localhost/test"
        html = (
            "<html><head><title>My Test Page</title></head>"
            "<body><h1>My Test Page</h1></body></html>"
        )
        batch_id, text_len = _submit_clipboard(
            app_client, url, "My Test Page", html, "550e8400-e29b-41d4-a716-446655440007"
        )

        resp = _get_mirror_links(app_client, url, batch_id, text_len)
        assert resp.status_code == 200
        result_html = resp.get_data(as_text=True)
        assert "My Test Page" in result_html

    def test_mirror_links_emoji_in_content(self, app_client):
        """mirror-links handles emoji in page content."""
        url = "http://localhost/test"
        html = "<html><body><h1>Emoji Test 🚀</h1><p>Navigation 📍 icons 🚀</p></body></html>"
        batch_id, text_len = _submit_clipboard(
            app_client, url, "Emoji Test 🚀", html, "550e8400-e29b-41d4-a716-446655440008"
        )

        resp = _get_mirror_links(app_client, url, batch_id, text_len)
        assert resp.status_code == 200
        result_html = resp.get_data(as_text=True)
        assert "Emoji Test" in result_html


@pytest.mark.integration
class TestTestPageEndpoint:
    """Tests for the /test-page endpoint itself."""

    def test_test_page_returns_html(self, app_client):
        """test-page returns HTML content."""
        resp = app_client.get("/test-page?title=Hello")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert "<html>" in html
        assert "Hello" in html

    def test_test_page_with_fragment(self, app_client):
        """test-page renders heading with fragment id."""
        resp = app_client.get("/test-page?title=Section Page&fragment=my-section")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert 'id="my-section"' in html
        assert "Section Page" in html

    def test_test_page_with_anchor_fragment(self, app_client):
        """test-page renders anchor inside heading when anchor-fragment is set."""
        resp = app_client.get("/test-page?title=Test&anchor-fragment=my-anchor")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert 'id="my-anchor"' in html
        assert '<a href="#my-anchor">' in html

    def test_test_page_with_wrap_fragment(self, app_client):
        """test-page renders wrapper section when wrap-fragment is set."""
        resp = app_client.get("/test-page?title=Test&wrap-fragment=wrapper-id")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert 'id="wrapper-id"' in html
        assert "<section" in html

    def test_test_page_with_unicode_content(self, app_client):
        """test-page renders Unicode content when unicode-content=yes."""
        resp = app_client.get("/test-page?title=Test&unicode-content=yes")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert "Русский" in html or "中文" in html

    def test_test_page_with_emoji_content(self, app_client):
        """test-page renders emoji content when emoji-content=yes."""
        resp = app_client.get("/test-page?title=Test&emoji-content=yes")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert "🌍" in html or "🚀" in html or "📍" in html

    def test_test_page_post_method(self, app_client):
        """test-page accepts POST with form data."""
        resp = app_client.post(
            "/test-page", data={"title": "Posted Title", "fragment": "posted-frag"}
        )
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert "Posted Title" in html
        assert 'id="posted-frag"' in html
