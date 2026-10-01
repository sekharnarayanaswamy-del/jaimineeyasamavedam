"""
Core static website generator orchestrator for Jaimineeya Samaveda
"""

import os
import re
import json
import shutil
import markdown
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Optional, Any

from .models import Sama, Kandah, Parva
from .constants import SITE_CONFIG, AUDIO_FILENAME_FORMAT
from .formatters import format_rik_text_html, format_mantra_text_html
from .search import (
    clean_text_for_search,
    strip_diacritics,
    transliterate_to_latin,
    generate_search_index_file
)
from .assets import generate_styles_css, generate_main_js

try:
    from utils import get_generated_metadata, normalize_to_dd_mm_yyyy
except ImportError:
    try:
        from src.utils import get_generated_metadata, normalize_to_dd_mm_yyyy
    except ImportError:
        def get_generated_metadata(): return {"version": "3.0", "generated_at": ""}
        def normalize_to_dd_mm_yyyy(d): return d

try:
    from samam_utils import count_samams_with_fallback
except ImportError:
    try:
        from src.samam_utils import count_samams_with_fallback
    except ImportError:
        def count_samams_with_fallback(text):
            return len(re.findall(r'\(\d+\)', text))


class WebsiteGenerator:
    """Generates static HTML website from parsed data - Rig Veda style"""
    
    def __init__(self, parvas: List[Parva], output_dir: str, audio_dir: str, mode: str = 'samhita', custom_title: str = None, font: str = 'AdishilaVedic', font_sans: str = 'AdishilaSanVedic', metadata: Dict = None, closing_mantras: List[str] = None, output_mode: str = 'combined', kpully: bool = False):
        self.parvas = parvas
        self.output_dir = Path(output_dir)
        self.audio_dir = Path(audio_dir)
        self.mode = mode
        self.font = font
        self.font_sans = font_sans
        self.closing_mantras = closing_mantras or []
        self.output_mode = output_mode or 'combined'
        self.kpully = bool(kpully)
        
        # Content inclusion flags
        self.has_riks = self.output_mode in ('combined', 'rik', 'rik_nometa')
        self.has_samams = self.output_mode in ('combined', 'samam', 'samam_nometa')
        self.has_metadata = self.output_mode in ('combined', 'samam', 'rik')
        
        self.is_malayalam = (self.mode == 'malayalam' or 'malayalam' in str(self.output_dir).lower() or 'malayalam' in str(self.font).lower())
        if self.is_malayalam:
            if self.mode != 'malayalam':
                self.mode = 'malayalam'
            if self.font == 'AdishilaVedic':
                self.font = 'Noto Serif Malayalam'
                self.font_sans = 'Noto Sans Malayalam'
            self.config = SITE_CONFIG['malayalam'].copy()
        else:
            self.config = SITE_CONFIG.get(mode, SITE_CONFIG['samhita']).copy()
        
        if custom_title:
            self.config['title_sa'] = custom_title
            self.config['footer_sa'] = custom_title
        
        self.labels = self._get_labels()
        
        sys_meta = get_generated_metadata()
        raw_generated_at = metadata.get("generated_at", sys_meta["generated_at"]) if metadata else sys_meta["generated_at"]
        clean_generated_at = normalize_to_dd_mm_yyyy(raw_generated_at)
        
        self.metadata = {
            "version": metadata.get("version", sys_meta["version"]) if metadata else sys_meta["version"],
            "generated_at": clean_generated_at,
            "last_updated": datetime.now().strftime("%d-%m-%Y")
        }
        self.generated_at = clean_generated_at
        
        self.rishi_index = {}
        self.devata_index = {}
        self.chandas_index = {}
        self.header_index = []
        self.total_riks_classified = 0

    def _get_labels(self):
        if getattr(self, 'is_malayalam', False):
            return {
                'parva': 'പാഠഃ',
                'kandah': 'ഖണ്ഡഃ',
                'sama': 'സാമ:',
                'arsheyam': 'ആർഷേയമ്',
                'rik': 'ഋക്',
                'home': 'മുഖ്യപുറം (Home)',
                'search': 'അന്വേഷണം (Search)',
                'jump_placeholder': 'ഉദാ. 1.1.1',
                'indices': 'മറ്റു വർഗ്ഗീകരണങ്ങൾ (Indices)',
                'rishi': 'ഋഷയഃ',
                'devata': 'ദേവതാഃ',
                'chandas': 'ഛന്ദാംസി',
                'anukramanika': 'അനുക്രമണിക',
                'varnanukraman': 'വർണ്ണാനുക്രമണം (Alphabetical Index)',
                'top_20': 'പ്രമുഖ (Top 20)',
            }
        else:
            return {
                'parva': 'पर्व:',
                'kandah': 'खण्ड:',
                'sama': 'साम:',
                'arsheyam': 'आर्षेयम्',
                'rik': 'ऋक्',
                'home': 'मुख्यपृष्ठम् (Home)',
                'search': 'अन्वेषणम् (Search)',
                'jump_placeholder': 'e.g. 1.1.1 or 1.45',
                'indices': 'अन्य वर्गीकरणम् (Indices)',
                'rishi': 'ऋषयः',
                'devata': 'देवताः',
                'chandas': 'छन्दांसि',
                'anukramanika': 'अनुक्रमणिका',
                'varnanukraman': 'वर्णानुक्रमण (Varnanukraman)',
                'top_20': 'प्रमुखाः (Top 20)',
            }
        
    def generate(self):
        """Generate all website files"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / 'css').mkdir(exist_ok=True)
        (self.output_dir / 'js').mkdir(exist_ok=True)
        (self.output_dir / 'kandah').mkdir(exist_ok=True)
        
        # Copy JaimineeyaSwara font if in malayalam mode or kpully mode
        if self.is_malayalam or self.kpully:
            (self.output_dir / 'fonts').mkdir(exist_ok=True)
            src_font = Path('fonts/JaimineeyaSwara.ttf')
            if src_font.exists():
                shutil.copy2(src_font, self.output_dir / 'fonts' / 'JaimineeyaSwara.ttf')
        
        self._create_audio_directories()
        self._collect_indices()
        
        self._generate_css()
        self._generate_js()
        self._generate_search_index()
        self._generate_homepage()
        self._generate_indices()
        self._generate_kandah_pages()
        self._generate_procedure_pages()
        self._generate_metadata_json()
        
        print(f"  Website generated at: {self.output_dir}")
        print(f"  Audio placeholder directories created at: {self.audio_dir}")
        
    def _create_audio_directories(self):
        """Create audio placeholder directories for each Parva"""
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        for parva in self.parvas:
            parva_folder = self._sanitize_foldername(parva.title)
            (self.audio_dir / parva_folder).mkdir(exist_ok=True)
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
        """Generate CSS stylesheet matching standalone HTML viewer swara modifier styling"""
        css = generate_styles_css(self.font, self.font_sans, self.is_malayalam, self.kpully)
        with open(self.output_dir / 'css' / 'styles.css', 'w', encoding='utf-8') as f:
            f.write(css)

    def _generate_js(self):
        """Generate JavaScript for interactivity with deterministic navigation"""
        js = generate_main_js()
        with open(self.output_dir / 'js' / 'main.js', 'w', encoding='utf-8') as f:
            f.write(js)

    def _clean_text_for_search(self, html_text: str) -> str:
        return clean_text_for_search(html_text)

    def _strip_diacritics(self, text: str) -> str:
        return strip_diacritics(text)

    def _transliterate_to_latin(self, text: str) -> str:
        return transliterate_to_latin(text)

    def _generate_search_index(self):
        generate_search_index_file(self.parvas, self.output_dir, self.has_riks, self.has_samams, self.has_metadata)

    def _get_html_head(self, title: str, depth: int = 0) -> str:
        """Generate HTML head section"""
        prefix = '../' * depth
        full_title = f"{title} | {self.config['title_sa']}" if title != self.config['title_sa'] else title
        
        if getattr(self, 'is_malayalam', False):
            google_fonts = '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Noto+Sans+Malayalam:wght@400;500;600;700&family=Noto+Serif+Malayalam:wght@400;500;600;700&display=swap" rel="stylesheet">'
        else:
            google_fonts = '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Noto+Sans+Devanagari:wght@400;500;600&family=Noto+Serif+Devanagari:wght@400;500;600&display=swap" rel="stylesheet">'
        
        return f'''<!DOCTYPE html>
<html lang="sa">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{self.config['meta_desc']}">
    <meta name="keywords" content="{self.config['keywords']}">
    <meta name="version" content="{self.metadata['version']}">
    <title>{full_title}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    {google_fonts}
    <link rel="stylesheet" href="{prefix}css/styles.css?v={int(datetime.now().timestamp())}">
</head>'''

    def _get_top_nav_html(self, depth=0):
        """Get HTML for top-right navigation links"""
        prefix = '../' * depth
        L = self.labels
        return f'''
            <nav class="top-nav">
                <a href="https://jaimineeyasamavedam.org/"><i class="nav-icon">🏠</i>{L['home']}</a>
                <a href="#"><i class="nav-icon">🔍</i>{L['search']}</a>
            </nav>'''

    def _get_sidebar_html(self, current_parva_id: str = "", current_kandah_id: str = "", depth: int = 0) -> str:
        """Generate left sidebar with navigation"""
        prefix = '../' * depth
        L = self.labels
        
        # Parva links (like Mandala in Rig Veda)
        parva_links = ""
        for parva in self.parvas:
            active = 'active' if parva.id == current_parva_id else ''
            parva_links += f'<a href="{prefix}kandah/{parva.id}/1.html" class="parva-link {active}">{parva.parva_number}</a>\n'
        
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
                    kandah_links += f'<a href="{prefix}kandah/{current_parva_id}/{kandah.kandah_number}.html" class="kandah-link {active}">{kandah.kandah_number}</a>\n'
                
                kandah_section = f'''
                <div class="nav-section">
                            <h3>{L['kandah']} <span class="number">({len(current_parva.kandahs)})</span></h3>
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
                            cnt = 0
                            if sama.mantra_text:
                                matches = re.findall(r'(?:\|\||॥)\s*[\d०-९]+\s*(?:\|\||॥)', sama.mantra_text)
                                cnt = len(matches)
                            
                            if cnt == 0: cnt = 1
                            range_end = current_samam_start + cnt - 1
                            label_text = f"{current_samam_start}–{range_end}" if cnt > 1 else f"{current_samam_start}"
                            sama_links += f'<a href="#sama-{current_samam_start}" class="sama-link">{label_text}</a>\n'
                            total_real_samams += cnt
                            current_samam_start = range_end + 1
                        
                        sama_section = f'''
                        <div class="nav-section">
                            <h3>{L['sama']} <span class="number">({total_real_samams})</span></h3>
                            <div class="nav-links">
                                {sama_links}
                            </div>
                        </div>'''
        
        return f'''<aside class="sidebar-left">
    <div class="logo">
        <a href="{prefix}index.html">
            <div class="logo-text">{self.config['title_sa']}</div>
            <div class="logo-subtitle">{self.config['title_en']}</div>
            <div class="logo-version" style="font-size: 0.85em; color: var(--text-secondary); margin-top: 4px;">v{self.metadata['version']}</div>
        </a>
    </div>
    
    <div class="nav-section">
        <h3>{L['parva']}</h3>
        <div class="nav-links">
            {parva_links}
        </div>
    </div>
    {kandah_section}
    {sama_section}
    
    <div class="nav-section">
        <h3>Jump to</h3>
        <input type="text" class="jump-input" id="sidebar-jump" placeholder="{L['jump_placeholder']}">
    </div>

    <div class="nav-section">
        <a href="#" class="search-btn">
            <i class="nav-icon">🔍</i> {L['search']}
        </a>
    </div>

    <div class="sidebar-footer">
        <a href="{prefix}index.html" class="footer-btn">{self.mode.capitalize()} Home</a>
        {f'<a href="{prefix}classification/anukramanika.html" class="footer-btn">{L["anukramanika"]}</a>' if self.mode == "collection" else ""}
        {f"""<a href="{prefix}classification/rishi.html" class="footer-btn">{L['rishi']}</a>
        <a href="{prefix}classification/devata.html" class="footer-btn">{L['devata']}</a>
        <a href="{prefix}classification/chandas.html" class="footer-btn">{L['chandas']}</a>""" if self.mode != 'collection' and getattr(self, 'has_metadata', True) else ""}
    </div>
</aside>'''

    def _get_jump_sidebar_html(self, samas: List[Sama]) -> str:
        """Generate right sidebar with jump links"""
        L = self.labels
        jump_links = ""
        for sama in samas:
            jump_links += f'<a href="#sama-entry-{sama.sama_number}" class="sama-link">{sama.sama_number}</a>\n'
        
        return f'''<aside class="sidebar-right">
    <h3>{L['sama']} <span class="number">({len(samas)})</span></h3>
    <div class="jump-links">
        {jump_links}
    </div>
</aside>'''


    def _generate_homepage(self):
        """Generate the homepage"""
        L = self.labels
        total_kandahs = sum(len(p.kandahs) for p in self.parvas)
        total_arsheyams = sum(len(k.samas) for p in self.parvas for k in p.kandahs)
        total_samas = sum(
            count_samams_with_fallback(s.mantra_text)
            for p in self.parvas for k in p.kandahs for s in k.samas
        )
        
        parva_sections = ""
        for parva in self.parvas:
            parva_clean = parva.title.replace('॥', '').replace('||', '').replace('|', '').strip()
            kandah_cards = ""
            parva_sama_count = 0
            for kandah in parva.kandahs:
                kandah_sama_count = sum(
                    count_samams_with_fallback(s.mantra_text)
                    for s in kandah.samas
                )
                parva_sama_count += kandah_sama_count
                kandah_clean = kandah.title.replace('॥', '').replace('||', '').replace('|', '').strip()
                
                kandah_card_count = f"{kandah_sama_count} {L['sama'].replace(':', '')}" if getattr(self, 'has_samams', True) else f"{len(kandah.samas)} {L['arsheyam']}"
                kandah_cards += f'''
                <a href="kandah/{parva.id}/{kandah.kandah_number}.html" class="kandah-card">
                    <div class="number">{kandah.kandah_number}</div>
                    <div class="title">{kandah_clean}</div>
                    <div class="count">{kandah_card_count}</div>
                </a>'''
            
            parva_sections += f'''
            <section class="parva-section">
                <h2>{parva.parva_number}. {parva_clean}</h2>
                <div class="kandah-grid">
                    {kandah_cards}
                </div>
            </section>'''
        
        html = f'''{self._get_html_head(self.config['title_sa'])}
<body>
    <div class="page-container">
        {self._get_sidebar_html()}
        
        <main class="main-content" style="max-width: 1200px;">
            {self._get_top_nav_html()}
            <div class="home-hero">
                <h1>{self.config['title_sa']}</h1>
                <p class="subtitle">{self.config['title_en']}</p>
                
                <div class="stats-row">
                    <div class="stat-item">
                        <div class="stat-value">{len(self.parvas)}</div>
                        <div class="stat-label">{L['parva']} (Parva)</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{total_kandahs}</div>
                        <div class="stat-label">{L['kandah']} (Kandah)</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{total_arsheyams}</div>
                        <div class="stat-label">{L['arsheyam']} (Arsheyam)</div>
                    </div>
                    {f"""<div class="stat-item">
                        <div class="stat-value">{self.total_riks_classified}</div>
                        <div class="stat-label">{L['rik']} (Rik)</div>
                    </div>""" if getattr(self, 'has_riks', True) else ""}
                    {f"""<div class="stat-item">
                        <div class="stat-value">{total_samas}</div>
                        <div class="stat-label">{L['sama']} (Sama)</div>
                    </div>""" if getattr(self, 'has_samams', True) else ""}
                </div>
                
                {f"""
                <div class="anya-vargeekaran-card">
                    <h2>{L['indices']}</h2>
                    <div class="index-grid-homepage">
                        <a href="classification/rishi.html" class="index-link-item">
                            <span class="title">{L['rishi']}</span>
                            <span class="stats">({len(self.rishi_index)})</span>
                        </a>
                        <a href="classification/devata.html" class="index-link-item">
                            <span class="title">{L['devata']}</span>
                            <span class="stats">({len(self.devata_index)})</span>
                        </a>
                        <a href="classification/chandas.html" class="index-link-item">
                            <span class="title">{L['chandas']}</span>
                            <span class="stats">({len(self.chandas_index)})</span>
                        </a>
                        <a href="classification/anukramanika.html" class="index-link-item">
                            <span class="title">{L['anukramanika']}</span>
                            <span class="stats">({len(self.header_index)})</span>
                        </a>
                    </div>
                </div>""" if (self.mode != 'collection' and getattr(self, 'has_metadata', True)) else ""}
            </div>
            
            {parva_sections}
            
            <footer class="footer">
                {self.config['footer_sa']}<br>
                Generated on {self.generated_at}
            </footer>
        </main>
    </div>
    <div class="search-modal" id="search-modal">
        <div class="search-modal-content">
            <div class="search-modal-header">
                <h3>{L['search']}</h3>
                <button class="search-close" id="search-close">&times;</button>
            </div>
            <div class="search-input-container">
                <input type="text" class="search-input" id="search-input" placeholder="Search (Malayalam, Devanagari, English, IAST)...">
                <span class="search-hint">Search for Mantras, Rishis, Devatas, or Chandas</span>
            </div>
            <div class="search-results" id="search-results"></div>
        </div>
    </div>
    <div class="search-overlay" id="search-overlay"></div>
    <script src="search-index.js"></script>
    <script src="js/main.js?v={int(datetime.now().timestamp())}"></script>
</body>
</html>'''
        
        with open(self.output_dir / 'index.html', 'w', encoding='utf-8') as f:
            f.write(html)

    def _to_devanagari_num(self, n: Any) -> str:
        """Convert a number to Devanagari numerals"""
        devanagari_digits = '०१२३४५६७८९'
        return "".join(devanagari_digits[int(d)] for d in str(n) if d.isdigit())

    def _normalize_index_key(self, text: str) -> str:
        """Normalize metadata keys to merge duplicates (spaces, punctuation)"""
        if not text:
            return ""
        
        # Remove common surrounding punctuation/whitespace
        # Keep the Devanagari Visarga (ः) as it's part of the name
        text = text.strip(' \t\n\r.|॥,:;()\'"')
        
        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _collect_indices(self):
        """Collect data for all indices and track unique Rik counts"""
        self.rishi_index = defaultdict(list)
        self.devata_index = defaultdict(list)
        self.chandas_index = defaultdict(list)
        self.header_index = [] 
        
        self.total_riks_classified = 0
        all_rik_nums = set()
        
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
                    if sama.rik_classifications:
                        for c in sama.rik_classifications:
                            rik_num = c.get('Global_Rik_Num')
                            if rik_num: all_rik_nums.add(rik_num)
                            
                            ref = {'link': link_rel, 'location': location, 'rik_num': rik_num}
                            
                            if c.get('Rishi'):
                                key = self._normalize_index_key(c['Rishi'])
                                if key: self.rishi_index[key].append(ref)
                            if c.get('Devata'):
                                key = self._normalize_index_key(c['Devata'])
                                if key: self.devata_index[key].append(ref)
                            if c.get('Chandas'):
                                key = self._normalize_index_key(c['Chandas'])
                                if key: self.chandas_index[key].append(ref)
        
        self.total_riks_classified = len(all_rik_nums)

    def _generate_indices(self):
        """Generate all index pages"""
        # (Already collected by generate())
        
        # Create classification dir
        (self.output_dir / 'classification').mkdir(exist_ok=True)
        
        self._generate_anukramanika_page()
        self._generate_index_page_generic("ऋषयः (Rishis)", self.rishi_index, "rishi.html", item_label="Rishis", show_top_20=True)
        self._generate_index_page_generic("देवताः (Devatas)", self.devata_index, "devata.html", item_label="Devatas", show_top_20=True)
        self._generate_index_page_generic("छन्दांसि (Chandas)", self.chandas_index, "chandas.html", item_label="Chandas", show_top_20=True)

    def _generate_anukramanika_page(self):
        """Generate a dedicated page for the Alphabetical Headers Index"""
        total_samas = sum(count_samams_with_fallback(s.mantra_text) for p in self.parvas for k in p.kandahs for s in k.samas)
        total_arsheyams = sum(len(k.samas) for p in self.parvas for k in p.kandahs)

        html = f'''{self._get_html_head("सामानुक्रमणिका (Alphabetical Index)", depth=1)}
<body>
    <div class="page-container">
        {self._get_sidebar_html(depth=1)}
        <main class="main-content" style="max-width: 1200px;">
            {self._get_top_nav_html(depth=1)}
            <div class="page-header">
                <h1>सामानुक्रमणिका (Alphabetical Index)</h1>
                <div class="stats-summary" style="margin-top: 0.3rem; color: var(--text-muted); font-size: 1.1rem; font-family: '{self.font}', serif;">
                    {total_arsheyams} आर्षेयम् • {total_samas} साम • {self.total_riks_classified} ऋचः
                </div>
            </div>
            
            <section class="alphabetical-section">
                {self._get_header_index_html()}
            </section>
        </main>
    </div>
    <div class="search-modal" id="search-modal">
        <div class="search-modal-content">
            <div class="search-modal-header">
                <h3>अन्वेषणम् (Search)</h3>
                <button class="search-close" id="search-close">&times;</button>
            </div>
            <div class="search-input-container">
                <input type="text" class="search-input" id="search-input" placeholder="Search (Devanagari, English, IAST)...">
                <span class="search-hint">Search for Mantras, Rishis, Devatas, or Chandas in Devanagari or English</span>
            </div>
            <div class="search-results" id="search-results"></div>
        </div>
    </div>
    <div class="search-overlay" id="search-overlay"></div>
    <script src="../search-index.js"></script>
    <script src="../js/main.js?v={int(datetime.now().timestamp())}"></script>
</body>
</html>'''
        with open(self.output_dir / 'classification' / 'anukramanika.html', 'w', encoding='utf-8') as f:
            f.write(html)

    def _generate_index_page_generic(self, title, data_dict, filename, item_label="Items", show_top_20=False):
        """Generate an enhanced index page with 3-column row grid layout"""
        total_items = len(data_dict)
        # Use a set to count unique arsheyam containers covered by this classification
        unique_arsheyams = {r['location'] for refs in data_dict.values() for r in refs}
        total_arsheyams = len(unique_arsheyams)
        
        # Determine Sanskrit label for items
        item_trans = item_label
        if "rishi" in title.lower(): item_trans = "ऋषयः"
        elif "devata" in title.lower(): item_trans = "देवताः"
        elif "chanda" in title.lower(): item_trans = "छन्दांसि"
        
        # We also want to show the global Arsheyam count if needed, 
        # but the request says show 722 if it's the global count.
        global_arsheyams = sum(len(k.samas) for p in self.parvas for k in p.kandahs)

        # 2. Prepare Top 20 (Prominent Items)
        top_20_html = ""
        if show_top_20:
            # Sort by count descending
            sorted_by_count = sorted(data_dict.items(), key=lambda x: len(x[1]), reverse=True)[:20]
            
            cards_html = ""
            for i, (name, refs) in enumerate(sorted_by_count, 1):
                safe_id = f"term-{name.replace(' ', '_')}" 
                cards_html += f'''
                <a href="#{safe_id}" class="rishi-card">
                    <div class="rishi-rank">{i}</div>
                    <div class="rishi-info">
                        <span class="rishi-name">{name}</span>
                    </div>
                    <div class="rishi-count">{len(refs)} ऋचः</div>
                </a>'''
            
            top_20_html = ""
            if len(data_dict) > 20:
                cards_html += f'''
                <a href="#char-rest" class="rishi-card rest-card">
                    <div class="rishi-rank">...</div>
                    <div class="rishi-info">
                        <span class="rishi-name">शिष्टाः / वर्णानुक्रमण</span>
                        <div class="rishi-count">Alphabetical Rest ↓</div>
                    </div>
                </a>'''
            
            top_20_html = f'''
            <section class="index-summary-section">
                <h2 class="index-section-header">प्रमुखाः {title.split(' ')[0]} (Top 20)</h2>
                <div class="top-20-grid">
                    {cards_html}
                </div>
            </section>'''

        # 3. Prepare Alphabetical Rest
        alpha_groups = defaultdict(list)
        for key in sorted(data_dict.keys()):
            char = key[0] if key else '?'
            alpha_groups[char].append(key)
            
        alpha_nav_html = ""
        for char in sorted(alpha_groups.keys()):
            count = len(alpha_groups[char])
            alpha_nav_html += f'''
            <a href="#char-{char}" class="alpha-btn">
                <span class="alpha-char">{char}</span>
                <span class="alpha-count">{count}</span>
            </a>'''
            
        # 4. List Items in Grid
        list_html = ""
        for char in sorted(alpha_groups.keys()):
            grid_items_html = ""
            for key in alpha_groups[char]:
                refs = data_dict[key]
                
                # Deduplicate locations
                unique_refs = []
                seen_locs = set()
                for r in refs:
                    if r['location'] not in seen_locs:
                        unique_refs.append(r)
                        seen_locs.add(r['location'])
                
                refs_links = " ".join([f'<a href="{r["link"]}">{r["location"]}</a>' for r in unique_refs])
                term_id = f"term-{key.replace(' ', '_')}"
                
                grid_items_html += f'''
                <div class="index-list-item" id="{term_id}">
                    <div style="display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.75rem; margin-bottom: 0.2rem;">
                        <span class="item-name" style="color: var(--primary-maroon); min-width: fit-content;">{key}</span>
                        <span class="item-count">({len(refs)})</span>
                    </div>
                    <div class="item-refs">
                        {refs_links}
                    </div>
                </div>'''
            
            list_html += f'''
            <div class="index-char-group" id="char-{char}">
                <div class="index-char-title">{char}</div>
                <div class="index-items-grid">
                    {grid_items_html}
                </div>
            </div>'''

        html = f'''{self._get_html_head(title, depth=1)}
<body>
    <div class="page-container">
        {self._get_sidebar_html(depth=1)}
        <main class="main-content" style="max-width: 1200px;">
            {self._get_top_nav_html(depth=1)}
            <div class="page-header">
                <h1>{title}</h1>
                <div class="stats-summary" style="margin-top: 0.3rem; color: var(--text-muted); font-size: 1.1rem; font-family: '{self.font}', serif;">
                    {total_items} {item_trans} • {total_arsheyams} आर्षेयम्
                </div>
            </div>
            
            {top_20_html}
            
            <section class="alphabetical-section" id="char-rest">
                <h2 class="index-section-header">वर्णानुक्रमण (Varnanukraman)</h2>
                <div class="alphabet-nav">
                    {alpha_nav_html}
                </div>
                
                <div class="index-list-container">
                    {list_html}
                </div>
            </section>
        </main>
    </div>
    <div class="search-modal" id="search-modal">
        <div class="search-modal-content">
            <div class="search-modal-header">
                <h3>अन्वेषणम् (Search)</h3>
                <button class="search-close" id="search-close">&times;</button>
            </div>
            <div class="search-input-container">
                <input type="text" class="search-input" id="search-input" placeholder="Search (Devanagari, English, IAST)...">
                <span class="search-hint">Search for Mantras, Rishis, Devatas, or Chandas in Devanagari or English</span>
            </div>
            <div class="search-results" id="search-results"></div>
        </div>
    </div>
    <div class="search-overlay" id="search-overlay"></div>
    <script src="../search-index.js"></script>
    <script src="../js/main.js?v={int(datetime.now().timestamp())}"></script>
</body>
</html>'''
        with open(self.output_dir / 'classification' / filename, 'w', encoding='utf-8') as f:
            f.write(html)

    def _get_header_index_html(self):
        """Generate common HTML for Headers Index (nav + list)"""
        # Group by starting letter
        alpha_groups = defaultdict(list)
        for item in sorted(self.header_index, key=lambda x: x['text']):
            char = item['text'][0] if item['text'] else '?'
            alpha_groups[char].append(item)
            
        # 1. Alphabet Nav
        alpha_nav_html = ""
        for char in sorted(alpha_groups.keys()):
            count = len(alpha_groups[char])
            alpha_nav_html += f'''
            <a href="#char-{char}" class="alpha-btn">
                <span class="alpha-char">{char}</span>
                <span class="alpha-count">{count}</span>
            </a>'''
            
        alpha_nav_section = f'''
        <div class="alphabet-nav">
            {alpha_nav_html}
        </div>'''
        
        # 2. List Grid
        list_html = ""
        for char in sorted(alpha_groups.keys()):
            grid_items_html = ""
            for item in alpha_groups[char]:
                grid_items_html += f'''
                <a href="{item["link"]}" class="index-item-card simple-card">
                    <div class="item-main">
                        <div class="item-name">{item["text"]}</div>
                        <div class="item-count-badge">{item["location"]}</div>
                    </div>
                </a>'''
            
            list_html += f'''
            <div class="index-char-group" id="char-{char}">
                <div class="index-char-title">{char}</div>
                <div class="index-items-grid header-index-grid">
                    {grid_items_html}
                </div>
            </div>'''
            
        return f'''
        {alpha_nav_section}
        <div class="index-list-container">
            {list_html}
        </div>'''

            
    def _generate_kandah_pages(self):
        """Generate individual Kandah pages with Samas (like Sukta pages in Rig Veda)"""
        for p_idx, parva in enumerate(self.parvas):
            # Create parva directory
            parva_dir = self.output_dir / 'kandah' / parva.id
            parva_dir.mkdir(parents=True, exist_ok=True)
            
            for k_idx, kandah in enumerate(parva.kandahs):
                # Build Table of Contents
                toc_items = ""
                for sama in kandah.samas:
                    toc_items += f'<li><a href="#sama-{sama.sama_number}">{parva.parva_number}.{kandah.kandah_number}.{sama.sama_number}</a></li>\n'
                
                # Accumulator State for Kandah (Global Footnotes)
                kandah_counter = {'val': 0}
                kandah_seen_footnotes = {}  # content -> (id, display_num)
                kandah_all_footnotes = []   # list of (id, display_num, text)
                
                # Tracking Rik occurrences for unique anchors
                rik_occurrence_map = defaultdict(int)

                # Build Sama entries
                sama_entries = ""
                for sama in kandah.samas:
                    # Update: reliance on parser-assigned sama.sama_number which 
                    # now matches the starting mantra sequence ID.
                    # Parse footnote dict for this sama
                    current_footnotes_dict = {}
                    if sama.footnotes:
                        for fn in sama.footnotes:
                            # Parse "sN - text" or "sN : text"
                            # Removed local 'import re' to avoid UnboundLocalError
                            parts = re.match(r'(s\d+)\s*[-–—:]\s*(.*)', fn)
                            if parts:
                                current_footnotes_dict[parts.group(1)] = parts.group(2)
                            else:
                                # Fallback if format is just "s1 text" or other
                                # Try to grab sN at start
                                parts = re.match(r'(s\d+)\s+(.*)', fn)
                                if parts:
                                    current_footnotes_dict[parts.group(1)] = parts.group(2)
                    
                    
                    # Rik metadata (displayed above Rik text - in purple like renderPDF.py)
                    rik_metadata_html = ""
                    if sama.rik_metadata and getattr(self, 'has_metadata', True):
                        # Clean existing dandas/dots to prevent double symbols
                        # Added single danda '।' (U+0964) to the strip set
                        clean_meta = sama.rik_metadata.strip(' .|॥।\n\r\t')
                        if clean_meta:
                            # Normalize all internal danda variations (| || । ॥) to single '॥'
                            # Also handles spacing around them
                            # Removed local 'import re'
                            clean_meta = re.sub(r'\s*[|॥।]+\s*', ' ॥ ', clean_meta)
                            rik_metadata_html = f'<div class="rik-metadata">॥ {clean_meta} ॥</div>'
                    
                    # Rik text
                    rik_html = ""
                    if sama.rik_text and getattr(self, 'has_riks', True):
                        formatted_rik, _ = format_rik_text_html(sama.rik_text, current_footnotes_dict, kandah_counter, kandah_seen_footnotes, kandah_all_footnotes)
                        rik_html = f'''
                        <div class="rik-box">
                            {rik_metadata_html}
                            <div class="rik-text sanskrit-text">{formatted_rik}</div>
                        </div>'''
                    
                    # Sama title and metadata (displayed above Sama/Mantra text - in green)
                    sama_header_items = []
                    if getattr(self, 'has_metadata', True):
                        if sama.title:
                            # Clean existing dandas/dots - Added single danda '।'
                            clean_title = sama.title.strip(' .|॥।\n\r\t')
                            if clean_title:
                                # Normalize all internal danda variations
                                clean_title = re.sub(r'\s*[|॥।]+\s*', ' ॥ ', clean_title)
                                sama_header_items.append(f'<div class="sama-header-text">॥ {clean_title} ॥</div>')
                        
                        # Samam Metadata (render if present, also in green)
                        if sama.saman_metadata:
                            clean_smeta = sama.saman_metadata.strip(' .|॥।\n\r\t')
                            if clean_smeta:
                                clean_smeta = re.sub(r'\s*[|॥।]+\s*', ' ॥ ', clean_smeta)
                                sama_header_items.append(f'<div class="sama-metadata-text">॥ {clean_smeta} ॥</div>')
                    
                    sama_header_html = f'<div class="sama-header-container">{"".join(sama_header_items)}</div>' if sama_header_items else ""

                    # Mantra text with Sama header above it
                    mantra_html = ""
                    if sama.mantra_text and getattr(self, 'has_samams', True):
                        formatted_mantra, _ = format_mantra_text_html(sama.mantra_text, current_footnotes_dict, kandah_counter, kandah_seen_footnotes, kandah_all_footnotes)
                        mantra_html = f'''
                        <div class="mantra-box">
                            {sama_header_html}
                            <div class="mantra-container sanskrit-large">{formatted_mantra}</div>
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
                    
                    if getattr(self, 'has_samams', True):
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
                    
                    if getattr(self, 'has_riks', True):
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
                    
                    # Generate Rik Anchors for Jump Navigation
                    rik_anchor_tags = ""
                    for rid in sama.rik_ids:
                        rik_occurrence_map[rid] += 1
                        occ = rik_occurrence_map[rid]
                        anchor_id = f"rik-{rid}" if occ == 1 else f"rik-{rid}_{occ}"
                        rik_anchor_tags += f'<span id="{anchor_id}" class="rik-anchor"></span>'

                    # Use parser-assigned sama_number as the anchor start
                    start_samam_for_entry = sama.sama_number
                    verse_count = count_samams_with_fallback(sama.mantra_text)
                    if verse_count == 0: verse_count = 1
                    
                    # Generate unique anchors for EVERY verse number in the current range
                    verse_anchors = ""
                    for s_num in range(start_samam_for_entry, start_samam_for_entry + verse_count):
                        verse_anchors += f'<span id="sama-{s_num}" class="sama-anchor"></span>'
                    
                    sama_entries += f'''
                    {verse_anchors}
                    <article class="sama-entry" id="sama-entry-{sama.sama_number}" data-sama-start="{start_samam_for_entry}">
                        {rik_anchor_tags}
                        <div class="sama-id-row">
                            <span class="sama-id">
                                <a href="#sama-entry-{sama.sama_number}">{parva.parva_number}.{kandah.kandah_number}.{sama.sama_number}</a>
                            </span>
                        </div>
                        
                        <!-- Classification / Vargeekaran Section -->
                        {f"""<div class="classification-container">
                            <table class="classification-table">
                                <thead>
                                    <tr>
                                        <th>Global #</th>
                                        <th>ऋषिः (Rishi)</th>
                                        <th>देवता (Devata)</th>
                                        <th>छन्दः (Chandas)</th>
                                    </tr>
                                </thead>
                                {"".join([f'''
                                    <tr>
                                        <td><span class="number">{c['Global_Rik_Num']}</span></td>
                                        <td class="class-value">{c['Rishi']}</td>
                                        <td class="class-value">{c['Devata']}</td>
                                        <td class="class-value">{c['Chandas']}</td>
                                    </tr>''' for c in sama.rik_classifications])}
                            </table>
                        </div>""" if (self.mode != 'collection' and getattr(self, 'has_riks', True) and getattr(self, 'has_metadata', True) and sama.rik_classifications) else ""}

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

                # Render Closing Mantras (Only on the last page of the entire collection)
                closing_mantras_html = ""
                if p_idx == len(self.parvas) - 1 and k_idx == len(parva.kandahs) - 1 and self.closing_mantras:
                    cm_lines = "".join([f'<p class="closing-mantra-line">{line}</p>' for line in self.closing_mantras])
                    closing_mantras_html = f'''
                    <section class="closing-mantras-section">
                        <div class="closing-mantras-content">
                            {cm_lines}
                        </div>
                    </section>'''
                
                parva_clean = parva.title.replace('॥', '').replace('||', '').replace('|', '').strip()
                kandah_clean = kandah.title.replace('॥', '').replace('||', '').replace('|', '').strip()
                
                # Calculate real sama count for this Kandah
                kandah_sama_count = sum(count_samams_with_fallback(s.mantra_text) for s in kandah.samas)
                
                # Check for procedure_ref at Kandah (section) or Parva (supersection) level
                procedure_link = ""
                for sama in kandah.samas:
                    if sama.procedure_ref:
                        scope = sama.procedure_ref.get('scope', '')
                        if scope == 'section':
                            # This procedure applies to the entire Kandah
                            slug = Path(sama.procedure_ref.get('file', '')).stem
                            proc_anchor = f"../../prayoga/{slug}.html"
                            proc_title = sama.procedure_ref.get('title', 'विधिः')
                            procedure_link = f'<div class="procedure-box"><span class="procedure-label">विधिः</span><a href="{proc_anchor}" class="procedure-text">{proc_title}</a></div>'
                            break
                        elif scope == 'supersection':
                            # Show supersection procedure on each Kandah page
                            slug = Path(sama.procedure_ref.get('file', '')).stem
                            proc_anchor = f"../../prayoga/{slug}.html"
                            proc_title = sama.procedure_ref.get('title', 'विधिः')
                            procedure_link = f'<div class="procedure-box"><span class="procedure-label">विधिः</span><a href="{proc_anchor}" class="procedure-text">{proc_title}</a></div>'
                            break
                
                L = self.labels
                home_title = L['home'].split(' ')[0]
                all_kandah_text = L.get('all_kandah', 'सम्पूर्णम्') if getattr(self, 'is_malayalam', False) else 'सम्पूर्णम्'
                if getattr(self, 'is_malayalam', False):
                    all_kandah_text = 'സമ്പൂർണ്ണം'
                
                html = f'''{self._get_html_head(f"{parva_clean} - {kandah_clean}", depth=2)}
<body>
    <div class="page-container">
        {self._get_sidebar_html(current_parva_id=parva.id, current_kandah_id=kandah.id, depth=2)}
        
        <main class="main-content">
            {self._get_top_nav_html(depth=2)}
            <nav class="breadcrumb">
                <a href="../../index.html">{home_title}</a>
                <span class="breadcrumb-separator">›</span>
                <span>{parva_clean}</span>
                <span class="breadcrumb-separator">›</span>
                <span>{kandah_clean}</span>
            </nav>
            
            <header class="page-header">
                <h1>{parva_clean} - {kandah_clean}</h1>
                <div class="page-meta">
                    <p class="page-subtitle">{L['parva']} <span class="number">{parva.parva_number}</span> | {L['kandah']} <span class="number">{kandah.kandah_number}</span> | {L['sama']} <span class="number">{kandah_sama_count}</span></p>
                </div>
                {procedure_link}
            </header>
            
            <div class="toc">
                <h4>{L['kandah']} {kandah.kandah_number} - {all_kandah_text}</h4>
                <ul class="toc-list">
                    {toc_items}
                </ul>
            </div>
            
            {sama_entries}
            
            {kandah_footnotes_html}
            
            {closing_mantras_html}
            
            <footer class="footer">
                {self.config['footer_sa']}
            </footer>
        </main>
        
    </div>
    <div class="search-modal" id="search-modal">
        <div class="search-modal-content">
            <div class="search-modal-header">
                <h3>अन्वेषणम् (Search)</h3>
                <button class="search-close" id="search-close">&times;</button>
            </div>
            <div class="search-input-container">
                <input type="text" class="search-input" id="search-input" placeholder="Search (Devanagari, English, IAST)...">
                <span class="search-hint">Search for Mantras, Rishis, Devatas, or Chandas in Devanagari or English</span>
            </div>
            <div class="search-results" id="search-results"></div>
        </div>
    </div>
    <div class="search-overlay" id="search-overlay"></div>
    <script src="../../search-index.js"></script>
    <script src="../../js/main.js?v={int(datetime.now().timestamp())}"></script>
</body>
</html>'''
                
                with open(parva_dir / f'{kandah.kandah_number}.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                    
    def _generate_procedure_pages(self):
        """Generate standalone HTML pages for procedures from Markdown files"""
        prayoga_dir = self.output_dir / 'prayoga'
        prayoga_dir.mkdir(parents=True, exist_ok=True)
        
        # Collect all unique procedure Markdown files from Samas
        procedures = {}
        for parva in self.parvas:
            for kandah in parva.kandahs:
                for sama in kandah.samas:
                    if sama.procedure_ref:
                        file_path = sama.procedure_ref.get('file', '')
                        if file_path and file_path.endswith('.md'):
                            slug = Path(file_path).stem
                            title_meta = sama.procedure_ref.get('title', 'विधिः')
                            # Also build the backlink for the very first Sama that links to this procedure
                            backlink = f"../kandah/{parva.id}/{kandah.kandah_number}.html#sama-{sama.sama_number}"
                            if file_path not in procedures:
                                procedures[file_path] = {
                                    'slug': slug, 
                                    'title': title_meta, 
                                    'backlink': backlink, 
                                    'backlink_title': f"{parva.title} - {kandah.title}"
                                }

        # Render each markdown file
        for file_path, proc_info in procedures.items():
            full_md_path = Path("data/input/prayoga") / file_path
            if not full_md_path.exists():
                print(f"[WARNING] Procedure file not found: {full_md_path}")
                continue
            
            with open(full_md_path, 'r', encoding='utf-8') as f:
                md_content = f.read()

            # Frontmatter stripping
            if md_content.startswith('---'):
                parts = md_content.split('---', 2)
                if len(parts) >= 3:
                    md_content = parts[2].strip()

            html_content = markdown.markdown(md_content, extensions=['tables'])

            # Render page layout with base styling
            title = proc_info['title']
            html = f'''{self._get_html_head(title, depth=1)}
<body>
    <div class="page-container">
        {self._get_sidebar_html(depth=1)}
        <main class="main-content" style="max-width: 1200px;">
            {self._get_top_nav_html(depth=1)}
            <div class="page-header" style="text-align: left; margin-bottom: 20px;">
                <a href="{proc_info['backlink']}" style="color: #2e7d32; text-decoration: none; font-weight: 500;">← Back to {proc_info['backlink_title']}</a>
                <h1>{title}</h1>
            </div>
            
            <div class="procedure-markdown-content" style="background: white; padding: 2.5rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); font-size: 1.15rem; line-height: 1.7; color: #333;">
                <style>
                    .procedure-markdown-content h1, .procedure-markdown-content h2, .procedure-markdown-content h3 {{
                        color: #5c3a21;
                        margin-top: 1.5em;
                        margin-bottom: 0.5em;
                    }}
                    .procedure-markdown-content h1 {{ font-size: 2rem; border-bottom: 2px solid #f0f0f0; padding-bottom: 0.3em; }}
                    .procedure-markdown-content h2 {{ font-size: 1.5rem; }}
                    .procedure-markdown-content p {{ margin-bottom: 1.2em; }}
                    .procedure-markdown-content ul, .procedure-markdown-content ol {{ margin-bottom: 1.2em; padding-left: 2em; }}
                    .procedure-markdown-content li {{ margin-bottom: 0.5em; }}
                    .procedure-markdown-content strong {{ color: #2e7d32; }}
                </style>
                {html_content}
            </div>
        </main>
    </div>
</body>
</html>'''
            
            out_path = prayoga_dir / f"{proc_info['slug']}.html"
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(html)


    def _generate_metadata_json(self):
        """Generate metadata.json for reference"""
        metadata = {
            "title": self.config['title_sa'],
            "title_en": self.config['title_en'],
            "version": self.metadata["version"],
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


