import sys
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
    P = Parva (Supersection), K = Kandah (literal global section ID), S = Samam number.
    Handles both single IDs (X.Y.Z) and ranges (X.Y.A-X.Y.B).
    """
    results = []
    
    # Extract ranges first
    range_pattern = re.compile(r'(\d+)\.(\d+)\.(\d+)\s*-\s*(\d+)\.(\d+)\.(\d+)')
    for match in range_pattern.finditer(content):
        p1, k1, s1, p2, k2, s2 = map(int, match.groups())
        if p1 == p2 and k1 == k2 and s1 <= s2:
            results.extend([(p1, k1, s) for s in range(s1, s2 + 1)])
        else:
            print(f"Warning: Invalid range {p1}.{k1}.{s1}-{p2}.{k2}.{s2}")
            
    # Remove ranges so we don't process them again as single IDs
    content_no_ranges = range_pattern.sub('', content)
    
    pattern = re.compile(r'(\d+)\.(\d+)\.(\d+)')
    matches = pattern.finditer(content_no_ranges)
    results.extend([(int(m.group(1)), int(m.group(2)), int(m.group(3))) for m in matches])
    
    return results


def parse_filter_file(content):
    """
    Parse filter file, extracting Devanagari-numeral section headers and P.K.S IDs.
    Section headers are lines matching: १) Title or २) Title etc.
    Returns: list of {'title': str, 'ids': [(P, K, S), ...]}
    """
    sections = []
    current_section = {"title": "सङ्ग्रहः", "ids": []}
    section_pattern = re.compile(r'^([०-९]+)\)\s*(.*)$')
    pks_pattern = re.compile(r'(\d+)\.(\d+)\.(\d+)')
    range_pattern = re.compile(r'(\d+)\.(\d+)\.(\d+)\s*-\s*(\d+)\.(\d+)\.(\d+)')
    has_seen_header = False

    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
        sec_match = section_pattern.match(line)
        if sec_match:
            if has_seen_header or current_section["ids"]:
                sections.append(current_section)
            current_section = {"title": line, "ids": []}
            has_seen_header = True
            continue
            
        # Process ranges
        for match in range_pattern.finditer(line):
            p1, k1, s1, p2, k2, s2 = map(int, match.groups())
            if p1 == p2 and k1 == k2 and s1 <= s2:
                current_section["ids"].extend([(p1, k1, s) for s in range(s1, s2 + 1)])
            else:
                print(f"Warning: Invalid or cross-section range pattern {match.group(0)}")
                
        # Remove ranges from the line to avoid parsing them as single identifiers
        line_no_ranges = range_pattern.sub('', line)
        
        # Process single IDs
        ids = pks_pattern.findall(line_no_ranges)
        if ids:
            current_section["ids"].extend([(int(p), int(k), int(s)) for p, k, s in ids])

    if current_section["ids"] or has_seen_header:
        sections.append(current_section)

    # If no section headers found, return the flat list as one section
    if not sections:
        all_ids = parse_p_k_s(content)
        return [{"title": "सङ्ग्रहः", "ids": all_ids}]
    return sections


def extract_specific_samam(mantra_text, target_s_val):
    """
    Extract only the part of the mantra text that corresponds to a specific Samam number.
    Assumes Samams end with ॥N॥.
    """
    if not mantra_text:
        return ""
    # Match ॥ followed by optional spaces, Devanagari digits, optional spaces, followed by ॥
    pattern = r'॥\s*([०-९]+)\s*॥'
    matches = list(re.finditer(pattern, mantra_text))
    
    prev_end = 0
    for m in matches:
        # Convert Devanagari digits to int
        deva_num = m.group(1)
        arabic = deva_num.translate(str.maketrans('०१२३४५६७८९', '0123456789'))
        try:
            current_val = int(arabic)
        except ValueError:
            continue
            
        if current_val == target_s_val:
            # We found our Samam. It starts after the previous Samam's marker (or at 0)
            # and ends at the end of its own marker.
            return mantra_text[prev_end:m.end()].strip()
        
        prev_end = m.end()
    
    return None


def main():
    # 0. Load Configuration
    from utils import load_pipeline_config
    pipeline_cfg = load_pipeline_config()
    curate_cfg = pipeline_cfg.get('curate_jsv', {})

    parser = argparse.ArgumentParser(
        description='Curate a subset of JSV JSON (Samhita/Aaranam) based on P.K.S filters.\n'
                    'P = Parva, K = Kandah (ordinal), S = Samam number (from mantra text ॥N॥).'
    )
    parser.add_argument('--sources', nargs='+', default=None, help='Source JSON files')
    parser.add_argument('--filter', default=None, help='Filter text file with P.K.S identifiers')
    parser.add_argument('--output', default=None, help='Output JSON file')
    parser.add_argument('--title', default=None, help='Title for the curated collection')

    args = parser.parse_args()

    # Priority: CLI > Config > Defaults
    sources = args.sources or curate_cfg.get('sources')
    if not sources:
        print("Error: No source files provided. Use --sources or configure in pipeline_config.yaml")
        sys.exit(1)

    filter_file = args.filter or curate_cfg.get('filter')
    if not filter_file:
        print("Error: No filter file provided. Use --filter or configure in pipeline_config.yaml")
        sys.exit(1)

    output_file = args.output or curate_cfg.get('output')
    if not output_file:
        print("Error: No output file provided. Use --output or configure in pipeline_config.yaml")
        sys.exit(1)

    title = args.title or curate_cfg.get('title', 'जैमिनीय साम सूक्तमाला')

    # 1. Load and Merge Source JSONs
    source_data = {"supersection": {}, "closing_mantras": []}
    for src in sources:
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
    filter_path = Path(filter_file)
    if not filter_path.exists():
        print(f"Error: Filter file {filter_file} not found.")
        return

    print(f"Reading filter: {filter_path}", flush=True)
    with open(filter_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract title from filter file if present
    title_match = re.search(r'#\s*Title\s*\n(.+?)\n\s*#\s*End\s*Title', content, re.IGNORECASE)
    if title_match:
        extracted_title = title_match.group(1).strip()
        if extracted_title:
            title = extracted_title

    sections_list = parse_filter_file(content)
    total_ids = sum(len(s['ids']) for s in sections_list)
    if not total_ids:
        print(f"Warning: No valid P.K.S identifiers found in {filter_file}")
        return
    print(f"Found {total_ids} identifiers in {len(sections_list)} section(s).", flush=True)


    # 3. Build Curated Structure
    curated_data = {
        "meta": {
            "version": "1.1",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_file": ", ".join(sources),
            "filter_file": str(filter_file),
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

    output_sections_root = curated_data["supersection"]["supersection_1"]["sections"]
    # Build all output sections from the filter's section headers
    for sec_idx, filter_sec in enumerate(sections_list, 1):
        output_sections_root[f"section_{sec_idx}"] = {
            "section_title": filter_sec["title"],
            "subsections": {}
        }

    source_super = source_data.get("supersection", {})

    # Pre-map ordinal sections for each Parva
    parva_section_map = {}
    for ss_key, ss_data in source_super.items():
        if not isinstance(ss_data, dict):
            continue
        sec_keys = sorted(
            [k for k in ss_data.get('sections', {}).keys() if k.lower() != 'count'],
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
    added_subsections = set()

    for sec_idx, filter_sec in enumerate(sections_list, 1):
        target_sec = output_sections_root[f"section_{sec_idx}"]
        target_subsections = target_sec["subsections"]
        last_source_id = None
        current_target_sub = None

        for p, k_ord, s_val in filter_sec["ids"]:
            ss_key = f"supersection_{p}"

            # Access the Parva
            ss_data = source_super.get(ss_key)
            if not ss_data:
                print(f"  Missing Parva: {ss_key}", flush=True)
                missing_ids.append(f"{p}.{k_ord}.{s_val}")
                continue

            # Get section by ordinal within the supersection
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

            # Avoid duplicate Samam entries
            full_key = (ss_key, sec_key, sub_key, s_val)
            if full_key in added_subsections:
                print(f"  Samam {s_val} (already added, skipping duplicate)", flush=True)
                continue

            added_subsections.add(full_key)
            current_source_id = (ss_key, sec_key, sub_key)
        
            if current_source_id == last_source_id and current_target_sub is not None:
                print(f"  Grouping Samam {s_val} into existing Arsheyam {sub_key}", flush=True)
                source_sub_data = sec_data["subsections"][sub_key]
                if "corrected-mantra_sets" in source_sub_data:
                    for mset in source_sub_data["corrected-mantra_sets"]:
                        if not isinstance(mset, dict): continue
                        raw_text = mset.get("corrected-mantra", "")
                        specific_text = extract_specific_samam(raw_text, s_val)
                        if specific_text:
                            import copy
                            mset_copy = copy.deepcopy(mset)
                            mset_copy["corrected-mantra"] = specific_text
                            current_target_sub["corrected-mantra_sets"].append(mset_copy)
                continue

            # New Arsheyam Entry
            sub_data = sec_data["subsections"][sub_key]
            import copy
            found_count += 1
            target_sub_key = f"subsection_{found_count}"
            sub_copy = copy.deepcopy(sub_data)

            # Extract target Samam
            new_mantra_sets = []
            if "corrected-mantra_sets" in sub_copy:
                for mset in sub_copy["corrected-mantra_sets"]:
                    if not isinstance(mset, dict): continue
                    raw_text = mset.get("corrected-mantra", "")
                    specific_text = extract_specific_samam(raw_text, s_val)
                    if specific_text:
                        mset["corrected-mantra"] = specific_text
                        new_mantra_sets.append(mset)

            sub_copy["corrected-mantra_sets"] = new_mantra_sets

            # Drop Rik and metadata
            for kk in ['rik_text', 'rik_metadata', 'saman_metadata',
                       'rik_classifications', 'rik_id', 'rik_ids', 'mantra_sets']:
                if kk in sub_copy:
                    del sub_copy[kk]

            if "header" not in sub_copy or not isinstance(sub_copy["header"], dict):
                sub_copy["header"] = {"header": ""}
            sub_copy["header"]["header_number"] = found_count
            target_subsections[target_sub_key] = sub_copy

            last_source_id = current_source_id
            current_target_sub = sub_copy

    # 4. Save Output
    output_path = Path(output_file)
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

