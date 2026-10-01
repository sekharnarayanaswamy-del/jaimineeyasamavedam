#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Master Jaimineeya Samavedam Pipeline Runner.

Automates the complete pipeline across corpora (Samhita, Aaranam, Collections)
and target scripts (Devanagari, Malayalam) with full support for named render profiles.

Named Profiles (configured in src/pipeline_config.yaml):
  - fast_preview : HTML & TXT in Kodunthirapully mode (skips slow LaTeX PDF compilation)
  - standard     : PDF + HTML for active texts (Samhita, Aaranam)
  - chanting     : Practitioner chanting editions (NoMeta, swaras above/below)
  - full_release : Complete formal release suite (All corpora, all modes, PDF/HTML/TXT)

Usage:
    # Run active default profile from pipeline_config.yaml (defaults to fast_preview):
    python src/run_pipeline.py

    # Run a specific named profile:
    python src/run_pipeline.py --profile fast_preview
    python src/run_pipeline.py -p standard
    python src/run_pipeline.py -p chanting
    python src/run_pipeline.py -p full_release

    # Inspect all configured profiles:
    python src/run_pipeline.py --list-profiles

    # Ad-hoc overrides:
    python src/run_pipeline.py --html-only
    python src/run_pipeline.py --corpora samhita aaranam
    python src/run_pipeline.py --modes combined separate
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

# Default source assets
DEFAULT_DEVA_INPUT = (
    ROOT_DIR / "data" / "corpora" / "samhita" / "01_input" / "Samhita_Devanagari_Unicode.txt"
    if (ROOT_DIR / "data" / "corpora" / "samhita" / "01_input" / "Samhita_Devanagari_Unicode.txt").exists()
    else ROOT_DIR / "data" / "input" / "Samhita_Devanagari_Unicode.txt"
)
DEFAULT_DEVA_JSON = ROOT_DIR / "data" / "output" / "Samhita_corrected_out.json"

DEFAULT_AARANAM_INPUT = (
    ROOT_DIR / "data" / "corpora" / "aaranam" / "01_input" / "Aaranam_latest.txt"
    if (ROOT_DIR / "data" / "corpora" / "aaranam" / "01_input" / "Aaranam_latest.txt").exists()
    else ROOT_DIR / "data" / "input" / "Aaranam_latest.txt"
)
DEFAULT_AARANAM_JSON = ROOT_DIR / "data" / "output" / "Aaranam_latest_out.json"

DEFAULT_COLLECTION_JSON = ROOT_DIR / "data" / "output" / "Collection_latest_out.json"

DEFAULT_MAL_INPUT = ROOT_DIR / "data" / "input" / "Malayalam" / "Samam_Malayalam_Unicode.txt"
DEFAULT_MAL_JSON = ROOT_DIR / "data" / "output" / "malayalam" / "Samam_Malayalam.json"
DEFAULT_KPULLY_JSON = ROOT_DIR / "Malayalam_JSV" / "malayalam" / "Samam_kpully_Devanagari_json.json"


def load_config():
    """Load centralized pipeline configuration."""
    sys.path.insert(0, str(ROOT_DIR / "src"))
    from utils import load_pipeline_config
    return load_pipeline_config()


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


def sync_standalone_readers():
    """Copies canonical standalone HTML readers to docs/standalone-html/ for GitHub Pages."""
    docs_standalone = ROOT_DIR / "docs" / "standalone-html"
    docs_standalone.mkdir(parents=True, exist_ok=True)
    (docs_standalone / "Malayalam").mkdir(exist_ok=True)
    (docs_standalone / "Devanagari").mkdir(exist_ok=True)

    sam_renders_html = ROOT_DIR / "data" / "corpora" / "samhita" / "05_renders" / "html"

    targets = [
        ("Samam_kpully_Malayalam.html", "Malayalam"),
        ("Samam_kpully_Devanagari.html", "Devanagari"),
    ]

    copied_any = False
    print("\n[PIPELINE] Syncing standalone HTML readers to docs/standalone-html...")
    for fname, script_subfolder in targets:
        src_file = sam_renders_html / fname
        if not src_file.exists():
            fallback = ROOT_DIR / "data" / "output" / "html" / script_subfolder / fname
            if not fallback.exists():
                fallback = ROOT_DIR / "data" / "output" / "html" / fname
            if fallback.exists():
                src_file = fallback

        if src_file.exists():
            try:
                dest_root = docs_standalone / fname
                dest_root.write_bytes(src_file.read_bytes())
                dest_sub = docs_standalone / script_subfolder / fname
                dest_sub.write_bytes(src_file.read_bytes())
                print(f"  [SYNC] {fname} -> docs/standalone-html/ & docs/standalone-html/{script_subfolder}/")
                copied_any = True
            except Exception as e:
                print(f"  [WARN] Could not sync reader {fname}: {e}")

    # Refresh catalog index if publisher exists
    publish_script = ROOT_DIR / "scripts" / "publish_standalone_html.py"
    if publish_script.exists():
        try:
            run_cmd([sys.executable, str(publish_script)], description="Refreshing docs/standalone-html catalog index")
        except Exception as e:
            print(f"[WARN] Could not refresh catalog index: {e}")


def print_profiles(cfg):
    """Print formatted list of configured render profiles."""
    active = cfg.get("active_profile", "fast_preview")
    profiles = cfg.get("render_profiles", {})
    print("=" * 75)
    print(" Jaimineeya Samavedam — Configured Render Profiles")
    print("=" * 75)
    for name, p in profiles.items():
        is_active = " [ACTIVE DEFAULT]" if name == active else ""
        print(f"\n* Profile: {name}{is_active}")
        print(f"    Description : {p.get('description', '')}")
        print(f"    Corpora     : {', '.join(p.get('corpora', []))}")
        print(f"    Modes       : {', '.join(p.get('modes', []))}")
        print(f"    Formats     : {', '.join(p.get('formats', []))}")
        print(f"    KPully Mode : {p.get('kpully', False)}")
    print("\n" + "=" * 75)


def main():
    cfg = load_config()
    active_profile_name = cfg.get("active_profile", "fast_preview")
    profiles = cfg.get("render_profiles", {})

    parser = argparse.ArgumentParser(
        description="Run the end-to-end Jaimineeya Samavedam pipeline with named profiles."
    )
    parser.add_argument(
        "--profile", "-p",
        default=None,
        help=f"Named render profile to execute (default: active_profile '{active_profile_name}')",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List all configured render profiles and exit",
    )
    parser.add_argument(
        "--corpora",
        nargs="+",
        choices=["samhita", "aaranam", "collections", "purvarchikam", "uttararchikam", "all"],
        default=None,
        help="Override corpora to process (choices: samhita, aaranam, collections, purvarchikam, uttararchikam, all)",
    )
    parser.add_argument(
        "--script",
        choices=["both", "devanagari", "malayalam"],
        default="both",
        help="Target script to process for Samhita (default: both)",
    )
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=["combined", "separate", "nometa"],
        default=None,
        help="Override output modes (choices: combined, separate, nometa)",
    )
    parser.add_argument(
        "--kpully",
        action="store_true",
        default=None,
        help="Force enable Kodunthirapully stacked swara rendering",
    )
    parser.add_argument(
        "--no-kpully",
        dest="kpully",
        action="store_false",
        help="Force disable Kodunthirapully stacked swara rendering",
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
    parser.add_argument(
        "--skip-migrate",
        action="store_true",
        help="Skip post-run stage synchronization to data/corpora/",
    )
    parser.add_argument(
        "--build-websites",
        action="store_true",
        help="Build all static micro-websites in docs/ using src/tools/generate_all_websites.py",
    )

    args = parser.parse_args()

    if args.list_profiles:
        print_profiles(cfg)
        sys.exit(0)

    # 1. Resolve Profile Settings
    profile_name = args.profile or active_profile_name
    profile = profiles.get(profile_name, {})
    if not profile and profile_name not in profiles:
        print(f"[WARN] Unknown profile '{profile_name}'. Falling back to defaults.")

    # Corpora resolution
    if args.corpora:
        corpora = ["samhita", "aaranam", "collections", "purvarchikam", "uttararchikam"] if "all" in args.corpora else args.corpora
    else:
        corpora = profile.get("corpora", ["samhita"])

    # Modes resolution
    modes = args.modes or profile.get("modes", ["combined"])

    # KPully resolution
    if args.kpully is not None:
        kpully_active = args.kpully
    else:
        kpully_active = profile.get("kpully", True)

    # Formats resolution
    formats = profile.get("formats", ["html", "txt"])
    if args.html_only:
        formats = ["html", "txt"]
    elif args.pdf_only:
        formats = ["pdf"]
    elif args.txt_only:
        formats = ["txt"]

    start_time = time.time()
    scripts_to_run = ["devanagari", "malayalam"] if args.script == "both" else [args.script]

    format_label = ", ".join(f.upper() for f in formats)

    print("=" * 75)
    print(" Jaimineeya Samavedam — Publication & Curation Pipeline")
    print("=" * 75)
    print(f" Profile          : {profile_name}")
    print(f" Corpora Target   : {', '.join(c.capitalize() for c in corpora)}")
    print(f" Render Modes     : {', '.join(modes)}")
    print(f" Target Formats   : {format_label}")
    print(f" KPully Mode      : {'Enabled' if kpully_active else 'Disabled'}")
    if "samhita" in corpora:
        print(f" Samhita Scripts  : {', '.join(s.capitalize() for s in scripts_to_run)}")
    print("=" * 75)

    # Determine render flags based on formats
    extra_flags = []
    if "pdf" not in formats and ("html" in formats and "txt" in formats):
        extra_flags.append("--no-pdf")
    elif "pdf" not in formats and "html" in formats:
        extra_flags.append("--html-only")
    elif formats == ["pdf"]:
        extra_flags.append("--pdf-only")
    elif formats == ["txt"]:
        extra_flags.append("--txt-only")
    if args.legacy_html:
        extra_flags.append("--legacy-html")

    kpully_cli_flags = ["-kpully"] if kpully_active else []

    # ----------------------------------------------------
    # 1. SAMHITA PIPELINE
    # ----------------------------------------------------
    if "samhita" in corpora:
        print("\n>>> CORPUS: SAMHITA (संहिता)")
        deva_input_path = DEFAULT_DEVA_INPUT
        deva_json_path = DEFAULT_DEVA_JSON

        if not deva_input_path.exists():
            print(f"[ERROR] Samhita Devanagari input not found: {deva_input_path}", file=sys.stderr)
            sys.exit(1)

        deva_json_path.parent.mkdir(parents=True, exist_ok=True)

        if "devanagari" in scripts_to_run:
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
                description="Samhita Step 1: Generating JSON AST from source text",
            )

            # Step 1B: Render Devanagari in requested modes
            mode_descriptions = {
                "combined": "Combined (Rik + Samam + Metadata)",
                "separate": "Samam+meta and Rik+meta",
                "nometa": "Samam only (no meta) and Rik only (no meta)",
            }
            for mode in modes:
                cmd = [
                    sys.executable,
                    "-X", "utf8",
                    str(ROOT_DIR / "src" / "render.py"),
                    str(deva_json_path),
                    "--script", "devanagari",
                    "--output-mode", mode,
                    "-o", "Samhita",
                ] + extra_flags + kpully_cli_flags
                desc = mode_descriptions.get(mode, mode)
                run_cmd(cmd, description=f"Samhita Step 2: Rendering Devanagari {desc} ({format_label})")

        # Step 1C & 1D: Malayalam KPully & Devanagari KPully (from Malayalam AST)
        if "malayalam" in scripts_to_run or kpully_active:
            mal_input_path = DEFAULT_MAL_INPUT
            mal_json_path = DEFAULT_MAL_JSON

            if mal_input_path.exists():
                mal_json_path.parent.mkdir(parents=True, exist_ok=True)
                run_cmd(
                    [
                        sys.executable,
                        "-X", "utf8",
                        str(ROOT_DIR / "src" / "generate_json.py"),
                        str(mal_input_path),
                        "--output",
                        str(mal_json_path),
                    ],
                    description="Samhita Step 3: Generating Malayalam JSON AST",
                )

                # Render Malayalam KPully
                mal_kpully_cmd = [
                    sys.executable,
                    "-X", "utf8",
                    str(ROOT_DIR / "src" / "render.py"),
                    str(mal_json_path),
                    "--script", "malayalam",
                    "-kpully",
                    "--output-mode", "separate",
                    "--samam-only",
                    "-o", "Samam_kpully_Malayalam",
                ] + extra_flags
                run_cmd(mal_kpully_cmd, description=f"Samhita Step 4: Rendering Malayalam KPully ({format_label})")

                # Transliterate Malayalam AST to Devanagari AST
                kpully_json_path = DEFAULT_KPULLY_JSON
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

                # Render Devanagari KPully from Malayalam AST
                if kpully_json_path.exists():
                    deva_kpully_from_mal_cmd = [
                        sys.executable,
                        "-X", "utf8",
                        str(ROOT_DIR / "src" / "render.py"),
                        str(kpully_json_path),
                        "--script", "devanagari",
                        "-kpully",
                        "--output-mode", "separate",
                        "--samam-only",
                        "-o", "Samam_kpully_Devanagari",
                    ] + extra_flags
                    run_cmd(deva_kpully_from_mal_cmd, description=f"Samhita Step 5: Rendering Devanagari KPully ({format_label})")

    # ----------------------------------------------------
    # 2. AARANAM PIPELINE
    # ----------------------------------------------------
    if "aaranam" in corpora:
        print("\n>>> CORPUS: AARANAM (आरण्यकम्)")
        aaranam_input = DEFAULT_AARANAM_INPUT
        aaranam_json = DEFAULT_AARANAM_JSON

        if not aaranam_input.exists():
            print(f"[WARN] Aaranam input file not found: {aaranam_input}. Skipping Aaranam.")
        else:
            aaranam_json.parent.mkdir(parents=True, exist_ok=True)
            # Step 2A: Parse source text to JSON AST
            run_cmd(
                [
                    sys.executable,
                    "-X", "utf8",
                    str(ROOT_DIR / "src" / "generate_json.py"),
                    str(aaranam_input),
                    "--type", "aaranam",
                    "--output",
                    str(aaranam_json),
                ],
                description="Aaranam Step 1: Generating JSON AST from source text",
            )
            # Sync to stage-numbered corpus AST
            aar_ast_dir = ROOT_DIR / "data" / "corpora" / "aaranam" / "02_ast"
            aar_ast_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(aaranam_json), str(aar_ast_dir / "Aaranam_latest_out.json"))
            shutil.copy2(str(aaranam_json), str(aar_ast_dir / "Aaranam_ast.json"))

            # Step 2B: Generate Aaranam Rik Table & Vargeekaran Canonical AST
            run_cmd(
                [
                    sys.executable,
                    "-X", "utf8",
                    str(ROOT_DIR / "src" / "generate_rik_table.py"),
                    "--type", "aaranam",
                ],
                description="Aaranam Step 2: Generating Canonical Vargeekaran AST",
            )
            aar_v_json = ROOT_DIR / "data" / "output" / "Aaranam_vargeekaran.json"
            if aar_v_json.exists():
                aar_can_dir = ROOT_DIR / "data" / "corpora" / "aaranam" / "04_canonical"
                aar_can_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(aar_v_json), str(aar_can_dir / "Aaranam_vargeekaran.json"))

            # Step 2C: Render Aaranam in requested modes
            for mode in modes:
                cmd = [
                    sys.executable,
                    "-X", "utf8",
                    str(ROOT_DIR / "src" / "render.py"),
                    str(aaranam_json),
                    "--type", "aaranam",
                    "--output-mode", mode,
                    "-o", "Aaranam",
                ] + extra_flags + kpully_cli_flags
                run_cmd(cmd, description=f"Aaranam Step 3: Rendering Aaranam ({mode}) ({format_label})")

    # ----------------------------------------------------
    # 3. COLLECTIONS PIPELINE
    # ----------------------------------------------------
    if "collections" in corpora:
        print("\n>>> CORPUS: COLLECTIONS (साम सङ्ग्रह)")
        collections_ast_dir = ROOT_DIR / "data" / "corpora" / "collections" / "02_ast"
        collections_canon_dir = ROOT_DIR / "data" / "corpora" / "collections" / "04_canonical"
        collection_books = [
            ("Sooktamala", "Sooktamala.json"),
            ("Prayogamala-Purvabhagam", "Prayogamala-Purvabhagam.json"),
            ("prayogamala-Uttarabhagam", "prayogamala-Uttarabhagam.json"),
        ]
        rendered_any = False
        for book_name, book_file in collection_books:
            book_json = collections_ast_dir / book_file
            if not book_json.exists():
                book_json = collections_canon_dir / book_file
            if not book_json.exists():
                fallback = ROOT_DIR / "data" / "output" / book_file
                if fallback.exists():
                    book_json = fallback
            if book_json.exists():
                rendered_any = True
                for mode in modes:
                    cmd = [
                        sys.executable,
                        "-X", "utf8",
                        str(ROOT_DIR / "src" / "render.py"),
                        str(book_json),
                        "--type", "collection",
                        "--output-mode", mode,
                        "-o", book_name,
                    ] + extra_flags + kpully_cli_flags
                    run_cmd(cmd, description=f"Collections: Rendering {book_name} ({mode}) ({format_label})")

        if not rendered_any:
            collection_json = DEFAULT_COLLECTION_JSON
            if collection_json.exists():
                for mode in modes:
                    cmd = [
                        sys.executable,
                        "-X", "utf8",
                        str(ROOT_DIR / "src" / "render.py"),
                        str(collection_json),
                        "--type", "collection",
                        "--output-mode", mode,
                        "-o", "Collection",
                    ] + extra_flags + kpully_cli_flags
                    run_cmd(cmd, description=f"Collections: Rendering Collection ({mode}) ({format_label})")

    # ----------------------------------------------------
    # 4. PURVARCHIKAM PIPELINE (पूर्वार्चिकम् - ऋक्)
    # ----------------------------------------------------
    if "purvarchikam" in corpora:
        print("\n>>> CORPUS: PURVARCHIKAM (पूर्वार्चिकम् - ऋक्)")
        purva_input = ROOT_DIR / "data" / "input" / "vedic_text.txt"
        purva_json = ROOT_DIR / "data" / "output" / "Purvarchikam_out.json"

        run_cmd(
            [
                sys.executable,
                "-X", "utf8",
                str(ROOT_DIR / "src" / "generate_json.py"),
                str(purva_input),
                "--type", "purvarchikam",
                "--output", str(purva_json),
            ],
            description="Purvarchikam: Generating JSON AST from vedic_text.txt",
        )

        for mode in modes:
            cmd = [
                sys.executable,
                "-X", "utf8",
                str(ROOT_DIR / "src" / "render.py"),
                str(purva_json),
                "--type", "purvarchikam",
                "--output-mode", mode,
                "--rik-only",
                "-o", "Purvarchikam",
            ] + extra_flags + kpully_cli_flags
            run_cmd(cmd, description=f"Purvarchikam: Rendering ({mode}) ({format_label})")

    # ----------------------------------------------------
    # 5. UTTARARCHIKAM PIPELINE (उत्तरार्चिकम् - ऋक्)
    # ----------------------------------------------------
    if "uttararchikam" in corpora:
        print("\n>>> CORPUS: UTTARARCHIKAM (उत्तरार्चिकम् - ऋक्)")
        uttara_input = ROOT_DIR / "data" / "input" / "vedic_text.txt"
        uttara_json = ROOT_DIR / "data" / "output" / "Uttararchikam_out.json"

        run_cmd(
            [
                sys.executable,
                "-X", "utf8",
                str(ROOT_DIR / "src" / "generate_json.py"),
                str(uttara_input),
                "--type", "uttararchikam",
                "--output", str(uttara_json),
            ],
            description="Uttararchikam: Generating JSON AST from vedic_text.txt",
        )

        for mode in modes:
            cmd = [
                sys.executable,
                "-X", "utf8",
                str(ROOT_DIR / "src" / "render.py"),
                str(uttara_json),
                "--type", "uttararchikam",
                "--output-mode", mode,
                "--rik-only",
                "-o", "Uttararchikam",
            ] + extra_flags + kpully_cli_flags
            run_cmd(cmd, description=f"Uttararchikam: Rendering ({mode}) ({format_label})")

    # ----------------------------------------------------
    # 6. POST-RUN CORPUS STAGE MIGRATION & MANIFEST SYNC
    # ----------------------------------------------------
    if not args.skip_migrate:
        run_cmd(
            [
                sys.executable,
                "-X", "utf8",
                str(ROOT_DIR / "src" / "tools" / "migrate_corpora_and_archive.py"),
                "--keep-legacy",
            ],
            description="Syncing outputs to stage-numbered corpus directories (05_renders/{pdf,html,txt})",
        )

    # ----------------------------------------------------
    # 5. SYNC STANDALONE HTML READERS (docs/standalone-html)
    # ----------------------------------------------------
    sync_standalone_readers()

    # ----------------------------------------------------
    # 6. STATIC MICRO-WEBSITES (docs/)
    # ----------------------------------------------------
    if getattr(args, "build_websites", False):
        gen_websites_script = ROOT_DIR / "src" / "tools" / "generate_all_websites.py"
        if gen_websites_script.exists():
            run_cmd([sys.executable, str(gen_websites_script)], description="Building all static micro-websites in docs/")

    elapsed = time.time() - start_time

    # ----------------------------------------------------
    # SUMMARY REPORT
    # ----------------------------------------------------
    print("\n" + "=" * 75)
    print(f" Pipeline Run Completed Successfully in {elapsed:.1f} seconds! [Profile: {profile_name}]")
    print("=" * 75)
    print(" Processed Corpora :", ", ".join(c.capitalize() for c in corpora))
    print(" Rendered Formats  :", format_label)
    print(" Active Outputs    : data/output/{pdf,html,txt}/")
    print(" Staged Corpora    : data/corpora/<corpus>/05_renders/{pdf,html,txt}/")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()
