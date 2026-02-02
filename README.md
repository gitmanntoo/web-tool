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

- <a href="http://localhost:8532/js/mirror-links.js?mode=bookmarklet" target="_blank">links</a>
    - Builds links for Obsidian (with a favicon) and standard markdown. 
    - The first link is copied to the clipboard.
- <a href="http://localhost:8532/js/mirror-favicons.js?mode=bookmarklet" target="_blank">favicons</a>
    - Gets details for all favicons for the current page.
    - The links have format `<page url root>: <favicon url>` which is the same format used in the local favicon cache.
- <a href="http://localhost:8532/js/mirror-text.js?mode=bookmarklet" target="_blank">text</a>
    - Extracts the text on the page using NLP techniques.
    - Extracted text includes snippets found in `<script>` tags.
- <a href="http://localhost:8532/js/mirror-soup-text.js?mode=bookmarklet" target="_blank">soup-text</a>
    - Extracts text on the page using BeautifulSoup's `get_text()` method.
    - This method does not extract text in `<script>` tags which may exclude some important blocks.
- <a href="http://localhost:8532/js/mirror-html-source.js?mode=bookmarklet" target="_blank">html-source</a>
    - Displays the HTML source of the page using Prism formatting.
    - This may fail on some larger, complex pages.
- <a href="http://localhost:8532/js/mirror-html-source.js?mode=bookmarklet&format=text" target="_blank">html-source-text</a>
    - Display the HTML source of the page using plain text.
    - This should always work.

## Use Docker

This shell script will run web-tool on the default port 8532 with local storage for the favicon cache.

<pre>
# Stop and remove the currently running web-tool, ignoring errors.
docker stop web-tool || true
docker rm web-tool || true

# Download the latest image and run it.
docker pull dockmann/web-tool
docker run -d --restart always -p 8532:8532 -v $(pwd)/web-tool:/data --name web-tool dockmann/web-tool
</pre>

## Dependencies

- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing.
- [CairoSVG](https://cairosvg.org/) for SVG conversion.
- [Magika](https://google.github.io/magika/) for content type identification.
- [NLTK :: Natural Language Toolkit](https://www.nltk.org/) for word identification.
- [Pillow](https://pillow.readthedocs.io/en/stable/) for ICO conversion.
- [Prism](https://prismjs.com/index.html) for syntax highlighting in HTML pages.

## Favicon Configuration

web-tool uses a three-tier favicon cache system:

1. **User Overrides** (`static/favicon-overrides.yml`) - Highest priority
   - Manual customizations that always take precedence
   - Edit this file to set your preferred favicons for specific sites
   - Format: `cache_key: favicon_url`

2. **App Defaults** (`static/favicon.yml`) - Medium priority
   - Curated defaults distributed with the application
   - Updated with new releases

3. **Auto-discovered** (`local-cache/favicon.yml` or `/data/favicon.yml` in container) - Lowest priority
   - Dynamically discovered favicons automatically cached on first use
   - Persists across restarts

When looking up a favicon, web-tool searches from most specific to least specific:
`netloc/path` → `subdomain.domain.tld` → `domain.tld`, checking overrides first, then defaults, then auto-discovered cache.

### Managing Favicon Overrides

**Via UI (Recommended):**
- Navigate to `/mirror-favicons?url=<page_url>` to see all available favicons for a page
- Click "Add to Overrides" button to add domain or path-based overrides
- Changes take effect immediately

**Via File Edit:**

Edit `static/favicon-overrides.yml` directly:

```yaml
# Domain-level override (applies to all pages on domain)
google.com: https://www.google.com/favicon.ico

# Path-level override (applies to specific section)
github.com/microsoft: https://github.githubassets.com/favicons/favicon.png
```

**Cache Key Rules:**
- **Domain only**: `example.com` - applies to all pages on the domain
- **Domain + path**: `example.com/docs` - applies to specific section (first path segment)
- www prefix is automatically normalized (`www.example.com` → `example.com`)
- More specific keys take precedence (path > subdomain > domain)

**Examples:**
```yaml
# Domain-level
ibm.com: https://www.ibm.com/favicon.ico
github.com: https://github.githubassets.com/favicons/favicon.svg

# Path-level
docs.python.org/3: https://docs.python.org/3/_static/py.svg
stackoverflow.com/questions: https://cdn.sstatic.net/Sites/stackoverflow/Img/favicon.ico
```

## Debug

Container detection status and clipboard proxy testing are available at:

- <a href="http://localhost:8532/debug/container" target="_blank">container status</a>
    - Returns JSON with `running_in_container` flag to verify container detection logic.
    - Use this to confirm whether the app is detecting a Docker container correctly.

- <a href="http://localhost:8532/debug/clip-cache" target="_blank">clip cache state</a>
    - Returns JSON with current clip_cache state including batch count, memory usage, and individual batch details.
    - Shows TTL, size limits, and how close the cache is to configured limits.

- <a href="http://localhost:8532/debug/clipboard-proxy" target="_blank">clipboard proxy test</a>
    - Interactive test page for the clipboard proxy functionality.
    - Simulates what happens when a bookmarklet successfully captures clipboard data.
    - Submit test data through the proxy to verify `/clip-collector` and `/mirror-clip` work correctly.

- <a href="http://localhost:8532/debug/favicon-files" target="_blank">favicon files</a>
    - Returns JSON showing the three-tier favicon cache system in precedence order.
    - Displays file paths, existence, size, modification time, entry count, and in-memory cache status.
    - Shows sample entries from each cache file (overrides, defaults, auto-discovered).

- <a href="http://localhost:8532/debug/title-variants" target="_blank">title variants</a>
    - Interactive test page for generating title string variants.
    - Enter any title string and click Generate to see all variants (Original, ASCII + Emoji, ASCII Only, Path Safe).
    - Duplicate variants are visually indicated with reduced opacity and gray background.

- <a href="http://localhost:8532/debug/url-variants" target="_blank">url variants</a>
    - Interactive test page for generating URL variants.
    - Enter any URL and click Generate to see all variants (Original, With Fragment, Clean, Root, Host).
    - Duplicate variants are visually indicated with reduced opacity and gray background.
