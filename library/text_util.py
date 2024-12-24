from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
import logging
import re
from typing import Any
from urllib.parse import urlparse
import yaml

from bs4 import BeautifulSoup, element
import esprima
from magika import Magika
from nltk.corpus import wordnet as wn
from nltk.corpus import words

from library import unicode_util

"""
NOTES:
- for script.String
    - split into lines
    - line must have more than 3 words
    - dist < 0.4
    - word_pct > 0.5

"""

MAX_WORD_LEN = len("pneumonoultramicroscopicsilicovolcanoconiosis")
PUNCT_THRESHOLD = 0.3333333333333333

# Special tags for code and HTML sections.
NONE_TAG = "<!none!>"
CODE_TAG = "<!code!>"
HEAD_TAG = "<!head!>"
BODY_TAG = "<!body!>"
TEXT_TAG = "<!text!>"
SPECIAL_TAG_LEN = 8
SPECIAL_TAGS = set([CODE_TAG, HEAD_TAG, BODY_TAG, TEXT_TAG])

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# Match opening and closing HTML tags (roughly)
START_TAG_REGEX = re.compile(r"<([a-zA-Z]+[1-6]?)", flags=re.MULTILINE)
END_TAG_REGEX = re.compile(r"<\/([a-zA-Z]+[1-6]?)>", flags=re.MULTILINE)


def split_special_tag(s: str) -> tuple[str, str]:
    tag = s[0:SPECIAL_TAG_LEN]
    other = s[SPECIAL_TAG_LEN:]

    if tag in SPECIAL_TAGS:
        return tag, other

    return '', s


# Build set of nltk words for lookups.
mgk = Magika()
nltk_words = set([x.lower() for x in words.words()])


def nvl(v: Any, default: Any) -> Any:
    if v is None:
        return default
    return v


def strip_quotes(s: str) -> str:
    """Strip leading and trailing single or double quotes."""
    # Remove whitespace
    s = s.strip()

    # Remove leading and trailing quotes.
    if s[0] == "'" and s[-1] == "'":
        s = s[1:-1]
    elif s[0] == '"' and s[-1] == '"':
        s = s[1:-1]

    # Strip whitespace again.
    return s.strip()


def eval_script_text(s: str) -> str:
    """Return a clean version of text with entities evaluated. 
    This is useful from text from script tags.
    """

    new_s = strip_quotes(s)

    # Use YAML to evaluate strings.
    try:
        # Try double quotes.
        yaml_text = f'data: "{new_s}"'
        x = yaml.load(yaml_text, Loader=yaml.Loader)
        return x['data']
    except Exception:
        pass

    try:
        # Try single quotes.
        yaml_text = f"data: '{new_s}'"
        x = yaml.load(yaml_text, Loader=yaml.Loader)
        return x['data']
    except Exception:
        pass

    # Nothing worked, revert to original text.
    return s


def is_word(s: str) -> bool:
    """Returns True if the string is a word."""

    # Check if string is a number.
    try:
        float(s)
        return False
    except ValueError:
        pass

    if s.lower() in nltk_words:
        return True
    elif len(wn.synsets(s)):
        return True

    return False


def like_html(s: str) -> bool:
    """Returns true if string looks like HTML."""

    # Collect opening and closing tags.
    tags = {}
    for m in START_TAG_REGEX.finditer(s):
        tags[m.start()] = ('<', m.group(1))

    for m in END_TAG_REGEX.finditer(s):
        tags[m.start()] = ('>', m.group(1))

    if len(tags) < 2:
        return False

    # Match opening and closing tags.
    tag_stack = []
    unmatched = []
    for k in sorted(tags.keys()):
        op, name = tags[k]
        name = name.lower()

        if op == '<':
            tag_stack.append(name)
        elif op == '>':
            last = tag_stack.pop()
            while last != name and len(tag_stack) > 0:
                unmatched.append(last)
                last = tag_stack.pop()

    # HTML-like if 95% of tags matched.
    return (len(unmatched) / len(tags)) < 0.05


def like_email(s: str) -> bool:
    """NOTE: regex seems to be more accurate than spacy.like_email"""
    new_text = unicode_util.strip_not_alnum(s)
    return bool(EMAIL_REGEX.match(new_text))


def like_url(s: str) -> bool:
    """NOTE: urlparse seems to be more accurate than spacy.like_url"""
    # Count tokens using a simple split. There should only be one.
    new_text = unicode_util.strip_not_alnum(s)
    tokens = new_text.split()
    if len(tokens) > 1:
        return False

    try:
        u = urlparse(new_text)
        return all([u.scheme, u.netloc])
    except Exception:
        return False


class WordCategory(Enum):
    NLTK_WORDS = 1
    NLTK_SYNSETS = 2
    LIKE_URL = 3
    LIKE_EMAIL = 4


def categorize_word(s: str) -> WordCategory:
    """Return the category of a word or an empty string if it is not a word."""

    new_text = s.strip()

    # If text is a number, do not count as a word.
    try:
        float(new_text)
        return None
    except ValueError:
        pass

    # Check if word exists in nltk.
    if new_text.lower() in nltk_words:
        return WordCategory.NLTK_WORDS
    elif len(wn.synsets(new_text)) > 0:
        return WordCategory.NLTK_SYNSETS
    elif like_url(new_text):
        return WordCategory.LIKE_URL
    elif like_email(new_text):
        return WordCategory.LIKE_EMAIL

    return None


@dataclass
class SoupToken:
    """A single token from an element string."""
    text: str
    word_category: WordCategory = None

    def __post_init__(self):
        # Special tags are kept and do not need further analysis.
        self.word_category = categorize_word(self.text)

    def is_word(self) -> bool:
        return self.word_category is not None


@dataclass
class SoupLine:
    """A single line of text from a SoupElem."""
    parent: 'SoupElem'
    name: str
    text: str
    keep: bool = True
    category_counter: Counter = field(default_factory=Counter)
    category_tensor: list[float] = field(default_factory=list)
    standard_dist: float = None
    tokens: list[SoupToken] = field(default_factory=list)
    word_count: int = 0
    longest_run: int = 0

    def __post_init__(self):
        """Analyze the text after initialization."""

        # Keep anything that is not from a script by default.
        if self.name == 'script.String':
            self.keep = False
        elif self.parent is not None:
            if self.parent.name == 'option':
                self.keep = False

        # Strip whitespace except for special tags.
        if self.parent is not None and self.parent.name in (
                'pre', 'code', 'span', 'br', 'hr', 'p'):
            self.keep = True
        else:
            self.text = self.text.strip()
            if self.text == "":
                # Blank line
                return

        # Count unicode major categories in text.
        self.longest_run = unicode_util.longest_run(self.text)
        self.category_counter = unicode_util.count_categories(self.text)
        self.category_tensor = unicode_util.category_tensor(
            self.category_counter)
        self.standard_dist = unicode_util.standard_distance(
            self.category_counter)

        self.word_count = 0
        tokens = self.text.split()
        for tok in tokens:
            new_token = SoupToken(tok)
            self.tokens.append(new_token)
            self.word_count += int(new_token.is_word())

        # For a script.String, only keep if the following criteria
        # are satisfied.
        if self.name == 'script.String':
            if self.longest_run > MAX_WORD_LEN:
                self.keep = False
            elif (self.word_count > 2 and self.standard_dist < 0.4
                    and self.word_pct() > 0.5):
                self.keep = True

    def word_pct(self) -> float:
        if len(self.tokens) > 0:
            return self.word_count / len(self.tokens)
        return 0.0

    def __str__(self) -> str:
        return self.text


@dataclass
class SoupElem:
    """A string token from a soup tree."""
    depth: int
    parent: 'SoupElem'
    name: str
    text: str
    keep: bool = False
    special_tag: str = ""
    lines: list[str] = field(default_factory=list)
    attrs: dict[str, str] = field(default_factory=dict)

    token_count: int = 0
    word_count: int = 0

    category_counter: Counter = field(default_factory=Counter)
    category_tensor: list[float] = field(default_factory=list)
    min_standard_dist: float = None
    max_standard_dist: float = None
    max_longest_run: int = 0

    magika_type: str = "none/none"

    def __post_init__(self):
        # Identify special tags.
        tag, other = split_special_tag(self.text)
        self.special_tag = tag
        if self.special_tag != "":
            self.text = other
        elif self.name in ('pre', 'code', 'span', 'br', 'hr', 'p'):
            self.keep = True
            self.text = "\n"

        m = mgk.identify_bytes(self.text.encode())
        self.magika_type = f"{m.output.group}/{m.output.ct_label}"

        for line in self.text.splitlines():
            new_line = SoupLine(self.parent, self.name, line)
            self.lines.append(new_line)

            self.word_count += new_line.word_count
            self.token_count += len(new_line.tokens)
            self.category_counter.update(new_line.category_counter)

            if self.min_standard_dist is None:
                self.min_standard_dist = new_line.standard_dist
                self.max_standard_dist = new_line.standard_dist
            elif new_line.standard_dist is not None:
                self.min_standard_dist = min(
                    self.min_standard_dist,
                    new_line.standard_dist,
                )
                self.max_standard_dist = max(
                    self.max_standard_dist,
                    new_line.standard_dist,
                )

            self.max_longest_run = max(
                new_line.longest_run,
                self.max_longest_run,
            )

            if new_line.keep:
                self.keep = True

        self.category_tensor = unicode_util.category_tensor(
            self.category_counter)

    def __str__(self) -> str:
        n = f"<{self.name}>" if self.name is not None else NONE_TAG

        return (
            f"{self.depth:6d} {n:20s} "
            f"L={self.line_count:3d} "
            f"W={self.word_count:3d}/{self.token_count:3d}/{self.word_pct():.2f} "
            f"C={self.alnum_count:3d}/{self.char_count:3d}/{self.alnum_pct():.2f} "
            f"{self.magika_type:20s} | {self.text}"
        )
        # f"words:{self.word_count:3d}/{self.tok_count():3d} "
        # f"({self.word_pct():3.2f}) "
        # f"alnum:{self.alnum_count:3d}/{self.char_count:3d} "
        # f"({self.alnum_pct():3.2f}) "
        # f"{self.magika_type} "
        # f"{self.text}")

    def get_name(self) -> str:
        if self.name is None:
            return NONE_TAG

        # Check for attributes.
        if self.name not in ('link', 'script'):
            attr_list = []
            for k in ('href', 'src', 'alt', 'title', 'caption', 'aria-label', 'longdesc'):
                if k in self.attrs:
                    v = self.attrs[k].strip()
                    if v:
                        attr_list.append(f'{k}="{v}"')

            if attr_list:
                return f"{self.name} {' '.join(attr_list)}".strip()

        return self.name
    
    def line_count(self) -> int:
        return len(self.lines)
    
    def category_str(self) -> str:
        return unicode_util.category_str(self.category_counter)

    def word_pct(self) -> float:
        """Return percentage of tokens that are words."""
        if self.token_count > 0:
            return self.word_count / self.token_count
        return 0.0

    def alnum_pct(self) -> float:
        """Return percentage of characters that are alphanumeric."""
        if self.char_count > 0:
            return self.alnum_count / self.char_count
        return 0.0


def walk_soup_tree_strings(
    elem: element.Tag,
    depth: int = 0,
    parent: SoupElem = None,
) -> list[SoupElem]:
    """Walk the HTML soup tree and collect a list of SoupElems."""

    tree_elem = []

    if elem.name == 'script':
        script_parent =  SoupElem(
            depth, parent, elem.name, "",
            attrs=elem.attrs,
        )
        tree_elem.append(script_parent)

        elem_text = elem.text.strip()
        if elem_text:
            # Tokenize the script and extract the String tokens.
            try:
                tokens = esprima.tokenize(elem_text)
                for tok in tokens:
                    if tok.type == "String":
                        tok_value = tok.value.strip()
                        if tok_value != "":
                            script_string_elem = SoupElem(
                                depth+1,
                                script_parent,
                                'script.String',
                                tok_value
                            )

                            tok_value = eval_script_text(tok_value)

                            # Try to parse text as HTML?
                            script_elem = []
                            if like_html(tok_value):
                                # Probable HTML.
                                script_soup = BeautifulSoup(tok_value, "html.parser")
                                script_elem = walk_soup_tree_strings(
                                    script_soup, depth + 2,
                                    parent=script_string_elem,
                                )
                                tok_value = ""

                            tree_elem.append(script_string_elem)
                            if tok_value == "":
                                script_string_elem.text = tok_value
                                tree_elem.extend(script_elem)
            except Exception:
                tree_elem.append(
                    SoupElem(
                        depth+1,
                        script_parent,
                        'script.String',
                        elem_text)
                )


    if hasattr(elem, 'children'):
        this_elem = SoupElem(
            depth, parent, elem.name, "",
            attrs=elem.attrs,
        )
        tree_elem.append(this_elem)

        # Iterate through children.
        child_elem_collector = []
        for child_index, child in enumerate(elem.children):
            child_elem = walk_soup_tree_strings(
                child, depth + 1,
                parent=parent)
            child_elem_collector.extend(child_elem)
            
        # Collect text for inline tags.
        if this_elem.name in ('span', 'code', 'pre',):
            collect_text = []
            for el in child_elem_collector:
                if el.name == 'div':
                    collect_text.append(' ')
                else:
                    collect_text.append(el.text)

            this_elem.text = "".join(collect_text)
            if this_elem.name in ('code', 'pre'):
                this_elem.text += "\n"
        else:
            tree_elem.extend(child_elem_collector)
    elif elem.text != "":
        # No children, but has text.
        tree_elem.append(
            SoupElem(
                depth,
                parent,
                elem.name,
                elem.text,
            )
        )

    return tree_elem
