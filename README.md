# web-tool
Utilities for extracting information from web pages.

Tools use the following pattern:

1. A bookmarklet captures information from a web page and copies it into the clipboard.
2. An endpoint in the web-tool processes the clipboard and returns the result.

All endpoints are hosted at http://localhost:8532.

## Dependencies

- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing.
- [CairoSVG](https://cairosvg.org/) for SVG conversion.
- [Magika](https://google.github.io/magika/) for HTML parsing.
- [Pillow](https://pillow.readthedocs.io/en/stable/) for ICO conversion.
- [Prism](https://prismjs.com/index.html) for syntax highlighting.