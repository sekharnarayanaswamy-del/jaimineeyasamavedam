#from docx import Document
import platform
from pathlib import Path
import re

import sys
import argparse
#from doc_utils import escape_for_latex
import jinja2
import subprocess
import tempfile
import os
import json
import urllib.parse
import yaml
from requests.models import PreparedRequest
import grapheme

# --- New import for utility functions ---
from utils import (
    combine_halants, combine_ardhaksharas,
    my_encodeURL, my_format,
    replacecolon, normalize_and_trim,
    parse_mantra_for_latex, 
    sanitize_data_structure,
    load_pipeline_config,
    get_generated_metadata
)
# --- End new import ---

# ----------------------------------------------------
# DEVANAGARI NUMERAL CONVERSION
# ----------------------------------------------------
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



CURRENT_PDF_FONT = "AdishilaVedic"
CURRENT_TOC_LEVEL = "section"

# ----------------------------------------------------
# 1. NEW UTILITY: Local Visarga Accent Ordering
# ----------------------------------------------------
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

# ----------------------------------------------------
# 2. NEW UTILITY: Accent Replacements (RAISED ZERO-WIDTH)
# ----------------------------------------------------
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

# ----------------------------------------------------
# 2. NEW UTILITY: Consecutive Accent Handler
# ----------------------------------------------------
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

# ----------------------------------------------------
# 3. NEW UTILITY: Remove Mantra Spaces (Samhita Mode)
# ----------------------------------------------------
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
    

# ----------------------------------------------------
# FOOTNOTE PROCESSING UTILITIES
# ----------------------------------------------------
def process_footnotes_latex(text, footnotes_dict, seen_markers=None, subsection_key=None):
    """
    Replace (s1), (s2) markers with state-aware LaTeX footnotes/references.
    
    Args:
        text: The text containing footnote markers like (s1), (s2)
        footnotes_dict: Dictionary { "s1": "text" }
        seen_markers: set of seen markers ("s1", "s2") for this subsection scope
        subsection_key: unique ID for the subsection to generate stable labels
    """
    if not footnotes_dict:
        return text
    
    # We need to find all markers matching (s\d+) in the text
    # and replace them sequentially to update the seen_markers set.
    
    def replacer(match):
        marker = match.group(1) # s1
        full_marker = match.group(0) # (s1)
        
        if marker not in footnotes_dict:
            return full_marker # Keep original if not found (or log error)
            
        footnote_text = footnotes_dict[marker]
        
        if seen_markers is not None and subsection_key is not None:
             label = f"fn:{subsection_key}:{marker}"
             if marker in seen_markers:
                 # Reference existing footnote
                 # Use rule (2.5ex) to ensure top alignment + raisebox (1.2ex) to match template
                 return f"\\rule{{0pt}}{{2.5ex}}\\textsuperscript{{\\raisebox{{1.2ex}}{{\\normalfont\\ref{{{label}}}}}}}"
             else:
                 # Create new footnote with label
                 seen_markers.add(marker)
                 return f"\\rule{{0pt}}{{2.5ex}}\\footnote{{{footnote_text}\\label{{{label}}}}}"
        else:
             # Fallback to stateless replacement (old behavior)
             return f"\\rule{{0pt}}{{2.5ex}}\\footnote{{{footnote_text}}}"

    # Sanitize invisible characters that break footnote matching
    # These are zero-width chars that can appear around (s1) markers from copy-paste
    invisible_chars_pattern = r'[\u200b\u200c\u200d\ufeff\u2060\u180e\u00ad]'
    text = re.sub(invisible_chars_pattern, '', text)
    
    pattern = r'\((s\d+)\)'
    new_text = re.sub(pattern, replacer, text)
    
    return new_text

def process_footnotes_html(text, footnotes_dict, local_counter=0, seen_markers_map=None, subsection_key=None):
    """
    Replace (s1), (s2) markers with HTML superscript links.
    Uses LOCAL counter for display numbering (resets per subsection).
    Uses subsection_key for unique IDs to prevent collisions across document.
    
    Args:
        text: Text to process
        footnotes_dict: Dict mapping markers to text
        local_counter: Current local counter for this subsection (display only)
        seen_markers_map: Map of seen markers to (unique_id, display_num) in this subsection
        subsection_key: Unique key for this subsection
        
    Returns:
        (processed_text, list_of_footnotes_data, new_local_counter)
        footnotes_data tuple: (unique_id, display_num, text)
    """
    if not footnotes_dict:
        return text, [], local_counter
    
    footnotes_list = []
    
    import os
    
    # Sanitize invisible characters that break footnote matching
    invisible_chars_pattern = r'[\u200b\u200c\u200d\ufeff\u2060\u180e\u00ad]'
    text = re.sub(invisible_chars_pattern, '', text)
    
    # regex to find (sX)
    matches = list(set(re.findall(r'\(s\d+\)', text))) # set to unique within this text block
    # Sort matches
    matches.sort(key=lambda x: int(x[2:-1]))
    
    # Sort matches
    matches.sort(key=lambda x: int(x[2:-1]))


    for marker_full in matches:
        marker = marker_full[1:-1] # strip ( ) -> s1
        if marker in footnotes_dict:
             footnote_text = footnotes_dict[marker].strip()
             
             # Check if CONTENT has been seen in the broader context
             if seen_markers_map is not None and footnote_text in seen_markers_map:
                 # Reuse existing number and ID
                 unique_id, dev_num = seen_markers_map[footnote_text]
                 # For duplicates, link to existing ID
                 replacement = f'<sup class="footnote-ref"><a href="#{unique_id}">{dev_num}</a></sup>'
                 text = text.replace(marker_full, replacement)
             else:
                 # New footnote
                 local_counter += 1
                 # footnote_text already fetched above
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

    return text, footnotes_list, local_counter

def process_footnotes_text(text, footnotes_dict):
    """
    Replace (s1), (s2) markers with Devanagari superscript numerals for plain text.
    Uses Unicode superscript characters where available.
    
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
        # Use parentheses for plain text to indicate superscript reference
        replacement = f'({devanagari_num})'
        text = re.sub(pattern, replacement, text)
        footnotes_list.append((devanagari_num, footnote_text))
    
    return text, footnotes_list


def split_rik_lines_text(text):
    """Ensure each Rik verse ends with a newline for plain text output."""
    if not text:
        return ""
    # Pattern to match a verse marker (e.g., ॥ ७ ॥) optionally followed by spaces
    # and ensure there's a newline after it.
    pattern = r'(॥\s*[\d०-९]+\s*॥)\s*'
    # Replace with the marker followed by a newline, but only if not already followed by one
    # To keep it simple, we'll just replace marker+any trailing space with marker+\n
    return re.sub(pattern, r'\1\n', text).strip()


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

                        
def CreatePdf(templateFileName, name, DocfamilyName, data, prayogas=None, current_os="Windows", output_mode="combined", font_family="AdishilaVedic", doc_title_sa="जैमिनीय साम संहिता", pdf_color_mode="bw", closing_mantras=None, summary_table=None, total_riks=None, total_samams=None, summary_title="संहिता सङ्ख्या", toc_level='section', has_riks=True, has_samams=True, output_dir_override=None, name_override=None, jsv_version=None, generated_at=None):
    data=escape_for_latex(data)
    
    outputdir="data/output"
    logdir=f"{outputdir}/logs"
    exit_code=0
    
    # Use overrides if provided
    name = name_override or name
    outputdir = output_dir_override or f"{outputdir}/pdf/{DocfamilyName}"
    
    TexFileName=f"{name}_{DocfamilyName}.tex"
    PdfFileName=f"{name}_{DocfamilyName}.pdf"
    TocFileName=f"{name}_{DocfamilyName}.toc"
    LogFileName=f"{name}_{DocfamilyName}.log"
    template = templateFileName
    Path(outputdir).mkdir(parents=True, exist_ok=True)
    Path(logdir).mkdir(parents=True, exist_ok=True)
    
    if not jsv_version or not generated_at:
        from utils import get_generated_metadata
        meta = get_generated_metadata()
        jsv_version = jsv_version or meta['version']
        generated_at = generated_at or meta['generated_at']
    
    document = template.render(
        supersections=data, 
        os=current_os, 
        output_mode=output_mode,
        version=jsv_version,
        generated_at=generated_at,
        font_family=font_family,
        doc_title_sa=doc_title_sa,
        pdf_color_mode=pdf_color_mode,
        closing_mantras=closing_mantras or [],
        font_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts").replace("\\", "/") + "/",
        summary_table=summary_table,
        total_riks=total_riks,
        total_samams=total_samams,
        summary_title=summary_title,
        toc_level=toc_level,
        has_riks=has_riks,
        has_samams=has_samams,
        prayogas=prayogas or []
    )
    

    tmpdirname="."
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpfilename=f"{tmpdirname}/{TexFileName}"

        with open(tmpfilename,"w",encoding="utf-8") as f:
            f.write(document)
        
        try:
            cmd = ["xelatex", "-interaction=nonstopmode", tmpfilename]
            proc = subprocess.run(cmd, cwd=tmpdirname, capture_output=True, text=True)
            
            # Step 2: run makeindex if .idx file exists to generate index (.ind)
            idx_file = Path(tmpdirname) / f"{Path(TexFileName).stem}.idx"
            if idx_file.exists() and idx_file.stat().st_size > 0:
                cmd_idx = ["makeindex", "-c", "-q", str(idx_file.name)]
                subprocess.run(cmd_idx, cwd=tmpdirname, capture_output=True, text=True)
                
            # Step 3: Pass 2 of xelatex to resolve TOC, index, and page cross-references
            proc = subprocess.run(cmd, cwd=tmpdirname, capture_output=True, text=True)
            if proc.returncode != 0:
                print(f"[WARNING] xelatex compilation returned non-zero code {proc.returncode}")
        except Exception as e:
            print(f"[WARNING] Failed to run xelatex: {e}")
        
        src_pdf_file=Path(f"{tmpdirname}/{PdfFileName}")
        dst_pdf_file=Path(f"{outputdir}/{PdfFileName}")
        src_log_file=Path(f"{tmpdirname}/{LogFileName}")
        dst_log_file=Path(f"{logdir}/{LogFileName}")
        src_tex_file=Path(f"{tmpdirname}/{TexFileName}")
        dst_tex_file=Path(f"{outputdir}/{TexFileName}")
        
        import shutil
        path = Path(src_tex_file)
        if path.is_file():
            try:
                shutil.copyfile(src_tex_file, dst_tex_file)
                src_tex_file.unlink(missing_ok=True)
            except Exception as e:
                print(f"[WARN] Could not move TeX file: {e}")
        path = Path(src_pdf_file)
        if path.is_file():
            try:
                shutil.copyfile(src_pdf_file, dst_pdf_file)
                src_pdf_file.unlink(missing_ok=True)
            except Exception as e:
                print(f"[WARN] Could not overwrite PDF file (may be locked in viewer): {e}")
        path = Path(src_log_file)
        if path.is_file():
            try:
                shutil.copyfile(src_log_file, dst_log_file)
                src_log_file.unlink(missing_ok=True)
            except Exception as e:
                print(f"[WARN] Could not move log file: {e}")

    return exit_code

def CreateTextFile(templateFileName, name, DocfamilyName, data, output_mode="combined", doc_title_sa="जैमिनीय साम संहिता", closing_mantras=None, toc_level='section', output_dir_override=None, name_override=None, jsv_version=None, generated_at=None):
    outputdir="data/output"
    logdir="data/output/logs"
    exit_code=0
    
    TexFileName=f"{name}_{DocfamilyName}_Unicode.tex"
    PdfFileName=f"{name}_{DocfamilyName}_Unicode.pdf"
    TextFileName=f"{name}_{DocfamilyName}_Unicode.txt"
    TocFileName=f"{name}_{DocfamilyName}_Unicode.toc"
    LogFileName=f"{name}_{DocfamilyName}_Unicode.log"
    template = templateFileName
    outputdir = f"{outputdir}/txt/{DocfamilyName}"  # Use DocfamilyName for directory
    Path(outputdir).mkdir(parents=True, exist_ok=True)
    Path(logdir).mkdir(parents=True, exist_ok=True)
    
    from utils import get_generated_metadata
    meta = get_generated_metadata()
    
    document = template.render(
        supersections=data, 
        output_mode=output_mode,
        doc_title_sa=doc_title_sa,
        version=jsv_version or meta['version'],
        generated_at=generated_at or meta['generated_at'],
        closing_mantras=closing_mantras or [],
        toc_level=toc_level
    )
    

    tmpdirname="."
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpfilename=f"{tmpdirname}/{TextFileName}"

        with open(tmpfilename,"w",encoding="utf-8") as f:
            f.write(document)
        
        src_text_file=Path(f"{tmpdirname}/{TextFileName}")
        dst_text_file=Path(f"{outputdir}/{TextFileName}")
        
        path = Path(src_text_file)
        if path.is_file():
            if dst_text_file.exists():
                dst_text_file.unlink()
            src_text_file.rename(dst_text_file)  

    return exit_code


def escape_for_latex(data):
    if isinstance(data, dict):
        new_data = {}
        for key in data.keys():
            if key == 'malayalam-mantra-sets':
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

    return data

    return data

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
    formatted_output.append(r"\vspace{0.4em}")
    formatted_output.append(r"\nopagebreak")

    # --- MANTRA CONTENT RENDERING ---
    all_mantra_rows, all_swara_rows = parse_mantra_for_latex(
        subsection, 
        supersection_title, 
        section_title, 
        subsection_title
    )
    
    paragraph_buffer = []
    
    footnotes_map = {}
    raw_footnotes = subsection.get('footnotes', []) 
    for note in raw_footnotes:
        if 'word' in note and 'content' in note:
            footnotes_map[note['word']] = note['content']

    for mantra_row, swara_row in zip(all_mantra_rows, all_swara_rows):
        
        is_verse_end = False
        if mantra_row:
            for token in reversed(mantra_row):
                if "SPACE_TOKEN" in token: continue
                if "॥" in token or "||" in token:
                    is_verse_end = True
                break 

        for i, (mantra_chunk, swara_chunk) in enumerate(zip(mantra_row, swara_row)):
            text_part = mantra_chunk.strip().replace(":", "ः")
            # Clean Stack Arguments
            text_part = clean_stack_arg(text_part)
            text_part = format_dandas(text_part)
            swara_part = swara_chunk.strip().replace('{}', '')
            swara_part = clean_stack_arg(swara_part)

            if "SPACE_TOKEN" in text_part:
                paragraph_buffer.append("")
                continue 

            extras = "" 
            
            # --- FOOTNOTE TRACKING (Ensure initialized at start of function too) ---
            # Extract footnotes from text_part if present
            # We look for (sX) patterns
            # First, sanitize invisible characters that can break matching
            invisible_chars_pattern = r'[\u200b\u200c\u200d\ufeff\u2060\u180e\u00ad]'
            text_part = re.sub(invisible_chars_pattern, '', text_part)
            
            if '(' in text_part and ')' in text_part:
                # Find all markers
                markers = re.findall(r'\((s\d+)\)', text_part)
                footnote_data = subsection.get('footnotes', {})
                for marker in markers:
                    # Remove marker from text_part so it doesn't go into stack
                    text_part = text_part.replace(f'({marker})', '')
                    
                    # Logic: If seen, use ref. If new, use footnote+label
                    # Use subsection_key to make label unique
                    # If subsection_key is None, fallback to unique-ish string or random
                    safe_key = subsection_key if subsection_key else "unknown"
                    label = f"fn:{safe_key}:{marker}"
                    
                    if marker in seen_markers:
                        # Refer to existing
                        # Use rule for top alignment + raisebox for template match
                        extras += f"\\rule{{0pt}}{{2.5ex}}\\textsuperscript{{\\raisebox{{1.2ex}}{{\\normalfont\\ref{{{label}}}}}}}"
                    else:
                        # Create new
                        fn_text = footnote_data.get(marker, f"Missing footnote: {marker}")
                        extras += f"\\rule{{0pt}}{{2.5ex}}\\footnote{{{fn_text}\\label{{{label}}}}}"
                        seen_markers.add(marker)
            
            # (Deleted old loop: for fn_text in found_footnotes...)

            if swara_part:
                clean_swara = swara_part.replace('{', '').replace('}', '')
                if len(clean_swara) > 1:
                    # LEFT STACK
                    stack_base = f"\\stackleft{{{text_part}}}{{{swara_part}}}"
                    spacing = "\\hspace{0.05em}"
                else:
                    # CENTER STACK
                    stack_base = f"\\stackcenter{{{text_part}}}{{{swara_part}}}"
                    spacing = "" # standard spacing handled by stackgap or none
            else:
                stack_base = text_part
                spacing = ""
            
            # Handle empty text_part (footnote marker was the only content)
            # Also handle "{}" which is left when marker like "{(s1)}" is stripped
            if (not text_part.strip() or text_part.strip() == '{}') and extras:
                # Output only the footnote, no empty braces or spacing
                token = extras
            else:
                # Normal case: stack + extras + spacing
                token = stack_base + extras + spacing

            if token and token != '{}':
                paragraph_buffer.append(token)
                paragraph_buffer.append("\\allowbreak")

        if is_verse_end:
            full_paragraph = "".join(paragraph_buffer)
            formatted_output.append(f"{{\\noindent\\justifying\\sloppy {full_paragraph}}}")
            formatted_output.append(r"\par\vspace{0.5em}") 
            paragraph_buffer = [] 

    # --- FINAL SPACING ---
    # The user wants an extra line between this subsection and the next metadata
    # if this subsection contains both Rik and Samam.
    is_mixed = bool(string_2.strip()) and bool(subsection.get('mantra_sets'))
    trailing_space = r"\par\vspace{1.5em}" if is_mixed else r"\par\vspace{0.6em}"

    if paragraph_buffer:
        full_paragraph = "".join(paragraph_buffer)
        formatted_output.append(f"{{\\noindent\\justifying\\sloppy {full_paragraph}}}")
        formatted_output.append(trailing_space)
    elif is_verse_end:
        # Update the last spacer if the paragraph ended exactly at a verse boundary
        if formatted_output and formatted_output[-1] == r"\par\vspace{0.5em}":
            formatted_output[-1] = trailing_space

    return "\n\n".join(formatted_output)


# ----------------------------------------------------
# RIK-ONLY FORMATTING (for separate output mode)
# ----------------------------------------------------
def format_rik_only(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None, subsection_key=None, toc_level='section'):
    """
    Format only Rik content (rik_metadata and rik_text) for separate output mode.
    Skips all Samam-related content.
    """
    formatted_output = []
    
    # --- FOOTNOTE TRACKING ---
    seen_markers = set()
    
    current_rik_id = subsection.get('rik_id')
    string_1 = subsection.get('rik_metadata', '')
    string_2 = subsection.get('rik_text', '')
    
    # Skip if no Rik content
    if not string_1 and not string_2:
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
    all_mantra_rows, all_swara_rows = parse_mantra_for_latex(
        subsection, 
        supersection_title, 
        section_title, 
        subsection_title
    )
    
    paragraph_buffer = []
    
    footnotes_map = {}
    raw_footnotes = subsection.get('footnotes', []) 
    for note in raw_footnotes:
        if 'word' in note and 'content' in note:
            footnotes_map[note['word']] = note['content']

    for mantra_row, swara_row in zip(all_mantra_rows, all_swara_rows):
        
        is_verse_end = False
        if mantra_row:
            for token in reversed(mantra_row):
                if "SPACE_TOKEN" in token: continue
                if "॥" in token or "||" in token:
                    is_verse_end = True
                break 

        for i, (mantra_chunk, swara_chunk) in enumerate(zip(mantra_row, swara_row)):
            text_part = mantra_chunk.strip().replace(":", "ः")
            text_part = clean_stack_arg(text_part)
            text_part = format_dandas(text_part)
            swara_part = swara_chunk.strip().replace('{}', '')
            swara_part = clean_stack_arg(swara_part)

            if "SPACE_TOKEN" in text_part:
                paragraph_buffer.append("")
                continue 

            extras = "" 
            
            # --- FOOTNOTE TRACKING (Ensure initialized at start of function too) ---
            # Extract footnotes from text_part if present
            # We look for (sX) patterns
            if '(' in text_part and ')' in text_part:
                # Find all markers
                markers = re.findall(r'\((s\d+)\)', text_part)
                footnote_data = subsection.get('footnotes', {})
                for marker in markers:
                    # Remove marker from text_part so it doesn't go into stack
                    text_part = text_part.replace(f'({marker})', '')
                    
                    # Logic: If seen, use ref. If new, use footnote+label
                    # Use subsection_key to make label unique
                    # If subsection_key is None, fallback to unique-ish string or random
                    safe_key = subsection_key if subsection_key else "unknown"
                    label = f"fn:{safe_key}:{marker}"
                    
                    if marker in seen_markers:
                        # Refer to existing
                        # Use rule for top alignment + raisebox for template match
                        extras += f"\\rule{{0pt}}{{2.5ex}}\\textsuperscript{{\\raisebox{{1.2ex}}{{\\normalfont\\ref{{{label}}}}}}}"
                    else:
                        # Create new
                        fn_text = footnote_data.get(marker, f"Missing footnote: {marker}")
                        extras += f"\\vphantom{{\\char\"0951}}\\footnote{{{fn_text}\\label{{{label}}}}}"
                        seen_markers.add(marker)
            
            # (Deleted old loop: for fn_text in found_footnotes...)

            if swara_part:
                clean_swara = swara_part.replace('{', '').replace('}', '')
                if len(clean_swara) > 1:
                    # LEFT STACK
                    stack_base = f"\\stackleft{{{text_part}}}{{{swara_part}}}"
                    spacing = "\\hspace{0.05em}"
                else:
                    # CENTER STACK
                    stack_base = f"\\stackcenter{{{text_part}}}{{{swara_part}}}"
                    spacing = ""
            else:
                stack_base = text_part
                spacing = ""
                      
            # Handle empty text_part (footnote marker was the only content)
            # Also handle "{}" which is left when marker like "{(s1)}" is stripped
            if (not text_part.strip() or text_part.strip() == '{}') and extras:
                # Output only the footnote, no empty braces or spacing
                token = extras
            else:
                # Normal case: stack + extras + spacing
                token = stack_base + extras + spacing

            if token and token != '{}':
                paragraph_buffer.append(token)
                paragraph_buffer.append("\\allowbreak")

        if is_verse_end:
            full_paragraph = "".join(paragraph_buffer)
            formatted_output.append(f"{{\\noindent\\justifying\\sloppy {full_paragraph}}}")
            formatted_output.append(r"\par\vspace{0.5em}") 
            paragraph_buffer = [] 

    if paragraph_buffer:
        full_paragraph = "".join(paragraph_buffer)
        formatted_output.append(f"{{\\noindent\\justifying\\sloppy {full_paragraph}}}")
        formatted_output.append(r"\par\vspace{0.5em}")

    return "\n\n".join(formatted_output)


# ----------------------------------------------------
# RIK NO-METADATA FORMATTING (for nometa output mode)
# ----------------------------------------------------
def format_rik_nometa(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None, subsection_key=None, toc_level='section'):
    """
    Format only Rik text (without rik_metadata) for nometa output mode.
    Skips all Samam-related content and metadata.
    """
    formatted_output = []
    
    # --- FOOTNOTE TRACKING ---
    seen_markers = set()
    
    current_rik_id = subsection.get('rik_id')
    string_2 = subsection.get('rik_text', '')
    
    # Skip if no Rik content
    if not string_2:
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
    all_mantra_rows, all_swara_rows = parse_mantra_for_latex(
        subsection, 
        supersection_title, 
        section_title, 
        subsection_title
    )
    
    paragraph_buffer = []
    
    footnotes_map = {}
    raw_footnotes = subsection.get('footnotes', []) 
    for note in raw_footnotes:
        if 'word' in note and 'content' in note:
            footnotes_map[note['word']] = note['content']

    for mantra_row, swara_row in zip(all_mantra_rows, all_swara_rows):
        
        is_verse_end = False
        if mantra_row:
            for token in reversed(mantra_row):
                if "SPACE_TOKEN" in token: continue
                if "॥" in token or "||" in token:
                    is_verse_end = True
                break 

        for i, (mantra_chunk, swara_chunk) in enumerate(zip(mantra_row, swara_row)):
            text_part = mantra_chunk.strip().replace(":", "ः")
            text_part = clean_stack_arg(text_part)
            text_part = format_dandas(text_part)
            swara_part = swara_chunk.strip().replace('{}', '')
            swara_part = clean_stack_arg(swara_part)

            if "SPACE_TOKEN" in text_part:
                paragraph_buffer.append("")
                continue 

            extras = "" 
            
            if '(' in text_part and ')' in text_part:
                markers = re.findall(r'\((s\d+)\)', text_part)
                footnote_data = subsection.get('footnotes', {})
                for marker in markers:
                    text_part = text_part.replace(f'({marker})', '')
                    safe_key = subsection_key if subsection_key else "unknown"
                    label = f"fn:{safe_key}:{marker}"
                    
                    if marker in seen_markers:
                        extras += f"\\rule{{0pt}}{{2.5ex}}\\textsuperscript{{\\raisebox{{1.2ex}}{{\\normalfont\\ref{{{label}}}}}}}"
                    else:
                        fn_text = footnote_data.get(marker, f"Missing footnote: {marker}")
                        extras += f"\\vphantom{{\\char\"0951}}\\footnote{{{fn_text}\\label{{{label}}}}}"
                        seen_markers.add(marker)

            if swara_part:
                clean_swara = swara_part.replace('{', '').replace('}', '')
                if len(clean_swara) > 1:
                    stack_base = f"\\stackleft{{{text_part}}}{{{swara_part}}}"
                    spacing = "\\hspace{0.05em}"
                else:
                    stack_base = f"\\stackcenter{{{text_part}}}{{{swara_part}}}"
                    spacing = ""
            else:
                stack_base = text_part
                spacing = ""
                      
            if (not text_part.strip() or text_part.strip() == '{}') and extras:
                token = extras
            else:
                token = stack_base + extras + spacing

            if token and token != '{}':
                paragraph_buffer.append(token)
                paragraph_buffer.append("\\allowbreak")

        if is_verse_end:
            full_paragraph = "".join(paragraph_buffer)
            formatted_output.append(f"{{\\noindent\\justifying\\sloppy {full_paragraph}}}")
            formatted_output.append(r"\par\vspace{0.5em}") 
            paragraph_buffer = [] 

    if paragraph_buffer:
        full_paragraph = "".join(paragraph_buffer)
        formatted_output.append(f"{{\\noindent\\justifying\\sloppy {full_paragraph}}}")
        formatted_output.append(r"\par\vspace{0.5em}")

    return "\n\n".join(formatted_output)


def format_mantra_sets_text(subsection,section_title,subsection_title):
    
    formatted_sets = []
    
    mantra_sets = subsection.get('mantra_sets', [])
    mantra_array = []
    for mantra_set in mantra_sets:
        mantra_words = mantra_set.get('mantra-words', [])
        mantra=""
        for w,word in enumerate(mantra_words):
            actual_word = word.get('word', 'WORD')
            
            mantra+=" " +actual_word
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
    # Note: #Start/#End of Mantra Sets markers are added by the Jinja2 template
    # Do not add them here to avoid duplication
    for mantra in mantra_array:
        # Keep mantra content together - replace \newline% with single space or nothing
        clean_mantra = mantra.replace('\\newline%', '').replace('\\newline', '')
        # Apply footnote application
        clean_mantra, _ = process_footnotes_text(clean_mantra, footnotes)
        formatted_sets.append(clean_mantra)
    return "\n".join(formatted_sets)


# ----------------------------------------------------
# MALAYALAM SAMAM-ONLY FORMATTING (Phase 1 pilot)
# ----------------------------------------------------
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
    "A", "B", "C", "D", "E", "F", "G", "H", "L",
    "a", "b", "c", "d", "e", "f", "g", "h", "l",
    "A1", "a1", "A_1", "a_1",
    "^", "˄", "Ʌ", "/\\", "∧", "⁀", "͡", "╭╮", "ͦ", "˚", "ॱ", "·",
    "|", "│", "।", "┃", "╷", "⃓", "\\", "╲", "⟍", "॑", "ˈ",
    "\uE001", "\uE002", "\uE003", "\uE004", "\uE005", "\uE006", "\uE008", "\uE00A", "\uE00B", "\uE00D"
}


def _apply_mantrakshara_modifier(syl_esc: str, mod: str) -> str:
    """Attach a swara modifier to a Mantrakshara in ModifierDarkBlue."""
    if not mod:
        return syl_esc
    m_clean = mod.strip("()")
    if m_clean in ("A", "a", "╭╮", "⁀", "\uE004"):
        return f"{syl_esc}\\rlap{{\\swarafont \\textcolor{{ModifierDarkBlue}}{{\\raisebox{{1.5ex}}{{\\hspace{{-0.4em}}\uE004}}}}}}"
    elif m_clean in ("A1", "a1", "A_1", "a_1", "\uE00D"):
        return f"{syl_esc}\\rlap{{\\swarafont \\textcolor{{ModifierDarkBlue}}{{\\raisebox{{1.5ex}}{{\\hspace{{-0.4em}}\uE00D}}}}}}"
    elif m_clean in ("B", "b", "^", "˄", "/\\", "∧", "\uE005"):
        return f"{syl_esc}\\rlap{{\\swarafont \\textcolor{{ModifierDarkBlue}}{{\\raisebox{{1.5ex}}{{\uE005}}}}}}"
    elif m_clean in ("C", "c", "ॱ", "·", "\uE001"):
        return f"{syl_esc}\\rlap{{\\swarafont \\textcolor{{ModifierDarkBlue}}{{\\raisebox{{0.30ex}}{{\\hspace{{0.05em}}\uE001}}}}}}"
    elif m_clean in ("D", "d", "Ʌ", "\uE006"):
        return f"{syl_esc}\\rlap{{\\swarafont \\textcolor{{ModifierDarkBlue}}{{\\raisebox{{1.5ex}}{{\uE006}}}}}}"
    elif m_clean in ("E", "e", "┃", "\uE002"):
        return f"{syl_esc}{{\\swarafont \\textcolor{{ModifierDarkBlue}}{{\uE002}}}}"
    elif m_clean in ("F", "f", "╷"):
        return f"{syl_esc}{{\\swarafont \\textcolor{{ModifierDarkBlue}}{{\uE002}}}}"
    elif m_clean in ("G", "g", "\\", "╲", "⟍", "\uE003"):
        return f"{syl_esc}\\rlap{{\\swarafont \\textcolor{{ModifierDarkBlue}}{{\\raisebox{{-0.35ex}}{{\\hspace{{-0.50em}}\uE003}}}}}}"
    elif m_clean in ("H", "h", "L", "l", "|", "│", "॑", "ˈ", "\uE00C"):
        return f"{syl_esc}\\rlap{{\\swarafont \\textcolor{{ModifierDarkBlue}}{{\\raisebox{{1.30ex}}{{\\hspace{{-0.55em}}\uE00C}}}}}}"
    return syl_esc


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
            # Check if p has trailing modifier char (e.g. \uE001, \uE003, \uE004, etc.)
            m = re.search(r"([\uE001-\uE00C\^\\/\|\_]+)$", p)
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


MALAYALAM_SWARA_GLYPH_MAP = {
    # Grantha Pla family
    "𑌪𑍍𑌲": "\uE020",
    "𑌪𑍍𑌲𑌾": "\uE021",
    "𑌪𑍍𑌲𑌿": "\uE022",
    "𑌪𑍍𑌲𑍀": "\uE023",
    "𑌪𑍍𑌲𑍁": "\uE024",
    "𑌪𑍍𑌲𑍂": "\uE025",
    "𑌪𑍍𑌲𑍍": "\uE026",
    
    # Malayalam Pla family
    "പ്ല": "\uE020",
    "പ്ലാ": "\uE021",
    "പ്ലി": "\uE022",
    "പ്ലീ": "\uE023",
    "പ്ലു": "\uE024",
    "പ്ലൂ": "\uE025",
    "പ്ല്": "\uE026",
    
    # Grantha Sha family
    "𑌶𑌾": "\uE010",
    "𑌶𑌿": "\uE011",
    "\u11336\u1133F": "\uE011",
    "𑌶𑍀": "\uE012",
    "𑌶𑍍": "\uE013",
    "𑌶𑍁": "\uE014",
    "𑌶𑍂": "\uE015",
    "𑌶𑍃": "\uE016",
    "𑌶𑍄": "\uE017",
    "𑌶𑍇": "\uE018",
    "𑌶𑍈": "\uE019",
    "𑌶𑍋": "\uE01A",
    "𑌶𑍌": "\uE01B",
    
    # Malayalam Sha family
    "ശ𑌾": "\uE010",
    "ശാ": "\uE010",
    "ശ𑌿": "\uE011",
    "ശി": "\uE011",
    "ശ𑍀": "\uE012",
    "ശീ": "\uE012",
    "ശ്": "\uE013",
    "ശു": "\uE014",
    "ശൂ": "\uE015",
    "ശൃ": "\uE016",
    "ശൄ": "\uE017",
    "ശെ": "\uE018",
    "ശൈ": "\uE019",
    "ശൊ": "\uE01A",
    "ശൌ": "\uE01B",
    "ശൗ": "\uE01B",
    
    # Other Conjuncts / Forms
    "𑌤𑍍𑌰": "\uE01D",  # Tra (A17)
    "ത്ര": "\uE01D",
    "𑌕𑍍𑌰": "\uE01E",  # Kra (A19)
    "ക്ര": "\uE01E",
    "𑌕𑍍𑌰𑍍": "\uE01F", # Kra + virama
    "ക്ര്": "\uE01F",
    "𑌶𑍍𑌰𑍂": "\uE027", # Shruu
    "ശ്രൂ": "\uE027",
    "𑌶𑍍𑌰𑍃": "\uE028", # Shrr
    "ശ്രൃ": "\uE028",
    "𑌷𑍃": "\uE028",
    "𑌣𑍁": "\uE029",  # Nna+U
    "ണു": "\uE029",
}


def _swara_latex(swara: str) -> str:
    """Latex for pure swara marker pitch glyphs rendered in bold SwaraRed using JaimineeyaSwara font."""
    if not swara:
        return ""
    # Filter out modifiers which attach directly to Mantrakshara
    if swara in MODIFIER_KEYS or swara in ("A", "B", "C", "D", "E", "F", "G", "H", "L", "a", "b", "c", "d", "e", "f", "g", "h", "l"):
        return ""
    mapped_swara = MALAYALAM_SWARA_GLYPH_MAP.get(swara, swara)
    return f"{{\\swarafont \\bfseries \\textcolor{{SwaraRed}}{{{mapped_swara}}}}}"


def wrap_latin_for_latex(text: str) -> str:
    r"""Wrap any Latin/English character sequences with {\latinfont ...} so they render in Nimbus Roman."""
    if not text:
        return text
    if r'\latinfont' in text:
        return text
    return re.sub(r'([A-Za-z0-9][A-Za-z0-9\s,\.\-\':;/\(\)]*)', r'{\\latinfont \1}', text)


def _render_malayalam_mantra_body(subsection):
    """Helper to render Malayalam mantra body with top swara stacks and footnotes."""
    from malayalam.ml_text import tokenize_mantra_line
    from malayalam.ml_transliterate import split_malayalam_syllables, devanagari_to_malayalam
    
    mantra_sets = subsection.get('malayalam-mantra-sets', [])
    if not mantra_sets:
        mantra_sets = subsection.get('corrected-mantra_sets', [])
    if not mantra_sets:
        mantra_sets = subsection.get('mantra_sets', [])
    if not mantra_sets:
        return []

    footnote_data = subsection.get('footnotes', {})
    paragraph_buffer = []
    formatted_paragraphs = []
    
    for mantra_set in mantra_sets:
        line = mantra_set.get('malayalam-mantra') or mantra_set.get('corrected-mantra') or mantra_set.get('mantra', '')
        if not line:
            continue
        is_verse_end = bool(re.search(r'॥\s*[०-९\d]+\s*॥\s*$', line))
        for tok in tokenize_mantra_line(line):
            t = tok['type']
            if t == 'space':
                paragraph_buffer.append(" ")
            elif t == 'danda':
                paragraph_buffer.append(format_dandas(tok['char']))
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
                word = tok['word'].translate(_ENGLISH_DIGITS)
                swara = tok['swara']
                if not word:
                    continue

                # Strip trailing punctuation (like _, ., ,) so swara marker stays on the preceding mantrakshara
                core_word = word.rstrip("_,.")
                trailing_punct = word[len(core_word):]

                if not core_word:
                    paragraph_buffer.append(f"{{\\malayalamfont {escape_for_latex(word)}}}")
                    continue

                if swara:
                    swara_parts, mod_parts = _parse_swara_and_modifiers(swara)
                    
                    syllables = split_malayalam_syllables(core_word)
                    parts = []
                    for idx, syl in enumerate(syllables):
                        syl_esc = escape_for_latex(syl)
                        if idx == len(syllables) - 1:
                            # Attach all modifiers to the final mantrakshara syllable
                            for mod in mod_parts:
                                syl_esc = _apply_mantrakshara_modifier(syl_esc, mod)
                                if mod in ("C", "c", "ॱ", "·", "\uE001"):
                                    syl_esc += r"\hspace{0.25em}"
                            
                            swara_str = "".join(swara_parts)
                            swara_latex = _swara_latex(swara_str)
                            if swara_latex:
                                stack_code = f"\\stackcenter{{\\malayalamfont {syl_esc}}}{{{swara_latex}}}"
                                parts.append(stack_code)
                            else:
                                parts.append(f"{{\\malayalamfont {syl_esc}}}")
                        else:
                            parts.append(f"{{\\malayalamfont {syl_esc}}}")
                    if trailing_punct:
                        parts.append(f"{{\\malayalamfont {escape_for_latex(trailing_punct)}}}")
                    paragraph_buffer.append("".join(parts))
                else:
                    syl_parts = []
                    syllables = split_malayalam_syllables(core_word)
                    for syl in syllables:
                        syl_esc = escape_for_latex(syl)
                        syl_parts.append(f"{{\\malayalamfont {syl_esc}}}")
                    if trailing_punct:
                        syl_parts.append(f"{{\\malayalamfont {escape_for_latex(trailing_punct)}}}")
                    paragraph_buffer.append("".join(syl_parts))
            else:
                extra_text = tok.get("text", "").translate(_ENGLISH_DIGITS)
                extra_esc = escape_for_latex(extra_text)
                paragraph_buffer.append(f"{{\\malayalamfont {extra_esc}}}")
        if is_verse_end:
            full_paragraph = "".join(paragraph_buffer)
            formatted_paragraphs.append(f"{{\\noindent\\justifying\\sloppy {{\\malayalamfont {full_paragraph}}}}}")
            formatted_paragraphs.append(r"\par\vspace{0.5em}")
            paragraph_buffer = []

    if paragraph_buffer:
        full_paragraph = "".join(paragraph_buffer)
        formatted_paragraphs.append(f"{{\\noindent\\justifying\\sloppy {{\\malayalamfont {full_paragraph}}}}}")
        formatted_paragraphs.append(r"\par\vspace{0.6em}")

    return formatted_paragraphs


def format_malayalam_rik_block(subsection, prev_rik_id=None, include_metadata=True):
    """Format Rik metadata + Rik text (with elevated Vedic accents and footnotes) for LaTeX PDF."""
    from malayalam.ml_transliterate import devanagari_to_malayalam, split_malayalam_syllables

    current_rik_id = subsection.get('rik_id')
    rik_ids = subsection.get('rik_ids', [current_rik_id] if current_rik_id else [])
    rik_metadata = subsection.get('rik_metadata', '')
    rik_text = subsection.get('rik_text', '')
    
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


def format_malayalam_rik_only(subsection, supersection_title, section_title, subsection_title, prev_rik_id=None, toc_level='section'):
    """Rik-only mode (with metadata) for Malayalam."""
    return format_malayalam_rik_block(subsection, prev_rik_id=prev_rik_id, include_metadata=True)


def format_malayalam_rik_nometa(subsection, supersection_title, section_title, subsection_title, prev_rik_id=None, toc_level='section'):
    """Rik-only mode (without metadata) for Malayalam."""
    return format_malayalam_rik_block(subsection, prev_rik_id=prev_rik_id, include_metadata=False)


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


def _normalize_malayalam_samam_text_line(line: str) -> str:
    """Normalize Malayalam Samam line for Unicode text export:
    1. Converts Devanagari/Malayalam numerals to ASCII English numerals (e.g. ॥१॥ -> ॥ 1 ॥).
    2. Converts any internal PUA characters to standard Grantha Unicode equivalents.
    3. Converts swara modifier shorthand tags (A..H) to their authentic Unicode symbols.
    """
    if not line:
        return ""
    
    # 1. Convert verse numerals to ASCII English digits with clean spacing
    line = re.sub(r'॥\s*([०-९\d]+)\s*॥', lambda m: f"॥ {m.group(1).translate(_ENGLISH_DIGITS)} ॥", line)
    
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
        
    # 3. Map Swara Modifier codes to Unicode symbols (using non-combining characters for standalone text rendering)
    mod_to_unicode = {
        'A': '⁀', 'a': '⁀', '\uE004': '⁀', '╭╮': '⁀',
        'B': '∧', 'b': '∧', '\uE005': '∧',
        'C': '·', 'c': '·', '\uE001': '·', 'ॱ': '·',
        'D': 'Ʌ', 'd': 'Ʌ', '\uE006': 'Ʌ',
        'E': '┃', 'e': '┃', '\uE002': '┃',
        'F': '╷', 'f': '╷',
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
    return line


def format_malayalam_samam_text(subsection, section_title, subsection_title):
    """Plain-text artifact for Malayalam Samam with Grantha swara markers and Unicode modifiers."""
    formatted_sets = []
    
    # 1. Check corrected-mantra_sets (preserves Grantha swara markers)
    corrected_mantra_sets = subsection.get('corrected-mantra_sets', [])
    if corrected_mantra_sets:
        for corrected in corrected_mantra_sets:
            c_mantra = corrected.get('corrected-mantra', '')
            if c_mantra:
                formatted_sets.append(_normalize_malayalam_samam_text_line(c_mantra))
        if formatted_sets:
            return "\n".join(formatted_sets)

    # 2. Check malayalam-mantra-sets
    for mantra_set in subsection.get('malayalam-mantra-sets', []):
        mantra = mantra_set.get('malayalam-mantra', '')
        if mantra:
            formatted_sets.append(_normalize_malayalam_samam_text_line(mantra))
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
            formatted_sets.append(_normalize_malayalam_samam_text_line(" ".join(words)))

    return "\n".join(formatted_sets)


# ----------------------------------------------------
# RIK-ONLY TEXT FORMATTING (for separate output mode)
# ----------------------------------------------------
def format_rik_only_text(subsection, section_title, subsection_title, prev_rik_id=None):
    """Format only Rik content for plain text output."""
    formatted_output = []
    
    current_rik_id = subsection.get('rik_id')
    rik_ids = subsection.get('rik_ids', [current_rik_id] if current_rik_id else [])
    rik_metadata = subsection.get('rik_metadata', '')
    rik_text = subsection.get('rik_text', '')
    
    # Skip if no Rik content or if this Rik was already shown
    show_rik_info = (prev_rik_id is None) or (current_rik_id != prev_rik_id)
    
    # Also show if rik_ids contains multiple Riks and the max ID differs from prev
    if not show_rik_info and len(rik_ids) > 1:
        max_rik_id = max(rik_ids) if rik_ids else None
        if max_rik_id is not None and max_rik_id != prev_rik_id:
            show_rik_info = True

    if not show_rik_info or (not rik_metadata and not rik_text):
        return ""
    
    # Rik ID header
    if current_rik_id:
        formatted_output.append(f"॥ ऋक् {to_devanagari_numeral(current_rik_id)} ॥")
    
    # Rik Metadata
    if rik_metadata:
        formatted_output.append(rik_metadata)
    
    # Rik Text (keep accent markers matching vedic_text.txt encoding)
    if rik_text:
        footnotes = subsection.get('footnotes', {})
        rik_text, _ = process_footnotes_text(rik_text, footnotes)
        formatted_output.append(rik_text)
    
    return "\n".join(formatted_output)


# ----------------------------------------------------
# SAMAM-ONLY TEXT FORMATTING (for separate output mode)
# ----------------------------------------------------
def format_samam_only_text(subsection, section_title, subsection_title):
    """Format only Samam content for plain text output."""
    formatted_output = []
    
    header = subsection.get('header', {}).get('header', '')
    saman_metadata = subsection.get('saman_metadata', '')
    
    # Header with Samam metadata on same line
    if header and saman_metadata:
        formatted_output.append(f"{header}  {saman_metadata}")
    elif header:
        formatted_output.append(header)
    elif saman_metadata:
        formatted_output.append(saman_metadata)
    
    # Mantra content
    mantra_sets = subsection.get('mantra_sets', [])
    corrected_mantra_sets = subsection.get('corrected-mantra_sets', [])
    
    # Use corrected mantras if available
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
        # Clean LaTeX formatting for plain text
        clean_mantra = mantra.replace('\\newline%', ' ')
        clean_mantra = clean_mantra.replace('\\newline', ' ')
        clean_mantra = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', clean_mantra)  # Remove \command{...}
        clean_mantra = re.sub(r'\\[a-zA-Z]+', '', clean_mantra)  # Remove \command
        clean_mantra = re.sub(r'\s+', ' ', clean_mantra).strip()  # Clean extra spaces
        
        # Apply footnote application
        clean_mantra, _ = process_footnotes_text(clean_mantra, footnotes)
        formatted_output.append(clean_mantra)
    
    return "\n".join(formatted_output)


# ----------------------------------------------------
# RIK NO-METADATA TEXT FORMATTING (for nometa output mode)
# ----------------------------------------------------
def format_rik_nometa_text(subsection, section_title, subsection_title, prev_rik_id=None):
    """Format only Rik text (without metadata) for plain text output."""
    formatted_output = []
    
    current_rik_id = subsection.get('rik_id')
    rik_ids = subsection.get('rik_ids', [current_rik_id] if current_rik_id else [])
    rik_text = subsection.get('rik_text', '')
    
    # Skip if no Rik content or if this Rik was already shown
    show_rik_info = (prev_rik_id is None) or (current_rik_id != prev_rik_id)

    # Also show if rik_ids contains multiple Riks and the max ID differs from prev
    if not show_rik_info and len(rik_ids) > 1:
        max_rik_id = max(rik_ids) if rik_ids else None
        if max_rik_id is not None and max_rik_id != prev_rik_id:
            show_rik_info = True

    if not show_rik_info or not rik_text:
        return ""
    
    # Rik ID header
    if current_rik_id:
        formatted_output.append(f"॥ ऋक् {to_devanagari_numeral(current_rik_id)} ॥")
    
    # Rik Text only (NO metadata)
    if rik_text:
        footnotes = subsection.get('footnotes', {})
        rik_text, _ = process_footnotes_text(rik_text, footnotes)
        formatted_output.append(rik_text)
    
    return "\n".join(formatted_output)


# ----------------------------------------------------
# SAMAM NO-METADATA TEXT FORMATTING (for nometa output mode)
# ----------------------------------------------------
def format_samam_nometa_text(subsection, section_title, subsection_title):
    """Format only Samam mantra text (without header or metadata) for plain text output.
    
    Note: The header is output separately by the template's SubSection Title section,
    so we do NOT include it here to avoid duplication.
    """
    formatted_output = []
    
    # Mantra content
    mantra_sets = subsection.get('mantra_sets', [])
    corrected_mantra_sets = subsection.get('corrected-mantra_sets', [])
    
    # Use corrected mantras if available
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
        # Clean LaTeX formatting for plain text
        clean_mantra = mantra.replace('\\newline%', ' ')
        clean_mantra = clean_mantra.replace('\\newline', ' ')
        clean_mantra = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', clean_mantra)  # Remove \command{...}
        clean_mantra = re.sub(r'\\[a-zA-Z]+', '', clean_mantra)  # Remove \command
        clean_mantra = re.sub(r'\s+', ' ', clean_mantra).strip()  # Clean extra spaces
        
        # Apply footnote application
        clean_mantra, _ = process_footnotes_text(clean_mantra, footnotes)
        formatted_output.append(clean_mantra)
    
    return "\n".join(formatted_output)


# ----------------------------------------------------
# HTML GENERATION FUNCTIONS
# ----------------------------------------------------

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

def replace_accents_html(text):
    """
    Replaces ASCII accent markers with Unicode Vedic accent characters for HTML.
    Positioning is controlled by CSS classes in the template.
    """
    if not text:
        return text
    
    replacements = [
        # Swarita (Vertical line above) - U+0951
        ('(1)', '<span class="accent-swarita">\u0951</span>'),
        # Anudatta (Horizontal line below) - U+1CD2
        ('(2)', '<span class="accent-anudatta">\u1CD2</span>'),
        # Kampa (Curve) - U+1CF8
        ('(3)', '<span class="accent-kampa">\u1CF8</span>'),
        # Trikampa - U+1CF9
        ('(4)', '<span class="accent-trikampa">\u1CF9</span>'),
    ]
    
    for marker, replacement in replacements:
        text = text.replace(marker, replacement)
    
    # Wrap visarga in span for CSS targeting (fixes NotoSansDevanagari circle issue)
    text = text.replace('ः', '<span class="visarga">ः</span>')
    
    return text

def format_mantra_sets_html(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None, subsection_key=None, 
                              footnote_counter=0, footnotes_accumulator=None, seen_content_map=None):
    """
    Formats mantra data as HTML using table-based layout for word/swara stacking.
    Uses tables similar to existing HTML output in the project.
    Only renders rik_metadata and rik_text if rik_id differs from prev_rik_id.
    """
    # Use passed state objects
    # global HTML_FOOTNOTE_COUNTER, HTML_SEEN_CONTENT_MAP -- REMOVED globals
    
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
    
    # Clean titles
    display_sub_title = re.sub(r'^([|॥]+)\s*', r'\1 ', subsection_title) if subsection_title else ''

    # 1. Rik Metadata - Only if rik_id changed
    if string_1 and show_rik_info:
        s1 = escape_for_html(string_1)
        # PRESERVE SPACES FOR METADATA
        s1 = format_dandas_html(s1, preserve_spaces=True)

        s1, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(s1, footnote_data, HTML_FOOTNOTE_COUNTER, seen_markers_map, subsection_key)
        collected_footnotes.extend(fnotes)
        formatted_output.append(f'<div class="rik-metadata sanskrit-text">{s1}</div>')

    # 2. Rik Text (With accents) - Only if rik_id changed
    if string_2 and show_rik_info:
        s2 = remove_mantra_spaces(string_2)
        # Remove LaTeX newline commands that shouldn't appear in HTML
        s2 = s2.replace('\\newline%', '').replace('\\newline', '')
        s2 = escape_for_html(s2)
        # Process footnotes
        s2, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(s2, footnote_data, HTML_FOOTNOTE_COUNTER, seen_markers_map, subsection_key)
        collected_footnotes.extend(fnotes)
        
        s2 = handle_consecutive_trikamba_html(s2)  # Fix overlap for consecutive trikamba
        s2 = replace_accents_html(s2)
        # Split multi-Rik text so each Rik is on its own line
        s2 = split_rik_lines_html(s2)
        s2 = format_dandas_html(s2)
        formatted_output.append(f'<div class="rik-text sanskrit-text">{s2}</div>')

    # 3. Combined Header
    header_parts = []
    if display_sub_title:
        header_title = escape_for_html(display_sub_title)
        header_title = format_dandas_html(header_title)
        header_parts.append(f'<span class="header-title">{header_title}</span>')
    if string_3:
        meta = escape_for_html(string_3)
        # PRESERVE SPACES FOR METADATA
        meta = format_dandas_html(meta, preserve_spaces=True)

        meta, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(meta, footnote_data, HTML_FOOTNOTE_COUNTER, seen_markers_map, subsection_key)
        collected_footnotes.extend(fnotes)
        header_parts.append(f'<span class="header-meta">{meta}</span>')
    
    if header_parts:
        formatted_output.append(f'<div class="subsection-header">{" &nbsp; ".join(header_parts)}</div>')

    # --- MANTRA CONTENT RENDERING (Inline-block for wrapping) ---
    all_mantra_rows, all_swara_rows = parse_mantra_for_latex(
        subsection, 
        supersection_title, 
        section_title, 
        subsection_title
    )
    
    for mantra_row, swara_row in zip(all_mantra_rows, all_swara_rows):
        
        is_verse_end = False
        if mantra_row:
            for token in reversed(mantra_row):
                if "SPACE_TOKEN" in token:
                    continue
                if "॥" in token or "||" in token:
                    is_verse_end = True
                break

        # Build inline-block elements for mantra and swara stacking
        word_elements = []
        
        for i, (mantra_chunk, swara_chunk) in enumerate(zip(mantra_row, swara_row)):
            text_part = mantra_chunk.strip().replace(":", "ः")
            text_part = text_part.replace('{', '').replace('}', '').strip()
            
            swara_part = swara_chunk.strip().replace('{}', '').replace('{', '').replace('}', '')
            # Remove LaTeX formatting commands from swara
            swara_part = swara_part.replace('\\textcolor{SwaraRed} ', '').replace('\\smallredfont ', '').strip()

            if "SPACE_TOKEN" in text_part:
                # Skip space tokens - CSS will handle spacing
                continue

            # Escape and format for HTML
            text_part = escape_for_html(text_part)
            text_part = format_dandas_html(text_part)
            
            # Process footnotes in mantra text
            text_part, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(text_part, footnote_data, HTML_FOOTNOTE_COUNTER, seen_markers_map, subsection_key)
            collected_footnotes.extend(fnotes)

            swara_part = escape_for_html(swara_part) if swara_part else '&nbsp;'
            
            # Create stacked word element
            word_html = f'<span class="mantra-word"><span class="mantra-text">{text_part}</span><span class="swara-text">{swara_part}</span></span>'
            word_elements.append(word_html)

        # Create verse div with flowing content
        if word_elements:
            verse_html = ''.join(word_elements)
            # Add extra margin if this is a mixed subsection (Rik + Samam)
            is_mixed = bool(string_2.strip())
            style = ' style="margin-bottom: 2.5rem;"' if is_mixed else ''
            formatted_output.append(f'<div class="mantra-verse"{style}>{verse_html}</div>')

    # If no mantra verses were added but it was a rik-only or header-only section, 
    # we don't necessarily add the extra margin here as it might be handled by the next section's top margin.
    # However, to be safe, if it's a mixed section and we only have Rik text so far (unlikely for mantra_sets),
    # we'd add it to the last div.

    # Accumulate footnotes for section-level rendering (don't render inline)
    if collected_footnotes and footnotes_accumulator is not None:
        footnotes_accumulator.extend(collected_footnotes)

    return '\n'.join(formatted_output), HTML_FOOTNOTE_COUNTER


# ----------------------------------------------------
# RIK-ONLY HTML FORMATTING (for separate output mode)
# ----------------------------------------------------
def format_rik_only_html(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None, subsection_key=None,
                         footnote_counter=0, footnotes_accumulator=None, seen_content_map=None):
    """
    Format only Rik content (rik_metadata and rik_text) for HTML separate output mode.
    Skips all Samam-related content.
    """
    # Use passed state
    HTML_FOOTNOTE_COUNTER = footnote_counter
    formatted_output = []
    collected_footnotes = []
    footnote_data = subsection.get('footnotes', {})
    seen_markers_map = seen_content_map if seen_content_map is not None else {}
    
    current_rik_id = subsection.get('rik_id')
    string_1 = subsection.get('rik_metadata', '')
    string_2 = subsection.get('rik_text', '')
    
    # Skip if no Rik content
    if not string_1 and not string_2:
        return "", HTML_FOOTNOTE_COUNTER
    
    # Only show if rik_id changed (avoid duplicates)
    show_rik_info = (prev_rik_id is None) or (current_rik_id != prev_rik_id)
    if not show_rik_info:
        return "", HTML_FOOTNOTE_COUNTER
    
    # Rik Metadata
    if string_1:
        s1 = escape_for_html(string_1)
        # PRESERVE SPACES FOR METADATA
        s1 = format_dandas_html(s1, preserve_spaces=True)

        s1, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(s1, footnote_data, HTML_FOOTNOTE_COUNTER, seen_markers_map, subsection_key)
        collected_footnotes.extend(fnotes)
        formatted_output.append(f'<div class="rik-metadata sanskrit-text">{s1}</div>')

    # Rik Text (with accents)
    if string_2:
        s2 = remove_mantra_spaces(string_2)
        # Remove LaTeX newline commands that shouldn't appear in HTML
        s2 = s2.replace('\\newline%', '').replace('\\newline', '')
        s2 = escape_for_html(s2)
        
        s2, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(s2, footnote_data, HTML_FOOTNOTE_COUNTER, seen_markers_map, subsection_key)
        collected_footnotes.extend(fnotes)
        
        s2 = handle_consecutive_trikamba_html(s2)  # Fix overlap for consecutive trikamba
        s2 = replace_accents_html(s2)
        # Split multi-Rik text so each Rik is on its own line
        s2 = split_rik_lines_html(s2)
        s2 = format_dandas_html(s2)
        formatted_output.append(f'<div class="rik-text sanskrit-text">{s2}</div>')

    # Accumulate footnotes for section-level rendering (don't render inline)
    if collected_footnotes and footnotes_accumulator is not None:
        footnotes_accumulator.extend(collected_footnotes)

    return '\n'.join(formatted_output), HTML_FOOTNOTE_COUNTER


# ----------------------------------------------------
# SAMAM-ONLY HTML FORMATTING (for separate output mode)
# ----------------------------------------------------
def format_samam_only_html(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None, subsection_key=None,
                           footnote_counter=0, footnotes_accumulator=None, seen_content_map=None):
    """
    Format only Samam content (header, saman_metadata, mantra text) for HTML separate output mode.
    Skips all Rik-related content.
    """
    # Use passed state
    HTML_FOOTNOTE_COUNTER = footnote_counter
    formatted_output = []
    collected_footnotes = []
    footnote_data = subsection.get('footnotes', {})
    seen_markers_map = seen_content_map if seen_content_map is not None else {}
    
    string_3 = subsection.get('saman_metadata', '')
    
    # Clean titles
    display_sub_title = re.sub(r'^([|॥]+)\s*', r'\1 ', subsection_title) if subsection_title else ''

    # Combined Header: subsection title + samam metadata
    header_parts = []
    if display_sub_title:
        header_title = escape_for_html(display_sub_title)
        header_title = format_dandas_html(header_title)
        header_parts.append(f'<span class="header-title">{header_title}</span>')
    if string_3:
        meta = escape_for_html(string_3)
        # PRESERVE SPACES FOR METADATA
        meta = format_dandas_html(meta, preserve_spaces=True)

        meta, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(meta, footnote_data, HTML_FOOTNOTE_COUNTER, seen_markers_map, subsection_key)
        collected_footnotes.extend(fnotes)
        header_parts.append(f'<span class="header-meta">{meta}</span>')
    
    if header_parts:
        formatted_output.append(f'<div class="subsection-header">{" &nbsp; ".join(header_parts)}</div>')

    # Mantra Content
    all_mantra_rows, all_swara_rows = parse_mantra_for_latex(
        subsection, 
        supersection_title, 
        section_title, 
        subsection_title
    )
    
    for mantra_row, swara_row in zip(all_mantra_rows, all_swara_rows):
        word_elements = []
        
        for i, (mantra_chunk, swara_chunk) in enumerate(zip(mantra_row, swara_row)):
            text_part = mantra_chunk.strip().replace(":", "ः")
            text_part = text_part.replace('{', '').replace('}', '').strip()
            
            swara_part = swara_chunk.strip().replace('{}', '').replace('{', '').replace('}', '')
            # Remove LaTeX formatting commands from swara
            swara_part = swara_part.replace('\\textcolor{SwaraRed} ', '').replace('\\smallredfont ', '').strip()

            if "SPACE_TOKEN" in text_part:
                continue

            text_part = escape_for_html(text_part)
            text_part = format_dandas_html(text_part)
            
            text_part, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(text_part, footnote_data, HTML_FOOTNOTE_COUNTER, seen_markers_map, subsection_key)
            collected_footnotes.extend(fnotes)

            swara_part = escape_for_html(swara_part) if swara_part else '&nbsp;'
            
            word_html = f'<span class="mantra-word"><span class="mantra-text">{text_part}</span><span class="swara-text">{swara_part}</span></span>'
            word_elements.append(word_html)

        if word_elements:
            verse_html = ''.join(word_elements)
            formatted_output.append(f'<div class="mantra-verse">{verse_html}</div>')

    # Accumulate footnotes for section-level rendering (don't render inline)
    if collected_footnotes and footnotes_accumulator is not None:
        footnotes_accumulator.extend(collected_footnotes)
            
    return '\n'.join(formatted_output), HTML_FOOTNOTE_COUNTER


# ----------------------------------------------------
# RIK NO-METADATA HTML FORMATTING (for nometa output mode)
# ----------------------------------------------------
def format_rik_nometa_html(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None, subsection_key=None,
                           footnote_counter=0, footnotes_accumulator=None, seen_content_map=None):
    """
    Format only Rik text (without rik_metadata) for HTML nometa output mode.
    Skips all Samam-related content and metadata.
    """
    # Use passed state
    HTML_FOOTNOTE_COUNTER = footnote_counter
    formatted_output = []
    collected_footnotes = []
    footnote_data = subsection.get('footnotes', {})
    seen_markers_map = seen_content_map if seen_content_map is not None else {}
    
    current_rik_id = subsection.get('rik_id')
    string_2 = subsection.get('rik_text', '')
    
    # Skip if no Rik content
    if not string_2:
        return "", HTML_FOOTNOTE_COUNTER
    
    # Only show if rik_id changed (avoid duplicates)
    show_rik_info = (prev_rik_id is None) or (current_rik_id != prev_rik_id)
    if not show_rik_info:
        return "", HTML_FOOTNOTE_COUNTER
    
    # Rik Text (with accents) - NO METADATA
    if string_2:
        s2 = remove_mantra_spaces(string_2)
        # Remove LaTeX newline commands that shouldn't appear in HTML
        s2 = s2.replace('\\newline%', '').replace('\\newline', '')
        s2 = escape_for_html(s2)
        
        s2, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(s2, footnote_data, HTML_FOOTNOTE_COUNTER, seen_markers_map, subsection_key)
        collected_footnotes.extend(fnotes)
        
        s2 = handle_consecutive_trikamba_html(s2)  # Fix overlap for consecutive trikamba
        s2 = replace_accents_html(s2)
        # Split multi-Rik text so each Rik is on its own line
        s2 = split_rik_lines_html(s2)
        s2 = format_dandas_html(s2)
        formatted_output.append(f'<div class="rik-text">{s2}</div>')

    # Accumulate footnotes for section-level rendering (don't render inline)
    if collected_footnotes and footnotes_accumulator is not None:
        footnotes_accumulator.extend(collected_footnotes)

    return '\n'.join(formatted_output), HTML_FOOTNOTE_COUNTER


# ----------------------------------------------------
# SAMAM NO-METADATA HTML FORMATTING (for nometa output mode)
# ----------------------------------------------------
def format_samam_nometa_html(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None, subsection_key=None,
                             footnote_counter=0, footnotes_accumulator=None, seen_content_map=None):
    """
    Format only Samam content (header, mantra text) for HTML nometa output mode.
    Skips all Rik-related content and saman_metadata.
    """
    # Use passed state
    HTML_FOOTNOTE_COUNTER = footnote_counter
    formatted_output = []
    collected_footnotes = []
    footnote_data = subsection.get('footnotes', {})
    seen_markers_map = seen_content_map if seen_content_map is not None else {}
    
    # Clean titles - NO saman_metadata
    display_sub_title = re.sub(r'^([|॥]+)\s*', r'\1 ', subsection_title) if subsection_title else ''

    # Header only (NO saman_metadata)
    if display_sub_title:
        header_title = escape_for_html(display_sub_title)
        header_title = format_dandas_html(header_title)
        formatted_output.append(f'<div class="subsection-header"><span class="header-title">{header_title}</span></div>')

    # Mantra Content
    all_mantra_rows, all_swara_rows = parse_mantra_for_latex(
        subsection, 
        supersection_title, 
        section_title, 
        subsection_title
    )
    
    for mantra_row, swara_row in zip(all_mantra_rows, all_swara_rows):
        word_elements = []
        
        for i, (mantra_chunk, swara_chunk) in enumerate(zip(mantra_row, swara_row)):
            text_part = mantra_chunk.strip().replace(":", "ः")
            text_part = text_part.replace('{', '').replace('}', '').strip()
            
            swara_part = swara_chunk.strip().replace('{}', '').replace('{', '').replace('}', '')
            # Remove LaTeX formatting commands from swara
            swara_part = swara_part.replace('\\textcolor{SwaraRed} ', '').replace('\\smallredfont ', '').strip()

            if "SPACE_TOKEN" in text_part:
                continue

            text_part = escape_for_html(text_part)
            text_part = format_dandas_html(text_part)
            
            text_part, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(text_part, footnote_data, HTML_FOOTNOTE_COUNTER, seen_markers_map, subsection_key)
            collected_footnotes.extend(fnotes)

            swara_part = escape_for_html(swara_part) if swara_part else '&nbsp;'
            
            word_html = f'<span class="mantra-word"><span class="mantra-text">{text_part}</span><span class="swara-text">{swara_part}</span></span>'
            word_elements.append(word_html)

        if word_elements:
            verse_html = ''.join(word_elements)
            formatted_output.append(f'<div class="mantra-verse">{verse_html}</div>')

    # Accumulate footnotes for section-level rendering (don't render inline)
    if collected_footnotes and footnotes_accumulator is not None:
        footnotes_accumulator.extend(collected_footnotes)
            
    return '\n'.join(formatted_output), HTML_FOOTNOTE_COUNTER

def format_malayalam_samam_html(subsection, header_text='', include_metadata=False):
    """Format Malayalam Samam content with top-stacked red swaras for HTML."""
    from malayalam.ml_text import tokenize_mantra_line
    from malayalam.ml_transliterate import split_malayalam_syllables
    
    formatted_output = []
    
    # Header
    header_parts = []
    if header_text:
        header_title = escape_for_html(header_text).translate(_ENGLISH_DIGITS)
        header_title = format_dandas_html(header_title)
        header_parts.append(f'<span class="header-title">{header_title}</span>')
    
    if include_metadata:
        saman_metadata = subsection.get('saman_metadata', '')
        if saman_metadata:
            meta = escape_for_html(saman_metadata).translate(_ENGLISH_DIGITS)
            meta = format_dandas_html(meta, preserve_spaces=True)
            header_parts.append(f'<span class="header-meta">{meta}</span>')
            
    if header_parts:
        formatted_output.append(f'<div class="subsection-header">{" &nbsp; ".join(header_parts)}</div>')
    
    mantra_sets = subsection.get('malayalam-mantra-sets', [])
    for mantra_set in mantra_sets:
        line = mantra_set.get('malayalam-mantra', '')
        if not line:
            continue
        tokens = tokenize_mantra_line(line)
        word_elements = []
        for tok in tokens:
            t = tok['type']
            if t == 'space':
                word_elements.append('<span class="word-space">&nbsp;</span>')
            elif t == 'danda':
                d = format_dandas_html(tok['char'])
                word_elements.append(f'<span class="mantra-word"><span class="swara-text">&nbsp;</span><span class="mantra-text">{d}</span></span>')
            elif t == 'footnote':
                fn_text = tok["text"].translate(_ENGLISH_DIGITS)
                word_elements.append(f'<span class="mantra-word"><span class="swara-text">&nbsp;</span><span class="mantra-text"><sup>{fn_text}</sup></span></span>')
            elif t == 'marker':
                word_elements.append(f'<span class="mantra-word"><span class="swara-text">{escape_for_html(tok["marker"])}</span><span class="mantra-text">&nbsp;</span></span>')
            elif t == 'word':
                word = tok['word'].translate(_ENGLISH_DIGITS)
                swara = tok['swara']
                if not word:
                    continue
                if swara:
                    syllables = split_malayalam_syllables(word)
                    for idx, syl in enumerate(syllables):
                        if idx == len(syllables) - 1:
                            s_esc = escape_for_html(swara)
                            word_elements.append(f'<span class="mantra-word"><span class="swara-text">{s_esc}</span><span class="mantra-text">{syl}</span></span>')
                        else:
                            word_elements.append(f'<span class="mantra-word"><span class="swara-text">&nbsp;</span><span class="mantra-text">{syl}</span></span>')
                else:
                    word_elements.append(f'<span class="mantra-word"><span class="swara-text">&nbsp;</span><span class="mantra-text">{word}</span></span>')
            else:
                extra_text = tok.get("text", "").translate(_ENGLISH_DIGITS)
                word_elements.append(f'<span class="mantra-word"><span class="swara-text">&nbsp;</span><span class="mantra-text">{extra_text}</span></span>')
        if word_elements:
            formatted_output.append(f'<div class="mantra-verse">{"".join(word_elements)}</div>')
    return '\n'.join(formatted_output), 0


def preprocess_html_data(supersections, output_mode):
    """
    Pre-processes the data structure to generate HTML for subsections and footnotes
    BEFORE template rendering. This avoids global state issues in Jinja.
    Returns: A list of dicts for the alphabetical index.
    """
    
    # Store index entries as (title, anchor_id)
    index_entries = []
    
    for super_key, supersection in supersections.items():
        for section_key, section in supersection.get('sections', {}).items():
            if section_key == 'count': continue

            
            # --- SECTION STATE ---
            footnote_counter = 0
            footnotes_accumulator = []
            seen_content_map = {}
            
            section['html_subsections'] = [] # List of HTML strings
            
            prev_rik_id = None
            
            for subsection_key, subsection in section.get('subsections', {}).items():
                unique_key = f"{super_key}_{section_key}_{subsection_key}"
                
                # Dispatch based on mode
                html_content = ""
                if output_mode == 'rik':
                    html_content, footnote_counter = format_rik_only_html(
                        subsection, None, None, subsection.get('header', {}).get('header'), {}, 
                        prev_rik_id, unique_key, 
                        footnote_counter, footnotes_accumulator, seen_content_map
                    )
                elif output_mode == 'rik_nometa':
                    html_content, footnote_counter = format_rik_nometa_html(
                        subsection, None, None, subsection.get('header', {}).get('header'), {}, 
                        prev_rik_id, unique_key, 
                        footnote_counter, footnotes_accumulator, seen_content_map
                    )
def format_malayalam_samam_html(subsection, subsection_title, include_metadata=True,
                                 footnote_counter=0, footnotes_accumulator=None, seen_content_map=None, subsection_key=None):
    """
    Format Malayalam Samam content as semantic HTML with clean Grantha swara stacking.
    - Strips all parentheses from the swara marker line.
    - Aligns swara modifiers (Mod-A..Mod-H) cleanly without parentheses.
    """
    from malayalam.ml_text import tokenize_mantra_line
    from malayalam.ml_transliterate import split_malayalam_syllables
    
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
        meta, fnotes, footnote_counter = process_footnotes_html(meta, footnote_data, footnote_counter, seen_markers_map, subsection_key)
        collected_footnotes.extend(fnotes)
        header_parts.append(f'<span class="header-meta">{meta}</span>')
        
    if header_parts:
        formatted_output.append(f'<div class="subsection-header">{" &nbsp; ".join(header_parts)}</div>')
        
    # 2. Mantra verses
    mantra_array = []
    corrected_mantra_sets = subsection.get('corrected-mantra_sets', [])
    if corrected_mantra_sets:
        for corrected in corrected_mantra_sets:
            c_mantra = corrected.get('corrected-mantra', '')
            if c_mantra:
                mantra_array.append(c_mantra)
    elif subsection.get('mantra_sets'):
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
                mantra_array.append(" ".join(words))
    elif subsection.get('malayalam-mantra-sets'):
        for mset in subsection.get('malayalam-mantra-sets', []):
            m = mset.get('malayalam-mantra', '')
            if m:
                mantra_array.append(m)

    for mantra_line in mantra_array:
        clean_mantra = mantra_line.replace('\\newline%', ' ').replace('\\newline', ' ')
        tokens = tokenize_mantra_line(clean_mantra)
        
        verse_tokens = []
        for tok in tokens:
            t = tok['type']
            if t == 'space':
                verse_tokens.append('<span class="word-space">&nbsp;</span>')
            elif t == 'danda':
                danda_text = escape_for_html(tok.get('char', '।'))
                verse_tokens.append(f'<span class="danda">{danda_text}</span>')
            elif t == 'word':
                word = tok['word'].translate(_ENGLISH_DIGITS)
                swara = tok['swara']
                if not word:
                    continue
                core_word = word.rstrip("_,.")
                trailing_punct = word[len(core_word):]
                syllables = split_malayalam_syllables(core_word)
                swara_parts, mod_parts = _parse_swara_and_modifiers(swara)
                
                for idx, syl in enumerate(syllables):
                    syl_esc = escape_for_html(syl)
                    if idx == len(syllables) - 1:
                        swara_str = "".join(swara_parts).strip("()")
                        swara_display = MALAYALAM_SWARA_GLYPH_MAP.get(swara_str, swara_str)
                        mod_spans = []
                        for mod in mod_parts:
                            m_clean = mod.strip("()")
                            if m_clean in ("C", "c", "ॱ", "·", "\uE001"):
                                mod_spans.append('<span class="swara-mod mod-c">&#xE001;</span>')
                            elif m_clean in ("H", "h", "|", "│", "॑", "ˈ", "\uE00C"):
                                mod_spans.append('<span class="swara-mod mod-h">&#xE00C;</span>')
                            elif m_clean in ("A", "a", "╭╮", "⁀", "\uE004"):
                                mod_spans.append('<span class="swara-mod mod-a">&#xE004;</span>')
                            elif m_clean in ("A1", "a1", "A_1", "a_1", "\uE00D"):
                                mod_spans.append('<span class="swara-mod mod-a1">&#xE00D;</span>')
                            elif m_clean in ("B", "b", "^", "˄", "/\\", "∧", "\uE005"):
                                mod_spans.append('<span class="swara-mod mod-b">&#xE005;</span>')
                            elif m_clean in ("D", "d", "Ʌ", "\uE006"):
                                mod_spans.append('<span class="swara-mod mod-d">&#xE006;</span>')
                            elif m_clean in ("G", "g", "\\", "╲", "⟍", "\uE003"):
                                mod_spans.append('<span class="swara-mod mod-g">&#xE003;</span>')
                            elif m_clean in ("E", "e", "┃", "\uE002"):
                                mod_spans.append('<span class="swara-mod mod-e">&#xE002;</span>')
                            elif m_clean in ("F", "f", "╷"):
                                mod_spans.append('<span class="swara-mod mod-f">&#xE002;</span>')
                        
                        mod_html = "".join(mod_spans)
                        swara_html = f'<span class="swara-text">{escape_for_html(swara_display)}</span>' if swara_display else '<span class="swara-text">&nbsp;</span>'
                        verse_tokens.append(f'<span class="mantra-word">{swara_html}<span class="mantra-text">{syl_esc}{mod_html}</span></span>')
                    else:
                        verse_tokens.append(f'<span class="mantra-word"><span class="swara-text">&nbsp;</span><span class="mantra-text">{syl_esc}</span></span>')
                if trailing_punct:
                    verse_tokens.append(f'<span class="mantra-punct">{escape_for_html(trailing_punct)}</span>')
            elif t == 'footnote':
                fn_key = tok.get('marker', '')
                fn_text = footnote_data.get(fn_key, '')
                if fn_text:
                    fn_esc, fnotes, footnote_counter = process_footnotes_html(f"({fn_key})", footnote_data, footnote_counter, seen_markers_map, subsection_key)
                    collected_footnotes.extend(fnotes)
                    verse_tokens.append(fn_esc)
            else:
                extra_text = escape_for_html(tok.get('text', '').translate(_ENGLISH_DIGITS))
                if extra_text:
                    verse_tokens.append(f'<span class="extra-text">{extra_text}</span>')

        if verse_tokens:
            formatted_output.append(f'<div class="mantra-verse">{"".join(verse_tokens)}</div>')

    if collected_footnotes and footnotes_accumulator is not None:
        footnotes_accumulator.extend(collected_footnotes)

    return '\n'.join(formatted_output), footnote_counter


def preprocess_html_data(supersections, output_mode='combined'):
    """
    Pre-processes all subsection content for HTML template rendering.
    """
    index_entries = []
    
    for super_key, supersection in supersections.items():
        for section_key, section in supersection.get('sections', {}).items():
            if section_key == 'count': continue
            
            # --- SECTION STATE ---
            footnote_counter = 0
            footnotes_accumulator = []
            seen_content_map = {}
            
            section['html_subsections'] = [] # List of HTML strings
            
            prev_rik_id = None
            
            for subsection_key, subsection in section.get('subsections', {}).items():
                unique_key = f"{super_key}_{section_key}_{subsection_key}"
                is_malayalam = bool(subsection.get('malayalam-mantra-sets') or subsection.get('corrected-mantra_sets'))
                
                # Dispatch based on mode
                html_content = ""
                if output_mode == 'rik':
                    html_content, footnote_counter = format_rik_only_html(
                        subsection, None, None, subsection.get('header', {}).get('header'), {}, 
                        prev_rik_id, unique_key, 
                        footnote_counter, footnotes_accumulator, seen_content_map
                    )
                elif output_mode == 'rik_nometa':
                    html_content, footnote_counter = format_rik_nometa_html(
                        subsection, None, None, subsection.get('header', {}).get('header'), {}, 
                        prev_rik_id, unique_key, 
                        footnote_counter, footnotes_accumulator, seen_content_map
                    )
                elif output_mode == 'samam':
                    if is_malayalam:
                        html_content, footnote_counter = format_malayalam_samam_html(
                            subsection, subsection.get('header', {}).get('header', ''), include_metadata=True,
                            footnote_counter=footnote_counter, footnotes_accumulator=footnotes_accumulator,
                            seen_content_map=seen_content_map, subsection_key=unique_key
                        )
                    else:
                        html_content, footnote_counter = format_samam_only_html(
                            subsection, None, None, subsection.get('header', {}).get('header'), {}, 
                            prev_rik_id, unique_key, 
                            footnote_counter, footnotes_accumulator, seen_content_map
                        )
                elif output_mode == 'samam_nometa':
                    if is_malayalam:
                        html_content, footnote_counter = format_malayalam_samam_html(
                            subsection, subsection.get('header', {}).get('header', ''), include_metadata=False,
                            footnote_counter=footnote_counter, footnotes_accumulator=footnotes_accumulator,
                            seen_content_map=seen_content_map, subsection_key=unique_key
                        )
                    else:
                        html_content, footnote_counter = format_samam_nometa_html(
                            subsection, None, None, subsection.get('header', {}).get('header'), {}, 
                            prev_rik_id, unique_key, 
                            footnote_counter, footnotes_accumulator, seen_content_map
                        )
                else:
                    if is_malayalam:
                        r_html = ""
                        if subsection.get('rik_text') or subsection.get('rik_metadata'):
                            r_html, footnote_counter = format_rik_only_html(
                                subsection, None, None, subsection.get('header', {}).get('header'), {}, 
                                prev_rik_id, unique_key, 
                                footnote_counter, footnotes_accumulator, seen_content_map
                            )
                        s_html, footnote_counter = format_malayalam_samam_html(
                            subsection, subsection.get('header', {}).get('header', ''), include_metadata=True,
                            footnote_counter=footnote_counter, footnotes_accumulator=footnotes_accumulator,
                            seen_content_map=seen_content_map, subsection_key=unique_key
                        )
                        html_content = f"{r_html}\n{s_html}" if r_html else s_html
                    else:
                        html_content, footnote_counter = format_mantra_sets_html(
                            subsection, None, None, subsection.get('header', {}).get('header'), {}, 
                            prev_rik_id, unique_key, 
                            footnote_counter, footnotes_accumulator, seen_content_map
                        )
                
                # INDEX COLLECT
                header = subsection.get('header', {}).get('header', '')
                if header:
                    # Consistent logic with PDF: strip dandas and spaces
                    index_title = re.sub(r'[|॥]', '', header).strip()
                    if index_title:
                        # Append to list; we'll deduplicate by adding disambiguation if needed
                        index_entries.append({
                            'title': index_title,
                            'anchor': f"{super_key}-{section_key}-{subsection_key}"
                        })

                section['html_subsections'].append({
                    'id': f"{super_key}-{section_key}-{subsection_key}",
                    'content': html_content
                })
                
                prev_rik_id = subsection.get('rik_id')
                
            # --- GENERATE FOOTNOTE HTML ---
            # Using the logic from render_section_footnotes but locally
            if footnotes_accumulator:
                 output = ['<hr class="footnote-separator"/>']
                 output.append('<div class="footnote-section">')
                 for unique_id, display_num, text in footnotes_accumulator:
                     output.append(f'<div class="footnote-item" id="{unique_id}"><sup class="footnote-ref">{display_num}</sup> {text}</div>')
                 output.append('</div>')
                 section['html_footer'] = '\n'.join(output)
            else:
                 section['html_footer'] = ""

    # Deduplicate and sort index alphabetically
    # To properly sort devanagari we can just use python sorted, it works decently.
    # Group by title to remove duplicates pointing to different anchors (or keep them?)
    # Usually index groups by title and lists pages. For HTML we'll just link to the first occurrence
    unique_index = {}
    title_counts = {}
    
    # Sort by anchor to maintain document order before deduplication/suffixing
    index_entries.sort(key=lambda x: x['anchor'])
    
    for entry in index_entries:
        title = entry['title']
        if title in unique_index:
            # Duplicate title found! Add a numeric suffix to make it unique in the index
            title_counts[title] = title_counts.get(title, 1) + 1
            unique_title = f"{title} ({title_counts[title]})"
            unique_index[unique_title] = entry['anchor']
        else:
            unique_index[title] = entry['anchor']
            title_counts[title] = 1
            
    # Sorted list for template
    sorted_index = []
    for title in sorted(unique_index.keys()):
        sorted_index.append({
            'title': title,
            'anchor': unique_index[title]
        })
    
    return sorted_index


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



def CreateHtmlFile(templateFileName, name, DocfamilyName, data, html_font="'AdishilaVedic', 'AdishilaSanVedic'", output_mode="combined", doc_title_sa="जैमिनीय साम संहिता", closing_mantras=None, summary_table=None, total_riks=None, total_samams=None, summary_title="संहिता सङ्ख्या", toc_level='section', has_riks=True, has_samams=True, output_dir_override=None, name_override=None, jsv_version=None, generated_at=None):
    """
    Creates an HTML file from the template and data.
    Similar to CreatePdf but outputs HTML instead.
    
    Args:
        html_font: Font family string for HTML output (e.g., "'AdishilaVedic', 'AdishilaSanVedic'")
        output_mode: 'combined', 'rik', or 'samam' for filtering content
        doc_title_sa: Sanskrit title for the document
        closing_mantras: List of closing mantra lines to render at the end
    """
    outputdir = "data/output"
    exit_code = 0
    
    # Malayalam script mode has no HTML template yet; skip gracefully
    if templateFileName is None:
        return
    
    # Use overrides if provided
    name = name_override or name
    outputdir = output_dir_override or f"{outputdir}/html/{DocfamilyName}"
    
    HtmlFileName = f"{name}_{DocfamilyName}.html"
    template = templateFileName
    Path(outputdir).mkdir(parents=True, exist_ok=True)
    
    global HTML_FOOTNOTE_COUNTER
    HTML_FOOTNOTE_COUNTER = 0 # Not used in pre-process mode but kept for safety
    
    # PRE-PROCESS DATA
    html_index = preprocess_html_data(data, output_mode)
    
    if not jsv_version or not generated_at:
        from utils import get_generated_metadata
        meta = get_generated_metadata()
        jsv_version = jsv_version or meta['version']
        generated_at = generated_at or meta['generated_at']
    
    import base64
    jaimineeya_swara_b64 = ""
    font_file = Path("fonts/JaimineeyaSwara.ttf")
    if font_file.exists():
        with open(font_file, "rb") as f_font:
            jaimineeya_swara_b64 = base64.b64encode(f_font.read()).decode("ascii")
    
    document = template.render(
        supersections=data, 
        html_font=html_font, 
        output_mode=output_mode,
        doc_title_sa=doc_title_sa,
        version=jsv_version,
        generated_at=generated_at,
        html_index=html_index,
        closing_mantras=closing_mantras or [],
        summary_table=summary_table,
        total_riks=total_riks,
        total_samams=total_samams,
        summary_title=summary_title,
        toc_level=toc_level,
        has_riks=has_riks,
        has_samams=has_samams,
        jaimineeya_swara_b64=jaimineeya_swara_b64
    )
    
    output_path = Path(f"{outputdir}/{HtmlFileName}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(document)
    
    print(f"HTML file created: {output_path}")
    return exit_code


def main():
    # Force UTF-8 encoding for console output
    if sys.stdout.encoding.lower() != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    # 0. Load Configuration from centralized pipeline_config.yaml
    pipeline_cfg = load_pipeline_config()
    config = pipeline_cfg.get('render', {})
    
    cfg_defaults = config.get('defaults', {})
    cfg_types = config.get('types', {})
    cfg_paths = config.get('paths', {})

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Generate PDF, HTML, and Text from Vedic text JSON',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Output Modes:
  combined  - Single output with both Rik and Samam content (default)
  separate  - Two separate outputs: Rik-only and Samam-only (with metadata)
  nometa    - Two separate outputs: Rik-only and Samam-only (without metadata)

Examples:
  python renderPDF.py input.json
  python renderPDF.py input.json --output-mode separate
  python renderPDF.py input.json --output-mode nometa
        """
    )
    parser.add_argument('input_file', nargs='?', default=None,
                        help='Input JSON file (auto-selected based on --type if not specified)')
    parser.add_argument('--output-mode', dest='output_mode',
                        choices=['combined', 'separate', 'nometa'], default=None,
                        help='Output mode: combined (default), separate, or nometa')
    parser.add_argument('--pdf-font', dest='pdf_font', default=None,
                        help='Font for PDF output')
    parser.add_argument('--html-font', dest='html_font', default=None,
                        help="Font for HTML output")
    parser.add_argument('--type', choices=['samhita', 'aaranam', 'collection'], default='samhita',
                        help='Type of Samaveda text: samhita, aaranam, or collection')
    
    parser.add_argument('--script', dest='script',
                        choices=['devanagari', 'malayalam'], default='devanagari',
                        help='Rendering script: devanagari (default) or malayalam (Phase 1 Samam-only pilot)')
    
    # NEW CLI OPTION
    parser.add_argument('--pdf-color-mode', dest='pdf_color_mode',
                        choices=['bw', 'color'], default=None,
                        help='Color mode for PDF output: bw or color')
                        
    parser.add_argument('--toc-level', dest='toc_level',
                        choices=['section', 'subsection', 'both'], default=None,
                        help='Determines which headers appear in the TOC.')
    
    parser.add_argument('--title', dest='title', default=None,
                        help='Custom Sanskrit title for the document.')
    
    parser.add_argument('--output', '-o', dest='output', default=None,
                        help='Override the default output basename or specify a full output path.')
    
    args = parser.parse_args()
    mode_type = args.type
    type_settings = cfg_types.get(mode_type, {})

    # Priority Merging: CLI > Config Type > Config Default > Hardcoded fallback
    output_mode = args.output_mode or type_settings.get('output_mode') or cfg_defaults.get('output_mode', 'combined')
    pdf_font = args.pdf_font or type_settings.get('pdf_font') or cfg_defaults.get('pdf_font', 'AdishilaVedic')
    html_font = args.html_font or type_settings.get('html_font') or cfg_defaults.get('html_font', "'AdishilaVedic', 'AdishilaSanVedic'")
    pdf_color_mode = args.pdf_color_mode or type_settings.get('pdf_color_mode') or cfg_defaults.get('pdf_color_mode', 'bw')
    toc_level = args.toc_level or type_settings.get('toc_level') or cfg_defaults.get('toc_level', 'section')
    
    global CURRENT_PDF_FONT
    CURRENT_PDF_FONT = pdf_font
    global CURRENT_TOC_LEVEL
    CURRENT_TOC_LEVEL = toc_level
    
    # Handle output path overrides
    out_dir = None
    out_name = None
    if args.output:
        out_path = Path(args.output)
        if args.output.endswith('/') or args.output.endswith('\\') or out_path.is_dir():
            out_dir = str(out_path)
            out_name = None
        else:
            out_dir = str(out_path.parent) if str(out_path.parent) != '.' else None
            out_name = out_path.name
    
    # Auto-select default input file
    input_file = args.input_file or type_settings.get('input_file')
    if not input_file:
         # Fallback to historical hardcoded defaults
         if mode_type == 'aaranam':
             input_file = 'data/output/Aaranam_latest_out.json'
         elif mode_type == 'collection':
             input_file = 'data/output/Collection_latest_out.json'
         else:
             input_file = 'data/output/Agneyam-Pavamanam_latest_out.json'
    
    file_prefix = type_settings.get('file_prefix') or (
        "Aaranam" if mode_type == 'aaranam' else 
        "Collection" if mode_type == 'collection' else "Samhita"
    )

    # Path configuration
    tpl_paths = cfg_paths.get('templates', {})
    template_dir = tpl_paths.get('pdf', "templates/pdf")
    text_template_dir = tpl_paths.get('text', "templates/text")
    html_template_dir = tpl_paths.get('html', "templates/html")
    
    templateFile_Grantha = f"{template_dir}/Grantha_main.template"
    templateFile_Devanagari = f"{template_dir}/Devanagari_main.template"
    templateFile_Tamil = f"{template_dir}/Tamil_main.template"
    templateFile_Malayalam = f"{template_dir}/Malayalam_main.template"
    
    text_templateFile_Devanagari = f"{text_template_dir}/Devanagari_main.template"
    html_templateFile_Devanagari = f"{html_template_dir}/Devanagari_main_html.template"

    outputdir = cfg_paths.get('output_root', "data/output")
    logdir = cfg_paths.get('logs', "data/output/logs")
    
    # LaTeX/Text Jinja environment (uses LaTeX-style delimiters)
    latex_jinja_env = jinja2.Environment(
    block_start_string = r'\BLOCK{',
    block_end_string = '}',
    variable_start_string = r'\VAR{',
    variable_end_string = '}',
    comment_start_string = r'\#{',
    comment_end_string = '}',
    line_statement_prefix = '%-',
    line_comment_prefix = '%#',
    trim_blocks = True,
    lstrip_blocks=True,
    autoescape = False,
    loader = jinja2.FileSystemLoader(os.path.abspath('.')),
    extensions=['jinja2.ext.loopcontrols']
    )
    latex_jinja_env.filters["my_encodeURL"] = my_encodeURL
    latex_jinja_env.filters["escape_for_latex"] = escape_for_latex
    latex_jinja_env.filters["replace_footnotes"] = replace_footnote_markers_filter
    latex_jinja_env.filters["format_mantra_sets_text"] = format_mantra_sets_text
    latex_jinja_env.filters["format_mantra_sets"] = format_mantra_sets
    latex_jinja_env.filters["format_rik_only"] = format_rik_only
    latex_jinja_env.filters["format_samam_only"] = format_samam_only
    latex_jinja_env.filters["format_rik_only_text"] = format_rik_only_text
    latex_jinja_env.filters["format_samam_only_text"] = format_samam_only_text
    latex_jinja_env.filters["format_rik_nometa"] = format_rik_nometa
    latex_jinja_env.filters["format_samam_nometa"] = format_samam_nometa
    latex_jinja_env.filters["format_rik_nometa_text"] = format_rik_nometa_text
    latex_jinja_env.filters["format_malayalam_rik_only"] = format_malayalam_rik_only
    latex_jinja_env.filters["format_malayalam_rik_nometa"] = format_malayalam_rik_nometa
    latex_jinja_env.filters["format_malayalam_samam_only"] = format_malayalam_samam_only
    latex_jinja_env.filters["format_malayalam_samam_nometa"] = format_malayalam_samam_nometa
    latex_jinja_env.filters["format_malayalam_combined"] = format_malayalam_combined
    latex_jinja_env.filters["format_malayalam_samam"] = format_malayalam_samam
    latex_jinja_env.filters["format_malayalam_samam_text"] = format_malayalam_samam_text
    latex_jinja_env.filters["format_samam_nometa_text"] = format_samam_nometa_text
    latex_jinja_env.filters["split_rik_lines"] = split_rik_lines_text
    latex_jinja_env.filters["replacecolon"] = replacecolon
    latex_jinja_env.filters["clean_toc_title"] = clean_toc_title
    
    # HTML Jinja environment (uses same LaTeX-style delimiters for consistency)
    html_jinja_env = jinja2.Environment(
    block_start_string = r'\BLOCK{',
    block_end_string = '}',
    variable_start_string = r'\VAR{',
    variable_end_string = '}',
    comment_start_string = r'\#{',
    comment_end_string = '}',
    line_statement_prefix = '%-',
    line_comment_prefix = '%#',
    trim_blocks = True,
    lstrip_blocks=True,
    autoescape = False,
    loader = jinja2.FileSystemLoader(os.path.abspath('.')),
    extensions=['jinja2.ext.loopcontrols']
    )
    html_jinja_env.filters["format_mantra_sets_html"] = format_mantra_sets_html
    html_jinja_env.filters["format_rik_only_html"] = format_rik_only_html
    html_jinja_env.filters["format_samam_only_html"] = format_samam_only_html
    html_jinja_env.filters["format_rik_nometa_html"] = format_rik_nometa_html
    html_jinja_env.filters["format_samam_nometa_html"] = format_samam_nometa_html
    html_jinja_env.filters["escape_for_html"] = escape_for_html
    html_jinja_env.filters["replacecolon"] = replacecolon
    html_jinja_env.filters["reset_html_footnote_counter"] = reset_html_footnote_counter
    html_jinja_env.filters["render_section_footnotes"] = render_section_footnotes
    html_jinja_env.filters["clean_toc_title"] = clean_toc_title

    # Load input JSON data
    ts_string_Devanagari = Path(input_file).read_text(encoding="utf-8")
    data_Devanagari = json.loads(ts_string_Devanagari)
    
    # Extract metadata for cascading versioning
    meta = data_Devanagari.get('meta', {})
    jsv_version = meta.get('version')
    # Use actual generation time instead of cascading from JSON
    generated_at = get_generated_metadata()['generated_at']
    if jsv_version:
        print(f"[INFO] Using cascading Version {jsv_version} (Final Generation: {generated_at})")
    
    # --- MALAYALAM SCRIPT MODE (Phase 1 Samam-only pilot) ---
    script = args.script
    if script == 'malayalam':
        from malayalam.ml_text import transform_ast
        from malayalam.ml_transliterate import devanagari_to_malayalam
        data_Devanagari, ml_warnings, ml_stats = transform_ast(data_Devanagari)
        print(f"[INFO] Malayalam script mode: Full Samhita "
              f"({ml_stats['marked_words']} marked words, {len(ml_warnings)} warnings)")
        # Transliterate supersection and section titles to Malayalam
        for ss_key, ss_data in data_Devanagari.get('supersection', {}).items():
            if ss_data.get('supersection_title'):
                try:
                    ss_data['supersection_title'] = devanagari_to_malayalam(ss_data['supersection_title'])
                except Exception:
                    pass
            for sec_key, sec_data in ss_data.get('sections', {}).items():
                if sec_key != 'count' and sec_data.get('section_title'):
                    try:
                        sec_data['section_title'] = devanagari_to_malayalam(sec_data['section_title'])
                    except Exception:
                        pass

    supersections = data_Devanagari.get('supersection', {})
    supersections = sanitize_data_structure(supersections)
    closing_mantras = data_Devanagari.get('closing_mantras', [])
    
    # Pre-processing section titles (if needed)
    for ss_key, ss_data in supersections.items():
        for sec_key, sec_data in ss_data.get('sections', {}).items():
            if sec_key == 'count': continue
            # Keep original title without prepended continuous numbering
            pass
    
    # Generate Summary Table
    summary_table = []
    total_riks = 0
    total_samams = 0
    
    for ss_key, ss_data in supersections.items():
        patha_name = ss_data.get('supersection_title', '').replace('॥', '').strip()
        patha_riks = 0
        patha_samams = 0
        khanda_rows = []
        for sec_key, sec_data in ss_data.get('sections', {}).items():
            if sec_key == 'count': continue
            khanda_name = sec_data.get('section_title', '').replace('॥', '').replace(':', 'ः').strip()
            
            seen_riks = set()
            samam_count = 0
            
            # Smart count: only count if displayable text exists
            for sub_key, sub_data in sec_data.get('subsections', {}).items():
                rik_text = sub_data.get('rik_text', '').strip()
                rik_ids = sub_data.get('rik_ids', [])
                
                # Only count Rik if there is Rik text to display
                if rik_text:
                    if rik_ids:
                        seen_riks.update(rik_ids)
                    else:
                        r_id = sub_data.get('rik_id')
                        if r_id is not None:
                            seen_riks.add(r_id)
                
                # Samam count logic
                sub_samam_count = 0
                has_samam_text = False
                for ms in sub_data.get('corrected-mantra_sets', []):
                    mantra = ms.get('corrected-mantra', '')
                    if mantra.strip():
                        has_samam_text = True
                    # Count all ॥ N ॥ markers
                    m_markers = re.findall(r'॥\s*[०-९]+\s*॥', mantra)
                    if m_markers:
                        sub_samam_count += len(m_markers)
                
                # If no markers found but mantra sets exist, count as 1 if there's text
                if sub_samam_count == 0 and has_samam_text:
                    sub_samam_count = 1
                
                samam_count += sub_samam_count
                    
            # Total aggregation format for section headers
            sec_riks = len(seen_riks)
            
            # Summary table row generation
            if sec_riks > 0 or samam_count > 0:
                if khanda_name:
                    khanda_rows.append({
                        'khanda': khanda_name,
                        'riks': to_devanagari_numeral(sec_riks),
                        'samams': to_devanagari_numeral(samam_count)
                    })
                patha_riks += sec_riks
                patha_samams += samam_count
                total_riks += sec_riks
                total_samams += samam_count

            count_parts = []
            if script == 'malayalam':
                if sec_riks > 0 and samam_count > 0:
                    count_parts.append(f"ऋ-{sec_riks}")
                    count_parts.append(f"സാ-{samam_count}")
                elif sec_riks > 0:
                    count_parts.append(str(sec_riks))
                elif samam_count > 0:
                    count_parts.append(str(samam_count))
                else:
                    count_parts.append("0")
            else:
                if sec_riks > 0 and samam_count > 0:
                    count_parts.append(f"ऋ-{to_devanagari_numeral(sec_riks)}")
                    count_parts.append(f"सा-{to_devanagari_numeral(samam_count)}")
                elif sec_riks > 0:
                    count_parts.append(to_devanagari_numeral(sec_riks))
                elif samam_count > 0:
                    count_parts.append(to_devanagari_numeral(samam_count))
                else:
                    count_parts.append("०")
            
            sec_data['Count'] = ", ".join(count_parts) if khanda_name else ""
        
        # Add total count for the supersection using similar combined logic
        ss_count_parts = []
        if script == 'malayalam':
            if patha_riks > 0 and patha_samams > 0:
                ss_count_parts.append(f"ऋ-{patha_riks}")
                ss_count_parts.append(f"സാ-{patha_samams}")
            elif patha_riks > 0:
                ss_count_parts.append(str(patha_riks))
            else:
                ss_count_parts.append(str(patha_samams))
        else:
            if patha_riks > 0 and patha_samams > 0:
                ss_count_parts.append(f"ऋ-{to_devanagari_numeral(patha_riks)}")
                ss_count_parts.append(f"सा-{to_devanagari_numeral(patha_samams)}")
            elif patha_riks > 0:
                ss_count_parts.append(to_devanagari_numeral(patha_riks))
            else:
                ss_count_parts.append(to_devanagari_numeral(patha_samams))
            
        ss_data['Count'] = ", ".join(ss_count_parts)
        
        if khanda_rows:
            summary_table.append({
                'patha': patha_name,
                'patha_riks': to_devanagari_numeral(patha_riks),
                'patha_samams': to_devanagari_numeral(patha_samams),
                'khandas': khanda_rows
            })
                
    total_riks_dev = to_devanagari_numeral(total_riks)
    total_samams_dev = to_devanagari_numeral(total_samams)
    
    # Define Sanskrit title based on type (for PDF/html generation)
    # Priority: CLI > Config Type > JSON Meta > Default
    doc_title_sa = args.title or type_settings.get('doc_title')
    
    if not doc_title_sa:
        doc_title_sa = data_Devanagari.get('meta', {}).get('title')
        
    summary_title_sa = type_settings.get('summary_title')
    
    if not doc_title_sa:
        if mode_type == 'aaranam':
            doc_title_sa = "जैमिनीय साम आरण्य गानम्"
            summary_title_sa = "आरण्यम् सङ्ख्या"
        elif mode_type == 'collection':
            doc_title_sa = "जैमिनीय साम सूक्त माला"
            summary_title_sa = "सूक्तम् सङ्ख्या"
        else:
            doc_title_sa = "जैमिनीय साम संहिता"
            summary_title_sa = "संहिता सङ्ख्या"
    
    current_os = platform.system()

    # Malayalam script: transliterate the title on the title page
    if script == 'malayalam' and doc_title_sa:
        from malayalam.ml_transliterate import devanagari_to_malayalam
        try:
            doc_title_sa = devanagari_to_malayalam(doc_title_sa)
        except Exception:
            pass
    
    print(f"Processing {input_file} in '{output_mode}' mode...")
    print(f"Document Title: {doc_title_sa}")
    
    # Procedures are loaded from JSON's procedure_ref field (injected by generate_json.py --procedures)
    # No backward compatibility with prayoga_index.yaml
    prayoga_dir = Path("data/input/prayoga")
    procedures = {}
    
    for super_key, supersection in supersections.items():
        for section_key, section in supersection.get('sections', {}).items():
            if section_key == 'count': continue
            for subsection_key, subsection in section.get('subsections', {}).items():
                # Only include procedures that are explicitly referenced in the JSON
                if subsection.get('procedure_ref'):
                    procedure_ref = subsection['procedure_ref']
                    file_path = procedure_ref.get('file', '')
                    if file_path and file_path not in procedures:
                        full_md_path = prayoga_dir / file_path
                        if full_md_path.exists():
                            with open(full_md_path, 'r', encoding='utf-8') as f:
                                md_content = f.read()
                            if md_content.startswith('---'):
                                parts = md_content.split('---', 2)
                                if len(parts) >= 3:
                                    md_content = parts[2].strip()
                            latex_content = md_content.replace('_', '\\_').replace('&', '\\&').replace('%', '\\%').replace('$', '\\$')
                            latex_content = re.sub(r'(?m)^### (.*?)$', r'\\subsubsection*{\1}', latex_content)
                            latex_content = re.sub(r'(?m)^## (.*?)$', r'\\subsection*{\1}', latex_content)
                            latex_content = re.sub(r'(?m)^# (.*?)$', r'\\section*{\1}', latex_content)
                            latex_content = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', latex_content)
                            latex_content = re.sub(r'\*(.*?)\*', r'\\textit{\1}', latex_content)
                            latex_content = re.sub(r'(?m)^- (.*?)$', r'$\\bullet$ \1\n\n', latex_content)
                            
                            procedures[file_path] = {
                                'slug': Path(file_path).stem,
                                'title': procedure_ref.get('title', 'विधिः'),
                                'latex_content': latex_content
                            }
    
    prayogas_list = list(procedures.values())

    doc_family = 'Malayalam' if script == 'malayalam' else 'Devanagari'

    # Template selection (Malayalam script uses its own Samam-only templates)
    if script == 'malayalam':
        template_file_src = templateFile_Malayalam
        text_template_file_src = f"{text_template_dir}/Malayalam_main.template"
        html_template_file_src = f"{html_template_dir}/Malayalam_main_html.template"
        pdf_font = "NotoSerifMalayalam"
        html_font = "Noto Serif Malayalam"
    else:
        template_file_src = templateFile_Devanagari
        text_template_file_src = text_templateFile_Devanagari
        html_template_file_src = html_templateFile_Devanagari

    if output_mode == 'combined':
        # Default: Combined output (Rik + Samam together)
        template_file = latex_jinja_env.get_template(template_file_src)
        text_template_file = latex_jinja_env.get_template(text_template_file_src)
        html_template_file = html_jinja_env.get_template(html_template_file_src) if html_template_file_src else None
        
        CreatePdf(template_file, f"{file_prefix}", doc_family, supersections, prayogas=prayogas_list, current_os=current_os, output_mode='combined', font_family=pdf_font, doc_title_sa=doc_title_sa, pdf_color_mode=pdf_color_mode, closing_mantras=closing_mantras, summary_table=summary_table, total_riks=total_riks_dev, total_samams=total_samams_dev, summary_title=summary_title_sa, toc_level=toc_level, has_riks=total_riks > 0, has_samams=total_samams > 0, output_dir_override=out_dir, name_override=out_name, jsv_version=jsv_version, generated_at=generated_at)
        CreateTextFile(text_template_file, f"{file_prefix}", doc_family, supersections, output_mode='combined', doc_title_sa=doc_title_sa, closing_mantras=closing_mantras, toc_level=toc_level, output_dir_override=out_dir, name_override=out_name, jsv_version=jsv_version, generated_at=generated_at)
        CreateHtmlFile(html_template_file, f"{file_prefix}", doc_family, supersections, html_font=html_font, output_mode='combined', doc_title_sa=doc_title_sa, closing_mantras=closing_mantras, summary_table=summary_table, total_riks=total_riks_dev, total_samams=total_samams_dev, summary_title=summary_title_sa, toc_level=toc_level, has_riks=total_riks > 0, has_samams=total_samams > 0, output_dir_override=out_dir, name_override=out_name, jsv_version=jsv_version, generated_at=generated_at)
        print("Success! Generated combined output files.")
        
    elif output_mode == 'separate':
        # Separate mode: Generate Rik-only and Samam-only files (with metadata, jsv_version=jsv_version, generated_at=generated_at)
        template_file = latex_jinja_env.get_template(template_file_src)
        text_template_file = latex_jinja_env.get_template(text_template_file_src)
        html_template_file = html_jinja_env.get_template(html_template_file_src) if html_template_file_src else None
        
        # Rik-only output: Pass output_mode='rik' to template
        print("Generating Rik-only output (with metadata)...")
        final_out_name = f"{out_name}_Rik" if out_name else "Rik"
        CreatePdf(template_file, f"Rik", doc_family, supersections, prayogas=prayogas_list, current_os=current_os, output_mode='rik', font_family=pdf_font, doc_title_sa=doc_title_sa, pdf_color_mode=pdf_color_mode, closing_mantras=closing_mantras, summary_table=summary_table, total_riks=total_riks_dev, total_samams=total_samams_dev, summary_title=summary_title_sa, toc_level=toc_level, has_riks=total_riks > 0, has_samams=total_samams > 0, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at)
        CreateTextFile(text_template_file, f"Rik", doc_family, supersections, output_mode='rik', doc_title_sa=doc_title_sa, closing_mantras=closing_mantras, toc_level=toc_level, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at)
        CreateHtmlFile(html_template_file, f"Rik", doc_family, supersections, html_font=html_font, output_mode='rik', doc_title_sa=doc_title_sa, closing_mantras=closing_mantras, summary_table=summary_table, total_riks=total_riks_dev, total_samams=total_samams_dev, summary_title=summary_title_sa, toc_level=toc_level, has_riks=total_riks > 0, has_samams=total_samams > 0, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at)
        
        # Samam-only output: Pass output_mode='samam' to template
        print("Generating Samam-only output (with metadata)...")
        final_out_name = f"{out_name}_Samam" if out_name else "Samam"
        CreatePdf(template_file, f"Samam", doc_family, supersections, prayogas=prayogas_list, current_os=current_os, output_mode='samam', font_family=pdf_font, doc_title_sa=doc_title_sa, pdf_color_mode=pdf_color_mode, closing_mantras=closing_mantras, summary_table=summary_table, total_riks=total_riks_dev, total_samams=total_samams_dev, summary_title=summary_title_sa, toc_level=toc_level, has_riks=total_riks > 0, has_samams=total_samams > 0, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at)
        CreateTextFile(text_template_file, f"Samam", doc_family, supersections, output_mode='samam', doc_title_sa=doc_title_sa, closing_mantras=closing_mantras, toc_level=toc_level, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at)
        CreateHtmlFile(html_template_file, f"Samam", doc_family, supersections, html_font=html_font, output_mode='samam', doc_title_sa=doc_title_sa, closing_mantras=closing_mantras, summary_table=summary_table, total_riks=total_riks_dev, total_samams=total_samams_dev, summary_title=summary_title_sa, toc_level=toc_level, has_riks=total_riks > 0, has_samams=total_samams > 0, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at)
        
        print("Success! Generated separate Rik and Samam output files.")
        
    else:
        # Nometa mode: Generate Rik-only and Samam-only files (without metadata, jsv_version=jsv_version, generated_at=generated_at)
        template_file = latex_jinja_env.get_template(template_file_src)
        text_template_file = latex_jinja_env.get_template(text_template_file_src)
        html_template_file = html_jinja_env.get_template(html_template_file_src) if html_template_file_src else None
        
        # Rik-only output (no metadata, jsv_version=jsv_version, generated_at=generated_at): Pass output_mode='rik_nometa' to template
        print("Generating Rik-only output (without metadata)...")
        final_out_name = f"{out_name}_Rik_NoMeta" if out_name else "Rik_NoMeta"
        CreatePdf(template_file, f"Rik_NoMeta", doc_family, supersections, current_os=current_os, output_mode='rik_nometa', font_family=pdf_font, doc_title_sa=doc_title_sa, pdf_color_mode=pdf_color_mode, closing_mantras=closing_mantras, summary_table=summary_table, total_riks=total_riks_dev, total_samams=total_samams_dev, summary_title=summary_title_sa, toc_level=toc_level, has_riks=total_riks > 0, has_samams=total_samams > 0, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at)
        CreateTextFile(text_template_file, f"Rik_NoMeta", doc_family, supersections, output_mode='rik_nometa', doc_title_sa=doc_title_sa, closing_mantras=closing_mantras, toc_level=toc_level, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at)
        CreateHtmlFile(html_template_file, f"Rik_NoMeta", doc_family, supersections, html_font=html_font, output_mode='rik_nometa', doc_title_sa=doc_title_sa, closing_mantras=closing_mantras, summary_table=summary_table, total_riks=total_riks_dev, total_samams=total_samams_dev, summary_title=summary_title_sa, toc_level=toc_level, has_riks=total_riks > 0, has_samams=total_samams > 0, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at)
        
        # Samam-only output (no metadata, jsv_version=jsv_version, generated_at=generated_at): Pass output_mode='samam_nometa' to template
        print("Generating Samam-only output (without metadata)...")
        final_out_name = f"{out_name}_Samam_NoMeta" if out_name else "Samam_NoMeta"
        CreatePdf(template_file, f"Samam_NoMeta", doc_family, supersections, current_os=current_os, output_mode='samam_nometa', font_family=pdf_font, doc_title_sa=doc_title_sa, pdf_color_mode=pdf_color_mode, closing_mantras=closing_mantras, summary_table=summary_table, total_riks=total_riks_dev, total_samams=total_samams_dev, summary_title=summary_title_sa, toc_level=toc_level, has_riks=total_riks > 0, has_samams=total_samams > 0, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at)
        CreateTextFile(text_template_file, f"Samam_NoMeta", doc_family, supersections, output_mode='samam_nometa', doc_title_sa=doc_title_sa, closing_mantras=closing_mantras, toc_level=toc_level, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at)
        CreateHtmlFile(html_template_file, f"Samam_NoMeta", doc_family, supersections, html_font=html_font, output_mode='samam_nometa', doc_title_sa=doc_title_sa, closing_mantras=closing_mantras, summary_table=summary_table, total_riks=total_riks_dev, total_samams=total_samams_dev, summary_title=summary_title_sa, toc_level=toc_level, has_riks=total_riks > 0, has_samams=total_samams > 0, output_dir_override=out_dir, name_override=final_out_name, jsv_version=jsv_version, generated_at=generated_at)
        
        print("Success! Generated separate Rik and Samam output files without metadata.")

if __name__ == "__main__":
    main()