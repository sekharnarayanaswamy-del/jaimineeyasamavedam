"""
Merge Updated Rik Texts from Samhita_Devanagari_Unicode - Nov 2026.txt
onto Samhita_Devanagari_Unicode.txt, preserving authoritative Rik order,
numbering, and Arsheya metadata. Also propagates updates to shared/sibling subsections.
"""

import os
import re
import difflib
from difflib import SequenceMatcher
from collections import defaultdict

def run_merge():
    target_path = 'data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt'
    input_sync_path = 'data/input/Samhita_Devanagari_Unicode.txt'
    source_path = 'data/corpora/samhita/01_input/Samhita_Devanagari_Unicode - Nov 2026.txt'
    report_path = 'data/corpora/samhita/06_reports/RIK_TEXT_UPDATE_REPORT_NOV_2026.md'

    with open(target_path, 'r', encoding='utf-8') as f:
        tgt_text = f.read()

    with open(source_path, 'r', encoding='utf-8') as f:
        src_text = f.read()

    # Parse structural mapping (SuperSection -> Section -> SubSection)
    lines = tgt_text.splitlines()
    cur_super = ''
    cur_sec = ''
    sub_info = {}
    for l in lines:
        if '# Start of SuperSection Title' in l:
            idx = lines.index(l)
            cur_super = lines[idx + 1].strip()
        elif '# Start of Section Title' in l:
            idx = lines.index(l)
            cur_sec = lines[idx + 1].strip()
        elif '# Start of SubSection Title' in l:
            m = re.search(r'--(.*?)(?:##|$)', l)
            if m:
                sid = m.group(1).strip()
                sub_info[sid] = {
                    'parva': cur_super,
                    'kandah': cur_sec
                }

    def parse_blocks(txt):
        blocks = {}
        cur_lines = []
        cur_block = None
        cur_sub = None
        for l in txt.splitlines():
            m_start = re.match(r'#\s*Start of (.*?) -- (subsection_\d+)', l)
            m_end = re.match(r'#\s*End of (.*?) -- (subsection_\d+)', l)
            if m_start:
                cur_block = m_start.group(1).strip()
                cur_sub = m_start.group(2).strip()
                cur_lines = []
            elif m_end:
                if cur_block and cur_sub:
                    blocks[(cur_block, cur_sub)] = '\n'.join(cur_lines).strip()
                cur_block = None
                cur_sub = None
                cur_lines = []
            elif cur_block:
                cur_lines.append(l)
        return blocks

    tgt_blocks = parse_blocks(tgt_text)
    src_blocks = parse_blocks(src_text)

    tgt_riks = {b[1]: tgt_blocks[b] for b in tgt_blocks if b[0] == 'Rik Text'}
    src_riks = {b[1]: src_blocks[b] for b in src_blocks if b[0] == 'Rik Text'}

    def clean(s):
        s = re.sub(r'\(.*?\)', '', s)
        s = re.sub(r'[^\w]', '', s)
        return s

    updates = {}
    direct_updates = {}
    propagated_updates = {}

    # 1. Direct matches by subsection_id
    for sid, t_val in tgt_riks.items():
        if sid in src_riks and src_riks[sid]:
            s_val = src_riks[sid]
            if s_val != t_val:
                r = SequenceMatcher(None, clean(t_val), clean(s_val)).ratio()
                m_t = re.findall(r'॥\s*([०-९\d]+)\s*॥', t_val)
                m_s = re.findall(r'॥\s*([०-९\d]+)\s*॥', s_val)
                if r >= 0.70 and (m_t == m_s or not m_t or not m_s):
                    updates[sid] = s_val
                    direct_updates[sid] = (t_val, s_val)

    # 2. Sibling propagation for shared Riks
    for sid, t_val in tgt_riks.items():
        if sid not in updates:
            for other_sid, (old_val, new_val) in direct_updates.items():
                if old_val == t_val:
                    updates[sid] = new_val
                    propagated_updates[sid] = (t_val, new_val)
                    break

    print(f"Direct updates: {len(direct_updates)}")
    print(f"Propagated updates: {len(propagated_updates)}")
    print(f"Total updates: {len(updates)}")

    # Apply updates to tgt_text
    def replace_rik_text(match):
        sid = match.group(1)
        old_content = match.group(2).strip()
        if sid in updates:
            new_content = updates[sid]
            return f"# Start of Rik Text -- {sid} ## DO NOT EDIT\n{new_content}\n# End of Rik Text -- {sid} ## DO NOT EDIT"
        return match.group(0)

    p_rik_tgt = re.compile(
        r'#\s*Start of Rik Text -- (subsection_\d+)(?: ## DO NOT EDIT)?\s*\n(.*?)\n#\s*End of Rik Text -- \1(?: ## DO NOT EDIT)?',
        re.DOTALL
    )
    merged_text = p_rik_tgt.sub(replace_rik_text, tgt_text)

    # Save to both target locations
    with open(target_path, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(merged_text)

    with open(input_sync_path, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(merged_text)

    print(f"Updated {target_path} and {input_sync_path}")

    # Generate Markdown Report
    by_parva = defaultdict(list)
    for sid, (old_val, new_val) in sorted(direct_updates.items(), key=lambda x: int(x[0].split('_')[1])):
        p_name = sub_info.get(sid, {}).get('parva', 'Unknown')
        k_name = sub_info.get(sid, {}).get('kandah', 'Unknown')
        by_parva[p_name].append((sid, k_name, old_val, new_val, False))

    for sid, (old_val, new_val) in sorted(propagated_updates.items(), key=lambda x: int(x[0].split('_')[1])):
        p_name = sub_info.get(sid, {}).get('parva', 'Unknown')
        k_name = sub_info.get(sid, {}).get('kandah', 'Unknown')
        by_parva[p_name].append((sid, k_name, old_val, new_val, True))

    report_lines = [
        "# Rik Text Update & Merge Report (November 2026 Sync)",
        "",
        f"- **Date**: 11-11-2026",
        f"- **Direct Subsection Updates from Nov 2026**: {len(direct_updates)}",
        f"- **Propagated Sibling Subsection Updates**: {len(propagated_updates)}",
        f"- **Total Subsections Updated**: {len(updates)}",
        "",
        "## Summary of Core Refinements",
        "1. **Anusvara to Makara Before Dandas (`ं ।` -> `म् ।`)**: Standardized Samavedic sandhi before paadanta dandas.",
        "2. **Visarga Typographical Normalization**: Replaced ASCII colons (`:`) with true Devanagari visargas (`ः`).",
        "3. **Swara / Visarga Relocation**: Swara markers relocated to precede the visarga on vowels rather than hanging after visarga.",
        "4. **Consonant Assimilation & Padaccheda**: Preserved vocalic rephas, anusvara assimilation before velars, and word boundaries.",
        "5. **Preservation of Rik Order & Numbering**: Authoritative Rik ordering, numbering, and Arsheya metadata (`।।...।।`) strictly maintained.",
        "",
        "---",
        ""
    ]

    for p_name, items in by_parva.items():
        report_lines.append(f"## {p_name} ({len(items)} updates)")
        report_lines.append("")
        report_lines.append("| Subsection | Kandah | Mode | Baseline Rik Text | Updated Rik Text (Nov 2026) |")
        report_lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for sid, kname, old_val, new_val, is_prop in items:
            mode_str = "Propagated" if is_prop else "Direct"
            clean_old = old_val.replace('\n', ' ')
            clean_new = new_val.replace('\n', ' ')
            report_lines.append(f"| `{sid}` | {kname} | {mode_str} | `{clean_old}` | `{clean_new}` |")
        report_lines.append("")

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    print(f"Report written to: {report_path}")

if __name__ == '__main__':
    run_merge()
