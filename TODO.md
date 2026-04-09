# TODO — Upcoming Work

## PR: Docker improvements

- [ ] Add script to run docker (e.g., `make docker-run` or a dedicated shell script)

## PR: Inline image enhancements

- [ ] Add width to images (currently only `height` is set on inline `<img>` tags; adding `width` can prevent layout shift)

## PR: Fragment title handling

- [ ] Fix fragment title (title extraction does not currently handle non-HTML content — see `library/util.py:369`)
