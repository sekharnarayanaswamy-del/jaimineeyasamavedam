"""
Export standalone .tex source files for all Samhita editions.
These can be opened in TeXstudio or VS Code with LaTeX Workshop for side-by-side editing.
"""

import sys
import os
from pathlib import Path
import json

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "src"))

from src.render import latex_jinja_env, escape_for_latex, reset_latex_doc_markers
from utils import get_generated_metadata, normalize_to_dd_mm_yyyy

def export_all_tex_sources(output_dir="data/output/tex"):
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = ROOT_DIR / "data/output/Samhita_corrected_out.json"
    with open(json_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    meta = get_generated_metadata()
    jsv_version = meta["version"]
    generated_at = normalize_to_dd_mm_yyyy(meta["generated_at"])
    font_path = str(ROOT_DIR / "fonts").replace("\\", "/") + "/"

    configs = [
        ("Devanagari_book.template", "Samhita_book_bw_Devanagari.tex", "bw"),
        ("Devanagari_book.template", "Samhita_book_Devanagari.tex", "color"),
        ("Devanagari_main.template", "Samhita_bw_Devanagari.tex", "bw"),
        ("Devanagari_main.template", "Samhita_Devanagari.tex", "color"),
    ]

    print(f"Exporting .tex sources to: {out_dir.resolve()}")
    for tpl_name, tex_name, color_mode in configs:
        reset_latex_doc_markers()
        data = json.loads(json.dumps(raw_data["supersection"]))
        data = escape_for_latex(data)

        template = latex_jinja_env.get_template(f"templates/pdf/{tpl_name}")
        doc = template.render(
            supersections=data,
            os="Windows",
            output_mode="combined",
            version=jsv_version,
            generated_at=generated_at,
            font_family="AdishilaVedic",
            doc_title_sa="जैमिनीयसामवेद संहिता",
            pdf_color_mode=color_mode,
            closing_mantras=raw_data.get("closing_mantras", []),
            font_path=font_path,
            summary_table=None,
            total_riks="६८०",
            total_samams="१४४०",
            summary_title="संहिता सङ्ख्या",
            toc_level="both",
            has_riks=True,
            has_samams=True,
            prayogas=[],
            kpully=False,
        )
        out_file = out_dir / tex_name
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(doc)
        print(f"  -> {tex_name} ({out_file.stat().st_size / 1024:.1f} KB)")

if __name__ == "__main__":
    export_all_tex_sources()
