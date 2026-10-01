"""
Publish Standalone HTML Readers to docs/standalone-html/
-------------------------------------------------------
Publishes strictly the 2 canonical Kodunthirapully (kpully) HTML editions:
  1. Samhita_kpully_Devanagari.html (Devanagari script)
  2. Samam_kpully_Malayalam.html (Malayalam script)

Purges any obsolete or legacy HTML files from docs/standalone-html/ and updates
the catalog portal index.html.
"""

import os
import shutil
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPORA_DIR = REPO_ROOT / "data" / "corpora"
SOURCE_DIR = REPO_ROOT / "data" / "output" / "html"
TARGET_DIR = REPO_ROOT / "docs" / "standalone-html"

# Canonical readers to publish
CANONICAL_READERS = {
    "Samam_kpully_Devanagari.html": {
        "title": "Samam (Devanagari) — Kodunthirapully Edition",
        "category": "Samam Chants",
        "script": "Devanagari",
        "description": "Canonical Devanagari Jaimineeya Samam chanting edition in swaras-above Kodunthirapully layout.",
        "featured": True,
        "subfolder": "Devanagari",
        "aliases": ["Samhita_kpully_Devanagari.html"],
    },
    "Samam_kpully_Malayalam.html": {
        "title": "Samam (Malayalam) — Kodunthirapully Edition",
        "category": "Samam Chants",
        "script": "Malayalam",
        "description": "Canonical Malayalam Jaimineeya Samam chanting edition featuring custom JaimineeyaSwara typography and elevated Kodunthirapully swara modifiers.",
        "featured": True,
        "subfolder": "Malayalam",
    }
}


def hash_file(path: Path) -> str:
    """Computes SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def format_size(bytes_val: int) -> str:
    """Formats byte count to human-readable string."""
    if bytes_val >= 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.1f} MB"
    return f"{bytes_val / 1024:.0f} KB"


def cleanup_obsolete_files(target_dir: Path):
    """Deletes all obsolete HTML files in docs/standalone-html except the 2 kpully files and index.html."""
    allowed_root = {"Samam_kpully_Malayalam.html", "Samam_kpully_Devanagari.html", "Samhita_kpully_Devanagari.html", "index.html"}
    allowed_sub = {
        "Devanagari": {"Samam_kpully_Devanagari.html", "Samhita_kpully_Devanagari.html"},
        "Malayalam": {"Samam_kpully_Malayalam.html"}
    }

    deleted_count = 0

    # Clean root directory files
    if target_dir.exists():
        for item in list(target_dir.iterdir()):
            if item.is_file():
                if item.suffix.lower() == ".html" and item.name not in allowed_root:
                    try:
                        item.unlink()
                        deleted_count += 1
                        print(f"  [DELETED] {item.name}")
                    except Exception as e:
                        print(f"  [WARN] Could not delete {item.name}: {e}")

    # Clean subdirectories
    for sub in ["Devanagari", "Malayalam"]:
        sub_dir = target_dir / sub
        if sub_dir.exists() and sub_dir.is_dir():
            for item in list(sub_dir.iterdir()):
                if item.is_file() and item.name not in allowed_sub.get(sub, set()):
                    try:
                        item.unlink()
                        deleted_count += 1
                        print(f"  [DELETED] {sub}/{item.name}")
                    except Exception as e:
                        print(f"  [WARN] Could not delete {sub}/{item.name}: {e}")

    # Remove any other unexpected directories
    if target_dir.exists():
        for item in list(target_dir.iterdir()):
            if item.is_dir() and item.name not in ["Devanagari", "Malayalam"]:
                try:
                    shutil.rmtree(item)
                    print(f"  [DELETED DIR] {item.name}")
                except Exception as e:
                    print(f"  [WARN] Could not remove directory {item.name}: {e}")

    if deleted_count > 0:
        print(f"[CLEANUP] Successfully purged {deleted_count} obsolete HTML files from {target_dir.relative_to(REPO_ROOT)}.")


def build_catalog_page(items):
    categories = ["All", "Featured", "Devanagari", "Malayalam"]
    total_files = len(items)
    dev_count = sum(1 for x in items if x["script"] == "Devanagari")
    mal_count = sum(1 for x in items if x["script"] == "Malayalam")
    total_size_mb = sum(x["bytes"] for x in items) / (1024 * 1024)
    items_json = json.dumps(items)

    pills_html = " ".join(f'<button class="filter-btn {("active" if cat=="All" else "")}" data-filter="{cat}">{cat}</button>' for cat in categories)

    initial_cards_html = []
    for item in items:
        script_badge_class = "badge-devanagari" if item["script"] == "Devanagari" else "badge-malayalam"
        featured_badge = '<span class="badge badge-featured">★ Featured</span>' if item["featured"] else ''
        card = f'''
            <div class="card{(' featured' if item['featured'] else '')}">
                <div>
                    <div class="card-header">
                        <div class="badges">
                            <span class="badge {script_badge_class}">{item['script']}</span>
                            <span class="badge badge-category">{item['category']}</span>
                            {featured_badge}
                        </div>
                        <div class="file-size">{item['size_fmt']}</div>
                    </div>
                    <h2 class="card-title">{item['title']}</h2>
                    <p class="card-desc">{item['description']}</p>
                </div>
                <div>
                    <div class="card-filename">{item['filename']}</div>
                    <div class="card-actions">
                        <a href="{item['rel_url']}" target="_blank" rel="noopener" class="btn btn-primary">
                            📖 Open Reader
                        </a>
                        <a href="{item['rel_url']}" download class="btn btn-secondary" title="Download HTML">
                            ⬇
                        </a>
                    </div>
                </div>
            </div>'''
        initial_cards_html.append(card)

    initial_cards_str = "\n".join(initial_cards_html)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>जैमिनीय सामवेदः | Standalone HTML Readers</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Noto+Serif+Devanagari:wght@400;600;700&family=Noto+Serif+Malayalam:wght@400;600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0f1117;
            --bg-secondary: #171b26;
            --bg-card: #1c2233;
            --bg-card-hover: #242c42;
            --accent-gold: #e5a93c;
            --accent-gold-light: #f7d070;
            --accent-saffron: #f37032;
            --accent-teal: #2dd4bf;
            --text-main: #f1f5f9;
            --text-muted: #94a3b8;
            --border-color: rgba(229, 169, 60, 0.2);
            --border-card: rgba(255, 255, 255, 0.08);
            --radius-md: 12px;
            --radius-sm: 8px;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-main);
            min-height: 100vh;
            line-height: 1.6;
            display: flex;
            flex-direction: column;
        }}

        .hero {{
            background: linear-gradient(180deg, #1a1e2e 0%, var(--bg-primary) 100%);
            border-bottom: 1px solid var(--border-color);
            padding: 3rem 1.5rem 2.5rem;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}

        .hero::before {{
            content: "";
            position: absolute;
            top: -50%;
            left: 50%;
            transform: translateX(-50%);
            width: 800px;
            height: 350px;
            background: radial-gradient(ellipse, rgba(229, 169, 60, 0.12) 0%, rgba(15, 17, 23, 0) 70%);
            pointer-events: none;
        }}

        .badge-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(229, 169, 60, 0.15);
            color: var(--accent-gold);
            border: 1px solid rgba(229, 169, 60, 0.35);
            padding: 4px 14px;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            margin-bottom: 1rem;
        }}

        .hero h1 {{
            font-family: 'Cinzel', 'Noto Serif Devanagari', serif;
            font-size: clamp(2rem, 5vw, 3.2rem);
            color: var(--accent-gold-light);
            text-shadow: 0 2px 10px rgba(229, 169, 60, 0.3);
            margin-bottom: 0.5rem;
            letter-spacing: 1px;
        }}

        .hero p.subtitle {{
            font-size: 1.15rem;
            color: var(--text-muted);
            max-width: 780px;
            margin: 0 auto 1.5rem;
        }}

        .hero-stats {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            flex-wrap: wrap;
            margin-top: 1rem;
        }}

        .stat-item {{
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border-card);
            border-radius: var(--radius-sm);
            padding: 8px 18px;
            font-size: 0.9rem;
        }}

        .stat-value {{
            font-weight: 700;
            color: var(--accent-gold);
            margin-right: 4px;
        }}

        .container {{
            max-width: 1100px;
            width: 100%;
            margin: 0 auto;
            padding: 2.5rem 1.5rem;
            flex: 1;
        }}

        .controls {{
            display: flex;
            flex-direction: column;
            gap: 1.2rem;
            margin-bottom: 2rem;
        }}

        .search-box {{
            position: relative;
            width: 100%;
        }}

        .search-input {{
            width: 100%;
            padding: 14px 20px 14px 46px;
            background: var(--bg-secondary);
            border: 1px solid var(--border-card);
            border-radius: var(--radius-md);
            color: var(--text-main);
            font-size: 1.05rem;
            transition: all 0.2s ease;
            outline: none;
        }}

        .search-input:focus {{
            border-color: var(--accent-gold);
            box-shadow: 0 0 0 3px rgba(229, 169, 60, 0.15);
        }}

        .search-icon {{
            position: absolute;
            left: 16px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            font-size: 1.1rem;
        }}

        .filter-pills {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}

        .filter-btn {{
            background: var(--bg-secondary);
            border: 1px solid var(--border-card);
            color: var(--text-muted);
            padding: 7px 16px;
            border-radius: 9999px;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.2s ease;
            font-weight: 500;
        }}

        .filter-btn:hover {{
            color: var(--text-main);
            background: rgba(255, 255, 255, 0.08);
        }}

        .filter-btn.active {{
            background: var(--accent-gold);
            color: #0f1117;
            font-weight: 600;
            border-color: var(--accent-gold);
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
            gap: 2rem;
        }}

        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: var(--radius-md);
            padding: 1.8rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.2s ease;
            position: relative;
        }}

        .card:hover {{
            background: var(--bg-card-hover);
            transform: translateY(-3px);
            border-color: rgba(229, 169, 60, 0.4);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        }}

        .card.featured {{
            border-color: rgba(229, 169, 60, 0.45);
            background: linear-gradient(145deg, rgba(229, 169, 60, 0.08) 0%, var(--bg-card) 65%);
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 0.8rem;
            gap: 8px;
        }}

        .badges {{
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
        }}

        .badge {{
            font-size: 0.75rem;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .badge-devanagari {{
            background: rgba(243, 112, 50, 0.2);
            color: #ff8a50;
            border: 1px solid rgba(243, 112, 50, 0.3);
        }}

        .badge-malayalam {{
            background: rgba(45, 212, 191, 0.2);
            color: #2dd4bf;
            border: 1px solid rgba(45, 212, 191, 0.3);
        }}

        .badge-category {{
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-muted);
        }}

        .badge-featured {{
            background: rgba(229, 169, 60, 0.25);
            color: var(--accent-gold);
            border: 1px solid rgba(229, 169, 60, 0.4);
        }}

        .file-size {{
            font-size: 0.8rem;
            color: var(--text-muted);
            white-space: nowrap;
        }}

        .card-title {{
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-main);
            margin-bottom: 0.5rem;
            line-height: 1.4;
        }}

        .card-desc {{
            font-size: 0.95rem;
            color: var(--text-muted);
            margin-bottom: 1.4rem;
            flex-grow: 1;
            line-height: 1.5;
        }}

        .card-filename {{
            font-family: monospace;
            font-size: 0.8rem;
            color: #64748b;
            margin-bottom: 1rem;
            word-break: break-all;
        }}

        .card-actions {{
            display: flex;
            gap: 10px;
        }}

        .btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            padding: 10px 18px;
            border-radius: var(--radius-sm);
            font-size: 0.95rem;
            font-weight: 600;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.2s ease;
            flex: 1;
        }}

        .btn-primary {{
            background: var(--accent-gold);
            color: #0f1117;
            border: 1px solid var(--accent-gold);
        }}

        .btn-primary:hover {{
            background: var(--accent-gold-light);
            border-color: var(--accent-gold-light);
            box-shadow: 0 4px 12px rgba(229, 169, 60, 0.35);
        }}

        .btn-secondary {{
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-main);
            border: 1px solid var(--border-card);
            flex: 0 0 auto;
        }}

        .btn-secondary:hover {{
            background: rgba(255, 255, 255, 0.12);
        }}

        .no-results {{
            grid-column: 1 / -1;
            text-align: center;
            padding: 4rem 1rem;
            color: var(--text-muted);
        }}

        footer {{
            border-top: 1px solid var(--border-card);
            padding: 2rem 1.5rem;
            text-align: center;
            font-size: 0.85rem;
            color: var(--text-muted);
            background: var(--bg-secondary);
        }}

        footer a {{
            color: var(--accent-gold);
            text-decoration: none;
        }}

        footer a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <header class="hero">
        <div class="badge-pill">Kodunthirapully Editions</div>
        <h1>जैमिनीय सामवेदः</h1>
        <p class="subtitle">Canonical Self-Contained Standalone HTML Readers with Kodunthirapully Vedic Swara Accents (Devanagari &amp; Malayalam scripts)</p>
        <div class="hero-stats">
            <div class="stat-item"><span class="stat-value">{total_files}</span> Editions Available</div>
            <div class="stat-item"><span class="stat-value">{dev_count}</span> Devanagari</div>
            <div class="stat-item"><span class="stat-value">{mal_count}</span> Malayalam</div>
            <div class="stat-item"><span class="stat-value">{total_size_mb:.1f} MB</span> Total Chants</div>
        </div>
    </header>

    <main class="container">
        <div class="controls">
            <div class="search-box">
                <span class="search-icon">🔍</span>
                <input type="text" id="searchInput" class="search-input" placeholder="Search by title, script, or filename...">
            </div>
            <div class="filter-pills" id="filterPills">
                {pills_html}
            </div>
        </div>

        <div class="grid" id="readerGrid">
{initial_cards_str}
        </div>
        <div class="no-results" id="noResults" style="display: none;">
            <h3>No editions matched your search</h3>
            <p>Try adjusting your search terms or filter selection.</p>
        </div>
    </main>

    <footer>
        <p>जैमिनीय सामवेद प्रकाशनम् | Standalone Editions archive served directly via GitHub Pages.</p>
        <p style="margin-top: 4px;">Each reader is 100% self-contained with embedded swara fonts and responsive layout.</p>
    </footer>

    <script>
        const readers = {items_json};
        let currentFilter = 'All';
        let currentSearch = '';

        const grid = document.getElementById('readerGrid');
        const noResults = document.getElementById('noResults');
        const searchInput = document.getElementById('searchInput');
        const filterPills = document.getElementById('filterPills');

        function renderCards() {{
            grid.innerHTML = '';
            const query = currentSearch.toLowerCase().trim();

            const filtered = readers.filter(item => {{
                if (currentFilter === 'Featured' && !item.featured) return false;
                if (currentFilter === 'Devanagari' && item.script !== 'Devanagari') return false;
                if (currentFilter === 'Malayalam' && item.script !== 'Malayalam') return false;

                if (query) {{
                    const matchText = (item.title + ' ' + item.filename + ' ' + item.category + ' ' + item.script + ' ' + item.description).toLowerCase();
                    if (!matchText.includes(query)) return false;
                }}
                return true;
            }});

            if (filtered.length === 0) {{
                noResults.style.display = 'block';
                return;
            }} else {{
                noResults.style.display = 'none';
            }}

            filtered.forEach(item => {{
                const card = document.createElement('div');
                card.className = 'card' + (item.featured ? ' featured' : '');

                const scriptBadgeClass = item.script === 'Devanagari' ? 'badge-devanagari' : 'badge-malayalam';

                card.innerHTML = `
                    <div>
                        <div class="card-header">
                            <div class="badges">
                                <span class="badge ${{scriptBadgeClass}}">${{item.script}}</span>
                                <span class="badge badge-category">${{item.category}}</span>
                                ${{item.featured ? '<span class="badge badge-featured">★ Featured</span>' : ''}}
                            </div>
                            <div class="file-size">${{item.size_fmt}}</div>
                        </div>
                        <h2 class="card-title">${{item.title}}</h2>
                        <p class="card-desc">${{item.description}}</p>
                    </div>
                    <div>
                        <div class="card-filename">${{item.filename}}</div>
                        <div class="card-actions">
                            <a href="${{item.rel_url}}" target="_blank" rel="noopener" class="btn btn-primary">
                                📖 Open Reader
                            </a>
                            <a href="${{item.rel_url}}" download class="btn btn-secondary" title="Download HTML">
                                ⬇
                            </a>
                        </div>
                    </div>
                `;
                grid.appendChild(card);
            }});
        }}

        searchInput.addEventListener('input', (e) => {{
            currentSearch = e.target.value;
            renderCards();
        }});

        filterPills.addEventListener('click', (e) => {{
            if (e.target.classList.contains('filter-btn')) {{
                filterPills.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
                e.target.classList.add('active');
                currentFilter = e.target.getAttribute('data-filter');
                renderCards();
            }}
        }});

        renderCards();
    </script>
</body>
</html>"""
    return html


def main():
    print(f"Target directory: {TARGET_DIR}")

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    target_dev = TARGET_DIR / "Devanagari"
    target_mal = TARGET_DIR / "Malayalam"
    target_dev.mkdir(exist_ok=True)
    target_mal.mkdir(exist_ok=True)

    # 1. Clean up all obsolete non-kpully HTML files
    cleanup_obsolete_files(TARGET_DIR)

    # 2. Sync only the 2 canonical KPully readers
    sam_renders = CORPORA_DIR / "samhita" / "05_renders" / "html"
    items = []

    for filename, meta in CANONICAL_READERS.items():
        subfolder = meta["subfolder"]
        target_sub = target_mal if subfolder == "Malayalam" else target_dev

        # Resolve source from 05_renders or data/output/html
        stem = Path(filename).stem
        alt_filename = f"{stem}_Samam.html" if not stem.endswith("_Samam") else filename
        candidates = [
            sam_renders / alt_filename if sam_renders.exists() else None,
            sam_renders / filename if sam_renders.exists() else None,
            SOURCE_DIR / subfolder / alt_filename,
            SOURCE_DIR / subfolder / filename,
            SOURCE_DIR / alt_filename,
            SOURCE_DIR / filename,
        ]
        existing_cands = [c for c in candidates if c and c.exists()]
        src_path = None
        if existing_cands:
            existing_cands.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            src_path = existing_cands[0]

        if not src_path or not src_path.exists():
            # Check if already present in target directory
            if (target_sub / filename).exists():
                src_path = target_sub / filename
            elif (TARGET_DIR / filename).exists():
                src_path = TARGET_DIR / filename

        if not src_path or not src_path.exists():
            print(f"[WARN] Source reader not found: {filename}")
            continue

        # Copy to root and subfolder
        dest_root = TARGET_DIR / filename
        dest_sub = target_sub / filename
        shutil.copy2(src_path, dest_root)
        shutil.copy2(src_path, dest_sub)

        # Also populate aliases (e.g. legacy URLs like Samhita_kpully_Devanagari.html)
        aliases = meta.get("aliases", [])
        for alias in aliases:
            shutil.copy2(src_path, TARGET_DIR / alias)
            shutil.copy2(src_path, target_sub / alias)

        file_bytes = dest_root.stat().st_size
        print(f"[SYNC] Published {filename} ({format_size(file_bytes)}) -> docs/standalone-html/")

        items.append({
            "filename": filename,
            "script": meta["script"],
            "category": meta["category"],
            "title": meta["title"],
            "description": meta["description"],
            "featured": meta["featured"],
            "bytes": file_bytes,
            "size_fmt": format_size(file_bytes),
            "rel_url": f"{subfolder}/{filename}",
        })

    items.sort(key=lambda x: (x["script"], x["title"]))

    # 3. Write catalog index.html
    index_html = build_catalog_page(items)
    index_path = TARGET_DIR / "index.html"
    index_path.write_text(index_html, encoding="utf-8")
    print(f"[INDEX] Generated clean catalog at: {index_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
