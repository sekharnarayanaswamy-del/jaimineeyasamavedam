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

## Recent Features & Changes (Feb 2026)

### Data Normalization & Formatting
*   **Danda Standardization**: The codebase now enforces strict normalization of Danda characters. All variations of pipes (`||`, `| |`, `।।`) in the input text are automatically converted to standard Devanagari Dandas (`॥` and `।`) during parsing. This ensures consistent regex matching for verse numbers and structural breaks across both PDF and Website generation.
    *   *Affected Files*: `src/utils.py`, `src/generate_website.py`, `src/render_pdf.py`
    *   *Visuals*: Headers and TOC entries in the PDF now correctly use `\enspace` sized spacing for single dandas (`\enspace । `).

### Website Generator Improvements
*   **Module Structure**: Fixed import issues where `samam_utils` was not being correctly resolved from the `src/tools` directory. The script now dynamically adjusts `sys.path`.
*   **Stability**: resolved scope issues (UnboundLocalError) related to the `re` module in the Kandah page generation logic.
*   **Audio Handling**: Audio placeholder generation is now robust, creating directories for each Parva.

### Layout & Navigation
*   **Layout**: The website uses a **two-column layout** (Left Sidebar + Main Content). The Right Sidebar (Jump Links) has been removed.
*   **Navigation**: All navigation is handled in the **Left Sidebar**.
    *   It lists Parvas (1-6).
    *   When a Parva is selected, it lists its Kandahs.
    *   Inside a Kandah page, it lists **Sama Ranges** (e.g., 1-5, 6-10) for quick scrolling.
*   **Samam Counting**: The script now counts verses by parsing delimiters (`||` or `॥`) inside the text, rather than just counting headers. This ensures the "Sama Count" reflects the actual chanted verses.
*   **Unified Counting Logic**: A new shared module `src/tools/samam_utils.py` provides central logic for finding and counting Samams.

### Index Generation
Code is included and **enabled** to generate classification indices for **Rishi**, **Devata**, and **Chandas**, as well as an alphabetical **Header Index**.

**Status**: *Active*. Indices are generated during the build process.

**Access**:
Links to the indices are available on the Homepage under "सङ्क्रमणिका / वर्गीकरणम्".

## Verified Workflow: Aaranam Processing

For processing the `Aaranam_input.txt` file, use the following command sequence:

1.  **Generate JSON (Correction Mode)**
    ```bash
    python src/generate_json.py data/input/Aaranam_input.txt
    ```
    *Output*: `data/output/Aaranam_input_out.json`

2.  **Generate PDF**
    ```bash
    python src/render_pdf.py data/output/Aaranam_input_out.json
    lualatex data/output/pdf/Devanagari/Devanagari_Devanagari_Unicode.tex
    ```

3.  **Generate Website**
    ```bash
    python src/generate_website.py --source-file data/output/Aaranam_input_out.json
    ```
    *Output*: `docs/` folder (Parvas, Kandahs, Indices)

4.  **Preview Website**
    ```bash
    python -m http.server 8080 --directory docs
    ```


## Correction Cycle Workflow (v4.1 - Unified)

This project supports a robust correction workflow where you can enrich the JSON data with metadata (Rishi, Devata, Chandas) from an external file.

### Metadata Correction Workflow

This workflow is file-format agnostic, supporting **CSV**, **Excel (.xlsx)**, and **Unicode Text (.txt)**.

#### Step 1: Generate Metadata Table
Run the granular table generator to create the baseline file.
```bash
python src/generate_granular_table.py
```
*Output:* `data/output/JSV_Samam_Granular_Table.csv` (and optionally `.xlsx` if configured)

#### Step 2: Edit Metadata
You can edit the generated file using one of these methods:

**Method A: CSV in VS Code (Recommended)**
1.  Open `data/output/JSV_Samam_Granular_Table.csv` in VS Code.
2.  Use the **"Edit CSV"** extension (by janisdd) to view and edit as a table.
3.  *Why?* This safeguards against encoding issues common with external spreadsheet software.

**Method B: Excel (.xlsx)**
1.  Open the CSV or generated XLSX in Excel.
2.  Edit the metadata columns.
3.  **Save As** `.xlsx` to preserve Unicode characters safely.

**Method C: Excel (.txt)**
1.  If you must save strictly from Excel without `.xlsx`, use **"Save As > Unicode Text (*.txt)"**.
2.  This format (Tab-delimited UTF-16) is safe for Devanagari.

#### Step 3: Generate JSON with Enrichment
Pass the edited file to `generate_json.py` using the `--metadata-file` argument. The script automatically detects the format.

```bash
# Using a CSV (edited in VS Code)
python src/generate_json.py "data/input/Samhita_with_Rishi_Devata_Chandas.txt" \
    --input-mode correction \
    --metadata-file "data/output/JSV_Samam_Granular_Table.csv"

# Using an Excel file
python src/generate_json.py "data/input/Samhita_with_Rishi_Devata_Chandas.txt" \
    --input-mode correction \
    --metadata-file "data/output/JSV_Samam_Granular_Table.xlsx"
```

#### Step 4: Regenerate Artifacts
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

### Linking from Main Website (jaimineeyasamavedam.org)

To link the "Sacred Texts" menu item on the main WordPress site to the generated GitHub Pages deployment:

1.  **Log in to WordPress Admin** (`jaimineeyasamavedam.org/wp-admin`).
2.  Go to **Appearance > Menus**.
3.  Select the **Primary Menu**.
4.  Add a **Custom Link**:
    *   **URL**: `https://sekharnarayanaswamy-del.github.io/jaimineeyasamavedam/index.html`
    *   **Link Text**: `Sacred Texts`
5.  Click **Add to Menu** and save.




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
    *   **Visarga-Accent Swap**: The `step_preprocess_visarga_accent()` function ensures that Vedic accents appearing after a Visarga (`ः`) are correctly applied to the preceding character (the vowel) for accurate rendering (e.g., swapping `Wordः(1)` to `Word(1)ः`).
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
| `--metadata-file` | Metadata enrichment file. Supports **.csv, .xlsx, .txt**. | None |
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
    *   Optionally enriches with metadata from external file using `--metadata-file`.

#### Examples

**Run in Correction Mode (default):**
```bash
python src/generate_json.py data\input\Samhita_with_Rishi_Devata_Chandas.txt
```

**Run in Initial Mode:**
```bash
python src/generate_json.py data\input\Samhita_with_Rishi_Devata_Chandas.txt --input-mode initial
```

**Run in Correction Mode with Metadata Enrichment:**
```bash
# Using CSV (Recommended for VS Code)
python src/generate_json.py data\input\Samhita_with_Rishi_Devata_Chandas.txt --metadata-file data/output/JSV_Samam_Granular_Table.csv

# Using Excel
python src/generate_json.py data\input\Samhita_with_Rishi_Devata_Chandas.txt --metadata-file data/output/JSV_Samam_Granular_Table.xlsx
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
| `combined` | Single output with both Rik and Samam content together (default). | `Samhita_Devanagari.*` |
| `separate` | Two separate outputs: Rik-only and Samam-only files **with metadata** (rik_metadata, saman_metadata included). | `Rik_Devanagari.*`, `Samam_Devanagari.*` |
| `nometa` | Two separate outputs: Rik-only and Samam-only files **without metadata** (cleaner output, text only). | `Rik_NoMeta_Devanagari.*`, `Samam_NoMeta_Devanagari.*` |

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

---

### 3. `generate_Rik_for_samhita.py`

This script generates a specialized "Samhita" format output (Rik text in *scriptio continua*) for traditional recitation verification. It can produce both high-quality PDF (via LuaLaTeX) and HTML outputs.

**Location:** `src/generate_Rik_for_samhita.py`

#### Usage

```bash
python src/generate_Rik_for_samhita.py [OPTIONS]
```

#### Arguments

| Argument | Short | Description | Default |
| :--- | :--- | :--- | :--- |
| `--input` | `-i` | Path to the input text file. | `data/input/vedic_text.txt` |
| `--output` | `-o` | Base name for the output files (PDF/HTML). | `vedic_output` |
| `--format` | `-f` | Output format(s) to generate: `pdf`, `html`, or `all`. | `all` |

#### Examples

**Generate All Outputs (PDF & HTML):**
```bash
python src/generate_Rik_for_samhita.py -i data/input/my_text.txt -o my_output
```

**Generate Only HTML:**
```bash
python src/generate_Rik_for_samhita.py -i data/input/my_text.txt -f html
```

---

### 4. Footnote Formatting Guide

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
