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

# --- 2.5. HELPER: Sanitize Invisible Characters ---
def sanitize_invisible_chars(text):
    """
    Remove invisible Unicode characters that can break pattern matching.
    These often get introduced when copy-pasting from web pages or PDFs.
    """
    if not text:
        return text
    # Characters to remove around footnote markers
    invisible_chars = [
        '\u200b',  # Zero-width space
        '\u200c',  # Zero-width non-joiner
        '\u200d',  # Zero-width joiner (FOUND IN YOUR FILE!)
        '\ufeff',  # BOM / Zero-width no-break space
        '\u2060',  # Word joiner
        '\u180e',  # Mongolian vowel separator
        '\u00ad',  # Soft hyphen
    ]
    for char in invisible_chars:
        text = text.replace(char, '')
    return text

def parse_mantra_set(mantra_set_text):
    mantra_sets = []
    mantras = [
        m.strip() 
        for m in mantra_set_text.split('\n') 
        if m.strip() and not m.strip().startswith('<') and not m.strip().startswith('#')
    ]
    full_text = "\n".join(mantras)
    return mantras, full_text

# --- 3. CLASS: Rik Metadata Parser (ENHANCED) ---
class RikMetadataParser:
    """
    Parses rishi_devata_chandas_for_rik.txt with support for Rik-specific 
    Devata and Chandas overrides.
    
    Format: (1-10) 1 Rishi1 2 Rishi2...।। Devata।। 8 SpecialDevata।। Chandas।।
    
    Numbers before a name indicate Rik-specific assignment.
    Names without numbers are defaults for all Riks in that section.
    """
    
    def __init__(self, filepath):
        self.section_lines = []
        self.load_data(filepath)
        self.current_section_idx = -1
        self.current_section_idx = -1
        self.current_map = {} 

    def _split_ignoring_parens(self, text, pattern):
        """
        Splits text by regex pattern, but ignores matches inside parentheses.
        Returns a list of tokens similar to re.split, including valid delimiters.
        """
        # 1. Identify forbidden regions (inside parentheses)
        forbidden_ranges = []
        depth = 0
        start_idx = -1
        for i, char in enumerate(text):
            if char == '(':
                if depth == 0: start_idx = i
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0 and start_idx != -1:
                    forbidden_ranges.append((start_idx, i))
                    start_idx = -1
        
        # 2. Find all matches of the pattern
        matches = list(pattern.finditer(text))
        
        # 3. Filter matches that overlap with forbidden regions
        valid_matches = []
        for m in matches:
            m_start, m_end = m.span()
            is_forbidden = False
            for f_start, f_end in forbidden_ranges:
                # If match starts inside a forbidden range
                if f_start < m_start < f_end:
                    is_forbidden = True
                    break
            if not is_forbidden:
                valid_matches.append(m)
        
        # 4. Construct tokens list
        tokens = []
        last_end = 0
        for m in valid_matches:
            # Text before the match
            tokens.append(text[last_end:m.start()])
            # The delimiter (capturing group 1 if present, else group 0)
            # The pattern is expected to be wrapped in a capturing group like (pattern)
            val = m.group(1) if m.re.groups > 0 else m.group(0)
            tokens.append(val)
            last_end = m.end()
        # Remaining text
        tokens.append(text[last_end:])
        
        return tokens

    def process_value_for_rik(self, text, rik_id):
        """
        Resolves conditional content inside parentheses for a specific Rik ID.
        Also cleans formatting labels like 'ऋषिः'.
        """
        if not text or '(' not in text:
            return text
            
        def replace_match(match):
            content = match.group(1)
            
            # Simple check: if no numbers, it's just text (applies to all)
            if not any(char.isdigit() for char in content):
                # Clean labels
                cleaned = re.sub(r'(?:ऋषिः|देवता|छन्दः)\s*', '', content).strip()
                return f"({cleaned})" if cleaned else ""
                
            # Parse inner content for overrides
            # 1. Default (text before first number)
            default_val = ""
            leading_match = re.match(r'^([^\d]+?)(?=\d|$)', content)
            if leading_match:
                default_val = leading_match.group(1).strip().rstrip(',').strip()
            
            # 2. Overrides (Number Val)
            overrides = {}
            pattern = re.compile(
                r'((?:\d+(?:\s*[,–-]\s*\d+)*(?:,\s*)?)+)\s+([^\d,]+?)(?=\s*\d+(?:\s*[,–-]\s*\d+)*\s+[^\d]|$)'
            )
            # Use strict finditer on the inner content
            for m in pattern.finditer(content):
                num_str = m.group(1).strip()
                val = m.group(2).strip().rstrip(',').strip()
                if val:
                    for rid in self.parse_range_string(num_str):
                        overrides[rid] = val
                        
            # 3. Determine final value for this Rik ID
            parts = []
            
            # Add default value if present (cleaned)
            clean_default = re.sub(r'(?:ऋषिः|देवता|छन्दः)\s*', '', default_val).strip()
            if clean_default:
                parts.append(clean_default)
                
            # Add specific override if present (cleaned)
            if rik_id in overrides:
                clean_override = re.sub(r'(?:ऋषिः|देवता|छन्दः)\s*', '', overrides[rik_id]).strip()
                if clean_override:
                    parts.append(clean_override)
            
            if not parts:
                return ""
                
            return f"({' '.join(parts)})"

        # Apply replacement to all parenthesized blocks
        return re.sub(r'\(([^)]+)\)', replace_match, text)

    def load_data(self, filepath):
        if not os.path.exists(filepath):
            print(f"[WARNING] Rik Metadata file '{filepath}' not found.")
            return
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            self.section_lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]

    def parse_range_string(self, range_str):
        """Parse a range string like '1, 3, 5-8' into list of integers."""
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

    def parse_devata_chandas_section(self, section_text):
        """
        Parse a Devata or Chandas section for Rik-specific entries.
        Uses _split_ignoring_parens to robustly handle values that may contain numbers in parens.
        """
        if not section_text:
            return "", {}
        
        section_text = section_text.strip().strip('।|,').strip()
        if not section_text:
            return "", {}
        
        rik_specific_map = {}
        default_value = ""
        
        # Pattern for number groups: "1" or "1, 2" or "1-3, 5"
        # Must be wrapped in capturing group for split to return it
        num_pattern = re.compile(r'((?:\d+(?:\s*[,–-]\s*\d+)*(?:,\s*)?)+)')
        
        # Tokenize: [Text, NumGroup, Text, NumGroup, Text...]
        tokens = self._split_ignoring_parens(section_text, num_pattern)
        
        # The first token is the default value (if any)
        # However, due to regex, if it starts with number, first token is empty string
        # tokens[0] = Text before first number (Default)
        # tokens[1] = First Number Group
        # tokens[2] = Value for First Number Group
        # ...
        
        if tokens:
            # Clean up default value
            val = tokens[0].strip().rstrip(',').strip()
            if val:
                default_value = val
                
            # Iterate over pairs (Number, Value)
            for i in range(1, len(tokens) - 1, 2):
                num_str = tokens[i].strip()
                val_text = tokens[i+1].strip().rstrip(',').strip()
                
                # If val_text is empty, it might mean the number group continues or is malformed, 
                # but typically it means the value is empty.
                if val_text:
                    for rik_id in self.parse_range_string(num_str):
                        rik_specific_map[rik_id] = val_text
                        
        return default_value, rik_specific_map

    def parse_section_line(self, line):
        """
        Parse a full metadata line for a section (Kandah).
        
        Format examples:
        1) (1-10) 1 Rishi1 2 Rishi2...।। Devata।। Chandas।।
        2) (1-10) 1 Rishi1...।। Devata।। 8 OverrideDevata।। Chandas।।
        3) (1-10) 1 Rishi1...।। Default, 2 Override1 3 Override2।। Chandas।।
        
        Returns: {rik_id: "।। Rishi Devata Chandas ।।"} 
        """
        # 1. Extract Rik range from (1-10) prefix
        range_match = re.match(r'^\s*\(([\d\s–-]+)\)', line)
        rik_range = []
        if range_match:
            rik_range = self.parse_range_string(range_match.group(1))
            line = re.sub(r'^\s*\([\d\s–-]+\)', '', line).strip()
        
        # 2. Split by ।। to separate Rishi, Devata, Chandas sections
        parts = line.split('।।')
        
        # First part is Rishi section (before first ।।)
        rishi_section = parts[0] if parts else ""
        
        # Remaining parts are Devata and Chandas (after first ।।)
        suffix_parts = parts[1:] if len(parts) > 1 else []
        
        # 3. Parse Rishi section (numbers before names)
        # 3. Parse Rishi section (numbers before names)
        rishi_map = {}
        # Pattern matching number groups, ensuring they are separated
        num_group_pattern = re.compile(r'((?:\d+(?:\s*[–-]\s*\d+)*(?:,\s*)?)+)')
        
        # Use new split method to avoid splitting numbers inside parens
        tokens = self._split_ignoring_parens(rishi_section, num_group_pattern)
        
        # Handle implicit first rishi or normal structure
        default_rishi = ""
        if len(tokens) > 0 and tokens[0].strip():
             default_rishi = tokens[0].strip().rstrip(',').strip()
        
        for i in range(1, len(tokens), 2):
            num_str = tokens[i]
            name_text = tokens[i+1] if (i+1) < len(tokens) else ""
            name_text = name_text.strip().rstrip(',').strip()
            
            if name_text:
                for rik_id in self.parse_range_string(num_str):
                    rishi_map[rik_id] = name_text
        
        # If there's a default rishi found at start, fill in missing IDs
        if default_rishi:
            for rik_id in rik_range:
                if rik_id not in rishi_map:
                    rishi_map[rik_id] = default_rishi
        
        # 4. Parse Devata and Chandas sections
        # Key insight: The LAST non-empty part is Chandas, everything else is Devata
        devata_default, devata_specific = "", {}
        chandas_default, chandas_specific = "", {}
        
        # Clean and filter non-empty parts
        clean_suffix_parts = [p.strip().strip('।|') for p in suffix_parts if p.strip().strip('।|')]
        
        if len(clean_suffix_parts) == 0:
            # No Devata or Chandas
            pass
        elif len(clean_suffix_parts) == 1:
            # Single part - could be Devata only or Chandas only
            # Treat as Chandas (since that's typically the last field)
            chandas_default, chandas_specific = self.parse_devata_chandas_section(clean_suffix_parts[0])
        else:
            # Multiple parts: LAST is Chandas, rest are Devata
            # Combine all Devata parts (they might be split by ।।, e.g., "अग्निः ।। 8 इन्द्रः")
            devata_parts = clean_suffix_parts[:-1]
            chandas_part = clean_suffix_parts[-1]
            
            # Parse Chandas (last part)
            chandas_default, chandas_specific = self.parse_devata_chandas_section(chandas_part)
            
            # Parse Devata (all middle parts combined)
            # Each part may have default + overrides
            for part in devata_parts:
                part_default, part_specific = self.parse_devata_chandas_section(part)
                
                # First non-empty default becomes the Devata default
                if part_default and not devata_default:
                    devata_default = part_default
                
                # Merge all Rik-specific overrides
                devata_specific.update(part_specific)
        
        # 5. Build combined metadata map for each Rik
        meta_map = {}
        for rik_id in rik_range:
            # Get Rishi for this Rik (processed)
            rishi = self.process_value_for_rik(rishi_map.get(rik_id, ""), rik_id)
            
            # Get Devata for this Rik (specific or default, processed)
            devata = self.process_value_for_rik(devata_specific.get(rik_id, devata_default), rik_id)
            
            # Get Chandas for this Rik (specific or default, processed)
            chandas = self.process_value_for_rik(chandas_specific.get(rik_id, chandas_default), rik_id)
            
            # Build combined metadata string - only include non-empty parts
            parts_list = []
            if rishi:
                parts_list.append(rishi)
            if devata:
                parts_list.append(devata)
            if chandas:
                parts_list.append(chandas)
            
            if parts_list:
                meta_map[rik_id] = "।। " + " ".join(parts_list) + " ।।"
        
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
                            # Normalize internal pipes to Devanagari dandas
                        meta_part = meta_part.replace('||', '॥').replace('|', '।')
                        
                        if meta_part:
                            metadata = '।। ' + meta_part + ' ।।'

            # Store as (rik_id, title, metadata) tuple in order
            current_section.append((rik_id, title, metadata))
        
        # Don't forget the last section
        if current_section:
            self.sections.append(current_section)
        
        print(f"[INFO] Loaded {len(self.sections)} sections from Samam metadata file.")
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
    
    # Normalize pipes -> dandas
    text = text.replace('||', '॥').replace('|', '।')
    
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
    
    # Build section-to-supersection mapping by scanning file order
    section_to_supersection = {}
    current_supersection = None
    for line in content.split('\n'):
        ss_match = re.match(r'# Start of SuperSection Title -- (\S+) ## DO NOT EDIT', line)
        if ss_match:
            current_supersection = ss_match.group(1)
        sec_match = re.match(r'# Start of Section Title -- (\S+) ## DO NOT EDIT', line)
        if sec_match and current_supersection:
            section_to_supersection[sec_match.group(1)] = current_supersection
    
    # Extract sections and assign to correct supersection
    for sec_match in section_pattern.finditer(content):
        sec_id = sec_match.group(1)
        sec_title = sec_match.group(2).strip()
        # Use the mapping to find the correct supersection
        ss_id = section_to_supersection.get(sec_id, 'supersection_1')
        if ss_id in data["supersection"]:
            data["supersection"][ss_id]["sections"][sec_id] = {
                "section_title": sec_title,
                "subsections": {}
            }
    
    # Extract Rik metadata for each subsection
    rik_metadata_map = {}
    for rm_match in rik_metadata_pattern.finditer(content):
        sub_id = rm_match.group(1)
        meta_text = rm_match.group(2).strip().replace('\n', ' ')
        # Strip any literal \newline commands that may have crept in
        meta_text = meta_text.replace('\\newline%', ' ').replace('\\newline', ' ')
        # Normalize pipes
        meta_text = meta_text.replace('||', '॥').replace('|', '।')
        rik_metadata_map[sub_id] = meta_text
    
    # Extract Rik text for each subsection
    rik_text_map = {}
    for rt_match in rik_text_pattern.finditer(content):
        # ... existing extraction ...
        sub_id = rt_match.group(1)
        # Sanitize Rik text: remove newlines, carriage returns, backslashes, and literal \newline commands
        rik_text = rt_match.group(2).strip().replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
        rik_text = rik_text.replace('\\newline%', ' ').replace('\\newline', ' ').replace('\\', '')
        rik_text_map[sub_id] = rik_text
    
    # Extract subsection headers (Samam header + metadata)
    subsection_headers = {}
    for sub_match in subsection_pattern.finditer(content):
        sub_id = sub_match.group(1)
        header_line = sub_match.group(2).strip()
        # Split header and saman_metadata (they're separated by double space)
        parts = header_line.split('  ', 1)
        header = parts[0].strip()
        saman_metadata = parts[1].strip() if len(parts) > 1 else ""
        # Normalize pipes
        saman_metadata = saman_metadata.replace('||', '॥').replace('|', '।')
        subsection_headers[sub_id] = {"header": header, "saman_metadata": saman_metadata}
    
    # Extract mantra sets
    mantra_sets_map = {}
    for m_match in mantra_pattern.finditer(content):
        sub_id = m_match.group(1)
        mantra_text = m_match.group(2).strip()
        # Sanitize invisible characters that break footnote pattern matching
        mantra_text = sanitize_invisible_chars(mantra_text)
        # Parse mantras - each line is part of the mantra content
        mantras = [sanitize_invisible_chars(line) for line in mantra_text.split('\n') if line.strip()]
        mantra_sets_map[sub_id] = mantras
    
    # Extract footnotes
    # Extract footnotes
    footnote_pattern = re.compile(
        r'# Start of Footnote -- (\S+) ## DO NOT EDIT\s*\n(.*?)\s*\n# End of Footnote',
        re.MULTILINE | re.DOTALL
    )
    footnotes_map = {}
    for fn_match in footnote_pattern.finditer(content):
        sub_id = fn_match.group(1)
        footnote_text = fn_match.group(2).strip()
        # Parse footnotes: "s1 - footnote text" or "s1: footnote text" or "s1 : footnote text"
        footnotes = {}
        for line in footnote_text.split('\n'):
            line = line.strip()
            if not line: continue
            
            # Try to match sN separator text
            # Separator can be - or :
            m_fn = re.match(r'^(s\d+)\s*[-:]\s*(.*)$', line)
            if m_fn:
                key = m_fn.group(1).strip()
                text = m_fn.group(2).strip()
                footnotes[key] = text
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
    
    parser = argparse.ArgumentParser(
        description='Generate JSON for Samhita rendering',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Input Modes:
  initial     - Reads raw text files and combines with external metadata files
                (rishi_devata_chandas_for_rik.txt, sama_rishi_chandas_out.txt, vedic_text.txt)
  correction  - Reads processed Unicode text file with embedded metadata

Examples:
  python generate_json_for_samhita.py corrections_003.txt --input-mode initial
  python generate_json_for_samhita.py Full_Samhita_ip_with_FN.txt --input-mode correction --output output.json
        """
    )
    parser.add_argument('input_file', type=str,
                        help='Input text file to process')
    parser.add_argument('--input-mode', choices=['initial', 'correction'], default='correction',
                        help='Input mode: initial or correction (default: correction)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output JSON file path (default: auto-generated from input filename)')
    
    args = parser.parse_args()
    
    input_file = args.input_file
    
    if args.input_mode == 'initial':
        # Initial mode: use multiple source files
        rik_meta = "rishi_devata_chandas_for_rik.txt"
        saman_meta = "sama_rishi_chandas_out.txt"
        rik_text = "vedic_text.txt"
        
        output_file_path = args.output or (Path(input_file).stem + "_out.json")
        print(f"Processing {input_file} in INITIAL mode...")
        output_data = convert_corrections_to_json(input_file, rik_meta, saman_meta, rik_text)
        
    else:
        # Correction mode: parse Unicode text file
        output_file_path = args.output or (Path(input_file).stem + "_out.json")
        print(f"Processing {input_file} in CORRECTION mode...")
        output_data = parse_unicode_text_file(input_file)
    
    if output_data:
        try:
            with open(output_file_path, 'w', encoding='utf-8') as outfile:
                json.dump(output_data, outfile, indent=4, ensure_ascii=False)
            print(f"Success! Saved to '{output_file_path}'")
        except IOError as e:
            print(f"Error writing to file: {e}")