#!/usr/bin/env python3
"""
Sanskrit Sandhi Patch Applicator for Jaimineeya Samaveda Samhita (Swara-Aware).

Applies selected Sandhi corrections chosen via the HTML Audit Portal
or CLI filters to both AST JSON and Unicode raw text.

Features:
- Swara-aware pattern matching: seamlessly replaces Sandhi phonetic irregularities
  in Vedic Rik verses and Sāman chants while preserving parenthetical swaras
  (e.g. (1), (2), (ति), (ता), (प्ली)) and Vedic combining accents intact.
- Safe dry-run preview (--dry-run)
- Automatic timestamped backups (.bak)
- Atomic JSON and Text updates across both corpora and canonical paths
- Detailed Markdown application report
"""

import sys
import json
import re
import difflib
import shutil
import argparse
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

DEFAULT_AST_PATH = ROOT_DIR / 'data/corpora/samhita/02_ast/Samhita_ast.json'
DEFAULT_OUT_AST_PATH = ROOT_DIR / 'data/output/Samhita_corrected_out.json'
DEFAULT_TXT_PATH = ROOT_DIR / 'data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt'
DEFAULT_SYNC_TXT_PATH = ROOT_DIR / 'data/input/Samhita_Devanagari_Unicode.txt'
DEFAULT_FINDINGS_PATH = ROOT_DIR / 'data/corpora/samhita/06_reports/sandhi_audit_findings.json'
DEFAULT_PATCH_PATH = ROOT_DIR / 'data/corpora/samhita/06_reports/sandhi_selected_patch.json'
DEFAULT_REPORT_PATH = ROOT_DIR / 'data/corpora/samhita/06_reports/SANDHI_PATCH_APPLIED_REPORT.md'

def swara_aware_replace(text: str, sus: str, sug: str) -> tuple[str, bool]:
    """
    Replaces a Sandhi irregularity 'sus' with 'sug' in 'text', preserving
    any interspersed Vedic swaras (e.g. (1), (2), (ति), (ता), (प्ली)) and accents.
    """
    if not sus or not sug or not text:
        return text, False
        
    # 1. Direct exact replacement if literal substring exists
    if sus in text:
        return text.replace(sus, sug, 1), True
        
    # 2. Build swara-aware regex matching sus with optional swaras between characters
    swara_unit = r'(?:\([^\)]+\)|[\u1cd0-\u1cf9\u0951\u0952\s])*'
    pattern_parts = []
    for ch in sus.strip():
        if ch in ' ।॥':
            pattern_parts.append(r'[\s।॥]*')
        else:
            pattern_parts.append(re.escape(ch) + swara_unit)
    pattern = ''.join(pattern_parts)
    
    m = re.search(pattern, text)
    if not m:
        return text, False
        
    matched_span = m.group(0)
    matcher = difflib.SequenceMatcher(None, sus, sug)
    opcodes = matcher.get_opcodes()
    new_span = matched_span
    success = False
    
    for tag, i1, i2, j1, j2 in reversed(opcodes):
        if tag in ('replace', 'delete', 'insert'):
            old_chunk = sus[i1:i2]
            new_chunk = sug[j1:j2]
            if old_chunk in new_span:
                new_span = new_span.replace(old_chunk, new_chunk, 1)
                success = True
            elif 'ं' in old_chunk and 'म्' in new_chunk:
                # Anusvara before danda or vowel with intervening swara annotations
                sub_span, n = re.subn(
                    r'([\u0902])(\s*(?:\([^\)]+\)|[\u1cd0-\u1cf9\u0951\u0952])*[\s।॥अआइईउऊऋएऐओऔ])',
                    r'म् \2',
                    new_span,
                    count=1
                )
                if n > 0:
                    new_span = sub_span
                    success = True
            elif 'ः' in old_chunk:
                # Visarga sandhi with intervening space or accent
                sub_span, n = re.subn(
                    r'([^\u093e\u093f\u0940\u0941\u0942\u0943\u0944\u0947\u0948\u094b\u094c\s])ः\s*',
                    r'\1ो ',
                    new_span,
                    count=1
                )
                if n > 0:
                    new_span = sub_span
                    success = True
                    
    if success:
        return text[:m.start()] + new_span + text[m.end():], True
        
    return text, False

def get_subsection_line_range(lines: list[str], sub_key: str) -> tuple[int, int]:
    """Finds the inclusive line range [start, end) for a given subsection in Unicode text."""
    tag = f'-- {sub_key} '
    start_idx = None
    last_tag_idx = None
    for i, line in enumerate(lines):
        if tag in line:
            if start_idx is None:
                start_idx = i
            last_tag_idx = i
    if start_idx is None:
        return None, None
        
    end_idx = len(lines)
    for j in range(last_tag_idx + 1, len(lines)):
        if '-- subsection_' in lines[j] and tag not in lines[j]:
            end_idx = j
            break
    return start_idx, end_idx

def load_patch_items(patch_file: Path = None, findings_file: Path = None, select_high=False, select_headers=False):
    """Loads patch items either from an exported patch JSON or from audit findings based on flags."""
    if patch_file and patch_file.exists():
        print(f"[INFO] Loading patch items from: {patch_file}")
        with open(patch_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict) and 'patch_items' in data:
            return data['patch_items']
        elif isinstance(data, list):
            return data
        else:
            raise ValueError(f"Unrecognized patch file format in {patch_file}")
            
    if select_high or select_headers:
        if not findings_file or not findings_file.exists():
            findings_file = DEFAULT_FINDINGS_PATH
        print(f"[INFO] Selecting patch items from findings: {findings_file}")
        with open(findings_file, 'r', encoding='utf-8') as f:
            findings = json.load(f)
        selected = []
        for f in findings:
            if select_headers and f.get('field') == 'Arsheyam Header':
                selected.append(f)
            elif select_high and f.get('severity') == 'High':
                selected.append(f)
        return selected

    if DEFAULT_PATCH_PATH.exists():
        print(f"[INFO] Loading default patch file: {DEFAULT_PATCH_PATH}")
        with open(DEFAULT_PATCH_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('patch_items', data) if isinstance(data, dict) else data

    raise FileNotFoundError("No patch file specified. Use --patch <file> or --select-high / --select-headers.")

def apply_sandhi_patch(patch_items: list, dry_run: bool = False,
                       ast_path: Path = DEFAULT_AST_PATH,
                       out_ast_path: Path = DEFAULT_OUT_AST_PATH,
                       txt_path: Path = DEFAULT_TXT_PATH,
                       sync_txt_path: Path = DEFAULT_SYNC_TXT_PATH,
                       report_path: Path = DEFAULT_REPORT_PATH):
    """Applies patch items to AST JSON and Unicode text files using swara-aware replacement."""
    
    print(f"[INFO] Processing {len(patch_items)} patch items (dry_run={dry_run})...")
    
    if not ast_path.exists():
        raise FileNotFoundError(f"AST file not found at: {ast_path}")
        
    with open(ast_path, 'r', encoding='utf-8') as f:
        ast_data = json.load(f)
        
    txt_lines = txt_path.read_text(encoding='utf-8').splitlines() if txt_path.exists() else []
    
    results = []
    ast_replacements = 0
    txt_replacements = 0
    
    for item in patch_items:
        sub_key = item['sub_key']
        field = item['field']
        sus = item['suspect']
        sug = item['suggested']
        rule = item.get('rule_name', '')
        
        ast_done = False
        txt_done = False
        
        # 1. Swara-aware AST Replacement
        supersections = ast_data.get('supersections', ast_data.get('supersection', {}))
        for ss in supersections.values():
            if not isinstance(ss, dict): continue
            for sec in ss.get('sections', {}).values():
                if not isinstance(sec, dict): continue
                if sub_key in sec.get('subsections', {}):
                    sub = sec['subsections'][sub_key]
                    
                    if field == 'Arsheyam Header' and 'header' in sub:
                        h = sub['header'].get('header', '')
                        new_h, ok = swara_aware_replace(h, sus, sug)
                        if ok:
                            if not dry_run: sub['header']['header'] = new_h
                            ast_done = True
                            ast_replacements += 1
                            
                    elif field == 'Rik Metadata':
                        rm = sub.get('rik_metadata', '')
                        new_rm, ok = swara_aware_replace(rm, sus, sug)
                        if ok:
                            if not dry_run: sub['rik_metadata'] = new_rm
                            ast_done = True
                            ast_replacements += 1
                            
                    elif field == 'Rik Text':
                        rt = sub.get('rik_text', '')
                        new_rt, ok = swara_aware_replace(rt, sus, sug)
                        if ok:
                            if not dry_run: sub['rik_text'] = new_rt
                            ast_done = True
                            ast_replacements += 1
                            
                    elif field == 'Saman Metadata':
                        sm = sub.get('saman_metadata', '')
                        new_sm, ok = swara_aware_replace(sm, sus, sug)
                        if ok:
                            if not dry_run: sub['saman_metadata'] = new_sm
                            ast_done = True
                            ast_replacements += 1
                            
                    elif field == 'Samam Chant':
                        for m_set in sub.get('corrected-mantra_sets', sub.get('mantra_sets', [])):
                            cm = m_set.get('corrected-mantra', '')
                            new_cm, ok_cm = swara_aware_replace(cm, sus, sug)
                            if ok_cm:
                                if not dry_run: m_set['corrected-mantra'] = new_cm
                                ast_done = True
                                ast_replacements += 1
                            m_raw = m_set.get('mantra', '')
                            new_m, ok_m = swara_aware_replace(m_raw, sus, sug)
                            if ok_m and not dry_run:
                                m_set['mantra'] = new_m
                                
        # 2. Swara-aware Text Replacement within subsection block
        if txt_lines:
            s_idx, e_idx = get_subsection_line_range(txt_lines, sub_key)
            if s_idx is not None:
                sub_block = '\n'.join(txt_lines[s_idx:e_idx])
                new_block, ok_txt = swara_aware_replace(sub_block, sus, sug)
                if ok_txt:
                    if not dry_run:
                        new_lines = new_block.splitlines()
                        txt_lines = txt_lines[:s_idx] + new_lines + txt_lines[e_idx:]
                    txt_done = True
                    txt_replacements += 1
                    
        results.append({
            'sub_key': sub_key,
            'field': field,
            'suspect': sus,
            'suggested': sug,
            'rule_name': rule,
            'ast_applied': ast_done,
            'txt_applied': txt_done
        })
        
    print(f"[SUMMARY] Matched & applied in AST: {ast_replacements}, in Unicode TXT: {txt_replacements}")
    
    if not dry_run:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Backup AST
        if ast_path.exists():
            bak_ast = ast_path.with_suffix(f'.json.{ts}.bak')
            shutil.copy2(ast_path, bak_ast)
            print(f"[BACKUP] Created {bak_ast.name}")
        # Save AST
        with open(ast_path, 'w', encoding='utf-8') as f:
            json.dump(ast_data, f, ensure_ascii=False, indent=2)
        if out_ast_path.parent.exists():
            with open(out_ast_path, 'w', encoding='utf-8') as f:
                json.dump(ast_data, f, ensure_ascii=False, indent=2)
                
        # Backup & Save Text
        if txt_lines and txt_path.exists():
            bak_txt = txt_path.with_suffix(f'.txt.{ts}.bak')
            shutil.copy2(txt_path, bak_txt)
            print(f"[BACKUP] Created {bak_txt.name}")
            final_text = '\n'.join(txt_lines) + '\n'
            txt_path.write_text(final_text, encoding='utf-8')
            if sync_txt_path.parent.exists():
                sync_txt_path.write_text(final_text, encoding='utf-8')
                
        print("[SUCCESS] All swara-aware modifications committed to disk.")
    else:
        print("[DRY-RUN] No files were modified on disk.")
        
    # Generate Markdown Report
    generate_patch_applied_report(results, dry_run, report_path)
    return results

def generate_patch_applied_report(results: list, dry_run: bool, report_path: Path):
    """Generates a comprehensive Markdown report of applied changes."""
    lines = [
        "# ॥ सामसंहिता सन्धि-संशोधन-वृत्तान्तः ॥",
        f"## Sanskrit Sandhi Corrections Applied Report ({'DRY RUN PREVIEW' if dry_run else 'APPLIED TO DISK'})",
        "",
        f"- **Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **Total Items Processed**: {len(results)}",
        f"- **AST Replacements**: {sum(1 for r in results if r['ast_applied'])}",
        f"- **Unicode Text Replacements**: {sum(1 for r in results if r['txt_applied'])}",
        "",
        "| # | Subsection | Field | Suspect (Before) | Suggested (After) | AST Applied | TXT Applied | Rule |",
        "| :---: | :--- | :--- | :--- | :--- | :---: | :---: | :--- |"
    ]
    
    for i, r in enumerate(results, 1):
        ast_sym = '✅' if r['ast_applied'] else '❌'
        txt_sym = '✅' if r['txt_applied'] else '❌'
        lines.append(f"| {i} | `{r['sub_key']}` | {r['field']} | `{r['suspect']}` | **`{r['suggested']}`** | {ast_sym} | {txt_sym} | {r['rule_name']} |")
        
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text('\n'.join(lines), encoding='utf-8')
    print(f"[INFO] Wrote report to: {report_path}")

def main():
    parser = argparse.ArgumentParser(description="Apply selected Sanskrit Sandhi corrections to Samhita AST and Unicode text (Swara-Aware).")
    parser.add_argument('--patch', '-p', type=Path, default=None, help='Path to selected patch JSON file')
    parser.add_argument('--dry-run', action='store_true', help='Preview replacements without modifying files')
    parser.add_argument('--select-high', action='store_true', help='Select all High severity cases from audit')
    parser.add_argument('--select-headers', action='store_true', help='Select all Ārṣeyam subsection header cases')
    parser.add_argument('--ast', type=Path, default=DEFAULT_AST_PATH, help='Target AST JSON path')
    parser.add_argument('--txt', type=Path, default=DEFAULT_TXT_PATH, help='Target Unicode text path')
    parser.add_argument('--report', type=Path, default=DEFAULT_REPORT_PATH, help='Output markdown report path')
    args = parser.parse_args()
    
    patch_items = load_patch_items(args.patch, select_high=args.select_high, select_headers=args.select_headers)
    apply_sandhi_patch(
        patch_items=patch_items,
        dry_run=args.dry_run,
        ast_path=args.ast,
        txt_path=args.txt,
        report_path=args.report
    )

if __name__ == '__main__':
    main()
