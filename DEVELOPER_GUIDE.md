# Jaimineeya Samavedam Website Generator - Developer Guide

This project generates a static website for the Jaimineeya Samavedam, parsing a custom text format and producing a structure similar to the Rig Veda website.

## Core Components

### 1. `src/generate_website.py`
This is the main script. It contains two primary classes:

*   **`JSVParser`**: Responsible for parsing the input text file (`data/input/Samhita_...txt`). It builds a hierarchical object model of Parvas (Chapters), Kandahs (Sections), and Samas (Verses).
*   **`WebsiteGenerator`**: Takes the parsed objects and generates the HTML structure.

### 2. Output Structure (`docs/`)
The script generates the website into the `docs/` folder (configured for GitHub Pages).
*   `index.html`: The homepage with statistics and navigation.
*   `kandah/{parva_id}/{kandah_num}.html`: Individual pages for each section.
*   `css/`: Stylesheets.
*   `js/`: JavaScript files.

## Recent Features & Changes

### Layout & Navigation
*   **Layout**: The website uses a **two-column layout** (Left Sidebar + Main Content). The Right Sidebar (Jump Links) has been removed.
*   **Navigation**: All navigation is handled in the **Left Sidebar**.
    *   It lists Parvas (1-6).
    *   When a Parva is selected, it lists its Kandahs.
    *   Inside a Kandah page, it lists **Sama Ranges** (e.g., 1-5, 6-10) for quick scrolling.
*   **Samam Counting**: The script now counts verses by parsing delimiters (`||` or `॥`) inside the text, rather than just counting headers. This ensures the "Sama Count" reflects the actual chanted verses.
*   **Unified Counting Logic**: A new shared module `src/samam_utils.py` provides central logic for finding and counting Samams, ensuring consistency across all scripts (`generate_website.py`, `generate_granular_table.py`, etc.).

### Index Generation
Code is included and **enabled** to generate classification indices for **Rishi**, **Devata**, and **Chandas**, as well as an alphabetical **Header Index**.

**Status**: *Active*. Indices are generated during the build process.

**Code Location**:
*   `_generate_indices()`: Method to orchestrate index creation.
*   `_collect_indices()`: Method to parse metadata strings.
*   `_generate_classification_home()`: Creates `classification/index.html`.

**Access**:
Links to the indices are available on the Homepage under "सङ्क्रमणिका / वर्गीकरणम्".

## Correction Cycle Workflow (v4.0 - Excel Enhanced)

This project supports two correction workflows for managing metadata. Both use the JSON as the single source of truth.

### Option A: Excel-Based Workflow (Recommended)

This workflow allows editing metadata directly in Excel and applying changes back to JSON.

#### Step 1: Generate Excel from JSON
```bash
python src/generate_granular_table.py
```
*Output: `data/output/JSV_Samam_Granular_Table.xlsx`*

#### Step 2: Edit Metadata in Excel
Open the Excel file and edit these columns:
- **Individual Fields**: `Rik_Rishi`, `Rik_Devata`, `Rik_Chandas`, `Samam_Rishi`, `Samam_Devata`, `Samam_Chandas`
- **Full Metadata Strings**: `Rik_Metadata`, `Saman_Metadata`

Save and close the file when done.

#### Step 3: Preview Changes (Dry Run)
```bash
python src/apply_excel_corrections.py --dry-run
```
*Review the changes that would be applied.*

#### Step 4: Apply Corrections to JSON
```bash
python src/apply_excel_corrections.py
```
*Creates automatic backup before modifying JSON.*

#### Step 5: Regenerate All Outputs
```bash
# Regenerate PDF/HTML/Text
python src/render_pdf.py

# Regenerate Website
python src/generate_website.py --source-file data/output/Samhita_with_Rishi_Devata_Chandas_out.json
```

---

### Option B: CSV-Based Workflow (Legacy)

This workflow uses CSV files passed to `generate_json.py` for metadata enrichment.

#### Step 1: Generate Metadata CSV (Baseline)
```bash
python src/generate_granular_table.py
```
*Output: `data/output/JSV_Samam_Granular_Table.csv`*

#### Step 2: Edit Metadata (CSV)
Copy the CSV to your input folder and edit in a spreadsheet editor (must support UTF-8).

#### Step 3: Edit Text (Txt)
Edit the mantra text in the Unicode Text File as needed.

#### Step 4: Generate JSON (Fusion)
```bash
python src/generate_json.py "data/input/Samhita_with_Rishi_Devata_Chandas.txt" \
    --input-mode correction \
    --metadata-csv "data/input/granular_table.csv"
```

#### Step 5: Regenerate Artifacts
```bash
python src/generate_website.py --source-file data/output/Samhita_with_Rishi_Devata_Chandas_out.json
python src/render_pdf.py
```

## Deployment & Publishing

### How it Works
The website is hosted using **GitHub Pages**, configured to serve static content from the `docs/` folder on the `format-mantras` branch. 
Any file committed and pushed to `docs/` becomes immediately available on the live site.

### Publishing Steps
To publish the latest generated website:

1.  **Generate Fresh Artifacts**:
    Ensure you have run `src/generate_website.py` so the `docs/` folder contains the latest HTML.

2.  **Commit Changes**:
    Stage the changes in `docs/` (and other source files).
    ```bash
    git add .
    git commit -m "Update website content [v3.0]"
    ```

3.  **Push to GitHub**:
    ```bash
    git push origin format-mantras
    ```

4.  **Verification**:
    *   Wait 1-2 minutes for GitHub to deploy.
    *   Visit the live site to verify changes.



## PDF Generation (Vedic Compilation)

### 1. `src/render_pdf.py`
This script converts the fused JSON output (`data/output/Samhita_with_Rishi_Devata_Chandas_out.json`) into HTML segment files suitable for LaTeX processing. It splits the output by language script (Devanagari, Grantham, etc.) if configured.

### Usage
Run the script passing the JSON file path:
```bash
python src/render_pdf.py data/output/Samhita_with_Rishi_Devata_Chandas_out.json
```

### Output
*   Generates HTML/LaTeX friendly text segments in `data/output/html/Devanagari/`.
*   These files are used as source material for typesetting the physical book/PDF using LaTeX.

## Samhita Generation (Rik Text)

### 1. `src/generate_Rik_for_samhita.py`

This script is a specialized generator for creating the **Rik Samhita** document, which presents the text in `scriptio continua` (continuous text without spaces between words), primarily for traditional recitation verification.

### Key Logic Pipeline

1.  **Text Normalization (Scriptio Continua)**:
    *   The `remove_mantra_spaces()` function strips spaces within mantra lines to create continuous text.
    *   **Crucially**, it preserves spaces in "structure lines" (Headers, Colophons) identified by keywords like `अथ`, `इति`, `समाप्तः`.

2.  **Accent Handling**:
    *   **Replacement**: Converts ASCII markers `(1)`, `(2)`, `(3)` into proper Swara markers.
        *   **LaTeX**: Uses custom `\accentmark{}` commands.
        *   **HTML**: Uses `<span class="accent-...">` with Unicode entities.
    *   **Collision Avoidance**: The `handle_consecutive_accents()` function detects problematic sequences (e.g., Anudatta followed by Anudatta) and inserts small kerns `\kern0.15em` to prevent visual overlap.

3.  **Layout & Formatting**:
    *   **Gluing Numerals**: Mantra numbers (e.g., `|| 1 ||`) are "glued" to the preceding text using a non-breaking space (tilde `~` in LaTeX) to prevent them from being orphaned on a new line.
    *   **Header Protection**: Headers and their associated section numbers are wrapped in `\mbox{...}` to enforce that they stay on a single line.
    *   **Line Breaks**: Explicit line breaks (`\\`) are inserted after headers and mantra blocks to force the desired flow.

4.  **Output Generation**:
    *   **PDF**: Uses **LuaLaTeX** for high-quality font rendering (HarfBuzz). It generates a `.tex` file and compiles it.
    *   **HTML**: Generates a self-contained HTML file with embedded CSS for accent positioning, useful for quick previews without LaTeX.

## Running the Generator

```bash
python src/generate_website.py
```

## Running a Local Server

```bash
python -m http.server 8080 --directory docs
```
Then visit: http://localhost:8080

## CLI Usage Reference

### 1. `generate_json.py`

This script converts raw text input into a structured JSON file used for rendering.

**Location:** `src/generate_json.py`

#### Usage

```bash
python src/generate_json.py <input_file> [OPTIONS]
```

#### Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `input_file` | Input text file to process (positional, required). | - |
| `--input-mode` | Processing mode: `initial` or `correction`. | `correction` |
| `--output` | Path for the generated JSON output file. | Auto-generated: `data/output/<input_basename>_out.json` |
| `--metadata-csv` | CSV file to enrich metadata (correction mode only). | None |
| `--initial-json` | Trusted Initial JSON output to map Rik IDs correctly (correction mode only). | None |

#### Modes

*   **Initial Mode (`--input-mode initial`)**:
    *   Reads from the input file (expects text with structural markers).
    *   Also reads auxiliary metadata files:
        *   `data/input/rishi_devata_chandas_for_rik.txt` - Rik metadata (Rishi, Devata, Chandas)
        *   `data/input/sama_rishi_chandas_out.txt` - Samam metadata
        *   `data/input/vedic_text.txt` - Rik text content
    *   Used for the first pass of processing from raw input.
    *   Input file must contain structural markers (SuperSection, Section, SubSection, Mantra Sets).

*   **Correction Mode (`--input-mode correction`)** *(default)*:
    *   Reads from the input file (expects processed Unicode text with embedded metadata).
    *   **Does NOT** read auxiliary files. It expects all metadata to be present in the input file itself.
    *   Used for subsequent passes after manual edits.
    *   Optionally enriches with metadata from CSV file using `--metadata-csv`.

#### Examples

**Run in Correction Mode (default):**
```bash
python src/generate_json.py data\input\Samhita_with_Rishi_Devata_Chandas.txt
```

**Run in Initial Mode:**
```bash
python src/generate_json.py data\input\Samhita_with_Rishi_Devata_Chandas.txt --input-mode initial
```

**Run in Correction Mode with CSV Metadata Enrichment:**
```bash
python src/generate_json.py data\input\Samhita_with_Rishi_Devata_Chandas.txt --metadata-csv data/output/JSV_Samam_Granular_Table.csv
```

---

### 2. `render_pdf.py`

This script takes the JSON output from the previous step and generates PDF, HTML, and Text files.

**Location:** `src/render_pdf.py`

#### Usage

```bash
python src/render_pdf.py [INPUT_FILE] [OPTIONS]
```

#### Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `input_file` | The input JSON file path (Positional). | `data/output/Samhita_with_Rishi_Devata_Chandas_out.json` |
| `--output-mode` | Output style: `combined`, `separate`, or `nometa`. | `combined` |
| `--pdf-font` | Font name to use for PDF generation. | `AdiShila Vedic` |
| `--html-font` | Font family string for HTML output. | `'AdiShila Vedic', 'Adishila SanVedic'` |

#### Output Modes

| Mode | Description | Generated Files |
| :--- | :--- | :--- |
| `combined` | Single output with both Rik and Samam content together (default). | `Devanagari_Devanagari_Unicode.*` |
| `separate` | Two separate outputs: Rik-only and Samam-only files **with metadata** (rik_metadata, saman_metadata included). | `Rik_Devanagari_Unicode.*`, `Samam_Devanagari_Unicode.*` |
| `nometa` | Two separate outputs: Rik-only and Samam-only files **without metadata** (cleaner output, text only). | `Rik_NoMeta_Devanagari_Unicode.*`, `Samam_NoMeta_Devanagari_Unicode.*` |

#### Examples

**Generate Combined Output (Standard):**
```bash
python src/render_pdf.py
```

**Generate Separate Rik and Samam Files (with metadata):**
```bash
python src/render_pdf.py data/output/Samhita_with_Rishi_Devata_Chandas_out.json --output-mode separate
```

**Generate Separate Rik and Samam Files (without metadata):**
```bash
python src/render_pdf.py data/output/Samhita_with_Rishi_Devata_Chandas_out.json --output-mode nometa
```

#### Output Locations

Files are generated in the following directories:
- **PDF/LaTeX**: `data/output/pdf/Devanagari/`
- **Text**: `data/output/txt/Devanagari/`
- **HTML**: `data/output/html/Devanagari/`

---

### 3. Footnote Formatting Guide

This section describes how to correctly format footnotes in the source text file.

#### Footnote Syntax

Footnotes use the format `(sN)` where N is a number (e.g., `(s1)`, `(s2)`, `(s3)`).

#### Placement Rules

> [!IMPORTANT]
> **Footnote markers must be placed immediately after the swara** with NO space.

**Correct:**
```
इ(श)(s1)     ← footnote attaches to इ (correct)
वा(चा)(s2)   ← footnote attaches to वा (correct)
```

**Incorrect:**
```
इ(श) (s1)    ← space before footnote - may attach to wrong character
इ (s1)(श)    ← footnote before swara - incorrect placement
```

#### Pattern

The general pattern for a mantra character with swara and footnote is:
```
Word(Swara)(sN)
```

Where:
- `Word` = The Devanagari character/syllable
- `(Swara)` = The swara marking in parentheses
- `(sN)` = The footnote marker (no space before it)

#### Footnote Definitions

Footnotes are defined in a separate block in the source file:
```
# Start of Footnote -- subsection_1 ## DO NOT EDIT
s1: Kerala Padhati explanation here
s2: Thogur Padhati explanation here
# End of Footnote -- subsection_1 ## DO NOT EDIT
```
