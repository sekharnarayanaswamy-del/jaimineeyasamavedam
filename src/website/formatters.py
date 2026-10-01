"""
Vedic and Chanting Text Formatters for HTML Rendering
Provides alignment, accent placement, swara modifier markup, and footnote handling
conforming to the standalone HTML viewer architecture.
"""

import re
import html
from typing import Dict, List, Tuple, Any
from .constants import MALAYALAM_MODIFIER_MAP, MALAYALAM_SWARA_SUBS, HTML_MOD_MAP

try:
    from utils import (
        combine_ardhaksharas,
        step_preprocess_visarga_accent
    )
except ImportError:
    try:
        from src.utils import combine_ardhaksharas, step_preprocess_visarga_accent
    except ImportError:
        def combine_ardhaksharas(s): return list(s)
        def step_preprocess_visarga_accent(s): return s

try:
    from render_pdf import (
        replace_accents_html,
        format_dandas_html,
        escape_for_html,
        remove_mantra_spaces,
        handle_consecutive_trikamba_html,
        process_footnotes_html
    )
    HAS_RENDER_IMPORTS = True
except ImportError:
    try:
        from src.render_pdf import (
            replace_accents_html,
            format_dandas_html,
            escape_for_html,
            remove_mantra_spaces,
            handle_consecutive_trikamba_html,
            process_footnotes_html
        )
        HAS_RENDER_IMPORTS = True
    except ImportError:
        HAS_RENDER_IMPORTS = False

try:
    from renderers.filters.html_filters import (
        render_deva_html_from_line,
        render_vedic_html_from_line,
        render_mod_html,
        format_deva_syl_html
    )
    HAS_STANDALONE_HTML_FILTERS = True
except ImportError:
    try:
        from src.renderers.filters.html_filters import (
            render_deva_html_from_line,
            render_vedic_html_from_line,
            render_mod_html,
            format_deva_syl_html
        )
        HAS_STANDALONE_HTML_FILTERS = True
    except ImportError:
        HAS_STANDALONE_HTML_FILTERS = False


# --- Local fallback functions ---
def local_escape_for_html(text: str) -> str:
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


def local_replace_accents_html(text: str) -> str:
    """
    Replaces ASCII accent markers with Unicode Vedic accent characters for HTML.
    Fixes dotted circle issue across all fonts by keeping Visarga contiguous to the syllable.
    """
    if not text:
        return text

    # Step 1: Reorder any accent marker that precedes a Visarga so syllable + ः remain contiguous
    text = re.sub(r'(\([1-4]\))\s*([ः:])', r'ः\1', text)
    text = re.sub(r'([\u0951\u1CD2\u1CF8\u1CF9])\s*([ः:])', r'ः\1', text)
    text = re.sub(r'(<span class="accent-[^"]+">[^<]+</span>)\s*([ः:])', r'ः\1', text)

    # Step 2: Accents following Visarga receive .accent-visarga to shift backwards over the syllable
    visarga_replacements = [
        ('ः(1)', 'ः<span class="accent-swarita accent-visarga">\u0951</span>'),
        ('ः(2)', 'ः<span class="accent-anudatta accent-visarga">\u1CD2</span>'),
        ('ः(3)', 'ः<span class="accent-kampa accent-visarga">\u1CF8</span>'),
        ('ः(4)', 'ः<span class="accent-trikampa accent-visarga">\u1CF9</span>'),
        ('ः\u0951', 'ः<span class="accent-swarita accent-visarga">\u0951</span>'),
        ('ः\u1CD2', 'ः<span class="accent-anudatta accent-visarga">\u1CD2</span>'),
        ('ः\u1CF8', 'ः<span class="accent-kampa accent-visarga">\u1CF8</span>'),
        ('ः\u1CF9', 'ः<span class="accent-trikampa accent-visarga">\u1CF9</span>'),
    ]
    for marker, replacement in visarga_replacements:
        text = text.replace(marker, replacement)

    # Step 3: Standard accents (on syllables without Visarga)
    replacements = [
        ('(1)', '<span class="accent-swarita">\u0951</span>'),
        ('(2)', '<span class="accent-anudatta">\u1CD2</span>'),
        ('(3)', '<span class="accent-kampa">\u1CF8</span>'),
        ('(4)', '<span class="accent-trikampa">\u1CF9</span>'),
        ('\u0951', '<span class="accent-swarita">\u0951</span>'),
        ('\u1CD2', '<span class="accent-anudatta">\u1CD2</span>'),
        ('\u1CF8', '<span class="accent-kampa">\u1CF8</span>'),
        ('\u1CF9', '<span class="accent-trikampa">\u1CF9</span>'),
    ]
    for marker, replacement in replacements:
        text = text.replace(marker, replacement)
    return text


def local_process_footnotes_html(text: str, footnotes_dict=None, counter_obj=None, seen_map=None, accumulator=None) -> Tuple[str, List]:
    """
    Process footnotes with global accumulation support.
    """
    if not text:
        return text, []
    
    if footnotes_dict is None:
        footnotes_dict = {}
        
    if counter_obj is None: counter_obj = {'val': 0}
    if seen_map is None: seen_map = {}
    if accumulator is None: accumulator = []
    
    collected_footnotes = []
    devanagari_digits = '०१२३४५६७८९'
    
    def replacer(match):
        marker_num = match.group(1)
        marker_key = f's{marker_num}'
        footnote_text = footnotes_dict.get(marker_key, '').strip()
        
        if footnote_text and footnote_text in seen_map:
            unique_id, display_num = seen_map[footnote_text]
        else:
            counter_obj['val'] += 1
            val = counter_obj['val']
            unique_id = f'fn-kandah-{val}'
            display_num = ''.join(devanagari_digits[int(d)] for d in str(val))
            
            if footnote_text:
                seen_map[footnote_text] = (unique_id, display_num)
                accumulator.append((unique_id, display_num, footnote_text))
                collected_footnotes.append((unique_id, val, footnote_text))
        
        return f'<sup class="footnote-ref"><a href="#{unique_id}">{display_num}</a></sup>'
    
    pattern = r'\(s(\d+)\)'
    processed_text = re.sub(pattern, replacer, text)
    return processed_text, collected_footnotes


def local_format_dandas_html(text: str) -> str:
    """Formats danda symbols for HTML output."""
    if not text or not isinstance(text, str):
        return text

    text = re.sub(r'\|\|', '॥', text)
    text = re.sub(r'\|\s*\|', '॥', text)
    text = re.sub(r'।।', '॥', text)
    text = text.replace('|', '।')

    danda_pattern = r'(?:\|\||॥)'
    digits = r'[\d०-९]+'
    pattern = rf'({danda_pattern})\s*({digits})\s*({danda_pattern})'
    text = re.sub(pattern, r'<span class="mantra-number">\1 \2 \3</span>', text)

    text = text.replace('॥', ' <span class="danda">॥</span> ')
    text = text.replace('।', ' <span class="danda">।</span> ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def local_remove_mantra_spaces(text: str) -> str:
    """Removes all spaces within the text to create continuous Samhita text."""
    if not text:
        return text
    text = re.sub(r'\s+', '', text)
    text = text.replace('\u00A0', '')
    text = text.replace('\u200B', '')
    text = text.replace('\u200C', '')
    text = text.replace('\u200D', '')
    return text


def local_handle_consecutive_trikamba(text: str) -> str:
    """Insert thin space between consecutive trikamba accent marks."""
    if not text:
        return text
    pattern = r'\(4\)([^\(\)]{1,3})\(4\)'
    replacement = r'(4)\1 (4)'
    return re.sub(pattern, replacement, text)


if HAS_RENDER_IMPORTS:
    _escape_html = escape_for_html
    _replace_accents = replace_accents_html
    _format_dandas = format_dandas_html
    _remove_spaces = remove_mantra_spaces
    _handle_trikamba = handle_consecutive_trikamba_html
else:
    _escape_html = local_escape_for_html
    _replace_accents = local_replace_accents_html
    _format_dandas = local_format_dandas_html
    _remove_spaces = local_remove_mantra_spaces
    _handle_trikamba = local_handle_consecutive_trikamba


def split_rik_lines_html(text: str) -> str:
    """
    Splits multi-Rik text so each Rik appears on its own line in HTML.
    Splits after each verse marker (॥ N ॥) and joins with <br>.
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
    return '<br>'.join(lines)


def _fix_visarga_accent_with_zwj(text: str) -> str:
    """Swaps Visarga and accent marker so accent applies to preceding vowel."""
    if not text:
        return text
    text = text.replace(':', 'ः')
    text = re.sub(r'\s+ः', 'ः', text)
    pattern = r'([ः])\s*(\([^)]+\))'
    text = re.sub(pattern, r'\2\1', text)
    return text


def format_rik_text_html(rik_text: str, footnotes_dict=None, counter_obj=None, seen_map=None, accumulator=None) -> Tuple[str, List]:
    """
    Format Rik text for HTML display with proper accent marks.
    Removes spaces (Samhita mode) and converts accent markers to Unicode.
    Also processes footnote markers via accumulator logic.
    Returns: (formatted_text, collected_footnotes)
    """
    if not rik_text:
        return "", []
    
    text = _remove_spaces(rik_text)
    text = _handle_trikamba(text)
    text = _escape_html(text)
    text, collected_footnotes = local_process_footnotes_html(text, footnotes_dict, counter_obj, seen_map, accumulator)
    text = _replace_accents(text)
    text = split_rik_lines_html(text)
    text = _format_dandas(text)
    return text, collected_footnotes


def split_malayalam_clusters(word: str) -> List[str]:
    """Splits a Malayalam word into constituent grapheme clusters."""
    try:
        from malayalam.ml_transliterate import split_malayalam_syllables
        return split_malayalam_syllables(word)
    except Exception:
        pattern = r'(?:[\u0D05-\u0D14]|(?:[\u0D15-\u0D3A\u0D7A-\u0D7F](?:\u0D4D[\u0D15-\u0D3A])*[\u0D3E-\u0D4D\u0D57\u0D62\u0D63]?[\u0D02\u0D03]?))'
        clusters = re.findall(pattern, word)
        if not clusters or ''.join(clusters) != word:
            return [word]
        return clusters


def format_malayalam_mantra_html(mantra_text: str, footnotes_dict=None, counter_obj=None, seen_map=None, accumulator=None) -> Tuple[str, List]:
    """
    Formats Malayalam Samam text using the standalone HTML viewer / curation tool
    ruby-based swara stacking architecture with swara modifiers.
    """
    if not mantra_text:
        return "", []
    if footnotes_dict is None: footnotes_dict = {}
    if counter_obj is None: counter_obj = {'val': 0}
    if seen_map is None: seen_map = {}
    if accumulator is None: accumulator = []

    if HAS_STANDALONE_HTML_FILTERS:
        fn_counter_obj = [counter_obj.get('val', 0)]
        collected_fnotes = []
        
        # Split into verse units
        clean_mantra = mantra_text.replace('\\newline%', ' ').replace('\\newline', ' ').replace('ർ', 'ൎ').replace('ര്', 'ൎ').replace('൪', 'ൎ')
        clean_mantra = re.sub(r'[\u200b\u200c\ufeff\u2060\u180e\u00ad]', '', clean_mantra)
        clean_mantra = re.sub(r'\u200d(?=\()', '', clean_mantra)
        clean_mantra = re.sub(r'(\S)\s+\(', r'\1(', clean_mantra)
        
        verse_parts = re.split(r'(॥\s*[\d०-९]+\s*॥)', clean_mantra)
        formatted_verses = []
        
        for idx_v in range(0, len(verse_parts), 2):
            v_text = verse_parts[idx_v].strip()
            v_marker = verse_parts[idx_v + 1] if idx_v + 1 < len(verse_parts) else ''
            
            if not v_text and not v_marker:
                continue
                
            v_html = render_vedic_html_from_line(
                v_text,
                footnote_data=footnotes_dict,
                seen_markers_map=seen_map,
                footnote_counter_obj=fn_counter_obj,
                collected_footnotes=collected_fnotes
            )
            if v_marker:
                num_m = re.search(r'[\d०-९]+', v_marker)
                v_num = num_m.group(0) if num_m else ''
                v_marker_html = f'<span class="mantra-word verse-num-word"><span class="mantra-text verse-num-marker"><span class="danda">॥</span><span class="verse-num">{v_num}</span><span class="danda">॥</span></span><span class="swara-text">&nbsp;</span></span>'
                formatted_verses.append(f'<div class="mantra-verse">{v_html} {v_marker_html}</div>')
            elif v_html:
                formatted_verses.append(f'<div class="mantra-verse">{v_html}</div>')

        counter_obj['val'] = fn_counter_obj[0]
        if collected_fnotes and accumulator is not None:
            accumulator.extend(collected_fnotes)
        return '\n'.join(formatted_verses), collected_fnotes

    # Fallback to local parsing if html_filters is unavailable
    devanagari_digits = '०१२३४५६७८९'
    html_parts = []
    collected_footnotes = []

    text = mantra_text.replace('\n', ' ').strip()
    text = re.sub(r'(\S)\s+\(', r'\1(', text)
    text = re.sub(r'\|\|', '॥', text)
    text = re.sub(r'\|\s*\|', '॥', text)
    text = re.sub(r'।।', '॥', text)
    text = text.replace('|', '।')

    token_re = re.compile(
        r'(\s+)|'
        r'(\|\||॥|\||।)|'
        r'(\(s\d+\))|'
        r'([^\s\|।॥()]+(?:\([^)]+\))*|\([^)]+\))'
    )

    matches = list(token_re.finditer(text))
    skip_next_space = False
    pending_danda_has_a1 = False

    for idx_m in range(len(matches)):
        m = matches[idx_m]
        space, danda, fn, word_match = m.groups()
        if space:
            if not skip_next_space:
                html_parts.append('<span class="word-space">&nbsp;</span>')
            continue
        elif danda:
            if pending_danda_has_a1:
                while html_parts and (html_parts[-1] == ' ' or html_parts[-1].isspace() or 'word-space' in html_parts[-1]):
                    html_parts.pop()
                html_parts.append('<span class="word-space">&nbsp;</span>')
                arc_html = '<span class="swara-mod mod-a1" title="MOD-A1: Arc over Danda">&#xE00D;</span>'
                html_parts.append(f'<span class="danda danda-with-arc">{danda}{arc_html}</span><span class="word-space">&nbsp;</span>')
                skip_next_space = True
                pending_danda_has_a1 = False
                continue
            m_num = re.match(r'॥\s*([\d०-९]+)\s*॥', danda)
            if m_num:
                html_parts.append(f'<span class="danda">॥</span><span class="mantra-word"><span class="swara-text">&nbsp;</span><span class="mantra-text"><span class="mantra-number">{m_num.group(1)}</span></span></span><span class="danda">॥</span><div class="mantra-break"></div>')
                skip_next_space = False
            else:
                is_adjacent = skip_next_space
                adj_cls = ' danda-adjacent' if is_adjacent else ''
                html_parts.append(f'<span class="danda{adj_cls}">{danda}</span>')
                skip_next_space = False
            continue
        elif fn:
            marker_key = fn.strip('()')
            footnote_text = footnotes_dict.get(marker_key, '').strip()
            if footnote_text and footnote_text in seen_map:
                unique_id, display_num = seen_map[footnote_text]
            else:
                counter_obj['val'] += 1
                val = counter_obj['val']
                unique_id = f'fn-kandah-{val}'
                display_num = ''.join(devanagari_digits[int(d)] for d in str(val))
                if footnote_text:
                    seen_map[footnote_text] = (unique_id, display_num)
                    accumulator.append((unique_id, display_num, footnote_text))
                    collected_footnotes.append((unique_id, val, footnote_text))
            html_parts.append(f'<sup class="footnote-ref"><a href="#{unique_id}">{display_num}</a></sup>')
            continue
        elif word_match:
            tok = word_match.strip()
            if not tok:
                continue

            m_num = re.match(r'॥\s*([\d०-९]+)\s*॥', tok)
            if m_num:
                html_parts.append(f'<span class="danda">॥</span><span class="mantra-word"><span class="swara-text">&nbsp;</span><span class="mantra-text"><span class="mantra-number">{m_num.group(1)}</span></span></span><span class="danda">॥</span><div class="mantra-break"></div>')
                continue

            if tok in ('_', '._', '_.'):
                html_parts.append(f'<span class="mantra-punct">{tok}</span>')
                continue
            elif tok == '.':
                html_parts.append('<span class="mantra-punct">.</span>')
                continue
            elif tok == ',':
                html_parts.append('<span class="mantra-punct">,</span>')
                continue

            base = re.sub(r'\([^)]+\)', '', tok).strip()
            parens = re.findall(r'\(([^)]+)\)', tok)

            swara_val = ''
            mods = []
            fn_marker = None
            has_mod_a1 = False
            for p in parens:
                if p in ('A1', 'a1', 'A_1', 'a_1'):
                    mods.append(('mod-a1', '&#xE00D;'))
                elif p in ('A', 'a', '⁀'):
                    mods.append(('mod-a', '&#xE004;'))
                elif p in MALAYALAM_MODIFIER_MAP:
                    mods.append(MALAYALAM_MODIFIER_MAP[p])
                elif re.match(r's\d+', p):
                    fn_marker = p
                else:
                    swara_val = MALAYALAM_SWARA_SUBS.get(p, p)

            core_word = base.rstrip("_,.")
            trailing_punct = base[len(core_word):]
            if not core_word:
                core_word = base if base else '&nbsp;'

            syllables = split_malayalam_clusters(core_word) if core_word != '&nbsp;' else ['&nbsp;']

            mod_html = ''
            has_mod_g = False
            for m_cls, m_glyph in mods:
                if m_cls == 'mod-g':
                    has_mod_g = True
                elif m_cls == 'mod-b':
                    mod_html += f'<span class="swara-mod mod-b"><span class="caret-glyph">&#xE005;</span><span class="swara-on-caret">{swara_val or "&nbsp;"}</span></span>'
                    swara_val = ''
                elif m_cls == 'mod-c':
                    mod_html += '<span class="swara-mod mod-c">&#xE001;</span>'
                elif m_cls == 'mod-h':
                    mod_html += '<span class="swara-mod mod-h">&#xE00C;</span>'
                elif m_cls == 'mod-e':
                    mod_html += '<span class="swara-mod mod-e">&#xE002;</span>'
                elif m_cls == 'mod-f':
                    mod_html += '<span class="swara-mod mod-f">&#x2577;</span>'
                else:
                    mod_html += f'<span class="swara-mod {m_cls}">{m_glyph}</span>'

            fn_html = ''
            if fn_marker:
                footnote_text = footnotes_dict.get(fn_marker, '').strip()
                if footnote_text and footnote_text in seen_map:
                    unique_id, display_num = seen_map[footnote_text]
                else:
                    counter_obj['val'] += 1
                    val = counter_obj['val']
                    unique_id = f'fn-kandah-{val}'
                    display_num = ''.join(devanagari_digits[int(d)] for d in str(val))
                    if footnote_text:
                        seen_map[footnote_text] = (unique_id, display_num)
                        accumulator.append((unique_id, display_num, footnote_text))
                        collected_footnotes.append((unique_id, val, footnote_text))
                fn_html = f'<sup class="footnote-ref"><a href="#{unique_id}">{display_num}</a></sup>'

            for idx, syl in enumerate(syllables):
                if idx == len(syllables) - 1:
                    sw_disp = swara_val if swara_val else '&nbsp;'
                    syl_core = f'<span class="syl-mod-g-wrap">{syl}<span class="swara-mod mod-g">&#xE003;</span></span>' if (has_mod_g and syl != '&nbsp;') else syl
                    html_parts.append(f'<span class="mantra-word"><span class="swara-text">{sw_disp}</span><span class="mantra-text">{syl_core}{mod_html}</span></span>{fn_html}')
                else:
                    html_parts.append(f'<span class="mantra-word"><span class="swara-text">&nbsp;</span><span class="mantra-text">{syl}</span></span>')

            if trailing_punct:
                html_parts.append(f'<span class="mantra-punct">{trailing_punct}</span>')

    return ''.join(html_parts), collected_footnotes


def format_mantra_text_html(mantra_text: str, footnotes_dict=None, counter_obj=None, seen_map=None, accumulator=None) -> Tuple[str, List]:
    """
    Format Sama mantra text for HTML display with stacked word/swara layout and swara modifiers.
    Uses the standalone HTML viewer rendering pipeline (`render_deva_html_from_line`)
    with full support for swara modifiers (A, A1, A2, B, B1, C, D, D1, D2, E, F, G, H, I, J, K, etc.).
    """
    if not mantra_text:
        return "", []

    # Detect Malayalam / Grantha content
    if re.search(r'[\u0D00-\u0D7F\U00011300-\U0001137F]', mantra_text):
        return format_malayalam_mantra_html(mantra_text, footnotes_dict, counter_obj, seen_map, accumulator)

    mantra_text = step_preprocess_visarga_accent(mantra_text)

    if footnotes_dict is None: footnotes_dict = {}
    if counter_obj is None: counter_obj = {'val': 0}
    if seen_map is None: seen_map = {}
    if accumulator is None: accumulator = []

    if HAS_STANDALONE_HTML_FILTERS:
        fn_counter_obj = [counter_obj.get('val', 0)]
        collected_fnotes = []
        
        clean_mantra = mantra_text.replace('\\newline%', ' ').replace('\\newline', ' ')
        clean_mantra = re.sub(r'[\u200b\u200c\ufeff\u2060\u180e\u00ad]', '', clean_mantra)
        clean_mantra = re.sub(r'\u200d(?=\()', '', clean_mantra)
        clean_mantra = re.sub(r'(\S)\s+\(', r'\1(', clean_mantra)
        
        verse_parts = re.split(r'(॥\s*[\d०-९]+\s*॥)', clean_mantra)
        formatted_verses = []
        
        for idx_v in range(0, len(verse_parts), 2):
            v_text = verse_parts[idx_v].strip()
            v_marker = verse_parts[idx_v + 1] if idx_v + 1 < len(verse_parts) else ''
            
            if not v_text and not v_marker:
                continue
                
            v_html = render_deva_html_from_line(
                v_text,
                with_modifiers=True,
                footnote_data=footnotes_dict,
                seen_markers_map=seen_map,
                footnote_counter_obj=fn_counter_obj,
                collected_footnotes=collected_fnotes
            )
            if v_marker:
                v_num_match = re.search(r'[\d०-९]+', v_marker)
                v_num = v_num_match.group(0) if v_num_match else ''
                v_marker_html = f'<span class="mantra-word verse-num-word"><span class="mantra-text verse-num-marker"><span class="danda">॥</span><span class="verse-num">{v_num}</span><span class="danda">॥</span></span><span class="swara-text">&nbsp;</span></span>'
                formatted_verses.append(f'{v_html} {v_marker_html}<div class="mantra-break"></div>')
            elif v_html:
                formatted_verses.append(v_html)

        counter_obj['val'] = fn_counter_obj[0]
        if collected_fnotes and accumulator is not None:
            accumulator.extend(collected_fnotes)
        return ' '.join(formatted_verses), collected_fnotes

    # Fallback to local parsing if html_filters is not available
    devanagari_digits = '०१२३४५६७८९'
    html_parts = []
    collected_footnotes = []

    text = mantra_text.replace('\n', ' ').replace('\r', '').strip()
    text = re.sub(r'(\S)\s+\(', r'\1(', text)
    text = re.sub(r'\|\|', '॥', text)
    text = re.sub(r'\|\s*\|', '॥', text)
    text = re.sub(r'।।', '॥', text)
    text = text.replace('|', '।')

    i = 0
    while i < len(text):
        if text[i].isspace() or text[i] in '\u200c\u200d\ufeff':
            i += 1
            continue

        if text[i] in '।॥|':
            number_match = re.match(r'॥\s*(\d+)\s*॥', text[i:])
            if number_match:
                num = number_match.group(1)
                html_parts.append(
                    f'<span class="mantra-word">'
                    f'<span class="mantra-text"><span class="mantra-number">॥ {num} ॥</span></span>'
                    f'<span class="swara-text">&nbsp;</span>'
                    f'</span>'
                    f'<div class="mantra-break"></div>'
                )
                i += len(number_match.group(0))
            else:
                danda = text[i]
                html_parts.append(
                    f'<span class="mantra-word">'
                    f'<span class="mantra-text"><span class="danda">{danda}</span></span>'
                    f'<span class="swara-text">&nbsp;</span>'
                    f'</span>'
                )
                i += 1
            continue

        footnote_match = re.match(r'\(s(\d+)\)', text[i:])
        if footnote_match:
            marker_num = footnote_match.group(1)
            marker_key = f's{marker_num}'
            footnote_text = footnotes_dict.get(marker_key, '').strip()

            if footnote_text and footnote_text in seen_map:
                unique_id, display_num = seen_map[footnote_text]
            else:
                counter_obj['val'] += 1
                val = counter_obj['val']
                unique_id = f'fn-kandah-{val}'
                display_num = ''.join(devanagari_digits[int(d)] for d in str(val))
                if footnote_text:
                    seen_map[footnote_text] = (unique_id, display_num)
                    accumulator.append((unique_id, display_num, footnote_text))
                    collected_footnotes.append((unique_id, val, footnote_text))

            html_parts.append(f'<sup class="footnote-ref"><a href="#{unique_id}">{display_num}</a></sup>')
            i += len(footnote_match.group(0))
            continue

        match = re.match(r'([^\s()।॥]+)\s*\(([^)]+)\)\s*([:ः]?)', text[i:])
        if match:
            word = match.group(1)
            swara = match.group(2)
            trailing_visarga = match.group(3)
            if trailing_visarga:
                word += trailing_visarga

            if re.match(r's\d+$', swara):
                marker_key = swara
                footnote_text = footnotes_dict.get(marker_key, '').strip()

                if footnote_text and footnote_text in seen_map:
                    unique_id, display_num = seen_map[footnote_text]
                else:
                    counter_obj['val'] += 1
                    val = counter_obj['val']
                    unique_id = f'fn-kandah-{val}'
                    display_num = ''.join(devanagari_digits[int(d)] for d in str(val))
                    if footnote_text:
                        seen_map[footnote_text] = (unique_id, display_num)
                        accumulator.append((unique_id, display_num, footnote_text))
                        collected_footnotes.append((unique_id, val, footnote_text))

                word = _escape_html(word)
                html_parts.append(
                    f'<span class="mantra-word"><span class="mantra-text">{word}</span><span class="swara-text">&nbsp;</span></span>'
                    f'<sup class="footnote-ref"><a href="#{unique_id}">{display_num}</a></sup>'
                )
            else:
                clusters = combine_ardhaksharas(word)
                if len(clusters) > 0:
                    last_cluster = clusters[-1]
                    preceding = "".join(clusters[:-1])
                    if preceding:
                        for cl in clusters[:-1]:
                            cl_esc = _escape_html(cl)
                            html_parts.append(
                                f'<span class="mantra-word">'
                                f'<span class="mantra-text">{cl_esc}</span>'
                                f'<span class="swara-text">&nbsp;</span>'
                                f'</span>'
                            )
                    last_cluster = _escape_html(last_cluster)
                    swara = _escape_html(swara)
                    html_parts.append(
                        f'<span class="mantra-word">'
                        f'<span class="mantra-text">{last_cluster}</span>'
                        f'<span class="swara-text">{swara}</span>'
                        f'</span>'
                    )
                else:
                    word = _escape_html(word)
                    swara = _escape_html(swara)
                    html_parts.append(
                        f'<span class="mantra-word">'
                        f'<span class="mantra-text">{word}</span>'
                        f'<span class="swara-text">{swara}</span>'
                        f'</span>'
                    )
            i += len(match.group(0))
        else:
            simple_word_match = re.match(r'([^\s()।॥]+)', text[i:])
            if simple_word_match:
                word = simple_word_match.group(1)
                clusters = combine_ardhaksharas(word)
                for cl in clusters:
                    cl_esc = _escape_html(cl)
                    html_parts.append(
                        f'<span class="mantra-word">'
                        f'<span class="mantra-text">{cl_esc}</span>'
                        f'<span class="swara-text">&nbsp;</span>'
                        f'</span>'
                    )
                i += len(simple_word_match.group(0))
            else:
                i += 1

    return ''.join(html_parts), collected_footnotes
