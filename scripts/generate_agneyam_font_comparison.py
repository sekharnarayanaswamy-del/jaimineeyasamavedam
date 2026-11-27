#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Single-page comparison generator for Samhita Agneyam (A4 BW):
1) Body font regular : 18 pt
2) Body font bold    : 18 pt
3) Body font regular : 20 pt
4) Body font bold    : 20 pt

Proportionately scales subsection headers, parva/khanda titles, swaras, and arcs.
Generates:
  - 4 individual single-page A4 BW PDFs
  - 1 unified 4-page comparison PDF (flip-through)
  - High-resolution preview PNGs for visual inspection
"""

import os
import subprocess
import shutil
from pathlib import Path
import pymupdf

REPO_ROOT = Path(__file__).resolve().parent.parent
TEX_SOURCE = REPO_ROOT / "data" / "corpora" / "samhita_aranyakam" / "05_renders" / "tex" / "Samhita_Aranyakam_flow_bw_Samam_Devanagari.tex"
PDF_OUT_SAMHITA = REPO_ROOT / "data" / "corpora" / "samhita" / "05_renders" / "pdf"
PDF_OUT_COMBINED = REPO_ROOT / "data" / "corpora" / "samhita_aranyakam" / "05_renders" / "pdf"
TEMP_DIR = REPO_ROOT / "temp_font_comparison"

CASES = [
    {
        "id": "18pt_regular",
        "title": "18 pt Regular",
        "desc": "Case 1: Body font regular : 18 pt",
        "scale_body": 1.50,
        "scale_header": 1.60,
        "scale_swara": 1.05,
        "scale_arc": 1.38,
        "scale_glyph": 0.98,
        "body_font_file": "AdishilaVedic.ttf",
        "body_bold_file": "AdishilaVedicBold.ttf",
        "is_bold_body": False,
        "skip_footins": "20pt plus 4pt minus 2pt",
        "pdf_name": "Samhita_Agneyam_18pt_regular_A4_bw.pdf"
    },
    {
        "id": "18pt_bold",
        "title": "18 pt Bold",
        "desc": "Case 2: Body font bold : 18 pt",
        "scale_body": 1.50,
        "scale_header": 1.60,
        "scale_swara": 1.05,
        "scale_arc": 1.38,
        "scale_glyph": 0.98,
        "body_font_file": "AdishilaVedicBold.ttf",
        "body_bold_file": "AdishilaVedicBold.ttf",
        "is_bold_body": True,
        "skip_footins": "20pt plus 4pt minus 2pt",
        "pdf_name": "Samhita_Agneyam_18pt_bold_A4_bw.pdf"
    },
    {
        "id": "20pt_regular",
        "title": "20 pt Regular",
        "desc": "Case 3: Body font regular : 20 pt",
        "scale_body": 1.68,
        "scale_header": 1.79,
        "scale_swara": 1.18,
        "scale_arc": 1.55,
        "scale_glyph": 1.10,
        "body_font_file": "AdishilaVedic.ttf",
        "body_bold_file": "AdishilaVedicBold.ttf",
        "is_bold_body": False,
        "skip_footins": "24pt plus 4pt minus 2pt",
        "pdf_name": "Samhita_Agneyam_20pt_regular_A4_bw.pdf"
    },
    {
        "id": "20pt_bold",
        "title": "20 pt Bold",
        "desc": "Case 4: Body font bold : 20 pt",
        "scale_body": 1.68,
        "scale_header": 1.79,
        "scale_swara": 1.18,
        "scale_arc": 1.55,
        "scale_glyph": 1.10,
        "body_font_file": "AdishilaVedicBold.ttf",
        "body_bold_file": "AdishilaVedicBold.ttf",
        "is_bold_body": True,
        "skip_footins": "24pt plus 4pt minus 2pt",
        "pdf_name": "Samhita_Agneyam_20pt_bold_A4_bw.pdf"
    }
]

def build_font_definitions(c: dict, fonts_dir_posix: str) -> str:
    body_font = c["body_font_file"]
    bold_attr = f", BoldFont={c['body_bold_file']}" if not c["is_bold_body"] else ""
    swara_bold = "AdishilaVedicBold.ttf" if c["is_bold_body"] else "AdishilaVedic.ttf"
    
    return f"""
% --- DYNAMIC FONT DEFINITIONS FOR {c['title']} ---
\\setmainfont[Scale={c['scale_body']:.2f}, Script=Devanagari, Renderer=Harfbuzz, Ligatures=TeX, Path={fonts_dir_posix}/{bold_attr}]{{{body_font}}}
\\newfontfamily\\devafont[Scale={c['scale_body']:.2f}, Script=Devanagari, Renderer=Harfbuzz, Ligatures=TeX, Path={fonts_dir_posix}/{bold_attr}]{{{body_font}}}
\\newfontfamily\\headerfont[Scale={c['scale_header']:.2f}, Script=Devanagari, Renderer=Harfbuzz, Ligatures=TeX, Path={fonts_dir_posix}/]{{AdishilaVedicBold.ttf}}
\\newfontfamily\\smallredfont[Scale={c['scale_swara']:.2f}, Script=Devanagari, Renderer=Harfbuzz, Ligatures=TeX, Color=SwaraRed, Path={fonts_dir_posix}/, BoldFont=AdishilaVedicBold.ttf]{{{swara_bold}}}
\\newfontfamily\\swarafont[Scale={c['scale_glyph']:.2f}, Script=Grantha, Ligatures=TeX, AutoFakeBold=3.5, AutoFakeSlant, Path={fonts_dir_posix}/]{{JaimineeyaSwara.ttf}}
\\newfontfamily\\arcfontDeva[Scale={c['scale_arc']:.2f}, Script=Grantha, Ligatures=TeX, AutoFakeBold=3.5, Path={fonts_dir_posix}/]{{JaimineeyaSwara.ttf}}
\\setlength{{\\skip\\footins}}{{{c['skip_footins']}}}
"""

def main():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    PDF_OUT_SAMHITA.mkdir(parents=True, exist_ok=True)
    PDF_OUT_COMBINED.mkdir(parents=True, exist_ok=True)

    with open(TEX_SOURCE, "r", encoding="utf-8") as f:
        master_tex = f.read()

    preamble_end = master_tex.find(r"\begin{document}")
    if preamble_end == -1:
        raise ValueError("Could not find \\begin{document} in master tex")
    base_preamble = master_tex[:preamble_end]

    # Extract Agneyam chant text (up to Samam 15 to ensure plenty of overflow text)
    body_start = master_tex.find(r"\chapter*{\centering आग्नेयपाठः}")
    marker = r"॥ साम सङ्ख्या : १५ ॥"
    m_idx = master_tex.find(marker)
    if m_idx == -1:
        marker = r"॥ १५ ॥"
        m_idx = master_tex.find(marker)
    if body_start == -1 or m_idx == -1:
        raise ValueError("Could not find Agneyam start/end markers in master tex")
    
    # Ensure the line containing the closing marker is fully included with all its closing braces
    body_end = master_tex.find("\n", m_idx) + 1
    agneyam_body = master_tex[body_start:body_end]

    fonts_dir_posix = (REPO_ROOT / "fonts").as_posix()

    generated_single_pages = []
    comparison_doc = pymupdf.open()

    for idx, c in enumerate(CASES):
        print(f"\n==========================================")
        print(f"Compiling Case {idx+1}: {c['desc']}...")
        print(f"==========================================")

        # Replace font definition block in preamble
        # Find where \setmainfont starts and \setcounter{tocdepth} begins
        f_start = base_preamble.find(r"\setmainfont")
        f_end = base_preamble.find(r"\setcounter{tocdepth}")
        if f_start == -1 or f_end == -1:
            raise ValueError("Could not locate font definitions block in preamble")

        custom_fonts = build_font_definitions(c, fonts_dir_posix)
        case_preamble = base_preamble[:f_start] + custom_fonts + "\n" + base_preamble[f_end:]

        # Configure custom running header for plain page style (used by \chapter*)
        header_config = f"""
\\fancypagestyle{{plain}}{{%
  \\fancyhf{{}}%
  \\fancyhead[L]{{\\footnotesize\\headerfont आग्नेयपाठः \\enspace---\\enspace प्रथम खण्डः}}%
  \\fancyhead[C]{{}}%
  \\fancyhead[R]{{\\footnotesize\\textbf{{{c['desc']}}}\\quad Page \\thepage}}%
  \\fancyfoot[C]{{\\footnotesize jaimineeyasamavedam.org -- {c['title']}}}%
  \\renewcommand{{\\headrulewidth}}{{0.4pt}}%
}}
\\pagestyle{{plain}}
"""
        case_preamble = case_preamble.replace(r"\fancyhead[LE,RO]{\thepage}", "% overridden")
        case_preamble = case_preamble.replace(r"\fancyhead[LO,RE]{\leftmark}", "% overridden")
        case_preamble = case_preamble.replace(r"\fancyhead[C]{\rightmark}", header_config)

        case_tex_filename = f"agneyam_{c['id']}.tex"
        case_tex_path = TEMP_DIR / case_tex_filename

        full_doc = (
            case_preamble +
            "\n\\begin{document}\n"
            "\\raggedbottom\n"
            "\\pagestyle{fancy}\n"
            "\\pagenumbering{arabic}\n"
            "\\setcounter{page}{1}\n" +
            agneyam_body +
            "\n\\end{document}\n"
        )

        with open(case_tex_path, "w", encoding="utf-8") as f_out:
            f_out.write(full_doc)

        res = subprocess.run(
            ["lualatex", "--interaction=nonstopmode", case_tex_filename],
            cwd=str(TEMP_DIR),
            capture_output=True,
            text=True
        )

        pdf_temp = TEMP_DIR / f"agneyam_{c['id']}.pdf"
        if not pdf_temp.exists() or res.returncode != 0:
            print(f"lualatex failed for {c['id']}, returncode {res.returncode}")
            if pdf_temp.exists():
                print(f"PDF exists despite non-zero return code, proceeding...")
            else:
                raise RuntimeError(f"Failed to generate {pdf_temp}")

        # Extract strictly Page 1 (the single page comparison)
        src_pdf = pymupdf.open(pdf_temp)
        print(f"Raw compilation produced {len(src_pdf)} pages for {c['id']}")

        one_page_pdf = pymupdf.open()
        one_page_pdf.insert_pdf(src_pdf, from_page=0, to_page=0) # Strictly Page 1

        # Save to output locations
        out_samhita = PDF_OUT_SAMHITA / c["pdf_name"]
        out_combined = PDF_OUT_COMBINED / c["pdf_name"]

        one_page_pdf.save(out_samhita)
        shutil.copyfile(out_samhita, out_combined)
        print(f"[OK] Saved single page: {out_samhita} ({out_samhita.stat().st_size:,} bytes)")

        # Render preview PNG image for conversational inspection
        pix = one_page_pdf[0].get_pixmap(dpi=150)
        img_name = f"agneyam_comparison_{c['id']}.png"
        img_path = Path("C:/Users/sekha/.gemini/antigravity/brain/2dbccc89-e689-4ab9-9da5-8615b5c667af") / img_name
        pix.save(img_path)
        print(f"[OK] Rendered preview image: {img_path}")

        # Add to the multi-page comparison document
        comparison_doc.insert_pdf(one_page_pdf)
        generated_single_pages.append(out_samhita)

    # Save 4-page combined flip-through comparison PDF
    comparison_pdf_samhita = PDF_OUT_SAMHITA / "Samhita_Agneyam_comparison_all_4cases_A4_bw.pdf"
    comparison_pdf_combined = PDF_OUT_COMBINED / "Samhita_Agneyam_comparison_all_4cases_A4_bw.pdf"

    comparison_doc.save(comparison_pdf_samhita)
    shutil.copyfile(comparison_pdf_samhita, comparison_pdf_combined)
    print(f"\n[SUCCESS] Generated 4-page comparison flipbook: {comparison_pdf_samhita} ({comparison_pdf_samhita.stat().st_size:,} bytes)")

    # -------------------------------------------------------------
    # Generate Visual Composite Comparison Images
    # -------------------------------------------------------------
    from PIL import Image, ImageDraw, ImageFont

    artifacts_dir = Path("C:/Users/sekha/.gemini/antigravity/brain/2dbccc89-e689-4ab9-9da5-8615b5c667af")
    img_files = [artifacts_dir / f"agneyam_comparison_{c['id']}.png" for c in CASES]
    pil_imgs = [Image.open(f) for f in img_files]

    # 1. 2x2 Grid Comparison Overview
    w, h = pil_imgs[0].size
    thumb_w, thumb_h = w // 2, h // 2
    grid_img = Image.new("RGB", (thumb_w * 2 + 30, thumb_h * 2 + 70), (245, 245, 245))

    positions = [
        (10, 40),
        (thumb_w + 20, 40),
        (10, thumb_h + 55),
        (thumb_w + 20, thumb_h + 55)
    ]

    for p_img, (gx, gy) in zip(pil_imgs, positions):
        resized = p_img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        grid_img.paste(resized, (gx, gy))

    draw = ImageDraw.Draw(grid_img)
    grid_path = artifacts_dir / "agneyam_4cases_overview_grid.png"
    grid_img.save(grid_path)
    print(f"[OK] Saved 2x2 grid overview: {grid_path}")

    # 2. Verse 1-2 Side-by-Side Zoom Crop Comparison
    # Crop Verse 1 & 2 area from each page: y from 22% to 48%, x from 7% to 93%
    crop_boxes = (int(w * 0.07), int(h * 0.22), int(w * 0.93), int(h * 0.46))
    cropped_verses = [img.crop(crop_boxes) for img in pil_imgs]
    
    vw, vh = cropped_verses[0].size
    composite_zoom = Image.new("RGB", (vw, vh * 4 + 160), (255, 255, 255))
    zdraw = ImageDraw.Draw(composite_zoom)

    labels = [
        "Case 1: Body Font Regular -- 18 pt (AdishilaVedic, Scale=1.50)",
        "Case 2: Body Font Bold -- 18 pt (AdishilaVedicBold, Scale=1.50)",
        "Case 3: Body Font Regular -- 20 pt (AdishilaVedic, Scale=1.68)",
        "Case 4: Body Font Bold -- 20 pt (AdishilaVedicBold, Scale=1.68)"
    ]

    for i, (cv, label) in enumerate(zip(cropped_verses, labels)):
        zy = i * (vh + 40)
        zdraw.rectangle([0, zy, vw, zy + 30], fill=(230, 235, 245))
        zdraw.text((20, zy + 6), label, fill=(10, 25, 80))
        composite_zoom.paste(cv, (0, zy + 32))
        zdraw.line([0, zy + vh + 36, vw, zy + vh + 36], fill=(180, 180, 180), width=2)

    zoom_path = artifacts_dir / "agneyam_4cases_verse_zoom.png"
    composite_zoom.save(zoom_path)
    print(f"[OK] Saved verse zoom comparison: {zoom_path}")

    # Clean up temp directory
    try:
        shutil.rmtree(TEMP_DIR)
        print("[CLEANUP] Removed temporary directory temp_font_comparison")
    except Exception as e:
        print(f"[WARN] Cleanup note: {e}")

if __name__ == "__main__":
    main()
