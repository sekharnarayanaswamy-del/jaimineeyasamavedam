"""Generate comprehensive Publication Blog in Markdown (.md) and Standalone HTML (.html)
for the Jaimineeya Samaveda Malayalam Digitization Project.
"""

import base64
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONT_PATH = ROOT / "fonts" / "JaimineeyaSwara.ttf"
OUT_MD = ROOT / "docs" / "blog" / "Malayalam_JSV_Publication_Blog.md"
OUT_HTML = ROOT / "docs" / "blog" / "Malayalam_JSV_Publication_Blog.html"
ARTIFACT_DIR = Path(r"C:\Users\sekha\.gemini\antigravity-ide\brain\33a78242-ade0-47ff-b909-95b423204936")

# 1. Base64 font encoding
b64_font = ""
if FONT_PATH.exists():
    with open(FONT_PATH, "rb") as f:
        b64_font = base64.b64encode(f.read()).decode("ascii")

# 2. Markdown Blog Post Content
md_content = """# Revitalizing the Jaimineeya Samaveda in Malayalam Script: Typographic Innovation, Custom Font Engineering, and a Unified Multi-Format Publishing Pipeline

> **By the Jaimineeya Samaveda Digitization Project**  
> *Published: August 2026*  
> *Repository: [github.com/sekharnarayanaswamy-del/jaimineeyasamavedam](https://github.com/sekharnarayanaswamy-del/jaimineeyasamavedam)*

---

## 1. Executive Summary & The Sacred Heritage

The **Jaimineeya Shakha** of the *Samaveda* (*Jaiminīya Sāmavedam*) is one of the most ancient, musically intricate, and geographically endangered oral traditions of Vedic chanting. While the Kauthuma and Ranayaniya traditions are widely published across India, the authentic musical recitation of the Jaimineeya tradition has been preserved almost exclusively through the guru-shishya lineages of the **Namboodiri tradition of Kerala** and select Tamil Nadu lineages.

Unlike standard Vedic texts that employ simple accent strokes (Udatta / Anudatta / Svarita), the Jaimineeya Samaveda employs a sophisticated two-dimensional notation system:
1. **Primary Svara Pitch Markers:** Subscript letters (traditionally Grantha or Malayalam characters) that specify the exact pitch movements (such as *Avaroham*, *Anvangulyam*, *Udgamam*, *Yanam*, and *Plutam*).
2. **Svara Modifiers:** Structural performance indicators that qualify the chant—including multi-syllable spanning melodic arches, peak carets, upper shoulder dots, descending tone slashes, and phrasing dandas.

Until today, producing a faithful, publication-grade digital edition in **Malayalam script** remained an unsolved challenge. Traditional typesetting engines suffered from severe character overlapping, missing manuscript ligatures, clipping of tone markers, and an inability to represent multi-syllable musical bridges cleanly.

Today, we are proud to announce the **complete, end-to-end digital publishing ecosystem for the Jaimineeya Samaveda in Malayalam Script**, delivering high-fidelity outputs across:
- 🌐 **Interactive Web Edition (HTML5)** with responsive flexbox stacking and live word-bridging modifiers.
- 📄 **Archival Print Edition (LuaLaTeX / PDF)** with mathematical sub-point kerning and vector-perfect typography.
- 📝 **Universal Unicode Plaintext (.txt)** with standard Grantha codepoints and intuitive non-combining modifier symbols.

---

## 2. The Typographic & Technical Challenge

Transliterating Jaimineeya Samavedam from traditional palm-leaf manuscripts and Devanagari baselines into digital Malayalam presented three fundamental hurdles:

### Hurdle 1: The Grantha-Malayalam Hybrid Conundrum
Traditional Kerala Jaimineeya manuscripts write the base sacred text (*Mantrakshara*) in **Malayalam script**, while the overhead pitch markers (*Svaras*) are rendered in archaic **Grantha script** with specific regional overrides:
- **Vedic *Pla* (പ്ല):** A custom composite base glyph combining Grantha *Pa* with a Malayalam subscript *La*, distinct from standard classical Grantha.
- **Manuscript *Sha* (ശ):** The Jaimineeya tradition specifically employs the Malayalam base letter **ശ** (`U+0D36`) coupled with detached Grantha vowel arms (such as *Shi* 𑌶𑌿, *Shii* 𑌶𑍀, and *Shaa* ശാ) rather than standard Grantha *Śa* (𑌶).

Standard system fonts lack these ligature forms, resulting in missing glyph boxes (`[?]`) or unsightly broken dotted circles (`◌`).

### Hurdle 2: Multi-Syllable Spanning Swara Modifiers
Several crucial musical modifiers in the Jaimineeya tradition—such as **Modifier (A) Syllable Spanning Arc** and **Modifier (D) Chevron Roof**—do not belong to a single syllable. They visually and musically **span across the boundary between two adjacent words** (e.g. bridging `ഹോ` and `ബാ` / `ഹോ` and `ഇഴാ`).

Standard typesetting engines provide no native mechanism for anchoring a glyph at the right edge of one syllable and stretching it over the whitespace to the next.

### Hurdle 3: Multi-Format Visual Uniformity
Publishing across Web, Print PDF, and Plaintext required maintaining identical visual conventions and color hierarchies across all platforms:
- **Mantrakshara (Base Text):** Deep Typography Black (`#0f172a`).
- **Swara Pitch Markers:** Vedic Sacred Red (`#c62828`).
- **Swara Modifiers:** Performance Dark Blue (`#002171`).

---

## 3. Engineering Innovations

### Innovation 1: The `JaimineeyaSwara.ttf` Custom OpenType Font
To establish absolute typographic control, we engineered a dedicated OpenType font, **`JaimineeyaSwara.ttf`**, containing:
- **19 Ayugma Pure Grantha Bases (`A01`–`A19`):** Full coverage of *Avaroham* (𑌕), *Anvangulyam* (𑌖), *Udgamam* (𑌚), *Yanam* (𑌟), *Namanam* (𑌣), *Aavarttam* (𑌤), *Utthanam* (𑌥), *Kshepanam* (𑌪), *Plutam* (\uE020), *Tra* (\uE01D), and *Kra* (\uE01E).
- **10 Custom Manuscript Ligatures (`LIG-01`–`LIG-10`):** Including *Shaa* (`\uE010`), *Shi* (`\uE011`), *Shii* (`\uE012`), *Sha-Virama* (`\uE013`), *Plaa* (`\uE021`), *Pli* (`\uE022`), *Plii* (`\uE023`), *Shruu* (`\uE027`), *Shrr* (`\uE028`), and *Nna+U* (`\uE029`).
- **8 Canonical Vedic Swara Modifiers (`MOD-A`–`MOD-H`):** Built with zero-advance bounding boxes for clean dynamic overlay.

### Innovation 2: The Canonical 8 Vedic Swara Modifiers

| ID | Shortcut | Modifier Name | Glyph Codepoint | Visual Position | Lakshana Role |
| :--- | :---: | :--- | :---: | :---: | :--- |
| **MOD-A** | `(A)` / `(⁀)` | **Syllable Spanning Arc (Tie)** | `\uE004` / `U+2040` | Stacked Above (2 Syllables) | Overhead curved arch spanning across two words for connected tone transition. |
| **MOD-B** | `(B)` / `(∧)` | **Peak Elevation Caret** | `\uE005` / `U+2227` | Stacked Above (2 Syllables) | Elevated melodic peak over syllable transition. |
| **MOD-C** | `(C)` / `(·)` | **Shoulder Pause Dot** | `\uE001` / `U+00B7` | Upper-Right Shoulder | High pause dot attached to the upper shoulder of the preceding syllable. |
| **MOD-D** | `(D)` / `(Ʌ)` | **Chevron Roof** | `\uE006` / `U+0245` | Stacked Above (2 Syllables) | Roof-tone modulation spanning across words. |
| **MOD-E** | `(E)` / `(┃)` | **Phrasing Heavy Danda** | `\uE002` / `U+2503` | Inline | Structural major cadence division. |
| **MOD-F** | `(F)` / `(╷)` | **Light Vertical Line** | `\uE002` / `U+2577` | Inline | Minor phrasing tone separator. |
| **MOD-G** | `(G)` / `(\)` | **Descending Tone Slash** | `\uE003` / `U+005C` | Stacked Below | Downward falling pitch attached to the bottom-center of the preceding consonant. |
| **MOD-H** | `(H)` / `(\\|)` | **Overhead Swarita** | `\uE00C` / `U+007C` | Stacked Above | Vertical upper tone stroke situated directly on top of the base syllable. |

### Innovation 3: Dynamic Right-Edge Modifier Anchoring (HTML / CSS)
In the HTML presentation layer, spanning modifiers (Mod-A, Mod-B, Mod-D) are dynamically anchored to the preceding syllable using responsive CSS transforms:

```css
.swara-mod.mod-a, .swara-mod.mod-d {
    position: absolute;
    top: -0.28em;
    left: 100%;
    transform: translateX(-40%);
    pointer-events: none;
}
```

This guarantees that the arch or chevron cleanly bridges the gap between words regardless of screen size, font scale, or syllable width!

---

## 4. The 3-Step Proofreading & Correction Workflow

To enable Vedic scholars and editors to proofread and correct the text without technical friction, we designed a transparent, text-first workflow:

```mermaid
graph LR
    A["1. Export Standard Unicode Plaintext<br/>(Samhita_Malayalam_Unicode.txt)"] --> B["2. Hand-Annotate Swara Modifiers<br/>(A..H in text editor)"]
    B --> C["3. Multi-Format Build Pipeline<br/>(HTML, PDF, Web)"]
```

1. **Step 1: Automated Transliteration Baseline:** The Devanagari Samhita text is transliterated to Malayalam base letters with Grantha swaras and English verse numerals (`॥ 1 ॥`).
2. **Step 2: Scholar Annotation in Plaintext:** The editor opens `Samhita_Malayalam_Unicode.txt` in any standard text editor and inserts intuitive modifier notations:
   ```text
   ഹോ(𑌖)(A) ബാ(𑌪𑍍𑌲) മാ(𑌕)(B) യാ ഓ(𑌤)(C) ഗ്നാ(𑌤) ബാ(𑌪𑍍𑌲)(G) ദാ(𑌚𑌿)(H)
   ```
3. **Step 3: Multi-Format Compilation:** Running `python src/render_pdf.py` instantly parses the annotations and updates the HTML portal, the LuaLaTeX print edition, and the live catalog.

---

## 5. Live Typographic Previews & Verification

### The High-Resolution Glyph Inventory
![Jaimineeya Swara Font Inventory](glyph_grid_JaimineeyaSwara.png)

### The Interactive HTML Review Catalog
Scholars and developers can inspect all 8 modifiers, 19 Ayugma bases, and 229 full corpus markers in real time via [`glyph_table.html`](glyph_table.html).

---

## 6. Open Source & Future Directions

All font source files, templates, renderers, and transliteration scripts are open-source under permissive licenses:
- **Repository:** [https://github.com/sekharnarayanaswamy-del/jaimineeyasamavedam](https://github.com/sekharnarayanaswamy-del/jaimineeyasamavedam)
- **Key Files:**
  - Font: `fonts/JaimineeyaSwara.ttf`
  - HTML Template: `templates/html/Malayalam_main_html.template`
  - Rendering Engine: `src/render_pdf.py`
  - Spec & Developer Guide: `Malayalam_JSV/spec.md`

We invite Vedic scholars, typographers, and digital humanities researchers to explore the repository, submit corrections, and help preserve this invaluable oral heritage for generations to come.
"""

# 3. HTML Blog Post Content (Rich Modern Styling with Embedded Font)
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Revitalizing the Jaimineeya Samaveda in Malayalam Script | Publication Blog</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Serif+Malayalam:wght@400;500;600;700&family=Fira+Code:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    @font-face {{
        font-family: 'JaimineeyaSwara';
        src: url('data:font/truetype;charset=utf-8;base64,{b64_font}') format('truetype');
    }}

    :root {{
        --bg-page: #f8fafc;
        --bg-card: #ffffff;
        --text-primary: #0f172a;
        --text-secondary: #475569;
        --text-muted: #64748b;
        --brand-blue: #002171;
        --brand-blue-light: #1e3a8a;
        --swara-red: #c62828;
        --accent-teal: #0d9488;
        --border-subtle: #e2e8f0;
        --code-bg: #0f172a;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background: var(--bg-page);
        color: var(--text-primary);
        line-height: 1.7;
        font-size: 17px;
        padding-bottom: 80px;
    }}

    /* Top Hero Header */
    .hero-banner {{
        background: linear-gradient(135deg, #001a54 0%, #002171 50%, #1e3a8a 100%);
        color: white;
        padding: 80px 20px 60px;
        text-align: center;
        position: relative;
        overflow: hidden;
        border-bottom: 4px solid #3b82f6;
    }}
    .hero-banner::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: radial-gradient(circle at 20% 30%, rgba(239, 68, 68, 0.15), transparent 40%),
                    radial-gradient(circle at 80% 70%, rgba(59, 130, 246, 0.2), transparent 50%);
        pointer-events: none;
    }}
    .hero-content {{
        max-width: 960px;
        margin: 0 auto;
        position: relative;
        z-index: 1;
    }}
    .badge-pill {{
        display: inline-block;
        background: rgba(255, 255, 255, 0.15);
        color: #bfdbfe;
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 6px 16px;
        border-radius: 20px;
        margin-bottom: 20px;
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }}
    h1 {{
        font-size: 42px;
        font-weight: 800;
        letter-spacing: -1px;
        line-height: 1.25;
        margin-bottom: 20px;
    }}
    .hero-subtitle {{
        font-size: 20px;
        color: #cbd5e1;
        line-height: 1.5;
        max-width: 820px;
        margin: 0 auto 28px;
    }}
    .meta-bar {{
        display: flex;
        justify-content: center;
        gap: 24px;
        font-size: 14px;
        color: #94a3b8;
        font-weight: 500;
    }}

    /* Main Container */
    .article-container {{
        max-width: 900px;
        margin: -30px auto 0;
        background: var(--bg-card);
        border-radius: 16px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.02);
        padding: 50px 60px;
        border: 1px solid var(--border-subtle);
    }}

    h2 {{
        font-size: 28px;
        font-weight: 800;
        color: var(--brand-blue);
        margin: 45px 0 18px;
        padding-bottom: 10px;
        border-bottom: 2px solid #e2e8f0;
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    h3 {{
        font-size: 22px;
        font-weight: 700;
        color: #1e293b;
        margin: 30px 0 12px;
    }}
    p {{
        margin-bottom: 20px;
        color: #334155;
    }}

    /* Callout Boxes */
    .callout {{
        background: #f0fdf4;
        border-left: 4px solid #16a34a;
        padding: 20px 24px;
        border-radius: 0 12px 12px 0;
        margin: 28px 0;
    }}
    .callout-title {{
        font-weight: 700;
        color: #166534;
        font-size: 16px;
        margin-bottom: 6px;
    }}

    .callout-challenge {{
        background: #fef2f2;
        border-left: 4px solid #dc2626;
        padding: 20px 24px;
        border-radius: 0 12px 12px 0;
        margin: 28px 0;
    }}
    .callout-challenge .callout-title {{
        color: #991b1b;
    }}

    /* Interactive Live Mantra Preview Cards */
    .preview-card {{
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        padding: 24px;
        margin: 30px 0;
        text-align: center;
    }}
    .preview-card-title {{
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--text-muted);
        font-weight: 700;
        margin-bottom: 16px;
    }}
    .mantra-display {{
        display: inline-flex;
        align-items: flex-end;
        background: white;
        padding: 16px 28px;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
    }}
    .mantra-word {{
        display: inline-flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-end;
        vertical-align: bottom;
        position: relative;
        font-size: 1.8rem;
    }}
    .swara-text {{
        font-family: 'JaimineeyaSwara', serif;
        font-size: 1.15rem;
        color: var(--swara-red);
        line-height: 1;
        margin-bottom: 4px;
        font-weight: bold;
        min-height: 1.1em;
        user-select: none;
    }}
    .mantra-text {{
        font-family: 'Noto Serif Malayalam', serif;
        font-size: 1.8rem;
        font-weight: 500;
        line-height: 1.1;
        color: var(--text-primary);
        position: relative;
    }}
    .word-space {{
        width: 0.50em;
        display: inline-block;
    }}
    .swara-mod {{
        color: var(--brand-blue);
        font-family: 'JaimineeyaSwara', serif;
        font-weight: bold;
    }}
    .swara-mod.mod-a {{
        position: absolute;
        top: -0.28em;
        left: 100%;
        transform: translateX(-40%);
        font-size: 1.25rem;
    }}
    .swara-mod.mod-b {{
        position: absolute;
        top: -0.32em;
        left: 100%;
        transform: translateX(-40%);
        font-size: 1.25rem;
    }}
    .swara-mod.mod-c {{
        position: absolute;
        top: -0.15em;
        right: -0.35em;
        font-size: 1.15rem;
    }}
    .swara-mod.mod-g {{
        position: absolute;
        bottom: -0.38em;
        left: 28%;
        transform: translateX(-50%);
        font-size: 1.35rem;
    }}
    .swara-mod.mod-h {{
        position: absolute;
        top: -0.35em;
        left: 50%;
        transform: translateX(-50%);
        font-size: 1.25rem;
    }}

    /* Tables */
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 25px 0;
        font-size: 15px;
    }}
    th {{
        background: #f1f5f9;
        color: #334155;
        font-weight: 700;
        text-align: left;
        padding: 12px 16px;
        border-bottom: 2px solid #cbd5e1;
    }}
    td {{
        padding: 12px 16px;
        border-bottom: 1px solid #e2e8f0;
        vertical-align: middle;
    }}
    tr:hover td {{
        background: #f8fafc;
    }}
    .glyph-sample {{
        font-family: 'JaimineeyaSwara', serif;
        font-size: 28px;
        color: var(--brand-blue);
        font-weight: bold;
    }}
    .badge-above {{ background: #e0e7ff; color: #3730a3; padding: 4px 8px; border-radius: 4px; font-weight: 700; font-size: 11px; text-transform: uppercase; }}
    .badge-below {{ background: #fef3c7; color: #92400e; padding: 4px 8px; border-radius: 4px; font-weight: 700; font-size: 11px; text-transform: uppercase; }}
    .badge-shoulder {{ background: #f3e8ff; color: #6b21a8; padding: 4px 8px; border-radius: 4px; font-weight: 700; font-size: 11px; text-transform: uppercase; }}
    .badge-inline {{ background: #f1f5f9; color: #334155; padding: 4px 8px; border-radius: 4px; font-weight: 700; font-size: 11px; text-transform: uppercase; }}

    /* Code Blocks */
    pre {{
        background: var(--code-bg);
        color: #f8fafc;
        padding: 20px;
        border-radius: 10px;
        font-family: 'Fira Code', monospace;
        font-size: 14px;
        line-height: 1.6;
        overflow-x: auto;
        margin: 24px 0;
    }}
    code {{
        font-family: 'Fira Code', monospace;
        background: #f1f5f9;
        color: #0f172a;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 14px;
    }}
    pre code {{
        background: transparent;
        color: inherit;
        padding: 0;
    }}

    /* Workflow Stepper */
    .step-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 18px;
        margin: 28px 0;
    }}
    .step-card {{
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 22px 18px;
        text-align: center;
        position: relative;
    }}
    .step-num {{
        width: 34px;
        height: 34px;
        background: var(--brand-blue);
        color: white;
        font-weight: 800;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 12px;
    }}
    .step-title {{
        font-size: 16px;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 6px;
    }}
    .step-desc {{
        font-size: 13px;
        color: var(--text-muted);
        line-height: 1.4;
    }}

    /* Footer */
    footer {{
        margin-top: 50px;
        padding-top: 30px;
        border-top: 1px solid #e2e8f0;
        text-align: center;
        font-size: 14px;
        color: var(--text-muted);
    }}
    a {{ color: #2563eb; text-decoration: none; font-weight: 600; }}
    a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>

<div class="hero-banner">
    <div class="hero-content">
        <span class="badge-pill">Vedic Digital Humanities &bull; Open Source Typography</span>
        <h1>Revitalizing the Jaimineeya Samaveda in Malayalam Script</h1>
        <div class="hero-subtitle">
            Typographic Innovation, Custom Grantha Font Engineering, and a Unified Multi-Format Publishing Pipeline for Sacred Kerala Vedic Chants.
        </div>
        <div class="meta-bar">
            <span>📅 August 2026</span>
            <span>🏛️ Jaimineeya Samaveda Digitization Project</span>
            <span>📜 Open Access</span>
        </div>
    </div>
</div>

<article class="article-container">

    <div class="callout">
        <div class="callout-title">The Sacred Jaimineeya Shakha Heritage</div>
        The <em>Jaiminīya Sāmaveda</em> represents one of the oldest living musical traditions in the world. Preserved by the Namboodiri Jaimineeyas of Kerala, its two-dimensional notation encodes delicate pitch contours (*Avaroham*, *Udgamam*, *Plutam*) and structural performance modifiers that have challenged digital typesetting for decades.
    </div>

    <h2>1. The Typographic Challenge</h2>
    <p>
        Rendering authentic Malayalam Jaimineeya Samaveda requires solving three distinct challenges:
    </p>
    <ul>
        <li><strong>Subscript Svara Markers:</strong> 19 distinct pitch markers written in archaic Grantha script layered directly over Malayalam syllables.</li>
        <li><strong>Manuscript Overrides:</strong> Kerala manuscripts use a unique hybrid <em>Pla</em> base (combining Grantha Pa with Malayalam subscript La) and a Malayalam <em>Sha</em> base with detached Grantha vowel arms.</li>
        <li><strong>Multi-Syllable Spanning Modifiers:</strong> Tonal arches and roof chevrons that visually span across the inter-word space between adjacent syllables.</li>
    </ul>

    <h2>2. Live Typographic Demonstration</h2>
    <p>
        The following live render is generated directly using our custom open-source webfont <code>JaimineeyaSwara.ttf</code>:
    </p>

    <div class="preview-card">
        <div class="preview-card-title">Live Flexbox Stacking & Word-Bridging Modifiers Preview</div>
        <div class="mantra-display">
            <!-- Word 1 with Mod-A Arch spanning to Word 2 -->
            <span class="mantra-word">
                <span class="swara-text">𑌖</span>
                <span class="mantra-text">ഹോ<span class="swara-mod mod-a">&#xE004;</span></span>
            </span>
            <span class="word-space">&nbsp;</span>
            <!-- Word 2 with Mod-G descending tone slash -->
            <span class="mantra-word">
                <span class="swara-text">𑌪𑍍𑌲</span>
                <span class="mantra-text">ബാ<span class="swara-mod mod-g">&#xE003;</span></span>
            </span>
            <span class="word-space">&nbsp;</span>
            <!-- Word 3 with Mod-C shoulder dot -->
            <span class="mantra-word">
                <span class="swara-text">𑌤</span>
                <span class="mantra-text">ഓ<span class="swara-mod mod-c">&#xE001;</span></span>
            </span>
            <span class="word-space">&nbsp;</span>
            <!-- Word 4 with Mod-H overhead swarita -->
            <span class="mantra-word">
                <span class="swara-text">𑌚𑌿</span>
                <span class="mantra-text">ദാ<span class="swara-mod mod-h">&#xE00C;</span></span>
            </span>
        </div>
    </div>

    <h2>3. The 8 Canonical Vedic Swara Modifiers</h2>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Shortcut</th>
                <th>Modifier Name</th>
                <th style="text-align:center;">Glyph</th>
                <th>Codepoints</th>
                <th>Position</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>MOD-A</strong></td>
                <td><code>(A) / (⁀)</code></td>
                <td>Syllable Spanning Arc (Tie)</td>
                <td style="text-align:center;" class="glyph-sample">&#xE004;</td>
                <td><code>U+E004 / U+2040</code></td>
                <td><span class="badge-above">Above (2 Syllables)</span></td>
            </tr>
            <tr>
                <td><strong>MOD-B</strong></td>
                <td><code>(B) / (∧)</code></td>
                <td>Peak Elevation Caret</td>
                <td style="text-align:center;" class="glyph-sample">&#xE005;</td>
                <td><code>U+E005 / U+2227</code></td>
                <td><span class="badge-above">Above (2 Syllables)</span></td>
            </tr>
            <tr>
                <td><strong>MOD-C</strong></td>
                <td><code>(C) / (·)</code></td>
                <td>Shoulder Pause Dot</td>
                <td style="text-align:center;" class="glyph-sample">&#xE001;</td>
                <td><code>U+E001 / U+00B7</code></td>
                <td><span class="badge-shoulder">Shoulder</span></td>
            </tr>
            <tr>
                <td><strong>MOD-D</strong></td>
                <td><code>(D) / (Ʌ)</code></td>
                <td>Chevron Roof</td>
                <td style="text-align:center;" class="glyph-sample">&#xE006;</td>
                <td><code>U+E006 / U+0245</code></td>
                <td><span class="badge-above">Above (2 Syllables)</span></td>
            </tr>
            <tr>
                <td><strong>MOD-E</strong></td>
                <td><code>(E) / (┃)</code></td>
                <td>Phrasing Heavy Danda</td>
                <td style="text-align:center;" class="glyph-sample">&#xE002;</td>
                <td><code>U+E002 / U+2503</code></td>
                <td><span class="badge-inline">Inline</span></td>
            </tr>
            <tr>
                <td><strong>MOD-F</strong></td>
                <td><code>(F) / (╷)</code></td>
                <td>Light Vertical Line</td>
                <td style="text-align:center;" class="glyph-sample">&#x2577;</td>
                <td><code>U+E002 / U+2577</code></td>
                <td><span class="badge-inline">Inline</span></td>
            </tr>
            <tr>
                <td><strong>MOD-G</strong></td>
                <td><code>(G) / (\\)</code></td>
                <td>Descending Tone Slash</td>
                <td style="text-align:center;" class="glyph-sample">&#xE003;</td>
                <td><code>U+E003 / U+005C</code></td>
                <td><span class="badge-below">Center Bottom</span></td>
            </tr>
            <tr>
                <td><strong>MOD-H</strong></td>
                <td><code>(H) / (|)</code></td>
                <td>Overhead Swarita</td>
                <td style="text-align:center;" class="glyph-sample">&#xE00C;</td>
                <td><code>U+E00C / U+007C</code></td>
                <td><span class="badge-above">Above Consonant</span></td>
            </tr>
        </tbody>
    </table>

    <h2>4. The 3-Step Scholar Proofreading Workflow</h2>
    <div class="step-grid">
        <div class="step-card">
            <div class="step-num">1</div>
            <div class="step-title">Unicode Export</div>
            <div class="step-desc">Export pristine Unicode plaintext with Grantha swaras and English numerals.</div>
        </div>
        <div class="step-card">
            <div class="step-num">2</div>
            <div class="step-title">Hand Annotation</div>
            <div class="step-desc">Scholars enter intuitive modifier tags <code>(A)</code>–<code>(H)</code> in any text editor.</div>
        </div>
        <div class="step-card">
            <div class="step-num">3</div>
            <div class="step-title">Multi-Format Build</div>
            <div class="step-desc">One command compiles to responsive Web HTML and archival LuaLaTeX PDF.</div>
        </div>
    </div>

    <h2>5. Project Resources & Open Source</h2>
    <p>
        Explore the repository, test the tools, and contribute to the digitization of the sacred Jaimineeya heritage:
    </p>
    <ul>
        <li>💻 <strong>GitHub Repository:</strong> <a href="https://github.com/sekharnarayanaswamy-del/jaimineeyasamavedam" target="_blank">github.com/sekharnarayanaswamy-del/jaimineeyasamavedam</a></li>
        <li>🎨 <strong>Interactive Glyph Table:</strong> <a href="../../data/output/malayalam/glyph_table.html" target="_blank">glyph_table.html</a></li>
        <li>🔤 <strong>Custom Font:</strong> <code>fonts/JaimineeyaSwara.ttf</code></li>
        <li>📖 <strong>Specification & Developer Guide:</strong> <code>Malayalam_JSV/spec.md</code></li>
    </ul>

    <footer>
        Jaimineeya Samaveda Digitization Project &bull; Preserving Vedic Heritage Through Open Typographic Engineering
    </footer>

</article>

</body>
</html>
"""

# Write outputs
OUT_MD.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.write_text(md_content, encoding="utf-8")
print(f"Generated Markdown Blog: {OUT_MD}")

OUT_HTML.write_text(html_content, encoding="utf-8")
print(f"Generated HTML Blog: {OUT_HTML}")

# Copy to artifacts directory
art_md = ARTIFACT_DIR / "Malayalam_JSV_Publication_Blog.md"
art_html = ARTIFACT_DIR / "Malayalam_JSV_Publication_Blog.html"
shutil.copy(OUT_MD, art_md)
shutil.copy(OUT_HTML, art_html)
print(f"Copied to artifacts: {art_md}, {art_html}")
