"""
Static Website Generator for Jaimineeya Samaveda
"""

from .models import Sama, Kandah, Parva
from .constants import SITE_CONFIG, AUDIO_FILENAME_FORMAT, MALAYALAM_MODIFIER_MAP, HTML_MOD_MAP
from .parser import JSVParser
from .generator import WebsiteGenerator
from .formatters import (
    format_rik_text_html,
    format_mantra_text_html,
    format_malayalam_mantra_html,
    local_escape_for_html,
    local_replace_accents_html,
    local_process_footnotes_html,
    local_format_dandas_html,
    local_remove_mantra_spaces,
    local_handle_consecutive_trikamba,
    split_rik_lines_html,
    split_malayalam_clusters,
)
from .assets import generate_styles_css, generate_main_js
from .search import (
    clean_text_for_search,
    strip_diacritics,
    transliterate_to_latin,
    generate_search_index_file,
)

__all__ = [
    'Sama',
    'Kandah',
    'Parva',
    'SITE_CONFIG',
    'AUDIO_FILENAME_FORMAT',
    'MALAYALAM_MODIFIER_MAP',
    'HTML_MOD_MAP',
    'JSVParser',
    'WebsiteGenerator',
    'format_rik_text_html',
    'format_mantra_text_html',
    'format_malayalam_mantra_html',
    'generate_styles_css',
    'generate_main_js',
    'clean_text_for_search',
    'strip_diacritics',
    'transliterate_to_latin',
    'generate_search_index_file',
    'local_escape_for_html',
    'local_replace_accents_html',
    'local_process_footnotes_html',
    'local_format_dandas_html',
    'local_remove_mantra_spaces',
    'local_handle_consecutive_trikamba',
    'split_rik_lines_html',
    'split_malayalam_clusters',
]
