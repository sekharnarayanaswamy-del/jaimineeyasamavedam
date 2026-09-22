<style>
@page {
    size: A4 landscape;
}
</style>

# PDF / HTML / TXT Generation Log

**Generated:** 21-09-2026  
**Version:** 3.28  
**Branch:** refactor

---

## Devanagari Samhita

| Step | CLI Command | Input | Output |
|------|-------------|-------|--------|
| JSON | `python -X utf8 src/generate_json.py data/baselines/golden/Devanagari/samhita/inputs/Samhita_Devanagari_Unicode.txt --output data/output/Samhita_corrected_out.json --type samhita --input-mode correction` | `data/baselines/golden/Devanagari/samhita/inputs/Samhita_Devanagari_Unicode.txt` | `data/output/Samhita_corrected_out.json` |
| Vargeekaran | `python -X utf8 src/generate_rik_table.py data/output/Samhita_corrected_out.json -o data/output/JSV_Rik_Table.csv -j data/output/Vargeekaran_latest.json` | `Samhita_corrected_out.json` | `Vargeekaran_latest.json`, `JSV_Rik_Table.csv`, `JSV_Rik_Table.xlsx` |
| Combined | `python -X utf8 src/render_pdf.py data/output/Vargeekaran_latest.json --output-mode combined` | `Vargeekaran_latest.json` | `Samhita_Devanagari.pdf`, `Samhita_Devanagari.html`, `Samhita_Devanagari_Unicode.txt` |
| Separate | `python -X utf8 src/render_pdf.py data/output/Vargeekaran_latest.json --output-mode separate` | `Vargeekaran_latest.json` | `Rik_Devanagari.pdf`, `Samam_Devanagari.pdf` + `.html`, `_Unicode.txt` |
| NoMeta | `python -X utf8 src/render_pdf.py data/output/Vargeekaran_latest.json --output-mode nometa` | `Vargeekaran_latest.json` | `Rik_NoMeta_Devanagari.pdf`, `Samam_NoMeta_Devanagari.pdf` + `.html`, `_Unicode.txt` |
| Kpully | `python -X utf8 src/render_pdf.py data/output/Vargeekaran_latest.json -kpully --output-mode combined` | `Vargeekaran_latest.json` | `Samhita_kpully_Devanagari.pdf`, `Samhita_kpully_Devanagari.html`, `Samhita_kpully_Devanagari_Unicode.txt` |

## Devanagari Aaranam

| Step | CLI Command | Input | Output |
|------|-------------|-------|--------|
| JSON | `python -X utf8 src/generate_json.py data/baselines/golden/Devanagari/aaranam/inputs/Aaranam_latest.txt --output data/output/Aaranam_latest_out.json --type aaranam --input-mode correction` | `data/baselines/golden/Devanagari/aaranam/inputs/Aaranam_latest.txt` | `data/output/Aaranam_latest_out.json` |
| Vargeekaran | `python -X utf8 src/generate_rik_table.py --type aaranam -j data/output/Aaranam_vargeekaran.json` | `Aaranam_latest_out.json` | `Aaranam_vargeekaran.json`, `Aaranam_Rik_Table_Baseline.csv`, `Aaranam_Rik_Table_Baseline.xlsx` |
| Combined | `python -X utf8 src/render_pdf.py data/output/Aaranam_vargeekaran.json --type aaranam --output-mode combined` | `Aaranam_vargeekaran.json` | `Aaranam_Devanagari.pdf`, `Aaranam_Devanagari.html`, `Aaranam_Devanagari_Unicode.txt` |
| Separate | `python -X utf8 src/render_pdf.py data/output/Aaranam_vargeekaran.json --type aaranam --output-mode separate` | `Aaranam_vargeekaran.json` | `Aaranam_Rik_Devanagari.pdf`, `Aaranam_Samam_Devanagari.pdf` + `.html`, `_Unicode.txt` |
| NoMeta | `python -X utf8 src/render_pdf.py data/output/Aaranam_vargeekaran.json --type aaranam --output-mode nometa` | `Aaranam_vargeekaran.json` | `Aaranam_Rik_NoMeta_Devanagari.pdf`, `Aaranam_Samam_NoMeta_Devanagari.pdf` + `.html`, `_Unicode.txt` |

## Devanagari Collection

| Step | CLI Command | Input | Output |
|------|-------------|-------|--------|
| Combined | `python -X utf8 src/render_pdf.py data/output/Collection_latest_out.json --type collection --output-mode combined -o Devanagari_collection` | `Collection_latest_out.json` | `Devanagari_collection.pdf`, `Devanagari_collection.html`, `Devanagari_collection_Unicode.txt` |
| Separate | `python -X utf8 src/render_pdf.py data/output/Collection_latest_out.json --type collection --output-mode separate -o Devanagari_collection` | `Collection_latest_out.json` | `Devanagari_collection_Rik.pdf`, `Devanagari_collection_Samam.pdf` + `.html`, `_Unicode.txt` |
| NoMeta | `python -X utf8 src/render_pdf.py data/output/Collection_latest_out.json --type collection --output-mode nometa -o Devanagari_collection` | `Collection_latest_out.json` | `Devanagari_collection_Rik_NoMeta.pdf`, `Devanagari_collection_Samam_NoMeta.pdf` + `.html`, `_Unicode.txt` |

## Malayalam Samam

| Step | CLI Command | Input | Output |
|------|-------------|-------|--------|
| JSON | `python -X utf8 src/generate_json.py data/baselines/golden/Malayalam/input/Samam_Malayalam_Unicode.txt --output Malayalam_JSV/malayalam/Samam_Malayalam_out.json` | `data/baselines/golden/Malayalam/input/Samam_Malayalam_Unicode.txt` | `Samam_Malayalam_out.json` |
| Combined | `python -X utf8 src/render_pdf.py Malayalam_JSV/malayalam/Samam_Malayalam_out.json --script malayalam --output-mode combined -o Samam_Malayalam_Samam` | `Samam_Malayalam_out.json` | `Samam_Malayalam_Samam.pdf`, `Samam_Malayalam_Samam.html`, `Samam_Malayalam_Samam_Unicode.txt` |
| Separate | `python -X utf8 src/render_pdf.py Malayalam_JSV/malayalam/Samam_Malayalam_out.json --script malayalam --output-mode separate -o Samam_Malayalam_Samam` | `Samam_Malayalam_out.json` | `Samam_Malayalam_Samam_Rik.pdf`, `Samam_Malayalam_Samam.pdf` + `.html`, `_Unicode.txt` |
| NoMeta | `python -X utf8 src/render_pdf.py Malayalam_JSV/malayalam/Samam_Malayalam_out.json --script malayalam --output-mode nometa -o Samam_Malayalam_Samam` | `Samam_Malayalam_out.json` | `Samam_Malayalam_Samam_Rik_NoMeta.pdf`, `Samam_Malayalam_Samam_Samam_NoMeta.pdf` + `.html`, `_Unicode.txt` |

## Malayalam Samhita

| Step | CLI Command | Input | Output |
|------|-------------|-------|--------|
| JSON | `python -X utf8 src/generate_json.py data/baselines/golden/Malayalam/input/Samhita_Malayalam_corrected.txt --output data/output/Samhita_Malayalam_out.json` | `data/baselines/golden/Malayalam/input/Samhita_Malayalam_corrected.txt` | `Samhita_Malayalam_out.json` |
| Combined | `python -X utf8 src/render_pdf.py data/output/Samhita_Malayalam_out.json --script malayalam --output-mode combined -o Samhita_Malayalam` | `Samhita_Malayalam_out.json` | `Samhita_Malayalam.pdf`, `Samhita_Malayalam.html`, `Samhita_Malayalam_Unicode.txt` |
| Separate | `python -X utf8 src/render_pdf.py data/output/Samhita_Malayalam_out.json --script malayalam --output-mode separate -o Samhita_Malayalam` | `Samhita_Malayalam_out.json` | `Samhita_Malayalam_Samam.pdf`, `Samhita_Malayalam_Samam.html`, `Samhita_Malayalam_Samam_Unicode.txt` |
| NoMeta | `python -X utf8 src/render_pdf.py data/output/Samhita_Malayalam_out.json --script malayalam --output-mode nometa -o Samhita_Malayalam` | `Samhita_Malayalam_out.json` | `Samhita_Malayalam_Samam_NoMeta.pdf`, `Samhita_Malayalam_Samam_NoMeta.html`, `Samhita_Malayalam_Samam_NoMeta_Unicode.txt` |

## Malayalam Kpully (Devanagari Transliteration)

| Step | CLI Command | Input | Output |
|------|-------------|-------|--------|
| Separate | `python -X utf8 src/render_pdf.py Malayalam_JSV/malayalam/Samam_kpully_Devanagari_json.json --script devanagari -kpully --output-mode separate --samam-only -o Samhita_kpully_Devanagari` | `Samam_kpully_Devanagari_json.json` | `Samhita_kpully_Devanagari_preview.pdf`, `Samhita_kpully_Devanagari.html` |

---

## Output Directory Structure

```
data/output/
├── pdf/
│   ├── Devanagari/
│   │   ├── Samhita_Devanagari.pdf
│   │   ├── Aaranam_Devanagari.pdf
│   │   ├── Rik_Devanagari.pdf
│   │   ├── Samam_Devanagari.pdf
│   │   ├── Rik_NoMeta_Devanagari.pdf
│   │   ├── Samam_NoMeta_Devanagari.pdf
│   │   ├── Samhita_kpully_Devanagari.pdf
│   │   ├── Devanagari_collection.pdf
│   │   ├── Devanagari_collection_Rik.pdf
│   │   ├── Devanagari_collection_Samam.pdf
│   │   ├── Devanagari_collection_Rik_NoMeta.pdf
│   │   └── Devanagari_collection_Samam_NoMeta.pdf
│   └── Malayalam/
│       ├── Samhita_Malayalam.pdf
│       ├── Samam_Malayalam_Samam.pdf
│       ├── Samam_Malayalam_Samam_Rik.pdf
│       ├── Samam_Malayalam_Samam_Samam_NoMeta.pdf
│       ├── Samhita_Malayalam_Samam.pdf
│       └── Samhita_Malayalam_Samam_NoMeta.pdf
├── html/
│   ├── Devanagari/
│   │   ├── Samhita_Devanagari.html
│   │   ├── Aaranam_Devanagari.html
│   │   ├── Rik.html, Samam.html, Rik_NoMeta.html, Samam_NoMeta.html
│   │   ├── Samhita_kpully_Devanagari.html
│   │   ├── Devanagari_collection.html
│   │   ├── Devanagari_collection_Rik.html
│   │   ├── Devanagari_collection_Samam.html
│   │   ├── Devanagari_collection_Rik_NoMeta.html
│   │   └── Devanagari_collection_Samam_NoMeta.html
│   └── Malayalam/
│       ├── Samhita_Malayalam.html
│       ├── Samam_Malayalam_Samam.html
│       ├── Samam_Malayalam_Samam_Rik.html
│       ├── Samam_Malayalam_Samam_Rik_NoMeta.html
│       ├── Samam_Malayalam_Samam_Samam_NoMeta.html
│       ├── Samhita_Malayalam_Samam.html
│       └── Samhita_Malayalam_Samam_NoMeta.html
└── txt/
    ├── Devanagari/
    │   ├── Samhita_Devanagari_Unicode.txt
    │   ├── Aaranam_Devanagari_Unicode.txt
    │   ├── Rik_Devanagari_Unicode.txt
    │   ├── Samam_Devanagari_Unicode.txt
    │   ├── Rik_NoMeta_Devanagari_Unicode.txt
    │   ├── Samam_NoMeta_Devanagari_Unicode.txt
    │   ├── Samhita_kpully_Devanagari_Unicode.txt
    │   ├── Devanagari_collection_Unicode.txt
    │   ├── Devanagari_collection_Rik_Unicode.txt
    │   ├── Devanagari_collection_Samam_Unicode.txt
    │   ├── Devanagari_collection_Rik_NoMeta_Unicode.txt
    │   └── Devanagari_collection_Samam_NoMeta_Unicode.txt
    └── Malayalam/
        ├── Samhita_Malayalam_Unicode.txt
        ├── Samam_Malayalam_Samam_Unicode.txt
        ├── Samam_Malayalam_Samam_Rik_Unicode.txt
        ├── Samam_Malayalam_Samam_Rik_NoMeta_Unicode.txt
        ├── Samam_Malayalam_Samam_Samam_NoMeta_Unicode.txt
        ├── Samhita_Malayalam_Samam_Unicode.txt
        └── Samhita_Malayalam_Samam_NoMeta_Unicode.txt
```
