"""
Source Text and AST Parser for Jaimineeya Website Generation
"""

import re
import json
from pathlib import Path
from typing import List, Optional, Dict, Any

from .models import Sama, Kandah, Parva
from .constants import AUDIO_FILENAME_FORMAT

try:
    from utils import extract_closing_mantras, devanagari_to_int
except ImportError:
    try:
        from src.utils import extract_closing_mantras, devanagari_to_int
    except ImportError:
        def extract_closing_mantras(c): return []
        def devanagari_to_int(s): return int(s)

try:
    from samam_utils import count_samams_with_fallback
except ImportError:
    def count_samams_with_fallback(text): 
        return len(re.findall(r'\(\d+\)', text))


class JSVParser:
    """Parses the Samhita source file (JSON or legacy structured text) into Parva -> Kandah -> Sama structure"""
    
    def __init__(self, source_file: str, procedure_index: dict = None):
        self.source_file = source_file
        self.procedure_index = procedure_index or {}
        self.metadata = {}
        self.parvas: List[Parva] = []
        self.current_parva: Optional[Parva] = None
        self.current_kandah: Optional[Kandah] = None
        self.current_sama: Optional[Sama] = None
        self.closing_mantras: List[str] = []

    def parse(self) -> List[Parva]:
        """Main parsing method - delegates based on file type"""
        if self.source_file.lower().endswith('.json'):
            parvas = self._parse_json()
        else:
            parvas = self._parse_text_file()
            
        # Post-process to ensure sama_number matches natural sequence IDs
        self._post_process_numbering()
        return parvas

    def _post_process_numbering(self):
        """
        Recalculate all sama_number properties to match the natural mantra sequence.
        This ensures that Search hits and Jump-to targets correctly align with anchors.
        """
        for parva in self.parvas:
            for kandah in parva.kandahs:
                running_mantra_count = 0
                for sama in kandah.samas:
                    sama.sama_number = running_mantra_count + 1
                    cnt = count_samams_with_fallback(sama.mantra_text)
                    if cnt == 0: cnt = 1
                    running_mantra_count += cnt

    def _parse_json(self) -> List[Parva]:
        """Parse JSON source file"""
        with open(self.source_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.metadata = data.get('meta', {})
        self.closing_mantras = data.get('closing_mantras', [])
            
        super_keys = sorted(data.get('supersection', {}).keys(), 
                          key=lambda x: int(x.split('_')[1]) if '_' in x else 0)
                          
        for ss_key in super_keys:
            ss_data = data['supersection'][ss_key]
            title = ss_data.get('supersection_title', ss_key)
            self._start_new_parva(ss_key, title)
            
            sec_keys = sorted([k for k in ss_data.get('sections', {}).keys() if k != 'count'],
                            key=lambda x: int(x.split('_')[1]) if '_' in x else 0)
                            
            for sec_key in sec_keys:
                sec_data = ss_data['sections'][sec_key]
                sec_title = sec_data.get('section_title', sec_key)
                self._start_new_kandah(sec_key, sec_title)
                
                sub_keys = sorted(sec_data.get('subsections', {}).keys(),
                                key=lambda x: int(x.split('_')[1]) if '_' in x else 0)
                                
                for sub_key in sub_keys:
                    sub_data = sec_data['subsections'][sub_key]
                    header_info = sub_data.get('header', {})
                    sama_title = header_info.get('header', '')
                    
                    self._start_new_sama(sub_key, sama_title)
                    
                    s: Optional[Sama] = self.current_sama
                    if s is not None:
                        s.rik_metadata = sub_data.get('rik_metadata', '')
                        s.saman_metadata = sub_data.get('saman_metadata', '')
                        s.rik_text = sub_data.get('rik_text', '')
                        
                        ms = sub_data.get('corrected-mantra_sets', [])
                        mantra_list = []
                        for m in ms:
                             if isinstance(m, dict):
                                 mantra_list.append(m.get('corrected-mantra', ''))
                        s.mantra_text = '\n'.join(mantra_list)
                        s.procedure_ref = sub_data.get('procedure_ref', {})
                        
                        fns = sub_data.get('footnotes', {})
                        fn_list = []
                        if isinstance(fns, dict):
                            for k, v in fns.items():
                                 fn_list.append(f"{k}: {v}")
                        s.footnotes = fn_list
                        
                        # Classification fields
                        s.saman_rishi = sub_data.get('saman_rishi', '')
                        s.saman_devata = sub_data.get('saman_devata', '')
                        s.saman_chandas = sub_data.get('saman_chandas', '')
                        s.rik_rishi = sub_data.get('rik_rishi', '')
                        s.rik_devata = sub_data.get('rik_devata', '')
                        s.rik_chandas = sub_data.get('rik_chandas', '')
                        s.rik_classifications = sub_data.get('rik_classifications', [])
                        s.rik_ids = sub_data.get('rik_ids', [])
                        if not s.rik_ids and sub_data.get('rik_id'):
                            s.rik_ids = [sub_data.get('rik_id')]
        
        self._finalize_current_sama()
        return self.parvas

    def _parse_text_file(self) -> List[Parva]:
        """Legacy Parsing method (Text File)"""
        content = self._read_file()
        
        from utils import extract_metadata_from_text
        self.metadata = extract_metadata_from_text(content)
        self.closing_mantras = extract_closing_mantras(content)
        
        lines = content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if '# Start of SuperSection Title --' in line:
                parva_id = self._extract_id(line, 'supersection_')
                i += 1
                title = lines[i].strip() if i < len(lines) else ""
                self._start_new_parva(parva_id, title)
                
            elif '# Start of Section Title --' in line:
                section_id = self._extract_id(line, 'section_')
                i += 1
                title = lines[i].strip() if i < len(lines) else ""
                self._start_new_kandah(section_id, title)
                
            elif '# Start of SubSection Title --' in line:
                subsection_id = self._extract_id(line, 'subsection_')
                i += 1
                title = lines[i].strip() if i < len(lines) else ""
                if self.current_sama and self.current_sama.id == subsection_id:
                    self.current_sama.title = title
                else:
                    self._start_new_sama(subsection_id, title)
                    
            elif '# Start of Rik Metadata --' in line:
                subsection_id = self._extract_id(line, 'subsection_')
                i += 1
                metadata = lines[i].strip() if i < len(lines) else ""
                self._ensure_sama_exists(subsection_id)
                if self.current_sama:
                    if self.current_sama.rik_metadata:
                        self.current_sama.rik_metadata += f"  {metadata}"
                    else:
                        self.current_sama.rik_metadata = metadata
                    
            elif '# Start of Rik Text --' in line:
                subsection_id = self._extract_id(line, 'subsection_')
                i += 1
                rik_text = lines[i].strip() if i < len(lines) else ""
                self._ensure_sama_exists(subsection_id)
                if self.current_sama:
                    self.current_sama.rik_text = rik_text
                    rik_nums = re.findall(r'(?:॥|\|\||।।|।|\|)\s*([\d०-९]+)\s*(?:॥|\|\||।।|।|\|)', rik_text)
                    if rik_nums:
                        self.current_sama.rik_ids.extend([devanagari_to_int(n) for n in rik_nums])
                    
            elif '#Start of Mantra Sets --' in line or '# Start of Mantra Sets --' in line:
                subsection_id = self._extract_id(line, 'subsection_')
                mantra_lines = []
                i += 1
                while i < len(lines) and '#End of Mantra Sets' not in lines[i] and '# End of Mantra Sets' not in lines[i]:
                    mantra_lines.append(lines[i])
                    i += 1
                if self.current_sama:
                    self.current_sama.mantra_text = '\n'.join(mantra_lines).strip()
                continue
                
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
        sanitized = re.sub(r'[^\w\u0900-\u097F]', '', text)
        return sanitized[:30] if sanitized else "unknown"
