# Jaimineeya Samavedam Pipeline — Complete Workflows Guide

**Target Scope**: Comprehensive guide to the data transformation pipelines in `jaimineeyasamavedam`.  
**Audience**: Maintainers, editors, and software developers working on liturgical text curation and publication.  
**Companion Documents**: [`VERIFICATION_COOKBOOK.md`](../VERIFICATION_COOKBOOK.md) · [`refactoring_spec.md`](../src/tools/refactoring_spec.md)

---

## 1. Architectural Overview & Workflow Comparison

The Jaimineeya Samavedam (JSV) toolchain operates under two fundamentally different operational models:

1. **The Initial Ingestion Workflow (`--input-mode initial`)**:
   - Used **only when onboarding or bootstrapping** a brand-new corpus from disparate, unaligned raw source files.
   - Merges fragmented text files, separate Rik metadata lists, and Saman lists into a unified initial AST and a single consolidated Unicode markup text.

2. **The Correction & Publishing Workflow (`--input-mode correction`, DEFAULT)**:
   - The **standard day-to-day production workflow** for maintaining and publishing the canonical corpus.
   - Uses a **single master Unicode text file** as the absolute source of truth.
   - Enriches the parsed text with human reconciliation tables and builds all publication targets (static website, XeLaTeX/LuaLaTeX PDFs, Kodunthirapully swara layouts, and plaintext).

```mermaid
graph TD
    subgraph "WORKFLOW 1: INITIAL INGESTION (--input-mode initial)"
        RawText["Raw Vedic Text<br/><i>data/input/vedic_text.txt</i>"]
        RikMeta["Rik Metadata<br/><i>data/input/rishi_devata_chandas_for_rik.txt</i>"]
        SamaMeta["Sama Metadata<br/><i>data/input/sama_rishi_chandas_out.txt</i>"]
        PrayogaIdx["Prayoga Index<br/><i>data/input/prayoga/prayoga_index.yaml</i>"]
        
        RawText --> InitParser["<b>convert_corrections_to_json()</b><br/><i>src/generate_json.py --input-mode initial</i>"]
        RikMeta --> InitParser
        SamaMeta --> InitParser
        PrayogaIdx --> InitParser
        
        InitParser --> InitialAST["Initial AST JSON<br/><i>data/corpora/samhita/02_ast/Samhita_ast.json</i>"]
        InitParser --> ConsolidatedText["<b>Consolidated Master Text</b><br/><i>data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt</i>"]
    end

    subgraph "WORKFLOW 2: UNIFIED PRODUCTION & PUBLISHING (DEFAULT)"
        MasterText["<b>Master Source of Truth</b><br/><i>data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt</i>"]
        --> Preflight["<b>Stage 2: Tag Integrity Pre-flight</b><br/><i>src/tools/renumber_sooktam.py --no-increment --no-renumber</i>"]
        --> UnifiedParser["<b>Stage 3: AST Generation & Auto-Enrichment</b><br/><i>src/generate_json.py --type samhita</i><br/>(Parses text + RDC auto-enrichment)"]
        
        ReconExcel["Human Reconciliation Asset<br/><i>data/output/Rik Reconciliation table (JSV-KSV).xlsx</i>"] --> UnifiedParser
        
        UnifiedParser --> AstJSON["<b>Canonical AST (Samhita_ast.json)</b><br/><i>data/corpora/samhita/02_ast/Samhita_ast.json</i>"]
        
        AstJSON --> ReconEngine["<b>Stage 4: Rik Classification Table Export</b><br/><i>src/generate_rik_table.py --type samhita</i>"]
        ReconEngine --> Tables["<b>Classification Tables</b><br/>JSV_Rik_Table.csv & .xlsx"]
        
        AstJSON --> Audit["<b>Stage 5: Macro Verification & Continuity</b><br/><i>src/generate_json_summary.py</i><br/>(Asserts 6 Pathas, 59 Khandas, 1226 Samas)"]
        
        AstJSON --> SiteGen["<b>Stage 6A: Website Generator</b><br/><i>src/generate_website.py --samhita</i><br/>-> docs/samhita/ (722 Search Items)"]
        AstJSON --> PDFGen["<b>Stage 6B: PDF, HTML & PlainText Renderer</b><br/><i>src/render.py (Combined, -kpully, Separate)</i><br/>-> data/corpora/samhita/05_renders/{pdf,html,txt}/"]
    end
```

---

## 2. Workflow 1: Initial Ingestion Workflow (`--input-mode initial`)

### Purpose
Historically, the Jaimineeya Samavedam materials existed in fragmented, unaligned files: raw text OCR dumps, independent lists of Riks with Rishi/Devata/Chandas, and separate Saman indices. The **Initial Ingestion Workflow** automates the alignment and unification of these independent source assets.

### Input Files Required
| Asset | Default Path | Description |
|---|---|---|
| **Raw Vedic Text** | `data/input/vedic_text.txt` | Unannotated Devanagari verse lines and section delimiters. |
| **Rik Metadata** | `data/input/rishi_devata_chandas_for_rik.txt` | Tabular classification mapping Rik IDs to Rishi, Devata, and Chandas. |
| **Saman Metadata** | `data/input/sama_rishi_chandas_out.txt` | Sequence of Saman names, IDs, and traditional annotations. |
| **Prayoga Linking** | `data/input/prayoga/prayoga_index.yaml` | Hierarchical mapping linking ritual procedure files to Kandas/Samas. |

### Execution Command
```bash
python src/generate_json.py --type samhita --input-mode initial
```

### Internal Processing Steps
1. **`RikMetadataParser`**: Tokenizes multi-attribute lines into structured metadata objects, handling parentheses, ranges, and section overrides.
2. **`RikTextParser`**: Scans the raw Vedic text, identifying section boundaries and mapping isolated verse blocks.
3. **`SamanMetadataParser`**: Correlates the sequential stream of Samans with the underlying Rik text.
4. **`step_preprocess_visarga_accent`**: Corrects Devanagari Unicode combining character order (ensures Halants, Ardhaksharas, and Visargas precede accents).
5. **`extract_closing_mantras`**: Extracts concluding Mangala Shlokas and stamps them into top-level metadata.

### Output Produced
- `data/corpora/samhita/02_ast/Samhita_ast.json`: The assembled Abstract Syntax Tree (AST).
- `data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt`: A single, consolidated Unicode markup text with all headers, subsections, delimiters (`॥ N ॥`), and embedded metadata.

> [!NOTE]
> Once `Samhita_Devanagari_Unicode.txt` is generated, **Workflow 1 is retired for that corpus**. All subsequent editorial and publishing work transitions permanently to **Workflow 2 (Canonical Workflow)**.

---

## 3. Workflow 2: Unified Production & Publishing Workflow (Default)

### Purpose
This is the primary production workflow for the Jaimineeya Samavedam. In this mode, editors edit **one canonical text file** (`data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt`). The pipeline parses this file, automatically merges it with curated reconciliation workbooks, and compiles all downstream publication targets from a single canonical AST (`Samhita_ast.json`).

### Input Files Required
| Asset | Default Path | Nature | Description |
|---|---|---|---|
| **Canonical Source Text** | `data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt` | Single Source of Truth | 836 KB text file with 5,263 lines of structured Vedic markup. |
| **Reconciliation Workbook** | `data/output/Rik Reconciliation table (JSV-KSV).xlsx` | Human Editorial Asset | 587 curated entries mapping JSV Samams to Kauthuma Samaveda (KSV) parallels. |

---

### Step-by-Step Production Pipeline

#### Stage 1: Source Text Curation
Maintainers make corrections directly in `data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt`:
- Correcting Vedic accents: Swarita (`॑` / U+0951), Anudatta (`॒` / U+0952), Kampa (`᳸` / U+1CF8), Trikampa (`३॑`).
- Adjusting verse delimiters: `॥ १ ॥`, `॥ २ ॥`.
- Modifying subsection headers: `# SubSection: ...`.

#### Stage 2: Structural Tag Integrity Pre-flight Check
Before parsing, verify that all structural tags (`# Start of SuperSection`, `# Start of Section`, `# End of SubSection`) are perfectly balanced:
```bash
python src/tools/renumber_sooktam.py data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt --type samhita --no-increment --no-renumber
```
- **Verification Rule**: Must report `Structural Integrity Check...` with **zero tag mismatches** and **zero unclosed tags**.

#### Stage 3: Generate & Auto-Enrich Canonical JSON AST
Parse the unified markup into the formal AST schema and automatically enrich with Ṛk & Sāmam RDC:
```bash
python src/generate_json.py --type samhita
```
- **CLI Options**: `--type samhita` (default), `--output <path>` (optional override).
- **Execution**: Parses structural text and automatically reconciles Ṛk & Sāmam RDC with Sanskrit Pada-cheda.
- **Output**: `data/corpora/samhita/02_ast/Samhita_ast.json` (The single canonical AST, 722 SubSections, 100% RDC coverage).

#### Stage 4: Rik Classification Table Export & Tabular Reconciliation
Generate human-readable and machine-readable tabular exports from the canonical AST:
```bash
python src/generate_rik_table.py --type samhita
```
- **Outputs**:
  - `data/corpora/samhita/03_reconciliation/JSV_Rik_Table.csv`: Tabular export with 587 unique Rik rows.
  - `data/corpora/samhita/03_reconciliation/JSV_Rik_Table.xlsx`: Formatted spreadsheet version.

##### 1. Rik RDC Population (`rik_rishi`, `rik_devata`, `rik_chandas`)
- **Primary Source**: `data/output/Rik Reconciliation table (JSV-KSV).xlsx` (587 curated Rik classifications mapped by scholars).
- **Primary Key**: Sequential `Global_Rik_Num` (1 to 587) assigned across the 722 subsections based on unique `(SuperSection, Section, Rik_ID)` tuples.
- **Fallback Resolution**: If a cell in the reconciliation Excel is blank or unclassified, the pipeline automatically falls back to parsing the raw `rik_metadata` string in the subsection (e.g. `अग्निः । अग्निः । गायत्री` $\rightarrow$ Ṛṣi: `अग्निः`, Devatā: `अग्निः`, Chandas: `गायत्री`).
- **Structured Representation**: Each subsection receives `rik_rishi`, `rik_devata`, and `rik_chandas` as top-level strings, alongside a normalized `rik_classifications` list.

##### 2. Sāmam RDC Population (`saman_rishi`, `saman_devata`, `saman_chandas`)
- **Primary Source**: Derived directly from the `saman_metadata` string in each subsection (e.g., `।। वत्सो गायत्र्यग्निः ।। ।। शौनश्शेपो गायत्र्यग्निः ।।`).
- **Multi-Element Array Data Structure (`List[str]`)**:
  In Jaiminīya Sāmaveda Saṃhitā, an Ārṣeyam subsection can contain one, two, or three distinct Sāmam chants. To preserve 1-to-1 correspondence with each Sāmam chant without loss or flattening, Sāmam RDC fields are structured as **JSON arrays (lists of strings)**:
  ```json
  "saman_rishi": ["वत्सः", "शौनश्शेपः"],
  "saman_devata": ["अग्निः", "अग्निः"],
  "saman_chandas": ["गायत्री", "गायत्री"]
  ```
  For single-chant subsections (669 out of 722), the lists contain a single element:
  ```json
  "saman_rishi": ["गोतमः"],
  "saman_devata": ["अग्निः"],
  "saman_chandas": ["गायत्री"]
  ```
- **Sanskrit Grammatical Pada-cheda (पदच्छेदः)**:
  The raw chant notes in `saman_metadata` follow continuous Vedic Saṃhitā sandhi. The enrichment engine performs automatic linguistic Pada-cheda:
  - **Scope Prefix Detachment**: Strips scope indicators like `द्वयोः`, `द्वयोर्`, `द्वयोरि-` $\rightarrow$ `इ-`, `त्रयाणां`, resolving initial sandhi boundaries.
  - **Compound (Samāsa) Decomposition**: Deconstructs Dvandva/Karmadhāraya compounds like `गायत्र्यग्निः` $\rightarrow$ Chandas `गायत्री`, Devatā `अग्निः`; `विराड्गात्र्यग्निः` $\rightarrow$ Chandas `विराड्गायत्री`, Devatā `अग्निः`; `त्रिष्टुबग्निर्रुद्रः` $\rightarrow$ Chandas `त्रिष्टुप्`, Devatā `अग्निरुद्रौ`. Handles Pūrvarūpa avagraha (`ऽ...`) and Rutva (`र...`) variants.
  - **Visarga Restoration**: Restores nominative singular endings:
    - `-o` $\rightarrow$ `-aḥ` (`गोतमो` $\rightarrow$ `गोतमः`, `भरद्वाजो` $\rightarrow$ `भरद्वाजः`).
    - Halantas in `-r`, `-s`, `-ś`, `-ṣ` $\rightarrow$ `-aḥ` (`श्रुतर्षिर्` $\rightarrow$ `श्रुतर्षिः`, `भरद्वाजस्` $\rightarrow$ `भरद्वाजः`).
    - Stems lacking visarga in raw chant notes (`प्रजापति` $\rightarrow$ `प्रजापतिः`, `अगस्त्य` $\rightarrow$ `अगस्त्यः`).
  - **Inheritance Fallback**: When Chandas or Devatā is not explicitly declared in a Sāmam clause, it defaults to the parent Ṛk's `rik_chandas` or `rik_devata`.

- **Output**:
  - `data/corpora/samhita/02_ast/Samhita_ast.json`: Canonical parsed & enriched AST (100% RDC coverage).

#### Stage 5: Structural Summary & Liturgical Invariant Audit
Audit the generated AST to ensure no verses or chapters were dropped or duplicated:
```bash
# 1. Macro counts across all 6 Pathas and 59 Khandas
python src/generate_json_summary.py

# 2. Sequential continuity check across all 1226 Samas
python src/tools/check_continuity.py data/corpora/samhita/02_ast/Samhita_ast.json
```
- **Mandatory Liturgical Invariants**:
  - **Pathas (SuperSections)**: Exactly **6**
  - **Khandas (Sections)**: Exactly **59**
  - **SubSections**: Exactly **722**
  - **Liturgical Samas**: Exactly **1226**
  - **Continuity**: Zero missing verse numbers, zero duplicate verse numbers.

#### Stage 6: Multi-Target Publishing

##### Target 6A: Static Documentation Website (`docs/samhita/`)
```bash
python src/generate_website.py --samhita
```
- **Outputs**:
  - `docs/samhita/index.html`: Responsive homepage with navigation and Suchi.
  - `docs/samhita/kandah/`: Individual HTML pages for each Khanda.
  - `docs/samhita/search-index.js`: Lunr.js search index containing 722 searchable verse records.
  - `docs/samhita/classification/`: Indices for Rishi, Devata, Chandas, and Anukramanika.
- **Backlog Notice**: An active backlog item tracks reconciling the updated array-structured Sāmam RDC (`List[str]`) with `src/website/models.py`, `src/website/parser.py`, `src/website/generator.py`, and `search-index.js` for all micro-website generation targets.

##### Target 6B: XeLaTeX / LuaLaTeX PDF Publication
```bash
# Standard layout (swara markings below mantra text)
python src/render.py data/corpora/samhita/02_ast/Samhita_ast.json --type samhita --output-mode combined

# Kodunthirapully paddhati (-kpully: swara markings placed directly ABOVE mantra text)
python src/render.py data/corpora/samhita/02_ast/Samhita_ast.json -kpully
```
- **Outputs**:
  - Compiled `.pdf` documents in `data/corpora/samhita/05_renders/pdf/`.
  - Supports `--pdf-color-mode bw` or `color`.

##### Target 6C: PlainText Unicode Export
```bash
python src/render.py data/corpora/samhita/02_ast/Samhita_ast.json --type samhita --output-mode separate
```
- **Outputs**: Clean `.txt` files in `data/corpora/samhita/05_renders/txt/` (Combined, Rik-only, Samam-only, and Nometa).

---

## 4. Building & Verifying the Initial Golden Baseline

To establish rigorous non-regression guarantees, the repository maintains an isolated, frozen **Golden Baseline Anchor**:

### Golden Baseline Directory Hierarchy
```text
data/baselines/golden/
├── samhita/
│   ├── inputs/
│   │   ├── Samhita_corrected.txt                  (836,261 bytes | SHA: 737facc9...)
│   │   └── Rik Reconciliation table (JSV-KSV).xlsx (3,019,400 bytes | SHA: fffb8ca9...)
│   └── outputs/
│       ├── Samhita_corrected_out.json              (1,454,233 bytes | SHA: 3b7af797...)
│       ├── Vargeekaran.json                        (2,003,724 bytes | SHA: cbaaaaf3...)
│       ├── JSV_Rik_Table.csv                       (128,886 bytes   | SHA: 5c82d5fd...)
│       ├── JSV_Structure_Summary.csv               (3,859 bytes     | SHA: bf0c33a2...)
│       └── JSV_Structure_Summary.txt               (6,580 bytes     | SHA: 06119830...)
└── aaranam/
    ├── inputs/
    └── outputs/
```

### Automated Equivalence Verification Tool (`src/tools/verify_golden_equivalence.py`)
Run this single command to prove that the pipeline deterministically reproduces the Golden Baseline:
```bash
python src/tools/verify_golden_equivalence.py
```

#### What It Executes:
1. Spawns an isolated sandbox run using `golden/samhita/inputs/`.
2. Executes `generate_json.py` (Correction Mode).
3. Executes `generate_rik_table.py` with Excel reconciliation.
4. Performs AST node-by-node equivalence tests against `golden/samhita/outputs/`.
5. Performs line-by-line CSV equivalence tests (normalizing volatile metadata headers).
6. Audits all 4 macro invariants (6 Pathas, 59 Khandas, 722 SubSections, 1226 Samas).

#### Verified Output:
```text
======================================================================
  JAIMINEEYA PIPELINE: GOLDEN BASELINE EQUIVALENCE VERIFICATION
======================================================================
Corpus       : Samhita
Input Text   : Samhita_corrected.txt (836,261 bytes)
Recon Excel  : Rik Reconciliation table (JSV-KSV).xlsx (3,019,400 bytes)
----------------------------------------------------------------------
[1/4] Running generate_json.py (Correction Mode)...
      -> AST generated successfully.
[2/4] Running generate_rik_table.py with Excel reconciliation...
      -> Vargeekaran and Rik Table generated successfully.
[3/4] Performing node-by-node AST and data equivalence tests...
      - Samhita AST Equivalence   : [PASS] 100% MATCH
      - Vargeekaran Equivalence   : [PASS] 100% MATCH
      - Rik Table CSV Equivalence : [PASS] 100% MATCH
[4/4] Verifying liturgical invariants...
      - Pathas (SuperSections)    : 6 (Expected: 6) -> [PASS]
      - Khandas (Sections)        : 59 (Expected: 59) -> [PASS]
      - SubSections               : 722 (Expected: 722) -> [PASS]
      - Liturgical Samas          : 1226 (Expected: 1226) -> [PASS]
======================================================================
  OVERALL STATUS: 100% GOLDEN EQUIVALENCE VERIFIED [SUCCESS]
  The pipeline run reproduces the Golden Baseline outputs deterministically.
======================================================================
```

---

## 5. Summary Cheat Sheet for Maintainers

| Task | Command |
|---|---|
| **Quick Health Check** | `python src/tools/run_regression_suite.py` |
| **Golden Baseline Equivalence** | `python src/tools/verify_golden_equivalence.py` |
| **Tag Pre-flight Check** | `python src/tools/renumber_sooktam.py data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt --type samhita --no-increment --no-renumber` |
| **Generate & Enrich Samhita AST** | `python src/generate_json.py --type samhita` |
| **Export Samhita Rik Tables** | `python src/generate_rik_table.py --type samhita` |
| **Check Samhita Continuity** | `python src/tools/check_continuity.py data/corpora/samhita/02_ast/Samhita_ast.json` |
| **Compile Samhita Website** | `python src/generate_website.py --samhita` |
| **Render Samhita PDF (-kpully)** | `python src/render.py data/corpora/samhita/02_ast/Samhita_ast.json -kpully` |
| **Compile Aaranam JSON** | `python src/generate_json.py data/input/Aaranam_latest.txt --type aaranam` |
| **Compile Aaranam Website** | `python src/generate_website.py --aaranam` |

---

## 6. Active Pipeline Backlog

### Backlog Item: Reconcile Array-Structured RDC with Micro-Website Reader & Search
- **Context**: The canonical AST (`Samhita_ast.json`) now carries scalar Ṛk RDC strings and multi-element Sāmam RDC arrays (`List[str]`) with Sanskrit Pada-cheda.
- **Action Required**:
  1. **Website Parser & Data Model**: Update `src/website/models.py` (`saman_rishi`, `saman_devata`, `saman_chandas`) to accept `Union[str, List[str]]` and ensure `src/website/parser.py` maps them directly from `Samhita_ast.json`.
  2. **Micro-Website UI**: Adapt `src/website/formatters.py` and `generator.py` to render both scalar Ṛk metadata and multi-chant Sāmam metadata (e.g. split cards/badges for multi-Sāmam subsections such as `subsection_10`).
  3. **Classification & Search Index**: Update `classification/rishi.html`, `classification/devata.html`, `classification/chandas.html`, and `search-index.js` across all 8 micro-website targets (`samhita`, `aaranam`, `collections`, `kpully-devanagari`, `malayalam`, etc.) to index and query both Ṛk and Sāmam RDC elements.
