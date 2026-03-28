"""
Script to renumber all supersections, sections, and subsections in JSV files.
Supports both .txt (line-by-line regex) and .json (object-based re-indexing) formats.
"""
import re
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

def int_to_devanagari(n):
    mapping = {'0':'०', '1':'१', '2':'२', '3':'३', '4':'४', 
               '5':'५', '6':'६', '7':'७', '8':'८', '9':'९'}
    return "".join(mapping[c] for c in str(n))

def renumber_text_file(input_file):
    print(f"Renumbering TEXT file: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_sup = 0
    current_sec = 0
    current_sub = 1

    new_lines = []
    for line in lines:
        if '# Start of SuperSection Title' in line:
            current_sup += 1
        if '# Start of Section Title' in line:
            current_sec += 1

        # Apply replacements using current counters
        def replace_supersection(m):
            return f'supersection_{current_sup}' if current_sup > 0 else m.group(0)
        def replace_section(m):
            return f'section_{current_sec}' if current_sec > 0 else m.group(0)
        def replace_subsection(m):
            return f'subsection_{current_sub}'

        line = re.sub(r'subsection_(\d+)', replace_subsection, line)
        line = re.sub(r'(?<!super)(?<!sub)section_(\d+)', replace_section, line)
        line = re.sub(r'supersection_(\d+)', replace_supersection, line)
        
        new_lines.append(line)

        # Increment subsection counter AFTER the end of the mantra sets block
        if '#End of Mantra Sets' in line or '# End of Mantra Sets' in line:
            current_sub += 1

    # Pass 2: Renumber Samams contiguously within text
    final_lines = []
    samam_counter = 1
    in_mantra_set = False
    in_subsection_title = False

    for line in new_lines:
        # Clean up old subsection titles
        if '# Start of SubSection Title' in line:
            in_subsection_title = True
        elif '# End of SubSection Title' in line:
            in_subsection_title = False
        elif in_subsection_title and line.strip():
            text = line.strip()
            if text.startswith('॥') and (text.endswith('॥') or text.endswith(')')):
                prefix = line[:line.find('॥')]
                # Handle various header formats
                m1 = re.match(r'^॥\s*(.+?)\s*-\s*[०-९]+\s*॥$', text)
                m2 = re.match(r'^॥\s*(.+?)\s*॥\s*\([०-९]+\)$', text)
                
                inner = None
                if m1: inner = m1.group(1).strip()
                elif m2: inner = m2.group(1).strip()
                elif text.endswith('॥'): inner = text[1:-1].strip()
                
                if inner: line = f"{prefix}॥ {inner} ॥\n"

        if '#Start of Mantra Sets' in line or '# Start of Mantra Sets' in line:
            in_mantra_set = True
            
        if in_mantra_set:
            def samam_repl(m):
                nonlocal samam_counter
                res = f"॥ {int_to_devanagari(samam_counter)} ॥"
                samam_counter += 1
                return res
            line = re.sub(r'(?:॥|\|\|)\s*([०-९\d]+)\s*(?:॥|\|\|)', samam_repl, line)
            
        if '#End of Mantra Sets' in line or '# End of Mantra Sets' in line:
            in_mantra_set = False
            
        final_lines.append(line)

    with open(input_file, 'w', encoding='utf-8') as f:
        f.writelines(final_lines)
    
    print(f"Success! {current_sup} SuperSections, {current_sec} Sections, {current_sub-1} SubSections.")
    print(f"Total Samams Renumbered: {samam_counter - 1}")

def renumber_json_file(input_file, output_file=None):
    print(f"Renumbering JSON file: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    new_data = {
        "meta": data.get("meta", {}),
        "supersection": {}
    }
    new_data["meta"]["renumbered_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    global_samam_count = 0
    ss_idx = 1
    
    # Sort supersections by ID
    ss_keys = sorted(data.get("supersection", {}).keys(), key=lambda x: int(x.split('_')[1]) if '_' in x else 0)

    for old_ss_id in ss_keys:
        old_ss = data["supersection"][old_ss_id]
        new_ss_id = f"supersection_{ss_idx}"
        
        new_ss = {
            "supersection_title": old_ss.get("supersection_title", ""),
            "supersection_number": ss_idx,
            "sections": {}
        }
        
        sec_idx = 1
        old_sec_data = old_ss.get("sections", {})
        sec_keys = sorted([k for k in old_sec_data.keys() if k.startswith('section_')], 
                         key=lambda x: int(x.split('_')[1]) if '_' in x else 0)
        
        for old_sec_id in sec_keys:
            old_sec = old_sec_data[old_sec_id]
            new_sec_id = f"section_{sec_idx}"
            
            new_sec = {
                "section_title": old_sec.get("section_title", ""),
                "section_number": sec_idx,
                "Count": "०",
                "subsections": {}
            }
            
            sub_idx = 1
            local_samam_count = 0
            old_sub_data = old_sec.get("subsections", {})
            sub_keys = sorted(old_sub_data.keys(), key=lambda x: int(x.split('_')[1]) if '_' in x else 0)
            
            for old_sub_id in sub_keys:
                old_sub = old_sub_data[old_sub_id]
                new_sub_id = f"subsection_{sub_idx}"
                
                # Update header number and copy structure
                import copy
                new_sub = copy.deepcopy(old_sub)
                if "header" in new_sub:
                    new_sub["header"]["header_number"] = sub_idx
                
                # Renumber Samams in mantras
                for ms in new_sub.get("corrected-mantra_sets", []):
                    mantra = ms.get("corrected-mantra", "")
                    
                    def samam_repl(m):
                        nonlocal global_samam_count, local_samam_count
                        global_samam_count += 1
                        local_samam_count += 1
                        return f"॥ {int_to_devanagari(global_samam_count)} ॥"
                    
                    ms["corrected-mantra"] = re.sub(r'॥\s*[०-९\d]+\s*॥', samam_repl, mantra)
                
                new_sec["subsections"][new_sub_id] = new_sub
                sub_idx += 1
                
            new_sec["Count"] = int_to_devanagari(local_samam_count)
            new_ss["sections"][new_sec_id] = new_sec
            sec_idx += 1
            
        new_ss["sections"]["count"] = {"current_count": sec_idx - 1}
        new_data["supersection"][new_ss_id] = new_ss
        ss_idx += 1

    if "closing_mantras" in data: new_data["closing_mantras"] = data["closing_mantras"]

    if not output_file: output_file = input_file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, ensure_ascii=False, indent=4)
    
    print(f"Successfully renumbered JSON: {ss_idx-1} SuperSections, {global_samam_count} Samams.")

def main():
    parser = argparse.ArgumentParser(description="Renumber JSV files (JSON or TXT).")
    parser.add_argument('input_file', help="Path to input JSV file")
    parser.add_argument('--output', help="Output file path (optional)")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: {input_path} not found.")
        sys.exit(1)

    if input_path.suffix.lower() == '.json':
        renumber_json_file(args.input_file, args.output)
    else:
        renumber_text_file(args.input_file)

if __name__ == "__main__":
    main()
