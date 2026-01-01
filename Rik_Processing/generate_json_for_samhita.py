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
                
                # Use raw_text as-is - no truncation needed
                # (Previously had logic to find first swara marker, but it was cutting off valid text)
                
                # Strip line number prefix (e.g., "12: ") if present at the start
                # The input file has format: "N: text ॥ num ॥"
                raw_text = re.sub(r'^\s*\d+:\s*', '', raw_text)
                
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

    def get_current_section_max_id(self):
        """Returns the maximum Rik ID in the current section, or 0 if empty/no section."""
        if not self.current_map:
            return 0
        return max(self.current_map.keys())

    
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
            # Skip comment lines starting with #
            if line.startswith('#'):
                continue
            
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
    
    # NOTE: saman_meta_parser advances per section along with other parsers
    # since sama_rishi_chandas_out.txt now uses local Rik IDs per section

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

    global_rik_offset = 0
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
            # Update offset based on the section we are about to leave (if any)
            # But wait - we are about to advance to a NEW section.
            # So the offset should be incremented by the size of the previous section?
            # Actually, rik_text_parser is currently at the END of the previous section.
            if rik_text_parser.current_section_idx >= 0:
                 section_max = rik_text_parser.get_current_section_max_id()
                 global_rik_offset += section_max
                 print(f"[DEBUG] Finished Section {rik_text_parser.current_section_idx+1}. Max ID: {section_max}. New Offset: {global_rik_offset}")

            # Advance ALL external parsers - they all use local Rik IDs per section now
            rik_meta_parser.advance_section()
            rik_text_parser.advance_section()
            saman_meta_parser.advance_section()  # Now advances per section (local Rik IDs)

            
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
                    # Got valid rik_id from saman metadata (now Local ID per section)
                    
                    # Rik IDs are now local per section, so use directly
                    local_rik_id = rik_id_from_saman
                    # print(f"  [DEBUG] Rik Global: {rik_id_from_saman}, Offset: {global_rik_offset} -> Local: {local_rik_id}")

                    display_rik_text = rik_text_parser.get_text_by_rik_id(local_rik_id)
                    
                    # Rik Metadata seems to work with Global IDs (based on user observation/file content), 
                    # but if it fails we might need to check if it also needs conversion.
                    # Assuming Metadata file follows the same numbering as Saman Metadata (Global).
                    raw_rik_meta = rik_meta_parser.get_metadata_by_rik_id(rik_id_from_saman)
                    
                    # Track for carry-forward (when rik_id changes)
                    if rik_id_from_saman != last_rik_id:
                        # New Rik ID - update last known values
                        last_rik_id = rik_id_from_saman
                        last_rik_text = display_rik_text
                        last_rik_meta = raw_rik_meta
                    else:
                        # Same Rik ID as previous - reuse LAST KNOWN TEXT even if lookup returned None for current sub-part
                        # (Though mostly we want to display it again if it's the same Rik)
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

def extract_rik_only_data(combined_data):
    """Extract only Rik-related content from combined data."""
    rik_data = {"supersection": {}}
    
    for ss_id, ss_content in combined_data.get("supersection", {}).items():
        rik_data["supersection"][ss_id] = {
            "supersection_title": ss_content.get("supersection_title", ""),
            "sections": {}
        }
        
        for sec_id, sec_content in ss_content.get("sections", {}).items():
            if sec_id == "count":
                rik_data["supersection"][ss_id]["sections"]["count"] = sec_content
                continue
                
            rik_data["supersection"][ss_id]["sections"][sec_id] = {
                "section_title": sec_content.get("section_title", ""),
                "section_count": sec_content.get("section_count", ""),
                "subsections": {}
            }
            
            # Track unique Rik IDs to avoid duplicates
            seen_rik_ids = set()
            
            for sub_id, sub_content in sec_content.get("subsections", {}).items():
                rik_id = sub_content.get("rik_id")
                
                # Skip if we've already seen this Rik ID
                if rik_id in seen_rik_ids:
                    continue
                seen_rik_ids.add(rik_id)
                
                rik_data["supersection"][ss_id]["sections"][sec_id]["subsections"][sub_id] = {
                    "header": sub_content.get("header", {"header": f"Rik {rik_id}"}),
                    "rik_id": rik_id,
                    "rik_metadata": sub_content.get("rik_metadata", ""),
                    "rik_text": sub_content.get("rik_text", ""),
                    "saman_metadata": "",  # Empty for Rik-only
                    "corrected-mantra_sets": [],  # Empty for Rik-only
                    "mantra_sets": [],  # Empty for Rik-only
                }
    
    return rik_data


def extract_samam_only_data(combined_data):
    """Extract only Samam-related content from combined data."""
    samam_data = {"supersection": {}}
    
    for ss_id, ss_content in combined_data.get("supersection", {}).items():
        samam_data["supersection"][ss_id] = {
            "supersection_title": ss_content.get("supersection_title", ""),
            "sections": {}
        }
        
        for sec_id, sec_content in ss_content.get("sections", {}).items():
            if sec_id == "count":
                samam_data["supersection"][ss_id]["sections"]["count"] = sec_content
                continue
                
            samam_data["supersection"][ss_id]["sections"][sec_id] = {
                "section_title": sec_content.get("section_title", ""),
                "section_count": sec_content.get("section_count", ""),
                "subsections": {}
            }
            
            for sub_id, sub_content in sec_content.get("subsections", {}).items():
                samam_data["supersection"][ss_id]["sections"][sec_id]["subsections"][sub_id] = {
                    "header": sub_content.get("header", {}),
                    "saman_metadata": sub_content.get("saman_metadata", ""),
                    "corrected-mantra_sets": sub_content.get("corrected-mantra_sets", []),
                    "mantra_sets": sub_content.get("mantra_sets", []),
                }
    
    return samam_data


# --- UNICODE TEXT FILE PARSER (for correction cycle) ---
def parse_unicode_text_file(filepath):
    """
    Parse the structured Unicode text file back into JSON format.
    Uses # Start/End markers to identify sections.
    """
    import re
    
    if not os.path.exists(filepath):
        print(f"[ERROR] Unicode file '{filepath}' not found.")
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Initialize data structure
    data = {"supersection": {}}
    
    # Patterns for matching markers
    supersection_pattern = re.compile(
        r'# Start of SuperSection Title -- (\S+) ## DO NOT EDIT\s*\n([^\n]+)\s*\n# End of SuperSection Title', 
        re.MULTILINE
    )
    section_pattern = re.compile(
        r'# Start of Section Title -- (\S+) ## DO NOT EDIT\s*\n([^\n]+)\s*\n# End of Section Title', 
        re.MULTILINE
    )
    rik_metadata_pattern = re.compile(
        r'# Start of Rik Metadata -- (\S+) ## DO NOT EDIT\s*\n(.*?)\s*\n# End of Rik Metadata', 
        re.MULTILINE | re.DOTALL
    )
    rik_text_pattern = re.compile(
        r'# Start of Rik Text -- (\S+) ## DO NOT EDIT\s*\n(.*?)\s*\n# End of Rik Text', 
        re.MULTILINE | re.DOTALL
    )
    subsection_pattern = re.compile(
        r'# Start of SubSection Title -- (\S+) ## DO NOT EDIT\s*\n([^\n]+)\s*\n# End of SubSection Title', 
        re.MULTILINE
    )
    mantra_pattern = re.compile(
        r'#Start of Mantra Sets -- (\S+) ## DO NOT EDIT\s*\n(.*?)\s*\n#End of Mantra Sets', 
        re.MULTILINE | re.DOTALL
    )
    
    # Extract supersections
    for ss_match in supersection_pattern.finditer(content):
        ss_id = ss_match.group(1)
        ss_title = ss_match.group(2).strip()
        data["supersection"][ss_id] = {
            "supersection_title": ss_title,
            "sections": {}
        }
    
    # Extract sections
    for sec_match in section_pattern.finditer(content):
        sec_id = sec_match.group(1)
        sec_title = sec_match.group(2).strip()
        # Find which supersection this belongs to (assume first for now)
        for ss_id in data["supersection"]:
            if sec_id not in data["supersection"][ss_id]["sections"]:
                data["supersection"][ss_id]["sections"][sec_id] = {
                    "section_title": sec_title,
                    "subsections": {}
                }
    
    # Extract Rik metadata for each subsection
    rik_metadata_map = {}
    for rm_match in rik_metadata_pattern.finditer(content):
        sub_id = rm_match.group(1)
        rik_metadata_map[sub_id] = rm_match.group(2).strip()
    
    # Extract Rik text for each subsection
    rik_text_map = {}
    for rt_match in rik_text_pattern.finditer(content):
        sub_id = rt_match.group(1)
        rik_text_map[sub_id] = rt_match.group(2).strip()
    
    # Extract subsection headers (Samam header + metadata)
    subsection_headers = {}
    for sub_match in subsection_pattern.finditer(content):
        sub_id = sub_match.group(1)
        header_line = sub_match.group(2).strip()
        # Split header and saman_metadata (they're separated by double space)
        parts = header_line.split('  ', 1)
        header = parts[0].strip()
        saman_metadata = parts[1].strip() if len(parts) > 1 else ""
        subsection_headers[sub_id] = {"header": header, "saman_metadata": saman_metadata}
    
    # Extract mantra sets
    mantra_sets_map = {}
    for m_match in mantra_pattern.finditer(content):
        sub_id = m_match.group(1)
        mantra_text = m_match.group(2).strip()
        # Parse mantras - each line is part of the mantra content
        mantras = [line for line in mantra_text.split('\n') if line.strip()]
        mantra_sets_map[sub_id] = mantras
    
    # Extract footnotes
    footnote_pattern = re.compile(
        r'# Start of Footnote -- (\S+) ## DO NOT EDIT\s*\n(.*?)\n# End of Footnote',
        re.MULTILINE | re.DOTALL
    )
    footnotes_map = {}
    for fn_match in footnote_pattern.finditer(content):
        sub_id = fn_match.group(1)
        footnote_text = fn_match.group(2).strip()
        # Parse footnotes: "s1 - footnote text" format
        footnotes = {}
        for line in footnote_text.split('\n'):
            line = line.strip()
            if ' - ' in line:
                key, text = line.split(' - ', 1)
                footnotes[key.strip()] = text.strip()
        if footnotes:
            footnotes_map[sub_id] = footnotes
    
    # Build complete subsections
    all_subsection_ids = set(subsection_headers.keys()) | set(mantra_sets_map.keys())
    
    # Determine which section each subsection belongs to based on order
    subsection_to_section = {}
    current_section = None
    for line in content.split('\n'):
        sec_match = re.match(r'# Start of Section Title -- (\S+) ## DO NOT EDIT', line)
        if sec_match:
            current_section = sec_match.group(1)
        sub_match = re.match(r'# Start of SubSection Title -- (\S+) ## DO NOT EDIT', line)
        if sub_match and current_section:
            subsection_to_section[sub_match.group(1)] = current_section
    
    # Add subsections to their sections
    for sub_id in sorted(all_subsection_ids, key=lambda x: int(x.replace('subsection_', '')) if x.startswith('subsection_') else 0):
        sec_id = subsection_to_section.get(sub_id, 'section_1')
        
        # Find the supersection containing this section
        for ss_id in data["supersection"]:
            if sec_id in data["supersection"][ss_id]["sections"]:
                header_info = subsection_headers.get(sub_id, {"header": "", "saman_metadata": ""})
                
                # Extract rik_id from subsection number
                sub_num = int(sub_id.replace('subsection_', '')) if sub_id.startswith('subsection_') else 0
                
                # Build subsection entry
                subsection_entry = {
                    "header": {"header": header_info["header"], "header_number": sub_num},
                    "rik_id": sub_num,  # Will be corrected by Rik mapping if needed
                    "rik_metadata": rik_metadata_map.get(sub_id, ""),
                    "rik_text": rik_text_map.get(sub_id, ""),
                    "saman_metadata": header_info["saman_metadata"],
                    "mantra_sets": [],
                    "corrected-mantra_sets": [{"corrected-mantra": '\n'.join(mantra_sets_map.get(sub_id, []))}],
                    "footnotes": footnotes_map.get(sub_id, {})
                }
                
                data["supersection"][ss_id]["sections"][sec_id]["subsections"][sub_id] = subsection_entry
                break
    
    return data


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate JSON for Samhita rendering')
    parser.add_argument('--input-mode', choices=['initial', 'correction'], default='initial',
                        help='Input mode: initial (from multiple source files) or correction (from Unicode text)')
    parser.add_argument('--unicode-file', type=str, 
                        default='output_text/txt/Devanagari/Devanagari_Devanagari_Unicode.txt',
                        help='Path to Unicode text file (for correction mode)')
    parser.add_argument('--corrections-file', type=str, default='corrections_003.txt',
                        help='Path to corrections file (for initial mode)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output JSON file path')
    
    args = parser.parse_args()
    
    if args.input_mode == 'initial':
        # Initial mode: use multiple source files
        input_file = args.corrections_file
        rik_meta = "rishi_devata_chandas_for_rik.txt"
        saman_meta = "sama_rishi_chandas_out.txt"
        rik_text = "vedic_text.txt"
        
        output_file_path = args.output or (Path(input_file).stem + "_merged_out.json")
        print(f"Processing {input_file} in INITIAL mode...")
        output_data = convert_corrections_to_json(input_file, rik_meta, saman_meta, rik_text)
        
    else:
        # Correction mode: parse Unicode text file
        unicode_file = args.unicode_file
        output_file_path = args.output or "corrections_003_merged_out.json"
        print(f"Processing {unicode_file} in CORRECTION mode...")
        output_data = parse_unicode_text_file(unicode_file)
    
    if output_data:
        try:
            with open(output_file_path, 'w', encoding='utf-8') as outfile:
                json.dump(output_data, outfile, indent=4, ensure_ascii=False)
            print(f"Success! Saved to '{output_file_path}'")
        except IOError as e:
            print(f"Error writing to file: {e}")