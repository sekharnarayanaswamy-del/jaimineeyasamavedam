import json

def compare_json_content(f1, f2):
    with open(f1, 'r', encoding='utf-8') as h1:
        d1 = json.load(h1)
    with open(f2, 'r', encoding='utf-8') as h2:
        d2 = json.load(h2)
    
    # Check section_2 subsection_1 mantra
    try:
        sub1_d1 = d1['supersection']['supersection_1']['sections']['section_2']['subsections']['subsection_1']['corrected-mantra_sets'][0]['corrected-mantra']
        sub1_d2 = d2['supersection']['supersection_1']['sections']['section_2']['subsections']['subsection_1']['corrected-mantra_sets'][0]['corrected-mantra']
        print(f"Sub1 M1 d1: {sub1_d1[:50]}...")
        print(f"Sub1 M1 d2: {sub1_d2[:50]}...")
    except Exception as e:
        print(f"Diff at Sub1: {e}")

compare_json_content('data/output/prayogamala-ub.json', 'data/output/prayogamala-ubn.json')
