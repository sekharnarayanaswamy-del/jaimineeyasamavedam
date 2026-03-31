import json
import sys

def compare_json(f1, f2):
    with open(f1, 'r', encoding='utf-8') as h1:
        d1 = json.load(h1)
    with open(f2, 'r', encoding='utf-8') as h2:
        d2 = json.load(h2)
    
    ss1 = d1['supersection'].get('supersection_1', {}).get('sections', {})
    ss2 = d2['supersection'].get('supersection_1', {}).get('sections', {})
    
    for k in sorted(ss1.keys()):
        if k == 'count': continue
        v1 = ss1[k]
        v2 = ss2.get(k, {})
        print(f"{k}: {len(v1.get('subsections', {}))} vs {len(v2.get('subsections', {}))}")
        
compare_json('data/output/prayogamala-ub.json', 'data/output/prayogamala-ubn.json')
