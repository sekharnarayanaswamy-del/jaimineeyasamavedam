# Technical Specification (SPEC.md)
## Jaimineeya Samaveda (JSV) Devanagari-to-Malayalam Transliteration & Stacking Pipeline

---

## 1. Executive Summary & Objective

This project automates the conversion, transliteration, and typesetting of the **Jaimineeya Samaveda (JSV) Samhita** from digital Devanagari sources into publication-ready **Malayalam script with stacked Grantha swara notations**.

By parsing the existing digital Devanagari text directly from `C:\Users\sekha\OneDrive\Documents\GitHub\jaimineeyasamavedam`, this solution bypasses manual re-typing and error-prone manuscript OCR while preserving 100% base-text accuracy.

### Primary Goals:
1. **Automated Base Transliteration:** Convert Sanskrit Devanagari base text into standard Malayalam script with 100% phonetic accuracy.
2. **Swara Notation Mapping:** Map subscript Devanagari swara letters to authentic **Grantha Unicode glyphs** (`U+11300`–`U+1137F`). The relevant Grantha characters are available in the `https://docs.google.com/spreadsheets/d/1S0xu2DdhuhbZLVrSjJrKp-iH152Ys_QB0fWNLK6MSYI/edit?gid=0#gid=0` Google Sheet.  There has to be the logic to override Grantha rules for "Pla" and "Sha" and associated ligatures. Rest of the swaras are classical Grantha and so Grantha ligatures are applicable.  
3. **Layout Stack Inversion:** Invert vertical positioning—transforming Devanagari *subscript* swaras (below base text) into Malayalam *superscript* swaras (stacked directly above base text).
4. **Editable Intermediate Formats:** Export intermediate representations as structured JSON and lightweight plain-text compact markup for quick proofreading and git diffing. We have a Unicode export for Devanagari already. 
5. **Typesetting Output:** Compile publication-grade PDFs using XeLaTeX/LuaLaTeX and micro-positioning macros. An extensive JSON --> TEX mapper is already available and could possibly be extended (render_pdf.py) to handle the Malayalam text. 
6. **Modifier table:** This is a new artifact in Malayalam that is not present in Devangari. We need to define a scheme to introduce swara modifiers. The Unicode encoding for this could be derived from the "Modified Set" table in https://docs.google.com/spreadsheets/d/1S0xu2DdhuhbZLVrSjJrKp-iH152Ys_QB0fWNLK6MSYI/edit?gid=0#gid=0` Google Sheet. Suggestion is also given for the modifier encoding. 
7. **Correction workflow:** The correction workflow for Devanagari is already available and we should reuse that for Malayalam as well. Manual corrections done in Unicode text file and then converted to json file with generate_json.py and then subsequently converted to html, tex/pdf and Unicode text. 
7. **Reuse existing assets:** Use the assets available in the jaimineeyasamavedam project. The key .py files are generate_json.py, render_pdf.py, generate_website.py. Also, read the skills and documentation available in the project folder. 

---

## 2. Technical Architecture & Data Flow

```
+---------------------------+
| Devanagari Source Text    |
| (Vedic JSV Samhita Markup)|
+-------------+-------------+
              |
              v
+-------------+-------------+
| 1. Vedic Parser           |
| (parse_vedic_markup)      |
+-------------+-------------+
              |
              v
+-------------+-------------+
| 2. Aksharamukha & Grantha |
| Transliteration Engine    |
+-------------+-------------+
              |
              v
+-------------+-------------+
| 3. Swara Inverter         |
| (Subscript -> Superscript)|
+-------------+-------------+
              |
              v
+-------------+-------------+
| 4. JSON / Compact Markup  |
| Intermediate Storage      |
+-------------+-------------+
              |
              +-----------------------+
              |                       |
              v                       v
+-------------+-------------+ +-------+-------------------+
| 5a. XeLaTeX PDF Renderer  | | 5b. HTML / Web Generator  |
| (render_vedic_latex)      | | (generate_vedic_website)|
+---------------------------+ +---------------------------+
```

---

## 3. Key Pipeline Modules

### 3.1 Parser & Structural Normalization
- Extracts structural elements: `Parva` (SuperSection), `Kandah` (Section), `Arsheyam` (SubSection), `Samam` (Mantra Sets), and `Rik` (Individual verse).
- Normalizes dandas (`॥`), Devanagari numerals (`०-९`), visargas, and footnoting hooks (`(s1)`).
- Preserves ZWJ/ZWNJ placement and strips extraneous invisible control codes.

### 3.2 Transliteration Engine
- Uses `aksharamukha` library for Sanskrit Devanagari to Malayalam transliteration.
- Maps custom Vedic swara markers to Grantha Unicode characters (`U+11300`–`U+1137F`).
- Implements Visarga-Accent Preprocessing (relocating accent positioning visually relative to preceding vowels and Visarga `ः`).

### 3.3 Swara Stacking & Layout Inversion
- Inverts vertical swara positioning: Devanagari subscript swara marks are mapped to Malayalam superscript swara stackings above base aksharas.
- Micro-positioning macros in TeX handle exact glyph heights and horizontal alignments.

### 3.4 Data Models & Intermediate Formats
- **JSON Format:** Hierarchical structure (`Parva` -> `Kandah` -> `Arsheyam` -> `Samam` -> `Rik`).
- **Compact Markup:** Text representation suitable for diffing and manuscript proofreading.

---

## 4. Verification & Validation Plan

1. **Automated Syntax Check:** Run script execution tests and syntax verification.
2. **Akshara Integrity Verification:** Round-trip and phonetic verification across transliterated strings.
3. **Typesetting & Visual QA:** XeLaTeX compilation testing and visual stack alignment inspection.

---

## 5. Execution Instructions

```bash
# Run spec generator
python Malayalam_JSV/generate_spec.py
```

---

## 6. Frozen Swara Lookup (reviewed 2026-08-14)

The 229 distinct swara markers (25,606 total occurrences) extracted from
`data/input/Samhita_corrected.txt` are resolved through the frozen table
`Malayalam_JSV/swara_lookup_frozen.json`, generated by
`Malayalam_JSV/generate_marker_review.py`. The pipeline reads the frozen
JSON; it never reads the live Google Sheet.

### 6.1 Approved decisions (revised 2026-08-14: Ayugma-only mapping)

- **Only the Ayugma table is used.** Yugma swaras (even swaras) are not used
  by the Samhita and are omitted from `swara_mapping.json`. The corpus
  markers use exactly the Ayugma letter set (क ख च ट ण त थ प फ भ य स श ष
  प्ल त्र र क्र ङ); letters outside it do not occur as markers.
- **The 'Grantha Glyph' column is authoritative.** `grantha_text` is taken
  verbatim from the glyph column and `grantha_codepoints` are derived from
  the actual glyph characters, so they cannot drift from the curated glyphs.
  The 'Grantha Hex' column is kept as `sheet_hex_reference` for audit only
  (it is stale in places: A04, A13, A17).
- **A13 (Saa) -> Malayalam ശ (U+0D36)** per the reference manuscript: the
  sheet's Grantha Glyph column holds the Malayalam character for this swara.
  All `श`-family markers (श, शा, शि, शु, शी, …) now stack ശ + MALAYALAM
  matras (U+0D3E…U+0D4D): Grantha matras cannot shape onto the Malayalam
  base and produced dotted circles; `generate_marker_review.py` rewrites the
  matra codepoints (093E→0D3E etc.) whenever the last emitted base letter is
  A13.
- **Sheet anomalies FIXED in the sheet (2026-08-14), no overrides needed:**
  A04 glyph is now canonical ट = U+1131F (hex column still says U+1133D
  UPADHMANIYA — stale); A15/A17/A19 now carry the virama
  (𑌪𑍍𑌲 / 𑌤𑍍𑌰 / 𑌕𑍍𑌰) and resolve as sheet entries. No marker is
  `source=decided` anymore.
- **Corrupted markers** (9 occurrences, `source=corrupt` in the frozen
  table) are resolved best-effort and flagged in QA; no source data edits:
  `चा। द्ध्रिषाऔ(टि`, `शि। उपई(कि`, `Sटा`, `टि `, `खि `, `टा `, `षै `
  plus two source-annotation errors (input file to be corrected; the
  overrides become inert once the markers are removed):
  - `मा` — `नार्क्ता(मा)`: the marker does not match its word (नार्क्ता ends
    in -क्ता); the same mantra later renders the word मा with marker (कि).
  - `वृ` — `वृ(वृ)`: flagged corrupt per review.
  (No markers remain `source=fallback`.)

### 6.2 Generated artifacts
- `Malayalam_JSV/swara_mapping.json` — Ayugma-only swara table (19 entries,
  glyph-derived text + codepoints, `sheet_hex_reference` audit column) +
  modifiers deferred + fixed matra table; regenerable from
  `Malayalam_JSV/generate_swara_mapping.py <sheet.csv>`.
- `Malayalam_JSV/samhita_marker_review.csv` — human review table (all 229
  markers with per-character resolution, sheet-entry matches, flags).
- `Malayalam_JSV/swara_lookup_frozen.json` — machine-readable frozen lookup
  consumed by `src/malayalam/`; each entry carries BOTH `grantha_text`
  (actual Unicode glyph characters) and `grantha_codepoints`.

### 6.3 Fonts
Bundled in `fonts/` (static hinted TTFs from notofonts.github.io):
`NotoSerifMalayalam-Regular.ttf`, `NotoSansMalayalam-Regular.ttf`,
`NotoSansGrantha-Regular.ttf`, `NotoSerifGrantha-Regular.ttf`. Validated
with fontTools: Grantha faces contain U+11317/U+1134D/U+1133E; Malayalam
faces contain U+0D15.

### 6.4 Pilot implementation (supersection_1 / section_1, Samam only)

**Transliteration module** (`src/malayalam/`):
- `ml_map.py` — loads `swara_lookup_frozen.json` (lru_cache); exposes
  `marker_to_grantha` (prefers the frozen `grantha_text` characters, so the
  manuscript-truth Malayalam ശ flows through), `marker_source`,
  `is_footnote_marker`, `coverage_report`.
- `ml_transliterate.py` — Aksharamukha wrapper (danda placeholders,
  `devanagari_to_malayalam`, `devanagari_to_grantha` fallback for unknown
  markers), combining-mark normalization (virama-before-matra removal,
  space-detach fix, ാ+െ/േ collapse), post-processing (word-final മ്→ം,
  ാ-collapse, ്ൃ→ൃ), and syllable/grapheme splitting. `split_malayalam_syllables`
  merges C+virama+C conjuncts and chillu+consonant into one syllable — this
  mirrors `utils.combine_halants` and is the unit a swara stacks above.
  `devanagari_syllable_count` does NOT count a trailing `म्` (anusvara, not
  a syllable: `ता(त) म्` → Malayalam `താം` = 1 syllable).
- `ml_text.py` — `tokenize_mantra_line` (Word(Swara) pairs, dandas,
  footnotes, Devanagari-numeral runs kept verbatim), `transform_subsection`
  adds `malayalam-mantra-sets` = [{malayalam-mantra, devanagari-mantra}],
  `transform_ast`, `render_intermediate_text`, and a CLI:
  `python -m malayalam.ml_text --input data/output/Vargeekaran.json --output <json> --text-out <txt> --qa-out <qa> --supersection supersection_1 --section section_1`
  (run from repo root with `$env:PYTHONPATH="src"`).
  `transform_line` merges a STANDALONE anusvara word (`म्`, `ं`, `म्ः`;
  609 occurrences corpus-wide) into the preceding word token: as a separate
  word it would render as a bare Malayalam combining mark U+0D02 with no
  base (visible dotted circle).
- Syllable-count QA: asserts Devanagari syllable count == Malayalam syllable
  count per marked word; any mismatch is a warning. Pilot: 317 marked words,
  0 warnings, 0 unknown markers (60 distinct markers; every marked word
  resolves from the sheet — sources: sheet 317 / decided 0 / fallback 0
  occurrences in the pilot).

**Rendering** (`src/render_pdf.py --script malayalam`, Samam-only pilot):
- Transforms the AST in `main()` via `ml_text.transform_ast`, forces
  `output_mode='samam'`, uses `templates/pdf/Malayalam_main.template` +
  `templates/text/Malayalam_main.template`, and skips HTML output
  (`CreateHtmlFile` no-ops on a `None` template).
- `format_malayalam_samam` re-tokenizes each `malayalam-mantra` line and
  stacks the Grantha swara ABOVE the final syllable of the word with
  `\stackon` (via `\stackcenter` / `\stackleft`; `\stackleft` for swaras of
  >1 glyph). Swara glyphs are grouped into per-script font runs
  (`_swara_latex`): Grantha-block characters use `\granthafont`; non-Grantha
  characters (e.g. the manuscript-truth Malayalam ശ) use `\malayalamfont`,
  so mixed swaras like `ശ + Malayalam matra` get a font for every character.
  The stack gap is `\setstackgap{L}{0.7\baselineskip}` (template), which
  raises the swara ~16 pt (measured ink-to-ink) above the base syllable.
  Devanagari mantra numerals are converted to Malayalam digits
  (൧-൯) for the PDF only; the intermediate text keeps Devanagari numerals.
- Headers (supersection/section/subsection titles, TOC, index) remain
  Devanagari in phase 1 and are rendered with `\devafont`.

**Font & Typography Setup (xelatex/MiKTeX)**:
- `\setmainfont` & `\malayalamfont`: `NotoSerifMalayalam-Regular.ttf` for base Malayalam text.
- `\swarafont`: `JaimineeyaSwara.ttf` for superscript swaras, precomposed viramas, manuscript ligatures (Pla/Sha), and all 11 Vedic modifiers.
- `\devafont`: `NotoSerifDevanagari-Regular.ttf` for Vedic accents (Swarita, Anudatta, Kampa).
- `\latinfont`: `Nimbus Roman.ttf` for English numerals, page numbers, title metadata, and English text in footnotes.

---

## 5. Execution CLI Commands

### Step A: Generate AST JSON from Corrections
```powershell
python -X utf8 src/generate_json.py data/input/Malayalam/Samhita_Malayalam_corrected.txt --output data/output/malayalam/Samhita_Malayalam.json
```

### Step B: Compile PDF, HTML, and Unicode TXT
*   **Combined Mode (Full Samhita: Rik + Samam + RDC + Footnotes + Index):**
    ```powershell
    $env:PYTHONPATH="src"; python -X utf8 src/render_pdf.py data/output/malayalam/Samhita_Malayalam.json --script malayalam
    ```
*   **Separate Mode (Rik & Samam with metadata):**
    ```powershell
    $env:PYTHONPATH="src"; python -X utf8 src/render_pdf.py data/output/malayalam/Samhita_Malayalam.json --script malayalam --output-mode separate
    ```
*   **No-Metadata Mode (Mantra text only):**
    ```powershell
    $env:PYTHONPATH="src"; python -X utf8 src/render_pdf.py data/output/malayalam/Samhita_Malayalam.json --script malayalam --output-mode nometa
    ```

---

## 6. Output Artifacts (`data/output/`)
- **PDFs:** `data/output/pdf/Malayalam/` (`Samhita_Malayalam.pdf`, `Rik_Malayalam.pdf`, `Samam_Malayalam.pdf`, `Rik_NoMeta_Malayalam.pdf`, `Samam_NoMeta_Malayalam.pdf`)
- **HTMLs:** `data/output/html/Malayalam/` (`Samhita_Malayalam.html`, `Rik_Malayalam.html`, `Samam_Malayalam.html`, `Rik_NoMeta_Malayalam.html`, `Samam_NoMeta_Malayalam.html`)
- **Unicode TXTs:** `data/output/txt/Malayalam/` (`Samhita_Malayalam_Unicode.txt`, `Rik_Malayalam_Unicode.txt`, `Samam_Malayalam_Unicode.txt`, `Rik_NoMeta_Malayalam_Unicode.txt`, `Samam_NoMeta_Malayalam_Unicode.txt`)
- **Glyph Inventory:** `data/output/malayalam/glyph_table.html` & `data/output/malayalam/glyph_grid_JaimineeyaSwara.png`

