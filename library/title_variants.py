"""Title variant generation and deduplication utilities."""

from library.text_format import path_safe_filename, text_ascii_only, text_with_ascii_and_emojis


class TitleVariants:
    """Container for title variants with different transformations."""

    def __init__(self, original: str):
        """
        Generate all title variants from an original title string.

        Args:
            original: The original title text
        """
        self.original = original
        self.ascii_and_emojis = text_with_ascii_and_emojis(original)
        self.ascii_only = text_ascii_only(original)
        self.path_safe = path_safe_filename(original)

    def __repr__(self) -> str:
        return (
            f"TitleVariants(\n"
            f"  original={self.original!r},\n"
            f"  ascii_and_emojis={self.ascii_and_emojis!r},\n"
            f"  ascii_only={self.ascii_only!r},\n"
            f"  path_safe={self.path_safe!r}\n"
            f")"
        )


def deduplicate_variants(variants: list[tuple[str, str]]) -> list[dict]:
    """Deduplicate variant tuples, tracking duplicates by value.

    Args:
        variants: List of (value, label) tuples.

    Returns:
        List of dicts with 'value', 'label', and 'is_duplicate' keys.
        Duplicate labels are skipped. Duplicate values are marked.
    """
    seen_labels = set()
    seen_values = set()
    result = []
    for value, label in variants:
        if label in seen_labels:
            continue
        is_duplicate = value in seen_values
        result.append({"value": value, "label": label, "is_duplicate": is_duplicate})
        seen_labels.add(label)
        seen_values.add(value)
    return result
