# web-tool
Utilities for extracting information from web pages.

[![Docker Hub](https://img.shields.io/docker/v/dockmann/web-tool?label=dockmann%2Fweb-tool)](https://hub.docker.com/r/dockmann/web-tool) [![GitHub](https://img.shields.io/badge/GitHub-gitmanntoo%2Fweb--tool-blue)](https://github.com/gitmanntoo/web-tool)

Tools use the following pattern:

1. A bookmarklet captures information from a web page and copies it into the clipboard.
2. An endpoint in the web-tool processes the clipboard and returns the result.

All endpoints are hosted at <http://localhost:8532>.

## Bookmarklet Endpoints

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
    - Displays the HTML source of the page using plain text.
    - This should always work.

## Debug Endpoints

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

- <a href="http://localhost:8532/debug/inline-image" target="_blank">inline image</a>
    - Convert pasted or uploaded images to inline base64 `<img>` tags.
    - Adjustable output height; useful for generating favicon-style inline images.

- <a href="http://localhost:8532/test-pages-interactive" target="_blank">test pages</a>
    - <strong><a href="http://localhost:8532/test-pages-interactive" target="_blank">Interactive test page builder</a></strong> — configure parameters and load test pages in the browser
    - <a href="http://localhost:8532/test-page" target="_blank">Raw test page</a> — parameterized endpoint for direct URL access
    - Parameters: `title`, `fragment`, `anchor-fragment`, `wrap-fragment`, `url-has-parens`, `url-has-brackets`, `url-has-space`, `unicode-content`, `emoji-content`

## Favicon Cache

web-tool uses a three-tier favicon cache, checked in priority order:

1. **User Overrides** (`static/favicon-overrides.yml`) — highest priority, manually added via UI or file edit
2. **App Defaults** (`static/favicon.yml`) — curated favicons shipped with the app
3. **Auto-discovered** (`local-cache/favicon.yml`, or `/data/favicon.yml` in containers) — cached on first use

Lookup searches by progressively broader keys (`docs.google.com/spreadsheets` → `docs.google.com` → `google.com`), checking overrides first, then defaults, then discovered. First match wins.

### Inline Images

Overrides can store favicons as inline base64 PNGs, avoiding remote fetches at render time:

<pre>
# Plain URL
crummy.com: https://www.crummy.com/favicon.ico

# Inline image (added via UI with "Save as inline" checked)
ibm.com:
  url: https://www.ibm.com/content/dam/adobe-cms/default/images/icon-512x512.png
  inline_image:
    data_url: data:image/png;base64,iVBORw0KGgo...
    width: 20
    height: 20
</pre>

Inline images are resized to 20px height. Only overrides support inline images; defaults and auto-discovered entries store plain URLs.

### Adding Overrides

**Via UI:** Navigate to `/mirror-favicons?url=<page_url>`, click "Add to Overrides" on any favicon. Check "Save as inline" to embed the image as base64.

**Via file edit:** Add entries to `static/favicon-overrides.yml`. Keys are normalized domains (`www.` is stripped):

- **Domain only**: `example.com` — matches all pages on the domain
- **Domain + path**: `example.com/docs` — matches the first path segment

## Running with Docker

Stops any running container, pulls the latest image, and starts web-tool with auto-restart.

- `-d` runs the container in the background
- `--restart always` restarts the container if it crashes or when Docker restarts
- `-p ${PORT}:8532` maps a host port to the container's port 8532
- `-v ${DATA_DIR}:/data` persists the favicon cache to the host; omit to skip persistence
- `mkdir -p` creates the data directory before Docker can create it as root

<pre>
PORT=8532
DATA_DIR=$(pwd)/web-tool

# Create data directory owned by current user so appuser (uid 1000) can write to it.
mkdir -p "${DATA_DIR}"

# Stop and remove the currently running web-tool, ignoring errors.
docker stop web-tool || true
docker rm web-tool || true

# Download the latest image and run it.
docker pull dockmann/web-tool
docker run -d --restart always \
  -p ${PORT}:8532 \
  -v ${DATA_DIR}:/data \
  --name web-tool dockmann/web-tool
</pre>

## Building and Publishing

To build and push the Docker image locally (replaces the deprecated GitHub Actions workflow):

**Prerequisites:**
- Docker with buildx support
- Docker Hub access token ([create one here](https://hub.docker.com/settings/security))

**Setup:**
<pre>
export DOCKERHUB_USERNAME=dockmann
export DOCKERHUB_TOKEN=your-token-here
</pre>

**Commands:**

| Command | Description |
|---------|-------------|
| `make docker-release` | Full release: build, push, and update Docker Hub description |
| `make docker-push` | Build and push multi-platform image only |
| `make docker-describe` | Update Docker Hub description from README.md |

**Versioning:**
- Tagged commits (e.g., `v1.0.1`) → image tagged as `1.0.1`
- Untagged commits → image tagged as `dev-<short-sha>` (e.g., `dev-abc123`)

**Example workflow:**
<pre>
# Create a release tag
git tag v1.0.1
git push origin v1.0.1

# Build and push with version tag
make docker-release
</pre>

## Dependencies

- [Flask](https://flask.palletsprojects.com/) for the web framework.
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) for HTML parsing.
- [lxml](https://lxml.de/) for HTML and XML processing.
- [CairoSVG](https://cairosvg.org/) for SVG conversion.
- [Magika](https://google.github.io/magika/) for content type identification.
- [NLTK :: Natural Language Toolkit](https://www.nltk.org/) for word identification.
- [Pillow](https://pillow.readthedocs.io/en/stable/) for ICO conversion.
- [PyMuPDF](https://pymupdf.readthedocs.io/) for PDF processing.
- [Prism](https://prismjs.com/index.html) for syntax highlighting in HTML pages.

