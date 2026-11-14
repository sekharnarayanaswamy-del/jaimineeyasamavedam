import argparse
import subprocess
import re
import html
import json
from pathlib import Path
from collections import Counter

parser = argparse.ArgumentParser(description="Generate Sanskrit Sandhi Application Audit Report")
parser.add_argument(
    "--base",
    default="2820e674",
    help="Base commit to compare against (default: 2820e674 - pre-sandhi baseline)",
)
parser.add_argument(
    "--output",
    default="data/corpora/samhita/06_reports/SANDHI_APPLICATION_AUDIT_REPORT.html",
    help="Output HTML report path",
)
args = parser.parse_args()

# 1. Fetch original content at baseline
p_orig = subprocess.run(
    ['git', 'show', f'{args.base}:data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt'],
    capture_output=True, text=True, encoding='utf-8'
)
if p_orig.returncode != 0:
    print(f"[WARN] Could not fetch baseline commit '{args.base}'. Falling back to HEAD~1.")
    p_orig = subprocess.run(
        ['git', 'show', 'HEAD~1:data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt'],
        capture_output=True, text=True, encoding='utf-8'
    )

orig_lines = p_orig.stdout.splitlines()

# 2. Fetch current content
curr_path = Path('data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt')
curr_lines = curr_path.read_text(encoding='utf-8').splitlines()

# 3. Robust structural block parsing
def parse_blocks(lines):
    blocks = {}
    current_ssec = "आग्नेयपाठः"
    current_sec = "Section 1"
    current_sub = "subsection_1"
    current_field = "Preamble"
    
    for idx, line in enumerate(lines):
        line_num = idx + 1
        if '# Start of SuperSection Title' in line:
            current_field = "SuperSection Title"
        elif '# Start of Section Title' in line:
            current_field = "Section Title"
        elif '# Start of SubSection Title' in line:
            m = re.search(r'subsection_\d+', line)
            if m:
                current_sub = m.group(0)
            current_field = "SubSection Title"
        elif '# Start of Rik Metadata' in line:
            current_field = "Rik Metadata"
        elif '# Start of Rik Text' in line:
            current_field = "Rik Text"
        elif '# Start of Saman Metadata' in line:
            current_field = "Saman Metadata"
        elif '#Start of Mantra Sets' in line or '# Start of Mantra Sets' in line:
            current_field = "Mantra Sets (Chants)"
        elif line.startswith('# End of') or line.startswith('#End of'):
            pass
        elif line.strip():
            if current_field == "SuperSection Title":
                current_ssec = line.strip()
            key = (current_ssec, current_sub, current_field)
            if key not in blocks:
                blocks[key] = []
            blocks[key].append((line_num, line))
    return blocks

orig_blocks = parse_blocks(orig_lines)
curr_blocks = parse_blocks(curr_lines)

changes = []

for key, o_list in orig_blocks.items():
    if key not in curr_blocks:
        continue
    c_list = curr_blocks[key]
    current_ssec, current_sub, current_field = key
    
    o_text = "\n".join(l for _, l in o_list).strip()
    c_text = "\n".join(l for _, l in c_list).strip()
    
    if o_text == c_text:
        continue
        
    line_num = c_list[0][0]
    old_line = o_text
    new_line = c_text
    
    category = "Metadata Sandhi Normalization"
    badge_class = "cat-meta"

    if current_field == "Rik Text":
        if 'टट्य' in old_line and '३' in new_line:
            category = "Ṛgveda Inline Numeral ३"
            badge_class = "cat-num"
        elif 'ठ' in old_line and '१' in new_line:
            category = "Ṛgveda Inline Numeral १(1)"
            badge_class = "cat-num"
        elif 'ं' in old_line and any(c in new_line for c in ['न्', 'ङ्', 'ञ्', 'ण्', 'म्']):
            category = "Parasavarṇa Sandhi (Homorganic Nasal)"
            badge_class = "cat-para"
        elif 'न्ज' in old_line and 'ञ्ज' in new_line:
            category = "Ścutva Sandhi (न्ज → ञ्ज)"
            badge_class = "cat-scut"
        elif 'न्च' in old_line and 'ञ्च' in new_line:
            category = "Ścutva Sandhi (न्च → ञ्च)"
            badge_class = "cat-scut"
        else:
            category = "Rik Text Sandhi"
            badge_class = "cat-para"

    elif current_field == "Mantra Sets (Chants)":
        if 'न्ज' in old_line and 'ञ्ज' in new_line:
            category = "Ścutva Sandhi (न्ज → ञ्ज)"
            badge_class = "cat-scut"
        elif 'न्च' in old_line and 'ञ्च' in new_line:
            category = "Ścutva Sandhi (न्च → ञ्च)"
            badge_class = "cat-scut"
        else:
            category = "Chant Sandhi / Normalization"
            badge_class = "cat-scut"

    elif current_field in ["Rik Metadata", "Saman Metadata", "SubSection Title"]:
        if 'वांगिरसौ' in old_line and 'वाङ्गिरसौ' in new_line:
            category = "Parasavarṇa Sandhi (Velar ङ्)"
            badge_class = "cat-para"
        elif 'ककुप' in old_line and 'ककुप्' in new_line:
            category = "Typographical Normalization (ककुप्)"
            badge_class = "cat-typo"
        elif 'ः' in old_line and 'स्' in new_line:
            category = "Visarga Sandhi (विसर्जनीयस्य सः)"
            badge_class = "cat-meta"
        elif '।' in old_line and '।' not in new_line:
            category = "Option 1 Continuous Sandhi"
            badge_class = "cat-meta"
        else:
            category = "Option 1 Continuous Sandhi"
            badge_class = "cat-meta"

    changes.append({
        'line_num': line_num,
        'ssec': current_ssec,
        'sub': current_sub,
        'field': current_field,
        'category': category,
        'badge_class': badge_class,
        'old': old_line,
        'new': new_line
    })

# Compute stats
counts = Counter(c['category'] for c in changes)
cat_meta_cnt = sum(c for k, c in counts.items() if 'Option 1' in k or 'Metadata' in k or 'Visarga' in k)
cat_para_cnt = sum(c for k, c in counts.items() if 'Parasavarṇa' in k)
cat_scut_cnt = sum(c for k, c in counts.items() if 'Ścutva' in k or 'Chant' in k)
cat_num_cnt = sum(c for k, c in counts.items() if 'Numeral' in k)
cat_typo_cnt = sum(c for k, c in counts.items() if 'Typographical' in k)

# Build HTML
html_content = f"""<!DOCTYPE html>
<html lang="sa">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sanskrit Sandhi Application Audit Report — Jaiminīya Sāmaveda Saṃhitā</title>
<style>
  :root {{
    --bg-page: #f8fafc;
    --card-bg: #ffffff;
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --border-color: #e2e8f0;
    --accent-blue: #2563eb;
    --diff-del-bg: #fee2e2;
    --diff-del-text: #991b1b;
    --diff-add-bg: #dcfce7;
    --diff-add-text: #166534;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background-color: var(--bg-page);
    color: var(--text-primary);
    line-height: 1.5;
    margin: 0;
    padding: 24px;
  }}
  .container {{
    max-width: 1400px;
    margin: 0 auto;
  }}
  header {{
    background: white;
    padding: 24px 32px;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    margin-bottom: 24px;
    border-left: 6px solid #2563eb;
  }}
  h1 {{
    margin: 0 0 8px 0;
    font-size: 26px;
    color: #1e293b;
  }}
  .subtitle {{
    color: var(--text-secondary);
    font-size: 15px;
    margin: 0;
  }}
  .stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }}
  .stat-card {{
    background: white;
    padding: 16px 20px;
    border-radius: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    border-top: 4px solid #94a3b8;
  }}
  .stat-card.meta {{ border-top-color: #7c3aed; }}
  .stat-card.para {{ border-top-color: #2563eb; }}
  .stat-card.scut {{ border-top-color: #0d9488; }}
  .stat-card.num {{ border-top-color: #ea580c; }}
  .stat-card.total {{ border-top-color: #16a34a; }}
  .stat-value {{
    font-size: 28px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 4px;
  }}
  .stat-label {{
    font-size: 13px;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 600;
  }}
  .controls-bar {{
    background: white;
    padding: 16px 20px;
    border-radius: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    margin-bottom: 24px;
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    align-items: center;
    justify-content: space-between;
  }}
  .search-box {{
    flex: 1;
    min-width: 280px;
    position: relative;
  }}
  .search-box input {{
    width: 100%;
    padding: 10px 14px;
    font-size: 14px;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    outline: none;
    box-sizing: border-box;
  }}
  .search-box input:focus {{
    border-color: var(--accent-blue);
    box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
  }}
  .filter-pills {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }}
  .pill {{
    padding: 6px 14px;
    font-size: 13px;
    border-radius: 20px;
    background: #f1f5f9;
    color: #475569;
    cursor: pointer;
    border: 1px solid transparent;
    user-select: none;
    transition: all 0.15s ease;
  }}
  .pill:hover {{
    background: #e2e8f0;
    color: #0f172a;
  }}
  .pill.active {{
    background: #2563eb;
    color: white;
    font-weight: 600;
  }}
  .table-card {{
    background: white;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    overflow: hidden;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }}
  th, td {{
    padding: 12px 16px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
    vertical-align: top;
  }}
  th {{
    background-color: #f8fafc;
    color: #475569;
    font-weight: 600;
    position: sticky;
    top: 0;
    z-index: 10;
  }}
  tr:hover {{ background-color: #f8fafc; }}
  .line-no {{
    font-family: monospace;
    color: #64748b;
    font-size: 12px;
    white-space: nowrap;
  }}
  .badge {{
    display: inline-block;
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    white-space: nowrap;
  }}
  .cat-meta {{ background: #f3e8ff; color: #6b21a8; }}
  .cat-para {{ background: #dbeafe; color: #1e40af; }}
  .cat-scut {{ background: #ccfbf1; color: #0f766e; }}
  .cat-num {{ background: #ffedd5; color: #9a3412; }}
  .cat-typo {{ background: #f1f5f9; color: #334155; }}
  .devanagari {{
    font-family: "Siddhanta", "AdishilaVedic", "Nirmala UI", sans-serif;
    font-size: 15px;
    line-height: 1.6;
  }}
  .diff-old {{
    background-color: var(--diff-del-bg);
    color: var(--diff-del-text);
    padding: 6px 10px;
    border-radius: 6px;
    text-decoration: line-through;
    opacity: 0.85;
  }}
  .diff-new {{
    background-color: var(--diff-add-bg);
    color: var(--diff-add-text);
    padding: 6px 10px;
    border-radius: 6px;
    font-weight: 500;
  }}
  .hidden-row {{ display: none !important; }}
</style>
</head>
<body>

<div class="container">
  <header>
    <h1>Sanskrit Sandhi Application Audit Report</h1>
    <p class="subtitle">Complete audit of all continuous Paninian Sandhi, Parasavarṇa assimilation, Ścutva rules, Ṛgveda inline numerals, and typographical normalizations applied to <code>Samhita_Devanagari_Unicode.txt</code> (Baseline: <code>{args.base}</code> → Current Edition).</p>
  </header>

  <div class="stats-grid">
    <div class="stat-card total">
      <div class="stat-value">{len(changes)}</div>
      <div class="stat-label">Total Blocks / Items Modified</div>
    </div>
    <div class="stat-card meta">
      <div class="stat-value">{cat_meta_cnt}</div>
      <div class="stat-label">Option 1 Continuous Sandhi</div>
    </div>
    <div class="stat-card para">
      <div class="stat-value">{cat_para_cnt}</div>
      <div class="stat-label">Parasavarṇa Sandhi (8.4.58)</div>
    </div>
    <div class="stat-card scut">
      <div class="stat-value">{cat_scut_cnt}</div>
      <div class="stat-label">Ścutva Sandhi (8.4.40)</div>
    </div>
    <div class="stat-card num">
      <div class="stat-value">{cat_num_cnt}</div>
      <div class="stat-label">Ṛgveda Numerals (३ &amp; १(1))</div>
    </div>
  </div>

  <div class="controls-bar">
    <div class="search-box">
      <input type="text" id="searchInput" placeholder="Filter by line #, text segment, or subsection (e.g. अग्निन्दूतं, युञ्जना, subsection_28)..." onkeyup="filterRows()">
    </div>
    <div class="filter-pills">
      <div class="pill active" onclick="setCategory('all', this)">All ({len(changes)})</div>
      <div class="pill" onclick="setCategory('Option 1', this)">Option 1 Sandhi ({cat_meta_cnt})</div>
      <div class="pill" onclick="setCategory('Parasavarṇa', this)">Parasavarṇa ({cat_para_cnt})</div>
      <div class="pill" onclick="setCategory('Ścutva', this)">Ścutva ({cat_scut_cnt})</div>
      <div class="pill" onclick="setCategory('Numeral', this)">Ṛgveda Numerals ({cat_num_cnt})</div>
      <div class="pill" onclick="setCategory('Typographical', this)">Typo Normalization ({cat_typo_cnt})</div>
    </div>
  </div>

  <div class="table-card">
    <table id="auditTable">
      <thead>
        <tr>
          <th style="width: 80px;">Line #</th>
          <th style="width: 140px;">Subsection</th>
          <th style="width: 160px;">Field</th>
          <th style="width: 240px;">Rule Category</th>
          <th style="width: 440px;">Original Text</th>
          <th style="width: 440px;">After Modification (Transformed)</th>
        </tr>
      </thead>
      <tbody>
"""

for c in changes:
    safe_old = html.escape(c['old'])
    safe_new = html.escape(c['new'])
    safe_cat = html.escape(c['category'])
    safe_sub = html.escape(c['sub'])
    safe_field = html.escape(c['field'])
    
    html_content += f"""        <tr data-cat="{safe_cat}" data-search="{c['line_num']} {safe_sub} {safe_field} {safe_cat} {safe_old} {safe_new}">
          <td class="line-no">L{c['line_num']}</td>
          <td><strong>{safe_sub}</strong></td>
          <td><span class="badge cat-typo">{safe_field}</span></td>
          <td><span class="badge {c['badge_class']}">{safe_cat}</span></td>
          <td class="devanagari"><div class="diff-old">{safe_old}</div></td>
          <td class="devanagari"><div class="diff-new">{safe_new}</div></td>
        </tr>
"""

html_content += """      </tbody>
    </table>
  </div>
</div>

<script>
let currentCategory = 'all';

function setCategory(cat, el) {
  currentCategory = cat;
  document.querySelectorAll('.filter-pills .pill').forEach(p => p.classList.remove('active'));
  el.classList.add('active');
  filterRows();
}

function filterRows() {
  const query = document.getElementById('searchInput').value.toLowerCase().trim();
  const rows = document.querySelectorAll('#auditTable tbody tr');
  
  rows.forEach(row => {
    const rowCat = row.getAttribute('data-cat') || '';
    const rowSearch = (row.getAttribute('data-search') || '').toLowerCase();
    
    let matchesCat = true;
    if (currentCategory !== 'all') {
      matchesCat = rowCat.includes(currentCategory);
    }
    
    let matchesSearch = true;
    if (query.length > 0) {
      matchesSearch = rowSearch.includes(query);
    }
    
    if (matchesCat && matchesSearch) {
      row.classList.remove('hidden-row');
    } else {
      row.classList.add('hidden-row');
    }
  });
}
</script>

</body>
</html>
"""

report_file = Path(args.output)
report_file.parent.mkdir(parents=True, exist_ok=True)
report_file.write_text(html_content, encoding='utf-8')
print(f"Audit report written to: {report_file}")
