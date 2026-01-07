# CLI Usage Documentation

This document describes how to use the primary scripts `generate_json_for_samhita.py` and `renderPDF.py` for processing Jaimineeya Sama Veda text.

## 1. `generate_json_for_samhita.py`

This script converts raw text input into a structured JSON file used for rendering.

**Location:** `Rik_Processing/generate_json_for_samhita.py`

### Usage

```bash
python Rik_Processing/generate_json_for_samhita.py <input_file> [OPTIONS]
```

### Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `input_file` | Input text file to process (positional, required). | - |
| `--input-mode` | Processing mode: `initial` or `correction`. | `correction` |
| `--output` | Path for the generated JSON output file. | Auto-generated: `<input_basename>_out.json` |

### Modes

*   **Initial Mode (`--input-mode initial`)**:
    *   Reads from the input file.
    *   Also reads auxiliary metadata files like `rishi_devata_chandas_for_rik.txt` and `vedic_text.txt`.
    *   Used for the first pass of processing.

*   **Correction Mode (`--input-mode correction`)** *(default)*:
    *   Reads from the input file (expects processed Unicode text with embedded metadata).
    *   **Does NOT** read auxiliary files (`rishi_devata_chandas_for_rik.txt`, etc.). It expects all metadata to be present in the input file itself.
    *   Used for subsequent passes after manual edits.

### Required Dependency Files

The following file is **required** and must be present in the working directory (not configurable via CLI):

| File | Purpose |
| :--- | :--- |
| `sama_rishi_chandas_out.txt` | Provides Saman metadata (Rishi, Chandas, Devata) for each subsection. Used by `SamanMetadataParser` to concatenate metadata entries based on the number of mantras in each subsection. |

> **Note:** The script looks for `sama_rishi_chandas_out.txt` relative to the current working directory. Ensure this file exists before running the script.

### Examples

**Run in Correction Mode (default, most common):**
```bash
python Rik_Processing/generate_json_for_samhita.py output_text/txt/Devanagari/Full_Samhita_ip_with_FN.txt
```

**Run in Correction Mode with custom output:**
```bash
python Rik_Processing/generate_json_for_samhita.py output_text/txt/Devanagari/Full_Samhita_ip_with_FN.txt --output my_output.json
```

**Run in Initial Mode:**
```bash
python Rik_Processing/generate_json_for_samhita.py corrections_003.txt --input-mode initial
```

---


## 2. `renderPDF.py`

This script takes the JSON output from the previous step and generates PDF, HTML, and Text files.

**Location:** `Devanagari_standalone/working_baseline/renderPDF.py`

### Usage

```bash
python Devanagari_standalone/working_baseline/renderPDF.py [INPUT_FILE] [OPTIONS]
```

### Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `input_file` | The input JSON file path (Positional). | `corrections_003_out.json` |
| `--output-mode` | Output style: `combined` (Rik+Samam) or `separate` (Rik/Samam files). | `combined` |
| `--pdf-font` | Font name to use for PDF generation. | `AdiShila Vedic` |
| `--html-font` | Font family string for HTML output. | `'AdiShila Vedic', 'Adishila SanVedic'` |

### Examples

**Generate Combined Output (Standard):**
```bash
python Devanagari_standalone/working_baseline/renderPDF.py Unicode_input_with_FN_out.json
```

**Generate Separate Rik and Samam Files:**
```bash
python Devanagari_standalone/working_baseline/renderPDF.py Unicode_input_with_FN_out.json --output-mode separate
```

**Custom Font:**
```bash
python Devanagari_standalone/working_baseline/renderPDF.py Unicode_input_with_FN_out.json --pdf-font "Siddhanta"
```

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

