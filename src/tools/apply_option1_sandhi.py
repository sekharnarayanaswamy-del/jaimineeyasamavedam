#!/usr/bin/env python3
"""
Apply Option 1: Complete Continuous Sandhi across the entire Samhita:
1. Rik Metadata:
   Combines [Rishi], [Devata], and [Chandas] into continuous Paninian Sandhi.
   E.g.: ।। भारद्वाजो बार्हस्पत्यः । अग्निः । गायत्री ।। -> ।। भारद्वाजो बार्हस्पत्योऽग्निर्गायत्री ।।
2. Sāmam Metadata:
   Removes single dandas (।) inserted in Option 2, ensuring clean continuous flow.
   E.g.: ।। सूर्यो । गायत्री । सूर्यः ।। -> ।। सूर्यो गायत्री सूर्यः ।।
         ।। श्नौष्टम् । श्नुष्टो गायत्र्यग्निः ।। -> ।। श्नौष्टम् श्नुष्टो गायत्र्यग्निः ।।
         ।। देवाः । ककुप् । सोमः ।। -> ।। देवाः ककुप्सोमः ।।
"""

import sys
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.sanskrit_sandhi import combine_rishi_devata_chandas
from src.tools.apply_metadata_dandas import parse_single_rik_block

def format_rik_metadata_option1(raw_text: str) -> str:
    """Converts a Rik metadata block into Option 1 continuous Sandhi."""
    inner_blocks = [b.strip() for b in re.split(r'\s*।।\s*', raw_text) if b.strip()]
    if not inner_blocks:
        return raw_text
        
    sandhi_blocks = []
    for b in inner_blocks:
        # Strip any existing single or double dandas
        clean_b = re.sub(r'\s*[।॥]+\s*', ' ', b).strip()
        parts = parse_single_rik_block(clean_b)
        if parts:
            sandhi_text = combine_rishi_devata_chandas(parts)
            sandhi_blocks.append(sandhi_text)
        else:
            # Fallback: clean danda removal
            sandhi_blocks.append(clean_b)
            
    return "।। " + " ।। ।। ".join(sandhi_blocks) + " ।।"

def format_samam_metadata_option1(raw_text: str) -> str:
    """Removes single dandas from Samam metadata, ensuring continuous flow."""
    if not raw_text.strip():
        return raw_text
        
    # Split by double dandas
    inner_blocks = [b.strip() for b in re.split(r'\s*।।\s*', raw_text) if b.strip()]
    if not inner_blocks:
        return raw_text
        
    single_danda_re = re.compile(r'(?<!\u0964)\u0964(?!\u0964)')
    new_blocks = []
    for b in inner_blocks:
        # Remove single dandas
        cleaned = single_danda_re.sub('', b)
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Apply specific continuous sandhi combinations where applicable:
        # ककुप् सोमः -> ककुप्सोमः
        cleaned = re.sub(r'ककुप्\s+सोमः', 'ककुप्सोमः', cleaned)
        # ककुप् इन्द्रसोमौ -> ककुबिन्द्रसोमौ
        cleaned = re.sub(r'ककुप्\s+इन्द्रसोमौ', 'ककुबिन्द्रसोमौ', cleaned)
        # उष्णिक् इन्द्रः -> उष्णिगिन्द्रः
        cleaned = re.sub(r'उष्णिक्\s+इन्द्रः', 'उष्णिगिन्द्रः', cleaned)
        
        new_blocks.append(cleaned)
        
    return "।। " + " ।। ।। ".join(new_blocks) + " ।।"

def process_corpus_file(file_path: Path, dry_run=False):
    print(f"Processing: {file_path}")
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
        
        new_meta = format_rik_metadata_option1(meta_body)
        if new_meta != meta_body:
            rik_changes += 1
        return f"{prefix}{new_meta}{suffix}"
        
    content_new = rik_meta_pat.sub(repl_rik, content)
    
    # 2. Process SubSection Title blocks (Sāmam Metadata)
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
            new_saman_meta = format_samam_metadata_option1(saman_meta)
            if new_saman_meta != saman_meta:
                samam_changes += 1
            return f"{prefix}{hdr}  {new_saman_meta}{suffix}"
        return match.group(0)
        
    content_new = sub_title_pat.sub(repl_sub, content_new)
    
    print(f"  Rik metadata blocks modified:   {rik_changes}")
    print(f"  Samam metadata blocks modified: {samam_changes}")
    
    if not dry_run:
        file_path.write_text(content_new, encoding='utf-8')
        print(f"  Successfully written changes to {file_path}")

if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv
    p1 = ROOT_DIR / 'data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt'
    p2 = ROOT_DIR / 'data/input/Samhita_Devanagari_Unicode.txt'
    
    process_corpus_file(p1, dry_run=dry_run)
    if not dry_run and p2.exists():
        process_corpus_file(p2, dry_run=dry_run)
