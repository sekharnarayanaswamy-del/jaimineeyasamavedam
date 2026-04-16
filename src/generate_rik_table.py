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

from utils import get_generated_metadata

# Try to import openpyxl for Excel handling
try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

DEFAULT_INPUT = r'data\output\Samhita_corrected_out.json'
DEFAULT_OUTPUT_CSV = r'data\output\JSV_Rik_Table.csv'
DEFAULT_RECON_EXCEL = r'data\output\Rik Reconciliation table (JSV-KSV).xlsx'
DEFAULT_VARGEEKARAN_JSON = r'data\output\Vargeekaran.json'

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

def load_reconciliation_data(excel_path):
    """Load Rishi, Chandas, Devata mapping from Excel."""
    mapping = {} # Global_Rik_Num -> (Rishi, Chandas, Devata)
    if not excel_path or not os.path.exists(excel_path):
        print(f"[WARNING] Reconciliation Excel not found at: {excel_path}")
        return mapping
    
    if not HAS_OPENPYXL:
        print("[ERROR] 'openpyxl' is required to read Excel files. Please install it.")
        return mapping

    print(f"Loading reconciliation data from {excel_path}...")
    try:
        wb = openpyxl.load_workbook(excel_path, data_only=True)
        ws = wb.active
        
        # We expect: 
        # Column A: Global_Rik_Num (Index 0)
        # Column I: Rishi (Index 8)
        # Column J: Chandas (Index 9)
        # Column K: Devata (Index 10)
        
        row_count = 0
        # Data starts from row 3 (Row 1: Metadata, Row 2: Headers)
        for row in ws.iter_rows(min_row=3, values_only=True):
            if not row or len(row) < 11:
                continue
            
            try:
                # Row index 0 is Column A
                if row[0] is not None:
                    # Handle both integer and string (in case Excel formatted it weirdly)
                    rik_num = int(row[0])
                    # Row index 8 is I (Rishi), 9 is J (Chandas), 10 is K (Devata)
                    rishi = str(row[8]).strip() if row[8] is not None else ""
                    chandas = str(row[9]).strip() if row[9] is not None else ""
                    devata = str(row[10]).strip() if row[10] is not None else ""
                    
                    mapping[rik_num] = {
                        "rishi": rishi,
                        "chandas": chandas,
                        "devata": devata
                    }
                    row_count += 1
            except (ValueError, TypeError):
                continue
                
        print(f"Successfully loaded {row_count} classification entries from Excel.")
    except Exception as e:
        print(f"[ERROR] Failed to read Excel: {e}")
        
    return mapping

def main(mode='samhita', input_file=None, output_csv=None, recon_excel=None, v_json=None):
    # 0. Load Configuration
    from utils import load_pipeline_config
    pipeline_cfg = load_pipeline_config()
    table_cfg = pipeline_cfg.get('generate_rik_table', {})
    
    # Use the provided mode, or the one from config, or default to 'samhita'
    active_mode = mode or table_cfg.get('default_type') or 'samhita'
    mode_cfg = table_cfg.get(active_mode, {})

    # Priority: Function Args > Mode Config > Root Config > Default Constants
    input_file = input_file or mode_cfg.get('input') or table_cfg.get('input') or DEFAULT_INPUT
    output_csv = output_csv or mode_cfg.get('output_csv') or table_cfg.get('output_csv') or DEFAULT_OUTPUT_CSV
    recon_excel = recon_excel or mode_cfg.get('recon_excel') or table_cfg.get('recon_excel') or DEFAULT_RECON_EXCEL
    v_json = v_json or mode_cfg.get('v_json') or table_cfg.get('v_json') or DEFAULT_VARGEEKARAN_JSON

    # Get metadata
    metadata = get_generated_metadata()
    JSV_VERSION = metadata['version']
    GENERATED_AT = metadata['generated_at']

    print(f"Generating Rik Table (v{JSV_VERSION})...")
    print(f"Input JSON : {input_file}")
    print(f"Output CSV : {output_csv}")
    print(f"Recon Excel: {recon_excel}")
    print(f"V-JSON Out : {v_json}")

    # Load the JSON
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Use cascading metadata if present in JSON, otherwise fallback
    json_meta = data.get('meta', {})
    if json_meta.get('version'):
        JSV_VERSION = json_meta['version']
        print(f"[INFO] Using cascading Version {JSV_VERSION}")
    
    # Always use fresh timestamp for the export
    GENERATED_at = GENERATED_AT

    # Load Excel Reconciliation Data
    recon_data = load_reconciliation_data(recon_excel)

    # CSV rows
    rows = []
    
    # Vargeekaran JSON data
    vargeekaran_data = []

    # Get the supersection container
    supersection_container = data.get('supersection', {})

    # Sort supersection keys numerically
    ss_keys = sorted(supersection_container.keys(), key=lambda x: int(x.split('_')[1]) if '_' in x else 0)

    global_rik_counter = 0
    # Track unique Riks to assign Global_Rik_Num and classification
    # Key: (supersection_key, section_key, rik_id)
    # Value: { 'Global_Rik_Num': ..., 'classification': ... }
    unique_riks = {}
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
                        
                        # Check if we've seen this unique Rik before
                        if current_rik_key not in unique_riks:
                            global_rik_counter += 1
                            classification = recon_data.get(global_rik_counter, {"rishi": "", "chandas": "", "devata": ""})
                            unique_riks[current_rik_key] = {
                                'Global_Rik_Num': global_rik_counter,
                                'classification': classification
                            }
                            
                            # Add row for this unique Rik to the CSV (unique list)
                            # Replace ASCII markers with Unicode accents
                            clean_text = replace_accents_unicode(combined_text)
                            row_entry = {
                                'Global_Rik_Num': global_rik_counter,
                                'Patha_Name': ss_title,
                                'Khanda': sec_title,
                                'Rik_ID': line_rik_id,
                                'Rishi': classification['rishi'],
                                'Chandas': classification['chandas'],
                                'Devata': classification['devata'],
                                'Rik_Text': clean_text,
                                'Rik_Metadata': rik_metadata
                            }
                            rows.append(row_entry)

                        # Always inject into sub_data for Vargeekaran JSON
                        res = unique_riks[current_rik_key]
                        if 'rik_classifications' not in sub_data:
                            sub_data['rik_classifications'] = []
                        
                        sub_data['rik_classifications'].append({
                            "Global_Rik_Num": res['Global_Rik_Num'],
                            "Rishi": res['classification']['rishi'],
                            "Chandas": res['classification']['chandas'],
                            "Devata": res['classification']['devata']
                        })
                            
                        # Reset for next Rik group
                        current_rik_parts = []

    # Write CSV with UTF-8 BOM for Excel compatibility
    with open(output_csv, 'w', encoding='utf-8-sig', newline='') as f:
        # Line 1: <Filename> <Version> <Timestamp>
        filename = os.path.basename(output_csv)
        f.write(f"{filename} {JSV_VERSION} {GENERATED_AT}\n")

        fieldnames = [
            'Global_Rik_Num', 'Patha_Name', 'Khanda', 'Rik_ID', 'Rishi', 'Chandas', 'Devata', 'Rik_Text', 'Rik_Metadata'
        ]
        
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV saved to: {output_csv}")
    
    # Write Enhanced Vargeekaran JSON (Full Samhita structure with injected info)
    with open(v_json, 'w', encoding='utf-8') as f:
        # Update meta if needed or keep original
        if 'meta' not in data:
            data['meta'] = {}
        data['meta']['description'] = "Enhanced Samhita with Rishi, Devata, Chandas classification"
        data['meta']['generated_at'] = GENERATED_AT
        data['meta']['version'] = JSV_VERSION

        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Vargeekaran JSON saved to: {v_json}")
    
    print(f"Total Unique Riks: {len(rows)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a Rik-level table listing every unique Rik."
    )
    parser.add_argument("--type", choices=["samhita", "aaranam"],
                        help="Mode of operation: 'samhita' (default) or 'aaranam'")
    parser.add_argument("input", nargs="?",
                        help="Override Input JSON file")
    parser.add_argument("-o", "--output",
                        help="Override Output CSV file")
    parser.add_argument("-e", "--excel",
                        help="Override Reconciliation Excel file")
    parser.add_argument("-j", "--json_out",
                        help="Override Output Vargeekaran JSON file")

    args = parser.parse_args()
    main(mode=args.type, input_file=args.input, output_csv=args.output, recon_excel=args.excel, v_json=args.json_out)
