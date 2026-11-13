#!/usr/bin/env python3
"""
Cleanup script to resolve artifacts from previous Sandhi patches:
1. Revert over-patched stobha repetitions in subsection_259 so only the paadanta word is patched.
2. Remove spurious space between makara and opening parenthesis: 'म् (' -> 'म्('.
3. Normalize double space before danda: 'म्  ।' -> 'म् ।' and 'म्  ॥' -> 'म् ॥'.
"""

import re
import json
import shutil
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent

TXT_PATHS = [
    ROOT_DIR / 'data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt',
    ROOT_DIR / 'data/input/Samhita_Devanagari_Unicode.txt'
]

AST_PATHS = [
    ROOT_DIR / 'data/corpora/samhita/02_ast/Samhita_ast.json',
    ROOT_DIR / 'data/output/Samhita_corrected_out.json'
]

def clean_text_content(content: str) -> tuple[str, dict]:
    stats = {'sub259': 0, 'm_paren': 0, 'm_danda': 0}
    
    # 1. Fix subsection_259
    # Target any variation of all 4 हिम्
    pattern_259 = r'हिम्\s*\(ट\)\s*हिम्\s*\(त\)\s*हिम्\s*\(ट\)\s*हिम्\s*\(ख\)'
    if re.search(pattern_259, content):
        content = re.sub(pattern_259, 'हिं(ट) हिं(त) हिं(ट) हिम्(ख)', content)
        stats['sub259'] += 1
        
    # 2. Fix 'म् (' -> 'म्('
    def fix_paren(match):
        stats['m_paren'] += 1
        return match.group(1) + match.group(2)
        
    content = re.sub(r'(\S+म्)\s+(\([^\)]+\))', fix_paren, content)
    
    # 3. Fix 'म्  ।' -> 'म् ।' and 'म्  ॥' -> 'म् ॥'
    def fix_danda(match):
        stats['m_danda'] += 1
        return match.group(1) + ' ' + match.group(2)
        
    content = re.sub(r'(\S+म्)\s{2,}([।॥])', fix_danda, content)
    
    return content, stats

def main():
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    print(f"[INFO] Starting Sandhi Artifact Cleanup ({ts})...")
    
    # Clean Unicode TXT files
    for p in TXT_PATHS:
        if p.exists():
            bak = p.with_suffix(f'.txt.{ts}.bak')
            shutil.copy2(p, bak)
            print(f"[BACKUP] Created {bak.name}")
            
            text = p.read_text(encoding='utf-8')
            cleaned, stats = clean_text_content(text)
            p.write_text(cleaned, encoding='utf-8')
            print(f"[UPDATED] {p.name}: sub259={stats['sub259']}, m_paren={stats['m_paren']}, m_danda={stats['m_danda']}")

    # Clean AST JSON files
    for p in AST_PATHS:
        if p.exists():
            bak = p.with_suffix(f'.json.{ts}.bak')
            shutil.copy2(p, bak)
            print(f"[BACKUP] Created {bak.name}")
            
            text = p.read_text(encoding='utf-8')
            cleaned, stats = clean_text_content(text)
            p.write_text(cleaned, encoding='utf-8')
            print(f"[UPDATED] {p.name}: sub259={stats['sub259']}, m_paren={stats['m_paren']}, m_danda={stats['m_danda']}")

    print("[SUCCESS] Cleanup completed successfully.")

if __name__ == '__main__':
    main()

