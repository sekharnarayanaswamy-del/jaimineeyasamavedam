import json
import csv

try:
    with open('data/output/Samhita_with_Rishi_Devata_Chandas_out.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        sub7 = data['supersection']['supersection_1']['sections']['section_1']['subsections']['subsection_7']
        print(f"JSON subsection_7 Rik ID: {sub7.get('rik_id')}")
        print(f"JSON subsection_7 Rik Metadata: {sub7.get('rik_metadata')}")
except Exception as e:
    print(f"JSON Read Error: {e}")

try:
    with open('data/output/JSV_Samam_Granular_Table.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        found = False
        for row in reader:
            if row.get('Arsheyam_Num') == '7':
                print(f"CSV Arsheyam_Num 7 Found at Global_Samam_Num {row.get('Global_Samam_Num')}")
                print(f"CSV Rik ID: {row.get('Rik_ID')}")
                print(f"CSV Rik Metadata: {row.get('Rik_Metadata')}")
                found = True
                break
        if not found:
            print("CSV Arsheyam_Num 7 NOT FOUND")
except Exception as e:
    print(f"CSV Read Error: {e}")
