# Jaimineeya Samavedam Digitalization Project - Developer Guide

This guide provides a comprehensive overview of the Jaimineeya Samavedam digitalization project, focusing on the workflows for data correction, website generation, and PDF document creation.

## 1. Project Overview

The goal of this project is to digitize the Jaimineeya Samavedam Samhita, providing:
1.  A **Modern Website** for easy browsing and listening.
2.  **Print-ready PDF** documents (LaTeX-based) for physical publication.
3.  **Specialized Views** like the *Rik* or *Samam* of Samhita for traditional chanting verification.

The system is built on a custom text-to-JSON parsing engine that handles the specific structural requirements of the Samaveda (Parva > Kandah > Sama) and supports a robust **Correction Cycle** for iterative data improvement.

## 2. Architecture & Core Components

The system is modular, with distinct scripts handling data parsing, rendering, and export.

### 2.1 `src/generate_json.py`
**Role**: The central parser and "Source of Truth". It converts raw text files (with custom markup) into a structured JSON database.
*   **`RikMetadataParser` (Class)**: Responsible for parsing the auxiliary metadata file (`rishi_devata_chandas_for_rik.txt`). It handles complex logic for mapping Rishi/Devata/Chandas to Rik IDs, including range-based assignments `(1-10)` and specific overrides.
*   **`convert_corrections_to_json`**: The main driver function for the "Correction Mode". It reads the processed Unicode text file, extracts hierarchy (SuperSection > Section), and embeds metadata.
*   **`parse_unicode_text_file`**: Handles the reading of the main input file, ensuring encoding safety and stripping invisible characters.

### 2.2 `src/generate_website.py`
**Role**: Generates the static HTML website for GitHub Pages.
*   **`JSVParser` (Class)**: A robust parser that reads the JSON output and hydrates python objects (`Parva`, `Kandah`, `Sama`). It abstracts the JSON structure into a workable Object Model.
*   **`WebsiteGenerator` (Class)**: Takes the `JSVParser` objects and orchestrates the HTML creation. It handles:
    *   Template rendering (Jinja2).
    *   Navigation generation (Left Sidebar).
    *   Audio filename mapping.
*   **`format_rik_text_html`**: Handles the specific HTML formatting for Rik text, including accent rendering (`<span>` classes) and footnote linking.

### 2.3 `src/render_pdf.py`
**Role**: Converts JSON data into high-quality LaTeX/HTML segments for the physical book.
*   **`CreatePdf`**: The main orchestration function. It loads the JSON and applies templates to generate `.tex` files for compilation.
*   **`process_footnotes_latex`**: A specialized processor that converts `(sN)` text markers into true LaTeX footnotes (`\footnote{...}`), resolving them against the metadata dictionary.
*   **`replace_accents`**: The core rendering engine for Vedic Accents. It maps ASCII markers `(1)` to zero-width, raised LaTeX glyphs (e.g., `\makebox[0pt]{\raisebox{...}}`).
*   **`remove_mantra_spaces`**: Implements the *scriptio continua* logic (removing space between words) while preserving formatting lines.

### 2.4 `src/generate_Rik_for_samhita.py`
**Role**: A specialized reporting tool that generates the "Rik Samhita" (Continuous Text) view.
*   **`generate_and_compile_latex`**: Generates a standalone PDF focused purely on Recitation Text, bypassing the complex layout of the main book.
*   **`step_preprocess_visarga_accent`**: A critical utility (shared logic) that handles the visual swapping of Visarga and Accents (`Wordः(1)` $\rightarrow$ `Word(1)ः`) to ensure correct rendering.

### 2.5 `src/generate_granular_table.py`
**Role**: The "Exporter" for the Correction Cycle.
*   **`parse_metadata_str`**: A smart parser that breaks down raw metadata strings (e.g., "Rishi... Devata... Chandas") into structured fields.
*   **`normalize_key`**: logic to clean up inconsistencies in Rishi/Devata names (whitespace, punctuation) to ensure better grouping in the CSV export.

---

## 3. Workflows (Main Use Cases)

### 3.1 Workflow A: Core Data Pipeline (Initial & Corrections)

This workflow covers the full lifecycle of the Samhita data: from importing new Unicode text for the first time to iteratively refining it and its metadata.

#### Phase 1: Initial Import (New Text)

Use this mode when you have a fresh text file (containing `SuperSection` / `Section` markers) and want to generate the baseline JSON. This mode combines your main text with the auxiliary data files.

**Prerequisites**:
*   Main input text file (e.g., `data/input/Agneyam_New.txt`)
*   Auxiliary files present in `data/input/`:
    *   `vedic_text.txt` (Rik text source)
    *   `rishi_devata_chandas_for_rik.txt` (Rik metadata)
    *   `sama_rishi_chandas_out.txt` (Samam metadata)

**Command**:
```bash
# 1. Generate JSON (Baseline)
python src/generate_json.py "data/input/Agneyam_New.txt" --input-mode initial

# 2. Generate Master Correction File (Unicode Text)
python src/render_pdf.py data/output/Agneyam_New_out.json
```
*Outputs*: 
*   **JSON**: `data/output/Agneyam_New_out.json`
*   **Correction File**: `data/output/txt/Devanagari/Samhita_Devanagari_Unicode.txt`
*   **LaTeX Source**: `data/output/pdf/Devanagari/Samhita_Devanagari.tex`

> **Next Step**: Move the generated `..._Unicode.txt` file to your `data/input/` folder (e.g., rename to `Agneyam_New.txt`) to use it as the source for Phase 2.

#### Phase 2: The Correction Cycle (Iterative Updates)

This is the daily maintenance workflow. It allows you to fix metadata (Rishi, Devata, Chandas) or text errors using Excel, CSV, or by editing the text file, and then feed those changes back into the system.

**Prerequisite**: You have the Unicode Text File generated in Phase 1 (and moved to `data/input/`).

**Steps:**

**Option A: Direct Correction (Text & Metadata) - *Primary Workflow***
1.  **Edit the Text File**:
    *   Open `data/input/Agneyam_New.txt` (or your renamed correction file) in VS Code.
    *   Fix mantra text errors, Rik headers, or metadata (lines starting with `(s1)...`).
2.  **Regenerate JSON**:
    ```bash
    python src/generate_json.py "data/input/Agneyam_New.txt" --input-mode correction
    ```

**Option B: Bulk Metadata Correction (Excel) - *Additional Workflow***
1.  **Generate Editable Table**:
    ```bash
    python src/generate_granular_table.py
    ```
    *Output*: `data/output/JSV_Samam_Granular_Table.xlsx`
2.  **Edit Excel**: Update `Rik_Rishi`, `Samam_Devata`, etc. in the `.xlsx` file.
3.  **Regenerate JSON (with Metadata overlay)**:
    ```bash
    python src/generate_json.py "data/input/Agneyam_New.txt" \
        --input-mode correction \
        --metadata-file "data/output/JSV_Samam_Granular_Table.xlsx"
    ```

**Final Step (Common): Regenerate Artifacts**
Update the Website, PDF, HTML, and Text outputs to reflect the changes.
```bash
# Website
python src/generate_website.py --source-file data/output/Agneyam_New_out.json

# PDF, HTML, and Unicode Text
python src/render_pdf.py data/output/Agneyam_New_out.json
```
*   *PDF Source*: `data/output/pdf/Devanagari/Samhita_Devanagari.tex`
*   *HTML Output*: `data/output/html/Devanagari/Samhita_Devanagari.html`
*   *Text Output*: `data/output/txt/Devanagari/Samhita_Devanagari_Unicode.txt`

### 3.2 Workflow B: Website Generation & Publishing

This workflow generates the static HTML site for `jaimineeyasamavedam.org`.

1.  **Generate Website**:
    ```bash
    python src/generate_website.py --source-file <path_to_json>
    ```
    *Output*: `docs/` folder.

2.  **Preview Locally**:
    ```bash
    python -m http.server 8080 --directory docs
    ```
    Visit `http://localhost:8080` to verify changes.

3.  **Publish (Deploy)**:
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
    python src/render_pdf.py <path_to_json> --output-mode combined
    ```
    *Output*: `data/output/html/Devanagari/Samhita_Devanagari.tex` (and associated files).

2.  **Compile PDF**:
    Use LuaLaTeX (required for HarfBuzz font rendering).
    ```bash
    lualatex data/output/html/Devanagari/Samhita_Devanagari.tex
    ```

### 3.4 Workflow D: Rik Samhita Generation

This extracts the "Rik" (verses) in a continuous format (*scriptio continua*) for recitation verification.

1.  **Generate**:
    ```bash
    # Generates both PDF and HTML
    python src/generate_Rik_for_samhita.py -i data/input/vedic_text.txt
    ```

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

### `src/render_pdf.py`
*Generates PDF, HTML, and Unicode Text from JSON.*

```bash
python src/render_pdf.py [INPUT_JSON] [OPTIONS]
```
| Option | Description |
| :--- | :--- |
| `--output-mode` | `combined` (default), `separate` (split Rik/Samam), or `nometa`. |
| `--pdf-font` | Custom font name for LaTeX. |

### `src/generate_website.py`
*Generates the static website.*

```bash
python src/generate_website.py [OPTIONS]
```
| Option | Description |
| :--- | :--- |
| `--source-file` | Path to the input JSON file. |
| `--output-dir` | Output directory (default: `docs`). |

### `src/generate_Rik_for_samhita.py`
*Generates continuous Rik text document.*

```bash
python src/generate_Rik_for_samhita.py [OPTIONS]
```
| Option | Description |
| :--- | :--- |
| `-i`, `--input` | Input text file. |
| `-f`, `--format` | Output format: `pdf`, `html`, or `all`. |

---

## 5. Technical Reference

### Data Normalization
*   **Danda Standardization**: All pipe variations (`||`, `| |`, `||`) are normalized to standard Devanagari Dandas (`॥`, `।`).
*   **Continuous Text**: `remove_mantra_spaces()` creates continuous text for Samhita views, preserving structure lines (Colophons).

### Visual Rendering Logic
*   **Visarga-Accent Swap**: A critical rendering fix (`step_preprocess_visarga_accent` in `src/utils.py`) handles the Vedic convention where an accent marked *after* a Visarga (`ः`) must visually appear on the preceding vowel.
    *   *Logic*: Swaps `Wordः(1)` $\rightarrow$ `Word(1)ः` just before rendering.
    *   *Applied In*: PDF, Website, and Rik Samhita generators.
*   **Accent Collision**: `handle_consecutive_accents()` allows fine-tuning (kerning) when two accents might overlap visually (e.g. Swarita + Anudatta).
*   **Font Path Configuration**: To support flexible compilation environments, absolute font paths are calculated in Python and passed to LaTeX templates, allowing `fontspec` to locate project-local fonts.

### Footnote Syntax
Footnotes in the source text must follow the `(sN)` pattern **immediately following** the swara, with no space.
*   **Correct**: `इ(श)(s1)`
*   **Incorrect**: `इ(श) (s1)` (Space creates detachment)
