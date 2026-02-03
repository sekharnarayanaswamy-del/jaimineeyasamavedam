import json
import sys

def find_subsection(file_path, target_sub, output_file):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for ss_id, ss_val in data.get("supersection", {}).items():
            for sec_id, sec_val in ss_val.get("sections", {}).items():
                if target_sub in sec_val.get("subsections", {}):
                    output_file.write(f"FOUND in {file_path} at {ss_id} -> {sec_id}:\n")
                    output_file.write(json.dumps(sec_val["subsections"][target_sub], ensure_ascii=False, indent=2))
                    output_file.write("\n\n")
                    return
        output_file.write(f"NOT FOUND {target_sub} in {file_path}\n\n")
    except Exception as e:
        output_file.write(f"Error reading {file_path}: {e}\n\n")

with open('temp_debug_output.txt', 'w', encoding='utf-8') as f:
    f.write("--- Checking Samhita Output ---\n")
    find_subsection('data/output/Samhita_with_Rishi_Devata_Chandas_out.json', 'subsection_727', f)

    f.write("\n--- Checking Agneyam Output ---\n")
    find_subsection('data/output/Agneyam-Pavamanam_latest_out.json', 'subsection_727', f)
