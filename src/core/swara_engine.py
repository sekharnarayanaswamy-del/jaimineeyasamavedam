"""
Centralized Vedic Swara Engine for Jaimineeya Samaveda Pipeline.

Unifies accent transformations, Visarga-accent permutations, numeral conversions,
and danda normalizations across all formats (LaTeX, HTML, Unicode Text).
"""

import re
from typing import List, Optional

# --- Unicode Swara Constants ---
UDATTA_SWARITA = '\u0951'       # Devanagari Stress Sign Udatta (Swarita ॑)
ANUDATTA = '\u0952'             # Devanagari Stress Sign Anudatta (॒)
VEDIC_ANUDATTA_BELOW = '\u1CD2' # Vedic Tone Prekampa / Anudatta
VEDIC_KAMPA = '\u1CF8'          # Vedic Tone Ring Above
VEDIC_TRIKAMPA = '\u1CF9'       # Vedic Tone Double Ring Above
VISARGA = '\u0903'              # ः
HALANT = '\u094D'               # ्
DANDA_SINGLE = '\u0964'         # ।
DANDA_DOUBLE = '\u0965'         # ॥

# Unified pattern for Samam markers: ॥ N ॥, ॥N॥, or || N [क/a] ||
SAMAM_PATTERN = re.compile(r'(?:॥|\|\|)\s*[\d०-९]+(?:\s*[a-zA-Zक-ह])?\s*(?:॥|\|\|)')

# Numeral translation tables
DEVA_TO_ARABIC_TABLE = str.maketrans('०१२३४५६७८९', '0123456789')
ARABIC_TO_DEVA_TABLE = str.maketrans('0123456789', '०१२३४५६७८९')


def devanagari_to_int(text: Optional[str]) -> int:
    """Converts a Devanagari numeral string into an integer."""
    if not text:
        return 0
    digits = re.sub(r'[^\d०-९]', '', str(text))
    if not digits:
        return 0
    return int(digits.translate(DEVA_TO_ARABIC_TABLE))


def int_to_devanagari(n: int) -> str:
    """Converts an integer to a Devanagari numeral string."""
    return str(n).translate(ARABIC_TO_DEVA_TABLE)


def normalize_dandas(text: str) -> str:
    """
    Normalizes ASCII pipes and inconsistent double dandas into standard Devanagari.
    e.g., '||' -> '॥', '|' -> '।', '।।' -> '॥'
    """
    if not text:
        return ""
    text = re.sub(r'\|\|', DANDA_DOUBLE, text)
    text = re.sub(r'\|\s*\|', DANDA_DOUBLE, text)
    text = re.sub(r'।।', DANDA_DOUBLE, text)
    text = text.replace('|', DANDA_SINGLE)
    # Remove redundant dandas following separators
    text = re.sub(r'([.\u0964\u0965])\s*[\u0964\u0965\|]+\s*', r'\1', text)
    return text.strip()


def fix_visarga_accent_order(text: str) -> str:
    """
    Swaps Visarga (ः) with immediately following accent marker (1)/(2)/(3) etc.
    so the accent applies to the preceding vowel/character instead of the Visarga.
    Normalizes ASCII colons to Visarga.
    """
    if not text:
        return ""
    # Normalize colon to Visarga
    text = text.replace(':', VISARGA)
    # Remove space before Visarga
    text = re.sub(r'\s+ः', VISARGA, text)
    # Swap Visarga and Accent markup (e.g., ः(1) -> (1)ः)
    pattern = r'([ः])\s*(\([^)]+\))'
    text = re.sub(pattern, r'\2\1', text)
    # Also swap Unicode accents if already converted (e.g., ः॑ -> ॑ः)
    text = re.sub(r'([ः])([\u0951\u0952\u1CD2\u1CF8\u1CF9])', r'\2\1', text)
    return text


def count_samams(text: str) -> int:
    """Counts Samam markers in text using the unified pattern."""
    if not text:
        return 0
    return len(SAMAM_PATTERN.findall(text))


def replace_accents_unicode(text: str) -> str:
    """
    Replaces numerical accent notations with authentic Vedic Unicode glyphs.
    (1) -> Swarita (U+0951)
    (2) -> Anudatta (U+1CD2 or U+0952)
    (3) -> Kampa (U+1CF8)
    (4) -> Trikampa (U+1CF9)
    """
    if not text:
        return ""
    replacements = [
        (r'\(1\)', UDATTA_SWARITA),
        (r'\(2\)', VEDIC_ANUDATTA_BELOW),
        (r'\(3\)', VEDIC_KAMPA),
        (r'\(4\)', VEDIC_TRIKAMPA),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)
    return text
