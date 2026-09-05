# Jaimineeya Samavedam: Formatting & Tuning Guide

This document is the definitive operational guide for typography, sizing, spacing, and visual geometry across both **PDF (LaTeX)** and **HTML (Web)** generation pipelines for Devanagari, Malayalam, and Grantha.

---

## 1. Devanagari PDF (LaTeX)

### A. Font Families & Sizing
Defined in [`templates/pdf/Devanagari_main.template`](file:///c:/Users/sekha/OneDrive/Documents/GitHub/jaimineeyasamavedam/templates/pdf/Devanagari_main.template):

| Target | Parameter / Macro | Location | Current Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Document Base** | `\documentclass[12pt, a4paper, openany]{book}` | Line 1 | `12pt` | Base size for all LaTeX calculations. |
| **Main & Mantra Font** | `\setmainfont[Scale=1.35...]` / `\devafont` | Lines 64–75 | `Scale=1.35` (~`16.2pt`) | Primary Sanskrit / Devanagari chant text (`AdishilaVedic.ttf`). |
| **Section Headers** | `\newfontfamily\headerfont[Scale=1.45...]` | Lines 66, 73 | `Scale=1.45` (~`17.4pt`) | Bold titles for Parva, Kanda, and Samam headings. |
| **Red Swara Font** | `\newfontfamily\smallredfont[Scale=0.95...]` | Lines 67, 74 | `Scale=0.95` (~`11.4pt`) | Red pitch indicators above/below syllables. |
| **Vedic PUA Glyph Font** | `\newfontfamily\swarafont[Scale=0.88...]` | Lines 68, 75 | `Scale=0.88` (~`10.5pt`) | Specialized chant glyphs (`JaimineeyaSwara.ttf`). |

### B. Vertical Line & Paragraph Rhythm
Defined in [`templates/pdf/Devanagari_main.template`](file:///c:/Users/sekha/OneDrive/Documents/GitHub/jaimineeyasamavedam/templates/pdf/Devanagari_main.template) and [`src/render_pdf.py`](file:///c:/Users/sekha/OneDrive/Documents/GitHub/jaimineeyasamavedam/src/render_pdf.py):

| Target | Parameter / Macro | Location | Current Value | Tuning Effect |
| :--- | :--- | :--- | :--- | :--- |
| **Inter-line Baseline Stretch** | `\setstretch{2.50}` | `Devanagari_main.template:L95` | `2.50` | Controls distance between lines in a verse. In KPully, swaras are raised above the text; `2.50` ensures that the red swaras of line $N+1$ have clear clearance below line $N$. |
| **Inter-verse Spacing** | `\par\vspace{0.35em}` | `src/render_pdf.py:L901` | `0.35em` | Vertical blank space between two verses. |
| **Header-to-Mantra Gap** | `\vspace{0.15em}` | `src/render_pdf.py:L1261` | `0.15em` | Keeps the Samam header closely tied to its chant text. |
| **Rik-to-Samam Gap** | `\vspace{0.3em}` | `src/render_pdf.py:L1229` | `0.3em` | Separation between Rik verse and following Samam set. |
| **Page Margins** | `\usepackage[margin=2.0cm...]{geometry}` | `Devanagari_main.template:L101` | `2.0cm` | Left, right, bottom margins (top is `2.5cm`). |

### C. Horizontal Syllable & Danda Spacing
Defined in `_render_devanagari_mantra_body()` in [`src/render_pdf.py`](file:///c:/Users/sekha/OneDrive/Documents/GitHub/jaimineeyasamavedam/src/render_pdf.py):

| Target | Code / Macro | Location | Value | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Intra-Word Syllables** | `\hskip 0pt plus 1.5pt\allowbreak ` | Line 924 | `0pt` base | Keeps syllables within a chant word tight while providing natural break flexibility. |
| **Multi-Swara Separation** | `\hspace{0.18em} ` | Line 922 | `0.18em` | Gentle breathing room when adjacent syllables have complex swara clusters. |
| **Pre-Danda Spacing** | `\nolinebreak\hspace{0.04em}।` | Line 947 | `0.04em` | Danda follows word with controlled spacing. |
| **Post-Danda Separation** | `\allowbreak\hspace{0.20em} ` | Line 947 | `0.20em` | Clean pause before the next sentence. `\allowbreak` allows clean line breaking at dandas. |
| **Verse Numerals** | `\hspace{0.20em}\mbox{॥ {num} ॥}` | Line 898 | `0.20em` | Standard spaced danda box for the terminal verse number. |

### D. Swara Stacking & Elevation
Defined in [`templates/pdf/Devanagari_main.template`](file:///c:/Users/sekha/OneDrive/Documents/GitHub/jaimineeyasamavedam/templates/pdf/Devanagari_main.template):

| Macro | Location | Elevation | Description |
| :--- | :--- | :--- | :--- |
| `\swarastack{#1}{#2}` (KPully) | Lines 137–141 | `\raisebox{2.35ex}[0pt][0pt]{#2}` | Centers swara `#2` strictly above akshara `#1` with zero horizontal expansion. |
| `\stackunder{#1}{#2}` (Standard) | Lines 146–150 | Standard LaTeX subscript stack | Positions swaras below the akshara base. |
| `\dandaWithArc` (MOD-A1) | Lines 169–176 | Stem at `0.802*dimen0` | Symmetrically balances whitespace and centers arc atop danda. |
| `\modGUnder` (MOD-G) | Lines 190–195 | `\raisebox{-0.18ex}[0pt][0pt]{\hspace{0.22em}\char"E003}` | Lower under-slash positioned at bottom-center of syllable. |
| `\caretWithSwara` (MOD-B) | Lines 201–209 | `\raisebox{2.35ex}[0pt][0pt]` | Positions apex swara exactly on the horizontal swara line atop the caret. |

---

## 2. Devanagari HTML (Web)

Defined in [`templates/html/Devanagari_main_html.template`](file:///c:/Users/sekha/OneDrive/Documents/GitHub/jaimineeyasamavedam/templates/html/Devanagari_main_html.template):

### A. Root & Base Sizing
- `body`: `font-size: 16px;` (Line 64)
- `.sanskrit-text`: `font-size: 1.2rem;` (`19.2px`, Line 79)
- `.sanskrit-large`: `font-size: 1.4rem;` (`22.4px`, Line 82)

### B. Mantra Words & Ruby Akshara
- `.mantra-text`: `font-size: 1.5rem;` (`24px`, Line 300)
- `.akshara-base`, `rb.akshara-base`: `font-size: 1.5rem;` (`24px`, Line 307)
- `rt.swara-above`: `font-size: 0.80rem;` (`12.8px`, Line 345), `transform: translateY(0.1em)`
- `.swara-text` (fallback text row): `font-size: 0.80rem;` (Line 340)
- `.danda`: `font-size: 1.5rem;` (Line 360), `margin: 0 0.15em;`
- `.verse-num`: `font-size: 1.4rem;` (Line 370)

### C. Micro-Modifiers (`.swara-mod`)
- `.swara-mod.mod-a` (slur arc): `font-size: 0.60em;`, `top: -0.85em;`, `left: 100%; transform: translateX(-40%);`
- `.swara-mod.mod-a1` (arc over danda): `font-size: 0.60em;`, `top: -0.85em;`, `left: 100%; transform: translateX(-20%);`
- `.swara-mod.mod-a2` (overhead center arc): `font-size: 0.60em;`, `top: -0.85em;`, `left: 50%; transform: translateX(-50%);`
- `.swara-mod.mod-c` (shoulder dot): `font-size: 0.65em;`, `left: 100%; transform: translateX(-0.15em);`

---

## 3. Malayalam PDF & HTML Reference

### A. PDF (`templates/pdf/Malayalam_main.template`)
- `\documentclass[12pt, a4paper]{book}`
- `\setstretch{2.15}` (Malayalam baseline stretch)
- `Scale=1.15` for `Aksharamukha-Malayalam` / `JaimineeyaMalayalam.ttf`
- `\swarastack`: `\raisebox{2.35ex}[0pt][0pt]{#2}`
- Intra-word syllable rule (`src/render_pdf.py:L1945`): `\hskip 0pt plus 1.5pt\allowbreak `

### B. HTML (`templates/html/Malayalam_main_html.template`)
- `.swara-mod.mod-a1` (arc over danda): `transform: translateX(-20%);` (synchronized with Malayalam script danda geometry).

---

## 4. Quick Tuning Cheat Sheet

| I want to change... | File | Line / Location | Parameter to edit |
| :--- | :--- | :--- | :--- |
| **Line spacing between lines in a verse (PDF)** | `templates/pdf/Devanagari_main.template` | Line 95 | `\setstretch{...}` (increase if swaras touch line above) |
| **Devanagari Mantra Font Size (PDF)** | `templates/pdf/Devanagari_main.template` | Lines 64, 71 | `\setmainfont[Scale=...]`, `\devafont[Scale=...]` |
| **Red Swara Font Size (PDF)** | `templates/pdf/Devanagari_main.template` | Lines 67, 74 | `\smallredfont[Scale=...]` |
| **Devanagari Mantra Font Size (HTML)** | `templates/html/Devanagari_main_html.template` | Line 300 | `.mantra-text { font-size: ... }` |
| **Red Swara Font Size (HTML)** | `templates/html/Devanagari_main_html.template` | Line 345 | `rt.swara-above { font-size: ... }` |
| **Space between word and danda (PDF)** | `src/render_pdf.py` | Line 928 | `\hspace{0.04em}।` |
| **Space after danda before next sentence (PDF)** | `src/render_pdf.py` | Line 928 | `\allowbreak\hspace{0.20em}{}` |
| **Space between verses (PDF)** | `src/render_pdf.py` | Line 901 | `\par\vspace{...}` |
| **Arc position over danda (HTML)** | `templates/html/Devanagari_main_html.template` | Line 398 | `.swara-mod.mod-a1 { transform: translateX(...) }` |
