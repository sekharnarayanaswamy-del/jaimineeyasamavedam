"""
Plain Text Unicode Renderer for Jaimineeya Samaveda Pipeline.

Generates clean, standardized plaintext Vedic outputs with authentic
accents and section-delimited formatting.
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

from src.renderers.base_renderer import BaseRenderer
from src.core.models import VedicDocument


class TextRenderer(BaseRenderer):
    """Renderer responsible for generating plain-text Unicode exports."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)

    def render(
        self,
        document: Union[VedicDocument, Dict[str, Any]],
        output_path: Optional[Path] = None,
        **kwargs: Any
    ) -> int:
        """
        Renders a VedicDocument to a Unicode plain-text file.
        Delegates to CreateTextFile to preserve exact spacing and accents.
        """
        # Lazy import to avoid circular dependency
        from render_pdf import CreateTextFile, latex_jinja_env

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
            template_name = kwargs.get("template_name", "templates/text/Devanagari_main.template")
            template_file = latex_jinja_env.get_template(template_name)

        name = kwargs.get("name", "Samhita")
        doc_family = kwargs.get("doc_family", "Devanagari")

        out_dir = str(output_path.parent) if output_path else kwargs.get("output_dir_override")
        out_name = output_path.name if output_path else kwargs.get("name_override")

        return CreateTextFile(
            templateFileName=template_file,
            name=name,
            DocfamilyName=doc_family,
            data=data,
            output_mode=kwargs.get("output_mode", "combined"),
            doc_title_sa=doc_title,
            closing_mantras=closing_mantras,
            toc_level=kwargs.get("toc_level", "section"),
            output_dir_override=out_dir,
            name_override=out_name,
            jsv_version=version,
            generated_at=generated_at
        )
