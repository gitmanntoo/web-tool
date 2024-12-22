from collections import Counter, OrderedDict
import unicodedata


# Define a dictionary of unicode category names 
# From: [Chapter 4 – Unicode 16.0.0](https://www.unicode.org/versions/Unicode16.0.0/core-spec/chapter-4/#G124142)
GENERAL_CATEGORY_NAMES = {
    'Lu': 'Letter, Uppercase',
    'Ll': 'Letter, Lowercase',
    'Lt': 'Letter, Titlecase',
    'Lm': 'Letter, Modifier',
    'Lo': 'Letter, Other',
    'Mn': 'Mark, Nonspacing',
    'Mc': 'Mark, Spacing Combining',
    'Me': 'Mark, Enclosing',
    'Nd': 'Number, Decimal Digit',
    'Nl': 'Number, Letter',
    'No': 'Number, Other',
    'Zs': 'Separator, Space',
    'Zl': 'Separator, Line',
    'Zp': 'Separator, Paragraph',
    'Cc': 'Other, Control',
    'Cf': 'Other, Format',
    'Cs': 'Other, Surrogate',
    'Co': 'Other, Private Use',
    'Cn': 'Other, Not Assigned',
    'Sm': 'Symbol, Math',
    'Sc': 'Symbol, Currency',
    'Sk': 'Symbol, Modifier',
    'So': 'Symbol, Other',
    'Pc': 'Punctuation, Connector',
    'Pd': 'Punctuation, Dash',
    'Ps': 'Punctuation, Open',
    'Pe': 'Punctuation, Close',
    'Pi': 'Punctuation, Initial Quote',
    'Pf': 'Punctuation, Final Quote',
    'Po': 'Punctuation, Other'
}

# Category names from most to least frequent in languages.
CATEGORY_NAMES = OrderedDict([
    ('L', 'Letter'),
    ('Z', 'Separator'),
    ('P', 'Punctuation'),
    ('S', 'Symbol'),
    ('N', 'Number'),
    ('M', 'Mark'),
    ('C', 'Other'),
])

# Typical values for english tensor.
STANDARD_TENSOR = [0.85, 0.12, 0.3, 0, 0, 0, 0, ]

# Map from GENERAL_CATEGORY to parent CATEGORY.
CATEGORY_MAP = {
    x:x[0] for x in GENERAL_CATEGORY_NAMES
}

# Define some sets for faster categorization.
# Alphanumeric characters.
ALNUM = {
    x for x in GENERAL_CATEGORY_NAMES
    if x[0] in ('L', 'N')
}

NOT_ALNUM = {
    x for x in GENERAL_CATEGORY_NAMES
    if x not in ALNUM
}


def is_alnum(c: str) -> bool:
    """True if the character is a unicode letter or number."""
    return unicodedata.category(c) in ALNUM


def is_not_alnum(c: str) -> bool:
    """True if the character is not a unicode letter or number."""
    return unicodedata.category(c) in NOT_ALNUM


def strip_not_alnum(s: str) -> str:
    """
    Strip punctuation from the start and end of a string in a Unicode-safe manner.

    Parameters:
    s (str): The input string.

    Returns:
    str: The string with punctuation stripped from the start and end.
    """
    # Strip punctuation from the start and end of the string
    start = 0
    while start < len(s) and is_not_alnum(s[start]):
        start += 1
    end = len(s) - 1
    while end >= 0 and is_not_alnum(s[end]):
        end -= 1

    # Return the stripped string
    return s[start:end+1]


def count_categories(s: str) -> Counter:
    counts = Counter()
    for c in s:
        cat = unicodedata.category(c)
        counts[CATEGORY_MAP[cat]] += 1

    return counts


def category_tensor(c: Counter) -> list[float]:
    """Ratio of category to total in order of CATEGORY_NAMES."""

    out = []
    for k in CATEGORY_NAMES:
        if c.total() > 0:
            out.append(c[k] / c.total())
        else:
            out.append(0)

    return out


def category_str(c: Counter) -> str:
    """Convert categories into a string with each value between 0 and 99.
    """
    out_pct = []
    for k in CATEGORY_NAMES:
        pct = 0
        if c.total() > 0:
            pct = int(100 * c[k] / c.total())
            if pct == 100:
                pct = 99

            out_pct.append(f"{pct:2d}")

    return " ".join(out_pct)


def standard_distance(c: Counter) -> float:
    """Calculate the Euclidian distance between the counts 
    and the STANDARD_TENSOR.
    """
    cat_tensor = category_tensor(c)

    # Sum of squared distances.
    s = 0
    for i, t in enumerate(cat_tensor):
        s += (t - STANDARD_TENSOR[i]) ** 2

    # Return square root of sum.
    return s ** 0.5
