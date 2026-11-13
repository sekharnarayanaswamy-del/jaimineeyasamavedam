#!/usr/bin/env python3
"""
Apply Option 2 with dandas across the entire Samhita (Rik and Samam metadata).
Rik metadata: [Rishi] । [Devata] । [Chandas]
Samam metadata: standardize internal dandas and separate uncompounded fields.
"""

import re
import sys
from pathlib import Path

# Complete Chandas list for Rik metadata
CHANDAS_LIST = sorted([
    'गायत्री', 'बृहती', 'त्रिष्टुप्', 'अनुष्टुप्', 'जगती', 'उष्णिक्', 'पंक्तिः', 'पङ्क्त्तिः', 'ककुप्', 'ककुप',
    'विराट्', 'विराड्गायत्री', 'सतोबृहती', 'अतिजगति', 'अतिजगती', 'शक्वरी', 'अतिशक्वरी', 'प्रगाथः',
    'द्विपदा विराट्', 'द्विपदाविराट्', 'त्रिपदाविराटगायत्री', 'विराट्गायत्री', 'महापंक्तिः', 'अष्टिपंक्तिः',
    'ककुबुष्णिहा', 'पुरउष्णिक्', 'पादनिचृद्गायत्री', 'स्कन्धोग्रीवी', 'विराट्त्रिष्टुप्',
    'विराडनुष्टुप्', 'पिपीलिकमध्या', 'यवमध्या', 'अत्यष्टिः', 'धृतिः', 'अतिधृतिः', 'पङ्क्तिः', 'बृहति',
    'त्रिपदा अनुष्टुप्पिपीलिकामध्या', 'यवमध्या गायत्री', 'अष्टिः', 'अतिशक्करी', 'त्रिपदा गायत्री',
    'अति जगती', 'एकपदा', 'विराटुष्णिक्', 'पदपङ्क्तिः', 'ऋषिः विराट्'
], key=len, reverse=True)

# Complete Devatas list for Rik metadata
DEVATA_LIST = sorted([
    'अग्निः', 'इन्द्रः', 'पवमानः सोमः', 'सोमः', 'सूर्यः', 'सविता', 'विश्वेदेवाः', 'मरुतः', 'रुद्रः',
    'वायुः', 'मित्रः', 'वरुणः', 'बृहस्पतिः', 'ब्रह्मणस्पतिः', 'सोमेन्द्रौ', 'इन्द्राग्नी', 'श्येनसोमौ',
    'मरुद्वायू', 'उषाः', 'वेनः', 'अश्विनौ', 'पूषा', 'मित्रारुणौ', 'मित्रावरुणौ', 'विश्वकर्मन्',
    'इन्द्रश्च सोमश्च', 'इन्द्रावरुणौ', 'इन्द्राविष्णू', 'सरस्वती', 'वातः', 'आदित्यः', 'आपः',
    'अदितिः', 'आदित्याः', 'यूपः', 'मित्रावरुणादित्याः', 'वाजिनः', 'आपो देवीः', 'इन्द्रासोमौ',
    'द्यावापृथिवी', 'विष्णुः', 'उषा', 'अंगिराः', 'दधिक्रा वा', 'बहुः'
], key=len, reverse=True)

def parse_single_rik_block(clean: str):
    """Parse a single ।। ... ।। block into (rishi, devata, chandas)."""
    chandas_paren = ""
    m_paren = re.search(r'\s*(\([^\)]+\))\s*$', clean)
    base_clean = clean
    if m_paren:
        chandas_paren = " " + m_paren.group(1).strip()
        base_clean = clean[:m_paren.start()].strip()
    
    matched_chandas = None
    remaining = base_clean
    for ch in CHANDAS_LIST:
        if base_clean.endswith(ch):
            matched_chandas = ch + chandas_paren
            remaining = base_clean[:-len(ch)].strip()
            break
            
    devata_paren = ""
    m_dev_paren = re.search(r'\s*(\([^\)]+\))\s*$', remaining)
    base_rem = remaining
    if m_dev_paren:
        devata_paren = " " + m_dev_paren.group(1).strip()
        base_rem = remaining[:m_dev_paren.start()].strip()
        
    matched_devata = None
    rishi = base_rem
    for dev in DEVATA_LIST:
        if base_rem.endswith(dev):
            matched_devata = dev + devata_paren
            rishi = base_rem[:-len(dev)].strip()
            break
            
    parts = []
    if rishi:
        parts.append(rishi)
    if matched_devata:
        parts.append(matched_devata)
    if matched_chandas:
        parts.append(matched_chandas)
        
    return parts

def format_rik_metadata_line(raw_text: str) -> str:
    """Converts a Rik metadata line to Option 2 with dandas."""
    inner_blocks = [b.strip() for b in re.split(r'\s*।।\s*', raw_text) if b.strip()]
    if not inner_blocks:
        return raw_text
    
    reformatted_blocks = []
    for b in inner_blocks:
        # Check if already has single dandas
        if ' । ' in b or '।' in b:
            clean = re.sub(r'\s*।\s*', ' । ', b).strip()
            reformatted_blocks.append(clean)
        else:
            parts = parse_single_rik_block(b)
            if parts:
                reformatted_blocks.append(" । ".join(parts))
            else:
                reformatted_blocks.append(b)
                
    return "।। " + " ।। ।। ".join(reformatted_blocks) + " ।।"

# Meters and Devatas for Samam metadata
SAMAM_METERS = sorted([
    'गायत्री', 'बृहती', 'त्रिष्टुप्', 'अनुष्टुप्', 'जगती', 'उष्णिक्', 'पंक्तिः', 'पङ्क्त्तिः', 'ककुप्', 'ककुप',
    'विराट्', 'विराड्गायत्री', 'सतोबृहती', 'अतिजगति', 'अतिजगती', 'शक्वरी', 'अतिशक्वरी', 'प्रगाथः',
    'द्विपदा विराट्', 'द्विपदाविराट्', 'त्रिपदाविराटगायत्री', 'विराट्गायत्री', 'महापंक्तिः', 'अष्टिपंक्तिः',
    'ककुबुष्णिहा', 'पुरउष्णिक्', 'पादनिचृद्गायत्री', 'स्कन्धोग्रीवी', 'विराट्त्रिष्टुप्',
    'विराडनुष्टुप्', 'पिपीलिकमध्या', 'यवमध्या', 'अत्यष्टिः', 'धृतिः', 'अतिधृतिः', 'पङ्क्तिः', 'बृहति',
    'विराङ्गायत्री', 'पंक्ति'
], key=len, reverse=True)

SAMAM_DEVATAS = sorted([
    'अग्निः', 'इन्द्रः', 'पवमानः सोमः', 'सोमः', 'सूर्यः', 'सविता', 'विश्वेदेवाः', 'मरुतः', 'रुद्रः',
    'वायुः', 'मित्रः', 'वरुणः', 'बृहस्पतिः', 'ब्रह्मणस्पतिः', 'सोमेन्द्रौ', 'इन्द्राग्नी', 'श्येनसोमौ',
    'मरुद्वायू', 'उषाः', 'वेनः', 'अश्विनौ', 'पूषा', 'मित्रारुणौ', 'मित्रावरुणौ', 'विश्वकर्मन्',
    'इन्द्रश्च सोमश्च', 'इन्द्रावरुणौ', 'इन्द्राविष्णू', 'सरस्वती', 'वातः', 'आदित्यः', 'आपः',
    'अदितिः', 'आदित्याः', 'यूपः', 'मित्रावरुणादित्याः', 'वाजिनः', 'आपो देवीः', 'इन्द्रासोमौ',
    'इन्द्रसोमौ', 'सूर्यः इन्द्रो वा'
], key=len, reverse=True)

def format_samam_metadata_block(block: str) -> str:
    """Format a single Samam metadata block (between ।।)."""
    b = block.strip()
    if not b:
        return ""
    
    # Normalize existing danda spacing
    b = re.sub(r'\s*।\s*', ' । ', b).strip()
    
    # Check each danda-separated part to see if it has uncompounded [Rishi] [Chandas] [Devata]
    subparts = b.split(' । ')
    new_subparts = []
    for sp in subparts:
        sp_strip = sp.strip()
        words = sp_strip.split()
        
        # Check if words end with Devata and penultimate is Meter
        if len(words) >= 3:
            matched_dev = None
            matched_meter = None
            
            # Check 2-word devata first (e.g. पवमानः सोमः)
            if len(words) >= 4 and f"{words[-2]} {words[-1]}" in SAMAM_DEVATAS:
                cand_dev = f"{words[-2]} {words[-1]}"
                cand_meter = words[-3]
                if cand_meter in SAMAM_METERS:
                    matched_dev = cand_dev
                    matched_meter = cand_meter
                    rishi_words = words[:-3]
            elif words[-1] in SAMAM_DEVATAS:
                cand_dev = words[-1]
                cand_meter = words[-2]
                if cand_meter in SAMAM_METERS:
                    matched_dev = cand_dev
                    matched_meter = cand_meter
                    rishi_words = words[:-2]
            
            if matched_dev and matched_meter:
                rishi = " ".join(rishi_words)
                new_subparts.extend([rishi, matched_meter, matched_dev])
                continue
                
        # Check if words end with Devata and penultimate ends with compound like -गायत्री or -बृहती
        if len(words) >= 2:
            last = words[-1]
            penult = words[-2]
            if last in SAMAM_DEVATAS and any(penult.endswith(m) for m in ['गायत्री', 'बृहती', 'वृहती', 'बहती', 'जगती', 'उष्णिक्', 'ककुप्']):
                rishi_meter = " ".join(words[:-1])
                new_subparts.extend([rishi_meter, last])
                continue
                
        new_subparts.append(sp_strip)
        
    return " । ".join(new_subparts)

def format_samam_metadata_line(raw_text: str) -> str:
    """Format full Samam metadata line."""
    if not raw_text.strip():
        return raw_text
    
    inner_blocks = [b.strip() for b in re.split(r'\s*।।\s*', raw_text) if b.strip()]
    if not inner_blocks:
        return raw_text
        
    new_blocks = [format_samam_metadata_block(b) for b in inner_blocks]
    return "।। " + " ।। ।। ".join(new_blocks) + " ।।"

def process_unicode_file(file_path: Path, dry_run=False):
    content = file_path.read_text(encoding='utf-8')
    
    # 1. Process Rik Metadata blocks
    rik_meta_pat = re.compile(
        r'(#\s*Start\s+of\s+Rik\s+Metadata\s+--\s+(?:subsection_\d+).*?DO\s+NOT\s+EDIT\s*\n)(.*?)(\n\s*#\s*End\s+of\s+Rik\s+Metadata)',
        re.DOTALL
    )
    
    rik_changes = 0
    def repl_rik(match):
        nonlocal rik_changes
        prefix = match.group(1)
        meta_body = match.group(2).strip()
        suffix = match.group(3)
        
        new_meta = format_rik_metadata_line(meta_body)
        if new_meta != meta_body:
            rik_changes += 1
        return f"{prefix}{new_meta}{suffix}"
        
    content_new = rik_meta_pat.sub(repl_rik, content)
    
    # 2. Process SubSection Title blocks
    sub_title_pat = re.compile(
        r'(#\s*Start\s+of\s+SubSection\s+Title\s+--\s+(?:subsection_\d+).*?DO\s+NOT\s+EDIT\s*\n)(.*?)(\n\s*#\s*End\s+of\s+SubSection\s+Title)',
        re.DOTALL
    )
    
    samam_changes = 0
    def repl_sub(match):
        nonlocal samam_changes
        prefix = match.group(1)
        title_body = match.group(2).strip()
        suffix = match.group(3)
        
        parts = title_body.split('  ', 1)
        if len(parts) > 1:
            hdr = parts[0].strip()
            saman_meta = parts[1].strip()
            new_saman_meta = format_samam_metadata_line(saman_meta)
            if new_saman_meta != saman_meta:
                samam_changes += 1
            return f"{prefix}{hdr}  {new_saman_meta}{suffix}"
        return match.group(0)
        
    content_new = sub_title_pat.sub(repl_sub, content_new)
    
    print(f"Total Rik metadata lines modified: {rik_changes}")
    print(f"Total Samam metadata lines modified: {samam_changes}")
    
    if not dry_run:
        file_path.write_text(content_new, encoding='utf-8')
        print(f"Successfully written changes to {file_path}")

if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv
    p = Path('data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt')
    process_unicode_file(p, dry_run=dry_run)
