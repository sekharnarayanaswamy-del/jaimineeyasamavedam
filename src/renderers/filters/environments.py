"""
Jinja2 Environment Factories and Default Instances for Jaimineeya Samaveda Pipeline.
-----------------------------------------------------------------------------------
Configures custom LaTeX-delimiter Jinja environments with registered LaTeX,
HTML, and PlainText Vedic rendering filters.
"""

import os
from pathlib import Path
from typing import Optional, Union

import jinja2

from src.renderers.filters.latex_filters import register_latex_filters
from src.renderers.filters.html_filters import register_html_filters
from src.renderers.filters.text_filters import register_text_filters, split_rik_lines_text


def create_latex_jinja_env(loader_path: Optional[Union[str, Path]] = None) -> jinja2.Environment:
    """
    Creates and configures a Jinja2 environment for LaTeX and PlainText templates.
    Uses LaTeX-style block and variable delimiters to avoid syntax collisions.
    Registers all LaTeX and PlainText filters.
    """
    search_path = os.path.abspath(str(loader_path or "."))
    env = jinja2.Environment(
        block_start_string=r"\BLOCK{",
        block_end_string="}",
        variable_start_string=r"\VAR{",
        variable_end_string="}",
        comment_start_string=r"\#{",
        comment_end_string="}",
        line_statement_prefix="%-",
        line_comment_prefix="%#",
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
        loader=jinja2.FileSystemLoader(search_path),
        extensions=["jinja2.ext.loopcontrols"],
    )
    register_latex_filters(env)
    register_text_filters(env)
    # Compatibility alias matching legacy render_pdf.py
    env.filters["split_rik_lines"] = split_rik_lines_text
    return env


def create_html_jinja_env(loader_path: Optional[Union[str, Path]] = None) -> jinja2.Environment:
    """
    Creates and configures a Jinja2 environment for HTML Reader templates.
    Uses consistent LaTeX-style block and variable delimiters.
    Registers all HTML reader filters (accents, footnotes, dandas).
    """
    search_path = os.path.abspath(str(loader_path or "."))
    env = jinja2.Environment(
        block_start_string=r"\BLOCK{",
        block_end_string="}",
        variable_start_string=r"\VAR{",
        variable_end_string="}",
        comment_start_string=r"\#{",
        comment_end_string="}",
        line_statement_prefix="%-",
        line_comment_prefix="%#",
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
        loader=jinja2.FileSystemLoader(search_path),
        extensions=["jinja2.ext.loopcontrols"],
    )
    register_html_filters(env)
    try:
        from src.renderers.html_common import (
            get_viewer_notes_css,
            get_viewer_notes_js,
            get_viewer_notes_html,
            get_viewer_toolbar_controls_html,
            render_section_bm_btn,
            render_inline_note_btn,
        )
    except ImportError:
        from renderers.html_common import (
            get_viewer_notes_css,
            get_viewer_notes_js,
            get_viewer_notes_html,
            get_viewer_toolbar_controls_html,
            render_section_bm_btn,
            render_inline_note_btn,
        )
    env.globals["notes_css"] = get_viewer_notes_css()
    env.globals["notes_js"] = get_viewer_notes_js("jsv")
    env.globals["notes_drawer_html"] = get_viewer_notes_html()
    env.globals["notes_toolbar_controls"] = get_viewer_toolbar_controls_html()
    env.globals["render_section_bm_btn"] = render_section_bm_btn
    env.globals["render_inline_note_btn"] = render_inline_note_btn
    return env


# Pre-configured default instances (bound to repository root)
latex_jinja_env = create_latex_jinja_env()
html_jinja_env = create_html_jinja_env()
