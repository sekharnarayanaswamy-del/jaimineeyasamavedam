import json
import re
from collections import defaultdict

JSON_FILE = r'data\output\Samhita_with_Rishi_Devata_Chandas_out.json'
OUTPUT_REPORT = r'data\output\JSON_Samam_Continuity_Report.txt'
SAMAM_PATTERN = re.compile(r'(?:॥|\|\|)\s*[\d०-९]+\s*(?:॥|\|\|)')

def extract_samam_numbers(text):
    """Parses Samam numbers from mantra text."""
    matches = SAMAM_PATTERN.findall(text)
    numbers = []
    
    dev_map = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
               '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}
               
    for m in matches:
        # Extract digits
        num_str_match = re.search(r'[\d०-९]+', m)
        if num_str_match:
            num_str = num_str_match.group()
            # Convert to Arabic
            arabic_num = ''.join(dev_map.get(c, c) for c in num_str)
            try:
                numbers.append(int(arabic_num))
            except ValueError:
                pass
    return numbers

def check_json_continuity():
    print(f"Reading JSON: {JSON_FILE}...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    report_lines = []
    report_lines.append("JAIMINEEYA SAMAVEDA SAMHITA - JSON CONTINUITY CHECK")
    report_lines.append("====================================================")
    
    issues_found = False

    # Traverse structure
    supersection_container = data.get('supersection', {})
    # Sort keys
    ss_keys = sorted(supersection_container.keys(), key=lambda x: int(x.split('_')[1]) if '_' in x else 0)

    for ss_key in ss_keys:
        ss_data = supersection_container[ss_key]
        ss_title = ss_data.get('supersection_title', ss_key)
        
        report_lines.append(f"\nPatha: {ss_title} ({ss_key})")
        report_lines.append("-" * 50)
        
        sections = ss_data.get('sections', {})
        sec_keys = sorted(sections.keys(), key=lambda x: int(x.split('_')[1]) if '_' in x else 0)
        
        for sec_key in sec_keys:
            sec_data = sections[sec_key]
            sec_title = sec_data.get('section_title', sec_key)
            
            # Collect all numbers for this section (Khanda)
            khanda_numbers = []
            
            subsections = sec_data.get('subsections', {})
            sub_keys = sorted(subsections.keys(), key=lambda x: int(x.split('_')[1]) if '_' in x else 0)
            
            for sub_key in sub_keys:
                sub_data = subsections[sub_key]
                
                # Check corrected mantras
                mantra_sets = sub_data.get('corrected-mantra_sets', [])
                found_in_sub = False
                for ms in mantra_sets:
                    mantra = ms.get('corrected-mantra', '')
                    nums = extract_samam_numbers(mantra)
                    if nums:
                        khanda_numbers.extend(nums)
                        found_in_sub = True
                
                if not found_in_sub:
                    # Fallback if no numbers found in mantra text?
                    # The granular table logic uses arsheyam number as fallback if no samam markers found.
                    # But continuity check specifically looks for numbers IN the text usually.
                    # Let's see if we should fallback. Interpretation: "The Samam number gets reset when a new Kandah starts."
                    # If text has no numbers, it might be implicitly numbered or missing markers.
                    pass

            # Now validate the sequence for this Khanda
            if not khanda_numbers:
                report_lines.append(f"  {sec_title}: NO SAMAM NUMBERS FOUND")
                issues_found = True
                continue
            
            khanda_numbers.sort()
            
            # 1. Check start
            start_val = khanda_numbers[0]
            if start_val != 1:
                report_lines.append(f"  {sec_title}: Starts at {start_val} (Expected 1)")
                issues_found = True
            
            # 2. Check duplicates
            duplicates = sorted(list(set([x for x in khanda_numbers if khanda_numbers.count(x) > 1])))
            if duplicates:
                report_lines.append(f"  {sec_title}: Duplicates found: {duplicates}")
                issues_found = True
                
            # 3. Check gaps
            expected_set = set(range(1, khanda_numbers[-1] + 1))
            actual_set = set(khanda_numbers)
            missing = sorted(list(expected_set - actual_set))
            
            if missing:
                report_lines.append(f"  {sec_title}: Gaps found! Missing: {missing}")
                issues_found = True
            
            if not missing and not duplicates and start_val == 1:
                # report_lines.append(f"  {sec_title}: OK (1 to {khanda_numbers[-1]})")
                pass

    if not issues_found:
        report_lines.append("\nSUCCESS: All Khandas have contiguous Samam numbering starting from 1.")
    else:
        report_lines.append("\nISSUES FOUND: Please review the list above.")

    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
        
    print(f"Report contents:\n")
    print('\n'.join(report_lines))
    print(f"\nSaved to: {OUTPUT_REPORT}")

if __name__ == "__main__":
    check_json_continuity()
