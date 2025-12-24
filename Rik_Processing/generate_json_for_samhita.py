import sys
from pathlib import Path
import json
import re
import os

# --- 1. HELPER: Devanagari Digit Converter ---
def devanagari_to_int(text):
    """Converts Devanagari digits string to integer."""
    if not text: return None
    mapping = {'०':'0', '१':'1', '२':'2', '३':'3', '४':'4', 
               '५':'5', '६':'6', '७':'7', '८':'8', '९':'9'}
    converted = "".join([mapping.get(char, char) for char in text])
    try:
        return int(converted)
    except ValueError:
        return None

# --- 2. HELPER: Safe File Reader ---
def safe_read_file(file_path):
    if not os.path.exists(file_path):
        print(f"[WARNING] File '{file_path}' not found. Returning empty list.")
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if "\n\n" in content:
             lines = [line.strip() for line in content.split('\n\n') if line.strip()]
        else:
             lines = [line.strip() for line in content.split('\n') if line.strip()]
    return lines

def parse_mantra_set(mantra_set_text):
    mantra_sets = []
    mantras = [
        m.strip() 
        for m in mantra_set_text.split('\n') 
        if m.strip() and not m.strip().startswith('<') and not m.strip().startswith('#')
    ]
    full_text = "\n".join(mantras)
    return mantras, full_text

# --- 3. CLASS: Rik Metadata Parser (ORIGINAL) ---
class RikMetadataParser:
    def __init__(self, filepath):
        self.section_lines = []
        self.load_data(filepath)
        self.current_section_idx = -1
        self.current_map = {} 

    def load_data(self, filepath):
        if not os.path.exists(filepath):
            print(f"[WARNING] Rik Metadata file '{filepath}' not found.")
            return
        with open(filepath, 'r', encoding='utf-8') as f:
            self.section_lines = [line.strip() for line in f if line.strip()]

    def parse_range_string(self, range_str):
        indices = []
        range_str = range_str.replace('–', '-').replace(' ', '')
        parts = range_str.split(',')
        for part in parts:
            if '-' in part:
                try:
                    subparts = part.split('-')
                    if len(subparts) == 2 and subparts[0] and subparts[1]:
                        start, end = int(subparts[0]), int(subparts[1])
                        indices.extend(range(start, end + 1))
                except ValueError: continue
            else:
                try:
                    if part: indices.append(int(part))
                except ValueError: continue
        return indices

    def parse_section_line(self, line):
        range_match = re.match(r'^\s*\(([\d\s–-]+)\)', line)
        if range_match:
            line = re.sub(r'^\s*\([\d\s–-]+\)', '', line).strip()
        
        parts = line.split('।।')
        mapping_text = parts[0]
        suffix = "।।".join(parts[1:]).strip()
        if suffix: 
            suffix = suffix.strip('।| ') 
            suffix = "।। " + suffix + "।।"

        num_group_pattern = re.compile(r'((?:\d+(?:\s*[–-]\s*\d+)?(?:,\s*)?)+)')
        tokens = num_group_pattern.split(mapping_text)
        
        meta_map = {}
        for i in range(1, len(tokens), 2):
            num_str = tokens[i]
            name_text = tokens[i+1] if (i+1) < len(tokens) else ""
            name_text = name_text.strip().rstrip(',').strip()
            full_entry = f"।। {name_text} {suffix}"
            for rik_id in self.parse_range_string(num_str):
                meta_map[rik_id] = full_entry
        return meta_map

    def advance_section(self):
        self.current_section_idx += 1
        if self.current_section_idx < len(self.section_lines):
            self.current_map = self.parse_section_line(self.section_lines[self.current_section_idx])
        else:
            self.current_map = {}

    def get_metadata_by_rik_id(self, rik_id):
        return self.current_map.get(rik_id, "")

# --- 4. CLASS: Rik Text Parser (ORIGINAL) ---
class RikTextParser:
    def __init__(self, filepath):
        self.sections = [] 
        self.current_section_idx = -1
        self.current_map = {}
        self.load_data(filepath)

    def load_data(self, filepath):
        if not os.path.exists(filepath):
            print(f"[WARNING] Rik Text file '{filepath}' not found.")
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        raw_sections = re.split(r'॥\s*इति[^॥]+॥', content)
        
        for block in raw_sections:
            if not block.strip(): continue
            section_map = {}
            lines = block.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line: continue
                match = re.match(r'^(\d+)[:.]\s*(.*?)॥\s*([०-९\d]+)\s*॥', line)
                if match:
                    samam_id_str = match.group(1)
                    raw_text = match.group(2).strip()
                    rik_num_str = match.group(3) 
                    rik_id_int = devanagari_to_int(rik_num_str)
                    clean_text = f"{raw_text} ॥ {rik_num_str} ॥"
                    section_map[samam_id_str] = {
                        "text": clean_text,
                        "rik_id": rik_id_int
                    }
            if section_map:
                self.sections.append(section_map)

    def advance_section(self):
        self.current_section_idx += 1
        if self.current_section_idx < len(self.sections):
            self.current_map = self.sections[self.current_section_idx]
        else:
            self.current_map = {}

    def get_data_by_samam_id(self, samam_id_str):
        return self.current_map.get(samam_id_str, None)


# --- 5. MAIN CONVERSION LOGIC ---

def clean_rik_metadata_format(text):
    if not text: return ""
    text = " ".join(text.split())
    text = re.sub(r'[।|]+\s*$', '', text).strip()
    if not text: return ""
    return text + "।।"

def convert_corrections_to_json(
    file_path="corrections_003.txt",
    rik_meta_file="rishi_devata_chandas_for_rik.txt",
    saman_meta_file="sama_rishi_chandas_out.txt",
    rik_text_file="vedic_text.txt"
):
    print(f"--- Step 1: Loading External Datasets ---")
    
    rik_meta_parser = RikMetadataParser(rik_meta_file)
    rik_text_parser = RikTextParser(rik_text_file) 
    
    # Read external lines for Saman Metadata
    # We strip empty lines, assuming "4-2." is not empty.
    read_lines = lambda p: [l.strip() for l in open(p, 'r', encoding='utf-8').readlines() if l.strip()] if os.path.exists(p) else []
    saman_meta_iter = iter(read_lines(saman_meta_file))

    print(f"--- Step 2: Parsing Structure from {file_path} ---")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None

    json_output = {"supersection": {}}
    
    supersection_pattern = re.compile(r'# Start of SuperSection Title -- (supersection_\d+) ## DO NOT EDIT\s*(.*?)\s*# End of SuperSection Title -- \1 ## DO NOT EDIT\s*(.*?)(?=# Start of SuperSection Title -- supersection_\d+ ## DO NOT EDIT|$)', re.DOTALL)
    section_pattern = re.compile(r'# Start of Section Title -- (section_\d+) ## DO NOT EDIT\s*(.*?)\s*\((.*?)\)\s*# End of Section Title -- \1 ## DO NOT EDIT\s*(.*?)(?=# Start of Section Title -- section_\d+ ## DO NOT EDIT|# Start of SuperSection Title -- supersection_\d+ ## DO NOT EDIT|$)', re.DOTALL)
    subsection_pattern = re.compile(r'# Start of SubSection Title -- (subsection_\d+) ## DO NOT EDIT\s*(.*?)\s*# End of SubSection Title -- \1 ## DO NOT EDIT\s*#Start of Mantra Sets -- \1 ## DO NOT EDIT\s*(.*?)\s*#End of Mantra Sets -- \1 ## DO NOT EDIT', re.DOTALL)

    supersections_data = supersection_pattern.findall(file_content)
    
    if not supersections_data:
        print("[ERROR] No SuperSections found.")
        return None

    global_subsection_offset = 0

    for supersection_id, title_content, supersection_content in supersections_data:
        supersection_id = supersection_id.strip()
        title_content = re.sub(r'<[^>]+>', '', title_content, flags=re.DOTALL)
        supersection_title = re.sub(r'[|॥\s]', '', title_content).strip()
        
        json_output["supersection"][supersection_id] = {
            "supersection_title": supersection_title,
            "sections": {}
        }
        current_supersection_sections = json_output["supersection"][supersection_id]["sections"]
        sections_data = section_pattern.findall(supersection_content)
        
        section_count = len(sections_data)
        current_supersection_sections["count"] = { "prev_count": 0, "current_count": section_count, "total_count": section_count }
        
        for section_id, section_title, section_count_str, section_content in sections_data:
            # Advance external parsers
            rik_meta_parser.advance_section()
            rik_text_parser.advance_section() 
            
            clean_section_title = section_title.strip()
            current_supersection_sections[section_id] = {
                "section_title": clean_section_title,
                "section_count": section_count_str.strip(),
                "subsections": {}
            }
            
            subsections_data = subsection_pattern.findall(section_content)
            
            current_section_subsection_count = 0
            
            for subsection_id, raw_header_text, mantra_set_content in subsections_data:
                current_section_subsection_count += 1
                
                clean_header_text = re.sub(r'<[^>]+>', '', raw_header_text.strip()).strip().rstrip('…|').replace(':', 'ः')
                mantra_list, full_saman_text = parse_mantra_set(mantra_set_content)

                # --- 1. SAMAN METADATA LOGIC (SYNCHRONIZED) ---
                # Always fetch the next line from the external file to stay in sync
                saman_meta_val = ""
                try:
                    raw_line = next(saman_meta_iter, "")
                    if raw_line:
                        # Clean initial numbering (e.g., "5-1. ")
                        line_cleaned = re.sub(r'^\d+(?:-\d+)?\.\s*', '', raw_line)
                        
                        # Split at first danda (||, ॥, ।।, or ।। ।)
                        split_pattern = r'\s*(?:\|\||॥|।।)+\s*(?:[।|])?\s*'
                        parts = re.split(split_pattern, line_cleaned, maxsplit=1)
                        
                        # Logic:
                        # parts[0] is the Name (discarded).
                        # parts[1] is the Metadata (kept).
                        if len(parts) > 1:
                            meta_part = parts[1].strip()
                            if meta_part:
                                # Standardize danda wrapping
                                if not meta_part.startswith('।।'):
                                    meta_part = '।। ' + meta_part
                                if not meta_part.endswith('।।'):
                                    meta_part = meta_part + ' ।।'
                                saman_meta_val = meta_part
                        # If len(parts) == 1, it's just a name or empty numbering -> Metadata empty.
                        
                except StopIteration:
                    # End of file
                    pass
                
                # --- 2. RIK MAPPING LOGIC (ORIGINAL) ---
                try:
                    global_num = int(subsection_id.split('_')[1])
                    samam_local_id = str(global_num - global_subsection_offset)
                    
                    text_entry = rik_text_parser.get_data_by_samam_id(samam_local_id)
                    
                    if text_entry:
                        display_rik_text = text_entry["text"]
                        associated_rik_id = text_entry["rik_id"] 
                        raw_rik_meta = rik_meta_parser.get_metadata_by_rik_id(associated_rik_id)
                    else:
                        display_rik_text = None
                        raw_rik_meta = ""
                        
                except (IndexError, ValueError):
                    display_rik_text = None
                    raw_rik_meta = ""

                rik_meta_val = clean_rik_metadata_format(raw_rik_meta)
                if not display_rik_text:
                    rik_meta_val = "" 

                current_supersection_sections[section_id]["subsections"][subsection_id] = {
                    "header": { "header": clean_header_text },
                    "rik_metadata": rik_meta_val,     
                    "rik_text": display_rik_text,     
                    "saman_metadata": saman_meta_val, 
                    "corrected-mantra_sets": [{
                        "corrected-mantra": full_saman_text, 
                        "corrected-swara": ""
                    }],
                    "mantra_sets": []
                }
            
            global_subsection_offset += current_section_subsection_count

    return json_output

if __name__ == "__main__":
    input_file = "corrections_003.txt"
    rik_meta = "rishi_devata_chandas_for_rik.txt"
    saman_meta = "sama_rishi_chandas_out.txt"
    rik_text = "vedic_text.txt"

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    
    output_file_path = Path(input_file).stem + "_merged_out.json"
    print(f"Processing {input_file}...")
    output_data = convert_corrections_to_json(input_file, rik_meta, saman_meta, rik_text)
    
    if output_data:
        try:
            with open(output_file_path, 'w', encoding='utf-8') as outfile:
                json.dump(output_data, outfile, indent=4, ensure_ascii=False)
            print(f"Success! Saved to '{output_file_path}'")
        except IOError as e:
            print(f"Error writing to file: {e}")