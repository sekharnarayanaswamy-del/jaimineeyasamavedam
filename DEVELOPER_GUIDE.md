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

## Git Baseline & GitHub Updates

To ensure work is saved and synchronized:

1.  **Baseline Locally**:
    ```bash
    git add .
    git commit -m "Baseline: Synchronized CSV correction cycle and updated website"
    ```

2.  **Push to GitHub**:
    ```bash
    git push origin main
    ```
    *Note: GitHub Pages is configured to serve from the `docs/` folder, so pushing these changes automatically updates the live website.*

## Running the Generator

```bash
python src/generate_website.py
```

## Running a Local Server

```bash
python -m http.server 8080 --directory docs
```
Then visit: http://localhost:8080
