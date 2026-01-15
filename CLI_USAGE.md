# CLI Usage Documentation

This document describes how to use the primary scripts `generate_json_for_samhita.py` and `renderPDF.py` for processing Jaimineeya Sama Veda text.

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

### Modes

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

### Examples

**Run in Correction Mode (default):**
```bash
python src/generate_json.py data/input/Agneyam-Pavamanam_latest.txt
```

**Run in Initial Mode:**
```bash
python src/generate_json.py data/input/Agneyam-Pavamanam_latest.txt --input-mode initial
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
| `input_file` | The input JSON file path (Positional). | `data/output/Agneyam-Pavamanam_latest_out.json` |
| `--output-mode` | Output style: `combined` (Rik+Samam) or `separate` (Rik/Samam files). | `combined` |
| `--pdf-font` | Font name to use for PDF generation. | `AdiShila Vedic` |
| `--html-font` | Font family string for HTML output. | `'AdiShila Vedic', 'Adishila SanVedic'` |

### Examples

**Generate Combined Output (Standard):**
```bash
python src/render_pdf.py
```

**Generate Separate Rik and Samam Files:**
```bash
python src/render_pdf.py data/output/Agneyam-Pavamanam_latest_out.json --output-mode separate
```

---

## 3. `generate_Rik_for_samhita.py`

This script generates a PDF containing primarily Rik text, intended for Samhita verification or specific output formats.

**Location:** `src/generate_Rik_for_samhita.py`

### Usage

```bash
python src/generate_Rik_for_samhita.py
```

### Arguments

*   **None**: This script currently uses hardcoded paths.
*   **Input**: `data/input/vedic_text.txt`
*   **Output**: `data/output/vedic_output.pdf`

---

## 3. Footnote Formatting Guide

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

