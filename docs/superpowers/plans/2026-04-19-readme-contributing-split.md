# README / CONTRIBUTING Split Plan

## Overview

Separate user-facing content in README.md from developer-facing content by creating CONTRIBUTING.md.

## Steps

### 1. Create CONTRIBUTING.md

Create `CONTRIBUTING.md` at repo root containing:

- Header: "Contributing to web-tool" with brief intro
- **Building and Publishing** — moved from README.md lines 148-173:
  - Prerequisites, setup, commands table, versioning
- **Release Workflows** — moved from README.md lines 174-215:
  - Option 1 (Local Tagging) and Option 2 (GitHub Releases)
- **Dependencies** — moved from README.md lines 216-227:
  - Full dependency list with links

### 2. Update README.md

- Remove "Building and Publishing" section (lines 148-173)
- Remove "Release Workflows" section (lines 174-215)
- Remove "Dependencies" section (lines 216-227)
- Add trailing line: "For development and release instructions, see [CONTRIBUTING.md](CONTRIBUTING.md)."

### 3. Verify

- Confirm README.md is coherent for end users
- Confirm CONTRIBUTING.md contains all developer content without duplication

## Spec

docs/superpowers/specs/2026-04-19-readme-contributing-split-design.md
