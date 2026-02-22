"""
Generate a Rik-level table listing every unique Rik.
This table contains one row per Rik, avoiding n:1 Samam-to-Rik duplication issues.

Usage:
    python src/generate_rik_table.py [input_json] [-o output_csv]

Examples:
    # Use defaults:
    python src/generate_rik_table.py

    # Specify input file:
    python src/generate_rik_table.py data/output/Samhita_Devanagari_Unicode_out.json

    # Specify both input and output:
    python src/generate_rik_table.py data/output/Samhita_Devanagari_Unicode_out.json -o data/output/My_Rik_Table.csv
"""
import argparse
import json
import csv
import os
import sys

# Add tools directory to path for imports if needed
sys.path.append(os.path.join(os.path.dirname(__file__), 'tools'))
from utils import get_generated_metadata

DEFAULT_INPUT = r'data\output\Samhita_with_Rishi_Devata_Chandas_out.json'
DEFAULT_OUTPUT = r'data\output\JSV_Rik_Table.csv'

def replace_accents_unicode(text):
    """
    Replaces ASCII parenthesis accent markers with actual Unicode accents.
    (1): Swarita (U+0951)
    (2): Anudatta (U+1CD2)
    (3): Kampa (U+1CF8)
    (4): Trikampa (U+1CF9)
    """
    if not text:
        return text
    replacements = [
        ('(1)', '\u0951'),
        ('(2)', '\u1CD2'),
        ('(3)', '\u1CF8'),
        ('(4)', '\u1CF9'),
    ]
    for marker, unicode_val in replacements:
        text = text.replace(marker, unicode_val)
    return text

def main(input_file=None, output_csv=None):
    input_file = input_file or DEFAULT_INPUT
    output_csv = output_csv or DEFAULT_OUTPUT

    # Get metadata
    metadata = get_generated_metadata()
    JSV_VERSION = metadata['version']
    GENERATED_AT = metadata['generated_at']

    print(f"Generating Rik Table (v{JSV_VERSION})...")
    print(f"Input  : {input_file}")
    print(f"Output : {output_csv}")

    # Load the JSON
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # CSV rows
    rows = []

    # Get the supersection container
    supersection_container = data.get('supersection', {})

    # Sort supersection keys numerically
    ss_keys = sorted(supersection_container.keys(), key=lambda x: int(x.split('_')[1]) if '_' in x else 0)

    global_rik_counter = 0

    # Track previous Rik ID to detect changes for Global Rik Num increment
    prev_rik_id_global_context = None

    for ss_key in ss_keys:
        ss_data = supersection_container[ss_key]
        ss_title = ss_data.get('supersection_title', ss_key)
        
        # Get sections
        sections = ss_data.get('sections', {})
        sec_keys = sorted(sections.keys(), key=lambda x: int(x.split('_')[1]) if '_' in x else 0)
        
        for sec_key in sec_keys:
            sec_data = sections[sec_key]
            sec_title = sec_data.get('section_title', sec_key)
            
            # Get subsections (Arsheyams/Riks)
            subsections = sec_data.get('subsections', {})
            sub_keys = sorted(subsections.keys(), key=lambda x: int(x.split('_')[1]) if '_' in x else 0)
            
            for sub_key in sub_keys:
                sub_data = subsections[sub_key]
                
                # Get Rik info
                try:
                    base_rik_id = int(sub_data.get('rik_id', 0))
                except ValueError:
                    base_rik_id = 0
                    
                rik_metadata = sub_data.get('rik_metadata', '')
                rik_text_full = sub_data.get('rik_text', '')
                
                # Split rik text by new line to handle multiple Riks in the same Arsheyam
                rik_lines = [line.strip() for line in rik_text_full.split('\n') if line.strip()]
                
                current_rik_parts = []
                import re
                
                for i, line in enumerate(rik_lines):
                    current_rik_parts.append(line)
                    match = re.search(r'॥\s*([०-९\d]+)\s*॥\s*$', line)
                    is_last_line = (i == len(rik_lines) - 1)
                    
                    # Process the group when we hit a verse number or end of the lines
                    if match or is_last_line:
                        if match:
                            num_str = match.group(1)
                            # convert devanagari to int
                            devanagari_digits = '०१२३४५६७८९'
                            for j, char in enumerate(devanagari_digits):
                                num_str = num_str.replace(char, str(j))
                            try:
                                line_rik_id = int(num_str)
                            except ValueError:
                                line_rik_id = base_rik_id
                        else:
                            line_rik_id = base_rik_id

                        # Combine all lines matching this Rik ID
                        combined_text = ' '.join(current_rik_parts)
                        current_rik_key = (ss_key, sec_key, line_rik_id)
                        
                        # We identify unique Riks by their context (Supersection, Section, Rik_ID)
                        # If this unique key changes, it's a new Rik.
                        if current_rik_key != prev_rik_id_global_context:
                            global_rik_counter += 1
                            prev_rik_id_global_context = current_rik_key
                            
                            # Replace ASCII markers with Unicode accents
                            clean_text = replace_accents_unicode(combined_text)

                            # Add row for this unique Rik
                            rows.append({
                                'Global_Rik_Num': global_rik_counter,
                                'Patha_Name': ss_title,
                                'Khanda': sec_title,
                                'Rik_ID': line_rik_id,
                                'Rik_Text': clean_text,
                                'Rik_Metadata': rik_metadata
                            })
                            
                        # Reset for next Rik group
                        current_rik_parts = []

    # Write CSV with UTF-8 BOM for Excel compatibility
    with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
        # Line 1: <Filename> <Version> <Timestamp>
        filename = os.path.basename(output_csv)
        f.write(f"{filename} {JSV_VERSION} {GENERATED_AT}\n")

        fieldnames = [
            'Global_Rik_Num', 'Patha_Name', 'Khanda', 'Rik_ID', 'Rik_Text', 'Rik_Metadata'
        ]
        
        # Note: If we use DictWriter, we need to handle the header writing carefully
        # if we already wrote a metadata line.
        # But for CSV compliance with standard tools, having a metadata line first is technically breaking the CSV structure
        # for some parsers provided they expect header on line 1.
        # However, the previous script did it, so we follow the pattern.
        
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV saved to: {output_csv}")
    print(f"Total Unique Riks: {len(rows)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a Rik-level table listing every unique Rik."
    )
    parser.add_argument("input", nargs="?", default=DEFAULT_INPUT,
                        help=f"Input JSON file (default: {DEFAULT_INPUT})")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT,
                        help=f"Output CSV file (default: {DEFAULT_OUTPUT})")

    args = parser.parse_args()
    main(input_file=args.input, output_csv=args.output)
