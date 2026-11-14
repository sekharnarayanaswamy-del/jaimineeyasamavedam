---
name: sync_csv_metadata
description: Protocol for syncing Rik and Samam metadata between generated JSON and CSV correction tables.
---

# Sync CSV Metadata Skill

This skill documents the round-trip lifecycle of modifying Vedic metadata (Rishi, Devata, Chandas).

## The Round-Trip Architecture
1. **Extraction**: `generate_granular_table.py` / `generate_rik_table.py` flatten the deeply nested JSON into tabular CSV/Excel formats. 
2. **Key Concept**: The system uses `Global_Rik_Num` as the stable primary key (1..587) to map Ṛk metadata back to verses.
3. **Correction Workflow**: Scholars edit the CSV/Excel files (e.g. `data/output/Rik Reconciliation table (JSV-KSV).xlsx`).
4. **Re-injection & Enrichment**: `src/tools/enrich_ast_rdc.py` reads the reconciliation workbook, injects `rik_rishi`, `rik_devata`, `rik_chandas`, and extracts `saman_rishi`, `saman_devata`, `saman_chandas` directly from `saman_metadata`.

## RDC Population Specification
*   **Ṛk RDC (`rik_rishi`, `rik_devata`, `rik_chandas`)**:
    - Primary source: `data/output/Rik Reconciliation table (JSV-KSV).xlsx`.
    - Fallback: Parsed from raw `rik_metadata` string in the subsection when cell is empty.
    - Format: Scalar string (`str`).
*   **Sāmam RDC (`saman_rishi`, `saman_devata`, `saman_chandas`)**:
    - Primary source: Derived from `saman_metadata` field in each subsection.
    - Format: **JSON array (`List[str]`)** to accurately represent subsections with multiple Sāmam chants:
      ```json
      "saman_rishi": ["वत्सः", "शौनश्शेपः"],
      "saman_devata": ["अग्निः", "अग्निः"],
      "saman_chandas": ["गायत्री", "गायत्री"]
      ```
    - **Sanskrit Pada-cheda (पदच्छेदः)**: Always decompose Sandhi compounds (`गायत्र्यग्निः` $\rightarrow$ `गायत्री`, `अग्निः`) and restore nominative Visargas (`गोतमो` $\rightarrow$ `गोतमः`, `श्रुतर्षिर्` $\rightarrow$ `श्रुतर्षिः`).

## Rules for Agents
*   **Do not hardcode metadata fixes in Python**. 
*   **Fallback Resolution**: If metadata parsing (e.g., splitting a raw string "Rishi: X, Devata: Y, Chandas: Z") fails during extraction, utilize the smart string parser (`parse_metadata_str`) and normalize keys `normalize_key()`.
*   **Array Integrity**: Maintain `saman_rishi`, `saman_devata`, and `saman_chandas` as `List[str]` across AST manipulations.
