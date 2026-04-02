# Jaimineeya Samavedam Digitalization Project - Developer Guide

This guide provides a comprehensive overview of the Jaimineeya Samavedam digitalization project, focusing on the workflows for data correction, website generation, and PDF document creation.

## 1. Project Overview

The goal of this project is to digitize the Jaimineeya Samavedam Samhita, providing:
1.  A **Modern Website** for easy browsing and listening.
2.  **Print-ready PDF** documents (LaTeX-based) for physical publication.
3.  **Specialized Views** like the *Rik* or *Samam* of Samhita for traditional chanting verification.

The system is built on a custom text-to-JSON parsing engine that handles the specific structural requirements of the Samaveda (Parva > Kandah > Arsheyam > Samam) and supports a robust **Correction Cycle** for iterative data improvement.

*   **Parva**: Top-level super-section.
*   **Kandah**: Section level.
*   **Arsheyam**: The titular grouping (Subsection header), which can contain one or more Samams.
*   **Samam**: The actual mantra unit containing text with swara markings.
*   **Rik**: Individual verses associated with an Arsheyam/Samam (extracted and classified individually).

## 2. Architecture & Core Components

The system is modular, with distinct scripts handling data parsing, rendering, and export.

### 2.1 `src/generate_json.py`
**Role**: The central parser and "Source of Truth". It converts raw text files (with custom markup) into a structured JSON database.
*   **`RikMetadataParser` (Class)**: Responsible for parsing the auxiliary metadata file (`rishi_devata_chandas_for_rik.txt`). It handles complex logic for mapping Rishi/Devata/Chandas to Rik IDs, including range-based assignments `(1-10)` and specific overrides.
*   **`convert_corrections_to_json`**: The main driver function for the "Correction Mode". It reads the processed Unicode text file, extracts hierarchy (SuperSection > Section), and embeds metadata.
*   **Robust Parsing Logic**: The parser now uses a space-tolerant, multi-line regex system for markers (e.g., `# Start of SuperSection Title -- ID ## DO NOT EDIT`). It correctly handles markers regardless of whether there are zero, one, or many spaces before the `##` marker, making it robust against minor manual editing variations.
*   **`parse_unicode_text_file`**: Handles the reading of the main input file, ensuring encoding safety and stripping invisible characters.

### 2.2 `src/generate_website.py`
**Role**: Generates the static HTML website for GitHub Pages.
*   **`JSVParser` (Class)**: A robust parser that reads the JSON output and populates python objects (`Parva`, `Kandah`, `Arsheyam`). It abstracts the JSON structure into a workable Object Model.
*   **`WebsiteGenerator` (Class)**: Takes the `JSVParser` objects and orchestrates the HTML creation. It handles:
    *   Template rendering (Jinja2).
    *   Navigation generation (Left Sidebar).
    *   Audio filename mapping.
    *   Applying `SITE_CONFIG` settings based on the selected mode (`samhita` or `aranam`).
    *   **Enhanced Indices**: Generates advanced classification pages (Rishi, Devata, Chandas) with a 3-column "Top 20" prominent card section and a single-column, horizontal-flowing alphabetical index (**वर्णानुक्रमण**) designed for maximum density and readability. Includes aggregate unique Rik counting (currently ~587 Riks).
*   **`format_rik_text_html`**: Handles the specific HTML formatting for Rik text, including accent rendering (`<span>` classes) and footnote linking.

### 2.3 `src/render_pdf.py`
**Role**: Converts JSON data into high-quality LaTeX/HTML segments for the physical book.
*   **`CreatePdf`**: The main orchestration function. It loads the JSON and applies templates to generate `.tex` files for compilation.
*   **`process_footnotes_latex`**: A specialized processor that converts `(sN)` text markers into true LaTeX footnotes (`\footnote{...}`), resolving them against the metadata dictionary.
*   **`replace_accents`**: The core rendering engine for Vedic Accents. It maps ASCII markers `(1)` to zero-width, raised LaTeX glyphs (e.g., `\makebox[0pt]{\raisebox{...}}`).
*   **`TOC Configuration`**: Supports a configurable Table of Contents level (`section`, `subsection`, or `both`) for both PDF (using `\addcontentsline`) and HTML (using conditional template rendering).
*   **`remove_mantra_spaces`**: Implements the *scriptio continua* logic (removing space between words) while preserving formatting lines.

### 2.4 `src/generate_Rik_for_samhita.py`
**Role**: A specialized reporting tool that generates the "Rik Samhita" (Continuous Text) view.
*   **`generate_and_compile_latex`**: Generates a standalone PDF focused purely on Recitation Text, bypassing the complex layout of the main book.
*   **`step_preprocess_visarga_accent`**: A critical utility (shared logic) that handles the visual swapping of Visarga and Accents (`Wordः(1)` $\rightarrow$ `Word(1)ः`) to ensure correct rendering.

### 2.5 `src/generate_granular_table.py`
**Role**: The "Exporter" for the Correction Cycle.
*   **`parse_metadata_str`**: A smart parser that breaks down raw metadata strings (e.g., "Rishi... Devata... Chandas") into structured fields.
*   **`normalize_key`**: logic to clean up inconsistencies in Rishi/Devata names (whitespace, punctuation) to ensure better grouping in the CSV export.

### 2.6 `src/generate_rik_table.py`
**Role**: The "Bridge Builder" that integrates external classification (Rishi, Devata, Chandas) into the Samhita.
*   **Unique Rik Extraction**: Iterates through the hierarchical JSON and extracts unique Riks, splitting multi-verse Arsheyams into individual rows using positional markers (e.g., `॥ ९ ॥`).
*   **Classification Integration**: Loads mapping data from the **Reconciliation Excel** (`Rik Reconciliation table (JSV-KSV).xlsx`). It maps each unique verse to its <Rishi, Devata, Chandas> tuple using the `Global_Rik_Num`.
*   **Accent Normalization**: Converts ASCII markers (e.g., `(1)`) into literal Unicode Swaras (e.g., `U+0951`) for clean CSV representation.
*   **Structure Injection**: Dynamically injects a `rik_classifications` list into each Arsheyam (Subsection) in the JSON. This list identifies the Riks associated with that Arsheyam and their respective classifications.
*   **Output**:
    *   `JSV_Rik_Table.csv`: A flattened, deduplicated verse-level table.
    *   `Vargeekaran.json`: The **Enhanced Source of Truth** used by the website generator for classification-based navigation.

### 2.7 `src/generate_missing_metadata_report.py`
**Role**: Data quality validation tool that identifies missing metadata.
*   Checks for Riks without metadata or metadata without associated Rik text.
*   Checks for Samams without metadata.
*   Supports configurable modes (`rik`, `samam`, `combined`) via CLI arguments.
*   Output: `data/output/JSV_Missing_Metadata_Report.md` and `.csv`.

### 2.8 Collection Utilities (`src/curate_jsv.py`, `src/tools/build_collection.py`)
**Role**: Utilities to create curated selections (सूक्तमाला) from existing Samhita or Aaranam datasets.
*   **`curate_jsv.py`**: Merges data from multiple JSON sources based on a text filter containing Parva.Kandah.Samam (P.K.S) identifiers.
*   **`build_collection.py`**: Extracts specific Samams using P.K.S identifiers from a single source JSON and bundles them into a structured Collection format.

---

## 3. Workflows (Main Use Cases)

### 3.1 Workflow A: Core Data Pipeline (Initial & Corrections)

This workflow covers the full lifecycle of the Samhita data: from importing new Unicode text for the first time to iteratively refining it and its metadata.

#### Phase 1: Initial Import (New Text)

Use this mode when you have a fresh text file (containing `SuperSection` / `Section` markers) and want to generate the baseline JSON. This mode combines your main text with the auxiliary data files.

**Prerequisites**:
*   Main input text file (e.g., `data/input/Agneyam-Pavamanam_corrected.txt`)
*   Auxiliary files present in `data/input/`:
    *   `vedic_text.txt` (Rik text source)
    *   `rishi_devata_chandas_for_rik.txt` (Rik metadata)
    *   `sama_rishi_chandas_out.txt` (Samam metadata)

**Command**:
```bash
# 1. Generate JSON (Baseline)
python src/generate_json.py "data/input/Agneyam-Pavamanam_corrected.txt" --input-mode initial

# 2. Generate Master Correction File (Unicode Text)
python src/render_pdf.py data/output/Agneyam-Pavamanam_corrected_out.json
```
*Outputs*: 
*   **JSON**: `data/output/Agneyam-Pavamanam_corrected_out.json`
*   **Correction File**: `data/output/txt/Devanagari/Samhita_Devanagari_Unicode.txt`
*   **LaTeX Source**: `data/output/pdf/Devanagari/Samhita_Devanagari.tex`

> **Next Step**: Move the generated `..._Unicode.txt` file to your `data/input/` folder (e.g., rename to `Agneyam-Pavamanam_corrected.txt`) to use it as the source for Phase 2.

#### Phase 2: The Correction Cycle (Iterative Updates)

The generated Unicode text from Phase 1 is taken up for further corrections by Vedic scholars. This is the daily maintenance workflow. It allows one to fix Rik/Samam text errors or metadata (Rishi, Devata, Chandas) by editing the text file or Excel/csv files and then feed those changes back into the system.

**Prerequisite**: You have the updated Unicode Text File in `data/input/`.

**Steps:**

**Option A: Direct Correction (Text & Metadata) - *Primary Workflow***
1.  **Edit the Text File**:
    *   Open `data/input/Agneyam-Pavamanam_corrected.txt` (or your renamed correction file) in an editor of your choice.
    *   Fix mantra text errors, Rik headers, or metadata (lines starting with `(s1)...`).
    *   The text file should be in UTF-8 encoded text format.   
2.  **Regenerate JSON**:
    ```bash
    python src/generate_json.py "data/input/Agneyam-Pavamanam_corrected.txt" --input-mode correction
    ```

**Option B: Bulk Metadata Correction (Excel / CSV) - *Additional Workflow***
1.  **Generate Editable Table**:
    ```bash
    python src/generate_granular_table.py
    ```
    *Output*: `data/output/JSV_Samam_Granular_Table.xlsx` and `data/output/JSV_Samam_Granular_Table.csv`
2.  **Edit Table**: Update `Rik_Rishi`, `Samam_Devata`, etc. in the `.xlsx` or `.csv` file.
3.  **Regenerate JSON (with Metadata overlay)**:
    ```bash
    # Using Excel
    python src/generate_json.py "data/input/Agneyam-Pavamanam_corrected.txt" --input-mode correction --metadata-file "data/output/JSV_Samam_Granular_Table.xlsx"
    
    # Or using CSV
    python src/generate_json.py "data/input/Agneyam-Pavamanam_corrected.txt" --input-mode correction --metadata-file "data/output/JSV_Samam_Granular_Table.csv"
    ```

**Final Step (Common): Regenerate Artifacts**
Update the Website, PDF, HTML, and Text outputs to reflect the changes.

1. **Integrate Classifications** (Required for Website):
   This step maps the Riks to their Rishi, Devata, and Chandas from the Excel sheet and generates the `Vargeekaran.json`.
   ```bash
   python src/generate_rik_table.py data/output/Agneyam-Pavamanam_corrected_out.json
   ```

2. **Regenerate Site & Book**:
   ```bash
   # Website (uses the Vargeekaran JSON generated above)
   python src/generate_website.py --source-file data/output/Vargeekaran.json
   
   # PDF, HTML, and Unicode Text
   python src/render_pdf.py data/output/Agneyam-Pavamanam_corrected_out.json
   ```
*   *PDF Source*: `data/output/pdf/Devanagari/Samhita_Devanagari.tex`
*   *HTML Output*: `data/output/html/Devanagari/Samhita_Devanagari.html`
*   *Text Output*: `data/output/txt/Devanagari/Samhita_Devanagari_Unicode.txt`

### 3.2 Workflow B: Website Generation & Publishing

This workflow generates the static HTML site for `jaimineeyasamavedam.org`.

#### Site Architecture

The website uses a **common landing page** (`docs/index.html`) that links to two independent sub-sites:

```
docs/
├── index.html              ← Common landing page (gateway)
├── samhita/                ← Samhita sub-site
│   ├── index.html
│   ├── css/, js/, kandah/
│   ├── classification/
│   └── metadata.json
└── aranam/                 ← Aaranam (Aranya Ganam) sub-site
    ├── index.html
    ├── css/, js/, kandah/
    ├── classification/
    └── metadata.json
```

The landing page is a static HTML file maintained manually. Each sub-site is generated independently using `generate_website.py` with the appropriate mode flag.

#### Steps

1.  **Generate Samhita Website**:
    ```bash
    python src/generate_website.py --source-file data/output/Agneyam-Pavamanam_latest_out.json -o docs/samhita
    ```

2.  **Generate Aaranam Website**:
    ```bash
    python src/generate_website.py --source-file data/output/Aaranam_latest_out.json -o docs/aranam -a
    ```

3.  **Preview Locally**:
    ```bash
    python -m http.server 8080 --directory docs
    ```
    Visit `http://localhost:8080` — the landing page will link to both sub-sites.

4.  **Publish (Deploy)**:
    Commit and push the `docs/` folder to the `format-mantras` branch. GitHub Pages will automatically deploy it.
    ```bash
    git add docs/
    git commit -m "Update website content"
    git push origin format-mantras
    ```

### 3.3 Workflow C: PDF Book Generation

This workflow creates the high-quality PDF for the physical book.

1.  **Generate LaTeX Source**:
    ```bash
    # For Samhita (default bw)
    python src/render_pdf.py data/output/Agneyam-Pavamanam_latest_out.json --output-mode combined
    
    # For Aaranam (color printout)
    python src/render_pdf.py data/output/Aaranam_latest_out.json --output-mode combined --type aaranam --pdf-color-mode color
    ```
    *Output*: `data/output/pdf/Devanagari/Samhita_Devanagari.tex` or `data/output/pdf/Devanagari/Aaranam_Devanagari.tex` (and associated HTML/text files). 
    *Note*: Use `--pdf-color-mode color` to enable colored metadata and Swara marks, or let it default to `bw` (black/white) for book typesetting.

2.  **Compile PDF**:
    Use LuaLaTeX (required for HarfBuzz font rendering). Run from the project root.
    ```bash
    # For Samhita
    lualatex data/output/pdf/Devanagari/Samhita_Devanagari.tex
    
    # For Aaranam
    lualatex data/output/pdf/Devanagari/Aaranam_Devanagari.tex
    ```

### 3.4 Workflow D: Rik Samhita Generation

This extracts the "Rik" (verses) in a continuous format (*scriptio continua*) for recitation verification.

1.  **Generate**:
    ```bash
    # Generates both PDF and HTML
    python src/generate_Rik_for_samhita.py -i data/input/vedic_text.txt
    ```

### 3.5 Workflow E: Collection Generation (Sooktam / Sūkta Māla)

This workflow handles publishing a **curated collection** of samams from a Unicode Devanagari text input. Unlike the Samhita/Aaranam workflows, a collection is a standalone selection of mantras with its own sequential numbering.

#### Input Format

The input file (e.g., `data/input/Sooktam.txt`) uses the same markup conventions:
*   `# SuperSection Title` / `# End of SuperSection Title` — Top-level grouping
*   `# Section Title` / `# End of Section Title` — Khanda-level grouping (e.g., Sūktam names)
*   `# SubSection Title` / `# End of SubSection Title` — Samam headers (Atha/Iti)
*   `# Start of Mantra Sets` / `# End of Mantra Sets` — Mantra content
*   `# Closing Mantras` / `# End of Closing Mantras` — Optional closing prayers (centered in output)

#### Closing Mantras

A special section at the end of the input file enclosed in `# Closing Mantras` / `# End of Closing Mantras` markers. Each line becomes a centered mantra in the output:
*   **HTML**: Rendered in a `subsection`-styled card (beige background, blue left border) with centered text
*   **PDF**: Rendered contiguously on the last content page in bold centered text (no separate page)
*   **Text**: Preserved with round-trip markers for re-editing

#### Steps

1.  **Parse Input to JSON**:
    ```bash
    python src/generate_json.py data/input/Sooktam.txt --input-mode initial --output data/output/Sooktam_out.json
    ```

2.  **Generate Outputs** (HTML, LaTeX, Text):
    ```bash
    python src/render_pdf.py data/output/Sooktam_out.json --type collection --pdf-color-mode color
    ```

3.  **Compile PDF** (optional):
    ```bash
    lualatex data/output/pdf/Devanagari/Collection_Devanagari.tex
    ```

*Outputs*:
*   **HTML**: `data/output/html/Devanagari/Collection_Devanagari.html`
*   **LaTeX**: `data/output/pdf/Devanagari/Collection_Devanagari.tex`
*   **Text**: `data/output/txt/Devanagari/Collection_Devanagari_Unicode.txt`

#### Utility Scripts

*   **`src/tools/renumber_sooktam.py`**: A vital utility for managing IDs and sequential numbering in JSV files.
    *   **Robust Renumbering**: Sequentially updates all IDs (`supersection_N`, `section_N`, `subsection_N`) and mantra numbers (`॥N॥`) based on header anchors (`# Start of ... Title`).
    *   **Custom Offsets**: Supports starting numbers for SuperSection, Section, and Subsection via CLI arguments.
    *   **Samam Counting**: By default, Samam numbers reset to 1 at every *SuperSection* boundary. Use `--contiguous-samams` for fully global contiguous numbering.
    *   **Reset per SuperSection**: Optional flag to reset Section/Subsection counters at each SuperSection boundary.
    *   **Preserve Modes**: `preserve-super` only skips renumbering SuperSections, while `--preserve-all` preserves all section/supersection structure IDs and only renumbers the Samams within them.

---

## 4. CLI Reference

### `src/generate_json.py`
*Parses input text to JSON.*

```bash
python src/generate_json.py <input_file> [OPTIONS]
```
| Option | Description |
| :--- | :--- |
| `--input-mode` | `initial` (raw text) or `correction` (default). |
| `--metadata-file` | Path to `.xlsx`, `.csv`, or `.txt` file to enrich metadata. |
| `--output` | Custom output path (optional). |
| `--initial-json` | Path to a trusted initial JSON file (for re-mapping Rik IDs). |

### `src/render_pdf.py`
*Generates LaTeX (PDF), single-page HTML, and Unicode Text from JSON.*
Note: The HTML output automatically generates both a Table of Contents (Anukramanika) and an Alphabetical Index (Varnanukramanika).

```bash
python src/render_pdf.py [INPUT_JSON] [OPTIONS]
```
| Option | Description |
| :--- | :--- |
| `--output-mode` | `combined` (default), `separate` (split Rik/Samam), or `nometa`. |
| `--type` | Type of Samaveda text: `samhita` (default), `aaranam`, or `collection`. |
| `--pdf-font` | Custom font name for LaTeX (default: `AdishilaVedic`). |
| `--html-font` | Font family string for HTML output (default: `'AdishilaVedic', 'AdishilaSanVedic'`). |
| `--pdf-color-mode` | `color` (colored metadata/swara marks) or `bw` (default, black/white for book typesetting). |
| `--toc-level` | TOC hierarchy: `section` (default), `subsection`, or `both`. Controls both PDF and HTML TOC. |

> **Dynamic Title**: The document title on the PDF title page, HTML header, and text output is determined by `--type`:
> *   `samhita` → **जैमिनीय साम संहिता**
> *   `aaranam` → **जैमिनीय साम आरण्य गानम्**
> *   `collection` → **जैमिनीय साम सूक्त माला**
>
> The output file prefix also changes accordingly (`Samhita_`, `Aaranam_`, vs `Collection_`).

### `src/generate_website.py`
*Generates the static website. Each mode generates an independent sub-site; the common landing page (`docs/index.html`) is maintained manually.*

```bash
python src/generate_website.py [OPTIONS]
```
| Option | Description |
| :--- | :--- |
| `--source-file`, `-s` | Path to the input JSON file. |
| `--output-dir`, `-o` | Output directory (default: `docs`). Use `docs/samhita` or `docs/aranam` for the dual-site layout. |
| `--audio-dir`, `-d` | Directory for audio placeholder folders (default: `data/input/Audio_Placeholders`). |
| `--samhita`, `-m` | Generate for Samhita / Prakruti Ganam. This is the default and uses the `samhita` configuration key. |
| `--aranam`, `-a` | Generate for Aaranam / Aranya Ganam mode (uses `aranam` configuration key). |

### `src/generate_Rik_for_samhita.py`
*Generates continuous Rik text document.*

```bash
python src/generate_Rik_for_samhita.py [OPTIONS]
```
| Option | Description |
| :--- | :--- |
| `-i`, `--input` | Input text file. |
| `-f`, `--format` | Output format: `pdf`, `html`, or `all`. |

### `src/generate_granular_table.py`
*Generates a fine granular table listing every individual Samam with Rik mapping.*

```bash
python src/generate_granular_table.py [OPTIONS]
```
| Option | Description |
| :--- | :--- |
| `-i`, `--input` | Path to the input JSON file (default: `data\output\Samhita_with_Rishi_Devata_Chandas_out.json`). |
| `-o`, `--output` | Path to the output CSV file (default: `data\output\JSV_Samam_Granular_Table.csv`). |
*Output*: CSV and XLSX files with per-Samam rows including Global_Rik_Num, Patha, Khanda, metadata fields.

### `src/generate_rik_table.py`
*Generates the Rik-level CSV and the Vargeekaran JSON.*

```bash
python src/generate_rik_table.py [INPUT_JSON] [OPTIONS]
```
| Option | Description |
| :--- | :--- |
| `INPUT_JSON` | Path to the source JSON file (default: `data\output\Samhita_corrected_out.json`). |
| `-o`, `--output` | Path to the output CSV table (default: `data\output\JSV_Rik_Table.csv`). |
| `-e`, `--excel` | Path to the Reconciliation Excel (mapping Riks to R/D/C). (default: `data\output\Rik Reconciliation table (JSV-KSV).xlsx`) |
| `-j`, `--json_out` | Path to save the enriched/Vargeekaran JSON (default: `data\output\Vargeekaran.json`). |

*Output*: A UTF-8-sig CSV for metadata reconciliation and the **Vargeekaran JSON** required for the website's classification logic.

### `src/generate_missing_metadata_report.py`
*Generates a report of missing Rik and Samam metadata.*

```bash
python src/generate_missing_metadata_report.py [OPTIONS]
```
| Option | Description |
| :--- | :--- |
| `--mode` | `rik` (Rik issues only), `samam` (Samam issues only), or `combined` (default, both). |

### `src/curate_jsv.py`
*Curates a subset of JSV JSON (Samhita/Aaranam) by combining sources based on P.K.S filters.*

```bash
python src/curate_jsv.py --sources <file1> <file2> --filter <txt_file> --output <json_file>
```
| Option | Description |
| :--- | :--- |
| `--sources` | Source JSON files to look up identifiers from. |
| `--filter` | Filter text file containing P.K.S identifiers. |
| `--output` | Curated JSON output file. |
| `--title` | Collection title (default: जैमिनीय साम सूक्तमाला). |

### `src/tools/build_collection.py`
*Extracts Samams by P.K.S IDs from a JSON file and constructs a standalone Collection JSON.*

```bash
python src/tools/build_collection.py [OPTIONS]
```
| Option | Description |
| :--- | :--- |
| `--ids` | List of IDs (e.g., 1.1.1 1.1.2). |
| `--file` | Plain text file containing IDs to extract. |
| `--source` | Source JSON file (default: `data/output/Vargeekaran.json`). |
| `--output` | Output JSON file (default: `data/output/Collection_latest_out.json`). |
| `--title` | Title for the collection (default: जैमिनीय साम सूक्तमाला). |

### `src/tools/renumber_sooktam.py`
*Renumbers IDs and Samam markers in TXT or JSON files with custom offsets.*

```bash
# Renumber a text file (in-place) with custom offsets
python src/tools/renumber_sooktam.py data/input/Aaranam_latest.txt --start-super 7 --start-section 65 --start-subsection 728

# Renumber a JSON file (outputs to a new file)
python src/tools/renumber_sooktam.py data/output/Sooktam_out.json --preserve-super
```
| Option | Description |
| :--- | :--- |
| `input_file` | Path to the `.txt` or `.json` file to renumber. |
| `--preserve-super` | If set, preserves existing SuperSection IDs. |
| `--preserve-all` | If set, preserves all SuperSection, Section, and SubSection IDs (only resets Samam numbering). |
| `--start-super` | Starting number for SuperSections (default: 1). |
| `--start-section` | Starting number for Sections (default: 1). |
| `--start-subsection` | Starting number for SubSections (default: 1). |
| `--reset-per-super` | Reset section and subsection counters at each SuperSection boundary. |
| `--contiguous-samams` | Do NOT reset Samam numbering at SuperSection boundaries (contiguous throughout file). |

---

### `src/tools/copy_rik_ids.py`
*Utility to safely duplicate a Rik and its metadata within the source JSON based on a specific position.*

```bash
python src/tools/copy_rik_ids.py [OPTIONS]
```
| Option | Description |
| :--- | :--- |
| `input_json` | JSON file containing the source Rik data. |
| `--source-id` | Original `rik_id` identifying the block to duplicate. |
| `--target-subsection` | Destination subsection where the duplicate should be added. |
| `--position` | Index pos (0-based) to insert the copied block within the subsection. |

---

## 5. Technical Reference

### Data Normalization
*   **Danda Standardization**: All pipe variations (`||`, `| |`, `॥`) are normalized to standard Devanagari Dandas (`॥`, `।`). Specifically, double pipes (`||`) are explicitly replaced with double dandas (`॥`) in the input source for uniformity.
*   **Section Markers**: The `RikTextParser` supports both `खण्डः` (Khanda) and `पर्वा` (Parva) markers as section boundaries, ensuring accurate extraction across different Samaveda portions.
*   **Continuous Text**: `remove_mantra_spaces()` creates continuous text for Samhita views, preserving structure lines (Colophons).

### Visual Rendering Logic
*   **Visarga-Accent Swap**: A critical rendering fix (`step_preprocess_visarga_accent` in `src/utils.py`) handles the Vedic convention where an accent marked *after* a Visarga (`ः`) must visually appear on the preceding vowel.
    *   *Logic*: Swaps `Wordः(1)` $\rightarrow$ `Word(1)ः` just before rendering.
    *   *Applied In*: PDF, Website, and Rik Samhita generators.
*   **Accent Collision**: `handle_consecutive_accents()` allows fine-tuning (kerning) when two accents might overlap visually (e.g. Swarita + Anudatta).
*   **Sankhya Table Logic**: The summary table ("Sankhya") correctly counts unique Rik IDs by processing the `rik_ids` list in each subsection, ensuring that subsections containing multiple grouped Riks are counted accurately.
*   **Font Path Configuration**: To support flexible compilation environments, absolute font paths are calculated in Python and passed to LaTeX templates, allowing `fontspec` to locate project-local fonts.

### 5.3 Footnote Syntax
Footnotes in the source text must follow the `(sN)` pattern **immediately following** the swara, with no space.
*   **Correct**: `इ(श)(s1)`
*   **Incorrect**: `इ(श) (s1)` (Space creates detachment)

### 5.4 Sidebar "Jump to" Logic
The website includes a "Jump to" input field in the sidebar that allows users to navigate directly to a specific Parva, Kandah, or Sama.
*   **Input Formats**:
    *   `P.K` — Navigates to Parva `P`, Kandah `K`.
    *   `P.K.S` — Navigates to Parva `P`, Kandah `K`, and scrolls to Sama `S`.
*   **Implementation**: This is handled by a client-side JavaScript function `handleJump()` in `js/main.js`. It dynamically calculates the relative path prefix (`../`) based on the current page's depth (e.g., if the user is in a Kandah page, it uses `../../` to reach the root before navigating to the target).
*   **Dynamic Path Resolution**: The logic checks `window.location.pathname` to determine the depth, ensuring correctly resolved links from both the homepage, classification indices, and specific content pages.

### 5.4 Rik Identification & Global Mapping (Vargeekaran.json)
The `src/generate_rik_table.py` script generates the `Vargeekaran.json`, which acts as the **Enriched Source of Truth** for the website.
*   **Sequential verse numbering**: It maintains a global counter as it traverses the Samhita hierarchy. This counter matches the row index in the Reconciliation Excel and becomes the `Global_Rik_Num` used for classification lookups.
*   **Verse Extraction**: The parser looks for Devanagari verse numbers (e.g., `॥ ७ ॥`) within Arsheyam text blocks. It converts these Devanagari digits to standard integers to determine the relative `Rik_ID`.
*   **Classification Injection**: Instead of modifying the core JSON schema, it adds a `rik_classifications` list to each Arsheyam (Subsection).
    *   **Structure**: Each entry in `rik_classifications` contains: `Global_Rik_Num`, `Rishi`, `Devata`, and `Chandas`.
    *   **Purpose**: This allows the `JSVParser` and `WebsiteGenerator` to group Samams by their associated Riks and display accurate metadata on the individual classification pages.
*   **Sorting**: All data is processed using a strict numerical sort on SuperSection and Section keys to ensure the global counter remains stable across runs.

### 5.5 Typography System
The website's visual hierarchy is driven by a two-font system designed to balance traditional aesthetics with modern readability.
*   **Adishila Vedic (Serif)**: Used for all traditional Sanskrit content, mantra text, and metadata labels.
*   **Adishila San Vedic (Sans-serif)**: Used for numerals, counts, and interactive navigation elements.

Detailed mapping of CSS classes to font families and fine-tuning instructions can be found in the **[Typography Guide](docs/typography_guide.md)**. Changes to the typography are made in the CSS fragments within `src/generate_website.py`.

---

## 6. Modifying Website Styles (CSS)

The website styles are not stored in a separate `.css` file but are dynamically generated by the `WebsiteGenerator._generate_css` method in `src/generate_website.py`.

### 6.1 Indirection Layers
To maintain a consistent theme, colors follow a three-layered indirection system:

1.  **Core Palette (Hex Codes)**: Defined at the top of `:root` (e.g., `--color-accent: #FF6B35`).
2.  **Theme Mapping (Semantic Names)**: Core variables are mapped to functional names (e.g., `--primary-maroon: var(--color-accent)`).
3.  **Component Styles (Classes)**: Individual CSS rules use these semantic variables.

### 6.2 Example: Changing "Indices" Header to Blue
If you want to change the color of the "Indices" section title on the Home page (which uses the `.anya-vargeekaran-card h2` selector):

**Step 1: Locate the Rule**
Open `src/generate_website.py` and search for `.anya-vargeekaran-card h2`. You will find:
```css
.anya-vargeekaran-card h2 {
    color: var(--color-secondary);
    ...
}
```

**Step 2: Decide the Scope of Change**
*   **To change only this specific header**: Edit line 1981 directly:
    `color: #0000FF; /* Blue */`
*   **To change all secondary text (Global)**: Locate line 839 in the `:root` section:
    `--color-secondary: #0000FF;`

**Step 3: Update the Source**
Modify the string inside the `_generate_css` method in `src/generate_website.py`.

**Step 4: Regenerate**
Run the generator to see the changes:
```bash
python src/generate_website.py --source-file data/output/Vargeekaran.json -o docs
```
Usage of `!important` should be minimized and reserved for situations where global hierarchy rules (like the numeral group) conflict with specific component needs.
