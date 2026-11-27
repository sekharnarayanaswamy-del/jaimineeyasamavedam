#!/usr/bin/env python3
"""
Generate 2-page sample PDFs of body text for font comparison:
- Baseline: Current body size (Scale=1.50, ~18pt) & regular weight
- Variant 1: +2pt scaled body (Scale=1.68, ~20pt) with headers and swaras scaled proportionately
- Variant 2: Current body size (Scale=1.50), but all body text in Bold (AdishilaVedicBold.ttf)
"""

import os
import subprocess
import shutil
import pymupdf

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX_SOURCE = os.path.join(ROOT_DIR, "data", "corpora", "samhita_aranyakam", "05_renders", "tex", "Samhita_Aranyakam_flow_Samam_Devanagari.tex")
PDF_OUT_DIR = os.path.join(ROOT_DIR, "data", "corpora", "samhita_aranyakam", "05_renders", "pdf")
TEMP_DIR = os.path.join(ROOT_DIR, "temp_samples")

def generate_samples():
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(PDF_OUT_DIR, exist_ok=True)

    with open(TEX_SOURCE, "r", encoding="utf-8") as f:
        text = f.read()

    preamble = text[:text.find(r"\begin{document}")]
    body_start = text.find(r"\chapter*{\centering आग्नेयपाठः}")
    body_end = text.find("\n", text.find(r"mbox{॥ २५ ॥}"))
    body = text[body_start:body_end]

    variants = [
        {
            "name": "baseline",
            "pdf_name": "Samhita_Aranyakam_sample_baseline.pdf",
            "preamble": preamble,
            "desc": "Baseline (Scale=1.50, regular weight)"
        },
        {
            "name": "plus2pt",
            "pdf_name": "Samhita_Aranyakam_sample_plus2pt.pdf",
            "preamble": preamble.replace("Scale=1.50, Script=Devanagari", "Scale=1.68, Script=Devanagari")
                               .replace("Scale=1.60, Script=Devanagari", "Scale=1.79, Script=Devanagari")
                               .replace("Scale=1.05, Script=Devanagari", "Scale=1.18, Script=Devanagari")
                               .replace("Scale=0.98, Script=Grantha", "Scale=1.10, Script=Grantha")
                               .replace("Scale=1.38, Script=Grantha", "Scale=1.55, Script=Grantha")
                               .replace(r"\fancyhead[LO]{\rightmark}", r"\fancyhead[LO,RE]{\leftmark}\fancyhead[C]{\rightmark}")
                               .replace(r"\fancyhead[RE]{\leftmark}", ""),
            "desc": "Variant 1: +2pt scaled (Scale=1.68, headers & swaras scaled proportionately, Supersection+Section in running header)"
        },
        {
            "name": "body_bold",
            "pdf_name": "Samhita_Aranyakam_sample_body_bold.pdf",
            "preamble": preamble.replace("{AdishilaVedic.ttf}", "{AdishilaVedicBold.ttf}")
                               .replace(r"\fancyhead[LO]{\rightmark}", r"\fancyhead[LO,RE]{\leftmark}\fancyhead[C]{\rightmark}")
                               .replace(r"\fancyhead[RE]{\leftmark}", ""),
            "desc": "Variant 2: Current size (Scale=1.50), body in Bold"
        },
        {
            "name": "plus2pt_bold",
            "pdf_name": "Samhita_Aranyakam_sample_plus2pt_bold.pdf",
            "preamble": preamble.replace("Scale=1.50, Script=Devanagari", "Scale=1.68, Script=Devanagari")
                               .replace("Scale=1.60, Script=Devanagari", "Scale=1.79, Script=Devanagari")
                               .replace("Scale=1.05, Script=Devanagari", "Scale=1.18, Script=Devanagari")
                               .replace("Scale=0.98, Script=Grantha", "Scale=1.10, Script=Grantha")
                               .replace("Scale=1.38, Script=Grantha", "Scale=1.55, Script=Grantha")
                               .replace("{AdishilaVedic.ttf}", "{AdishilaVedicBold.ttf}")
                               .replace(r"\fancyhead[LO]{\rightmark}", r"\fancyhead[LO,RE]{\leftmark}\fancyhead[C]{\rightmark}")
                               .replace(r"\fancyhead[RE]{\leftmark}", ""),
            "desc": "Variant 3: +2pt scaled AND body in Bold (Scale=1.68, AdishilaVedicBold)"
        }
    ]

    for v in variants:
        print(f"Building {v['desc']}...")
        tex_path = os.path.join(TEMP_DIR, f"{v['name']}.tex")
        full_tex = v["preamble"] + "\n\\begin{document}\n\\raggedbottom\n\\pagestyle{fancy}\n\\pagenumbering{arabic}\n\\setcounter{page}{1}\n" + body + "\n\\end{document}\n"
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(full_tex)

        res = subprocess.run(["lualatex", "--interaction=nonstopmode", f"{v['name']}.tex"], cwd=TEMP_DIR, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Warning: {v['name']} compilation returned {res.returncode}")

        pdf_temp = os.path.join(TEMP_DIR, f"{v['name']}.pdf")
        if os.path.exists(pdf_temp):
            src_doc = pymupdf.open(pdf_temp)
            final_doc = pymupdf.open()
            final_doc.insert_pdf(src_doc, from_page=0, to_page=1)
            final_out_path = os.path.join(PDF_OUT_DIR, v["pdf_name"])
            final_doc.save(final_out_path)
            print(f"Generated {final_out_path} ({len(final_doc)} pages)")
        else:
            print(f"Failed to generate {pdf_temp}")

if __name__ == "__main__":
    generate_samples()
