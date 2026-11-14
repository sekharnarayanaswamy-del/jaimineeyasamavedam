#!/usr/bin/env python3
"""
Split Samhita Devanagari Unicode Text File by Parva (SuperSection).

Extracts the 6 SuperSections (Parvas) of Jaimineeya Samavedam Samhita:
1. आग्नेयपाठः (Agneya Patha) - Parva 1 (Sections 1-12, Subsections 1-125)
2. तद्वपाठः (Tadva Patha)   - Parva 2 (Sections 13-25, Subsections 127-250)
3. बृहतिपाठः (Brihati Patha) - Parva 3 (Sections 26-34, Subsections 252-346)
4. असाविपाठः (Asavi Patha)   - Parva 4 (Sections 35-41, Subsections 348-411)
5. ऐन्द्रपाठः (Aindra Patha)  - Parva 5 (Sections 42-52, Subsections 1413-1517)
6. पवमानपाठः (Pavamana Patha)- Parva 6 (Sections 53-64, Subsections 519-727)

Writes standalone, fully valid Unicode input files for each Parva to:
- data/corpora/samhita/01_input/parvas/
- data/input/parvas/
"""

import sys
import re
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "src"))

PARVA_METADATA = {
    "supersection_1": {
        "num": 1,
        "name_sa": "आग्नेयपाठः",
        "slug": "Agneya_Patha",
        "file_prefix": "Parva_1_Agneya_Patha",
    },
    "supersection_2": {
        "num": 2,
        "name_sa": "तद्वपाठः",
        "slug": "Tadva_Patha",
        "file_prefix": "Parva_2_Tadva_Patha",
    },
    "supersection_3": {
        "num": 3,
        "name_sa": "बृहतिपाठः",
        "slug": "Brihati_Patha",
        "file_prefix": "Parva_3_Brihati_Patha",
    },
    "supersection_4": {
        "num": 4,
        "name_sa": "असाविपाठः",
        "slug": "Asavi_Patha",
        "file_prefix": "Parva_4_Asavi_Patha",
    },
    "supersection_5": {
        "num": 5,
        "name_sa": "ऐन्द्रपाठः",
        "slug": "Aindra_Patha",
        "file_prefix": "Parva_5_Aindra_Patha",
    },
    "supersection_6": {
        "num": 6,
        "name_sa": "पवमानपाठः",
        "slug": "Pavamana_Patha",
        "file_prefix": "Parva_6_Pavamana_Patha",
    },
}

def split_samhita_by_parva(source_path: Path, output_dirs: list[Path], dry_run: bool = False):
    print(f"Reading master Samhita file: {source_path}")
    content = source_path.read_text(encoding='utf-8')
    
    from core.version import get_corpus_edition
    current_edition = get_corpus_edition("samhita")
    
    # Extract version header
    header_match = re.match(r'^(.*?)(?=#\s*Start\s+of\s+SuperSection\s+Title)', content, re.DOTALL)
    orig_header = header_match.group(1).strip() if header_match else f"जैमिनीयसामवेद संहिता\n\nVersion {current_edition}"
    
    # Extract Version line
    version_line = f"Version {current_edition}"
    v_match = re.search(r'Version\s+[^\n]+', orig_header)
    if v_match:
        version_line = v_match.group(0)

    # Supersection regex
    supersection_pattern = re.compile(
        r'(#\s*Start\s+of\s+SuperSection\s+Title\s+--\s+(supersection_\d+)\s*##\s*DO\s+NOT\s+EDIT\s*\n(.*?)\n\s*#\s*End\s+of\s+SuperSection\s+Title\s+--\s+\2\s*##\s*DO\s+NOT\s+EDIT.*?(?=#\s*Start\s+of\s+SuperSection\s+Title\s+--\s+supersection_\d+|$))',
        re.DOTALL
    )

    matches = list(supersection_pattern.finditer(content))
    if not matches:
        print("[ERROR] No SuperSections found in source file!")
        return []

    print(f"Discovered {len(matches)} Parvas / SuperSections.\n")
    results = []

    for m in matches:
        full_block = m.group(1).strip()
        sec_id = m.group(2)
        title_sa = m.group(3).strip()
        
        meta = PARVA_METADATA.get(sec_id, {
            "num": int(sec_id.replace("supersection_", "")),
            "name_sa": title_sa,
            "slug": f"Parva_{sec_id}",
            "file_prefix": f"Parva_{sec_id}"
        })
        
        # Count sections and subsections
        sections = re.findall(r'#\s*Start\s+of\s+Section\s+Title\s+--\s+(section_\d+)', full_block)
        subsections = re.findall(r'#\s*Start\s+of\s+SubSection\s+Title\s+--\s+(subsection_\d+)', full_block)
        
        # Build individual Parva file content
        file_header = f"जैमिनीयसामवेद संहिता - {title_sa}\n\n{version_line}\n\n"
        parva_content = file_header + full_block + "\n"
        
        filename = f"{meta['file_prefix']}_Devanagari_Unicode.txt"
        
        results.append({
            "parva_num": meta["num"],
            "id": sec_id,
            "title_sa": title_sa,
            "sections_count": len(sections),
            "subsections_count": len(subsections),
            "sections_range": f"{sections[0]} - {sections[-1]}" if sections else "None",
            "subsections_range": f"{subsections[0]} - {subsections[-1]}" if subsections else "None",
            "char_count": len(parva_content),
            "filename": filename,
            "content": parva_content
        })

    # Summary table
    print("=" * 80)
    print(f"{'Parva':<8} | {'Title':<16} | {'Sections':<10} | {'Subsections':<12} | {'Filename':<45}")
    print("-" * 80)
    for r in results:
        print(f"Parva {r['parva_num']:<2} | {r['title_sa']:<16} | {r['sections_count']:<10} | {r['subsections_count']:<12} | {r['filename']:<45}")
    print("=" * 80)

    # Write files
    if not dry_run:
        for out_dir in output_dirs:
            out_dir.mkdir(parents=True, exist_ok=True)
            print(f"\nWriting to directory: {out_dir}")
            for r in results:
                target_file = out_dir / r["filename"]
                target_file.write_text(r["content"], encoding='utf-8')
                print(f"  [CREATED] {r['filename']} ({r['sections_count']} sections, {r['subsections_count']} subsections)")

    return results

def main():
    parser = argparse.ArgumentParser(description="Split Samhita text into per-Parva Unicode files.")
    parser.add_argument("--source", type=Path, default=ROOT_DIR / "data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    output_dirs = [
        ROOT_DIR / "data/corpora/samhita/01_input/parvas",
        ROOT_DIR / "data/input/parvas",
    ]

    split_samhita_by_parva(args.source, output_dirs, dry_run=args.dry_run)

if __name__ == '__main__':
    main()
