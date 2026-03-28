# Complete Pipeline Architecture
## OCR → Analysis → Scholar Review → Integration → Website

---

## Overview: 5-Stage Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           COMPLETE PIPELINE                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  STAGE 1 │    │  STAGE 2 │    │  STAGE 3 │    │  STAGE 4 │    │  STAGE 5 │  │
│  │          │    │          │    │          │    │          │    │          │  │
│  │   OCR    │───►│ ANALYSIS │───►│  SCHOLAR │───►│ INTEGRATE│───►│ WEBSITE  │  │
│  │          │    │          │    │  REVIEW  │    │          │    │          │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                                                                  │
│  External        Python          Browser          Python          Static/       │
│  Process         Scripts         Tool             Scripts         Dynamic       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Stage 1: OCR Processing (External)

**Input**: Scanned PDF/images of manuscripts  
**Output**: Markdown files with JSON content  
**Tool**: External OCR service (e.g., Google Vision, Azure, custom)

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: OCR                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Scanned Images          OCR Service           Raw Output        │
│  ┌─────────────┐        ┌───────────┐        ┌─────────────┐    │
│  │ page_001.png│        │           │        │batch_0001   │    │
│  │ page_002.png│───────►│  External │───────►│  _raw.md    │    │
│  │ page_003.png│        │  OCR API  │        │batch_0002   │    │
│  │    ...      │        │           │        │  _raw.md    │    │
│  │ page_449.png│        │           │        │    ...      │    │
│  └─────────────┘        └───────────┘        └─────────────┘    │
│                                                                  │
│  Output Location: brahmana_XX_images/batch_NNNN_raw.md          │
│                                                                  │
│  Output Format (JSON inside .md):                               │
│  {                                                               │
│    "page_analysis": {                                            │
│      "page_metadata": { "page_number": 1, "anuvaka_info": {...}},│
│      "lyrics_section": { "raw_text": "^1^इषे त्वा^2^..." },     │
│      "commentary_section": { "raw_text": "...", "explanations": }│
│    }                                                             │
│  }                                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Owner**: OCR team / External service  
**Frequency**: Once per book, re-run if quality issues

---

## Stage 2: Analysis & Initial Mapping (Python Scripts)

**Input**: OCR markdown files + TB.json/TA.json base structure  
**Output**: Page mappings, word-to-bhashya mappings, initial issues flagged  
**Tools**: Python analysis scripts

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  STAGE 2: ANALYSIS & MAPPING                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Step 2.1: Convert MD → JSON                                            │    │
│  │  Script: convert_and_extract_commentary.py                              │    │
│  │                                                                          │    │
│  │  batch_0001_raw.md  ───►  batch_0001_raw.json                           │    │
│  │  batch_0002_raw.md  ───►  batch_0002_raw.json                           │    │
│  │       ...                      ...                                       │    │
│  │                                                                          │    │
│  │  Also creates: commentary_index.json, commentary_navigation.csv         │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                               │                                                  │
│                               ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Step 2.2: Build Page-to-Anuvaka Mapping                                │    │
│  │  Script: build_page_mapping.py                                          │    │
│  │                                                                          │    │
│  │  Inputs:  batch_*.json + TB.json.backup (structure)                     │    │
│  │  Output:  page_mapping_prasna1.json                                     │    │
│  │                                                                          │    │
│  │  Logic:                                                                  │    │
│  │  - Pre-scan for Prapaataka boundary markers                             │    │
│  │  - Assign pages to anuvakas within boundaries                           │    │
│  │  - Flag conflicts for review                                            │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                               │                                                  │
│                               ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Step 2.3: Extract Word-to-Bhashya References                           │    │
│  │  Script: build_word_to_bhashya_v2.py                                    │    │
│  │                                                                          │    │
│  │  Inputs:  batch_*.json + page_mapping + TB.json.backup                  │    │
│  │  Output:  word_to_bhashya_prasna1.json                                  │    │
│  │                                                                          │    │
│  │  Logic:                                                                  │    │
│  │  - Extract text BETWEEN ^N^ and ^N+1^ markers                           │    │
│  │  - Match shloka phrases to SamhitaPaata (fuzzy matching)                │    │
│  │  - Pair shloka refs with bhashya refs                                   │    │
│  │  - Flag: shloka_only, bhashya_only, sequence gaps                       │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                               │                                                  │
│                               ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Step 2.4: Generate Initial Review Documents                            │    │
│  │  Script: generate_scholar_review.py                                     │    │
│  │                                                                          │    │
│  │  Outputs:                                                                │    │
│  │  - scholar_review_prasna1.md (detailed issues)                          │    │
│  │  - scholar_checklist_prasna1.txt (prioritized todo)                     │    │
│  │  - reference_validation_report.json (sequence analysis)                 │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  OUTPUTS FROM STAGE 2 (Ready for Scholar Review):                               │
│  ├── page_mapping_prasna1.json         # Which page → which anuvaka            │
│  ├── word_to_bhashya_prasna1.json      # Ref mappings with issues flagged      │
│  ├── scholar_review_prasna1.md         # Human-readable issues report          │
│  └── scholar_checklist_prasna1.txt     # Priority checklist                    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Owner**: Developer / Automated  
**Frequency**: Run after each OCR batch, re-run when mappings need refresh

---

## Stage 3: Scholar Review Tool (Browser-Based)

**Input**: All Stage 2 outputs + original images + base structure  
**Output**: Correction files (scholar_corrections_*.json)  
**Tool**: Web-based Scholar Review Tool

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  STAGE 3: SCHOLAR REVIEW TOOL                                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         TOOL INPUTS                                      │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                          │    │
│  │  From Stage 2:                    From Stage 1:       Base Structure:    │    │
│  │  ┌─────────────────────┐         ┌─────────────┐     ┌─────────────┐    │    │
│  │  │page_mapping_*.json  │         │Original     │     │TB.json      │    │    │
│  │  │word_to_bhashya_*.json│        │Images       │     │TA.json      │    │    │
│  │  │scholar_review_*.md  │         │(.png/.jpg)  │     │             │    │    │
│  │  └─────────────────────┘         └─────────────┘     └─────────────┘    │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                        │                                         │
│                                        ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                    SCHOLAR REVIEW INTERFACE                              │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                          │    │
│  │  ┌──────────────────┐  ┌────────────────────────────────────────────┐   │    │
│  │  │                  │  │  Extracted Text (from OCR)                 │   │    │
│  │  │  Original Image  │  │  ──────────────────────────────────────    │   │    │
│  │  │                  │  │  Lyrics: ^1^इषे त्वा^2^ऊर्जे...            │   │    │
│  │  │  [Zoom] [Pan]    │  │  Commentary: ^1^इषे इति...                 │   │    │
│  │  │                  │  │                                            │   │    │
│  │  │                  │  │  SamhitaPaata Reference:                   │   │    │
│  │  │                  │  │  Panchasat 1.1.1: इषे त्वोर्जे त्वा...     │   │    │
│  │  └──────────────────┘  └────────────────────────────────────────────┘   │    │
│  │                                                                          │    │
│  │  ┌──────────────────────────────────────────────────────────────────┐   │    │
│  │  │  Reference Table (from word_to_bhashya_*.json)                   │   │    │
│  │  │  ─────────────────────────────────────────────────────────────   │   │    │
│  │  │  │Ref│ Shloka        │ Bhashya          │ Match   │ Action     │ │   │    │
│  │  │  │ 1 │ इषे त्वा      │ इषे अन्नाय...    │ ✓ 95%   │            │ │   │    │
│  │  │  │ 2 │ ऊर्जे त्वा    │ [NO BHASHYA]     │ ⚠       │ [Add]      │ │   │    │
│  │  │  │ 3 │ [NO SHLOKA]   │ वायवः स्थेति... │ ?       │ [Add]      │ │   │    │
│  │  │  │11 │ [OCR ERROR]   │ [OCR ERROR]      │ ✗       │ [Remove]   │ │   │    │
│  │  └──────────────────────────────────────────────────────────────────┘   │    │
│  │                                                                          │    │
│  │  ┌──────────────────────────────────────────────────────────────────┐   │    │
│  │  │  Corrections Panel                                               │   │    │
│  │  │  ─────────────────────────────────────────────────────────────   │   │    │
│  │  │  Page Assignment: [Pr1.A3 ▼] (Script assigned: Pr1.A4)          │   │    │
│  │  │  Remove Refs: [11] [12] [+Add]                                   │   │    │
│  │  │  [💾 Save]  [Next Page →]                                        │   │    │
│  │  └──────────────────────────────────────────────────────────────────┘   │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                        │                                         │
│                                        ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         TOOL OUTPUT                                      │    │
│  ├─────────────────────────────────────────────────────────────────────────┤    │
│  │                                                                          │    │
│  │  scholar_corrections_prasna1.json:                                       │    │
│  │  {                                                                       │    │
│  │    "corrections": {                                                      │    │
│  │      "P1.Pr1.A1": {                                                      │    │
│  │        "remove_refs": [11, 12, 13],                                      │    │
│  │        "add_shloka_to_bhashya": [                                        │    │
│  │          {"ref_num": 5, "shloka_phrase": "...", "panchasat": "1.1.2"}   │    │
│  │        ]                                                                 │    │
│  │      },                                                                  │    │
│  │      "P1.Pr1.A2": {                                                      │    │
│  │        "page_reassignment": {                                            │    │
│  │          "pages": [15, 16],                                              │    │
│  │          "from": "P1.Pr1.A3",                                            │    │
│  │          "to": "P1.Pr1.A2"                                               │    │
│  │        }                                                                 │    │
│  │      }                                                                   │    │
│  │    }                                                                     │    │
│  │  }                                                                       │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Owner**: Scholar  
**Frequency**: Iterative - may review same pages multiple times

---

## Stage 4: Post-Correction Integration (Python Scripts)

**Input**: Correction files + Stage 2 outputs + base structure  
**Output**: Fully integrated JSON files  
**Tools**: Python integration scripts

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  STAGE 4: POST-CORRECTION INTEGRATION                                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Step 4.1: Apply Scholar Corrections                                    │    │
│  │  Script: apply_scholar_corrections.py                                   │    │
│  │                                                                          │    │
│  │  Inputs:                                                                 │    │
│  │  - word_to_bhashya_prasna1.json (from Stage 2)                          │    │
│  │  - scholar_corrections_prasna1.json (from Stage 3)                      │    │
│  │                                                                          │    │
│  │  Actions:                                                                │    │
│  │  - Remove invalid references                                            │    │
│  │  - Add shloka phrases to bhashya-only refs                              │    │
│  │  - Add bhashya text to shloka-only refs                                 │    │
│  │  - Mark combined references                                             │    │
│  │  - Update page assignments in mapping                                   │    │
│  │                                                                          │    │
│  │  Output: word_to_bhashya_prasna1.json (UPDATED)                         │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                               │                                                  │
│                               ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Step 4.2: Integrate into TB/TA Structure                               │    │
│  │  Script: integrate_word_to_bhashya.py                                   │    │
│  │                                                                          │    │
│  │  Inputs:                                                                 │    │
│  │  - TB_with_commentary.json (or TB.json.backup)                          │    │
│  │  - word_to_bhashya_prasna1.json (corrected)                             │    │
│  │                                                                          │    │
│  │  Output:                                                                 │    │
│  │  - TB_with_word_bhashya.json                                            │    │
│  │                                                                          │    │
│  │  Structure Added:                                                        │    │
│  │  Anuvakkam: {                                                            │    │
│  │    "bhattabhaskarabhashya": {                                            │    │
│  │      "word_to_bhashya": [                                                │    │
│  │        {"ref_num": 1, "shloka_phrase": "...", "bhashya_text": "..."}    │    │
│  │      ],                                                                  │    │
│  │      "word_to_bhashya_summary": {"matched": 12, "total": 15}            │    │
│  │    }                                                                     │    │
│  │  }                                                                       │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                               │                                                  │
│                               ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Step 4.3: Merge All Prasnas (if multiple)                              │    │
│  │  Script: merge_tb_commentary.py                                         │    │
│  │                                                                          │    │
│  │  Inputs: TB.json from each Prasna directory                             │    │
│  │  Output: TB_with_commentary.json (consolidated)                         │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                               │                                                  │
│                               ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Step 4.4: Generate Web-Optimized Files                                 │    │
│  │  Script: create_web_tb.py                                               │    │
│  │                                                                          │    │
│  │  Outputs:                                                                │    │
│  │  - TB_web.json (smaller, web-friendly)                                  │    │
│  │  - TB_web_with_refs.json (with word_to_bhashya)                         │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  OUTPUTS FROM STAGE 4:                                                          │
│  ├── TB_with_word_bhashya.json    # Full integrated file (~11 MB)              │
│  ├── TB_web_with_refs.json        # Web-optimized (~6 MB)                      │
│  └── TB_with_commentary.json      # All Prasnas merged                         │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Owner**: Developer / Automated  
**Frequency**: Run after each Scholar Review session

---

## Stage 5: Website Generation

**Input**: Integrated JSON files from Stage 4  
**Output**: Static or dynamic website  
**Tools**: Static site generator or web framework

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  STAGE 5: WEBSITE GENERATION                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Option A: Static Site                                                  │    │
│  │                                                                          │    │
│  │  TB_web_with_refs.json  ───►  Static Site Generator  ───►  HTML Files   │    │
│  │                               (e.g., Next.js SSG,                       │    │
│  │                                Hugo, Eleventy)                          │    │
│  │                                                                          │    │
│  │  Hosting: GitHub Pages, Netlify, Vercel, Firebase                       │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Option B: Dynamic Site                                                 │    │
│  │                                                                          │    │
│  │  TB_web_with_refs.json  ───►  Backend API  ───►  Frontend SPA           │    │
│  │                               (Flask/FastAPI)    (React/Vue)            │    │
│  │                                                                          │    │
│  │  Hosting: GCP, AWS, Azure                                               │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Website Features:                                                      │    │
│  │                                                                          │    │
│  │  1. Hierarchical Navigation                                             │    │
│  │     Prasna → Prapaataka → Anuvaka → Panchasat                           │    │
│  │                                                                          │    │
│  │  2. Shloka Display                                                      │    │
│  │     - SamhitaPaata (continuous)                                         │    │
│  │     - PadaPaata (word-by-word)                                          │    │
│  │     - GhanaPatam (if available)                                         │    │
│  │                                                                          │    │
│  │  3. Interactive Commentary                                              │    │
│  │     - Click on shloka phrase → highlight bhashya                        │    │
│  │     - Hover for quick preview                                           │    │
│  │     - Reference numbers shown inline                                    │    │
│  │                                                                          │    │
│  │  4. Search                                                              │    │
│  │     - Full-text search in Sanskrit                                      │    │
│  │     - Search in commentary                                              │    │
│  │                                                                          │    │
│  │  5. Audio Integration (future)                                          │    │
│  │     - Link to audio recitations                                         │    │
│  │     - Synchronized highlighting                                         │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Owner**: Web Developer  
**Frequency**: Deploy after each major content update

---

## Complete Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          END-TO-END DATA FLOW                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  STAGE 1: OCR                                                                    │
│  ─────────────────────────────────────────────────────────────────────────────  │
│  Scanned Images ──────────────────────────────────────────►  batch_*.md         │
│                                                                                  │
│  STAGE 2: ANALYSIS                                                               │
│  ─────────────────────────────────────────────────────────────────────────────  │
│  batch_*.md + TB.json.backup                                                     │
│       │                                                                          │
│       ├──► convert_and_extract_commentary.py ──► batch_*.json                   │
│       │                                               │                          │
│       └──────────────────────────────────────────────┤                          │
│                                                       │                          │
│       ├──► build_page_mapping.py ──────────────────► page_mapping_*.json        │
│       │                                               │                          │
│       └──────────────────────────────────────────────┤                          │
│                                                       │                          │
│       └──► build_word_to_bhashya_v2.py ────────────► word_to_bhashya_*.json     │
│                                                       │                          │
│       └──► generate_scholar_review.py ─────────────► scholar_review_*.md        │
│                                                                                  │
│  STAGE 3: SCHOLAR REVIEW                                                         │
│  ─────────────────────────────────────────────────────────────────────────────  │
│  word_to_bhashya_*.json + images + TB.json                                       │
│       │                                                                          │
│       └──► SCHOLAR REVIEW TOOL ────────────────────► scholar_corrections_*.json │
│                                                                                  │
│  STAGE 4: INTEGRATION                                                            │
│  ─────────────────────────────────────────────────────────────────────────────  │
│  word_to_bhashya_*.json + scholar_corrections_*.json                             │
│       │                                                                          │
│       ├──► apply_scholar_corrections.py ──────────► word_to_bhashya_*.json      │
│       │                                             (UPDATED)                    │
│       │                                               │                          │
│       ├──► integrate_word_to_bhashya.py ──────────► TB_with_word_bhashya.json   │
│       │                                               │                          │
│       ├──► merge_tb_commentary.py ────────────────► TB_with_commentary.json     │
│       │                                               │                          │
│       └──► create_web_tb.py ──────────────────────► TB_web_with_refs.json       │
│                                                                                  │
│  STAGE 5: WEBSITE                                                                │
│  ─────────────────────────────────────────────────────────────────────────────  │
│  TB_web_with_refs.json                                                           │
│       │                                                                          │
│       └──► Site Generator / Web App ──────────────► LIVE WEBSITE                │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## File Inventory

### Input Files (Per Book)
| File | Source | Purpose |
|------|--------|---------|
| `batch_NNNN_raw.md` | OCR | Raw OCR output |
| `TB.json.backup` | Base | Original structure |
| `TA.json.backup` | Base | Original structure |
| `page_NNN.png` | Scans | Original images |

### Intermediate Files (Per Prasna)
| File | Script | Purpose |
|------|--------|---------|
| `batch_NNNN_raw.json` | Stage 2.1 | Converted OCR |
| `commentary_index.json` | Stage 2.1 | Navigation index |
| `page_mapping_prasnaX.json` | Stage 2.2 | Page assignments |
| `word_to_bhashya_prasnaX.json` | Stage 2.3 | Ref mappings |
| `scholar_review_prasnaX.md` | Stage 2.4 | Issues report |
| `scholar_corrections_prasnaX.json` | Stage 3 | Corrections |

### Output Files
| File | Stage | Purpose |
|------|-------|---------|
| `TB_with_word_bhashya.json` | 4 | Full integrated |
| `TB_with_commentary.json` | 4 | All Prasnas merged |
| `TB_web_with_refs.json` | 4 | Web-optimized |

---

## Iteration Workflow

The pipeline supports iterative improvement:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         ITERATIVE WORKFLOW                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Initial Pass:                                                                   │
│  OCR → Analysis → Review (50%) → Integration → Website (v1)                     │
│                                                                                  │
│  Iteration 2:                                                                    │
│  Review (remaining 50%) → Integration → Website (v2)                            │
│                                                                                  │
│  Iteration 3:                                                                    │
│  Review (fix issues from v2) → Integration → Website (v3)                       │
│                                                                                  │
│  OCR Quality Issue Found:                                                        │
│  Re-OCR affected pages → Re-Analysis → Re-Review → Integration → Website        │
│                                                                                  │
│  New Book Added:                                                                 │
│  OCR (new book) → Analysis → Review → Integration (merge) → Website             │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Tool Summary

| Stage | Tool | Type | Status |
|-------|------|------|--------|
| 1 | OCR Service | External | Existing |
| 2.1 | convert_and_extract_commentary.py | Script | ✅ Complete |
| 2.2 | build_page_mapping.py | Script | ✅ Complete |
| 2.3 | build_word_to_bhashya_v2.py | Script | ✅ Complete |
| 2.4 | generate_scholar_review.py | Script | ✅ Complete |
| 3 | **Scholar Review Tool** | Web App | 🔨 To Build |
| 4.1 | apply_scholar_corrections.py | Script | ✅ Complete |
| 4.2 | integrate_word_to_bhashya.py | Script | ✅ Complete |
| 4.3 | merge_tb_commentary.py | Script | ✅ Complete |
| 4.4 | create_web_tb.py | Script | ✅ Complete |
| 5 | Website | Web App | 📋 Planned |

---

## Next Steps

1. **Build Scholar Review Tool (Stage 3)** - The missing piece
2. **Test end-to-end** with Prasna 1 data
3. **Process Prasna 2 and 3** through pipeline
4. **Build Website (Stage 5)** for public access

---

*End of Pipeline Architecture Document*
