#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Devanagari -> Grantha transliteration for the Jaimineeya Samaveda.

Wraps aksharamukha for high-fidelity conversion of Vedic Sanskrit ASTs,
mantras, and metadata to canonical Grantha Unicode (U+11300 - U+1137F)
with Grantha/Tamil numerals (U+0BE6 - U+0BEF).
"""

import copy
import re
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

try:
    from aksharamukha import transliterate
except ImportError:
    transliterate = None

# Grantha syllable regex for phonetic syllable segmentation
GRANTHA_SYLLABLE_RE = re.compile(
    r'(?:[\U00011305-\U00011314\U00011360-\U00011363]|(?:[\U00011315-\U00011339]\U0001134D)*[\U00011315-\U00011339](?:[\U0001133E-\U0001134D\U00011357\U00011362\U00011363])?)(?:[\U00011301-\U00011303])?(?:[_,.\\·ॱ़┃L╷^⁀∧✓↗])*'
)

# Numeral translations
DEVA_TO_GRANTHA_DIGITS = str.maketrans("०१२३४५६७८९", "௦௧௨௩௪௫௬௭௮௯")
ASCII_TO_GRANTHA_DIGITS = str.maketrans("0123456789", "௦௧௨௩௪௫௬௭௮௯")
GRANTHA_TO_ASCII_DIGITS = str.maketrans("௦௧௨௩௪௫௬௭௮௯", "0123456789")

# Footnote pattern (s1, s2, ...)
FOOTNOTE_RE = re.compile(r"\(s\d+\)")


def to_grantha_numeral(n: Any) -> str:
    """Convert an integer or numeric string into Grantha/Tamil numerals."""
    if n is None:
        return ""
    s = str(n).strip()
    s = s.translate(DEVA_TO_GRANTHA_DIGITS)
    s = s.translate(ASCII_TO_GRANTHA_DIGITS)
    return s


def split_grantha_syllables(text: str) -> List[str]:
    """Splits a Grantha word into distinct phonetic syllables with attached modifiers."""
    if not text:
        return []
    return [m.group(0) for m in GRANTHA_SYLLABLE_RE.finditer(text)]


@lru_cache(maxsize=10000)
def _transliterate_chunk(text: str) -> str:
    if transliterate is None:
        raise RuntimeError("aksharamukha is not installed. Install with: pip install aksharamukha")
    return transliterate.process("Devanagari", "Grantha", text)


@lru_cache(maxsize=10000)
def grantha_to_devanagari(text: str) -> str:
    """Transliterate Grantha text back to Devanagari."""
    if not text:
        return ""
    if transliterate is None:
        return text
    return transliterate.process("Grantha", "Devanagari", text)


def devanagari_to_grantha(text: str) -> str:
    """Transliterate Devanagari text to Grantha, preserving footnote markers (s1), (s2)..."""
    if not text:
        return ""

    # Preserve footnote markers (s1), (s2)...
    placeholders = {}
    counter = 0

    def mask_footnote(match):
        nonlocal counter
        ph = f"___FN{counter}___"
        placeholders[ph] = match.group(0)
        counter += 1
        return ph

    masked = FOOTNOTE_RE.sub(mask_footnote, text)
    result = _transliterate_chunk(masked)

    # Restore placeholders
    for ph, orig in placeholders.items():
        result = result.replace(ph, orig)

    return result


def transform_line(line: str) -> str:
    """Transliterate one mantra line from Devanagari to Grantha."""
    if not line:
        return ""
    return devanagari_to_grantha(line)


def transform_ast(data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """Deep-copy AST data, transliterating all Sanskrit fields to Grantha.

    Returns:
        (transformed_data, stats_dict)
    """
    out = copy.deepcopy(data)
    stats = {
        "supersections": 0,
        "sections": 0,
        "subsections": 0,
        "mantras": 0,
        "riks": 0,
    }

    # Support both 'supersections' and 'supersection'
    ss_dict = out.get("supersections")
    if ss_dict is None:
        ss_dict = out.get("supersection", {})

    for ss_key, ss_data in ss_dict.items():
        if ss_key == "count" or not isinstance(ss_data, dict):
            continue
        stats["supersections"] += 1

        if ss_data.get("supersection_title"):
            ss_data["supersection_title_deva"] = ss_data["supersection_title"]
            ss_data["supersection_title"] = devanagari_to_grantha(ss_data["supersection_title"])
        if ss_data.get("supersection_title_toc"):
            ss_data["supersection_title_toc_deva"] = ss_data["supersection_title_toc"]
            ss_data["supersection_title_toc"] = devanagari_to_grantha(ss_data["supersection_title_toc"])

        sec_dict = ss_data.get("sections", {})
        for sec_key, sec_data in sec_dict.items():
            if sec_key == "count" or not isinstance(sec_data, dict):
                continue
            stats["sections"] += 1

            if sec_data.get("section_title"):
                sec_data["section_title_deva"] = sec_data["section_title"]
                sec_data["section_title"] = devanagari_to_grantha(sec_data["section_title"])
            if sec_data.get("section_title_toc"):
                sec_data["section_title_toc_deva"] = sec_data["section_title_toc"]
                sec_data["section_title_toc"] = devanagari_to_grantha(sec_data["section_title_toc"])

            sub_dict = sec_data.get("subsections", {})
            for sub_key, sub_data in sub_dict.items():
                if not isinstance(sub_data, dict):
                    continue
                stats["subsections"] += 1

                # Header
                hdr = sub_data.get("header")
                if isinstance(hdr, dict) and hdr.get("header"):
                    hdr["header_deva"] = hdr["header"]
                    hdr["header"] = devanagari_to_grantha(hdr["header"])

                # Rik metadata and text
                if sub_data.get("rik_metadata"):
                    sub_data["rik_metadata_deva"] = sub_data["rik_metadata"]
                    sub_data["rik_metadata"] = devanagari_to_grantha(sub_data["rik_metadata"])
                if sub_data.get("rik_text"):
                    sub_data["rik_text_deva"] = sub_data["rik_text"]
                    sub_data["rik_text"] = devanagari_to_grantha(sub_data["rik_text"])
                    stats["riks"] += 1

                # Saman metadata
                if sub_data.get("saman_metadata"):
                    sub_data["saman_metadata"] = devanagari_to_grantha(sub_data["saman_metadata"])

                # Footnotes dictionary
                if sub_data.get("footnotes") and isinstance(sub_data["footnotes"], dict):
                    sub_data["footnotes"] = {
                        k: devanagari_to_grantha(v) if isinstance(v, str) else v
                        for k, v in sub_data["footnotes"].items()
                    }

                # Mantra sets
                m_sets = sub_data.get("corrected-mantra_sets") or sub_data.get("mantra_sets") or []
                grantha_sets = []
                for mset in m_sets:
                    raw_mantra = mset.get("corrected-mantra") or mset.get("mantra", "")
                    if not raw_mantra and mset.get("mantra-words"):
                        raw_mantra = " ".join(
                            f"{w.get('word', '')}({w['swara']})" if w.get("swara") else w.get("word", "")
                            for w in mset.get("mantra-words", [])
                        )
                    gr_line = transform_line(raw_mantra) if raw_mantra else ""
                    stats["mantras"] += 1
                    grantha_sets.append({
                        "grantha-mantra": gr_line,
                        "corrected-mantra": gr_line,
                        "mantra": gr_line,
                        "devanagari-mantra": raw_mantra,
                    })

                sub_data["corrected-mantra_sets"] = grantha_sets
                sub_data["grantha-mantra-sets"] = grantha_sets

    # Closing mantras
    closing = out.get("closing-mantras") or out.get("closing_mantras", [])
    if closing:
        out["closing_mantras"] = [devanagari_to_grantha(c) for c in closing]
        out["closing-mantras"] = out["closing_mantras"]

    return out, stats
