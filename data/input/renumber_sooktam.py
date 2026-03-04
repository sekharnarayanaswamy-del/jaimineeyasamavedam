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

# Write the output
with open(input_file, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"\nDone! File updated successfully.")
print(f"Total: {len(supersection_map)} supersections, {len(section_map)} sections, {len(subsection_map)} subsections")
