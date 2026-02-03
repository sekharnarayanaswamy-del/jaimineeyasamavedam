import json

def get_rik_id(file_path, target_sub):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for ss_id, ss_val in data.get("supersection", {}).items():
            for sec_id, sec_val in ss_val.get("sections", {}).items():
                if target_sub in sec_val.get("subsections", {}):
                    return sec_val["subsections"][target_sub].get("rik_id")
    except:
        return None

r726 = get_rik_id('data/output/Samhita_with_Rishi_Devata_Chandas_out.json', 'subsection_726')
print(f"Subsection 726 Rik ID: {r726}")
