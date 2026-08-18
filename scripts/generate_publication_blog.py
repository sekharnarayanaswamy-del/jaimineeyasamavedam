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

# 2. Read existing Markdown content or fallback
if OUT_MD.exists():
    md_content = OUT_MD.read_text(encoding="utf-8")
else:
    md_content = """# Revitalizing the Jaimineeya Samaveda in Malayalam Script: Typographic Innovation, Custom Font Engineering, and a Unified Multi-Format Publishing Pipeline

> **By the Jaimineeya Samaveda Digitization Project**  
> *Published: August 2026*  
> *Repository: [github.com/sekharnarayanaswamy-del/jaimineeyasamavedam](https://github.com/sekharnarayanaswamy-del/jaimineeyasamavedam)*

---

## 1. Executive Summary & The Sacred Heritage

The **Jaimineeya Shakha** of the *Samaveda* (*Jaiminīya Sāmavedam*) is one of the most ancient, musically intricate, and endangered oral traditions of Vedic chanting. While the Kauthuma and Ranayaniya traditions are more well known and established across India, the authentic musical recitation of the Jaimineeya tradition has been preserved almost exclusively through the guru-shishya lineages of **Tamil Nadu and by the Namboodiri tradition of Kerala**. This shakha was nearing extinction in Tamilnadu and was salvaged at the instance of Kanchi Mahaperiyava by Brahmasri Makarabhushanam Iyengar (Guruji) who set up the Thogur Jaimineeya Samaveda Patashala nearly fifty years ago. Through the efforts of Guruji, a set of his direct and indirect disciples went through formal, rigorous Vedic studies lasting twelve years which has helped to rescue this precious tradition from the brink. In addition to this, Guruji has published many works in Grantha and Devanagari drawing from manuscripts originally in Grantha.   

The Jaimineeya Samaveda employs a sophisticated system of Yugma and Ayugma swaras (Dharalakshanam of Sabhapati) for phonetic encoding of its Samagana. There was a migration of Jaimini Sama vedins from the Kaveri delta like Anbil, Tiruchi to Kerala around 250-300 years ago. These brahmins are today settled mainly in Kodunthirapully Agraharam in Palakkad. Brahmasri Sahasranama Iyer has very meticulously written by hand the Samhita and Aranyam portions using a special scheme : Malayalam mantrakshara, Grantha/mixed Grantha Malayalam swara markers and a set of swara modifier mnemonics to help easy recitation. The efficacy of his method is borne out by the passage of time that even today the young and old in the village use the paper copies of his manuscript to chant. 

As part of the overall digitalization efforts of Jaimineeya Samaveda, we have now taken an important step to digitize the "Kodunthirapully Padhati". There were some technical challenges caused by the swara notation with mixed Grantha/Malayalam and the mnemonics. To solve this, we have designed a new font, **JaimineeyaSwara** to depict the Grantha/Malayalam swara markers and the graphical swara modifier mnemonics. 

Here is a brief summary of the implementation of Jaimineeya Samaveda in Malayalam given below:
1. **Primary Svara Pitch Markers:** Subscript letters (traditionally Grantha or Malayalam characters) that specify the exact pitch movements (such as *Avaroham*, *Anvangulyam*, *Udgamam*, *Yanam*, and *Plutam*).
2. **Svara Modifiers:** Structural performance indicators that qualify the chant—including multi-syllable spanning melodic arches, peak carets, upper shoulder dots, descending tone slashes, and phrasing dandas.

With this, we are so happy to announce a **complete, end-to-end digital publishing ecosystem for the Jaimineeya Samaveda in Malayalam Script**, delivering high-fidelity outputs across:
- 🌐 **Interactive Web Edition (HTML5)** with responsive flexbox stacking and live word-bridging modifiers.
- 📄 **Archival Print Edition (LuaLaTeX / PDF)** with mathematical sub-point kerning and vector-perfect typography.
- 📝 **Universal Unicode Plaintext (.txt)** with standard Grantha codepoints and intuitive non-combining modifier symbols to aid in further refinement and curation of more Jaimineeya Samaveda content in Malayalam.

---

## 2. The Typographic & Technical Challenge

Transliterating Jaimineeya Samavedam from traditional palm-leaf manuscripts and Devanagari baselines into digital Malayalam presented three fundamental hurdles:

### Hurdle 1: The Grantha-Malayalam Hybrid Conundrum
Traditional Kerala Jaimineeya manuscripts write the base sacred text (*Mantrakshara*) in **Malayalam script**, while the overhead pitch markers (*Svaras*) are rendered in archaic **Grantha script** with specific regional overrides:
- **Vedic *Pla* (പ്ല):** A custom composite base glyph combining Grantha *Pa* with a Malayalam subscript *La*, distinct from standard classical Grantha.
- **Manuscript *Sha* (ശ):** The manuscript reference specifically employs the Malayalam base letter **ശ** (`U+0D36`) coupled with detached Grantha vowel arms (of *Shi* 𑌶𑌿, *Shii* 𑌶𑍀, and *Shaa* ശാ) rather than standard Grantha *Śa* (𑌶).

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
| **MOD-A** | `(A)` / `(⁀)` | **Syllable Spanning Arc (Tie)** | `\\uE004` / `U+2040` | Stacked Above (2 Syllables) | Overhead curved arch spanning across two words for connected tone transition. |
| **MOD-B** | `(B)` / `(∧)` | **Peak Elevation Caret** | `\\uE005` / `U+2227` | Stacked Above (2 Syllables) | Elevated melodic peak over syllable transition. |
| **MOD-C** | `(C)` / `(·)` | **Shoulder Pause Dot** | `\\uE001` / `U+00B7` | Upper-Right Shoulder | High pause dot attached to the upper shoulder of the preceding syllable. |
| **MOD-D** | `(D)` / `(Ʌ)` | **Chevron Roof** | `\\uE006` / `U+0245` | Stacked Above (2 Syllables) | Roof-tone modulation spanning across words. |
| **MOD-E** | `(E)` / `(┃)` | **Phrasing Heavy Danda** | `\\uE002` / `U+2503` | Inline | Structural major cadence division. |
| **MOD-F** | `(F)` / `(╷)` | **Light Vertical Line** | `\\uE002` / `U+2577` | Inline | Minor phrasing tone separator. |
| **MOD-G** | `(G)` / `(\\)` | **Descending Tone Slash** | `\\uE003` / `U+005C` | Stacked Below | Downward falling pitch attached to the bottom-center of the preceding consonant. |
| **MOD-H** | `(H)` / `(|)` | **Overhead Swarita** | `\\uE00C` / `U+007C` | Stacked Above | Vertical upper tone stroke situated directly on top of the base syllable. |

---

## 4. The 3-Step Scholar Proofreading Workflow

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

## 6. Open Source & Project Links

All font source files, templates, renderers, and transliteration scripts are open-source under permissive licenses:
- 💻 **GitHub Repository:** [https://github.com/sekharnarayanaswamy-del/jaimineeyasamavedam](https://github.com/sekharnarayanaswamy-del/jaimineeyasamavedam)
- 🔤 **Custom Font:** [`fonts/JaimineeyaSwara.ttf`](https://github.com/sekharnarayanaswamy-del/jaimineeyasamavedam/blob/format-mantras/fonts/JaimineeyaSwara.ttf)
- 📖 **Specification & Developer Guide:** [`Malayalam_JSV/spec.md`](https://github.com/sekharnarayanaswamy-del/jaimineeyasamavedam/blob/format-mantras/Malayalam_JSV/spec.md)
- 🎨 **Interactive Glyph Table:** [`data/output/malayalam/glyph_table.html`](https://github.com/sekharnarayanaswamy-del/jaimineeyasamavedam/blob/format-mantras/data/output/malayalam/glyph_table.html)
- 🌐 **Interactive Publication Blog:** [`docs/blog/Malayalam_JSV_Publication_Blog.html`](https://github.com/sekharnarayanaswamy-del/jaimineeyasamavedam/blob/format-mantras/docs/blog/Malayalam_JSV_Publication_Blog.html)
- ⚙️ **Rendering Engine:** [`src/render_pdf.py`](https://github.com/sekharnarayanaswamy-del/jaimineeyasamavedam/blob/format-mantras/src/render_pdf.py)
- 📑 **HTML Template:** [`templates/html/Malayalam_main_html.template`](https://github.com/sekharnarayanaswamy-del/jaimineeyasamavedam/blob/format-mantras/templates/html/Malayalam_main_html.template)
"""

# 3. HTML Template with Base64 font placeholder
html_template = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Revitalizing the Jaimineeya Samaveda in Malayalam Script | Publication Blog</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Serif+Malayalam:wght@400;500;600;700&family=Fira+Code:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    @font-face {
        font-family: 'JaimineeyaSwara';
        src: url('data:font/truetype;charset=utf-8;base64,__BASE64_FONT__') format('truetype');
    }

    :root {
        --bg-page: #f8fafc;
        --bg-card: #ffffff;
        --text-primary: #0f172a;
        --text-secondary: #475569;
        --text-muted: #64748b;
        --brand-blue: #1e3a8a;
        --brand-accent: #3b82f6;
        --swara-red: #c62828;
        --border-subtle: #e2e8f0;
        --shadow-elevation: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        background-color: var(--bg-page);
        color: var(--text-primary);
        line-height: 1.7;
        font-size: 17px;
        transition: background 0.3s ease, color 0.3s ease;
    }

    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #312e81 100%);
        color: white;
        padding: 70px 20px 80px;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .hero-banner::after {
        content: '';
        position: absolute;
        bottom: 0; left: 0; right: 0;
        height: 40px;
        background: var(--bg-page);
        clip-path: polygon(0 100%, 100% 100%, 100% 0, 0 100%);
        transition: background 0.3s ease;
    }
    .hero-content {
        max-width: 900px;
        margin: 0 auto;
    }
    .badge-pill {
        display: inline-block;
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.25);
        color: #93c5fd;
        font-weight: 700;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 6px 16px;
        border-radius: 20px;
        margin-bottom: 20px;
    }
    h1 {
        font-size: clamp(30px, 4.5vw, 44px);
        font-weight: 800;
        line-height: 1.25;
        letter-spacing: -0.02em;
        margin-bottom: 18px;
        text-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }
    .hero-subtitle {
        font-size: clamp(17px, 2vw, 20px);
        color: #cbd5e1;
        max-width: 760px;
        margin: 0 auto 25px;
        font-weight: 400;
        line-height: 1.5;
    }
    .meta-bar {
        display: flex;
        justify-content: center;
        gap: 20px;
        color: #94a3b8;
        font-size: 14px;
        font-weight: 500;
        flex-wrap: wrap;
    }

    /* Top Toolbar */
    .top-toolbar {
        max-width: 960px;
        margin: 0 auto 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .theme-pill-container {
        display: flex;
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(8px);
        border-radius: 24px;
        padding: 4px;
        gap: 4px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .theme-btn {
        background: transparent;
        border: none;
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .theme-btn.active {
        background: #ffffff;
        color: var(--brand-blue);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Main Container */
    .article-container {
        max-width: 960px;
        margin: -30px auto 0;
        background: var(--bg-card);
        border-radius: 16px;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.02);
        padding: 50px 60px;
        border: 1px solid var(--border-subtle);
    }

    h2 {
        font-size: 26px;
        font-weight: 800;
        color: var(--brand-blue);
        margin: 45px 0 18px;
        padding-bottom: 10px;
        border-bottom: 2px solid #e2e8f0;
    }
    h3 {
        font-size: 20px;
        font-weight: 700;
        color: var(--text-primary);
        margin: 28px 0 12px;
    }
    p {
        margin-bottom: 20px;
        color: var(--text-secondary);
    }

    .callout {
        background: #f0fdf4;
        border-left: 4px solid #16a34a;
        padding: 20px 24px;
        border-radius: 0 12px 12px 0;
        margin: 28px 0;
    }
    .callout-title {
        font-weight: 700;
        color: #166534;
        font-size: 17px;
        margin-bottom: 8px;
    }

    /* Live Interactive Sandbox Playground */
    .interactive-playground {
        background: #f1f5f9;
        border: 2px solid #cbd5e1;
        border-radius: 16px;
        padding: 30px;
        margin: 35px 0;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
    }
    .playground-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        flex-wrap: wrap;
        gap: 12px;
    }
    .playground-title {
        font-size: 18px;
        font-weight: 800;
        color: var(--brand-blue);
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .sample-buttons {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
    }
    .sample-chip {
        background: white;
        border: 1px solid #cbd5e1;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        color: #334155;
        cursor: pointer;
        transition: all 0.15s ease;
    }
    .sample-chip:hover {
        background: var(--brand-blue);
        color: white;
        border-color: var(--brand-blue);
    }
    .input-box-wrapper {
        margin-bottom: 20px;
    }
    .mantra-input {
        width: 100%;
        padding: 14px 18px;
        border-radius: 10px;
        border: 2px solid #94a3b8;
        font-family: 'Fira Code', 'Noto Serif Malayalam', monospace;
        font-size: 16px;
        color: #0f172a;
        background: white;
        transition: border-color 0.2s ease;
        outline: none;
    }
    .mantra-input:focus {
        border-color: #2563eb;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15);
    }
    .render-output-stage {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 30px 20px;
        min-height: 120px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03);
    }

    /* Live Mantra Flexbox Display */
    .mantra-display {
        display: inline-flex;
        align-items: flex-end;
        background: white;
        padding: 14px 24px;
        border-radius: 10px;
    }
    .mantra-word {
        display: inline-flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-end;
        vertical-align: bottom;
        position: relative;
        font-size: 1.75rem;
    }
    .swara-text {
        font-family: 'JaimineeyaSwara', serif;
        font-size: 1.10rem;
        color: var(--swara-red);
        line-height: 1;
        margin-bottom: 4px;
        font-weight: bold;
        min-height: 1.1em;
        user-select: none;
        text-align: center;
    }
    .mantra-text {
        font-family: 'Noto Serif Malayalam', serif;
        font-size: 1.75rem;
        font-weight: 500;
        line-height: 1.1;
        color: var(--text-primary);
        position: relative;
    }
    .word-space {
        width: 0.45em;
        display: inline-block;
    }
    .swara-mod {
        color: var(--brand-blue);
        font-family: 'JaimineeyaSwara', serif;
        font-weight: bold;
    }
    .swara-mod.mod-a {
        position: absolute;
        top: -0.28em;
        left: 100%;
        transform: translateX(-40%);
        font-size: 1.20rem;
        pointer-events: none;
    }
    .swara-mod.mod-b {
        position: absolute;
        top: -0.22em;
        left: 100%;
        transform: translateX(-50%);
        pointer-events: none;
        display: inline-flex;
        flex-direction: column;
        align-items: center;
    }
    .swara-mod.mod-b .caret-glyph {
        display: block;
        color: var(--brand-blue);
        font-size: 1.20rem;
        line-height: 1;
    }
    .swara-mod.mod-b .swara-on-caret {
        position: absolute;
        top: -1.15em;
        left: 50%;
        transform: translateX(-50%);
        color: var(--swara-red);
        font-size: 1.05rem;
        font-weight: bold;
        font-family: 'JaimineeyaSwara', serif;
        line-height: 1;
        white-space: nowrap;
    }
    .swara-mod.mod-c {
        position: absolute;
        top: -0.15em;
        right: -0.35em;
        font-size: 1.10rem;
    }
    .swara-mod.mod-d {
        position: absolute;
        top: -0.30em;
        left: 100%;
        transform: translateX(-40%);
        font-size: 1.20rem;
        pointer-events: none;
    }
    .swara-mod.mod-e {
        position: relative;
        margin-left: 0.15em;
        font-size: 1.35rem;
        vertical-align: -0.05em;
    }
    .swara-mod.mod-f {
        position: relative;
        margin-left: 0.15em;
        font-size: 1.35rem;
        vertical-align: -0.05em;
    }
    .swara-mod.mod-g {
        position: absolute;
        bottom: -0.38em;
        left: 28%;
        transform: translateX(-50%);
        font-size: 1.35rem;
    }
    .swara-mod.mod-h {
        position: absolute;
        top: -0.35em;
        left: 50%;
        transform: translateX(-50%);
        font-size: 1.20rem;
    }

    /* Tables */
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 25px 0;
        font-size: 15px;
    }
    th {
        background: #f1f5f9;
        color: #334155;
        font-weight: 700;
        text-align: left;
        padding: 12px 16px;
        border-bottom: 2px solid #cbd5e1;
    }
    td {
        padding: 12px 16px;
        border-bottom: 1px solid #e2e8f0;
        vertical-align: middle;
    }
    tr:hover td {
        background: #f8fafc;
    }
    .glyph-sample {
        font-family: 'JaimineeyaSwara', serif;
        font-size: 28px;
        color: var(--brand-blue);
        font-weight: bold;
    }
    .badge-above { background: #e0e7ff; color: #3730a3; padding: 4px 8px; border-radius: 4px; font-weight: 700; font-size: 11px; text-transform: uppercase; }
    .badge-below { background: #fef3c7; color: #92400e; padding: 4px 8px; border-radius: 4px; font-weight: 700; font-size: 11px; text-transform: uppercase; }
    .badge-shoulder { background: #f3e8ff; color: #6b21a8; padding: 4px 8px; border-radius: 4px; font-weight: 700; font-size: 11px; text-transform: uppercase; }
    .badge-inline { background: #f1f5f9; color: #334155; padding: 4px 8px; border-radius: 4px; font-weight: 700; font-size: 11px; text-transform: uppercase; }

    /* Workflow Stepper */
    .step-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 18px;
        margin: 28px 0;
    }
    .step-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 22px 18px;
        text-align: center;
    }
    .step-num {
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
    }
    .step-title {
        font-size: 16px;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 6px;
    }
    .step-desc {
        font-size: 13px;
        color: var(--text-muted);
        line-height: 1.4;
    }

    /* Dark Mode Themes Support */
    body.theme-dark {
        --bg-page: #0b0f19;
        --bg-card: #131b2e;
        --text-primary: #f1f5f9;
        --text-secondary: #cbd5e1;
        --text-muted: #94a3b8;
        --brand-blue: #60a5fa;
        --swara-red: #f87171;
        --border-subtle: #1e293b;
    }
    body.theme-dark .interactive-playground { background: #0d1527; border-color: #1e293b; }
    body.theme-dark .mantra-input { background: #1e293b; color: white; border-color: #334155; }
    body.theme-dark .render-output-stage { background: #0f172a; border-color: #1e293b; }
    body.theme-dark .mantra-display { background: #1e293b; }
    body.theme-dark th { background: #1e293b; color: #e2e8f0; border-color: #334155; }
    body.theme-dark td { border-color: #1e293b; }
    body.theme-dark tr:hover td { background: #1a233a; }
    body.theme-dark .step-card { background: #1e293b; border-color: #334155; }
    body.theme-dark .sample-chip { background: #1e293b; color: #e2e8f0; border-color: #334155; }
    body.theme-dark h2 { border-color: #1e293b; }

    /* Palm Leaf / Heritage Theme */
    body.theme-manuscript {
        --bg-page: #fbf7ee;
        --bg-card: #fffdf9;
        --text-primary: #2d2419;
        --text-secondary: #5c4b37;
        --brand-blue: #78350f;
        --border-subtle: #e7dfd0;
    }
    body.theme-manuscript .hero-banner {
        background: linear-gradient(135deg, #451a03 0%, #78350f 50%, #92400e 100%);
    }

    footer {
        margin-top: 50px;
        padding-top: 30px;
        border-top: 1px solid var(--border-subtle);
        text-align: center;
        font-size: 14px;
        color: var(--text-muted);
    }
    a { color: #2563eb; text-decoration: none; font-weight: 600; }
    a:hover { text-decoration: underline; }
</style>
</head>
<body>

<div class="hero-banner">
    <div class="top-toolbar">
        <div></div>
        <div class="theme-pill-container">
            <button class="theme-btn active" onclick="setTheme('light')">☀️ Modern Light</button>
            <button class="theme-btn" onclick="setTheme('dark')">🌙 Night Dark</button>
            <button class="theme-btn" onclick="setTheme('manuscript')">📜 Palm-Leaf</button>
        </div>
    </div>
    <div class="hero-content">
        <span class="badge-pill">Vedic Digital Humanities &bull; Open Source Typography</span>
        <h1>Revitalizing the Jaimineeya Samaveda in Malayalam Script</h1>
        <div class="hero-subtitle">
            Typographic Innovation, Custom Grantha Font Engineering, and a Unified Multi-Format Publishing Pipeline for Sacred Kerala & Tamil Nadu Vedic Chants.
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
        <div class="callout-title">The Sacred Jaimineeya Shakha Heritage & The Kodunthirapully Paddhati</div>
        The <em>Jaiminīya Sāmaveda</em> represents one of the oldest and most musically intricate traditions of Vedic chanting. Preserved by the lineages of <strong>Tamil Nadu and the Namboodiri tradition of Kerala</strong>, this shakha was saved from the brink of extinction through the divine vision of Kanchi Mahaperiyava and the lifelong dedication of <strong>Brahmasri Makarabhushanam Iyengar (Guruji)</strong>, who founded the Thogur Jaimineeya Samaveda Patashala nearly fifty years ago.
    </div>

    <h2>1. Executive Summary & The Sacred Heritage</h2>
    <p>
        The Jaimineeya Samaveda employs a sophisticated system of Yugma and Ayugma swaras (<em>Dharalakshanam of Sabhapati</em>) for phonetic encoding of its Samagana. 
    </p>
    <p>
        Following a migration of Jaimini Samavedins from the Kaveri delta (Anbil, Tiruchi) to Kerala around 250–300 years ago, a prominent community settled in <strong>Kodunthirapully Agraharam in Palakkad</strong>. In this tradition, <strong>Brahmasri Sahasranama Iyer</strong> meticulously hand-wrote the Samhita and Aranyam portions using a unique and effective scheme: Malayalam mantraksharas, Grantha and mixed Grantha-Malayalam swara markers, and a set of graphical swara modifier mnemonics to facilitate fluent recitation. Even today, young and old scholars in Kodunthirapully chant from paper copies of these revered manuscripts.
    </p>
    <p>
        As part of our overall digitization efforts, we have now implemented the digital <strong>"Kodunthirapully Paddhati"</strong>. To overcome the technical challenges of mixed Grantha/Malayalam typography and complex visual mnemonics, we engineered the <strong>JaimineeyaSwara</strong> font and built an automated multi-format publishing pipeline delivering:
    </p>
    <ul>
        <li>🌐 <strong>Interactive Web Edition (HTML5):</strong> With responsive flexbox stacking, live word-bridging modifiers, and searchable metadata.</li>
        <li>📄 <strong>Archival Print Edition (LuaLaTeX / PDF):</strong> With mathematical sub-point kerning, authentic manuscript ligatures, and vector-perfect layout.</li>
        <li>📝 <strong>Universal Unicode Plaintext (.txt):</strong> With standard Grantha codepoints and intuitive modifier mnemonics to enable ongoing curation and scholarship.</li>
    </ul>

    <h2>2. The Typographic Challenge</h2>
    <p>
        Rendering authentic Malayalam Jaimineeya Samaveda requires solving three distinct challenges:
    </p>
    <ul>
        <li><strong>Subscript Svara Markers:</strong> 19 distinct pitch markers written in archaic Grantha script layered directly over Malayalam syllables.</li>
        <li><strong>Manuscript Overrides:</strong> Kerala manuscripts use a unique hybrid <em>Pla</em> base (combining Grantha Pa with Malayalam subscript La) and a Malayalam <em>Sha</em> base with detached Grantha vowel arms.</li>
        <li><strong>Multi-Syllable Spanning Modifiers:</strong> Tonal arches and roof chevrons that visually span across the inter-word space between adjacent syllables.</li>
    </ul>

    <!-- INTERACTIVE MANTRA PLAYGROUND -->
    <h2>3. Live Interactive Mantra Sandbox</h2>
    <p>
        Test the live stacking engine in real-time. Type or click any sample below to see how our custom font and dynamic anchoring render your text:
    </p>

    <div class="interactive-playground">
        <div class="playground-header">
            <div class="playground-title">
                <span>⚡ Live Stacking & Modifier Engine</span>
            </div>
            <div class="sample-buttons">
                <button class="sample-chip" onclick="loadSample('ഹോ(𑌖)(A) ബാ(𑌪𑍍𑌲) മാ(𑌕)(B) യാ')">Sample 1: Arc + Caret</button>
                <button class="sample-chip" onclick="loadSample('ഓ(𑌤)(C) ഗ്നാ(𑌤) ബാ(𑌪𑍍𑌲)(G)')">Sample 2: Dot + Slash</button>
                <button class="sample-chip" onclick="loadSample('ഹോ(𑌪𑍍𑌲)(D) ഇഴാ(𑌶𑌾) ദാ(𑌚𑌿)(H)')">Sample 3: Chevron + Swarita</button>
                <button class="sample-chip" onclick="loadSample('വാ(𑌚)(E) ഇ(𑌚)(F)')">Sample 4: Phrasing Dandas</button>
            </div>
        </div>

        <div class="input-box-wrapper">
            <input type="text" id="mantraInput" class="mantra-input" value="ഹോ(𑌖)(A) ബാ(𑌪𑍍𑌲) മാ(𑌕)(B) യാ ഓ(𑌤)(C) ഗ്നാ(𑌤) ബാ(𑌪𑍍𑌲)(G) ദാ(𑌚𑌿)(H)" oninput="renderPlayground()" placeholder="Type mantra text with (Swara) and (A..H) modifiers..." />
        </div>

        <div class="render-output-stage" id="playgroundOutput">
            <!-- Dynamic Live Render Target -->
        </div>
    </div>

    <h2>4. The 8 Canonical Vedic Swara Modifiers</h2>
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

    <h2>5. The 3-Step Scholar Proofreading Workflow</h2>
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

    <h2>6. Project Resources & Open Source</h2>
    <p>
        Explore the repository, test the tools, and contribute to the digitization of the sacred Jaimineeya heritage:
    </p>
    <ul>
        <li>💻 <strong>GitHub Repository:</strong> <a href="https://github.com/sekharnarayanaswamy-del/jaimineeyasamavedam" target="_blank">github.com/sekharnarayanaswamy-del/jaimineeyasamavedam</a></li>
        <li>🔤 <strong>Custom Font:</strong> <a href="https://github.com/sekharnarayanaswamy-del/jaimineeyasamavedam/blob/format-mantras/fonts/JaimineeyaSwara.ttf" target="_blank"><code>fonts/JaimineeyaSwara.ttf</code></a></li>
        <li>📖 <strong>Specification & Developer Guide:</strong> <a href="https://github.com/sekharnarayanaswamy-del/jaimineeyasamavedam/blob/format-mantras/Malayalam_JSV/spec.md" target="_blank"><code>Malayalam_JSV/spec.md</code></a></li>
        <li>🎨 <strong>Interactive Glyph Table:</strong> <a href="../../data/output/malayalam/glyph_table.html" target="_blank"><code>data/output/malayalam/glyph_table.html</code></a></li>
        <li>🌐 <strong>Malayalam Digital Static Website:</strong> <a href="../malayalam/index.html" target="_blank"><code>docs/malayalam/index.html</code></a></li>
    </ul>

    <footer>
        Jaimineeya Samaveda Digitization Project &bull; Preserving Vedic Heritage Through Open Typographic Engineering
    </footer>

</article>

<script>
function setTheme(theme) {
    document.body.className = '';
    if (theme !== 'light') {
        document.body.classList.add('theme-' + theme);
    }
    document.querySelectorAll('.theme-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
}

function loadSample(text) {
    document.getElementById('mantraInput').value = text;
    renderPlayground();
}

function renderPlayground() {
    const raw = document.getElementById('mantraInput').value;
    const container = document.getElementById('playgroundOutput');
    
    // Parse words
    const tokens = raw.trim().split(/\\s+/);
    let html = '<div class="mantra-display">';

    const modMap = {
        'A': { cls: 'mod-a', glyph: '&#xE004;' },
        'a': { cls: 'mod-a', glyph: '&#xE004;' },
        '⁀': { cls: 'mod-a', glyph: '&#xE004;' },
        'B': { cls: 'mod-b', glyph: '&#xE005;' },
        'b': { cls: 'mod-b', glyph: '&#xE005;' },
        '∧': { cls: 'mod-b', glyph: '&#xE005;' },
        '^': { cls: 'mod-b', glyph: '&#xE005;' },
        'C': { cls: 'mod-c', glyph: '&#xE001;' },
        'c': { cls: 'mod-c', glyph: '&#xE001;' },
        '·': { cls: 'mod-c', glyph: '&#xE001;' },
        'D': { cls: 'mod-d', glyph: '&#xE006;' },
        'd': { cls: 'mod-d', glyph: '&#xE006;' },
        'Ʌ': { cls: 'mod-d', glyph: '&#xE006;' },
        'E': { cls: 'mod-e', glyph: '&#xE002;' },
        'e': { cls: 'mod-e', glyph: '&#xE002;' },
        '┃': { cls: 'mod-e', glyph: '&#xE002;' },
        'F': { cls: 'mod-f', glyph: '&#x2577;' },
        'f': { cls: 'mod-f', glyph: '&#x2577;' },
        '╷': { cls: 'mod-f', glyph: '&#x2577;' },
        'G': { cls: 'mod-g', glyph: '&#xE003;' },
        'g': { cls: 'mod-g', glyph: '&#xE003;' },
        '\\\\': { cls: 'mod-g', glyph: '&#xE003;' },
        'H': { cls: 'mod-h', glyph: '&#xE00C;' },
        'h': { cls: 'mod-h', glyph: '&#xE00C;' },
        '|': { cls: 'mod-h', glyph: '&#xE00C;' },
    };

    const swaraSubs = {
        '𑌪𑍍𑌲': '&#xE020;',
        'Pla': '&#xE020;',
        'പ്ല': '&#xE020;',
        '𑌪𑍍𑌲𑌾': '&#xE021;',
        'Plaa': '&#xE021;',
        'പ്ലാ': '&#xE021;',
        '𑌪𑍍𑌲𑌿': '&#xE022;',
        'Pli': '&#xE022;',
        'പ്ലി': '&#xE022;',
        '𑌪𑍍𑌲𑍀': '&#xE023;',
        'Plii': '&#xE023;',
        'പ്ലീ': '&#xE023;',
        'ശ𑌾': '&#xE010;',
        'ശാ': '&#xE010;',
        'Shaa': '&#xE010;',
        'ശ𑌿': '&#xE011;',
        'ശി': '&#xE011;',
        'Shi': '&#xE011;',
        'ശ𑍀': '&#xE012;',
        'ശീ': '&#xE012;',
        'Shii': '&#xE012;',
        'ശ്': '&#xE013;',
        'ത്ര': '&#xE01D;',
        'Tra': '&#xE01D;',
        'ക്ര': '&#xE01E;',
        'Kra': '&#xE01E;',
    };

    for (let i = 0; i < tokens.length; i++) {
        let t = tokens[i];
        if (i > 0) html += '<span class="word-space">&nbsp;</span>';

        // Extract swara (xxx) and modifier (y)
        let swara = '';
        let mod = '';
        let base = t;

        // Check for swara (𑌖)
        const swMatch = base.match(/\\(([^)]+)\\)/g);
        if (swMatch) {
            for (let m of swMatch) {
                const inner = m.replace(/[()]/g, '');
                if (modMap[inner]) {
                    mod = modMap[inner];
                } else {
                    swara = swaraSubs[inner] || inner;
                }
                base = base.replace(m, '');
            }
        }

        let modHtml = '';
        if (mod) {
            if (mod.cls === 'mod-b') {
                modHtml = `<span class="swara-mod mod-b"><span class="caret-glyph">&#xE005;</span><span class="swara-on-caret">${swara || '&nbsp;'}</span></span>`;
                swara = '';
            } else {
                modHtml = `<span class="swara-mod ${mod.cls}">${mod.glyph}</span>`;
            }
        }

        html += `
        <span class="mantra-word">
            <span class="swara-text">${swara || '&nbsp;'}</span>
            <span class="mantra-text">${base}${modHtml}</span>
        </span>
        `;
    }

    html += '</div>';
    container.innerHTML = html;
}

// Initial render
window.onload = renderPlayground;
</script>
</body>
</html>
"""

html_content = html_template.replace("__BASE64_FONT__", b64_font)

# Write outputs
OUT_MD.parent.mkdir(parents=True, exist_ok=True)
OUT_MD.write_text(md_content, encoding="utf-8")
print(f"Preserved Markdown Blog: {OUT_MD}")

OUT_HTML.write_text(html_content, encoding="utf-8")
print(f"Generated HTML Blog: {OUT_HTML}")

# Copy to artifacts directory
try:
    if ARTIFACT_DIR.exists():
        art_md = ARTIFACT_DIR / "Malayalam_JSV_Publication_Blog.md"
        art_html = ARTIFACT_DIR / "Malayalam_JSV_Publication_Blog.html"
        shutil.copy(OUT_MD, art_md)
        shutil.copy(OUT_HTML, art_html)
        print(f"Copied to artifacts: {art_md}, {art_html}")
except Exception as e:
    print(f"Artifact copy notice: {e}")
