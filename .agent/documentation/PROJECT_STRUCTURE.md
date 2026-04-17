# Jaimineeya Samavedam: Project Structure

This document provides a comprehensive overview of the `jaimineeyasamavedam` repository structure and its core components.

## 1. Directory Hierarchy

```text
jaimineeyasamavedam/
├── .agent/              # AI Agent workflows, documentation, and skills
├── data/                # Primary project data repository
│   ├── input/           # Raw Vedic source text and metadata tables
│   ├── output/          # Generated JSON, CSV, and diagnostic reports
│   └── audio_source/    # Source audio files (if any)
├── docs/                # Ready-to-publish Static Website (GitHub Pages)
│   ├── samhita/         # Sama Samhita sub-site
│   ├── aaranam/         # Aranya Ganam sub-site
│   └── collection/      # Curated themed collections (Sooktamala, etc.)
├── src/                 # Processing pipeline source code (Python)
│   └── tools/           # Helper scripts for data conversion and cleanup
├── fonts/               # Digital Vedic fonts (Adishila, Noto Sans)
├── templates/           # Design templates for HTML and LuaLaTeX
└── website_configuration/ # Sub-site specific rendering rules
```

## 2. Core Pillars & Important Files

### **A. The Data Engine (`data/`)**
- **`data/input/`**:
    - [`Samhita_corrected.txt`](../../data/input/Samhita_corrected.txt): The master unified source file for the Jaimineeya Samhita.
    - [`Aaranam_latest.txt`](../../data/input/Aaranam_latest.txt): The master source for the Aaranam collection.
    - [`Rik Reconciliation table.xlsx`](../../data/input/Rik%20Reconciliation%20table.xlsx): The source of truth for Rishi/Devata metadata.
- **`data/output/`**:
    - [`Vargeekaran.json`](../../data/output/Vargeekaran.json): The processed, hierarchical database of the Samhita.
    - [`Aaranam_vargeekaran.json`](../../data/output/Aaranam_vargeekaran.json): The processed database of the Aaranam.
    - [`JSV_Rik_Table.csv`](../../data/output/JSV_Rik_Table.csv): A flattened table used for corrections and analysis.

### **B. The Logic Engine (`src/`)**
- [`generate_json.py`](../../src/generate_json.py): The primary parser that converts plain-text Vedic markup into structured JSON.
- [`generate_rik_table.py`](../../src/generate_rik_table.py): Integrates metadata from Excel sheets into the main JSON database.
- [`generate_website.py`](../../src/generate_website.py): The "Static Site Generator" that creates the beautiful parchment-styled web pages.
- [`render_pdf.py`](../../src/render_pdf.py): A complex wrapper for LuaLaTeX that produces high-quality Vedic PDFs with accurate accents.
- [`pipeline_config.yaml`](../../src/pipeline_config.yaml): The central switchboard for mapping input files to output paths.

### **C. The Web Engine (`docs/`)**
- [`index.html`](../../docs/index.html): The project gateway (Dashboard).
- [`main.js`](../../docs/samhita/js/main.js): The navigation and client-side search engine (Samhita example).
- [`styles.css`](../../docs/samhita/css/styles.css): The design system, including font-specific Vedic accent alignments.
- [`search-index.js`](../../docs/samhita/search-index.js): An offline-ready database for ultra-fast mantra searching.

### **D. The Agent Workspace (`.agent/`)**
- **`documentation/`**: Architectural guides and technical manuals for developers/AI.
- **`workflows/`**: Step-by-step guides for common tasks (e.g., committing changes).
- **`skills/`**: Specialized instructions for project-specific operations.

---

## 3. Maintenance Philosophy
This project is designed as a **Static Pipeline**. 
1. **Never edit files in `docs/` directly.**
2. Always modify the **Source Text** (`data/input/`) or the **Config** (`pipeline_config.yaml`).
3. Run the relevant `src/` script to propagate changes to the Website or PDF.
