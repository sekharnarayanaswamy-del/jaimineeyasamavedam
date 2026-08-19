"""Devanagari -> Malayalam transliteration for the Jaimineeya Samaveda.

Wraps aksharamukha with the edge-case fixes ported from pdfconverter
(convert_devanagari_to_malayalam.py): danda preservation, dotted-circle
orphan cleanup, Malayalam O/AU canonicalization, word-final "മ്" -> "ം",
and syllable/grapheme counting used to assert transliteration alignment.

Swara markers (Word(Swara)) are masked before transliteration so the base
word and the marker are processed independently; ml_text.py re-attaches the
resolved Grantha marker.
"""

import re
import unicodedata
from functools import lru_cache

try:
    from aksharamukha import transliterate
except ImportError:  # pragma: no cover
    transliterate = None

try:
    import grapheme
except ImportError:
    grapheme = None

from utils import combine_ardhaksharas

# --- Danda placeholders (same scheme as pdfconverter) ---
_DANDA1 = "\u00A6\u00A6\u00A6"
_DANDA2 = "\u00A6\u00A6\u00A6\u00A6"

_MALAYALAM_VIROMA = "\u0D4D"
_DEVANAGARI_VIROMA = "\u094D"

# --- Script ranges ---
_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F\u1CD0-\u1CF9\uA8E0-\uA8FF]+")
_MALAYALAM_MATRA = r"\u0D3E-\u0D57\u0D66-\u0D6F"


def _transliterate_devanagari_to_malayalam(text: str) -> str:
    if transliterate is None:
        raise RuntimeError(
            "aksharamukha is not installed. Install with: pip install aksharamukha"
        )
    return transliterate.process("Devanagari", "Malayalam", text)


@lru_cache(maxsize=1)
def _transliterate_devanagari_to_grantha(text: str) -> str:
    """Fallback for markers not present in the frozen lookup (render literally)."""
    if transliterate is None:
        raise RuntimeError(
            "aksharamukha is not installed. Install with: pip install aksharamukha"
        )
    return transliterate.process("Devanagari", "Grantha", text)


def devanagari_to_grantha(text: str) -> str:
    return _transliterate_devanagari_to_grantha(text)


def normalize_combining_marks(text: str) -> str:
    """Eliminate dotted-circle artifacts (ported from pdfconverter): spurious
    virama before a matra, spaces detaching a combining mark, and
    NFD-decomposed matra pairs."""
    text = re.sub(
        r"([\u0D15-\u0D39])\u0D4D([" + _MALAYALAM_MATRA + r"\u0D02\u0D03\u0D01])",
        r"\1\2",
        text,
    )
    text = re.sub(
        r"([\u0900-\u097F\u0D00-\u0D7F])\s+([\u0D3E-\u0D57\u0D66-\u0D6F\u0D00-\u0D03])",
        r"\1\2",
        text,
    )
    text = unicodedata.normalize("NFC", text)
    # Malayalam O/AU do not NFC-recompose; collapse explicitly.
    text = text.replace("\u0D3E\u0D46", "\u0D4B")  # ാെ -> ോ
    text = text.replace("\u0D3E\u0D47", "\u0D4C")  # ാേ -> ൌ
    return text


# Translate Devanagari and Malayalam numerals (excluding ൪ which is used for Vedic repha) to English ASCII digits
_DIGITS_TO_ENGLISH = str.maketrans("०१२३४५६७८९൦൧൨൩൫൬൭൮൯", "0123456789012356789")


def post_process_malayalam(text: str) -> str:
    """Cleanup applied after aksharamukha transliteration (ported edge cases)."""
    text = normalize_combining_marks(text)
    # Vedic transliteration rule 2: Devanagari ळ (U+0933) -> Malayalam ഴ (U+0D34)
    text = text.replace("ള", "ഴ").replace("ൾ", "ഴ്")
    # Vedic transliteration rule 1: Vocalic r / Repha before consonants (e.g. र्हा -> ൪ഹാ)
    text = re.sub(r"(?:ർ|ര\u0D4D)(?=[ക-ഹ])", "൪", text)
    # Vedic transliteration rule 3: Word-final AA swara / matra -> short vowel (അ)
    # e.g. സംഹിതാ -> സംഹിത, മാലാ -> മാല, സൂക്തമാലാ -> സൂക്തമാല
    text = re.sub(r"ാ(?=[\s।॥\?!\.,;\)\"']|$)", "", text)
    text = re.sub(r"ആ(?=[\s।॥\?!\.,;\)\"']|$)", "അ", text)
    # Word-final halant ma -> anusvara (e.g. സൂക്തമ് -> സൂക്തം)
    text = re.sub(r"മ്(?=[\s।॥\?!\.,;\)]|$)", "ം", text)
    # Collapse duplicated AA matras
    text = re.sub(r"ാ+", "ാ", text)
    # Virama before ൃ/ൄ (ക്ിൃ -> കൃ)
    text = text.replace("്ൃ", "ൃ").replace("്ൄ", "ൄ")
    # Convert all numerals to English ASCII digits
    text = text.translate(_DIGITS_TO_ENGLISH)
    return text


def devanagari_to_malayalam(text: str) -> str:
    """Transliterate a Devanagari run to Malayalam, preserving dandas.

    The caller is responsible for masking swara markers (ml_text.py).
    Non-Devanagari runs (spaces, dandas, footnote markers) are preserved.
    """
    text = text.replace("।।", "॥").replace("||", "॥")
    text = text.replace("॥", _DANDA2).replace("।", _DANDA1)
    tokens = _DEVANAGARI_RE.split(text)
    parts = _DEVANAGARI_RE.findall(text)
    out = []
    for i, token in enumerate(tokens):
        if token:
            out.append(token)
        if i < len(parts):
            out.append(post_process_malayalam(_transliterate_devanagari_to_malayalam(parts[i])))
    result = "".join(out)
    result = result.replace(_DANDA2, "॥").replace(_DANDA1, "।").replace("\u00A6", "")
    return result


def devanagari_syllable_count(text: str) -> int:
    """Number of Devanagari syllables (combine_ardhaksharas) in a word.

    A word-final 'म्' is an anusvara (source convention writes it as a
    separate token that the pipeline merges into the word), not a syllable.
    """
    parts = combine_ardhaksharas(text)
    count = len(parts)
    if parts and parts[-1] == "\u092E\u094D":
        count -= 1
    return count


def malayalam_grapheme_count(text: str) -> int:
    """Number of Malayalam grapheme clusters in a word."""
    return len(split_malayalam_graphemes(text))


def malayalam_syllable_count(text: str) -> int:
    """Number of Malayalam syllables (conjuncts merged) in a word."""
    return len(split_malayalam_syllables(text))


def split_malayalam_graphemes(text: str) -> list[str]:
    """Split a Malayalam word into grapheme clusters (raw, unmerged)."""
    if grapheme is None:
        result: list[str] = []
        buf = ""
        for ch in text:
            if unicodedata.combining(ch):
                buf += ch
            else:
                if buf:
                    result.append(buf)
                buf = ch
        if buf:
            result.append(buf)
        return result
    return list(grapheme.graphemes(text))


def split_malayalam_syllables(text: str) -> list[str]:
    """Split a Malayalam word into syllables (conjuncts merged).

    Malayalam writes conjuncts as C+virama+C, so raw grapheme clusters like
    ['ഗ്', 'നാ'] are one syllable. Chillu letters (U+0D7A-U+0D7F) carry an
    implicit virama and merge with the following cluster the same way, e.g.
    ഇർമാ = [ഇ][ർ][മാ] -> [ഇ][ർമാ]. This mirrors utils.combine_halants for
    Devanagari and is the unit a swara marker attaches to in the PDF.
    """
    clusters = split_malayalam_graphemes(text)
    merged: list[str] = []
    for cluster in clusters:
        if merged and (
            merged[-1].endswith(_MALAYALAM_VIROMA)
            or (len(merged[-1]) == 1 and "\u0D7A" <= merged[-1] <= "\u0D7F")
        ):
            merged[-1] += cluster
        else:
            merged.append(cluster)
    return merged