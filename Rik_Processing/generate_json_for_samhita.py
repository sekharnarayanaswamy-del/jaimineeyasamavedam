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

        # Split by section markers like "॥ इति प्रथमः खण्डः ॥"
        raw_sections = re.split(r'॥\s*इति[^॥]+॥', content)
        
        # Pattern to match Rik text ending with ॥ num ॥
        # Captures text before the number and the Devanagari/Arabic numeral
        rik_pattern = re.compile(r'([^॥]+?)॥\s*([०-९\d]+)\s*॥')
        
        for block in raw_sections:
            if not block.strip(): 
                continue
            section_map = {}  # {rik_id: text}
            
            # Find all Rik entries in this section block
            for match in rik_pattern.finditer(block):
                raw_text = match.group(1).strip()
                rik_num_str = match.group(2)
                rik_id_int = devanagari_to_int(rik_num_str)
                
                # Skip if no swara markers (header lines)
                if '(' not in raw_text and ')' not in raw_text:
                    continue
                
                # Extract only the actual Rik text - find first swara marker and take from nearest word start
                # Look for pattern like "word(num)" which indicates actual Rik content
                rik_start_match = re.search(r'[\u0900-\u097F]+\([0-9०-९]+\)', raw_text)
                if rik_start_match:
                    # Find the start of the word containing the first swara
                    # Look back for whitespace or line break before first Sanskrit character of that word
                    rik_start = rik_start_match.start()
                    # Go back to find start of the word containing the match
                    while rik_start > 0 and raw_text[rik_start-1] not in '\n\r ':
                        rik_start -= 1
                    raw_text = raw_text[rik_start:].strip()
                
                clean_text = f"{raw_text} ॥ {rik_num_str} ॥"
                # Store by rik_id (overwrite if duplicate - take last occurrence)
                section_map[rik_id_int] = clean_text
            
            if section_map:
                self.sections.append(section_map)
                print(f"[INFO] RikTextParser Section {len(self.sections)}: Loaded {len(section_map)} unique Riks")

    def advance_section(self):
        self.current_section_idx += 1
        if self.current_section_idx < len(self.sections):
            self.current_map = self.sections[self.current_section_idx]
        else:
            self.current_map = {}

    def get_text_by_rik_id(self, rik_id):
        """Get rik text by rik_id. Returns None if not found."""
        if rik_id is None:
            return None
        return self.current_map.get(rik_id, None)
    
    def get_data_by_samam_id(self, samam_id_str):
        """Legacy method - kept for compatibility."""
        return None


# --- 4b. CLASS: Saman Metadata Parser (NEW) ---
class SamanMetadataParser:
    """Parses sama_rishi_chandas_out.txt and provides sequential samam access."""
    
    def __init__(self, filepath):
        self.sections = []  # List of lists: [(rik_id, title, metadata), ...]
        self.current_section_idx = -1
        self.current_samams = []  # Current section's samams in order
        self.samam_counter = 0    # Index into current_samams
        self.load_data(filepath)
    
    def load_data(self, filepath):
        if not os.path.exists(filepath):
            print(f"[WARNING] Saman Metadata file '{filepath}' not found.")
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        current_section = []  # List of (rik_id, title, metadata) tuples in order
        prev_rik_id = 0
        
        for line in lines:
            # Parse format: "RikId-SamamCount. [Title] ।। [Metadata] ।।"
            match = re.match(r'^(\d+)-(\d+)\.(.*)$', line)
            if not match:
                continue
            
            rik_id = int(match.group(1))
            samam_idx = int(match.group(2))
            rest = match.group(3).strip()
            
            # Detect section break: Rik ID resets to 1 after being higher
            if rik_id == 1 and prev_rik_id > 1 and current_section:
                self.sections.append(current_section)
                current_section = []
            
            prev_rik_id = rik_id
            
            # Extract title (part before ।।) and metadata (part after first ।।)
            title = ""
            metadata = ""
            if rest:
                # Split at first danda sequence
                split_pattern = r'\s*(?:\|{2}|॥|।{2})+\s*'
                parts = re.split(split_pattern, rest, maxsplit=1)
                # Title is the part before ।।
                title = parts[0].strip() if parts else ""
                if len(parts) > 1:
                    meta_part = parts[1].strip()
                    if meta_part:
                        # Clean and standardize danda wrapping
                        meta_part = re.sub(r'^[।|॥\s]+', '', meta_part)
                        meta_part = re.sub(r'[।|॥\s]+$', '', meta_part)
                        if meta_part:
                            metadata = '।। ' + meta_part + ' ।।'
            
            # Store as (rik_id, title, metadata) tuple in order
            current_section.append((rik_id, title, metadata))
        
        # Don't forget the last section
        if current_section:
            self.sections.append(current_section)
        
        print(f"[INFO] Loaded {len(self.sections)} sections from Saman metadata file.")
        for i, sec in enumerate(self.sections):
            print(f"  Section {i+1}: {len(sec)} samams")
    
    def advance_section(self):
        """Move to next section, reset counter."""
        self.current_section_idx += 1
        if self.current_section_idx < len(self.sections):
            self.current_samams = self.sections[self.current_section_idx]
        else:
            self.current_samams = []
        self.samam_counter = 0
    
    def get_next_samam(self):
        """Get next samam's (rik_id, title, metadata). Returns (None, '', '') if exhausted."""
        if self.samam_counter >= len(self.current_samams):
            return (None, "", "")
        
        rik_id, title, metadata = self.current_samams[self.samam_counter]
        self.samam_counter += 1
        return (rik_id, title, metadata)
    
    def peek_next_samam(self):
        """Peek at next samam without advancing counter. Returns (rik_id, title, metadata) or (None, '', '')."""
        if self.samam_counter >= len(self.current_samams):
            return (None, "", "")
        return self.current_samams[self.samam_counter]
    
    def peek_rik_id(self):
        """Peek at current samam's rik_id without advancing counter."""
        if self.samam_counter >= len(self.current_samams):
            return None
        return self.current_samams[self.samam_counter][0]
    
    def get_metadata_for_rik(self, rik_id):
        """Get next available metadata for given Rik ID. Returns empty string if exhausted."""
        # Legacy method - kept for compatibility but not used in new flow
        return ""
    
    def get_remaining_for_rik(self, rik_id):
        """Get all remaining metadata for this Rik (for concatenation case)."""
        # Legacy method - kept for compatibility
        return []
    
    def count_remaining_for_rik(self, rik_id):
        """Count how many remaining samams (from current position) have the specified Rik ID."""
        count = 0
        for i in range(self.samam_counter, len(self.current_samams)):
            if self.current_samams[i][0] == rik_id:
                count += 1
            else:
                # Stop counting once we hit a different Rik ID
                break
        return count


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
    saman_meta_parser = SamanMetadataParser(saman_meta_file)
    
    # Initialize saman parser to first section (contains all samams for sequential processing)
    saman_meta_parser.advance_section()

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
            # Advance external parsers (only Rik parsers - saman parser is processed sequentially)
            rik_meta_parser.advance_section()
            rik_text_parser.advance_section()
            # NOTE: saman_meta_parser does NOT advance sections - it's processed sequentially

            
            clean_section_title = section_title.strip()
            current_supersection_sections[section_id] = {
                "section_title": clean_section_title,
                "section_count": section_count_str.strip(),
                "subsections": {}
            }
            
            subsections_data = subsection_pattern.findall(section_content)
            
            current_section_subsection_count = 0
            
            # Track last known Rik values for carry-forward
            last_rik_id = None
            last_rik_text = None
            last_rik_meta = ""
            
            # Track titles used in this section to detect duplicate/continuation samams
            used_titles_in_section = set()
            
            for subsection_id, raw_header_text, mantra_set_content in subsections_data:
                current_section_subsection_count += 1
                
                clean_header_text = re.sub(r'<[^>]+>', '', raw_header_text.strip()).strip().rstrip('…|').replace(':', 'ः')
                mantra_list, full_saman_text = parse_mantra_set(mantra_set_content)
                
                # Count how many mantras (samams) are in this subsection by finding mantra number markers (॥N॥)
                # Pattern matches Devanagari numerals enclosed in dandas: ॥१॥, ॥२॥, ॥१०॥, etc.
                mantra_markers = re.findall(r'॥\s*[०-९]+\s*॥', full_saman_text)
                num_mantras = len(mantra_markers) if mantra_markers else 1
                
                # --- 1. GET SAMAM METADATA FOR ALL MANTRAS IN THIS SUBSECTION ---
                # Consume 'num_mantras' entries from sama_rishi_chandas_out.txt
                saman_meta_val = ""
                rik_id_from_saman = None
                
                for mantra_idx in range(num_mantras):
                    rik_id, saman_title, saman_meta = saman_meta_parser.get_next_samam()
                    
                    # Use the first valid rik_id
                    if rik_id is not None and rik_id_from_saman is None:
                        rik_id_from_saman = rik_id
                    
                    # Concatenate metadata from all samams
                    if saman_meta:
                        saman_meta_val = (saman_meta_val + " " + saman_meta).strip() if saman_meta_val else saman_meta

                
                # --- 3. DETERMINE RIK_TEXT AND RIK_METADATA ---
                if rik_id_from_saman is not None:
                    # Got valid rik_id from saman metadata
                    display_rik_text = rik_text_parser.get_text_by_rik_id(rik_id_from_saman)
                    raw_rik_meta = rik_meta_parser.get_metadata_by_rik_id(rik_id_from_saman)
                    
                    # Track for carry-forward (when rik_id changes)
                    if rik_id_from_saman != last_rik_id:
                        # New Rik ID - update last known values
                        last_rik_id = rik_id_from_saman
                        last_rik_text = display_rik_text
                        last_rik_meta = raw_rik_meta
                    else:
                        # Same Rik ID as previous - use last known text (don't re-display)
                        # Actually we SHOULD display the same rik_text for all samams of same Rik
                        pass
                else:
                    # No saman metadata - use carry-forward
                    rik_id_from_saman = last_rik_id
                    display_rik_text = last_rik_text
                    raw_rik_meta = last_rik_meta
                    saman_meta_val = ""

                rik_meta_val = clean_rik_metadata_format(raw_rik_meta)
                if not display_rik_text:
                    rik_meta_val = ""

                current_supersection_sections[section_id]["subsections"][subsection_id] = {
                    "header": { "header": clean_header_text },
                    "rik_id": rik_id_from_saman,
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