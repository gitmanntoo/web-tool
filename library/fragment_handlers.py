"""Fragment text resolution handlers for extracting anchor/heading text from HTML."""

from urllib.parse import urlunparse

from bs4 import BeautifulSoup

HEADING_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6"]


def _find_fragment_anchor(soup: BeautifulSoup, parsed_url, fragment: str):
    """Find anchor tag with href matching the fragment.

    Args:
        soup: BeautifulSoup parsed HTML object
        parsed_url: Parsed URL object (from urlparse)
        fragment: The URL fragment to search for

    Returns:
        The anchor tag if found, None otherwise
    """
    # Look for anchor with fragment as href
    anchor = soup.find(href=f"#{fragment}")
    if anchor:
        return anchor

    # Look for anchor with full URL as href
    url_with_fragment = urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            "",
            "",
            fragment,
        )
    )
    return soup.find(href=url_with_fragment)


def fragment_handler_heading_with_id(
    soup: BeautifulSoup | None, parsed_url, fragment: str
) -> str | None:
    """Handler: Heading element with id attribute matching fragment."""
    heading = soup.find(HEADING_TAGS, id=fragment)
    if heading and (text := heading.text.strip()):
        return text
    return None


def fragment_handler_anchor_inside_heading(
    soup: BeautifulSoup | None, parsed_url, fragment: str
) -> str | None:
    """Handler: Anchor tag inside heading (e.g., <h2>Text<a href="#fragment">¶</a></h2>)."""
    anchor = _find_fragment_anchor(soup, parsed_url, fragment)
    if anchor and anchor.parent and anchor.parent.name in HEADING_TAGS:
        heading_text = anchor.parent.get_text(strip=True)
        anchor_text = anchor.get_text(strip=True)
        if anchor_text and heading_text.endswith(anchor_text):
            heading_text = heading_text[: -len(anchor_text)].strip()
        if heading_text:
            return heading_text
    return None


def fragment_handler_element_before_heading(
    soup: BeautifulSoup | None, parsed_url, fragment: str
) -> str | None:
    """Handler: Element with id/name before a heading."""
    # Try id attribute
    element = soup.find(id=fragment)
    if element:
        next_elem = element.find_next_sibling()
        if next_elem and next_elem.name in HEADING_TAGS:
            if text := next_elem.text.strip():
                return text

    # Try name attribute (older HTML)
    element = soup.find(attrs={"name": fragment})
    if element:
        next_elem = element.find_next_sibling()
        if next_elem and next_elem.name in HEADING_TAGS:
            if text := next_elem.text.strip():
                return text
    return None


def fragment_handler_wrapper_with_id(
    soup: BeautifulSoup | None, parsed_url, fragment: str
) -> str | None:
    """Handler: Wrapper element (section/div/article) with id containing a heading."""
    wrapper = soup.find(["section", "div", "article"], id=fragment)
    if wrapper:
        heading = wrapper.find(HEADING_TAGS)
        if heading and (text := heading.text.strip()):
            return text
    return None


def fragment_handler_anchor_with_text(
    soup: BeautifulSoup | None, parsed_url, fragment: str
) -> str | None:
    """Handler: Anchor tag with href matching fragment that has text content."""
    anchor = _find_fragment_anchor(soup, parsed_url, fragment)
    if anchor and (text := anchor.text.strip()):
        return text
    return None


def fragment_handler_anchor_siblings(
    soup: BeautifulSoup | None, parsed_url, fragment: str
) -> str | None:
    """Handler: Previous or next sibling heading of anchor without text."""
    anchor = _find_fragment_anchor(soup, parsed_url, fragment)
    if not anchor:
        return None

    # Check previous sibling
    prev = anchor.find_previous_sibling()
    if prev and prev.name in HEADING_TAGS:
        if text := prev.text.strip():
            return text

    # Check next sibling
    next_elem = anchor.find_next_sibling()
    if next_elem and next_elem.name in HEADING_TAGS:
        if text := next_elem.text.strip():
            return text
    return None
