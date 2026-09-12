"""
HTML Reader Renderer for Jaimineeya Samaveda Pipeline.

Generates standalone responsive HTML readers with embedded fonts,
audio drawer synchronization, and Suchi navigation.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

from src.renderers.base_renderer import BaseRenderer
from src.core.models import VedicDocument


class HTMLRenderer(BaseRenderer):
    """Renderer responsible for generating standalone and VedaVMS HTML readers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

    def render(
        self,
        document: Union[VedicDocument, Dict[str, Any]],
        output_path: Optional[Path] = None,
        **kwargs: Any
    ) -> int:
        """
        Renders a VedicDocument to a standalone HTML file.
        Delegates to CreateHtmlFile to preserve font embeddings and swara CSS.
        """
        # Lazy import to avoid circular dependency
        from render_pdf import CreateHtmlFile, html_jinja_env

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
            template_name = kwargs.get("template_name", "templates/html/Devanagari_main_html.template")
            try:
                template_file = html_jinja_env.get_template(template_name)
            except Exception:
                template_file = None

        name = kwargs.get("name", "Samhita")
        doc_family = kwargs.get("doc_family", "Devanagari")

        out_dir = str(output_path.parent) if output_path else kwargs.get("output_dir_override")
        out_name = output_path.name if output_path else kwargs.get("name_override")

        return CreateHtmlFile(
            templateFileName=template_file,
            name=name,
            DocfamilyName=doc_family,
            data=data,
            html_font=kwargs.get("html_font", "'AdishilaVedic', 'AdishilaSanVedic'"),
            output_mode=kwargs.get("output_mode", "combined"),
            doc_title_sa=doc_title,
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
            script=kwargs.get("script", "devanagari"),
            with_modifiers=kwargs.get("with_modifiers", True),
            kpully=kwargs.get("kpully", False)
        )
