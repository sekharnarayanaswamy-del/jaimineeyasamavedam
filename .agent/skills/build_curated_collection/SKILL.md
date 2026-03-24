---
name: build_curated_collection
description: Guide on using the P.K.S (Parva.Kandah.Samam) identifiers to construct independent custom text collections (Sooktamala).
---

# Build Curated Collection Skill

This skill outlines how to build a new standalone text (Sooktamala) using specific verses from the larger Samhita or Aaranam codebase.

## 1. P.K.S Identifiers
*   Every single Samam in the project is identified by a unique tuple: `P.K.S`
    *   **P** = Parva (SuperSection index, e.g., `1` for Agneyam)
    *   **K** = Kandah (Section ordinal index)
    *   **S** = Samam number (Numeric value extracted from Devanagari boundary `॥ N ॥`)

## 2. The Extraction Workflow
When tasked to create a custom selection (e.g., "Ritu Shanti Japam"):
1.  **Identify Verses**: Gather the `P.K.S` identifiers from the user (e.g., `1.1.1`, `1.4.2`).
2.  **Use Tools**: Do NOT manually copy-paste JSON. Use the CLI utilities:
    *   `src/tools/build_collection.py` (pulls from a single source JSON like `Vargeekaran.json`).
    *   `src/curate_jsv.py` (pulls and merges from multiple source JSONs).
3.  **Command**: Provide the tool with a `--filter` text file containing the list of IDs.
4.  **Result**: The tool outputs a clean, standalone JSON formatted under a single Supersection and `"सङ्ग्रहः"` (Collection) Section, preserving all inner text, swaras, and footnotes perfectly.
