---
name: build_curated_collection
description: Guide on using the P.K.S (Parva.Kandah.Samam) identifiers to construct independent custom text collections (Sooktamala).
---

# Build Curated Collection Skill

This skill outlines how to build a new standalone text (Sooktamala/Ritu Shanti Japam, etc) using specific verses from the larger Samhita or Aaranam codebase.

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

## 3. Alternate Workflow
We could also build a new standalone text (Sooktamala/Ritu Shanti Japam, etc) by manually creating a new Unicode text file containing the required collection. This should be done in the same format as for Samhita or Aaranam:  
* Example : `data\input\Sooktam.txt`

Workflow
1. Use `generate_json.py` to generate JSON files from the text files for Samhita or Aaranam: `data\input\Vargeekaran.txt` and `data\input\Aaranam_latest.txt`. 

* Use 2.1 or 2.2 appropriate 

2.1 Use `build_collection.py` to generate a JSON file from the text file for Sooktamala or Ritu Shanti Japam: `data\input\Sooktam.txt`.

2.2 Use `curate_jsv.py` to generate a JSON file from the json files for Samhita or Aaranam: `data\output\Vargeekaran.json` and `data\output\Aaranam_latest.json` and using a filter file `data\input\Ritu-shanti.txt`. If section headers have to be used to build the TOC, then use --toc-level <level> where level is the TOC hierarchy: section (default), subsection, or both. Controls both PDF and HTML TOC.



