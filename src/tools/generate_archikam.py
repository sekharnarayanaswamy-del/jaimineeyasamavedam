#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jaimineeya Samavedam - Purvarchikam & Uttararchikam (Rik Only) Generator.
-----------------------------------------------------------------------
Extracts Purvarchikam or Uttararchikam from data/input/vedic_text.txt,
builds the canonical AST JSON via generate_json.py, and renders publication-grade
HTML readers, PDFs (via LuaLaTeX), and plain-text exports via render.py.

Usage:
    # Generate both Purvarchikam and Uttararchikam (HTML + Text):
    python src/tools/generate_archikam.py --archikam both --no-pdf

    # Generate Purvarchikam (PDF + HTML + Text):
    python src/tools/generate_archikam.py --archikam purvarchikam

    # Generate Uttararchikam (PDF + HTML + Text):
    python src/tools/generate_archikam.py --archikam uttararchikam

    # Generate HTML only:
    python src/tools/generate_archikam.py --archikam purvarchikam --html-only
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]


def run_command(cmd_list, description=""):
    if description:
        print(f"\n[ARCHIKAM] {description}...")
    print(f"  $ {' '.join(str(x) for x in cmd_list)}")
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(ROOT_DIR / "src")
    res = subprocess.run(cmd_list, cwd=str(ROOT_DIR), env=env)
    if res.returncode != 0:
        print(f"[ERROR] Step failed with exit code {res.returncode}: {description}", file=sys.stderr)
        sys.exit(res.returncode)


def process_archikam(archikam_type, formats, output_override=None, kpully=False):
    title_label = "Purvarchikam (पूर्वार्चिकम्)" if archikam_type == "purvarchikam" else "Uttararchikam (उत्तरार्चिकम्)"
    print(f"\n{'='*70}")
    print(f" Generating {title_label} - Rik Only")
    print(f"{'='*70}")

    input_file = ROOT_DIR / "data" / "input" / "vedic_text.txt"
    if not input_file.exists():
        print(f"[ERROR] Master Vedic text not found at {input_file}", file=sys.stderr)
        sys.exit(1)

    json_file = ROOT_DIR / "data" / "output" / f"{archikam_type.capitalize()}_out.json"

    # Step 1: Generate JSON AST
    run_command(
        [
            sys.executable,
            "-X", "utf8",
            str(ROOT_DIR / "src" / "generate_json.py"),
            str(input_file),
            "--type", archikam_type,
            "--output", str(json_file),
        ],
        description=f"Step 1: Generating JSON AST for {archikam_type.capitalize()}",
    )

    # Step 2: Render
    render_flags = []
    if "pdf" not in formats and ("html" in formats and "txt" in formats):
        render_flags.append("--no-pdf")
    elif "pdf" not in formats and "html" in formats:
        render_flags.append("--html-only")
    elif formats == ["pdf"]:
        render_flags.append("--pdf-only")
    elif formats == ["txt"]:
        render_flags.append("--txt-only")

    if kpully:
        render_flags.append("-kpully")

    out_name = output_override or f"{archikam_type.capitalize()}"

    run_command(
        [
            sys.executable,
            "-X", "utf8",
            str(ROOT_DIR / "src" / "render.py"),
            str(json_file),
            "--type", archikam_type,
            "--output-mode", "separate",
            "--rik-only",
            "-o", out_name,
        ] + render_flags,
        description=f"Step 2: Rendering {archikam_type.capitalize()} documents ({', '.join(formats).upper()})",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate Purvarchikam and Uttararchikam (Rik only) using unified pipeline templates."
    )
    parser.add_argument(
        "--archikam", "-a",
        choices=["purvarchikam", "uttararchikam", "both"],
        default="both",
        help="Target Archikam to generate: purvarchikam, uttararchikam, or both (default: both)",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["pdf", "html", "txt", "all"],
        default="all",
        help="Output format: pdf, html, txt, or all (default: all)",
    )
    parser.add_argument(
        "--no-pdf",
        action="store_true",
        help="Skip PDF compilation (generates HTML and Text only)",
    )
    parser.add_argument(
        "--html-only",
        action="store_true",
        help="Generate only HTML output",
    )
    parser.add_argument(
        "--pdf-only",
        action="store_true",
        help="Generate only PDF output",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Custom output base filename",
    )
    parser.add_argument(
        "-kpully", "--kpully",
        action="store_true",
        default=False,
        help="Enable Kodunthirapully stacked swara rendering",
    )

    args = parser.parse_args()

    # Determine formats
    if args.html_only:
        formats = ["html"]
    elif args.pdf_only:
        formats = ["pdf"]
    elif args.no_pdf:
        formats = ["html", "txt"]
    elif args.format == "all":
        formats = ["pdf", "html", "txt"]
    else:
        formats = [args.format]

    targets = ["purvarchikam", "uttararchikam"] if args.archikam == "both" else [args.archikam]

    for target in targets:
        process_archikam(target, formats, output_override=args.output, kpully=args.kpully)

    # Step 3: Stage into data/corpora/Rik/ and update run_manifest and TRACEABILITY.md
    run_command(
        [
            sys.executable,
            "-X", "utf8",
            str(ROOT_DIR / "src" / "tools" / "migrate_corpora_and_archive.py"),
            "--keep-legacy",
        ],
        description="Syncing outputs to data/corpora/Rik/ stage directory and refreshing Traceability Report",
    )

    print("\n" + "=" * 70)
    print(" Archikam Generation Completed Successfully!")
    print(f" Outputs available in: {ROOT_DIR / 'data' / 'corpora' / 'Rik' / '05_renders'}")
    print(f" Traceability Report : {ROOT_DIR / 'data' / 'corpora' / 'Rik' / '06_reports' / 'TRACEABILITY.md'}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
