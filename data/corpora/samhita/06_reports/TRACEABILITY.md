# Jaimineeya Samavedam — Traceability & Lineage Report: Samhita

- **Corpus**: `samhita`
- **Edition**: `3.41`
- **Generated Timestamp**: `05-11-2026 00:11:02`
- **Validation Status**: `PASSED`

---

## 1. Liturgical Invariants & Metrics
| Metric | Active Count | Baseline Invariant | Status |
| :--- | :--- | :--- | :--- |
| **Pathas (SuperSections)** | 6 | 6 | PASS |
| **Khandas (Sections)** | 59 | 59 | PASS |
| **Samas (Liturgical Chants)** | 1226 | 1226 | PASS |

---

## 2. End-to-End Pipeline Lineage Flowchart
The following diagram illustrates how active master inputs flow through intermediate parsed/canonical ASTs to produce each final render in `05_renders/`:

```mermaid
flowchart TD
    classDef input fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#01579b;
    classDef ast fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#e65100;
    classDef canon fill:#e8f5e9,stroke:#388e3c,stroke-width:2px,color:#1b5e20;
    classDef render fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#4a148c;

    subgraph S1["Stage 01: Master Source Inputs"]
        IN_DEVA["Samhita_Devanagari_Unicode.txt<br/>Standard Devanagari Source"]:::input
        IN_MAL["Samam_Malayalam_Unicode.txt<br/>Kodunthirapully Malayalam Source"]:::input
    end

    subgraph S2["Stage 02 and 04: Intermediate ASTs"]
        AST_DEVA["Samhita_ast.json<br/>Parsed Devanagari AST"]:::ast
        AST_MAL["Samam_Malayalam.json<br/>Parsed Malayalam AST"]:::ast
        AST_KPULLY["Samam_kpully_Devanagari.json<br/>Transliterated KPully AST"]:::ast
        CANON["Vargeekaran.json<br/>Canonical Enriched AST"]:::canon
    end

    subgraph S3["Stage 05: Compiled Renders"]
        R_COMB["Samhita_Devanagari (.html, .pdf, .txt)<br/>Combined Study Edition (Rik and Samam)"]:::render
        R_SEP["Samhita_Rik and Samhita_Samam (.html, .pdf, .txt)<br/>Separate Editions with Metadata"]:::render
        R_NOMETA["Samhita_Rik_NoMeta and Samam_NoMeta (.html, .pdf, .txt)<br/>Continuous Chanting Editions"]:::render
        R_MAL["Samam_kpully_Malayalam (.html, .pdf, .txt)<br/>Kodunthirapully Malayalam Chanting"]:::render
        R_KPULLY["Samam_kpully_Devanagari (.html, .pdf, .txt)<br/>Kodunthirapully Devanagari Chanting"]:::render
    end

    IN_DEVA -->|generate_json.py| AST_DEVA
    AST_DEVA -->|generate_rik_table.py| CANON
    AST_DEVA -->|render.py combined| R_COMB
    AST_DEVA -->|render.py separate| R_SEP
    AST_DEVA -->|render.py nometa| R_NOMETA

    IN_MAL -->|generate_json.py| AST_MAL
    AST_MAL -->|render.py -kpully| R_MAL
    AST_MAL -->|ml_transliterate.py| AST_KPULLY
    AST_KPULLY -->|render.py -kpully| R_KPULLY
```

---

## 3. Direct Output-to-Source Lineage Mapping
This table directly maps each compiled file in `05_renders/` back to the active master source text in `01_input/` and intermediate AST in `02_ast/` that produced it.

| Output Render Artifact | Format | Compiled Timestamp | Purpose / Description | Master Input File (`01_input/`) | Intermediate AST (`02_ast/`) | Pipeline Generation Path |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| [`Samam_kpully_Devanagari.pdf`](../05_renders/pdf/Samam_kpully_Devanagari.pdf) | `PDF` | `22-10-2026 14:33:50` | Kodunthirapully Chanting (Devanagari) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json -> Samam_kpully_Devanagari.json` | `generate_json.py -> ml_transliterate.py -> render.py (-kpully)` |
| [`Samam_kpully_Devanagari_Samam.pdf`](../05_renders/pdf/Samam_kpully_Devanagari_Samam.pdf) | `PDF` | `22-10-2026 14:33:50` | Kodunthirapully Chanting (Devanagari) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json -> Samam_kpully_Devanagari.json` | `generate_json.py -> ml_transliterate.py -> render.py (-kpully)` |
| [`Samam_kpully_Devanagari_Samam_NoMeta.pdf`](../05_renders/pdf/Samam_kpully_Devanagari_Samam_NoMeta.pdf) | `PDF` | `05-11-2026 00:10:56` | Kodunthirapully Chanting (Devanagari) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json -> Samam_kpully_Devanagari.json` | `generate_json.py -> ml_transliterate.py -> render.py (-kpully)` |
| [`Samam_kpully_Malayalam.pdf`](../05_renders/pdf/Samam_kpully_Malayalam.pdf) | `PDF` | `01-10-2026 23:59:01` | Kodunthirapully Chanting (Malayalam) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json` | `generate_json.py -> render.py (-kpully)` |
| [`Samam_kpully_Malayalam_Samam.pdf`](../05_renders/pdf/Samam_kpully_Malayalam_Samam.pdf) | `PDF` | `22-10-2026 13:47:08` | Kodunthirapully Chanting (Malayalam) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json` | `generate_json.py -> render.py (-kpully)` |
| [`Samam_kpully_Malayalam_Samam_NoMeta.pdf`](../05_renders/pdf/Samam_kpully_Malayalam_Samam_NoMeta.pdf) | `PDF` | `05-11-2026 00:10:47` | Kodunthirapully Chanting (Malayalam) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json` | `generate_json.py -> render.py (-kpully)` |
| [`Samam_Malayalam_Samam.pdf`](../05_renders/pdf/Samam_Malayalam_Samam.pdf) | `PDF` | `05-11-2026 00:10:38` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_book_Devanagari.pdf`](../05_renders/pdf/Samhita_book_Devanagari.pdf) | `PDF` | `04-11-2026 22:26:36` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_book_Devanagari_preview.pdf`](../05_renders/pdf/Samhita_book_Devanagari_preview.pdf) | `PDF` | `04-11-2026 22:26:36` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_Devanagari.pdf`](../05_renders/pdf/Samhita_Devanagari.pdf) | `PDF` | `04-11-2026 21:21:22` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_Devanagari_preview.pdf`](../05_renders/pdf/Samhita_Devanagari_preview.pdf) | `PDF` | `04-11-2026 21:21:22` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_kpully_Devanagari.pdf`](../05_renders/pdf/Samhita_kpully_Devanagari.pdf) | `PDF` | `01-10-2026 23:59:01` | Kodunthirapully Chanting (Devanagari) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json -> Samam_kpully_Devanagari.json` | `generate_json.py -> ml_transliterate.py -> render.py (-kpully)` |
| [`Samhita_kpully_Devanagari_Samam.pdf`](../05_renders/pdf/Samhita_kpully_Devanagari_Samam.pdf) | `PDF` | `22-10-2026 13:47:23` | Kodunthirapully Chanting (Devanagari) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json -> Samam_kpully_Devanagari.json` | `generate_json.py -> ml_transliterate.py -> render.py (-kpully)` |
| [`Samhita_Malayalam.pdf`](../05_renders/pdf/Samhita_Malayalam.pdf) | `PDF` | `01-10-2026 23:59:01` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_Rik_Devanagari.pdf`](../05_renders/pdf/Samhita_Rik_Devanagari.pdf) | `PDF` | `01-10-2026 23:59:01` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_Rik_NoMeta_Devanagari.pdf`](../05_renders/pdf/Samhita_Rik_NoMeta_Devanagari.pdf) | `PDF` | `01-10-2026 23:59:01` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_Samam_Devanagari.pdf`](../05_renders/pdf/Samhita_Samam_Devanagari.pdf) | `PDF` | `01-10-2026 23:59:01` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_Samam_NoMeta_Devanagari.pdf`](../05_renders/pdf/Samhita_Samam_NoMeta_Devanagari.pdf) | `PDF` | `01-10-2026 23:59:01` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samam_kpully_Devanagari.html`](../05_renders/html/Samam_kpully_Devanagari.html) | `HTML` | `22-10-2026 14:33:51` | Kodunthirapully Chanting (Devanagari) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json -> Samam_kpully_Devanagari.json` | `generate_json.py -> ml_transliterate.py -> render.py (-kpully)` |
| [`Samam_kpully_Devanagari_Samam.html`](../05_renders/html/Samam_kpully_Devanagari_Samam.html) | `HTML` | `22-10-2026 15:40:00` | Kodunthirapully Chanting (Devanagari) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json -> Samam_kpully_Devanagari.json` | `generate_json.py -> ml_transliterate.py -> render.py (-kpully)` |
| [`Samam_kpully_Devanagari_Samam_NoMeta.html`](../05_renders/html/Samam_kpully_Devanagari_Samam_NoMeta.html) | `HTML` | `05-11-2026 00:10:56` | Kodunthirapully Chanting (Devanagari) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json -> Samam_kpully_Devanagari.json` | `generate_json.py -> ml_transliterate.py -> render.py (-kpully)` |
| [`Samam_kpully_Malayalam.html`](../05_renders/html/Samam_kpully_Malayalam.html) | `HTML` | `13-10-2026 12:27:05` | Kodunthirapully Chanting (Malayalam) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json` | `generate_json.py -> render.py (-kpully)` |
| [`Samam_kpully_Malayalam_Samam.html`](../05_renders/html/Samam_kpully_Malayalam_Samam.html) | `HTML` | `22-10-2026 16:25:48` | Kodunthirapully Chanting (Malayalam) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json` | `generate_json.py -> render.py (-kpully)` |
| [`Samam_kpully_Malayalam_Samam_NoMeta.html`](../05_renders/html/Samam_kpully_Malayalam_Samam_NoMeta.html) | `HTML` | `05-11-2026 00:10:48` | Kodunthirapully Chanting (Malayalam) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json` | `generate_json.py -> render.py (-kpully)` |
| [`Samam_Malayalam_Samam.html`](../05_renders/html/Samam_Malayalam_Samam.html) | `HTML` | `05-11-2026 00:10:39` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_Devanagari.html`](../05_renders/html/Samhita_Devanagari.html) | `HTML` | `04-11-2026 19:17:50` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_kpully_Devanagari.html`](../05_renders/html/Samhita_kpully_Devanagari.html) | `HTML` | `13-10-2026 12:27:06` | Kodunthirapully Chanting (Devanagari) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json -> Samam_kpully_Devanagari.json` | `generate_json.py -> ml_transliterate.py -> render.py (-kpully)` |
| [`Samhita_kpully_Devanagari_Samam.html`](../05_renders/html/Samhita_kpully_Devanagari_Samam.html) | `HTML` | `22-10-2026 13:47:23` | Kodunthirapully Chanting (Devanagari) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json -> Samam_kpully_Devanagari.json` | `generate_json.py -> ml_transliterate.py -> render.py (-kpully)` |
| [`Samhita_Malayalam.html`](../05_renders/html/Samhita_Malayalam.html) | `HTML` | `22-10-2026 16:43:30` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_Rik_Devanagari.html`](../05_renders/html/Samhita_Rik_Devanagari.html) | `HTML` | `22-10-2026 15:45:01` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_Rik_NoMeta_Devanagari.html`](../05_renders/html/Samhita_Rik_NoMeta_Devanagari.html) | `HTML` | `22-10-2026 15:45:04` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_Samam_Devanagari.html`](../05_renders/html/Samhita_Samam_Devanagari.html) | `HTML` | `22-10-2026 15:45:03` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_Samam_NoMeta_Devanagari.html`](../05_renders/html/Samhita_Samam_NoMeta_Devanagari.html) | `HTML` | `22-10-2026 15:45:05` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samam_kpully_Devanagari_Samam_NoMeta_Unicode.txt`](../05_renders/txt/Samam_kpully_Devanagari_Samam_NoMeta_Unicode.txt) | `TXT` | `05-11-2026 00:10:56` | Kodunthirapully Chanting (Devanagari) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json -> Samam_kpully_Devanagari.json` | `generate_json.py -> ml_transliterate.py -> render.py (-kpully)` |
| [`Samam_kpully_Devanagari_Samam_Unicode.txt`](../05_renders/txt/Samam_kpully_Devanagari_Samam_Unicode.txt) | `TXT` | `22-10-2026 15:40:00` | Kodunthirapully Chanting (Devanagari) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json -> Samam_kpully_Devanagari.json` | `generate_json.py -> ml_transliterate.py -> render.py (-kpully)` |
| [`Samam_kpully_Devanagari_Unicode.txt`](../05_renders/txt/Samam_kpully_Devanagari_Unicode.txt) | `TXT` | `22-10-2026 14:33:50` | Kodunthirapully Chanting (Devanagari) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json -> Samam_kpully_Devanagari.json` | `generate_json.py -> ml_transliterate.py -> render.py (-kpully)` |
| [`Samam_kpully_Malayalam_Devanagari_Unicode.txt`](../05_renders/txt/Samam_kpully_Malayalam_Devanagari_Unicode.txt) | `TXT` | `01-10-2026 23:59:01` | Kodunthirapully Chanting (Malayalam) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json` | `generate_json.py -> render.py (-kpully)` |
| [`Samam_kpully_Malayalam_Samam_Devanagari_Unicode.txt`](../05_renders/txt/Samam_kpully_Malayalam_Samam_Devanagari_Unicode.txt) | `TXT` | `22-10-2026 15:39:56` | Kodunthirapully Chanting (Malayalam) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json` | `generate_json.py -> render.py (-kpully)` |
| [`Samam_kpully_Malayalam_Samam_NoMeta_Devanagari_Unicode.txt`](../05_renders/txt/Samam_kpully_Malayalam_Samam_NoMeta_Devanagari_Unicode.txt) | `TXT` | `05-11-2026 00:10:47` | Kodunthirapully Chanting (Malayalam) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json` | `generate_json.py -> render.py (-kpully)` |
| [`Samam_kpully_Malayalam_Samam_NoMeta_Unicode.txt`](../05_renders/txt/Samam_kpully_Malayalam_Samam_NoMeta_Unicode.txt) | `TXT` | `05-11-2026 00:10:47` | Kodunthirapully Chanting (Malayalam) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json` | `generate_json.py -> render.py (-kpully)` |
| [`Samam_kpully_Malayalam_Samam_Unicode.txt`](../05_renders/txt/Samam_kpully_Malayalam_Samam_Unicode.txt) | `TXT` | `22-10-2026 16:25:48` | Kodunthirapully Chanting (Malayalam) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json` | `generate_json.py -> render.py (-kpully)` |
| [`Samam_kpully_Malayalam_Unicode.txt`](../05_renders/txt/Samam_kpully_Malayalam_Unicode.txt) | `TXT` | `01-10-2026 23:59:01` | Kodunthirapully Chanting (Malayalam) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json` | `generate_json.py -> render.py (-kpully)` |
| [`Samam_Malayalam_Samam_Devanagari_Unicode.txt`](../05_renders/txt/Samam_Malayalam_Samam_Devanagari_Unicode.txt) | `TXT` | `05-11-2026 00:10:39` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samam_Malayalam_Samam_Unicode.txt`](../05_renders/txt/Samam_Malayalam_Samam_Unicode.txt) | `TXT` | `05-11-2026 00:10:38` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_Devanagari_Unicode.txt`](../05_renders/txt/Samhita_Devanagari_Unicode.txt) | `TXT` | `04-11-2026 14:41:56` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_Devanagari_Unicode_with FN.txt`](../05_renders/txt/Samhita_Devanagari_Unicode_with FN.txt) | `TXT` | `04-11-2026 13:27:43` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_kpully_Devanagari_Samam_Unicode.txt`](../05_renders/txt/Samhita_kpully_Devanagari_Samam_Unicode.txt) | `TXT` | `22-10-2026 13:47:23` | Kodunthirapully Chanting (Devanagari) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json -> Samam_kpully_Devanagari.json` | `generate_json.py -> ml_transliterate.py -> render.py (-kpully)` |
| [`Samhita_kpully_Devanagari_Unicode.txt`](../05_renders/txt/Samhita_kpully_Devanagari_Unicode.txt) | `TXT` | `01-10-2026 23:59:01` | Kodunthirapully Chanting (Devanagari) | [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | `Samam_Malayalam.json -> Samam_kpully_Devanagari.json` | `generate_json.py -> ml_transliterate.py -> render.py (-kpully)` |
| [`Samhita_Malayalam_Devanagari_Unicode.txt`](../05_renders/txt/Samhita_Malayalam_Devanagari_Unicode.txt) | `TXT` | `22-10-2026 16:43:29` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_Malayalam_Unicode.txt`](../05_renders/txt/Samhita_Malayalam_Unicode.txt) | `TXT` | `22-10-2026 16:43:29` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_Rik_Devanagari_Unicode.txt`](../05_renders/txt/Samhita_Rik_Devanagari_Unicode.txt) | `TXT` | `22-10-2026 15:45:01` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_Rik_NoMeta_Devanagari_Unicode.txt`](../05_renders/txt/Samhita_Rik_NoMeta_Devanagari_Unicode.txt) | `TXT` | `22-10-2026 15:45:04` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_Samam_Devanagari_Unicode.txt`](../05_renders/txt/Samhita_Samam_Devanagari_Unicode.txt) | `TXT` | `22-10-2026 15:45:02` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |
| [`Samhita_Samam_NoMeta_Devanagari_Unicode.txt`](../05_renders/txt/Samhita_Samam_NoMeta_Devanagari_Unicode.txt) | `TXT` | `22-10-2026 15:45:04` | Standard Samhita Text | [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | `Samhita_ast.json (Canonical: Vargeekaran.json)` | `generate_json.py -> render.py` |

---

## 4. Active Master Inputs (`01_input/`)
Only the active master source files utilized for pipeline generation are listed below:

| Active Input File | Size | SHA-256 Checksum |
| :--- | :--- | :--- |
| [`Samam_Malayalam_Unicode.txt`](../01_input/Samam_Malayalam_Unicode.txt) | 34.9 KB | `d77551cdfd6c8fd7a33ee0678f6c7b79e2e3afeb1dcab0a7f2067283f3ecf18f` |
| [`Samhita_Devanagari_Unicode.txt`](../01_input/Samhita_Devanagari_Unicode.txt) | 1.30 MB | `cc966727b94941cb9ec8fd7b04fd1c9b4e4854629ba9f51f3233cc33b955f76c` |

---

## 5. Intermediate ASTs & Canonical Datasets

### Parsed ASTs (`02_ast/`)
| AST File | Size | SHA-256 Checksum |
| :--- | :--- | :--- |
| [`Samam_kpully_Devanagari.json`](../02_ast/Samam_kpully_Devanagari.json) | 52.0 KB | `1f9b8d92c93b8d5bab712a17f4269c14af1e8547539ff01a0c4037ea34a4674a` |
| [`Samam_Malayalam.json`](../02_ast/Samam_Malayalam.json) | 66.0 KB | `f258b084562a24d1ef1a25b801cd38fe1237effd48732aceb32afb474a545c69` |
| [`Samhita_ast.json`](../02_ast/Samhita_ast.json) | 1.63 MB | `d664e2632c5f5bcadf8e530e80a4ed07d8061bed32dafff3d132bed2a429e5cc` |

### Canonical Datasets (`04_canonical/`)
| Canonical File | Size | SHA-256 Checksum |
| :--- | :--- | :--- |
| [`Vargeekaran.json`](../04_canonical/Vargeekaran.json) | 2.10 MB | `2f9477b963e415d71f27e78bf5660858306522283b4d638577aea7cbe9e3186f` |

### Reconciliation Tables (`03_reconciliation/`)
| File Name | Size |
| :--- | :--- |
| [`JSV_Rik_Table - for analysis.xlsx`](../03_reconciliation/JSV_Rik_Table - for analysis.xlsx) | 232.6 KB |
| [`JSV_Rik_Table.csv`](../03_reconciliation/JSV_Rik_Table.csv) | 275.4 KB |
| [`JSV_Rik_Table.txt`](../03_reconciliation/JSV_Rik_Table.txt) | 203.4 KB |
| [`JSV_Rik_Table.xlsx`](../03_reconciliation/JSV_Rik_Table.xlsx) | 93.2 KB |
| [`JSV_Samam_Granular_Table.csv`](../03_reconciliation/JSV_Samam_Granular_Table.csv) | 830.0 KB |
| [`JSV_Samam_Granular_Table.xlsx`](../03_reconciliation/JSV_Samam_Granular_Table.xlsx) | 130.7 KB |
| [`Rik Reconciliation table (JSV-KSV).xlsx`](../03_reconciliation/Rik Reconciliation table (JSV-KSV).xlsx) | 2.88 MB |

---

## 6. Compiled Render Catalog (`05_renders/`)

### PDF Documents (`05_renders/pdf/`)
| File Name | Mode / Edition | Target Script | Size | SHA-256 Checksum |
| :--- | :--- | :--- | :--- | :--- |
| [`Samam_kpully_Devanagari.pdf`](../05_renders/pdf/Samam_kpully_Devanagari.pdf) | Separate (Samam Only) | Devanagari (Kodunthirapully) | 111.3 KB | `2f7d3d5f7360a015c72a1598a360d7368c1f95991d676f1fd35264cdf78f2313` |
| [`Samam_kpully_Devanagari_Samam.pdf`](../05_renders/pdf/Samam_kpully_Devanagari_Samam.pdf) | Separate (Samam Only) | Devanagari (Kodunthirapully) | 111.3 KB | `2f7d3d5f7360a015c72a1598a360d7368c1f95991d676f1fd35264cdf78f2313` |
| [`Samam_kpully_Devanagari_Samam_NoMeta.pdf`](../05_renders/pdf/Samam_kpully_Devanagari_Samam_NoMeta.pdf) | NoMeta (Continuous Chanting) | Devanagari (Kodunthirapully) | 129.2 KB | `8ddb3dd924573a90372e4f4aee458002885221781703f7336102a4d3ea9ced79` |
| [`Samam_kpully_Malayalam.pdf`](../05_renders/pdf/Samam_kpully_Malayalam.pdf) | Separate (Samam Only) | Malayalam | 85.6 KB | `75ee383a9dbb09d2cdcb755a28b7dd0e4408b9c2bf3acdf5bd2fba2236176386` |
| [`Samam_kpully_Malayalam_Samam.pdf`](../05_renders/pdf/Samam_kpully_Malayalam_Samam.pdf) | Separate (Samam Only) | Malayalam | 86.0 KB | `758ec28e3d86b788372eb8bd0cc36e97594aec7dac5ae9a350dac0e4eb1270f6` |
| [`Samam_kpully_Malayalam_Samam_NoMeta.pdf`](../05_renders/pdf/Samam_kpully_Malayalam_Samam_NoMeta.pdf) | NoMeta (Continuous Chanting) | Malayalam | 90.7 KB | `2ef67ceea640b34a413f23b271cdb30c79bf37d908ff5e6f49fbff795ee4af5c` |
| [`Samam_Malayalam_Samam.pdf`](../05_renders/pdf/Samam_Malayalam_Samam.pdf) | Separate (Samam Only) | Malayalam | 89.7 KB | `b6ca0d8cac2b5ec64400ffc9ff852a53570cc914dda2ba617c1ba0a370f0964c` |
| [`Samhita_book_Devanagari.pdf`](../05_renders/pdf/Samhita_book_Devanagari.pdf) | Combined (Study Edition) | Devanagari (Standard) | 1.86 MB | `75929dff4545e5a6b95ecdfaac0db10fccea3cf20bcb40b8aeb374adf01bde0f` |
| [`Samhita_book_Devanagari_preview.pdf`](../05_renders/pdf/Samhita_book_Devanagari_preview.pdf) | Combined (Study Edition) | Devanagari (Standard) | 1.86 MB | `75929dff4545e5a6b95ecdfaac0db10fccea3cf20bcb40b8aeb374adf01bde0f` |
| [`Samhita_Devanagari.pdf`](../05_renders/pdf/Samhita_Devanagari.pdf) | Combined (Study Edition) | Devanagari (Standard) | 1.55 MB | `b4cea45844522374bb5eab8007fbcc4bbd60660835686c869eb4dfd2bf0cbb00` |
| [`Samhita_Devanagari_preview.pdf`](../05_renders/pdf/Samhita_Devanagari_preview.pdf) | Combined (Study Edition) | Devanagari (Standard) | 1.55 MB | `b4cea45844522374bb5eab8007fbcc4bbd60660835686c869eb4dfd2bf0cbb00` |
| [`Samhita_kpully_Devanagari.pdf`](../05_renders/pdf/Samhita_kpully_Devanagari.pdf) | Combined (Study Edition) | Devanagari (Kodunthirapully) | 110.3 KB | `ff12a87022de8232ce094893184cf74183c695217e7ace27071f5c607e01faf7` |
| [`Samhita_kpully_Devanagari_Samam.pdf`](../05_renders/pdf/Samhita_kpully_Devanagari_Samam.pdf) | Combined (Study Edition) | Devanagari (Kodunthirapully) | 111.3 KB | `93e48f81fb936e5aded7cd95f8ce0051f51c7d9cd3851589a9860a03d646625c` |
| [`Samhita_Malayalam.pdf`](../05_renders/pdf/Samhita_Malayalam.pdf) | Combined (Study Edition) | Malayalam | 1.16 MB | `2b0cdc46cdba0b8e88c35934264b6be7e60ab98641ffc7d148fcb8e23e7bc615` |
| [`Samhita_Rik_Devanagari.pdf`](../05_renders/pdf/Samhita_Rik_Devanagari.pdf) | Combined (Study Edition) | Devanagari (Standard) | 292.2 KB | `c6cc143e730ba4f51d213636eb19461ddc69b16d1968307f8ee0a76264f7024c` |
| [`Samhita_Rik_NoMeta_Devanagari.pdf`](../05_renders/pdf/Samhita_Rik_NoMeta_Devanagari.pdf) | NoMeta (Continuous Chanting) | Devanagari (Standard) | 247.1 KB | `cd8233161739fabfe1655b25e9e03ce376b6da2880e82ceb92bf740a47466833` |
| [`Samhita_Samam_Devanagari.pdf`](../05_renders/pdf/Samhita_Samam_Devanagari.pdf) | Combined (Study Edition) | Devanagari (Standard) | 877.7 KB | `6b59301ed7ffd0278295e847a715ce1eee0e8678409c723c99ca185fdf53ddf3` |
| [`Samhita_Samam_NoMeta_Devanagari.pdf`](../05_renders/pdf/Samhita_Samam_NoMeta_Devanagari.pdf) | NoMeta (Continuous Chanting) | Devanagari (Standard) | 845.3 KB | `1d527fada63117071b42b518cb25494e2fb2dee7d402dc32d6dd29ea353cd2d5` |

### HTML Readers (`05_renders/html/`)
| File Name | Mode / Edition | Target Script | Size | SHA-256 Checksum |
| :--- | :--- | :--- | :--- | :--- |
| [`Samam_kpully_Devanagari.html`](../05_renders/html/Samam_kpully_Devanagari.html) | Separate (Samam Only) | Devanagari (Kodunthirapully) | 2.90 MB | `8cd94bb530d29357eda90dc952607452ea22556be0a0c166002e8803a90480d8` |
| [`Samam_kpully_Devanagari_Samam.html`](../05_renders/html/Samam_kpully_Devanagari_Samam.html) | Separate (Samam Only) | Devanagari (Kodunthirapully) | 2.90 MB | `3af9562cee1b821cd6c41bd08468a5cca45433013c03c741aa92c0ea8326a34f` |
| [`Samam_kpully_Devanagari_Samam_NoMeta.html`](../05_renders/html/Samam_kpully_Devanagari_Samam_NoMeta.html) | NoMeta (Continuous Chanting) | Devanagari (Kodunthirapully) | 2.90 MB | `111b07288d71d44308ad5f1f773b2b737e830eca20ad3d28f8f94aabdd68ec8f` |
| [`Samam_kpully_Malayalam.html`](../05_renders/html/Samam_kpully_Malayalam.html) | Separate (Samam Only) | Malayalam | 1.23 MB | `4aad3e687a26955e67d33d3a73a7955290537e4a6f86cc4e229f996196ad5bc7` |
| [`Samam_kpully_Malayalam_Samam.html`](../05_renders/html/Samam_kpully_Malayalam_Samam.html) | Separate (Samam Only) | Malayalam | 1.23 MB | `a45206dfa8b66925ba13ec36578a1da35297a096c508610dbdb34048b04b3a0c` |
| [`Samam_kpully_Malayalam_Samam_NoMeta.html`](../05_renders/html/Samam_kpully_Malayalam_Samam_NoMeta.html) | NoMeta (Continuous Chanting) | Malayalam | 1.23 MB | `b532f7eed8ec09f90428c2544cddc832ea10ee83fa2851a8f592e7c77ab65712` |
| [`Samam_Malayalam_Samam.html`](../05_renders/html/Samam_Malayalam_Samam.html) | Separate (Samam Only) | Malayalam | 1.23 MB | `73d548aa454f3c93af4693541700801061ec8a06dd3bbaab952c2ba6610e23a9` |
| [`Samhita_Devanagari.html`](../05_renders/html/Samhita_Devanagari.html) | Combined (Study Edition) | Devanagari (Standard) | 11.64 MB | `50fd0315caa7545eced82ff4191854ce92bbf5da120d86827667873843c08fd7` |
| [`Samhita_kpully_Devanagari.html`](../05_renders/html/Samhita_kpully_Devanagari.html) | Combined (Study Edition) | Devanagari (Kodunthirapully) | 11.84 MB | `599ef446d29485550fbfc5b5a30afb9c5e60cc8246558a0489e6eb16c4c95207` |
| [`Samhita_kpully_Devanagari_Samam.html`](../05_renders/html/Samhita_kpully_Devanagari_Samam.html) | Combined (Study Edition) | Devanagari (Kodunthirapully) | 2.90 MB | `8d040fee7b234e2841b0bb401d7f714f5c5a221e589ea50712cda0e77a4f0fa3` |
| [`Samhita_Malayalam.html`](../05_renders/html/Samhita_Malayalam.html) | Combined (Study Edition) | Malayalam | 1.23 MB | `3b9a95bb29a42bdd55a90b34830759e84332ec1c9de2d3feeb608ca0a63dd0c0` |
| [`Samhita_Rik_Devanagari.html`](../05_renders/html/Samhita_Rik_Devanagari.html) | Combined (Study Edition) | Devanagari (Standard) | 3.77 MB | `f335088e3a5bdafeb84e157f1c779718af3c805a60af25155588659942e169aa` |
| [`Samhita_Rik_NoMeta_Devanagari.html`](../05_renders/html/Samhita_Rik_NoMeta_Devanagari.html) | NoMeta (Continuous Chanting) | Devanagari (Standard) | 3.65 MB | `4f77a9e68a77a2bb221051b8ae9f7b8e413137a0927517508697217db08cdd23` |
| [`Samhita_Samam_Devanagari.html`](../05_renders/html/Samhita_Samam_Devanagari.html) | Combined (Study Edition) | Devanagari (Standard) | 10.93 MB | `b0d0af29bc28c4831dc7abc26ad83e6a9d2c979ed1421ff2534d4aad481f1d00` |
| [`Samhita_Samam_NoMeta_Devanagari.html`](../05_renders/html/Samhita_Samam_NoMeta_Devanagari.html) | NoMeta (Continuous Chanting) | Devanagari (Standard) | 10.80 MB | `b8fea04b8dbed31f53539c2d12c11687826b9f7f257b87c1ce4880253aa95287` |

### PlainText Exports (`05_renders/txt/`)
| File Name | Mode / Edition | Target Script | Size | SHA-256 Checksum |
| :--- | :--- | :--- | :--- | :--- |
| [`Samam_kpully_Devanagari_Samam_NoMeta_Unicode.txt`](../05_renders/txt/Samam_kpully_Devanagari_Samam_NoMeta_Unicode.txt) | NoMeta (Continuous Chanting) | Devanagari (Kodunthirapully) | 33.6 KB | `d1d5b915d8d046aa143ccdb8af349f8bc7806693eecb2013ba3b70afa69d87af` |
| [`Samam_kpully_Devanagari_Samam_Unicode.txt`](../05_renders/txt/Samam_kpully_Devanagari_Samam_Unicode.txt) | Separate (Samam Only) | Devanagari (Kodunthirapully) | 33.7 KB | `c8bbd096c1b1eb6aaf5c7f0903344b4116e6d34cef9048337ad575424c5f2286` |
| [`Samam_kpully_Devanagari_Unicode.txt`](../05_renders/txt/Samam_kpully_Devanagari_Unicode.txt) | Separate (Samam Only) | Devanagari (Kodunthirapully) | 33.7 KB | `9ed2b744564a7b0816acb681f56422ec310a254d5c4a20b12a77b08ce82e4ca2` |
| [`Samam_kpully_Malayalam_Devanagari_Unicode.txt`](../05_renders/txt/Samam_kpully_Malayalam_Devanagari_Unicode.txt) | Separate (Samam Only) | Malayalam | 33.5 KB | `4e5d03dba92470f578e4f049877708ee0d034fe8f81a898d73e83058e3817bf2` |
| [`Samam_kpully_Malayalam_Samam_Devanagari_Unicode.txt`](../05_renders/txt/Samam_kpully_Malayalam_Samam_Devanagari_Unicode.txt) | Separate (Samam Only) | Malayalam | 33.5 KB | `0fc24e23c5cc19835eff7f1af0cccc40657eaeecfceb172f1dd19fadc66a3227` |
| [`Samam_kpully_Malayalam_Samam_NoMeta_Devanagari_Unicode.txt`](../05_renders/txt/Samam_kpully_Malayalam_Samam_NoMeta_Devanagari_Unicode.txt) | NoMeta (Continuous Chanting) | Malayalam | 33.5 KB | `e7414ba92aaa3445bc5d950ecff9c09e304261b061855697a4fb5b510f355277` |
| [`Samam_kpully_Malayalam_Samam_NoMeta_Unicode.txt`](../05_renders/txt/Samam_kpully_Malayalam_Samam_NoMeta_Unicode.txt) | NoMeta (Continuous Chanting) | Malayalam | 34.9 KB | `b3a54cddf68bb74cd9c0648ebf76677193500c1c0de994b4a7297bdb10bd892b` |
| [`Samam_kpully_Malayalam_Samam_Unicode.txt`](../05_renders/txt/Samam_kpully_Malayalam_Samam_Unicode.txt) | Separate (Samam Only) | Malayalam | 35.0 KB | `67c928109b8c35165d98735321e6f1e5457b484793805ddfe49a800529203731` |
| [`Samam_kpully_Malayalam_Unicode.txt`](../05_renders/txt/Samam_kpully_Malayalam_Unicode.txt) | Separate (Samam Only) | Malayalam | 34.9 KB | `70449397215eb686683607030d814158887c5685eaeba483fc507e9b446fc106` |
| [`Samam_Malayalam_Samam_Devanagari_Unicode.txt`](../05_renders/txt/Samam_Malayalam_Samam_Devanagari_Unicode.txt) | Separate (Samam Only) | Malayalam | 33.4 KB | `f2a26cd00f1c22a3f2492b8a8fedf729e26ba3a99ab5495ae8c3a8ffe7262dce` |
| [`Samam_Malayalam_Samam_Unicode.txt`](../05_renders/txt/Samam_Malayalam_Samam_Unicode.txt) | Separate (Samam Only) | Malayalam | 34.8 KB | `4c4f3de47c293a8b1bde2972a3cc6ef39eee577e63750ad43dd88db2ce9176c1` |
| [`Samhita_Devanagari_Unicode.txt`](../05_renders/txt/Samhita_Devanagari_Unicode.txt) | Combined (Study Edition) | Devanagari (Standard) | 1.30 MB | `cc966727b94941cb9ec8fd7b04fd1c9b4e4854629ba9f51f3233cc33b955f76c` |
| [`Samhita_Devanagari_Unicode_with FN.txt`](../05_renders/txt/Samhita_Devanagari_Unicode_with FN.txt) | Combined (Study Edition) | Devanagari (Standard) | 1.30 MB | `627047c770cc7118396edfb095198617c0ed767b9b0bd304f9c12af228f8a05e` |
| [`Samhita_kpully_Devanagari_Samam_Unicode.txt`](../05_renders/txt/Samhita_kpully_Devanagari_Samam_Unicode.txt) | Combined (Study Edition) | Devanagari (Kodunthirapully) | 33.7 KB | `33ce4dafe6028fef5876ede707325746de4daffc35b4841bb9494ea09f88ef67` |
| [`Samhita_kpully_Devanagari_Unicode.txt`](../05_renders/txt/Samhita_kpully_Devanagari_Unicode.txt) | Combined (Study Edition) | Devanagari (Kodunthirapully) | 1.30 MB | `53cd3187795481264ec8511f48e4fad37ce7b8be34f5d485aaa5436cdcd892ad` |
| [`Samhita_Malayalam_Devanagari_Unicode.txt`](../05_renders/txt/Samhita_Malayalam_Devanagari_Unicode.txt) | Combined (Study Edition) | Malayalam | 33.5 KB | `72891fbdae38f2677499bcf690cee032431a16b0e9b5d3761a3e1781d55e99fe` |
| [`Samhita_Malayalam_Unicode.txt`](../05_renders/txt/Samhita_Malayalam_Unicode.txt) | Combined (Study Edition) | Malayalam | 34.9 KB | `5d589085f6974674f9f8340ac4f7451ca218cc140afef61d5611cfb783687fd6` |
| [`Samhita_Rik_Devanagari_Unicode.txt`](../05_renders/txt/Samhita_Rik_Devanagari_Unicode.txt) | Combined (Study Edition) | Devanagari (Standard) | 319.5 KB | `e1e0317e27eb1f857d7bd67bc7b9b9799e59383f8ea990eb558c6d540d3990f1` |
| [`Samhita_Rik_NoMeta_Devanagari_Unicode.txt`](../05_renders/txt/Samhita_Rik_NoMeta_Devanagari_Unicode.txt) | NoMeta (Continuous Chanting) | Devanagari (Standard) | 288.6 KB | `9a41d388e9fad77142993c63354170ab650c91592ac84ff12e02c1d6789d9683` |
| [`Samhita_Samam_Devanagari_Unicode.txt`](../05_renders/txt/Samhita_Samam_Devanagari_Unicode.txt) | Combined (Study Edition) | Devanagari (Standard) | 963.8 KB | `f82b40fa4a8a3091cb040d6c2c03cb07b606a63b58bb043be00a96bef345d575` |
| [`Samhita_Samam_NoMeta_Devanagari_Unicode.txt`](../05_renders/txt/Samhita_Samam_NoMeta_Devanagari_Unicode.txt) | NoMeta (Continuous Chanting) | Devanagari (Standard) | 816.7 KB | `9090a03d13348389d37bcbef70f0251a9c48519c38e7101cf3798b7e68df191b` |

---

## 7. Audit Reports & Integrity Check

### Audit Reports (`06_reports/`)
| Report File | Size |
| :--- | :--- |
| [`JSON_Samam_Continuity_Report.txt`](JSON_Samam_Continuity_Report.txt) | 823 B |
| [`JSV_Structure_Summary.csv`](JSV_Structure_Summary.csv) | 4.0 KB |
| [`JSV_Structure_Summary.txt`](JSV_Structure_Summary.txt) | 6.8 KB |
| [`Samhita_corrected_out_continuity_report.txt`](Samhita_corrected_out_continuity_report.txt) | 987 B |

### Verification Command
To verify cryptographic and liturgical invariants against golden baselines:
```bash
python src/tools/validate_run.py samhita
```
