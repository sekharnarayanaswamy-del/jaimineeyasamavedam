# Jaimineeya Samaveda Processing & Publishing Pipeline

A production-grade Vedic text processing, transliteration, and typesetting system for the **Jaimineeya Samaveda (JSV) Samhita** in both **Devanagari** and **Malayalam (with authentic Grantha swara notations & Vedic modifiers)**.

> [!NOTE]
> The legacy-font conversion tools that used to live in `pdfconverter/` are now
> a separate private repository,
> **[Converter-tools](https://github.com/sekharnarayanaswamy-del/Converter-tools)**.
> It covers three decoding subprojects: Sanskrit98 PDF → Malayalam
> (Mahanyasam, Sringeri Paddhati), Siddhanta PDF → HTML (Kauthuma Sāmaveda
> Saṃhitā), and Ganapathy Grantha Word → Sanskrit 2020 Word (Taittiriya
> Saṃhitā with Sapta Lakshana).

---

## 🚀 One-Shot Master Pipeline & Named Render Profiles

To run the pipeline using the configured **active default profile** (`fast_preview`):

```powershell
python src/run_pipeline.py
```

### Named Render Profiles (`src/pipeline_config.yaml`):
Instead of passing complex CLI combinations every time, standard render subsets are managed as named profiles:

| Profile | Target Corpora | Modes | Formats | KPully | Description |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **`fast_preview`** *(Default)* | Samhita | `combined` | HTML, TXT | **True** | Fast curation iteration (~5s) in Kodunthirapully mode, skips slow LaTeX PDF compilation. |
| **`standard`** | Samhita, Aaranam | `combined` | PDF, HTML | False | Standard publication set for primary liturgical study. |
| **`chanting`** | Samhita | `nometa` | PDF, HTML | **True** | Practitioner chanting editions without RDC headers. |
| **`full_release`** | Samhita, Aaranam, Collections | `combined`, `separate`, `nometa` | PDF, HTML, TXT | **True** | Exhaustive release suite generating all variants and formats. |

### Profile CLI Usage:
```powershell
# List all configured profiles and show active default:
python src/run_pipeline.py --list-profiles

# Run a specific profile:
python src/run_pipeline.py --profile fast_preview
python src/run_pipeline.py -p standard
python src/run_pipeline.py -p chanting
python src/run_pipeline.py -p full_release

# Ad-hoc overrides:
python src/run_pipeline.py --html-only
python src/run_pipeline.py --corpora samhita aaranam
python src/run_pipeline.py --modes combined separate
```

---

## 📂 Source Text Subfolder Locations & Staging Layout

Source texts reside in dedicated per-corpus subfolders under both the **Golden Baselines** anchor repository and the **Stage-Numbered Corpora** workspace:

### 1. Golden Baselines Anchor Directory (`data/baselines/golden/`)
* **Samhita (Devanagari)**: `data/baselines/golden/Devanagari/samhita/input/Samhita_Devanagari_Unicode.txt`
* **Samhita (Malayalam)**: `data/baselines/golden/Malayalam/samhita/input/Samam_Malayalam_Unicode.txt`
* **Aaranam (Devanagari)**: `data/baselines/golden/Devanagari/aaranam/input/Aaranam_latest.txt`
* **Collections (Devanagari)**: `data/baselines/golden/Devanagari/collection/input/`

### 2. Stage-Numbered Corpus Workspace (`data/corpora/<corpus>/`)
Each corpus directory is strictly partitioned into six sequential processing stages:
* `01_input/`: Canonical master source texts and metadata tables.
* `02_ast/`: Parsed JSON Abstract Syntax Trees (`*_out.json`).
* `03_reconciliation/`: Reconciliation tables, cross-references, and CSV exports.
* `04_curated/`: Curated subsets and custom filtered selections.
* `05_renders/`: Clean render outputs partitioned exclusively into format subdirectories (`pdf/`, `html/`, `txt/`). **No loose files reside at the root of `05_renders/`**.
* `06_reports/`: Structural integrity summaries and continuity audits.
* `run_manifest.json`: Active run metadata, structural metrics, and timestamp tracking.

---

## 🏷️ 3-Tier Versioning & Numbering Scheme

The project maintains three strictly decoupled versioning tiers:

1. **Tier 1: Engine Version** (e.g. `engine_version: "4.0.0"` in `src/pipeline_config.yaml`)  
   Reflects the architectural generation engine (parsers, compilers, renderers).
2. **Tier 2: Corpus Editions** (e.g. `editions: { samhita: "3.28", aaranam: "1.14", collections: "2.05", kpully: "1.00" }` in `src/pipeline_config.yaml` and `src/VERSION`)  
   Tracks editorial and liturgical content maturity for each specific corpus independently.
3. **Tier 3: Active Run / Manifest Version** (`run_manifest.json` in each corpus folder)  
   Tracks live execution artifacts with precise UTC timestamps, git commit hashes, and domain metrics (Pathas, Khandas, Samas).

---

## 🛡️ Validation & Golden Promotion Workflow

To guarantee that text edits or code changes never introduce regressions:

```powershell
# 1. Run dual-track validation (Track A domain invariance + Track B semantic diff):
python src/tools/validate_run.py samhita
python src/tools/validate_run.py aaranam
python src/tools/validate_run.py all

# 2. When intentional curation changes are verified, promote the active run to golden baseline:
python src/tools/validate_run.py samhita --promote

# 3. Run full automated regression suite:
python src/tools/run_regression_suite.py
```

> [!NOTE]
> `render.py` has zero dependency on `.yaml` configuration files and dynamically binds to the active corpus edition. All global settings, build profiles, and corpus paths are centralized in `src/pipeline_config.yaml`.
> For an exhaustive architectural walkthrough of the 3-tier numbering hierarchy, golden promotion mechanics, and curation workflows, see [VERSIONING_AND_WORKFLOW.md](VERSIONING_AND_WORKFLOW.md).


---

## 📖 Step-by-Step & Individual CLI Workflows

### 1. Malayalam Pipeline (Full Samhita, Rik + Samam + RDC)

The Malayalam workflow supports interactive editing of Unicode text files, JSON AST conversion, and rendering to PDF, HTML, and Unicode TXT.

#### Step A: Generate JSON from Text / Corrections
Whenever you edit or correct [`data/input/Malayalam/Samam_Malayalam_Unicode.txt`](data/input/Malayalam/Samam_Malayalam_Unicode.txt), convert it into the AST JSON:
```powershell
python -X utf8 src/generate_json.py data/input/Malayalam/Samam_Malayalam_Unicode.txt --output data/corpora/samhita/02_ast/Samam_Malayalam.json
```

#### Step B: Render PDF, HTML, and TXT
Run `src/render.py` with `--script malayalam` in one of the three output modes:

1. **Combined Mode (Default — Rik + Samam + Rishi/Devata/Chandas):**
   ```powershell
   python -X utf8 src/render.py data/corpora/samhita/02_ast/Samam_Malayalam.json --script malayalam
   ```
   *Generates:*
   - `data/corpora/samhita/05_renders/pdf/Samam_Malayalam.pdf`
   - `data/corpora/samhita/05_renders/html/Samam_Malayalam.html`
   - `data/corpora/samhita/05_renders/txt/Samam_Malayalam_Unicode.txt`

2. **Separate Mode (Separate Rik and Samam files with Metadata):**
   ```powershell
   python -X utf8 src/render.py data/corpora/samhita/02_ast/Samam_Malayalam.json --script malayalam --output-mode separate
   ```

3. **No-Metadata Mode (Mantra Texts Only, no RDC headers):**
   ```powershell
   python -X utf8 src/render.py data/corpora/samhita/02_ast/Samam_Malayalam.json --script malayalam --output-mode nometa
   ```

---

### 2. Devanagari Pipeline (Standard Sanskrit)

#### Step A: Generate JSON from Devanagari Source
```powershell
python -X utf8 src/generate_json.py data/input/Samhita_Devanagari_Unicode.txt --output data/corpora/samhita/02_ast/Samhita_ast.json
```

#### Step B: Render Devanagari Outputs
1. **Combined Mode:**
   ```powershell
   python -X utf8 src/render.py data/corpora/samhita/02_ast/Samhita_ast.json
   ```
2. **Separate Mode:**
   ```powershell
   python -X utf8 src/render.py data/corpora/samhita/02_ast/Samhita_ast.json --output-mode separate
   ```
3. **NoMeta Mode:**
   ```powershell
   python -X utf8 src/render.py data/corpora/samhita/02_ast/Samhita_ast.json --output-mode nometa
   ```
4. **Kodunthirapully Variant (`-kpully`):**
   Render Devanagari Samam with red swara markings positioned **above** the mantra text (edition `1.00`):
   ```powershell
   python -X utf8 src/render.py data/corpora/samhita/02_ast/Samhita_ast.json -kpully --output-mode nometa -o Samhita_kpully_Devanagari
   ```

---

### 3. Aranyakam Parva Splitting Tool (`scripts/split_aranyakam_parvas.py`)

Extracts individual parva files from the unified master Aranyakam Unicode file [`data/corpora/aaranam/01_input/Aaranam_latest.txt`](data/corpora/aaranam/01_input/Aaranam_latest.txt) (2,677 lines):

```powershell
python scripts/split_aranyakam_parvas.py
```

#### Outputs:
1. **Canonical Continuous Files** (`Parva_7_...` to `Parva_12_...`) in [`data/corpora/aaranam/01_input/parvas/`](data/corpora/aaranam/01_input/parvas/):
   - `Parva_7_Vrata_Parva_Devanagari_Unicode.txt` (व्रत पर्व, 974 lines, 56 subsections)
   - `Parva_8_Arkani_Patha_Devanagari_Unicode.txt` (अर्काणि पाठः, 919 lines, 56 subsections)
   - `Parva_9_Dvandva_Parva_Devanagari_Unicode.txt` (द्वन्द्व – पर्व, 515 lines, 29 subsections)
   - `Parva_10_Shukriya_Parva_Devanagari_Unicode.txt` (शुक्रिय पर्व, 124 lines, 7 subsections)
   - `Parva_11_Shakvarya_Parva_Devanagari_Unicode.txt` (शाक्वर्य पर्व, 42 lines, 1 subsection)
   - `Parva_12_Aupanishada_Parva_Devanagari_Unicode.txt` (औपनिषद पर्व, 93 lines, 5 subsections, with Closing Mantras)
2. **Aranyakam-Relative Aliases** (`Parva_1_...` to `Parva_6_...`) in [`data/corpora/aaranam/01_input/parvas/`](data/corpora/aaranam/01_input/parvas/) for liturgical convenience.
3. **Mirrored Canonical Files** directly in [`data/corpora/aaranam/01_input/`](data/corpora/aaranam/01_input/).
4. **AST Compatibility**: 100% verified through `src/generate_json.py` (`parse_unicode_text_file`) with zero line loss ($974+919+515+124+42+93=2,667$ content lines).

---

### 4. Unified Samhita + Aranyakam Samam Compilation (`scripts/recompile_samhita_aranyakam_samam.py`)

Compiles the complete unified Samam chanting corpus across both **Samhita** (Supersections 1–6) and **Aranyakam** (Supersections 7–12) into continuous-flow publications ($1,521$ Samams, $876$ Arsheyams across $12$ Supersections and $71$ Sections):

```powershell
# 1. Compile A4 Flow Edition (Color & B&W):
python scripts/recompile_samhita_aranyakam_samam.py --all-colors

# 2. Compile Book Format (180x228mm Crown Quarto, B&W):
python scripts/recompile_samhita_aranyakam_samam.py --book --bw

# 3. Build/Refresh Combined AST independently:
python scripts/build_combined_ast.py
```

#### Key Publications Generated in `data/corpora/samhita_aranyakam/05_renders/pdf/`:
- `Samhita_Aranyakam_flow_bw_Samam_Devanagari.pdf` (A4 Flow, Black & White, 251 pages)
- `Samhita_Aranyakam_book_flow_bw_Samam_Devanagari.pdf` (180×228mm Book Flow, Black & White, 385 pages)
- `Samhita_Aranyakam_flow_Samam_Devanagari.pdf` (A4 Flow, Color edition)

#### Key Typography & Layout Features:
- **20 pt Body Typography Profile** (`\documentclass[12pt, ...]{book}`):
  - **Main Chant Text (`\devafont`)**: `Scale=1.68` (**20.16 pt**), `AdishilaVedic.ttf` with `AutoFakeBold=1.18`.
  - **Section & Parva Headings (`\headerfont`)**: `Scale=1.79` (**21.48 pt**), `AdishilaVedicBold.ttf`.
  - **Swara Numbers (`\smallredfont`)**: `Scale=1.18` (**14.16 pt**), `AdishilaVedic.ttf`.
  - **Overhead Arcs (`\arcfontDeva`)**: `Scale=1.55` (**18.60 pt**), `JaimineeyaSwara.ttf`.
  - **Vedic PUA Modifiers (`\swarafont`)**: `Scale=1.10` (**13.20 pt**), `JaimineeyaSwara.ttf`.
- **Balanced Running Header**: Alternates `[Supersection Name] — [Section Name] — [Page Number]` across verso/recto pages using `fancyhdr`.
- **Flowing Footnotes with Tab Separation**: Formats footnote apparatus into a continuous paragraph using `\usepackage[perpage,para]{footmisc}` separated by tab spacing (`\hskip 2.0em plus 1.0em minus 0.5em`), separated from body text by a clear `\footnoterule` and swara-safe clearance (`\skip\footins` at 16pt).
- **Manuscript Apparatus Support**: Ingests footnote abbreviations (`को.प` for Kodunthirapully, `तो.प` for Togur).

---

## 🔤 Malayalam Vedic Font & Swara Modifiers

The custom OpenType font [`fonts/JaimineeyaSwara.ttf`](fonts/JaimineeyaSwara.ttf) includes:
- **74 Precomposed Virama Glyphs (ക്, ച്, etc.)** featuring authentic Malayalam Chandrakala viramas.
- **Vedic Manuscript Ligatures & Bases:** Custom glyphs for `Pla` (`pla_jsv`), `Sha` (`sha_mal`), `Kra` (`k_ra_jsv`), and `Tra` (`t_ra_gran`).
- **All 11 Canonical Vedic Swara Modifiers:**

| # | Modifier | Typing Shortcut / Input | Stacking Position | Hex / PUA |
|---|---|:---:|:---:|:---:|
| 1 | **Syllable Arc (Tie / Breve)** | `(⁀)` or `(͡)` | Stacked Above | `E004 / 2040 / 0361` |
| 2 | **Caret (^ / ˄)** | `(^)` or `(˄)` | Stacked Above | `E005 / 005E / 02C4` |
| 3 | **Roof (/\\ / Ʌ)** | `(/\)` or `(Ʌ)` | Stacked Above | `E006 / 0245 / 2227` |
| 4 | **Combining Small Ring (˚ / ͦ)** | `(˚)` or `(ͦ)` | Stacked Above | `E009 / 0366 / 02DA` |
| 5 | **High/Mid-Dot (H / ॱ)** | `(ॱ)` or `(·)` | Stacked Above | `E001 / 0971 / 00B7` |
| 6 | **Underbar (_)** | `(_)` or `_` | Stacked Below | `E007 / 005F` |
| 7 | **Phrasing Danda (L / ╷)** | `(╷)` or `(L)` or `(⃓)` | Stacked Below | `E002 / 2577 / 20D3` |
| 8 | **Descending Tone (\\ / ╲)** | `(\)` or `(╲)` | Stacked Below | `E003 / 005C / 2572` |
| 9 | **Ascending Tone (/)** | `(/)` | Stacked Below | `E008 / 002F` |
| 10 | **Low Comma / Hook (,)** | `(,)` or `(ˏ)` | Stacked Below | `E00A / 002C / 0326` |
| 11 | **Phrasing Double Danda (\|\|)** | `(\|\|)` or `(॥)` | Inline | `E00B / 0965` |

### Visual Documentation & Tables
- **Interactive Glyph Inventory:** [`data/output/malayalam/glyph_table.html`](data/output/malayalam/glyph_table.html)
- **High-Res Font Chart:** [`data/output/malayalam/glyph_grid_JaimineeyaSwara.png`](data/output/malayalam/glyph_grid_JaimineeyaSwara.png)

---

## 🛠️ Font & Table Regeneration Scripts

To rebuild the font or regenerate the glyph table after editing mappings:
```powershell
python scripts/build_swara_font.py
python scripts/generate_glyph_grid.py
```
