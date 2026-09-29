"""
Plain-text export Jinja filters for Jaimineeya Samaveda Pipeline.
----------------------------------------------------------------
Provides filters for generating clean, unformatted plain-text exports
across all document modes (Combined, Rik-only, Samam-only, NoMeta) in
both Devanagari and Malayalam scripts.
"""

import re
from typing import Dict, Any, List, Optional, Tuple

try:
    from core.swara_engine import int_to_devanagari
except ImportError:
    from src.core.swara_engine import int_to_devanagari

try:
    from utils import get_canonical_rik_id
except ImportError:
    from src.utils import get_canonical_rik_id

_ENGLISH_DIGITS = str.maketrans("०१२३४५६७८९൦൧൨൩൪൫൬൭൮൯", "01234567890123456789")


def to_devanagari_numeral(num: Any) -> str:
    """Convert Arabic numerals to Devanagari numerals."""
    if num is None:
        return ""
    try:
        return int_to_devanagari(int(num))
    except (ValueError, TypeError):
        mapping = {'0': '०', '1': '१', '2': '२', '3': '३', '4': '४',
                   '5': '५', '6': '६', '7': '७', '8': '८', '9': '९'}
        return ''.join(mapping.get(c, c) for c in str(num))


def process_footnotes_text(text: str, footnotes_dict: Optional[Dict[str, str]]) -> Tuple[str, List[Tuple[str, str]]]:
    """
    Replace (s1), (s2) markers with Devanagari superscript numerals for plain text.
    
    Args:
        text: The text containing footnote markers
        footnotes_dict: Dictionary mapping marker to footnote text
    
    Returns:
        Tuple of (processed_text, footnotes_list for display)
    """
    if not footnotes_dict:
        return text, []
    
    footnotes_list = []
    for marker, footnote_text in sorted(footnotes_dict.items(), key=lambda x: int(x[0].replace('s', ''))):
        num = int(marker.replace('s', ''))
        devanagari_num = to_devanagari_numeral(num)
        pattern = rf'\({re.escape(marker)}\)'
        replacement = f'({devanagari_num})'
        text = re.sub(pattern, replacement, text)
        footnotes_list.append((devanagari_num, footnote_text))
    
    return text, footnotes_list


def split_rik_lines_text(text: str) -> str:
    """Ensure each Rik verse ends with a newline for plain text output."""
    if not text:
        return ""
    pattern = r'(॥\s*[\d०-९]+\s*॥)\s*'
    return re.sub(pattern, r'\1\n', text).strip()


def normalize_malayalam_samam_text_line(line: str) -> str:
    """Normalizes PUA characters, Grantha glyphs, and swaras for plain text export."""
    if not line:
        return ""
    # 1. Translate verse numbers in dandas
    line = re.sub(r'॥\s*([०-९\d൦-൯]+)\s*॥', lambda m: f"॥ {m.group(1).translate(_ENGLISH_DIGITS)} ॥", line)
    
    # 2. Map PUA swara characters to authentic Grantha characters
    pua_to_grantha = {
        '\uE010': '𑌶𑌾',
        '\uE011': '𑌶𑌿',
        '\uE012': '𑌶𑍀',
        '\uE013': '𑌶𑍍',
        '\uE015': '𑌶𑍁',
        '\uE016': '𑌶𑍂',
        '\uE020': '𑌪𑍍𑌲',
        '\uE021': '𑌪𑍍𑌲𑌾',
        '\uE022': '𑌪𑍍𑌲𑌿',
        '\uE023': '𑌪𑍍𑌲𑍀',
        '\uE027': '𑌶𑍍𑌰𑍂',
        '\uE028': '𑌷𑍃',
        '\uE029': '𑌣𑍁',
    }
    for pua, gran in pua_to_grantha.items():
        line = line.replace(pua, gran)
        
    # 3. Map Swara Modifier codes to Unicode symbols
    mod_to_unicode = {
        'A': '⁀', 'a': '⁀', '\uE004': '⁀', '╭╮': '⁀',
        'A1': '⁀', 'a1': '⁀', 'A_1': '⁀', 'a_1': '⁀', '\uE00D': '⁀',
        'A2': '⁀', 'a2': '⁀', 'A_2': '⁀', 'a_2': '⁀', '\uE02E': '⁀',
        'B': '^', 'b': '^', '\uE005': '^',
        'C': '·', 'c': '·', '\uE001': '·', 'ॱ': '·',
        'D': '∧', 'd': '∧', '\uE006': '∧', 'Ʌ': '∧',
        'D1': '↗', 'd1': '↗', 'D_1': '↗', 'd_1': '↗', '\uE00E': '↗',
        'D2': '✓', 'd2': '✓', 'D_2': '✓', 'd_2': '✓', '\uE00F': '✓',
        'I': '⫽', 'i': '⫽', '\uE02A': '⫽',
        'J': '¯', 'j': '¯', '\uE02B': '¯',
        'B1': '/', 'b1': '/', 'B_1': '/', 'b_1': '/', '\uE02C': '/',
        'K': '⨯', 'k': '⨯', '\uE02D': '⨯',
        'E': '┃', 'e': '┃', '\uE002': '┃',
        'F': '╷', 'f': '╷', '\uE008': '╷',
        'G': '\\', 'g': '\\', '\uE003': '\\',
        'H': '|', 'h': '|', '\uE00C': '|',
        'L': '|', 'l': '|',
    }
    
    def _rep_paren(m):
        content = m.group(1)
        if content in mod_to_unicode:
            return f"({mod_to_unicode[content]})"
        return m.group(0)
    
    line = re.sub(r'\(([^)]+)\)', _rep_paren, line)
    line = line.replace('൪', 'ൎ')
    return line


def format_mantra_sets_text(subsection: dict, section_title: str = "", subsection_title: str = "") -> str:
    """Format mantra sets for plain-text export."""
    formatted_sets = []
    
    mantra_sets = subsection.get('mantra_sets', [])
    mantra_array = []
    for mantra_set in mantra_sets:
        mantra_words = mantra_set.get('mantra-words', [])
        mantra = ""
        for word in mantra_words:
            actual_word = word.get('word', 'WORD')
            mantra += " " + actual_word
        mantra_array.append(mantra)
        
    corrected_mantra_sets = subsection.get('corrected-mantra_sets', [])
    corrected_mantra_array = []
    if corrected_mantra_sets is not None:
        for corrected in corrected_mantra_sets:
            corrected_mantra = corrected.get('corrected-mantra', '')
            if corrected_mantra:
                corrected_mantra_array.append(corrected_mantra)
                
    if len(corrected_mantra_array) != 0:
        mantra_array = corrected_mantra_array

    footnotes = subsection.get('footnotes', {})
    for mantra in mantra_array:
        clean_mantra = mantra.replace('\\newline%', '').replace('\\newline', '')
        clean_mantra, _ = process_footnotes_text(clean_mantra, footnotes)
        formatted_sets.append(clean_mantra)

    return "\n".join(formatted_sets)


def format_malayalam_samam_text(subsection: dict, section_title: str = "", subsection_title: str = "") -> str:
    """Plain-text artifact for Malayalam Samam with Grantha swara markers and Unicode modifiers."""
    formatted_sets = []
    
    # 1. Prioritize native malayalam-mantra-sets
    for mantra_set in subsection.get('malayalam-mantra-sets', []):
        mantra = mantra_set.get('malayalam-mantra', '')
        if mantra:
            formatted_sets.append(normalize_malayalam_samam_text_line(mantra))
    if formatted_sets:
        return "\n".join(formatted_sets)
        
    # 2. Check corrected-mantra_sets
    corrected_mantra_sets = subsection.get('corrected-mantra_sets', [])
    if corrected_mantra_sets:
        for corrected in corrected_mantra_sets:
            c_mantra = corrected.get('corrected-mantra', '')
            if c_mantra:
                formatted_sets.append(normalize_malayalam_samam_text_line(c_mantra))
        if formatted_sets:
            return "\n".join(formatted_sets)

    # 3. Check mantra_sets
    for mantra_set in subsection.get('mantra_sets', []):
        words = []
        for word_dict in mantra_set.get('mantra-words', []):
            w = word_dict.get('word', '')
            sw = word_dict.get('swara', '')
            if sw:
                words.append(f"{w}({sw})")
            else:
                words.append(w)
        if words:
            formatted_sets.append(normalize_malayalam_samam_text_line(" ".join(words)))

    return "\n".join(formatted_sets)


def format_rik_only_text(subsection: dict, section_title: str = "", subsection_title: str = "", prev_rik_id: Optional[Any] = None, prev_rik_text: Optional[str] = None) -> str:
    """Format only Rik content for plain text output."""
    formatted_output = []
    
    current_rik_id = get_canonical_rik_id(subsection)
    rik_ids = subsection.get('rik_ids', [current_rik_id] if current_rik_id else [])
    rik_metadata = subsection.get('rik_metadata', '')
    rik_text = subsection.get('rik_text', '')
    
    # Skip consecutive duplicate Rik text across multiple Samams
    if prev_rik_text and rik_text and rik_text.strip() == prev_rik_text.strip():
        return ""

    show_rik_info = (prev_rik_id is None) or (current_rik_id != prev_rik_id)
    if not show_rik_info and len(rik_ids) > 1:
        max_rik_id = max(rik_ids) if rik_ids else None
        if max_rik_id is not None and max_rik_id != prev_rik_id:
            show_rik_info = True

    if not show_rik_info or (not rik_metadata and not rik_text):
        return ""
    
    if current_rik_id:
        formatted_output.append(f"॥ ऋक् {to_devanagari_numeral(current_rik_id)} ॥")
    
    if rik_metadata:
        formatted_output.append(rik_metadata)
    
    if rik_text:
        footnotes = subsection.get('footnotes', {})
        rik_text, _ = process_footnotes_text(rik_text, footnotes)
        formatted_output.append(rik_text)
    
    return "\n".join(formatted_output)


def format_samam_only_text(subsection: dict, section_title: str = "", subsection_title: str = "") -> str:
    """Format only Samam content for plain text output."""
    formatted_output = []
    
    header = subsection.get('header', {}).get('header', '')
    saman_metadata = subsection.get('saman_metadata', '')
    
    if header and saman_metadata:
        formatted_output.append(f"{header}  {saman_metadata}")
    elif header:
        formatted_output.append(header)
    elif saman_metadata:
        formatted_output.append(saman_metadata)
    
    mantra_sets = subsection.get('mantra_sets', [])
    corrected_mantra_sets = subsection.get('corrected-mantra_sets', [])
    
    mantra_array = []
    if corrected_mantra_sets:
        for corrected in corrected_mantra_sets:
            corrected_mantra = corrected.get('corrected-mantra', '')
            if corrected_mantra:
                mantra_array.append(corrected_mantra)
    else:
        for mantra_set in mantra_sets:
            mantra_words = mantra_set.get('mantra-words', [])
            mantra = ""
            for word in mantra_words:
                actual_word = word.get('word', '')
                mantra += " " + actual_word
            mantra_array.append(mantra.strip())
    
    footnotes = subsection.get('footnotes', {})
    for mantra in mantra_array:
        clean_mantra = mantra.replace('\\newline%', ' ')
        clean_mantra = clean_mantra.replace('\\newline', ' ')
        clean_mantra = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', clean_mantra)
        clean_mantra = re.sub(r'\\[a-zA-Z]+', '', clean_mantra)
        clean_mantra = re.sub(r'\s+', ' ', clean_mantra).strip()
        clean_mantra, _ = process_footnotes_text(clean_mantra, footnotes)
        formatted_output.append(clean_mantra)
    
    return "\n".join(formatted_output)


def format_rik_nometa_text(subsection: dict, section_title: str = "", subsection_title: str = "", prev_rik_id: Optional[Any] = None, prev_rik_text: Optional[str] = None) -> str:
    """Format only Rik text (without metadata) for plain text output."""
    formatted_output = []
    
    current_rik_id = get_canonical_rik_id(subsection)
    rik_ids = subsection.get('rik_ids', [current_rik_id] if current_rik_id else [])
    rik_text = subsection.get('rik_text', '')
    
    # Skip consecutive duplicate Rik text across multiple Samams
    if prev_rik_text and rik_text and rik_text.strip() == prev_rik_text.strip():
        return ""

    show_rik_info = (prev_rik_id is None) or (current_rik_id != prev_rik_id)
    if not show_rik_info and len(rik_ids) > 1:
        max_rik_id = max(rik_ids) if rik_ids else None
        if max_rik_id is not None and max_rik_id != prev_rik_id:
            show_rik_info = True

    if not show_rik_info or not rik_text:
        return ""
    
    if current_rik_id:
        formatted_output.append(f"॥ ऋक् {to_devanagari_numeral(current_rik_id)} ॥")
    
    if rik_text:
        footnotes = subsection.get('footnotes', {})
        rik_text, _ = process_footnotes_text(rik_text, footnotes)
        formatted_output.append(rik_text)
    
    return "\n".join(formatted_output)


def format_samam_nometa_text(subsection: dict, section_title: str = "", subsection_title: str = "") -> str:
    """Format only Samam mantra text (without header or metadata) for plain text output."""
    formatted_output = []
    
    mantra_sets = subsection.get('mantra_sets', [])
    corrected_mantra_sets = subsection.get('corrected-mantra_sets', [])
    
    mantra_array = []
    if corrected_mantra_sets:
        for corrected in corrected_mantra_sets:
            corrected_mantra = corrected.get('corrected-mantra', '')
            if corrected_mantra:
                mantra_array.append(corrected_mantra)
    else:
        for mantra_set in mantra_sets:
            mantra_words = mantra_set.get('mantra-words', [])
            mantra = ""
            for word in mantra_words:
                actual_word = word.get('word', '')
                mantra += " " + actual_word
            mantra_array.append(mantra.strip())
    
    footnotes = subsection.get('footnotes', {})
    for mantra in mantra_array:
        clean_mantra = mantra.replace('\\newline%', ' ')
        clean_mantra = clean_mantra.replace('\\newline', ' ')
        clean_mantra = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', clean_mantra)
        clean_mantra = re.sub(r'\\[a-zA-Z]+', '', clean_mantra)
        clean_mantra = re.sub(r'\s+', ' ', clean_mantra).strip()
        clean_mantra, _ = process_footnotes_text(clean_mantra, footnotes)
        formatted_output.append(clean_mantra)
    
    return "\n".join(formatted_output)


def register_text_filters(env: Any):
    """Registers all plaintext Jinja filters to a Jinja2 Environment."""
    env.filters["format_mantra_sets_text"] = format_mantra_sets_text
    env.filters["format_rik_only_text"] = format_rik_only_text
    env.filters["format_samam_only_text"] = format_samam_only_text
    env.filters["format_rik_nometa_text"] = format_rik_nometa_text
    env.filters["format_samam_nometa_text"] = format_samam_nometa_text
    env.filters["format_malayalam_samam_text"] = format_malayalam_samam_text
    env.filters["split_rik_lines"] = split_rik_lines_text
