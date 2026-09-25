"""
Publish Standalone HTML Readers to docs/standalone-html/
Allows browsing and reading full self-contained HTML Vedic readers via GitHub Pages
without disturbing the existing microsite at docs/index.html.
"""

import os
import shutil
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / "data" / "output" / "html"
TARGET_DIR = REPO_ROOT / "docs" / "standalone-html"

# Specific friendly titles, descriptions, and categories
METADATA = {
    # Devanagari Primary Readers
    "Samhita_kpully_Devanagari.html": {
        "title": "Samhita (Devanagari) — Fine-Tuned Edition",
        "category": "Samhita",
        "description": "Fine-tuned canonical Jaimineeya Samhita reader with modern swara alignments, optimized margins, and high-fidelity typography.",
        "featured": True,
    },
    "Samhita_Devanagari.html": {
        "title": "Samhita (Devanagari) — Complete Edition",
        "category": "Samhita",
        "description": "Full Devanagari Samhita text with complete swara notation and layout.",
        "featured": True,
    },
    "Samhita_Final_Enriched_Set_Devanagari.html": {
        "title": "Samhita (Devanagari) — Final Enriched Set",
        "category": "Samhita",
        "description": "Enriched Samhita edition with supplemental cross-references and attributes.",
        "featured": False,
    },
    "Samhita_with_Rishi_Devata_Chandas.html": {
        "title": "Samhita — Rishi, Devata & Chandas Edition",
        "category": "Samhita",
        "description": "Devanagari Samhita edition annotated with Rishi, Devata, and Chandas for each verse.",
        "featured": True,
    },
    "Samhita_K1_K2_Devanagari.html": {
        "title": "Samhita — Kanda 1 & 2 (Devanagari)",
        "category": "Samhita",
        "description": "Portion containing Kandas 1 and 2 of Jaimineeya Samhita.",
        "featured": False,
    },
    "Samhita_K1_K2_Devanagari_Kpully_Samam_NoMeta.html": {
        "title": "Samhita K1-K2 (Kpully Samam, No Metadata)",
        "category": "Samhita",
        "description": "Kanda 1 & 2 Samam chants without structural metadata.",
        "featured": False,
    },
    "Samhita_K1_K2_Devanagari_Samam_NoMeta.html": {
        "title": "Samhita K1-K2 (Devanagari Samam, No Metadata)",
        "category": "Samhita",
        "description": "Kanda 1 & 2 Samam chanting text only.",
        "featured": False,
    },
    "Samhita.html": {
        "title": "Samhita (Base Edition)",
        "category": "Samhita",
        "description": "Compact Samhita text rendering.",
        "featured": False,
    },
    "Aaranam_Devanagari.html": {
        "title": "Aaranam (Devanagari) — Complete Edition",
        "category": "Aaranam",
        "description": "Complete Jaimineeya Aaranam (Aranyaka-gana) reader in Devanagari script.",
        "featured": True,
    },
    "Aaranam_Complete_Set_Devanagari.html": {
        "title": "Aaranam — Complete Set (Devanagari)",
        "category": "Aaranam",
        "description": "Integrated complete Aaranam collection.",
        "featured": False,
    },
    "Aaranam_Samam.html": {
        "title": "Aaranam — Samam Chants (Devanagari)",
        "category": "Aaranam",
        "description": "Aaranam Samam chanting texts with musical notation.",
        "featured": False,
    },
    "Aaranam_Rik.html": {
        "title": "Aaranam — Rik Verses (Devanagari)",
        "category": "Aaranam",
        "description": "Aaranam source Rik verses with accents.",
        "featured": False,
    },
    "Aaranam_Samam_NoMeta.html": {
        "title": "Aaranam — Samam Only (No Metadata)",
        "category": "Aaranam",
        "description": "Pure Aaranam Samam chanting text without headings/metadata.",
        "featured": False,
    },
    "Aaranam_Rik_NoMeta.html": {
        "title": "Aaranam — Rik Only (No Metadata)",
        "category": "Aaranam",
        "description": "Pure Aaranam Rik text without headings/metadata.",
        "featured": False,
    },
    "Aranyam_samam.html": {
        "title": "Aranyam Samam (Devanagari)",
        "category": "Aaranam",
        "description": "Aranyaka Samam chanting edition.",
        "featured": False,
    },
    "Aranam_Devanagari.html": {
        "title": "Aaranam (Alternative Rendering)",
        "category": "Aaranam",
        "description": "Variant rendering of Aaranam Devanagari.",
        "featured": False,
    },
    "Collection_Devanagari.html": {
        "title": "Curated Collection (Devanagari)",
        "category": "Collection",
        "description": "Custom curated selection of Jaimineeya chants and hymns in Devanagari.",
        "featured": True,
    },
    "Prayogamala-Purvabhagam_Devanagari.html": {
        "title": "Prayogamala — Purvabhagam (Devanagari)",
        "category": "Prayoga",
        "description": "Purvabhagam liturgical procedures and chant sequences.",
        "featured": True,
    },
    "prayogamala-Uttarabhagam_Devanagari.html": {
        "title": "Prayogamala — Uttarabhagam (Devanagari)",
        "category": "Prayoga",
        "description": "Uttarabhagam liturgical procedures and chant sequences.",
        "featured": True,
    },
    "Prayogamala - Purvabhagam.html": {
        "title": "Prayogamala — Purvabhagam (Standard)",
        "category": "Prayoga",
        "description": "Standard edition of Purvabhagam prayoga text.",
        "featured": False,
    },
    "Prayogamala - Uttarabhagam.html": {
        "title": "Prayogamala — Uttarabhagam (Standard)",
        "category": "Prayoga",
        "description": "Standard edition of Uttarabhagam prayoga text.",
        "featured": False,
    },
    "Prayogamala-UB.html": {
        "title": "Prayogamala UB (Compact)",
        "category": "Prayoga",
        "description": "Compact edition of Uttarabhagam prayoga.",
        "featured": False,
    },
    "Prayogamala - PB.html": {
        "title": "Prayogamala PB (Compact)",
        "category": "Prayoga",
        "description": "Compact edition of Purvabhagam prayoga.",
        "featured": False,
    },
    "Sooktamala_Devanagari.html": {
        "title": "Sooktamala (Devanagari) — Complete",
        "category": "Sooktamala",
        "description": "Comprehensive anthology of Vedic Sooktams from Jaimineeya tradition.",
        "featured": True,
    },
    "Sooktamala.html": {
        "title": "Sooktamala (Standard Reader)",
        "category": "Sooktamala",
        "description": "Anthology of Vedic Sooktams in standard rendering.",
        "featured": False,
    },
    "nakshatra-sooktam.html": {
        "title": "Nakshatra Sooktam (Devanagari)",
        "category": "Special",
        "description": "Nakshatra Sooktam chant with swaras.",
        "featured": False,
    },
    "taittiriya_upanishad_sanskrit.html": {
        "title": "Taittiriya Upanishad (Sanskrit)",
        "category": "Special",
        "description": "Taittiriya Upanishad reader with Vedic accents.",
        "featured": False,
    },
    "Ritu_shanti_japam.html": {
        "title": "Ritu Shanti Japam (Devanagari)",
        "category": "Special",
        "description": "Ritu Shanti Japam prayer and chanting sequence.",
        "featured": False,
    },
    "Ritu Shanti Japam.html": {
        "title": "Ritu Shanti Japam (Standard)",
        "category": "Special",
        "description": "Standard edition of Ritu Shanti Japam.",
        "featured": False,
    },
    "Ritu Shanti Japam - Samam only.html": {
        "title": "Ritu Shanti Japam — Samam Only",
        "category": "Special",
        "description": "Samam chants for Ritu Shanti Japam.",
        "featured": False,
    },
    "Samam_Devanagari.html": {
        "title": "Samam (Devanagari) — Complete Chants",
        "category": "Samam / Rik",
        "description": "Complete collection of Jaimineeya Samam chanting verses in Devanagari.",
        "featured": True,
    },
    "Rik_Devanagari.html": {
        "title": "Rik (Devanagari) — Source Verses",
        "category": "Samam / Rik",
        "description": "Source Rik verses with accents in Devanagari.",
        "featured": False,
    },
    "Samam_Devanagari_Unicode.html": {
        "title": "Samam (Devanagari Unicode Standard)",
        "category": "Samam / Rik",
        "description": "Devanagari Samam text formatted with standard Unicode codepoints.",
        "featured": False,
    },
    "Rik_Devanagari_Unicode.html": {
        "title": "Rik (Devanagari Unicode Standard)",
        "category": "Samam / Rik",
        "description": "Devanagari Rik text formatted with standard Unicode codepoints.",
        "featured": False,
    },
    "Samam_NoMeta_Devanagari.html": {
        "title": "Samam (Devanagari, No Metadata)",
        "category": "Samam / Rik",
        "description": "Pure chanting text of Devanagari Samam.",
        "featured": False,
    },
    "Rik_NoMeta_Devanagari.html": {
        "title": "Rik (Devanagari, No Metadata)",
        "category": "Samam / Rik",
        "description": "Pure source verses of Devanagari Rik.",
        "featured": False,
    },
    "Devanagari_Devanagari_Unicode.html": {
        "title": "Devanagari Unicode Text Set",
        "category": "Samam / Rik",
        "description": "Comprehensive Unicode compilation in Devanagari.",
        "featured": False,
    },

    # Malayalam Readers
    "Samam_Malayalam_Samam.html": {
        "title": "Samam (Malayalam) — Fine-Tuned Edition",
        "category": "Samam / Rik",
        "description": "Fine-tuned canonical Malayalam Jaimineeya Samam reader featuring JaimineeyaSwara typography and optimized layout.",
        "featured": True,
    },
    "Samam_kpully_Malayalam_Samam.html": {
        "title": "Samam (Malayalam, Kpully Baseline)",
        "category": "Samam / Rik",
        "description": "Kpully baseline edition of Malayalam Samam chants.",
        "featured": True,
    },
    "Samam_kpully_Malayalam.html": {
        "title": "Samam (Malayalam, KPully Edition)",
        "category": "Samam / Rik",
        "description": "KPully baseline edition of Malayalam Samam chants featuring KPully swara modifier glyphs.",
        "featured": True,
    },
    "Samam_Malayalam_legacy_Samam.html": {
        "title": "Samam (Malayalam, Legacy Reader)",
        "category": "Samam / Rik",
        "description": "Legacy reader baseline for comparison and archival verification.",
        "featured": False,
    },
    "Samhita_Malayalam.html": {
        "title": "Samhita (Malayalam) — Complete Edition",
        "category": "Samhita",
        "description": "Full Jaimineeya Samhita reader rendered in Malayalam script with swaras.",
        "featured": True,
    },
    "Samhita_Malayalam_v2_Malayalam.html": {
        "title": "Samhita (Malayalam v2)",
        "category": "Samhita",
        "description": "Alternate v2 compilation of Malayalam Samhita.",
        "featured": False,
    },
    "Samam_Malayalam.html": {
        "title": "Samam (Malayalam Script)",
        "category": "Samam / Rik",
        "description": "Complete Samam chanting text in Malayalam script.",
        "featured": False,
    },
    "Rik_Malayalam.html": {
        "title": "Rik (Malayalam Script)",
        "category": "Samam / Rik",
        "description": "Complete Rik verses rendered in Malayalam script.",
        "featured": False,
    },
    "Samam_Malayalam_Rik.html": {
        "title": "Samam & Rik (Malayalam)",
        "category": "Samam / Rik",
        "description": "Paired Samam and Rik verses in Malayalam script.",
        "featured": False,
    },
    "Samam_Malayalam_Samam_NoMeta.html": {
        "title": "Samam (Malayalam, No Metadata)",
        "category": "Samam / Rik",
        "description": "Pure Malayalam Samam chanting text without headings.",
        "featured": False,
    },
    "Samam_Malayalam_Rik_NoMeta.html": {
        "title": "Rik (Malayalam, No Metadata)",
        "category": "Samam / Rik",
        "description": "Pure Malayalam Rik text without headings.",
        "featured": False,
    },
    "Samam_NoMeta_Malayalam.html": {
        "title": "Samam NoMeta (Malayalam)",
        "category": "Samam / Rik",
        "description": "Comprehensive Malayalam chanting text with minimal markup.",
        "featured": False,
    },
    "Samam_NoMeta_Malayalam_v2_Samam_NoMeta_Malayalam.html": {
        "title": "Samam NoMeta v2 (Malayalam)",
        "category": "Samam / Rik",
        "description": "Version 2 release of Malayalam Samam chants without metadata.",
        "featured": False,
    },
    "Samam_NoMeta_Malayalam_v2_Rik_NoMeta_Malayalam.html": {
        "title": "Rik NoMeta v2 (Malayalam)",
        "category": "Samam / Rik",
        "description": "Version 2 release of Malayalam Rik verses without metadata.",
        "featured": False,
    },
}

def hash_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def infer_category(filename, script):
    fn = filename.lower()
    if "samhita" in fn:
        return "Samhita"
    if "aaranam" in fn or "aranam" in fn or "aranyam" in fn:
        return "Aaranam"
    if "prayoga" in fn:
        return "Prayoga"
    if "sooktamala" in fn:
        return "Sooktamala"
    if "nakshatra" in fn or "taittiriya" in fn or "ritu" in fn:
        return "Special"
    return "Samam / Rik"

def format_size(bytes_val):
    if bytes_val >= 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.1f} MB"
    return f"{bytes_val / 1024:.0f} KB"

def build_catalog_page(items):
    categories = ["All", "Featured", "Devanagari", "Malayalam", "Samhita", "Aaranam", "Prayoga", "Sooktamala", "Samam / Rik", "Special"]
    total_files = len(items)
    dev_count = sum(1 for x in items if x["script"] == "Devanagari")
    mal_count = sum(1 for x in items if x["script"] == "Malayalam")
    total_size_mb = sum(x["bytes"] for x in items) / (1024 * 1024)
    items_json = json.dumps(items)

    pills_html = " ".join(f'<button class="filter-btn {("active" if cat=="All" else "")}" data-filter="{cat}">{cat}</button>' for cat in categories)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
            max-width: 1300px;
            width: 100%;
            margin: 0 auto;
            padding: 2rem 1.5rem;
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
            grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
            gap: 1.5rem;
        }}

        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border-card);
            border-radius: var(--radius-md);
            padding: 1.5rem;
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
            background: linear-gradient(145deg, rgba(229, 169, 60, 0.06) 0%, var(--bg-card) 60%);
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
            font-size: 1.18rem;
            font-weight: 700;
            color: var(--text-main);
            margin-bottom: 0.4rem;
            line-height: 1.4;
        }}

        .card-desc {{
            font-size: 0.9rem;
            color: var(--text-muted);
            margin-bottom: 1.2rem;
            flex-grow: 1;
        }}

        .card-filename {{
            font-family: monospace;
            font-size: 0.78rem;
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
            padding: 9px 16px;
            border-radius: var(--radius-sm);
            font-size: 0.9rem;
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
        <div class="badge-pill">Independent Web Readers</div>
        <h1>जैमिनीय सामवेदः</h1>
        <p class="subtitle">Self-Contained Standalone HTML Readers with High-Fidelity Vedic Accents (Devanagari &amp; Malayalam scripts)</p>
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
                <input type="text" id="searchInput" class="search-input" placeholder="Search by title, text, category, or file name (e.g. 'kpully', 'samhita', 'purvabhagam', 'malayalam')...">
            </div>
            <div class="filter-pills" id="filterPills">
                {pills_html}
            </div>
        </div>

        <div class="grid" id="readerGrid"></div>
        <div class="no-results" id="noResults" style="display: none;">
            <h3>No editions matched your search</h3>
            <p>Try adjusting your search terms or filter selection.</p>
        </div>
    </main>

    <footer>
        <p>जैमिनीय सामवेद प्रकाशनम् | Standalone Editions archive served directly via GitHub Pages.</p>
        <p style="margin-top: 4px;">Each reader is 100% self-contained with embedded swara glyph fonts and typography styles.</p>
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
                if (!['All', 'Featured', 'Devanagari', 'Malayalam'].includes(currentFilter)) {{
                    if (item.category !== currentFilter) return false;
                }}

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
    print(f"Syncing standalone HTML files from: {SOURCE_DIR}")
    print(f"Target directory: {TARGET_DIR}")

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    target_dev = TARGET_DIR / "Devanagari"
    target_mal = TARGET_DIR / "Malayalam"
    target_dev.mkdir(exist_ok=True)
    target_mal.mkdir(exist_ok=True)

    items = []
    seen_hashes = {}

    for script_folder, target_folder in [("Devanagari", target_dev), ("Malayalam", target_mal)]:
        src_folder = SOURCE_DIR / script_folder
        if not src_folder.exists():
            continue

        for file_path in sorted(src_folder.iterdir()):
            filename = file_path.name
            if not filename.endswith(".html"):
                continue
            if filename.startswith("test_") or filename.startswith("~$") or "Copy" in filename:
                continue
            if filename in ["Samhita_kpully_Devanagari_Devanagari.html", "Samam_Malayalam_Samam_Malayalam.html", "Samam_Malayalam_Malayalam.html"]:
                continue

            file_hash = hash_file(file_path)
            if file_hash in seen_hashes:
                prev_name = seen_hashes[file_hash]
                print(f"Skipping duplicate: {filename} (identical to {prev_name})")
                continue
            seen_hashes[file_hash] = filename

            dest_file = target_folder / filename
            shutil.copy2(file_path, dest_file)
            file_bytes = dest_file.stat().st_size

            meta = METADATA.get(filename, {})
            title = meta.get("title", filename.replace(".html", "").replace("_", " "))
            category = meta.get("category", infer_category(filename, script_folder))
            description = meta.get("description", f"Standalone Vedic chant reader in {script_folder} script.")
            featured = meta.get("featured", False)

            items.append({
                "filename": filename,
                "script": script_folder,
                "category": category,
                "title": title,
                "description": description,
                "featured": featured,
                "bytes": file_bytes,
                "size_fmt": format_size(file_bytes),
                "rel_url": f"{script_folder}/{filename}",
            })

    items.sort(key=lambda x: (not x["featured"], x["script"], x["title"]))

    print(f"Copied {len(items)} standalone HTML readers.")

    index_html = build_catalog_page(items)
    index_path = TARGET_DIR / "index.html"
    index_path.write_text(index_html, encoding="utf-8")
    print(f"Created catalog index at: {index_path}")

if __name__ == "__main__":
    main()

