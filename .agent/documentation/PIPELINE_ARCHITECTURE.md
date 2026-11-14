# Jaimineeya Samavedam Pipeline Architecture

This document provides a diagrammatic overview of the various workflow pipelines used to process, curate, and publish the Jaimineeya Samavedam text and metadata.

## 1. Core Data Processing Pipeline

This is the primary flow for transforming master text into the canonical AST and downstream publications.

```mermaid
graph TD
    subgraph "Phase 1: Normalization & Pre-flight"
        A1["Master Unicode Text (data/corpora/samhita/01_input/Samhita_Devanagari_Unicode.txt)"] --> B1("renumber_sooktam.py")
        B1 --> C1["Normalized Text"]
    end

    subgraph "Phase 2: Ingestion & Auto-Enrichment"
        C1 --> D1("generate_json.py")
        D2["Reconciliation Excel (.xlsx)"] --> D1
        D1 --> E1["Canonical AST (data/corpora/samhita/02_ast/Samhita_ast.json)<br/>100% Complete with Rik & Samam RDC"]
    end

    subgraph "Phase 3: Tabular Classification Export"
        E1 --> F1("generate_rik_table.py")
        F1 --> G2["Rik Tables (data/corpora/samhita/03_reconciliation/JSV_Rik_Table.csv & .xlsx)"]
    end

    subgraph "Phase 4: Publication"
        E1 --> H1("generate_website.py")
        E1 --> H2("render.py")
        H1 --> I1["Static Websites (docs/...)"]
        H2 --> I2["PDF (LuaLaTeX), HTML & Plaintext"]
    end
```

---

## 2. Collection & Curation Workflow

This secondary pipeline is used to create specific subsets or thematic collections (like Sooktamala or Ashirvachana Samani).

```mermaid
graph LR
    E1["Samhita_ast.json"] --> J1("curate_jsv.py")
    K1["Selection Filter (.txt)"] --> J1
    J1 --> L1["Subset JSON (data/output/..._out.json)"]
    L1 --> M1("generate_website.py")
    M1 --> N1["Collection Site (docs/collection/...)"]
```

---

## 3. Custom Sooktamala Pipeline

For independent collections using the P.K.S (Parva.Kandah.Samam) identifier system.

```mermaid
graph TD
    O1["Structural Index (YAML)"] --> P1("build_curated_collection")
    E1["Samhita_ast.json"] --> P1
    P1 --> Q1["Sooktamala.json"]
    Q1 --> R1("generate_website.py")
    R1 --> S1["Sooktamala Site (docs/collection/sooktamala)"]
```

---

## 4. Prayoga & Procedure Integration

How ritual instructions are embedded into the Samam display.

```mermaid
graph TD
    T1["Prayoga Markdown (.md)"] --> U1("manage_prayoga_procedures")
    V1["Procedure Index (YAML)"] --> W1("generate_json.py")
    W1 --> E1
    E1 -- "Procedure Ref" --> H1
    H1 -- "Embedded Link" --> I1
```

---

## 5. RDC (Ṛṣi, Devatā, Chandas) Population Architecture

The generation pipeline populates two parallel sets of liturgical classifications for each subsection in the AST:

### Ṛk Verse RDC (`rik_rishi`, `rik_devata`, `rik_chandas`)
- **Direct Re-injection**: Injected from the human reconciliation workbook `data/output/Rik Reconciliation table (JSV-KSV).xlsx`.
- **Primary Indexing Key**: Matched via `Global_Rik_Num` (1 to 587 unique Ṛks across 722 subsections).
- **Fallback**: If an Excel cell is unpopulated, falls back to parsing the raw `rik_metadata` string in the subsection.
- **Data Type**: Scalar strings (`str`).

### Sāmam Chant RDC (`saman_rishi`, `saman_devata`, `saman_chandas`)
- **Direct Metadata Extraction**: Derived from each subsection's `saman_metadata` field (e.g. `।। वत्सो गायत्र्यग्निः ।। ।। शौनश्शेपो गायत्र्यग्निः ।।`).
- **Multi-Element Arrays (`List[str]`)**: An Ārṣeyam subsection may contain 1, 2, or 3 Sāmam chants. To maintain exact 1-to-1 fidelity with each chant, the fields are stored as JSON arrays:
  ```json
  "saman_rishi": ["वत्सः", "शौनश्शेपः"],
  "saman_devata": ["अग्निः", "अग्निः"],
  "saman_chandas": ["गायत्री", "गायत्री"]
  ```
- **Sanskrit Sandhi & Pada-cheda (पदच्छेदः)**:
  - Detaches scope prefixes (`द्वयोः`, `द्वयोर्`, `त्रयाणां`).
  - Decomposes Sandhi compounds (e.g., `गायत्र्यग्निः` $\rightarrow$ Chandas: `गायत्री`, Devata: `अग्निः`).
  - Restores nominative Visarga (`गोतमो` $\rightarrow$ `गोतमः`, `श्रुतर्षिर्` $\rightarrow$ `श्रुतर्षिः`, `प्रजापति` $\rightarrow$ `प्रजापतिः`).
  - Inherits parent Ṛk Chandas/Devatā if omitted in a Sāmam clause.

---

## Key Maintenance Commands

| Pipeline | Command Example |
| :--- | :--- |
| **Core AST (Parse & Enrich)** | `python src/generate_json.py --type samhita` |
| **Rik Table Export** | `python src/generate_rik_table.py --type samhita` |
| **Website** | `python src/generate_website.py --samhita` |
| **Curation** | `python src/curate_jsv.py` |
| **PDF** | `python src/render.py data/corpora/samhita/02_ast/Samhita_ast.json -kpully` |
