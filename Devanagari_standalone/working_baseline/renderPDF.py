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
from requests.models import PreparedRequest
import grapheme

# --- New import for utility functions ---
from convert_txt_to_json_1 import (
    combine_halants, combine_ardhaksharas,
    my_encodeURL, my_format,
    replacecolon, normalize_and_trim,
    parse_mantra_for_latex, 
    sanitize_data_structure
)
# --- End new import ---

# ----------------------------------------------------
# DEVANAGARI NUMERAL CONVERSION
# ----------------------------------------------------
HTML_FOOTNOTE_COUNTER = 0

def to_devanagari_numeral(num):
    """Convert Arabic numerals to Devanagari numerals."""
    if num is None:
        return ""
    mapping = {'0': '०', '1': '१', '2': '२', '3': '३', '4': '४',
               '5': '५', '6': '६', '7': '७', '8': '८', '9': '९'}
    return ''.join(mapping.get(c, c) for c in str(num))

# ----------------------------------------------------
# 1. NEW UTILITY: Accent Replacements (RAISED ZERO-WIDTH)
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
    
    replacements = [
        # Swarita (Vertical line above) - all accents at same level
        ('(1)', r'\makebox[0pt][l]{\raisebox{0.6ex}{\accentmark{12}{\char"0951}}}'),  
        
        # Anudatta (Horizontal line below) - same level  
        ('(2)', r'\makebox[0pt][l]{\raisebox{0.6ex}{\accentmark{15}{\char"1CD2}}}'),  
        
        # Kampa (Curve) - same level
        ('(3)', r'\makebox[0pt][l]{\raisebox{0.6ex}{\accentmark{12}{\char"1CF8}}}'),  
        
        # Trikampa - same level
        ('(4)', r'\makebox[0pt][l]{\raisebox{0.6ex}{\accentmark{12}{\char"1CF9}}}'),  
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
    that were prone to visual overlap with AdiShila Vedic font.
    
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

# ----------------------------------------------------
# FOOTNOTE PROCESSING UTILITIES
# ----------------------------------------------------
def process_footnotes_latex(text, footnotes_dict):
    """
    Replace (s1), (s2) markers with LaTeX \\footnote{} commands.
    LaTeX automatically handles page-relative numbering.
    
    Args:
        text: The text containing footnote markers like (s1), (s2)
        footnotes_dict: Dictionary mapping marker to footnote text, e.g. {"s1": "footnote text"}
    
    Returns:
        Text with markers replaced by LaTeX footnote commands
    """
    if not footnotes_dict:
        return text
    
    for marker, footnote_text in footnotes_dict.items():
        pattern = rf'\({re.escape(marker)}\)'
        # LaTeX footnote command - will be auto-numbered per page
        replacement = f'\\\\footnote{{{footnote_text}}}'
        text = re.sub(pattern, replacement, text)
    
    return text

def process_footnotes_html(text, footnotes_dict, global_counter=0):
    """
    Replace (s1), (s2) markers with HTML superscript links.
    Uses continuous numbering across the document.
    
    Args:
        text: The text containing footnote markers like (s1), (s2)
        footnotes_dict: Dictionary mapping marker to footnote text
        global_counter: Current global footnote counter for continuous numbering
    
    Returns:
        Tuple of (processed_text, footnotes_list, updated_counter)
        footnotes_list contains (number, text) tuples for display at end
    """
    if not footnotes_dict:
        return text, [], global_counter
    
    footnotes_list = []
    
    # regex to find (sX)
    matches = list(set(re.findall(r'\(s\d+\)', text))) # set to unique, though usually one per token
    # Sort matches to process in order s1, s2... to maintain consistency if multiple in one block
    matches.sort(key=lambda x: int(x[2:-1]))
    
    for marker_full in matches:
        marker = marker_full[1:-1] # strip ( ) -> s1
        if marker in footnotes_dict:
             global_counter += 1
             footnote_text = footnotes_dict[marker]
             devanagari_num = to_devanagari_numeral(global_counter)
             
             # Replace this specific marker occurrence
             replacement = f'<sup class="footnote-ref"><a href="#fn-{global_counter}" id="fnref-{global_counter}">{devanagari_num}</a></sup>'
             text = text.replace(marker_full, replacement)
             
             footnotes_list.append((global_counter, devanagari_num, footnote_text))

    return text, footnotes_list, global_counter

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
    text = text.replace('।', r' । ')

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

def CreateCompilation():
    outputdir="outputs/md/Compilation"
    templateFileName_md="templates/PanchasatCompile_main.md"
    templateFileName_tex="templates/PanchasatCompile_main.tex"
    exit_code=0
    ts_string = Path("TS_withPadaGhanaJataiKrama.json").read_text(encoding="utf-8")
    parseTree = json.loads(ts_string)
    for kanda in parseTree['TS']['Kanda']:
        kandaInfo=kanda['id']
        for prasna in kanda['Prasna']:
            prasnaInfo=prasna['id']
            CreateMd(templateFileName_md,f"TS_{kandaInfo}_{prasnaInfo}","Compilation",prasna)
                       
def CreatePdf (templateFileName,name,DocfamilyName,data, current_os="Windows", output_mode="combined"):
    data=escape_for_latex(data)
    
    outputdir="output_text"
    logdir=f"{outputdir}/logs"
    exit_code=0
    
    TexFileName=f"{name}_{DocfamilyName}_Unicode.tex"
    PdfFileName=f"{name}_{DocfamilyName}_Unicode.pdf"
    TocFileName=f"{name}_{DocfamilyName}_Unicode.toc"
    LogFileName=f"{name}_{DocfamilyName}_Unicode.log"
    template = templateFileName
    outputdir = f"{outputdir}/pdf/{DocfamilyName}"  # Use DocfamilyName for directory
    Path(outputdir).mkdir(parents=True, exist_ok=True)
    Path(logdir).mkdir(parents=True, exist_ok=True)
    document = template.render(supersections=data, os=current_os, output_mode=output_mode)
    

    tmpdirname="."
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpfilename=f"{tmpdirname}/{TexFileName}"

        with open(tmpfilename,"w",encoding="utf-8") as f:
            f.write(document)
        
        # Uncomment to run latexmk
        # result = subprocess.Popen(["latexmk","-lualatex", "--interaction=nonstopmode","--silent",tmpfilename],cwd=tmpdirname)
        # result.wait()
        
        src_pdf_file=Path(f"{tmpdirname}/{PdfFileName}")
        dst_pdf_file=Path(f"{outputdir}/{PdfFileName}")
        src_log_file=Path(f"{tmpdirname}/{LogFileName}")
        dst_log_file=Path(f"{logdir}/{LogFileName}")
        src_tex_file=Path(f"{tmpdirname}/{TexFileName}")
        dst_tex_file=Path(f"{outputdir}/{TexFileName}")
        
        path = Path(src_tex_file)
        if path.is_file():
            if dst_tex_file.exists():
                dst_tex_file.unlink()
            src_tex_file.rename(dst_tex_file)  
        path = Path(src_pdf_file)
        if path.is_file():
            if dst_pdf_file.exists():
                dst_pdf_file.unlink()
            src_pdf_file.rename(dst_pdf_file)
        path = Path(src_log_file)
        if path.is_file():
            if dst_log_file.exists():
                dst_log_file.unlink()
            src_log_file.rename(dst_log_file)

    return exit_code

def CreateTextFile (templateFileName,name,DocfamilyName,data, output_mode="combined"):
    data=escape_for_latex(data)
    
    outputdir="output_text"
    logdir=f"{outputdir}/logs"
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
    document = template.render(supersections=data, output_mode=output_mode)
    

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
            new_data[key] = escape_for_latex(data[key])
        return new_data
    elif isinstance(data, list):
        return [escape_for_latex(item) for item in data]
    elif isinstance(data, str):
        latex_special_chars = {
            "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
            "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\^{}",
            "\\": r"\textbackslash{}", "\n": "\\newline%\n", "-": r"{-}",
            "\xA0": "~", "[": r"{[}", "]": r"{]}",
        }
        return "".join([latex_special_chars.get(c, c) for c in data])

    return data

def format_mantra_sets(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None):
    
    formatted_output = []
    
    # --- DATA EXTRACTION ---
    current_rik_id = subsection.get('rik_id')
    string_1 = subsection.get('rik_metadata', '')
    string_2 = subsection.get('rik_text', '')
    string_3 = subsection.get('saman_metadata', '')
    
    # Determine if we should show rik_metadata and rik_text (only when rik_id changes)
    show_rik_info = (prev_rik_id is None) or (current_rik_id != prev_rik_id)
    
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
        formatted_output.append(f"\\addcontentsline{{toc}}{{subsection}}{{{samam_header_only}}}")
        formatted_output.append(f"\\index{{{index_title}}}")

    # 2. String 1: Rik Metadata (Plain Centered) - Only if rik_id changed
    # COLOR: BLUE
    if string_1 and show_rik_info:
        s1 = format_dandas(string_1)
        s1 = process_footnotes_latex(s1, subsection.get('footnotes', {}))
        formatted_output.append(f"{{\\centering \\textcolor{{AccentPurple}}{{{s1}}} \\par}}")
        formatted_output.append(r"\vspace{0.6em}")

    # 3. String 2: Rik Text (With Vedic Accents, Upright) - Only if rik_id changed
    # COLOR: BLUE
    if string_2 and show_rik_info:
        # Step A: Remove Spaces (Samhita Mode)
        s2 = remove_mantra_spaces(string_2)
        # Step B: Handle Consecutive Accent Kerning
        s2 = handle_consecutive_accents(s2)
        # Step C: Replace Accents with LaTeX commands (with adjusted sizes)
        s2 = replace_accents(s2)
        # Process Footnotes in Rik Text
        s2 = process_footnotes_latex(s2, subsection.get('footnotes', {}))
        # Step D: Format Dandas (Spaces around dandas only)
        s2 = format_dandas(s2)
        # Output: Upright (not italics)
        formatted_output.append(f"{{\\centering \\textcolor{{blue}}{{{s2}}} \\par}}")
        formatted_output.append(r"\vspace{0.8em}")

    # 4. Combined Header: || Subsection header || || samam_metadata ||
    header_part = display_sub_title.strip()
    header_part = f"\\textcolor{{AccentGreen}}{{{header_part}}}"  
    
    # COLOR: Samam Metadata -> BROWN
    meta_part = format_dandas(string_3).strip()
    meta_part = process_footnotes_latex(meta_part, subsection.get('footnotes', {}))
    if meta_part:
        meta_part = f"\\textcolor{{AccentPurple}}{{{meta_part}}}"
    
    combined_header = ""
    if header_part and meta_part:
        combined_header = f"{header_part} \\quad {meta_part}"
    elif header_part:
        combined_header = header_part
    elif meta_part:
        combined_header = meta_part
        
    if combined_header:
         formatted_output.append(f"{{\\centering \\textbf{{{combined_header}}} \\par}}")

    formatted_output.append(r"\nopagebreak")                
    formatted_output.append(r"\vspace{0.5em}")
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
            
            # --- FOOTNOTE PROCESSING FOR MANTRA TOKENS ---
            # Extract footnotes from text_part if present
            # We look for (sX) patterns
            found_footnotes = []
            if '(' in text_part and ')' in text_part:
                # Find all markers
                markers = re.findall(r'\((s\d+)\)', text_part)
                footnote_data = subsection.get('footnotes', {})
                for marker in markers:
                    if marker in footnote_data:
                        found_footnotes.append(footnote_data[marker])
                        # Remove marker from text_part so it doesn't go into stack
                        text_part = text_part.replace(f'({marker})', '')
            
            # Append accumulated footnotes to extras
            for fn_text in found_footnotes:
                extras += f"\\footnote{{{fn_text}}}"

            if swara_part:
                clean_swara = swara_part.replace('{', '').replace('}', '')
                if len(clean_swara) > 1:
                    stack = f"\\stackleft{{{text_part}}}{{{swara_part}}}\\hspace{{0.05em}}"
                else:
                    stack = f"\\stackcenter{{{text_part}}}{{{swara_part}}}"
            else:
                stack = text_part
            
                      
            token = stack + extras

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
# RIK-ONLY FORMATTING (for separate output mode)
# ----------------------------------------------------
def format_rik_only(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None):
    """
    Format only Rik content (rik_metadata and rik_text) for separate output mode.
    Skips all Samam-related content.
    """
    formatted_output = []
    
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
        formatted_output.append(f"\\addcontentsline{{toc}}{{subsection}}{{{rik_id_display}}}")

    # Rik Metadata
    if string_1:
        s1 = format_dandas(string_1)
        # Apply footnotes
        s1 = process_footnotes_latex(s1, subsection.get('footnotes', {}))
        formatted_output.append(f"{{\\centering \\textcolor{{AccentPurple}}{{{s1}}} \\par}}")
        formatted_output.append(r"\vspace{0.6em}")

    # Rik Text (with Vedic Accents)
    if string_2:
        s2 = remove_mantra_spaces(string_2)
        s2 = handle_consecutive_accents(s2)
        s2 = replace_accents(s2)
        # Apply footnotes
        s2 = process_footnotes_latex(s2, subsection.get('footnotes', {}))
        s2 = format_dandas(s2)
        formatted_output.append(f"{{\\centering \\textcolor{{blue}}{{{s2}}} \\par}}")
        formatted_output.append(r"\vspace{0.8em}")

    return "\n\n".join(formatted_output)


# ----------------------------------------------------
# SAMAM-ONLY FORMATTING (for separate output mode)
# ----------------------------------------------------
def format_samam_only(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None):
    """
    Format only Samam content (header, saman_metadata, mantra text) for separate output mode.
    Skips all Rik-related content.
    """
    formatted_output = []
    
    string_3 = subsection.get('saman_metadata', '')
    
    # Clean titles
    display_sub_title = re.sub(r'^([|॥]+)\s*', r'\1 ', subsection_title) if subsection_title else ""
    index_title = re.sub(r'[|॥]', '', subsection_title).strip() if subsection_title else ""

    # Page Break / Indexing
    formatted_output.append(r"\par\filbreak")
    formatted_output.append(r"\phantomsection")
    if subsection_title:
        formatted_output.append(f"\\addcontentsline{{toc}}{{subsection}}{{{display_sub_title}}}")
        formatted_output.append(f"\\index{{{index_title}}}")

    # Combined Header: Subsection header + samam_metadata
    header_part = display_sub_title.strip()
    header_part = f"\\textcolor{{AccentGreen}}{{{header_part}}}" if header_part else ""
    
    meta_part = format_dandas(string_3).strip()
    meta_part = process_footnotes_latex(meta_part, subsection.get('footnotes', {}))
    if meta_part:
        meta_part = f"\\textcolor{{AccentPurple}}{{{meta_part}}}"
    
    combined_header = ""
    if header_part and meta_part:
        combined_header = f"{header_part} \\quad {meta_part}"
    elif header_part:
        combined_header = header_part
    elif meta_part:
        combined_header = meta_part
        
    if combined_header:
        formatted_output.append(f"{{\\centering \\textbf{{{combined_header}}} \\par}}")

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
            
            # --- FOOTNOTE PROCESSING FOR MANTRA TOKENS ---
            # Extract footnotes from text_part if present
            # We look for (sX) patterns
            found_footnotes = []
            if '(' in text_part and ')' in text_part:
                # Find all markers
                markers = re.findall(r'\((s\d+)\)', text_part)
                footnote_data = subsection.get('footnotes', {})
                for marker in markers:
                    if marker in footnote_data:
                        found_footnotes.append(footnote_data[marker])
                        # Remove marker from text_part so it doesn't go into stack
                        text_part = text_part.replace(f'({marker})', '')
            
            # Append accumulated footnotes to extras
            for fn_text in found_footnotes:
                extras += f"\\footnote{{{fn_text}}}"

            if swara_part:
                clean_swara = swara_part.replace('{', '').replace('}', '')
                if len(clean_swara) > 1:
                    stack = f"\\stackleft{{{text_part}}}{{{swara_part}}}\\hspace{{0.05em}}"
                else:
                    stack = f"\\stackcenter{{{text_part}}}{{{swara_part}}}"
            else:
                stack = text_part
                      
            token = stack + extras

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
    formatted_sets.append(f"#Start of Mantra Sets -- {subsection_title} ## DO NOT EDIT")
    for mantra in mantra_array:
        # Keep mantra content together - replace \newline% with single space or nothing
        clean_mantra = mantra.replace('\\newline%', '').replace('\\newline', '')
        formatted_sets.append(clean_mantra)
    formatted_sets.append(f"#End of Mantra Sets -- {subsection_title} ## DO NOT EDIT")
    return "\n".join(formatted_sets)


# ----------------------------------------------------
# RIK-ONLY TEXT FORMATTING (for separate output mode)
# ----------------------------------------------------
def format_rik_only_text(subsection, section_title, subsection_title, prev_rik_id=None):
    """Format only Rik content for plain text output."""
    formatted_output = []
    
    current_rik_id = subsection.get('rik_id')
    rik_metadata = subsection.get('rik_metadata', '')
    rik_text = subsection.get('rik_text', '')
    
    # Skip if no Rik content or if this Rik was already shown
    show_rik_info = (prev_rik_id is None) or (current_rik_id != prev_rik_id)
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
    
    for mantra in mantra_array:
        # Clean LaTeX formatting for plain text
        clean_mantra = mantra.replace('\\newline%', ' ')
        clean_mantra = clean_mantra.replace('\\newline', ' ')
        clean_mantra = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', clean_mantra)  # Remove \command{...}
        clean_mantra = re.sub(r'\\[a-zA-Z]+', '', clean_mantra)  # Remove \command
        clean_mantra = re.sub(r'\s+', ' ', clean_mantra).strip()  # Clean extra spaces
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

def format_dandas_html(text):
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

    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def replace_accents_html(text):
    """
    Replaces ASCII accent markers with Unicode Vedic accent characters for HTML.
    AdiShila Vedic font properly supports these characters.
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
    
    return text

def format_mantra_sets_html(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None):
    """
    Formats mantra data as HTML using table-based layout for word/swara stacking.
    Uses tables similar to existing HTML output in the project.
    Only renders rik_metadata and rik_text if rik_id differs from prev_rik_id.
    """
    global HTML_FOOTNOTE_COUNTER
    formatted_output = []
    collected_footnotes = []
    
    # --- DATA EXTRACTION ---
    current_rik_id = subsection.get('rik_id')
    string_1 = subsection.get('rik_metadata', '')
    string_2 = subsection.get('rik_text', '')
    string_3 = subsection.get('saman_metadata', '')
    footnote_data = subsection.get('footnotes', {})
    
    # Determine if we should show rik_metadata and rik_text (only when rik_id changes)
    show_rik_info = (prev_rik_id is None) or (current_rik_id != prev_rik_id)
    
    # Clean titles
    display_sub_title = re.sub(r'^([|॥]+)\s*', r'\1 ', subsection_title) if subsection_title else ''

    # 1. Rik Metadata - Only if rik_id changed
    if string_1 and show_rik_info:
        s1 = escape_for_html(string_1)
        s1 = format_dandas_html(s1)
        s1, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(s1, footnote_data, HTML_FOOTNOTE_COUNTER)
        collected_footnotes.extend(fnotes)
        formatted_output.append(f'<div class="rik-metadata">{s1}</div>')

    # 2. Rik Text (With accents) - Only if rik_id changed
    if string_2 and show_rik_info:
        s2 = remove_mantra_spaces(string_2)
        s2 = escape_for_html(s2)
        # Process footnotes
        s2, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(s2, footnote_data, HTML_FOOTNOTE_COUNTER)
        collected_footnotes.extend(fnotes)
        
        s2 = replace_accents_html(s2)
        s2 = format_dandas_html(s2)
        formatted_output.append(f'<div class="rik-text">{s2}</div>')

    # 3. Combined Header
    header_parts = []
    if display_sub_title:
        header_parts.append(f'<span class="header-title">{escape_for_html(display_sub_title)}</span>')
    if string_3:
        meta = escape_for_html(string_3)
        meta = format_dandas_html(meta)
        meta, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(meta, footnote_data, HTML_FOOTNOTE_COUNTER)
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
            text_part, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(text_part, footnote_data, HTML_FOOTNOTE_COUNTER)
            collected_footnotes.extend(fnotes)

            swara_part = escape_for_html(swara_part) if swara_part else '&nbsp;'
            
            # Create stacked word element
            word_html = f'<span class="mantra-word"><span class="mantra-text">{text_part}</span><span class="swara-text">{swara_part}</span></span>'
            word_elements.append(word_html)

        # Create verse div with flowing content
        if word_elements:
            verse_html = ''.join(word_elements)
            formatted_output.append(f'<div class="mantra-verse">{verse_html}</div>')

    # Append accumulated footnotes for this subsection
    if collected_footnotes:
        formatted_output.append('<hr class="footnote-separator"/>')
        formatted_output.append('<div class="footnote-section">')
        for num, display_num, text in collected_footnotes:
             formatted_output.append(f'<div class="footnote-item" id="fn-{num}"><sup class="footnote-ref">{display_num}</sup> {text}</div>')
        formatted_output.append('</div>')

    return '\n'.join(formatted_output)


# ----------------------------------------------------
# RIK-ONLY HTML FORMATTING (for separate output mode)
# ----------------------------------------------------
def format_rik_only_html(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None):
    """
    Format only Rik content (rik_metadata and rik_text) for HTML separate output mode.
    Skips all Samam-related content.
    """
    global HTML_FOOTNOTE_COUNTER
    formatted_output = []
    collected_footnotes = []
    footnote_data = subsection.get('footnotes', {})
    
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
    
    # Rik Metadata
    if string_1:
        s1 = escape_for_html(string_1)
        s1 = format_dandas_html(s1)
        s1, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(s1, footnote_data, HTML_FOOTNOTE_COUNTER)
        collected_footnotes.extend(fnotes)
        formatted_output.append(f'<div class="rik-metadata">{s1}</div>')

    # Rik Text (with accents)
    if string_2:
        s2 = remove_mantra_spaces(string_2)
        s2 = escape_for_html(s2)
        
        s2, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(s2, footnote_data, HTML_FOOTNOTE_COUNTER)
        collected_footnotes.extend(fnotes)
        
        s2 = replace_accents_html(s2)
        s2 = format_dandas_html(s2)
        formatted_output.append(f'<div class="rik-text">{s2}</div>')

    # Append accumulated footnotes
    # Append accumulated footnotes
    if collected_footnotes:
        formatted_output.append('<hr class="footnote-separator"/>')
        formatted_output.append('<div class="footnote-section">')
        for num, display_num, text in collected_footnotes:
             formatted_output.append(f'<div class="footnote-item" id="fn-{num}"><sup class="footnote-ref">{display_num}</sup> {text}</div>')
        formatted_output.append('</div>')

    return '\n'.join(formatted_output)


# ----------------------------------------------------
# SAMAM-ONLY HTML FORMATTING (for separate output mode)
# ----------------------------------------------------
def format_samam_only_html(subsection, supersection_title, section_title, subsection_title, footnote_dict={}, prev_rik_id=None):
    """
    Format only Samam content (header, saman_metadata, mantra text) for HTML separate output mode.
    Skips all Rik-related content.
    """
    global HTML_FOOTNOTE_COUNTER
    formatted_output = []
    collected_footnotes = []
    footnote_data = subsection.get('footnotes', {})
    
    string_3 = subsection.get('saman_metadata', '')
    
    # Clean titles
    display_sub_title = re.sub(r'^([|॥]+)\s*', r'\1 ', subsection_title) if subsection_title else ''

    # Combined Header: subsection title + samam metadata
    header_parts = []
    if display_sub_title:
        header_parts.append(f'<span class="header-title">{escape_for_html(display_sub_title)}</span>')
    if string_3:
        meta = escape_for_html(string_3)
        meta = format_dandas_html(meta)
        meta, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(meta, footnote_data, HTML_FOOTNOTE_COUNTER)
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
            
            text_part, fnotes, HTML_FOOTNOTE_COUNTER = process_footnotes_html(text_part, footnote_data, HTML_FOOTNOTE_COUNTER)
            collected_footnotes.extend(fnotes)

            swara_part = escape_for_html(swara_part) if swara_part else '&nbsp;'
            
            word_html = f'<span class="mantra-word"><span class="mantra-text">{text_part}</span><span class="swara-text">{swara_part}</span></span>'
            word_elements.append(word_html)

        if word_elements:
            verse_html = ''.join(word_elements)
            formatted_output.append(f'<div class="mantra-verse">{verse_html}</div>')

    # Append accumulated footnotes
    # Append accumulated footnotes
    if collected_footnotes:
        formatted_output.append('<hr class="footnote-separator"/>')
        formatted_output.append('<div class="footnote-section">')
        for num, display_num, text in collected_footnotes:
             formatted_output.append(f'<div class="footnote-item" id="fn-{num}"><sup class="footnote-ref">{display_num}</sup> {text}</div>')
        formatted_output.append('</div>')
            
    return '\n'.join(formatted_output)


def CreateHtmlFile(templateFileName, name, DocfamilyName, data, html_font="'AdiShila Vedic', 'Adishila SanVedic'", output_mode="combined"):
    """
    Creates an HTML file from the template and data.
    Similar to CreatePdf but outputs HTML instead.
    
    Args:
        html_font: Font family string for HTML output (e.g., "'AdiShila Vedic', 'Adishila SanVedic'")
        output_mode: 'combined', 'rik', or 'samam' for filtering content
    """
    outputdir = "output_text"
    exit_code = 0
    
    HtmlFileName = f"{name}_{DocfamilyName}_Unicode.html"
    template = templateFileName
    outputdir = f"{outputdir}/html/{DocfamilyName}"  # Use DocfamilyName for directory
    Path(outputdir).mkdir(parents=True, exist_ok=True)
    
    global HTML_FOOTNOTE_COUNTER
    HTML_FOOTNOTE_COUNTER = 0
    
    document = template.render(supersections=data, html_font=html_font, output_mode=output_mode)
    
    output_path = Path(f"{outputdir}/{HtmlFileName}")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(document)
    
    print(f"HTML file created: {output_path}")
    return exit_code


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Generate PDF, HTML, and Text from Vedic text JSON',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Output Modes:
  combined  - Single output with both Rik and Samam content (default)
  separate  - Two separate outputs: Rik-only and Samam-only

Examples:
  python renderPDF.py input.json
  python renderPDF.py input.json --output-mode separate
        """
    )
    parser.add_argument('input_file', nargs='?', default='corrections_003_out.json',
                        help='Input JSON file (default: corrections_003_out.json)')
    parser.add_argument('--output-mode', dest='output_mode',
                        choices=['combined', 'separate'], default='combined',
                        help='Output mode: combined (default) or separate')
    parser.add_argument('--pdf-font', dest='pdf_font', default='AdiShila Vedic',
                        help='Font for PDF output (default: AdiShila Vedic)')
    parser.add_argument('--html-font', dest='html_font', default="'AdiShila Vedic', 'Adishila SanVedic'",
                        help="Font for HTML output (default: 'AdiShila Vedic', 'Adishila SanVedic')")
    
    args = parser.parse_args()
    input_file = args.input_file
    output_mode = args.output_mode
    pdf_font = args.pdf_font
    html_font = args.html_font
    template_dir="pdf_templates"
    text_template_dir="text_templates"
    html_template_dir="html_templates"
    
    templateFile_Grantha=f"{template_dir}/Grantha_main.template"
    templateFile_Devanagari=f"{template_dir}/Devanagari_main.template"
    templateFile_Tamil=f"{template_dir}/Tamil_main.template"
    templateFile_Malayalam=f"{template_dir}/Malayalam_main.template"
    
    text_templateFile_Devanagari=f"{text_template_dir}/Devanagari_main.template"
    html_templateFile_Devanagari=f"{html_template_dir}/Devanagari_main_html.template"

    outputdir="output_text"
    logdir="pdf_logs"
    
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
    latex_jinja_env.filters["format_mantra_sets"] = format_mantra_sets
    latex_jinja_env.filters["format_mantra_sets_text"] = format_mantra_sets_text
    latex_jinja_env.filters["format_rik_only"] = format_rik_only
    latex_jinja_env.filters["format_samam_only"] = format_samam_only
    latex_jinja_env.filters["format_rik_only_text"] = format_rik_only_text
    latex_jinja_env.filters["format_samam_only_text"] = format_samam_only_text
    latex_jinja_env.filters["replacecolon"] = replacecolon
    
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
    html_jinja_env.filters["escape_for_html"] = escape_for_html
    html_jinja_env.filters["replacecolon"] = replacecolon

    # Load input JSON data
    ts_string_Devanagari = Path(input_file).read_text(encoding="utf-8")
    data_Devanagari = json.loads(ts_string_Devanagari)
    
    supersections = data_Devanagari.get('supersection', {})
    supersections = sanitize_data_structure(supersections)
    
    current_os = platform.system()
    
    print(f"Processing {input_file} in '{output_mode}' mode...")
    
    if output_mode == 'combined':
        # Default: Combined output (Rik + Samam together)
        template_file = latex_jinja_env.get_template(templateFile_Devanagari)
        text_template_file = latex_jinja_env.get_template(text_templateFile_Devanagari)
        html_template_file = html_jinja_env.get_template(html_templateFile_Devanagari)
        
        CreatePdf(template_file, f"Devanagari", "Devanagari", supersections, current_os=current_os, output_mode='combined')
        CreateTextFile(text_template_file, f"Devanagari", "Devanagari", supersections, output_mode='combined')
        CreateHtmlFile(html_template_file, f"Devanagari", "Devanagari", supersections, html_font=html_font, output_mode='combined')
        print("Success! Generated combined output files.")
        
    else:
        # Separate mode: Generate Rik-only and Samam-only files
        template_file = latex_jinja_env.get_template(templateFile_Devanagari)
        text_template_file = latex_jinja_env.get_template(text_templateFile_Devanagari)
        html_template_file = html_jinja_env.get_template(html_templateFile_Devanagari)
        
        # Rik-only output: Pass output_mode='rik' to template
        print("Generating Rik-only output...")
        CreatePdf(template_file, f"Rik", "Devanagari", supersections, current_os=current_os, output_mode='rik')
        CreateTextFile(text_template_file, f"Rik", "Devanagari", supersections, output_mode='rik')
        CreateHtmlFile(html_template_file, f"Rik", "Devanagari", supersections, html_font=html_font, output_mode='rik')
        
        # Samam-only output: Pass output_mode='samam' to template
        print("Generating Samam-only output...")
        CreatePdf(template_file, f"Samam", "Devanagari", supersections, current_os=current_os, output_mode='samam')
        CreateTextFile(text_template_file, f"Samam", "Devanagari", supersections, output_mode='samam')
        CreateHtmlFile(html_template_file, f"Samam", "Devanagari", supersections, html_font=html_font, output_mode='samam')
        
        print("Success! Generated separate Rik and Samam output files.")

if __name__ == "__main__":
    main()