import json
import re
import argparse
from pathlib import Path
from datetime import datetime


def to_devanagari_num(n):
    """Convert an integer to Devanagari numeral string."""
    deva_digits = '०१२३४५६७८९'
    return ''.join(deva_digits[int(d)] for d in str(n))


def get_samam_numbers(sub_data):
    """
    Extract all Samam numbers from the corrected-mantra text of a subsection.
    Samam boundaries are marked by ॥N॥ where N is in Devanagari digits.
    Returns a list of integer Samam numbers found.
    """
    mantras = sub_data.get('corrected-mantra_sets', [])
    mantra_text = ' '.join(
        m.get('corrected-mantra', '') for m in mantras if isinstance(m, dict)
    )
    # Match ॥ followed by optional spaces, Devanagari digits, optional spaces, followed by ॥
    matches = re.findall(r'॥\s*([०-९]+)\s*॥', mantra_text)
    result = []
    for m in matches:
        # Convert Devanagari digits to int
        arabic = m.translate(str.maketrans('०१२३४५६७८९', '0123456789'))
        result.append(int(arabic))
    return result


def parse_p_k_s(content):
    """
    Extract P.K.S identifiers from text using regex.
    P = Parva (Supersection), K = Kandah (Section, ordinal), S = Samam number.
    """
    pattern = re.compile(r'(\d+)\.(\d+)\.(\d+)')
    matches = pattern.findall(content)
    return [(int(p), int(k), int(s)) for p, k, s in matches]


def main():
    parser = argparse.ArgumentParser(
        description='Curate a subset of JSV JSON (Samhita/Aaranam) based on P.K.S filters.\n'
                    'P = Parva, K = Kandah (ordinal), S = Samam number (from mantra text ॥N॥).'
    )
    parser.add_argument('--sources', nargs='+', required=True, help='Source JSON files (e.g., data/output/Vargeekaran.json data/output/Aaranam.json)')
    parser.add_argument('--filter', required=True, help='Filter text file with P.K.S identifiers')
    parser.add_argument('--output', required=True, help='Output JSON file')
    parser.add_argument('--title', default='जैमिनीय साम सूक्तमाला', help='Title for the curated collection')

    args = parser.parse_args()

    # 1. Load and Merge Source JSONs
    source_data = {"supersection": {}, "closing_mantras": []}
    for src in args.sources:
        source_path = Path(src)
        if not source_path.exists():
            print(f"Error: Source file {src} not found.")
            return

        print(f"Loading source: {source_path}", flush=True)
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Merge supersections
                for ss_id, ss_content in data.get("supersection", {}).items():
                    if ss_id not in source_data["supersection"]:
                        source_data["supersection"][ss_id] = ss_content
                    else:
                        for sec_id, sec_content in ss_content.get("sections", {}).items():
                            if "sections" not in source_data["supersection"][ss_id]:
                                source_data["supersection"][ss_id]["sections"] = {}
                            source_data["supersection"][ss_id]["sections"][sec_id] = sec_content
                            
                # Merge closing mantras
                cm = data.get("closing_mantras", [])
                if cm:
                    source_data["closing_mantras"].extend(cm)
        except Exception as e:
            print(f"Error loading JSON from {src}: {e}")
            return
    print("All sources loaded and merged.", flush=True)

    # 2. Parse Filter File
    filter_path = Path(args.filter)
    if not filter_path.exists():
        print(f"Error: Filter file {args.filter} not found.")
        return

    print(f"Reading filter: {filter_path}", flush=True)
    with open(filter_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Try to extract title from filter file (between # Title and #End Title markers)
    title = args.title
    title_match = re.search(r'#\s*Title\s*\n(.+?)\n\s*#\s*End\s*Title', content, re.IGNORECASE)
    if title_match:
        extracted_title = title_match.group(1).strip()
        if extracted_title:
            title = extracted_title
            print(f"Title from filter file: {title}", flush=True)

    id_list = parse_p_k_s(content)
    if not id_list:
        print(f"Warning: No valid P.K.S identifiers found in {args.filter}")
        return
    print(f"Found {len(id_list)} identifiers in filter file.", flush=True)


    # 3. Build Curated Structure
    curated_data = {
        "meta": {
            "version": "1.1",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_file": ", ".join(args.sources),
            "filter_file": str(args.filter),
            "title": title
        },
        "supersection": {
            "supersection_1": {
                "supersection_title": title,
                "sections": {
                    "section_1": {
                        "section_title": "सङ्ग्रहः",
                        "subsections": {}
                    }
                }
            }
        },
        "closing_mantras": source_data.get("closing_mantras", [])
    }

    target_subsections = curated_data["supersection"]["supersection_1"]["sections"]["section_1"]["subsections"]
    source_super = source_data.get("supersection", {})

    # Pre-map ordinal sections for each Parva
    parva_section_map = {}
    for ss_key, ss_data in source_super.items():
        if not isinstance(ss_data, dict):
            continue
        sec_keys = sorted(
            [k for k in ss_data.get('sections', {}).keys() if k != 'count'],
            key=lambda x: int(x.split('_')[1]) if '_' in x else 0
        )
        parva_section_map[ss_key] = sec_keys

    # Pre-build a Samam-number index: (ss_key, sec_key) -> { samam_num -> sub_key }
    print("Building Samam index...", flush=True)
    samam_index = {}
    for ss_key, ss_data in source_super.items():
        if not isinstance(ss_data, dict):
            continue
        for sec_key, sec_data in ss_data.get('sections', {}).items():
            if not isinstance(sec_data, dict):
                continue
            subsections_dict = sec_data.get("subsections", {})
            sub_keys = sorted(
                subsections_dict.keys(),
                key=lambda x: int(x.split('_')[1]) if '_' in x else 0
            )
            idx = {}
            for sub_key in sub_keys:
                sub_data = subsections_dict[sub_key]
                samam_nums = get_samam_numbers(sub_data)
                for sn in samam_nums:
                    idx[sn] = sub_key
            samam_index[(ss_key, sec_key)] = idx
    print("Samam index built.", flush=True)

    found_count = 0
    missing_ids = []
    # Track already-added subsections to avoid duplicates (e.g., 1.8.7 and 1.8.8 both in subsection_87)
    added_subsections = set()

    for p, k_ord, s_val in id_list:
        print(f"Processing ID: {p}.{k_ord}.{s_val}", flush=True)
        ss_key = f"supersection_{p}"

        # Access the Parva
        ss_data = source_super.get(ss_key)
        if not ss_data:
            print(f"  Missing Parva: {ss_key}", flush=True)
            missing_ids.append(f"{p}.{k_ord}.{s_val}")
            continue

        # Get the ordinal Kandah
        parva_sections = parva_section_map.get(ss_key, [])
        if k_ord < 1 or k_ord > len(parva_sections):
            print(f"  Kandah {k_ord} out of range in {ss_key} (Max: {len(parva_sections)})", flush=True)
            missing_ids.append(f"{p}.{k_ord}.{s_val}")
            continue

        sec_key = parva_sections[k_ord - 1]
        sec_data = ss_data.get("sections", {}).get(sec_key)
        if not sec_data:
            print(f"  Internal Error: {sec_key} missing", flush=True)
            missing_ids.append(f"{p}.{k_ord}.{s_val}")
            continue

        # Look up Samam number in the index
        idx = samam_index.get((ss_key, sec_key), {})
        sub_key = idx.get(s_val)

        if not sub_key:
            print(f"  Samam {s_val} NOT found in {ss_key}.{sec_key}", flush=True)
            missing_ids.append(f"{p}.{k_ord}.{s_val}")
            continue

        # Avoid duplicate subsection entries
        full_key = (ss_key, sec_key, sub_key)
        if full_key in added_subsections:
            print(f"  Samam {s_val} -> {sub_key} (already added, skipping duplicate)", flush=True)
            continue

        added_subsections.add(full_key)
        sub_data = sec_data["subsections"][sub_key]
        samam_nums_in_sub = get_samam_numbers(sub_data)
        print(f"  Samam {s_val} -> {sub_key} (contains Samams {samam_nums_in_sub})", flush=True)

        found_count += 1
        target_sub_key = f"subsection_{found_count}"
        target_subsections[target_sub_key] = sub_data

    # 4. Save Output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(curated_data, f, ensure_ascii=False, indent=4)
        print(f"\nSuccessfully created curated file with {found_count} Arsheyams at {output_path}", flush=True)
    except Exception as e:
        print(f"Error saving output: {e}", flush=True)

    if missing_ids:
        print(f"Notice: {len(missing_ids)} identifiers not found: {', '.join(missing_ids[:15])}{'...' if len(missing_ids) > 15 else ''}")


if __name__ == "__main__":
    main()

