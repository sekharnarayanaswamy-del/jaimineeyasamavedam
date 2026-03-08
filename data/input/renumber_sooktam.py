"""
Script to renumber all supersections, sections, and subsections in Sooktam.txt
sequentially starting from 1.
Uses line-by-line processing with regex to avoid encoding/matching issues.
"""
import re

input_file = r"c:\Users\sekha\OneDrive\Documents\GitHub\jaimineeyasamavedam\data\input\Sooktam.txt"

with open(input_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Pass 1: Collect all unique IDs in order of first appearance
supersection_ids = []
section_ids = []
subsection_ids = []

for line in lines:
    # Find subsection IDs
    for m in re.finditer(r'subsection_(\d+)', line):
        old_id = m.group(1)
        if old_id not in subsection_ids:
            subsection_ids.append(old_id)
    
    # Find section IDs (not super/sub) - use word boundary approach
    # Match "section_" that is NOT preceded by "super" or "sub"
    for m in re.finditer(r'(?<!super)(?<!sub)section_(\d+)', line):
        old_id = m.group(1)
        if old_id not in section_ids:
            section_ids.append(old_id)
    
    # Find supersection IDs
    for m in re.finditer(r'supersection_(\d+)', line):
        old_id = m.group(1)
        if old_id not in supersection_ids:
            supersection_ids.append(old_id)

# Build mappings
supersection_map = {old: str(i+1) for i, old in enumerate(supersection_ids)}
section_map = {old: str(i+1) for i, old in enumerate(section_ids)}
subsection_map = {old: str(i+1) for i, old in enumerate(subsection_ids)}

print(f"=== SuperSections: {len(supersection_map)} ===")
for old, new in supersection_map.items():
    status = "" if old == new else " <-- CHANGED"
    print(f"  supersection_{old} -> supersection_{new}{status}")

print(f"\n=== Sections: {len(section_map)} ===")
for old, new in section_map.items():
    status = "" if old == new else " <-- CHANGED"
    print(f"  section_{old} -> section_{new}{status}")

print(f"\n=== SubSections: {len(subsection_map)} ===")
for old, new in subsection_map.items():
    status = "" if old == new else " <-- CHANGED"
    print(f"  subsection_{old} -> subsection_{new}{status}")

# Pass 2: Replace in each line
# Strategy: Process each line, replace subsection_ first, then section_, then supersection_
# Use a function-based regex replacement to look up the mapping

new_lines = []
for line in lines:
    # Replace subsection_NNN
    def replace_subsection(m):
        old_id = m.group(1)
        new_id = subsection_map.get(old_id, old_id)
        return f'subsection_{new_id}'
    line = re.sub(r'subsection_(\d+)', replace_subsection, line)
    
    # Replace section_NNN (not preceded by super or sub)
    def replace_section(m):
        old_id = m.group(1)
        new_id = section_map.get(old_id, old_id)
        return f'section_{new_id}'
    line = re.sub(r'(?<!super)(?<!sub)section_(\d+)', replace_section, line)
    
    # Replace supersection_NNN
    def replace_supersection(m):
        old_id = m.group(1)
        new_id = supersection_map.get(old_id, old_id)
        return f'supersection_{new_id}'
    line = re.sub(r'supersection_(\d+)', replace_supersection, line)
    
    new_lines.append(line)

def int_to_devanagari(n):
    mapping = {'0':'०', '1':'१', '2':'२', '3':'३', '4':'४', 
               '5':'५', '6':'६', '7':'७', '8':'८', '9':'९'}
    return "".join(mapping[c] for c in str(n))

# Pass 2.5: Count samams per section
section_samam_count = {}
current_sec = None
in_mantra_set_count = False

for line in new_lines:
    if '# Start of Section Title' in line:
        m = re.search(r'(?<!super)(?<!sub)section_\d+', line)
        if m:
            current_sec = m.group(0)
            if current_sec not in section_samam_count:
                section_samam_count[current_sec] = 0

    if '#Start of Mantra Sets' in line or '# Start of Mantra Sets' in line:
        in_mantra_set_count = True
        
    if in_mantra_set_count and current_sec:
        count = len(re.findall(r'(?:॥|\|\|)\s*[०-९\d]+\s*(?:॥|\|\|)', line))
        section_samam_count[current_sec] += count

    if '#End of Mantra Sets' in line or '# End of Mantra Sets' in line:
        in_mantra_set_count = False

# Pass 3: Process text & renumber samams contiguously
final_lines = []
samam_counter = 1
in_mantra_set = False

in_subsection_title = False
in_section_title = False
current_title_section = None

for line in new_lines:
    # Clean up old subsection titles that might have counts
    if '# Start of SubSection Title' in line:
        in_subsection_title = True
    elif '# End of SubSection Title' in line:
        in_subsection_title = False
    elif in_subsection_title and line.strip():
        text = line.strip()
        if text.startswith('॥') and (text.endswith('॥') or text.endswith(')')):
            prefix = line[:line.find('॥')]
            m1 = re.match(r'^॥\s*(.+?)\s*-\s*[०-९]+\s*॥$', text)
            m2 = re.match(r'^॥\s*(.+?)\s*॥\s*\([०-९]+\)$', text)
            
            if m1:
                inner = m1.group(1).strip()
            elif m2:
                inner = m2.group(1).strip()
            elif text.endswith('॥'):
                inner = text[1:-1].strip()
            else:
                inner = None
            
            if inner:
                line = f"{prefix}॥ {inner} ॥\n"

    # Skip updating section title count since it's now handled by generate_json.py

    if '#Start of Mantra Sets' in line or '# Start of Mantra Sets' in line:
        in_mantra_set = True
        
    if in_mantra_set:
        def samam_repl(m):
            global samam_counter
            res = f"॥ {int_to_devanagari(samam_counter)} ॥"
            samam_counter += 1
            return res
            
        line = re.sub(r'(?:॥|\|\|)\s*([०-९\d]+)\s*(?:॥|\|\|)', samam_repl, line)
        
    if '#End of Mantra Sets' in line or '# End of Mantra Sets' in line:
        in_mantra_set = False
        
    final_lines.append(line)

# Write the output
with open(input_file, 'w', encoding='utf-8') as f:
    f.writelines(final_lines)

print(f"\nDone! File updated successfully.")
print(f"Total: {len(supersection_map)} supersections, {len(section_map)} sections, {len(subsection_map)} subsections")
print(f"Total Samams Renumbered: {samam_counter - 1}")
