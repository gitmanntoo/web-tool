from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
import logging
import re
from urllib.parse import urlparse
import yaml

from bs4 import BeautifulSoup, element
import esprima
from magika import Magika
from nltk.corpus import wordnet as wn
from nltk.corpus import words
import spacy
import spacy.tokens

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

# HTML tags with rules for inclusion or exclusion.
HTML_RULES = {
    # Combine strings under span into one line.
    'span': 'inline',
    # Exclude option lists.
    'option': 'exclude',
}


def split_special_tag(s: str) -> tuple[str, str]:
    tag = s[0:SPECIAL_TAG_LEN]
    other = s[SPECIAL_TAG_LEN:]

    if tag in SPECIAL_TAGS:
        return tag, other

    return '', s


# Initialize spaCy and Magika.
# command line: python -m spacy download en_core_web_sm
mgk = Magika()
nlp = spacy.load("en_core_web_sm")
nltk_words = set([x.lower() for x in words.words()])


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


# def extract_text_from_html(html_text: str) -> list[str]:
#     """Extract text from HTML and return a list of strings."""
#     # Parse the HTML.
#     soup = BeautifulSoup(html_text, "html.parser")
#     # Walk the soup tree and collect text snippets from leaf nodes.
#     head_text = walk_soup_tree(soup.head)
#     body_text = walk_soup_tree(soup.body)

#     all_text = OrderedDict()

#     all_text[f"{HEAD_TAG}--- HEAD ---"] = len(head_text)
#     for k in head_text.keys():
#         all_text[k] = head_text[k]

#     all_text[f"{BODY_TAG}--- BODY ---"] = len(body_text)
#     for k in body_text.keys():
#         all_text[k] = body_text[k]

#     # Extract text from the ordered dictionary.
#     extracted_text = extract_text(all_text)
#     # Process lines in the extracted text to remove repeated empty lines.
#     out = []
#     last_line = ""
#     for text in extracted_text:
#         text_lines = text.splitlines()
#         for line in text_lines:
#             line = line.rstrip()
#             if line == "" and line == last_line:
#                 continue

#             last_line = line
#             out.append(line)

#     return "\n".join(out)


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

    u = urlparse(new_text)
    return all([u.scheme, u.netloc])


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
    """A single token from an element string.
    This combines features of nltk and spacy tokens.
    """
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
    parent_name: str
    name: str
    text: str
    keep: bool = True
    category_counts: Counter = field(default_factory=Counter)
    category_tensor: list[float] = field(default_factory=list)
    standard_dist: float = None
    tokens: list[SoupToken] = field(default_factory=list)
    word_count: int = 0

    def __post_init__(self):
        """Analyze the text after initialization."""

        # Keep anything that is not from a script by default.
        if self.name == 'script.String':
            self.keep = False
        elif HTML_RULES.get(self.parent_name) == 'exclude':
            self.keep = False

        self.text = self.text.rstrip()
        if self.text == "":
            # Blank line
            return

        # Count unicode major categories in text.
        self.category_counts = unicode_util.count_categories(self.text)
        self.category_tensor = unicode_util.category_tensor(
            self.category_counts)
        self.standard_dist = unicode_util.standard_distance(
            self.category_counts)

        self.word_count = 0
        tokens = self.text.split()
        for tok in tokens:
            new_token = SoupToken(tok)
            self.tokens.append(new_token)
            self.word_count += int(new_token.is_word())

        # For a script.String, only keep if the following criteria
        # are satisfied.
        if self.name == 'script.String':
            if self.word_count > 2 and self.standard_dist < 0.4 and self.word_pct() > 0.5:
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
    parent_name: str
    name: str
    text: str
    keep: bool = False
    special_tag: str = ""
    lines: list[str] = field(default_factory=list)

    token_count: int = 0
    word_count: int = 0
    min_standard_dist: float = None
    max_standard_dist: float = None

    char_count: int = 0
    alnum_count: int = 0
    category_counter: Counter = field(default_factory=Counter)
    char_counter: Counter = field(default_factory=Counter)

    magika_type: str = "none/none"
    tokens: list[SoupToken] = field(default_factory=list)

    def __post_init__(self):
        # Identify special tags.
        tag, other = split_special_tag(self.text)
        self.special_tag = tag
        if self.special_tag != "":
            self.text = other

        self.text = self.text.rstrip()
        if self.text == "":
            return

        for line in self.text.splitlines():
            new_line = SoupLine(self.parent_name, self.name, line)
            self.lines.append(new_line)

            self.word_count += new_line.word_count
            self.token_count += len(new_line.tokens)

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

            if new_line.keep:
                self.keep = True

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
        return NONE_TAG if self.name is None else self.name

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
    parent_name: str = '',
) -> list[SoupElem]:
    """Walk the HTML soup tree and collect a list of SoupElems."""

    if elem.name in HTML_RULES:
        parent_name = elem.name

    tree_elem = []

    if elem.name == 'script':
        tree_elem.append(
            SoupElem(depth, parent_name, elem.name, ""))

        elem_text = elem.text.strip()
        if elem_text:
            # Tokenize the script and extract the String tokens.
            tokens = esprima.tokenize(elem_text)
            for tok in tokens:
                if tok.type == "String":
                    tok_value = tok.value.strip()
                    if tok_value != "":
                        tree_elem.append(
                            SoupElem(
                                depth+1,
                                '',
                                'script.String',
                                eval_script_text(tok_value))
                        )

    if hasattr(elem, 'children'):
        tree_elem.append(SoupElem(
            depth, parent_name, elem.name, ""))

        # Iterate through children.
        for child_index, child in enumerate(elem.children):
            child_elem = walk_soup_tree_strings(
                child, depth + 1,
                parent_name=parent_name)
            tree_elem.extend(child_elem)
    elif (x := elem.text.rstrip()) != "":
        # No children, but has text.
        tree_elem.append(
            SoupElem(
                depth,
                parent_name,
                elem.name,
                x,
            )
        )

    return tree_elem


# def walk_soup_tree_strings_SAVE(
#         elem: element.Tag, depth: int = 0) -> list[SoupElem]:
#     """Walk the HTML soup tree and collect a list of SoupElems."""

#     tree_strings = []

#     # HEAD and BODY tags add special markers.
#     if elem.name == "head":
#         tree_strings.append(
#             SoupElem(depth, elem.name, f"{HEAD_TAG}--- {elem.name} ---")
#         )
#     elif elem.name == "body":
#         tree_strings.append(
#             SoupElem(depth, elem.name, f"{BODY_TAG}--- {elem.name} ---")
#         )

#     # Process tags that combine children.
#     if elem.name in ("pre", "code"):
#         elem_strings = []
#         # Pre and code tags are special blocks that should not be processed.
#         if hasattr(elem, "children"):
#             for child in elem.children:
#                 child_strings = walk_soup_tree_strings(child, depth + 1)
#                 elem_strings.extend(child_strings)
#         elif (x := elem.text.strip()) != "":
#             elem_strings.append(
#                 SoupElem(depth, TEXT_TAG, x)
#             )

#         # Combine all child strings.
#         new_text = "\n".join([
#             x.text for x in elem_strings
#         ])
#         tree_strings.append(SoupElem(depth, elem.name, new_text))

#         # elem_text = elem.get_text().strip()
#         # if elem_text:
#         #     print(elem_text)
#         #     tree_strings.append(
#         #         SoupElem(depth, elem.name, f"{CODE_TAG}{elem_text}")
#         #     )

#         return tree_strings
#     elif elem.name == "script":
#         elem_text = elem.text.strip()
#         if elem_text:
#             # Tokenize the script and extract the String tokens.
#             tokens = esprima.tokenize(elem_text)
#             for tok in tokens:
#                 if tok.type == "String":
#                     tok_value = tok.value.strip()

#                     # Remove leading and trailing quotes.
#                     if tok_value[0] == "'" and tok_value[-1] == "'":
#                         tok_value = tok_value[1:-1]
#                     elif tok_value[0] == '"' and tok_value[-1] == '"':
#                         tok_value = tok_value[1:-1]
#                     tok_value = tok_value.strip()

#                     if tok_value != "":
#                         tree_strings.append(
#                             SoupElem(
#                                 depth, f"{elem.name}.String",
#                                 eval_script_text(tok_value))
#                         )

#         return tree_strings

#     # Process children.
#     if hasattr(elem, "children"):
#         for child in elem.children:
#             child_strings = walk_soup_tree_strings(child, depth + 1)
#             tree_strings.extend(child_strings)
#     elif (x := elem.text.strip()) != "":
#         tree_strings.append(
#             SoupElem(depth, TEXT_TAG, x)
#         )

#     return tree_strings


# def walk_soup_tree(elem: element.Tag, depth: int = 0) -> OrderedDict:
#     """Walk the HTML soup tree and collect text snippets from leaf nodes.

#     Returns:
#         OrderedDict: A dictionary of text snippets with occurrence counts.
#     """
#     # Collect text snippets in an ordered dictionary so 
#     # duplicate text appears only once.
#     tree_text = OrderedDict()

#     if elem.name == "script":
#         elem_text = elem.text.strip()
#         if elem_text:
#             # Tokenize the script and extract the String tokens.
#             tokens = esprima.tokenize(elem_text)
#             for tok in tokens:
#                 if tok.type == "String":
#                     tok_value = tok.value.strip()

#                     # Remove leading and trailing quotes.
#                     if tok_value[0] == "'" and tok_value[-1] == "'":
#                         tok_value = tok_value[1:-1]
#                     elif tok_value[0] == '"' and tok_value[-1] == '"':
#                         tok_value = tok_value[1:-1]
#                     tok_value = tok_value.strip()

#                     if tok_value != "":
#                         if tok_value in tree_text:
#                             tree_text[tok_value] += 1
#                         else:
#                             tree_text[tok_value] = 1

#             return tree_text
#     elif elem.name in ("pre", "code"):
#         # Pre and code tags are special blocks that should not be processed.
#         elem_text = elem.get_text().strip()
#         if elem_text:
#             elem_text = f"{CODE_TAG}{elem_text}"
#             tree_text[elem_text] = 1

#         return tree_text
#     elif hasattr(elem, "children"):
#         for child in elem.children:
#             child_text = walk_soup_tree(child, depth + 1)

#             if child_text:
#                 if elem.name == "span":
#                     # SPAN tags are inline so combine the text from all 
#                     # children into a single string.
#                     new_text = "".join(child_text.keys())
#                     tree_text[new_text] = 1
#                 else:
#                     for k in child_text:
#                         if k in tree_text:
#                             tree_text[k] += child_text[k]
#                         else:
#                             tree_text[k] = child_text[k]

#         return tree_text
#     elif (x := elem.text.strip()) != "":
#         tree_text[x] = 1
#         return tree_text


# def get_token_type(tok: spacy.tokens.Token) -> tuple[str, str, str]:
#     """Categorize a token into a word type: REAL, PUNCT, SPACE, or OTHER.
#     """

#     def print_and_return(
#         word_type: str, sub_type: str, lemma: str
#     ) -> tuple[str, str, str]:
#         # print(word_type, sub_type, lemma)
#         return word_type, sub_type, lemma

#     # Word without surrounding whitespace.
#     tok_text = tok.text.strip()
#     tok_lemma = tok.lemma_.strip()

#     if tok_text == "":
#         return print_and_return("SPACE", "space", tok_lemma)
    
#     # Count punctuation in the word.
#     punct_count = sum([1 for c in tok_lemma if c in string.punctuation])
#     if punct_count == len(tok_lemma):
#         return print_and_return("PUNCT", "all", tok_lemma)
#     elif (punct_count / len(tok.text)) > PUNCT_THRESHOLD:
#         # If the word is all punctuation, it's a punctuation word.
#         if not (tok.like_url or tok.like_email or tok.like_num):
#             return print_and_return("PUNCT", "some", tok_lemma)

#     if tok_lemma != tok.text and tok_lemma != tok.text.lower() and len(tok_lemma) <= MAX_WORD_LEN:
#         # Lemma is the base form of the word. It only differs from the original when the word is
#         # part of the model vocabulary.
#         return print_and_return("REAL", "lemma", tok_lemma)
#     elif tok.is_alpha and len(tok_lemma) <= MAX_WORD_LEN:
#         # If word is all alphabetic, it's a real word.
#         return print_and_return("REAL", "alpha", tok_lemma)
#     elif tok.like_url or tok.like_email or tok.like_num:
#         # These are special categories recognized by spaCy.
#         return print_and_return("REAL", "like", tok_lemma)
    
#     # Word is something else.
#     return print_and_return("OTHER", "other", tok_lemma)


# def extract_text(all_text: OrderedDict) -> list[str]:
#     """Process strings and return list of meaningful strings."""

#     extracted_text = []
#     for idx, k in enumerate(all_text.keys()):
#         # If text starts with the special code, add it without any processing.
#         if k.startswith(CODE_TAG):
#             extracted_text.append("")
#             extracted_text.append(k[len(CODE_TAG):])
#             extracted_text.append("")
#             continue
#         elif k.startswith(HEAD_TAG) or k.startswith(BODY_TAG):
#             extracted_text.append(k[len(CODE_TAG):])
#             continue

#         # Only process strings that occur once.
#         if all_text[k] > 1:
#             continue

#         # Evaluate string to evaluate special characters.
#         try:
#             if k.startswith('"') and k.endswith('"'):
#                 cmd = f"'''{k}'''"
#             else:
#                 cmd = f'"""{k}"""'

#             new_text = eval(cmd)
#         except Exception:
#             new_text = k

#         new_text = new_text.strip()
#         if new_text == "":
#             # Skip empty strings.
#             continue
#         # elif len(new_text.split()) < 2:
#         #     # Skip single word strings.
#         #     continue

#         # m = mgk.identify_bytes(new_text.encode())
#         # if m.output.group != "text":
#         #     # Skip strings that are not text.
#         #     continue

#         # Tokenize the text.
#         doc = nlp(new_text)
#         doc_stats = Counter()

#         for tok in doc:
#             word_type, _, _ = get_token_type(tok)
#             doc_stats[word_type] += 1

#         if (doc_stats["PUNCT"] / len(doc)) > PUNCT_THRESHOLD:
#             # Skip strings that are mostly punctuation.
#             continue

#         extracted_text.append(new_text)

#     return extracted_text

