#!/usr/bin/env python3
"""
Enrich AST with Rik and Samam RDC (Rishi, Devata, Chandas)

1. Rik RDC: Directly re-injected from Rik Reconciliation table (JSV-KSV).xlsx
   with fallback to raw rik_metadata parser.
2. Samam RDC: Derived from saman_metadata using Sandhi compound and
   domain-aware Sanskrit grammatical classification with Padacheda (पदच्छेदः),
   e.g. गोतमो -> गोतमः, भरद्वाजो -> भरद्वाजः, श्रुतर्षिर् -> श्रुतर्षिः.
"""

import sys
import os
import json
import re
from pathlib import Path

# Try to import openpyxl
try:
    import openpyxl
except ImportError:
    print("[ERROR] 'openpyxl' library required.")
    sys.exit(1)

# Sandhi-compound mappings for (Chandas, Devata) in Samam metadata
BASE_COMPOUNDS = {
    # Gayatri
    'गायत्र्यग्निः': ('गायत्री', 'अग्निः'),
    'गायत्रीन्द्रः': ('गायत्री', 'इन्द्रः'),
    'गायत्रीसोमः': ('गायत्री', 'सोमः'),
    'गायत्री सोमः': ('गायत्री', 'सोमः'),
    'गायत्रीन्द्रसूर्यो': ('गायत्री', 'इन्द्रसूर्यौ'),
    'गायत्रीन्द्र पूषणौ': ('गायत्री', 'इन्द्रपूषणौ'),
    'गायत्र्यश्विनौ': ('गायत्री', 'अश्विनौ'),
    # Virad Gayatri / Virad
    'विराड्गात्र्यग्निः': ('विराड्गायत्री', 'अग्निः'),
    'विराड्गात्र्यग्नि': ('विराड्गायत्री', 'अग्निः'),
    'विराड्गायत्र्यग्निः': ('विराड्गायत्री', 'अग्निः'),
    'विराडग्निः': ('विराट्', 'अग्निः'),
    # Brihati
    'बृहत्यग्निः': ('बृहती', 'अग्निः'),
    'वृहत्यग्निः': ('बृहती', 'अग्निः'),
    'ब्रहत्यग्निः': ('बृहती', 'अग्निः'),
    'बुहत्यग्निः': ('बृहती', 'अग्निः'),
    'बृहतीन्द्रः': ('बृहती', 'इन्द्रः'),
    'बृहतीसोमः': ('बृहती', 'सोमः'),
    'बृहती सोमः': ('बृहती', 'सोमः'),
    'वृहती सोमः': ('बृहती', 'सोमः'),
    'महाबृहतीन्द्रः': ('महाबृहती', 'इन्द्रः'),
    'महाबृहत्यग्निः': ('महाबृहती', 'अग्निः'),
    'सतोबृहतीन्द्रः': ('सतोबृहती', 'इन्द्रः'),
    'सतोबृहत्यग्निः': ('सतोबृहती', 'अग्निः'),
    # Anushtubh
    'अनुष्टुबग्निः': ('अनुष्टुप्', 'अग्निः'),
    'अनुष्टबग्निः': ('अनुष्टुप्', 'अग्निः'),
    'अनुष्टुबिन्द्रः': ('अनुष्टुप्', 'इन्द्रः'),
    'अनुष्टुप्सोमः': ('अनुष्टुप्', 'सोमः'),
    'अनुष्टुप् सोमः': ('अनुष्टुप्', 'सोमः'),
    # Trishtubh
    'त्रिष्टुबग्निः': ('त्रिष्टुप्', 'अग्निः'),
    'त्रिष्टुपग्निः': ('त्रिष्टुप्', 'अग्निः'),
    'त्रिष्टुबग्निर्रुद्रः': ('त्रिष्टुप्', 'अग्निरुद्रौ'),
    'त्रिष्टुबग्निर्वैश्वानरः': ('त्रिष्टुप्', 'अग्निर्वैश्वानरः'),
    'त्रिष्टुबिन्द्रः': ('त्रिष्टुप्', 'इन्द्रः'),
    'त्रिष्टुप्सोमः': ('त्रिष्टुप्', 'सोमः'),
    'त्रिष्टुप् सोमः': ('त्रिष्टुप्', 'सोमः'),
    'त्रिष्टुप्पूषा': ('त्रिष्टुप्', 'पूषा'),
    # Ushnik
    'उष्णिगग्निः': ('उष्णिक्', 'अग्निः'),
    'उष्णिगिन्द्रः': ('उष्णिक्', 'इन्द्रः'),
    'उष्णिक् सोमः': ('उष्णिक्', 'सोमः'),
    'उष्णिक्सोमः': ('उष्णिक्', 'सोमः'),
    # Pankti
    'पङ्क्तिरग्निः': ('पङ्क्तिः', 'अग्निः'),
    'पङ्क्तिरिन्द्रः': ('पङ्क्तिः', 'इन्द्रः'),
    'पङ्क्तिः सोमः': ('पङ्क्तिः', 'सोमः'),
    'पङ्क्तिस्सोमः': ('पङ्क्तिः', 'सोमः'),
    'पङ्क्तिसोमः': ('पङ्क्तिः', 'सोमः'),
    # Jagati
    'जगत्यग्निः': ('जगती', 'अग्निः'),
    'जगतीन्द्रः': ('जगती', 'इन्द्रः'),
    'जगती सोमः': ('जगती', 'सोमः'),
    # Kakubh
    'ककुबग्निः': ('ककुप्', 'अग्निः'),
    'ककुबिन्द्रः': ('ककुप्', 'इन्द्रः'),
    'ककुप्सोमः': ('ककुप्', 'सोमः'),
    'ककुप् सोमः': ('ककुप्', 'सोमः'),
}

# Expand with Sandhi purvarupa (ऽ) and rutva (र-) forms
COMPOUNDS = dict(BASE_COMPOUNDS)
for k, v in list(BASE_COMPOUNDS.items()):
    if k.startswith('अ'):
        COMPOUNDS['ऽ' + k[1:]] = v
        COMPOUNDS['र' + k[1:]] = v
    elif k.startswith('उ'):
        COMPOUNDS['ऽ' + k[1:]] = v

STANDALONE_CHANDAS = [
    'गायत्री', 'बृहती', 'वृआती', 'अनुष्टुप्', 'त्रिष्टुप्', 'उष्णिक्',
    'पङ्क्तिः', 'जगती', 'ककुप्', 'विराट्', 'द्विपदा', 'अतिच्छन्दाः',
    'महाबृहती', 'सतोबृहती'
]

STANDALONE_DEVATAS = [
    'अग्निः', 'इन्द्रः', 'सोमः', 'सोमेन्द्रौ', 'इन्द्रसोमौ', 'वायुः', 'सूर्यः', 'मित्रः', 'वरुणः',
    'मित्रावरुणौ', 'विश्वेदेवाः', 'रुद्रः', 'सविता', 'पूषा', 'सरस्वती', 'बृहस्पतिः',
    'ब्रह्मणस्पतिः', 'अश्विनौ', 'वैश्वानरः', 'उषा', 'प्रजापतिः'
]

def load_reconciliation_table(excel_path):
    print(f"[1/4] Loading Reconciliation Table from: {excel_path}...")
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    ws = wb.active
    
    rik_recon = {}
    for row in ws.iter_rows(min_row=3, values_only=True):
        if not row or row[0] is None:
            continue
        try:
            grn = int(row[0])
            rishi = str(row[8]).strip() if (row[8] is not None and str(row[8]).strip().lower() != 'none') else ""
            chandas = str(row[9]).strip() if (row[9] is not None and str(row[9]).strip().lower() != 'none') else ""
            devata = str(row[10]).strip() if (row[10] is not None and str(row[10]).strip().lower() != 'none') else ""
            meta = str(row[5]).strip() if (len(row) > 5 and row[5] is not None and str(row[5]).strip().lower() != 'none') else ""
            rik_recon[grn] = {
                'rishi': rishi,
                'chandas': chandas,
                'devata': devata,
                'metadata': meta
            }
        except (ValueError, TypeError):
            continue
            
    print(f"      Loaded {len(rik_recon)} Rik classifications.")
    return rik_recon

def parse_raw_rik_metadata(meta_str):
    if not meta_str:
        return {'rishi': '', 'chandas': '', 'devata': ''}
    clean = re.sub(r'^[।॥\s]+|[।॥\s]+$', '', meta_str).strip()
    words = clean.split()
    chandas = ""
    devata = ""
    rishi = ""
    if len(words) >= 3:
        chandas = words[-1]
        devata = words[-2]
        rishi = ' '.join(words[:-2])
    elif len(words) == 2:
        chandas = words[-1]
        devata = words[0]
    return {'rishi': rishi, 'chandas': chandas, 'devata': devata}

# --- Padacheda Helpers ---

def clean_scope(text):
    """Detach scope prefixes (द्वयोः, त्रयाणां, etc.) and resolve sandhi at boundary"""
    text = re.sub(r'^द्वयोरि', 'इ', text)
    text = re.sub(r'^द्वयोरा', 'आ', text)
    text = re.sub(r'^द्वयोरु', 'उ', text)
    text = re.sub(r'^द्वयोरे', 'ए', text)
    text = re.sub(r'^द्वयोरग्नि', 'अग्नि', text)
    text = re.sub(r'^द्वयोरसि', 'असि', text)
    text = re.sub(r'^द्वयोरत्र', 'अत्र', text)
    text = re.sub(r'^द्वयोर्', '', text)
    text = re.sub(r'^द्वयोः\s*', '', text)
    text = re.sub(r'^त्रयाणामि', 'इ', text)
    text = re.sub(r'^त्रयाणाम्', '', text)
    text = re.sub(r'^त्रयाणां\s*', '', text)
    text = re.sub(r'^चतुर्णां\s*', '', text)
    return text.strip()

def padacheda_word(w):
    """
    Apply Pada-cheda (पदच्छेदः) to restore Visarga:
    गोतमो -> गोतमः
    भरद्वाजो -> भरद्वाजः
    श्रुतर्षिर् -> श्रुतर्षिः
    भरद्वाजस् -> भरद्वाजः
    """
    if not w:
        return ''
    # Ends in -o from masculine a-stem: o -> aḥ (ः)
    if w.endswith('ो'):
        return w[:-1] + 'ः'
    # Ends in rutva/satva halanta: -r, -s, -ś, -ṣ -> ः
    if w.endswith('र्') or w.endswith('स्') or w.endswith('श्') or w.endswith('ष्'):
        return w[:-2] + 'ः'
    # Bare consonant r after i/u/ri
    if len(w) > 2 and w.endswith('र') and w[-2] in 'िुृ':
        return w[:-1] + 'ः'
    # Known nominal stems lacking visarga in raw chant notes
    if w in ['प्रजापति', 'अगस्त्य', 'इन्द्र', 'वत्स', 'कण्व', 'कुत्स', 'सोम', 'अग्नि', 'सूर्य', 'मित्र', 'वरुण', 'रुद्र']:
        return w + 'ः'
    return w

def padacheda_phrase(phrase):
    """Apply Pada-cheda across all words of a phrase"""
    if not phrase:
        return ''
    phrase = clean_scope(phrase)
    words = phrase.split()
    return ' '.join(padacheda_word(w) for w in words)

def parse_single_saman_clause(clause, default_c="", default_d=""):
    """Parse a single Samam metadata clause with compound decomposition and Padacheda."""
    c_clean = re.sub(r'[।॥]', ' ', clause).strip()
    c_clean = re.sub(r'\s+', ' ', c_clean)
    if not c_clean:
        return None
        
    rishi = ""
    chandas = ""
    devata = ""
    
    # Check compounds (sorted by length descending for greedy match)
    for comp_k, (ch, dev) in sorted(COMPOUNDS.items(), key=lambda x: len(x[0]), reverse=True):
        if comp_k in c_clean:
            chandas = ch
            devata = dev
            idx = c_clean.find(comp_k)
            r_part = c_clean[:idx].strip()
            # If compound started with 'र' (e.g. रनुष्टुबग्निः from अग्निरनुष्टुबग्निः),
            # the 'र' belongs to the previous word as visarga
            if comp_k.startswith('र'):
                r_part = r_part + 'ः'
            rishi = padacheda_phrase(r_part)
            break
            
    if not (chandas and devata):
        words = c_clean.split()
        if words:
            for d in STANDALONE_DEVATAS:
                d_stem = d.replace('ः', '')
                if words[-1] in [d, d_stem, d_stem + 'ो', d_stem + 'ा']:
                    devata = d
                    words_rem = words[:-1]
                    if words_rem:
                        for ch in STANDALONE_CHANDAS:
                            if words_rem[-1] == ch:
                                chandas = ch
                                words_rem = words_rem[:-1]
                                break
                    rishi = padacheda_phrase(' '.join(words_rem))
                    break

    if not rishi and not chandas and not devata:
        if 'वा' in c_clean or '(' in clause:
            return None
        rishi = padacheda_phrase(c_clean)
        
    if not chandas:
        chandas = default_c
    if not devata:
        devata = default_d
        
    if rishi or chandas or devata:
        return {'rishi': rishi.strip(), 'chandas': chandas.strip(), 'devata': devata.strip()}
    return None

def extract_multi_saman_rdc(meta_str, default_chandas="", default_devata=""):
    """
    Extract and derive Samam RDC list from saman_metadata with complete Padacheda.
    Handles multi-chant subsections returning a list of dicts.
    """
    if not meta_str:
        return [{'rishi': '', 'chandas': default_chandas, 'devata': default_devata}]
        
    raw = re.sub(r'^[।॥\s]+|[।॥\s]+$', '', meta_str).strip()
    clauses = [c.strip() for c in re.split(r'\s*।।\s*', raw) if c.strip() and not re.match(r'^[।॥\s]+$', c)]
    if not clauses:
        return [{'rishi': '', 'chandas': default_chandas, 'devata': default_devata}]
        
    results = []
    for c in clauses:
        parsed = parse_single_saman_clause(c, default_c=default_chandas, default_d=default_devata)
        if parsed and (parsed['rishi'] or parsed['devata'] or parsed['chandas']):
            results.append(parsed)
            
    if not results:
        results.append({
            'rishi': padacheda_phrase(clauses[0]),
            'chandas': default_chandas,
            'devata': default_devata
        })
        
    return results

def enrich_ast(ast, rik_recon):
    unique_riks = {}
    excel_pointer = 0
    total_subs = 0
    
    for ss_key, ss_data in ast.get('supersection', {}).items():
        for sec_key, sec_data in ss_data.get('sections', {}).items():
            for sub_key, sub_data in sec_data.get('subsections', {}).items():
                total_subs += 1
                rik_id = sub_data.get('rik_id', 0)
                rik_key = (ss_key, sec_key, rik_id)
                
                if rik_key not in unique_riks:
                    excel_pointer += 1
                    unique_riks[rik_key] = excel_pointer
                    
                curr_grn = unique_riks[rik_key]
                r_info = rik_recon.get(curr_grn, {})
                
                r_rishi = r_info.get('rishi', '')
                r_chandas = r_info.get('chandas', '')
                r_devata = r_info.get('devata', '')
                
                # Fallback to raw string parser if cell was empty
                if not r_rishi or not r_chandas or not r_devata:
                    fallback = parse_raw_rik_metadata(sub_data.get('rik_metadata', ''))
                    if not r_rishi: r_rishi = fallback['rishi']
                    if not r_chandas: r_chandas = fallback['chandas']
                    if not r_devata: r_devata = fallback['devata']
                    
                sub_data['rik_rishi'] = r_rishi
                sub_data['rik_chandas'] = r_chandas
                sub_data['rik_devata'] = r_devata
                
                # Update / ensure rik_classifications
                sub_data['rik_classifications'] = [{
                    "Global_Rik_Num": curr_grn,
                    "Rik_ID": rik_id,
                    "Rishi": r_rishi,
                    "Chandas": r_chandas,
                    "Devata": r_devata,
                    "Rik_Metadata": sub_data.get('rik_metadata', '')
                }]
                
                # Samam RDC with Padacheda (array format for multiple chants)
                sm = sub_data.get('saman_metadata', '')
                s_list = extract_multi_saman_rdc(
                    sm,
                    default_chandas=sub_data['rik_chandas'],
                    default_devata=sub_data['rik_devata']
                )
                sub_data['saman_rishi'] = [item['rishi'] for item in s_list]
                sub_data['saman_chandas'] = [item['chandas'] for item in s_list]
                sub_data['saman_devata'] = [item['devata'] for item in s_list]
                
    return total_subs

def main():
    repo_root = Path(__file__).resolve().parents[2]
    recon_path = repo_root / "data" / "output" / "Rik Reconciliation table (JSV-KSV).xlsx"
    ast_primary = repo_root / "data" / "corpora" / "samhita" / "02_ast" / "Samhita_ast.json"
    
    if not recon_path.exists():
        print(f"[ERROR] Recon table not found: {recon_path}")
        sys.exit(1)
        
    rik_recon = load_reconciliation_table(str(recon_path))
    
    print(f"[2/4] Enriching AST with Padacheda: {ast_primary}...")
    with open(ast_primary, 'r', encoding='utf-8') as f:
        ast = json.load(f)
        
    total_subs = enrich_ast(ast, rik_recon)
    
    # Save canonical enriched AST
    print(f"[3/4] Saving canonical enriched AST file...")
    with open(ast_primary, 'w', encoding='utf-8') as f:
        json.dump(ast, f, ensure_ascii=False, indent=2)
    print(f"      Saved: {ast_primary}")
    
    print(f"[4/4] Verifying Population Statistics across {total_subs} subsections...")
    has_rr = sum(1 for ss in ast['supersection'].values() for sec in ss['sections'].values() for sub in sec['subsections'].values() if sub.get('rik_rishi'))
    has_rc = sum(1 for ss in ast['supersection'].values() for sec in ss['sections'].values() for sub in sec['subsections'].values() if sub.get('rik_chandas'))
    has_rd = sum(1 for ss in ast['supersection'].values() for sec in ss['sections'].values() for sub in sec['subsections'].values() if sub.get('rik_devata'))

    has_sr = sum(1 for ss in ast['supersection'].values() for sec in ss['sections'].values() for sub in sec['subsections'].values() if sub.get('saman_rishi'))
    has_sc = sum(1 for ss in ast['supersection'].values() for sec in ss['sections'].values() for sub in sec['subsections'].values() if sub.get('saman_chandas'))
    has_sd = sum(1 for ss in ast['supersection'].values() for sec in ss['sections'].values() for sub in sec['subsections'].values() if sub.get('saman_devata'))

    print("=" * 60)
    print("॥ RDC PADACHEDA ENRICHMENT SUMMARY ॥")
    print("=" * 60)
    print(f"Total Subsections: {total_subs}")
    print(f"  Rik Rishi:     {has_rr} / {total_subs} ({has_rr/total_subs*100:.1f}%)")
    print(f"  Rik Chandas:   {has_rc} / {total_subs} ({has_rc/total_subs*100:.1f}%)")
    print(f"  Rik Devata:    {has_rd} / {total_subs} ({has_rd/total_subs*100:.1f}%)")
    print(f"  Samam Rishi:   {has_sr} / {total_subs} ({has_sr/total_subs*100:.1f}%)")
    print(f"  Samam Chandas: {has_sc} / {total_subs} ({has_sc/total_subs*100:.1f}%)")
    print(f"  Samam Devata:  {has_sd} / {total_subs} ({has_sd/total_subs*100:.1f}%)")
    print("=" * 60)
    print("SUCCESS: Pada-cheda applied across all Samam RDC entries.")

if __name__ == "__main__":
    main()
