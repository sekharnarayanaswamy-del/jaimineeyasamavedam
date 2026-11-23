#!/usr/bin/env python3
"""
Build Combined AST for Jaimineeya Samaveda: Samhita + Aranyakam
---------------------------------------------------------------
Combines Samhita (supersections 1-6) and Aranyakam (supersections 7-12)
into a single continuous AST for unified publication.
"""

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def build_combined_ast():
    sam_path = ROOT_DIR / 'data' / 'corpora' / 'samhita' / '02_ast' / 'Samhita_ast.json'
    aar_path = ROOT_DIR / 'data' / 'corpora' / 'aaranam' / '02_ast' / 'Aaranam_ast.json'

    with open(sam_path, encoding='utf-8') as f:
        sam_ast = json.load(f)
    with open(aar_path, encoding='utf-8') as f:
        aar_ast = json.load(f)

    v_sam = sam_ast.get('meta', {}).get('version', '3.34')
    v_aar = aar_ast.get('meta', {}).get('version', '3.28')

    combined_ast = {
        'meta': {
            'version': f"{v_sam}+{v_aar}",
            'generated_at': sam_ast.get('meta', {}).get('generated_at', ''),
            'title': 'जैमिनीयसामवेद-संहितारण्यकम्',
            'description': 'Jaimineeya Sama Samhita and Aranyakam combined Samam edition with associated metadata'
        },
        'supersection': {},
        'closing_mantras': aar_ast.get('closing_mantras', [])
    }

    s_ss = sam_ast.get('supersections') or sam_ast.get('supersection', {})
    a_ss = aar_ast.get('supersections') or aar_ast.get('supersection', {})

    def ss_sort_key(k):
        if '_' in k:
            parts = k.split('_')
            if parts[1].isdigit():
                return int(parts[1])
        return 999

    for k in sorted(s_ss.keys(), key=ss_sort_key):
        if k != 'count':
            combined_ast['supersection'][k] = s_ss[k]

    for k in sorted(a_ss.keys(), key=ss_sort_key):
        if k != 'count':
            combined_ast['supersection'][k] = a_ss[k]

    # Assign contiguous numbering for all individual Samams across Kandah/Parvah/Bhaga boundaries
    # No numbering for Arsheyams (subsections).
    global_samam_count = 0
    DEVA_DIGITS = str.maketrans('0123456789', '०१२३४५६७८९')

    def to_devanagari(n):
        return str(n).translate(DEVA_DIGITS)

    def renumber_samam_match(match):
        nonlocal global_samam_count
        global_samam_count += 1
        dev_num = to_devanagari(global_samam_count)
        return f"॥ {dev_num} ॥"

    def sec_sort_key(k):
        if '_' in k and k.split('_')[1].isdigit():
            return int(k.split('_')[1])
        return 999

    import re

    for ss_key in sorted(combined_ast['supersection'].keys(), key=ss_sort_key):
        ss_data = combined_ast['supersection'][ss_key]
        for sec_key in sorted(ss_data.get('sections', {}).keys(), key=sec_sort_key):
            if sec_key == 'count':
                continue
            sec_data = ss_data['sections'][sec_key]
            for sub_key in sorted(sec_data.get('subsections', {}).keys(), key=sec_sort_key):
                sub_data = sec_data['subsections'][sub_key]

                # Fallback saman_metadata from rik_metadata if absent
                if not sub_data.get('saman_metadata', '').strip() and sub_data.get('rik_metadata', '').strip():
                    sub_data['saman_metadata'] = sub_data['rik_metadata']

                # Renumber individual samams contiguously in corrected-mantra_sets
                if sub_data.get('corrected-mantra_sets'):
                    for m_obj in sub_data['corrected-mantra_sets']:
                        if 'corrected-mantra' in m_obj:
                            m_obj['corrected-mantra'] = re.sub(
                                r'॥\s*[०-९\d]+\s*॥',
                                renumber_samam_match,
                                m_obj['corrected-mantra']
                            )
                elif sub_data.get('mantra_sets'):
                    for m_obj in sub_data['mantra_sets']:
                        if 'mantra' in m_obj:
                            m_obj['mantra'] = re.sub(
                                r'॥\s*[०-९\d]+\s*॥',
                                renumber_samam_match,
                                m_obj['mantra']
                            )

    out_dir = ROOT_DIR / 'data' / 'corpora' / 'samhita_aranyakam' / '02_ast'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / 'Samhita_Aranyakam_ast.json'

    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(combined_ast, f, ensure_ascii=False, indent=2)

    print(f"Successfully generated combined AST: {out_file.relative_to(ROOT_DIR)} ({out_file.stat().st_size:,} bytes)")
    print(f"Total supersections: {len(combined_ast['supersection'])}, Total global Samams: {global_samam_count}")
    print(f"Total supersections: {len(combined_ast['supersection'])}")
    for k, v in combined_ast['supersection'].items():
        print(f"  [{k}] {v.get('supersection_title')}")

    # Also ensure renders directory exists
    (ROOT_DIR / 'data' / 'corpora' / 'samhita_aranyakam' / '05_renders' / 'pdf').mkdir(parents=True, exist_ok=True)
    return out_file

if __name__ == '__main__':
    build_combined_ast()
