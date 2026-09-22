#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Malayalam Jaimineeya Samavedam Pipeline Runner.

Automates the complete Malayalam pipeline:
  1. Plain-text parsing to JSON AST (via src/generate_json.py)
  2. Multi-mode rendering (Combined, Separate, NoMeta) to HTML, PDF, Malayalam TXT,
     and Transliterated Devanagari TXT (via src/render_pdf.py --script malayalam)
  3. Optional sync to docs/ directory for GitHub Pages live preview

Usage:
    python src/run_malayalam_pipeline.py
    python src/run_malayalam_pipeline.py data/input/Malayalam/Samam_Malayalam_Unicode.txt
    python src/run_malayalam_pipeline.py --html-only --publish
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

DEFAULT_INPUT_TXT = ROOT_DIR / "data" / "input" / "Malayalam" / "Samam_Malayalam_Unicode.txt"
DEFAULT_JSON_OUT = ROOT_DIR / "Malayalam_JSV" / "malayalam" / "Samam_Malayalam_out.json"
DEFAULT_OUTPUT_BASE = "Samam_Malayalam_Samam"
DOCS_DIR = ROOT_DIR / "docs"


def run_cmd(cmd_list, description=""):
    """Run a subprocess command with UTF-8 encoding and check return code."""
    if description:
        print(f"\n[PIPELINE] {description}...")
    print(f"  $ {' '.join(str(x) for x in cmd_list)}")
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    res = subprocess.run(cmd_list, cwd=str(ROOT_DIR), env=env)
    if res.returncode != 0:
        print(f"[ERROR] Step failed with exit code {res.returncode}: {description}", file=sys.stderr)
        sys.exit(res.returncode)


def main():
    parser = argparse.ArgumentParser(description="Run the full Malayalam Jaimineeya Samavedam pipeline.")
    parser.add_argument(
        "input_file",
        nargs="?",
        default=str(DEFAULT_INPUT_TXT),
        help=f"Input Malayalam plain text file (default: {DEFAULT_INPUT_TXT.relative_to(ROOT_DIR)})",
    )
    parser.add_argument(
        "--json-output",
        "-j",
        default=str(DEFAULT_JSON_OUT),
        help=f"Output JSON AST path (default: {DEFAULT_JSON_OUT.relative_to(ROOT_DIR)})",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=DEFAULT_OUTPUT_BASE,
        help=f"Output file basename or prefix (default: {DEFAULT_OUTPUT_BASE})",
    )
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=["separate", "nometa", "combined"],
        default=["separate"],
        help="Output modes to render (default: separate [Samam-only])",
    )
    parser.add_argument(
        "--samam-only",
        action="store_true",
        default=True,
        help="Generate only Samam output (default: True)",
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
        "--publish",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Publish to docs/ (default: False; docs/ is reserved for src/generate_website.py)",
    )
    parser.add_argument(
        "--skip-kpully",
        action="store_true",
        help="Skip Devanagari Kpully HTML+PDF generation",
    )
    parser.add_argument(
        "--legacy-html",
        action="store_true",
        help="Use legacy single-page HTML layout instead of modern VedaVMS reader layout",
    )

    args = parser.parse_args()

    input_path = Path(args.input_file).resolve()
    json_path = Path(args.json_output).resolve()
    output_base_name = Path(args.output).stem if Path(args.output).suffix else Path(args.output).name

    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    json_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(" Malayalam Jaimineeya Samavedam Pipeline")
    print("=" * 60)
    print(f" Input File : {input_path.relative_to(ROOT_DIR)}")
    print(f" JSON AST   : {json_path.relative_to(ROOT_DIR)}")
    print(f" Output Base: {output_base_name}")
    print(f" Modes      : {', '.join(args.modes)}")
    if args.html_only:
        print(" Flags      : --html-only")
    elif args.pdf_only:
        print(" Flags      : --pdf-only")
    print("=" * 60)

    # 1. JSON Generation
    generate_json_cmd = [
        sys.executable,
        str(ROOT_DIR / "src" / "generate_json.py"),
        str(input_path),
        "--output",
        str(json_path),
    ]
    run_cmd(generate_json_cmd, description="Step 1: Generating JSON AST")

    # 1b. Generate / Sync Devanagari AST for Kpully rendering
    kpully_json_path = ROOT_DIR / "Malayalam_JSV" / "malayalam" / "Samam_kpully_Devanagari_json.json"
    if not args.skip_kpully:
        try:
            from malayalam.ml_transliterate import convert_malayalam_data_to_devanagari
            import json
            with open(json_path, "r", encoding="utf-8") as f_in:
                mal_data = json.load(f_in)
            deva_data = convert_malayalam_data_to_devanagari(mal_data)
            kpully_json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(kpully_json_path, "w", encoding="utf-8") as f_out:
                json.dump(deva_data, f_out, ensure_ascii=False, indent=2)
            print(f"[INFO] Synced Devanagari AST -> {kpully_json_path.relative_to(ROOT_DIR)}")
        except Exception as e:
            print(f"[WARN] Could not update {kpully_json_path.name}: {e}")

    # 2. Rendering across selected modes (Samam-only)
    extra_flags = []
    if args.samam_only:
        extra_flags.append("--samam-only")
    if args.html_only:
        extra_flags.append("--html-only")
    elif args.pdf_only:
        extra_flags.append("--pdf-only")
    if args.legacy_html:
        extra_flags.append("--legacy-html")

    for mode in args.modes:
        render_cmd = [
            sys.executable,
            "-X", "utf8",
            str(ROOT_DIR / "src" / "render_pdf.py"),
            str(json_path),
            "--script",
            "malayalam",
            "--output-mode",
            mode,
            "-o",
            output_base_name,
        ] + extra_flags
        run_cmd(render_cmd, description=f"Step 2: Rendering in '{mode}' mode")

    # 2b. Malayalam Kpully Rendering (HTML + PDF) - Samam only
    if not args.skip_kpully:
        mal_kpully_cmd = [
            sys.executable,
            "-X", "utf8",
            str(ROOT_DIR / "src" / "render_pdf.py"),
            str(json_path),
            "--script",
            "malayalam",
            "-kpully",
            "--output-mode",
            "separate",
            "--samam-only",
            "-o",
            "Samam_kpully_Malayalam",
        ] + extra_flags
        run_cmd(mal_kpully_cmd, description="Step 2b: Rendering Malayalam Kpully (HTML + PDF, Samam-only)")

    # 2c. Devanagari Kpully Rendering (HTML + PDF) - Samam only, no Rik mode
    if not args.skip_kpully and kpully_json_path.exists():
        kpully_cmd = [
            sys.executable,
            "-X", "utf8",
            str(ROOT_DIR / "src" / "render_pdf.py"),
            str(kpully_json_path),
            "--script",
            "devanagari",
            "-kpully",
            "--output-mode",
            "separate",
            "--samam-only",
            "-o",
            "Samhita_kpully_Devanagari",
        ] + extra_flags
        run_cmd(kpully_cmd, description="Step 2c: Rendering Devanagari Kpully (HTML + PDF, Samam-only)")

    # 3. Publishing step: Reserved for src/generate_website.py
    if args.publish:
        print("\n[PIPELINE] Step 3: Publishing HTML and PDF files to docs/...")
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        malayalam_docs_dir = DOCS_DIR / "malayalam"
        malayalam_docs_dir.mkdir(parents=True, exist_ok=True)

        html_dir = ROOT_DIR / "data" / "output" / "html" / "Malayalam"
        copied = []
        for html_file in html_dir.glob(f"{output_base_name}*.html"):
            target_mal = malayalam_docs_dir / html_file.name
            shutil.copy2(html_file, target_mal)
            copied.append(target_mal)
        if copied:
            print(f"[INFO] Published {len(copied)} files to docs/")
    else:
        print("\n[INFO] 'docs/' directory is reserved for 'src/generate_website.py'. Pipeline outputs are preserved in data/output/.")

    print("\n" + "=" * 60)
    print(" Pipeline completed successfully!")
    print("=" * 60)
    print(" Generated Artifacts:")
    print(f"  - HTML     : data/output/html/Malayalam/{output_base_name}.html")
    print(f"  - PDF      : data/output/pdf/Malayalam/{output_base_name}.pdf")
    print(f"  - TXT      : data/output/txt/Malayalam/{output_base_name}_Unicode.txt")
    if not args.skip_kpully:
        print(f"  - Malayalam KPully HTML : data/output/html/Malayalam/Samam_kpully_Malayalam.html")
        print(f"  - Malayalam KPully PDF  : data/output/pdf/Malayalam/Samam_kpully_Malayalam.pdf")
        print(f"  - Malayalam KPully TXT  : data/output/txt/Malayalam/Samam_kpully_Malayalam_Unicode.txt")
        print(f"  - Devanagari KPully HTML: data/output/html/Devanagari/Samhita_kpully_Devanagari.html")
        print(f"  - Devanagari KPully PDF : data/output/pdf/Devanagari/Samhita_kpully_Devanagari.pdf")
        print(f"  - Devanagari KPully TXT : data/output/txt/Devanagari/Samhita_kpully_Devanagari_Unicode.txt")
    print(f"  Note: 'docs/' folder is reserved for 'src/generate_website.py'.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
