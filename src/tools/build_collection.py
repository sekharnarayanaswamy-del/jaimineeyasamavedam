import json
import argparse
import sys
import re
from pathlib import Path
from datetime import datetime

def to_devanagari_numeral(num):
    """Convert Arabic numerals to Devanagari numerals."""
    if num is None:
        return ""
    mapping = {'0': '०', '1': '१', '2': '२', '3': '३', '4': '४',
               '5': '५', '6': '६', '7': '७', '8': '८', '9': '९'}
    return ''.join(mapping.get(c, c) for c in str(num))

def parse_id(id_str):
    """Parse ID string like 1.1.1 into (supersection_idx, section_idx, subsection_idx)"""
    parts = id_str.split('.')
    if len(parts) < 3:
        return None
    try:
        return [int(p) for p in parts[:3]]
    except ValueError:
        return None

def main():
    parser = argparse.ArgumentParser(description='Create a Vedic Collection JSON from a list of Arsheyam IDs')
    parser.add_argument('--ids', nargs='+', help='List of IDs (e.g., 1.1.1 1.1.2)')
    parser.add_argument('--file', help='Text file containing IDs (one per line)')
    parser.add_argument('--source', default='data/output/Vargeekaran.json', help='Source JSON file (default: Vargeekaran.json)')
    parser.add_argument('--output', default='data/output/Collection_latest_out.json', help='Output JSON file')
    parser.add_argument('--title', default='जैमिनीय साम सूक्तमाला', help='Collection Title')
    
    args = parser.parse_args()
    
    id_list = []
    id_pattern = re.compile(r'(\d+)\.(\d+)\.(\d+)')

    def extract_ids_from_text(text):
        found = []
        # Find all matches for P.K.S
        for match in id_pattern.finditer(text):
            found.append(f"{match.group(1)}.{match.group(2)}.{match.group(3)}")
        return found

    if args.ids:
        for item in args.ids:
            id_list.extend(extract_ids_from_text(item))
    
    if args.file:
        file_path = Path(args.file)
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                id_list.extend(extract_ids_from_text(content))
    
    if not id_list:
        print("Error: No IDs provided. Use --ids or --file.")
        sys.exit(1)
    
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"Error: Source file {args.source} not found.")
        sys.exit(1)
        
    print(f"Loading source: {source_path}")
    with open(source_path, 'r', encoding='utf-8') as f:
        source_data = json.loads(f.read())
        
    # Resulting structure
    collection = {
        "meta": {
            "version": "1.0",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "title": args.title,
            "description": f"Custom collection of {len(id_list)} Arsheyams"
        },
        "supersection": {
            "supersection_1": {
                "supersection_title": args.title,
                "sections": {}
            }
        }
    }
    
    source_super = source_data.get('supersection', {})
    
    # We'll put everything under a single section for simplicity in the collection
    # OR we can try to preserve the original section names.
    # User request: "makes a collection out of that". Usually collections are grouped by theme.
    # Let's create one section called "सङ्ग्रहः" (Collection) if not specified.
    
    current_section = {
        "section_title": "सङ्ग्रहः",
        "subsections": {}
    }
    collection["supersection"]["supersection_1"]["sections"]["section_1"] = current_section
    
    found_count = 0
    for i, id_str in enumerate(id_list):
        parsed = parse_id(id_str)
        if not parsed:
            print(f"Warning: Skipping invalid ID format: {id_str}")
            continue
            
        p_idx, k_idx, s_idx = parsed
        
        ss_key = f"supersection_{p_idx}"
        sec_key = f"section_{k_idx}"
        sub_key = f"subsection_{s_idx}"
        
        # Look up in source
        ss_data = source_super.get(ss_key)
        if not ss_data:
            print(f"Warning: Supersection {p_idx} not found for ID {id_str}")
            continue
            
        sec_data = ss_data.get('sections', {}).get(sec_key)
        if not sec_data:
            print(f"Warning: Section {k_idx} not found for ID {id_str}")
            continue
            
        sub_data = sec_data.get('subsections', {}).get(sub_key)
        if not sub_data:
            # Try to handle cases where there might be a mismatch in naming
            print(f"Warning: Subsection {s_idx} not found for ID {id_str}")
            continue
            
        # Copy the data
        # We'll use a new key in the target to maintain order
        target_sub_key = f"subsection_{found_count + 1}"
        
        # Deep copy/clone essential fields
        new_sub = {
            "header": sub_data.get("header", {}),
            "rik_id": sub_data.get("rik_id"),
            "rik_ids": sub_data.get("rik_ids", []),
            "rik_metadata": sub_data.get("rik_metadata", ""),
            "rik_text": sub_data.get("rik_text", ""),
            "saman_metadata": sub_data.get("saman_metadata", ""),
            "corrected-mantra_sets": sub_data.get("corrected-mantra_sets", []),
            "footnotes": sub_data.get("footnotes", {}),
            "mantra_sets": sub_data.get("mantra_sets", [])
        }
        
        # Prepend the ID to the header/title if possible to show origin
        if "header" in new_sub["header"]:
            orig_header = new_sub["header"]["header"]
            # new_sub["header"]["header"] = f"{id_str} {orig_header}"
        
        current_section["subsections"][target_sub_key] = new_sub
        found_count += 1
        
    # Save the output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(collection, f, ensure_ascii=False, indent=4)
        
    print(f"Successfully created collection with {found_count} items at {output_path}")
    print(f"You can now run: python src/render_pdf.py --type collection")

if __name__ == "__main__":
    main()
