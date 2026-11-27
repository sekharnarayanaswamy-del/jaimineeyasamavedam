#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Splits data/corpora/aaranam/01_input/Aaranam_latest.txt into individual parva files.
Generates:
  - Canonical continuous files: Parva_7_... to Parva_12_...
  - Aranyakam-relative aliases: Parva_1_... to Parva_6_...
Places them in data/corpora/aaranam/01_input/parvas/ and mirrors to data/corpora/aaranam/01_input/.
"""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = REPO_ROOT / "data" / "corpora" / "aaranam" / "01_input" / "Aaranam_latest.txt"
PARVAS_DIR = REPO_ROOT / "data" / "corpora" / "aaranam" / "01_input" / "parvas"
AARANAM_INPUT_DIR = REPO_ROOT / "data" / "corpora" / "aaranam" / "01_input"

PARVA_DEFINITIONS = [
    {
        "global_id": 7,
        "aranyakam_id": 1,
        "ss_tag": "supersection_7",
        "slug": "Vrata_Parva",
        "title": "व्रत पर्व"
    },
    {
        "global_id": 8,
        "aranyakam_id": 2,
        "ss_tag": "supersection_8",
        "slug": "Arkani_Patha",
        "title": "अर्काणि पाठः"
    },
    {
        "global_id": 9,
        "aranyakam_id": 3,
        "ss_tag": "supersection_9",
        "slug": "Dvandva_Parva",
        "title": "द्वन्द्व – पर्व"
    },
    {
        "global_id": 10,
        "aranyakam_id": 4,
        "ss_tag": "supersection_10",
        "slug": "Shukriya_Parva",
        "title": "शुक्रिय पर्व"
    },
    {
        "global_id": 11,
        "aranyakam_id": 5,
        "ss_tag": "supersection_11",
        "slug": "Shakvarya_Parva",
        "title": "शाक्वर्य पर्व"
    },
    {
        "global_id": 12,
        "aranyakam_id": 6,
        "ss_tag": "supersection_12",
        "slug": "Aupanishada_Parva",
        "title": "औपनिषद पर्व"
    }
]

def make_header(title: str) -> str:
    return (
        "# [JSV METADATA]\n"
        "# Version: 3.28\n"
        "# Generated At: 2026-04-19 22:32:11\n"
        "# [END METADATA]\n"
        "\n"
        f"जैमिनीय  साम  आरण्यक  गानम् - {title}\n"
        "\n"
        "Version 3.1 23rd February 2026\n"
        "\n"
    )

def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        full_text = f.read()

    lines = full_text.splitlines(keepends=True)
    print(f"Loaded {len(lines)} lines from {INPUT_FILE}")

    # Find start indices of each supersection
    starts = {}
    for p in PARVA_DEFINITIONS:
        tag = f"# Start of SuperSection Title -- {p['ss_tag']} ##"
        found = False
        for idx, line in enumerate(lines):
            if tag in line:
                starts[p['global_id']] = idx
                found = True
                break
        if not found:
            raise ValueError(f"Could not find tag {tag} in {INPUT_FILE}")

    PARVAS_DIR.mkdir(parents=True, exist_ok=True)

    generated_files = []

    for i, p in enumerate(PARVA_DEFINITIONS):
        gid = p['global_id']
        aid = p['aranyakam_id']
        start_idx = starts[gid]
        end_idx = starts[PARVA_DEFINITIONS[i+1]['global_id']] if i+1 < len(PARVA_DEFINITIONS) else len(lines)

        slice_text = "".join(lines[start_idx:end_idx])
        header = make_header(p['title'])
        full_parva_content = header + slice_text

        # 1. Canonical continuous: Parva_X_...
        canonical_filename = f"Parva_{gid}_{p['slug']}_Devanagari_Unicode.txt"
        canonical_path = PARVAS_DIR / canonical_filename
        with open(canonical_path, "w", encoding="utf-8") as f_out:
            f_out.write(full_parva_content)
        generated_files.append(canonical_path)

        # 2. Mirror in 01_input root
        mirror_path = AARANAM_INPUT_DIR / canonical_filename
        with open(mirror_path, "w", encoding="utf-8") as f_out:
            f_out.write(full_parva_content)
        generated_files.append(mirror_path)

        # 3. Aranyakam-relative alias: Parva_1_... to Parva_6_... in parvas/
        alias_filename = f"Parva_{aid}_{p['slug']}_Devanagari_Unicode.txt"
        alias_path = PARVAS_DIR / alias_filename
        with open(alias_path, "w", encoding="utf-8") as f_out:
            f_out.write(full_parva_content)
        generated_files.append(alias_path)

        print(f"Generated Parva {gid} (Aranyakam {aid}): {p['title']} ({p['slug']}) -> {canonical_filename} ({len(lines[start_idx:end_idx])} content lines)")

    print(f"\nSuccessfully generated {len(generated_files)} files.")

if __name__ == "__main__":
    main()
