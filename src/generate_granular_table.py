"""
Generate a fine granular table listing every individual Samam.
Uses the shared samam_utils module for consistent counting.
Output is UTF-8 with BOM for Excel compatibility.
"""
import json
import csv
import re
from samam_utils import SAMAM_PATTERN

INPUT_FILE = r'data\output\Samhita_with_Rishi_Devata_Chandas_out.json'
OUTPUT_CSV = r'data\output\JSV_Samam_Granular_Table.csv'

# Load the JSON
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

# CSV rows
rows = []

# Get the supersection container
supersection_container = data.get('supersection', {})

# Sort supersection keys numerically
ss_keys = sorted(supersection_container.keys(), key=lambda x: int(x.split('_')[1]) if '_' in x else 0)

global_samam_num = 0

for ss_key in ss_keys:
    ss_data = supersection_container[ss_key]
    ss_title = ss_data.get('supersection_title', ss_key)
    patha_num = int(ss_key.split('_')[1]) if '_' in ss_key else 0
    
    # Get sections
    sections = ss_data.get('sections', {})
    sec_keys = sorted(sections.keys(), key=lambda x: int(x.split('_')[1]) if '_' in x else 0)
    
    for sec_key in sec_keys:
        sec_data = sections[sec_key]
        sec_title = sec_data.get('section_title', sec_key)
        
        # Get subsections (Arsheyams)
        subsections = sec_data.get('subsections', {})
        sub_keys = sorted(subsections.keys(), key=lambda x: int(x.split('_')[1]) if '_' in x else 0)
        
        for sub_key in sub_keys:
            sub_data = subsections[sub_key]
            
            # Get Arsheyam header
            header_data = sub_data.get('header', {})
            arsheyam_name = header_data.get('header', '')
            arsheyam_num = header_data.get('header_number', 0)
            
            # Get Rik info
            rik_id = sub_data.get('rik_id', '')
            rik_metadata = sub_data.get('rik_metadata', '')
            
            # Get Saman metadata
            saman_metadata = sub_data.get('saman_metadata', '')
            
            # Get corrected mantra and extract Samam numbers
            mantra_sets = sub_data.get('corrected-mantra_sets', [])
            for ms in mantra_sets:
                mantra = ms.get('corrected-mantra', '')
                
                # Find all Samam numbers in this mantra
                samam_matches = SAMAM_PATTERN.findall(mantra)
                
                if samam_matches:
                    # Extract the number from each match (e.g., "॥1॥" -> "1")
                    for match in samam_matches:
                        # Extract just the number
                        num_match = re.search(r'[\d०-९]+', match)
                        if num_match:
                            samam_num_str = num_match.group()
                            # Convert Devanagari to Arabic if needed
                            dev_map = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
                                      '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}
                            samam_num_arabic = ''.join(dev_map.get(c, c) for c in samam_num_str)
                            samam_num = int(samam_num_arabic)
                            
                            global_samam_num += 1
                            
                            rows.append({
                                'Global_Samam_Num': global_samam_num,
                                'Patha_Num': patha_num,
                                'Patha_Name': ss_title,
                                'Khanda': sec_title,
                                'Samam_Num': samam_num,
                                'Arsheyam_Name': arsheyam_name,
                                'Arsheyam_Num': arsheyam_num,
                                'Rik_ID': rik_id,
                                'Rik_Metadata': rik_metadata,
                                'Saman_Metadata': saman_metadata
                            })
                else:
                    # No Samam markers found - still count this subsection
                    global_samam_num += 1
                    rows.append({
                        'Global_Samam_Num': global_samam_num,
                        'Patha_Num': patha_num,
                        'Patha_Name': ss_title,
                        'Khanda': sec_title,
                        'Samam_Num': arsheyam_num,  # Use arsheyam number as fallback
                        'Arsheyam_Name': arsheyam_name,
                        'Arsheyam_Num': arsheyam_num,
                        'Rik_ID': rik_id,
                        'Rik_Metadata': rik_metadata,
                        'Saman_Metadata': saman_metadata
                    })

# Write CSV with UTF-8 BOM for Excel compatibility
with open(OUTPUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
    fieldnames = ['Global_Samam_Num', 'Patha_Num', 'Patha_Name', 'Khanda', 
                  'Samam_Num', 'Arsheyam_Name', 'Arsheyam_Num', 
                  'Rik_ID', 'Rik_Metadata', 'Saman_Metadata']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"CSV saved to: {OUTPUT_CSV}")
print(f"Total Samam entries: {len(rows)}")

# Summary by Patha
print("\n=== Summary by Patha ===")
from collections import Counter
patha_counts = Counter(r['Patha_Name'] for r in rows)
for patha, count in patha_counts.items():
    print(f"  {patha}: {count}")
