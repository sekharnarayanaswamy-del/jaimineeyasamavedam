r"""
LaTeX/PDF Jinja filters for Jaimineeya Samaveda Pipeline.
Provides LaTeX typography, accent macros (\sva, \uda, \anu, \mlswara),
syllable-level swara positioning, and section formatting across both
Devanagari and Malayalam scripts.
"""

import re
import urllib.parse
from typing import Dict, Any, List, Optional, Tuple, Union

try:
    from utils import (
        combine_halants, combine_ardhaksharas,
        my_encodeURL, my_format,
        replacecolon, normalize_and_trim,
        parse_mantra_for_latex,
        get_canonical_rik_id
    )
except ImportError:
    from src.utils import (
        combine_halants, combine_ardhaksharas,
        my_encodeURL, my_format,
        replacecolon, normalize_and_trim,
        parse_mantra_for_latex,
        get_canonical_rik_id
    )

try:
    from core.swara_engine import int_to_devanagari, split_deva_syllables, tokenize_mantra_line
except ImportError:
    from src.core.swara_engine import int_to_devanagari, split_deva_syllables, tokenize_mantra_line

try:
    from malayalam.ml_transliterate import split_malayalam_syllables, devanagari_to_malayalam
    from malayalam.ml_map import marker_to_grantha
except ImportError:
    from src.malayalam.ml_transliterate import split_malayalam_syllables, devanagari_to_malayalam
    from src.malayalam.ml_map import marker_to_grantha

try:
    from src.renderers.filters.text_filters import process_footnotes_text
except ImportError:
    from renderers.filters.text_filters import process_footnotes_text

# --- General Swara & Text Helpers ---
CURRENT_PDF_FONT = "AdishilaVedic"
LATEX_DOC_MARKERS_MAP = {}

def reset_latex_doc_markers() -> None:
    """Reset the document-level footnote marker map between renders."""
    global LATEX_DOC_MARKERS_MAP
    LATEX_DOC_MARKERS_MAP.clear()

def set_current_pdf_font(font: str) -> None:
    global CURRENT_PDF_FONT
    if font:
        CURRENT_PDF_FONT = font
def to_devanagari_numeral(num):
    """Convert Arabic numerals to Devanagari numerals."""
    if num is None:
        return ""
    mapping = {'0': '०', '1': '१', '2': '२', '3': '३', '4': '४',
               '5': '५', '6': '६', '7': '७', '8': '८', '9': '९'}
    return ''.join(mapping.get(c, c) for c in str(num))

def fix_visarga_accent_order_local(text):
    """
    Always swap so accent appears on character BEFORE visarga.
    Input: Word:(1) -> Word(1):  (accent now on preceding character)
    """
    if not text: return text
    
    # Normalize colons
    text = text.replace(':', 'ः')
    text = re.sub(r'\s+ः', 'ः', text)
    
    # Always swap Visarga + Accent to Accent + Visarga
    pattern = r'([ः])\s*(\([^)]+\))'
    text = re.sub(pattern, r'\2\1', text)
    
    return text

def replace_accents(text):
    r"""
    Replaces ASCII markers (1), (2), etc., with raised accent marks.
    
    Uses \makebox[0pt] to create zero-width accent overlays that don't
    add horizontal spacing. The accents are raised using \raisebox and
    made bold/larger using \accentmark.
    
    Unicode Vedic Accent Characters:
    - U+0951 = ॑ (Swarita - vertical line above)
    - U+1CD2 = ᳒ (Anudatta - horizontal line below) 
    - U+1CF8 = ᳸ (Kampa - curved mark)
    - U+1CF9 = ᳹ (Trikampa - double curve)
    """
    if not text: return text
    
    if 'Adishila' in CURRENT_PDF_FONT:
        replacements = [
            ('(1)', r'\raisebox{0.6ex}{\accentmark{12}{\char"0951}}'),
            ('(2)', r'\raisebox{0.6ex}{\accentmark{15}{\char"1CD2}}'),
            ('(3)', r'\raisebox{0.4ex}{\accentmark{12}{\char"1CF8}}'),
            ('(4)', r'\raisebox{0.4ex}{\accentmark{12}{\char"1CF9}}'),
        ]
    else:
        # For Noto Sans and other fonts, use a Non-Breaking Space (\char"00A0) as a base
        # to suppress dotted circles. Wrap in \makebox[0pt] to hide the NBSP width.
        replacements = [
            ('(1)', r'\raisebox{0.7ex}{\makebox[0pt]{\accentmark{12}{\char"00A0\char"0951}}}'), # Swarita
            ('(2)', r'\raisebox{-0.1ex}{\makebox[0pt]{\accentmark{15}{\char"00A0\char"1CD2}}}'), # Anudatta
            ('(3)', r'\raisebox{0.5ex}{\makebox[0pt]{\accentmark{12}{\char"00A0\char"1CF8}}}'), # Kampa
            ('(4)', r'\raisebox{0.5ex}{\makebox[0pt]{\accentmark{12}{\char"00A0\char"1CF9}}}'), # Trikamba
        ]
  
    for marker, replacement in replacements:
        text = text.replace(marker, replacement)
    
    return text

def handle_consecutive_accents(text):
    r"""
    Previously inserted \kern to separate specific accent transitions 
    that were prone to visual overlap with AdishilaVedic font.
    
    With Noto Sans Devanagari, this kerning is not needed and causes
    unwanted spacing. Returning text unchanged.
    """
    if not text: return text
    
    # NOTE: Kerning disabled for Noto Sans Devanagari
    # The font handles accent spacing properly without manual adjustments
    # Keep the patterns commented for reference if switching fonts:
    
    # CASE A: Anudatta (2) followed by Anudatta (2)
    # pat_2_2 = r'(\(2\))(?=[^()]{1,5}\(2\))'
    # text = re.sub(pat_2_2, r'\1\\kern0.15em', text)

    # CASE B: Swarita (1) followed by Anudatta (2)
    # pat_1_2 = r'(\(1\))(?=[^()]{1,5}\(2\))'
    # text = re.sub(pat_1_2, r'\1\\kern0.15em', text)

    # CASE C: Anudatta (2) followed by Kampa (3) or Trikampa (4)
    # pat_2_3= r'(\(2\))(?=[^()]{1,5}\(3\))'
    # text = re.sub(pat_2_3, r'\1\\kern0.15em', text)

    # pat_2_4= r'(\(2\))(?=[^()]{1,5}\(4\))'
    # text = re.sub(pat_2_4, r'\1\\kern0.15em', text)
    
    return text

def remove_mantra_spaces(text):
    """
    Removes all spaces within the text to create continuous Samhita text.
    Handles all types of Unicode whitespace characters.
    Preserves Dandas.
    """
    if not text: return text
    
    # Remove all Unicode whitespace characters using regex
    # \s covers: space, tab, newline, carriage return, form feed, vertical tab
    # Also explicitly remove non-breaking space (U+00A0) and other invisible separators
    text = re.sub(r'\s+', '', text)
    text = text.replace('\u00A0', '')  # Non-breaking space
    text = text.replace('\u200B', '')  # Zero-width space
    text = text.replace('\u200C', '')  # Zero-width non-joiner
    text = text.replace('\u200D', '')  # Zero-width joiner
    text = text.replace('\uFEFF', '')  # Byte order mark
    
    return text

def split_rik_lines_latex(text):
    """
    Splits multi-Rik text so each Rik appears on its own line in LaTeX.
    Splits after each verse marker (॥ N ॥) and joins with \\newline.
    If only one Rik is present, returns the text unchanged.
    """
    if not text:
        return text
    parts = re.split(r'((?:॥|\|\|)\s*[०-९\d]+\s*(?:॥|\|\|))', text)
    if len(parts) <= 1:
        return text
    lines = []
    current = ''
    for part in parts:
        if re.match(r'(?:॥|\|\|)\s*[०-९\d]+\s*(?:॥|\|\|)', part):
            current += part
            lines.append(current.strip())
            current = ''
        else:
            current += part
    if current.strip():
        lines.append(current.strip())
    lines = [l for l in lines if l]
    if len(lines) <= 1:
        return text
    # Use standard LaTeX line break (\\) for multi-verse Riks
    return ' \\\\ '.join(lines)

def process_footnotes_latex(text, footnotes_dict, seen_markers=None, subsection_key=None, doc_markers_map=None):
    """
    Replace (s1), (s2) markers with state-aware LaTeX footnotes/references.
    
    Args:
        text: The text containing footnote markers like (s1), (s2)
        footnotes_dict: Dictionary { "s1": "text" }
        seen_markers: set of seen markers ("s1", "s2") for this subsection scope
        subsection_key: unique ID for the subsection to generate stable labels
        doc_markers_map: document-level dict mapping marker to label
    """
    if not text:
        return text
        
    if footnotes_dict is None:
        footnotes_dict = {}

    if doc_markers_map is None:
        doc_markers_map = LATEX_DOC_MARKERS_MAP
    
    def replacer(match):
        marker = match.group(1) # s1
        full_marker = match.group(0) # (s1)
        
        if footnotes_dict and marker in footnotes_dict:
            footnote_text = footnotes_dict[marker]
            if seen_markers is not None and subsection_key is not None:
                label = f"fn:{subsection_key}:{marker}"
                if marker in seen_markers:
                    # Reference existing footnote
                    return f"\\rule{{0pt}}{{2.5ex}}\\textsuperscript{{\\raisebox{{1.2ex}}{{\\normalfont\\ref{{{label}}}}}}}"
                else:
                    # Create new footnote with label
                    seen_markers.add(marker)
                    if doc_markers_map is not None:
                        doc_markers_map[marker] = label
                    return f"\\rule{{0pt}}{{2.5ex}}\\footnote{{{footnote_text}\\label{{{label}}}}}"
            else:
                return f"\\rule{{0pt}}{{2.5ex}}\\footnote{{{footnote_text}}}"
        elif doc_markers_map is not None and marker in doc_markers_map:
            label = doc_markers_map[marker]
            if seen_markers is not None:
                seen_markers.add(marker)
            return f"\\rule{{0pt}}{{2.5ex}}\\textsuperscript{{\\raisebox{{1.2ex}}{{\\normalfont\\ref{{{label}}}}}}}"
        return full_marker

    # Sanitize invisible characters that break footnote matching
    invisible_chars_pattern = r'[\u200b\u200c\ufeff\u2060\u180e\u00ad]'
    text = re.sub(invisible_chars_pattern, '', text)
    text = re.sub(r'\u200d(?=\()', '', text)
    
    pattern = r'\((s\d+)\)'
    new_text = re.sub(pattern, replacer, text)
    
    return new_text

def replace_footnote_markers_filter(text, footnotes_dict={}):
    """Filter to replace footnote markers in text."""
    if not text:
        return ""
    processed_text, _ = process_footnotes_text(text, footnotes_dict)
    return processed_text

def format_dandas(text):
    """
    Adds spaces around danda symbols (| || । ॥) and cleans up extra spaces.
    Safe to use on strings that might be None.
    """
    if not text or not isinstance(text, str):
        return text

    # --- STEP 1: Normalize Double Dandas ---
    # Convert ASCII ||, spaced | |, Devanagari ।। (two singles), and OCR II to ॥
    # IMPORTANT: We must catch '।।' (two U+0964) before processing singles!
    text = re.sub(r'\|\|', '॥', text)       
    text = re.sub(r'\|\s*\|', '॥', text)    
    text = re.sub(r'।।', '॥', text)         
    text = re.sub(r'II', '॥', text)         

    # --- STEP 2: Normalize Single Danda ---
    # Convert remaining ASCII | to Devanagari ।
    text = text.replace('|', '।')

    # --- STEP 3: Apply Spacing Rules ---
    
    # Rule B: Double Danda (॥) -> Standard spaces
    text = text.replace('॥', r' ॥ ')

    # --- STEP 4: Cleanup ---
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # --- STEP 5: Prevent Line Breaks in Mantra Numbers ---
    danda_pattern = r'(?:\|\||॥)'      
    digits = r'[\d०-९]+'        
    pattern = rf'({danda_pattern})\s+({digits})\s+({danda_pattern})'
    text = re.sub(pattern, r'\\mbox{\1 \2 \3}', text)

    # Rule A: Single Danda (।) -> Add \enspace BEFORE it
    # \enspace is 0.5em, roughly the width of a digit, very visible.
    # We also keep a normal space after it.
    text = text.replace('।', r'\enspace । ')

    return text

def clean_stack_arg(text):
    r"""
    Aggressively removes LaTeX newlines, paragraphs, comments, and line breaks.
    """
    if not text:
        return ""
    text = re.sub(r'\\+newline', '', text)
    text = re.sub(r'\\par', '', text)
    text = text.replace('%', '').replace('\n', ' ').replace('\r', '')
    return text.strip()

def escape_for_latex(data):
    if isinstance(data, dict):
        new_data = {}
        for key in data.keys():
            if key in ('malayalam-mantra-sets', 'corrected-mantra_sets', 'mantra_sets'):
                new_data[key] = data[key]
            else:
                new_data[key] = escape_for_latex(data[key])
        return new_data
    elif isinstance(data, list):
        return [escape_for_latex(item) for item in data]
    elif isinstance(data, str):
        latex_special_chars = {
            "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
            "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\^{}",
            "\\": r"\textbackslash{}", "\n": " ", "-": r"{-}",
            "\xA0": "~", "[": r"{[}", "]": r"{]}",
        }
        return "".join([latex_special_chars.get(c, c) for c in data])

# --- Devanagari LaTeX Filters & Renderers ---
def _format_deva_word_latex(word: str, with_modifiers: bool = True) -> str:
    """Format any inline swara modifiers inside Devanagari words with a small gap."""
    if not word:
        return ""
    if not with_modifiers:
        for m_ch in ('_', '·', 'ॱ', '.', ',', '\\', '┃', 'L', '╷', '^', '⁀', '∧', '✓'):
            word = word.replace(m_ch, '')
        return word.replace('&', r'\&').replace('%', r'\%').replace('$', r'\$').replace('#', r'\#')
        
    gap = r"\hspace{0.18em}"
    res = []
    i = 0
    while i < len(word):
        ch = word[i]
        if ch == '_':
            res.append(r"\underbarMark{}")
        elif ch in ('·', 'ॱ', '़'):
            res.append(f"{{\\swarafont \\textcolor{{ModifierSkyBlue}}{{\\raisebox{{0.25ex}}{{\\hspace{{0.08em}}\\char\"E001}}}}{gap}}}")
        elif ch == '.':
            res.append(f"{{\\textcolor{{ModifierSkyBlue}}{{\\textbf{{.}}}}{gap}}}")
        elif ch == ',':
            res.append(f"{{\\textcolor{{ModifierSkyBlue}}{{\\textbf{{,}}}}{gap}}}")
        elif ch == '\\':
            res.append(f"{{\\swarafont \\textcolor{{ModifierSkyBlue}}{{\\raisebox{{-0.35ex}}{{\\hspace{{-0.15em}}\\char\"E003}}}}{gap}}}")
        elif ch in ('┃', 'L'):
            res.append(f"{{\\swarafont \\textcolor{{ModifierSkyBlue}}{{\\raisebox{{0.05ex}}{{\\hspace{{0.05em}}\\char\"E002}}}}\\hspace{{0.18em}}}}")
        elif ch == '╷':
            res.append(f"{{\\swarafont \\textcolor{{ModifierSkyBlue}}{{\\raisebox{{0.15ex}}{{\\hspace{{0.04em}}\\char\"E008}}}}{gap}}}")
        elif ch == '&':
            res.append(r"\&")
        elif ch == '%':
            res.append(r"\%")
        elif ch == '$':
            res.append(r"\$")
        elif ch == '#':
            res.append(r"\#")
        else:
            res.append(ch)
        i += 1
    return "".join(res)


def _apply_deva_modifier_latex(chunk: str, mod: str) -> str:
    """Apply swara modifier styling in LaTeX with zero horizontal footprint and a small following gap."""
    m = mod.strip('()')
    
    # Standalone punctuation/spacing modifiers
    if m in ('C', 'c', '·', 'ॱ', '़', '\uE001'):
        glyph = r"\rlap{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\raisebox{0.78ex}{\hspace{0.02em}\char" + '"E001}}}}'
        return f"{chunk}{glyph}"
    elif m in ('E', 'e', '┃', '\uE002'):
        glyph = r"{\swarafont \textcolor{ModifierSkyBlue}{\textbf{\raisebox{-0.18ex}{\hspace{0.05em}\char" + '"E002}}}}' + r"\hspace{0.12em}"
        return f"{chunk}{glyph}"
    elif m == '.':
        glyph = r"{\Large\textcolor{ModifierSkyBlue}{\textbf{.}}}" + r"\hspace{0.08em}"
        return f"{chunk}{glyph}"
    elif m == ',':
        glyph = r"{\Large\textcolor{ModifierSkyBlue}{\textbf{,}}}" + r"\hspace{0.08em}"
        return f"{chunk}{glyph}"
        
    # Overhead Conjunct Arc (MOD-A2): centered over the syllable itself
    elif m in ('A2', 'a2', 'A_2', 'a_2', '\uE02E'):
        return f"\\arcOverSyllable{{{chunk}}}"
        
    # Zero-width overlay/stacked modifiers (strictly zero extra horizontal gap!)
    elif m in ('G', 'g', '\\', '\uE003'):
        return f"\\modGUnder{{{chunk}}}"
    elif m in ('A', 'a', '⁀', '\uE004'):
        glyph = r"\rlap{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\raisebox{1.18ex}{\hspace{-0.38em}\char" + '"E004}}}}'
        return f"{chunk}{glyph}"
    elif m in ('D', 'd', '∧', 'Ʌ', '\uE006'):
        glyph = r"\rlap{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\raisebox{1.15ex}{\hspace{-0.32em}\char" + '"E006}}}}'
        return f"{chunk}{glyph}"
    elif m in ('A1', 'a1', 'A_1', 'a_1', '\uE00D'):
        glyph = r"\rlap{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\raisebox{1.18ex}{\char" + '"E00D}}}}'
        return f"{chunk}{glyph}"
    elif m in ('D1', 'd1', 'D_1', 'd_1', '↗', '\uE00E'):
        glyph = r"\rlap{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\raisebox{1.05ex}{\hspace{0.04em}\char" + '"E00E}}}}'
        return f"{chunk}{glyph}"
    elif m in ('D2', 'd2', 'D_2', 'd_2', '✓', '\uE00F'):
        glyph = r"\rlap{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\raisebox{1.05ex}{\hspace{0.04em}\char" + '"E00F}}}}'
        return f"{chunk}{glyph}"
    elif m in ('H', 'h', '|', '\uE00C'):
        glyph = r"\rlap{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\raisebox{0.48ex}{\hspace{-0.18em}\char" + '"E00C}}}}'
        return f"{chunk}{glyph}"
    elif m in ('F', 'f', '╷', '\uE008'):
        glyph = r"\rlap{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\raisebox{1.05ex}{\hspace{0.04em}\char" + '"E008}}}}'
        return f"{chunk}{glyph}"
    elif m in ('B', 'b', '^', '˄', '/\\', '\uE005'):
        glyph = r"\rlap{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\raisebox{1.15ex}{\hspace{-0.32em}\char" + '"E005}}}}'
        return f"{chunk}{glyph}"
    elif m in ('B1', 'b1', 'B_1', 'b_1', '/', '\uE02C'):
        glyph = r"\rlap{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\raisebox{1.15ex}{\hspace{-0.32em}\char" + '"E02C}}}}'
        return f"{chunk}{glyph}"
    elif m in ('I', 'i', '⫽', '\uE02A'):
        glyph = r"\rlap{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\raisebox{0.50ex}{\hspace{0.04em}\char" + '"E02A}}}}'
        return f"{chunk}{glyph}"
    elif m in ('J', 'j', '¯', '\uE02B'):
        glyph = r"\rlap{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\raisebox{0.80ex}{\hspace{0.04em}\char" + '"E02B}}}}'
        return f"{chunk}{glyph}"
    elif m in ('K', 'k', '⨯', '\uE02D'):
        glyph = r"\rlap{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\raisebox{0.50ex}{\hspace{0.04em}\char" + '"E02D}}}}'
        return f"{chunk}{glyph}"
    elif m == '_':
        return f"{chunk}\\underbarMark{{}}"
    else:
        clean_mod = mod.replace('^', r'\^{}').replace('_', r'\_').replace('\\', r'\textbackslash{}').replace('$', r'\$')
        return f"{chunk}({clean_mod})"


def _format_single_deva_word_latex(tok, with_modifiers=True, exclude_mods=None, exclude_swara=False):
    """Format a single Devanagari word token with swara stacking and modifiers."""
    if exclude_mods is None:
        exclude_mods = set()
    word = tok.get('word', '')
    swara = tok.get('swara', '')
    visarga = tok.get('visarga', '')
    if visarga:
        word += visarga
    
    if not word or word in ('.', ','):
        if word == '.':
            return r"{\Large\textcolor{ModifierSkyBlue}{\textbf{.}}}\hspace{0.08em}"
        elif word == ',':
            return r"{\Large\textcolor{ModifierSkyBlue}{\textbf{,}}}\hspace{0.08em}"
        return ""
    
    if with_modifiers:
        core_word = word.rstrip('_,.\\·ॱ┃L╷^⁀∧✓़')
        trailing_punct = word[len(core_word):]
        sw_parts, mods = _parse_swara_and_modifiers(swara) if swara else ([], [])
        mods = [m for m in mods if m not in exclude_mods and m.strip('()') not in exclude_mods]
    else:
        core_word = word.rstrip('_,.\\·ॱ┃L╷^⁀∧✓़')
        trailing_punct = ''
        sw_parts, _ = _parse_swara_and_modifiers(swara) if swara else ([], [])
        mods = []
    
    if not core_word:
        res = []
        for p in word:
            if p == '.':
                res.append(r"{\Large\textcolor{ModifierSkyBlue}{\textbf{.}}}\hspace{0.08em}")
            elif p == ',':
                res.append(r"{\Large\textcolor{ModifierSkyBlue}{\textbf{,}}}\hspace{0.08em}")
            elif p == '_':
                res.append(r"\underbarMark{}")
            else:
                res.append(_format_deva_word_latex(p, with_modifiers=with_modifiers))
        return "".join(res)

    mod_c_set = {'C', 'c', '·', 'ॱ', '़', '\uE001'}
    mod_h_set = {'H', 'h', '|', '│', '॑', 'ˈ', '\uE00C'}
    
    has_mod_c = any(m.strip('()') in mod_c_set for m in mods)
    has_mod_h = any(m.strip('()') in mod_h_set for m in mods)
    
    mods = [m for m in mods if m.strip('()') not in mod_c_set and m.strip('()') not in mod_h_set]

    sw_str = "" if exclude_swara else (" ".join(sw_parts) if sw_parts else "")
    
    syllables = split_deva_syllables(core_word) if core_word else []
    last_syl = syllables.pop() if syllables else ''
    
    word_chunks = []
    for syl in syllables:
        syl_formatted = _format_deva_word_latex(syl, with_modifiers=with_modifiers)
        word_chunks.append(syl_formatted)
    
    last_syl_formatted = _format_deva_word_latex(last_syl, with_modifiers=with_modifiers) if last_syl else ''
    
    # Syllable-level modifiers applied directly to last_syl_formatted before stacking
    if with_modifiers and last_syl_formatted:
        has_mod_g = any(m.strip('()') in ('G', 'g', '\\', '\uE003') for m in mods)
        if has_mod_g:
            mods = [m for m in mods if m.strip('()') not in ('G', 'g', '\\', '\uE003')]
            last_syl_formatted = f"\\modGUnder{{{last_syl_formatted}}}"

        # Attach MOD-C (upper shoulder dot) at ~0.78ex height right above top-right of syllable
        if has_mod_c:
            last_syl_formatted += r"\rlap{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\raisebox{0.4ex}{\hspace{-0.1em}\char" + '"E001}}}}'
            
        # Attach MOD-H (high pitch swarita) at ~0.48ex height
        if has_mod_h:
            last_syl_formatted += r"\rlap{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\raisebox{0.2ex}{\hspace{-0.3em}\char" + '"E00C}}}}'

        syl_mods = []
        outer_mods = []
        for m in mods:
            m_clean = m.strip('()')
            if m_clean in ('E', 'e', '┃', '\uE002', '_', '.', ','):
                syl_mods.append(m)
            else:
                outer_mods.append(m)
        
        if trailing_punct:
            for p in trailing_punct:
                if p not in exclude_mods:
                    if p == '.':
                        last_syl_formatted += r"{\Large\textcolor{ModifierSkyBlue}{\textbf{.}}}\hspace{0.08em}"
                    elif p == ',':
                        last_syl_formatted += r"{}\hspace{0.04em}{\Large\textcolor{ModifierSkyBlue}{\textbf{,}}}\hspace{0.08em}"
                    elif p == '_':
                        last_syl_formatted += r"\underbarMark{}"
                    else:
                        last_syl_formatted = _apply_deva_modifier_latex(last_syl_formatted, p)
        for sm in syl_mods:
            if sm == '.':
                last_syl_formatted += r"{\Large\textcolor{ModifierSkyBlue}{\textbf{.}}}\hspace{0.08em}"
            elif sm == ',':
                last_syl_formatted += r"{}\hspace{0.04em}{\Large\textcolor{ModifierSkyBlue}{\textbf{,}}}\hspace{0.08em}"
            elif sm == '_':
                last_syl_formatted += r"\underbarMark{}"
            else:
                last_syl_formatted = _apply_deva_modifier_latex(last_syl_formatted, sm)
        
        mods = outer_mods

    if sw_str and last_syl_formatted:
        sw_styled = f"{{\\smallredfont \\textcolor{{SwaraRed}}{{{sw_str}}}}}"
        chunk = f"\\stackcenter{{{last_syl_formatted}}}{{{sw_styled}}}"
    elif sw_str and not last_syl_formatted:
        sw_styled = f"{{\\smallredfont \\textcolor{{SwaraRed}}{{{sw_str}}}}}"
        chunk = f"\\stackcenter{{\\phantom{{अ}}}}{{{sw_styled}}}"
    else:
        chunk = f"{{{last_syl_formatted}}}"
    
    if with_modifiers and mods:
        for mod in mods:
            chunk = _apply_deva_modifier_latex(chunk, mod)
    
    word_chunks.append(chunk)
    return "".join(word_chunks)


def _render_devanagari_mantra_body(subsection, subsection_key=None, seen_markers=None, with_modifiers: bool = None):
    """Helper to render Devanagari mantra body with swaras and modifiers."""
    if seen_markers is None:
        seen_markers = set()
    if with_modifiers is None:
        with_modifiers = True
        
    from core.swara_engine import tokenize_mantra_line
    
    content_lines = subsection.get('content_lines') or subsection.get('content')
    if content_lines:
        paras = []
        for line in content_lines:
            # content_lines are already escaped by the top-level escape_for_latex(data) in CreatePdf
            line_fmt = format_dandas(line)
            paras.append(f"{{\\sloppy {line_fmt} \\par}}")
        return paras

    mantra_sets = subsection.get('corrected-mantra_sets', [])
    if not mantra_sets:
        mantra_sets = subsection.get('mantra_sets', [])
    if not mantra_sets:
        return []

    MOD_A_SET = {'A', 'a', '⁀', '\uE004', '╭╮', '͡'}
    MOD_A1_SET = {'A1', 'a1', 'A_1', 'a_1', '\uE00D'}
    MOD_A2_SET = {'A2', 'a2', 'A_2', 'a_2', '\uE02E'}
    MOD_B_SET = {'B', 'b', '^', '˄', '/\\', '\uE005'}
    MOD_D_SET = {'D', 'd', '∧', 'Ʌ', '\uE006'}
    DEVA_DIGITS = str.maketrans('0123456789', '०१२३४५६७८९')
    
    footnote_data = subsection.get('footnotes', {})
    formatted_paragraphs = []
    
    for mantra_set in mantra_sets:
        line = mantra_set.get('corrected-mantra') or mantra_set.get('mantra', '')
        if not line:
            continue
        tokens = tokenize_mantra_line(line)
        paragraph_buffer = []
        
        idx = 0
        while idx < len(tokens):
            v_count, v_num = _match_verse_num_marker(tokens, idx)
            if v_count > 0:
                v_num_deva = str(v_num).translate(DEVA_DIGITS)
                paragraph_buffer.append(f"\\nolinebreak\\hspace{{0.20em}}\\mbox{{॥ {v_num_deva} ॥}}")
                full_paragraph = "".join(paragraph_buffer)
                formatted_paragraphs.append(f"{{\\noindent\\centering\\sloppy {full_paragraph}\\par}}")
                formatted_paragraphs.append(r"\vspace{0.35em}")
                paragraph_buffer = []
                idx += v_count
                continue
            
            tok = tokens[idx]
            t = tok['type']
            
            if t == 'space':
                prev_tok = tokens[idx - 1] if idx > 0 else None
                next_tok = tokens[idx + 1] if idx + 1 < len(tokens) else None
                
                prev_is_danda = (prev_tok and prev_tok['type'] in ('danda', 'footnote'))
                next_is_danda = (next_tok and next_tok['type'] in ('danda', 'footnote'))
                
                if prev_is_danda or next_is_danda:
                    paragraph_buffer.append(" ")
                else:
                    prev_multi = (prev_tok and _has_multiple_swaras(prev_tok))
                    next_multi = (next_tok and _has_multiple_swaras(next_tok))
                    if prev_multi or next_multi:
                        paragraph_buffer.append(r"\hspace{0.30em} ")
                    else:
                        paragraph_buffer.append(r"\hskip 0pt plus 1.5pt\allowbreak ")
            elif t == 'danda':
                ch = tok['char']
                next_m_idx = idx + 1
                while next_m_idx < len(tokens) and tokens[next_m_idx]['type'] == 'space':
                    next_m_idx += 1
                if with_modifiers and next_m_idx < len(tokens) and tokens[next_m_idx]['type'] == 'marker':
                    m_str = tokens[next_m_idx]['marker'].strip('()')
                    if m_str in MOD_A1_SET and paragraph_buffer:
                        third_w_idx = next_m_idx + 1
                        while third_w_idx < len(tokens) and tokens[third_w_idx]['type'] == 'space':
                            third_w_idx += 1
                        if third_w_idx < len(tokens) and tokens[third_w_idx]['type'] == 'word':
                            while paragraph_buffer and ('\\hskip' in paragraph_buffer[-1] or '\\hspace' in paragraph_buffer[-1] or paragraph_buffer[-1].isspace()):
                                paragraph_buffer.pop()
                            prev_chunk = paragraph_buffer.pop() if paragraph_buffer else ""
                            next_tok = tokens[third_w_idx]
                            chunk2 = _format_single_deva_word_latex(next_tok, with_modifiers=True)
                            paragraph_buffer.append(f"\\mbox{{{prev_chunk} \\dandaWithArc{{{ch}}} {chunk2}}}")
                            idx = third_w_idx + 1
                            continue
                if ch == '।':
                    paragraph_buffer.append(r"\nolinebreak\hspace{0.04em}।\allowbreak\hspace{0.20em} ")
                elif ch == '॥':
                    paragraph_buffer.append(r"\nolinebreak\hspace{0.06em}॥\allowbreak\hspace{0.22em} ")
                else:
                    paragraph_buffer.append(f"\\nolinebreak\\hspace{{0.04em}}{ch}\\allowbreak\\hspace{{0.20em}} ")
            elif t == 'marker':
                if with_modifiers:
                    m_str = tok['marker'].strip('()')
                    if m_str in MOD_A_SET or m_str in MOD_A1_SET:
                        next_w_idx = idx + 1
                        while next_w_idx < len(tokens) and tokens[next_w_idx]['type'] == 'space':
                            next_w_idx += 1
                        if next_w_idx < len(tokens) and tokens[next_w_idx]['type'] == 'danda' and paragraph_buffer:
                            # Standalone arc over danda
                            d_char = tokens[next_w_idx]['char']
                            third_idx = next_w_idx + 1
                            while third_idx < len(tokens) and tokens[third_idx]['type'] == 'space':
                                third_idx += 1
                            if third_idx < len(tokens) and tokens[third_idx]['type'] == 'word':
                                while paragraph_buffer and ('\\hskip' in paragraph_buffer[-1] or '\\hspace' in paragraph_buffer[-1] or paragraph_buffer[-1].isspace()):
                                    paragraph_buffer.pop()
                                prev_chunk = paragraph_buffer.pop() if paragraph_buffer else ""
                                next_tok = tokens[third_idx]
                                chunk2 = _format_single_deva_word_latex(next_tok, with_modifiers=True)
                                paragraph_buffer.append(f"\\mbox{{{prev_chunk} \\dandaWithArc{{{d_char}}} {chunk2}}}")
                                idx = third_idx + 1
                                continue
                        elif next_w_idx < len(tokens) and tokens[next_w_idx]['type'] == 'word' and paragraph_buffer:
                            prev_chunk = paragraph_buffer.pop()
                            next_tok = tokens[next_w_idx]
                            chunk2 = _format_single_deva_word_latex(next_tok, with_modifiers=True)
                            arc_glyph = r"\rlap{\swarafont \textcolor{ModifierSkyBlue}{\raisebox{1.18ex}{\hspace{-0.38em}\char" + '"E004}}}'
                            paragraph_buffer.append(f"\\mbox{{{prev_chunk}{arc_glyph}{chunk2}}}")
                            idx = next_w_idx + 1
                            continue
                    elif m_str in MOD_D_SET:
                        next_w_idx = idx + 1
                        while next_w_idx < len(tokens) and tokens[next_w_idx]['type'] == 'space':
                            next_w_idx += 1
                        if next_w_idx < len(tokens) and tokens[next_w_idx]['type'] == 'word' and paragraph_buffer:
                            prev_chunk = paragraph_buffer.pop()
                            next_tok = tokens[next_w_idx]
                            chunk2 = _format_single_deva_word_latex(next_tok, with_modifiers=True)
                            d_glyph = r"\rlap{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\raisebox{1.18ex}{\hspace{-0.32em}\char" + '"E006}}}}'
                            paragraph_buffer.append(f"\\mbox{{{prev_chunk}{d_glyph}{chunk2}}}")
                            idx = next_w_idx + 1
                            continue
                    m_esc = _apply_deva_modifier_latex("", tok['marker'])
                    paragraph_buffer.append(m_esc)
            elif t == 'footnote':
                marker = tok.get('text', '').strip('()')
                fn_text = footnote_data.get(marker, '')
                if fn_text:
                    safe_key = subsection_key if subsection_key else "unknown"
                    label = f"fn:{safe_key}:{marker}"
                    if marker in seen_markers:
                        paragraph_buffer.append(f"\\rule{{0pt}}{{2.5ex}}\\textsuperscript{{\\raisebox{{1.2ex}}{{\\normalfont\\ref{{{label}}}}}}}")
                    else:
                        paragraph_buffer.append(f"\\rule{{0pt}}{{2.5ex}}\\footnote{{{fn_text}\\label{{{label}}}}}")
                        seen_markers.add(marker)
                        if LATEX_DOC_MARKERS_MAP is not None:
                            LATEX_DOC_MARKERS_MAP[marker] = label
                elif LATEX_DOC_MARKERS_MAP and marker in LATEX_DOC_MARKERS_MAP:
                    label = LATEX_DOC_MARKERS_MAP[marker]
                    if seen_markers is not None:
                        seen_markers.add(marker)
                    paragraph_buffer.append(f"\\rule{{0pt}}{{2.5ex}}\\textsuperscript{{\\raisebox{{1.2ex}}{{\\normalfont\\ref{{{label}}}}}}}")
            elif t == 'word':
                sw = tok.get('swara', '')
                sw_parts, tok_mods = _parse_swara_and_modifiers(sw)
                has_mod_a1 = any(m.strip('()') in MOD_A1_SET for m in tok_mods)
                has_mod_a = any(m.strip('()') in MOD_A_SET for m in tok_mods)
                has_mod_b = any(m.strip('()') in MOD_B_SET for m in tok_mods)
                has_mod_d = any(m.strip('()') in MOD_D_SET for m in tok_mods)
                
                # Check if this word is followed by a danda
                d_idx = idx + 1
                while d_idx < len(tokens) and tokens[d_idx]['type'] == 'space':
                    d_idx += 1
                next_is_danda = (d_idx < len(tokens) and tokens[d_idx]['type'] == 'danda')
                
                # If mod is MOD-A / ⁀ but followed by danda, it is an arc over danda (MOD-A1)
                if has_mod_a and next_is_danda:
                    has_mod_a1 = True
                    has_mod_a = False
                
                # Peak Elevation Caret (MOD-B): bridges across 2 syllables with swara sitting atop apex
                if has_mod_b and with_modifiers:
                    next_w_idx = idx + 1
                    while next_w_idx < len(tokens) and tokens[next_w_idx]['type'] == 'space':
                        next_w_idx += 1
                    if next_w_idx < len(tokens) and tokens[next_w_idx]['type'] == 'word':
                        next_tok = tokens[next_w_idx]
                        next_sw = next_tok.get('swara', '')
                        _, next_mods = _parse_swara_and_modifiers(next_sw)
                        next_has_a1 = any(m.strip('()') in MOD_A1_SET for m in next_mods)
                        next_has_a = any(m.strip('()') in MOD_A_SET for m in next_mods)
                        
                        d2_idx = next_w_idx + 1
                        while d2_idx < len(tokens) and tokens[d2_idx]['type'] == 'space':
                            d2_idx += 1
                        next_tok_next_is_danda = (d2_idx < len(tokens) and tokens[d2_idx]['type'] == 'danda')
                        if next_has_a and next_tok_next_is_danda:
                            next_has_a1 = True
                            
                        if next_has_a1 and next_tok_next_is_danda:
                            # Chained MOD-B + MOD-A1 over danda: e.g. घा(^)तो(A1) । हाइ
                            d_char = tokens[d2_idx]['char']
                            third_w_idx = d2_idx + 1
                            while third_w_idx < len(tokens) and tokens[third_w_idx]['type'] == 'space':
                                third_w_idx += 1
                            if third_w_idx < len(tokens) and tokens[third_w_idx]['type'] == 'word':
                                third_tok = tokens[third_w_idx]
                                sw_label = " ".join(sw_parts) if sw_parts else ""
                                chunk1 = _format_single_deva_word_latex(tok, with_modifiers=True, exclude_mods=MOD_B_SET, exclude_swara=True)
                                chunk2 = _format_single_deva_word_latex(next_tok, with_modifiers=True, exclude_mods=MOD_A1_SET | MOD_A_SET)
                                chunk3 = _format_single_deva_word_latex(third_tok, with_modifiers=True)
                                combined_mbox = f"\\mbox{{{chunk1}\\caretWithSwara{{{sw_label}}}{chunk2} \\dandaWithArc{{{d_char}}} {chunk3}}}"
                                paragraph_buffer.append(combined_mbox)
                                idx = third_w_idx + 1
                                continue
                        
                        sw_label = " ".join(sw_parts) if sw_parts else ""
                        chunk1 = _format_single_deva_word_latex(tok, with_modifiers=True, exclude_mods=MOD_B_SET, exclude_swara=True)
                        chunk2 = _format_single_deva_word_latex(next_tok, with_modifiers=True)
                        paragraph_buffer.append(f"\\mbox{{{chunk1}\\caretWithSwara{{{sw_label}}}{chunk2}}}")
                        idx = next_w_idx + 1
                        continue
                
                if has_mod_d and with_modifiers:
                    next_w_idx = idx + 1
                    while next_w_idx < len(tokens) and tokens[next_w_idx]['type'] == 'space':
                        next_w_idx += 1
                    
                    if next_w_idx < len(tokens) and tokens[next_w_idx]['type'] == 'word':
                        next_tok = tokens[next_w_idx]
                        next_sw = next_tok.get('swara', '')
                        _, next_mods = _parse_swara_and_modifiers(next_sw)
                        next_has_a1 = any(m.strip('()') in MOD_A1_SET for m in next_mods)
                        next_has_a = any(m.strip('()') in MOD_A_SET for m in next_mods)
                        
                        d2_idx = next_w_idx + 1
                        while d2_idx < len(tokens) and tokens[d2_idx]['type'] == 'space':
                            d2_idx += 1
                        next_tok_next_is_danda = (d2_idx < len(tokens) and tokens[d2_idx]['type'] == 'danda')
                        if next_has_a and next_tok_next_is_danda:
                            next_has_a1 = True
                        
                        if next_has_a1 and next_tok_next_is_danda:
                            # Chained MOD-D + MOD-A1 over danda: e.g. बाहू(∧)तो(A1) । हाइ
                            d_char = tokens[d2_idx]['char']
                            third_w_idx = d2_idx + 1
                            while third_w_idx < len(tokens) and tokens[third_w_idx]['type'] == 'space':
                                third_w_idx += 1
                            if third_w_idx < len(tokens) and tokens[third_w_idx]['type'] == 'word':
                                third_tok = tokens[third_w_idx]
                                chunk1 = _format_single_deva_word_latex(tok, with_modifiers=True, exclude_mods=MOD_D_SET)
                                chunk2 = _format_single_deva_word_latex(next_tok, with_modifiers=True, exclude_mods=MOD_A1_SET | MOD_D_SET | MOD_A_SET)
                                chunk3 = _format_single_deva_word_latex(third_tok, with_modifiers=True)
                                d_glyph = r'\hspace{0.18em}\makebox[0pt][c]{\raisebox{1.18ex}{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\char"E006}}}}\hspace{0.18em}'
                                combined_mbox = f"\\mbox{{{chunk1}{d_glyph}{chunk2} \\dandaWithArc{{{d_char}}} {chunk3}}}"
                                paragraph_buffer.append(combined_mbox)
                                idx = third_w_idx + 1
                                continue
                        
                        chunk1 = _format_single_deva_word_latex(tok, with_modifiers=True, exclude_mods=MOD_D_SET)
                        chunk2 = _format_single_deva_word_latex(next_tok, with_modifiers=True)
                        d_glyph = r'\hspace{0.18em}\makebox[0pt][c]{\raisebox{1.18ex}{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\char"E006}}}}\hspace{0.18em}'
                        combined_mbox = f"\\mbox{{{chunk1}{d_glyph}{chunk2}}}"
                        paragraph_buffer.append(combined_mbox)
                        idx = next_w_idx + 1
                        continue

                if has_mod_a1 and with_modifiers and next_is_danda:
                    d_char = tokens[d_idx]['char']
                    next_w_idx = d_idx + 1
                    while next_w_idx < len(tokens) and tokens[next_w_idx]['type'] == 'space':
                        next_w_idx += 1
                    if next_w_idx < len(tokens) and tokens[next_w_idx]['type'] == 'word':
                        next_tok = tokens[next_w_idx]
                        chunk1 = _format_single_deva_word_latex(tok, with_modifiers=True, exclude_mods=MOD_A1_SET | MOD_A_SET)
                        chunk2 = _format_single_deva_word_latex(next_tok, with_modifiers=True)
                        combined_mbox = f"\\mbox{{{chunk1} \\dandaWithArc{{{d_char}}} {chunk2}}}"
                        paragraph_buffer.append(combined_mbox)
                        idx = next_w_idx + 1
                        continue
                
                if has_mod_a and with_modifiers:
                    next_w_idx = idx + 1
                    while next_w_idx < len(tokens) and tokens[next_w_idx]['type'] == 'space':
                        next_w_idx += 1
                    
                    if next_w_idx < len(tokens) and tokens[next_w_idx]['type'] == 'word':
                        next_tok = tokens[next_w_idx]
                        chunk1 = _format_single_deva_word_latex(tok, with_modifiers=True, exclude_mods=MOD_A_SET)
                        chunk2 = _format_single_deva_word_latex(next_tok, with_modifiers=True)
                        arc_glyph = r"\rlap{\swarafont \textcolor{ModifierSkyBlue}{\raisebox{1.18ex}{\hspace{-0.38em}\char" + '"E004}}}'
                        combined_mbox = f"\\mbox{{{chunk1}{arc_glyph}{chunk2}}}"
                        paragraph_buffer.append(combined_mbox)
                        idx = next_w_idx + 1
                        continue
                
                chunk = _format_single_deva_word_latex(tok, with_modifiers=with_modifiers)
                paragraph_buffer.append(chunk)
            idx += 1
            
        if paragraph_buffer:
            full_paragraph = "".join(paragraph_buffer)
            formatted_paragraphs.append(f"{{\\noindent\\centering\\sloppy {full_paragraph}\\par}}")
            formatted_paragraphs.append(r"\vspace{0.8em}")
            
    return formatted_paragraphs


def format_mantra_sets(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None, subsection_key=None, toc_level='section'):
    
    formatted_output = []
    
    # --- FOOTNOTE TRACKING ---
    seen_markers = set()
    
    # --- DATA EXTRACTION ---
    current_rik_id = subsection.get('rik_id')
    current_rik_ids = subsection.get('rik_ids', [current_rik_id] if current_rik_id else [])
    string_1 = subsection.get('rik_metadata', '')
    string_2 = subsection.get('rik_text', '')
    string_3 = subsection.get('saman_metadata', '')
    
    # Determine if we should show rik_metadata and rik_text
    # Show if: first subsection, OR if any rik_id in current rik_ids differs from prev_rik_id
    # This ensures that when a subsection spans multiple Riks (e.g., [7, 8]) and Rik 7 was already
    # shown, we still display the combined text that includes Rik 8
    show_rik_info = (prev_rik_id is None) or (current_rik_id != prev_rik_id)
    # Also show if rik_ids contains multiple Riks and the last one differs from prev
    if not show_rik_info and len(current_rik_ids) > 1:
        # If we have multiple Riks in this subsection, check if the MAX Rik ID is new
        max_rik_id = max(current_rik_ids) if current_rik_ids else None
        if max_rik_id is not None and max_rik_id != prev_rik_id:
            show_rik_info = True
    
    # Clean titles for Display
    # Clean titles for Display
    display_sub_title = re.sub(r'^([|॥]+)\s*', r'\1 ', subsection_title)
    
    # --- SPLIT HEADER FOR INDEX/TOC ---
    # The user wants TOC and Index to ONLY have the Header (excluding Metadata)
    # Since the input title string contains "|| Header || || Metadata ||", we must split it.
    
    samam_header_only = display_sub_title
    
    # Regex to capture first block: || Text ||  (Non-greedy)
    # We look for [Dandas] [Content] [Dandas]
    m_split = re.match(r'([|॥]+\s*.*?[|॥]+)', display_sub_title)
    if m_split:
        samam_header_only = m_split.group(1).strip()
    
    # Index title: Strip dandas from the Clean Header
    index_title = re.sub(r'[|॥]', '', samam_header_only).strip()

    # --- LAYOUT CONSTRUCTION ---
    
    # 1. Page Break / Indexing Logic
    formatted_output.append(r"\par\filbreak")              
    formatted_output.append(r"\phantomsection")
    if subsection_title:
        # Use Clean Header for TOC and Index
        # Ensure TOC entry has proper danda formatting
        toc_title = format_dandas(samam_header_only)
        if toc_level == 'subsection':
            formatted_output.append(f"\\addcontentsline{{toc}}{{section}}{{{toc_title}}}")
        elif toc_level == 'both':
            formatted_output.append(f"\\addcontentsline{{toc}}{{subsection}}{{{toc_title}}}")
        formatted_output.append(f"\\index{{{index_title}}}")

    # 2. String 1: Rik Metadata (Plain Centered) - Only if rik_id changed
    # COLOR: BLUE
    if string_1 and show_rik_info:
        s1 = format_dandas(string_1)
        s1 = process_footnotes_latex(s1, subsection.get('footnotes', {}), seen_markers, subsection_key)
        formatted_output.append(f"{{\\centering \\textcolor{{AccentPurple}}{{{s1}}} \\par}}")
        formatted_output.append(r"\vspace{0.6em}")

    # 3. String 2: Rik Text (With Vedic Accents, Upright) - Only if rik_id changed
    # COLOR: BLUE
    if string_2 and show_rik_info:
        # Step A: Remove Spaces (Samhita Mode)
        s2 = remove_mantra_spaces(string_2)
        # Step A.1: Fix Visarga-Accent Order
        # s2 = fix_visarga_accent_order_local(s2)
        # Step B: Handle Consecutive Accent Kerning
        s2 = handle_consecutive_accents(s2)
        # Step C: Replace Accents with LaTeX commands (with adjusted sizes)
        s2 = replace_accents(s2)
        # Process Footnotes in Rik Text
        s2 = process_footnotes_latex(s2, subsection.get('footnotes', {}), seen_markers, subsection_key)
        # Step D: Format Dandas (Spaces around dandas only)
        # s2 = format_dandas(s2) -- moved after splitting
        
        # Split multi-Rik text so each Rik is on its own line
        s2 = split_rik_lines_latex(s2)
        s2 = format_dandas(s2)
        
        # SAFETY PATCH: Remove any lingering \newline commands that might have snuck in
        s2 = s2.replace(r'\newline', ' ').replace(r'\textbackslash{}newline', ' ')
        
        # Output: Upright (not italics)
        formatted_output.append(f"{{\\centering \\textcolor{{blue}}{{{s2}}} \\par}}")
        
        # --- NEW: Layout grouping for Rik + Samam ---
        has_samam_content = bool(display_sub_title.strip() or string_3.strip() or subsection.get('mantra_sets'))
        if has_samam_content:
            formatted_output.append(r"\nopagebreak")                
            formatted_output.append(r"\vspace{0.3em}") # Reduced space to keep together
            formatted_output.append(r"\nopagebreak")
        else:
            formatted_output.append(r"\vspace{0.8em}")

    # 4. Combined Header: || Subsection header || || samam_metadata ||
    header_part = display_sub_title.strip()
    header_part = format_dandas(header_part)
    header_part = f"\\textbf{{\\textcolor{{AccentGreen}}{{{header_part}}}}}"  
    
    # COLOR: Samam Metadata -> BROWN
    meta_part = format_dandas(string_3).strip()
    meta_part = process_footnotes_latex(meta_part, subsection.get('footnotes', {}), seen_markers, subsection_key)
    if meta_part:
        meta_part = f"\\textcolor{{AccentBrown}}{{{meta_part}}}"
    
    combined_header = ""
    if header_part and meta_part:
        combined_header = f"{header_part} \\quad {meta_part}"
    elif header_part:
        combined_header = header_part
    elif meta_part:
        combined_header = meta_part
    
    if combined_header:
        formatted_output.append(f"{{\\centering {combined_header} \\par}}")
        
    # Procedure links are shown at section/supersection header level in template
    # No sama-level procedure links (subsection scope shown at header)

    # Keep header with mantra text
    formatted_output.append(r"\nopagebreak")                
    formatted_output.append(r"\vspace{0.15em}")
    formatted_output.append(r"\nopagebreak")

    # --- MANTRA CONTENT RENDERING ---
    body_paras = _render_devanagari_mantra_body(subsection, subsection_key, seen_markers)
    formatted_output.extend(body_paras)

    return "\n\n".join(formatted_output)


# ----------------------------------------------------
# RIK-ONLY FORMATTING (for separate output mode)
# ----------------------------------------------------
def format_rik_only(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None, subsection_key=None, toc_level='section', prev_rik_text=None):
    """
    Format only Rik content (rik_metadata and rik_text) for separate output mode.
    Skips all Samam-related content.
    """
    formatted_output = []
    
    # --- FOOTNOTE TRACKING ---
    seen_markers = set()
    
    current_rik_id = get_canonical_rik_id(subsection)
    string_1 = subsection.get('rik_metadata', '')
    string_2 = subsection.get('rik_text', '')
    
    # Skip if no Rik content
    if not string_1 and not string_2:
        return ""
    
    # Skip consecutive duplicate Rik text across multiple Samams
    if prev_rik_text and string_2 and string_2.strip() == prev_rik_text.strip():
        return ""

    # Only show if rik_id changed (avoid duplicates)
    show_rik_info = (prev_rik_id is None) or (current_rik_id != prev_rik_id)
    if not show_rik_info:
        return ""
    
    # Page Break / Indexing
    formatted_output.append(r"\par\filbreak")
    formatted_output.append(r"\phantomsection")
    
    rik_id_display = f"ऋक् {to_devanagari_numeral(current_rik_id)}" if current_rik_id else ""
    if rik_id_display:
        if toc_level == 'subsection':
            formatted_output.append(f"\\addcontentsline{{toc}}{{section}}{{{rik_id_display}}}")
        elif toc_level == 'both':
            formatted_output.append(f"\\addcontentsline{{toc}}{{subsection}}{{{rik_id_display}}}")

    # Rik Metadata
    if string_1:
        s1 = format_dandas(string_1)
        # Apply footnotes
        s1 = process_footnotes_latex(s1, subsection.get('footnotes', {}), seen_markers, subsection_key)
        formatted_output.append(f"{{\\centering \\textcolor{{AccentPurple}}{{{s1}}} \\par}}")
        formatted_output.append(r"\vspace{0.6em}")

    # Rik Text (with Vedic Accents)
    if string_2:
        s2 = remove_mantra_spaces(string_2)
        # s2 = fix_visarga_accent_order_local(s2)
        s2 = handle_consecutive_accents(s2)
        s2 = replace_accents(s2)
        # Apply footnotes
        s2 = process_footnotes_latex(s2, subsection.get('footnotes', {}), seen_markers, subsection_key)
        s2 = format_dandas(s2)
        formatted_output.append(f"{{\\centering \\textcolor{{blue}}{{{s2}}} \\par}}")
        formatted_output.append(r"\vspace{0.8em}")

    return "\n\n".join(formatted_output)


# ----------------------------------------------------
# SAMAM-ONLY FORMATTING (for separate output mode)
# ----------------------------------------------------
def format_samam_only(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None, subsection_key=None, toc_level='section'):
    """
    Format only Samam content (header, saman_metadata, mantra text) for separate output mode.
    Skips all Rik-related content.
    """
    formatted_output = []
    
    # --- FOOTNOTE TRACKING ---
    seen_markers = set()
    
    string_3 = subsection.get('saman_metadata', '')
    
    # Clean titles
    display_sub_title = re.sub(r'^([|॥]+)\s*', r'\1 ', subsection_title) if subsection_title else ""
    index_title = re.sub(r'[|॥]', '', subsection_title).strip() if subsection_title else ""

    # Page Break / Indexing
    formatted_output.append(r"\par\filbreak")
    formatted_output.append(r"\phantomsection")
    if subsection_title:
        toc_title = display_sub_title.strip()
        if toc_level == 'subsection':
            formatted_output.append(f"\\addcontentsline{{toc}}{{section}}{{{toc_title}}}")
        elif toc_level == 'both':
            formatted_output.append(f"\\addcontentsline{{toc}}{{subsection}}{{{toc_title}}}")
        formatted_output.append(f"\\index{{{index_title}}}")

    # Combined Header: Subsection header + samam_metadata
    header_part = display_sub_title.strip()
    header_part = f"\\textbf{{\\textcolor{{AccentGreen}}{{{header_part}}}}}" if header_part else ""
    
    meta_part = format_dandas(string_3).strip()
    meta_part = process_footnotes_latex(meta_part, subsection.get('footnotes', {}), seen_markers, subsection_key)
    if meta_part:
        meta_part = f"\\textcolor{{AccentBrown}}{{{meta_part}}}"
    
    combined_header = ""
    if header_part and meta_part:
        combined_header = f"{header_part} \\quad {meta_part}"
    elif header_part:
        combined_header = header_part
    elif meta_part:
        combined_header = meta_part
        
    # Procedure links are shown at section/supersection header level in template
    # No sama-level procedure links (handled at header)
    
    if combined_header:
         formatted_output.append(f"{{\\centering {combined_header} \\par}}")

    formatted_output.append(r"\nopagebreak")
    formatted_output.append(r"\vspace{0.5em}")
    formatted_output.append(r"\nopagebreak")

    # Mantra Content Rendering (Samam text only - no Rik text)
    body_paras = _render_devanagari_mantra_body(subsection, subsection_key, seen_markers)
    formatted_output.extend(body_paras)

    return "\n\n".join(formatted_output)


# ----------------------------------------------------
# RIK NO-METADATA FORMATTING (for nometa output mode)
# ----------------------------------------------------
def format_rik_nometa(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None, subsection_key=None, toc_level='section', prev_rik_text=None):
    """
    Format only Rik text (without rik_metadata) for nometa output mode.
    Skips all Samam-related content and metadata.
    """
    formatted_output = []
    
    # --- FOOTNOTE TRACKING ---
    seen_markers = set()
    
    current_rik_id = get_canonical_rik_id(subsection)
    string_2 = subsection.get('rik_text', '')
    
    # Skip if no Rik content
    if not string_2:
        return ""
    
    # Skip consecutive duplicate Rik text across multiple Samams
    if prev_rik_text and string_2.strip() == prev_rik_text.strip():
        return ""

    # Only show if rik_id changed (avoid duplicates)
    show_rik_info = (prev_rik_id is None) or (current_rik_id != prev_rik_id)
    if not show_rik_info:
        return ""
    
    # Page Break / Indexing
    formatted_output.append(r"\par\filbreak")
    formatted_output.append(r"\phantomsection")
    
    rik_id_display = f"ऋक् {to_devanagari_numeral(current_rik_id)}" if current_rik_id else ""
    if rik_id_display:
        if toc_level == 'subsection':
            formatted_output.append(f"\\addcontentsline{{toc}}{{section}}{{{rik_id_display}}}")
        elif toc_level == 'both':
            formatted_output.append(f"\\addcontentsline{{toc}}{{subsection}}{{{rik_id_display}}}")

    # Rik Text (with Vedic Accents) - NO METADATA
    if string_2:
        s2 = remove_mantra_spaces(string_2)
        s2 = handle_consecutive_accents(s2)
        s2 = replace_accents(s2)
        # Apply footnotes
        s2 = process_footnotes_latex(s2, subsection.get('footnotes', {}), seen_markers, subsection_key)
        # Split multi-Rik text so each Rik is on its own line
        s2 = split_rik_lines_latex(s2)
        s2 = format_dandas(s2)
        formatted_output.append(f"{{\\centering \\textcolor{{blue}}{{{s2}}} \\par}}")
        formatted_output.append(r"\vspace{0.8em}")

    return "\n\n".join(formatted_output)


# ----------------------------------------------------
# SAMAM NO-METADATA FORMATTING (for nometa output mode)
# ----------------------------------------------------
def format_samam_nometa(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None, subsection_key=None, toc_level='section'):
    """
    Format only Samam content (header, mantra text) for nometa output mode.
    Skips all Rik-related content and saman_metadata.
    """
    formatted_output = []
    
    # --- FOOTNOTE TRACKING ---
    seen_markers = set()
    
    # Clean titles - skip saman_metadata
    display_sub_title = re.sub(r'^([|॥]+)\s*', r'\1 ', subsection_title) if subsection_title else ""
    index_title = re.sub(r'[|॥]', '', subsection_title).strip() if subsection_title else ""

    # Page Break / Indexing
    formatted_output.append(r"\par\filbreak")
    formatted_output.append(r"\phantomsection")
    if subsection_title:
        toc_title = display_sub_title.strip()
        if toc_level == 'subsection':
            formatted_output.append(f"\\addcontentsline{{toc}}{{section}}{{{toc_title}}}")
        elif toc_level == 'both':
            formatted_output.append(f"\\addcontentsline{{toc}}{{subsection}}{{{toc_title}}}")
        formatted_output.append(f"\\index{{{index_title}}}")

    # Header only (NO saman_metadata)
    header_part = display_sub_title.strip()
    if header_part:
        header_part = f"\\textcolor{{AccentGreen}}{{{header_part}}}"
        formatted_output.append(f"{{\\centering \\textbf{{{header_part}}} \\par}}")

    formatted_output.append(r"\nopagebreak")
    formatted_output.append(r"\vspace{0.5em}")
    formatted_output.append(r"\nopagebreak")

    # Mantra Content Rendering (Samam text only - no metadata)
    body_paras = _render_devanagari_mantra_body(subsection, subsection_key, seen_markers)
    formatted_output.extend(body_paras)

    return "\n\n".join(formatted_output)

# --- Malayalam LaTeX Filters & Renderers ---
_ENGLISH_DIGITS = str.maketrans("०१२३४५६७८९൦൧൨൩൪൫൬൭൮൯", "01234567890123456789")

MODIFIER_DIRECT_MAP = {
    # Modifiers from updated Google Sheet (A..H)
    "A": "\uE004",  # Syllable Arc (Tie) ╭╮ / ⁀
    "B": "\uE005",  # Caret / Peak /\ / ^
    "C": "\uE001",  # High/Mid-Dot ॱ / ·
    "D": "\uE006",  # Chevron Roof Ʌ
    "E": "\uE002",  # Heavy Vertical ┃
    "F": "\uE002",  # Light Vertical ╷
    "G": "\uE003",  # Descending Tone \ / ⟍
    "H": "\uE002",  # Swarita ॑ / |

    # Lowercase variants
    "a": "\uE004", "b": "\uE005", "c": "\uE001", "d": "\uE006",
    "e": "\uE002", "f": "\uE002", "g": "\uE003", "h": "\uE002",

    # Direct Symbols matching "How to enter" column
    "^": "\uE005", "˄": "\uE005",
    "Ʌ": "\uE006", "/\\": "\uE006", "∧": "\uE006",
    "⁀": "\uE004", "͡": "\uE004", "╭╮": "\uE004",
    "ͦ": "\uE009", "˚": "\uE009",
    "ॱ": "\uE001", "·": "\uE001",
    "_": "\uE007",
    "|": "\uE002", "│": "\uE002", "।": "।",
    "┃": "\uE002", "╷": "\uE002", "⃓": "\uE002",
    "\\": "\uE003", "╲": "\uE003", "⟍": "\uE003",
    "/": "\uE008",
    ",": "\uE00A", "ˏ": "\uE00A", "̦": "\uE00A",
    "||": "\uE00B", "॥": "\uE00B",
    "॑": "\uE002", "ˈ": "\uE002",
    "L": "\uE002", "l": "\uE002",
}


MODIFIER_KEYS = {
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L",
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l",
    "A1", "a1", "A_1", "a_1",
    "A2", "a2", "A_2", "a_2",
    "B1", "b1", "B_1", "b_1",
    "D1", "d1", "D_1", "d_1",
    "D2", "d2", "D_2", "d_2",
    "^", "˄", "Ʌ", "/\\", "∧", "⁀", "͡", "╭╮", "ͦ", "˚", "ॱ", "·", "़",
    "|", "│", "।", "┃", "╷", "⃓", "\\", "╲", "⟍", "॑", "ˈ",
    "↗", "✓", "⫽", "¯", "/", "⨯",
    "\uE001", "\uE002", "\uE003", "\uE004", "\uE005", "\uE006", "\uE008", "\uE00A", "\uE00B", "\uE00C", "\uE00D",
    "\uE00E", "\uE00F", "\uE02A", "\uE02B", "\uE02C", "\uE02D", "\uE02E"
}


def _apply_mantrakshara_modifier(syl_esc: str, mod: str) -> str:
    """Attach a swara modifier to a Mantrakshara in ModifierSkyBlue."""
    if not mod:
        return syl_esc
    m_clean = mod.strip("()")
    if m_clean in ("A", "a", "╭╮", "⁀", "\uE004"):
        return f"{syl_esc}\\rlap{{\\Large\\swarafont \\textcolor{{ModifierSkyBlue}}{{\\textbf{{\\raisebox{{1.15ex}}{{\\hspace{{-0.40em}}\\char\"E004}}}}}}}}"
    elif m_clean in ("A1", "a1", "A_1", "a_1", "\uE00D"):
        return f"{syl_esc}\\rlap{{\\Large\\swarafont \\textcolor{{ModifierSkyBlue}}{{\\textbf{{\\raisebox{{1.15ex}}{{\\hspace{{-0.55em}}\\char\"E00D}}}}}}}}"
    elif m_clean in ("A2", "a2", "A_2", "a_2", "\uE02E"):
        return f"\\arcOverSyllable{{{syl_esc}}}"
    elif m_clean in ("B", "b", "^", "˄", "/\\", "∧", "\uE005"):
        return f"{syl_esc}\\rlap{{\\Large\\swarafont \\textcolor{{ModifierSkyBlue}}{{\\textbf{{\\raisebox{{1.15ex}}{{\\hspace{{-0.40em}}\\char\"E005}}}}}}}}"
    elif m_clean in ("B1", "b1", "B_1", "b_1", "/", "\uE02C"):
        return f"{syl_esc}\\rlap{{\\Large\\swarafont \\textcolor{{ModifierSkyBlue}}{{\\textbf{{\\raisebox{{1.15ex}}{{\\hspace{{-0.35em}}\\char\"E02C}}}}}}}}"
    elif m_clean in ("C", "c", "ॱ", "·", "़", "\uE001"):
        return f"{syl_esc}\\rlap{{\\Large\\swarafont \\textcolor{{ModifierSkyBlue}}{{\\textbf{{\\raisebox{{0.38ex}}{{\\hspace{{0.02em}}\\char\"E001}}}}}}}}"
    elif m_clean in ("D", "d", "Ʌ", "∧", "\uE006"):
        return f"{syl_esc}\\rlap{{\\Large\\swarafont \\textcolor{{ModifierSkyBlue}}{{\\textbf{{\\raisebox{{1.15ex}}{{\\hspace{{-0.65em}}\\char\"E006}}}}}}}}"
    elif m_clean in ("D1", "d1", "D_1", "d_1", "↗", "\uE00E"):
        return f"{syl_esc}\\rlap{{\\Large\\swarafont \\textcolor{{ModifierSkyBlue}}{{\\textbf{{\\raisebox{{1.15ex}}{{\\hspace{{-0.40em}}\\char\"E00E}}}}}}}}"
    elif m_clean in ("D2", "d2", "D_2", "d_2", "✓", "\uE00F"):
        return f"{syl_esc}\\rlap{{\\Large\\swarafont \\textcolor{{ModifierSkyBlue}}{{\\textbf{{\\raisebox{{0.50ex}}{{\\hspace{{0.10em}}\\char\"E00F\\hspace{{0.05em}}}}}}}}}}"
    elif m_clean in ("E", "e", "┃", "\uE002"):
        return f"{syl_esc}{{\\swarafont \\textcolor{{ModifierSkyBlue}}{{\\textbf{{\\raisebox{{-0.18ex}}{{\\hspace{{0.05em}}\\char\"E002}}}}}}}}"
    elif m_clean in ("F", "f", "╷", "\uE008"):
        return f"{syl_esc}{{\\Large\\swarafont \\textcolor{{ModifierSkyBlue}}{{\\textbf{{\\raisebox{{0.05ex}}{{\\hspace{{0.05em}}\\char\"E008}}}}}}}}"
    elif m_clean in ("G", "g", "\\", "╲", "⟍", "\uE003"):
        return f"\\modGUnder{{{syl_esc}}}"
    elif m_clean in ("H", "h", "L", "l", "|", "│", "॑", "ˈ", "\uE00C"):
        return f"{syl_esc}\\rlap{{\\Large\\swarafont \\textcolor{{ModifierSkyBlue}}{{\\textbf{{\\raisebox{{0.48ex}}{{\\hspace{{-0.18em}}\\char\"E00C}}}}}}}}"
    elif m_clean in ("I", "i", "⫽", "\uE02A"):
        return f"{syl_esc}{{\\Large\\swarafont \\textcolor{{ModifierSkyBlue}}{{\\textbf{{\\raisebox{{0.50ex}}{{\\hspace{{0.10em}}\\char\"E02A\\hspace{{0.05em}}}}}}}}}}"
    elif m_clean in ("J", "j", "\uE02B"):
        return f"{syl_esc}{{\\Large\\swarafont \\textcolor{{ModifierSkyBlue}}{{\\textbf{{\\raisebox{{0.80ex}}{{\\hspace{{0.10em}}\\char\"E02B\\hspace{{0.05em}}}}}}}}}}"
    elif m_clean in ("K", "k", "\uE02D"):
        return f"{syl_esc}{{\\Large\\swarafont \\textcolor{{ModifierSkyBlue}}{{\\textbf{{\\raisebox{{0.50ex}}{{\\hspace{{0.10em}}\\char\"E02D\\hspace{{0.05em}}}}}}}}}}"
    elif m_clean == "_":
        return f"{syl_esc}\\underbarMark{{}}"
    return syl_esc


def _has_mod_a1(tok) -> bool:
    """Check if a token carries MOD-A1 (arc over danda)."""
    if not tok:
        return False
    if tok.get('type') == 'marker':
        return tok.get('marker', '').strip("()") in ("A1", "a1", "A_1", "a_1", "\uE00D")
    if tok.get('type') == 'word':
        sw = tok.get('swara', '')
        if sw:
            _, mods = _parse_swara_and_modifiers(sw)
            return any(m.strip("()") in ("A1", "a1", "A_1", "a_1", "\uE00D") for m in mods)
    return False


def _has_multiple_swaras(tok) -> bool:
    """Check if a word token has multiple or compound swara glyphs."""
    if not tok or tok.get('type') != 'word':
        return False
    sw = tok.get('swara', '')
    if not sw:
        return False
    sw_parts, _ = _parse_swara_and_modifiers(sw)
    if len(sw_parts) > 1:
        return True
    if sw_parts:
        sw_text = sw_parts[0].strip("()")
        if "\u1134D" in sw_text or "\u0D4D" in sw_text or "\u094D" in sw_text or len(sw_text) >= 3:
            return True
    return False


def _match_verse_num_marker(tokens: list, idx: int) -> tuple[int, str | None]:
    """Check if tokens starting at idx form a composite verse number marker like || N || or ॥ N ॥.
    Returns (token_count, number_string) if matched, else (0, None).
    """
    if idx >= len(tokens):
        return 0, None
    sub = tokens[idx:]
    if sub[0].get('type') != 'danda' or sub[0].get('char') not in ('॥', '||', '|', '।।'):
        return 0, None

    j = 1
    while j < len(sub) and sub[j].get('type') == 'space':
        j += 1
    
    if j < len(sub) and sub[j].get('type') in ('word', 'other'):
        val = (sub[j].get('word') or sub[j].get('text') or '').translate(_ENGLISH_DIGITS).strip()
        if re.match(r'^\d+$', val):
            num_str = val
            j += 1
            while j < len(sub) and sub[j].get('type') == 'space':
                j += 1
            if j < len(sub) and sub[j].get('type') == 'danda' and sub[j].get('char') in ('॥', '||', '|', '।।'):
                j += 1
                while j < len(sub) and sub[j].get('type') == 'space':
                    j += 1
                return j, num_str
    return 0, None


def _parse_swara_and_modifiers(swara_str: str):
    """Decompose swara string into pitch swara markers and Mantrakshara modifiers."""
    if not swara_str:
        return [], []
    if "(" in swara_str:
        parens = re.findall(r"\(([^)]+)\)", swara_str)
    else:
        parens = [swara_str]
    
    swaras = []
    mods = []
    for p in parens:
        if p in MODIFIER_KEYS:
            mods.append(p)
        else:
            # Check if p has trailing modifier char (e.g. \uE001-\uE02E, ↗, ✓, etc.)
            m = re.search(r"([\uE001-\uE02E\^\\/\|\_↗✓·ॱ∧⁀⫽¯⨯]+)$", p)
            if m:
                base = p[:m.start()]
                trailing_mods = p[m.start():]
                if base:
                    swaras.append(base)
                for tm in trailing_mods:
                    mods.append(tm)
            else:
                swaras.append(p)
    return swaras, mods


SWARA_CANONICAL_MAP = {
    # Sha base and combinations
    "𑌶": "\u0D36",                 # Grantha Sha -> Malayalam Sha
    "\u11336": "\u0D36",
    "𑌶𑌾": "\uE010",               # Shaa
    "\u11336\u1133E": "\uE010",
    "ശാ": "\uE010",
    "𑌶𑌿": "\uE011",               # Shi
    "\u11336\u1133F": "\uE011",
    "ശി": "\uE011",
    "𑌶𑍀": "\uE012",               # Shii
    "\u11336\u11340": "\uE012",
    "ശീ": "\uE012",
    "𑌶𑍍": "\uE013",               # Sha + Virama
    "\u11336\u1134D": "\uE013",
    "ശ്": "\uE013",
    "𑌶𑍁": "\uE015",               # Shu
    "\u11336\u11341": "\uE015",
    "ശു": "\uE015",
    "𑌶𑍂": "\uE016",               # Shuu
    "\u11336\u11342": "\uE016",
    "ശൂ": "\uE016",
    "𑌶𑍃": "\uE017",               # Shr
    "\u11336\u11343": "\uE017",
    "𑌶𑍄": "\uE018",               # Shrr
    "\u11336\u11344": "\uE018",
    "𑌶𑍇": "\uE019",               # She
    "\u11336\u11347": "\uE019",
    "𑌶𑍈": "\uE01A",               # Shai
    "\u11336\u11348": "\uE01A",
    "𑌶𑍋": "\uE01B",               # Sho
    "\u11336\u1134B": "\uE01B",
    "𑌶𑍌": "\uE01C",               # Shau
    "\u11336\u1134C": "\uE01C",

    # Tra & Kra
    "𑌤𑍍𑌰": "\uE01D",               # Tra
    "\u11324\u1134D\u11330": "\uE01D",
    "𑌤𑍍𑌰𑌾": "\uE01D",
    "ത്രാ": "\uE01D",
    "ത്ര": "\uE01D",
    "𑌕𑍍𑌰": "\uE01E",               # Kra
    "\u11315\u1134D\u11330": "\uE01E",
    "ക്രം": "\uE01E",
    "ക്ര": "\uE01E",
    "𑌕𑍍𑌰𑍍": "\uE01F",              # Kra + Virama
    "\u11315\u1134D\u11330\u1134D": "\uE01F",
    "ക്ര്": "\uE01F",

    # Pla family
    "𑌪𑍍𑌲": "\uE020",               # Pla
    "\u1132A\u1134D\u11332": "\uE020",
    "പ്ല": "\uE020",
    "𑌪𑍍𑌲𑌾": "\uE021",              # Plaa
    "\u1132A\u1134D\u11332\u1133E": "\uE021",
    "പ്ലാ": "\uE021",
    "𑌪𑍍𑌲𑌿": "\uE022",              # Pli
    "\u1132A\u1134D\u11332\u1133F": "\uE022",
    "പ്ലി": "\uE022",
    "𑌪𑍍𑌲𑍀": "\uE023",              # Plii
    "\u1132A\u1134D\u11332\u11340": "\uE023",
    "പ്ലീ": "\uE023",
    "𑌪𑍍𑌲𑍁": "\uE024",              # Plu
    "\u1132A\u1134D\u11332\u11341": "\uE024",
    "പ്ലു": "\uE024",
    "𑌪𑍍𑌲𑍂": "\uE025",              # Pluu
    "\u1132A\u1134D\u11332\u11342": "\uE025",
    "പ്ലൂ": "\uE025",
    "𑌪𑍍𑌲𑍍": "\uE026",              # Pla + Virama
    "\u1132A\u1134D\u11332\u1134D": "\uE026",
    "പ്ല്": "\uE026",

    # Clean composites
    "ശൃ": "\uE027",
    "𑌷𑍃": "\uE028",               # Shrr
    "\u11337\u11343": "\uE028",
    "ഷൃ": "\uE028",
    "𑌣𑍂": "\uE029",               # Nna + U
    "\u11323\u11342": "\uE029",
    "ണൂ": "\uE029",
}


def _swara_latex(swara: str) -> str:
    """Latex for pure swara marker pitch glyphs rendered in bold SwaraRed."""
    if not swara:
        return ""
    # Filter out modifiers which attach directly to Mantrakshara
    if swara in MODIFIER_KEYS or swara in ("A", "B", "C", "D", "E", "F", "G", "H", "L", "a", "b", "c", "d", "e", "f", "g", "h", "l"):
        return ""
    # Resolve to canonical PUA/Malayalam ligature if mapped
    from malayalam.ml_map import marker_to_grantha
    g_swara = marker_to_grantha(swara)
    clean_swara = SWARA_CANONICAL_MAP.get(g_swara, g_swara)
    return f"{{\\swarafont \\bfseries \\textcolor{{SwaraRed}}{{{clean_swara}}}}}"


def wrap_latin_for_latex(text: str) -> str:
    r"""Wrap any Latin/English character sequences with {\latinfont ...} so they render in Nimbus Roman."""
    if not text:
        return text
    if r'\latinfont' in text:
        return text
    return re.sub(r'([A-Za-z0-9][A-Za-z0-9\s,\.\-\':;/\(\)]*)', r'{\\latinfont \1}', text)


def _format_single_malayalam_word_latex(tok, with_modifiers=True, exclude_mods=None, exclude_swara=False):
    """Format a single Malayalam word token with swara stack and modifiers."""
    from malayalam.ml_transliterate import split_malayalam_syllables, devanagari_to_malayalam
    
    word = tok.get('word', '')
    swara = tok.get('swara', '')
    if not word:
        return ""
        
    # Extract embedded parenthesized swara modifiers from word if present
    if "(" in word:
        embedded_mods = re.findall(r"\(([^)]+)\)", word)
        if embedded_mods:
            word = re.sub(r"\([^)]*\)", "", word)
            swara = (swara or "") + "".join(f"({m})" for m in embedded_mods)
        
    word = devanagari_to_malayalam(word)
    if swara:
        swara = devanagari_to_malayalam(swara)
    
    if word in ('.', ','):
        if word == '.':
            return r"{\Large\textcolor{ModifierSkyBlue}{\textbf{.}}}\hspace{0.08em}"
        elif word == ',':
            return r"{\Large\textcolor{ModifierSkyBlue}{\textbf{,}}}\hspace{0.08em}"
        return ""
    
    exclude_mods = exclude_mods or set()
    core_word = word.rstrip("_,.")
    trailing_punct = word[len(core_word):]
    
    if not core_word:
        res = []
        for p in word:
            if p == '.':
                res.append(r"{\Large\textcolor{ModifierSkyBlue}{\textbf{.}}}\hspace{0.08em}")
            elif p == ',':
                res.append(r"{\Large\textcolor{ModifierSkyBlue}{\textbf{,}}}\hspace{0.08em}")
            elif p == '_':
                res.append(r"\underbarMark{}")
            else:
                p_esc = escape_for_latex(p)
                res.append(f"{{\\malayalamfont \\textcolor{{ModifierSkyBlue}}{{{p_esc}}}}}")
        return "".join(res)
    
    MOD_A2_SET = {'A2', 'a2', 'A_2', 'a_2', '\uE02E'}
    mod_c_set = {'C', 'c', '·', 'ॱ', '़', '\uE001'}
    mod_h_set = {'H', 'h', '|', '│', '॑', 'ˈ', '\uE00C'}
    
    swara_parts, mod_parts = _parse_swara_and_modifiers(swara) if swara else ([], [])
    active_mods = [m for m in mod_parts if m.strip("()") not in exclude_mods]
    
    has_mod_a2 = any(m.strip("()") in MOD_A2_SET for m in active_mods)
    active_mods = [m for m in active_mods if m.strip("()") not in MOD_A2_SET]
    
    has_mod_c = any(m.strip("()") in mod_c_set for m in active_mods)
    has_mod_h = any(m.strip("()") in mod_h_set for m in active_mods)
    
    if with_modifiers:
        active_mods = [m for m in active_mods if m.strip("()") not in mod_c_set and m.strip("()") not in mod_h_set]
    
    syllables = split_malayalam_syllables(core_word)
    parts = []
    
    for idx, syl in enumerate(syllables):
        syl_esc = escape_for_latex(syl)
        if syl in ("_", ".", ",", ";", "._", "_.", ",_"):
            if syl == '.':
                parts.append(r"{\Large\textcolor{ModifierSkyBlue}{\textbf{.}}}\hspace{0.08em}")
            elif syl == ',':
                parts.append(r"{\Large\textcolor{ModifierSkyBlue}{\textbf{,}}}\hspace{0.08em}")
            elif syl == '_':
                parts.append(r"\underbarMark{}")
            else:
                parts.append(f"{{\\malayalamfont \\textcolor{{ModifierSkyBlue}}{{{syl_esc}}}}}")
        elif idx == len(syllables) - 1:
            syl_mod = syl_esc
            if with_modifiers:
                has_mod_g = any(m.strip("()") in ("G", "g", "\\", "╲", "⟍", "\uE003") for m in active_mods)
                active_mods = [m for m in active_mods if m.strip("()") not in ("G", "g", "\\", "╲", "⟍", "\uE003")]
                if has_mod_g:
                    syl_mod = f"\\modGUnder{{{syl_mod}}}"
                if has_mod_c:
                    syl_mod += r"\rlap{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\raisebox{0.38ex}{\hspace{0.02em}\char" + '"E001}}}}'
                if has_mod_h:
                    syl_mod += r"\rlap{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\raisebox{0.48ex}{\hspace{-0.18em}\char" + '"E00C}}}}'
                for mod in active_mods:
                    syl_mod = _apply_mantrakshara_modifier(syl_mod, mod)
            
            swara_str = "".join(swara_parts)
            swara_latex = _swara_latex(swara_str) if (not exclude_swara and swara_str) else ""
                
            if swara_latex:
                stack_code = f"\\stackcenter{{\\malayalamfont {syl_mod}}}{{{swara_latex}}}"
            else:
                stack_code = f"{{\\malayalamfont {syl_mod}}}"
            
            if has_mod_a2 and with_modifiers:
                stack_code = f"\\arcOverSyllable{{{stack_code}}}"
            
            if trailing_punct and with_modifiers:
                for p in trailing_punct:
                    if p not in exclude_mods:
                        if p == '_':
                            stack_code += r"\underbarMark{}"
                        elif p == '.':
                            stack_code += r"{\Large\textcolor{ModifierSkyBlue}{\textbf{.}}}\hspace{0.08em}"
                        elif p == ',':
                            stack_code += r"{\Large\textcolor{ModifierSkyBlue}{\textbf{,}}}\hspace{0.08em}"
                        else:
                            p_esc = escape_for_latex(p)
                            stack_code += f"{{\\malayalamfont \\textcolor{{ModifierSkyBlue}}{{{p_esc}}}}}"
            parts.append(stack_code)
        else:
            parts.append(f"{{\\malayalamfont {syl_esc}}}")
            
    return "".join(parts)


def _render_malayalam_mantra_body(subsection):
    """Helper to render Malayalam mantra body with top swara stacks and footnotes."""
    from core.swara_engine import tokenize_mantra_line
    from malayalam.ml_transliterate import devanagari_to_malayalam
    
    mantra_sets = subsection.get('malayalam-mantra-sets', [])
    if not mantra_sets:
        mantra_sets = subsection.get('corrected-mantra_sets', [])
    if not mantra_sets:
        mantra_sets = subsection.get('mantra_sets', [])
    if not mantra_sets:
        return []

    MOD_A_SET = {'A', 'a', '⁀', '\uE004', '╭╮', '͡'}
    MOD_A1_SET = {'A1', 'a1', 'A_1', 'a_1', '\uE00D'}
    MOD_A2_SET = {'A2', 'a2', 'A_2', 'a_2', '\uE02E'}
    MOD_B_SET = {'B', 'b', '^', '˄', '/\\', '\uE005'}
    MOD_D_SET = {'D', 'd', '∧', 'Ʌ', '\uE006'}

    footnote_data = subsection.get('footnotes', {})
    paragraph_buffer = []
    formatted_paragraphs = []
    
    for mantra_set in mantra_sets:
        line = mantra_set.get('malayalam-mantra') or mantra_set.get('corrected-mantra') or mantra_set.get('mantra', '')
        if not line:
            continue
        line = devanagari_to_malayalam(line)
        line = line.replace('ർ', 'ൎ').replace('ര്', 'ൎ').replace('൪', 'ൎ')
        tokens = tokenize_mantra_line(line)
        
        idx_t = 0
        while idx_t < len(tokens):
            v_count, v_num = _match_verse_num_marker(tokens, idx_t)
            if v_count > 0:
                paragraph_buffer.append(f"\\nolinebreak\\hspace{{0.65em plus 0.25em minus 0.1em}}\\mbox{{\\malayalamfont ॥{v_num}॥}}")
                full_paragraph = "".join(paragraph_buffer)
                formatted_paragraphs.append(f"{{\\noindent\\justifying\\sloppy {{\\malayalamfont {full_paragraph}}}}}")
                formatted_paragraphs.append(r"\par\vspace{1.1em}")
                paragraph_buffer = []
                idx_t += v_count
                continue

            tok = tokens[idx_t]
            t = tok['type']
            if t == 'space':
                prev_tok = tokens[idx_t - 1] if idx_t > 0 else None
                next_tok = tokens[idx_t + 1] if idx_t + 1 < len(tokens) else None
                
                # Space is preserved around normal dandas / footnotes or when adjacent to multi-swaras
                prev_is_danda = (prev_tok and prev_tok['type'] in ('danda', 'footnote'))
                next_is_danda = (next_tok and next_tok['type'] in ('danda', 'footnote'))
                
                prev_multi = (prev_tok and _has_multiple_swaras(prev_tok))
                next_multi = (next_tok and _has_multiple_swaras(next_tok))
                
                if prev_is_danda or next_is_danda or prev_multi or next_multi:
                    paragraph_buffer.append(" ")
                else:
                    paragraph_buffer.append(r"\hskip 0pt plus 1.5pt\allowbreak ")
            elif t == 'danda':
                ch = tok['char']
                next_m_idx = idx_t + 1
                while next_m_idx < len(tokens) and tokens[next_m_idx]['type'] == 'space':
                    next_m_idx += 1
                if next_m_idx < len(tokens) and tokens[next_m_idx]['type'] == 'marker':
                    m_str = tokens[next_m_idx]['marker'].strip('()')
                    if m_str in MOD_A1_SET and paragraph_buffer:
                        third_w_idx = next_m_idx + 1
                        while third_w_idx < len(tokens) and tokens[third_w_idx]['type'] == 'space':
                            third_w_idx += 1
                        if third_w_idx < len(tokens) and tokens[third_w_idx]['type'] == 'word':
                            while paragraph_buffer and ('\\hskip' in paragraph_buffer[-1] or '\\hspace' in paragraph_buffer[-1] or paragraph_buffer[-1].isspace() or paragraph_buffer[-1] == ' '):
                                paragraph_buffer.pop()
                            prev_chunk = paragraph_buffer.pop() if paragraph_buffer else ""
                            next_tok = tokens[third_w_idx]
                            chunk2 = _format_single_malayalam_word_latex(next_tok, with_modifiers=True)
                            d_char = ch.replace('|', '।')
                            paragraph_buffer.append(f"\\mbox{{{prev_chunk} \\dandaWithArc{{{d_char}}} {chunk2}}}")
                            idx_t = third_w_idx + 1
                            continue
                paragraph_buffer.append(format_dandas(ch))
            elif t == 'footnote':
                marker = tok.get('text', '').strip('()')
                fn_text = footnote_data.get(marker, '')
                if fn_text:
                    try:
                        fn_text = devanagari_to_malayalam(fn_text)
                    except Exception:
                        pass
                    fn_esc = escape_for_latex(fn_text)
                    fn_esc = wrap_latin_for_latex(fn_esc)
                    paragraph_buffer.append(f"\\footnote{{\\malayalamfont {fn_esc}}}")
            elif t == 'marker':
                m_str = tok['marker']
                m_esc = _apply_mantrakshara_modifier("", m_str)
                paragraph_buffer.append(m_esc)
            elif t == 'word':
                word = tok.get('word', '')
                sw = tok.get('swara', '')
                if not word:
                    idx_t += 1
                    continue
                
                sw_parts, tok_mods = _parse_swara_and_modifiers(sw)
                has_mod_a1 = any(m.strip('()') in MOD_A1_SET for m in tok_mods)
                has_mod_a = any(m.strip('()') in MOD_A_SET for m in tok_mods)
                has_mod_b = any(m.strip('()') in MOD_B_SET for m in tok_mods)
                has_mod_d = any(m.strip('()') in MOD_D_SET for m in tok_mods)
                
                # Check if followed by danda
                d_idx = idx_t + 1
                while d_idx < len(tokens) and tokens[d_idx]['type'] == 'space':
                    d_idx += 1
                next_is_danda = (d_idx < len(tokens) and tokens[d_idx]['type'] == 'danda')
                if has_mod_a and next_is_danda:
                    has_mod_a1 = True
                    has_mod_a = False
                
                # Peak Elevation Caret (MOD-B): bridges across 2 syllables with swara sitting atop apex
                if has_mod_b:
                    next_w_idx = idx_t + 1
                    while next_w_idx < len(tokens) and tokens[next_w_idx]['type'] == 'space':
                        next_w_idx += 1
                    if next_w_idx < len(tokens) and tokens[next_w_idx]['type'] == 'word':
                        next_tok = tokens[next_w_idx]
                        next_sw = next_tok.get('swara', '')
                        _, next_mods = _parse_swara_and_modifiers(next_sw)
                        next_has_a1 = any(m.strip('()') in MOD_A1_SET for m in next_mods)
                        next_has_a = any(m.strip('()') in MOD_A_SET for m in next_mods)
                        
                        d2_idx = next_w_idx + 1
                        while d2_idx < len(tokens) and tokens[d2_idx]['type'] == 'space':
                            d2_idx += 1
                        next_tok_next_is_danda = (d2_idx < len(tokens) and tokens[d2_idx]['type'] == 'danda')
                        if next_has_a and next_tok_next_is_danda:
                            next_has_a1 = True
                            
                        if next_has_a1 and next_tok_next_is_danda:
                            # Chained MOD-B + MOD-A1 over danda: e.g. ഘാ(∧)തൊ(A1) । ഹാഇ
                            d_char = tokens[d2_idx]['char'].replace('|', '।')
                            third_w_idx = d2_idx + 1
                            while third_w_idx < len(tokens) and tokens[third_w_idx]['type'] == 'space':
                                third_w_idx += 1
                            if third_w_idx < len(tokens) and tokens[third_w_idx]['type'] == 'word':
                                third_tok = tokens[third_w_idx]
                                sw_label = _swara_latex("".join(sw_parts)) if sw_parts else ""
                                chunk1 = _format_single_malayalam_word_latex(tok, with_modifiers=True, exclude_mods=MOD_B_SET, exclude_swara=True)
                                chunk2 = _format_single_malayalam_word_latex(next_tok, with_modifiers=True, exclude_mods=MOD_A1_SET | MOD_A_SET)
                                chunk3 = _format_single_malayalam_word_latex(third_tok, with_modifiers=True)
                                combined_mbox = f"\\mbox{{{chunk1}\\caretWithSwara{{{sw_label}}}{chunk2} \\dandaWithArc{{{d_char}}} {chunk3}}}"
                                paragraph_buffer.append(combined_mbox)
                                idx_t = third_w_idx + 1
                                continue
                        
                        sw_label = _swara_latex("".join(sw_parts)) if sw_parts else ""
                        chunk1 = _format_single_malayalam_word_latex(tok, with_modifiers=True, exclude_mods=MOD_B_SET, exclude_swara=True)
                        chunk2 = _format_single_malayalam_word_latex(next_tok, with_modifiers=True)
                        paragraph_buffer.append(f"\\mbox{{{chunk1}\\caretWithSwara{{{sw_label}}}{chunk2}}}")
                        idx_t = next_w_idx + 1
                        continue

                # MOD-D bridging across 2 syllables (or chained MOD-D + MOD-A1 over danda)
                if has_mod_d:
                    next_w_idx = idx_t + 1
                    while next_w_idx < len(tokens) and tokens[next_w_idx]['type'] == 'space':
                        next_w_idx += 1
                    if next_w_idx < len(tokens) and tokens[next_w_idx]['type'] == 'word':
                        next_tok = tokens[next_w_idx]
                        next_sw = next_tok.get('swara', '')
                        _, next_mods = _parse_swara_and_modifiers(next_sw)
                        next_has_a1 = any(m.strip('()') in MOD_A1_SET for m in next_mods)
                        next_has_a = any(m.strip('()') in MOD_A_SET for m in next_mods)
                        
                        d2_idx = next_w_idx + 1
                        while d2_idx < len(tokens) and tokens[d2_idx]['type'] == 'space':
                            d2_idx += 1
                        next_tok_next_is_danda = (d2_idx < len(tokens) and tokens[d2_idx]['type'] == 'danda')
                        if next_has_a and next_tok_next_is_danda:
                            next_has_a1 = True
                            
                        if next_has_a1 and next_tok_next_is_danda:
                            # Chained MOD-D + MOD-A1 over danda
                            d_char = tokens[d2_idx]['char'].replace('|', '।')
                            third_w_idx = d2_idx + 1
                            while third_w_idx < len(tokens) and tokens[third_w_idx]['type'] == 'space':
                                third_w_idx += 1
                            if third_w_idx < len(tokens) and tokens[third_w_idx]['type'] == 'word':
                                third_tok = tokens[third_w_idx]
                                chunk1 = _format_single_malayalam_word_latex(tok, with_modifiers=True, exclude_mods=MOD_D_SET)
                                chunk2 = _format_single_malayalam_word_latex(next_tok, with_modifiers=True, exclude_mods=MOD_A1_SET | MOD_D_SET | MOD_A_SET)
                                chunk3 = _format_single_malayalam_word_latex(third_tok, with_modifiers=True)
                                d_glyph = r'\hspace{0.18em}\makebox[0pt][c]{\raisebox{1.18ex}{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\char"E006}}}}\hspace{0.18em}'
                                combined_mbox = f"\\mbox{{{chunk1}{d_glyph}{chunk2} \\dandaWithArc{{{d_char}}} {chunk3}}}"
                                paragraph_buffer.append(combined_mbox)
                                idx_t = third_w_idx + 1
                                continue
                        
                        chunk1 = _format_single_malayalam_word_latex(tok, with_modifiers=True, exclude_mods=MOD_D_SET)
                        chunk2 = _format_single_malayalam_word_latex(next_tok, with_modifiers=True)
                        d_glyph = r'\hspace{0.18em}\makebox[0pt][c]{\raisebox{1.18ex}{\Large\swarafont \textcolor{ModifierSkyBlue}{\textbf{\char"E006}}}}\hspace{0.18em}'
                        combined_mbox = f"\\mbox{{{chunk1}{d_glyph}{chunk2}}}"
                        paragraph_buffer.append(combined_mbox)
                        idx_t = next_w_idx + 1
                        continue

                # MOD-A1 over danda: bridges word1, danda, word2
                if has_mod_a1 and next_is_danda:
                    d_char = tokens[d_idx]['char'].replace('|', '।')
                    next_w_idx = d_idx + 1
                    while next_w_idx < len(tokens) and tokens[next_w_idx]['type'] == 'space':
                        next_w_idx += 1
                    if next_w_idx < len(tokens) and tokens[next_w_idx]['type'] == 'word':
                        next_tok = tokens[next_w_idx]
                        chunk1 = _format_single_malayalam_word_latex(tok, with_modifiers=True, exclude_mods=MOD_A1_SET | MOD_A_SET)
                        chunk2 = _format_single_malayalam_word_latex(next_tok, with_modifiers=True)
                        combined_mbox = f"\\mbox{{{chunk1} \\dandaWithArc{{{d_char}}} {chunk2}}}"
                        paragraph_buffer.append(combined_mbox)
                        idx_t = next_w_idx + 1
                        continue

                # MOD-A bridging across 2 words without danda
                if has_mod_a:
                    next_w_idx = idx_t + 1
                    while next_w_idx < len(tokens) and tokens[next_w_idx]['type'] == 'space':
                        next_w_idx += 1
                    if next_w_idx < len(tokens) and tokens[next_w_idx]['type'] == 'word':
                        next_tok = tokens[next_w_idx]
                        chunk1 = _format_single_malayalam_word_latex(tok, with_modifiers=True, exclude_mods=MOD_A_SET)
                        chunk2 = _format_single_malayalam_word_latex(next_tok, with_modifiers=True)
                        arc_glyph = r"\rlap{\swarafont \textcolor{ModifierSkyBlue}{\raisebox{1.18ex}{\hspace{-0.38em}\char" + '"E004}}}'
                        combined_mbox = f"\\mbox{{{chunk1}{arc_glyph}{chunk2}}}"
                        paragraph_buffer.append(combined_mbox)
                        idx_t = next_w_idx + 1
                        continue

                chunk = _format_single_malayalam_word_latex(tok, with_modifiers=True)
                paragraph_buffer.append(chunk)
            else:
                extra_text = tok.get("text", "")
                extra_esc = escape_for_latex(extra_text)
                if extra_text.strip() in (".", ",", "_", "._", "_.", ",_", ",.", ";"):
                    paragraph_buffer.append(f"{{\\malayalamfont \\textcolor{{ModifierSkyBlue}}{{{extra_esc}}}}}")
                else:
                    paragraph_buffer.append(f"{{\\malayalamfont {extra_esc}}}")
            idx_t += 1

        if paragraph_buffer:
            full_paragraph = "".join(paragraph_buffer)
            formatted_paragraphs.append(f"{{\\noindent\\justifying\\sloppy {{\\malayalamfont {full_paragraph}}}}}")
            formatted_paragraphs.append(r"\par\vspace{1.1em}")
            paragraph_buffer = []

    if paragraph_buffer:
        full_paragraph = "".join(paragraph_buffer)
        formatted_paragraphs.append(f"{{\\noindent\\justifying\\sloppy {{\\malayalamfont {full_paragraph}}}}}")
        formatted_paragraphs.append(r"\par\vspace{1.1em}")

    return formatted_paragraphs


def format_malayalam_rik_block(subsection, prev_rik_id=None, include_metadata=True, prev_rik_text=None):
    """Format Rik metadata + Rik text (with elevated Vedic accents and footnotes) for LaTeX PDF."""
    from malayalam.ml_transliterate import devanagari_to_malayalam, split_malayalam_syllables

    current_rik_id = get_canonical_rik_id(subsection)
    rik_ids = subsection.get('rik_ids', [current_rik_id] if current_rik_id else [])
    rik_metadata = subsection.get('rik_metadata', '')
    rik_text = subsection.get('rik_text', '')
    
    # Skip consecutive duplicate Rik text across multiple Samams
    if prev_rik_text and rik_text and rik_text.strip() == prev_rik_text.strip():
        return ""

    show_rik = (prev_rik_id is None) or (current_rik_id != prev_rik_id) or (len(rik_ids) > 1 and max(rik_ids) != prev_rik_id)
    if not show_rik or (not rik_metadata and not rik_text):
        return ""
    
    footnote_data = subsection.get('footnotes', {})
    out = []
    if include_metadata and rik_metadata:
        try:
            rm = devanagari_to_malayalam(rik_metadata)
        except Exception:
            rm = rik_metadata
        rm = format_dandas(rm)
        rm_esc = escape_for_latex(rm)
        out.append(f"{{\\centering {{\\malayalamfont \\textcolor{{AccentPurple}}{{{rm_esc}}}}} \\par}}")
        out.append(r"\nopagebreak\vspace{0.2em}\nopagebreak")
    
    if rik_text:
        try:
            rt = devanagari_to_malayalam(rik_text)
        except Exception:
            rt = rik_text
        rt = clean_stack_arg(rt)
        
        # Replace footnote markers (s1), etc. with LaTeX footnotes
        def _replace_fn(match):
            m = match.group(1)
            fn = footnote_data.get(m, '')
            if fn:
                try:
                    fn = devanagari_to_malayalam(fn)
                except Exception:
                    pass
                fn_esc = escape_for_latex(fn)
                fn_esc = wrap_latin_for_latex(fn_esc)
                return f"\\footnote{{\\malayalamfont {fn_esc}}}"
            return ""
        
        rt = re.sub(r'\(s(\d+)\)', r'(s\1)', rt)
        rt = re.sub(r'\((s\d+)\)', _replace_fn, rt)
        
        # Format Vedic accents over Malayalam syllables using stackengine
        tokens = re.findall(r'\\footnote\{[^}]*\}|॥\s*[\d०-९]+\s*॥|[।॥]|\s+|[^\s।॥()]+(?:\(\d+\))*', rt)
        tok_out = []
        for tok in tokens:
            if tok.isspace():
                continue
            elif tok in ['।', '॥']:
                tok_out.append(f'\\hspace{{0.25em}}{tok}\\hspace{{0.25em}}')
            elif re.match(r'॥\s*[\d०-९]+\s*॥', tok):
                tok_out.append(f'\\hspace{{0.35em}}\\mbox{{{tok.translate(_ENGLISH_DIGITS)}}}')
            elif tok.startswith(r'\footnote'):
                tok_out.append(tok)
            else:
                segs = re.findall(r'[^\s()]+?(?:\(\d+\)|$)', tok)
                seg_out = []
                for seg in segs:
                    m_acc = re.match(r'^(.*?)\((\d+)\)$', seg)
                    if m_acc:
                        base_word, acc_num = m_acc.group(1), m_acc.group(2)
                        sylls = split_malayalam_syllables(base_word)
                        if len(sylls) > 1:
                            prefix = escape_for_latex(''.join(sylls[:-1]))
                            last_syl = escape_for_latex(sylls[-1])
                        else:
                            prefix = ''
                            last_syl = escape_for_latex(base_word)
                        if acc_num == '1':
                            seg_out.append(f'{prefix}\\rikSwarita{{{last_syl}}}')
                        elif acc_num == '2':
                            seg_out.append(f'{prefix}\\rikAnudatta{{{last_syl}}}')
                        elif acc_num == '3':
                            seg_out.append(f'{prefix}\\rikKampa{{{last_syl}}}')
                        elif acc_num == '4':
                            seg_out.append(f'{prefix}\\rikTrikampa{{{last_syl}}}')
                        else:
                            seg_out.append(escape_for_latex(seg))
                    else:
                        seg_out.append(escape_for_latex(seg))
                tok_out.append(''.join(seg_out))
        
        rt_formatted = "".join(tok_out)
        out.append(f"{{\\noindent\\justifying\\sloppy {{\\malayalamfont \\textcolor{{AccentBlue}}{{{rt_formatted}}}}}}}")
        out.append(r"\par\vspace{0.5em}")
        
    return "\n".join(out)


def format_malayalam_samam_block(subsection, subsection_title, toc_level='section', include_metadata=True):
    """Format Samam subsection header + Saman metadata + Samam mantras in Malayalam for LaTeX PDF."""
    from malayalam.ml_transliterate import devanagari_to_malayalam

    formatted_output = []

    # Clean titles for Display
    display_sub_title = re.sub(r'^([|॥]+)\s*', r'\1 ', subsection_title) if subsection_title else ''

    # Header only (exclude metadata) for TOC/Index
    samam_header_only = display_sub_title
    m_split = re.match(r'([|॥]+\s*.*?[|॥]+)', display_sub_title)
    if m_split:
        samam_header_only = m_split.group(1).strip()
    index_title = re.sub(r'[|॥]', '', samam_header_only).strip()

    try:
        display_sub_title = devanagari_to_malayalam(display_sub_title)
        samam_header_only = devanagari_to_malayalam(samam_header_only)
        index_title = devanagari_to_malayalam(index_title)
    except Exception:
        pass

    formatted_output.append(r"\par\filbreak")
    formatted_output.append(r"\phantomsection")
    if subsection_title:
        toc_title = format_dandas(samam_header_only)
        mal_toc = "{\\malayalamfont " + toc_title + "}"
        if toc_level == 'subsection':
            formatted_output.append(f"\\addcontentsline{{toc}}{{section}}{{{mal_toc}}}")
        elif toc_level == 'both':
            formatted_output.append(f"\\addcontentsline{{toc}}{{subsection}}{{{mal_toc}}}")
        if index_title:
            formatted_output.append(f"\\index{{{index_title}}}")

    # SubSection Title + Saman Metadata
    header_parts = []
    if display_sub_title:
        header_parts.append(format_dandas(display_sub_title.strip()))
    
    if include_metadata:
        saman_metadata = subsection.get('saman_metadata', '')
        if saman_metadata:
            try:
                sm_mal = devanagari_to_malayalam(saman_metadata)
            except Exception:
                sm_mal = saman_metadata
            header_parts.append(f"\\textcolor{{AccentBrown}}{{{format_dandas(sm_mal)}}}")
    
    if header_parts:
        header_latex = "{\\malayalamfont \\textbf{\\textcolor{AccentGreen}{" + " \\quad ".join(header_parts) + "}}}"
        formatted_output.append("{\\centering " + header_latex + " \\par}")

    # Keep header with mantra text
    formatted_output.append(r"\nopagebreak")
    formatted_output.append(r"\vspace{0.4em}")
    formatted_output.append(r"\nopagebreak")

    mantra_paragraphs = _render_malayalam_mantra_body(subsection)
    formatted_output.extend(mantra_paragraphs)

    return "\n\n".join(formatted_output)


def format_malayalam_rik_only(subsection, supersection_title, section_title, subsection_title, prev_rik_id=None, toc_level='section', prev_rik_text=None):
    """Rik-only mode (with metadata) for Malayalam."""
    return format_malayalam_rik_block(subsection, prev_rik_id=prev_rik_id, include_metadata=True, prev_rik_text=prev_rik_text)


def format_malayalam_rik_nometa(subsection, supersection_title, section_title, subsection_title, prev_rik_id=None, toc_level='section', prev_rik_text=None):
    """Rik-only mode (without metadata) for Malayalam."""
    return format_malayalam_rik_block(subsection, prev_rik_id=prev_rik_id, include_metadata=False, prev_rik_text=prev_rik_text)


def format_malayalam_samam_only(subsection, supersection_title, section_title, subsection_title, toc_level='section'):
    """Samam-only mode (with metadata) for Malayalam."""
    return format_malayalam_samam_block(subsection, subsection_title, toc_level=toc_level, include_metadata=True)


def format_malayalam_samam_nometa(subsection, supersection_title, section_title, subsection_title, toc_level='section'):
    """Samam-only mode (without metadata) for Malayalam."""
    return format_malayalam_samam_block(subsection, subsection_title, toc_level=toc_level, include_metadata=False)


def format_malayalam_combined(subsection, supersection_title, section_title, subsection_title, prev_rik_id=None, toc_level='section'):
    """Combined mode: Rik (with metadata) followed by Samam (with metadata) for Malayalam."""
    parts = []
    rik_part = format_malayalam_rik_block(subsection, prev_rik_id=prev_rik_id, include_metadata=True)
    if rik_part:
        parts.append(rik_part)
    samam_part = format_malayalam_samam_block(subsection, subsection_title, toc_level=toc_level, include_metadata=True)
    if samam_part:
        parts.append(samam_part)
    return "\n\n".join(parts)


def format_malayalam_samam(subsection, supersection_title, section_title, subsection_title, toc_level='section'):
    """Legacy alias for format_malayalam_samam_only."""
    return format_malayalam_samam_only(subsection, supersection_title, section_title, subsection_title, toc_level=toc_level)

# --- Metadata / Title Helpers ---
def clean_toc_title(raw_title):
    """
    Cleans the raw subsection title to extract just the first block of text 
    wrapped in dandas (e.g., extracting just the Samam header and removing metadata).
    """
    if not raw_title: return ""
    display_sub_title = re.sub(r'^([|॥]+)\s*', r'\1 ', raw_title)
    m_split = re.match(r'([|॥]+\s*.*?[|॥]+)', display_sub_title)
    if m_split:
        return m_split.group(1).strip()
    return display_sub_title.strip()


def toc_header(text):
    """
    Extracts the clean header for Table of Contents:
    Removes leading 'अथ' and trailing 'प्रारम्भः' / 'प्रारम्भ'.
    """
    if not text:
        return ""
    t = str(text)
    t = re.sub(r'^\s*अथ\s+', '', t)
    t = re.sub(r'\s*प्रारम्भः?\s*$', '', t)
    return t.strip()


def register_latex_filters(env):
    """Registers all LaTeX rendering filters onto the provided Jinja2 environment."""
    env.filters["my_encodeURL"] = my_encodeURL
    env.filters["escape_for_latex"] = escape_for_latex
    env.filters["replace_footnotes"] = replace_footnote_markers_filter
    env.filters["format_mantra_sets"] = format_mantra_sets
    env.filters["format_rik_only"] = format_rik_only
    env.filters["format_samam_only"] = format_samam_only
    env.filters["format_rik_nometa"] = format_rik_nometa
    env.filters["format_samam_nometa"] = format_samam_nometa
    env.filters["format_malayalam_rik_only"] = format_malayalam_rik_only
    env.filters["format_malayalam_rik_nometa"] = format_malayalam_rik_nometa
    env.filters["format_malayalam_samam_only"] = format_malayalam_samam_only
    env.filters["format_malayalam_samam_nometa"] = format_malayalam_samam_nometa
    env.filters["format_malayalam_combined"] = format_malayalam_combined
    env.filters["format_malayalam_samam"] = format_malayalam_samam
    env.filters["split_rik_lines_latex"] = split_rik_lines_latex
    env.filters["replacecolon"] = replacecolon
    env.filters["clean_toc_title"] = clean_toc_title
    env.filters["toc_header"] = toc_header
    return env
