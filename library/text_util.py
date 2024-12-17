from collections import Counter, OrderedDict
from dataclasses import dataclass
import logging
import string

from bs4 import BeautifulSoup, element
import esprima
import spacy
from magika import Magika
from nltk.corpus import words

MAX_WORD_LEN = len("pneumonoultramicroscopicsilicovolcanoconiosis")
PUNCT_THRESHOLD = 0.3333333333333333

# Special tags for code and HTML sections.
CODE_TAG = "<!code!>"
HEAD_TAG = "<!head!>"
BODY_TAG = "<!body!>"
TEXT_TAG = "<!text!>"

# Initialize spaCy and Magika.
# command line: python -m spacy download en_core_web_sm
mgk = Magika()
nlp = spacy.load("en_core_web_sm")
nltk_words = set([x.lower() for x in words.words()])


def extract_text_from_html(html_text: str) -> list[str]:
    """Extract text from HTML and return a list of strings."""
    # Parse the HTML.
    soup = BeautifulSoup(html_text, "html.parser")
    # Walk the soup tree and collect text snippets from leaf nodes.
    head_text = walk_soup_tree(soup.head)
    body_text = walk_soup_tree(soup.body)

    all_text = OrderedDict()

    all_text[f"{HEAD_TAG}--- HEAD ---"] = len(head_text)
    for k in head_text.keys():
        all_text[k] = head_text[k]

    all_text[f"{BODY_TAG}--- BODY ---"] = len(body_text)
    for k in body_text.keys():
        all_text[k] = body_text[k]

    # Extract text from the ordered dictionary.
    extracted_text = extract_text(all_text)
    # Process lines in the extracted text to remove repeated empty lines.
    out = []
    last_line = ""
    for text in extracted_text:
        text_lines = text.splitlines()
        for line in text_lines:
            line = line.rstrip()
            if line == "" and line == last_line:
                continue

            last_line = line
            out.append(line)

    return "\n".join(out)


@dataclass
class SoupToken:
    """A string token from a soup tree."""
    depth: int
    name: str
    text: str
    doc: spacy.tokens.doc.Doc = None
    word_count: int = 0
    alnum_count: int = 0

    def __post_init__(self):
        try:
            self.alnum_count = sum([x.isalnum() for x in self.text])

            self.doc = nlp(self.text)

            self.word_count = 0
            for tok in self.doc:
                if tok.lemma_.lower() in nltk_words:
                    self.word_count += 1

        except Exception as e:
            logging.error(f"SoupToken: {e}")

    def __str__(self) -> str:
        doc_len = len(self.doc)
        word_pct = 0
        if doc_len > 0:
            word_pct = self.word_count / doc_len

        text_len = len(self.text)
        alnum_pct = 0
        if text_len > 0:
            alnum_pct = self.alnum_count / text_len

        return (f"{self.depth:6d} {self.name:15s} "
                f"words:{self.word_count:3d}/{doc_len:3d} ({word_pct:3.2f}) "
                f"alnum:{self.alnum_count:3d}/{text_len:3d} ({alnum_pct:3.2f}) "
                f"{self.text.splitlines()[0][:99]}")


def walk_soup_tree_strings(
        elem: element.Tag, depth: int = 0) -> list[SoupToken]:
    """Walk the HTML soup tree and collect a list of SoupTokens."""

    tree_strings = []

    # HEAD and BODY tags add special markers.
    if elem.name == "head":
        tree_strings.append(
            SoupToken(depth, elem.name, f"{HEAD_TAG}--- {elem.name} ---")
        )
    elif elem.name == "body":
        tree_strings.append(
            SoupToken(depth, elem.name, f"{BODY_TAG}--- {elem.name} ---")
        )

    # Process tags that combine children.
    if elem.name in ("pre", "code"):
        # Pre and code tags are special blocks that should not be processed.
        elem_text = elem.get_text().strip()
        if elem_text:
            tree_strings.append(
                SoupToken(depth, elem.name, f"{CODE_TAG}{elem_text}")
            )

        return tree_strings
    elif elem.name == "script":
        elem_text = elem.text.strip()
        if elem_text:
            # Tokenize the script and extract the String tokens.
            tokens = esprima.tokenize(elem_text)
            for tok in tokens:
                if tok.type == "String":
                    tok_value = tok.value.strip()

                    # Remove leading and trailing quotes.
                    if tok_value[0] == "'" and tok_value[-1] == "'":
                        tok_value = tok_value[1:-1]
                    elif tok_value[0] == '"' and tok_value[-1] == '"':
                        tok_value = tok_value[1:-1]
                    tok_value = tok_value.strip()

                    if tok_value != "":
                        tree_strings.append(
                            SoupToken(depth, f"{elem.name}.String", tok_value)
                        )

        return tree_strings

    # Process children.
    if hasattr(elem, "children"):
        for child in elem.children:
            child_strings = walk_soup_tree_strings(child, depth + 1)
            tree_strings.extend(child_strings)
    elif (x := elem.text.strip()) != "":
        tree_strings.append(
            SoupToken(depth, TEXT_TAG, x)
        )

    return tree_strings


def walk_soup_tree(elem: element.Tag, depth: int = 0) -> OrderedDict:
    """Walk the HTML soup tree and collect text snippets from leaf nodes.

    Returns:
        OrderedDict: A dictionary of text snippets with occurrence counts.
    """
    # Collect text snippets in an ordered dictionary so 
    # duplicate text appears only once.
    tree_text = OrderedDict()

    if elem.name == "script":
        elem_text = elem.text.strip()
        if elem_text:
            # Tokenize the script and extract the String tokens.
            tokens = esprima.tokenize(elem_text)
            for tok in tokens:
                if tok.type == "String":
                    tok_value = tok.value.strip()

                    # Remove leading and trailing quotes.
                    if tok_value[0] == "'" and tok_value[-1] == "'":
                        tok_value = tok_value[1:-1]
                    elif tok_value[0] == '"' and tok_value[-1] == '"':
                        tok_value = tok_value[1:-1]
                    tok_value = tok_value.strip()

                    if tok_value != "":
                        if tok_value in tree_text:
                            tree_text[tok_value] += 1
                        else:
                            tree_text[tok_value] = 1

            return tree_text
    elif elem.name in ("pre", "code"):
        # Pre and code tags are special blocks that should not be processed.
        elem_text = elem.get_text().strip()
        if elem_text:
            elem_text = f"{CODE_TAG}{elem_text}"
            tree_text[elem_text] = 1

        return tree_text
    elif hasattr(elem, "children"):
        for child in elem.children:
            child_text = walk_soup_tree(child, depth + 1)

            if child_text:
                if elem.name == "span":
                    # SPAN tags are inline so combine the text from all 
                    # children into a single string.
                    new_text = "".join(child_text.keys())
                    tree_text[new_text] = 1
                else:
                    for k in child_text:
                        if k in tree_text:
                            tree_text[k] += child_text[k]
                        else:
                            tree_text[k] = child_text[k]

        return tree_text
    elif (x := elem.text.strip()) != "":
        tree_text[x] = 1
        return tree_text


def get_token_type(tok: spacy.tokens.Token) -> tuple[str, str, str]:
    """Categorize a token into a word type: REAL, PUNCT, SPACE, or OTHER.
    """

    def print_and_return(
        word_type: str, sub_type: str, lemma: str
    ) -> tuple[str, str, str]:
        # print(word_type, sub_type, lemma)
        return word_type, sub_type, lemma

    # Word without surrounding whitespace.
    tok_text = tok.text.strip()
    tok_lemma = tok.lemma_.strip()

    if tok_text == "":
        return print_and_return("SPACE", "space", tok_lemma)
    
    # Count punctuation in the word.
    punct_count = sum([1 for c in tok_lemma if c in string.punctuation])
    if punct_count == len(tok_lemma):
        return print_and_return("PUNCT", "all", tok_lemma)
    elif (punct_count / len(tok.text)) > PUNCT_THRESHOLD:
        # If the word is all punctuation, it's a punctuation word.
        if not (tok.like_url or tok.like_email or tok.like_num):
            return print_and_return("PUNCT", "some", tok_lemma)

    if tok_lemma != tok.text and tok_lemma != tok.text.lower() and len(tok_lemma) <= MAX_WORD_LEN:
        # Lemma is the base form of the word. It only differs from the original when the word is
        # part of the model vocabulary.
        return print_and_return("REAL", "lemma", tok_lemma)
    elif tok.is_alpha and len(tok_lemma) <= MAX_WORD_LEN:
        # If word is all alphabetic, it's a real word.
        return print_and_return("REAL", "alpha", tok_lemma)
    elif tok.like_url or tok.like_email or tok.like_num:
        # These are special categories recognized by spaCy.
        return print_and_return("REAL", "like", tok_lemma)
    
    # Word is something else.
    return print_and_return("OTHER", "other", tok_lemma)


def extract_text(all_text: OrderedDict) -> list[str]:
    """Process strings and return list of meaningful strings."""

    extracted_text = []
    for idx, k in enumerate(all_text.keys()):
        # If text starts with the special code, add it without any processing.
        if k.startswith(CODE_TAG):
            extracted_text.append("")
            extracted_text.append(k[len(CODE_TAG):])
            extracted_text.append("")
            continue
        elif k.startswith(HEAD_TAG) or k.startswith(BODY_TAG):
            extracted_text.append(k[len(CODE_TAG):])
            continue

        # Only process strings that occur once.
        if all_text[k] > 1:
            continue

        # Evaluate string to evaluate special characters.
        try:
            if k.startswith('"') and k.endswith('"'):
                cmd = f"'''{k}'''"
            else:
                cmd = f'"""{k}"""'

            new_text = eval(cmd)
        except Exception:
            new_text = k

        new_text = new_text.strip()
        if new_text == "":
            # Skip empty strings.
            continue
        # elif len(new_text.split()) < 2:
        #     # Skip single word strings.
        #     continue

        # m = mgk.identify_bytes(new_text.encode())
        # if m.output.group != "text":
        #     # Skip strings that are not text.
        #     continue

        # Tokenize the text.
        doc = nlp(new_text)
        doc_stats = Counter()

        for tok in doc:
            word_type, _, _ = get_token_type(tok)
            doc_stats[word_type] += 1

        if (doc_stats["PUNCT"] / len(doc)) > PUNCT_THRESHOLD:
            # Skip strings that are mostly punctuation.
            continue

        extracted_text.append(new_text)

    return extracted_text

