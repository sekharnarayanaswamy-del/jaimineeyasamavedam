"""
Search indexing and fuzzy transliteration utilities for Jaimineeya Static Website
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any
from .models import Parva


def clean_text_for_search(html_text: str) -> str:
    """Strip HTML tags and swara spans to get plain Devanagari text for search matching"""
    if not html_text:
        return ""
    text = re.sub(r'<[^>]+>', ' ', html_text)
    # Remove swara notation (text within parentheses) for search matching
    text = re.sub(r'\([^)]*\)', '', text)
    # Normalize whitespace and zero-width characters
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\u00A0', ' ')
    text = text.replace('\u200B', '')
    text = text.replace('\u200C', '')
    text = text.replace('\u200D', '')
    text = text.replace('\u2060', '')
    return text.strip()


def strip_diacritics(text: str) -> str:
    """Remove Devanagari combining marks (diacritics) for permissive matching"""
    if not text:
        return ""
    diacritics = ''.join([chr(c) for c in range(0x0900, 0x0903)])
    diacritics += ''.join([chr(c) for c in range(0x093E, 0x094F)])
    diacritics += ''.join([chr(c) for c in range(0x0951, 0x0958)])
    diacritics += ''.join([chr(c) for c in range(0x1CD0, 0x1D00)])
    diacritics += '\u0964\u0965'
    diacritics += ''.join([chr(c) for c in range(0x0966, 0x0970)])
    diacritics += '0123456789'
    result = []
    for char in text:
        if char not in diacritics:
            result.append(char)
    return ''.join(result)


def transliterate_to_latin(text: str) -> str:
    """Convert Devanagari to Super-Permissive Latin for fuzzy matching"""
    if not text:
        return ""
    mapping = {
        'अ': 'a', 'आ': 'a', 'इ': 'i', 'ई': 'i', 'उ': 'u', 'ऊ': 'u', 'ऋ': 'r', 'ॠ': 'r',
        'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
        'क': 'k', 'ख': 'k', 'ग': 'g', 'घ': 'g', 'ङ': 'n',
        'च': 'c', 'छ': 'c', 'ज': 'j', 'झ': 'j', 'ञ': 'n',
        'ट': 't', 'ठ': 't', 'ड': 'd', 'ढ': 'd', 'ण': 'n',
        'त': 't', 'थ': 't', 'द': 'd', 'ध': 'd', 'न': 'n',
        'प': 'p', 'फ': 'p', 'ब': 'b', 'भ': 'b', 'म': 'm',
        'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 's', 'ष': 's', 'स': 's', 'ह': 'h',
        'ा': 'a', 'ि': 'i', 'ी': 'i', 'ु': 'u', 'ू': 'u', 'ृ': 'r', 'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
        'ं': 'n', 'ः': 'h', 'ँ': 'n',
    }
    result = []
    for char in text:
        if char in mapping:
            result.append(mapping[char])
        elif 'a' <= char.lower() <= 'z':
            result.append(char.lower())
    return ''.join(result)


def generate_search_index_file(parvas: List[Parva], output_dir: Path, has_riks: bool = True, has_samams: bool = True, has_metadata: bool = True):
    """Generate search-index.js with clean text for matching and HTML for display"""
    index = []
    for parva in parvas:
        for kandah in parva.kandahs:
            for sama in kandah.samas:
                sama_ref = f"{parva.parva_number}.{kandah.kandah_number}.{sama.sama_number}"
                link = f"kandah/{parva.id}/{kandah.kandah_number}.html#sama-{sama.sama_number}"

                rik_clean = clean_text_for_search(sama.rik_text) if has_riks else ""
                mantra_clean = clean_text_for_search(sama.mantra_text) if has_samams else ""
                title_clean = clean_text_for_search(sama.title) if has_metadata else ""
                metadata_clean = clean_text_for_search(sama.saman_metadata) if has_metadata else ""
                
                rik_permissive = strip_diacritics(rik_clean) if has_riks else ""
                mantra_permissive = strip_diacritics(mantra_clean) if has_samams else ""
                rik_latin = transliterate_to_latin(rik_clean) if has_riks else ""
                mantra_latin = transliterate_to_latin(mantra_clean) if has_samams else ""
                
                classifications = []
                if has_metadata and has_riks:
                    for c in sama.rik_classifications:
                        rishi_clean = clean_text_for_search(c.get("Rishi", ""))
                        devata_clean = clean_text_for_search(c.get("Devata", ""))
                        chandas_clean = clean_text_for_search(c.get("Chandas", ""))
                        classifications.append({
                            "rishi": c.get("Rishi", ""),
                            "rishi_clean": rishi_clean,
                            "rishi_permissive": strip_diacritics(rishi_clean),
                            "rishi_latin": transliterate_to_latin(rishi_clean),
                            "devata": c.get("Devata", ""),
                            "devata_clean": devata_clean,
                            "devata_permissive": strip_diacritics(devata_clean),
                            "devata_latin": transliterate_to_latin(devata_clean),
                            "chandas": c.get("Chandas", ""),
                            "chandas_clean": chandas_clean,
                            "chandas_permissive": strip_diacritics(chandas_clean),
                            "chandas_latin": transliterate_to_latin(chandas_clean),
                            "global_num": c.get("Global_Rik_Num", "")
                        })
                
                entry = {
                    "ref": sama_ref,
                    "link": link,
                    "parva_num": parva.parva_number,
                    "parva_title": parva.title,
                    "kandah_num": kandah.kandah_number,
                    "sama_num": sama.sama_number,
                    "rik_html": (sama.rik_text or "") if has_riks else "",
                    "mantra_html": (sama.mantra_text or "") if has_samams else "",
                    "title_html": (sama.title or "") if has_metadata else "",
                    "metadata_html": (sama.saman_metadata or "") if has_metadata else "",
                    "rik_clean": rik_clean,
                    "mantra_clean": mantra_clean,
                    "title_clean": title_clean,
                    "metadata_clean": metadata_clean,
                    "rik_permissive": rik_permissive,
                    "mantra_permissive": mantra_permissive,
                    "rik_latin": rik_latin,
                    "mantra_latin": mantra_latin,
                    "title_latin": transliterate_to_latin(title_clean),
                    "metadata_latin": transliterate_to_latin(metadata_clean),
                    "classifications": classifications
                }
                index.append(entry)
    
    index_path = output_dir / 'search-index.js'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('const SEARCH_INDEX = ')
        json.dump(index, f, ensure_ascii=False)
        f.write(';')
    print(f"  Search index: {len(index)} entries -> {index_path}")
