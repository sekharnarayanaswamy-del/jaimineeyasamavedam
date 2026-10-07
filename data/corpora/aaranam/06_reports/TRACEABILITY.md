# Jaimineeya Samavedam — Traceability & Lineage Report: Aaranam

- **Corpus**: `aaranam`
- **Edition**: `1.14`
- **Generated Timestamp**: `07-10-2026 08:15:24`
- **Validation Status**: `PASSED`

---

## 1. Liturgical Invariants & Metrics
| Metric | Active Count | Baseline Invariant | Status |
| :--- | :--- | :--- | :--- |
| **Pathas (SuperSections)** | 6 | 1 | CHECK |
| **Khandas (Sections)** | 25 | 29 | CHECK |
| **Samas (Liturgical Chants)** | 154 | 401 | CHECK |

---

## 2. Cryptographic Stage Lineage (01 -> 02 -> 04)
| Stage | Canonical File | Size | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| **Stage 01: Input** | `Aaranam_latest.txt` | 501.1 KB | `16f16c3da6dd740daaae479b903bb094303a0dd4c872f8963e9c6c9e837bafe4` |
| **Stage 02: Parsed AST** | `Aaranam_ast.json` | 605.9 KB | `8b976fcc6e36f42f65b670280c8257e2742c0fa49ad2b02b9cc3bd9f52f59547` |
| **Stage 04: Canonical AST** | `Aaranam_vargeekaran.json` | 745.9 KB | `c131686229eb530164610b33565b23103da4de770fc04f1086a306254c6ffbaa` |

---

## 3. Compiled Render Catalog (`05_renders/`)

### PDF Documents (`05_renders/pdf/`)
| File Name | Mode / Edition | Target Script | Size |
| :--- | :--- | :--- | :--- |
| [`Aaranam_Devanagari.pdf`](../05_renders/pdf/Aaranam_Devanagari.pdf) | Combined (Study Edition) | Devanagari (Standard) | 525.1 KB |
| [`Aaranam_Rik_Devanagari.pdf`](../05_renders/pdf/Aaranam_Rik_Devanagari.pdf) | Combined (Study Edition) | Devanagari (Standard) | 130.3 KB |
| [`Aaranam_Rik_NoMeta_Devanagari.pdf`](../05_renders/pdf/Aaranam_Rik_NoMeta_Devanagari.pdf) | NoMeta (Continuous Chanting) | Devanagari (Standard) | 118.4 KB |
| [`Aaranam_Samam_Devanagari.pdf`](../05_renders/pdf/Aaranam_Samam_Devanagari.pdf) | Combined (Study Edition) | Devanagari (Standard) | 486.8 KB |
| [`Aaranam_Samam_NoMeta_Devanagari.pdf`](../05_renders/pdf/Aaranam_Samam_NoMeta_Devanagari.pdf) | NoMeta (Continuous Chanting) | Devanagari (Standard) | 486.8 KB |

### HTML Readers (`05_renders/html/`)
| File Name | Mode / Edition | Target Script | Size |
| :--- | :--- | :--- | :--- |
| [`Aaranam_Devanagari.html`](../05_renders/html/Aaranam_Devanagari.html) | Combined (Study Edition) | Devanagari (Standard) | 7.69 MB |
| [`Aaranam_Rik_Devanagari.html`](../05_renders/html/Aaranam_Rik_Devanagari.html) | Combined (Study Edition) | Devanagari (Standard) | 872.6 KB |
| [`Aaranam_Rik_NoMeta_Devanagari.html`](../05_renders/html/Aaranam_Rik_NoMeta_Devanagari.html) | NoMeta (Continuous Chanting) | Devanagari (Standard) | 843.9 KB |
| [`Aaranam_Samam_Devanagari.html`](../05_renders/html/Aaranam_Samam_Devanagari.html) | Combined (Study Edition) | Devanagari (Standard) | 5.34 MB |
| [`Aaranam_Samam_NoMeta_Devanagari.html`](../05_renders/html/Aaranam_Samam_NoMeta_Devanagari.html) | NoMeta (Continuous Chanting) | Devanagari (Standard) | 5.34 MB |

### PlainText Exports (`05_renders/txt/`)
| File Name | Mode / Edition | Target Script | Size |
| :--- | :--- | :--- | :--- |
| [`Aaranam_Devanagari_Unicode.txt`](../05_renders/txt/Aaranam_Devanagari_Unicode.txt) | Combined (Study Edition) | Devanagari (Standard) | 504.1 KB |

---

## 4. Source & Intermediate Datasets

### 01_input (Source Texts)
| File Name | Size | SHA-256 |
| :--- | :--- | :--- |
| [`Aaranam_latest.txt`](../01_input/Aaranam_latest.txt) | 501.1 KB | `16f16c3da6dd740d...` |
| [`Aaranam_rik.txt`](../01_input/Aaranam_rik.txt) | 20.3 KB | `61ffd4ce9e19e7d5...` |
| [`Aaranam_rik_samam_table.txt`](../01_input/Aaranam_rik_samam_table.txt) | 27.2 KB | `aae94e1875c5e348...` |

### 03_reconciliation (Editorial Tables)
| File Name | Size |
| :--- | :--- |
| [`Aaranam_Rik_Table.csv`](../03_reconciliation/Aaranam_Rik_Table.csv) | 96.2 KB |
| [`Aaranam_Rik_Table_Baseline.csv`](../03_reconciliation/Aaranam_Rik_Table_Baseline.csv) | 96.2 KB |
| [`Rik Reconciliation table (JSV-KSV) - Aaranam_latest.xlsx`](../03_reconciliation/Rik Reconciliation table (JSV-KSV) - Aaranam_latest.xlsx) | 71.0 KB |

---

## 5. Audit Reports (`06_reports/`)
| Report File | Size |
| :--- | :--- |
| [`Aaranam_Continuity_Report_Final.txt`](Aaranam_Continuity_Report_Final.txt) | 1.0 KB |
| [`Aaranam_vargeekaran_continuity_report.txt`](Aaranam_vargeekaran_continuity_report.txt) | 1.0 KB |

---

## 6. Audit & Validation Commands
To verify cryptographic and liturgical invariants against golden baselines:
```bash
python src/tools/validate_run.py aaranam
```
