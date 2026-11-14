# Jaimineeya Samavedam Typography Guide

This document outlines the font mapping and typography rules applied across the website. Use this as a reference for fine-tuning the visual appearance.

## 🏛️ Core Fonts

| Font Family | Visual Style | Usage |
| :--- | :--- | :--- |
| **Adishila Vedic** | Traditional Serif | Sanskrit text, Mantra metadata, Traditional labels |
| **Adishila San Vedic** | Modern Sans-serif | Numerals, Counts, Navigation links, Table data |

---

## 📊 Master Typography Table

This table provides a comprehensive summary of UI elements, their fonts, and current sizes.

| Page Type | UI Element | Font Family | Size | Color | Example String | CSS Selector |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **🌍 Global** | Sidebar Logo Title | Adishila Vedic (Serif) | 1.8rem | Saffron (#FF6B35) | **जैमिनीय साम संहिता** | `.logo-text` |
| | Sidebar Logo Subtitle| Adishila Vedic (Serif) | 1rem | Muted Gray (#6B6B6B) | **Jaimineeya Sama...** | `.logo-subtitle` |
| | Sidebar Labels | Adishila Vedic (Serif) | 1.15rem | Charcoal (#2C2C2C) | **पर्व:, खण्ड:, साम:** | `.nav-section h3` |
| | Sidebar Pills | Adishila San (Sans) | 0.7rem | Dark Gray (#4A4A4A) | **1, 10, 20** | `.nav-links a` |
| | Jump to Input | Adishila San (Sans) | 0.9rem | Charcoal (#2C2C2C) | **e.g. 1.1.1** | `.jump-input` |
| | Search Button | Adishila Vedic (Serif) | 1.0rem | Brown (#8B4513) | **अन्वेषणम् (Search)** | `.search-btn` |
| | Footer Nav Buttons| Adishila Vedic (Serif) | 1.0rem | Saffron (#FF6B35) | **ऋषयः, देवताः** | `.footer-btn` |
| | Jump Nav Labels | Adishila Vedic (Serif) | 0.85rem | Muted Gray (#6B6B6B) | **साम: (19)** | `.sidebar-right h3` |
| | Jump Nav Icons | Adishila San (Sans) | 0.7rem | Dark Gray (#4A4A4A) | **1, 10, 20** | `.jump-links a` |
| **🏠 Home** | Hero Page Title | Adishila Vedic (Serif) | 3.0rem | Charcoal (#2C2C2C) | **जैमिनीयसामवेद: (Jaimineeya Samavedam)** | `.home-hero h1` |
| | Stats Values | Adishila San (Sans) | 2.2rem | Saffron (#FF6B35) | **6, 125, 1222** | `.stat-value` |
| | Stats Labels | Adishila Vedic (Serif) | 1.3rem | Muted Gray (#6B6B6B) | **पर्व: (Parva)** | `.stat-label` |
| | Indices Section Title| Adishila Vedic (Serif) | 2.2rem | Charcoal (#2C2C2C) | **अन्य वर्गीकरणम् (Indices)** | `.anya-vargeekaran-card h2` |
| | Index Pill Title | Adishila Vedic (Serif) | 1.5rem | Saffron (#FF6B35) | **ऋषयः (Rishi)** | `.index-link-item .title` |
| | Index Pill Count| Adishila San (Sans) | 0.8rem | Gray (#888) | **(172)** | `.index-link-item .stats` |
| **📖 Kandah** | Page Title | Adishila Vedic (Serif) | 1.8rem | Charcoal (#2C2C2C) | **अर्चिकपर्व - प्रथमः खण्डः** | `h1` |
| | Header Metadata | Adishila Vedic (Serif) | 1.1rem | Dark Gray (#4A4A4A) | **पर्व: १, खण्ड: १ | साम: १९** | `.page-subtitle` |
| | Metadata Numerals | Adishila San (Sans) | 0.8rem | Dark Gray (#4A4A4A) | **1, 12, 19** | `.page-meta .number` |
| | TOC Header | Adishila Vedic (Serif) | 1.2rem | Charcoal (#2C2C2C) | **खण्ड: 1 - सम्पूर्णम्** | `.toc h4` |
| | TOC Pills | Adishila San (Sans) | 0.9rem | Dark Gray (#4A4A4A) | **१.१.१, १.१.२** | `.toc-list li a` |
| **🕉️ Mantra** | Sama ID Badge | Adishila San (Sans) | 0.9rem | Saffron (#FF6B35) | **1.1.1** | `.sama-id` |
| | Metadata Line | Adishila Vedic (Serif) | 1.6rem | Purple (#7B1FA2) | **॥ भरद्वाजो बार्हस्पत्यः ... ॥** | `.rik-metadata` |
| | Class. Table Head | Adishila Vedic (Serif) | 1.1rem | White (#FFFFFF) | **Global #, ऋषिः, देवता** | `.classification-table th` |
| | Class. Table Values| Adishila Vedic (Serif) | 1.3rem | Charcoal (#2C2C2C) | **अग्निः, त्रिष्टुप्** | `.class-value` |
| | Table Numerals | Adishila San (Sans) | 0.9rem | Dark Gray (#4A4A4A) | **1, 10, 20** | `.sama-entry .number` |
| | Rik Text (Blue) | Adishila Vedic (Serif) | 1.6rem | Blue (#1565C0) | **इ॒षे त्वो॒र्जे त्वा॑...** | `.rik-text` |
| | Mantra Text | Adishila Vedic (Serif) | 1.6rem | Charcoal (#2C2C2C) | **इ॒षे त्वो॒र्जे त्वा॑...** | `.mantra-container` |
| | Mantra Numbering | Adishila Vedic (Serif) | 1.1rem | Charcoal (#2C2C2C) | **॥ १ ॥** | `.mantra-number` |
| **🗂️ Index** | Letter Heading | Adishila Vedic (Serif) | 1.2rem | Red (#B03A2E) | **अ, आ, इ** | `.alpha-char` |
| | Item Name | Adishila Vedic (Serif) | 1.3rem | Charcoal (#2C2C2C) | **वसिष्ठः, अग्निः** | `.item-name` |
| | Item Count Badge | Adishila San (Sans) | 0.75rem | Dark Gray (#777) | **(172), (5)** | `.item-count-badge` |
| | Location Refs | Adishila San (Sans) | 0.8rem | Saffron (#FF6B35) | **1.1.1, 1.1.2** | `.item-refs a` |
| | Top 20 Ranking | Adishila San (Sans) | 0.85rem | White (#FFFFFF) | **1, 2, 3** | `.rishi-rank` |

---

## 🎨 Element Specific Mappings

### 1. Traditional Elements (Serif Look)
These elements use the traditional **Adishila Vedic** font for a classical appearance.

| Element | CSS Selector | Description |
| :--- | :--- | :--- |
| **Homepage Stats Labels** | `.stat-label` | "पर्व: (Parva)", "खण्ड: (Kandah)", etc. |
| **Mantra Metadata** | `.rik-metadata` | Purple line: "॥ वसिष्ठो मैत्रावरुणिः ... ॥" |
| **Sama Headers** | `.sama-header-text` | Green line above mantra text |
| **Mantra Numbering** | `.mantra-number` | The "॥ १ ॥" marker inside/below mantra boxes |
| **Navigation Headers** | `.classification-table th` | Headers in the Mantra classification table |
| **Traditional Values** | `.class-value` | Values inside classification tables |
| **Kandah Metadata** | `.page-subtitle`, `.sama-count` | Labels on the Kandah page: "पर्व: ... खण्ड: ...", "साम: ..." |
| **Sidebar Headers** | `.nav-section h3`, `.sidebar-right h3` | Labels in the navigation: "पर्व:", "खण्ड:", "साम:" |

**Code Location:** `src/generate_website.py` around lines 921-923.
```css
.nav-section h3, .sidebar-right h3 {
    font-size: 1.15rem;
    text-transform: none; /* Allows "Jump to" instead of forced caps */
    letter-spacing: normal; /* Important: keeps Devanagari characters connected */
    font-family: 'AdishilaVedic', 'Noto Serif Devanagari', serif !important;
}

.nav-section h3 .number, .sidebar-right h3 .number {
    font-size: 0.85rem; /* Smaller size for bracketed counts */
}
```

---

### 2. Numerical & Dynamic Data (Sans Look)
These elements use the modern **Adishila San Vedic** font for maximum clarity and a scholarly index feel.

| Element | CSS Selector | Description |
| :--- | :--- | :--- |
| **Large Stats Values** | `.stat-value` | Large numbers on the homepage (e.g., "6", "125") |
| **Rank Indices** | `.rishi-rank` | The orange circles with numbers in Top 20 lists |
| **ToC / Nav Links** | `.toc-list li a`, `.nav-links a` | All numeric references in menus |
| **Summary Counts** | `.stats-summary` | Page header stats: "23 देवताः • 719 आर्षेयम्" (AdishilaVedic + English Numerals) |
| **Alphabetical Counts** | `.alpha-count` | Small numbers in alphabet navigation buttons |
| **Pill Counts** | `.index-link-item .stats` | Numbers in indices pills: "(172)", "(23)" |
| **Sama ID (Badge)** | `.sama-id` | Top-left badge on mantra entries: "1.1.1" |
| **Table Numerals** | `.number` (inside tables) | The "Global #" column values in classification tables |

**Code Location:** `src/generate_website.py` around lines 917-919.
```css
.stat-value, .rishi-rank, .number, .nav-links a, .toc-list li a, .jump-links a, 
.footnote-ref, .stats-summary, .stats-summary strong, .count, 
.rishi-count, .stats, .alpha-count, .item-count, .item-refs a, .item-count-badge, .sama-id, .sama-id a {
    font-family: 'AdishilaSanVedic', 'Noto Sans Devanagari', 'Inter', sans-serif !important;
}
```

---

### Sidebar Logo & Title
To adjust the size of the branding section in the sidebar:
**Location:** `src/generate_website.py` around lines 983-996.

```css
.logo-text {
    font-size: 1.8rem; /* Increased from 1.5rem */
}

.logo-subtitle {
    font-size: 1rem; /* Increased from 0.85rem */
}
```

```css
.index-link-item .title {
    font-size: 1.5rem; /* Change the Devanagari label size */
}

.index-link-item .stats {
    font-size: 0.8rem; /* Change the count (numeral) size */
    color: #888;
}
```

### Top 20 Classification Cards
To adjust the font weight or size of the names in the Top 20 lists (e.g., Rishi page):
**Location:** `src/generate_website.py` around lines 2397-2415.

```css
.rishi-name {
    font-weight: 400; /* Regular (400) or Bold (600) */
    font-size: 1.15rem;
}

.rishi-count {
    font-size: 0.8rem;
    font-weight: 400;
}
```

### Mantra Numbering (॥ १ ॥)
To adjust the size of the mantra index:
**Location:** `src/generate_website.py` around lines 1745-1750.

```css
.mantra-number {
    font-size: 1.6rem; /* Adjust this value */
    font-weight: 500;
}
```

### Kandah Page Sub-header (Metadata)
To adjust the second line of text on Kandah pages (labels and numbers):
**Location:** `src/generate_website.py` around lines 1133-1158.

```css
.page-subtitle, .sama-count {
    font-size: 1.1rem; /* Adjust labels and numbers together */
}

.page-meta .number {
    font-size: 0.8rem; /* Fine-tune only the numerals here */
    font-weight: 400;
}
```

### Mantra Classification & ID
To unify sizes for the Sama ID badge and the classification table:
**Location:** `src/generate_website.py` around lines 1261-1270 and 1977-1986.

```css
.sama-id, .sama-entry .number {
    font-size: 0.9rem; /* Compact metadata badges */
}

.classification-table {
    font-size: 1.1rem; /* Clearer table structure */
}
```

### Alphabetical Index (Anukramanika) References
To adjust the density of the location numerals in the index:
**Location:** `src/generate_website.py` around line 2286.

```css
.item-refs a {
    font-size: 0.8rem; /* Smaller size for dense linking */
}
```

---

> [!TIP]
> **Important**: All these styles are injected into the HTML during generation. After editing the fragments in `src/generate_website.py`, you **must** run the generator script to see the changes:
> `python src/generate_website.py --source-file data/output/Vargeekaran.json -o docs`

---

## 🌴 Malayalam & Grantha Swara Typography System

### Font Hierarchy

| Role | Font File | Visual Description | Usage |
| :--- | :--- | :--- | :--- |
| **Base Text** | `NotoSerifMalayalam-Regular.ttf` | Traditional Malayalam Serif | Mantra words, Titles, Headings, Footnote body |
| **Swara Notations** | `JaimineeyaSwara.ttf` | Red bold superscript (`#c62828`) | Stacks directly **above** Malayalam aksharas |
| **Vedic Accents** | `NotoSerifDevanagari-Regular.ttf` | Vedic Unicode Extensions | Swarita (`U+0951`), Anudatta (`U+1CD2`), Kampa |
| **Numerals & Latin** | `Nimbus Roman.ttf` | Classic Latin Serif | English numerals, page numbers, title metadata |

### Stacking Geometry
*   **Swara Elevation**: `\setstackgap{L}{0.7\baselineskip}` elevates swaras cleanly above Malayalam ascenders.
*   **Auto-Kerning**: `\swarastack` automatically computes the width of base syllables vs multi-glyph swaras (`\stackleft` / `\stackcenter`) to eliminate visual collisions.

### 11 Vedic Swara Modifiers Layout

| Modifier | Symbol | Stacking Position | Hex / PUA |
| :--- | :---: | :---: | :--- |
| **Syllable Arc (Tie)** | `⁀` / `͡` | **Stacked Above** | `U+E004` / `U+2040` |
| **Caret** | `^` / `˄` | **Stacked Above** | `U+E005` / `U+005E` |
| **Roof** | `/\` / `Ʌ` | **Stacked Above** | `U+E006` / `U+0245` |
| **Ring Above** | `˚` / `ͦ` | **Stacked Above** | `U+E009` / `U+0366` |
| **High/Mid-Dot** | `ॱ` / `·` | **Stacked Above** | `U+E001` / `U+0971` |
| **Underbar** | `_` | **Stacked Below** | `U+E007` / `U+005F` |
| **Phrasing Danda** | `╷` / `L` | **Stacked Below** | `U+E002` / `U+2577` |
| **Descending Tone** | `\` / `╲` | **Stacked Below** | `U+E003` / `U+005C` |
| **Ascending Tone** | `/` | **Stacked Below** | `U+E008` / `U+002F` |
| **Low Comma** | `,` / `ˏ` | **Stacked Below** | `U+E00A` / `U+002C` |
| **Double Danda** | `\|\|` / `॥` | **Inline** | `U+E00B` / `U+0965` |

---

## 📄 PDF Print Typography (A4 vs. Book Editions)

This section documents the exact font sizing, scaling rules, and page geometry applied during LaTeX document rendering (`templates/pdf/Devanagari_main.template` and `templates/pdf/Devanagari_book.template`).

### 1. Document Class & Font Scaling (AdishilaVedic)
Both PDF templates compile with `\documentclass[12pt, ...]{book}` (LaTeX base size = **12pt**). Fonts are scaled via `fontspec`:

| Font Family | Font Variable | Scale | Effective Base Size (12pt × Scale) | Usage |
| :--- | :--- | :--- | :--- | :--- |
| **AdishilaVedic** | `\devafont`, `\setmainfont` | `Scale=1.35` | **16.2 pt** | Main Devanagari text, Samam chant lines, Rik mula |
| **AdishilaVedicBold** | `\headerfont` | `Scale=1.45` | **17.4 pt** | Chapter and Section structural headers |
| **AdishilaVedic** | `\smallredfont` | `Scale=0.95` | **11.4 pt** | Swara number markings in SwaraRed (`#C62828`) |
| **JaimineeyaSwara** | `\swarafont` | `Scale=0.88` | **10.56 pt** | Vedic swara notations and modifiers |
| **JaimineeyaSwara** | `\arcfontDeva` | `Scale=1.25` | **15.0 pt** | Overhead connecting arcs |

*(Alternative Noto fonts, if selected: `Scale=1.05` for body [12.6 pt], `Scale=1.15` for headers [13.8 pt], `Scale=0.76` for swaras [9.12 pt]).*

### 2. Title & Cover Page Typography (A4 vs. Book)
Cover page sizing is tailored to physical dimensions:

| Element | A4 Edition (`Devanagari_main`) | Book Edition (`Devanagari_book`) | Style |
| :--- | :--- | :--- | :--- |
| **Mangalam & Guruvandana** | `\fontsize{11pt}{15pt}` | `\fontsize{9.5pt}{13pt}` | Upright |
| **Main Book Title** | `\fontsize{34pt}{42pt}` | `\fontsize{28pt}{34pt}` | Bold |
| **Subtitle** | `\fontsize{20pt}{26pt}` | `\fontsize{17pt}{22pt}` | Bold |
| **Publisher Header** (`प्रकाशकः`) | `\fontsize{15pt}{20pt}` | `\fontsize{13pt}{17pt}` | Bold |
| **Publisher Details & Year** | `\fontsize{14pt}{19pt}` | `\fontsize{12pt}{16pt}` | Upright |

### 3. Document Content Elements
Body font sizes remain identical across A4 and Book to maintain chanting legibility:

| Document Element | LaTeX Macro | Standard LaTeX Size | Rendered Effective Size (with 1.35x Scale) | Color |
| :--- | :--- | :--- | :--- | :--- |
| **Chapter Header** | `\chapter*` (`\huge\headerfont`) | 20.7 pt | **~30.0 pt** | Charcoal / Maroon |
| **Section Header** | `\section*` (`\Large\headerfont`) | 14.4 pt | **~20.9 pt** | Charcoal / Maroon |
| **Rik Mula Verse** | `\normalsize` | 12.0 pt | **16.2 pt** | AccentBlue (`#1565C0`, Bold) |
| **Samam Chant Line** | `\normalsize\bfseries` | 12.0 pt | **16.2 pt** | Charcoal (`#000000`, Bold) |
| **Samam Header** | `\normalsize` | 12.0 pt | **16.2 pt** | AccentGreen (`#2E7D32`, Bold) |
| **Rik Metadata** | `\footnotesize` | 10.0 pt | **13.5 pt** | AccentPurple (`#7B1FA2`) |
| **Samam Metadata** | `\footnotesize` | 10.0 pt | **13.5 pt** | AccentBrown (`#8B4513`) |
| **Footnotes** | `\footnotesize` | 10.0 pt | **13.5 pt** | Charcoal |
| **Summary Table** | `\small` | 11.0 pt | **14.85 pt** | AccentBlue & Charcoal |
| **Prayoga Appendix Header** | `\large\bfseries` | 14.4 pt | **19.44 pt** | AccentGreen |
| **Prayoga Appendix Body** | `\normalsize` | 12.0 pt | **16.2 pt** | Charcoal |
| **Closing Mantras** | `\normalsize\bfseries` | 12.0 pt | **16.2 pt** | Charcoal |
| **Index (वर्णानुक्रमणिका)** | `\footnotesize` | 10.0 pt | **13.5 pt** | Charcoal |
| **Page Header / Footer** | `\footnotesize` | 10.0 pt | **10.0 pt** | Muted Gray (Latin font) |

### 4. Page Geometry Differences
*   **A4 Edition**:
    *   Sheet: Standard A4 (`210mm × 297mm`), portrait, single-sided (`oneside`).
    *   Margins: Left = 18mm, Right = 18mm, Top = 20mm, Bottom = 20mm.
    *   Index columns: **3 columns**.
*   **Book Edition**:
    *   Sheet: Crown Quarto format (`180mm × 228mm`), double-sided (`twoside`).
    *   Margins: Inner (binding spine) = 18mm, Outer = 15mm, Top = 19mm, Bottom = 19mm.
    *   Index columns: **2 columns**.

### 5. Swara & Swara Modifier Typography Specifications

#### A. Swara Numbers (Chant Notations)
*   **Font Family**: `AdishilaVedic.ttf` / `AdishilaVedicBold.ttf` via `\smallredfont`
*   **Scale**: `Scale=0.95` (Effective size: **11.4 pt** at 12pt document base)
*   **Color**: `SwaraRed` (`HTML #C62828` in color mode; `RGB 0,0,0` in B&W mode)
*   **Stacking Mechanism**:
    *   **Standard Paddhati** (swaras below base syllable):
        `\swarastack{#1}{#2}` where `#2` is raised with `\raisebox{-1.05ex}[0pt][0pt]{#2}`.
    *   **Kodunthirapully Paddhati (`-kpully`)** (swaras above base syllable):
        `\swarastack{#1}{#2}` where `#2` is raised with `\raisebox{1.55ex}[1.75ex][0pt]{#2}`.
    *   **Width Awareness**: Automatically checks `\ifdim\swarasw>\swarabasew` and centers the stack to eliminate overlapping glyphs.

#### B. Swara Modifiers & Diacritics
*   **Primary Modifier Font**: `JaimineeyaSwara.ttf` via `\swarafont`
    *   **Scale**: `Scale=0.88` (Effective size: **10.56 pt**)
    *   **Font Features**: `Script=Grantha, Ligatures=TeX, AutoFakeBold=3.5, AutoFakeSlant`
    *   **Color**: `ModifierSkyBlue` (`HTML #0284C7` in color mode; `RGB 0,0,0` in B&W mode)
*   **Overhead Arc Font**: `JaimineeyaSwara.ttf` via `\arcfontDeva`
    *   **Scale**: `Scale=1.25` (Effective size: **15.0 pt**)
    *   **Font Features**: `AutoFakeBold=3.5`
    *   **Color**: `ModifierSkyBlue`

#### C. Comprehensive Swara Modifier Layout & LaTeX Macros

| Modifier Code | Name / Visual | Unicode / PUA | LaTeX Macro & Formatting | Placement / Offset |
| :--- | :--- | :--- | :--- | :--- |
| **MOD-A / MOD-A2** | Overhead Conjunct Arc | `U+E004` / `U+E02E` (`⁀` / `͡`) | `\arcOverSyllable{#2}` via `\Large\swarafont\textbf{...}` | Centered over base syllable (`\raisebox{1.18ex}`) |
| **MOD-A1** | Danda with Arc | `U+E00D` | `\dandaWithArc[#1]{#2}` via `\arcfontDeva` | Centered over danda stem (`0.802*dimen0` offset, `\raisebox{0.92ex}`) |
| **MOD-B** | Peak Elevation Caret | `U+E005` (`^` / `˄`) | `\caretWithSwara{#1}` via `\swarafont` | Bridges two syllables with swara atop apex (`\raisebox{2.35ex}`) |
| **MOD-D** | Roof / Angle Above | `U+E006` (`/\` / `Ʌ`) | `\rlap{\Large\swarafont\textbf{\char"E006}}` | Above syllable (`\raisebox{1.18ex}`) |
| **MOD-G** | Lower Under-Slash | `U+E003` (`\` / `╲`) | `\modGUnder{#1}` via `\swarafont\char"E003` | Below-right of syllable (`\raisebox{-0.30ex}`) |
| **MOD-UNDERBAR**| Underbar Dash | `U+E007` (`_`) | `\underbarMark{}` via `\rule{0.35em}{0.28ex}` | In-line right under-dash (`\raisebox{-0.22ex}`) |
| **Period / Dot**| Mid-High Tone Dot | `.` / `U+E001` (`·`) | `{\Large\textcolor{ModifierSkyBlue}{\textbf{.}}}` | In-line followed by `\hspace{0.08em}` |
| **Comma** | Low Tone Comma | `,` / `U+E00A` | `{\Large\textcolor{ModifierSkyBlue}{\textbf{,}}}` | In-line followed by `\hspace{0.08em}` |
| **MOD-RING** | Ring Above | `U+E009` (`˚` / `ͦ`) | `\swarafont\char"E009` | Above syllable |
| **MOD-PHRASING**| Vertical Phrasing Danda| `U+E002` (`╷`) | `\swarafont\char"E002` | Stacked below syllable |
| **MOD-SLASH** | Ascending Tone Slash | `U+E008` (`/`) | `\swarafont\char"E008` | Stacked below syllable |



