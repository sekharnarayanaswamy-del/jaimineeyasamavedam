"""
Grantha Pipeline Runner for Jaimineeya Samavedam.
-------------------------------------------------
Generates PDF, HTML, and TXT outputs for Samhita and Aranyakam (Aaranam)
transliterated into the Grantha script.
Explicitly excludes micro-website generation.
"""

import sys
import os
import shutil
import argparse
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

CORPORA = [
    {
        "name": "Aranyakam",
        "type": "aaranam",
        "input": "data/corpora/aaranam/02_ast/Aaranam_ast.json",
        "out_name": "Aaranam_Grantha",
        "bw_out_name": "Aaranam_flow_bw_Grantha",
        "bw_alias": "Aaranam_bw_Grantha",
        "render_dir": "data/corpora/aaranam/05_renders/pdf",
        "expected_files": [
            "data/corpora/aaranam/05_renders/pdf/Aaranam_Grantha.pdf",
            "data/corpora/aaranam/05_renders/html/Aaranam_Grantha.html",
            "data/corpora/aaranam/05_renders/txt/Aaranam_Grantha_Unicode.txt",
        ]
    },
    {
        "name": "Samhita",
        "type": "samhita",
        "input": "data/corpora/samhita/02_ast/Samhita_ast.json",
        "out_name": "Samhita_Grantha",
        "bw_out_name": "Samhita_flow_bw_Grantha",
        "bw_alias": "Samhita_bw_Grantha",
        "render_dir": "data/corpora/samhita/05_renders/pdf",
        "expected_files": [
            "data/corpora/samhita/05_renders/pdf/Samhita_Grantha.pdf",
            "data/corpora/samhita/05_renders/html/Samhita_Grantha.html",
            "data/corpora/samhita/05_renders/txt/Samhita_Grantha_Unicode.txt",
        ]
    }
]

def run_grantha_pipeline(pdf_color_mode='all'):
    python_exe = sys.executable
    render_script = str(ROOT_DIR / "src" / "render.py")
    all_success = True

    print("=" * 70)
    print("JAIMINEEYA SAMAVEDAM - GRANTHA SCRIPT RENDERING PIPELINE")
    print("Targets: PDF (LuaLaTeX), HTML (VedaVMS Reader), TXT (Plain Unicode)")
    print("Corpora: Samhita and Aranyakam (Aaranam)")
    print(f"Color Mode: {pdf_color_mode.upper()}")
    print("Note: Website generation is intentionally skipped.")
    print("=" * 70)

    for corpus in CORPORA:
        name = corpus["name"]
        inp = str(ROOT_DIR / corpus["input"])
        out = corpus["out_name"]
        ctype = corpus["type"]

        # 1. Color Flow Render
        if pdf_color_mode in ('color', 'all'):
            print(f"\n[>>>] Processing {name} ({ctype}) - Color Flow...")
            cmd = [
                python_exe,
                render_script,
                inp,
                "--script", "grantha",
                "--type", ctype,
                "--flow",
                "--pdf-color-mode", "color",
                "-o", out
            ]

            res = subprocess.run(cmd, cwd=str(ROOT_DIR))
            if res.returncode != 0:
                print(f"[ERROR] Failed to render {name} in Grantha script (exit code {res.returncode})")
                all_success = False
            else:
                print(f"[OK] Render completed for {name} (Color Flow).")
                for exp in corpus["expected_files"]:
                    exp_path = ROOT_DIR / exp
                    if exp_path.exists():
                        print(f"     + {exp} ({exp_path.stat().st_size:,} bytes)")
                    else:
                        print(f"     ! Missing expected file: {exp}")
                        all_success = False

        # 2. Black & White A4 Flow Render
        if pdf_color_mode in ('bw', 'all'):
            bw_name = corpus["bw_out_name"]
            print(f"\n[>>>] Processing {name} ({ctype}) - Black & White A4 Flow...")
            cmd_bw = [
                python_exe,
                render_script,
                inp,
                "--script", "grantha",
                "--type", ctype,
                "--flow",
                "--pdf-color-mode", "bw",
                "--pdf-only",
                "-o", bw_name
            ]

            res_bw = subprocess.run(cmd_bw, cwd=str(ROOT_DIR))
            if res_bw.returncode != 0:
                print(f"[ERROR] Failed to render BW {name} in Grantha script (exit code {res_bw.returncode})")
                all_success = False
            else:
                bw_pdf = ROOT_DIR / corpus["render_dir"] / f"{bw_name}.pdf"
                alias_pdf = ROOT_DIR / corpus["render_dir"] / f"{corpus['bw_alias']}.pdf"
                if bw_pdf.exists():
                    print(f"     + {bw_pdf.relative_to(ROOT_DIR)} ({bw_pdf.stat().st_size:,} bytes)")
                    try:
                        shutil.copyfile(bw_pdf, alias_pdf)
                        print(f"     + Alias: {alias_pdf.relative_to(ROOT_DIR)} ({alias_pdf.stat().st_size:,} bytes)")
                    except Exception as e:
                        print(f"     ! Could not create alias {alias_pdf.name}: {e}")
                else:
                    print(f"     ! Missing expected file: {bw_pdf.relative_to(ROOT_DIR)}")
                    all_success = False

    print("\n" + "=" * 70)
    if all_success:
        print("[SUCCESS] All Grantha renders generated and verified successfully!")
    else:
        print("[FAILURE] Some files failed to generate. Check logs above.")
    print("=" * 70)
    return 0 if all_success else 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grantha rendering pipeline")
    parser.add_argument("--pdf-color-mode", choices=["color", "bw", "all"], default="all",
                        help="Color mode for PDF: color, bw, or all (default: all)")
    parser.add_argument("--bw", action="store_true", help="Generate BW PDF only")
    args = parser.parse_args()

    mode = "bw" if args.bw else args.pdf_color_mode
    sys.exit(run_grantha_pipeline(pdf_color_mode=mode))
