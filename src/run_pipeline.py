#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Master Jaimineeya Samavedam Pipeline Runner.

Automates the complete pipeline for Samhita in one shot:
  1. Devanagari (Input: data/input/Samhita_Devanagari_Unicode.txt):
     - PDF, HTML, and TXT outputs across:
       * Combined (Rik + Samam + meta)
       * Samam + meta & Rik + meta (Separate mode)
       * Samam only no meta & Rik only no meta (NoMeta mode)
  2. Malayalam (Input: data/input/Malayalam/Samam_Malayalam_Unicode.txt):
     - PDF, HTML, and TXT outputs (Kodunthirapully paddhati / -kpully):
       * Malayalam Kpully
       * Devanagari Kpully (transliterated from Malayalam AST)

Usage:
    # Full one-shot generation for Samhita (Devanagari + Malayalam Kpully in PDF, HTML, TXT):
    python src/run_pipeline.py

    # Fast generation (skip LaTeX PDF compilation, generate HTML and TXT):
    python src/run_pipeline.py --html-only

    # PDF-only compilation:
    python src/run_pipeline.py --pdf-only

    # Single script:
    python src/run_pipeline.py --script devanagari
    python src/run_pipeline.py --script malayalam
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

# Default source assets
DEFAULT_DEVA_INPUT = ROOT_DIR / "data" / "input" / "Samhita_Devanagari_Unicode.txt"
DEFAULT_DEVA_JSON = ROOT_DIR / "data" / "output" / "Samhita_corrected_out.json"

DEFAULT_MAL_INPUT = ROOT_DIR / "data" / "input" / "Malayalam" / "Samam_Malayalam_Unicode.txt"
DEFAULT_MAL_JSON = ROOT_DIR / "data" / "output" / "malayalam" / "Samam_Malayalam.json"
DEFAULT_KPULLY_JSON = ROOT_DIR / "Malayalam_JSV" / "malayalam" / "Samam_kpully_Devanagari_json.json"


def run_cmd(cmd_list, description=""):
    """Run a subprocess command with UTF-8 environment and verify return code."""
    if description:
        print(f"\n[PIPELINE] {description}...")
    print(f"  $ {' '.join(str(x) for x in cmd_list)}")
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(ROOT_DIR / "src")
    res = subprocess.run(cmd_list, cwd=str(ROOT_DIR), env=env)
    if res.returncode != 0:
        print(f"[ERROR] Step failed with exit code {res.returncode}: {description}", file=sys.stderr)
        sys.exit(res.returncode)


def main():
    parser = argparse.ArgumentParser(
        description="Run the end-to-end Jaimineeya Samavedam Samhita pipeline for Devanagari and Malayalam in one shot."
    )
    parser.add_argument(
        "--script",
        choices=["both", "devanagari", "malayalam"],
        default="both",
        help="Target script to process (default: both)",
    )
    parser.add_argument(
        "--deva-input",
        default=str(DEFAULT_DEVA_INPUT),
        help=f"Devanagari source text (default: {DEFAULT_DEVA_INPUT.relative_to(ROOT_DIR)})",
    )
    parser.add_argument(
        "--deva-json",
        default=str(DEFAULT_DEVA_JSON),
        help=f"Devanagari output JSON (default: {DEFAULT_DEVA_JSON.relative_to(ROOT_DIR)})",
    )
    parser.add_argument(
        "--mal-input",
        default=str(DEFAULT_MAL_INPUT),
        help=f"Malayalam source text (default: {DEFAULT_MAL_INPUT.relative_to(ROOT_DIR)})",
    )
    parser.add_argument(
        "--mal-json",
        default=str(DEFAULT_MAL_JSON),
        help=f"Malayalam output JSON (default: {DEFAULT_MAL_JSON.relative_to(ROOT_DIR)})",
    )
    parser.add_argument(
        "--deva-modes",
        nargs="+",
        choices=["combined", "separate", "nometa"],
        default=["combined", "separate", "nometa"],
        help="Output modes to render for Devanagari (default: combined separate nometa)",
    )
    parser.add_argument(
        "--html-only",
        action="store_true",
        help="Generate only HTML and text outputs (skip PDF compilation)",
    )
    parser.add_argument(
        "--pdf-only",
        action="store_true",
        help="Generate only PDF outputs",
    )
    parser.add_argument(
        "--txt-only",
        action="store_true",
        help="Generate only plain text outputs",
    )
    parser.add_argument(
        "--legacy-html",
        action="store_true",
        help="Use legacy single-page HTML layout instead of modern VedaVMS reader layout",
    )

    args = parser.parse_args()

    start_time = time.time()
    scripts_to_run = ["devanagari", "malayalam"] if args.script == "both" else [args.script]

    format_label = "HTML, PDF, TXT"
    if args.html_only:
        format_label = "HTML, TXT"
    elif args.pdf_only:
        format_label = "PDF"
    elif args.txt_only:
        format_label = "TXT"

    print("=" * 70)
    print(" Jaimineeya Samavedam — Full Samhita Publication Pipeline")
    print("=" * 70)
    print(f" Target Script(s) : {', '.join(s.capitalize() for s in scripts_to_run)}")
    if "devanagari" in scripts_to_run:
        print(f" Devanagari Modes : {', '.join(args.deva_modes)}")
    if "malayalam" in scripts_to_run:
        print(f" Malayalam Modes  : KPully (Malayalam & Devanagari)")
    print(f" Target Formats   : {format_label}")
    print("=" * 70)

    # Format dispatch flags
    extra_flags = []
    if args.html_only:
        extra_flags.append("--html-only")
    elif args.pdf_only:
        extra_flags.append("--pdf-only")
    elif args.txt_only:
        extra_flags.append("--txt-only")
    if args.legacy_html:
        extra_flags.append("--legacy-html")

    # ----------------------------------------------------
    # 1. DEVANAGARI PIPELINE
    # ----------------------------------------------------
    if "devanagari" in scripts_to_run:
        deva_input_path = Path(args.deva_input).resolve()
        deva_json_path = Path(args.deva_json).resolve()

        if not deva_input_path.exists():
            print(f"[ERROR] Devanagari input file not found: {deva_input_path}", file=sys.stderr)
            sys.exit(1)

        deva_json_path.parent.mkdir(parents=True, exist_ok=True)

        # Step 1A: Parse source text to JSON AST
        run_cmd(
            [
                sys.executable,
                "-X", "utf8",
                str(ROOT_DIR / "src" / "generate_json.py"),
                str(deva_input_path),
                "--output",
                str(deva_json_path),
            ],
            description="Devanagari Step 1: Generating JSON AST from source text",
        )

        # Step 1B: Render Devanagari in requested modes
        # combined -> Samhita_Devanagari (Combined: Rik + Samam + meta)
        # separate -> Rik_Devanagari (Rik+meta) & Samam_Devanagari (Samam+meta)
        # nometa   -> Rik_NoMeta_Devanagari (Rik only no meta) & Samam_NoMeta_Devanagari (Samam only no meta)
        mode_descriptions = {
            "combined": "Combined (Rik + Samam + Metadata)",
            "separate": "Samam+meta and Rik+meta",
            "nometa": "Samam only (no meta) and Rik only (no meta)",
        }
        for mode in args.deva_modes:
            cmd = [
                sys.executable,
                "-X", "utf8",
                str(ROOT_DIR / "src" / "render_pdf.py"),
                str(deva_json_path),
                "--script", "devanagari",
                "--output-mode", mode,
            ] + extra_flags
            desc = mode_descriptions.get(mode, mode)
            run_cmd(cmd, description=f"Devanagari Step 2: Rendering {desc} ({format_label})")

    # ----------------------------------------------------
    # 2. MALAYALAM PIPELINE (KPULLY FOR MALAYALAM & DEVANAGARI)
    # ----------------------------------------------------
    if "malayalam" in scripts_to_run:
        mal_input_path = Path(args.mal_input).resolve()
        mal_json_path = Path(args.mal_json).resolve()

        if not mal_input_path.exists():
            print(f"[ERROR] Malayalam input file not found: {mal_input_path}", file=sys.stderr)
            sys.exit(1)

        mal_json_path.parent.mkdir(parents=True, exist_ok=True)

        # Step 2A: Parse source text to JSON AST
        run_cmd(
            [
                sys.executable,
                "-X", "utf8",
                str(ROOT_DIR / "src" / "generate_json.py"),
                str(mal_input_path),
                "--output",
                str(mal_json_path),
            ],
            description="Malayalam Step 1: Generating JSON AST from source text",
        )

        # Step 2B: Render Malayalam Kpully (PDF, HTML, TXT)
        mal_kpully_cmd = [
            sys.executable,
            "-X", "utf8",
            str(ROOT_DIR / "src" / "render_pdf.py"),
            str(mal_json_path),
            "--script", "malayalam",
            "-kpully",
            "--output-mode", "separate",
            "--samam-only",
            "-o", "Samam_kpully_Malayalam",
        ] + extra_flags
        run_cmd(mal_kpully_cmd, description=f"Malayalam Step 2: Rendering Malayalam KPully ({format_label})")

        # Step 2C: Transliterate Malayalam AST to Devanagari AST for Kpully rendering
        kpully_json_path = ROOT_DIR / "Malayalam_JSV" / "malayalam" / "Samam_kpully_Devanagari_json.json"
        try:
            from malayalam.ml_transliterate import convert_malayalam_data_to_devanagari
            import json
            with open(mal_json_path, "r", encoding="utf-8") as f_in:
                mal_data = json.load(f_in)
            deva_data = convert_malayalam_data_to_devanagari(mal_data)
            kpully_json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(kpully_json_path, "w", encoding="utf-8") as f_out:
                json.dump(deva_data, f_out, ensure_ascii=False, indent=2)
            print(f"[INFO] Synced Devanagari AST from Malayalam -> {kpully_json_path.relative_to(ROOT_DIR)}")
        except Exception as e:
            print(f"[WARN] Could not update {kpully_json_path.name}: {e}")

        # Step 2D: Render Devanagari Kpully (PDF, HTML, TXT) from Malayalam AST
        if kpully_json_path.exists():
            deva_kpully_from_mal_cmd = [
                sys.executable,
                "-X", "utf8",
                str(ROOT_DIR / "src" / "render_pdf.py"),
                str(kpully_json_path),
                "--script", "devanagari",
                "-kpully",
                "--output-mode", "separate",
                "--samam-only",
                "-o", "Samhita_kpully_Devanagari",
            ] + extra_flags
            run_cmd(deva_kpully_from_mal_cmd, description=f"Malayalam Step 3: Rendering Devanagari KPully ({format_label})")

    elapsed = time.time() - start_time

    # ----------------------------------------------------
    # SUMMARY & ARTIFACT REPORT
    # ----------------------------------------------------
    print("\n" + "=" * 70)
    print(f" Samhita Full Pipeline Completed Successfully in {elapsed:.1f} seconds!")
    print("=" * 70)

    if "devanagari" in scripts_to_run:
        print("\n [Devanagari Outputs] (data/output/{pdf,html,txt}/Devanagari/)")
        if "combined" in args.deva_modes:
            print("   1. Combined (Rik + Samam + meta) : Samhita_Devanagari.{pdf,html,txt}")
        if "separate" in args.deva_modes:
            print("   2. Samam + meta                  : Samam_Devanagari.{pdf,html,txt}")
            print("   3. Rik + meta                    : Rik_Devanagari.{pdf,html,txt}")
        if "nometa" in args.deva_modes:
            print("   4. Samam only (no meta)          : Samam_NoMeta_Devanagari.{pdf,html,txt}")
            print("   5. Rik only (no meta)            : Rik_NoMeta_Devanagari.{pdf,html,txt}")

    if "malayalam" in scripts_to_run:
        print("\n [Malayalam Outputs]")
        print("   6. Malayalam KPully              : data/output/{pdf,html,txt}/Malayalam/Samam_kpully_Malayalam.{pdf,html,txt}")
        print("   7. Devanagari KPully (from Mal)  : data/output/{pdf,html,txt}/Devanagari/Samhita_kpully_Devanagari.{pdf,html,txt}")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
