# Known Issues and Future Work

This document captures issues discovered during development sessions that are not directly related to the current task.

**Purpose:** Keep work focused on one task at a time. When you notice something that needs fixing but isn't part of what you're currently working on, capture it here rather than addressing it immediately. This prevents scope creep and keeps PRs focused.

**When to add items:**
- Bugs discovered that aren't related to the current task
- Improvements that would be nice but aren't required now
- Refactoring opportunities noticed while reading code
- Tooling issues or limitations encountered

**When NOT to add items:**
- Issues that ARE part of the current task (fix those now)
- Critical/blocking issues that prevent completion (address immediately)

## Tooling Issues

### GitHub CLI File Attachments
**Date:** 2026-04-19
**Session:** Housekeeping cleanup PR

**Issue:** The `gh` CLI `pr create --attach` flag is not supported. When attempting to attach the superpowers implementation plan using `gh pr comment 52 --body-file`, the content was pasted as inline text rather than as a proper file attachment.

**Workaround:** The plan content is accessible in the PR comment as inline text. For proper file attachments, use the GitHub web UI drag-and-drop feature.

**Resolution Options:**
1. Leave as-is - content is accessible in the comment
2. Use web UI for future attachments: `gh pr view <num> --web`
3. Explore GitHub API for programmatic file attachments
