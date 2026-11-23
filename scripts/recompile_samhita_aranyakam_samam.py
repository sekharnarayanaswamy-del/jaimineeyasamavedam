#!/usr/bin/env python3
"""
Unified Samhita + Aranyakam Samam-only Edition Generator (Devanagari):
---------------------------------------------------------------------
Compiles the combined Samam chanting text with associated metadata
(Samam header + Saman metadata, excluding Rik verses) for both Samhita
and Aranyakam into a single continuous-flow publication.

Variants:
1. A4 Flow (Color & BW):
   - Samhita_Aranyakam_flow_Samam_Devanagari.pdf (alias Samhita_Aranyakam_Samam_Devanagari.pdf)
   - Samhita_Aranyakam_flow_bw_Samam_Devanagari.pdf (alias Samhita_Aranyakam_bw_Samam_Devanagari.pdf)
2. Book Flow (when requested via --book):
   - Samhita_Aranyakam_book_flow_Samam_Devanagari.pdf (alias Samhita_Aranyakam_book_Samam_Devanagari.pdf)
   - Samhita_Aranyakam_book_flow_bw_Samam_Devanagari.pdf (alias Samhita_Aranyakam_book_bw_Samam_Devanagari.pdf)
"""

import sys
import shutil
import argparse
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def compile_variant(book=False, color_mode="color"):
    python_exe = sys.executable
    render_script = str(ROOT_DIR / "src" / "render.py")
    ast_builder = str(ROOT_DIR / "scripts" / "build_combined_ast.py")

    # 1. Ensure combined AST is up to date
    res_ast = subprocess.run([python_exe, ast_builder], cwd=str(ROOT_DIR))
    if res_ast.returncode != 0:
        print("[ERROR] Failed to build combined AST.")
        return 1

    ast_file = str(ROOT_DIR / "data" / "corpora" / "samhita_aranyakam" / "02_ast" / "Samhita_Aranyakam_ast.json")
    out_dir = str(ROOT_DIR / "data" / "corpora" / "samhita_aranyakam" / "05_renders" / "pdf")

    pfx_parts = ["Samhita_Aranyakam"]
    if book:
        pfx_parts.append("book")
    pfx_parts.append("flow")
    if color_mode == "bw":
        pfx_parts.append("bw")
    pfx_parts.append("Samam")

    base_name = "_".join(pfx_parts)

    cmd = [
        python_exe, "-X", "utf8",
        render_script,
        ast_file,
        "--type", "samhita",
        "--output-mode", "separate",
        "--samam-only",
        "--flow",
        "--title", "जैमिनीयसामवेद-संहितारण्यकम्",
        "--pdf-color-mode", color_mode,
        "--pdf-only",
        "--output-dir", out_dir,
        "-o", base_name
    ]

    if book:
        cmd.append("--book-print")

    print(f"\n[>>>] Compiling Combined Samam Edition ({base_name}, mode={color_mode})...")
    res = subprocess.run(cmd, cwd=str(ROOT_DIR))
    if res.returncode != 0:
        print(f"[ERROR] Failed to compile {base_name} (exit code {res.returncode})")
        return res.returncode

    # Create convenient alias
    gen_pdf = Path(out_dir) / f"{base_name}_Devanagari.pdf"
    prev_pdf = Path(out_dir) / f"{base_name}_Devanagari_preview.pdf"

    # If preview is newer than gen_pdf (e.g. gen_pdf was locked during compilation), try overwriting gen_pdf
    if prev_pdf.exists():
        if not gen_pdf.exists() or prev_pdf.stat().st_mtime > gen_pdf.stat().st_mtime:
            try:
                shutil.copyfile(prev_pdf, gen_pdf)
                print(f"[SYNC] Overwrote locked file with latest preview: {gen_pdf.name}")
            except Exception as e:
                print(f"[INFO] Main file currently locked in viewer ({e}); alias will use preview.")

    actual_src = gen_pdf if gen_pdf.exists() else prev_pdf
    if prev_pdf.exists() and gen_pdf.exists() and prev_pdf.stat().st_mtime > gen_pdf.stat().st_mtime:
        actual_src = prev_pdf

    alias_parts = ["Samhita_Aranyakam"]
    if book:
        alias_parts.append("book")
    if color_mode == "bw":
        alias_parts.append("bw")
    alias_parts.append("Samam_Devanagari.pdf")
    alias_pdf = Path(out_dir) / "_".join(alias_parts)

    if actual_src.exists():
        print(f"[SUCCESS] Generated: {actual_src.relative_to(ROOT_DIR)} ({actual_src.stat().st_size:,} bytes)")
        try:
            shutil.copyfile(actual_src, alias_pdf)
            print(f"[ALIAS] Created: {alias_pdf.relative_to(ROOT_DIR)} ({alias_pdf.stat().st_size:,} bytes)")
        except Exception as e:
            print(f"[WARN] Could not create alias {alias_pdf.name}: {e}")
    else:
        print(f"[ERROR] Expected PDF not found: {gen_pdf}")
        return 1

    return 0

def main():
    parser = argparse.ArgumentParser(description="Compile combined Samhita+Aranyakam Samam-only edition")
    parser.add_argument("--book", action="store_true", help="Compile 180x228mm Book format instead of A4")
    parser.add_argument("--bw", action="store_true", help="Compile Black & White edition")
    parser.add_argument("--all-colors", action="store_true", help="Compile both Color and BW editions")
    args = parser.parse_args()

    modes = []
    if args.all_colors:
        modes = ["color", "bw"]
    elif args.bw:
        modes = ["bw"]
    else:
        modes = ["color"]

    for m in modes:
        rc = compile_variant(book=args.book, color_mode=m)
        if rc != 0:
            return rc

    return 0

if __name__ == "__main__":
    sys.exit(main())
