"""
HTML Reader Jinja filters for Jaimineeya Samaveda Pipeline.
Provides standalone HTML reader formatting, CSS-based accent placements,
collapsible section footnotes, and Devanagari/Malayalam rendering.
"""

import re
import html
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
    from core.swara_engine import int_to_devanagari
except ImportError:
    from src.core.swara_engine import int_to_devanagari

try:
    from src.renderers.filters.latex_filters import (
        remove_mantra_spaces,
        _match_verse_num_marker,
        _parse_swara_and_modifiers,
        SWARA_CANONICAL_MAP,
    )
except ImportError:
    from renderers.filters.latex_filters import (
        remove_mantra_spaces,
        _match_verse_num_marker,
        _parse_swara_and_modifiers,
        SWARA_CANONICAL_MAP,
    )

try:
    from src.renderers.filters.text_filters import _ENGLISH_DIGITS
except ImportError:
    from renderers.filters.text_filters import _ENGLISH_DIGITS

# --- HTML Footnote State & Renderers ---
HTML_FOOTNOTE_COUNTER = 0
HTML_FOOTNOTES_ACCUMULATOR = []  # Accumulates footnotes across subsections within a section
HTML_SEEN_CONTENT_MAP = {} # Tracks seen footnote CONTENT -> (id, display_num)

def to_devanagari_numeral(num):
    """Convert Arabic numerals to Devanagari numerals."""
    if num is None:
        return ""
    mapping = {'0': '०', '1': '१', '2': '२', '3': '३', '4': '४',
               '5': '५', '6': '६', '7': '७', '8': '८', '9': '९'}
    return ''.join(mapping.get(c, c) for c in str(num))

def reset_html_footnote_counter(dummy=None):
    """Reset the HTML footnote counter AND clear the accumulator.
    Call this at section boundaries (start of each section).
    Takes a dummy argument so it can be used as a Jinja filter.
    Returns empty string so it doesn't output anything in the template.
    """
    global HTML_FOOTNOTE_COUNTER, HTML_FOOTNOTES_ACCUMULATOR, HTML_SEEN_CONTENT_MAP
    HTML_FOOTNOTES_ACCUMULATOR.clear()
    HTML_SEEN_CONTENT_MAP.clear()
    return ""

def accumulate_footnotes(footnotes_list):
    """Add footnotes to the section-level accumulator.
    Called by formatting functions instead of rendering inline.
    """
    global HTML_FOOTNOTES_ACCUMULATOR, HTML_SEEN_CONTENT_MAP
    HTML_FOOTNOTES_ACCUMULATOR.extend(footnotes_list)

def render_section_footnotes(dummy=None):
    """Render all accumulated footnotes for this section.
    Call this at section end in the template.
    Returns HTML for the footnote section, or empty string if no footnotes.
    """
    global HTML_FOOTNOTES_ACCUMULATOR
    
    if not HTML_FOOTNOTES_ACCUMULATOR:
        return ""
        
    output = ['<hr class="footnote-separator"/>']
    output.append('<div class="footnote-section">')
    for unique_id, display_num, text in HTML_FOOTNOTES_ACCUMULATOR:
        output.append(f'<div class="footnote-item" id="{unique_id}"><sup class="footnote-ref">{display_num}</sup> {text}</div>')
    output.append('</div>')
    
    return '\n'.join(output)

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

def replace_accents_html(text):
    """
    Replaces ASCII markers with HTML Unicode entities wrapped in spans for positioning.
    Fixes dotted circle issue across all fonts by ensuring Visarga (ः) attaches
    directly to the base syllable, with accents following Visarga styled with .accent-visarga.
    """
    if not text:
        return text

    # Step 1: Reorder any accent marker that precedes a Visarga so syllable + ः remain contiguous
    text = re.sub(r'(\([1-4]\))\s*([ः:])', r'ः\1', text)
    text = re.sub(r'([\u0951\u1CD2\u1CF8\u1CF9])\s*([ः:])', r'ः\1', text)
    text = re.sub(r'(<span class="accent-[^"]+">[^<]+</span>)\s*([ः:])', r'ः\1', text)

    # Step 2: Accents following Visarga receive .accent-visarga to shift backwards over the syllable
    visarga_replacements = [
        ('ः(1)', 'ः<span class="accent-swarita accent-visarga">&#x0951;</span>'),
        ('ः(2)', 'ः<span class="accent-anudatta accent-visarga">&#x1CD2;</span>'),
        ('ः(3)', 'ः<span class="accent-kampa accent-visarga">&#x1CF8;</span>'),
        ('ः(4)', 'ः<span class="accent-trikampa accent-visarga">&#x1CF9;</span>'),
        ('ः\u0951', 'ः<span class="accent-swarita accent-visarga">&#x0951;</span>'),
        ('ः\u1CD2', 'ः<span class="accent-anudatta accent-visarga">&#x1CD2;</span>'),
        ('ः\u1CF8', 'ः<span class="accent-kampa accent-visarga">&#x1CF8;</span>'),
        ('ः\u1CF9', 'ः<span class="accent-trikampa accent-visarga">&#x1CF9;</span>'),
    ]
    for marker, replacement in visarga_replacements:
        text = text.replace(marker, replacement)

    # Step 3: Standard accents (on syllables without Visarga)
    replacements = [
        ('(1)', '<span class="accent-swarita">&#x0951;</span>'),  # Swarita
        ('(2)', '<span class="accent-anudatta">&#x1CD2;</span>'),  # Anudatta
        ('(3)', '<span class="accent-kampa">&#x1CF8;</span>'),  # Kampa
        ('(4)', '<span class="accent-trikampa">&#x1CF9;</span>'),  # Trikampa
        ('\u0951', '<span class="accent-swarita">&#x0951;</span>'),
        ('\u1CD2', '<span class="accent-anudatta">&#x1CD2;</span>'),
        ('\u1CF8', '<span class="accent-kampa">&#x1CF8;</span>'),
        ('\u1CF9', '<span class="accent-trikampa">&#x1CF9;</span>'),
    ]
    for marker, replacement in replacements:
        text = text.replace(marker, replacement)
    return text

def split_rik_lines_html(text):
    """
    Splits multi-Rik text so each Rik appears on its own line.
    Splits after each verse marker (॥ N ॥) and joins with <br>.
    If only one Rik is present, returns the text unchanged.
    """
    if not text:
        return text
    # Split after each ॥ N ॥ pattern (Devanagari or ASCII digits)
    # The marker stays at the end of each segment
    parts = re.split(r'((?:॥|\|\|)\s*[०-९\d]+\s*(?:॥|\|\|))', text)
    if len(parts) <= 1:
        return text
    # Re-join: marker goes with the preceding text segment
    lines = []
    current = ''
    for part in parts:
        if re.match(r'(?:॥|\|\|)\s*[०-९\d]+\s*(?:॥|\|\|)', part):
            current += part
            lines.append(current.strip())
            current = ''
        else:
            current += part
    # If there's leftover text after the last marker, append it
    if current.strip():
        lines.append(current.strip())
    # Filter out empty lines
    lines = [l for l in lines if l]
    if len(lines) <= 1:
        return text
    return '<br>'.join(lines)

def process_footnotes_html(text, footnotes_dict=None, local_counter=0, seen_markers_map=None, subsection_key=None, doc_markers_map=None):
    """
    Replace (s1), (s2) markers with HTML superscript links.
    Uses LOCAL counter for display numbering (resets per subsection).
    Uses subsection_key for unique IDs to prevent collisions across document.
    Reuses existing footnote links if marker was already defined in the section or document context.
    
    Args:
        text: Text to process
        footnotes_dict: Dict mapping markers to text
        local_counter: Current local counter for this subsection (display only)
        seen_markers_map: Map of seen markers to (unique_id, display_num) in this section
        subsection_key: Unique key for this subsection
        doc_markers_map: Document-level fallback map for seen markers
        
    Returns:
        (processed_text, list_of_footnotes_data, new_local_counter)
        footnotes_data tuple: (unique_id, display_num, text)
    """
    if not text:
        return text, [], local_counter
    
    if footnotes_dict is None:
        footnotes_dict = {}
    
    footnotes_list = []
    
    # Sanitize invisible characters that break footnote matching
    invisible_chars_pattern = r'[\u200b\u200c\ufeff\u2060\u180e\u00ad]'
    text = re.sub(invisible_chars_pattern, '', text)
    text = re.sub(r'\u200d(?=\()', '', text)
    
    # regex to find (sX)
    matches = list(set(re.findall(r'\(s\d+\)', text))) # set to unique within this text block
    matches.sort(key=lambda x: int(x[2:-1]))

    for marker_full in matches:
        marker = marker_full[1:-1] # strip ( ) -> s1
        marker_key = f"@marker:{marker}"
        
        if marker in footnotes_dict:
            footnote_text = footnotes_dict[marker].strip()
            
            # Check if CONTENT has been seen in the broader context
            if seen_markers_map is not None and footnote_text in seen_markers_map:
                # Reuse existing number and ID
                unique_id, dev_num = seen_markers_map[footnote_text]
                # For duplicates, link to existing ID
                replacement = f'<sup class="footnote-ref"><a href="#{unique_id}">{dev_num}</a></sup>'
                text = text.replace(marker_full, replacement)
                seen_markers_map[marker_key] = (unique_id, dev_num)
                seen_markers_map[marker] = (unique_id, dev_num)
                if doc_markers_map is not None:
                    doc_markers_map[marker] = (unique_id, dev_num)
            else:
                # New footnote
                local_counter += 1
                devanagari_num = to_devanagari_numeral(local_counter)
                
                # Generate unique ID using subsection_key
                safe_key = subsection_key if subsection_key else "unknown"
                unique_id = f"fn-{safe_key}-{marker}"
                
                # Replace this specific marker occurrence
                replacement = f'<sup class="footnote-ref"><a href="#{unique_id}" id="ref-{unique_id}">{devanagari_num}</a></sup>'
                text = text.replace(marker_full, replacement)
                
                footnotes_list.append((unique_id, devanagari_num, footnote_text))
                
                if seen_markers_map is not None:
                    seen_markers_map[footnote_text] = (unique_id, devanagari_num)
                    seen_markers_map[marker_key] = (unique_id, devanagari_num)
                    seen_markers_map[marker] = (unique_id, devanagari_num)
                if doc_markers_map is not None:
                    doc_markers_map[marker] = (unique_id, devanagari_num)
        elif seen_markers_map is not None and (marker_key in seen_markers_map or marker in seen_markers_map):
            # Re-use already seen marker from section context
            unique_id, dev_num = seen_markers_map.get(marker_key) or seen_markers_map.get(marker)
            replacement = f'<sup class="footnote-ref"><a href="#{unique_id}">{dev_num}</a></sup>'
            text = text.replace(marker_full, replacement)
        elif doc_markers_map is not None and marker in doc_markers_map:
            # Re-use already seen marker from document context
            unique_id, dev_num = doc_markers_map[marker]
            replacement = f'<sup class="footnote-ref"><a href="#{unique_id}">{dev_num}</a></sup>'
            text = text.replace(marker_full, replacement)

    return text, footnotes_list, local_counter

# --- HTML Accent & Syllable Formatters ---
def escape_for_html(text):
    """Escape special HTML characters."""
    if not text:
        return text
    html_escapes = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
    }
    return ''.join(html_escapes.get(c, c) for c in text)

def format_dandas_html(text, preserve_spaces=False):
    """
    Formats danda symbols for HTML output.
    Adds appropriate spacing and wraps mantra numbers in spans.
    """
    if not text or not isinstance(text, str):
        return text

    # Normalize dandas
    text = re.sub(r'\|\|', '॥', text)
    text = re.sub(r'\|\s*\|', '॥', text)
    text = re.sub(r'।।', '॥', text)
    text = text.replace('|', '।')

    # Wrap mantra numbers in span
    danda_pattern = r'(?:\|\||॥)'
    digits = r'[\d०-९]+'
    pattern = rf'({danda_pattern})\s*({digits})\s*({danda_pattern})'
    text = re.sub(pattern, r'<span class="mantra-number">\1 \2 \3</span>', text)

    # Add spacing around dandas
    text = text.replace('॥', ' <span class="danda">॥</span> ')
    text = text.replace('।', ' <span class="danda">।</span> ')

    # Clean up extra spaces ONLY if we don't want to preserve manual alignments
    if not preserve_spaces:
        text = re.sub(r'\s+', ' ', text)
        
    return text.strip()


def handle_consecutive_trikamba_html(text):
    """
    Inserts a thin space between consecutive trikamba accent marks (4) in HTML
    to prevent visual overlap when rendered.
    
    This is only needed for HTML rendering; PDF rendering handles spacing correctly.
    """
    if not text:
        return text
    
    # Pattern: (4) followed by 1-3 characters (a single Devanagari grapheme cluster) 
    # and then another (4)
    # We insert a thin space character after the first character following (4)
    # when another (4) follows soon after
    
# Match: (4) + short text (1-3 chars) + (4)
    # Replace with: (4) + short text + thin space + (4)
    pattern = r'\(4\)([^\(\)]{1,3})\(4\)'
    replacement = r'(4)\1 (4)'  # Insert a regular space before the second (4)
    
    text = re.sub(pattern, replacement, text)
    
    return text

HTML_MOD_MAP = {
    'C': ('mod-c', '&#xE001;', 'Upper Shoulder Dot (·)'),
    'c': ('mod-c', '&#xE001;', 'Upper Shoulder Dot (·)'),
    '·': ('mod-c', '&#xE001;', 'Upper Shoulder Dot (·)'),
    'ॱ': ('mod-c', '&#xE001;', 'Upper Shoulder Dot (·)'),
    '़': ('mod-c', '&#xE001;', 'Upper Shoulder Dot (·)'),
    'H': ('mod-h', '&#xE00C;', 'High Pitch Swarita (|)'),
    'h': ('mod-h', '&#xE00C;', 'High Pitch Swarita (|)'),
    '|': ('mod-h', '&#xE00C;', 'High Pitch Swarita (|)'),
    'G': ('mod-g', '&#xE003;', 'Lower Under-Slash (\\)'),
    'g': ('mod-g', '&#xE003;', 'Lower Under-Slash (\\)'),
    '\\': ('mod-g', '&#xE003;', 'Lower Under-Slash (\\)'),
    'A': ('mod-a', '&#xE004;', 'Melodic Arc (⁀)'),
    'a': ('mod-a', '&#xE004;', 'Melodic Arc (⁀)'),
    '⁀': ('mod-a', '&#xE004;', 'Melodic Arc (⁀)'),
    'A1': ('mod-a1', '&#xE00D;', 'Arc over Danda'),
    'a1': ('mod-a1', '&#xE00D;', 'Arc over Danda'),
    'A_1': ('mod-a1', '&#xE00D;', 'Arc over Danda'),
    'a_1': ('mod-a1', '&#xE00D;', 'Arc over Danda'),
    'A2': ('mod-a2', '&#xE02E;', 'Overhead Conjunct Arc'),
    'a2': ('mod-a2', '&#xE02E;', 'Overhead Conjunct Arc'),
    'A_2': ('mod-a2', '&#xE02E;', 'Overhead Conjunct Arc'),
    'a_2': ('mod-a2', '&#xE02E;', 'Overhead Conjunct Arc'),
    '\uE02E': ('mod-a2', '&#xE02E;', 'Overhead Conjunct Arc'),
    'D': ('mod-d', '&#xE006;', 'Chevron Roof (∧)'),
    'd': ('mod-d', '&#xE006;', 'Chevron Roof (∧)'),
    '∧': ('mod-d', '&#xE006;', 'Chevron Roof (∧)'),
    'Ʌ': ('mod-d', '&#xE006;', 'Chevron Roof (∧)'),
    'D1': ('mod-d1', '&#xE00E;', 'Rising Stroke (↗)'),
    'd1': ('mod-d1', '&#xE00E;', 'Rising Stroke (↗)'),
    'D_1': ('mod-d1', '&#xE00E;', 'Rising Stroke (↗)'),
    'd_1': ('mod-d1', '&#xE00E;', 'Rising Stroke (↗)'),
    '↗': ('mod-d1', '&#xE00E;', 'Rising Stroke (↗)'),
    '\uE00E': ('mod-d1', '&#xE00E;', 'Rising Stroke (↗)'),
    'D2': ('mod-d2', '&#xE00F;', 'Check Tick (✓)'),
    'd2': ('mod-d2', '&#xE00F;', 'Check Tick (✓)'),
    'D_2': ('mod-d2', '&#xE00F;', 'Check Tick (✓)'),
    'd_2': ('mod-d2', '&#xE00F;', 'Check Tick (✓)'),
    '✓': ('mod-d2', '&#xE00F;', 'Check Tick (✓)'),
    '\uE00F': ('mod-d2', '&#xE00F;', 'Check Tick (✓)'),
    'I': ('mod-i', '&#xE02A;', 'Double Shoulder Dash (⫽)'),
    'i': ('mod-i', '&#xE02A;', 'Double Shoulder Dash (⫽)'),
    '⫽': ('mod-i', '&#xE02A;', 'Double Shoulder Dash (⫽)'),
    '\uE02A': ('mod-i', '&#xE02A;', 'Double Shoulder Dash (⫽)'),
    'J': ('mod-j', '&#xE02B;', 'Overhead Horizontal Bar (¯)'),
    'j': ('mod-j', '&#xE02B;', 'Overhead Horizontal Bar (¯)'),
    '¯': ('mod-j', '&#xE02B;', 'Overhead Horizontal Bar (¯)'),
    '\uE02B': ('mod-j', '&#xE02B;', 'Overhead Horizontal Bar (¯)'),
    'B1': ('mod-b1', '&#xE02C;', 'Diagonal Bridging Slash (/)'),
    'b1': ('mod-b1', '&#xE02C;', 'Diagonal Bridging Slash (/)'),
    'B_1': ('mod-b1', '&#xE02C;', 'Diagonal Bridging Slash (/)'),
    'b_1': ('mod-b1', '&#xE02C;', 'Diagonal Bridging Slash (/)'),
    '/': ('mod-b1', '&#xE02C;', 'Diagonal Bridging Slash (/)'),
    '\uE02C': ('mod-b1', '&#xE02C;', 'Diagonal Bridging Slash (/)'),
    'K': ('mod-k', '&#xE02D;', 'Shoulder Cross Mark (⨯)'),
    'k': ('mod-k', '&#xE02D;', 'Shoulder Cross Mark (⨯)'),
    '⨯': ('mod-k', '&#xE02D;', 'Shoulder Cross Mark (⨯)'),
    '\uE02D': ('mod-k', '&#xE02D;', 'Shoulder Cross Mark (⨯)'),
    'B': ('mod-b', '&#xE005;', 'Peak Elevation Caret (∧)'),
    'b': ('mod-b', '&#xE005;', 'Peak Elevation Caret (∧)'),
    '^': ('mod-b', '&#xE005;', 'Peak Elevation Caret (∧)'),
    '\uE005': ('mod-b', '&#xE005;', 'Peak Elevation Caret (∧)'),
    'E': ('mod-e', '&#xE002;', 'Bold Tone Column (┃)'),
    'e': ('mod-e', '&#xE002;', 'Bold Tone Column (┃)'),
    '┃': ('mod-e', '&#xE002;', 'Bold Tone Column (┃)'),
    '\uE002': ('mod-e', '&#xE002;', 'Bold Tone Column (┃)'),
    'F': ('mod-f', '&#xE008;', 'Danda with Overhead Dot (╷)'),
    'f': ('mod-f', '&#xE008;', 'Danda with Overhead Dot (╷)'),
    '╷': ('mod-f', '&#xE008;', 'Danda with Overhead Dot (╷)'),
    '\uE008': ('mod-f', '&#xE008;', 'Danda with Overhead Dot (╷)'),
    '_': ('mod-under', '_', 'Underbar'),
    ',': ('mod-comma', ',', 'Comma'),
    '.': ('mod-dot', '.', 'Dot')
}

def render_mod_html(mod_str: str) -> str:
    m = mod_str.strip('()')
    if m in HTML_MOD_MAP:
        cls, glyph, title = HTML_MOD_MAP[m]
        return f'<span class="swara-mod {cls}" title="{title}">{glyph}</span>'
    return f'<span class="swara-mod">{mod_str}</span>'

ALL_SWARA_PUNCT_CHARS = '_,.\\·ॱ़┃L╷^⁀∧✓↗⫽¯/⨯\uE001\uE002\uE003\uE004\uE005\uE006\uE008\uE00D\uE00E\uE00F\uE02A\uE02B\uE02C\uE02D\uE02E'

DEVA_SYLLABLE_RE = re.compile(
    r'(?:[\u0904-\u0914\u0960\u0961]|(?:[\u0915-\u0939\u0958-\u095F]\u094D)*[\u0915-\u0939\u0958-\u095F](?:[\u093E-\u094D\u094E\u094F\u0955-\u0957\u0962\u0963])?)(?:[\u0901-\u0903])?(?:[' + re.escape(ALL_SWARA_PUNCT_CHARS) + r'])*'
)

def split_deva_syllables(text: str):
    res = DEVA_SYLLABLE_RE.findall(text)
    return res if res else ([text] if text else [])

def format_deva_syl_html(syl: str, with_modifiers: bool = True) -> str:
    if not with_modifiers:
        return syl.rstrip(ALL_SWARA_PUNCT_CHARS)
    m = re.match(r'^(.*?)([' + re.escape(ALL_SWARA_PUNCT_CHARS) + r']*)$', syl)
    base = m.group(1) if m else syl
    extras = m.group(2) if m else ''
    extras_list = []
    has_mod_g = False
    for e in extras:
        if e in ('\\', '\uE003'):
            has_mod_g = True
        else:
            extras_list.append(render_mod_html(e))
    syl_core = f'<span class="syl-mod-g-wrap">{base}<span class="swara-mod mod-g" title="MOD-G: Lower Under-Slash (\\)">&#xE003;</span></span>' if has_mod_g else base
    return syl_core + ''.join(extras_list)

def render_deva_html_from_line(
    line: str,
    with_modifiers: bool = True,
    footnote_data: dict = None,
    seen_markers_map: dict = None,
    subsection_key: str = None,
    footnote_counter_obj: list = None,
    collected_footnotes: list = None,
    doc_markers_map: dict = None
) -> str:
    """Render a Devanagari mantra line to flexbox-stacked HTML matching visual baseline."""
    line = re.sub(r'[\u200b\u200c\ufeff\u2060\u180e\u00ad]', '', line)
    line = re.sub(r'\u200d(?=\()', '', line)
    line = re.sub(r'(\S)\s+\(', r'\1(', line)
    from core.swara_engine import tokenize_mantra_line
    tokens = tokenize_mantra_line(line)
    
    # Identify spanning markers that attach to the preceding word
    SPANNING_MARKERS = {'A', 'a', '⁀', 'A1', 'a1', 'A_1', 'a_1', '\uE00D', 'D', 'd', '∧', 'Ʌ', 'B', 'b', '^', 'B1', 'b1'}
    
    rendered_items = []
    
    idx = 0
    while idx < len(tokens):
        v_count, v_num = _match_verse_num_marker(tokens, idx)
        if v_count > 0:
            rendered_items.append({
                'type': 'verse_num',
                'html': f'<span class="mantra-word verse-num-word"><span class="mantra-text verse-num-marker"><span class="danda">॥</span><span class="verse-num">{v_num}</span><span class="danda">॥</span></span><span class="swara-text">&nbsp;</span></span>'
            })
            idx += v_count
            continue
            
        tok = tokens[idx]
        t = tok['type']
        
        if t == 'space':
            prev_is_danda = (idx > 0 and tokens[idx-1]['type'] == 'danda')
            if prev_is_danda:
                rendered_items.append({
                    'type': 'space',
                    'html': '<span class="mantra-word word-space"><span class="mantra-text">&nbsp;</span><span class="swara-text">&nbsp;</span></span>'
                })
        elif t == 'danda':
            rendered_items.append({
                'type': 'danda',
                'char': tok["char"],
                'html': f'<span class="mantra-word"><span class="mantra-text danda">{tok["char"]}</span><span class="swara-text">&nbsp;</span></span>'
            })
        elif t == 'marker':
            m_val = tok.get('marker', '').strip('()')
            if with_modifiers and m_val in SPANNING_MARKERS:
                if m_val in ('A', 'a', '⁀', '\uE004'):
                    d_idx = idx + 1
                    while d_idx < len(tokens) and tokens[d_idx]['type'] == 'space':
                        d_idx += 1
                    if d_idx < len(tokens) and tokens[d_idx]['type'] == 'danda' and tokens[d_idx]['char'] == '।':
                        m_val = 'A1'
                mod_h = render_mod_html(m_val)
                attached = False
                for prev_item in reversed(rendered_items):
                    if prev_item['type'] == 'word':
                        prev_item['spanning_mod'] = mod_h
                        prev_item['spanning_type'] = m_val
                        attached = True
                        break
                if not attached:
                    rendered_items.append({
                        'type': 'marker',
                        'html': f'<span class="mantra-word"><span class="mantra-text">{mod_h}</span><span class="swara-text">&nbsp;</span></span>'
                    })
            elif with_modifiers:
                mod_h = render_mod_html(tok['marker'])
                rendered_items.append({
                    'type': 'marker',
                    'html': f'<span class="mantra-word"><span class="mantra-text">{mod_h}</span><span class="swara-text">&nbsp;</span></span>'
                })
        elif t == 'footnote':
            marker_full = tok.get('text', '')
            marker = marker_full.strip('()')
            fn_html = f'<sup>{marker_full}</sup>'
            if footnote_data and marker in footnote_data:
                footnote_text = footnote_data[marker].strip()
                if seen_markers_map is not None and footnote_text in seen_markers_map:
                    unique_id, dev_num = seen_markers_map[footnote_text]
                    fn_html = f'<sup class="footnote-ref"><a href="#{unique_id}">{dev_num}</a></sup>'
                else:
                    if footnote_counter_obj is not None:
                        footnote_counter_obj[0] += 1
                        cnt = footnote_counter_obj[0]
                    else:
                        cnt = 1
                    dev_num = to_devanagari_numeral(cnt)
                    safe_key = subsection_key if subsection_key else "unknown"
                    unique_id = f"fn-{safe_key}-{marker}"
                    fn_html = f'<sup class="footnote-ref"><a href="#{unique_id}" id="ref-{unique_id}">{dev_num}</a></sup>'
                    if collected_footnotes is not None:
                        collected_footnotes.append((unique_id, dev_num, footnote_text))
                    if seen_markers_map is not None:
                        seen_markers_map[footnote_text] = (unique_id, dev_num)
                        seen_markers_map[f"@marker:{marker}"] = (unique_id, dev_num)
                        seen_markers_map[marker] = (unique_id, dev_num)
                    if doc_markers_map is not None:
                        doc_markers_map[marker] = (unique_id, dev_num)
            elif seen_markers_map is not None and (f"@marker:{marker}" in seen_markers_map or marker in seen_markers_map):
                unique_id, dev_num = seen_markers_map.get(f"@marker:{marker}") or seen_markers_map.get(marker)
                fn_html = f'<sup class="footnote-ref"><a href="#{unique_id}">{dev_num}</a></sup>'
            elif doc_markers_map is not None and marker in doc_markers_map:
                unique_id, dev_num = doc_markers_map[marker]
                fn_html = f'<sup class="footnote-ref"><a href="#{unique_id}">{dev_num}</a></sup>'
            
            if rendered_items and rendered_items[-1]['type'] == 'word':
                rendered_items[-1]['footnote_html'] = rendered_items[-1].get('footnote_html', '') + fn_html
            elif rendered_items and rendered_items[-1]['type'] in ('danda', 'verse_num'):
                rendered_items[-1]['html'] += fn_html
            else:
                rendered_items.append({
                    'type': 'footnote',
                    'html': fn_html
                })
        elif t == 'word':
            word = tok.get('word', '')
            swara = tok.get('swara', '')
            visarga = tok.get('visarga', '')
            if visarga:
                word += visarga
            
            span_mod_html = None
            span_mod_type = None
            if not with_modifiers:
                core_word = word.strip(ALL_SWARA_PUNCT_CHARS)
                punct_html = ''
                mods_html = ''
                sw_parts, _ = _parse_swara_and_modifiers(swara)
            else:
                leading_punct = ""
                while word and word[0] in ALL_SWARA_PUNCT_CHARS:
                    leading_punct += word[0]
                    word = word[1:]
                core_word = word.rstrip(ALL_SWARA_PUNCT_CHARS)
                trailing_punct = word[len(core_word):]
                punct_html = ''.join([render_mod_html(p) for p in (leading_punct + trailing_punct)])
                sw_parts, mods = _parse_swara_and_modifiers(swara)
                
                # Look ahead to check if followed by danda
                next_is_danda = False
                n_idx = idx + 1
                while n_idx < len(tokens) and tokens[n_idx]['type'] == 'space':
                    n_idx += 1
                if n_idx < len(tokens) and tokens[n_idx]['type'] == 'danda' and tokens[n_idx]['char'] == '।':
                    next_is_danda = True
                
                reg_mods = []
                has_mod_g_word = False
                for m in mods:
                    m_clean = m.strip('()')
                    if m_clean in SPANNING_MARKERS:
                        if m_clean in ('A', 'a', '⁀', '\uE004') and next_is_danda:
                            m_clean = 'A1'
                        span_mod_html = render_mod_html(m_clean)
                        span_mod_type = m_clean
                    elif m_clean in ('G', 'g', '\\', '\uE003'):
                        has_mod_g_word = True
                    else:
                        reg_mods.append(m)
                mods_html = ''.join([render_mod_html(m) for m in reg_mods])
            
            sw_letter = ' '.join(sw_parts) if sw_parts else ''
            syllables = split_deva_syllables(core_word) if core_word else []
            last_syl = syllables.pop() if syllables else ''
            
            w_html_parts = []
            for syl in syllables:
                syl_formatted = format_deva_syl_html(syl, with_modifiers=with_modifiers)
                w_html_parts.append(f'<span class="mantra-word"><span class="mantra-text">{syl_formatted}</span><span class="swara-text">&nbsp;</span></span>')
            
            last_syl_formatted = format_deva_syl_html(last_syl, with_modifiers=with_modifiers) if last_syl else ''
            if has_mod_g_word and 'syl-mod-g-wrap' not in last_syl_formatted:
                last_syl_formatted = f'<span class="syl-mod-g-wrap">{last_syl_formatted}<span class="swara-mod mod-g" title="MOD-G: Lower Under-Slash (\\)">&#xE003;</span></span>'
            
            rendered_items.append({
                'type': 'word',
                'prefix_syls_html': ''.join(w_html_parts),
                'last_syl_formatted': last_syl_formatted,
                'mods_html': mods_html,
                'punct_html': punct_html,
                'bot_content': sw_letter if sw_letter else "&nbsp;",
                'spanning_mod': span_mod_html,
                'spanning_type': span_mod_type
            })
        idx += 1

    # Now assemble final HTML, wrapping connected spanning groups in <span class="mantra-connected-group">
    final_output = []
    i = 0
    while i < len(rendered_items):
        item = rendered_items[i]
        if item['type'] == 'word' and item.get('spanning_mod'):
            # This word has a spanning modifier connecting to next word (and possibly danda)
            group_items = [item]
            j = i + 1
            while j < len(rendered_items):
                next_it = rendered_items[j]
                if next_it['type'] == 'space':
                    # Remove whitespace around danda inside spanning connected groups
                    j += 1
                    continue
                group_items.append(next_it)
                j += 1
                if next_it['type'] == 'word' and not next_it.get('spanning_mod'):
                    break
            
            has_a1_group = any(g.get('spanning_type') in ('A1', 'a1', 'A_1', 'a_1', '\uE00D') for g in group_items if g['type'] == 'word')
            group_html = []
            for g_item in group_items:
                if g_item['type'] == 'word':
                    span_mod_str = '' if (g_item.get('spanning_type') in ('A1', 'a1', 'A_1', 'a_1', '\uE00D')) else (g_item.get('spanning_mod') or '')
                    fn_str = g_item.get('footnote_html', '')
                    top_content = f"{g_item['last_syl_formatted']}{g_item['mods_html']}{g_item['punct_html']}{fn_str}{span_mod_str}" if (g_item['last_syl_formatted'] or g_item['mods_html'] or g_item['punct_html'] or fn_str or span_mod_str) else "&nbsp;"
                    bot_content = g_item['bot_content']
                    word_html = f"{g_item['prefix_syls_html']}<span class=\"mantra-word\"><span class=\"mantra-text\">{top_content}</span><span class=\"swara-text\">{bot_content}</span></span>"
                    group_html.append(word_html)
                elif g_item['type'] == 'danda' and has_a1_group:
                    a1_html = render_mod_html('A1')
                    d_ch = g_item.get("char", "।")
                    group_html.append('<span class="mantra-word word-space"><span class="mantra-text">&nbsp;</span><span class="swara-text">&nbsp;</span></span>')
                    group_html.append(f'<span class="mantra-word danda-word-a1"><span class="mantra-text danda danda-with-arc">{d_ch}{a1_html}</span><span class="swara-text">&nbsp;</span></span>')
                    group_html.append('<span class="mantra-word word-space"><span class="mantra-text">&nbsp;</span><span class="swara-text">&nbsp;</span></span>')
                else:
                    group_html.append(g_item['html'])
            
            final_output.append(f'<span class="mantra-connected-group">{"".join(group_html)}</span>')
            i = j
        else:
            if item['type'] == 'word':
                fn_str = item.get('footnote_html', '')
                top_content = f"{item['last_syl_formatted']}{item['mods_html']}{item['punct_html']}{fn_str}" if (item['last_syl_formatted'] or item['mods_html'] or item['punct_html'] or fn_str) else "&nbsp;"
                bot_content = item['bot_content']
                word_html = f"{item['prefix_syls_html']}<span class=\"mantra-word\"><span class=\"mantra-text\">{top_content}</span><span class=\"swara-text\">{bot_content}</span></span>"
                final_output.append(word_html)
            else:
                final_output.append(item['html'])
            i += 1
            
    return ''.join(final_output)


def format_mantra_sets_html(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None, subsection_key=None, 
                              footnote_counter=0, footnotes_accumulator=None, seen_content_map=None, with_modifiers=True, doc_markers_map=None):
    """
    Formats mantra data as HTML using ruby-based layout for word/swara stacking.
    Only renders rik_metadata and rik_text if rik_id differs from prev_rik_id.
    """
    HTML_FOOTNOTE_COUNTER = footnote_counter
    formatted_output = []
    collected_footnotes = []
    seen_markers_map = seen_content_map if seen_content_map is not None else {}

    # --- DATA EXTRACTION ---
    current_rik_id = subsection.get('rik_id')
    current_rik_ids = subsection.get('rik_ids', [current_rik_id] if current_rik_id else [])
    string_1 = subsection.get('rik_metadata', '')
    string_2 = subsection.get('rik_text', '')
    string_3 = subsection.get('saman_metadata', '')
    footnote_data = subsection.get('footnotes', {})
    
    show_rik_info = (prev_rik_id is None) or (current_rik_id != prev_rik_id)
    if not show_rik_info and len(current_rik_ids) > 1:
        max_rik_id = max(current_rik_ids) if current_rik_ids else None
        if max_rik_id is not None and max_rik_id != prev_rik_id:
            show_rik_info = True
    
    # Clean titles
    display_sub_title = re.sub(r'^([|॥]+)\s*', r'\1 ', subsection_title) if subsection_title else ''

    # 1. Rik Metadata - Only if rik_id changed
    if string_1 and show_rik_info:
        s1 = escape_for_html(string_1)
        s1 = format_dandas_html(s1, preserve_spaces=True)
        s1, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(s1, footnote_data, HTML_FOOTNOTE_COUNTER, seen_markers_map, subsection_key, doc_markers_map=doc_markers_map)
        collected_footnotes.extend(fnotes)
        formatted_output.append(f'<div class="rik-metadata sanskrit-text">{s1}</div>')

    # 2. Rik Text (With accents) - Only if rik_id changed
    if string_2 and show_rik_info:
        s2 = remove_mantra_spaces(string_2)
        s2 = s2.replace('\\newline%', '').replace('\\newline', '')
        s2 = escape_for_html(s2)
        s2, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(s2, footnote_data, HTML_FOOTNOTE_COUNTER, seen_markers_map, subsection_key, doc_markers_map=doc_markers_map)
        collected_footnotes.extend(fnotes)
        s2 = handle_consecutive_trikamba_html(s2)
        s2 = replace_accents_html(s2)
        s2 = split_rik_lines_html(s2)
        s2 = format_dandas_html(s2)
        formatted_output.append(f'<div class="rik-text sanskrit-text">{s2}</div>')

    # 3. Combined Header
    header_parts = []
    if display_sub_title and display_sub_title != section_title:
        header_title = escape_for_html(display_sub_title)
        header_title = format_dandas_html(header_title)
        header_parts.append(f'<span class="header-title">{header_title}</span>')
    ta_code = subsection.get('ta_code')
    if ta_code:
        header_parts.append(f'<span class="anuvaka-code">{escape_for_html(ta_code)}</span>')
    if string_3:
        meta = escape_for_html(string_3)
        meta = format_dandas_html(meta, preserve_spaces=True)
        meta, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(meta, footnote_data, HTML_FOOTNOTE_COUNTER, seen_markers_map, subsection_key, doc_markers_map=doc_markers_map)
        collected_footnotes.extend(fnotes)
        header_parts.append(f'<span class="header-meta">{meta}</span>')
    
    if header_parts:
        formatted_output.append(f'<div class="subsection-header">{" &nbsp; ".join(header_parts)}</div>')

    # 4. Baraha / Prose / Verse content lines
    content_lines = subsection.get('content_lines') or subsection.get('content')
    if content_lines:
        for line in content_lines:
            s_line = escape_for_html(line)
            s_line = format_dandas_html(s_line, preserve_spaces=True)
            formatted_output.append(f'<p class="sanskrit-text verse-p">{s_line}</p>')

    # --- MANTRA CONTENT RENDERING ---
    mantra_sets = subsection.get('corrected-mantra_sets', [])
    if not mantra_sets:
        mantra_sets = subsection.get('mantra_sets', [])

    mantra_array = []
    for mset in mantra_sets:
        m = mset.get('corrected-mantra') or mset.get('mantra', '')
        if m:
            mantra_array.append(m)
        elif mset.get('mantra-words'):
            words = []
            for word_dict in mset.get('mantra-words', []):
                w = word_dict.get('word', '')
                sw = word_dict.get('swara', '')
                if sw:
                    words.append(f"{w}({sw})")
                else:
                    words.append(w)
            if words:
                mantra_array.append(" ".join(words))

    fn_counter_obj = [HTML_FOOTNOTE_COUNTER]
    for mantra_line in mantra_array:
        clean_mantra = mantra_line.replace('\\newline%', ' ').replace('\\newline', ' ')
        clean_mantra = re.sub(r'[\u200b\u200c\ufeff\u2060\u180e\u00ad]', '', clean_mantra)
        clean_mantra = re.sub(r'\u200d(?=\()', '', clean_mantra)
        clean_mantra = re.sub(r'(\S)\s+\(', r'\1(', clean_mantra)
        
        verse_parts = re.split(r'(॥\s*[\d०-९]+\s*॥)', clean_mantra)
        
        for idx_v in range(0, len(verse_parts), 2):
            v_text = verse_parts[idx_v].strip()
            v_marker = verse_parts[idx_v + 1] if idx_v + 1 < len(verse_parts) else ''
            
            if not v_text and not v_marker:
                continue
                
            v_html = render_deva_html_from_line(
                v_text,
                with_modifiers=with_modifiers,
                footnote_data=footnote_data,
                seen_markers_map=seen_markers_map,
                subsection_key=subsection_key,
                footnote_counter_obj=fn_counter_obj,
                collected_footnotes=collected_footnotes,
                doc_markers_map=doc_markers_map
            )
            if v_marker:
                v_num_match = re.search(r'[\d०-९]+', v_marker)
                v_num = v_num_match.group(0) if v_num_match else ''
                v_html += f' <span class="mantra-word verse-num-word"><span class="mantra-text verse-num-marker"><span class="danda">॥</span><span class="verse-num">{v_num}</span><span class="danda">॥</span></span><span class="swara-text">&nbsp;</span></span>'
                
            is_mixed = bool(string_2.strip())
            style = ' style="margin-bottom: 2.5rem;"' if is_mixed else ''
            formatted_output.append(f'<div class="mantra-verse"{style}>{v_html}</div>')

    HTML_FOOTNOTE_COUNTER = fn_counter_obj[0]
    # Accumulate footnotes for section-level rendering (don't render inline)
    if collected_footnotes and footnotes_accumulator is not None:
        footnotes_accumulator.extend(collected_footnotes)

    return '\n'.join(formatted_output), HTML_FOOTNOTE_COUNTER


def format_rik_only_html(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None, subsection_key=None,
                         footnote_counter=0, footnotes_accumulator=None, seen_content_map=None, doc_markers_map=None, prev_rik_text=None):
    """
    Format only Rik content (rik_metadata and rik_text) for HTML separate output mode.
    Skips all Samam-related content.
    """
    HTML_FOOTNOTE_COUNTER = footnote_counter
    formatted_output = []
    collected_footnotes = []
    footnote_data = subsection.get('footnotes', {})
    seen_markers_map = seen_content_map if seen_content_map is not None else {}
    
    current_rik_id = get_canonical_rik_id(subsection)
    string_1 = subsection.get('rik_metadata', '')
    string_2 = subsection.get('rik_text', '')
    
    if not string_1 and not string_2:
        return "", HTML_FOOTNOTE_COUNTER
    
    # Skip consecutive duplicate Rik text across multiple Samams
    if prev_rik_text and string_2 and string_2.strip() == prev_rik_text.strip():
        return "", HTML_FOOTNOTE_COUNTER

    show_rik_info = (prev_rik_id is None) or (current_rik_id != prev_rik_id)
    if not show_rik_info:
        return "", HTML_FOOTNOTE_COUNTER
    
    if string_1:
        s1 = escape_for_html(string_1)
        s1 = format_dandas_html(s1, preserve_spaces=True)
        s1, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(s1, footnote_data, HTML_FOOTNOTE_COUNTER, seen_markers_map, subsection_key, doc_markers_map=doc_markers_map)
        collected_footnotes.extend(fnotes)
        formatted_output.append(f'<div class="rik-metadata sanskrit-text">{s1}</div>')

    if string_2:
        s2 = remove_mantra_spaces(string_2)
        s2 = s2.replace('\\newline%', '').replace('\\newline', '')
        s2 = escape_for_html(s2)
        s2, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(s2, footnote_data, HTML_FOOTNOTE_COUNTER, seen_markers_map, subsection_key, doc_markers_map=doc_markers_map)
        collected_footnotes.extend(fnotes)
        s2 = handle_consecutive_trikamba_html(s2)
        s2 = replace_accents_html(s2)
        s2 = split_rik_lines_html(s2)
        s2 = format_dandas_html(s2)
        formatted_output.append(f'<div class="rik-text sanskrit-text">{s2}</div>')

    if collected_footnotes and footnotes_accumulator is not None:
        footnotes_accumulator.extend(collected_footnotes)

    return '\n'.join(formatted_output), HTML_FOOTNOTE_COUNTER


def format_rik_nometa_html(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None, subsection_key=None,
                           footnote_counter=0, footnotes_accumulator=None, seen_content_map=None, doc_markers_map=None, prev_rik_text=None):
    """
    Format only Rik text (without rik_metadata) for HTML nometa output mode.
    Skips all Samam-related content and metadata.
    """
    HTML_FOOTNOTE_COUNTER = footnote_counter
    formatted_output = []
    collected_footnotes = []
    footnote_data = subsection.get('footnotes', {})
    seen_markers_map = seen_content_map if seen_content_map is not None else {}
    
    current_rik_id = get_canonical_rik_id(subsection)
    string_2 = subsection.get('rik_text', '')
    
    if not string_2:
        return "", HTML_FOOTNOTE_COUNTER
    
    # Skip consecutive duplicate Rik text across multiple Samams
    if prev_rik_text and string_2.strip() == prev_rik_text.strip():
        return "", HTML_FOOTNOTE_COUNTER

    show_rik_info = (prev_rik_id is None) or (current_rik_id != prev_rik_id)
    if not show_rik_info:
        return "", HTML_FOOTNOTE_COUNTER
    
    if string_2:
        s2 = remove_mantra_spaces(string_2)
        s2 = s2.replace('\\newline%', '').replace('\\newline', '')
        s2 = escape_for_html(s2)
        s2, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(s2, footnote_data, HTML_FOOTNOTE_COUNTER, seen_markers_map, subsection_key, doc_markers_map=doc_markers_map)
        collected_footnotes.extend(fnotes)
        s2 = handle_consecutive_trikamba_html(s2)
        s2 = replace_accents_html(s2)
        s2 = split_rik_lines_html(s2)
        s2 = format_dandas_html(s2)
        formatted_output.append(f'<div class="rik-text">{s2}</div>')

    if collected_footnotes and footnotes_accumulator is not None:
        footnotes_accumulator.extend(collected_footnotes)

    return '\n'.join(formatted_output), HTML_FOOTNOTE_COUNTER


def format_samam_only_html(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None, subsection_key=None,
                           footnote_counter=0, footnotes_accumulator=None, seen_content_map=None, with_modifiers=True, doc_markers_map=None):
    """
    Format only Samam content (header, saman_metadata, mantra text) for HTML separate output mode.
    Skips all Rik-related content.
    """
    HTML_FOOTNOTE_COUNTER = footnote_counter
    formatted_output = []
    collected_footnotes = []
    footnote_data = subsection.get('footnotes', {})
    seen_markers_map = seen_content_map if seen_content_map is not None else {}
    
    string_3 = subsection.get('saman_metadata', '')
    
    # Clean titles
    display_sub_title = re.sub(r'^([|॥]+)\s*', r'\1 ', subsection_title) if subsection_title else ''

    # Header
    header_parts = []
    if display_sub_title:
        header_title = escape_for_html(display_sub_title)
        header_title = format_dandas_html(header_title)
        header_parts.append(f'<span class="header-title">{header_title}</span>')
    if string_3:
        meta = escape_for_html(string_3)
        meta = format_dandas_html(meta, preserve_spaces=True)
        meta, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(meta, footnote_data, HTML_FOOTNOTE_COUNTER, seen_markers_map, subsection_key, doc_markers_map=doc_markers_map)
        collected_footnotes.extend(fnotes)
        header_parts.append(f'<span class="header-meta">{meta}</span>')
    
    if header_parts:
        formatted_output.append(f'<div class="subsection-header">{" &nbsp; ".join(header_parts)}</div>')

    # Mantra Content
    mantra_sets = subsection.get('corrected-mantra_sets', [])
    if not mantra_sets:
        mantra_sets = subsection.get('mantra_sets', [])

    mantra_array = []
    for mset in mantra_sets:
        m = mset.get('corrected-mantra') or mset.get('mantra', '')
        if m:
            mantra_array.append(m)
        elif mset.get('mantra-words'):
            words = []
            for word_dict in mset.get('mantra-words', []):
                w = word_dict.get('word', '')
                sw = word_dict.get('swara', '')
                if sw:
                    words.append(f"{w}({sw})")
                else:
                    words.append(w)
            if words:
                mantra_array.append(" ".join(words))

    fn_counter_obj = [HTML_FOOTNOTE_COUNTER]
    for mantra_line in mantra_array:
        clean_mantra = mantra_line.replace('\\newline%', ' ').replace('\\newline', ' ')
        clean_mantra = re.sub(r'[\u200b\u200c\ufeff\u2060\u180e\u00ad]', '', clean_mantra)
        clean_mantra = re.sub(r'\u200d(?=\()', '', clean_mantra)
        clean_mantra = re.sub(r'(\S)\s+\(', r'\1(', clean_mantra)
        
        verse_parts = re.split(r'(॥\s*[\d०-९]+\s*॥)', clean_mantra)
        
        for idx_v in range(0, len(verse_parts), 2):
            v_text = verse_parts[idx_v].strip()
            v_marker = verse_parts[idx_v + 1] if idx_v + 1 < len(verse_parts) else ''
            
            if not v_text and not v_marker:
                continue
                
            v_html = render_deva_html_from_line(
                v_text,
                with_modifiers=with_modifiers,
                footnote_data=footnote_data,
                seen_markers_map=seen_markers_map,
                subsection_key=subsection_key,
                footnote_counter_obj=fn_counter_obj,
                collected_footnotes=collected_footnotes,
                doc_markers_map=doc_markers_map
            )
            if v_marker:
                v_num_match = re.search(r'[\d०-९]+', v_marker)
                v_num = v_num_match.group(0) if v_num_match else ''
                v_html += f' <span class="mantra-word verse-num-word"><span class="mantra-text verse-num-marker"><span class="danda">॥</span><span class="verse-num">{v_num}</span><span class="danda">॥</span></span><span class="swara-text">&nbsp;</span></span>'
                
            formatted_output.append(f'<div class="mantra-verse">{v_html}</div>')

    HTML_FOOTNOTE_COUNTER = fn_counter_obj[0]
    if collected_footnotes and footnotes_accumulator is not None:
        footnotes_accumulator.extend(collected_footnotes)
            
    return '\n'.join(formatted_output), HTML_FOOTNOTE_COUNTER


def format_samam_nometa_html(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None, subsection_key=None,
                             footnote_counter=0, footnotes_accumulator=None, seen_content_map=None, with_modifiers=True, doc_markers_map=None):
    """
    Format only Samam content (header, mantra text) for HTML nometa output mode.
    Skips all Rik-related content and saman_metadata.
    """
    HTML_FOOTNOTE_COUNTER = footnote_counter
    formatted_output = []
    collected_footnotes = []
    footnote_data = subsection.get('footnotes', {})
    seen_markers_map = seen_content_map if seen_content_map is not None else {}
    
    # Clean titles
    display_sub_title = re.sub(r'^([|॥]+)\s*', r'\1 ', subsection_title) if subsection_title else ''

    # Header - ONLY subsection header, no metadata
    if display_sub_title:
        header_title = escape_for_html(display_sub_title)
        header_title = format_dandas_html(header_title)
        formatted_output.append(f'<div class="subsection-header"><span class="header-title">{header_title}</span></div>')

    # Mantra Content
    mantra_sets = subsection.get('corrected-mantra_sets', [])
    if not mantra_sets:
        mantra_sets = subsection.get('mantra_sets', [])

    mantra_array = []
    for mset in mantra_sets:
        m = mset.get('corrected-mantra') or mset.get('mantra', '')
        if m:
            mantra_array.append(m)
        elif mset.get('mantra-words'):
            words = []
            for word_dict in mset.get('mantra-words', []):
                w = word_dict.get('word', '')
                sw = word_dict.get('swara', '')
                if sw:
                    words.append(f"{w}({sw})")
                else:
                    words.append(w)
            if words:
                mantra_array.append(" ".join(words))

    fn_counter_obj = [HTML_FOOTNOTE_COUNTER]
    for mantra_line in mantra_array:
        clean_mantra = mantra_line.replace('\\newline%', ' ').replace('\\newline', ' ')
        clean_mantra = re.sub(r'[\u200b\u200c\ufeff\u2060\u180e\u00ad]', '', clean_mantra)
        clean_mantra = re.sub(r'\u200d(?=\()', '', clean_mantra)
        clean_mantra = re.sub(r'(\S)\s+\(', r'\1(', clean_mantra)
        
        verse_parts = re.split(r'(॥\s*[\d०-९]+\s*॥)', clean_mantra)
        
        for idx_v in range(0, len(verse_parts), 2):
            v_text = verse_parts[idx_v].strip()
            v_marker = verse_parts[idx_v + 1] if idx_v + 1 < len(verse_parts) else ''
            
            if not v_text and not v_marker:
                continue
                
            v_html = render_deva_html_from_line(
                v_text,
                with_modifiers=with_modifiers,
                footnote_data=footnote_data,
                seen_markers_map=seen_markers_map,
                subsection_key=subsection_key,
                footnote_counter_obj=fn_counter_obj,
                collected_footnotes=collected_footnotes,
                doc_markers_map=doc_markers_map
            )
            if v_marker:
                v_num_match = re.search(r'[\d०-९]+', v_marker)
                v_num = v_num_match.group(0) if v_num_match else ''
                v_html += f' <span class="mantra-word verse-num-word"><span class="mantra-text verse-num-marker"><span class="danda">॥</span><span class="verse-num">{v_num}</span><span class="danda">॥</span></span><span class="swara-text">&nbsp;</span></span>'
                
            formatted_output.append(f'<div class="mantra-verse">{v_html}</div>')

    HTML_FOOTNOTE_COUNTER = fn_counter_obj[0]
    if collected_footnotes and footnotes_accumulator is not None:
        footnotes_accumulator.extend(collected_footnotes)
            
    return '\n'.join(formatted_output), HTML_FOOTNOTE_COUNTER


def render_vedic_html_from_line(
    text: str,
    footnote_data: dict = None,
    seen_markers_map: dict = None,
    subsection_key: str = None,
    footnote_counter_obj: list = None,
    collected_footnotes: list = None,
    doc_markers_map: dict = None
) -> str:
    """Exact Python equivalent of renderVedicHTML from Curation Tool app.js.
    Renders stacked red swaras with <ruby> and blue modifiers with .swara-mod.
    """
    from malayalam.ml_transliterate import split_malayalam_syllables, devanagari_to_malayalam

    text = devanagari_to_malayalam(text)
    text = re.sub(r'[\u200b\u200c\ufeff\u2060\u180e\u00ad]', '', text)
    text = re.sub(r'\u200d(?=\()', '', text)
    text = re.sub(r'(\S)\s+\(', r'\1(', text)

    tokens = re.split(r'(\s+|[।॥])', text)
    html_parts = []
    chunk_re = re.compile(r'([^\s()_.,]+)?((?:\([^()]+\)|[_,.])*)')
    paren_re = re.compile(r'\(([^()]+)\)|(_|,|\.)')
    
    skip_next_space = False
    pending_danda_has_a1 = False
    for i in range(len(tokens)):
        token = tokens[i]
        if not token:
            continue
        m_fn = re.match(r'^\(s(\d+)\)$', token)
        if m_fn:
            marker = f"s{m_fn.group(1)}"
            fn_html = f'<sup>({marker})</sup>'
            if footnote_data and marker in footnote_data:
                footnote_text = footnote_data[marker].strip()
                if seen_markers_map is not None and footnote_text in seen_markers_map:
                    unique_id, dev_num = seen_markers_map[footnote_text]
                    fn_html = f'<sup class="footnote-ref"><a href="#{unique_id}">{dev_num}</a></sup>'
                else:
                    if footnote_counter_obj is not None:
                        footnote_counter_obj[0] += 1
                        cnt = footnote_counter_obj[0]
                    else:
                        cnt = 1
                    dev_num = to_devanagari_numeral(cnt)
                    safe_key = subsection_key if subsection_key else "unknown"
                    unique_id = f"fn-{safe_key}-{marker}"
                    fn_html = f'<sup class="footnote-ref"><a href="#{unique_id}" id="ref-{unique_id}">{dev_num}</a></sup>'
                    if collected_footnotes is not None:
                        collected_footnotes.append((unique_id, dev_num, footnote_text))
                    if seen_markers_map is not None:
                        seen_markers_map[footnote_text] = (unique_id, dev_num)
                        seen_markers_map[f"@marker:{marker}"] = (unique_id, dev_num)
                        seen_markers_map[marker] = (unique_id, dev_num)
                    if doc_markers_map is not None:
                        doc_markers_map[marker] = (unique_id, dev_num)
            elif seen_markers_map is not None and (f"@marker:{marker}" in seen_markers_map or marker in seen_markers_map):
                unique_id, dev_num = seen_markers_map.get(f"@marker:{marker}") or seen_markers_map.get(marker)
                fn_html = f'<sup class="footnote-ref"><a href="#{unique_id}">{dev_num}</a></sup>'
            elif doc_markers_map is not None and marker in doc_markers_map:
                unique_id, dev_num = doc_markers_map[marker]
                fn_html = f'<sup class="footnote-ref"><a href="#{unique_id}">{dev_num}</a></sup>'
            html_parts.append(fn_html)
            continue
        if token.isspace():
            if not skip_next_space:
                html_parts.append(' ')
            continue
        if token in ('।', '॥'):
            if pending_danda_has_a1:
                while html_parts and (html_parts[-1] == ' ' or html_parts[-1].isspace()):
                    html_parts.pop()
                html_parts.append(' ')
                arc_html = '<span class="swara-mod mod-a1" title="MOD-A1: Arc over Danda">&#xE00D;</span>'
                html_parts.append(f'<span class="danda danda-with-arc">{token}{arc_html}</span> ')
                skip_next_space = True
                pending_danda_has_a1 = False
                continue
            else:
                skip_next_space = False
            is_adjacent = skip_next_space
            adj_cls = ' danda-adjacent' if is_adjacent else ''
            html_parts.append(f'<span class="danda{adj_cls}">{token}</span>')
            continue
        
        # Look ahead: is the next non-whitespace token a danda?
        next_non_space = ''
        for j in range(i + 1, len(tokens)):
            if tokens[j] and not tokens[j].isspace():
                next_non_space = tokens[j]
                break
        next_is_danda = (next_non_space in ('।', '॥'))
        word_has_mod_a1_danda = False

        word_html = []
        for m in chunk_re.finditer(token):
            base = m.group(1) or ''
            extras = m.group(2) or ''
            if not base and not extras:
                continue
            
            swara_letter = ''
            modifiers_html = []
            has_mod_b = False
            has_mod_g = False
            
            for pm in paren_re.finditer(extras):
                inner = (pm.group(1) or pm.group(2) or '').strip()
                if inner in ('C', 'c', '·', 'ॱ', '़', '\uE001'):
                    modifiers_html.append('<span class="swara-mod mod-c" title="MOD-C: Upper Shoulder Dot">&#xE001;</span>')
                elif inner in ('H', 'h', 'L', 'l', '|', '│', '॑', 'ˈ', '\uE00C'):
                    modifiers_html.append('<span class="swara-mod mod-h" title="MOD-H: High Pitch Swarita">&#xE00C;</span>')
                elif inner in ('G', 'g', '\\', '╲', '⟍', '\uE003'):
                    has_mod_g = True
                elif inner in ('A1', 'a1', 'A_1', 'a_1', '\uE00D'):
                    if next_is_danda:
                        pending_danda_has_a1 = True
                        skip_next_space = True
                        word_has_mod_a1_danda = True
                    else:
                        modifiers_html.append('<span class="swara-mod mod-a1" title="MOD-A1: Arc over Danda">&#xE00D;</span>')
                elif inner in ('A', 'a', '╭╮', '⁀', '\uE004'):
                    if next_is_danda:
                        pending_danda_has_a1 = True
                        skip_next_space = True
                        word_has_mod_a1_danda = True
                    else:
                        modifiers_html.append('<span class="swara-mod mod-a" title="MOD-A: Melodic Arc (⁀)">&#xE004;</span>')
                elif inner in ('A2', 'a2', 'A_2', 'a_2', '\uE02E'):
                    modifiers_html.append('<span class="swara-mod mod-a2" title="MOD-A2: Overhead Conjunct Arc">&#xE02E;</span>')
                elif inner in ('D', 'd', '∧', 'Ʌ', '/\\', '\uE006'):
                    modifiers_html.append('<span class="swara-mod mod-d" title="MOD-D: Chevron Roof (∧)">&#xE006;</span>')
                elif inner in ('D1', 'd1', 'D_1', 'd_1', '↗', '\uE00E'):
                    modifiers_html.append('<span class="swara-mod mod-d1" title="MOD-D1: Rising Stroke (↗)">&#xE00E;</span>')
                elif inner in ('D2', 'd2', 'D_2', 'd_2', '✓', '\uE00F'):
                    modifiers_html.append('<span class="swara-mod mod-d2" title="MOD-D2: Check Tick (✓)">&#xE00F;</span>')
                elif inner in ('I', 'i', '⫽', '\uE02A'):
                    modifiers_html.append('<span class="swara-mod mod-i" title="MOD-I: Double Shoulder Dash (⫽)">&#xE02A;</span>')
                elif inner in ('J', 'j', '¯', '\uE02B'):
                    modifiers_html.append('<span class="swara-mod mod-j" title="MOD-J: Overhead Horizontal Bar (¯)">&#xE02B;</span>')
                elif inner in ('B1', 'b1', 'B_1', 'b_1', '/', '\uE02C'):
                    modifiers_html.append('<span class="swara-mod mod-b1" title="MOD-B1: Diagonal Bridging Slash (/)">&#xE02C;</span>')
                elif inner in ('K', 'k', '⨯', 'x', 'X', '\uE02D'):
                    modifiers_html.append('<span class="swara-mod mod-k" title="MOD-K: Shoulder Cross Mark (⨯)">&#xE02D;</span>')
                elif inner in ('B', 'b', '^', '˄', '/\\', '\uE005'):
                    has_mod_b = True
                elif inner in ('E', 'e', '┃', '\uE002'):
                    modifiers_html.append('<span class="swara-mod mod-e" title="MOD-E: Bold Tone Column (┃)">&#xE002;</span>')
                elif inner in ('F', 'f', '╷', '\uE008'):
                    modifiers_html.append('<span class="swara-mod mod-f" title="MOD-F: Danda with Overhead Dot (╷)">&#xE008;</span>')
                elif inner == '_':
                    modifiers_html.append('<span class="swara-mod mod-under" title="MOD-UNDERBAR">_</span>')
                elif inner == ',':
                    modifiers_html.append('<span class="swara-mod mod-comma" title="MOD-COMMA">,</span>')
                elif inner == '.':
                    modifiers_html.append('<span class="swara-mod mod-dot" title="MOD-DOT">.</span>')
                elif re.match(r'^s\d+$', inner):
                    marker = inner
                    fn_html = f'<sup>({marker})</sup>'
                    if footnote_data and marker in footnote_data:
                        footnote_text = footnote_data[marker].strip()
                        if seen_markers_map is not None and footnote_text in seen_markers_map:
                            unique_id, dev_num = seen_markers_map[footnote_text]
                            fn_html = f'<sup class="footnote-ref"><a href="#{unique_id}">{dev_num}</a></sup>'
                        else:
                            if footnote_counter_obj is not None:
                                footnote_counter_obj[0] += 1
                                cnt = footnote_counter_obj[0]
                            else:
                                cnt = 1
                            dev_num = to_devanagari_numeral(cnt)
                            safe_key = subsection_key if subsection_key else "unknown"
                            unique_id = f"fn-{safe_key}-{marker}"
                            fn_html = f'<sup class="footnote-ref"><a href="#{unique_id}" id="ref-{unique_id}">{dev_num}</a></sup>'
                            if collected_footnotes is not None:
                                collected_footnotes.append((unique_id, dev_num, footnote_text))
                            if seen_markers_map is not None:
                                seen_markers_map[footnote_text] = (unique_id, dev_num)
                                seen_markers_map[f"@marker:{marker}"] = (unique_id, dev_num)
                                seen_markers_map[marker] = (unique_id, dev_num)
                            if doc_markers_map is not None:
                                doc_markers_map[marker] = (unique_id, dev_num)
                    elif seen_markers_map is not None and (f"@marker:{marker}" in seen_markers_map or marker in seen_markers_map):
                        unique_id, dev_num = seen_markers_map.get(f"@marker:{marker}") or seen_markers_map.get(marker)
                        fn_html = f'<sup class="footnote-ref"><a href="#{unique_id}">{dev_num}</a></sup>'
                    elif doc_markers_map is not None and marker in doc_markers_map:
                        unique_id, dev_num = doc_markers_map[marker]
                        fn_html = f'<sup class="footnote-ref"><a href="#{unique_id}">{dev_num}</a></sup>'
                    modifiers_html.append(fn_html)
                else:
                    from malayalam.ml_map import marker_to_grantha
                    g_swara = marker_to_grantha(inner)
                    swara_letter = SWARA_CANONICAL_MAP.get(g_swara, g_swara)
            
            mods_str = ''.join(modifiers_html)
            syllables = split_malayalam_syllables(base) if base else []
            last_syl = syllables.pop() if syllables else ''
            
            for syl in syllables:
                word_html.append(f'<span class="akshara-base">{syl}</span>')
            
            if has_mod_g and last_syl:
                syl_core = f'<span class="syl-mod-g-wrap">{last_syl}<span class="swara-mod mod-g" title="MOD-G: Lower Under-Slash (\\)">&#xE003;</span></span>'
            elif has_mod_g and not last_syl:
                syl_core = '<span class="swara-mod mod-g" title="MOD-G: Lower Under-Slash (\\)">&#xE003;</span>'
            else:
                syl_core = last_syl

            if has_mod_b:
                caret_group = f'<span class="swara-mod mod-b"><span class="caret-glyph">&#xE005;</span><span class="swara-on-caret">{swara_letter}</span></span>'
                word_html.append(f'<span class="akshara-base">{syl_core}{mods_str}{caret_group}</span>')
            elif swara_letter and last_syl:
                word_html.append(f'<ruby class="vedic-ruby"><rb class="akshara-base">{syl_core}{mods_str}</rb><rt class="swara-above">{swara_letter}</rt></ruby>')
            elif swara_letter and not last_syl:
                word_html.append(f'<ruby class="vedic-ruby"><rb class="akshara-base">&nbsp;{syl_core}{mods_str}</rb><rt class="swara-above">{swara_letter}</rt></ruby>')
            elif syl_core or mods_str:
                word_html.append(f'<span class="akshara-base">{syl_core}{mods_str}</span>')
        
        html_parts.append(f'<span class="mantra-word">{"".join(word_html) or token}</span>')
        if not word_has_mod_a1_danda:
            skip_next_space = False
    
    return ''.join(html_parts)


def format_malayalam_samam_html(subsection, subsection_title, include_metadata=True,
                                 footnote_counter=0, footnotes_accumulator=None, seen_content_map=None, subsection_key=None, doc_markers_map=None):
    """
    Format Malayalam Samam content as semantic HTML with clean Grantha swara stacking,
    identically matching the visual output of the Curation Tool.
    """
    formatted_output = []
    collected_footnotes = []
    seen_markers_map = seen_content_map if seen_content_map is not None else {}
    footnote_data = subsection.get('footnotes', {})
    
    # 1. Header
    display_sub_title = re.sub(r'^([|॥]+)\s*', r'\1 ', subsection_title) if subsection_title else ''
    saman_metadata = subsection.get('saman_metadata', '') if include_metadata else ''
    
    header_parts = []
    if display_sub_title:
        header_title = escape_for_html(display_sub_title)
        header_title = format_dandas_html(header_title)
        header_parts.append(f'<span class="header-title">{header_title}</span>')
    if saman_metadata:
        meta = escape_for_html(saman_metadata)
        meta = format_dandas_html(meta, preserve_spaces=True)
        meta, fnotes, footnote_counter = process_footnotes_html(meta, footnote_data, footnote_counter, seen_markers_map, subsection_key, doc_markers_map=doc_markers_map)
        collected_footnotes.extend(fnotes)
        header_parts.append(f'<span class="header-meta">{meta}</span>')
        
    if header_parts:
        formatted_output.append(f'<div class="subsection-header">{" &nbsp; ".join(header_parts)}</div>')
        
    # 2. Mantra verses
    mantra_array = []
    mantra_sets = subsection.get('malayalam-mantra-sets', [])
    if not mantra_sets:
        mantra_sets = subsection.get('corrected-mantra_sets', [])
    if not mantra_sets:
        mantra_sets = subsection.get('mantra_sets', [])

    for mset in mantra_sets:
        m = mset.get('malayalam-mantra') or mset.get('corrected-mantra') or mset.get('mantra', '')
        if m:
            mantra_array.append(m)
        elif mset.get('mantra-words'):
            words = []
            for word_dict in mset.get('mantra-words', []):
                w = word_dict.get('word', '')
                sw = word_dict.get('swara', '')
                if sw:
                    words.append(f"{w}({sw})")
                else:
                    words.append(w)
            if words:
                mantra_array.append(" ".join(words))

    fn_counter_obj = [footnote_counter]
    for mantra_line in mantra_array:
        clean_mantra = mantra_line.replace('\\newline%', ' ').replace('\\newline', ' ').replace('ർ', 'ൎ').replace('ര്', 'ൎ').replace('൪', 'ൎ')
        clean_mantra = re.sub(r'[\u200b\u200c\ufeff\u2060\u180e\u00ad]', '', clean_mantra)
        clean_mantra = re.sub(r'\u200d(?=\()', '', clean_mantra)
        clean_mantra = re.sub(r'(\S)\s+\(', r'\1(', clean_mantra)
        
        verse_parts = re.split(r'(॥\s*[\d०-९]+\s*॥)', clean_mantra)
        
        for idx_v in range(0, len(verse_parts), 2):
            v_text = verse_parts[idx_v].strip()
            v_marker = verse_parts[idx_v + 1] if idx_v + 1 < len(verse_parts) else ''
            
            if not v_text and not v_marker:
                continue
                
            v_html = render_vedic_html_from_line(
                v_text,
                footnote_data=footnote_data,
                seen_markers_map=seen_markers_map,
                subsection_key=subsection_key,
                footnote_counter_obj=fn_counter_obj,
                collected_footnotes=collected_footnotes,
                doc_markers_map=doc_markers_map
            )
            if v_marker:
                num_m = re.search(r'[\d०-९]+', v_marker)
                v_num = num_m.group(0).translate(_ENGLISH_DIGITS) if num_m else ''
                v_marker_html = f'<span class="mantra-word verse-num-word"><span class="mantra-text verse-num-marker"><span class="danda">॥</span><span class="verse-num">{v_num}</span><span class="danda">॥</span></span><span class="swara-text">&nbsp;</span></span>'
                formatted_output.append(f'<div class="mantra-verse">{v_html} {v_marker_html}</div>')
            elif v_html:
                formatted_output.append(f'<div class="mantra-verse">{v_html}</div>')

    footnote_counter = fn_counter_obj[0]
    if collected_footnotes and footnotes_accumulator is not None:
        footnotes_accumulator.extend(collected_footnotes)

    return '\n'.join(formatted_output), footnote_counter

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


def register_html_filters(env):
    """Registers all HTML reader rendering filters onto the provided Jinja2 environment."""
    env.filters["format_mantra_sets_html"] = format_mantra_sets_html
    env.filters["format_rik_only_html"] = format_rik_only_html
    env.filters["format_samam_only_html"] = format_samam_only_html
    env.filters["format_rik_nometa_html"] = format_rik_nometa_html
    env.filters["format_samam_nometa_html"] = format_samam_nometa_html
    env.filters["format_malayalam_samam_html"] = format_malayalam_samam_html
    env.filters["escape_for_html"] = escape_for_html
    env.filters["replacecolon"] = replacecolon
    env.filters["reset_html_footnote_counter"] = reset_html_footnote_counter
    env.filters["render_section_footnotes"] = render_section_footnotes
    env.filters["clean_toc_title"] = clean_toc_title
    env.filters["toc_header"] = toc_header
    return env
