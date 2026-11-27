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
| `--procedures` | Path to procedure index YAML file (e.g., `data/input/prayoga/prayoga_index.yaml`). If omitted, no procedure links are added. | None |

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

## 2. `render.py` (and `render_pdf.py`)

This script takes the JSON AST output from the ingestion step and generates publication-grade PDF (LuaLaTeX), modern HTML reader, and plain Unicode Text files.

**Location:** `src/render.py` (alias `src/render_pdf.py`)

### Usage

```bash
python src/render.py [INPUT_FILE] [OPTIONS]
```

### Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `input_file` | The input JSON AST file path (Positional). | `data/corpora/samhita/02_ast/Samhita_ast.json` |
| `--output`, `-o` | Override the default output basename or specify a full output path. | Auto-generated based on input |
| `--output-mode` | Output style: `combined`, `separate`, or `nometa`. | `combined` |
| `--script` | Rendering script: `devanagari`, `malayalam`, or `grantha`. | `devanagari` |
| `--flow` | Enable continuous A4 flow layout (`CURRENT_FLOW_VARIANT`). Minimizes page breaks between mantras. | `False` |
| `--samam-only` | Render only Samam chanting content (skips Rik verses). | `False` |
| `--rik-only` | Render only Rik verses (skips Samam chants). | `False` |
| `--book-print` | Render in standard 180 × 228 mm book format instead of A4. | `False` |
| `--pdf-color-mode` | Color palette for PDF: `color` (hierarchical Vedic palette) or `bw` (pure monochrome). | `bw` |
| `--pdf-only` | Generate only PDF output (skips HTML and TXT generation). | `False` |
| `--html-only` | Generate only HTML output (skips PDF and TXT generation). | `False` |
| `--txt-only` | Generate only plain Unicode TXT output. | `False` |
| `--pdf-font` | Font name to use for PDF generation (`AdishilaVedic`, `NotoSerifGrantha`, `Noto Serif Malayalam`). | `AdishilaVedic` |
| `--html-font` | Font family string for HTML output. | `'AdishilaVedic', 'AdishilaSanVedic'` |
| `--toc-level` | TOC headers: `section`, `subsection`, or `both`. | `section` |
| `--title` | Custom Sanskrit title for the document. | From input JSON metadata or pipeline config. |
| `--legacy-html` | Use legacy single-page HTML layout instead of modern 2-column interactive reader layout. | `False` |

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

**Generate Devanagari HTML from Baraha `.docx` Source:**
```bash
python src/render_pdf.py "vedavms html/tu_baraha.docx" --html-only
```

**Custom Document Title:**
```bash
python src/render_pdf.py data/output/Prayogamala-pb.json --type collection --title "प्रयोगमाला पूर्वभागम्"
```

**Generate Separate Rik and Samam Files (with metadata):**
```bash
python src/render_pdf.py data/output/Agneyam-Pavamanam_corrected_out.json --output-mode separate
```

**Generate No-Metadata Output (for re-processing):**
```bash
python src/render_pdf.py data/output/Agneyam-Pavamanam_corrected_out.json --output-mode nometa
```

**Custom Output Path and Filename:**
```bash
python src/render_pdf.py data/output/Sooktamala.json -o data/exports/my_sooktam
```

### Notes and Best Practices
*   **Metadata Whitespace Preservation**: In HTML output, manual alignment of Rishi/Devata metadata is preserved. Ensure the source TXT file matches the desired visual layout.
*   **Aggregate Counting**: In `collection` mode, section headers automatically display aggregate counts. For mixed content, the format is **(ऋ-N, सा-M)**. If the section contains only one type, it shows only the numeral **(N)**.
*   **Navigation IDs**: Every section and subsection is assigned a unique ID (e.g., `#supersection_1-section_1-subsection_1`) for robust linking and table of contents navigation.

---

## 3. `generate_website.py`

This script generates the static HTML website from JSON data.

**Location:** `src/generate_website.py`

### Usage

```bash
python src/generate_website.py [OPTIONS]
```

### Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--source-file`, `-s` | Path to the input JSON file. | Required |
| `--output-dir`, `-o` | Output directory (default: `docs`). | `docs` |
| `--audio-dir`, `-d` | Directory for audio placeholder folders. | `data/input/Audio_Placeholders` |
| `--samhita`, `-m` | Generate for Samhita mode. | Default |
| `--aranam`, `-a` | Generate for Aaranam mode. | - |
| `--collection`, `-c` | Generate for Collection mode. | - |
| `--title` | Custom title for the collection (used with `--collection`). | From JSON metadata |

### Examples

**Generate Samhita website:**
```bash
python src/generate_website.py -s data/output/Vargeekaran.json -o docs/samhita
```

**Generate Collection with custom title:**
```bash
python src/generate_website.py -s data/output/Sooktamala.json -o docs/collection/sooktamala -c --title "साम सूक्तमाला"
```

---

## 4. `generate_Rik_for_samhita.py`

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

## 5. `generate_granular_table.py`

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

## 6. `apply_excel_corrections.py`

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

```text
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

## 7. `curate_jsv.py`

This script curates a subset of JSON files based on a list of P.K.S (Parva, Kandah, Samam) identifiers. It supports merging from multiple sources (Samhita, Aaranam, etc.) into a standalone curated JSON (Sooktamala).

**Location:** `src/curate_jsv.py`

### Usage

```bash
python src/curate_jsv.py --sources <src1> [src2...] --filter <filter_file> --output <output_file> [OPTIONS]
```

### Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--sources` | List of source JSON files (Samhita, Aaranam, etc.). | From `pipeline_config.yaml` |
| `--filter` | Text file containing P.K.S identifiers (one per line, e.g., `1.1.1`). | From `pipeline_config.yaml` |
| `--output` | Path to the output curated JSON file. | From `pipeline_config.yaml` |
| `--title` | Custom title for the curated collection. | "जैमिनीय साम सूक्तमाला" |
| `--mode` | Selection mode: `samam` (default), `rik`, `both`, or `rik_nometa`. | `samam` |

### Features

*   **Merging**: Automatically merges supersections and closing mantras from multiple JSON sources.
*   **P.K.S Filtering**: Precisely extracts specific Samams based on the global section **ordinal** index. 
    *   **Note**: The tool sorts source section keys (Kandahs) and assigns them numbers 1, 2, 3... based on their position. This ensures robust mapping regardless of naming conventions in the source JSON.
*   **Text Modes**:
    *   `samam`: Only includes Samam music text (musical notations), drops Rik meta.
    *   `rik`: Only includes the original Rik verse text, includes all Rik metadata.
    *   `both`: Includes both Samam and Rik text for comparison.
    *   `rik_nometa`: Includes ONLY the original Rik verse text, stripping all metadata fields.

### Examples

**Standard Samam Curation:**
```bash
python src/curate_jsv.py --sources data/output/Vargeekaran.json --filter data/input/Nakshatra_sooktam.txt --output data/output/nakshatra_sooktam.json
```

**Curate Rik Text instead of Samam (with metadata):**
```bash
python src/curate_jsv.py --sources data/output/Vargeekaran.json --filter my_filter.txt --output my_rik_collection.json --mode rik
```

**Curate Rik Text ONLY (no metadata):**
```bash
python src/curate_jsv.py --sources data/output/Vargeekaran.json --filter my_filter.txt --output my_rik_only.json --mode rik_nometa
```

---

## 8. `renumber_sooktam.py`

This script renumbers IDs (`supersection_N`, `section_N`, `subsection_N`) and mantra markers (`॥ N ॥`) in both `.txt` and `.json` files.

**Location:** `src/tools/renumber_sooktam.py`

### Features

*   **Component Grouping**: The tool uses a set-based tracking logic. If a verse is composed of separate blocks (e.g., `# Start of Rik Metadata` followed by `# Start of Rik Text`), they are all grouped under the same `subsection_N` ID even if separated by blank lines. Only repeated components (e.g., a second Metadata block) trigger a counter increment.
*   **Sequential Sync**: Ensures perfectly sequential IDs across curated collections.

### Usage

```bash
python src/tools/renumber_sooktam.py <input_file> [OPTIONS]
```

### Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `input_file` | Path to the `.txt` or `.json` file to renumber. | - |
| `--jsv-version` | Manual version override (e.g. 5.0). Updates src/VERSION. | None |
| `--no-increment` | Use current version from src/VERSION without bumping. | False |
| `--no-renumber` | Inject-Only mode: update metadata header but skip renumbering content. | False |
| `--preserve-super` | Preserve existing SuperSection IDs (only renumbers sections/subsections). | False |
| `--preserve-all` | Preserve ALL structure IDs (only renumbers Samams). | False |
| `--start-super` | Starting number for SuperSections. | 1 |
| `--start-section` | Starting number for Sections. | 1 |
| `--start-subsection` | Starting number for SubSections. | 1 |
| `--reset-per-super` | Reset Section/SubSection counters at every SuperSection boundary. | False |
| `--contiguous-samams` | Do NOT reset Samam numbering at SuperSection boundaries (global contiguous). | False |

### Examples

**Renumber TXT file resetting Samams per SuperSection (Default):**
```bash
python src/tools/renumber_sooktam.py data/output/txt/Devanagari/Samhita_Unicode.txt
```

**Renumber while keeping existing structure IDs (Samam-only renumbering):**
```bash
python src/tools/renumber_sooktam.py data/input/Aaranam_latest.txt --preserve-all
```

**Custom starting offsets:**
```bash
python src/tools/renumber_sooktam.py MyText.txt --start-super 5 --start-section 10
```

---

## 9. Footnote Formatting Guide

This section describes how to correctly format footnotes in the source text file.

### Footnote Syntax

Footnotes use the format `(sN)` where N is a number (e.g., `(s1)`, `(s2)`, `(s3)`).

### Placement Rules

> [!IMPORTANT]
> **Footnote markers must be placed immediately after the swara** with NO space.

**Correct:**
```text
इ(श)(s1)     ← footnote attaches to इ (correct)
वा(चा)(s2)   ← footnote attaches to वा (correct)
```

**Incorrect:**
```text
इ(श) (s1)    ← space before footnote - may attach to wrong character
इ (s1)(श)    ← footnote before swara - incorrect placement
```

### Pattern

The general pattern for a mantra character with swara and footnote is:
```text
Word(Swara)(sN)
```

Where:
- `Word` = The Devanagari character/syllable
- `(Swara)` = The swara marking in parentheses
- `(sN)` = The footnote marker (no space before it)

### Footnote Definitions

Footnotes are defined in a separate block in the source file:
```text
# Start of Footnote -- subsection_1 ## DO NOT EDIT
s1: Kerala Padhati explanation here
s2: Thogur Padhati explanation here
# End of Footnote -- subsection_1 ## DO NOT EDIT
```

### Invisible Characters Warning

> [!CAUTION]
> Avoid copying text from PDFs or web pages directly, as invisible Unicode characters (zero-width joiners, etc.) may be introduced. These can break footnote detection. If footnotes aren't rendering correctly, try deleting and retyping the `(sN)` marker.

---

## 10. Malayalam Script Pipeline (CLI Guide)

The Malayalam workflow converts, transliterates, and renders the Jaimineeya Samaveda into Malayalam base text with Grantha superscript swara notations and Vedic modifiers.

### Step 1: Generate JSON AST from Malayalam Text
```powershell
python -X utf8 src/generate_json.py data/input/Malayalam/Samhita_Malayalam_corrected.txt --output data/output/malayalam/Samhita_Malayalam.json
```

### Step 2: Render PDF, HTML, and Unicode TXT
Run `src/render_pdf.py` with `--script malayalam` in one of the 3 available output modes:

1. **Combined Mode (Default — Rik + Samam + Rishi/Devata/Chandas):**
   ```powershell
   $env:PYTHONPATH="src"; python -X utf8 src/render_pdf.py data/output/malayalam/Samhita_Malayalam.json --script malayalam
   ```
   *Generated Outputs:*
   - `data/output/pdf/Malayalam/Samhita_Malayalam.pdf`
   - `data/output/html/Malayalam/Samhita_Malayalam.html`
   - `data/output/txt/Malayalam/Samhita_Malayalam_Unicode.txt`

2. **Separate Mode (Separate Rik and Samam files with Metadata):**
   ```powershell
   $env:PYTHONPATH="src"; python -X utf8 src/render_pdf.py data/output/malayalam/Samhita_Malayalam.json --script malayalam --output-mode separate
   ```
   *Generated Outputs:*
   - `data/output/pdf/Malayalam/Rik_Malayalam.pdf` & `Samam_Malayalam.pdf`
   - `data/output/html/Malayalam/Rik_Malayalam.html` & `Samam_Malayalam.html`
   - `data/output/txt/Malayalam/Rik_Malayalam_Unicode.txt` & `Samam_Malayalam_Unicode.txt`

3. **No-Metadata Mode (Mantra Texts Only, no RDC headers):**
   ```powershell
   $env:PYTHONPATH="src"; python -X utf8 src/render_pdf.py data/output/malayalam/Samhita_Malayalam.json --script malayalam --output-mode nometa
   ```
   *Generated Outputs:*
   - `data/output/pdf/Malayalam/Rik_NoMeta_Malayalam.pdf` & `Samam_NoMeta_Malayalam.pdf`
   - `data/output/html/Malayalam/Rik_NoMeta_Malayalam.html` & `Samam_NoMeta_Malayalam.html`
   - `data/output/txt/Malayalam/Rik_NoMeta_Malayalam_Unicode.txt` & `Samam_NoMeta_Malayalam_Unicode.txt`

### All-in-One Command
```powershell
python -X utf8 src/generate_json.py data/input/Malayalam/Samhita_Malayalam_corrected.txt --output data/output/malayalam/Samhita_Malayalam.json; $env:PYTHONPATH="src"; python -X utf8 src/render_pdf.py data/output/malayalam/Samhita_Malayalam.json --script malayalam; python -X utf8 src/render_pdf.py data/output/malayalam/Samhita_Malayalam.json --script malayalam --output-mode separate; python -X utf8 src/render_pdf.py data/output/malayalam/Samhita_Malayalam.json --script malayalam --output-mode nometa
```

### Font Building & Glyph Table Generation
To re-build the custom font or regenerate the interactive HTML glyph table:
```powershell
python scripts/build_swara_font.py
python scripts/generate_glyph_grid.py
```

---

## 11. YAML Configuration Files Reference

The repository uses several YAML (`.yaml` / `.yml`) configuration files to centralize pipeline settings, render defaults, procedure mappings, web collections, and automated deployment.

### Overview of YAML Files

| File Path | Component / Role | Consumed By |
| :--- | :--- | :--- |
| [`src/pipeline_config.yaml`](../../src/pipeline_config.yaml) | **Master Pipeline Switchboard**: Centralized settings for input/output paths, default flags, and modes for all scripts. | `utils.py`, `renumber_sooktam.py`, `generate_json.py`, `curate_jsv.py`, `generate_rik_table.py`, `generate_website.py`, `render_pdf.py` |
| [`src/render_config.yaml`](../../src/render_config.yaml) | **Dedicated Rendering Configuration**: Font, color, TOC levels, and text-type presets for PDF/HTML output. | `render_pdf.py` |
| [`data/input/prayoga/prayoga_index.yaml`](../../data/input/prayoga/prayoga_index.yaml) | **Prayoga (Procedure) Linking Index**: Maps ritual procedure Markdown guides to mantra structure sections. | `generate_json.py` (`--procedures`), `generate_website.py`, `render_pdf.py` |
| [`docs/collection_config.yaml`](../../docs/collection_config.yaml) | **Gateway Homepage Collection Registry**: Configures curated collections showcased on the gateway landing page. | `docs/index.html` (Website Gateway) |
| [`.github/workflows/deploy-to-hostinger.yml`](../../.github/workflows/deploy-to-hostinger.yml) | **CI/CD Deployment Workflow**: Automates FTP sync of `docs/` to Hostinger production hosting upon git push. | GitHub Actions Runner |

---

### 11.1 `src/pipeline_config.yaml` (Master Pipeline Switchboard)

The primary central configuration file for the entire processing pipeline. Instead of remembering complex CLI arguments, scripts look up defaults in this file.

*   **Location:** `src/pipeline_config.yaml`
*   **Key Sections:**
    *   `project`: Project name, current version (`3.12`), `input_root`, and `output_root`.
    *   `renumber_sooktam`: Default offsets and flags for Samhita (`start_super: 1`, `reset_per_super: true`) and Aaranam (`start_super: 7`, `reset_per_super: false`).
    *   `generate_json`: Source paths for auxiliary files (`rik_meta`, `saman_meta`, `rik_text`), and type-specific paths for `samhita` and `aaranam`.
    *   `generate_rik_table`: Input JSON, output CSV, reconciliation Excel, and final Vargeekaran JSON destinations.
    *   `generate_aaranam_rik_table`: Path mappings for Aaranam baseline table creation.
    *   `curate_jsv`: Default sources, filter files, and output paths for custom collection extractions.
    *   `build_collection`: Default source and target output for themed collections.
    *   `generate_website`: Web generation defaults (`docs/`, audio directory, font) and per-type output configurations (`docs/samhita`, `docs/aaranam`, `docs/collection`).
    *   `render`: Rendering defaults (`output_mode`, `pdf_font`, `html_font`, `pdf_color_mode`, `toc_level`, `kpully`), document titles, template directories, and character normalization flags (`replace_colons_with_visarga`, `sanitize_invisible_chars`, `enable_footnote_consolidation`).
    *   `procedures`: Enables prayoga linking and specifies the index file location (`data/input/prayoga/prayoga_index.yaml`).

```yaml
# Example excerpt from src/pipeline_config.yaml:
project:
  name: "Jaimineeya Samavedam"
  version: "3.12"
  output_root: "data/output"
  input_root: "data/input"

generate_json:
  samhita:
    input: "data/input/Samhita_corrected.txt"
    output: "data/output/Samhita_corrected_out.json"
    mode: "correction"
```

---

### 11.2 `src/render_config.yaml` (Standalone Render Configuration)

Provides a lightweight configuration file specifically tailored for document rendering when calling `render_pdf.py` without specifying long command-line options.

*   **Location:** `src/render_config.yaml`
*   **Key Sections:**
    *   `defaults`: Default output style (`combined`, `separate`, `nometa`), fonts (`AdishilaVedic`), color mode (`bw` vs `color`), and table-of-contents depth (`section` or `subsection`).
    *   `types`: Presets for `samhita`, `aaranam`, and `collection` (input file paths, Sanskrit document titles `doc_title`, summary table titles `summary_title`, and file prefixes).
    *   `paths`: Paths to LaTeX/HTML/text templates (`templates/`) and logs.
    *   `advanced`: Toggle flags for summary table generation, footnote consolidation, colon-to-visarga replacement, and invisible character cleanup.

---

### 11.3 `data/input/prayoga/prayoga_index.yaml` (Prayoga Procedure Index)

Maps procedural ritual descriptions written in Markdown (`data/input/prayoga/*.md`) to structured mantra units in the text hierarchy.

*   **Location:** `data/input/prayoga/prayoga_index.yaml`
*   **How it works:**
    *   Each entry defines a `scope` (`supersection`, `section`, or `subsection`), a target structural `id` (e.g., `supersection_22`, `section_1`), the relative Markdown `file` name, and a display `title`.
    *   **Resolution Order**: Subsection-level mappings take precedence over section-level, which take precedence over supersection-level.
    *   **CLI Usage**: Pass to `generate_json.py` via `--procedures data/input/prayoga/prayoga_index.yaml` to inject procedure metadata into the generated JSON.
    *   **Downstream Effect**:
        *   `generate_website.py` produces dedicated readable procedure HTML pages and adds navigation links at section/subsection headers.
        *   `render_pdf.py` renders the Markdown into a LaTeX appendix (`॥ परिशिष्टम् ॥`) with automatic footnote hyperlinks pointing to the appendix.

```yaml
# Example entry from data/input/prayoga/prayoga_index.yaml:
procedures:
  - scope: section
    id: section_1
    file: aupasanam.md
    title: औपासनम् - विधिः
  - scope: supersection
    id: supersection_22
    file: udakashanti.md
    title: उदकशान्ति - विधिः
```

---

### 11.4 `docs/collection_config.yaml` (Gateway Collections Registry)

Controls the curated collections cards featured on the gateway homepage (`docs/index.html`).

*   **Location:** `docs/collection_config.yaml`
*   **Key Fields per Collection:**
    *   `id`: Unique identifier (e.g. `sooktamala`, `prayogamala-purva`, `prayogamala-uttara`).
    *   `title_sa`: Devanagari Sanskrit title (e.g. `साम सूक्तमाला`).
    *   `title_en`: English transliterated title (e.g. `Sama Sooktamala`).
    *   `description`: Brief description of the collection's contents and ritual purpose.
    *   `path`: Relative link to the collection entry page (e.g. `collection/sooktamala/index.html`).
    *   `icon`: Visual emoji icon representing the collection card.

---

### 11.5 `.github/workflows/deploy-to-hostinger.yml` (CI/CD Deployment Workflow)

Automates the build and deployment process via GitHub Actions.

*   **Location:** `.github/workflows/deploy-to-hostinger.yml`
*   **Trigger**: Triggered automatically on push to the `master` / `main` branch when changes are made.
*   **Action**: Uses FTPS / FTP action with repository secrets (`FTP_SERVER`, `FTP_USERNAME`, `FTP_PASSWORD`) to synchronize the generated static website directory (`docs/`) directly to the production Hostinger web host.

---

## 12. Grantha Script Pipeline (CLI Guide)

This pipeline transliterates Devanagari AST into authentic Grantha script using `src/grantha/gr_transliterate.py` and renders high-fidelity LuaLaTeX PDF publications, modern standalone HTML readers (with Latin numerals), and plain Unicode text outputs for both Samhita and Aranyakam.

**Runner Script:** `src/run_grantha_pipeline.py`

### Usage

```bash
# Generate complete Grantha release (Color Flow PDF, BW Flow PDF, standalone HTML, Unicode TXT)
python src/run_grantha_pipeline.py

# Generate only Black & White A4 Flow PDF (for printing)
python src/run_grantha_pipeline.py --bw
```

### CLI Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--pdf-color-mode` | Color mode for LuaLaTeX PDF: `color`, `bw`, or `all`. | `all` |
| `--bw` | Shortcut flag to build Black & White A4 flow PDF only. | `False` |

### Pipeline Outputs

| Corpus | Output File | Description |
| :--- | :--- | :--- |
| **Samhita** | `data/corpora/samhita/05_renders/pdf/Samhita_Grantha.pdf` | Color A4 Flow PDF (335 pages) |
| | `data/corpora/samhita/05_renders/pdf/Samhita_flow_bw_Grantha.pdf` | Black & White A4 Flow PDF (335 pages) |
| | `data/corpora/samhita/05_renders/html/Samhita_Grantha.html` | Interactive HTML reader with Latin numerals |
| | `data/corpora/samhita/05_renders/txt/Samhita_Grantha_Unicode.txt` | Clean Unicode plaintext in Grantha script |
| **Aranyakam** | `data/corpora/aaranam/05_renders/pdf/Aaranam_Grantha.pdf` | Color A4 Flow PDF (144 pages) |
| | `data/corpora/aaranam/05_renders/pdf/Aaranam_flow_bw_Grantha.pdf` | Black & White A4 Flow PDF (144 pages) |
| | `data/corpora/aaranam/05_renders/html/Aaranam_Grantha.html` | Interactive HTML reader with Latin numerals |
| | `data/corpora/aaranam/05_renders/txt/Aaranam_Grantha_Unicode.txt` | Clean Unicode plaintext in Grantha script |

---

## 13. Unified Samhita + Aranyakam Samam Edition Pipeline (CLI Guide)

This specialized pipeline generates the continuous liturgical chanting edition combining all Samams with their associated Rishi/Devata/Chandas metadata from both Samhita and Aranyakam into a single unified publication.

### Architectural Features:
1. **Contiguous Individual Samam Numbering (1 to 1,521)**:
   - Numbering extends seamlessly across all Khandah, Parvah, and Bhaga boundaries without resetting:
     - **Part 1 (प्रथमः भागः — संहिता)**: Samams **1 to 1,226** across Supersections 1–6 (Agneya: 1–182, Tadva: 183–382, Brihati: 383–534, Asavi: 535–640, Aindra: 641–826, Pavamana: 827–1,226).
     - **Part 2 (द्वितीयः भागः — आरण्यकम्)**: Samams **1,227 to 1,521** across Supersections 7–12 (Vrata: 1,227–1,334, Arkani: 1,335–1,414, Dvandva: 1,415–1,475, Shukriya: 1,476–1,494, Shakvarya: 1,495–1,497, Aupanisada: 1,498–1,521).
2. **Pure Unicode Subsection Headers (Ārṣeyams)**:
   - Subsection titles (Ārṣeyams) have **no numbers prepended** before them (e.g. `॥ वत्सस्यकाण्वस्यसामनीद्वे ॥` in `AccentGreen` followed by its metadata in `AccentBrown`).
3. **No Divider Lines**:
   - The horizontal dividing rules between Samam blocks are eliminated for an unobstructed, natural liturgical flow.
4. **Structural Part Dividers & Bookmarks**:
   - Dedicated division pages and clean PDF outline bookmarks for Part 1 (`प्रथमः भागः — संहिता`) and Part 2 (`द्वितीयः भागः — आरण्यकम्`).

**Generator Script:** `scripts/recompile_samhita_aranyakam_samam.py`  
**AST Builder:** `scripts/build_combined_ast.py`

### Usage

```bash
# 1. Compile A4 Flow Color Edition (Default)
python scripts/recompile_samhita_aranyakam_samam.py

# 2. Compile A4 Flow Black & White Edition
python scripts/recompile_samhita_aranyakam_samam.py --bw

# 3. Compile both Color and Black & White Editions (A4)
python scripts/recompile_samhita_aranyakam_samam.py --all-colors

# 4. Compile Book Format (180 × 228 mm) Color Edition
python scripts/recompile_samhita_aranyakam_samam.py --book

# 5. Compile Book Format (180 × 228 mm) Black & White Edition
python scripts/recompile_samhita_aranyakam_samam.py --book --bw
```

### CLI Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--book` | Compile Crown Quarto Book format (180 × 228 mm) instead of standard A4. | `False` (A4) |
| `--bw` | Compile pure Black & White monochrome edition instead of Vedic color. | `False` (Color) |
| `--all-colors` | Compile both Color and Black & White editions in a single run. | `False` |

### Publication Outputs

| Format | Color Mode | Output PDF File | Pages (20pt Edition) |
| :--- | :--- | :--- | :---: |
| **A4 Continuous Flow** | Vedic Color | `data/corpora/samhita_aranyakam/05_renders/pdf/Samhita_Aranyakam_flow_Samam_Devanagari.pdf` | 251 |
| **A4 Continuous Flow** | Black & White | `data/corpora/samhita_aranyakam/05_renders/pdf/Samhita_Aranyakam_flow_bw_Samam_Devanagari.pdf` | 251 |
| **Book (180 × 228 mm)** | Vedic Color | `data/corpora/samhita_aranyakam/05_renders/pdf/Samhita_Aranyakam_book_flow_Samam_Devanagari.pdf` | 385 |
| **Book (180 × 228 mm)** | Black & White | `data/corpora/samhita_aranyakam/05_renders/pdf/Samhita_Aranyakam_book_flow_bw_Samam_Devanagari.pdf` | 385 |

### Typography & Layout Specifications:
- **20 pt Chant Text**: `\devafont[Scale=1.68]` in `AdishilaVedic.ttf` with proportional headings (`Scale=1.79`), swaras (`Scale=1.18`), and arcs (`Scale=1.55`).
- **Balanced Running Header**: Alternates `[Supersection Name] — [Section Name] — [Page Number]` across verso/recto pages using `fancyhdr`.
- **Flowing Footnote Apparatus**: Configured via `\usepackage[perpage,para]{footmisc}` with tab separator (`\hskip 2.0em plus 1.0em minus 0.5em`) and elevated `\skip\footins` (16pt).
- **Variant Notations**: Standardized ingestion for manuscript markers `को.प` (Kodunthirapully) and `तो.प` (Togur).

---

## 14. Aranyakam Parva Splitting Tool (CLI Guide)

This tool slices the unified master Aranyakam text (`data/corpora/aaranam/01_input/Aaranam_latest.txt`, 2,677 lines) into individual Parva files matching the structure of the Samhita parvas.

**Location:** `scripts/split_aranyakam_parvas.py`

### Usage

```bash
python scripts/split_aranyakam_parvas.py
```

### Generated Files & Directory Layout

1. **Parvas Directory** (`data/corpora/aaranam/01_input/parvas/`):
   - Canonical continuous filenames (Parvas 7–12 across Samhita+Aranyakam):
     - `Parva_7_Vrata_Parva_Devanagari_Unicode.txt` (974 lines, 56 subsections)
     - `Parva_8_Arkani_Patha_Devanagari_Unicode.txt` (919 lines, 56 subsections)
     - `Parva_9_Dvandva_Parva_Devanagari_Unicode.txt` (515 lines, 29 subsections)
     - `Parva_10_Shukriya_Parva_Devanagari_Unicode.txt` (124 lines, 7 subsections)
     - `Parva_11_Shakvarya_Parva_Devanagari_Unicode.txt` (42 lines, 1 subsection)
     - `Parva_12_Aupanishada_Parva_Devanagari_Unicode.txt` (93 lines, 5 subsections, with Closing Mantras)
   - Aranyakam-relative aliases (`Parva_1_...` through `Parva_6_...`) for liturgical study.

2. **Root Directory Mirror** (`data/corpora/aaranam/01_input/`):
   - Canonical `Parva_7` through `Parva_12` files mirrored for root-level tool convenience.

### Invariants:
- Zero line loss ($974 + 919 + 515 + 124 + 42 + 93 = 2,667$ extracted content lines).
- 100% parseable by `src/generate_json.py` (`parse_unicode_text_file`).



