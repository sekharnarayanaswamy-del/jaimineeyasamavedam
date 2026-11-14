# LaTeX Workflow & Studio Guide

This guide explains how to effectively manage the Samaveda LaTeX project using **Antigravity** and your local **LaTeX Studio/Workshop** plugin.

## 1. The Power of Pair Programming
While your LaTeX Studio/Workshop plugin provides the visual environment, Antigravity acts as the specialized "typesetting engine" for the Jaimineeya Samavedam.

| Feature | Role of LaTeX Plugin | Role of Antigravity |
| :--- | :--- | :--- |
| **Viewing** | Provides syntax highlighting and PDF preview. | Explains complex Vedic macros (e.g., `\stackleft`). |
| **Editing** | Allows manual one-off tweaks to text. | Performs global, safe, AI-powered structural edits. |
| **Compilation** | Provides "Build" buttons and shortcuts. | Orchestrates the `lualatex` build process via CLI. |
| **Debugging** | Highlights errors in the code. | Analyzes `.log` files to find and fix root causes. |

## 2. Key Project Macros
The project uses custom commands to handle the unique requirements of Vedic typesetting:

### Devanagari Macros
*   **`\stackcenter{Mantrah}{Swarah}`**: Stacks a Swara mark centrally beneath a mantra syllable.
*   **`\stackleft{Mantrah}{Swarah}`**: Used for multi-character Swara marks (aligns based on the project's traditional layout).
*   **`\accentmark{Size}{Char}`**: Dynamically sizes and bolds Devanagari numerals or symbols.
*   **`\accentadj`**: Provides fine-tuned kerning (spacing adjustment) between colliding accents.

### Malayalam Macros & Stacking
*   **`\swarastack{Syllable}{Swara}`**: Dynamic width-aware stacking engine that places red swara notations **above** the base Malayalam akshara without collision.
*   **`\stackcenter{Syllable}{Swara}`** & **`\stackleft{Syllable}{Swara}`**: Overhead stacking commands mapped to `\swarastack`.
*   **`\accentmark{Size}{Char}`**: Sizes Vedic combining marks (`\devafont`) over/under Malayalam aksharas.
*   **`\makeindex` & `\apptocmd{\theindex}{\malayalamfont}{}{}`**: Compiles full two-column alphabetical indices in Malayalam (`അനുക്രമണിക`).

## 3. Recommended Workflow

### Step A: Generation

**Devanagari:**

python src/render_pdf.py data/output/Vargeekaran.json --type samhita


**Malayalam:**

python src/render_pdf.py data/output/malayalam/Samhita_Malayalam.json --script malayalam


### Step B: AI-Driven Refinement
Instead of hunting through 20,000+ lines of LaTeX, ask Antigravity to perform targeted shifts:
*   *"Make the Rishi/Devata metadata line purple in the PDF."*
*   *"Increase the vertical gap between the mantra lines by 10%."*

### Step C: Compilation & Preview
Use your plugin's **PDF Preview** to see the changes. If the build breaks, simply tell Antigravity:
> *"The build failed with an error about 'Undefined control sequence'. Please fix it."*

## 4. Environment & Font Requirements
*   **Devanagari**: Compiled with LuaLaTeX/XeLaTeX, `fontspec`, and `AdishilaVedic`.
*   **Malayalam**: Compiled with XeLaTeX (2-pass + `makeindex`) using:
    - Base Text: `NotoSerifMalayalam-Regular.ttf`
    - Superscript Swaras & Modifiers: `JaimineeyaSwara.ttf`
    - Vedic Accents: `NotoSerifDevanagari-Regular.ttf`
    - English Numerals & Footnotes: `Nimbus Roman.ttf`

## 5. PDF Typography & Page Geometry (A4 vs Book Edition)

The project maintains two distinct print targets for Devanagari Samaveda PDFs:
*   **A4 Edition** (`templates/pdf/Devanagari_main.template`): Desktop preview and standard A4 printing.
*   **Book Edition** (`templates/pdf/Devanagari_book.template`): Physical book printing (Crown Quarto trim).

### Font Scaling Factors (AdishilaVedic)
Both templates run under `\documentclass[12pt, ...]{book}`. The effective font size is determined by `fontspec` scaling:

| Macro / Family | Scale Factor | Effective Size | Purpose |
| :--- | :--- | :--- | :--- |
| `\devafont`, `\setmainfont` (AdishilaVedic) | `Scale=1.35` | **16.2 pt** | Main mantra text, Samam chant lines, Rik mula |
| `\headerfont` (AdishilaVedicBold) | `Scale=1.45` | **17.4 pt** | Chapter and Section structural titles |
| `\smallredfont` (AdishilaVedic) | `Scale=0.95` | **11.4 pt** | Swara number notations in SwaraRed (`#C62828`) |
| `\swarafont` (JaimineeyaSwara) | `Scale=0.88` | **10.56 pt** | Jaimineeya swara glyphs and accents |
| `\arcfontDeva` (JaimineeyaSwara) | `Scale=1.25` | **15.0 pt** | Overhead connecting arcs |

### Title Page Typography (A4 vs. Book)

| Element | A4 Edition | Book Edition |
| :--- | :--- | :--- |
| **Mangalam / Guruvandana** | `\fontsize{11pt}{15pt}` | `\fontsize{9.5pt}{13pt}` |
| **Main Book Title** | `\fontsize{34pt}{42pt}\bfseries` | `\fontsize{28pt}{34pt}\bfseries` |
| **Subtitle** | `\fontsize{20pt}{26pt}\bfseries` | `\fontsize{17pt}{22pt}\bfseries` |
| **Publisher Heading** | `\fontsize{15pt}{20pt}\bfseries` | `\fontsize{13pt}{17pt}\bfseries` |
| **Publisher Details & Year** | `\fontsize{14pt}{19pt}` | `\fontsize{12pt}{16pt}` |

### Document Body Elements

| Document Element | LaTeX Macro | Standard Size | Rendered Size (1.35x Scale) |
| :--- | :--- | :--- | :--- |
| **Chapter / Parva Header** | `\chapter*` (`\huge\headerfont`) | 20.7 pt | **~30.0 pt** |
| **Section / Kandah Header** | `\section*` (`\Large\headerfont`) | 14.4 pt | **~20.9 pt** |
| **Rik Mula Verse** | `\normalsize` (Upright Bold, Blue) | 12.0 pt | **16.2 pt** |
| **Samam Chant Line** | `\normalsize\bfseries` (Bold) | 12.0 pt | **16.2 pt** |
| **Samam Subsection Title** | `\normalsize` (Bold, Green) | 12.0 pt | **16.2 pt** |
| **Rik Metadata** | `\footnotesize` (Purple) | 10.0 pt | **13.5 pt** |
| **Samam Metadata** | `\footnotesize` (Brown) | 10.0 pt | **13.5 pt** |
| **Footnotes** | `\footnotesize` | 10.0 pt | **13.5 pt** |
| **Summary Table** | `\small` | 11.0 pt | **14.85 pt** |
| **Prayoga Appendix Header** | `\large\bfseries` | 14.4 pt | **19.44 pt** |
| **Prayoga Appendix Body** | `\normalsize` | 12.0 pt | **16.2 pt** |
| **Index (वर्णानुक्रमणिका)** | `\footnotesize` | 10.0 pt | **13.5 pt** |

### Page Dimensions & Layout
*   **A4 Edition**: `210mm × 297mm`, portrait, `oneside`. Margins: Left/Right = 18mm, Top/Bottom = 20mm. Index in 3 columns.
*   **Book Edition**: `180mm × 228mm`, `twoside`. Margins: Inner = 18mm, Outer = 15mm, Top/Bottom = 19mm. Index in 2 columns.

### Swara & Swara Modifier Font Specifications
*   **Swara Numbers (`\smallredfont`)**:
    *   Font: `AdishilaVedic.ttf` (`BoldFont=AdishilaVedicBold.ttf`), `Scale=0.95` (**11.4 pt**).
    *   Color: `SwaraRed` (`#C62828` in color; black in B&W).
    *   Placement: Stacked below base akshara (`\raisebox{-1.05ex}`) in Standard mode, or above base akshara (`\raisebox{1.55ex}`) in Kodunthirapully mode (`-kpully`).
*   **Swara Modifiers (`\swarafont`)**:
    *   Font: `JaimineeyaSwara.ttf`, `Script=Grantha`, `Scale=0.88` (**10.56 pt**), `AutoFakeBold=3.5`, `AutoFakeSlant`.
    *   Color: `ModifierSkyBlue` (`#0284C7` in color; black in B&W).
*   **Overhead Arcs (`\arcfontDeva`)**:
    *   Font: `JaimineeyaSwara.ttf`, `Scale=1.25` (**15.0 pt**), `AutoFakeBold=3.5`.
*   **Core Modifiers**:
    *   `\arcOverSyllable`: Overhead conjunct arc (`U+E004` / `U+E02E`) centered above syllables.
    *   `\dandaWithArc`: Arc over danda (`U+E00D`) positioned on the danda stem.
    *   `\caretWithSwara`: Peak elevation caret (`U+E005`) bridging two syllables with apex swara.
    *   `\modGUnder`: Lower under-slash (`U+E003`) below-right of syllable.
    *   `\underbarMark`: In-line under-dash rule (`\rule{0.35em}{0.28ex}`).
    *   Tone dots/commas: In-line `{\Large\textbf{.}}` / `{\Large\textbf{,}}` in ModifierSkyBlue.

---
*Created by Antigravity for the Jaimineeya Samavedam Digitalization Project.*

