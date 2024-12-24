# web-tool
Utilities for extracting information from web pages.

Tools use the following pattern:

1. A bookmarklet captures information from a web page and copies it into the clipboard.
2. An endpoint in the web-tool processes the clipboard and returns the result.

All endpoints are hosted at <http://localhost:8532>.

## Bookmarklets

Each of the links below will open the bookmarklet JavaScript in a new page and copy it to the clipboard. Add a bookmark in your
browser using the bookmarklet JavaScript for the URL. Name it anything you would like!

***NOTE:*** The host is set automatically to match the port used when running web-tool (e.g. the `-p` parameter in the docker command).
If the port is changed, the bookmarklets will need to be updated with the new port.

- <a href="http://localhost:8532/js/mirror-links.js?mode=bookmarklet" target="_blank">links</a>: 
- <a href="http://localhost:8532/js/mirror-favicons.js?mode=bookmarklet" target="_blank">favicons</a>
- <a href="http://localhost:8532/js/mirror-text.js?mode=bookmarklet" target="_blank">text</a>
- <a href="http://localhost:8532/js/mirror-soup-text.js?mode=bookmarklet" target="_blank">soup-text</a>
- <a href="http://localhost:8532/js/mirror-html-source.js?mode=bookmarklet" target="_blank">html-source</a>
- <a href="http://localhost:8532/js/mirror-html-source.js?mode=bookmarklet&format=text" target="_blank">html-source-text</a>

## Use Docker

<pre>
docker stop web-tool; \
  docker rm web-tool; \
  docker pull dockmann/web-tool && \
  docker run -d -p 8532:8532 -v $(pwd):/data --name web-tool dockmann/web-tool
</pre>

## Dependencies

- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing.
- [CairoSVG](https://cairosvg.org/) for SVG conversion.
- [Magika](https://google.github.io/magika/) for content type identification.
- [NLTK :: Natural Language Toolkit](https://www.nltk.org/) for word identification.
- [Pillow](https://pillow.readthedocs.io/en/stable/) for ICO conversion.
- [Prism](https://prismjs.com/index.html) for syntax highlighting in HTML pages.
