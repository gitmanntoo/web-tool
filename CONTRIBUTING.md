# Contributing to web-tool

This document is the developer reference for building, releasing, and contributing to web-tool.

## Building and Publishing

To build and push the Docker image locally:

**Prerequisites:**
- Docker with buildx support
- Docker Hub access token ([create one here](https://hub.docker.com/settings/security))

**Setup:**
<pre>
export DOCKERHUB_USERNAME=your-username
export DOCKERHUB_TOKEN=your-token-here
</pre>

**Commands:**

| Command | Description |
|---------|-------------|
| `make docker-release` | Build and push multi-platform image (versioned) |
| `make docker-push` | Build and push multi-platform image only |

**Versioning:**
- Tagged commits (e.g., `v1.0.1`) → image tagged as `1.0.1`
- Untagged commits → image tagged as `dev-<short-sha>` (e.g., `dev-abc123`)

### Release Workflows

You can create release tags either locally or via GitHub Releases. Both workflows use the same `make docker-release` command.

**Option 1: Local Tagging**

Create and push the tag locally, then build:

<pre>
# Create and push the tag
git tag v1.0.1
git push origin v1.0.1

# Build and push with version tag (run at the tagged commit)
make docker-release
</pre>

**Option 2: GitHub Releases**

Create a release via the GitHub UI, then build locally:

<pre>
# 1. Go to https://github.com/gitmanntoo/web-tool/releases/new
# 2. Click "Choose a tag" → type "v1.0.1" → click "Create new tag"
# 3. Fill in release title and description
# 4. Click "Publish release"

# 5. Pull the new tag locally
git fetch origin --tags

# 6. Check out the tagged commit
git checkout v1.0.1
# Note: This puts you in a 'detached HEAD' state. This is expected — you're
# viewing the code at the tagged commit, not on a branch. After building, you
# can return to main with: git switch -
# Or create a worktree for this version: git worktree add .worktrees/v1.0.1 v1.0.1

# 7. Build and push with version tag
make docker-release
</pre>

**Note:** The GitHub Releases workflow is useful when you want to:
- Write release notes in GitHub's UI
- Have the tag creation visible in the GitHub releases list
- Separate the tagging decision from the build process

### Updating Docker Hub Description

**Important:** The Docker Hub description is no longer updated automatically. After running `make docker-release`, the terminal will display a reminder with instructions.

Update the Docker Hub description manually:

1. Go to https://hub.docker.com/r/dockmann/web-tool
2. Click the **Edit** button (pencil icon) next to the description
3. Paste the contents of `README.md`
4. Click **Save**

This ensures the Docker Hub page stays in sync with the project README.

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
