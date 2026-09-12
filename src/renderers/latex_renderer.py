"""
LaTeX/PDF Renderer for Jaimineeya Samaveda Pipeline.

Wraps XeLaTeX / LuaLaTeX document compilation, managing templates, geometry,
Parchment styling, and cross-reference indexing.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union

from src.renderers.base_renderer import BaseRenderer
from src.core.models import VedicDocument


class LaTeXRenderer(BaseRenderer):
    """Renderer responsible for generating publication-grade Vedic PDFs via LaTeX."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

    def render(
        self,
        document: Union[VedicDocument, Dict[str, Any]],
        output_path: Optional[Path] = None,
        **kwargs: Any
    ) -> int:
        """
        Renders a VedicDocument to LaTeX and compiles to PDF.
        Delegates to CreatePdf to preserve 100% typographic and accent integrity.
        """
        # Lazy import to avoid circular dependency
        from render_pdf import CreatePdf, latex_jinja_env

        if isinstance(document, VedicDocument):
            data = document.to_dict().get("supersections", {})
            doc_title = kwargs.get("doc_title_sa") or document.meta.title
            version = kwargs.get("jsv_version") or document.meta.version
            generated_at = kwargs.get("generated_at") or document.meta.generated_at
            closing_mantras = kwargs.get("closing_mantras") or document.closing_mantras
        else:
            data = document.get("supersections", document.get("supersection", {}))
            doc_title = kwargs.get("doc_title_sa") or document.get("meta", {}).get("title", "")
            version = kwargs.get("jsv_version") or document.get("meta", {}).get("version", "")
            generated_at = kwargs.get("generated_at") or document.get("meta", {}).get("generated_at", "")
            closing_mantras = kwargs.get("closing_mantras") or document.get("closing_mantras", [])

        template_file = kwargs.get("template")
        if not template_file:
            template_name = kwargs.get("template_name", "templates/pdf/Devanagari_main.template")
            template_file = latex_jinja_env.get_template(template_name)

        name = kwargs.get("name", "Samhita")
        doc_family = kwargs.get("doc_family", "Devanagari")

        out_dir = str(output_path.parent) if output_path else kwargs.get("output_dir_override")
        out_name = output_path.stem if output_path else kwargs.get("name_override")

        return CreatePdf(
            templateFileName=template_file,
            name=name,
            DocfamilyName=doc_family,
            data=data,
            prayogas=kwargs.get("prayogas"),
            current_os=kwargs.get("current_os", "Windows"),
            output_mode=kwargs.get("output_mode", "combined"),
            font_family=kwargs.get("font_family", "AdishilaVedic"),
            doc_title_sa=doc_title,
            pdf_color_mode=kwargs.get("pdf_color_mode", "color"),
            closing_mantras=closing_mantras,
            summary_table=kwargs.get("summary_table"),
            total_riks=kwargs.get("total_riks"),
            total_samams=kwargs.get("total_samams"),
            summary_title=kwargs.get("summary_title", "संहिता सङ्ख्या"),
            toc_level=kwargs.get("toc_level", "section"),
            has_riks=kwargs.get("has_riks", True),
            has_samams=kwargs.get("has_samams", True),
            output_dir_override=out_dir,
            name_override=out_name,
            jsv_version=version,
            generated_at=generated_at,
            kpully=kwargs.get("kpully", False)
        )
