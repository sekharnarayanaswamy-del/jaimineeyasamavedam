# Jaimineeya Samaveda Pipeline — Refactoring & Validation Architecture

**Document Version**: 2.0.0  
**Updated Date**: 15-09-2026  
**Target Scope**: Architecture decoupling, Golden Replica Verification, and Step-by-Step Validation Workflow  

---

## 🏛️ 1. Refactoring Core Principles & Architectural Cleanliness

### A. Decoupling External Projects (Baraha & VedaVMS Decommissioning)
- **External Dependencies Retired**: All Baraha `.docx` ingestion and VedaVMS single-page reader generation logic were migrated to the dedicated `vedavms` repository (`c:\Users\sekha\OneDrive\Documents\GitHub\vedavms`).
- **Cleaned Codebase**: Removed `vedavms_html/`, `src/build_reader.py`, `src/baraha_reader.py`, `src/transliterate.py`, `src/config.json`, `src/refactor_for_baraha.md`, and purged all `is_baraha` conditional branches from `src/render_pdf.py`.
- **Pure Jaimineeya Focus**: The pipeline strictly focuses on Jaimineeya Samaveda canonical texts (Samhita, Aaranam, Prayogamala, Sooktamala) across Malayalam and Devanagari dual scripts.

### B. Core Domain Architecture
1. **Typed AST Schema (`src/core/models.py`)**:
   - `VedicDocument` $\rightarrow$ `SuperSection` $\rightarrow$ `Section` $\rightarrow$ `SubSection` $\rightarrow$ `MantraSet` $\rightarrow$ `RikMantra`
   - Lossless JSON serialization/deserialization with Pydantic domain models.
2. **Swara Engine (`src/core/swara_engine.py`)**:
   - Encapsulates Vedic accent normalization rules (Anudatta `॒`, Svarita `॑`, Deergha Svarita `᳚`, Kampa `᳸`).
   - Guarantees **zero dotted circles (`◌`)** by enforcing canonical Visarga/Anusvara accent ordering.
3. **Modular Renderer System (`src/renderers/`)**:
   - `LaTeXRenderer`: Generates LuaLaTeX/XeLaTeX PDF source.
   - `HTMLRenderer`: Generates standalone interactive HTML pages (`Malayalam_main_html.template` / `Devanagari_main_html.template`).
   - `TextRenderer`: Plaintext export with swara notation.
   - `SiteRenderer`: Multi-page static website platform (`src/generate_website.py` $\rightarrow$ `docs/`).

---

## 🔬 2. Validation & Non-Regression Framework

### Why Raw SHA-256 Checksums Are Insufficient
A raw byte checksum (SHA-256) is a binary lock. On every pipeline run, generated output JSONs embed volatile metadata timestamps (`"generated_at": "15-09-2026 15:41:00"`). A pure bitwise hash check will flag a false `[DIFF]` on every execution, even when text, structure, and accent markings are 100% identical.

### The Solution: Semantic AST Parity Verification
The system employs **Semantic AST Normalization** in `python src/tools/baseline.py verify`:
1. Re-executes the ingestion pipeline (`generate_json.py`, `generate_rik_table.py`) from golden baseline inputs.
2. Strips volatile metadata timestamps (`generated_at`).
3. Compares the generated JSON AST payload trees node-by-node against the frozen Golden Replica manifest (`data/baselines/LATEST.json`).
4. Asserts **100% structural and text equivalence**.

---

## 📊 3. Baseline Data Coverage

The baseline snapshot system ([`data/baselines/LATEST.json`](file:///c:/Users/sekha/OneDrive/Documents/GitHub/jaimineeyasamavedam/data/baselines/LATEST.json)) tracks **3 complete dataset families**:

1. **Devanagari Master Texts**:
   - `data/input/Samhita_corrected.txt` $\rightarrow$ `data/output/Samhita_corrected_out.json`
   - `data/input/Aaranam_latest.txt` $\rightarrow$ `data/output/Aaranam_latest_out.json`
   - `data/output/Vargeekaran.json` (Master reconciled dataset)
2. **Malayalam Master Texts**:
   - `data/input/Malayalam/Samhita_Malayalam_corrected.txt` $\rightarrow$ `data/output/Samhita_Malayalam_out.json`
   - `data/input/Malayalam/Samam_Malayalam_Unicode_full.txt`
3. **Curated Collections & Filters**:
   - `data/input/PM-PB_filter.txt` $\rightarrow$ `data/output/Prayogamala-Purvabhagam.json`
   - `data/input/PM-UB_filter.txt` $\rightarrow$ `data/output/prayogamala-Uttarabhagam.json`
   - `data/input/Filter_file_superset.txt` $\rightarrow$ `data/output/Sooktamala.json`

---

## 🚀 4. Step-by-Step Validation Workflow

Whenever refactoring code or modifying pipeline logic, execute the following 5 validation steps:

```bash
# Step 1: Run Automated 7-Point Health Check
python src/tools/run_regression_suite.py
# Validates: 6 Pathas, 59 Khandas, 1226 Samas, Typed AST models, Swara Visarga rules, Tag balance, Versioning, Renderers

# Step 2: Perform End-to-End Golden Replica Verification
python src/tools/baseline.py verify
# Re-runs pipeline from scratch on golden inputs and asserts 100% semantic AST parity against LATEST.json

# Step 3: Check Verse Continuity
python src/tools/check_continuity.py data/output/Vargeekaran.json
# Verifies verse numbers within every section run sequentially (1, 2, 3...) without gaps or duplicates

# Step 4: Verify Domain Metrics Breakdown
python src/generate_json_summary.py
# Confirms exact macro counts across all 6 Pathas and 59 Khandas

# Step 5: Freeze New Baseline Snapshot (After Verified Milestone Changes)
python src/tools/baseline.py create baseline-<date>-<milestone> -d "Description of milestone"
git add data/baselines/
git commit -m "chore: record baseline snapshot <milestone>"
```
