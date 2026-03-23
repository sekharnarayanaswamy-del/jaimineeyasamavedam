"""
Script to renumber all supersections, sections, and subsections in Sooktam.txt
sequentially starting from 1.
Uses line-by-line processing with regex to avoid encoding/matching issues.
"""
import re
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description="Renumber supersections, sections, subsets, and samams in a text file.")
parser.add_argument('input_file', nargs='?', default=r"c:\Users\sekha\OneDrive\Documents\GitHub\jaimineeyasamavedam\data\input\Sooktam.txt", help="Path to the input text file")
args = parser.parse_args()

input_file = args.input_file

print(f"Processing file: {input_file}")

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

print(f"=== SuperSections: {current_sup} ===")
print(f"=== Sections: {current_sec} ===")
print(f"=== SubSections: {current_sub - 1} ===")

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
print(f"Total: {current_sup} supersections, {current_sec} sections, {current_sub - 1} subsections")
print(f"Total Samams Renumbered: {samam_counter - 1}")
