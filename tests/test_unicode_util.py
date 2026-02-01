"""
Tests for library/unicode_util.py

Tests Unicode category analysis and utility functions.
"""

import pytest
from library.unicode_util import (
    GENERAL_CATEGORY_NAMES,
    CATEGORY_NAMES,
)


class TestGeneralCategoryNames:
    """Tests for GENERAL_CATEGORY_NAMES mapping."""

    def test_letter_categories(self):
        """Test that letter categories are properly defined."""
        assert GENERAL_CATEGORY_NAMES['Lu'] == 'Letter, Uppercase'
        assert GENERAL_CATEGORY_NAMES['Ll'] == 'Letter, Lowercase'
        assert GENERAL_CATEGORY_NAMES['Lt'] == 'Letter, Titlecase'
        assert GENERAL_CATEGORY_NAMES['Lm'] == 'Letter, Modifier'
        assert GENERAL_CATEGORY_NAMES['Lo'] == 'Letter, Other'

    def test_mark_categories(self):
        """Test that mark categories are properly defined."""
        assert GENERAL_CATEGORY_NAMES['Mn'] == 'Mark, Nonspacing'
        assert GENERAL_CATEGORY_NAMES['Mc'] == 'Mark, Spacing Combining'
        assert GENERAL_CATEGORY_NAMES['Me'] == 'Mark, Enclosing'

    def test_number_categories(self):
        """Test that number categories are properly defined."""
        assert GENERAL_CATEGORY_NAMES['Nd'] == 'Number, Decimal Digit'
        assert GENERAL_CATEGORY_NAMES['Nl'] == 'Number, Letter'
        assert GENERAL_CATEGORY_NAMES['No'] == 'Number, Other'

    def test_separator_categories(self):
        """Test that separator categories are properly defined."""
        assert GENERAL_CATEGORY_NAMES['Zs'] == 'Separator, Space'
        assert GENERAL_CATEGORY_NAMES['Zl'] == 'Separator, Line'
        assert GENERAL_CATEGORY_NAMES['Zp'] == 'Separator, Paragraph'

    def test_symbol_categories(self):
        """Test that symbol categories are properly defined."""
        assert GENERAL_CATEGORY_NAMES['Sm'] == 'Symbol, Math'
        assert GENERAL_CATEGORY_NAMES['Sc'] == 'Symbol, Currency'
        assert GENERAL_CATEGORY_NAMES['Sk'] == 'Symbol, Modifier'
        assert GENERAL_CATEGORY_NAMES['So'] == 'Symbol, Other'

    def test_punctuation_categories(self):
        """Test that punctuation categories are properly defined."""
        assert GENERAL_CATEGORY_NAMES['Pc'] == 'Punctuation, Connector'
        assert GENERAL_CATEGORY_NAMES['Pd'] == 'Punctuation, Dash'
        assert GENERAL_CATEGORY_NAMES['Ps'] == 'Punctuation, Open'
        assert GENERAL_CATEGORY_NAMES['Pe'] == 'Punctuation, Close'
        assert GENERAL_CATEGORY_NAMES['Po'] == 'Punctuation, Other'

    def test_other_categories(self):
        """Test that other categories are properly defined."""
        assert GENERAL_CATEGORY_NAMES['Cc'] == 'Other, Control'
        assert GENERAL_CATEGORY_NAMES['Cf'] == 'Other, Format'
        assert GENERAL_CATEGORY_NAMES['Cs'] == 'Other, Surrogate'
        assert GENERAL_CATEGORY_NAMES['Co'] == 'Other, Private Use'
        assert GENERAL_CATEGORY_NAMES['Cn'] == 'Other, Not Assigned'

    def test_all_categories_accounted_for(self):
        """Test that all 30 Unicode general categories are defined."""
        assert len(GENERAL_CATEGORY_NAMES) == 30

    def test_values_are_strings(self):
        """Test that all category values are non-empty strings."""
        for key, value in GENERAL_CATEGORY_NAMES.items():
            assert isinstance(key, str), f"Key {key} is not a string"
            assert isinstance(value, str), f"Value for {key} is not a string"
            assert len(value) > 0, f"Value for {key} is empty"


class TestCategoryNames:
    """Tests for CATEGORY_NAMES ordered dictionary."""

    def test_category_names_order(self):
        """Test that category names are in correct frequency order."""
        keys = list(CATEGORY_NAMES.keys())
        assert keys == ['L', 'Z', 'P', 'S', 'N', 'M', 'C']

    def test_category_names_values(self):
        """Test category name values."""
        assert CATEGORY_NAMES['L'] == 'Letter'
        assert CATEGORY_NAMES['Z'] == 'Separator'
        assert CATEGORY_NAMES['P'] == 'Punctuation'
        assert CATEGORY_NAMES['S'] == 'Symbol'
        assert CATEGORY_NAMES['N'] == 'Number'
        assert CATEGORY_NAMES['M'] == 'Mark'
        assert CATEGORY_NAMES['C'] == 'Other'

    def test_seven_categories_total(self):
        """Test that there are exactly 7 major categories."""
        assert len(CATEGORY_NAMES) == 7

    def test_all_values_are_strings(self):
        """Test that all values are non-empty strings."""
        for key, value in CATEGORY_NAMES.items():
            assert isinstance(value, str)
            assert len(value) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
