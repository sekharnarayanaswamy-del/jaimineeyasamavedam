import re

input_file = r"c:\Users\sekha\OneDrive\Documents\GitHub\jaimineeyasamavedam\data\input\Sooktam.txt"

with open(input_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

def int_to_devanagari(n):
    mapping = {'0':'०', '1':'१', '2':'२', '3':'३', '4':'४', 
               '5':'५', '6':'६', '7':'७', '8':'८', '9':'९'}
    return "".join(mapping[c] for c in str(n))

section_samam_count = {}
current_sec = None
in_mantra_set_count = False

for line in lines:
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

final_lines = []
in_subsection_title = False
in_section_title = False
current_title_section = None

for line in lines:
    # Handle subsection title cleanup
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

    # Handle section title count
    if '# Start of Section Title' in line:
        in_section_title = True
        m = re.search(r'(?<!super)(?<!sub)section_\d+', line)
        if m:
            current_title_section = m.group(0)
    elif '# End of Section Title' in line:
        in_section_title = False
        current_title_section = None
    elif in_section_title and current_title_section and line.strip():
        count = section_samam_count.get(current_title_section, 0)
        if count > 0:
            dev_count = int_to_devanagari(count)
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
                    line = f"{prefix}॥ {inner} ॥              ({dev_count})\n"

    final_lines.append(line)

with open('temp_output.txt', 'w', encoding='utf-8') as fh:
    for i in range(45):
        if "subsection" in lines[i] or "section" in lines[i] or "॥" in lines[i]:
            fh.write(final_lines[i])
