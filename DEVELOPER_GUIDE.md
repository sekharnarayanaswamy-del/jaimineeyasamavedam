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

## Correction Cycle Workflow (v3.0 - CSV Enhanced)
This project uses a CSV-driven correction cycle to manage structural IDs and Metadata (Rishi, Devata, Chandas) independently of the text. This allows for precise data management while preserving the ability to edit the text freely.

### 1. Generate Metadata CSV (Baseline)
Generate the granular CSV table from your current JSON. This file (`data/output/JSV_Samam_Granular_Table.csv`) becomes your **Metadata Source of Truth**.
```bash
python src/generate_granular_table.py
```
*Note: This script uses `samam_utils.py` to ensure verse counts match the website exactly.*

### 2. Edit Metadata (CSV)
Copy the generated CSV to your input folder (e.g., `data/input/granular_table.csv`). Open it in a spreadsheet editor (must support UTF-8).
*   **Edit IDs**: Modify `Rik_ID` if grouping is incorrect.
*   **Edit Metadata**: Fill in `Saman_Rishi`, `Saman_Devata`, `Saman_Chandas`.
    *   *Note: These specific fields are what power the Website Indices.*

### 3. Edit Text (Txt)
Edit the mantra text in the Unicode Text File (`data/input/Samhita_with_Rishi_Devata_Chandas.txt`) as usual. You can fix typos, swaras, etc.

### 4. Generate JSON (Fusion)
Run `generate_json.py` in **correction mode** by passing the CSV. This merges your text corrections with the refined structure and metadata from the CSV.
```bash
python src/generate_json.py "data/input/Samhita_with_Rishi_Devata_Chandas.txt" --input-mode correction --metadata-csv "data/input/granular_table.csv"
```
*Result*: `data/output/Samhita_with_Rishi_Devata_Chandas_out.json` is created with perfect structure and metadata.

### 5. Regenerate Artifacts
Generate the website directly from the new JSON. The website generator now reads the JSON directly to utilize the specific metadata fields for indexing.
```bash
# Update Website
python src/generate_website.py --source-file data/output/Samhita_with_Rishi_Devata_Chandas_out.json

# Update PDF Source
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

#### Modes

*   **Initial Mode (`--input-mode initial`)**:
    *   Reads from the input file.
    *   Also reads auxiliary metadata files:
        *   `data/input/rishi_devata_chandas_for_rik.txt`
        *   `data/input/sama_rishi_chandas_out.txt`
        *   `data/input/vedic_text.txt`
    *   Used for the first pass of processing.

*   **Correction Mode (`--input-mode correction`)** *(default)*:
    *   Reads from the input file (expects processed Unicode text with embedded metadata).
    *   **Does NOT** read auxiliary files. It expects all metadata to be present in the input file itself.
    *   Used for subsequent passes after manual edits.

#### Examples

**Run in Correction Mode (default):**
```bash
python src/generate_json.py data/input/Agneyam-Pavamanam_latest.txt
```

**Run in Initial Mode:**
```bash
python src/generate_json.py data/input/Agneyam-Pavamanam_latest.txt --input-mode initial
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
| `input_file` | The input JSON file path (Positional). | `data/output/Agneyam-Pavamanam_latest_out.json` |
| `--output-mode` | Output style: `combined` (Rik+Samam) or `separate` (Rik/Samam files). | `combined` |
| `--pdf-font` | Font name to use for PDF generation. | `AdiShila Vedic` |
| `--html-font` | Font family string for HTML output. | `'AdiShila Vedic', 'Adishila SanVedic'` |

#### Examples

**Generate Combined Output (Standard):**
```bash
python src/render_pdf.py
```

**Generate Separate Rik and Samam Files:**
```bash
python src/render_pdf.py data/output/Agneyam-Pavamanam_latest_out.json --output-mode separate
```

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
