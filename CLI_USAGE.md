# CLI Usage Documentation

This document describes how to use the primary scripts `generate_json.py` and `render_pdf.py` for processing Jaimineeya Sama Veda text.

## 1. `generate_json.py`

This script converts raw text input into a structured JSON file used for rendering.

**Location:** `src/generate_json.py`

### Usage

```bash
python src/generate_json.py <input_file> [OPTIONS]
```

### Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `input_file` | Input text file to process (positional, required). | - |
| `--input-mode` | Processing mode: `initial` or `correction`. | `correction` |
| `--output` | Path for the generated JSON output file. | Auto-generated: `data/output/<input_basename>_out.json` |
| `--metadata-csv` | CSV file to enrich metadata (correction mode only). | None |
| `--initial-json` | Trusted Initial JSON output to map Rik IDs correctly (correction mode only). | None |

### Modes

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

### Examples

**Run in Correction Mode (default):**
```bash
python src/generate_json.py data\input\Samhita_with_Rishi_Devata_Chandas.txt
```

**Run in Initial Mode:**
```bash
python src/generate_json.py data/input/Agneyam-Pavamanam_corrected.txt --input-mode initial
```

**Run in Correction Mode with CSV Metadata Enrichment:**
```bash
python src/generate_json.py data/input/Agneyam-Pavamanam_corrected.txt --metadata-csv data/output/JSV_Samam_Granular_Table.csv
```

---

## 2. `render_pdf.py`

This script takes the JSON output from the previous step and generates PDF, HTML, and Text files.

**Location:** `src/render_pdf.py`

### Usage

```bash
python src/render_pdf.py [INPUT_FILE] [OPTIONS]
```

### Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `input_file` | The input JSON file path (Positional). | `data/output/Agneyam-Pavamanam_corrected_out.json` |
| `--output-mode` | Output style: `combined`, `separate`, or `nometa`. | `combined` |
| `--pdf-font` | Font name to use for PDF generation. | `AdiShila Vedic` |
| `--html-font` | Font family string for HTML output. | `'AdiShila Vedic', 'Adishila SanVedic'` |

### Output Modes

| Mode | Description |
| :--- | :--- |
| `combined` | Single output with both Rik and Samam content, including all metadata. |
| `separate` | Two separate outputs: Rik-only and Samam-only, **with** metadata. |
| `nometa` | Two separate outputs: Rik-only and Samam-only, **without** metadata (plain text suitable for re-processing). |

### Examples

**Generate Combined Output (Standard):**
```bash
python src/render_pdf.py
```

**Generate Separate Rik and Samam Files (with metadata):**
```bash
python src/render_pdf.py data/output/Agneyam-Pavamanam_corrected_out.json --output-mode separate
```

**Generate No-Metadata Output (for re-processing):**
```bash
python src/render_pdf.py data/output/Agneyam-Pavamanam_corrected_out.json --output-mode nometa
```

> **Note:** The `nometa` mode generates text files with structural markers that can be used as input to `generate_json.py` in `initial` mode for re-processing.

---

## 3. `generate_Rik_for_samhita.py`

This script generates a PDF containing primarily Rik text, intended for Samhita verification or specific output formats.

**Location:** `src/generate_Rik_for_samhita.py`

### Usage

```bash
python generate_Rik_for_samhita.py [OPTIONS]
```

### Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `-i`, `--input` | Path to input text file. | `data/input/vedic_text.txt` |
| `-o`, `--output` | Base name for output files (PDF/Tex/HTML). | `vedic_output` |
| `-f`, `--format` | Output format: `pdf`, `html`, or `all`. | `all` |

### Features

*   **PDF Generation**: Creates a high-quality PDF using LuaLaTeX.
*   **HTML Generation**: Creates an HTML file for quick verification and web display.

### Examples

**Default Usage:**
```bash
python src/generate_Rik_for_samhita.py
```

**Custom Input and Output:**
```bash
python src/generate_Rik_for_samhita.py -i data/input/Uttararchikam.txt -o uttararchikam_rik
```

**Generate HTML Only:**
```bash
python src/generate_Rik_for_samhita.py -f html
```

---

## 4. `generate_granular_table.py`

This script generates a detailed Excel/CSV table listing every individual Samam with its metadata.

**Location:** `src/generate_granular_table.py`

### Usage

```bash
python src/generate_granular_table.py
```

### Output Files

| File | Description |
| :--- | :--- |
| `data/output/JSV_Samam_Granular_Table.csv` | CSV file (UTF-8 with BOM for Excel) |
| `data/output/JSV_Samam_Granular_Table.xlsx` | Excel file (requires `openpyxl`) |

### Output Columns

| Column | Description |
| :--- | :--- |
| `Global_Samam_Num` | Sequential Samam number (1-1226) |
| `Global_Rik_Num` | Sequential unique Rik number (1-530) |
| `Patha_Name` | Name of the Patha (आग्नेयपाठः, etc.) |
| `Khanda` | Section/Khanda name |
| `Rik_ID` | Rik ID within the section |
| `Arsheyam_Name` | Name of the Arsheyam |
| `Rik_Rishi`, `Rik_Devata`, `Rik_Chandas` | Rik metadata (parsed) |
| `Samam_Rishi`, `Samam_Devata`, `Samam_Chandas` | Samam metadata (parsed) |

---

## 5. `apply_excel_corrections.py`

This script reads corrections from the Excel file and applies them back to the JSON data. This enables an **Excel-based metadata correction workflow**.

**Location:** `src/apply_excel_corrections.py`

### Usage

```bash
# Preview changes (dry run - no modifications)
python src/apply_excel_corrections.py --dry-run

# Apply corrections (creates backup first)
python src/apply_excel_corrections.py
```

### Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--dry-run` | Preview changes without modifying JSON | False |
| `--excel` | Path to the Excel file | `data/output/JSV_Samam_Granular_Table.xlsx` |
| `--json` | Path to the JSON file to update | `data/output/Samhita_with_Rishi_Devata_Chandas_out.json` |

### Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  1. Generate Excel from JSON                                    │
│     python src/generate_granular_table.py                       │
│     → Creates JSV_Samam_Granular_Table.xlsx                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. Edit Metadata in Excel                                      │
│     - Open data/output/JSV_Samam_Granular_Table.xlsx            │
│     - Edit individual fields: Rik_Rishi, Rik_Devata,            │
│       Rik_Chandas, Samam_Rishi, Samam_Devata, Samam_Chandas     │
│     - Edit full strings: Rik_Metadata, Saman_Metadata           │
│     - Save and close the file                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. Apply Corrections to JSON                                   │
│     python src/apply_excel_corrections.py --dry-run  (preview)  │
│     python src/apply_excel_corrections.py            (apply)    │
│     → Updates JSON, creates backup automatically                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. Regenerate Outputs                                          │
│     python src/render_pdf.py                                    │
│     python src/generate_website.py                              │
│     → Creates updated HTML, PDF, TXT, Website                   │
└─────────────────────────────────────────────────────────────────┘
```

### Features

- **Dry Run Mode**: Preview all changes before applying
- **Automatic Backup**: Creates timestamped backup before modifying JSON
- **Change Report**: Shows detailed list of what was modified
- **Error Handling**: Reports rows that couldn't be matched

---

## 6. Footnote Formatting Guide

This section describes how to correctly format footnotes in the source text file.

### Footnote Syntax

Footnotes use the format `(sN)` where N is a number (e.g., `(s1)`, `(s2)`, `(s3)`).

### Placement Rules

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

### Pattern

The general pattern for a mantra character with swara and footnote is:
```
Word(Swara)(sN)
```

Where:
- `Word` = The Devanagari character/syllable
- `(Swara)` = The swara marking in parentheses
- `(sN)` = The footnote marker (no space before it)

### Footnote Definitions

Footnotes are defined in a separate block in the source file:
```
# Start of Footnote -- subsection_1 ## DO NOT EDIT
s1: Kerala Padhati explanation here
s2: Thogur Padhati explanation here
# End of Footnote -- subsection_1 ## DO NOT EDIT
```

### Invisible Characters Warning

> [!CAUTION]
> Avoid copying text from PDFs or web pages directly, as invisible Unicode characters (zero-width joiners, etc.) may be introduced. These can break footnote detection. If footnotes aren't rendering correctly, try deleting and retyping the `(sN)` marker.

