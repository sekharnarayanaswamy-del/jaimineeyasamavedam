#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate All 8 Jaimineeya Static Micro-Websites
===============================================
Automates end-to-end multi-page static site generation across all 8 canonical
editions:
  1. Samhita (Standard combined) -> docs/samhita/
  2. Aaranam (Standard combined) -> docs/aaranam/
  3. Collections (Sooktamala, Prayogamala Purva & Uttara) -> docs/collection/
  4. kpully:
     - Devanagari (swaras above syllables) -> docs/kpully-devanagari/
     - Malayalam (JaimineeyaSwara typography) -> docs/malayalam/
  5. Samhita with samam+metadata only -> docs/samhita-samam/
  6. Samhita with Rik+metadata only -> docs/samhita-rik/
  7. Samhita with Samam only, no metadata -> docs/samhita-samam-nometa/
  8. Samhita with Rik only, no metadata -> docs/samhita-rik-nometa/

Usage:
  # Build all 8 micro-websites:
  python src/tools/generate_all_websites.py

  # Build specific targets by number or key:
  python src/tools/generate_all_websites.py --targets 1 2 4
  python src/tools/generate_all_websites.py --targets samhita kpully_devanagari
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"

TARGET_DEFINITIONS = [
    {
        "id": "1",
        "key": "samhita",
        "name": "1. Samhita (Standard Combined)",
        "cmd": [
            sys.executable, "-X", "utf8", str(SRC_DIR / "generate_website.py"),
            "--samhita",
            "--output-mode", "combined",
            "-o", "docs/samhita"
        ],
        "output": ROOT_DIR / "docs" / "samhita"
    },
    {
        "id": "2",
        "key": "aaranam",
        "name": "2. Aaranam (Standard Combined)",
        "cmd": [
            sys.executable, "-X", "utf8", str(SRC_DIR / "generate_website.py"),
            "--aaranam",
            "--output-mode", "combined",
            "-o", "docs/aaranam"
        ],
        "output": ROOT_DIR / "docs" / "aaranam"
    },
    {
        "id": "3",
        "key": "collections",
        "name": "3. Collections (Sooktamala & Prayogamala)",
        "sub_tasks": [
            {
                "title": "Sooktamala",
                "cmd": [
                    sys.executable, "-X", "utf8", str(SRC_DIR / "generate_website.py"),
                    "-c",
                    "-s", "data/corpora/collections/02_ast/Sooktamala.json",
                    "-o", "docs/collection/sooktamala",
                    "--title", "साम सूक्तमाला"
                ],
                "output": ROOT_DIR / "docs" / "collection" / "sooktamala"
            },
            {
                "title": "Prayogamala-Purvabhagam",
                "cmd": [
                    sys.executable, "-X", "utf8", str(SRC_DIR / "generate_website.py"),
                    "-c",
                    "-s", "data/corpora/collections/02_ast/Prayogamala-Purvabhagam.json",
                    "-o", "docs/collection/prayogamala-purva",
                    "--title", "साम प्रयोगमाला - पूर्वभागः"
                ],
                "output": ROOT_DIR / "docs" / "collection" / "prayogamala-purva"
            },
            {
                "title": "prayogamala-Uttarabhagam",
                "cmd": [
                    sys.executable, "-X", "utf8", str(SRC_DIR / "generate_website.py"),
                    "-c",
                    "-s", "data/corpora/collections/02_ast/prayogamala-Uttarabhagam.json",
                    "-o", "docs/collection/prayogamala-uttara",
                    "--title", "साम प्रयोगमाला - उत्तरभागः"
                ],
                "output": ROOT_DIR / "docs" / "collection" / "prayogamala-uttara"
            }
        ]
    },
    {
        "id": "4",
        "key": "kpully",
        "name": "4. kpully (Devanagari + Malayalam Chanting)",
        "sub_tasks": [
            {
                "title": "kpully Devanagari",
                "cmd": [
                    sys.executable, "-X", "utf8", str(SRC_DIR / "generate_website.py"),
                    "--samhita",
                    "-kpully",
                    "--output-mode", "samam_nometa",
                    "-o", "docs/kpully-devanagari",
                    "--title", "जैमिनीय साम संहिता (कोडुनतिरपुळ्ळि पाठः)"
                ],
                "output": ROOT_DIR / "docs" / "kpully-devanagari"
            },
            {
                "title": "kpully Malayalam",
                "cmd": [
                    sys.executable, "-X", "utf8", str(SRC_DIR / "generate_website.py"),
                    "--malayalam",
                    "-o", "docs/malayalam"
                ],
                "output": ROOT_DIR / "docs" / "malayalam"
            }
        ]
    },
    {
        "id": "5",
        "key": "samhita_samam",
        "name": "5. Samhita (Samam + Metadata Only)",
        "cmd": [
            sys.executable, "-X", "utf8", str(SRC_DIR / "generate_website.py"),
            "--samhita",
            "--output-mode", "samam",
            "-o", "docs/samhita-samam",
            "--title", "जैमिनीय साम संहिता (साम सविशेषम्)"
        ],
        "output": ROOT_DIR / "docs" / "samhita-samam"
    },
    {
        "id": "6",
        "key": "samhita_rik",
        "name": "6. Samhita (Rik + Metadata Only)",
        "cmd": [
            sys.executable, "-X", "utf8", str(SRC_DIR / "generate_website.py"),
            "--samhita",
            "--output-mode", "rik",
            "-o", "docs/samhita-rik",
            "--title", "जैमिनीय साम संहिता (ऋक् सविशेषम्)"
        ],
        "output": ROOT_DIR / "docs" / "samhita-rik"
    },
    {
        "id": "7",
        "key": "samhita_samam_nometa",
        "name": "7. Samhita (Samam Only, No Metadata)",
        "cmd": [
            sys.executable, "-X", "utf8", str(SRC_DIR / "generate_website.py"),
            "--samhita",
            "--output-mode", "samam_nometa",
            "-o", "docs/samhita-samam-nometa",
            "--title", "जैमिनीय साम संहिता (साम गान पाठः)"
        ],
        "output": ROOT_DIR / "docs" / "samhita-samam-nometa"
    },
    {
        "id": "8",
        "key": "samhita_rik_nometa",
        "name": "8. Samhita (Rik Only, No Metadata)",
        "cmd": [
            sys.executable, "-X", "utf8", str(SRC_DIR / "generate_website.py"),
            "--samhita",
            "--output-mode", "rik_nometa",
            "-o", "docs/samhita-rik-nometa",
            "--title", "जैमिनीय साम संहिता (ऋक् पाठः)"
        ],
        "output": ROOT_DIR / "docs" / "samhita-rik-nometa"
    }
]


def run_command(cmd, desc=""):
    print(f"  [RUN] {desc}")
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(SRC_DIR)
    res = subprocess.run(cmd, cwd=str(ROOT_DIR), env=env)
    if res.returncode != 0:
        print(f"  [ERROR] Command failed with returncode {res.returncode}")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate all 8 Jaimineeya static micro-websites.")
    parser.add_argument(
        "--targets", "-t",
        nargs="+",
        default=None,
        help="Specify which targets to build (choices: 1..8 or key names)"
    )
    args = parser.parse_args()

    selected_targets = []
    if args.targets:
        allowed = {t.lower() for t in args.targets}
        for item in TARGET_DEFINITIONS:
            if item["id"] in allowed or item["key"] in allowed:
                selected_targets.append(item)
    else:
        selected_targets = TARGET_DEFINITIONS

    print("=" * 75)
    print(" Jaimineeya Samavedam — Multi-Site Static Website Generator Suite")
    print(f" Targets to build: {len(selected_targets)} / {len(TARGET_DEFINITIONS)}")
    print("=" * 75)

    start_total = time.time()
    success_count = 0
    total_tasks = 0

    for t in selected_targets:
        print(f"\n>>> Target: {t['name']}")
        if "sub_tasks" in t:
            for sub in t["sub_tasks"]:
                total_tasks += 1
                t0 = time.time()
                ok = run_command(sub["cmd"], desc=f"Building {sub['title']}")
                if ok:
                    success_count += 1
                    print(f"      OK ({time.time() - t0:.1f}s) -> {sub['output'].relative_to(ROOT_DIR)}")
                else:
                    print(f"      FAILED -> {sub['title']}")
        else:
            total_tasks += 1
            t0 = time.time()
            ok = run_command(t["cmd"], desc=f"Building {t['name']}")
            if ok:
                success_count += 1
                print(f"      OK ({time.time() - t0:.1f}s) -> {t['output'].relative_to(ROOT_DIR)}")
            else:
                print(f"      FAILED -> {t['name']}")

    # Apply Lunr search highlighting patches
    patcher_script = SRC_DIR / "patch_highlight_js.py"
    if patcher_script.exists():
        print("\n>>> Applying Lunr search highlighting patches across all generated sites...")
        run_command([sys.executable, str(patcher_script)], desc="Running patch_highlight_js.py")

    total_time = time.time() - start_total
    print("\n" + "=" * 75)
    print(f" Completed {success_count}/{total_tasks} micro-website generation tasks in {total_time:.1f}s")
    print("=" * 75)


if __name__ == "__main__":
    main()
