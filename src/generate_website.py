#!/usr/bin/env python3
"""
Jaimineeya Samavedam Static Website Generator

This script generates a beautiful, modern static website for the Jaimineeya Samavedam
following the Parva → Kandah → Sama hierarchy.

Design Reference: Based on https://hvram1.github.io/rigveda.sanatana.in/sukta/1/1/
Structural Change: Uses JSV hierarchy (NOT Mandala/Sukta):
    - Parva (Top level) - SuperSection in source file (like Mandala)
    - Kandah (Sub-level) - Section in source file (like Sukta)
    - Sama (Verse unit) - SubSection in source file (like Rik/Mantra)

Author: JSV Project
Version: 2.0.0
"""

import os
import re
import json
from utils import combine_ardhaksharas
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime

# --- Import text processing functions from render_pdf ---
try:
    from render_pdf import (
        replace_accents_html,
        format_dandas_html,
        escape_for_html,
        remove_mantra_spaces,
        handle_consecutive_trikamba_html,
        process_footnotes_html
    )
    from utils import parse_mantra_for_latex, combine_ardhaksharas
    HAS_RENDER_IMPORTS = True
except ImportError:
    # Fallback if imports fail - define local versions
    HAS_RENDER_IMPORTS = False

# --- Configuration ---
AUDIO_FILENAME_FORMAT = "JSV_{parva}_{kandah}_{sama}.mp3"


# --- Local fallback functions if imports fail ---
def local_escape_for_html(text):
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

def local_replace_accents_html(text):
    """
    Replaces ASCII accent markers with Unicode Vedic accent characters for HTML.
    Uses spans with zero-width positioning for correct display (matching renderPDF.py).
    """
    if not text:
        return text
    
    # Use spans with zero-width CSS positioning (matching the working renderPDF.py output)
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


def local_process_footnotes_html(text, footnotes_dict=None, counter_obj=None, seen_map=None, accumulator=None):
    """
    Process footnotes with global accumulation support.
    """
    if not text:
        return text, []
    
    if footnotes_dict is None:
        footnotes_dict = {}
        
    # Default state if not provided (fallback)
    if counter_obj is None: counter_obj = {'val': 0}
    if seen_map is None: seen_map = {}
    if accumulator is None: accumulator = []
    
    collected_footnotes = [] # Local collection for return (legacy)
    
    # Devanagari digits for footnote references
    devanagari_digits = '०१२३४५६७८९'
    
    def replacer(match):
        marker_num = match.group(1) # '1' from 's1'
        marker_key = f's{marker_num}'
        footnote_text = footnotes_dict.get(marker_key, '').strip()
        
        unique_id = ""
        display_num = ""
        
        if footnote_text and footnote_text in seen_map:
            # Reuse existing footnote
            unique_id, display_num = seen_map[footnote_text]
        else:
            # New footnote
            counter_obj['val'] += 1
            val = counter_obj['val']
            unique_id = f'fn-kandah-{val}'
            display_num = ''.join(devanagari_digits[int(d)] for d in str(val))
            
            if footnote_text:
                seen_map[footnote_text] = (unique_id, display_num)
                accumulator.append((unique_id, display_num, footnote_text))
                collected_footnotes.append((unique_id, val, footnote_text))
        
        # Return superscript link with Devanagari number - NO WHITESPACE before/after
        return f'<sup class="footnote-ref"><a href="#{unique_id}">{display_num}</a></sup>'
    
    # Find all (sN) patterns
    pattern = r'\(s(\d+)\)'
    processed_text = re.sub(pattern, replacer, text)
    
    return processed_text, collected_footnotes

def local_format_dandas_html(text):
    """
    Formats danda symbols for HTML output.
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

def local_remove_mantra_spaces(text):
    """
    Removes all spaces within the text to create continuous Samhita text.
    """
    if not text:
        return text
    
    # Remove all Unicode whitespace characters
    text = re.sub(r'\s+', '', text)
    text = text.replace('\u00A0', '')  # Non-breaking space
    text = text.replace('\u200B', '')  # Zero-width space
    text = text.replace('\u200C', '')  # Zero-width non-joiner
    text = text.replace('\u200D', '')  # Zero-width joiner
    
    return text

def local_handle_consecutive_trikamba(text):
    """Insert thin space between consecutive trikamba accent marks."""
    if not text:
        return text
    pattern = r'\(4\)([^\(\)]{1,3})\(4\)'
    replacement = r'(4)\1 (4)'
    return re.sub(pattern, replacement, text)

# Choose functions based on import success
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


def format_rik_text_html(rik_text, footnotes_dict=None, counter_obj=None, seen_map=None, accumulator=None):
    """
    Format Rik text for HTML display with proper accent marks.
    Removes spaces (Samhita mode) and converts accent markers to Unicode.
    Also processes footnote markers via accumulator logic.
    Returns: (formatted_text, collected_footnotes)
    """
    if not rik_text:
        return "", []
    
    # Step 1: Remove spaces (Samhita mode)
    text = _remove_spaces(rik_text)
    
    # Step 2: Handle consecutive trikamba
    text = _handle_trikamba(text)
    
    # Step 3: Escape HTML special characters (before adding our HTML)
    text = _escape_html(text)
    
    # Step 4: Process footnotes - convert (s1) to superscript references
    text, collected_footnotes = local_process_footnotes_html(text, footnotes_dict, counter_obj, seen_map, accumulator)
    
    # Step 5: Replace accent markers with Unicode combining characters
    text = _replace_accents(text)
    
    # Step 6: Format dandas
    text = _format_dandas(text)
    
    return text, collected_footnotes


def format_mantra_text_html(mantra_text, footnotes_dict=None, counter_obj=None, seen_map=None, accumulator=None):
    """
    Format Sama mantra text for HTML display with stacked word/swara layout.
    Parses the mantra text and creates HTML with mantra words and their associated swaras.
    Also processes footnote markers.
    Returns: (formatted_text, collected_footnotes)
    """
    if not mantra_text:
        return "", []
    
    if footnotes_dict is None:
        footnotes_dict = {}
    
    
    # Default state if not provided
    if counter_obj is None: counter_obj = {'val': 0}
    if seen_map is None: seen_map = {}
    if accumulator is None: accumulator = []
    if footnotes_dict is None: footnotes_dict = {}

    html_parts = []
    collected_footnotes = []

    # Devanagari digits for footnote references
    devanagari_digits = '०१२३४५६७८९'
    
    # Parse the mantra text for word/swara pairs
    # Pattern: Word + (Swara) where Swara is in parentheses
    i = 0
    text = mantra_text.replace('\n', ' ').replace('\r', '').strip()
    
    while i < len(text):
        # Skip whitespace - don't add spaces between mantra words (matching renderPDF.py)
        if text[i].isspace() or text[i] in '\u200c\u200d\ufeff':
            i += 1
            continue
        
        # Check for dandas - wrap in mantra-word for vertical alignment
        if text[i] in '।॥|':
            # Check for verse number: ॥N॥
            number_match = re.match(r'॥\s*(\d+)\s*॥', text[i:])
            if number_match:
                num = number_match.group(1)
                # Wrap verse number in mantra-word structure for alignment
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
                # Wrap danda in mantra-word structure for vertical alignment
                html_parts.append(
                    f'<span class="mantra-word">'
                    f'<span class="mantra-text"><span class="danda">{danda}</span></span>'
                    f'<span class="swara-text">&nbsp;</span>'
                    f'</span>'
                )
                i += 1
            continue
        
        # Check for footnote marker: (sN)
        footnote_match = re.match(r'\(s(\d+)\)', text[i:])
        if footnote_match:
            marker_num = footnote_match.group(1)
            marker_key = f's{marker_num}'
            footnote_text = footnotes_dict.get(marker_key, '').strip()

            unique_id = ""
            display_num = ""
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

            # Add superscript reference with Devanagari number - No whitespace
            html_parts.append(f'<sup class="footnote-ref"><a href="#{unique_id}">{display_num}</a></sup>')
            i += len(footnote_match.group(0))
            continue
        
        # Match pattern: [Word](Swara) - but NOT (sN) which is a footnote
        match = re.match(r'([^\s()।॥]+)\s*\(([^)]+)\)', text[i:])
        if match:
            word = match.group(1)
            swara = match.group(2)
            
        # Check if swara is actually a footnote marker like 's1'
            if re.match(r's\d+$', swara):
                # This is a footnote attached to a word, not a swara
                marker_num = swara[1:] # extract number from sN
                marker_key = swara
                footnote_text = footnotes_dict.get(marker_key, '').strip()

                unique_id = ""
                display_num = ""
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
                
                # Render word + footnote superscript - No whitespace
                word = _escape_html(word)
                html_parts.append(
                    f'<span class="mantra-word"><span class="mantra-text">{word}</span><span class="swara-text">&nbsp;</span></span>'
                    f'<sup class="footnote-ref"><a href="#{unique_id}">{display_num}</a></sup>'
                )
            else:
                # Normal word + swara - Split using combine_ardhaksharas logic (matching renderPDF.py)
                clusters = combine_ardhaksharas(word)
                if len(clusters) > 0:
                    last_cluster = clusters[-1]
                    preceding = "".join(clusters[:-1])
                    
                    if preceding:
                        html_parts.append(f'<span class="mantra-word"><span class="mantra-text">{_escape_html(preceding)}</span><span class="swara-text">&nbsp;</span></span>')
                    
                    # Logic from renderPDF.py: \stackleft if len > 1, else \stackcenter
                    align_cls = " swara-left" if len(swara.strip()) > 1 else ""
                    html_parts.append(
                        f'<span class="mantra-word">'
                        f'<span class="mantra-text">{_escape_html(last_cluster)}</span>'
                        f'<span class="swara-text{align_cls}">{_escape_html(swara)}</span>'
                        f'</span>'
                    )
                else:
                    # Fallback for empty/invalid
                    align_cls = " swara-left" if len(swara.strip()) > 1 else ""
                    html_parts.append(
                        f'<span class="mantra-word">'
                        f'<span class="mantra-text">{_escape_html(word)}</span>'
                        f'<span class="swara-text{align_cls}">{_escape_html(swara)}</span>'
                        f'</span>'
                    )
            i += len(match.group(0))
            continue
        
        # Otherwise, collect text until next special character
        j = i
        while j < len(text) and text[j] not in '()।॥|' and not text[j].isspace():
            j += 1
        
        if j > i:
            word = _escape_html(text[i:j])
            # Word without swara - use &nbsp; for empty swara slot (matching renderPDF.py)
            html_parts.append(f'<span class="mantra-word"><span class="mantra-text">{word}</span><span class="swara-text">&nbsp;</span></span>')
            i = j
        else:
            # Skip unhandled character
            i += 1
    
    return ''.join(html_parts), collected_footnotes


# --- Data Classes ---
@dataclass
class Sama:
    """Represents a single Sama (verse/song)"""
    id: str
    title: str = ""
    rik_metadata: str = ""
    rik_text: str = ""
    mantra_text: str = ""
    footnotes: List[str] = field(default_factory=list)
    audio_filename: str = ""
    sama_number: int = 0
    global_number: int = 0  # Global sama number across all kandahs

@dataclass
class Kandah:
    """Represents a Kandah (chapter/section)"""
    id: str
    title: str
    samas: List[Sama] = field(default_factory=list)
    kandah_number: int = 0

@dataclass
class Parva:
    """Represents a Parva (top-level section)"""
    id: str
    title: str
    kandahs: List[Kandah] = field(default_factory=list)
    parva_number: int = 0


# --- Parser Class ---
class JSVParser:
    """Parses the Samhita source file into Parva → Kandah → Sama structure"""
    
    def __init__(self, source_file: str):
        self.source_file = source_file
        self.parvas: List[Parva] = []
        self.current_parva: Optional[Parva] = None
        self.current_kandah: Optional[Kandah] = None
        self.current_sama: Optional[Sama] = None
        
    def parse(self) -> List[Parva]:
        """Main parsing method"""
        content = self._read_file()
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for SuperSection (Parva)
            if '# Start of SuperSection Title --' in line:
                parva_id = self._extract_id(line, 'supersection_')
                i += 1
                title = lines[i].strip() if i < len(lines) else ""
                self._start_new_parva(parva_id, title)
                
            # Check for Section (Kandah)
            elif '# Start of Section Title --' in line:
                section_id = self._extract_id(line, 'section_')
                i += 1
                title = lines[i].strip() if i < len(lines) else ""
                self._start_new_kandah(section_id, title)
                
            # Check for SubSection Title (Sama title)
            elif '# Start of SubSection Title --' in line:
                subsection_id = self._extract_id(line, 'subsection_')
                i += 1
                title = lines[i].strip() if i < len(lines) else ""
                if self.current_sama and self.current_sama.id == subsection_id:
                    self.current_sama.title = title
                else:
                    self._start_new_sama(subsection_id, title)
                    
            # Check for Rik Metadata
            elif '# Start of Rik Metadata --' in line:
                subsection_id = self._extract_id(line, 'subsection_')
                i += 1
                metadata = lines[i].strip() if i < len(lines) else ""
                self._ensure_sama_exists(subsection_id)
                if self.current_sama:
                    self.current_sama.rik_metadata = metadata
                    
            # Check for Rik Text
            elif '# Start of Rik Text --' in line:
                subsection_id = self._extract_id(line, 'subsection_')
                i += 1
                rik_text = lines[i].strip() if i < len(lines) else ""
                self._ensure_sama_exists(subsection_id)
                if self.current_sama:
                    self.current_sama.rik_text = rik_text
                    
            # Check for Mantra Sets
            elif '#Start of Mantra Sets --' in line or '# Start of Mantra Sets --' in line:
                subsection_id = self._extract_id(line, 'subsection_')
                mantra_lines = []
                i += 1
                while i < len(lines) and '#End of Mantra Sets' not in lines[i] and '# End of Mantra Sets' not in lines[i]:
                    mantra_lines.append(lines[i])
                    i += 1
                if self.current_sama:
                    self.current_sama.mantra_text = '\n'.join(mantra_lines).strip()
                continue  # Skip the i += 1 at end
                
            # Check for Footnotes
            elif '# Start of Footnote --' in line:
                footnote_lines = []
                i += 1
                while i < len(lines) and '# End of Footnote' not in lines[i]:
                    footnote_lines.append(lines[i].strip())
                    i += 1
                if self.current_sama:
                    self.current_sama.footnotes = [f for f in footnote_lines if f]
                continue
                
            i += 1
            
        # Finalize last sama if exists
        self._finalize_current_sama()
        
        return self.parvas
    
    def _read_file(self) -> str:
        """Read source file with proper encoding"""
        encodings = ['utf-8', 'utf-8-sig', 'utf-16', 'latin-1']
        for encoding in encodings:
            try:
                with open(self.source_file, 'r', encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
        raise ValueError(f"Could not read file with any encoding: {self.source_file}")
    
    def _extract_id(self, line: str, prefix: str) -> str:
        """Extract ID from marker line"""
        match = re.search(rf'{prefix}(\d+)', line)
        return match.group(1) if match else ""
    
    def _start_new_parva(self, parva_id: str, title: str):
        """Start a new Parva"""
        self._finalize_current_sama()
        parva = Parva(
            id=parva_id,
            title=title,
            parva_number=len(self.parvas) + 1
        )
        self.parvas.append(parva)
        self.current_parva = parva
        self.current_kandah = None
        self.current_sama = None
        
    def _start_new_kandah(self, kandah_id: str, title: str):
        """Start a new Kandah within current Parva"""
        self._finalize_current_sama()
        if not self.current_parva:
            return
        kandah = Kandah(
            id=kandah_id,
            title=title,
            kandah_number=len(self.current_parva.kandahs) + 1
        )
        self.current_parva.kandahs.append(kandah)
        self.current_kandah = kandah
        self.current_sama = None
        
    def _start_new_sama(self, sama_id: str, title: str = ""):
        """Start a new Sama within current Kandah"""
        self._finalize_current_sama()
        if not self.current_kandah:
            return
        sama = Sama(
            id=sama_id,
            title=title,
            sama_number=len(self.current_kandah.samas) + 1
        )
        self.current_kandah.samas.append(sama)
        self.current_sama = sama
        
    def _ensure_sama_exists(self, sama_id: str):
        """Ensure a Sama exists with given ID, create if needed"""
        if self.current_sama and self.current_sama.id == sama_id:
            return
        # If we're starting metadata/text for a new sama
        self._start_new_sama(sama_id)
            
    def _finalize_current_sama(self):
        """Finalize the current Sama (generate audio filename, etc.)"""
        if self.current_sama and self.current_parva and self.current_kandah:
            parva_name = self._sanitize_for_filename(self.current_parva.title)
            self.current_sama.audio_filename = AUDIO_FILENAME_FORMAT.format(
                parva=parva_name,
                kandah=f"{self.current_kandah.kandah_number:02d}",
                sama=f"{self.current_sama.sama_number:02d}"
            )
            
    def _sanitize_for_filename(self, text: str) -> str:
        """Sanitize text for use in filename"""
        # Remove special characters, keep alphanumeric and Devanagari
        sanitized = re.sub(r'[^\w\u0900-\u097F]', '', text)
        return sanitized[:30] if sanitized else "unknown"


# --- HTML Generator Class (Rig Veda Style) ---
class WebsiteGenerator:
    """Generates static HTML website from parsed data - Rig Veda style"""
    
    def __init__(self, parvas: List[Parva], output_dir: str, audio_dir: str):
        self.parvas = parvas
        self.output_dir = Path(output_dir)
        self.audio_dir = Path(audio_dir)
        self.generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def generate(self):
        """Generate all website files"""
        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'css').mkdir(exist_ok=True)
        (self.output_dir / 'js').mkdir(exist_ok=True)
        (self.output_dir / 'kandah').mkdir(exist_ok=True)
        
        # Create audio placeholder directories
        self._create_audio_directories()
        
        # Generate files
        self._generate_css()
        self._generate_js()
        self._generate_homepage()
        # self._generate_indices() # Metadata parsing needs refinement
        self._generate_kandah_pages()
        self._generate_metadata_json()
        
        print(f"✅ Website generated at: {self.output_dir}")
        print(f"✅ Audio placeholder directories created at: {self.audio_dir}")
        
    def _create_audio_directories(self):
        """Create audio placeholder directories for each Parva"""
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        for parva in self.parvas:
            parva_folder = self._sanitize_foldername(parva.title)
            (self.audio_dir / parva_folder).mkdir(exist_ok=True)
            # Create a placeholder README
            readme_path = self.audio_dir / parva_folder / "README.md"
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(f"# {parva.title}\n\n")
                f.write(f"Place audio files for {parva.title} here.\n\n")
                f.write("## Expected Filename Format\n")
                f.write(f"`JSV_{{ParvaName}}_{{KandahNum}}_{{SamaNum}}.mp3`\n\n")
                f.write("## Kandahs in this Parva\n")
                for kandah in parva.kandahs:
                    f.write(f"- {kandah.title} ({len(kandah.samas)} Samas)\n")
                    
    def _sanitize_foldername(self, text: str) -> str:
        """Sanitize text for folder name"""
        sanitized = re.sub(r'[^\w\u0900-\u097F\s]', '', text)
        return sanitized.replace(' ', '_').strip()[:50] if sanitized else "unknown"
        
    def _generate_css(self):
        """Generate CSS stylesheet - Rig Veda inspired style"""
        css = '''/* Jaimineeya Samavedam Website Styles */
/* Design inspired by rigveda.sanatana.in */

:root {
    /* Color Palette - Clean, Sacred */
    --primary-maroon: #8B0000;
    --primary-gold: #DAA520;
    --accent-orange: #FF6B35;
    --sacred-saffron: #FF9933;
    
    /* Light Theme (like Rig Veda site) */
    --bg-main: #FEFEFE;
    --bg-sidebar: #F8F5F0;
    --bg-hover: #F0EBE3;
    --bg-card: #FFFFFF;
    --bg-verse: #FFFEF5;
    
    --text-primary: #2D2D2D;
    --text-secondary: #555555;
    --text-muted: #888888;
    --text-link: #8B0000;
    --text-link-hover: #B22222;
    
    --border-color: #E0DCD5;
    --border-light: #F0EBE3;
    
    /* Typography */
    --font-heading: 'AdiShila Vedic', 'Adishila SanVedic', 'Noto Serif Devanagari', 'Noto Sans Devanagari', serif;
    --font-body: 'Noto Sans Devanagari', 'Inter', sans-serif;
    --font-sanskrit: 'AdiShila Vedic', 'Adishila SanVedic', 'Noto Serif Devanagari', 'Siddhanta', serif;
    
    /* Spacing */
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;
    --spacing-2xl: 3rem;
    
    /* Layout */
    --sidebar-width: 280px;
}

/* Reset & Base */
*, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

html {
    scroll-behavior: smooth;
    font-size: 16px;
}

body {
    font-family: var(--font-body);
    background: var(--bg-main);
    color: var(--text-primary);
    line-height: 1.8;
    min-height: 100vh;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    font-family: var(--font-heading);
    font-weight: 600;
    line-height: 1.4;
    margin-bottom: var(--spacing-md);
    color: var(--primary-maroon);
}

h1 { font-size: 1.8rem; }
h2 { font-size: 1.5rem; }
h3 { font-size: 1.25rem; }
h4 { font-size: 1.1rem; }

.sanskrit-text {
    font-family: var(--font-sanskrit);
    font-size: 1.2rem;
    line-height: 2;
    letter-spacing: 0.02em;
}

.sanskrit-large {
    font-size: 1.4rem;
    line-height: 2.2;
}

/* Links */
a {
    color: var(--text-link);
    text-decoration: none;
    transition: color 0.2s ease;
}

a:hover {
    color: var(--text-link-hover);
    text-decoration: underline;
}

/* Main Layout - 3 Column */
.page-container {
    display: flex;
    min-height: 100vh;
}

/* Left Sidebar */
.sidebar-left {
    width: var(--sidebar-width);
    background: var(--bg-sidebar);
    border-right: 1px solid var(--border-color);
    padding: var(--spacing-lg);
    position: fixed;
    height: 100vh;
    overflow-y: auto;
}

.sidebar-left::-webkit-scrollbar {
    width: 6px;
}

.sidebar-left::-webkit-scrollbar-thumb {
    background: var(--border-color);
    border-radius: 3px;
}

.logo {
    margin-bottom: var(--spacing-xl);
    padding-bottom: var(--spacing-lg);
    border-bottom: 1px solid var(--border-color);
}

.logo-text {
    font-family: var(--font-heading);
    font-size: 1.3rem;
    color: var(--primary-maroon);
    font-weight: 600;
}

.logo-subtitle {
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-top: 4px;
}

.nav-section {
    margin-bottom: var(--spacing-xl);
}

.nav-section h3 {
    font-size: 1.15rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: var(--spacing-sm);
    font-weight: 500;
}

.nav-links {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-xs);
}

.nav-links a {
    display: inline-block;
    padding: 4px 10px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-size: 0.9rem;
    transition: all 0.2s ease;
}

.nav-links a:hover,
.nav-links a.active {
    background: var(--primary-maroon);
    color: white;
    border-color: var(--primary-maroon);
    text-decoration: none;
}

.nav-list {
    list-style: none;
}

.nav-list li {
    margin-bottom: var(--spacing-xs);
}

.nav-list a {
    display: block;
    padding: 6px 10px;
    border-radius: 4px;
    transition: background 0.2s ease;
    font-family: var(--font-sanskrit);
    font-size: 1.2rem;
}

.nav-list a:hover {
    background: var(--bg-hover);
    text-decoration: none;
}

/* Main Content */
.main-content {
    flex: 1;
    margin-left: var(--sidebar-width);
    padding: var(--spacing-xl) var(--spacing-2xl);
    max-width: 900px;
}

/* Right Sidebar (Jump Navigation) */
.sidebar-right {
    width: 220px;
    padding: var(--spacing-lg);
    position: fixed;
    right: 0;
    height: 100vh;
    overflow-y: auto;
    border-left: 1px solid var(--border-color);
}

.sidebar-right h3 {
    font-size: 0.85rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: var(--spacing-md);
}

.jump-links {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
}

.jump-links a {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: var(--bg-sidebar);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-size: 0.85rem;
    transition: all 0.2s ease;
}

.jump-links a:hover {
    background: var(--primary-maroon);
    color: white;
    border-color: var(--primary-maroon);
    text-decoration: none;
}

/* Page Header */
.page-header {
    margin-bottom: var(--spacing-2xl);
    padding-bottom: var(--spacing-lg);
    border-bottom: 2px solid var(--primary-maroon);
}

.page-header h1 {
    margin-bottom: var(--spacing-sm);
}

.page-subtitle {
    color: var(--text-secondary);
    font-size: 1.3rem;
    font-family: var(--font-sanskrit);
}

.page-meta {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-top: var(--spacing-sm);
}

.page-meta .page-subtitle {
    margin: 0;
}

.sama-count {
    display: inline-block;
    background: var(--bg-sidebar);
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.9rem;
    color: var(--text-secondary);
}

/* Breadcrumb */
.breadcrumb {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-lg);
    font-size: 1.25rem;
    font-family: var(--font-sanskrit);
}

.breadcrumb a {
    color: var(--text-link);
}

.breadcrumb-separator {
    color: var(--text-muted);
}

/* Table of Contents */
.toc {
    background: var(--bg-sidebar);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: var(--spacing-lg);
    margin-bottom: var(--spacing-2xl);
}

.toc h4 {
    margin-bottom: var(--spacing-md);
    font-size: 1.2rem;
}

.toc-list {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-xs);
    list-style: none;
}

.toc-list li a {
    display: inline-block;
    padding: 4px 12px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-size: 0.9rem;
}

.toc-list li a:hover {
    background: var(--primary-maroon);
    color: white;
    border-color: var(--primary-maroon);
    text-decoration: none;
}

/* Sama Entry (Verse) - Rig Veda Style */
.sama-entry {
    margin-bottom: var(--spacing-2xl);
    padding-bottom: var(--spacing-xl);
    border-bottom: 1px solid var(--border-light);
}

.sama-entry:last-child {
    border-bottom: none;
}

.sama-header {
    display: flex;
    align-items: baseline;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-md);
}

.sama-id {
    font-family: var(--font-heading);
    font-size: 1.1rem;
    color: var(--primary-maroon);
    font-weight: 600;
    background: var(--bg-sidebar);
    padding: 4px 12px;
    border-radius: 4px;
}

.sama-id a {
    color: var(--primary-maroon);
}

.sama-id a:hover {
    text-decoration: none;
}

/* Metadata Links (Rishi, Devata, Chandas) */
.metadata-links {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
}

.metadata-link {
    display: inline-block;
    padding: 4px 12px;
    background: var(--bg-sidebar);
    border-radius: 4px;
    font-size: 0.9rem;
    color: var(--text-secondary);
    transition: all 0.2s ease;
}

.metadata-link:hover {
    background: var(--primary-gold);
    color: var(--text-primary);
    text-decoration: none;
}

.metadata-link.rishi {
    border-left: 3px solid #8B4513;
}

.metadata-link.devata {
    border-left: 3px solid #B22222;
}

.metadata-link.chandas {
    border-left: 3px solid #DAA520;
}

/* Sama Title */
.sama-title {
    font-family: var(--font-sanskrit);
    font-size: 1.1rem;
    color: var(--text-secondary);
    margin-bottom: var(--spacing-md);
    font-style: italic;
}

/* Rik Metadata - displayed above Rik text in purple */
.rik-metadata {
    font-family: var(--font-sanskrit);
    font-size: 1.6rem;
    color: #7b1fa2;
    text-align: center;
    margin-bottom: var(--spacing-sm);
}

/* Sama Header Text - displayed above Sama/Mantra text in green */
.sama-header-text {
    font-family: var(--font-sanskrit);
    font-size: 1.6rem;
    color: #2e7d32;
    text-align: center;
    margin-bottom: var(--spacing-sm);
}

/* Rik Text Box */
.rik-box {
    background: #FFF8DC;
    border-left: 4px solid var(--primary-gold);
    padding: var(--spacing-md) var(--spacing-lg);
    margin-bottom: var(--spacing-md);
    border-radius: 0 8px 8px 0;
}

.rik-label {
    font-size: 0.75rem;
    color: var(--primary-gold);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: var(--spacing-xs);
    font-weight: 600;
}

.rik-text {
    font-family: var(--font-sanskrit);
    font-size: 1.6rem;
    line-height: 2;
    color: #1565c0;
}

/* Mantra Text Box */
.mantra-box {
    background: var(--bg-verse);
    border-left: 4px solid var(--primary-maroon);
    padding: var(--spacing-md) var(--spacing-lg);
    margin-bottom: var(--spacing-md);
    border-radius: 0 8px 8px 0;
}

.mantra-label {
    font-size: 0.75rem;
    color: var(--primary-maroon);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: var(--spacing-xs);
    font-weight: 600;
}

.mantra-text {
    font-family: var(--font-sanskrit);
    font-size: 1.2rem;
    line-height: 2.2;
    color: var(--text-primary);
}

/* Audio Section */
.audio-section {
    margin-top: var(--spacing-md);
}

.audio-player {
    width: 100%;
    max-width: 400px;
}

.audio-pending {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--bg-sidebar);
    border: 1px dashed var(--border-color);
    border-radius: 4px;
    color: var(--text-muted);
    font-size: 0.9rem;
}

/* Footnotes */
.footnotes {
    margin-top: var(--spacing-md);
    padding-top: var(--spacing-md);
    border-top: 1px dashed var(--border-color);
}

.footnotes-label {
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-bottom: var(--spacing-xs);
}

.footnote-item {
    font-size: 0.9rem;
    color: var(--text-secondary);
    margin-bottom: var(--spacing-xs);
    padding-left: var(--spacing-md);
    border-left: 2px solid var(--border-color);
}

/* Homepage Styles */
.home-hero {
    text-align: center;
    padding: var(--spacing-2xl) 0;
    margin-bottom: var(--spacing-2xl);
    border-bottom: 2px solid var(--primary-maroon);
}

.home-hero h1 {
    font-size: 2.2rem;
    margin-bottom: var(--spacing-sm);
}

.home-hero .subtitle {
    font-size: 1.2rem;
    color: var(--text-secondary);
}

.stats-row {
    display: flex;
    justify-content: center;
    gap: var(--spacing-2xl);
    margin-top: var(--spacing-xl);
}

.stat-item {
    text-align: center;
}

.stat-value {
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--primary-maroon);
}

.stat-label {
    font-size: 0.9rem;
    color: var(--text-muted);
}

/* Parva Grid */
.parva-section {
    margin-bottom: var(--spacing-2xl);
}

.parva-section h2 {
    margin-bottom: var(--spacing-lg);
    padding-bottom: var(--spacing-sm);
    border-bottom: 1px solid var(--border-color);
}

.kandah-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: var(--spacing-md);
}

.kandah-card {
    display: block;
    padding: var(--spacing-md);
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    transition: all 0.2s ease;
}

.kandah-card:hover {
    border-color: var(--primary-maroon);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    text-decoration: none;
}

.kandah-card .number {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--primary-maroon);
}

.kandah-card .title {
    font-family: var(--font-sanskrit);
    font-size: 1.4rem;
    color: var(--text-primary);
    margin: var(--spacing-xs) 0;
}

.kandah-card .count {
    font-size: 0.85rem;
    color: var(--text-muted);
}

/* Footer */
.footer {
    margin-top: var(--spacing-2xl);
    padding: var(--spacing-xl);
    border-top: 1px solid var(--border-color);
    text-align: center;
    color: var(--text-muted);
    font-size: 0.9rem;
}

/* Responsive */
@media (max-width: 1200px) {
    .sidebar-right {
        display: none;
    }
}

@media (max-width: 900px) {
    .sidebar-left {
        position: static;
        width: 100%;
        height: auto;
        border-right: none;
        border-bottom: 1px solid var(--border-color);
    }
    
    .main-content {
        margin-left: 0;
        padding: var(--spacing-lg);
    }
    
    .page-container {
        flex-direction: column;
    }
}

@media (max-width: 600px) {
    .kandah-grid {
        grid-template-columns: 1fr;
    }
    
    .stats-row {
        flex-direction: column;
        gap: var(--spacing-lg);
    }
    
    .metadata-links {
        flex-direction: column;
    }
}

/* Audio Player Styles */
.audio-section {
    margin-top: var(--spacing-lg);
    display: flex;
    justify-content: center;
    width: 100%;
}

.audio-player-container {
    width: 100%;
    max-width: 400px;
    display: flex;
    justify-content: center;
}

.audio-player {
    width: 100%;
}

/* Mantra/Swara Stacking Styles - Matching renderPDF.py output */
.mantra-break {
    flex-basis: 100%;
    height: 1rem;
    width: 100%;
}

.mantra-word {
    display: inline-flex;
    flex-direction: column;
    align-items: stretch;
    vertical-align: top;
    margin: 0;
    padding: 0;
}

.mantra-text {
    font-family: var(--font-sanskrit);
    font-size: 1.6rem;
    line-height: 1.2;
    color: #000000;
}

.swara-text {
    font-family: var(--font-sanskrit);
    color: #c62828;
    font-size: 1.3rem;
    line-height: 1;
    text-align: center;
    margin-top: -0.2em;
    min-height: 1em;
    border-right: 1px solid transparent;
    padding-right: 2px;
}

.swara-left {
    text-align: left;
}

.mantra-verse {
    margin: 5px 0;
    display: inline-flex;
    flex-wrap: wrap;
    align-items: flex-start;
    text-align: center;
    gap: 0;
}

.word-space {
    width: 0.3em;
}

/* Vedic Accent Mark Styles - Zero-width positioning */
.accent-swarita {
    display: inline-block;
    width: 0;
    overflow: visible;
    color: #1565c0;
    font-weight: bold;
    font-size: 1.2em;
    position: relative;
    left: -0.1em;
    top: -0.15em;
}

.accent-anudatta {
    display: inline-block;
    width: 0;
    overflow: visible;
    color: #1565c0;
    font-weight: bold;
    font-size: 1.2em;
    position: relative;
    left: -0.1em;
    top: -0.15em;
}

.accent-kampa {
    display: inline-block;
    width: 0;
    overflow: visible;
    color: #1565c0;
    font-weight: bold;
    font-size: 1.2em;
    position: relative;
    left: -0.1em;
    top: -0.15em;
}

.accent-trikampa {
    display: inline-block;
    width: 0;
    overflow: visible;
    color: #1565c0;
    font-weight: bold;
    font-size: 1.2em;
    position: relative;
    left: -0.1em;
    top: -0.15em;
}

.danda {
    margin: 0 0.2em;
}

.mantra-number {
    display: inline-block;
    white-space: nowrap;
    color: var(--primary-maroon);
    font-weight: bold;
}

/* Footnote Section Styles - matching renderPDF.py */
.footnotes {
    margin-top: var(--spacing-lg);
}

.footnote-separator {
    border: none;
    border-top: 1px solid var(--border-color);
    margin: 20px 0 10px 0;
    width: 40%;
    margin-left: 0;
}

    padding: 10px 0;
    text-align: left;
    font-size: 0.9rem;
    line-height: 1.5;
    font-family: var(--font-sanskrit);
}

.footnote-item {
    padding: 5px 0;
    display: flex;
    align-items: flex-start;
}

.footnote-item .footnote-ref {
    color: #1565c0;
    font-weight: bold;
    margin-right: 0.5em;
    min-width: 1.5em;
    font-family: var(--font-sanskrit);
}

.footnote-item .footnote-text {
    margin-left: 0.5em;
}

/* Inline footnote superscript references - matching renderPDF.py */
sup.footnote-ref {
    font-size: 0.7em;
    vertical-align: super;
    line-height: 0;
    position: relative;
    top: -0.5em;
}

sup.footnote-ref a {
    color: #1565c0;
    text-decoration: none;
    font-weight: bold;
}

sup.footnote-ref a:hover {
    text-decoration: underline;
}

/* Print Styles */
@media print {
    .sidebar-left, .sidebar-right {
        display: none;
    }
    
    .main-content {
        margin: 0;
        max-width: 100%;
    }
}
/* Classification & Index Styles */
.classification-grid {
    display: grid;
    gap: var(--spacing-xl);
    max-width: 800px;
    margin: 0 auto;
}

.class-section {
    background: var(--bg-card);
    padding: var(--spacing-xl);
    border-radius: 8px;
    border: 1px solid var(--border-color);
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.class-section h2 {
    color: var(--accent-orange);
    text-align: center;
    margin-bottom: var(--spacing-lg);
    font-size: 1.4rem;
}

.button-row {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-md);
    justify-content: center;
}

.index-btn {
    display: inline-block;
    padding: var(--spacing-md) var(--spacing-lg);
    background: #FFF8E1;
    color: var(--text-primary);
    border-radius: 4px;
    border: 1px solid var(--primary-gold);
    font-family: var(--font-heading);
    transition: all 0.2s ease;
}

.index-btn:hover {
    background: var(--primary-gold);
    color: white;
    text-decoration: none;
    transform: translateY(-2px);
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.index-list {
    max-width: 800px;
    margin: 0 auto;
}

.index-entry {
    margin-bottom: var(--spacing-lg);
    border-bottom: 1px solid var(--border-light);
    padding-bottom: var(--spacing-sm);
}

.index-term {
    font-family: var(--font-heading);
    font-size: 1.2rem;
    color: var(--primary-maroon);
    margin-bottom: var(--spacing-xs);
    font-weight: 600;
}

.index-refs {
    font-size: 0.9rem;
    line-height: 1.6;
}

.index-refs a {
    color: var(--text-link);
    margin-right: 8px;
    display: inline-block;
}

.index-char-header {
    font-size: 1.5rem;
    color: var(--text-muted);
    border-bottom: 2px solid var(--primary-gold);
    margin: var(--spacing-xl) 0 var(--spacing-md) 0;
    padding-bottom: 4px;
}
'''
        with open(self.output_dir / 'css' / 'styles.css', 'w', encoding='utf-8') as f:
            f.write(css)
            
    def _generate_js(self):
        """Generate JavaScript for interactivity"""
        js = '''// Jaimineeya Samavedam Website JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                // Update URL without jumping
                history.pushState(null, null, this.getAttribute('href'));
            }
        });
    });

    // Highlight current section in jump links
    const observerOptions = {
        root: null,
        rootMargin: '-20% 0px -70% 0px',
        threshold: 0
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            const id = entry.target.getAttribute('id');
            const jumpLink = document.querySelector(`.jump-links a[href="#${id}"]`);
            if (jumpLink) {
                if (entry.isIntersecting) {
                    document.querySelectorAll('.jump-links a').forEach(a => a.classList.remove('active'));
                    jumpLink.classList.add('active');
                }
            }
        });
    }, observerOptions);

    document.querySelectorAll('.sama-entry').forEach(entry => {
        observer.observe(entry);
    });

    // Audio error handling
    document.querySelectorAll('audio').forEach(audio => {
        audio.addEventListener('error', function() {
            const container = this.closest('.audio-section');
            if (container) {
                container.innerHTML = `
                    <div class="audio-pending">
                        <span>🎵</span>
                        <span>Audio coming soon</span>
                    </div>
                `;
            }
        });
    });
});
'''
        with open(self.output_dir / 'js' / 'main.js', 'w', encoding='utf-8') as f:
            f.write(js)

    def _get_html_head(self, title: str, depth: int = 0) -> str:
        """Generate HTML head section"""
        prefix = '../' * depth
        return f'''<!DOCTYPE html>
<html lang="sa">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="जैमिनीय सामवेदम् - Jaimineeya Samavedam digital archive with authentic texts">
    <meta name="keywords" content="Samaveda, Jaimineeya, Vedas, Sanskrit, Hindu scriptures, Vedic chanting">
    <title>{title} | जैमिनीय सामवेदम्</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Noto+Sans+Devanagari:wght@400;500;600&family=Noto+Serif+Devanagari:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{prefix}css/styles.css">
</head>'''

    def _get_sidebar_html(self, current_parva_id: str = "", current_kandah_id: str = "", depth: int = 0) -> str:
        """Generate left sidebar with navigation"""
        prefix = '../' * depth
        
        # Parva links (like Mandala in Rig Veda)
        parva_links = ""
        for parva in self.parvas:
            active = 'active' if parva.id == current_parva_id else ''
            parva_links += f'<a href="{prefix}kandah/{parva.id}/1.html" class="{active}">{parva.parva_number}</a>\n'
        
        # Kandah links for current parva (if applicable)
        kandah_section = ""
        sama_section = ""
        
        if current_parva_id:
            current_parva = next((p for p in self.parvas if p.id == current_parva_id), None)
            if current_parva:
                # Kandah Section
                kandah_links = ""
                for kandah in current_parva.kandahs:
                    active = 'active' if kandah.id == current_kandah_id else ''
                    kandah_links += f'<a href="{prefix}kandah/{current_parva_id}/{kandah.kandah_number}.html" class="{active}">{kandah.kandah_number}</a>\n'
                
                kandah_section = f'''
                <div class="nav-section">
                            <h3>खण्ड: ({len(current_parva.kandahs)})</h3>
                    <div class="nav-links">
                        {kandah_links}
                    </div>
                </div>'''
                
                # Sama Section (only if a Kandah is selected)
                if current_kandah_id:
                    current_kandah = next((k for k in current_parva.kandahs if k.id == current_kandah_id), None)
                    if current_kandah:
                        import re
                        sama_links = ""
                        total_real_samams = 0
                        current_samam_start = 1
                        
                        for sama in current_kandah.samas:
                            # Calculate real Samam count by finding verse delimiters like || 1 || or ॥ १ ॥
                            cnt = 0
                            if sama.mantra_text:
                                matches = re.findall(r'(?:\|\||॥)\s*[\d०-९]+\s*(?:\|\||॥)', sama.mantra_text)
                                cnt = len(matches)
                            
                            # Fallback: if no delimiters found, count as 1
                            if cnt == 0: cnt = 1
                            
                            # Calculate range for label
                            range_end = current_samam_start + cnt - 1
                            if cnt > 1:
                                label_text = f"{current_samam_start}–{range_end}"
                            else:
                                label_text = f"{current_samam_start}"
                            
                            # Create link
                            sama_links += f'<a href="#sama-{sama.sama_number}">{label_text}</a>\n'
                            
                            # Update counters
                            total_real_samams += cnt
                            current_samam_start = range_end + 1
                        
                        sama_section = f'''
                        <div class="nav-section">
                            <h3>साम: ({total_real_samams})</h3>
                            <div class="nav-links">
                                {sama_links}
                            </div>
                        </div>'''
        
        return f'''<aside class="sidebar-left">
    <div class="logo">
        <a href="{prefix}index.html">
            <div class="logo-text">जैमिनीय सामवेदम्</div>
            <div class="logo-subtitle">Jaimineeya Samavedam</div>
        </a>
    </div>
    
    <div class="nav-section">
        <h3>पर्व:</h3>
        <div class="nav-links">
            {parva_links}
        </div>
    </div>
    {kandah_section}
    {sama_section}
    <div class="nav-section">
        <h3>Jump to</h3>
        <ul class="nav-list">
            <li><a href="{prefix}index.html">मुख्यपृष्ठम् (Home)</a></li>
        </ul>
    </div>
</aside>'''

    def _get_jump_sidebar_html(self, samas: List[Sama]) -> str:
        """Generate right sidebar with jump links"""
        jump_links = ""
        for sama in samas:
            jump_links += f'<a href="#sama-{sama.sama_number}">{sama.sama_number}</a>\n'
        
        return f'''<aside class="sidebar-right">
    <h3>साम: ({len(samas)})</h3>
    <div class="jump-links">
        {jump_links}
    </div>
</aside>'''

    def _parse_metadata(self, metadata_str: str) -> dict:
        """Parse metadata string into Rishi, Devata, Chandas"""
        result = {'rishi': '', 'devata': '', 'chandas': ''}
        if not metadata_str:
            return result
        
        # Remove outer markers like ।। and ॥
        cleaned = re.sub(r'^[।॥\s]+|[।॥\s]+$', '', metadata_str)
        
        # Split by ।। or spaces and try to identify parts
        parts = re.split(r'\s*।।\s*|\s+', cleaned)
        parts = [p.strip() for p in parts if p.strip()]
        
        if len(parts) >= 3:
            result['rishi'] = parts[0]
            result['devata'] = parts[1]
            result['chandas'] = parts[2]
        elif len(parts) == 2:
            result['rishi'] = parts[0]
            result['devata'] = parts[1]
        elif len(parts) == 1:
            result['rishi'] = parts[0]
        
        return result

    def _generate_homepage(self):
        """Generate the homepage"""
        import re
        
        total_kandahs = sum(len(p.kandahs) for p in self.parvas)
        total_samas = 0
        
        # Calculate total samas iterating through all content
        for p in self.parvas:
            for k in p.kandahs:
                for s in k.samas:
                    c = 0
                    if s.mantra_text:
                        c = len(re.findall(r'(?:\|\||॥)\s*[\d०-९]+\s*(?:\|\||॥)', s.mantra_text))
                    if c == 0: c = 1
                    total_samas += c
        
        # Generate Parva sections with Kandah grids
        parva_sections = ""
        for parva in self.parvas:
            kandah_cards = ""
            for kandah in parva.kandahs:
                # Calculate real count for this kandah
                kandah_sama_count = 0
                for s in kandah.samas:
                    c = 0
                    if s.mantra_text:
                         c = len(re.findall(r'(?:\|\||॥)\s*[\d०-९]+\s*(?:\|\||॥)', s.mantra_text))
                    if c == 0: c = 1
                    kandah_sama_count += c
                
                kandah_cards += f'''
                <a href="kandah/{parva.id}/{kandah.kandah_number}.html" class="kandah-card">
                    <div class="number">{kandah.kandah_number}</div>
                    <div class="title">{kandah.title}</div>
                    <div class="count">{kandah_sama_count} साम</div>
                </a>'''
            
            parva_sections += f'''
            <section class="parva-section">
                <h2>{parva.parva_number}. {parva.title}</h2>
                <div class="kandah-grid">
                    {kandah_cards}
                </div>
            </section>'''
        
        html = f'''{self._get_html_head("मुख्यपृष्ठम्")}
<body>
    <div class="page-container">
        {self._get_sidebar_html()}
        
        <main class="main-content">
            <div class="home-hero">
                <h1>जैमिनीय साम प्रकृति गानम्</h1>
                <p class="subtitle">Jaimineeya Sama Prakruti Ganam</p>
                
                <div class="stats-row">
                    <div class="stat-item">
                        <div class="stat-value">{len(self.parvas)}</div>
                        <div class="stat-label">पर्व: (Parva)</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{total_kandahs}</div>
                        <div class="stat-label">खण्ड: (Kandah)</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{total_samas}</div>
                        <div class="stat-label">साम: (Sama)</div>
                    </div>
                </div>
                
                <div class="quick-links" style="margin-top: 2rem; text-align: center; opacity: 0.7;">
                    <span class="index-btn" style="cursor: not-allowed; background: #f5f5f5; border-color: #ddd; color: #888;">सङ्क्रमणिका / वर्गीकरणम् (Coming Soon)</span>
                </div>
            </div>
            
            {parva_sections}
            
            <footer class="footer">
                जैमिनीय सामवेद प्रकृति गानम्<br>
                Generated on {self.generated_at}
            </footer>
        </main>
    </div>
    <script src="js/main.js"></script>
</body>
</html>'''
        
        with open(self.output_dir / 'index.html', 'w', encoding='utf-8') as f:
            f.write(html)

    def _collect_indices(self):
        """Collect data for all indices"""
        self.rishi_index = defaultdict(list)
        self.devata_index = defaultdict(list)
        self.chandas_index = defaultdict(list)
        self.header_index = [] 
        
        for parva in self.parvas:
            for kandah in parva.kandahs:
                for sama in kandah.samas:
                    # Link relative to classification/ folder
                    link_rel = f"../kandah/{parva.id}/{kandah.kandah_number}.html#sama-{sama.sama_number}"
                    location = f"{parva.parva_number}.{kandah.kandah_number}.{sama.sama_number}"
                    
                    # Sama Header Index
                    if sama.title:
                        clean_title = sama.title.strip(' .|॥')
                        if clean_title:
                            self.header_index.append({
                                'text': clean_title,
                                'link': link_rel,
                                'location': location
                            })
                    
                    # Metadata Indices
                    if sama.rik_metadata:
                        parts = self._parse_metadata(sama.rik_metadata)
                        ref = {'link': link_rel, 'location': location}
                        
                        if parts['rishi']: self.rishi_index[parts['rishi']].append(ref)
                        if parts['devata']: self.devata_index[parts['devata']].append(ref)
                        if parts['chandas']: self.chandas_index[parts['chandas']].append(ref)

    def _generate_indices(self):
        """Generate all index pages"""
        self._collect_indices()
        
        # Create classification dir
        (self.output_dir / 'classification').mkdir(exist_ok=True)
        
        self._generate_classification_home()
        self._generate_index_page_generic("ऋषयः (Rishis)", self.rishi_index, "rishi.html")
        self._generate_index_page_generic("देवताः (Devatas)", self.devata_index, "devata.html")
        self._generate_index_page_generic("छन्दांसि (Chandas)", self.chandas_index, "chandas.html")
        self._generate_header_index()

    def _generate_classification_home(self):
        """Generate the main classification landing page"""
        html = f'''{self._get_html_head("वर्गीकरणम् (Classifications)", depth=1)}
<body>
    <div class="page-container">
        {self._get_sidebar_html(depth=1)}
        
        <main class="main-content">
            <div class="page-header">
                <h1>सङ्क्रमणिका / वर्गीकरणम्</h1>
                <p class="page-subtitle">Indices and Classifications</p>
            </div>
            
            <div class="classification-grid">
                <section class="class-section">
                    <h2>अन्य वर्गीकरणम्</h2>
                    <div class="button-row">
                        <a href="rishi.html" class="index-btn">ऋषयः</a>
                        <a href="devata.html" class="index-btn">देवताः</a>
                        <a href="chandas.html" class="index-btn">छन्दांसि</a>
                    </div>
                </section>
                
                <section class="class-section">
                    <h2>अनुक्रमणिका:</h2>
                    <div class="button-row">
                        <a href="headers.html" class="index-btn">सामानुक्रमणिका (Headers)</a>
                    </div>
                </section>
            </div>
        </main>
    </div>
    <script src="../js/main.js"></script>
</body>
</html>'''
        with open(self.output_dir / 'classification' / 'index.html', 'w', encoding='utf-8') as f:
            f.write(html)

    def _generate_index_page_generic(self, title, data_dict, filename):
        """Generate a generic index page for a dictionary of items"""
        # Sort keys
        sorted_keys = sorted(data_dict.keys())
        
        items_html = ""
        for key in sorted_keys:
            refs = data_dict[key]
            refs_html = ", ".join([f'<a href="{r["link"]}">{r["location"]}</a>' for r in refs])
            items_html += f'''
            <div class="index-entry">
                <div class="index-term">{key}</div>
                <div class="index-refs">{refs_html}</div>
            </div>'''
            
        html = f'''{self._get_html_head(title, depth=1)}
<body>
    <div class="page-container">
        {self._get_sidebar_html(depth=1)}
        <main class="main-content">
            <div class="page-header">
                <h1>{title}</h1>
                <a href="index.html" class="back-link">← Back to Classifications</a>
            </div>
            <div class="index-list">
                {items_html}
            </div>
        </main>
    </div>
    <script src="../js/main.js"></script>
</body>
</html>'''
        with open(self.output_dir / 'classification' / filename, 'w', encoding='utf-8') as f:
            f.write(html)

    def _generate_header_index(self):
        """Generate Alphabetical Header Index"""
        # Sort by text
        sorted_items = sorted(self.header_index, key=lambda x: x['text'])
        
        items_html = ""
        current_char = ""
        
        for item in sorted_items:
            # Group by first character (optional, but nice)
            first_char = item['text'][0] if item['text'] else ''
            if first_char != current_char:
                current_char = first_char
                items_html += f'<div class="index-char-header">{current_char}</div>'
            
            items_html += f'''
            <div class="index-entry simple">
                <a href="{item["link"]}" class="index-term-link">{item["text"]}</a>
                <span class="index-loc">({item["location"]})</span>
            </div>'''
            
        html = f'''{self._get_html_head("सामानुक्रमणिका", depth=1)}
<body>
    <div class="page-container">
        {self._get_sidebar_html(depth=1)}
        <main class="main-content">
            <div class="page-header">
                <h1>सामानुक्रमणिका (Alphabetical Headers)</h1>
                <a href="index.html" class="back-link">← Back to Classifications</a>
            </div>
            <div class="index-list">
                {items_html}
            </div>
        </main>
    </div>
    <script src="../js/main.js"></script>
</body>
</html>'''
        with open(self.output_dir / 'classification' / 'headers.html', 'w', encoding='utf-8') as f:
            f.write(html)
            
    def _generate_kandah_pages(self):
        """Generate individual Kandah pages with Samas (like Sukta pages in Rig Veda)"""
        for parva in self.parvas:
            # Create parva directory
            parva_dir = self.output_dir / 'kandah' / parva.id
            parva_dir.mkdir(parents=True, exist_ok=True)
            
            for kandah in parva.kandahs:
                # Build Table of Contents
                toc_items = ""
                for sama in kandah.samas:
                    toc_items += f'<li><a href="#sama-{sama.sama_number}">{parva.parva_number}.{kandah.kandah_number}.{sama.sama_number}</a></li>\n'
                
                # Accumulator State for Kandah (Global Footnotes)
                kandah_counter = {'val': 0}
                kandah_seen_footnotes = {}  # content -> (id, display_num)
                kandah_all_footnotes = []   # list of (id, display_num, text)

                # Build Sama entries
                sama_entries = ""
                for sama in kandah.samas:
                    # Parse footnote dict for this sama
                    current_footnotes_dict = {}
                    if sama.footnotes:
                        for fn in sama.footnotes:
                            # Parse "sN - text" or "sN : text"
                            import re
                            parts = re.match(r'(s\d+)\s*[-–—:]\s*(.*)', fn)
                            if parts:
                                current_footnotes_dict[parts.group(1)] = parts.group(2)
                            else:
                                # Fallback if format is just "s1 text" or other
                                # Try to grab sN at start
                                parts = re.match(r'(s\d+)\s+(.*)', fn)
                                if parts:
                                    current_footnotes_dict[parts.group(1)] = parts.group(2)
                    
                    # Parse metadata
                    meta = self._parse_metadata(sama.rik_metadata)
                    
                    # Rik metadata (displayed above Rik text - in purple like renderPDF.py)
                    rik_metadata_html = ""
                    if sama.rik_metadata:
                        # Clean existing dandas/dots to prevent double symbols
                        # Added single danda '।' (U+0964) to the strip set
                        clean_meta = sama.rik_metadata.strip(' .|॥।\n\r\t')
                        if clean_meta:
                            # Normalize all internal danda variations (| || । ॥) to single '॥'
                            # Also handles spacing around them
                            import re
                            clean_meta = re.sub(r'\s*[|॥।]+\s*', ' ॥ ', clean_meta)
                            rik_metadata_html = f'<div class="rik-metadata">॥ {clean_meta} ॥</div>'
                    
                    # Rik text
                    rik_html = ""
                    if sama.rik_text:
                        formatted_rik, _ = format_rik_text_html(sama.rik_text, current_footnotes_dict, kandah_counter, kandah_seen_footnotes, kandah_all_footnotes)
                        rik_html = f'''
                        <div class="rik-box">
                            {rik_metadata_html}
                            <div class="rik-text sanskrit-text">{formatted_rik}</div>
                        </div>'''
                    
                    # Sama title and metadata (displayed above Sama/Mantra text - in green)
                    sama_header_html = ""
                    if sama.title:
                        # Clean existing dandas/dots - Added single danda '।'
                        clean_title = sama.title.strip(' .|॥।\n\r\t')
                        if clean_title:
                            # Normalize all internal danda variations
                            clean_title = re.sub(r'\s*[|॥।]+\s*', ' ॥ ', clean_title)
                            sama_header_html = f'<div class="sama-header-text">॥ {clean_title} ॥</div>'
                    
                    # Mantra text with Sama header above it
                    mantra_html = ""
                    if sama.mantra_text:
                        formatted_mantra, _ = format_mantra_text_html(sama.mantra_text, current_footnotes_dict, kandah_counter, kandah_seen_footnotes, kandah_all_footnotes)
                        mantra_html = f'''
                        <div class="mantra-box">
                            {sama_header_html}
                            <div class="mantra-text sanskrit-large">{formatted_mantra}</div>
                        </div>'''
                    
                    # Audio section
                    audio_html = ""
                    
                    # Define source directory for audio (relative to project root)
                    audio_src_root = Path('data/audio_source')
                    
                    # Output directory for this kandah's audio
                    kandah_audio_out_dir = parva_dir / 'audio'
                    kandah_audio_out_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Search paths - User requested: ParvaNumber folder only
                    # Then filename 1-1.mp3 (Kandah-Sama.mp3)
                    search_paths = [
                        audio_src_root / str(parva.parva_number),
                        audio_src_root / parva.id # Fallback
                    ]
                    
                    # 1. SAMA AUDIO
                    sama_audio_filename = None
                    sama_audio_found = False
                    
                    for search_path in search_paths:
                        # User requested format: Kandah-Subsection.mp3 (e.g. 1-1.mp3)
                        candidates = [
                            f"{kandah.kandah_number}-{sama.sama_number}.mp3", 
                            f"sama_{kandah.kandah_number}-{sama.sama_number}.mp3"
                        ]
                        for cand in candidates:
                            src_file = search_path / cand
                            if src_file.exists():
                                sama_audio_found = True
                                dest_filename = f"{kandah.kandah_number}-{sama.sama_number}.mp3"
                                dist_path = kandah_audio_out_dir / dest_filename
                                import shutil
                                shutil.copy2(src_file, dist_path)
                                sama_audio_filename = f"audio/{dest_filename}"
                                break
                        if sama_audio_found: break
                    
                    # 2. RIK AUDIO
                    rik_audio_filename = None
                    rik_audio_found = False
                    
                    for search_path in search_paths:
                         # Try 'rik_K-S.mp3'
                        candidates = [
                            f"rik_{kandah.kandah_number}-{sama.sama_number}.mp3", 
                            f"Rik_{kandah.kandah_number}-{sama.sama_number}.mp3"
                        ]
                        for cand in candidates:
                             src_file = search_path / cand
                             if src_file.exists():
                                 rik_audio_found = True
                                 dest_filename = f"rik_{kandah.kandah_number}-{sama.sama_number}.mp3"
                                 dist_path = kandah_audio_out_dir / dest_filename
                                 import shutil
                                 shutil.copy2(src_file, dist_path)
                                 rik_audio_filename = f"audio/{dest_filename}"
                                 break
                        if rik_audio_found: break

                    # Generate HTML
                    if sama_audio_found or rik_audio_found:
                         audio_players = []
                         
                         if rik_audio_found:
                             audio_players.append(f'''
                                <div class="audio-player-container">
                                    <div class="audio-label">Rik Audio</div>
                                    <audio controls class="audio-player">
                                        <source src="{rik_audio_filename}" type="audio/mpeg">
                                        Your browser does not support the audio element.
                                    </audio>
                                </div>''')
                         
                         if sama_audio_found:
                             audio_players.append(f'''
                                <div class="audio-player-container">
                                    <audio controls class="audio-player">
                                        <source src="{sama_audio_filename}" type="audio/mpeg">
                                        Your browser does not support the audio element.
                                    </audio>
                                </div>''')
                                
                         audio_html = f'<div class="audio-section">{"".join(audio_players)}</div>'
                    else:
                        audio_html = '''
                        <div class="audio-section">
                            <div class="audio-pending">
                                <span>🎵</span>
                                <span>Audio missing</span>
                            </div>
                        </div>'''
                    
                    # NO per-Sama footnotes section here - accumulated at Kandah level
                    
                    sama_entries += f'''
                    <article class="sama-entry" id="sama-{sama.sama_number}">
                        <div class="sama-id-row">
                            <span class="sama-id">
                                <a href="#sama-{sama.sama_number}">{parva.parva_number}.{kandah.kandah_number}.{sama.sama_number}</a>
                            </span>
                        </div>
                        {rik_html}
                        {mantra_html}
                        {audio_html}
                    </article>'''
                
                # Render accumulated footnotes for the Kandah
                kandah_footnotes_html = ""
                if kandah_all_footnotes:
                    fn_items = ""
                    for unique_id, display_num, text in kandah_all_footnotes:
                        fn_items += f'<div class="footnote-item" id="{unique_id}"><span class="footnote-ref">{display_num}</span><span class="footnote-text">{text}</span></div>'
                    
                    kandah_footnotes_html = f'''
                    <div class="footnotes">
                        <hr class="footnote-separator">
                        <div class="footnote-section">
                            {fn_items}
                        </div>
                    </div>'''
                
                html = f'''{self._get_html_head(f"{parva.title} - {kandah.title}", depth=2)}
<body>
    <div class="page-container">
        {self._get_sidebar_html(current_parva_id=parva.id, current_kandah_id=kandah.id, depth=2)}
        
        <main class="main-content">
            <nav class="breadcrumb">
                <a href="../../index.html">मुख्यपृष्ठम्</a>
                <span class="breadcrumb-separator">›</span>
                <span>{parva.title}</span>
                <span class="breadcrumb-separator">›</span>
                <span>{kandah.title}</span>
            </nav>
            
            <header class="page-header">
                <h1>{parva.title} - {kandah.title}</h1>
                <div class="page-meta">
                    <p class="page-subtitle">पर्व: {parva.parva_number} | खण्ड: {kandah.kandah_number}</p>
                    <span class="sama-count">साम: {len(kandah.samas)}</span>
                </div>
            </header>
            
            <div class="toc">
                <h4>खण्ड: {kandah.kandah_number} - सम्पूर्णम्</h4>
                <ul class="toc-list">
                    {toc_items}
                </ul>
            </div>
            
            {sama_entries}
            
            {kandah_footnotes_html}
            
            <footer class="footer">
                जैमिनीय सामवेद प्रकृति गानम्
            </footer>
        </main>
        
    </div>
    <script src="../../js/main.js"></script>
</body>
</html>'''
                
                with open(parva_dir / f'{kandah.kandah_number}.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                    
    def _generate_metadata_json(self):
        """Generate metadata.json for reference"""
        metadata = {
            "title": "जैमिनीय साम प्रकृति गानम्",
            "title_en": "Jaimineeya Sama Prakruti Ganam",
            "generated_at": self.generated_at,
            "hierarchy": "Parva → Kandah → Sama",
            "stats": {
                "total_parvas": len(self.parvas),
                "total_kandahs": sum(len(p.kandahs) for p in self.parvas),
                "total_samas": sum(sum(len(k.samas) for k in p.kandahs) for p in self.parvas)
            },
            "parvas": []
        }
        
        for parva in self.parvas:
            parva_data = {
                "id": parva.id,
                "number": parva.parva_number,
                "title": parva.title,
                "kandahs": []
            }
            for kandah in parva.kandahs:
                kandah_data = {
                    "id": kandah.id,
                    "number": kandah.kandah_number,
                    "title": kandah.title,
                    "sama_count": len(kandah.samas),
                    "samas": [
                        {
                            "id": sama.id,
                            "number": sama.sama_number,
                            "title": sama.title,
                            "audio_filename": sama.audio_filename
                        }
                        for sama in kandah.samas
                    ]
                }
                parva_data["kandahs"].append(kandah_data)
            metadata["parvas"].append(parva_data)
        
        with open(self.output_dir / 'metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)


# --- Main Entry Point ---
def main():
    """Main function to run the website generator"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate static website for Jaimineeya Samavedam',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Example usage:
  python generate_website.py
  python generate_website.py --source-file custom_input.txt
  python generate_website.py --output-dir ./my_website
        '''
    )
    
    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Default paths
    # Default paths
    default_source = project_root / 'data' / 'input' / 'Samhita_with_Rishi_Devata_Chandas.txt'
    # Changed default output to 'docs' for GitHub Pages support
    default_output = project_root / 'docs'
    default_audio = project_root / 'data' / 'input' / 'Audio_Placeholders'
    
    parser.add_argument(
        '--source-file', '-s',
        type=str,
        default=str(default_source),
        help='Path to the source text file (default: data/input/Samhita_with_Rishi_Devata_Chandas.txt)'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default=str(default_output),
        help='Output directory for generated website (default: docs)'
    )
    
    parser.add_argument(
        '--audio-dir', '-a',
        type=str,
        default=str(default_audio),
        help='Directory for audio placeholder folders (default: data/input/Audio_Placeholders)'
    )
    
    args = parser.parse_args()
    
    # Validate source file exists
    source_path = Path(args.source_file)
    if not source_path.exists():
        print(f"❌ Error: Source file not found: {source_path}")
        return 1
    
    print("=" * 60)
    print("  Jaimineeya Samavedam Website Generator (v2.0)")
    print("  Design: Inspired by rigveda.sanatana.in")
    print("=" * 60)
    print(f"\n📄 Source file: {source_path}")
    print(f"📁 Output directory: {args.output_dir}")
    print(f"🎵 Audio placeholders: {args.audio_dir}")
    print()
    
    # Parse the source file
    print("🔍 Parsing source file...")
    parser_obj = JSVParser(str(source_path))
    parvas = parser_obj.parse()
    
    # Print statistics
    total_kandahs = sum(len(p.kandahs) for p in parvas)
    total_samas = sum(sum(len(k.samas) for k in p.kandahs) for p in parvas)
    
    print(f"\n📊 Parsed Structure:")
    print(f"   • {len(parvas)} Parvas (पाठ)")
    print(f"   • {total_kandahs} Kandahs (खण्ड)")
    print(f"   • {total_samas} Samas (साम)")
    
    for parva in parvas:
        print(f"\n   {parva.parva_number}. {parva.title}")
        print(f"      └─ {len(parva.kandahs)} Kandahs, {sum(len(k.samas) for k in parva.kandahs)} Samas")
    
    # Generate website
    print("\n🏗️ Generating website (Rig Veda style)...")
    generator = WebsiteGenerator(parvas, args.output_dir, args.audio_dir)
    generator.generate()
    
    print("\n" + "=" * 60)
    print("  ✨ Website generation complete!")
    print("=" * 60)
    print(f"\nOpen {args.output_dir}/index.html to view the website.")
    
    return 0


if __name__ == '__main__':
    exit(main())
