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
### Concept 
When tasked to create a custom selection (e.g., "Ritu Shanti Japam"):
1.  **Identify Verses**: Gather the `P.K.S` identifiers from the user (e.g., `1.1.1`, `1.4.2`).
2.  **Use Tools**: Do NOT manually copy-paste JSON. Use the CLI utilities:
    *   `src/tools/build_collection.py` (pulls from a single source JSON like `Vargeekaran.json`).
    *   `src/curate_jsv.py` (pulls and merges from multiple source JSONs).
3.  **Command**: Provide the tool with a `--filter` text file containing the list of IDs.
4.  **Result**: The tool outputs a clean, standalone JSON formatted under a single Supersection and `"सङ्ग्रहः"` (Collection) Section, preserving all inner text, swaras, and footnotes perfectly.
### Pipeline
* Use `curate_jsv.py` to generate a JSON file from the json files for Samhita or Aaranam: `data\output\Vargeekaran.json` and `data\output\Aaranam_latest.json` and using a filter file `data\input\Ritu-shanti.txt`. 

    ``` python src\curate_jsv.py --sources data\output\Vargeekaran.json data\output\Aaranam_latest_out.json --filter data\input\Ritu-shanti.txt --output Ritu-shanti-latest.json```

* If subsection headers have to be used to build the TOC, then use --toc-level <level> where level is the TOC hierarchy: section (default), subsection, or both. Controls both PDF and HTML TOC.

    ``` python src\render_pdf.py Ritu-shanti-japam.json --type collection --toc-level subsection```

## 3. Alternate Workflow
We could also build a new standalone text (Sooktamala/Ritu Shanti Japam, etc) by manually creating a new Unicode text file containing the required collection. This should be done in the same format as for Samhita or Aaranam:  
* Example : `data\input\Sooktam.txt`


#### Pipeline for complex cases (Example): 
1. ``` python src\curate_jsv.py --sources data\output\Vargeekaran.json data\output\Aaranam_latest_out.json data\output\Sooktam_latest.json --filter data\input\Ritu-shanti.txt --output Ritu-shanti-latest.json```
2. ``` python src\tools\renumber_sooktam.py data\output\Ritu-shanti-latest.json```
3. ``` python src\render_pdf.py data\output\Ritu-shanti-latest.json --type collection --toc-level subsection```

Alternately, do the following if you want to add samams to an existing collection by copy/paste:
1. ``` copy data\output\txt\Devanagari\Samam_Devanagari_Unicode.txt data\output\txt\Devanagari\Ritu-shanti-japam.txt```
2. Copy/paste or enter additional samams. e.g. from Sooktam.txt to data\output\txt\Devanagari\Samam_Devanagari_Unicode.txt
3. ``` python src\tools\renumber_sooktam.py data\output\txt\Devanagari\Ritu-shanti-japam.txt```
4. ``` python src\generate_json.py data\output\txt\Devanagari\Ritu-shanti-japam.txt --output Ritu-shanti-japam.json```
5. ``` python src\render_pdf.py Ritu-shanti-japam.json --type collection --toc-level subsection```