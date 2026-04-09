"""
Tests for fragment variant generation in mirror-links endpoint.

Tests the fragment_variants list creation with duplicate detection,
verifying that is_duplicate is set correctly when fragment_text
equals fragment (fallback case).
"""


class TestFragmentVariants:
    """Tests for fragment variant generation."""

    def _make_fragment_variants(self, fragment, fragment_text):
        """
        Helper to build fragment_variants like the mirror-links endpoint does.
        """
        fragment_variants_data = [
            ("", "None"),
            (fragment, "Fragment"),
            (fragment_text, "Fragment Text"),
        ]

        seen_values = set()
        result = []
        for fragment_value, label in fragment_variants_data:
            value = fragment_value if label != "None" else ""
            is_duplicate = value in seen_values and label != "None"
            result.append({"value": value, "label": label, "is_duplicate": is_duplicate})
            seen_values.add(value)
        return result

    def test_none_not_marked_duplicate(self):
        """None option should never be marked as duplicate."""
        variants = self._make_fragment_variants("section1", "Section One")
        none_variant = next(v for v in variants if v["label"] == "None")
        assert none_variant["is_duplicate"] is False

    def test_fragment_not_duplicate_when_unique(self):
        """Fragment should not be duplicate when different from None."""
        variants = self._make_fragment_variants("section1", "Section One")
        fragment_variant = next(v for v in variants if v["label"] == "Fragment")
        assert fragment_variant["is_duplicate"] is False

    def test_fragment_text_duplicate_when_equal_to_fragment(self):
        """Fragment Text should be marked duplicate when equal to Fragment."""
        variants = self._make_fragment_variants("section1", "section1")
        fragment_text_variant = next(v for v in variants if v["label"] == "Fragment Text")
        assert fragment_text_variant["is_duplicate"] is True

    def test_fragment_text_not_duplicate_when_different(self):
        """Fragment Text should not be duplicate when different from Fragment."""
        variants = self._make_fragment_variants("section1", "Section One")
        fragment_text_variant = next(v for v in variants if v["label"] == "Fragment Text")
        assert fragment_text_variant["is_duplicate"] is False

    def test_all_three_options_present(self):
        """All three options (None, Fragment, Fragment Text) should be present."""
        variants = self._make_fragment_variants("section1", "Section One")
        labels = {v["label"] for v in variants}
        assert labels == {"None", "Fragment", "Fragment Text"}

    def test_values_correct(self):
        """Values should be correctly assigned to each option."""
        variants = self._make_fragment_variants("my-fragment", "My Fragment")
        none = next(v for v in variants if v["label"] == "None")
        fragment = next(v for v in variants if v["label"] == "Fragment")
        fragment_text = next(v for v in variants if v["label"] == "Fragment Text")

        assert none["value"] == ""
        assert fragment["value"] == "my-fragment"
        assert fragment_text["value"] == "My Fragment"

    def test_empty_fragment_and_text(self):
        """
        Fragment and Fragment Text are both empty.
        All three options have empty values, so Fragment and Fragment Text
        are duplicates of None.
        """
        variants = self._make_fragment_variants("", "")
        none = next(v for v in variants if v["label"] == "None")
        fragment = next(v for v in variants if v["label"] == "Fragment")
        fragment_text = next(v for v in variants if v["label"] == "Fragment Text")

        # None is not marked duplicate (by design - it's the reference)
        assert none["is_duplicate"] is False
        # Fragment is duplicate of None (both empty = no fragment)
        assert fragment["is_duplicate"] is True
        # Fragment Text is also duplicate of None
        assert fragment_text["is_duplicate"] is True

    def test_pydantic_style_fragment_falls_back_to_self(self):
        """
        Simulates pydantic URL case where fragment_text equals fragment
        because resolver couldn't find descriptive text.
        """
        fragment = "pydantic.json_schema.GenerateJsonSchema.ValidationsMapping"
        variants = self._make_fragment_variants(fragment, fragment)
        fragment_variant = next(v for v in variants if v["label"] == "Fragment")
        fragment_text_variant = next(v for v in variants if v["label"] == "Fragment Text")

        assert fragment_variant["value"] == fragment
        assert fragment_text_variant["value"] == fragment
        assert fragment_text_variant["is_duplicate"] is True
